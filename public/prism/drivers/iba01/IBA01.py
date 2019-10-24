#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import time
import json
import threading

import ampy.pyboard as pyboard

try:
    # run locally
    from stublogger import StubLogger
    from iba01_const import *
except:
    # run from prism
    from public.prism.drivers.iba01.stublogger import StubLogger
    from public.prism.drivers.iba01.iba01_const import *


VERSION = "0.2.0"


class IBA01(pyboard.Pyboard):
    """ Extend the base pyboard class with a little exec helper method, exec_cmd
    to make it more script friendly

    There is a lock on self.server_cmd() to sequence clients

    """
    def __init__(self, device, baudrate=115200, user='micro', password='python', wait=0, rawdelay=0, loggerIn=None):
        super().__init__(device, baudrate, user, password, wait, rawdelay)

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.device = device

        self.lock = threading.Lock()

    def server_cmd(self, cmds, repl_enter=True, repl_exit=True, blocking=True):
        """ execute a buffer on the open pyboard

        NOTE:  !! to get results back, the pyboard python code must wrap result in a print() !!

        :param buf: string of command(s)
        :return: success (True/False), result (if any)
        """
        if not isinstance(cmds, list):
            self.logger.error("cmd should be a list of micropython code (strings)")
            return False, "cmds should be a list"

        cmd = "\n".join(cmds)
        self.logger.debug("{} cmd: {}".format(self.device, cmd))

        with self.lock:
            # this was copied/ported from pyboard.py
            try:
                if repl_enter: self.enter_raw_repl()

                if blocking:
                    ret, ret_err = self.exec_raw(cmd + '\n', timeout=10, data_consumer=None)
                else:
                    self.exec_raw_no_follow(cmd)
                    ret_err = False
                    ret = None

            except pyboard.PyboardError as er:
                msg = "{}: {}".format(cmd, er)
                self.logger.error(msg)
                return False, msg
            except KeyboardInterrupt:
                return False, "KeyboardInterrupt"

            if repl_exit: self.exit_raw_repl()

            if ret_err:
                pyboard.stdout_write_bytes(ret_err)
                msg = "{}: {}".format(cmd, ret_err)
                self.logger.error(msg)
                return False, msg

            #print("A: {}".format(ret))
            if ret:
                pyb_str = ret.decode("utf-8")

                # expecting a JSON like dict object in string format, convert this string JSON to python dict
                # fix bad characters...
                fixed_string = pyb_str.replace("'", '"').replace("True", "true").replace("False", "false").replace("None", "null")
                try:
                    self.logger.debug(fixed_string.strip())
                    items = json.loads(fixed_string)
                except Exception as e:
                    self.logger.error(e)
                    return False, []

                return True, items

            return True, []

    def _verify_single_cmd_ret(self, cmd_dict, delay_poll_s=0.1):
        method = cmd_dict.get("method", None)
        args = cmd_dict.get("args", None)

        if method is None:
            return False, "method not specified"

        if args is None:
            return False, "args not specified"

        cmds = []
        c = str(cmd_dict)
        cmds.append("iba01_main.iba01.cmd({})".format(c))
        success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
        if not success:
            self.logger.error("{} {}".format(success, result))
            return success, result

        cmds = ["iba01_main.iba01.ret(method='{}')".format(method)]

        # it is assumed the command sent will post a return, with success set
        retry = 5
        succeeded = False
        while retry and not succeeded:
            time.sleep(delay_poll_s)
            success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
            self.logger.debug("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == "_debug":
                        self.logger.debug("PYBOARD DEBUG: {}".format(r["value"]))
                        retry += 1  # debug lines don't count against retrying
                    if r.get("method", False) == method:
                        succeeded = True
            else:
                return success, result

            retry -= 1

        if not succeeded:
            return False, "Failed to verify method {} was executed".format(method)

        if len(result) > 1:
            self.logger.error("More results than expected: {}".format(result))
            return False, "More results than expected, internal error"

        return result[0]["success"], result[0]

    # -------------------------------------------------------------------------------------------------
    # API (wrapper functions)
    # these are the important functions

    def start_server(self):
        cmds = ["import iba01_main"]
        success, result = self.server_cmd(cmds, repl_exit=False)
        self.logger.info("{} {}".format(success, result))
        return success, result

    def unique_id(self):
        c = {'method': 'unique_id', 'args': {}}
        return self._verify_single_cmd_ret(c)

    def slot(self):
        c = {'method': 'slot', 'args': {}}
        return self._verify_single_cmd_ret(c)

    def version(self):
        c = {'method': 'version', 'args': {}}
        return self._verify_single_cmd_ret(c)

    def debug(self, enable=True):
        c = {'method': 'debug', 'args': {"enable": enable}}
        return self._verify_single_cmd_ret(c)

    def get_server_method(self, method, all=False):
        """ Get return value message(s) from the server for a specific method
        - this function will remove the message(s) from the server queue

        :param method:
        :param all: set True for all the return messages
        :return: success, result
        """
        cmds = ["iba01_main.iba01.ret(method='{}', all={})".format(method, all)]
        retry = 5
        succeeded = False
        while retry and not succeeded:
            time.sleep(0.1)
            success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
            self.logger.debug("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == method:
                        succeeded = True
            else:
                return success, result

            retry -= 1

        if not succeeded:
            return False, "Failed to find method {}".format(method)

        return success, result

    def peek_server_method(self, method=None, all=False):
        """ Peek return message value(s from the server for a specific method
        - this function will NOT remove the message(s) from the server queue

        :param method:
        :param all: set True for all the return messages
        :return:
        """
        cmds = ["iba01_main.iba01.peek(method='{}', all='{}')".format(method, all)]
        retry = 5
        succeeded = False
        while retry and not succeeded:
            time.sleep(0.1)
            success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
            self.logger.debug("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == method:
                        succeeded = True
            else:
                return success, result

            retry -= 1

        if not succeeded:
            return False, "Failed to find method {}".format(method)

        return success, result

    def led(self, set):
        """ LED on/off
        :param set: [(#, True/False), ...], where #: 1=Red, 2=Yellow, 3=Green, 4=Blue
        :return:
        """
        if not isinstance(set, list):
            return False, "argument must be a list of tuples"
        c = {'method': 'led', 'args': {'set': set}}
        return self._verify_single_cmd_ret(c)

    def led_toggle(self, led, on_ms=500, off_ms=500, once=False):
        """ toggle and LED ON and then OFF
        - this is a blocking command

        :param led: # of LED, see self.LED_*
        :param on_ms: # of milliseconds to turn on LED
        :return:
        """
        c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_ms, 'off_ms': off_ms, 'once': once}}
        return self._verify_single_cmd_ret(c)

    def jig_closed_detect(self):
        """ Read Jig Closed feature on pyboard

        :return: success, result
        """
        c = {'method': 'jig_closed_detect', 'args': {}}
        return self._verify_single_cmd_ret(c)

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
        return self._verify_single_cmd_ret(c)

    def adc_read_multi(self, pins, samples=100, freq=100):
        """ Read single or Multiple pins at Freq rate
        - NON-BLOCKING
        - the result is a list of samples
        - results are raw ADC values, client needs to scale to VREF (3.3V)

        :param pins: list of pins
        :param samples: # of samples to take
        :param freq: rate of taking samples
        :return: success, result
        """
        c = {'method': 'adc_read_multi', 'args': {'pins': pins, 'samples': samples, 'freq': freq}}
        return self._verify_single_cmd_ret(c)

    def init_gpio(self, name, pin, mode, pull):
        """ Init GPIO

        :param name:
        :param pin:
        :param mode: one of pyb.Pin.IN, Pin.OUT_PP, Pin.OUT_OD, ..
        :param pull: one of pyb.Pin.PULL_NONE, pyb.Pin.PULL_UP, pyb.Pin.PULL_DN
        :return:
        """
        c = {'method': 'init_gpio', 'args': {'name': name, 'pin': pin, 'mode': mode, 'pull': pull}}
        return self._verify_single_cmd_ret(c)

    def get_gpio(self, pin):
        """ Get GPIO
        :param pin:
        :return:
        """
        c = {'method': 'get_gpio', 'args': {'pin': pin}}
        return self._verify_single_cmd_ret(c)

    def set_gpio(self, name, value):
        """ Set GPIO
        :param name:
        :param value: True|False
        :return:
        """
        c = {'method': 'set_gpio', 'args': {'name': name, 'value': value}}
        return self._verify_single_cmd_ret(c)

    def reset(self):
        """ Reset the I2C devices to a known/default state

        :return:
        """
        c = {'method': 'reset', 'args': {}}
        return self._verify_single_cmd_ret(c)

    def relay_v12(self, connect=True):
        """ Relay V12 control
        """
        c = {'method': 'relay_v12', 'args': {'connect': connect}}
        return self._verify_single_cmd_ret(c)

    def relay_vsys(self, connect=True):
        """ Relay V12 control
        """
        c = {'method': 'relay_vsys', 'args': {'connect': connect}}
        return self._verify_single_cmd_ret(c)

    def relay_vbat(self, connect=True):
        """ Relay V12 control
        """
        c = {'method': 'relay_vbat', 'args': {'connect': connect}}
        return self._verify_single_cmd_ret(c)

    def supply_enable(self, name, enable=True, voltage_mv=None, cal=True):
        """ set Supply (enable, voltage, calibrate)

        - voltage is set first
        - calibration only occurs if supply is enabled
        - If changing voltage while connected to the DUT, 'cal' should be set False.
          Note that reading current outside of calibrated voltages, may result in increased error.
          Calibrate all intended voltages before applying Supply to the DUT.

        :param name: <"V1"|"V2">
        :param enable: <True|False>,      # default: True
        :param voltage_mv: <voltage_mv>,  # if not specified, current setting and PG is returned
        :param cal: <True|False>}         # default: True
        :return: success, result {'name': name,
                                  'enable': <True|False>,
                                  'voltage_mv': <voltage_mv>,
                                  'pg': "PG_GOOD/BAD"  }
        """
        c = {'method': 'supply_enable', 'args': {'name': name, 'voltage_mv': voltage_mv, "enable": enable, "cal": cal}}
        return self._verify_single_cmd_ret(c)

    def supply_current(self, name):
        """ set Supply (enable, voltage, calibrate)

        - voltage is set first
        - calibration only occurs if supply is enabled
        - If changing voltage while connected to the DUT, 'cal' should be set False.
          Note that reading current outside of calibrated voltages, may result in increased error.
          Calibrate all intended voltages before applying Supply to the DUT.

        :param name: <"V1"|"V2">
        :return: success, result {'name': name,
                                  'enable': enable,
                                  'voltage_mv': voltage_mv,
                                  'current_ua': current_ua,
                                  'pg': pg_or_err, }
        """
        c = {'method': 'supply_current', 'args': {'name': name}}
        return self._verify_single_cmd_ret(c)

    def pwm(self, name, pin, timer, channel, freq, duty_cycle, enable=True):
        """ Setup PWM

        :param name:
        :param pin: name of the pin, can be the same as name
        :param timer: timer number, see http://micropython.org/resources/pybv11-pinout.jpg
        :param channel: timer channel number
        :param freq:
        :param duty_cycle: default 50%
        :return:
        """
        c = {'method': 'pwm', 'args': {'name': name, 'pin': pin, 'timer': timer, "channel": channel,
                                       'freq': freq, 'duty_cycle': duty_cycle,
                                       "enable": enable}}
        return self._verify_single_cmd_ret(c)
