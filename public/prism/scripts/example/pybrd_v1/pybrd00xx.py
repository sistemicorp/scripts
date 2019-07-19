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
#import ampy.files as files
import ampy.pyboard as pyboard
from public.prism.drivers.micropythonbrd.upybrd import pyboard2

# file and class name must match
class pybrd00xx(TestItem):

    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("SC.{}.{}".format(__name__, self.chan))

        self.pyb = None
        self.pyb_port = None

    def PYBRD0xxSETUP(self):
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type="MicroPyBrd")
        if len(drivers) > 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        self.logger.info("Found pybrd: {}".format(driver))
        self.pyb_port = driver["obj"]["port"]
        id = driver["obj"]["id"]

        if self.pyb_port is None:
            self.logger.error("Could not find pyboard driver")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return

        # save the id of the pyboard for the record
        _, _, _bullet = ctx.record.measurement("pyboard_id", id, ResultAPI.UNIT_INT)
        self.log_bullet(_bullet)

        self.pyb = pyboard2(self.pyb_port)

        self.item_end()  # always last line of test

    def PYBRD0xxTRDN(self):
        ctx = self.item_start()  # always first line of test
        self.pyb.close()
        self.item_end()  # always last line of test

    def PYBRD0010_LedToggle(self):
        """ In this test the user confirms if the LED under test blinked
        (this is also an example of one test item being run multiple times
        with different arguments)
        """
        ctx = self.item_start()  # always first line of test

        # 1=red, 2=green, 3=yellow, 4=blue
        LED_COLORS = ["Red", "Green", "Yellow", "Blue"]

        ontime_ms = ctx.item.get("ontime_ms", 300)
        lednum = ctx.item.get("lednum", 1)

        self.log_bullet("Watch which color Led blinks...")

        cmds = [ "import time, pyb",
                 "def led_cycle():",
                 " try:",
                 "  while True:",
                 "   pyb.LED({}).on()".format(lednum),
                 "   time.sleep_ms({})".format(ontime_ms),
                 "   pyb.LED({}).off()".format(lednum),
                 "   time.sleep_ms({})".format(ontime_ms),
                 " finally:",
                 "  pyb.LED({}).off()".format(lednum),
                 "",
                 "",
                 "",
                 "led_cycle()",
                 "",
                 ]

        # blocking is False, so we can move on and ask user what is blinking
        success, result = self.pyb.exec_cmd(cmds, blocking=False)
        if not success:
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

        # this resets the pyboard, so blinking will stop
        self.pyb.exit_raw_repl()

        self.item_end(_result)  # always last line of test

    def PYBRD0020_adc_read(self):
        """ Read ADC channel.

        {"id": "PYBRD0020_adc_read",      "enable": true,  "chan": "temp", "samples": 2, "delay_s": 0, "name": "MyKnob",
                                          "min": 18, "max": 26, "gain": 1, "unit": "UNIT_CELCIUS" },

        background: https://github.com/micropython/micropython/pull/3656
        http://docs.micropython.org/en/v1.9.4/pyboard/library/pyb.ADC.html#pyb-adc
        https://forum.micropython.org/viewtopic.php?f=6&t=4540&hilit=%27module%27+object+has+no+attribute+%27ADC%27&start=10
        """
        ctx = self.item_start()  # always first line of test

        chan = ctx.item.get("chan", None)
        samples = ctx.item.get("samples", 1)
        unit = getattr(ResultAPI, ctx.item.get("unit", ResultAPI.UNIT_NONE), ResultAPI.UNIT_NONE)
        min = ctx.item.get("min", None)
        max = ctx.item.get("max", None)
        delay_s = ctx.item.get("delay_s", 0)
        name = ctx.item.get("name", chan)  # if no name supplied use channel
        scale = ctx.item.get("scale", 1.0)

        if chan not in [0, 1, 2, 3, "temp", "vbat", "vref", "vcc"]:
            self.log_bullet("Error: Invalid ADC channel: {}".format(chan))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        cmds = [
            "import pyb",
        ]
        if chan in [0, 1, 2, 3]:
            pin_map = {0: "X19", 1: "X20", 2: "X21", 3: "X22"}
            cmds.append("adc = pyb.ADC(pyb.Pin('{}'))".format(pin_map[chan]))
            cmds.append("val = adc.read()")
        elif chan == "temp":
            cmds.append("adc = pyb.ADCAll(12, 0x70000)")
            cmds.append("val = adc.read_core_temp()")
        elif chan == "vbat":
            cmds.append("adc = pyb.ADCAll(12, 0x70000)")
            cmds.append("val = adc.read_core_vbat()")
        elif chan == "vref":
            cmds.append("adc = pyb.ADCAll(12, 0x70000)")
            cmds.append("val = adc.read_core_vref()")
        elif chan == "vcc":
            cmds.append("adc = pyb.ADCAll(12, 0x70000)")
            cmds.append("val = adc.read_vref()")

        cmds.append("print(val)")

        results = []
        success = True
        for i in range(samples):
            success, result = self.pyb.exec_cmd(cmds)
            self.logger.info("{} {} {}".format(i, success, result))
            results.append(float(result))
            time.sleep(delay_s)
            if not success: break

        if not success:
            self.log_bullet("ADC chan {}: Failed".format(chan))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        self.log_bullet("ADC chan {}: {}".format(chan, result))

        if samples != len(results):
            self.log_bullet("Warning: samples {} != len(results {}".format(samples, len(results)))
            # TODO: if there was an error taking samples, how to proceed?

        sum = 0
        for r in results: sum += r
        result = float(sum / len(results))
        result = float(result * scale)

        _, _result, _bullet = ctx.record.measurement("{}".format(name), result, unit, min, max)
        self.log_bullet(_bullet)

        self.item_end(_result)  # always last line of test

