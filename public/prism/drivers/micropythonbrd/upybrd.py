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
from stublogger import StubLogger


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

    def exec_cmd(self, cmds, repl_enter=True, repl_exit=True, blocking=True):
        """ execute a buffer on the open pyboard

        commands should be formed this way:
            pyb = pyboard2(args.port)
            cmds = ["from pyb import Pin",
                    "p_in = Pin('{}', Pin.IN, Pin.PULL_UP)".format(args.read_gpio),
                    "print(p_in.value())",
                    'print("hello")',
                    'print("world")'
            ]
            success, result = pyb.exec_cmd(cmds)
            pyb.close()

        NOTE:  !! to get results back you must wrap in a print() !!

        :param buf: string of command(s)
        :return: success (True/False), result (if any)
        """
        if not isinstance(cmds, list):
            self.logger.error("cmd should be a list of micropython code (strings)")
            return False, None

        cmd = "\n".join(cmds)
        print(cmd)

        # this was copied/ported from pyboard.py
        try:
            if repl_enter: self.enter_raw_repl()

            if blocking:
                ret, ret_err = self.exec_raw(cmd + '\n', timeout=1, data_consumer=None)
            else:
                self.exec_raw_no_follow(cmd)
                ret_err = False
                ret = None

        except pyboard.PyboardError as er:
            self.logger.error(er)
            return False, None
        except KeyboardInterrupt:
            return False, None

        if repl_exit: self.exit_raw_repl()

        if ret_err:
            pyboard.stdout_write_bytes(ret_err)
            self.logger.error(ret_err)
            return False, None

        if ret:
            return True, ret.decode("utf-8").strip()
        return True, {}

    def server_cmd(self, cmds, repl_enter=True, repl_exit=True, blocking=True):
        """ execute a buffer on the open pyboard

        commands should be formed this way:
            pyb = pyboard2(args.port)
            cmds = ["from pyb import Pin",
                    "p_in = Pin('{}', Pin.IN, Pin.PULL_UP)".format(args.read_gpio),
                    "print(p_in.value())",
                    'print("hello")',
                    'print("world")'
            ]
            success, result = pyb.exec_cmd(cmds)
            pyb.close()

        NOTE:  !! to get results back you must wrap in a print() !!

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
                # json-ize...
                # TODO: find some more complete code...
                fixed_string = ret.decode("utf-8").replace("'", '"').replace("True", "true").replace("False", "false").replace("None", "null")
                self.logger.info(fixed_string)
                items = json.loads(fixed_string)
                return True, items
            return True, []

    # -------------------------------------------------------------------------------------------------
    # API (wrapper functions)

    def _verify_single_cmd_ret(self, cmd_dict, delay_poll=0.1):
        method = cmd_dict.get("method", None)
        args = cmd_dict.get("args", None)

        if method is None:
            return False, "method not specified"

        if args is None:
            return False, "args not specified"

        cmds = []
        c = str(cmd_dict)
        cmds.append("upyb_server_01.server.cmd({})".format(c))
        success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
        if not success:
            self.logger.error("{} {}".format(success, result))
            return success, result

        cmds = ["upyb_server_01.server.ret(method='{}')".format(method)]

        # it is assumed the command sent will post a return, with success set
        retry = 5
        succeeded = False
        while retry and not succeeded:
            time.sleep(delay_poll)
            success, result = self.server_cmd(cmds, repl_enter=False, repl_exit=False)
            self.logger.info("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == method and r.get("success", False) == True:
                        succeeded = True
            else:
                return success, result

            retry -= 1

        if not succeeded:
            return False, "Failed to verify method {} was executed".format(method)

        if len(result) > 1:
            self.logger.error("More results than expected: {}".format(result))
            return False, "More results than expected, internal error"

        if not result[0]["success"]:
            return False, result[0]

        return success, result[0]

    def start_server(self):
        cmds = ["import upyb_server_01"]
        success, result = self.server_cmd(cmds, repl_exit=False)
        self.logger.info("{} {}".format(success, result))
        return success

    def get_server_method(self, method, all=False):
        cmds = ["upyb_server_01.server.ret(method='{}', all='{}')".format(method, all)]
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

    def led_toggle(self, led, on_ms=500):
        """ toggle and LED ON and then OFF
        - this is a blocking command

        :param led: # of LED, see self.LED_*
        :param on_ms: # of milliseconds to turn on LED
        :return:
        """
        on_time_ms = 400
        c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_time_ms}}
        return self._verify_single_cmd_ret(c, delay_poll=on_time_ms)

    def enable_jig_closed_detect(self, enable=True):
        c = {'method': 'enable_jig_closed_detect', 'args': {'enable': enable}}
        return self._verify_single_cmd_ret(c)

    def adc_read(self, pin, samples=1, samples_ms=1):
        c = {'method': 'adc_read', 'args': {'pin': pin, 'samples': samples, 'samples_ms': samples_ms}}
        return self._verify_single_cmd_ret(c)

    def adc_read_multi(self, pins, samples=100, freq=100):
        c = {'method': 'adc_read_multi', 'args': {'pins': pins, 'samples': samples, 'freq': freq}}
        return self._verify_single_cmd_ret(c)

