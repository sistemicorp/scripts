#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022
Martin Guthrie

"""
import re
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

# nRF Command Line Tools are installed per station, see README.md
NRFJPROG_PATH = './public/tools/nrf-command-line-tools/bin/nrfjprog'


def cli_version():
    """ check nrfjprog is installed and can load the J-Link library

    :return: <True/False>, <version string or error message>
    """
    try:
        result = subprocess.run([NRFJPROG_PATH, "--version"], capture_output=True,
                                text=True, check=False, timeout=30)
    except FileNotFoundError:
        return False, f"{NRFJPROG_PATH} not found, install nRF Command Line Tools, see drivers/nrfprog/README.md"
    except Exception as e:
        return False, f"{NRFJPROG_PATH} failed: {e}"

    if result.returncode != 0:
        # nrfjprog explains the failure in its first "ERROR:" line
        lines = (result.stdout + result.stderr).splitlines()
        errors = [l for l in lines if l.startswith("ERROR:")] or lines[-1:]
        return False, f"{NRFJPROG_PATH} rc {result.returncode}: {' '.join(errors[:1])}"

    nrfjprog = re.search(r"nrfjprog version: (\S+)", result.stdout)
    jlink = re.search(r"JLinkARM.dll version: (\S+)", result.stdout)
    if not nrfjprog or not jlink:
        return False, f"{NRFJPROG_PATH} version not found in output"

    return True, f"nrfjprog {nrfjprog.group(1)}, JLinkARM {jlink.group(1)}"


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
        cmd = [NRFJPROG_PATH]

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
        cmd = [NRFJPROG_PATH]

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


