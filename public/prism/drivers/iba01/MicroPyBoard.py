#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

MicroPyBoard_cli.py:
- provides command line functions to setup a pyboard.
- does NOT use the iba01_server

"""
try:
    # for when used by Prism
    from public.prism.drivers.iba01.list_serial import serial_ports
except:
    # for when called by main
    from list_serial import serial_ports

import re
import time

import ampy.files as files
import ampy.pyboard as pyboard

try:
    from stublogger import StubLogger
except:
    from public.prism.drivers.iba01.stublogger import StubLogger

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
            if "ttyACM" not in port:
                self.logger.info("NO micropython on {}".format(port))
                continue

            try:
                self.pyb = pyboard.Pyboard(port)
                # visual indication we are talking to the pyboard
                self.led_toggle(self.LED_BLUE, self.LED_FLASH_TIME_S)
                # get pyboard deets
                id = self.get_id()
                slot = self.get_slot()
                uname = self.uname()

                # TODO: detect if board is configured for IBA01, if not, should we
                #       configure it?

                self.led_toggle(self.LED_GREEN, self.LED_FLASH_TIME_S)

                self.pyb.close()
                self.pyb = None
                ports.append({"port": port, "id": id, 'slot': slot, "version": VERSION, "uname": uname})
                self.logger.info("Found micropython on {}".format(port))

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
        try:
            board_files = files.Files(self.pyb)
            files_list = [f for f in board_files.ls(directory, long_format=long_format, recursive=recursive)]
            self.logger.debug(files_list)

        except pyboard.PyboardError:
            self.logger.warning("unable to reach path: {}, micro sd card probably not available".format(directory))
            files_list = []

        return files_list

    def copy_file(self, local, directory='/flash'):
        with open(local, "rb") as infile:
            board_files = files.Files(self.pyb)
            board_files.put('{}/{}'.format(directory, local), infile.read())

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
        ret = ret.decode('utf-8').strip()[::-1]  # reverse it
        self.logger.info("{}".format(ret))
        self.pyb.exit_raw_repl()
        return ret

    def get_slot(self):
        """ Get the slot of an open pyboard

        The slot number is stored on the filesystem.  If the file is not on the internal
        filesystem, then check the microsd card.

        :return: slot #, 0,1,2,3, ..., -1 on no slot
        """
        self.pyb.enter_raw_repl()

        found_slot = False
        for path in ["/sd", "/flash"]:
            self.logger.info("Searching for SLOT# file on directory {}...".format(path))
            files = self.get_files(directory=path, long_format=False)

            for f in files:
                if "SLOT" in f:
                    found_slot = True
                    break

        if not found_slot:
            self.logger.warning("No SLOT# file found (required for Prism)")
            return -1

        m = re.match(r'^.*SLOT(?P<slot>\d)', f)
        slot = int(m.group('slot'))
        self.logger.info("{} -> {}".format(f, slot))
        return slot

    def set_slot(self, slot, directory='/flash'):
        """ Set pyboard slot number in Prism
        :param port: port of the pyboard
        :param slot: integer slot of the pyboard
        :return: -1 on fail, >=0 on success (slot number)
        """
        # remove the old ID if it exists
        self.logger.info("Removing any previous SLOT# files on directory {}".format(directory))
        files = self.get_files(directory=directory, long_format=False)
        for f in files:
            if "SLOT" in f:
                success = self.del_file(f)
                if not success:
                    self.logger.error("failed to delete file: {}".format(f))
                    return False

        self.pyb.enter_raw_repl()

        # write the new SLOT
        filename = "{}/SLOT{}".format(directory, slot)
        self.logger.info("Writing {}".format(filename))
        cmds = ["f = open('{}', 'w')".format(filename), 'f.close()']
        cmd = "\n".join(cmds) + "\n"
        ret = self.pyb.exec(cmd)
        ret = ret.decode('utf-8').strip()
        self.pyb.exit_raw_repl()
        slot = self.get_slot()
        return slot

