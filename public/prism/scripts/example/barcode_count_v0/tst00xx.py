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

from public.prism.drivers.scanners.Scanners import DRIVER_TYPE as DRIVER_TYPE_SCANNER


# file and class name must match
class tst00xx(TestItem):

    # The item timeout ends the textbox wait, so this only has to be longer than any item timeout
    TEXTBOX_TIMEOUT_SEC = 24 * 60 * 60

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("tst00xx.{}".format(self.chan))

    def _scanner(self):
        """ The scanner driver for this channel, or None """
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE_SCANNER)
        if not drivers: return None
        return drivers[0]["obj"]["hwdrv"]

    def TST0xxTEARDOWN(self):
        """  Always called at the end of testing
        - process any cleanup, closing, etc

            {"id": "TST0xxTEARDOWN",        "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.item_end()  # always last line of test

    def TST000_Scan(self):
        """ Scan barcode
        - args.regex is the barcode format, P###-S#####, its groups "product" and "sn"
          pick the fields, product goes to info product, sn is the serial number key
        - if nothing is scanned before the item timeout, Prism records TIMEOUT,
          and the scanner stops restarting the script, until the next good scan

        {"id": "TST000_Scan", "enable": true, "timeout": 300,
                              "args": {"regex": "^(?P<product>P\\d{3})-S(?P<sn>\\d{5})$"} },

        """
        ctx = self.item_start()   # always first line of test
        scanner = self._scanner()

        self.log_bullet("Scan barcode")
        user_text = self.input_textbox("Scan:", "barcode", timeout=self.TEXTBOX_TIMEOUT_SEC)

        if not user_text["success"]:
            # timed out or aborted, stop restarting the script, Prism records the TIMEOUT
            if scanner: scanner.stop_player()
            self.log_bullet("No scan: {}".format(user_text.get("err")))
            self.log_bullet("Press channel Start to resume")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return

        barcode = user_text["textbox"].strip()
        match = re.match(ctx.item.args.regex, barcode)
        if not match:
            _, _result, _bullet = ctx.record.measurement("barcode", barcode, ResultAPI.UNIT_STRING,
                                                         force_fail=True)
            self.log_bullet("Bad format: {}".format(barcode))
            self.item_end(_result)
            return

        ctx.record.record_info_set({"product": match.group("product")})
        ctx.record.add_key("sn", match.group("sn"), slot=0)

        # Note: ResultAPI.UNIT_STRING is used to format the measurement correctly in JSON
        _, _result, _bullet = ctx.record.measurement("barcode", barcode, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        # a good scan (re)starts the automatic restarts, after a timeout and channel Start
        if scanner: scanner.start_player()

        self.item_end(_result)  # always last line of test
