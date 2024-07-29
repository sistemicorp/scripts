#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022
Martin Guthrie

"""
import logging
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

    def __init__(self, serial_num, target=NRF_TARGET):
        """ init

        :param serial_num: JLink serial number
        :param loggerIn:
        """
        self.lock = threading.Lock()
        self.logger = logging.getLogger()
        self.serial_num = serial_num
        self.target = target

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

    def set_target(self, target):
        self.logger.info(target)
        self.target = target

    def recover(self):
        """ recover target

        :return:
        """
        cmd = ['./public/prism/drivers/nrfprog/nrfjprog']

        cmd.append("--snr")
        cmd.append(self.serial_num)
        cmd.append("-f")
        cmd.append(self.target)
        cmd.append("--recover")

        msg = " ".join(cmd)
        self.logger.info(msg)

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.logger.info(result)
        return result

    def program(self, file, sector_erase=True, verify=True, reset=True):
        """ program target

        :param file:
        :param sector_erase:
        :param verify:
        :param reset:
        :return: subprocess.run object
        """
        cmd = ['./public/prism/drivers/nrfprog/nrfjprog']

        cmd.append("--snr")
        cmd.append(self.serial_num)

        cmd.append("-f")
        cmd.append(self.target)

        # TODO: validate file exists, or maybe the caller has done so

        cmd.append("--program")
        cmd.append(file)

        if sector_erase:
            cmd.append("--sectorerase")

        if verify:
            cmd.append("--verify")

        if reset:
            cmd.append("--reset")

        msg = " ".join(cmd)
        self.logger.info(msg)

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.logger.info(result.stdout.replace("\n\n", "\n"))
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


