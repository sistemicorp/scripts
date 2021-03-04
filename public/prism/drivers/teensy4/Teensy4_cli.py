#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

This CLI provides a linux CLI interface to Teensy4 SimpleRPC.

"""
import sys
import time
import logging
import argparse

from Teensy4 import Teensy4

VERSION = "0.1.0"


# Command Line Interface...

def parse_args():
    epilog = """
    Usage examples:
       python3 teensy4_cli.py --port /dev/ttyACM0 led --on
       python Teensy4_cli.py --port COM5 led --on
    """
    parser = argparse.ArgumentParser(description='teensy4_cli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='Active serial port', required=True)

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    subp = parser.add_subparsers(dest="_cmd", help='commands')
    led_toggle_parser = subp.add_parser('led')
    led_toggle_parser.add_argument('--on',  dest="_on", action='store_true', help='led on', default=False, required=False)
    led_toggle_parser.add_argument('--off', dest="_off", action='store_true', help='led off', default=False, required=False)

    args = parser.parse_args()

    if args.show_version:
        logging.info("Version {}".format(VERSION))
        sys.exit(0)

    return args


def led(args, teensy):
    _success = True
    logging.info("led: {}".format(args))

    if args._on:
        logging.info("ON: turn on LED")

        response = teensy.led(True)
        success = response["success"]
        logging.info("{}".format(response))
        if not success: _success = False

    if args._off:
        logging.info("OFF: turn off LED")

        result = teensy.led(False)
        logging.info("{} {}".format(success, result))
        if not success: _success = False

    return _success




if __name__ == '__main__':
    args = parse_args()
    

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')

    teensy = Teensy4(args.port, loggerIn=logging)

    success = teensy.init()
    if not success:
        logging.error("Failed to create teensy instance")
        exit(1)

    if args._cmd == 'led':
        success = led(args, teensy)
        if not success:
            logging.error("Failed testing led")
            teensy.close()
            exit(1)

    logging.info("all tests passed")
    teensy.close()

