#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

Notes:
1)
"""
from time import sleep_ms

from iba01_const import *

PG_GOOD = "PG_GOOD"                 # PG good status
PG_UNSUPPORTED = "PG_UNSUPPORTED"   # PG unknown status
PG_BAD = "PG_BAD"                   # vPG bad status

DEBUG = False    # Debug for prints

_DEBUG_FILE = "iba01_supply12"


class Supply12(object):
    """ IBA01 Supply V1 and V2 class

    V1 uses TPS7A2501, V2 uses TPS7A7200

    V2 has a wider range than V1.  V2 is a fast transient response LDO.

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

    LDO_VOLTAGE_MIN = [1650,  500]  # LDO output minimum, based on type index
    LDO_VOLTAGE_MAX = [4500, 3500]  # LDO output maximum, based on type index
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
    DELAY_CAL_LOAD_SETTLE_MS = 20
    DELAY_PG_LOAD_SETTLE_MS = 100

    def __init__(self, perph, addr, name, debug_print=None, type=0):
        self._name = name
        self._perph = perph
        self._adc = perph.adc()
        self._addr = addr          # this is address if GIO expander than controls this LDO
        self._voltage_mv = 0       # cached output voltage
        self._debug = debug_print
        self._cal_mask = 0x0
        self._cal_matrix = {}  # { voltage: [(resistance, current_ua)], ...} # starting at zero
        self._type = type

        self.reset()
        self._enable = False

        if self._debug: self._debug("init {}".format(self.LDO_TYPE[type]), 102, _DEBUG_FILE, self._name)

    def reset(self):
        """ puts the LDOs into a known state
            Writes to the GPIO expander which controls the LDOs

        :return:
        """
        # set the config, All pins are 'input' except for the enable, which is output,
        # ands LDO is disabled, LOW
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P0, 0xFF)  # all inputs
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P1, 0xFE)  # all inputs, except P10 (LoadBias) is always active

        # because all the outputs are open-drain, and we only want the
        # LOW value, all the output states will be set to LOW, thus
        # to "activate" a pin, just the CONFIG register needs to be changed.
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_OUTPUT_P0, 0x00)  # all low
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_OUTPUT_P1, 0x00)  # all low

        # no polarity inversion
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_POL_P0, 0x00)  # no inversion
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_POL_P1, 0x00)  # no inversion

        # disable the LDO
        val = (0xFF & ~(0x1 << self.LDO_ENABLE_SHIFT)) & 0xff  # set P06 LOW
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P0, val)
        if self._debug:
            self._debug("reset CONFIG_P0 0x{:02x}".format(val), 115, _DEBUG_FILE, self._name)

        self.voltage_mv(self.LDO_VOLTAGE_MIN[self._type])

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
        _register = self._perph.PCA95535_read(self._addr, PCA9555_CMD_CONFIG_P0)
        if enable:
            register = _register | (0x01 << self.LDO_ENABLE_SHIFT)
        else:
            register = _register & ~(0x01 << self.LDO_ENABLE_SHIFT)

        self._enable = enable

        if self._debug:
            msg = "enable {}, 0x{:02x} -> 0x{:02x}".format(enable, _register, register)
            self._debug(msg, 152, _DEBUG_FILE, self._name)
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P0, register)
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
        if self.LDO_VOLTAGE_MIN[self._type] <= voltage_mv <= self.LDO_VOLTAGE_MAX[self._type] and (voltage_mv % self.LDO_VOLTAGE_50mv) == 0:
            self._voltage_mv = voltage_mv
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
            _register = self._perph.PCA95535_read(self._addr, PCA9555_CMD_CONFIG_P0)
            register = (_register & ~self.LDO_SET_VOLTAGE_MASK) | set_voltage

            if self._debug:
                msg = "voltage_mv {}, 0x{:02x} -> 0x{:02x}".format(self._voltage_mv, _register, register)
                self._debug(msg, 208, _DEBUG_FILE, self._name)

            self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P0, register)
            sleep_ms(self.DELAY_PG_LOAD_SETTLE_MS)
            return self.power_good()

        if self._debug:
            msg = "voltage_mv {} not supported".format(self._voltage)
            self._debug(msg, 216, _DEBUG_FILE, self._name)

        return False, "{} mV voltage is not supported".format(voltage_mv)

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        # check the pin via the I2C GPIO mux
        pg_cache = self._perph.PCA95535_read(self._addr, PCA9555_CMD_INPUT_P0)
        pg_ret = PG_BAD
        if pg_cache & 0x80: pg_ret = PG_GOOD

        if self._debug:
            msg = "power_good: {}".format(pg_ret)
            self._debug(msg, 231, _DEBUG_FILE, self._name)

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

        p1_config_cache = self._perph.PCA95535_read(self._addr, PCA9555_CMD_CONFIG_P1)
        cal_value = (~value & 0xf) << 1
        # P14/P15 are set the same
        if cal_value & (0x1 << 4): cal_value = cal_value | (0x1 << 5)
        else: cal_value = cal_value & ~(0x1 << 5)

        p1_config = p1_config_cache & (~(0x1f << 1) & 0xff) | (cal_value & 0xff)
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P1, p1_config)

        _res = 0.0
        if value & 0x1: _res += 1 / self.CAL_P11_R
        if value & 0x2: _res += 1 / self.CAL_P12_R
        if value & 0x4: _res += 1 / self.CAL_P13_R
        if value & 0x8: _res += 1 / self.CAL_P14_R
        if _res == 0.0: _res = 0
        else: _res = 1 / _res

        if self._debug:
            msg = "cal_load 0x{:02x} {:.1f}, 0x{:02x} -> 0x{:02x}".format(value, _res, p1_config_cache, p1_config)
            self._debug(msg, 267, _DEBUG_FILE, self._name)

        return True, _res

    def calibrate(self, auto=True, resistance=0.0):
        """ Add calibration data

        Initially we look only for the zero load bias current offset
        # TODO: add better calibration, use the resistance param

        :param resistance:
        :return:
        """
        self._cal_matrix[self._voltage_mv] = []

        if auto:
            test_cals = [0, 1, 2, 4, 8]  # sets the cal loads
            for c in test_cals:
                _, resistance = self.cal_load(c)
                sleep_ms(self.DELAY_CAL_LOAD_SETTLE_MS)
                _, current_ua = self.current_ua(calibrating=True)
                self._cal_matrix[self._voltage_mv].append((resistance, current_ua))

            _, _ = self.cal_load(0)  # remove cal load(s)

        else:
            _, current_ua = self.current_ua(calibrating=True)
            self._cal_matrix[self._voltage_mv].append((resistance, current_ua))

        if self._debug:
            msg = "calibrate: {} ".format(self._cal_matrix)
            self._debug(msg, 296, _DEBUG_FILE, self._name)

        return True, None

    def _get_calibration_offset(self, adc_value):
        if self._voltage_mv not in self._cal_matrix:
            # TODO: pick closest calibrated voltage
            pass

        # TODO: make this better, calibrate based on the current adc value.

        return True, self._cal_matrix[self._voltage_mv][0][1]

    def current_ua(self, calibrating=False):
        ch = self.ADC_CHANNEL[self._type]
        adc_value = 0
        self._perph.adc_acquire()
        for i in range(self.ADC_SAMPLES):
            adc_value += self._adc.read(rate=4, channel1=ch)

        self._perph.adc_release()
        adc_value /= self.ADC_SAMPLES

        if calibrating:
            offset_current = 0
        else:
            success, offset_current = self._get_calibration_offset(adc_value)
            if not success:
                if self._debug:
                    msg = "current_ua: _get_calibration_offset({}) failed at {} mv".format(adc_value, self._voltage_mv)
                    self._debug(msg, 329, _DEBUG_FILE, self._name)

        current_ma = int(adc_value / 0x7fff / 12.5 * 1000000.0) - offset_current

        if self._debug:
            msg = "current_ua: adc_value {} ".format(adc_value)
            self._debug(msg, 315, _DEBUG_FILE, self._name)

        return True, current_ma

    def get_enable_voltage_mv(self):
        return self._enable, self._voltage_mv


if False:
    # Self Tests, example session, (set to True),
    # martin@martin-Lenovo-YOGA-900-13ISK2:~/sistemi/git/scripts/public/prism/drivers/iba01$ rshell
    # Connecting to /dev/ttyACM0 (buffer-size 512)...
    # Trying to connect to REPL  connected
    # Testing if sys.stdin.buffer exists ... Y
    # Retrieving root directories ... /flash/
    # Setting time ... Oct 08, 2019 12:14:00
    # Evaluating board_name ... pyboard
    # Retrieving time epoch ... Jan 01, 2000
    # Welcome to rshell. Use Control-D (or the exit command) to exit rshell.
    # /home/martin/sistemi/git/scripts/public/prism/drivers/iba01> cp iba01_supply12.py /flash
    # /home/martin/sistemi/git/scripts/public/prism/drivers/iba01> repl
    # Entering REPL. Use Control-X to exit.
    # >
    # MicroPython v1.11-182-g7c15e50eb on 2019-07-30; PYBv1.1 with STM32F405RG
    # Type "help()" for more information.
    # >>>
    # >>> import iba01_supply12
    # iba01_perphs   :periphs   :  63: i2c scan: [32, 33, 34, 35, 64, 72]
    # iba01_perphs   :periphs   :  70: init complete, iba01 True
    # iba01_supply12 :V2        : 115: reset CONFIG_P0 0xbf
    # ...

    from iba01_perphs import Peripherals
    from time import sleep

    def _print(msg, line=0, file="unknown", name=''):
        print("{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg))

    perphs = Peripherals(debug_print=_print)

    #ldo = Supply12(perphs, V1_I2C_ADDR, "V1", debug_print=_print)
    ldo = Supply12(perphs, V2_I2C_ADDR, "V2", debug_print=_print, type=1)

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

