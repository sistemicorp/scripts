#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2025
Martin Guthrie

"""
import os
import logging
import threading
import subprocess

DRIVER_TYPE = "STLINKV3MODS"


class STLINKprog:
    """ STLink V3MODS Prog Tool driver
    - executes the subprocess commands
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

    def version(self):
        """ get driver version
        - this is used to test if the driver is working
        """
        cmd = [os.path.join('./public/prism/drivers/stlinkv3mods/bin', 'STM32_Programmer_CLI'), f"sn={self.serial_num}", "--version"]
        msg = " ".join(cmd)
        self.logger.info(msg)

        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = './public/prism/drivers/stlinkv3mods/bin'
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=my_env)
        return result

    def cli_cmd(self, cmd: list):
        """ execute cli command built from client
        - cmd should be list of strings
        """
        _cmd = [os.path.join('./public/prism/drivers/stlinkv3mods/bin', 'STM32_Programmer_CLI'), f"sn={self.serial_num}"]
        _cmd.extend(cmd)

        msg = " ".join(cmd)
        self.logger.info(msg)

        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = './public/prism/drivers/stlinkv3mods/bin'
        result = subprocess.run(_cmd, capture_output=True, text=True, check=False, env=my_env)
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


