#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

Notes:
1)
"""
import pyb
import machine
from upyb_INA220 import INA220

CHANNELS = ["V1", "V2", "V3"]
LDOS = [
    {"name": "V1", "control_addr": 0x18, },
    {"name": "V2", "control_addr": 0x19, },
]
LDOS_V3 = {"name": "V3", "control_addr": 0x1e, }

INPUT_COM = 0x00
OUTPUT_COM = 0x01
POLARITY_COM = 0x02
CONFIG_COM = 0x03

SAMPLES_1 = 8
SAMPLES_2 = 9
SAMPLES_4 = 10
SAMPLES_8 = 11
SAMPLES_16 = 12
SAMPLES_32 = 13

PG_GOOD = "PG_GOOD"
PG_BAD = "PG_BAD"
PG_UNSUPPORTED = "PG_UNSUPPORTED"


class SupplyStats(object):
    """

    This code uses the two INA220s on the board to make current and voltage
    measures on one of the supplies.

    """

    INA220_LOW_ADDR = 64
    INA220_HIGH_ADDR = 65

    INA220_RSENSE_0R6 = 0.6
    INA220_RSENSE_75 = 75
    samples = SAMPLES_1

    # etc... from your code...

    def __init__(self, i2c, supplies):
        self.supplies = supplies  # this gives you access to the LDOs, V3

        self.i2c = i2c
        self.INA220_LOW = INA220(self.i2c, self.INA220_LOW_ADDR,  self.INA220_RSENSE_75, "LOW", self.samples)
        self.INA220_HIGH = INA220(self.i2c, self.INA220_HIGH_ADDR, self.INA220_RSENSE_0R6, "HIGH", self.samples)


    def _get_supply_obj(self, name):
        return self.supplies.get(name, None)

    def bypass(self):
        """ Set the INA circuit bypassed

        :return: success
        """
        return True, None

    def get_stats(self, name):
        """

        :param name:
        :return: success, voltage, current
        """
        supply = self._get_supply_obj(name)

        # switch the relays as required...

        # on error, return False, {}

        # make the measurements...
        voltage_mv = 1
        current_ua = 1
        pg = supply.power_good()
        return True, {"v_mv": voltage_mv, "c_ua": current_ua, "pg": pg}


class V3(object):
    """ V3 Class
    - V3 is not like the other LDOs, so need a different class to handle it
    - V3 only has enable

    """

    OUTPUT_VOLTAGE_MV = 12000
    FEEDBACK_RESISTANCE = 10000

    def __init__(self, i2c, addr, name="V3"):
        # disable on init
        pass

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        # set the V3 enable pin via the I2C GPIO mux
        pass

    def get_feedback_resistance(self):
        """ return the feedback path resistance

        :return: success, ohms
        """
        # this will be a set value on the PCB
        return True, self.FEEDBACK_RESISTANCE

    def voltage_mv(self, voltage_mv):
        """ Set the LDO voltage

        :param voltage_mv:
        :return: success, voltage_mv
        """
        if voltage_mv == self.OUTPUT_VOLTAGE_MV:
            return True, voltage_mv
        return False, voltage_mv

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        return True, PG_UNSUPPORTED


class LDO(object):

    def __init__(self, i2c, addr, name):
        self._name = name
        self._i2c = i2c
        self._addr = addr
        self._voltage_mv = 0

        # set potenial outputs to their default state of all 0
        for name in LDOS:
            set_output_low = self.create_bit(OUTPUT_COM, 0x00)
            self.micropy_i2c.writeto(LDOS["control_addr"], set_output_low)

            # set polarity to its default value
            set_polarity_default = self.create_bit(POLARITY_COM, 0x70)
            self.micropy_i2c.writeto(LDOS["control_addr"], set_polarity_default)

    def create_bit(self, command, value):
        _bit = command | value
        bit = [(_bit >> 8) & 0xFF, (_bit) & 0xFF]
        bit = bytes(bytearray(bit)
        return bit

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        """ Enable/Disable the LDO

        :param enable: True/False
        :return: success, enable
        """
        # set the LDO control pins via the I2C GPIO mux
        # config pins 0-5 to be outputs
        for name in LDOS:
            # set all LDO pins to outputs
            set_config_out = self.create_bit(CONFIG_COM, 0xc00)
            self.micropy_i2c.writeto(LDOS["control_addr"], set_config_out)

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
        # set the LDO control pins via the I2C GPIO mux

        self._voltage = voltage_mv
        return True, voltage_mv

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        # check the pin via the I2C GPIO mux
        return True, PG_GOOD


class Supplies(object):

    def __init__(self, i2c):
        self.i2c = i2c
        self.ctx = {
            "supplies": {},  # supply objects, key'd on name
        }

        # init LDOs
        for ldo in LDOS:
            name = ldo["name"]
            i2c_addr = ldo["control_addr"]
            self.ctx["supplies"][name] = LDO(self.i2c, i2c_addr, name)

        # init special V3 case
        self.ctx["supplies"]["V3"] = V3(self.i2c, LDOS_V3["control_addr"], LDOS_V3["name"])

        self.stats = SupplyStats(self.i2c, self.ctx)

    def _get_supply_obj(self, name):
        return self.ctx["supplies"].get(name, None)

    def set_voltage_mv(self, name, voltage_mv):
        """ Set an LDO to a voltage

        :param name:
        :param voltage_mv:
        :return: success, voltage_mv
        """
        supply = self._get_supply_obj(name)
        if supply is None: return False, "unknown supply"

        return supply.voltage_mv(voltage_mv)

    def get_stats(self, name):
        """ Get data (voltage, current, PG, ...) for the supply

        :param name:
        :return: success, {"v_mv": <int>, "c_ua": <int>, ["pg": <bool>]}
        """
        supply = self._get_supply_obj(name)
        if supply is None: return False, {}

        return self.stats.get_stats(supply)

    def bypass_stats(self):
        """ Set the INA circuit to be bypassed

        :return: success, None
        """
        return self.stats.bypass()


# Test code
if True:

    i2c = machine.I2C("X", freq=400000)
    supplies = Supplies(i2c)
    success, n = supplies.stats.INA220_LOW.read_bus_voltage()
    print(success, n)
