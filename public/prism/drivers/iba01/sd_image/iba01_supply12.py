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

    V1 uses TPS7A7200, V2 uses TPS7A7200

    The PCA9555 setup, refer to the schematic:
        P00 = output, ~1600mV, Open-Drain
        P01 = output, ~8000mV, Open-Drain
        P02 = output, ~4000mV, Open-Drain
        P03 = output, ~2000mV, Open-Drain
        P04 = output, ~100mV,  Open-Drain
        P05 = output, ~50mV,   Open-Drain

        P06 = output, ENABLE, Open-Drain
        P07 = input, PowerGood

    Notes:
        1) For Open-Drain to be in the Hi-Z state, the pin must be set to an input.
        2) This driver does not cache the PCA9535 registers, instead, they are read
           before setting them.
    """
    LDO_TYPE = ["TPS7A7200", "TPS7A7200"]
    ADC_CHANNEL = [0, 1]
    GPIO_PORT = [
        {"PCA9555_CMD_INPUT": 0, "PCA9555_CMD_OUTPUT": 2, "PCA9555_CMD_POL": 4, "PCA9555_CMD_CONFIG": 6},
        {"PCA9555_CMD_INPUT": 1, "PCA9555_CMD_OUTPUT": 3, "PCA9555_CMD_POL": 5, "PCA9555_CMD_CONFIG": 7},
    ]

    LDO_ENABLE_SHIFT = 6    # bit location of the LDOs enable pin

    LDO_VOLTAGE_MIN = [500,   500]  # LDO output minimum, based on type index
    LDO_VOLTAGE_MAX = [3500, 3500]  # LDO output maximum, based on type index
    LDO_SET_VOLTAGE_MASK = 0x3f     # mask of the voltage set pins
    LDO_VOLTAGE_50mv = 50           # LSB of the LDO volt range
    LDO_VOLTAGE_50mv_SHIFT = 5      # register location of the 50mv pin
    LDO_VOLTAGE_100mv = 100         # voltage value of the 100mv pin
    LDO_VOLTAGE_100mv_SHIFT = 4     # register location of the 100mv pin
    LDO_VOLTAGE_200mv = 200         # voltage value of the 200mv pin
    LDO_VOLTAGE_200mv_SHIFT = 3     # register location of the 200mv pin
    LDO_VOLTAGE_400mv = 400         # voltage value of the 400mv pin
    LDO_VOLTAGE_400mv_SHIFT = 2     # register location of the 400mv pin
    LDO_VOLTAGE_800mv = 800         # voltage value of the 800mv pin
    LDO_VOLTAGE_800mv_SHIFT = 1     # register location of the 800mv pin
    LDO_VOLTAGE_1600mv = 1600       # voltage value of the 1600mv pin
    LDO_VOLTAGE_1600mv_SHIFT = 0    # register location of the 16000mv pin

    CAL_VOLTAGE_MV = 2000
    ADC_SAMPLES = 4  # number of samples to take an average over
    DELAY_CAL_LOAD_SETTLE_MS = 20
    DELAY_PG_LOAD_SETTLE_MS = 100
    CURR_TRANSFORM = 25.0 * 2.0  # gain of INA190 * Rsense

    def __init__(self, perph, addr, name, debug_print=None, type=0):
        self._name = name
        self._perph = perph
        self._gpio = self.GPIO_PORT[type]
        self._adc = perph.adc()
        self._addr = addr          # this is address if GIO expander than controls this LDO
        self._voltage_mv = 0       # cached output voltage
        self._debug = debug_print
        self._cal_mask = 0x0
        self._enable = False       # this may not be the case until after reset below...

        # !! Calibration needs to be done in order of increasing current !!!
        self._cal_matrix = {}  # { voltage_a: [(expected_ua_0, actual_ua_0),
                               #              (expected_ua_2000, actual_ua_2000),
                               #              (expected_ua_500, actual_ua_500),
                               #              (expected_ua_50, actual_ua_50)],
                               #   voltage_b: [ (...), ...], ... }
        self._type = type

        self.reset()
        # default calibration
        self.enable()
        self.voltage_mv(self.CAL_VOLTAGE_MV)
        self.calibrate(0)
        self.reset()

        if self._debug: self._debug("init {}".format(self.LDO_TYPE[type]), 102, _DEBUG_FILE, self._name)

    def reset(self):
        """ puts the LDOs into a known state
            Writes to the GPIO expander which controls the LDOs

        :return:
        """
        # set the config, All pins are 'input' except for the enable, which is output,
        # ands LDO is disabled, LOW
        self._perph.PCA95535_write(self._addr, self._gpio["PCA9555_CMD_CONFIG"], 0xFF)  # all inputs

        # because all the outputs are open-drain, and we only want the
        # LOW value, all the output states will be set to LOW, thus
        # to "activate" a pin, just the CONFIG register needs to be changed.
        self._perph.PCA95535_write(self._addr, self._gpio["PCA9555_CMD_OUTPUT"], 0x00)  # all low

        # no polarity inversion
        self._perph.PCA95535_write(self._addr, self._gpio["PCA9555_CMD_POL"], 0x00)  # no inversion

        # disable the LDO
        val = (0xFF & ~(0x1 << self.LDO_ENABLE_SHIFT)) & 0xff  # set Px6 LOW
        self._perph.PCA95535_write(self._addr, self._gpio["PCA9555_CMD_CONFIG"], val)
        if self._debug:
            self._debug("reset CONFIG_P0 0x{:02x}".format(val), 115, _DEBUG_FILE, self._name)

        self.voltage_mv(self.LDO_VOLTAGE_MIN[self._type])
        self._enable = False

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
        _register = self._perph.PCA95535_read(self._addr, self._gpio["PCA9555_CMD_CONFIG"])
        if enable:
            register = _register | (0x01 << self.LDO_ENABLE_SHIFT)
        else:
            register = _register & ~(0x01 << self.LDO_ENABLE_SHIFT)

        self._enable = enable

        if self._debug:
            msg = "enable {}, 0x{:02x} -> 0x{:02x}".format(enable, _register, register)
            self._debug(msg, 152, _DEBUG_FILE, self._name)
        self._perph.PCA95535_write(self._addr, self._gpio["PCA9555_CMD_CONFIG"], register)
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
            _register = self._perph.PCA95535_read(self._addr, self._gpio["PCA9555_CMD_CONFIG"])
            register = (_register & ~self.LDO_SET_VOLTAGE_MASK) | set_voltage

            if self._debug:
                msg = "voltage_mv {}, 0x{:02x} -> 0x{:02x}".format(self._voltage_mv, _register, register)
                self._debug(msg, 208, _DEBUG_FILE, self._name)

            self._perph.PCA95535_write(self._addr, self._gpio["PCA9555_CMD_CONFIG"], register)
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
        pg_cache = self._perph.PCA95535_read(self._addr, self._gpio["PCA9555_CMD_INPUT"])
        pg_ret = PG_BAD
        if pg_cache & 0x80: pg_ret = PG_GOOD

        if self._debug:
            msg = "power_good: {}".format(pg_ret)
            self._debug(msg, 231, _DEBUG_FILE, self._name)

        return True, pg_ret

    def calibrate(self, expected_ua):
        """ Add calibration data

        Initially we look only for the zero load bias current offset
        # TODO: add better calibration, use the resistance param

        :param expected_ua:
        :return:
        """
        if self._voltage_mv not in self._cal_matrix or expected_ua == 0:
            self._cal_matrix[self._voltage_mv] = []

        _, actual_ua = self.current_ua(calibrating=True)
        self._cal_matrix[self._voltage_mv].append((int(expected_ua), actual_ua))

        if self._debug:
            msg = "calibrate: {} ".format(self._cal_matrix)
            self._debug(msg, 296, _DEBUG_FILE, self._name)

        return True, None

    def _get_calibration_offset(self, current_ua):
        if self._voltage_mv not in self._cal_matrix:
            # fabricate a calibration offset, given that there is none for this voltage,
            # the guess cal will be based on zero current, so this is not great, but its something
            # this entry should always be present from init
            expected_ua, actual_ua = self._cal_matrix[self.CAL_VOLTAGE_MV][0]
            delta = (self._voltage_mv - self.CAL_VOLTAGE_MV) * 2.57  # 2.57 found experimentally
            actual_ua += delta
            if self._debug:
                msg = "_get_calibration_offset: no cal for this voltage, estimating"
                self._debug(msg, 312, _DEBUG_FILE, self._name)

        else:
            for expected_ua, actual_ua in self._cal_matrix[self._voltage_mv]:
                if current_ua <= actual_ua: break
                # FIXME: this is fine, but it ignores the calibration done at 0mA...
                # the last (only?) values from calmatrix will be used

        offset = actual_ua - expected_ua
        return True, int(offset)

    def current_ua(self, calibrating=False):
        ch = self.ADC_CHANNEL[self._type]
        adc_value = 0
        self._perph.adc_acquire()
        for i in range(self.ADC_SAMPLES):
            adc_value += self._adc.read(rate=4, channel1=ch)

        self._perph.adc_release()
        adc_value /= self.ADC_SAMPLES

        current_ua = int(float(adc_value) / float(0x7fff) * 4.096 / self.CURR_TRANSFORM * 1000000.0)

        if calibrating:
            offset_current = 0
        else:
            success, offset_current = self._get_calibration_offset(current_ua)
            if not success and self._debug:
                msg = "current_ua: _get_calibration_offset({}) failed at {} mv".format(current_ua, self._voltage_mv)
                self._debug(msg, 329, _DEBUG_FILE, self._name)

        current_ua -= offset_current

        if self._debug:
            msg = "current_ua: adc_value {} -> {} uA (offset: {})".format(adc_value, current_ua, offset_current)
            self._debug(msg, 338, _DEBUG_FILE, self._name)

        return True, current_ua

    def get_enable_voltage_mv(self):
        return self._enable, self._voltage_mv


if True:
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
    # ...

    from iba01_perphs import Peripherals
    from time import sleep

    def _print(msg, line=0, file="unknown", name=''):
        print("{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg))

    perphs = Peripherals(debug_print=_print)
    # on init perhs does a reset, so the relays are reset so V1/V2 are disconnected from DUT

    ldo = Supply12(perphs, V1_I2C_ADDR, "V1", debug_print=_print)
    ldo2 = Supply12(perphs, V2_I2C_ADDR, "V2", debug_print=_print, type=1)

    # basic enable/disable (after reset)
    ldo.enable()
    sleep(2)
    ldo.enable(False)
    sleep(1)

    # output some voltages, hold for a few sec and each one to measure
    test_voltages = [2000]
    cal_loads = [0x1, 0x2, 0x4]
    ldo.enable()
    for c in cal_loads:
        success, r = perphs.cal_load(c)
        for v in test_voltages:
            ldo.voltage_mv(v)
            if r == 0: expected_current = 0
            else: expected_current = int(v * 1000 / r)  # in uA
            _print("expected {} uA".format(expected_current))
            #ldo.calibrate(expected_current)  # comment this line out to test estimated calibration
            ldo.current_ua()
            sleep(2)

    ldo.enable(False)
