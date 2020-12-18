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

from MicroPyBoard import MicroPyBrd
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
       python3 MicroPyBoard_cli.py list      
    2) Copy file to MicroPython boards,
       python3 MicroPyBoard_cli.py -p /dev/ttyACM0 copy -f my_local_file.txt
    """
    parser = argparse.ArgumentParser(description='MicroPyBoard_cli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='serial port, required for most commands')

    subp = parser.add_subparsers(dest="cmd", help='commands')

    files_parser = subp.add_parser('files', help="List files")
    files_parser.add_argument("-d", '--dir', dest='dir', default="/flash",
                        action='store', help='set target directory')

    list_parser = subp.add_parser('list', help="List PyBoards found")

    identify_parser = subp.add_parser('identify', help="identify (blick red LED) the Pyboard on port")

    copy_parser = subp.add_parser('copy', help="copy file to PyBoard")
    copy_parser.add_argument("-d", '--dir', dest='dir', default="/flash",
                        action='store', help='set target directory')
    copy_parser.add_argument("-f", '--file', dest='file', action='store', required=True, help='file to copy')

    slot_parser = subp.add_parser('set_slot', help="set PyBoard SLOT# file")
    slot_parser.add_argument("-s", '--slot', dest='slot', action='store', required=True,
                             help='slot number, 0, 1, 2, 3')
    slot_parser.add_argument("-d", '--dir', dest='dir', default="/flash",
                        action='store', help='set target directory')

    args = parser.parse_args()

    if args.show_version:
        logging.info("Version {}".format(VERSION))
        sys.exit(0)

    if not args.cmd == 'list':
        if not args.port:
            parser.error("--port is required")

    return args


if __name__ == '__main__':
    args = parse_args()
    did_something = False

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
        logging.basicConfig(level=logging.INFO, format='%(levelname)7s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)7s %(lineno)4s %(message)s')

    pyb = MicroPyBrd(logging)

    if args.cmd == 'list':
        pyb.scan_ports()
        did_something = True

    if args.cmd == 'identify':
        pyb.open(args.port)
        logging.info("Flashing RED LED of port {}".format(args.port))
        for i in range(10): pyb.led_toggle(1)
        id = pyb.get_id()
        logging.info("port {}, id: {}".format(args.port, id))
        did_something = True

    if args.cmd == 'files':
        pyb.open(args.port)
        files_list = pyb.get_files(directory=args.dir)
        for f in files_list:
            logging.info(f)
        did_something = True

    if args.cmd == 'copy':
        pyb.open(args.port)
        pyb.copy_file(args.copy_file, directory=args.dir)
        did_something = True

    if args.cmd == 'set_slot':
        pyb.open(args.port)
        slot = pyb.set_slot(args.slot, directory=args.dir)
        logging.info("port {}, slot: {}".format(args.port, slot))
        did_something = True

    if not did_something:
        logging.info("Nothing to do... use --help for commands")

    pyb.close()
