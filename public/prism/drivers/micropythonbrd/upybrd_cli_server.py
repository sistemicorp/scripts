#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import sys
import time
import logging
import argparse

from upybrd import pyboard2

VERSION = "0.0.1"


# Command Line Interface...

def parse_args():
    epilog = """
    Usage examples:
       python3 upybrd_cli_server.py --port /dev/ttyACM0 adc -1
       python3 upybrd_cli_server.py --port /dev/ttyACM0 adc --all      
    """
    parser = argparse.ArgumentParser(description='upybrd_cli_server',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='Active serial port')
    parser.add_argument("-a", '--all', dest='all_funcs', default=0, action='store_true', help='run all tests')

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    subp = parser.add_subparsers(dest="_cmd", help='commands')
    led_toggle_parser = subp.add_parser('led_toggle')
    led_toggle_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    led_toggle_parser.add_argument('-1', dest="t1", action='store_true', help='toggle led using server.cmd', default=False, required=False)
    led_toggle_parser.add_argument('-2', dest="t2", action='store_true', help='toggle led using wrapper API', default=False, required=False)

    #subp1 = parser.add_subparsers(dest="jig_closed", help='jig_closed')
    jig_closed_parser = subp.add_parser('jig_closed')
    jig_closed_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    jig_closed_parser.add_argument('-1', dest="t1", action='store_true', help='start jig closed, and poll', default=False, required=False)

    #subp2 = parser.add_subparsers(dest="adc", help='adc')
    adc_parser = subp.add_parser('adc')
    adc_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    adc_parser.add_argument('-1', dest="t1", action='store_true', help='adc_read', default=False, required=False)
    adc_parser.add_argument('-2', dest="t2", action='store_true', help='adc_read_multi', default=False, required=False)

    args = parser.parse_args()

    if args.show_version:
        logging.info("Version {}".format(VERSION))
        sys.exit(0)

    if not args.port:
        parser.error("--port is required")

    return args


def test_led_toggle(args, pyb):
    did_something = False
    _all = False
    if args._cmd == "led_toggle": _all = args.all
    all = args.all_funcs or _all
    _success = True
    logging.info("test_led_toggle:")

    if all or args.t1:
        # This is an example of how to execute non-blocking, long running async task
        # using the server.cmd({}) interface
        did_something = True
        logging.info("T1: Toggle Red LED with raw commands...")

        cmds = ["upyb_server_01.server.cmd({{'method': 'led_toggle', 'args': {{ 'led': {} }} }})".format(pyb.LED_RED)]

        success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
        logging.info("{} {}".format(success, result))

        cmds = ["upyb_server_01.server.ret(method='led_toggle')"]

        retry = 5
        succeeded = False
        while retry and not succeeded:
            time.sleep(0.5)
            success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
            logging.info("{} {}".format(success, result))
            if success:
                for r in result:
                    if r.get("method", False) == 'led_toggle' and r.get("value", False) == True:
                        succeeded = True
            retry -= 1

        if _success and not success: _success = False

        cmds = ["upyb_server_01.server.cmd({{'method': 'led_toggle', 'args': {{ 'led': {}, 'on_ms': 0 }} }})".format(pyb.LED_RED)]

        success, result = pyb.server_cmd(cmds, repl_enter=False, repl_exit=False)
        logging.info("{} {}".format(success, result))

    if all or args.t2:
        did_something = True
        logging.info("T2: Toggle Red LED with wrapper API...")

        success, result = pyb.led_toggle(2, 200)
        logging.info("{} {}".format(success, result))
        if _success and not success: _success = False

        time.sleep(5)  # let the led toggle for a bit

        success, result = pyb.led_toggle(2, 0)
        logging.info("{} {}".format(success, result))
        if _success and not success: _success = False

    if did_something: return _success
    else: logging.error("No Tests were specified")
    return False


def test_jig_closed(args, pyb):
    did_something = False
    _all = False
    if args._cmd == "jig_closed": _all = args.all
    all = args.all_funcs or _all
    _success = True
    logging.info("test_jig_closed:")

    if all or args.t1:
        did_something = True

        logging.info("T1: Turning on Jig Closed Detect...")
        success, result = pyb.enable_jig_closed_detect()
        logging.info("{} {}".format(success, result))

        logging.info("Turning it on again...")
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
        logging.info("Turn OFF jig closed timer...")
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

        if _success and not success: _success = False

    if did_something: return _success
    else: logging.error("No Tests were specified")
    return False


def test_adc(args, pyb):
    did_something = False
    _all = False
    if args._cmd == "adc": _all = args.all
    all = args.all_funcs or _all
    _success = True
    logging.info("test_adc:")

    if all or args.t1:
        did_something = True
        logging.info("T1: Reading ADC...")
        success, result = pyb.adc_read("VREF")
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t2:
        did_something = True

        logging.info("T2: Reading (multi) ADC...")
        success, result = pyb.adc_read_multi(pins=["X19", "X20"])
        logging.info("{} {}".format(success, result))
        success, result = pyb.get_server_method("adc_read_multi_results")
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if did_something: return _success
    else: logging.error("No Tests were specified")
    return False


if __name__ == '__main__':
    args = parse_args()
    all_funcs = args.all_funcs

    pyb = None
    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(levelname)6s %(lineno)4s %(message)s')
        pyb = pyboard2(args.port)

    else:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)6s %(lineno)4s %(message)s')
        pyb = pyboard2(args.port, loggerIn=logging) # verbose version

    success, result = pyb.start_server()
    if not success:
        logging.error("Unable to start server")
        pyb.close()
        exit(1)

    if args._cmd == 'led_toggle' or all_funcs:
        success = test_led_toggle(args, pyb)
        if not success:
            logging.error("Failed testing led_toggle")
            pyb.close()
            exit(1)

    if args._cmd == "jig_closed" or all_funcs:
        success = test_jig_closed(args, pyb)
        if not success:
            logging.error("Failed testing jig_closed")
            pyb.close()
            exit(1)

    if args._cmd == "adc" or all_funcs:
        success = test_adc(args, pyb)
        if not success:
            logging.error("Failed testing adc")
            pyb.close()
            exit(1)

    pyb.close()

