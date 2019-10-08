#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

upybrd_cli.py:
- provides command line functions to setup a pyboard.
- does NOT use the upyboard server

"""
try:
    # for when used by Prism
    from public.prism.drivers.micropythonbrd.list_serial import serial_ports
except:
    # for when called by main
    from list_serial import serial_ports

import sys
import time
import logging
import argparse

import ampy.files as files
import ampy.pyboard as pyboard

try:
    from stublogger import StubLogger
except:
    from public.prism.drivers.micropythonbrd.stublogger import StubLogger

VERSION = "0.2.0"


class MicroPyBrd(object):
    """  Driver for the micopython board

    In Prism, this is only used for scanning ports and for using the
    CLI to do some commands... see MicroPyBoard_cli.py.

    TODO: Get rid of this class completely, should be able to use IBA01:IBA01()

    http://docs.micropython.org/en/v1.9.4/pyboard/pyboard/quickref.html

    How to use
    1) Sending commands,
         pyb = MicroPyBrd(logging)
         pyb.open(port)
         cmds = ["pyb.LED(1).on()", 'pyb.LED(1).off()']
         cmd = "\n".join(cmds)
         pyb.execbuffer(cmd)
         pyb.close()

    2) Get list of micropython boards,
         pyb = MicroPyBrd(logging)
         scan = pyb.scan_ports()
         # scan is a list of tuples, [(port, id#), (..), ..]
         pyb.close()

    LESSONS:
    1) pyb.enter_raw_repl()  # this does a softreset....!
    2) sometimes functions won't return a value, for example, pyb.freq(),
       need to wrap in a print, print(pyb.freq())
    3) References,
       http://docs.micropython.org/en/v1.9.4/pyboard/pyboard/tutorial/intro.html
       http://docs.micropython.org/en/v1.9.4/pyboard/pyboard/quickref.html
       http://docs.micropython.org/en/v1.9.3/esp8266/esp8266/tutorial/filesystem.html

    """

    BAUDRATE = 115200

    LED_RED    = 1
    LED_GREEN  = 2
    LED_YELLOW = 3
    LED_BLUE   = 4
    LED_FLASH_TIME_S = 0.5

    def __init__(self, loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()
        self.pyb = None       # handle to the pyboard
        self.serial = None    # serial port to the pyboard
        self.logger.debug("Done")

    def version(self):
        return VERSION

    def led_toggle(self, led, flash_s=LED_FLASH_TIME_S):
        self.pyb.enter_raw_repl()
        self.pyb.exec('pyb.LED({}).on()'.format(led))
        time.sleep(flash_s)
        self.pyb.exec('pyb.LED({}).off()'.format(led))
        self.pyb.exit_raw_repl()

    def uname(self):
        # get pyboard version info
        self.pyb.enter_raw_repl()
        cmds = ['import os',
                'print(os.uname())']
        cmd = "\n".join(cmds) + "\n"
        ret, _ = self.pyb.exec_raw(cmd)
        ret_string = ret.decode("utf-8").strip()
        # uname looks like: "(sysname='pyboard', nodename='pyboard', release='1.11.0', version='v1.11 on 2019-05-29', machine='PYBv1.1 with STM32F405RG')"
        # turn this into a dict
        items = list(ret_string.replace("(", "").replace(")", "").replace("'", "").split(","))
        uname = {}
        for item in items:
            key = item.split("=")[0].strip()
            value = item.split("=")[1].strip()
            uname[key] = value
        self.logger.info(uname)
        self.pyb.exit_raw_repl()
        return uname

    def scan_ports(self, port=None):
        """ Finds/validates all connected pyboards
        :return: list of pyboards, [(<port>, <ID>), ...]
        """
        ports = []
        if port: port_candidates = [port]
        else:    port_candidates = serial_ports()

        self.logger.info("Looking for Pyboard in {}".format(port_candidates))
        for port in port_candidates:
            try:
                self.pyb = pyboard.Pyboard(port)
                # visual indication we are talking to the pyboard
                self.led_toggle(self.LED_RED, self.LED_FLASH_TIME_S)
                id = self.get_id()
                if id is not None:
                    # visual indication success
                    self.led_toggle(self.LED_GREEN, self.LED_FLASH_TIME_S)
                uname = self.uname()
                self.pyb.close()
                self.pyb = None
                ports.append({"port": port, "id": id, "version": VERSION, "uname": uname})

            except Exception as e:
                self.logger.info(e)
                self.logger.info("NO micropython on {}".format(port))

        self.logger.info("Found {}".format(ports))
        return ports

    def open(self, port):
        self.logger.debug("open {}".format(port))
        self.pyb = pyboard.Pyboard(port)
        #self.pyb.enter_raw_repl()  # this does a softreset on micropython

    def close(self):
        self.logger.debug("close")
        if self.pyb: self.pyb.close()
        self.pyb = None

    def reset(self):
        self.logger.info("reset")
        self.pyb.enter_raw_repl()  # this does a softreset on micropython

    def get_files(self, directory='/flash', long_format=True, recursive=True):
        """ Get the files from an open pyboard
        :return: [ file, ...]
        """
        board_files = files.Files(self.pyb)
        files_list = [f for f in board_files.ls(directory, long_format=long_format, recursive=recursive)]
        self.logger.debug(files_list)
        return files_list

    def copy_file(self, local):
        with open(local, "rb") as infile:
            board_files = files.Files(self.pyb)
            board_files.put('/flash/{}'.format(local), infile.read())

    def del_file(self, file):
        board_files = files.Files(self.pyb)
        board_files.rm(file)
        return True

    def get_id(self):
        """ Get the id of an open pyboard
        :return: id, or None if no id on pyboard
        """
        # get pyboard version info
        self.pyb.enter_raw_repl()
        cmds = ['import machine',
                'id_bytes = machine.unique_id()',
                'res = ""',
                'for b in id_bytes:',
                ' res += "%02x" % b',
                'print(res)']
        cmd = "\n".join(cmds) + "\n"
        ret = self.pyb.exec(cmd)
        ret = ret.decode('utf-8').strip()
        self.logger.info("{}".format(ret))
        self.pyb.exit_raw_repl()
        return ret

