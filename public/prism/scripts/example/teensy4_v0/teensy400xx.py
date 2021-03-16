#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI

from public.prism.drivers.teensy4.hwdrv_teensy4 import DRIVER_TYPE

# file and class name must match
class teensy400xx(TestItem):
    """ Python Methods for Teensy 4

    """
    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("teensy400xx.{}".format(self.chan))
        self.teensy = None

    def T0xxSETUP(self):
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE)
        if len(drivers) > 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        id = driver["obj"]["unique_id"]  # save the id of the teensy4 for the record
        _, _, _bullet = ctx.record.measurement("teensy4_id", id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)
        self.logger.info("Found teensy4: {} {}, chan {}".format(driver, id, self.chan))

        self.teensy = driver["obj"]["teensy4"]

        answer = self.teensy.reset()
        success = answer["success"]

        if not success:
            self.logger.error("failed to reset teensy")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def T0xxTRDN(self):
        ctx = self.item_start()  # always first line of test

        answer = self.teensy.reset()
        success = answer["success"]

        if not success:
            self.logger.error("failed to reset teensy")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def T010_led(self):
        """ In this test the user confirms if the LED under test is ON or OFF
        (this is also an example of one test item being run multiple times
        with different arguments)

        {"id": "T010_led",            "enable": true, "set": false},

        where,
           set: <True/False>
        """
        ctx = self.item_start()  # always first line of test

        set = ctx.item.get("set", False)
        self.log_bullet("Setting LED {}".format(set))

        answer = self.teensy.led(set)
        success = answer["success"]
        result = answer["result"]["state"]

        if not success:
            self.logger.error(result)
            self.log_bullet("UNKNOWN TEENSY ERROR")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        if set: buttons = ["ON", "Fail"]
        else: buttons = ["OFF", "Fail"]
        user_select = self.input_button(buttons)

        if user_select["success"]:
            b_idx = user_select["button"]
            self.log_bullet("{} was pressed!".format(buttons[b_idx]))
            _, _result, _bullet = ctx.record.measurement("button", b_idx, ResultAPI.UNIT_INT, min=0, max=0)
            self.log_bullet(_bullet)

        else:
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet(user_select.get("err", "UNKNOWN ERROR"))

        self.item_end(_result)  # always last line of test

