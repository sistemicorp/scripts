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
import os
import time
import logging
import argparse

import ampy.files as files
import ampy.pyboard as pyboard

try:
    from stublogger import StubLogger
except:
    from public.prism.drivers.micropythonbrd.stublogger import StubLogger

VERSION = "0.0.1"


class MicroPyBrd(object):
    """  Driver for the micopython board

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

         Note: if id is None, then the board doesn't have an id assigned to it.
               Expect every pyboard in the system to have a different id (integer)

    3) Set the ID of the pyboard
        The ID is an identifier for the pyboard, so when you have multiple
        pyboards they can be identified.  When a pyboard ID has been set, that pyboard
        should be labelled with that ID number, so the operator can know which one it is.

        Use the Command Line Interface (CLI),
         python upybrd.py --port COM3 --set-id 1

        or, programmatically,
         pyb = MicroPyBrd(logging)
         pyb.set_pyb_id(<port>, <id>)
         pyb.close()

    Design:
    1) The id of the pyboard is a empty file in form of ID<#>

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
        files = self.get_files()
        for f in files:
            if f.startswith("/flash/ID"):
                # from: /flash/ID2 - 3 bytes -> extract the ID value of 2
                channel = int(f.split(" ")[0].split('/flash/ID')[1])
                return channel
        return None

    def set_pyb_id(self, port, id):
        """ Set (assign) the pyboard ID
        :param port: port of the pyboard
        :param id: integer ID of the pyboard
        :return: True on success, False otherwise
        """
        if not self.pyb:
            # make sure the port is valid
            port_candidates = serial_ports()
            if not port in port_candidates:
                self.logger.error("{} NOT in available ports {}".format(port, port_candidates))
                return False

            # scan the port, make sure its a pyboard
            current_configs = self.scan_ports(port)
            valid_port = False
            for cfg in current_configs:
                if cfg["port"] == port:
                    valid_port = True
                    break
            if not valid_port:
                self.logger.error("{} is not a valid micropython port".format(port))
                return False

            # ok, should be good, open that port
            self.open(port)

        board_files = files.Files(self.pyb)

        # remove the old ID if it exists
        files_list = self.get_files()
        for f in files_list:
            if f.startswith("/flash/ID"):
                # file list format looks like, '/flash/ID1 - 3 bytes'
                self.logger.info("removing ID: {}".format(f))
                board_files.rm(f.split(" ")[0])

        # create a dummy local file with contents
        fname = 'ID{}'.format(id)
        with open("dummy", "w") as f:
            f.write(fname)

        try:
            self.logger.info("Setting ID: {}".format(fname))
            with open("dummy", "rb") as infile:
                board_files.put('/flash/{}'.format(fname), infile.read())

            os.remove('dummy')
            return True

        except Exception as e:
            self.logger.error(e)
            return False


# Command Line Interface...

def parse_args():
    epilog = """
    Usage examples:
    1) List all MicroPython boards attached to the system,
       python3 upybrd_cli.py --list
    2) Setting the ID to 1 for the MicroPython board on COM3, 
       python3 upybrd_cli.py --port COM3 --set-id 1
       
    """
    parser = argparse.ArgumentParser(description='upybrd',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='Active serial port')

    parser.add_argument("-s", '--set-id', dest='set_id', default=None, type=int,
                        action='store', help='Set channel <#> to <port>, ex: -s 0 -p COM3')

    parser.add_argument("-l", '--list', dest='list', default=False,
                        action='store_true', help='list micropython boards')

    parser.add_argument("-i", '--identify', dest='identify', default=False,
                        action='store_true', help='blink red LED on specified port')

    parser.add_argument("-f", '--files', dest='files', default=False,
                        action='store_true', help='List files on pyboard')

    parser.add_argument("-c", '--copy', dest='copy_file',
                        action='store', help='copy local file to pyboard /flash')

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    args = parser.parse_args()

    if args.show_version:
        logging.info("Version {}".format(VERSION))
        sys.exit(0)

    if not args.list:
        if not args.port:
            parser.error("--port is required")

    return args


if __name__ == '__main__':
    args = parse_args()
    did_something = False

    #
    # see the class MicroPyBrd comments for how to set the ID of a micropython board
    # Examples,
    #  python upybrd.py -l
    #   INFO  129 Looking for Pyboard in ['COM1', 'COM4', 'COM6']
    #   INFO  158 NO micropython on COM1
    #   INFO  158 NO micropython on COM4
    #   INFO  143 Found micropython on COM6
    #   INFO  164 open COM6
    #   INFO  160 Found [{'port': 'COM6', 'id': 2, 'version': '0.0.1'}]
    #
    # python upybrd.py -p COM5 -f
    #   INFO  164 open COM5
    #   INFO  382 ['main.py', 'pybcdc.inf', 'README.txt', 'boot.py', 'System Volume Information', 'ID1']

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)6s %(lineno)4s %(message)s')

    if args.list:
        pyb = MicroPyBrd(logging)
        pyb.scan_ports()
        pyb.close()
        did_something = True

    if args.set_id is not None:
        pyb = MicroPyBrd(logging)
        pyb.set_pyb_id(args.port, args.set_id)
        pyb.close()
        did_something = True

    if args.identify:
        pyb = MicroPyBrd(logging)
        pyb.open(args.port)
        logging.info("Flashing RED LED of port {}".format(args.port))
        for i in range(10):
            pyb.led_toggle(1)

        pyb.close()
        did_something = True

    if args.files:
        pyb = MicroPyBrd(logging)
        pyb.open(args.port)
        files_list = pyb.get_files()
        for f in files_list:
            logging.info(f)
        pyb.close()
        did_something = True

    if args.copy_file:
        pyb = MicroPyBrd(logging)
        pyb.open(args.port)
        pyb.copy_file(args.copy_file)
        pyb.close()
        did_something = True

    if not did_something:
        logging.info("Nothing to do... use --help for commands")
