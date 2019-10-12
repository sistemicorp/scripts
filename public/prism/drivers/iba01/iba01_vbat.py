#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

Notes:
1)
"""
from time import sleep_ms

from iba01_INA220 import INA220
from iba01_const import *

PG_GOOD = "PG_GOOD"                 # PG good status
PG_UNSUPPORTED = "PG_UNSUPPORTED"   # PG unknown status
PG_BAD = "PG_BAD"                   # vPG bad status

DEBUG = False    # Debug for prints

_DEBUG_FILE = "iba01_vbat"


class SupplyVBAT(object):
    """ IBA01 Supply VBAT class

    VBAT uses LTC1118

    The PCA9555 setup, refer to the schematic:
        P00 = output, ~50mV,   Open-Drain
        P01 = output, ~100mV,  Open-Drain
        P02 = output, ~2000mV, Open-Drain
        P03 = output, ~4000mV, Open-Drain
        P04 = output, ~8000mV, Open-Drain
        P05 = output, ~1600mV, Open-Drain

        P06 = output, ENABLE, Open-Drain
        P07 = output, Cal Load 680, Open-Drain

        P10 = output, Cal Load 100, Open Drain
        P11 = output, -- tied to P10
        P12 = output, Cal Load 100, Open Drain
        P13 = output, -- tied to P12
        P14 = output, Cal Load 50, Open-Drain
        P15 = output, -- tied to P14
        P16 = output, -- tied to P14
        P17 = output, -- tied to P14

    Notes:
        1) For Open-Drain to be in the Hi-Z state, the pin must be set to an input.
        2) This driver does not cache the PCA9535 registers, instead, they are read
           before setting them.
        3) The calibration loads are handled like a bit-mask, each bit turns on
           a load, with special case of P14/15 which are turned on together

    """
    LDO_ENABLE_SHIFT = 6    # bit location of the LDOs enable pin, P06

    LDO_VOLTAGE_MIN = 1650          # LDO output minimum
    LDO_VOLTAGE_MAX = 4500          # LDO output maximum
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
    CAL_P07_R = 680
    CAL_P11_R = 100
    CAL_P12_R = 100
    CAL_P14_R = 50

    ADC_SAMPLES = 4  # number of samples to take an average over
    DELAY_CAL_LOAD_SETTLE_MS = 20
    DELAY_PG_LOAD_SETTLE_MS = 100

    def __init__(self, perph, addr, name, debug_print=None, type=0):
        self._name = name
        self._perph = perph
        self._addr = addr          # this is address if GIO expander than controls this LDO
        self._voltage_mv = 0       # cached output voltage
        self._debug = debug_print
        self._cal_mask = 0x0
        self._cal_matrix = {}  # { voltage: [(resistance, current_ua)], ...} # starting at zero

        self.ina220 = INA220(perph, INA220_I2C_ADDR, VBAT_INA220_RSENSE, "ina220", 4, debug_print)

        self.reset()
        self._enable = False

        if self._debug: self._debug("init", 95, _DEBUG_FILE, self._name)

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
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_OUTPUT_P0, 0x00 | (0x1 << self.LDO_ENABLE_SHIFT))  # all low, except P06
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_OUTPUT_P1, 0x00)  # all low

        # no polarity inversion
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_POL_P0, 0x00)  # no inversion
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_POL_P1, 0x00)  # no inversion

        # disable the LDO
        val = (0xFF & ~(0x1 << self.LDO_ENABLE_SHIFT)) & 0xff  # set P06 LOW
        self._perph.PCA95535_write(self._addr, PCA9555_CMD_CONFIG_P0, val)
        if self._debug:
            self._debug("reset CONFIG_P0 0x{:02x}".format(val), 115, _DEBUG_FILE, self._name)

        self.voltage_mv(self.LDO_VOLTAGE_MIN)

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        """ Enable/Disable the LDO

        LT1118 there is a pulldown on Enable (so this is reverse of V1/2)

        enable: Set P06 bit to High (so set to output)
        disable: Set P06 bit to Low (so set to input)

        :param enable: True/False
        :return: success, enable
        """
        _register = self._perph.PCA95535_read(self._addr, PCA9555_CMD_CONFIG_P0)
        if enable:
            register = _register & ~(0x01 << self.LDO_ENABLE_SHIFT)

        else:
            register = _register | (0x01 << self.LDO_ENABLE_SHIFT)

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
        if self.LDO_VOLTAGE_MIN<= voltage_mv <= self.LDO_VOLTAGE_MAX and (voltage_mv % self.LDO_VOLTAGE_50mv) == 0:
            self._voltage_mv = voltage_mv
            # set the LDO control pins via the I2C GPIO mux
            set_voltage = 0
            voltage_mv -= self.LDO_VOLTAGE_MIN
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
        success, vbus = self.ina220.read_bus_voltage()
        if not success: return False, PG_BAD

        if self._debug:
            msg = "power_good: vbus {}, voltage_mv {}".format(vbus, self._voltage_mv)
            self._debug(msg, 231, _DEBUG_FILE, self._name)

        if abs(self._voltage_mv - (vbus * 1000.0)) > 200: return True, PG_BAD

        return True, PG_GOOD

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
        if value & 0x1: _res += 1 / self.CAL_P07_R
        if value & 0x2: _res += 1 / self.CAL_P11_R
        if value & 0x4: _res += 1 / self.CAL_P12_R
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
        current_ma = 0
        return True, current_ma

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
    # >>> import iba01_supplyvbat
    # iba01_perphs   :periphs   :  63: i2c scan: [32, 33, 34, 35, 64, 72]
    # iba01_perphs   :periphs   :  70: init complete, iba01 True
    # iba01_supply12 :V2        : 115: reset CONFIG_P0 0xbf
    # ...

    from iba01_perphs import Peripherals
    from time import sleep_ms

    def _print(msg, line=0, file="unknown", name=''):
        print("{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg))

    perphs = Peripherals(debug_print=_print)

    vbat = SupplyVBAT(perphs, VBAT_I2C_ADDR, "VBAT", debug_print=_print)

    vbat.enable()
    vs = [1700, 1800, 2000, 3000, 4000, 4500]
    for v in vs:
        vbat.voltage_mv(v)
        sleep_ms(2000)
    vbat.enable(False)

