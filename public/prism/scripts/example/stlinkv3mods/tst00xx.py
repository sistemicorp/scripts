#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2025
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI

from public.prism.drivers.stlinkv3mods.STLINK import DRIVER_TYPE


# file and class name must match
class tst00xx(TestItem):

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("tst00xx.{}".format(self.chan))

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
        self.stlink = drivers[0]["obj"]["hwdrv"]  # instance

        # record the (unique) ID of stlink for tracking purposes
        success, _result, _bullet = ctx.record.measurement("stlink_sn",
                                                           self.stlink.serial_num,
                                                           ResultAPI.UNIT_STRING,
                                                           None,
                                                           None)

        self.log_bullet(_bullet)

        self.item_end()  # always last line of test

    def TST0xxTEARDOWN(self):
        """  Always called at the end of testing
        - process any cleanup, closing, etc

            {"id": "TST0xxTEARDOWN",        "enable": true },
        """
        ctx = self.item_start()  # always first line of test
        self.item_end()  # always last line of test
