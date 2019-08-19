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
from time import sleep
from upyb_i2c import UPYB_I2C, UPYB_I2C_HW_I2C1

CHANNELS = ["V1", "V2", "V3"]               # possible supply channels supported
LDOS = [                                    # LDO names and corresponding I2C addresses
    {"name": "V1", "control_addr": 0x18, },
    {"name": "V2", "control_addr": 0x19, },
]
LDOS_V3 = {"name": "V3", "control_addr": 0x1e, }

GPIO_COMMAND_INPUT = 0x00       # register pointer of the input port
GPIO_COMMAND_OUTPUT = 0x01      # register pointer of the output port
GPIO_COMMAND_POLARITY = 0x02    # register pointer of the polarity port
GPIO_COMMAND_CONFIG = 0x03      # register pointer of the config port

SAMPLES_1 = 8    # 1 sample taken
SAMPLES_2 = 9    # 2 samples taken
SAMPLES_4 = 10   # 4 samples taken
SAMPLES_8 = 11   # 8 samples taken
SAMPLES_16 = 12  # 16 samples taken
SAMPLES_32 = 13  # 32 samples taken

PG_GOOD = "PG_GOOD"                 # PG good status
PG_UNSUPPORTED = "PG_UNSUPPORTED"   # PG unknown status
PG_BAD = "PG_BAD"                   # vPG bad status

DEBUG = False    # Debug for prints


class SupplyStats(object):
    """

    This code uses the two INA220s on the board to make current and voltage
    measures on one of the supplies.

    """
    V1_RELAY_SHIFT = 0  # bit location of supply V1 relay controlled by GPIO expander
    V2_RELAY_SHIFT = 2  # bit location of supply V2 relay controlled by GPIO expander
    V3_RELAY_SHIFT = 4  # bit location of supply V3 relay controlled by GPIO expander

    GPIO_CONFIG_ALL_INPUT = 0x3f   # has the effect of setting p0-p5 to high
    GPIO_LATCH_SET_MASK = 0X02     # b10
    GPIO_LATCH_RESET_MASK = 0x01   # b01
    GPIO_LATCH_CLEAR_MASK = 0x03   # b11

    GPIO_RELAY_ADDR = 0x1e    # I2C address of GPIO expander tha controls the relays

    INA220_HIGH_ADDR = 0x40   # I2C address of INA220 with the high current range (rsense = 0.6)
    INA220_LOW_ADDR = 0x41    # I2C address of INA220 with the low current range (rsense = 75)

    INA220_MIN = 0               # the INA220 minimum current measurable
    INA220_LOW_MAX = 0.002667    # the low range INA220 maximum current measurable
    INA220_HIGH_MAX = 0.533333   # the High range INA220 maximum current measurable

    INA220_RSENSE_0R6 = 0.6     # high range current INA220 rsense of 0,6 ohms
    INA220_RSENSE_75 = 75       # low range current INA220 rsense of 75 ohms

    samples = SAMPLES_4  # number of samples the INA220 will take

    # etc... from your code...

    def __init__(self, i2c):

        self._i2c = i2c
        self.led = pyb.LED(2)
        self.INA220_LOW = INA220(self._i2c, self.INA220_LOW_ADDR,  self.INA220_RSENSE_75, "LOW", self.samples)
        self.INA220_HIGH = INA220(self._i2c, self.INA220_HIGH_ADDR, self.INA220_RSENSE_0R6, "HIGH", self.samples)

        # set all outputs to low
        self._GPIO_write(GPIO_COMMAND_OUTPUT, 0x00)

        self.bypass()

    def _GPIO_write(self, command, value):
        """ writes to the GPIO expander that controls the relays

        :param command: which command register is being accessed
        :param value: the data being written
        :return:
        """
        bytes_write = [command & 0xFF, value & 0xFF]
        bytes_write = bytes(bytearray(bytes_write))
        self._i2c.acquire()
        self._i2c.writeto(self.GPIO_RELAY_ADDR, bytes_write)
        self._i2c.release()

    def _GPIO_read(self, command):
        """ reads from the GPIO expander

        :param command: which command register it is reading from
        :return: read (int)
        """
        self._i2c.acquire()
        self._i2c.writeto(self.GPIO_RELAY_ADDR, bytes(bytearray([command & 0xff])))
        read = self._i2c.readfrom(self.GPIO_RELAY_ADDR, 1)
        self._i2c.release()
        # print("register: {}".format(read))
        return ord(read)

    def _set_ina_channel(self, channel):
        """ sets the supply channel by changing the relays

        :param channel: the desired supply channel (V1, V2, V3)
        :return: success (True/False)
        """

        reg_cache = self._GPIO_read(GPIO_COMMAND_CONFIG)
        if channel == CHANNELS[0]:   # V1
            _reg_cache = reg_cache & ~(self.GPIO_LATCH_CLEAR_MASK << self.V1_RELAY_SHIFT)
            set_channel = self.GPIO_LATCH_SET_MASK << self.V1_RELAY_SHIFT | _reg_cache

        elif channel == CHANNELS[1]:  # V2
            _reg_cache = reg_cache & ~(self.GPIO_LATCH_CLEAR_MASK << self.V2_RELAY_SHIFT)
            set_channel = self.GPIO_LATCH_SET_MASK << self.V2_RELAY_SHIFT | _reg_cache

        elif channel == CHANNELS[2]:  # V3
            _reg_cache = reg_cache & ~(self.GPIO_LATCH_CLEAR_MASK << self.V3_RELAY_SHIFT)
            set_channel = self.GPIO_LATCH_SET_MASK << self.V3_RELAY_SHIFT | _reg_cache

        else:
            print(DEBUG, "I2C ADDRESS {} : _set_ina_channel: unknown supply channel".format(self.GPIO_RELAY_ADDR))
            return False

        # set P6 LOW for the FET bypass helper
        set_channel_pfet = reg_cache & (~(0x1 << 6) & 0xff)
        self._GPIO_write(GPIO_COMMAND_CONFIG, set_channel_pfet)
        # sleep(0.005)

        set_channel &= (~(0x1 << 6) & 0xff)  # keep P6 LOW when relay is set
        print(DEBUG, "I2C ADDRESS {} : set_channel: {}".format(self.GPIO_RELAY_ADDR, set_channel))
        self._GPIO_write(GPIO_COMMAND_CONFIG, set_channel)
        self.led.on()
        sleep(0.005)

        # P6 should be set HIGH again, so the PFET is turned back off, now that the relay has switched
        config_register_p67 = reg_cache & 0xc0 | (0x1 << 6)
        config_reg = config_register_p67 | self.GPIO_CONFIG_ALL_INPUT
        print(DEBUG, "I2C ADDRESS {} : _set_ina_channel: reset all back to all input {}".format(self.GPIO_RELAY_ADDR, config_reg))
        self._GPIO_write(GPIO_COMMAND_CONFIG, config_reg)
        return True

    def bypass(self):
        """ Set the INA circuit bypassed

        :return: success (True/False)
        """
        self.led.off()
        config_reg_cache = self._GPIO_read(GPIO_COMMAND_CONFIG)
        config_reg = self.GPIO_LATCH_RESET_MASK << self.V1_RELAY_SHIFT | \
                     self.GPIO_LATCH_RESET_MASK << self.V2_RELAY_SHIFT | \
                     self.GPIO_LATCH_RESET_MASK << self.V3_RELAY_SHIFT

        config_register_p67 = config_reg_cache & 0xc0
        config_reg |= config_register_p67
        print(DEBUG, "I2C ADDRESS {}: config_reg RESET: {}".format(self.GPIO_RELAY_ADDR, config_reg))

        self._GPIO_write(GPIO_COMMAND_CONFIG, config_reg)
        sleep(0.5)
        # config = self._GPIO_read(GPIO_COMMAND_CONFIG)
        # print("read_config: {}".format(config))
        config_reg = config_register_p67 | self.GPIO_CONFIG_ALL_INPUT
        print(DEBUG, "I2C ADDRESS {} : config_reg INPUT: {}".format(self. GPIO_RELAY_ADDR, config_reg))
        self._GPIO_write(GPIO_COMMAND_CONFIG, config_reg)
        return True, None

    def get_stats(self, channel):
        """ triggers the IN220 to measure and calculate

        :param channel: the supply channel under test
        :return: success, current, pg status
        """
        # switch the relays as required...
        self._set_ina_channel(channel)

        # make the measurements...
        _, voltagelow = self.INA220_LOW.read_shunt_voltage()
        _, voltagehigh = self.INA220_HIGH.read_shunt_voltage()
        print(DEBUG, "voltage low_mv: {:10.6f}, voltage high_mv: {:10.6f}".format(voltagelow, voltagehigh))

        success1, high_ina = self.INA220_HIGH.measure_current()
        success2, low_ina = self.INA220_LOW.measure_current()
        print(DEBUG, "high INA Current:{:10.6f}A, low INA Current:{:10.6f}A".format(high_ina, low_ina))

        if success1 and success2:
            _success, pg = supplies.power_good(channel)

            if _success:
                if self.INA220_MIN < low_ina < self.INA220_HIGH_MAX or \
                        self.INA220_MIN < high_ina < self.INA220_HIGH_MAX:
                    if low_ina < self.INA220_LOW_MAX:
                        print(DEBUG, "GET_STATS: CURRENT_LOW: {:10.6f}, PG: {}".format(low_ina, pg))
                        return True, {"c_ua": low_ina, "pg": pg}

                    print(DEBUG, "GET_STATS: CURRENT_HIGH: {:10.6f}, PG: {}".format(high_ina, pg))
                    return True, {"c_ua": high_ina, "pg": pg}

                print(DEBUG, "GET_STATS: CURRENT OUT OF RANGE: {:10.6f}, PG: {}".format(0, pg))
                return False, "current out of range"

            print(DEBUG, "GET_STATS: CURRENT: {:10.6f}, PG FAILED: {}".format(0, pg))
            return False, {"c_ua": 0, "pg": pg}

        print(DEBUG, "Failed to get measurements")
        return False, "Failed to read measurements"


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

    LDO_ENABLE_SHIFT = 6    # bit location of the LDOs enable pin

    LDO_VOLTAGE_MIN = 900           # LDO output minimum
    LDO_VOLTAGE_MAX = 3500          # LDO output maximum
    LDO_SET_VOLTAGE_LENGTH = 0x3f   # mask of the voltage set pins
    LDO_VOLTAGE_CALIBRATION = 500   # LDO internal reference voltage
    LDO_VOLTAGE_SET_BIT = 0x1       # b01
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

    def __init__(self, i2c, addr, name):
        self._name = name
        self._i2c = i2c
        self._addr = addr
        self._voltage_mv = 0
        self.led = pyb.LED(3)

        # set potential outputs to their default state of all 0
        # LDO is controlled by the GPIO expander
        self._GPIO_write(GPIO_COMMAND_OUTPUT, 0x00)

        # set polarity to its default value
        self._GPIO_write(GPIO_COMMAND_POLARITY, 0x70)

        # set all GPIO pins 0-5 and 7 to input, p6 must be set to an output
        # LDO is disable and set to lowest output value
        self._GPIO_write(GPIO_COMMAND_CONFIG, 0xbf)

    def _GPIO_write(self, command, value):
        """ writes to the GPIO expander tha controls the two LDOs
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

        :param enable: True/False
        :return: success, enable
        """
        # set the LDO control pins via the I2C GPIO mux
        # config pins 0-5 to be outputs
        _register = self._GPIO_read(GPIO_COMMAND_CONFIG)
        # print("starting register: {}".format(_register))
        if enable:
            register = _register | (0x01 << self.LDO_ENABLE_SHIFT)
            # print("set register: {}".format())
        else:
            register = _register & ~(0x01 << self.LDO_ENABLE_SHIFT)
            # print("set register: {}".format())

        self._GPIO_write(GPIO_COMMAND_CONFIG, register)
        print(DEBUG, "I2C ADDRESS {} : {} enable: register: {} -> {}".format(self._addr, self._name, _register, register))
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
        if self.LDO_VOLTAGE_MIN <= voltage_mv <= self.LDO_VOLTAGE_MAX and voltage_mv % self.LDO_VOLTAGE_50mv == 0:
            self._voltage = voltage_mv
            # set the LDO control pins via the I2C GPIO mux
            set_voltage = 0
            voltage_mv = voltage_mv - self.LDO_VOLTAGE_CALIBRATION
            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_1600mv >= 0:
                set_voltage |= (self.LDO_VOLTAGE_SET_BIT << self.LDO_VOLTAGE_1600mv_SHIFT) & self.LDO_SET_VOLTAGE_LENGTH
                voltage_mv -= self.LDO_VOLTAGE_1600mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_800mv >= 0:
                set_voltage |= (self.LDO_VOLTAGE_SET_BIT << self.LDO_VOLTAGE_800mv_SHIFT) & self.LDO_SET_VOLTAGE_LENGTH
                voltage_mv -= self.LDO_VOLTAGE_800mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_400mv >= 0:
                set_voltage |= (self.LDO_VOLTAGE_SET_BIT << self.LDO_VOLTAGE_400mv_SHIFT) & self.LDO_SET_VOLTAGE_LENGTH
                voltage_mv -= self.LDO_VOLTAGE_400mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_200mv >= 0:
                set_voltage |= (self.LDO_VOLTAGE_SET_BIT << self.LDO_VOLTAGE_200mv_SHIFT) & self.LDO_SET_VOLTAGE_LENGTH
                voltage_mv -= self.LDO_VOLTAGE_200mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_100mv >= 0:
                set_voltage |= (self.LDO_VOLTAGE_SET_BIT << self.LDO_VOLTAGE_100mv_SHIFT) & self.LDO_SET_VOLTAGE_LENGTH
                voltage_mv -= self.LDO_VOLTAGE_100mv

            if voltage_mv and voltage_mv - self.LDO_VOLTAGE_50mv >= 0:
                set_voltage |= (self.LDO_VOLTAGE_SET_BIT << self.LDO_VOLTAGE_50mv_SHIFT) & self.LDO_SET_VOLTAGE_LENGTH
                voltage_mv -= self.LDO_VOLTAGE_50mv

            set_voltage = ~ set_voltage & self.LDO_SET_VOLTAGE_LENGTH
            _voltage_mv = self._GPIO_read(GPIO_COMMAND_CONFIG)
            _voltage_mv = (_voltage_mv & ~ self.LDO_SET_VOLTAGE_LENGTH) | set_voltage
            print(DEBUG, "voltage_mv : set_voltage: {0:8b}".format(set_voltage))

            self._GPIO_write(GPIO_COMMAND_CONFIG, _voltage_mv)
            sleep(0.1)
            success, pg_status = self.power_good()

            if success:
                return success, set_voltage
            return success, "PG failure"
        # if DEBUG: print("DEBUG: I2C ADDRESS {} : voltage_mv: selected voltage is not supported, {}".format(self._addr, voltage_mv))
        return False, "selected voltage is not supported"

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        # check the pin via the I2C GPIO mux
        pg_cache = self._GPIO_read(GPIO_COMMAND_CONFIG)
        pg_cache = (pg_cache & ~0x7F) & 0xff
        if pg_cache == 0x80:
            # power good
            print(DEBUG, "I2C ADDRESS {} : power_good status {}". format(self._addr, PG_GOOD))
            return True, PG_GOOD

        # power bad
        print(DEBUG, "I2C ADDRESS {} : power_good status {}".format(self._addr, PG_BAD))
        return False, PG_BAD


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
        self.ctx["supplies"]["V3"] = V3(self.i2c, LDOS_V3["name"], LDOS_V3["control_addr"])

        self.stats = SupplyStats(self.i2c)

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

    def power_good(self, name):
        """ Gets the power good pin status

        :param name:
        :return: success, status
        """
        supply = self._get_supply_obj(name)
        if supply is None: return False, "unknown supply"

        return supply.power_good()

    def bypass_stats(self):
        """ Set the INA circuit to be bypassed

        :return: success, None
        """
        return self.stats.bypass()


# Test code
if False:
    # sets supply channel and put INA220 circuit in bypass
    i2c = machine.I2C("X", freq=400000)
    # i2c = UPYB_I2C()
    # i2c.init(UPYB_I2C_HW_I2C1)
    supplies = Supplies(i2c)
    supplies_stats = SupplyStats(i2c)
    supplies.ctx["supplies"]["V1"].enable()
    for i in range(4):
        supplies.ctx["supplies"]["V1"].enable()
        success, n = supplies.stats.INA220_LOW.read_bus_voltage()
        print(DEBUG, success, n)
        supplies.stats._set_ina_channel("V1")
        sleep(2)
        supplies.stats.bypass()
        supplies.ctx["supplies"]["V1"].enable(False)
        sleep(1)

if False:
    # sets LDO voltage and reads current from INA220
    UPYB_I2C_HW_I2C1 = "X"
    i2c = UPYB_I2C(UPYB_I2C_HW_I2C1)
    # success, message = i2c.init(UPYB_I2C_HW_I2C1)
    # print(success, message)
    supplies = Supplies(i2c)
    supplies.ctx["supplies"]["V1"].enable()
    for i in range(10):
        supplies.stats._set_ina_channel("V1")
        sleep(1)
        supplies.ctx["supplies"]["V1"].voltage_mv(2700)
        sleep(0.5)
        supplies.stats.get_stats("V1")
        sleep(5)
        # supplies.stats.bypass()
        print("\n")
        sleep(1)

if False:
    # checks the entire range of the LDO adjustable output
    UPYB_I2C_HW_I2C1 = "X"
    i2c = UPYB_I2C(UPYB_I2C_HW_I2C1)
    # success, message = i2c.init(UPYB_I2C_HW_I2C1)
    # print(success, message)
    supplies = Supplies(i2c)
    supplies.ctx["supplies"]["V1"].enable()
    volt = 900
    i = 0
    supplies.stats._set_ina_channel("V1")
    while 900 <= volt <= 3500:
        if i <= 52:
            volt += 50
            i += 1
            supplies.ctx["supplies"]["V1"].voltage_mv(volt)

        if 52 < i < 104:
            volt -= 50
            i += 1
            supplies.ctx["supplies"]["V1"].voltage_mv(volt)

        if i == 104:
            volt = 0
            supplies.ctx["supplies"]["V1"].voltage_mv(volt)

        sleep(0.05)
    supplies.stats.bypass()











