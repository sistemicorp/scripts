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


DRIVER_TYPE = "STLINKV3MODS"


class STLINKprog:
    """ STLink V3MODS Prog Tool driver
    - executes the subprocess commands on the correct Segger
    """

    def __init__(self, serial_num):
        """ init

        :param serial_num: JLink serial number
        :param loggerIn:
        """
        self.lock = threading.Lock()
        self.logger = logging.getLogger()
        self.serial_num = serial_num

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
        """ program target

        :param file:
        :param sector_erase:
        :param verify:
        :param reset:
        :return: subprocess.run object
        """
        cmd = ['./public/prism/drivers/stlinkv3mods/st-flash']

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


