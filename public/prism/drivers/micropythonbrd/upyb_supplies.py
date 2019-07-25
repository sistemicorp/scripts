#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

Notes:
1)
"""
import pyb
from INA220 import INA220

CHANNELS = ["V1", "V2", "V3"]
LDOS = [
    {"name": "V1", "control_addr": 0x00, },
    {"name": "V2", "control_addr": 0x00, },
]

PG_GOOD = "PG_GOOD"
PG_BAD = "PG_BAD"
PG_UNSUPPORTED = "PG_UNSUPPORTED"


class SupplyStats(object):
    """

    This code uses the two INA220s on the board to make current and voltage
    measures on one of the supplies.

    """

    LOW_INA220_I2C_ADDR = 0x01
    HIGH_INA220_I2C_ADDR = 0x02

    LOW_SENSE = 20
    HIGH_SENSE = 0.2

    # etc... from your code...

    def __init__(self, i2c, supplies):
        self.supplies = supplies  # this gives you access to the LDOs, V3

    # etc... from your code...

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

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        """ Enable/Disable the LDO

        :param enable: True/False
        :return: success, enable
        """
        # set the LDO control pins via the I2C GPIO mux
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
        self.ctx["supplies"]["V3"] = V3(name)

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
if __name__ == "main":

    i2c = pyb.I2C("X9", "X10")
    supplies = Supplies(i2c)
