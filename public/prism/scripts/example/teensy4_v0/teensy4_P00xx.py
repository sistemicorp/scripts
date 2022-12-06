#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
import subprocess
import os
import time

from public.prism.drivers.iba01.list_serial import serial_ports
from public.prism.drivers.teensy4.Teensy4 import Teensy4

DRIVER_TYPE = "TEENSY4_PROG"
DRIVER_TYPE_UPDATE = "TEENSY4"  # matches Teensy4 driver type

TEENSY4_ASSETS_PATH = "./public/prism/scripts/example/teensy4_v0/assets"


# file and class name must match
class teensy4_P00xx(TestItem):
    """ Python Methods for Teensy 4

    This test script programs Teensy devices with driver code
    developed in public/prism/drivers/teensy4
    That driver contains the API for interfacing between Prism test scripts
    and the Teensy based interface board hardware.

    This is an example of how to program your Teensy4 interface board.

    """
    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("teensy400xx.{}".format(self.chan))
        self.teensy = None
        self._teensy_port = None

    def P0xxSETUP(self):
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE)
        if len(drivers) > 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        msg = "teensy4: {} {}, chan {}".format(driver, id, self.chan)
        self.log_bullet(msg)
        self.logger.info(msg)

        self.item_end()  # always last line of test

    def P0xxTRDN(self):
        ctx = self.item_start()  # always first line of test

        self.item_end()  # always last line of test

    def P100_Check(self):
        """ Check Teensy Connected

        {"id": "P100_Check",          "enable": true },

        use lsusb to see if there is a Teensy attached, expected output,
            $ lsusb
            Bus 001 Device 053: ID 16c0:0483 Van Ooijen Technische Informatica Teensyduino Serial
            Bus 001 Device 051: ID 16c0:0486 Van Ooijen Technische Informatica Teensyduino RawHID

        Note,
            - When 'Serial', likely this is a Teensy that was previously programmed.
            - when 'RawHID', likely this is a fresh Teensy - never programmed, or has been reset.

        """
        ctx = self.item_start()  # always first line of test
        result = subprocess.run(['lsusb'], stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.logger.info(result)

        # find out how many teensys are connected, there should only be ONE!
        _cnt = result.count('Teensyduino')
        self.log_bullet(f"Teensys on USB: {_cnt}")
        if _cnt != 1:
            self.log_bullet(f"Unexpected count")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def P200_Program(self):
        """ Program Teensy
        - the file argument assume path TEENSY4_ASSETS_PATH

        {"id": "P200_Program",        "enable": true, "file": "teensy4_server.ino.hex" },

        """
        ctx = self.item_start()  # always first line of test
        file_path = os.path.join(TEENSY4_ASSETS_PATH, ctx.item.file)

        if not os.path.isfile(file_path):
            self.log_bullet(f"file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"{ctx.item.file}")
        self.log_bullet(f"Press Teensy Button")

        result = subprocess.run(['./public/prism/drivers/teensy4/server/teensy_loader_cli', '--mcu=TEENSY41', '-w', '-v', file_path],
                                stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.logger.info(result)

        # expected output looks like,
        #   Teensy Loader, Command Line, Version 2.2
        #   Read "./public/prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
        #   Waiting for Teensy device...
        #    (hint: press the reset button)
        #   Found HalfKay Bootloader
        #   Read "./public/prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
        #   Programming..................................................................
        #   Booting

        # check for some key words to confirm success
        if not result.count('Programming'):
            self.log_bullet(f"Unexpected Programming")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        if not result.count('Booting'):
            self.log_bullet(f"Unexpected Booting")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def P300_Verify(self):
        """ Verify Teensy
        - by verifying that we can install instance of driver

        {"id": "P300_Verify",         "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.log_bullet(f"{ctx.item.delay}s wait for boot")
        time.sleep(ctx.item.delay)
        self.log_bullet("done wait")

        port_candidates = serial_ports()
        self.logger.info("Serial Ports to look for Teensy {}".format(port_candidates))

        found_teensy = False
        for port in port_candidates:
            if "ttyACM" not in port:  # this does not work on Windows as only see "COM#"
                self.logger.info("skipping port {}...".format(port))
                continue

            self.logger.info("Trying teensy at {}...".format(port))

            # create an instance of Teensy()
            _teensy = Teensy4(port, loggerIn=logging.getLogger("teensy.try"))
            success = _teensy.init()
            if not success:
                self.log_bullet(f"Failed init")
                self.logger.error("failed on {}...".format(port))

            else:
                self.log_bullet(f"Found teensy")
                found_teensy = True
                break

        if not found_teensy:
            self.log_bullet(f"Teensy not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        result = _teensy.unique_id()
        success = result['success']
        if not success:
            self.logger.error("failed on {}...".format('unique_id'))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        unique_id = result['result']['unique_id']
        _, _, _bullet = ctx.record.measurement("teensy4_id", unique_id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        result = _teensy.version()
        success = result['success']
        if not success:
            self.logger.error("failed on {}...".format('version'))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        version = result['result']['version']
        _, _, _bullet = ctx.record.measurement("teensy4_version", version, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        _teensy.close()
        self.item_end()  # always last line of test

    def P500_SETUP(self):
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE_UPDATE)
        if len(drivers) > 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        self._teensy_port = driver["obj"]["port"]  # cache for after update reconnect

        id = driver["obj"]["unique_id"]  # save the id of the teensy4 for the record
        _, _, _bullet = ctx.record.measurement("teensy4_id", id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)
        self.logger.info("Found teensy4: {} {}, chan {}".format(driver, id, self.chan))

        self.teensy = driver["obj"]["hwdrv"]

        answer = self.teensy.reset()
        success = answer["success"]

        if not success:
            self.logger.error("failed to reset teensy")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def P600_Update(self):
        ctx = self.item_start()  # always first line of test

        file_path = os.path.join(TEENSY4_ASSETS_PATH, ctx.item.file)

        if not os.path.isfile(file_path):
            self.log_bullet(f"file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"{ctx.item.file}")

        self.teensy.close()

        time.sleep(0.1)
        result = subprocess.run(['./public/prism/drivers/teensy4/server/teensy_loader_cli',
                                 '--mcu=TEENSY41',
                                 '-w',
                                 '-s',
                                 '-v',
                                 file_path],
                                stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.logger.info(result)

        # expected output looks like,
        #   Teensy Loader, Command Line, Version 2.2
        #   Read "./public/prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
        #   Waiting for Teensy device...
        #    (hint: press the reset button)
        #   Found HalfKay Bootloader
        #   Read "./public/prism/scripts/example/teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
        #   Programming..................................................................
        #   Booting

        # check for some key words to confirm success
        if not result.count('Programming'):
            self.log_bullet(f"Unexpected Programming")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        if not result.count('Booting'):
            self.log_bullet(f"Unexpected Booting")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def P700_Verify(self):
        """ Verify Teensy
        - by verifying that we can re-install instance of driver after the update
        - uses the cached serial port from P500_SETUP

        {"id": "P300_Verify",         "enable": true },

        """
        ctx = self.item_start()  # always first line of test
        self.log_bullet(f"{ctx.item.delay}s wait for boot")
        time.sleep(ctx.item.delay)
        self.log_bullet("done wait")

        self.logger.info("Trying teensy at {}...".format(self._teensy_port))

        # (re)create an instance of Teensy()
        self.teensy = Teensy4(self._teensy_port, loggerIn=logging.getLogger("teensy.try"))
        success = self.teensy.init()
        if not success:
            self.log_bullet(f"Failed init")
            self.logger.error("failed on {}...".format(self._teensy_port))

        else:
            self.log_bullet(f"Found teensy")

        result = self.teensy.unique_id()
        success = result['success']
        if not success:
            self.logger.error("failed on {}...".format('unique_id'))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        unique_id = result['result']['unique_id']
        _, _, _bullet = ctx.record.measurement("teensy4_id", unique_id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        result = self.teensy.version()
        success = result['success']
        if not success:
            self.logger.error("failed on {}...".format('version'))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        version = result['result']['version']
        _, _, _bullet = ctx.record.measurement("teensy4_version", version, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        self.item_end()  # always last line of test

