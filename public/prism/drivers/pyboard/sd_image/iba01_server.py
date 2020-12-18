#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019
"""
import time
import micropython

from iba01_queue import MicroPyQueue

micropython.alloc_emergency_exception_buf(100)
__DEBUG_FILE = "iba01_server"


class MicroPyServer(object):
    """ Async Worker MicroPython Server
    - runs in its own thread

    cmds: Are in this format: {"method": <class_method>, "args": {<args>}}

    ret: Are in this format: {"method": <class_method>, "value": { ...}}

    Notes:
        1) you cannot use print(), Instead, use the self._debug() API.

        2) debug new code with rshell/REPL.  'import upyb_server'
           and then execute commands,
               >>> iba01_server.server.cmd({'method': 'version', 'args': {}})
               >>> iba01_server.server.ret()

    """
    def __init__(self, debug=False):
        self._cmd = MicroPyQueue()
        self._ret = MicroPyQueue()
        self._debug_flag = debug

    # ===================================================================================
    # Public API to send commands and get results from the MicroPy Server
    #
    def cmd(self, cmd):
        """ Send (Add) a command to the MicroPy Server command queue
        - commands are executed in the order they are received

        :param cmd: dict format {"method": <class_method>, "args": {<args>}}
        :return: success (True/False)
        """
        if not isinstance(cmd, dict):
            self._ret.put({"method": "cmd", "value": "cmd must be a dict", "success": False})
            return False

        if not cmd.get("method", False):
            self._ret.put({"method": "cmd", "value": "cmd dict must have method key", "success": False})
            return False

        if not getattr(self, cmd["method"], False):
            self._ret.put({"method": "cmd", "value": "'{}' invalid method".format(cmd["method"]), "success": False})
            return False

        self._cmd.put(cmd)
        return True

    def ret(self, method=None, all=False):
        """ return result(s) of command

        :param method: string, if specified, only results of that command are returned
        :param all: True, will return all commands, otherwise only ONE return result is retrieved
        :return: success (True|False)
        """
        _ret = self._ret.get(method, all)
        print(_ret)
        return True

    def peek(self, method=None, all=False):
        """ Peek at item(s) in the queue, does not remove item(s)

        :param method:
        :param all:
        :return: success (True|False)
        """
        ret = self._ret.peek(method, all)
        print(ret)
        return True

    def update(self, item_update):
        """ Update an item in queue, or append item if it doesn't exist

        :param item_update: dict format {"method": <class_method>, "args": {<args>}}
        :return: success (True|False)
        """
        return self._ret.update(item_update)

    # ===================================================================================
    # private

    def _run(self):
        # run on thread
        while True:
            item = self._cmd.get()
            if item:
                method = item[0]["method"]
                args = item[0]["args"]
                method = getattr(self, method, None)
                if method is not None:
                    method(args)
                    # methods should always be found because they are checked before being queued

            # allows other threads to run, but generally speaking there should be no other threads(?)
            time.sleep_ms(self.SERVER_CMD_SLEEP_MS)

    def _debug(self, msg, line=0, file=__DEBUG_FILE, name="unknown"):
        """ Add debug statement

        :param msg:
        :param line:
        :return:
        """
        if self._debug_flag:
            self._ret.put({"method": "_debug", "value": "{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg), "success": True})

