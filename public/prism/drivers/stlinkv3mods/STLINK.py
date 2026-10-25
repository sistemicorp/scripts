#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2025
Martin Guthrie

"""
import os
import re
import logging
import threading
import subprocess

DRIVER_TYPE = "STLINKV3MODS"

# STM32CubeProgrammer is installed per station, see README.md
STLINK_CLI_PATH = './public/tools/STM32CubeProgrammer/bin/STM32_Programmer_CLI'


def cli_version():
    """ check STM32CubeProgrammer CLI is installed and runs

    :return: <True/False>, <version string or error message>
    """
    try:
        result = subprocess.run([STLINK_CLI_PATH, "--version"], capture_output=True,
                                text=True, check=False, timeout=30)
    except FileNotFoundError:
        return False, f"{STLINK_CLI_PATH} not found, install STM32CubeProgrammer, see drivers/stlinkv3mods/README.md"
    except Exception as e:
        return False, f"{STLINK_CLI_PATH} failed: {e}"

    if result.returncode != 0:
        return False, f"{STLINK_CLI_PATH} rc {result.returncode}: {result.stderr.strip()}"

    match = re.search(r"STM32CubeProgrammer version: (\S+)", result.stdout)
    if not match:
        return False, f"{STLINK_CLI_PATH} version not found in output"

    return True, match.group(1)


class STLINKprog:
    """ STLink V3MODS Prog Tool driver
    - executes the subprocess commands
    """
    STLINK_CLI_PATH = STLINK_CLI_PATH

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
        cmd = [self.STLINK_CLI_PATH, f"sn={self.serial_num}", "--version"]
        msg = " ".join(cmd)
        self.logger.info(msg)

        my_env = os.environ.copy()
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=my_env)
        return result

    def cli_cmd(self, cmd: list):
        """ execute cli command built from client
        - cmd should be list of strings
        """
        _cmd = [self.STLINK_CLI_PATH, f"sn={self.serial_num}"]
        _cmd.extend(cmd)

        msg = " ".join(_cmd)
        self.logger.info(msg)

        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = '.'
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


