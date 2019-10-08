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


class IBA01Control(object):
    """

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

    Notes:
        1) For Open-Drain to be in the Hi-Z state, the pin must be set to an input.
        2) This driver does not cache the PCA9535 registers, instead, they are read
           before setting them.


    """

    def __init__(self, i2c, addr, name, debug_print=None):
        self._name = name
        self._i2c = i2c
        self._addr = addr          # this is address if GIO expander than controls this LDO
        self._debug = debug_print

        self.reset()

        if self._debug: self._debug("init", 102, _DEBUG_FILE, self._name)

    def reset(self):
        """ puts the LDOs into a known state
            Writes to the GPIO expander which controls the LDOs

        :return:
        """
        # set the config, All pins are 'input' except for the enable, which is output,
        # ands LDO is disabled, LOW
        self._GPIO_write(PCA9555_CMD_CONFIG_P0, 0xFF)  # all inputs
        self._GPIO_write(PCA9555_CMD_CONFIG_P1, 0xFC)  # all inputs, except P10/P11, always enabled

        # because all the outputs are open-drain, and we only want the
        # LOW value, all the output states will be set to LOW, thus
        # to "activate" a pin, just the CONFIG register needs to be changed.
        self._GPIO_write(PCA9555_CMD_OUTPUT_P0, 0x00)  # all low
        self._GPIO_write(PCA9555_CMD_OUTPUT_P1, 0x03)  # all low, except P10/P11, always enabled

        # no polarity inversion
        self._GPIO_write(PCA9555_CMD_POL_P0, 0x00)  # no inversion
        self._GPIO_write(PCA9555_CMD_POL_P1, 0x00)  # no inversion

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


