#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
import time


from public.prism.drivers.fake.Fake import DRIVER_TYPE
from public.prism.drivers.ble_listener.BLEListener import DRIVER_TYPE as BLE_DRIVER_TYPE


# file and class name must match
class tstBLExx(TestItem):

    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("tstBLExx.{}".format(self.chan))

        self.hw_fake = None
        self.hw_ble = None

    def TST0xxSETUP(self):
        """  Setup up for testing
        - main purpose is to get a local handle to the connected hardware
        - store the ID of the hardware for tracking purposes

            {"id": "TST0xxSETUP",           "enable": true },

        """
        ctx = self.item_start()  # always first line of test

        # get instance of the hardware created by HWDriver:discover_channels()
        # per the script, the fake hw driver is used (see script config:drivers section)
        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE)
        self.logger.info(drivers)  # review this output to see HW attributes
        self.hw_fake = drivers[0]["obj"]["hwdrv"]  # instance of ./drivers/fake/Fake.py:Fake

        drivers = self.shared_state.get_drivers(self.chan, type=BLE_DRIVER_TYPE)
        self.logger.info(drivers)  # review this output to see HW attributes
        self.hw_ble = drivers[0]["obj"]["hwdrv"]

        self.item_end()  # always last line of test

    def TST0xxTEARDOWN(self):
        """  Always called at the end of testing
        - process any cleanup, closing, etc

            {"id": "TST0xxTEARDOWN",        "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.item_end()  # always last line of test

    def TST000_ble(self):
        """ Measurement example, simplest example

        {"id": "TST000_ble",            "enable": true, "rssi": {"min": -90, "max": 0}},

        """
        ctx = self.item_start()   # always first line of test

        uid_to_find = "abbaff00-e56a-484c-b832-8b17cf6cbfe8"

        polling, found = 20, False
        while polling and not found:
            polling -= 1  # limit polling
            self.logger.debug(f"polling for {uid_to_find}, attempts left {polling}...")

            success, ad = self.hw_ble.is_uid_present(uid_to_find)
            if not success:
                self.logger.error("ble driver error")
                self.log_bullet("INTERNAL ERROR")
                self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)  # always last line of test
                return

            if ad is not None:
                found = True
                break

            time.sleep(1.0)

        if not found:
            self.logger.info("BLE device not found")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        self.logger.info(ad)
        success, _result, _bullet = ctx.record.measurement(None,
                                                           ad["rssi"],
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.rssi.min,
                                                           ctx.item.rssi.max)

        self.log_bullet(_bullet)
        self.item_end(_result)  # always last line of test

