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
import pyudev

from public.prism.drivers.common.list_serial import serial_ports
from public.prism.drivers.A4401_BOND.A4401_BOND import A4401_BOND, DRIVER_TYPE, DRIVER_TYPE_PROG


BOND_ASSETS_PATH = "./public/prism/scripts/example/BOND_v0/assets"
BOND_TEENSY_CLI_LOADER_PATH = './public/prism/drivers/A4401_BOND/server/teensy_loader_cli'

# file and class name must match


class bond_P00xx(TestItem):
    """ Python Methods for BOND

    BOND uses the Teensy4 example as a starting point.

    Tests:
        PROG: program a new BOND (bond_progfresh_0.scr)
        UPD: update the BOND firmware (bond_update_0.scr)
        BOND: BOND self test examples (bond_selftest_0.scr), can be deleted
        Your product tests: your stage name, for example BLT100_voltage

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

    def PROG000_SETUP(self):
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

    def BOND010_led(self):
        """ Turn on/off LED

            {"id": "BOND010_led",             "enable": true, "set": true },
        """
        ctx = self.item_start()  # always first line of test

        self.expect(self.teensy.led(ctx.item.set))

        self.item_end()  # always last line of test

    def PROG010_check(self):
        """ Check Teensy Connected

        {"id": "PROG010_check",          "enable": true },

        use lsusb to see if there is a Teensy attached, example outputs,
            $ lsusb
            Bus 001 Device 053: ID 16c0:0483 Van Ooijen Technische Informatica Teensyduino Serial
            Bus 001 Device 051: ID 16c0:0486 Van Ooijen Technische Informatica Teensyduino RawHID
            Bus 005 Device 023: ID 16c0:0478 Van Ooijen ... Teensy Halfkay Bootloader

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
            self.log_bullet("Unexpected count")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def PROG020_program(self):
        """ Program Teensy
        - the file argument assume path BOND_ASSETS_PATH
        - Used for programming a fresh teensy that has only bootloader running
        - Teensy red LED should be dim RED for this to work... sometimes hard to get
          Teensy into that state...
        - FIXME: this programming doesn't always work.  But maybe most of the time
                 the Teensy is programmed by the Arduino IDE.  So this is here as
                 a prototype...

        {"id": "PROG020_program",        "enable": true, "file": "teensy4_server.ino.hex" },

        """
        ctx = self.item_start()  # always first line of test
        file_path = os.path.join(BOND_ASSETS_PATH, ctx.item.file)

        if not os.path.isfile(file_path):
            self.log_bullet("file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.logger.info(f"programming {ctx.item.file}")
        self.log_bullet(f"{ctx.item.file}")

        # one Teensy CLI loader at a time, released even if the item is stopped
        with self.shared_lock(DRIVER_TYPE_PROG):
            result = subprocess.run([BOND_TEENSY_CLI_LOADER_PATH,
                                     '--mcu=TEENSY41',
                                     '-w',
                                     '-v',
                                     '-s',
                                     file_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)

        self.logger.info(result)

        # expected output looks like,
        #  1747 bond_P00xx.py: 119 - teensy400xx.0: PROG020_program() INFO  : Teensy Loader, ...
        # Read ".../BOND_v0/assets/teensy4_server.ino.hex": 102400 bytes, 1.3% usage
        # Found HalfKay Bootloader
        # Programming.................................................................................................
        # Booting

        # check for some key words to confirm success
        if not result.stdout.count('Programming'):
            self.log_bullet("'Programming' did not occur")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        if not result.stdout.count('Booting'):
            self.log_bullet("'Booting' did not occur")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def PROG030_reconnect(self):
        """ Verify Teensy
        - by verifying that we can install instance of driver

        {"id": "PROG030_verify",         "enable": true, "delay": 10 },

        """
        ctx = self.item_start()  # always first line of test
        self.log_bullet(f"{ctx.item.delay}s wait for boot")
        self.sleep(ctx.item.delay)
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
            # Bare minimum init -- does not require 'pogo_hdr_definition._json'
            _teensy = A4401_BOND(port, loggerIn=logging.getLogger("teensy.try"))
            success = _teensy.init(skip_max11311=True)
            if not success:
                self.log_bullet("Failed init")
                self.logger.error("failed on {}...".format(port))

            else:
                self.log_bullet("Found teensy")
                found_teensy = True
                break

        if not found_teensy:
            self.log_bullet("Teensy not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        result = self.expect(_teensy.unique_id())

        unique_id = result['result']['unique_id']
        _, _, _bullet = ctx.record.measurement("teensy4_id", unique_id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        result = self.expect(_teensy.version())

        version = result['result']['version']
        _, _, _bullet = ctx.record.measurement("teensy4_version", version, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        _teensy.close()
        self.item_end()  # always last line of test

    def UPD000_SETUP(self):
        """ Setup teensy for Update (means its already running our server code)
        - close the current connection to Teensy
        - cache the port, so we can open it later in UPD020_verify

        {"id": "UPD000_SETUP",          "enable": true },

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
        # self._teensy_port = driver["obj"]["port"]  # cache for after update reconnect
        self.teensy = driver["obj"]["hwdrv"]

        self.expect(self.teensy.reset())   # set Teensy to a known good state

        self.item_end()  # always last line of test

    def UPD010_update(self):
        """ Update the teensy Firmware

        {"id": "UPD010_update",         "enable": true, "file": "teensy4_server.ino.hex" },

        :return:
        """
        ctx = self.item_start()  # always first line of test

        file_path = os.path.join(BOND_ASSETS_PATH, ctx.item.file)
        if not os.path.isfile(file_path):
            self.log_bullet("file not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(f"{ctx.item.file}")

        # block other instances from reboot/Teensy CLI loader,
        # released even if the item is stopped
        with self.shared_lock(DRIVER_TYPE):
            # close teensy connection, its going to get rebooted
            self.logger.info("reboot_to_bootloader")
            self.expect(self.teensy.reboot_to_bootloader())

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
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)
                self.logger.info(result)

                # expected output looks like,
                #   Teensy Loader, Command Line, Version 2.2
                #   Read ".../teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
                #   Waiting for Teensy device...
                #    (hint: press the reset button)
                #   Found HalfKay Bootloader
                #   Read ".../teensy4_v0/assets/teensy4_server.ino.hex": 70656 bytes, 0.9% usage
                #   Programming..................................................................
                #   Booting

                # check for some keywords to confirm success
                if result.stdout.count('Programming') and result.stdout.count('Booting'):
                    success = True
                    break

                attempts -= 1
                self.sleep(0.1)

        if not success:
            self.log_bullet("teensy_loader_cli failed")
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
        'usb_path': '/devices/pci0000:00/0000:00:08.1/0000:03:00.3/usb1/1-2/1-2.1/1-2.1.4/'
                    '1-2.1.4.1/1-2.1.4.1:1.0/tty/ttyACM3'

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

    def UPD020_verify(self):
        """ Verify Teensy
        - by verifying that we can re-install instance of driver after the update
        - this is difficult because on USB re-enumeration teensy may be on a different
          serial port.  So use the usb_path to find the correct port.
        - NOTE when BOND boots it has a long self test to run, so there is a large delay

        {"id": "UPD020_verify",         "enable": true, "delay": 5 },

        """
        ctx = self.item_start()  # always first line of test

        # Teensy should be re-enumerating on USB, using a simple delay to let that happen
        self.log_bullet(f"{ctx.item.delay}s wait for boot")
        TIME_WAIT_FOR_BOOT_S = 0
        TIME_STEP_S = 4
        while TIME_WAIT_FOR_BOOT_S < ctx.item.delay:
            self.sleep(TIME_STEP_S)
            TIME_WAIT_FOR_BOOT_S += TIME_STEP_S
            self.log_bullet(f"{TIME_WAIT_FOR_BOOT_S}s waited")
            if self.aborted.is_set():  # timed out or aborted
                self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
                return

        self.log_bullet("done wait")

        port = self._find_matching_ttyACM_from_usb_path(self._teensy_usb_path)
        if port is None:
            self.log_bullet("Failed find port")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.logger.info("Trying teensy at {}...".format(port))

        # re-connect to teensy at new port
        self.teensy.set_port(port)
        success = self.teensy.init()
        if not success:
            self.log_bullet("Failed init")
            self.logger.error("failed on {}...".format(port))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet("Found teensy")

        result = self.expect(self.teensy.unique_id())

        unique_id = result['result']['unique_id']
        _, _, _bullet = ctx.record.measurement("teensy4_id", unique_id, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        result = self.expect(self.teensy.version())

        version = result['result']['version']
        _, _, _bullet = ctx.record.measurement("teensy4_version", version, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        self.log_bullet("! ONLY RUN ONCE !")
        self.item_end()  # always last line of test

    def PROG800_usb_tree(self):
        """ USB Tree
        - this is debug code to learn about pyudev.Context()

        {"id": "PROG800_usb_tree",        "enable": true },

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

        self.logger.info(
            "===============================================================================")

        self.item_end()  # always last line of test

    def PROG990_TEARDOWN(self):
        """ teardown for programming BOND

        """
        ctx = self.item_start()  # always first line of test

        self.item_end()  # always last line of test

    def BOND000_SETUP(self):
        """ Setup for testing DUT

        {"id": "BOND000_SETUP",          "enable": true },

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
        self.teensy = driver["obj"]["hwdrv"]

        self.expect(self.teensy.reset())   # set Teensy to a known good state

        self.item_end()  # always last line of test

    def BOND030_adc_check(self):
        """ ADC Check/Validate conversion
        - each MAX11311 on each header has an ADC input connected to Voltage Reference
          for self testing each chip
        - BOND's reference voltage is 2500mV

        {"id": "BOND030_adc_check",      "enable": true, "hdr": 1 },

        """
        ctx = self.item_start()  # always first line of test
        EXPECTED_MV = 2500
        TOLERANCE_MV = 15

        if not (1 <= ctx.item.hdr <= 4):
            self.logger.error(f"invalid header index, 1 <= {ctx.item.hdr} <= 4")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        response = self.expect(self.teensy.bond_max_hdr_adc_cal(ctx.item.hdr))

        success, _result, _bullet = ctx.record.measurement(f"adc_cal_hdr_{ctx.item.hdr}",
                                                           response['result']['mV'],
                                                           unit=ResultAPI.UNIT_MILLIVOLTS,
                                                           min=EXPECTED_MV - TOLERANCE_MV,
                                                           max=EXPECTED_MV + TOLERANCE_MV)
        self.log_bullet(_bullet)

        self.item_end(_result)  # always last line of test

    def BOND040_voltage_check(self):
        """ Check BOND voltage rails
        - these voltages are checked when BOND driver is installed, see
          the A4401_BOND.init() function.
        - the names of the voltages are "V6V", "V5V", "V3V3A", "V3V3D", see A4401_BOND.BIST_VOLTAGES

        {"id": "BOND040_voltage_check",      "enable": true, "voltage": "V6V" },

        """
        ctx = self.item_start()  # always first line of test
        measurement_results = []

        if ctx.item.voltage not in self.teensy.BIST_VOLTAGES:
            self.logger.error(
                f"invalid voltage name {ctx.item.voltage} not in {self.teensy.BIST_VOLTAGES}")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        response = self.expect(self.teensy.bist_voltage(ctx.item.voltage))

        success, _result, _bullet = ctx.record.measurement(f"{ctx.item.voltage}",
                                                           response['result']['mv'],
                                                           unit=ResultAPI.UNIT_MILLIVOLTS)
        self.log_bullet(_bullet)
        measurement_results.append(_result)

        success, _result, _bullet = ctx.record.measurement(f"{ctx.item.voltage}_pass",
                                                           response['result']['pass'],
                                                           unit=ResultAPI.UNIT_BOOLEAN)
        self.log_bullet(_bullet)
        measurement_results.append(_result)

        self.item_end(measurement_results)  # always last line of test

    def BOND050_vbat_check(self):
        """ Check VBAT at voltage, and self test load

            {"id": "BOND050_vbat_check",      "enable": true, "voltage_mv": 3000 },
        """
        ctx = self.item_start()  # always first line of test
        SELFTEST_LOAD_OHMS = 200.0
        TOLERANCE_V = 0.1
        TOLERANCE_MA = 1.0

        measurement_results = []

        self.expect(self.teensy.vbat_set(ctx.item.voltage_mv))
        self.expect(self.teensy.iox_selftest(True))
        self.expect(self.teensy.iox_vbat_con(True))

        self.sleep(0.01)

        response = self.expect(self.teensy.vbat_read())

        _v = float(round(response['result']['v'], 3))
        _min = round(ctx.item.voltage_mv / 1000.0 - TOLERANCE_V, 3)
        _max = round(ctx.item.voltage_mv / 1000.0 + TOLERANCE_V, 3)
        success, _result, _bullet = ctx.record.measurement(f"{ctx.item.voltage_mv}_V",
                                                           _v,
                                                           unit=ResultAPI.UNIT_VOLTS,
                                                           min=_min,
                                                           max=_max)
        self.log_bullet(_bullet)
        measurement_results.append(_result)

        _ima_expected = float(round(ctx.item.voltage_mv / SELFTEST_LOAD_OHMS, 1))
        _ma_measured = round(response['result']['ima'], 2)
        success, _result, _bullet = ctx.record.measurement(f"{ctx.item.voltage_mv}_mA",
                                                           _ma_measured,
                                                           unit=ResultAPI.UNIT_MILLIAMPS,
                                                           min=_ima_expected - TOLERANCE_MA,
                                                           max=_ima_expected + TOLERANCE_MA)
        self.log_bullet(_bullet)
        measurement_results.append(_result)

        self.expect(self.teensy.iox_vbat_con(False))
        self.expect(self.teensy.iox_selftest(False))

        self.item_end(measurement_results)  # always last line of test

    def BOND020_version(self):
        """ Get Bond firmware version

            {"id": "BOND020_version",        "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        response = self.expect(self.teensy.version())

        success, _result, _bullet = ctx.record.measurement(None,
                                                           response['result']['version'],
                                                           unit=ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)
        self.item_end(_result)  # always last line of test

    def BOND060_vdut_check(self):
        """ Check VDUT at voltage, and self test load

            {"id": "BOND060_vdut_check",      "enable": true, "voltage_mv": 3000 },
        """
        ctx = self.item_start()  # always first line of test
        SELFTEST_LOAD_OHMS = 200.0
        TOLERANCE_V = 0.1
        TOLERANCE_MA = 1.0

        measurement_results = []

        self.expect(self.teensy.vdut_set(ctx.item.voltage_mv))
        self.expect(self.teensy.iox_selftest(True))
        self.expect(self.teensy.vdut_con(True))

        self.sleep(0.01)

        response = self.expect(self.teensy.vdut_read())

        _v = float(round(response['result']['v'], 3))
        _min = round(ctx.item.voltage_mv / 1000.0 - TOLERANCE_V, 3)
        _max = round(ctx.item.voltage_mv / 1000.0 + TOLERANCE_V, 3)
        success, _result, _bullet = ctx.record.measurement(f"{ctx.item.voltage_mv}_V",
                                                           _v,
                                                           unit=ResultAPI.UNIT_VOLTS,
                                                           min=_min,
                                                           max=_max)
        self.log_bullet(_bullet)
        measurement_results.append(_result)

        _ima_expected = float(round(ctx.item.voltage_mv / SELFTEST_LOAD_OHMS, 1))
        _ma_measured = round(response['result']['ima'], 2)
        success, _result, _bullet = ctx.record.measurement(f"{ctx.item.voltage_mv}_mA",
                                                           _ma_measured,
                                                           unit=ResultAPI.UNIT_MILLIAMPS,
                                                           min=_ima_expected - TOLERANCE_MA,
                                                           max=_ima_expected + TOLERANCE_MA)
        self.log_bullet(_bullet)
        measurement_results.append(_result)

        self.expect(self.teensy.vdut_con(False))
        self.expect(self.teensy.iox_selftest(False))

        self.item_end(measurement_results)  # always last line of test

    def BOND100_dac(self):
        """ Set BOND DAC pin

        {"id": "BOND100_dac",      "enable": true, "hdr": 1, "pin": 6, "mv": 3300 },

        """
        ctx = self.item_start()  # always first line of test

        if not (1 <= ctx.item.hdr <= 4):
            self.logger.error(f"invalid header index, 1 <= {ctx.item.hdr} <= 4")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.expect(self.teensy.bond_max_hdr_dac(ctx.item.hdr, ctx.item.pin, ctx.item.mv))

        self.item_end()  # always last line of test

    def BOND110_adc(self):
        """ read BOND ADC pin

        {"id": "BOND110_adc",            "enable": true, "hdr": 2, "pin": 14,
                                                       "min": 3200, "max": 3400 },

        """
        ctx = self.item_start()  # always first line of test

        if not (1 <= ctx.item.hdr <= 4):
            self.logger.error(f"invalid header index, 1 <= {ctx.item.hdr} <= 4")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        response = self.expect(self.teensy.bond_max_hdr_adc(ctx.item.hdr, ctx.item.pin))

        success, _result, _bullet = ctx.record.measurement(
            None, response['result']['mV'], min=ctx.item.min, max=ctx.item.max)
        self.log_bullet(_bullet)

        self.item_end(_result)  # always last line of test

    def BOND990_TEARDOWN(self):
        """ teardown BOND

        """
        ctx = self.item_start()  # always first line of test

        # self test load off, in case P1120/P1140 stopped part way
        self.expect(self.teensy.iox_selftest(False))

        # disconnect all power to the DUT
        self.expect(self.teensy.iox_vbat_con(False))
        self.expect(self.teensy.vdut_con(False))

        self.item_end()  # always last line of test
