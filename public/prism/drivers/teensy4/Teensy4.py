#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2026
Owen Li, Martin Guthrie

"""
import os
import json
import threading
import re
from simple_rpc import Interface
from serial import SerialException

try:
    # run locally
    from stublogger import StubLogger
except ImportError:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


DRIVER_TYPE = "TEENSY4"


class Teensy4:
    """ teensy4 SimpleRPC based driver

    Adding new RPC calls...

    1) Write server code by adding a function in teensy4_server.ino (Look at existing functions
       as example)
    2) Export the function by adding a name and description in the loop() (Look at existing
       exports as example)
    3) Write a method in this class that calls it with self._call().
    4) Test your new API with the Teensy4_cli.py script.
    5) Write function in teensy400xx.py to call your Teensy4 Class function (Look at existing
       functions as example)
    6) Add your function call to the test script!

    version.h:
    ----------
    There is a version for teensy4_server.ino and for the python code. The version number must be
    the same for testing to run.

    """
    GPIO_MODE_INPUT = "INPUT"
    GPIO_MODE_OUTPUT = "OUTPUT"
    GPIO_MODE_INPUT_PULLUP = "INPUT_PULLUP"
    GPIO_MODE_LIST = [GPIO_MODE_INPUT, GPIO_MODE_OUTPUT, GPIO_MODE_INPUT_PULLUP]

    JIG_CLOSE_GPIO = None  # GPIO number for Jig Closed detect, set to None if not using
    JIG_CLOSED_STATE = 0  # GPIO state when the jig is closed (Active-Low, with INPUT_PULLUP)

    GPIO_NUMBER_MIN = 0
    GPIO_NUMBER_MAX = 41

    # LED test indicators GPIO numbers and whether they are active_high, GPIO None is not used
    TEST_INDICATORS = {
        "pass": {'gpio': 20, 'active_high': True},
        "fail": {'gpio': 21, 'active_high': True},
        "other": {'gpio': 22, 'active_high': True}
    }

    # For Teensy FW version checking the SAME (c code) header file that created the Teensy4
    # firmware is used to check if that firmware is now running (deployed) on Teensy4.
    # if that FW is not running, there is probably a problem!  See method init().
    _version_file = os.path.join(os.path.dirname(__file__), "server/teensy4_server/version.h")

    def __init__(self, port, loggerIn=None):
        if loggerIn:
            self.logger = loggerIn
        else:
            self.logger = StubLogger()

        self._lock = threading.Lock()
        self.port = port
        self.rpc = None
        self._jig_closed_last = None

        self.my_version = self._get_version()
        self.logger.info(f"version {self.my_version}")

    def set_port(self, port):
        self.port = port

    def init(self):
        """ Init Teensy SimpleRPC connection
        :return: <True/False> whether Teensy SimpleRPC connection was created
        """
        self.logger.info("attempting to install Teensy on port {}".format(self.port))

        if self.rpc is None:
            try:
                self.rpc = Interface(self.port)

            except Exception as e:
                self.logger.error(e)
                return False

        version_response = self.version()
        if not version_response["success"]:
            self.logger.error("Unable to get version")
            return False

        if self.my_version != version_response["result"]["version"]:
            self.logger.error("version does not match, Python: {} Arduino: {}".format(
                self.my_version, version_response["result"]["version"]))
            return False

        if not self._test_indicator_check():
            return False

        if not self._jig_close_check():
            return False

        # finally, all is well
        self.logger.info("Installed Teensy on port {}".format(self.port))
        return True

    def close(self):
        """  Close connection

        :return:
        """
        if self.rpc is None:
            return True

        self.logger.info(f"closing {self.port}")
        try:
            self.rpc.close()
        except (SerialException, OSError) as e:
            self.logger.error(e)
        self.rpc = None
        return True

    # ----------------------------------------------------------------------------------------------
    # Helper Functions
    #
    # - function names should all begin with "_"
    # - functions are all private to this class

    def _call(self, method, *args, squelch=False):
        """ Call an RPC method on the Teensy

        :param method: RPC method name
        :param args: RPC arguments
        :param squelch: True does not log the call or a successful answer
        :return: {'success': <True/False>, 'method': <method>, 'result': {...}}
        """
        with self._lock:
            if not squelch:
                self.logger.info(f"{method} {args}" if args else method)

            if self.rpc is None:
                return self._error(method, "not connected")

            try:
                answer = self.rpc.call_method(method, *args)

            except (SerialException, OSError, ValueError, TypeError) as e:
                self.logger.error(f"{method}: {e}")
                return self._error(method, str(e))

            return self._rpc_validate(answer, squelch)

    def _error(self, method, error):
        return {'success': False, 'method': method, 'result': {'error': error}}

    def _get_version(self):
        """ Get Version from version.h
        - The version of the "RPC server" running on Teensy, is expected to be the
          same version of this Python code.  If there is a difference, then
          something is out of sync.  init() will fail if the versions do not match.
        - The Teensy Arduino Code uses version.h to set its version.  This function
          reads that same file to get the expected version running on Teensy.

        Expected version.h file contents, no other pattern is accounted for,
        !!no other lines or comments are allowed!!
            #define VERSION "1.0.0"
        Extract "1.0.0"

        :return: <version>|"ERROR"
        """
        regex = r"\d+\.\d+\.\d+"

        with open(self._version_file) as f:
            s = f.read()

        m = re.findall(regex, s)
        if not m:
            self.logger.error(f"Unable to find version in {self._version_file}: {s}")
            return "ERROR"

        return m[0]

    def _gpio_valid(self, pin_number):
        return isinstance(pin_number, int) and \
            self.GPIO_NUMBER_MIN <= pin_number <= self.GPIO_NUMBER_MAX

    def _test_indicator_check(self):
        """ Init the test indicator GPIOs as outputs, a GPIO of None is not used
        :return: True/False
        """
        for k, indicator in self.TEST_INDICATORS.items():
            pin_number = indicator['gpio']
            if pin_number is None:
                self.logger.info(f"Test Indicator {k} not defined (None)")
                continue
            if not self._gpio_valid(pin_number):
                self.logger.error("{} has Invalid GPIO {}".format(k, pin_number))
                return False
            answer = self.init_gpio(pin_number, self.GPIO_MODE_OUTPUT)
            if not answer['success']:
                self.logger.error(f"Test Indicator {k} GPIO init failed {answer}")
                return False
        return True

    def _jig_close_check(self):
        if self.JIG_CLOSE_GPIO is None:
            self.logger.info("Jig Closed Detector not defined (None)")
            return True

        if not self._gpio_valid(self.JIG_CLOSE_GPIO):
            self.logger.error(f"Invalid Jig Closed GPIO {self.JIG_CLOSE_GPIO}")
            return False

        answer = self.init_gpio(self.JIG_CLOSE_GPIO, self.GPIO_MODE_INPUT_PULLUP)
        if not answer['success']:
            self.logger.error(f"Jig Closed GPIO init failed {answer}")
            return False
        return True

    def _rpc_validate(self, answer, squelch=False):
        try:
            answer = json.loads(answer)
            if answer["success"]:
                if not squelch:
                    self.logger.info(answer)
            else:
                self.logger.error(answer)

        except Exception as e:
            self.logger.error(answer)
            self.logger.error(e)
            answer = {"success": False, "result": {"error": f"invalid response: {e}"}}

        return answer

    # Helper Functions
    # ----------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------
    # API (wrapper functions)
    #
    # - functions that are Teensy module functions (on-board)
    # - all RPC functions return dict: { "success": <True/False>, "result": { key: value, ... }}
    #

    def list(self):
        """ list
        :return: list of Teensy methods
        """
        return list(self.rpc.device['methods'])

    def unique_id(self):
        """ unique id
        :return: {'success': True, 'method': 'unique_id', 'result': {'unique_id': <MAC>}}
        """
        return self._call('unique_id')

    def slot(self):
        """ slot (deprecated, slots are ordered by USB path)
        :return: {'success': True, 'method': 'slot', 'result': {'id': <int>}}
        """
        return self._call('slot')

    def version(self):
        """ Version
        :return: {'success': True, 'method': 'version', 'result': {'version': <version>}}
        """
        return self._call('version')

    def reset(self):
        """ reset (not a Teensy reset)
        :return: {'success': True, 'method': 'reset', 'result': {}}
        """
        return self._call('reset')

    def reboot_to_bootloader(self):
        """ reboot
        :return: success = True/False, method = reset
        """
        try:
            with self._lock:
                self.logger.info("reboot_to_bootloader")
                self.rpc.call_method('reboot_to_bootloader')
                # reboot will not return, expect SerialException exception, fake the return success

        except SerialException:
            pass

        except Exception as e:
            self.logger.error(e)
            return {"success": False, "method": "reboot_to_bootloader", "result": {}}

        return {"success": True, "method": "reboot_to_bootloader", "result": {}}

    def led(self, set):
        """ LED on/off
        :param set: True/False
        :return: {'success': True, 'method': 'set_led', 'result': {'state': 'on'|'off'}}
        """
        return self._call('set_led', set)

    def read_adc(self, pin_number, sample_num=1, sample_rate_ms=1):
        """ Read an ADC pin
        - This is a BLOCKING function
        - result is raw ADC value, client needs to scale to VREF (3.3V)

        :param pin_number: (0 - 41)
        :param sample_num: Number of samples to average over, 1-1000
        :param sample_rate_ms: Millisecond delay between samples
        :return: {'success': True, 'method': 'read_adc', 'result': {'reading': <int>}}
        """
        return self._call('read_adc', pin_number, sample_num, sample_rate_ms)

    def init_gpio(self, pin_number, mode):
        """ Init GPIO
        :param pin_number: (0 - 41)
        :param mode: Teensy4.GPIO_MODE_*
        :return: {'success': True, 'method': 'init_gpio', 'result': {'mode': <mode>}}
        """
        if mode not in self.GPIO_MODE_LIST:
            err = "Invalid mode {} not in {}".format(mode, self.GPIO_MODE_LIST)
            self.logger.error(err)
            return self._error('init_gpio', err)

        return self._call('init_gpio', pin_number, mode.encode())

    def read_gpio(self, pin_number):
        """ Get GPIO
        :param pin_number: (0 - 41)
        :return: {'success': True, 'method': 'read_gpio', 'result': {'state': 1|0}}
        """
        squelch = pin_number == self.JIG_CLOSE_GPIO  # squelch jig closed polling
        return self._call('read_gpio', pin_number, squelch=squelch)

    def write_gpio(self, pin_number, state: bool):
        """ Set GPIO
        :param pin_number: (0 - 41)
        :param state: True/False
        :return: {'success': True, 'method': 'write_gpio', 'result': {'state': True|False}}
        """
        return self._call('write_gpio', pin_number, state)

    #
    # API (wrapper functions)
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Prism Player Callback functions
    #

    def jig_closed_detect(self):
        """ Read Jig Closed feature on Teensy
        This is used by Prism Player logic
        True - Jig Closed (testing will start)
        False - Jig Open
        None - Not implemented, or error

        # NOTE: !! if not using jig_closed_detect the play function should be None
        #          See hwdrv_teensy4.py:discover_channels()

        return: <True|False|None>
        """
        if self.JIG_CLOSE_GPIO is None:
            self.logger.error("Jig Closed JIG_CLOSE_GPIO not defined (None), returning None")
            # if not using jig_closed_detect feature see note above
            return None

        if self.rpc is None:
            self.logger.error("No rpc handler returning None")
            return None

        answer = self.read_gpio(self.JIG_CLOSE_GPIO)
        if not answer['success']:
            self.logger.error("Failed to detect Jig Close GPIO")
            return None

        closed = answer['result']['state'] == self.JIG_CLOSED_STATE
        if closed != self._jig_closed_last:  # log changes only, this is polled
            self.logger.info(f"Jig closed: {closed}")
            self._jig_closed_last = closed

        return closed

    def show_pass_fail(self, p=False, f=False, o=False):
        """ Set pass/fail indicator

        :param p: <True|False>  set the Pass LED
        :param f: <True|False>  set the Fail LED
        :param o: <True|False>  "other" is set
        :return: None
        """
        self.logger.info(f"pass: {p}, fail: {f}, other: {o}")
        if self.rpc is None:
            return

        states = {"pass": p, "fail": f, "other": o}
        for k, indicator in self.TEST_INDICATORS.items():
            if indicator['gpio'] is None:
                continue
            on = states.get(k, False)
            level = indicator['active_high'] if on else not indicator['active_high']
            answer = self.write_gpio(indicator['gpio'], level)
            if not answer['success']:
                self.logger.error(f"Test Indicator {k} failed {answer}")

    def jig_reset(self):
        """ Called by Prism at the start and end of testing
        - use this callback to set the hardware to a known good reset state
        - should also be called on hardware discovery

        :return: reset() response
        """
        return self.reset()

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Teensy OFF-Module Functions
    #
    # - APIs to features that are off the Teensy module
    # - for example, I2C component APIs, etc
    #
