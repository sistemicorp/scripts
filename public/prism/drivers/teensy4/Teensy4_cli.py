#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2023
Owen Li, Martin Guthrie

This CLI provides a linux CLI interface to Teensy4 SimpleRPC.

Example:  (note the starting folder)

martin@martin-staric2:~/git/scripts/public/prism/drivers/teensy4$ python3 Teensy4_cli.py --port /dev/ttyACM0 read_gpio --pin-number 2
          Teensy4.py   INFO   78 version 0.1.0
          Teensy4.py   INFO   87 attempting to install Teensy on port /dev/ttyACM0
          Teensy4.py   INFO  176 Jig Closed Detector not defined (None)
          Teensy4.py   INFO  113 Installed Teensy on port /dev/ttyACM0
      Teensy4_cli.py   INFO  161 read_gpio: Namespace(port='/dev/ttyACM0', verbose=0, _cmd='read_gpio', _pin_number=2)
      Teensy4_cli.py   INFO  165 {'success': True, 'method': 'read_gpio', 'result': {'state': 1}}
      Teensy4_cli.py   INFO  202 Success
          Teensy4.py   INFO  124 closing /dev/ttyACM0


"""
import logging
import argparse

from Teensy4 import Teensy4

# global teensy object
teensy = None


def parse_args():
    epilog = """
    Usage examples:
       python3 teensy4_cli.py --port /dev/ttyACM0 led --on

    Port: Teensy4 when plugged into USB on Linux will show up as a ttyACM# device in /dev.
          Use 'ls -al /dev/ttyACM*' to find the port. 
          
    Getting Help for a command:
    $ python3 Teensy4_cli.py --port /dev/ttyACM0 write_gpio --help
    usage: Teensy4_cli.py write_gpio [-h] --pin-number _PIN_NUMBER --state {True,False}

    options:
    -h, --help            show this help message and exit
    --pin-number _PIN_NUMBER
                        GPIO number (0-41)
    --state {True,False}  True|False
      
    Example:
    $ python3 Teensy4_cli.py --port /dev/ttyACM0 write_gpio --pin-number 2 --state False
          Teensy4.py   INFO   78 version 0.1.0
          Teensy4.py   INFO   87 attempting to install Teensy on port /dev/ttyACM0
          Teensy4.py   INFO  176 Jig Closed Detector not defined (None)
          Teensy4.py   INFO  113 Installed Teensy on port /dev/ttyACM0
      Teensy4_cli.py   INFO  116 write_gpio: Namespace(port='/dev/ttyACM0', verbose=0, _cmd='write_gpio', _pin_number=2, _state='False')
      Teensy4_cli.py   INFO  123 {'success': True, 'method': 'write_gpio', 'result': {'state': False}}
      Teensy4_cli.py   INFO  157 Success
          Teensy4.py   INFO  124 closing /dev/ttyACM0   
    """
    parser = argparse.ArgumentParser(description='teensy4_cli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str, required=True,
                        action='store', help='Active serial port')

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')

    subp = parser.add_subparsers(dest="_cmd", help='commands')

    led_toggle_parser = subp.add_parser('led')
    led_toggle_parser.add_argument('--on',  dest="_on", action='store_true', help='led on', default=False, required=False)
    led_toggle_parser.add_argument('--off', dest="_off", action='store_true', help='led off', default=False, required=False)

    uid_parser = subp.add_parser('uid')

    version_parser = subp.add_parser('version')

    write_gpio = subp.add_parser('write_gpio')
    write_gpio.add_argument('--pin-number', dest="_pin_number", action='store', type=int, help='GPIO number (0-41)',
                            default=None, required=True)
    write_gpio.add_argument('--state', dest="_state", choices=('1', '0'), help='True|False', required=True)

    read_gpio = subp.add_parser('read_gpio')
    read_gpio.add_argument('--pin-number', dest="_pin_number", action='store', type=int, help='GPIO number (0-41)',
                            default=None, required=True)


    # add new commands here...

    args = parser.parse_args()
    return args


def led(args):
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

        response = teensy.led(False)
        success = response["success"]
        logging.info("{}".format(response))
        if not success: _success = False

    return _success


def uid(args):
    _success = True
    logging.info("uid: {}".format(args))

    response = teensy.unique_id()
    success = response["success"]
    logging.info("{}".format(response))
    if not success: _success = False

    return success


def version(args):
    _success = True
    logging.info("version: {}".format(args))

    response = teensy.version()
    success = response["success"]
    logging.info("{}".format(response))
    if not success: _success = False

    return success


def write_gpio(args):
    _success = True
    logging.info("write_gpio: {}".format(args))

    _state = True
    if args._state == '0': _state = False

    response = teensy.write_gpio(args._pin_number, _state)
    success = response["success"]
    logging.info("{}".format(response))
    if not success: _success = False

    return success


def read_gpio(args):
    _success = True
    logging.info("read_gpio: {}".format(args))

    response = teensy.read_gpio(args._pin_number)
    success = response["success"]
    logging.info("{}".format(response))
    if not success: _success = False

    return success


if __name__ == '__main__':
    args = parse_args()
    exit_code = 0

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
        success = led(args)

    elif args._cmd == 'uid':
        success = uid(args)

    elif args._cmd == 'version':
        success = version(args)

    elif args._cmd == 'write_gpio':
        success = write_gpio(args)

    elif args._cmd == 'read_gpio':
        success = read_gpio(args)

    if success:
        logging.info("Success")

    else:
        logging.error("Failed")
        exit_code = 1

    teensy.close()
