#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
import re
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI

#from public.prism.drivers.fake.Fake import DRIVER_TYPE


# file and class name must match
class tst00xx(TestItem):

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("tst00xx.{}".format(self.chan))

    def TST0xxTEARDOWN(self):
        """  Always called at the end of testing
        - process any cleanup, closing, etc

            {"id": "TST0xxTEARDOWN",        "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.item_end()  # always last line of test

    def TST000_scan(self):
        """ Scan barcode
        - a regex is supplied to confirm barcode format

        {"id": "TST000_scan,            "enable": true, "regex": "^P\d{3}-S\d{5}$", "timeout": 10 },

        """
        ctx = self.item_start()   # always first line of test

        self.log_bullet("Scan barcode")

        user_text = self.input_textbox("Scan:", "change")
        if user_text["success"]:
            self.log_bullet(f"SCAN: {user_text['textbox']}")

            # qualify the text here
            if re.match(ctx.item.regex, user_text["textbox"]):
                # Note: ResultAPI.UNIT_STRING is used to format the measurement correctly in JSON
                _, _result, _bullet = ctx.record.measurement("input", user_text["textbox"], ResultAPI.UNIT_STRING)

                # Here, code could reach out to a dB and do some other kind of work

            else:
                _result = ResultAPI.RECORD_RESULT_FAIL
                _, _result, _bullet = ctx.record.measurement("input",
                                                             user_text["textbox"],
                                                             ResultAPI.UNIT_STRING,
                                                             force_fail=True)
            self.log_bullet(_bullet)

        else:
            # operator probably times out...
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet(user_text.get("err", "UNKNOWN ERROR"))

        self.item_end(_result)  # always last line of test
