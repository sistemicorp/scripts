#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022-2023
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
import os

from public.prism.drivers.nrfprog.NRFProg import NRFProg, DRIVER_TYPE

NRF52833DK_ASSETS_PATH = "./public/prism/scripts/example/nRF52833-DK/assets"


# file and class name must match
class prog_P00xx(TestItem):
    """ Python Methods for nRF52833-DK programming

    """
    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("nrfdk.{}".format(self.chan))
        self._nrfjprog = None

    def P0xxSETUP(self):
        """

        {"id": "P0xxSETUP",          "enable": true, "target": "nrf52"},

        :return:
        """
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
        self._nrfjprog = driver["obj"]["hwdrv"]

        msg = f"nrfjprog: {id}"
        self.log_bullet(msg)

        self._nrfjprog.set_target(ctx.item.target)
        self.log_bullet(ctx.item.target)

        self.item_end()  # always last line of test

    def P0xxTRDN(self):
        """ Teardown
        - always the last test called
        :return:
        """
        ctx = self.item_start()  # always first line of test

        self.item_end()  # always last line of test

    def P100_Program(self):
        """ Program
        - the file argument assume path TEENSY4_ASSETS_PATH

        {"id": "P100_Program",        "enable": true, "file": "teensy4_server.ino.hex" },

        """
        ctx = self.item_start()  # always first line of test
        file_path = os.path.join(NRF52833DK_ASSETS_PATH, ctx.item.file)

        if not os.path.isfile(file_path):
            self.log_bullet(f"file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"{ctx.item.file}")

        result = self._nrfjprog.program(file_path)
        rc = result.returncode
        if rc:
            self.log_bullet(f"program error {rc}")
            self.logger.error(result.stderr)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

