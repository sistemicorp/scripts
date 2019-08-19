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
    from stublogger import StubLogger
except:
    from public.prism.drivers.micropythonbrd.stublogger import StubLogger



VERSION = "0.0.1"


class pyboard2(pyboard.Pyboard):
    """ Extend the base pyboard class with a little exec helper method, exec_cmd
    to make it more script friendly

    """
    LED_RED    = 1
    LED_GREEN  = 2
    LED_YELLOW = 3
    LED_BLUE   = 4

    def __init__(self, device, baudrate=115200, user='micro', password='python', wait=0, rawdelay=0, loggerIn=None):
        super().__init__(device, baudrate, user, password, wait, rawdelay)

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.device = device

        self.lock = threading.Lock()

    def _repl_result(self, result):
        """ return repl result as a list of strings for client to parse

        :param result:
        :return: success (True/False), list (on success) or original repl result of success False
        """
        if isinstance(result, bytes):
            return True, result.decode("utf-8").splitlines()
        else:
            self.logger.warn("repl_result: unexpected return from pyboard type: {}".format(type(result)))
        # the repl return type was odd at this point but maybe the client expects that
        return False, result

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

    def _verify_single_cmd_ret(self, cmd_dict, delay_poll_ms=100):
        method = cmd_dict.get("method", None)
        args = cmd_dict.get("args", None)

        if method is None:
            return False, "method not specified"

        if args is None:
            return False, "args not specified"

        cmds = []
        c = str(cmd_dict)
        cmds.append("upyb_server.server.cmd({})".format(c))
        success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
        if not success:
            self.logger.error("{} {}".format(success, result))
            return success, result

        cmds = ["upyb_server.server.ret(method='{}')".format(method)]

        # it is assumed the command sent will post a return, with success set
        retry = 5
        succeeded = False
        while retry and not succeeded:
            time.sleep(delay_poll_ms / 1000)
            success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
            self.logger.debug("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == "_debug":
                        self.logger.info("PYBOARD DEBUG: {}".format(r["value"]))
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
        cmds = ["import upyb_server"]
        success, result = self.server_cmd(cmds, repl_exit=False)
        self.logger.info("{} {}".format(success, result))
        return success, result

    def unique_id(self):
        c = {'method': 'unique_id', 'args': {}}
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
        cmds = ["upyb_server.server.ret(method='{}', all='{}')".format(method, all)]
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
        cmds = ["upyb_server.server.peek(method='{}', all='{}')".format(method, all)]
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

    def led_toggle(self, led, on_ms=500, off_ms=500, once=False):
        """ toggle and LED ON and then OFF
        - this is a blocking command

        :param led: # of LED, see self.LED_*
        :param on_ms: # of milliseconds to turn on LED
        :return:
        """
        c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_ms, 'off_ms': off_ms, 'once': once}}
        return self._verify_single_cmd_ret(c)

    def enable_jig_closed_detect(self, enable=True):
        """ Enable Jig Closed feature on pyboard
        - starts a timer on the pyboard that reads the jig closed GPIO (X1)
        - posts messages on the state of the jig closed pin
        - NON-BLOCKING
        - client must read a result before the next result can be queued

        :param enable: True/False
        :return: success, result
        """
        c = {'method': 'enable_jig_closed_detect', 'args': {'enable': enable}}
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

    def set_ldo_voltage(self, name, voltage_mv):
        """ set LDO voltage

        :param name: "V1", "V2", "V3"
        :param voltage_mv: 900 to 3500
        :return: success, result
        """
        c = {'method': 'set_ldo_voltage', 'args': {'name': name, 'voltage_mv': voltage_mv}}
        return self._verify_single_cmd_ret(c)

    def power_good(self, name):
        """ Check the status of the power good pin

        :param name: "V1", "V2", "V3"
        :return: success, status
        """
        c = {'method': 'power_good', 'args': {'name': name}}
        return self._verify_single_cmd_ret(c)
