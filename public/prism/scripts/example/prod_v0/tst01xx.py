#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2023
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
from random import randint, random


# file name and class name must match
class tst01xx(TestItem):

    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("tst01xx.{}".format(self.chan))

    def TST500_SETUP(self):
        """  Setup up for testing
        - main purpose is to get a local handle to the connected hardware
        - store the ID of the hardware for tracking purposes

            {"id": "TST500_SETUP", "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

        self.item_end()  # always last line of test

    def TST990_TEARDOWN(self):
        """  Always called at the end of testing
        - process any cleanup, closing, etc

            {"id": "TST990_TEARDOWN",        "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.item_end()  # always last line of test

    def TST510_meas(self):
        """ Example test

        {"id": "TST510_meas", "enable": true,  "min": 0, "max": "%%TST510Max",
                      "fail": [ {"fid": "TST510-1", "msg": "Component R1"} ] },
        """
        ctx = self.item_start()   # always first line of test

        self.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

        # example of taking multiple measurements, and sending as a list of results
        # if any test fails, this test item fails
        # This test has a failure message in the script, depending on the failure mode,
        # "fail": [ {"fid": "TST510-1", "msg": "Component R1"} ] }
        FAIL_ID = 0

        measurement_results = []
        success, _result, _bullet = ctx.record.measurement("apples",
                                                           random(),
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.min,
                                                           ctx.item.max,
                                                           fail=ctx.item.fail[FAIL_ID])
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        success, _result, _bullet = ctx.record.measurement("bananas",
                                                           float(randint(0, 10)),
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.min,
                                                           ctx.item.max,
                                                           fail=ctx.item.fail[FAIL_ID])
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        self.item_end(item_result_state=measurement_results)  # always last line of test

    def TST520_skip(self):
        """ Example of a test that is skipped

        {"id": "TST520_skip", "enable": false },

        """
        ctx = self.item_start()   # always first line of test
        # this is a skipped test for testing, in some scripts

        self.log_bullet("Was I skipped?")

        self.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

        self.item_end()  # always last line of test
