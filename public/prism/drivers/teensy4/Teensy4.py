#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import time
import json
import threading

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.iba01.stublogger import StubLogger


VERSION = "0.1.0"


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

    def init(self):
        """ Init Teensy SimpleRPC connection

        :return: <True/False> whether Teensy SimpleRPC connection was created
        """
        self.rpc = None  # create SimpleRPC instance here
        # test something to be sure your Teensy is working...

        return False

    def close(self):
        """  Close connection

        :return:
        """
        # TODO: close the connection
        self.logger.info("closing")
        return True

    # -------------------------------------------------------------------------------------------------
    # API (wrapper functions)
    # these are the important functions
    #
    # all functions return dict: { "success": <True/False>, "result": { key: value, ... }}

    def unique_id(self):
        c = {'method': 'unique_id', 'args': {}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def slot(self):
        c = {'method': 'slot', 'args': {}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def version(self):
        c = {'method': 'version', 'args': {}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def led(self, set):
        """ LED on/off
        :param set: [(#, True/False), ...], where #: 1=Red, 2=Yellow, 3=Green, 4=Blue
        :return:
        """
        if not isinstance(set, list):
            return False, "argument must be a list of tuples"
        c = {'method': 'led', 'args': {'set': set}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def led_toggle(self, led, on_ms=500, off_ms=500, once=False):
        """ toggle and LED ON and then OFF
        - this is a blocking command

        :param led: # of LED, see self.LED_*
        :param on_ms: # of milliseconds to turn on LED
        :return:
        """
        c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_ms, 'off_ms': off_ms, 'once': once}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def jig_closed_detect(self):
        """ Read Jig Closed feature on teensy

        :return: success, result
        """
        c = {'method': 'jig_closed_detect', 'args': {}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def adc_read(self, pin, samples=1, samples_ms=1):
        """ Read an ADC pin
        - This is a BLOCKING function
        - result is raw ADC value, client needs to scale to VREF (3.3V)

        :param pin: pin name, X2, X3, etc
        :param samples: Number of samples to average over
        :param samples_ms: Delay between samples
        :return: success, result
        """
        c = {'method': 'adc_read', 'args': {'pin': pin, 'samples': samples, 'samples_ms': samples_ms}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def init_gpio(self, name, pin, mode, pull):
        """ Init GPIO

        :param name:
        :param pin:
        :param mode: one of pyb.Pin.IN, Pin.OUT_PP, Pin.OUT_OD, ..
        :param pull: one of pyb.Pin.PULL_NONE, pyb.Pin.PULL_UP, pyb.Pin.PULL_DN
        :return:
        """
        c = {'method': 'init_gpio', 'args': {'name': name, 'pin': pin, 'mode': mode, 'pull': pull}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def get_gpio(self, pin):
        """ Get GPIO
        :param pin:
        :return:
        """
        c = {'method': 'get_gpio', 'args': {'pin': pin}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

    def set_gpio(self, name, value):
        """ Set GPIO
        :param name:
        :param value: True|False
        :return:
        """
        c = {'method': 'set_gpio', 'args': {'name': name, 'value': value}}
        # FIXME: put SimpleRPC call here, and return the result JSON
        return {"success": False, "result": {}}

