#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022
Martin Guthrie

"""
import threading
import subprocess

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


DRIVER_TYPE = "NRFJPROG"


class NRFProg:
    """ NRF Prog Tool driver
    - executes the subprocess commands on the correct Segger
    """

    NRF_TARGET = "nrf52"

    def __init__(self, serial, loggerIn=None):
        self.lock = threading.Lock()

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.serial = serial

        self.my_version = self._get_version()

    def init(self):
        """ init
        - nothing to do
        :return: <True/False>
        """
        return True

    def close(self):
        """  Close connection
        - nothing to do
        :return:
        """
        return True

    # ----------------------------------------------------------------------------------------------
    # Helper Functions

    # Helper Functions
    # ----------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------
    # API (wrapper functions)
    # these are the important functions
    #
    # all functions return dict: { "success": <True/False>, "result": { key: value, ... }}

    def program(self, file, sector_erase=True, verify=True, reset=True):
        cmd = ['./public/prism/drivers/nrfprog/nrfjprog']

        cmd.append("--snr")
        cmd.append(self.serial)

        cmd.append("-f")
        cmd.append(self.NRF_TARGET)

        # TODO: validate file exists
        cmd.append("--program")
        cmd.append(file)

        if sector_erase:
            cmd.append("--sectorerase")

        if verify:
            cmd.append("--verify")

        if reset:
            cmd.append("--reset")

        result = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.logger.info(result)
        return result

    #
    # API (wrapper functions)
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    #

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------


