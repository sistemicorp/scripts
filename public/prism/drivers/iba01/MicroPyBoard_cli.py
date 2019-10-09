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

from MicorPyBoard import MicroPyBrd
import sys
import logging
import argparse


try:
    from stublogger import StubLogger
except:
    from public.prism.drivers.micropythonbrd.stublogger import StubLogger

VERSION = "0.0.1"


# Command Line Interface...

def parse_args():
    epilog = """
    Usage examples:
    1) List all MicroPython boards attached to the system,
       python3 upybrd_cli.py --list      
    2) Copy file to MicroPython boards,
       python3 upybrd_cli.py -p /dev/ttyACM0 --copy upyb_i2c.py
    """
    parser = argparse.ArgumentParser(description='upybrd',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='Active serial port')

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
