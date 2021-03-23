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

        self.teensy = driver["obj"]["hwdrv"]

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

    def T020_init_gpio(self):
        """ In this test a GPIO is initialized

        {"id": "T020_init_gpio",            "enable": true, "pin_number": 5, "mode": "OUTPUT"},

        where,
         pin_number: <0-41>
         mode: <INPUT-INPUT_PULLUP-OUTPUT>
        """
        ctx = self.item_start() #always first line of test

        pin_number = ctx.item.get("pin_number", None)

        if pin_number < 0 or pin_number>41 or pin_number is None:
            self.logger.error(pin_number)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        mode_from_item = ctx.item.get("mode", "GPIO_MODE_INPUT")
        mode = getattr(self.teensy, mode_from_item, None)

        if mode is None:  # it is None
            self.logger.error(mode_from_item)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("Initializing GPIO {} as {}".format(pin_number, mode))

        answer = self.teensy.init_gpio(pin_number, mode)
        success = answer["success"]
        result = answer["result"]["mode"]

        if not success:
            self.logger.error(answer["result"]["error"])
            self.log_bullet("UNKNOWN TEENSY ERROR")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("GPIO {} is initialized as {} ".format(pin_number, result))

        self.item_end()  # always last line of test

    def T030_read_gpio(self):
        """ In this test a GPIO is read

        {"id": "T030_init_gpio",            "enable": true, "pin_number": 5},

        where,
         pin_number: <0-41>
        """
        ctx = self.item_start() #always first line of test

        pin_number = ctx.item.get("pin_number", None)

        if pin_number < 0 or pin_number > 41 or pin_number is None:
            self.logger.error(pin_number)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("Reading GPIO {} ".format(pin_number))

        answer = self.teensy.read_gpio(pin_number)
        success = answer["success"]
        result = answer["result"]["state"]

        if not success:
            self.logger.error(answer["result"]["error"])
            self.log_bullet("UNKNOWN TEENSY ERROR")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("GPIO {} is {} ".format(pin_number, result))

        self.item_end()  # always last line of test

    def T040_write_gpio(self):
        """ In this test a GPIO is read

        {"id": "T040_write_gpio",            "enable": true, "pin_number": 5, "state": 1},

        where,
         pin_number: <0-41>
         state: <1/0> or <trule/false>
        """
        ctx = self.item_start() #always first line of test

        pin_number = ctx.item.get("pin_number", None)

        if pin_number < 0 or pin_number > 41 or pin_number is None:
            self.logger.error(pin_number)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        state = ctx.item.get("state", None)

        if state not in [0, 1] or state is None:
            self.logger.error(state)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("Writing GPIO {} as {}".format(pin_number, state))

        answer = self.teensy.write_gpio(pin_number, state)
        success = answer["success"]
        result = answer["result"]["state"]

        if not success:
            self.logger.error(answer["result"]["error"])
            self.log_bullet("UNKNOWN TEENSY ERROR")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("GPIO {} is written as {} ".format(pin_number, result))

        self.item_end()  # always last line of test

    def T050_read_adc(self):
        """ In this test a GPIO is read

        {"id": "T050_read_adc",            "enable": true, "pin_number": 5, "sample_num": 4, "sample_rate": 12},

        where,
         pin_number: <0-41>
         sample_num: number of samples to average
         sample_rate: milliseconds between each sample
        """
        ctx = self.item_start() #always first line of test

        pin_number = ctx.item.get("pin_number", None)

        if pin_number < 0 or pin_number > 41 or pin_number is None:
            self.logger.error(pin_number)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        sample_num = ctx.item.get("sample_num", None)

        if sample_num is None:
            self.logger.error(sample_num)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        sample_rate = ctx.item.get("sample_rate", None)

        if sample_rate is None:
            self.logger.error(sample_rate)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("Reading Analog Pin {}, {} times with an interval of {} ms".format(pin_number, sample_num, sample_rate))

        answer = self.teensy.read_adc(pin_number, sample_num, sample_rate)
        success = answer["success"]
        result = answer["result"]["reading"]

        if not success:
            self.logger.error(answer["result"]["error"])
            self.log_bullet("UNKNOWN TEENSY ERROR")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
            return

        self.log_bullet("Pin {}'s ADC reading is {}".format(pin_number, result))

        self.item_end()  # always last line of test