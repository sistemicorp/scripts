#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
import time
from core.test_item import TestItem
from public.prism.api import ResultAPI
from public.prism.drivers.iba01.iba01_const import *

# file and class name must match
class iba0100xx(TestItem):
    """ Python Methods for both PyBoard and IBA01

    - PYBRDxxxx methods are for PyBoard AND IBA01 only
    - IBA01xxxx methods are for IBA01 ONLY

    """

    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("pybrd00xx.{}".format(self.chan))

        self.pyb = None
        self.pyb_port = None
        self.slot = None

    def PYBRD0xxSETUP(self):
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type="IBA01")
        if len(drivers) > 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        self.logger.info("Found pybrd: {}".format(driver))
        self.pyb_port = driver["obj"]["port"]

        if self.pyb_port is None:
            self.logger.error("Could not find pyboard driver")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return

        id = driver["obj"]["id"]  # save the id of the pyboard for the record
        _, _, _bullet = ctx.record.measurement("pyboard_id", id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        self.slot = driver["obj"].get("slot", None)

        self.pyb = driver["obj"]["pyb"]

        success, result = self.pyb.reset()
        if not success:
            self.logger.error("failed to reset IBA01")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return

        self.item_end()  # always last line of test

    def PYBRD0xxTRDN(self):
        ctx = self.item_start()  # always first line of test

        success, result = self.pyb.reset()
        if not success:
            self.logger.error("failed to reset IBA01")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return

        self.item_end()  # always last line of test

    def PYBRD0010_LedToggle(self):
        """ In this test the user confirms if the LED under test blinked
        (this is also an example of one test item being run multiple times
        with different arguments)

        {"id": "PYBRD0010_LedToggle",     "enable": true, "lednum": 2, "ontime_ms": 300 },

        where,
           lednum: 1=red, 2=green, 3=yellow, 4=blue

        """
        ctx = self.item_start()  # always first line of test

        # 1=red, 2=green, 3=yellow, 4=blue
        LED_COLORS = ["Red", "Green", "Yellow", "Blue"]

        ontime_ms = ctx.item.get("ontime_ms", 300)
        lednum = ctx.item.get("lednum", 1)

        self.log_bullet("Watch which color Led blinks...")

        success, result = self.pyb.led_toggle(lednum, ontime_ms)
        if not success:
            self.logger.error(result)
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet("UNKNOWN PYBOARD ERROR")
            self.item_end(_result)  # always last line of test
            return

        buttons = ["{}".format(LED_COLORS[lednum-1]), "None", "Other"]
        user_select = self.input_button(buttons)

        if user_select["success"]:
            b_idx = user_select["button"]
            self.log_bullet("{} was pressed!".format(buttons[b_idx]))
            _, _result, _bullet = ctx.record.measurement("button", b_idx, ResultAPI.UNIT_INT, min=0, max=0)
            self.log_bullet(_bullet)

        else:
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet(user_select.get("err", "UNKNOWN ERROR"))

        # turn off blinky led
        self.pyb.led_toggle(lednum, 0)
        self.item_end(_result)  # always last line of test

    def PYBRD0020_adc_read(self):
        """ Read ADC channel.

        {"id": "PYBRD0020_adc_read",      "enable": true,  "pin": "TEMP", "samples": 2, "delay_s": 0, "name": "MyKnob",
                                          "min": 18, "max": 26, "gain": 1, "unit": "UNIT_CELCIUS" },

        background: https://github.com/micropython/micropython/pull/3656
        http://docs.micropython.org/en/v1.9.4/pyboard/library/pyb.ADC.html#pyb-adc
        https://forum.micropython.org/viewtopic.php?f=6&t=4540&hilit=%27module%27+object+has+no+attribute+%27ADC%27&start=10
        """
        ctx = self.item_start()  # always first line of test

        pin = ctx.item.get("pin", None)
        samples = ctx.item.get("samples", 1)
        unit = getattr(ResultAPI, ctx.item.get("unit", ResultAPI.UNIT_NONE), ResultAPI.UNIT_NONE)
        min = ctx.item.get("min", None)
        max = ctx.item.get("max", None)
        delay_ms = ctx.item.get("delay_s", 0)
        name = ctx.item.get("name", pin)  # if no name supplied use channel
        scale = ctx.item.get("scale", 4096)  # scale the result to the ADC range

        success, result = self.pyb.adc_read(pin, samples, delay_ms)
        self.logger.info("{} {}".format(success, result))

        if not success:
            self.log_bullet("ADC pin {}: Failed".format(pin))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        value = result["value"]["value"] * scale / 4096
        self.log_bullet("ADC pin {}: {}".format(pin, value))

        _, _result, _bullet = ctx.record.measurement("{}".format(name), value, unit, min, max)
        self.log_bullet(_bullet)

        self.item_end(_result)  # always last line of test

    def PYBRD0030_pwm(self):
        """ Turn on/off PWM
        - this function inits the GPIO (no need to call PYBRD0040_init_gpio)

        {"id": "PYBRD0030_pwm",           "enable": true,  "pin": "Y1", "freq": 1000, "duty_cycle": 25, "en": true},

        :return:
        """
        ctx = self.item_start()  # always first line of test

        en = ctx.item.get("en", True)
        pin = ctx.item.get("pin", None)
        name = "pwm_{}".format(pin)
        channel = 1  # this is the timer channel, TODO: make this depend on pin(?)
        freq = ctx.item.get("freq", 1000) + 100 * self.chan
        duty_cycle = ctx.item.get("duty_cycle", 50) + 10 * self.chan

        if pin in ["Y1", "Y7", "Y8", "Y11", "Y12", "X6", "X8"]: timer = 8
        # TODO: complete this list for other pins

        if en: success, result = self.pyb.init_gpio(name, "Y1", PYB_PIN_OUT_PP, PYB_PIN_PULLNONE)
        else:  success, result = self.pyb.init_gpio(name, "Y1", PYB_PIN_IN, PYB_PIN_PULLNONE)
        if not success:
            self.logger.error(result)
            self.log_bullet("pwm {}: Failed".format(name))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        success, result = self.pyb.pwm(name, name, timer, channel, freq, duty_cycle, en)
        if not success:
            self.logger.error(result)
            self.log_bullet("pwm {}: Failed".format(name))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        self.item_end()  # always last line of test

    def PYBRD0040_init_gpio(self):
        """ Init GPIO

        {"id": "PYBRD0040_init_gpio", "enable": true,  "pin": "X12", "mode": "PYB_PIN_IN", "pull": "PYB_PIN_PULLNONE"},

        :return:
        """
        ctx = self.item_start()  # always first line of test
        pin = ctx.item.get("pin", None)
        mode = ctx.item.get("mode", "PYB_PIN_IN")
        pull = ctx.item.get("pull", "PYB_PIN_PULLNONE")

        if mode == "PYB_PIN_IN": mode = PYB_PIN_IN
        elif mode == "PYB_PIN_OUT_PP": mode = PYB_PIN_OUT_PP
        elif mode == "PYB_PIN_OUT_OD": mode = PYB_PIN_OUT_OD
        else:
            self.logger.error("mode {} not supported".format(mode))
            self.log_bullet("mode {}: Failed".format(mode))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        if pull == "PYB_PIN_PULLNONE": pull = PYB_PIN_PULLNONE
        elif pull == "PYB_PIN_PULLDN": pull = PYB_PIN_PULLDN
        elif pull == "PYB_PIN_PULLUP": pull = PYB_PIN_PULLUP
        else:
            self.logger.error("pull {} not supported".format(pull))
            self.log_bullet("pull {}: Failed".format(pull))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        success, result = self.pyb.init_gpio(pin, pin, mode, pull)
        if not success:
            self.logger.error(result)
            self.log_bullet("init_gpio {}: Failed".format(pin))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.item_end()  # always last line of test

    def PYBRD0050_get_gpio(self):
        """ Init GPIO

        {"id": "PYBRD0050_get_gpio",  "enable": true,  "pin": "X12", "test": true, "unit": "UNIT_BOOL"},

        :return:
        """
        ctx = self.item_start()  # always first line of test
        pin = ctx.item.get("pin", None)
        test = ctx.item.get("test", True)
        unit = getattr(ResultAPI, ctx.item.get("unit", ResultAPI.UNIT_NONE), ResultAPI.UNIT_NONE)

        success, result = self.pyb.get_gpio(pin)
        self.logger.info(result)
        if not success:
            self.logger.error(result)
            self.log_bullet("get_gpio {}: Failed".format(pin))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        value = result["value"]["value"]
        if value: value = True
        else: value = False

        # measurement tests boleans for True, invert if necessary
        if not test: value = not value

        print(type(value))
        success, _result, _bullet = ctx.record.measurement("{}".format(pin), value, unit, None, None)
        self.log_bullet(_bullet)

        self.item_end(_result)  # always last line of test

    # PyBoard tests
    # --------------------------------------------------------------------------------
    # IBA01 tests

    def IBA010010_supply(self):
        """ Set Supply
        {"id": "PYBRD0030_supply",        "enable": true,  "name": "V1", "voltage_mv": 2000, "en": true, },
        name: <"V1"|"V2"|"VBAT">
        en: <true|false>
        """
        ctx = self.item_start()  # always first line of test
        name = ctx.item.get("name", None)
        voltage_mv = ctx.item.get("voltage_mv", None)
        en = ctx.item.get("en", True)

        success, result = self.pyb.supply_enable(name, enable=en, voltage_mv=voltage_mv, cal=True)

        if not success: _result = ResultAPI.RECORD_RESULT_INTERNAL_ERROR
        else: _result = ResultAPI.RECORD_RESULT_PASS

        self.item_end(_result)  # always last line of test

    def IBA010020_relay_v12(self):
        """ Set Supply
        {"id": "PYBRD0040_relay_v12",     "enable": true,  "connect": true },
        connect: <true|false>
        """
        ctx = self.item_start()  # always first line of test
        connect = ctx.item.get("connect", True)

        success, result = self.pyb.relay_v12(connect=connect)

        if not success: _result = ResultAPI.RECORD_RESULT_INTERNAL_ERROR
        else: _result = ResultAPI.RECORD_RESULT_PASS

        self.item_end(_result)  # always last line of test

    def IBA010030_relay_vsys(self):
        """ Set Supply
        {"id": "PYBRD0040_relay_vsys",     "enable": true,  "connect": true },
        connect: <true|false>
        """
        ctx = self.item_start()  # always first line of test
        connect = ctx.item.get("connect", True)

        success, result = self.pyb.relay_vsys(connect=connect)

        if not success: _result = ResultAPI.RECORD_RESULT_INTERNAL_ERROR
        else: _result = ResultAPI.RECORD_RESULT_PASS

        self.item_end(_result)  # always last line of test

    def IBA010040_relay_vbat(self):
        """ Set Supply
        {"id": "PYBRD0040_relay_vbat",     "enable": true,  "connect": true },
        connect: <true|false>
        """
        ctx = self.item_start()  # always first line of test
        connect = ctx.item.get("connect", True)

        success, result = self.pyb.relay_vbat(connect=connect)

        if not success: _result = ResultAPI.RECORD_RESULT_INTERNAL_ERROR
        else: _result = ResultAPI.RECORD_RESULT_PASS

        self.item_end(_result)  # always last line of test
