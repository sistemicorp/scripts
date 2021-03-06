#! /usr/bin/env python
# -*- coding: utf-8 -*-
import _thread
from machine import I2C
from time import sleep_ms

from iba01_ads1115 import ADS1115
from iba01_const import *


__DEBUG_FILE = "iba01_perphs"


class Peripherals(object):
    """ API for common peripherals, I2C, ADC, ...
    - adds a lock to sequence clients

    9V, Relay Control (I2C: CON_I2C_ADDR):
        The PCA9555 setup, refer to the schematic:
        P00 = output, V12CONN(ect),   Open-Drain
        P01 = output, V12DIS(connect),  Open-Drain
        P02 = output, VSYSCONN(ect) (and 9V), Open-Drain
        P03 = output, VSYSDIS(connect) (and 9V), Open-Drain
        P04 = output, VBATCONN(ect), Open-Drain
        P05 = output, VBATDIS(connect), Open-Drain
        P06 = spare, not used
        P07 = spare, not used

        P10 = output, 9VEN(able), push-pull, output HIGH, TLV61048
        P11 = output, 9VMODE, pulled LOW (1MHz mode), TLV61048
        P12 = spare, not used
        P13 = spare, not used
        P14 = spare, not used
        P15 = spare, not used
        P16 = spare, not used
        P17 = spare, not used

    How to use:
    1) Based on SCH A0109, A0110, ...

    """
    I2C_HW_IDs = [UPYB_I2C_HW_I2C1, UPYB_I2C_HW_I2C2]

    IBA01_SCAN = [32, 34, 35, 64, 72]  # 3 GPIO expanders, ADS1115, INA220

    RELAYV12_CON  = 0x1 << 0
    RELAYV12_DIS  = 0x1 << 1
    RELAYVSYS_CON = 0x1 << 2
    RELAYVSYS_DIS = 0x1 << 3
    RELAYVBAT_CON = 0x1 << 4
    RELAYVBAT_DIS = 0x1 << 5

    CAL_P10_R = 2000
    CAL_P11_R = 500
    CAL_P12_R = 50

    def __init__(self, i2c=0, freq=400000, adc_addr=0x48, adc_gain=1, debug_print=None):
        """
        - see http://docs.micropython.org/en/latest/pyboard/quickref.html#i2c-bus
        - note that we want to use HW I2C, not software emulated, so have id=1 for X10/X9, and
          id=2 for Y9/10

        """
        # this function defaults to "X" this board does not support "Y"
        self._i2c = I2C(self.I2C_HW_IDs[i2c], freq=freq)
        self._adc = ADS1115(self._i2c, address=adc_addr, gain=adc_gain)
        self._i2c_lock = _thread.allocate_lock()
        self._adc_lock = _thread.allocate_lock()
        self._name = "periphs"
        self._debug = debug_print
        self._iba01 = False

        scan = self._i2c.scan()
        if self._debug:
            self._debug("i2c scan: {}".format(scan), line=63, file=__DEBUG_FILE, name=self._name)

        if self.IBA01_SCAN == scan:
            self._iba01 = True
            self.reset()

        if self._debug:
            self._debug("init complete, iba01 {}".format(self._iba01),
                        line=70, file=__DEBUG_FILE, name=self._name)

    def is_iba01(self):
        return self._iba01

    def i2c_acquire(self):
        return self._i2c_lock.acquire()

    def i2c_release(self):
        return self._i2c_lock.release()

    def adc_acquire(self):
        return self._i2c_lock.acquire()

    def adc_release(self):
        return self._i2c_lock.release()

    def adc(self):
        return self._adc

    def i2c(self):
        return self._i2c

    def PCA95535_write(self, addr, command, value):
        """ writes to the GPIO expander that controls the two LDOs
            intakes the command bits and the value, creates one byte and writes to GPIO

        :param command: which command register is being accessed
        :param value: the data being writen
        :return:
        """
        bytes_write = [command & 0xFF, value & 0xFF]
        bytes_write = bytes(bytearray(bytes_write))
        self.i2c_acquire()
        self._i2c.writeto(addr, bytes_write)
        self.i2c_release()

    def PCA95535_read(self, addr, command):
        """ reads from the GPIO expander that conrols the two LDOs

        :param command: which command register is being accessed
        :return: read (int)
        """
        self.i2c_acquire()
        self._i2c.writeto(addr, bytes(bytearray([command & 0xff])))
        read = self._i2c.readfrom(addr, 1)
        self.i2c_release()
        # print("register: {}".format(read))
        return ord(read)

    def _relay(self, connect, con, dis):
        _reg = self.PCA95535_read(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P0)
        if connect: reg = _reg & (~(con)) & 0xff  # set bit low to pull down
        else: reg = _reg & (~(dis)) & 0xff  # set bit low to pull down
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P0, reg)
        sleep_ms(50)
        reg = _reg | con | dis  # set bit high to go back to input mode
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P0, reg)
        return True

    def relay_v12(self, connect=True):
        return self._relay(connect, self.RELAYV12_CON, self.RELAYV12_DIS)

    def relay_vsys(self, connect=True):
        return self._relay(connect, self.RELAYVSYS_CON, self.RELAYVSYS_DIS)

    def relay_vbat(self, connect=True):
        return self._relay(connect, self.RELAYVBAT_CON, self.RELAYVBAT_DIS)

    def cal_load(self, value):
        """ Enable calibration load(s)

        There are three bits of load. P10 is LSB, P12 is MSB.
        To turn on the bits, the CONFIG register needs each bit to be zero (active low)

        : param value: 0x0 to 0x7
        :return: success, load resistance in ohms
        """
        if value & ~0x7:
            return False, "value out of range"

        p1_output_cache = self.PCA95535_read(CON_I2C_ADDR, PCA9555_CMD_OUTPUT_P1)
        p1_output = (p1_output_cache & 0xf8) | (value & 0x7)
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_OUTPUT_P1, p1_output)

        _res = 0.0
        if value & 0x1: _res += 1 / self.CAL_P10_R
        if value & 0x2: _res += 1 / self.CAL_P11_R
        if value & 0x4: _res += 1 / self.CAL_P12_R
        if _res == 0.0: _res = 0
        else: _res = 1 / _res

        if self._debug:
            msg = "cal_load 0x{:02x} {:.1f}, 0x{:02x} -> 0x{:02x}, {} Ohms".format(value, _res, p1_output_cache, p1_output, _res)
            self._debug(msg, 267, __DEBUG_FILE, self._name)

        return True, _res

    def reset(self):
        """ puts the LDOs into a known state
            Writes to the GPIO expander which controls the LDOs

            Set P10, P11, P12 to output active LOW to turn off CAL loads

        :return:
        """
        # set the config, All pins are 'input' except for the enable, which is output,
        # ands LDO is disabled, LOW
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P0, 0xFF)  # all inputs
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P1, 0xF8)  # all inputs, except P10/P11/P12 always output

        # LOW value, all the output states will be set to LOW, thus
        # to "activate" a pin, just the CONFIG register needs to be changed.
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_OUTPUT_P0, 0x00)  # all low
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_OUTPUT_P1, 0x00)  # all low

        # no polarity inversion
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_POL_P0, 0x00)  # no inversion
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_POL_P1, 0x00)  # no inversion

        self.cal_load(0)
        self.relay_v12(False)
        self.relay_vbat(False)
        self.relay_vsys(False)


if False:

    def _print(msg, line=0, file="unknown", name=''):
        print("{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg))

    p = Peripherals(debug_print=_print)


