#! /usr/bin/env python
# -*- coding: utf-8 -*-
import _thread
from machine import I2C

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

        P10 = output, 9VEN(able), push-pull
        P11 = output, 9VMODE, push-pull
        P12 = spare, not used
        P13 = spare, not used
        P14 = spare, not used
        P15 = spare, not used
        P16 = spare, not used
        P17 = spare, not used

    How to use:
    ...

    """
    I2C_HW_IDs = [UPYB_I2C_HW_I2C1, UPYB_I2C_HW_I2C2]

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
        self._name = "peripherals"
        self._debug = debug_print

        self.reset()

        if self._debug:
            self._debug("init complete", line=36, file=__DEBUG_FILE, name=self._name)

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

    def reset(self):
        """ puts the LDOs into a known state
            Writes to the GPIO expander which controls the LDOs

        :return:
        """
        # set the config, All pins are 'input' except for the enable, which is output,
        # ands LDO is disabled, LOW
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P0, 0xFF)  # all inputs
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_CONFIG_P1, 0xFC)  # all inputs, except P10/P11, always enabled

        # because all the outputs are open-drain, and we only want the
        # LOW value, all the output states will be set to LOW, thus
        # to "activate" a pin, just the CONFIG register needs to be changed.
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_OUTPUT_P0, 0x00)  # all low
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_OUTPUT_P1, 0x03)  # all low, except P10/P11, always enabled

        # no polarity inversion
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_POL_P0, 0x00)  # no inversion
        self.PCA95535_write(CON_I2C_ADDR, PCA9555_CMD_POL_P1, 0x00)  # no inversion

