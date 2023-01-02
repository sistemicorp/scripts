#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2022
Owen Li, Martin Guthrie

"""
import json
import threading
import re
from simple_rpc import Interface
from serial import SerialException

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.iba01.stublogger import StubLogger


DRIVER_TYPE = "TEENSY4"


class Teensy4:
    """ teensy4 SimpleRPC based driver

    Adding new RPC calls...

    1) Write server code by adding a function in teensy4_server.ino (Look at existing functions as example)
    2) Export the function by adding a name and description in the loop() (Look at existing exports as example)
    3) Write function in Teensy4 Class (this one) to call your simpleRPC function (Look at existing
       functions as example).  Note the code is organized so that "on-board" Teensy functions are in one
       section, and off module functions are in another.
    4) Test your new API with the Teensy4_cli.py script.
    5) Write function in teensy400xx.py to call your Teensy4 Class function (Look at existing functions as example)
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

    JIG_CLOSE_GPIO = None  # GPIO number for Jig Closed detect, set to None if not using (Active-Low)

    GPIO_NUMBER_MIN = 0
    GPIO_NUMBER_MAX = 41

    # LED test indicators GPIO numbers and whether they are active_high. Set GPIO to None if not using
    TEST_INDICATORS = {
        "pass": {'gpio': 20, 'active_high': True},
        "fail": {'gpio': 21, 'active_high': True},
        "other": {'gpio': 22, 'active_high': True}
    }

    _version_file = "public/prism/drivers/teensy4/server/libraries/version/version.h"

    def __init__(self, port, loggerIn=None):
        self.lock = threading.Lock()

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.port = port
        self.rpc = None

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
            self.logger.error("version does not match, Python: {} Arduino: {}".format(self.my_version, version_response["result"]["version"]))
            return False

        # check if test indicator has valid GPIOs
        self._test_indicator_check()

        # check if jig close has valid GPIOs
        self._jig_close_check()

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
        self.rpc.close()
        self.rpc = None
        return True

    # ----------------------------------------------------------------------------------------------
    # Helper Functions
    #
    # - function names should all begin with "_"
    # - functions are all private to this class

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

    def _test_indicator_check(self):
        for k in self.TEST_INDICATORS.keys():
            pin_number = self.TEST_INDICATORS[k]['gpio']
            if pin_number < 0 or pin_number > 41:
                self.logger.error("{} has Invalid GPIO {}".format(k, pin_number))
                return False
            if pin_number is None:
                self.logger.error("Test Indicator not defined (None)")
                return False
            self.rpc.call_method('init_gpio', pin_number, self.GPIO_MODE_OUTPUT.encode())
        return True

    def _jig_close_check(self):
        if self.JIG_CLOSE_GPIO is None:
            self.logger.info("Jig Closed Detector not defined (None)")
            return True
        elif self.GPIO_NUMBER_MIN < self.JIG_CLOSE_GPIO > self.GPIO_NUMBER_MAX:
            self.logger.error("Invalid GPIO")
            return False
        else:
            self.rpc.call_method('init_gpio', self.JIG_CLOSE_GPIO, self.GPIO_MODE_INPUT_PULLUP.encode())
            return True

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
        return list(self.rpc.methods)

    def unique_id(self):
        """ unique id
        :return: success = True/False, method: unique_id, unique_id = MAC Address
        """
        answer = self.rpc.call_method('unique_id')
        return json.loads(answer)

    def slot(self):
        """ slot
        :return: success = True/False, method: slot, id = id
        """
        # TODO: implement arduino side
        answer = self.rpc.call_method('slot')
        return json.loads(answer)

    # def channel(self):
    #     c = {'method': 'slot', 'args': {}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def version(self):
        """ Version
        :return: success = True/False, method = version, version = version#
        """
        answer = self.rpc.call_method('version')
        return json.loads(answer)

    def reset(self):
        """ reset
        :return: success = True/False, method = reset
        """
        answer = self.rpc.call_method('reset')
        return json.loads(answer)

    def reboot_to_bootloader(self):
        """ reboot
        :return: success = True/False, method = reset
        """
        try:
            self.rpc.call_method('reboot_to_bootloader')
            # reboot will not return, expect SerialException exception, fake the return success

        except SerialException:
            pass

        except Exception as e:
            self.logger.error(e)
            return json.loads("""{"success": false}""")  # json false is lower case

        return json.loads("""{"success": true}""")  # json true is lower case

    def led(self, set):
        """ LED on/off
        :param set: True/False
        :return: success = True/False, method = set_led, result = state = ON/OFF
        """
        answer = self.rpc.call_method('set_led', set)
        return json.loads(answer)

    # def led_toggle(self, led, on_ms=500, off_ms=500, once=False):
    #     """ toggle and LED ON and then OFF
    #     - this is a blocking command
    #
    #     :param led: # of LED, see self.LED_*
    #     :param on_ms: # of milliseconds to turn on LED
    #     :return:
    #     """
    #     c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_ms, 'off_ms': off_ms, 'once': once}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def read_adc(self, pin_number, sample_num=1, sample_rate=1):
        """ Read an ADC pin
        - This is a BLOCKING function
        - result is raw ADC value, client needs to scale to VREF (3.3V)

        :param pin_number: (0 - 41)
        :param sample_num: Number of samples to average over
        :param sample_rate: Millisecond delay between samples
        :return: success = True/False, method = read_adc, result = reading = *
        """
        answer = self.rpc.call_method('read_adc', pin_number, sample_num, sample_rate)
        return json.loads(answer)

    def init_gpio(self, pin_number, mode):
        """ Init GPIO
        :param pin_number: (0 - 41)
        :param mode: Teensy4.MODE_*
        :return: success = True/False, method = init_gpio, result = init = Set pin (pin_number) to (mode)
        """
        if mode not in self.GPIO_MODE_LIST:
            err = "Invalid mode {} not in {}".format(mode, self.GPIO_MODE_LIST)
            self.logger.error(err)
            return {'success': False, 'value': {'err': err}}

        mode_b = mode.encode()
        answer = self.rpc.call_method('init_gpio', pin_number, mode_b)
        return json.loads(answer)

    def read_gpio(self, pin_number):
        """ Get GPIO
        :param pin_number: (0 - 41)
        :return: success = True/False, method = read_gpio, result = state = 1/0
        """
        answer = self.rpc.call_method('read_gpio', pin_number)
        return json.loads(answer)

    def write_gpio(self, pin_number, state):
        """ Set GPIO
        :param pin_number: (0 - 41)
        :param state: 1/0
        :return: success = True/False, method = write_gpio, result = state = 1/0
        """
        answer = self.rpc.call_method('write_gpio', pin_number, state)
        return json.loads(answer)

    #
    # API (wrapper functions)
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    #

    def jig_closed_detect(self):
        """ Read Jig Closed feature on Teensy
        This is used by Prism Player logic, and can only return True|False

        return: <True|False>
        """
        if self.JIG_CLOSE_GPIO is None:
            self.logger.info("Jig Closed Detector not defined (None), returning True")
            return True

        answer = json.loads(self.rpc.call_method('read_gpio', self.JIG_CLOSE_GPIO))
        success = answer['success']

        if not success:
            self.logger.error("Failed to detect Jig Close GPIO")
            return False

        if answer['result']['state'] != 1:
            self.logger.info("Jig close detected")
        else:
            self.logger.info("Jig close NOT detected")

        return not answer['result']['state']

    def show_pass_fail(self, p=False, f=False, o=False):
        """ Set pass/fail indicator

        :param p: <True|False>  set the Pass LED
        :param f: <True|False>  set the Fail LED
        :param o: <True|False>  "other" is set
        :return: None
        """
        if self.rpc is None:
            return

        for k in self.TEST_INDICATORS.keys():
            self.rpc.call_method('write_gpio', self.TEST_INDICATORS[k]['gpio'], not self.TEST_INDICATORS[k]['active_high'])

        if p and self.TEST_INDICATORS.get('pass', False):
            self.rpc.call_method('write_gpio', self.TEST_INDICATORS["pass"]["gpio"], self.TEST_INDICATORS["pass"]["active_high"])

        if f and self.TEST_INDICATORS.get('fail', False):
            self.rpc.call_method('write_gpio', self.TEST_INDICATORS["fail"]["gpio"], self.TEST_INDICATORS["fail"]["active_high"])

        if o and self.TEST_INDICATORS.get('other', False):
            self.rpc.call_method('write_gpio', self.TEST_INDICATORS["other"]["gpio"], self.TEST_INDICATORS["other"]["active_high"])

        return None

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Teensy OFF-Module Functions
    #
    # - APIs to features that are off the Teensy module
    # - for example, I2C component APIs, etc


