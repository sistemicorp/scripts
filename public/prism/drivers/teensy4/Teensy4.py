#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import time
import json
import threading
from simple_rpc import Interface

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.iba01.stublogger import StubLogger


class Teensy4():
    """ teensy4 SimpleRPC based driver

    ... add notes as required...

    """
    def __init__(self, port, baudrate=9600, loggerIn=None):
        self.lock = threading.Lock()

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.port = port
        self.rpc = None
        self.my_version = "0.1.0"


    def init(self):
        """ Init Teensy SimpleRPC connection
        :return: <True/False> whether Teensy SimpleRPC connection was created
        """
        self.logger.info("attempting to install Teensy on port {}".format(self.port))
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
            self.logger.error("version does not match, {} {}".format(...))
            return False

        # finally, all is well
        self.logger.info("Installed Teensy on port {}".format(self.port))
        return True

    def close(self):
        """  Close connection
          
        :return:
        """
        self.logger.info("closing")
        self.rpc.close()
        return True

    # -------------------------------------------------------------------------------------------------
    # API (wrapper functions)
    # these are the important functions
    #
    # all functions return dict: { "success": <True/False>, "result": { key: value, ... }}

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

    # def jig_closed_detect(self):
    #     """ Read Jig Closed feature on teensy
    #
    #     :return: success, result
    #     """
    #     c = {'method': 'jig_closed_detect', 'args': {}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    # def adc_read(self, pin, samples=1, samples_ms=1):
    #     """ Read an ADC pin
    #     - This is a BLOCKING function
    #     - result is raw ADC value, client needs to scale to VREF (3.3V)
    #
    #     :param pin: pin name, X2, X3, etc
    #     :param samples: Number of samples to average over
    #     :param samples_ms: Delay between samples
    #     :return: success, result
    #     """
    #     c = {'method': 'adc_read', 'args': {'pin': pin, 'samples': samples, 'samples_ms': samples_ms}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def init_gpio(self, pin_number, mode):
        """ Init GPIO
        :param pin_number: (0 - 41)
        :param mode: INPUT/ INPUT_PULLUP/ OUTPUT
        :return: success = True/False, method = init_gpio, result = init = Set pin (pin_number) to (mode)
        """
        mode_b = mode.encode()
        answer = self.rpc.call_method('init_gpio', pin_number, mode_b)
        return json.loads(answer)

    # def get_gpio(self, pin):
    #     """ Get GPIO
    #     :param pin:
    #     :return:
    #     """
    #     c = {'method': 'get_gpio', 'args': {'pin': pin}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    # def set_gpio(self, name, value):
    #     """ Set GPIO
    #     :param name:
    #     :param value: True|False
    #     :return:
    #     """
    #     c = {'method': 'set_gpio', 'args': {'name': name, 'value': value}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

