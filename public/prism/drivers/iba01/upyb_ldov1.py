#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

Notes:
1)
"""
import pyb
import machine
from time import sleep
from upyb_control import IBA01Control

PG_GOOD = "PG_GOOD"                 # PG good status
PG_UNSUPPORTED = "PG_UNSUPPORTED"   # PG unknown status
PG_BAD = "PG_BAD"                   # vPG bad status

DEBUG = False    # Debug for prints

_DEBUG_FILE = "upyb_ldov1"

PCA9555_CMD_INPUT_P0 = 0x0
PCA9555_CMD_INPUT_P1 = 0x1
PCA9555_CMD_OUTPUT_P0 = 0x2
PCA9555_CMD_OUTPUT_P1 = 0x3
PCA9555_CMD_POL_P0 = 0x4
PCA9555_CMD_POL_P1 = 0x5
PCA9555_CMD_CONFIG_P0 = 0x6
PCA9555_CMD_CONFIG_P1 = 0x7


class LDOV1(object):
    """

    The PCA9555 setup, refer to the schematic:
        P00 = output, ~50mV,   Open-Drain
        P01 = output, ~100mV,  Open-Drain
        P02 = output, ~2000mV, Open-Drain
        P03 = output, ~4000mV, Open-Drain
        P04 = output, ~8000mV, Open-Drain
        P05 = output, ~1600mV, Open-Drain

        P06 = output, ENABLE, Open-Drain
        P07 = input, PowerGood

        P10 = output, Load Bias Current, Open-Drain (this is a known resistive load)
        P11 = output, Cal Load 15k, Open-Drain
        P12 = output, Cal Load 4k, Open-Drain
        P13 = output, Cal Load 1k, Open-Drain
        P14 = output, Cal Load 100, Open-Drain
        P15 = output, Cal Load 100, Open-Drain (tied to P14 - !!USE Together!!

        P16 = spare, not used
        P17 = spare, not used

    Notes:
        1) For Open-Drain to be in the Hi-Z state, the pin must be set to an input.
        2) This driver does not cache the PCA9535 registers, instead, they are read
           before setting them.
        3) The calibration loads are handled like a bit-mask, each bit turns on
           a load, with special case of P14/15 which are turned on together

    """
    LDO_TYPE = ["TPS7A2501", "TPS7A7200"]
    ADC_CHANNEL = [0, 1]

    LDO_ENABLE_SHIFT = 6    # bit location of the LDOs enable pin

    LDO_VOLTAGE_MIN = [1650, 500]   # LDO output minimum, based on type index
    LDO_VOLTAGE_MAX = 3500          # LDO output maximum
    LDO_SET_VOLTAGE_MASK = 0x3f     # mask of the voltage set pins
    LDO_VOLTAGE_50mv = 50           # LSB of the LDO volt range
    LDO_VOLTAGE_50mv_SHIFT = 0      # register location of the 50mv pin
    LDO_VOLTAGE_100mv = 100         # voltage value of the 100mv pin
    LDO_VOLTAGE_100mv_SHIFT = 1     # register location of the 100mv pin
    LDO_VOLTAGE_200mv = 200         # voltage value of the 200mv pin
    LDO_VOLTAGE_200mv_SHIFT = 2     # register location of the 200mv pin
    LDO_VOLTAGE_400mv = 400         # voltage value of the 400mv pin
    LDO_VOLTAGE_400mv_SHIFT = 3     # register location of the 400mv pin
    LDO_VOLTAGE_800mv = 800         # voltage value of the 800mv pin
    LDO_VOLTAGE_800mv_SHIFT = 4     # register location of the 800mv pin
    LDO_VOLTAGE_1600mv = 1600       # voltage value of the 1600mv pin
    LDO_VOLTAGE_1600mv_SHIFT = 5    # register location of the 16000mv pin

    # the resistance at each GPIO pin for calibration
    CAL_P11_R = 15000
    CAL_P12_R = 4000
    CAL_P13_R = 1000
    CAL_P14_R = 100   # TODO: 100 is too large, HW needs to change to ~50

    ADC_SAMPLES = 4  # number of samples to take an average over

    def __init__(self, i2c, addr, name, adc, debug_print=None, type=0):
        self._name = name
        self._i2c = i2c
        self._addr = addr          # this is address if GIO expander than controls this LDO
        self._voltage_mv = 0       # cached output voltage
        self._debug = debug_print
        self._cal_mask = 0x0
        self._adc = adc
        self._cal_matrix = {}  # cals, voltage: [currents] # starting at zero
        self._type = type

        self.reset()

        if self._debug: self._debug("init {}".format(self.LDO_TYPE[type]), 102, _DEBUG_FILE, self._name)

    def reset(self):
        """ puts the LDOs into a known state
            Writes to the GPIO expander which controls the LDOs

        :return:
        """
        # set the config, All pins are 'input' except for the enable, which is output,
        # ands LDO is disabled, LOW
        self._GPIO_write(PCA9555_CMD_CONFIG_P0, 0xFF)  # all inputs
        self._GPIO_write(PCA9555_CMD_CONFIG_P1, 0xFE)  # all inputs, except P10 (LoadBias) is always active

        # because all the outputs are open-drain, and we only want the
        # LOW value, all the output states will be set to LOW, thus
        # to "activate" a pin, just the CONFIG register needs to be changed.
        self._GPIO_write(PCA9555_CMD_OUTPUT_P0, 0x00)  # all low
        self._GPIO_write(PCA9555_CMD_OUTPUT_P1, 0x00)  # all low

        # no polarity inversion
        self._GPIO_write(PCA9555_CMD_POL_P0, 0x00)  # no inversion
        self._GPIO_write(PCA9555_CMD_POL_P1, 0x00)  # no inversion

        # disable the LDO
        val = (0xFF & ~(0x1 << self.LDO_ENABLE_SHIFT)) & 0xff  # set P06 LOW
        if self._debug: self._debug("reset disable 0x{:02x}".format(val), 115, _DEBUG_FILE, self._name)
        self._GPIO_write(PCA9555_CMD_CONFIG_P0, val)

    def _GPIO_write(self, command, value):
        """ writes to the GPIO expander that controls the two LDOs
            intakes the command bits and the value, creates one byte and writes to GPIO

        :param command: which command register is being accessed
        :param value: the data being writen
        :return:
        """
        bytes_write = [command & 0xFF, value & 0xFF]
        bytes_write = bytes(bytearray(bytes_write))
        self._i2c.acquire()
        self._i2c.writeto(self._addr, bytes_write)
        self._i2c.release()

    def _GPIO_read(self, command):
        """ reads from the GPIO expander that conrols the two LDOs

        :param command: which command register is being accessed
        :return: read (int)
        """
        self._i2c.acquire()
        self._i2c.writeto(self._addr, bytes(bytearray([command & 0xff])))
        read = self._i2c.readfrom(self._addr, 1)
        self._i2c.release()
        # print("register: {}".format(read))
        return ord(read)

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        """ Enable/Disable the LDO

        enable: Set P06 bit to High (so set to input)
        disable: Set P06 bit to Low (so set to output)

        :param enable: True/False
        :return: success, enable
        """
        _register = self._GPIO_read(PCA9555_CMD_CONFIG_P0)
        if enable:
            register = _register | (0x01 << self.LDO_ENABLE_SHIFT)
        else:
            register = _register & ~(0x01 << self.LDO_ENABLE_SHIFT)

        if self._debug:
            msg = "enable {}, 0x{:02x} -> 0x{:02x}".format(enable, _register, register)
            self._debug(msg, 169, _DEBUG_FILE, self._name)
        self._GPIO_write(PCA9555_CMD_CONFIG_P0, register)
        return True, enable

    def get_feedback_resistance(self):
        """ return the feedback path resistance

        :return: success, ohms
        """
        # probably need to use the current voltage setting to compute resistance
        return True, 10000

    def voltage_mv(self, voltage_mv):
        """ Set the LDO voltage

        :param voltage_mv:
        :return: success, voltage_mv
        """
        # validate voltage_mv, check range, and divisible by 50 mV
        if self.LDO_VOLTAGE_MIN[self._type] <= voltage_mv <= self.LDO_VOLTAGE_MAX and (voltage_mv % self.LDO_VOLTAGE_50mv) == 0:
            self._voltage = voltage_mv
            # set the LDO control pins via the I2C GPIO mux
            set_voltage = 0
            voltage_mv -= self.LDO_VOLTAGE_MIN[self._type]
            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_1600mv >= 0:
                set_voltage |= (0x1 << self.LDO_VOLTAGE_1600mv_SHIFT) & self.LDO_SET_VOLTAGE_MASK
                voltage_mv -= self.LDO_VOLTAGE_1600mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_800mv >= 0:
                set_voltage |= (0x1 << self.LDO_VOLTAGE_800mv_SHIFT) & self.LDO_SET_VOLTAGE_MASK
                voltage_mv -= self.LDO_VOLTAGE_800mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_400mv >= 0:
                set_voltage |= (0x1 << self.LDO_VOLTAGE_400mv_SHIFT) & self.LDO_SET_VOLTAGE_MASK
                voltage_mv -= self.LDO_VOLTAGE_400mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_200mv >= 0:
                set_voltage |= (0x1 << self.LDO_VOLTAGE_200mv_SHIFT) & self.LDO_SET_VOLTAGE_MASK
                voltage_mv -= self.LDO_VOLTAGE_200mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_100mv >= 0:
                set_voltage |= (0x1 << self.LDO_VOLTAGE_100mv_SHIFT) & self.LDO_SET_VOLTAGE_MASK
                voltage_mv -= self.LDO_VOLTAGE_100mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_50mv >= -25:  # go halfway thru zero
                set_voltage |= (0x1 << self.LDO_VOLTAGE_50mv_SHIFT) & self.LDO_SET_VOLTAGE_MASK
                voltage_mv -= self.LDO_VOLTAGE_50mv

            set_voltage = ~set_voltage & self.LDO_SET_VOLTAGE_MASK
            _register = self._GPIO_read(PCA9555_CMD_CONFIG_P0)
            register = (_register & ~self.LDO_SET_VOLTAGE_MASK) | set_voltage

            if self._debug:
                msg = "voltage_mv {}, 0x{:02x} -> 0x{:02x}".format(self._voltage, _register, register)
                self._debug(msg, 231, _DEBUG_FILE, self._name)

            self._GPIO_write(PCA9555_CMD_CONFIG_P0, register)
            sleep(0.1)
            success, pg_status = self.power_good()

            if success:
                return success, set_voltage

            return success, "PG failure"

        if self._debug:
            msg = "voltage_mv {} not supported".format(self._voltage)
            self._debug(msg, 233, _DEBUG_FILE, self._name)

        return False, "selected voltage is not supported"

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        # check the pin via the I2C GPIO mux
        pg_cache = self._GPIO_read(PCA9555_CMD_INPUT_P0)
        pg_cache = (pg_cache & ~0x7F) & 0xff
        pg_ret = PG_BAD
        if pg_cache & 0x80:
            pg_ret = PG_GOOD

        if self._debug:
            msg = "power_good: {}".format(pg_ret)
            self._debug(msg, 259, _DEBUG_FILE, self._name)

        return True, pg_ret

    def cal_load(self, value):
        """ Enable calibration load(s)

        There are four bits of load. P11 is LSB, P14/15 is MSB.
        To turn on the bits, the CONFIG register needs each bit to be zero (active low)

        : param value: 0x0 to 0xf
        :return: success, load resistance in ohms
        """
        if value & ~0xf:
            return False, "value out of range"

        p1_config_cache = self._GPIO_read(PCA9555_CMD_CONFIG_P1)
        cal_value = (~value & 0xf) << 1
        # P14/P15 are set the same
        if cal_value & (0x1 << 4): cal_value = cal_value | (0x1 << 5)
        else: cal_value = cal_value & ~(0x1 << 5)

        p1_config = p1_config_cache & (~(0x1f << 1) & 0xff) | (cal_value & 0xff)
        self._GPIO_write(PCA9555_CMD_CONFIG_P1, p1_config)

        _res = 0.0
        if value & 0x1: _res += 1 / self.CAL_P11_R
        if value & 0x2: _res += 1 / self.CAL_P12_R
        if value & 0x4: _res += 1 / self.CAL_P13_R
        if value & 0x8: _res += 1 / self.CAL_P14_R
        if _res == 0.0: _res = 0
        else: _res = 1 / _res

        if self._debug:
            msg = "cal_load 0x{:02x} {:.1f}, 0x{:02x} -> 0x{:02x}".format(value, _res, p1_config_cache, p1_config)
            self._debug(msg, 298, _DEBUG_FILE, self._name)

        return True, _res

    def calibrate(self, resistance=0.0):
        """ Add calibration data

        Initially we look only for the zero load bias current offset
        # TODO: add better calibration, use the resistance param

        :param resistance:
        :return:
        """
        self._cal_matrix[self._voltage_mv] = []
        _, offset_current = self.current_ua(calibrating=True)
        self._cal_matrix[self._voltage_mv].append(offset_current)
        if self._debug:
            msg = "calibrate: {} ".format(self._cal_matrix)
            self._debug(msg, 315, _DEBUG_FILE, self._name)

    def current_ua(self, calibrating=False):
        if self._voltage_mv not in self._cal_matrix:
            return False, "Uncalibrated current for this voltage"

        if calibrating: offset_current = 0
        else: offset_current = self._cal_matrix[self._voltage_mv][0]

        ch = self.ADC_CHANNEL[self._type]
        adc_value = 0
        for i in range(self.ADC_SAMPLES):
            adc_value += self._adc.read(rate=4, channel1=ch)
        adc_value /= self.ADC_SAMPLES
        current_ma = int(adc_value / 0x7fff / 12.5 * 1000000.0) - offset_current

        if self._debug:
            msg = "current_ua: adc_value {} ".format(adc_value)
            self._debug(msg, 315, _DEBUG_FILE, self._name)

        return True, current_ma


if True:
    from upyb_i2c import UPYB_I2C, UPYB_I2C_HW_I2C1
    import upyb_ads1115

    def _print(msg, line=0, file="unknown", name=''):
        print("{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg))

    V1_I2C_ADDR = 0x20  # addr of GPIO expander controlling the LDO
    V2_I2C_ADDR = 0x21
    CON_I2C_ADDR = 0x23

    # i2c = machine.I2C("X")
    i2c = UPYB_I2C(UPYB_I2C_HW_I2C1, debug_print=_print)

    ads = upyb_ads1115.ADS1115(i2c, 0x48, gain=1)

    con = IBA01Control(i2c, CON_I2C_ADDR, "CON", debug_print=_print)

    #ldo = LDOV1(i2c, V1_I2C_ADDR, "V1", ads, debug_print=_print)
    ldo = LDOV1(i2c, V2_I2C_ADDR, "V2", ads, debug_print=_print, type=1)

    # basic enable/disable (after reset)
    ldo.enable()
    sleep(2)
    ldo.enable(False)
    sleep(1)

    # output some voltages, hold for a few sec and each one to measure
    test_voltages = [1700, 1800, 1900, 2000, 2100]
    ldo.enable()
    for v in test_voltages:
        ldo.voltage_mv(v)
        sleep(1)
    ldo.enable(False)

    # calibrate and apply loads, measure error
    TEST_VOLTAGE = 2000
    test_cals = [1, 2, 4, 8, 6]
    ldo.enable()
    ldo.voltage_mv(TEST_VOLTAGE)
    ldo.cal_load(0)
    ldo.calibrate()
    for c in test_cals:
        _, resistance = ldo.cal_load(c)
        _, current_ua = ldo.current_ua()
        expected_ua = TEST_VOLTAGE * 1000 / resistance
        err = (expected_ua - current_ua) * 100 / expected_ua
        _print("current: {} uA, expected {} uA, {:.1f}% error".format(current_ua, expected_ua, err))
        sleep(1)
    ldo.enable(False)
    ldo.cal_load(0)



