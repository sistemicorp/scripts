#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2025

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
import subprocess
import os
import time
import pyudev

from public.prism.drivers.common.list_serial import serial_ports
from public.prism.drivers.A4401_BOND.A4401_BOND import A4401_BOND, DRIVER_TYPE, DRIVER_TYPE_PROG


BOND_ASSETS_PATH = "./public/prism/scripts/example/BOND_v0/assets"
BOND_TEENSY_CLI_LOADER_PATH = './public/prism/drivers/A4401_BOND/server/teensy_loader_cli'

# file and class name must match
class bond_P00xx(TestItem):
    """ Python Methods for BOND

    BOND uses the Teensy4 example as a starting point.

    Helpful:
    https://forum.pjrc.com/threads/66942-Program-Teensy-4-from-command-line-without-pushing-the-button?highlight=bootloader
    https://forum.pjrc.com/threads/71624-teensy_loader_cli-with-multiple-Teensys-connected?p=316838#post316838

    """
    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("teensy400xx.{}".format(self.chan))
        self.teensy = None
        self._teensy_port = None
        self._teensy_usb_path = None
        self._teensy_ports_cache = None

    def P000_SETUP(self):
        """ Setup for programming BOND

        """
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE_PROG)
        if not (len(drivers) == 1):
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        msg = "teensy4: {} {}, chan {}".format(driver, id, self.chan)
        self.logger.info(msg)
        self.log_bullet(f"teensy4 {driver['type']} ch {self.chan}")

        self.item_end()  # always last line of test

    def P100_Check(self):
        """ Check Teensy Connected

        {"id": "P100_Check",          "enable": true },

        use lsusb to see if there is a Teensy attached, example outputs,
            $ lsusb
            Bus 001 Device 053: ID 16c0:0483 Van Ooijen Technische Informatica Teensyduino Serial
            Bus 001 Device 051: ID 16c0:0486 Van Ooijen Technische Informatica Teensyduino RawHID
            Bus 005 Device 023: ID 16c0:0478 Van Ooijen Technische Informatica Teensy Halfkay Bootloader

        Note,
            - When 'Serial', likely this is a Teensy that was previously programmed.
            - when 'RawHID', likely this is a fresh Teensy - never programmed, or has been reset.

        """
        ctx = self.item_start()  # always first line of test
        result = subprocess.run(['lsusb'], stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.logger.info(result)

        # find out how many teensys are connected, there should only be ONE!
        _cnt = result.count('Van Ooijen Technische Informatica')
        self.log_bullet(f"Teensys on USB: {_cnt}")
        if _cnt != 1:
            self.log_bullet(f"Unexpected count")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def P200_Program(self):
        """ Program Teensy
        - the file argument assume path BOND_ASSETS_PATH
        - Used for programming a fresh teensy that has only bootloader running
        - Teensy red LED should be dim RED for this to work... sometimes hard to get
          Teensy into that state...
        - FIXME: this programming doesn't always work.  But maybe most of the time
                 the Teensy is programmed by the Arduino IDE.  So this is here as
                 a prototype...

        {"id": "P200_Program",        "enable": true, "file": "teensy4_server.ino.hex" },

        """
        ctx = self.item_start()  # always first line of test
        file_path = os.path.join(BOND_ASSETS_PATH, ctx.item.file)

        if not os.path.isfile(file_path):
            self.log_bullet(f"file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.logger.info(f"programming {ctx.item.file}")
        self.log_bullet(f"{ctx.item.file}")

        self.shared_lock(DRIVER_TYPE_PROG).acquire()

        result = subprocess.run([BOND_TEENSY_CLI_LOADER_PATH,
                                 '--mcu=TEENSY41',
                                 '-w',
                                 '-v',
                                 '-s',
                                 file_path],
                                stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.logger.info(result)

        self.shared_lock(DRIVER_TYPE_PROG).release()

        # expected output looks like,
        #  1747                  bond_P00xx.py: 119 -                  teensy400xx.0:        P200_Program() INFO  : Teensy Loader, Command Line, Version 2.2
        # Read "./public/prism/scripts/example/BOND_v0/assets/teensy4_server.ino.hex": 102400 bytes, 1.3% usage
        # Found HalfKay Bootloader
        # Programming.................................................................................................
        # Booting

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

        {"id": "P300_Verify",         "enable": true, "delay": 10 },

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
            _teensy = A4401_BOND(port, loggerIn=logging.getLogger("teensy.try"))
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
        """ Setup teensy for Update (means its already running our server code)
        - close the current connection to Teensy
        - cache the port, so we can open it later in P700_Verify

        {"id": "P500_SETUP",          "enable": true },

        :return:
        """
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=DRIVER_TYPE)
        if not (len(drivers) == 1):
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]  # this is a dict from hwdrv_teensy4

        id = driver["obj"]["unique_id"]  # save the id of the teensy4 for the record
        _, _, _bullet = ctx.record.measurement("teensy4_id", id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)
        self.logger.info("Found teensy4: {} {}, chan {}".format(driver, id, self.chan))

        self._teensy_usb_path = driver["obj"]["usb_path"]  # cache for after update reconnect
        #self._teensy_port = driver["obj"]["port"]  # cache for after update reconnect
        self.teensy = driver["obj"]["hwdrv"]

        result = self.teensy.reset()   # set Teensy to a known good state
        if not result["success"]:
            self.logger.error("failed to reset teensy")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def P600_Update(self):
        """ Update the teensy Firmware

        {"id": "P600_Update",         "enable": true, "file": "teensy4_server.ino.hex" },

        :return:
        """
        ctx = self.item_start()  # always first line of test

        file_path = os.path.join(BOND_ASSETS_PATH, ctx.item.file)
        if not os.path.isfile(file_path):
            self.log_bullet(f"file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"{ctx.item.file}")

        # block other instances from reboot/Teensy CLI loader
        self.shared_lock(DRIVER_TYPE).acquire()

        # close teensy connection, its going to get rebooted
        self.logger.info("reboot_to_bootloader")
        result = self.teensy.reboot_to_bootloader()
        if not result['success']:
            self.logger.error("failed on {}...".format('reboot_to_bootloader'))
            self.shared_lock(DRIVER_TYPE).release()
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.teensy.close()

        attempts = 2
        success = False
        while attempts:
            # NOTE: there is a bug somewhere, so we have to try this twice!
            #       see https://forum.pjrc.com/threads/69236-TeensyLoader-CLI-issues

            result = subprocess.run([BOND_TEENSY_CLI_LOADER_PATH,
                                     '--mcu=TEENSY41',
                                     '-w',
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

            # check for some keywords to confirm success
            if result.count('Programming') and result.count('Booting'):
                success = True
                break

            attempts -= 1
            time.sleep(0.1)

        if not success:
            self.log_bullet(f"teensy_loader_cli failed")
            self.shared_lock(DRIVER_TYPE).release()
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def _find_matching_ttyACM_from_usb_path(self, ref_path):
        """ Find longest matching USB path
        - the USB path might look different on different systems...
        - TODO: find out how to break the path down to the port mapping on the hub.
                it would be better to match port hubs.  Today, just looking for longest match
                which will include the port.
          FIXME: This code might be a bit old now, see other project to see if this has changed.

        Example USB Device path:
        'usb_path': '/devices/pci0000:00/0000:00:08.1/0000:03:00.3/usb1/1-2/1-2.1/1-2.1.4/1-2.1.4.1/1-2.1.4.1:1.0/tty/ttyACM3'

        :param ref_path: path to find the longest match
        :return: string port (example ttyACM0)
        """
        # find the matching tty port from the usb_path
        port = None
        match_len = 0
        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty'):
            _node = str(device.device_node)
            if "ttyACM" in _node:
                device_path = device.device_path
                self.logger.info(f"{_node}, {device_path}")
                # compare strings to find longest matching
                _idx = 0
                while _idx < len(self._teensy_usb_path):
                    if device_path[_idx] == self._teensy_usb_path[_idx]:
                        if _idx > match_len:
                            port = _node
                            match_len = _idx

                    _idx += 1

                self.logger.info(f"{port} {match_len}")

        return port

    def P700_Verify(self):
        """ Verify Teensy
        - by verifying that we can re-install instance of driver after the update
        - this is difficult because on USB re-enumeration teensy may be on a different
          serial port.  So use the usb_path to find the correct port.

        {"id": "P700_Verify",         "enable": true, "delay": 5 },

        """
        ctx = self.item_start()  # always first line of test

        # Teensy should be re-enumerating on USB, using a simple delay to let that happen
        self.log_bullet(f"{ctx.item.delay}s wait for boot")
        time.sleep(ctx.item.delay)
        self.log_bullet("done wait")

        port = self._find_matching_ttyACM_from_usb_path(self._teensy_usb_path)
        if port is None:
            self.log_bullet(f"Failed find port")
            self.shared_lock(DRIVER_TYPE).release()
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.logger.info("Trying teensy at {}...".format(port))

        # (re)create an instance of Teensy()
        self.teensy = A4401_BOND(port, loggerIn=logging.getLogger("teensy.try"))
        success = self.teensy.init()
        if not success:
            self.log_bullet(f"Failed init")
            self.logger.error("failed on {}...".format(self._teensy_port))
            self.shared_lock(DRIVER_TYPE).release()
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"Found teensy")
        self.shared_lock(DRIVER_TYPE).release()

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

        self.log_bullet("! ONLY RUN ONCE !")
        self.item_end()  # always last line of test

    def P800_USBTree(self):
        """ USB Tree
        - this is debug code to learn about pyudev.Context()

        {"id": "P800_USBTree",        "enable": true },

        Device('/sys/devices/pci0000:00/0000:00:11.0/0000:02:03.0/usb1')
        Device('/sys/devices/pci0000:00/0000:00:11.0/0000:02:03.0/usb1/1-0:1.0')
        Device('/sys/devices/pci0000:00/0000:00:11.0/0000:02:03.0/usb1/1-2')
        Device('/sys/devices/pci0000:00/0000:00:11.0/0000:02:03.0/usb1/1-2/1-2:1.0')
        Device('/sys/devices/pci0000:00/0000:00:11.0/0000:02:03.0/usb1/1-2/1-2:1.0/tty/ttyACM2')
        Device('/sys/devices/pci0000:00/0000:00:11.0/0000:02:03.0/usb1/1-2/1-2:1.1')
        """
        ctx = self.item_start()  # always first line of test

        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty'):
            _node = str(device.device_node)
            if "ttyACM" in _node:
                self.logger.info(f"{device.device_node} {device.device_type}")
                self.logger.info(dir(device))
                self.logger.info(device.sys_path)
                self.logger.info(device.device_path)
                self.logger.info(device.subsystem)
                self.logger.info(device.parent)
                self.logger.info(device.traverse)
                self.logger.info(dir(device.properties))
                self.logger.info(device.properties.items)
                _parent = device.parent

        self.logger.info("===============================================================================")

        self.item_end()  # always last line of test

