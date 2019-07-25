#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

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
from upybrd import pyboard2
from stublogger import StubLogger

VERSION = "0.0.1"


# Command Line Interface...

def parse_args():
    epilog = """
    Usage examples:

       
    """
    parser = argparse.ArgumentParser(description='upybrd_cli_server',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='Active serial port')

    parser.add_argument("-1", '--test-1', dest='test_1',
                        action='store_true', help='test code, blink led')
    parser.add_argument("-2", '--test-2', dest='test_2',
                        action='store_true', help='test code, blink led check result later')
    parser.add_argument("-3", '--test-3', dest='test_3',
                        action='store_true', help='test code, blink led check result later')
    parser.add_argument("-4", '--test-4', dest='test_4',
                        action='store_true', help='test code, blink led check result later')
    parser.add_argument("-5", '--test-5', dest='test_5',
                        action='store_true', help='test code, adc read')
    parser.add_argument("-6", '--test-6', dest='test_6',
                        action='store_true', help='test code, adc multi read')

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    args = parser.parse_args()

    if args.show_version:
        logging.info("Version {}".format(VERSION))
        sys.exit(0)

    if not args.port:
        parser.error("--port is required")

    return args


if __name__ == '__main__':
    args = parse_args()
    did_something = False

    pyb = None
    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(levelname)6s %(lineno)4s %(message)s')
        pyb = pyboard2(args.port)

    else:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)6s %(lineno)4s %(message)s')
        pyb = pyboard2(args.port, loggerIn=logging) # verbose version


    if args.test_1:
        # This is an example of how to execute non-blocking, long running async task

        cmds = [
            "import upyb_server_01",
            "upyb_server_01.server.cmd({{'method': 'led_toggle', 'args': {{ 'led': {} }} }})".format(pyb.LED_RED),
        ]

        success, result = pyb.server_cmd(cmds, repl_enter=True, repl_exit=False)
        logging.info("{} {}".format(success, result))

        cmds = ["upyb_server_01.server.ret(method='led_toggle')"]

        retry = 5
        succeeded = False
        while retry and not succeeded:
            success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
            logging.info("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == 'led_toggle' and r.get("value", False) == True:
                        succeeded = True
            retry -= 1

        did_something = True

    if args.test_2:
        # This is an example of how to execute non-blocking, long running async task
        # This shows special case of 1, as the 'toggle_led' result is not posted until
        # after the led blinks, so here the first server.ret() does not get the expected
        # result and polling starts...
        pyb = pyboard2(args.port)

        cmds = [
            "import upyb_server_01",
            "upyb_server_01.server.cmd({{'method': 'led_toggle', 'args': {{ 'led': {} }} }})".format(pyb.LED_RED),
            "upyb_server_01.server.ret()",
        ]

        success, result = pyb.server_cmd(cmds, repl_exit=False)
        logging.info("{} {}".format(success, result))

        cmds = ["upyb_server_01.server.ret()"]

        retry = 5
        succeeded = False
        while retry and not succeeded:
            success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
            logging.info("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == 'led_toggle' and r.get("value", False) == True:
                        succeeded = True
            retry -= 1

        did_something = True

    if args.test_3:
        pyb = pyboard2(args.port)

        success = pyb.start_server()
        if success:
            success, result = pyb.led_toggle(2, 200)
            logging.info("{} {}".format(success, result))
        else:
            logging.error("Unable to start server")

        did_something = True

    if args.test_4:
        #pyb = pyboard2(args.port, loggerIn=logging) # verbose version
        pyb = pyboard2(args.port)

        success = pyb.start_server()
        logging.info("{}".format(success))
        if success:
            logging.info("- Turning on Jig Closed Detect...")
            success, result = pyb.enable_jig_closed_detect()
            logging.info("{} {}".format(success, result))

            logging.info("= Turning it on again...")
            success, result = pyb.enable_jig_closed_detect()
            logging.info("{} {}".format(success, result))

            # for fun, try and ask for more results, while the jig closed timer is running
            cmds = ["upyb_server_01.server.ret(all=True)"]
            retry = 20
            succeeded = False
            while retry and not succeeded:
                success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
                logging.info("{} {}".format(success, result))
                retry -= 1
                time.sleep(0.5)

            # turn off the jig closed
            logging.info("= Turn OFF jig closed timer...")
            success, result = pyb.enable_jig_closed_detect(False)
            logging.info("{} {}".format(success, result))

            # read the server queue a few times to confirm there are no new events...
            retry = 5
            succeeded = False
            while retry and not succeeded:
                success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
                logging.info("{} {}".format(success, result))
                retry -= 1
                time.sleep(0.5)

        else:
            logging.error("Unable to start server")

        did_something = True

    if args.test_5:
        #pyb = pyboard2(args.port, loggerIn=logging) # verbose version
        pyb = pyboard2(args.port)

        success = pyb.start_server()
        logging.info("{}".format(success))
        if success:
            logging.info("Reading ADC...")
            success, result = pyb.adc_read("VREF")
            logging.info("{} {}".format(success, result))

        else:
            logging.error("Unable to start server")

        did_something = True

    if args.test_6:
        #pyb = pyboard2(args.port, loggerIn=logging) # verbose version
        pyb = pyboard2(args.port)

        success = pyb.start_server()
        logging.info("{}".format(success))
        if success:
            logging.info("Reading (multi) ADC...")
            success, result = pyb.adc_read_multi(pins=["X19", "X20"])
            logging.info("{} {}".format(success, result))
            success, result = pyb.get_server_method("adc_read_multi_results")
            logging.info("{} {}".format(success, result))

        else:
            logging.error("Unable to start server")

        did_something = True

    pyb.close()

    if not did_something:
        logging.info("Nothing to do... use --help for commands")
