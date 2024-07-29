#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

This CLI provides a linux CLI interface to Fake.
Use this CLI to test your hardware driver.

Example:  (note the starting folder)
~/git/scripts/public/prism/drivers/ble_listener$ python3 blelistener_cli.py scan -t 30
  blelistener_cli.py   INFO   75 Scanning for 30 seconds...
      BLEListener.py   INFO   62 Starting scanner with 0.5 seconds
      BLEListener.py   INFO   86 uuids: ['abbaff00-e56a-484c-b832-8b17cf6cbfe8']
      BLEListener.py   INFO   98 1 items
  blelistener_cli.py   INFO   78 Ending scanning...
      BLEListener.py   INFO  135 closing...
  blelistener_cli.py   INFO  104 Success
      BLEListener.py   INFO  135 closing...
      BLEListener.py   INFO   73 BLE_LISTENER closed
      BLEListener.py   INFO  145 async completed

"""
import time
import logging
import argparse
from BLEListener import BLEListener

# global Fake object
ble_listener = None


def parse_args():
    epilog = """
    Usage examples:
       python3 blelistener_cli.py version

    Getting Help for a command:
    $ python3 blelistener_cli.py version --help
      
    """
    parser = argparse.ArgumentParser(description='blelistener_cli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')

    subp = parser.add_subparsers(dest="_cmd", help='commands')

    uid_parser = subp.add_parser('uid')

    version_parser = subp.add_parser('version')

    scan_parser = subp.add_parser('scan')
    scan_parser.add_argument("-t", '--time', dest='time', default=10.0, action='store', help='Time to scan in seconds')

    args = parser.parse_args()
    return args


def uid(args):
    logging.info("uid: {}".format(args))
    response = ble_listener.unique_id()
    logging.info("{}".format(response))
    return True


def version(args):
    logging.info("version: {}".format(args))
    response = ble_listener.version()
    logging.info("{}".format(response))
    return True


def scan(args):
    logging.info(f"Scanning for {args.time} seconds...")
    ble_listener.start_scanner()
    time.sleep(float(args.time))
    logging.info("Ending scanning...")
    ble_listener.close()
    return True


if __name__ == '__main__':
    args = parse_args()
    exit_code = 0

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')

    ble_listener = BLEListener(loggerIn=logging)

    if args._cmd == 'uid':
        success = uid(args)

    elif args._cmd == 'version':
        success = version(args)

    elif args._cmd == 'scan':
        success = scan(args)

    if success:
        logging.info("Success")

    else:
        logging.error("Failed")
        exit_code = 1

    if ble_listener:
        ble_listener.close()

    exit(exit_code)
