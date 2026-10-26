#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2020-2026
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
from public.prism.drivers.brother_ql.hwdrv_brother_ql import DRIVER_TYPE as BROTHER_DRIVER

# file and class name must match


class brthr00xx(TestItem):
    """ Brother Label Printer Example

    If the printer is serving multiple channels (driver arg {"shared": true}), then
    somehow need to know which station (channel) gets the printed label, the channel
    number is printed on the label.

    There could be more than one printer, one printer per test station (channel),
    by leaving out "shared".  get_drivers(self.chan, ...) returns this channel's
    printer, or the shared printer, so this code works for both.

    """

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("{}.{}".format(__name__, self.chan))
        self.printer = None

    def BRTHR0xxSETUP(self):
        """ Get the Printer handle from the shared state

        """
        ctx = self.item_start()  # always first line of test
        printer_info = self.shared_state.get_drivers(self.chan, type=BROTHER_DRIVER)
        if not printer_info:
            self.logger.error(f"driver {BROTHER_DRIVER} not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.printer = printer_info[0]['obj']['hwdrv']
        self.item_end()  # always last line of test

    def BRTHR0xxTRDN(self):
        ctx = self.item_start()  # always first line of test
        # there is nothing to do...
        self.item_end()  # always last line of test

    def BRTHR001_PrintRUID(self):
        """ Print the test record RUID on the label
        """
        ctx = self.item_start()   # always first line of test

        ruid = ctx.record.get_ruid()
        success = self.printer.print_ruid_barcode(ruid, self.chan)
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test
