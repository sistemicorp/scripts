#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

This CLI provides a linux CLI interface to the MicroPyBoard "server".

In order for this to work, all ther iba01_*.py files must be copied onto the
MicroPyBoard.

Originally this was/is intended to be Unit Tests for the IBA01 APIs.

"""
import sys
import time
import logging
import argparse

from IBA01 import IBA01
from sd_image.iba01_const import *

VERSION = "0.2.0"


# Command Line Interface...

def parse_args():
    epilog = """
    Usage examples:
       python3 IBA01_cli.py --port /dev/ttyACM0 adc --100
       python3 IBA01_cli.py --port /dev/ttyACM0 adc --all      
       python3 IBA01_cli.py --port /dev/ttyACM0 supplies --all      
    """
    parser = argparse.ArgumentParser(description='IBA01_cli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-p", '--port', dest='port', default=None, type=str,
                        action='store', help='Active serial port')
    parser.add_argument("-a", '--all', dest='all_funcs', default=0, action='store_true', help='run all tests')

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("-d", '--debug', dest='debug', default=False, action='store_true', help='Enable debug prints on pyboard')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    subp = parser.add_subparsers(dest="_cmd", help='commands')
    led_toggle_parser = subp.add_parser('led_toggle')
    led_toggle_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    led_toggle_parser.add_argument('--100', dest="t100", action='store_true', help='toggle led using server.cmd', default=False, required=False)
    led_toggle_parser.add_argument('--101', dest="t101", action='store_true', help='toggle led using wrapper API', default=False, required=False)
    led_toggle_parser.add_argument('--102', dest="t102", action='store_true', help='toggle led using wrapper API only once', default=False, required=False)

    jig_closed_parser = subp.add_parser('jig_closed')
    jig_closed_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    jig_closed_parser.add_argument('--100', dest="t100", action='store_true', help='get jig closed status', default=False, required=False)

    adc_parser = subp.add_parser('adc')
    adc_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    adc_parser.add_argument('--100', dest="t100", action='store_true', help='adc_read', default=False, required=False)
    adc_parser.add_argument('--200', dest="t200", action='store_true', help='adc_read_multi', default=False, required=False)

    pwm_parser = subp.add_parser('pwm')
    pwm_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    pwm_parser.add_argument('--100', dest="t100", action='store_true', help='PWM on Y1', default=False, required=False)

    misc_parser = subp.add_parser('misc')
    misc_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially', default=False, required=False)
    misc_parser.add_argument('--100', dest="t100", action='store_true', help='unique id', default=False, required=False)
    misc_parser.add_argument('--101', dest="t101", action='store_true', help='slot number', default=False, required=False)
    misc_parser.add_argument('--200', dest="t200", action='store_true', help='pyboard server version and uname', default=False, required=False)
    misc_parser.add_argument('--300', dest="t300", action='store_true', help='reset', default=False, required=False)
    misc_parser.add_argument('--400', dest="t400", action='store_true', help='Relay V12 Toggle', default=False, required=False)
    misc_parser.add_argument('--401', dest="t401", action='store_true', help='Relay VSYS Toggle', default=False, required=False)
    misc_parser.add_argument('--402', dest="t402", action='store_true', help='Relay VBAT Toggle', default=False, required=False)
    misc_parser.add_argument('--500', dest="t500", action='store_true', help='Init GPIO Y1 PP', default=False, required=False)
    misc_parser.add_argument('--501', dest="t501", action='store_true', help='Init GPIO X12 Input Pull-UP', default=False, required=False)

    supplies_parser = subp.add_parser('supplies')
    supplies_parser.add_argument('-a', "--all", dest="all", action='store_true', help='run all tests sequentially',
                             default=False, required=False)
    supplies_parser.add_argument('--100', dest="t100", action='store_true', help='set V1 supply, 1800, 2700 mV', default=False, required=False)
    supplies_parser.add_argument('--101', dest="t101", action='store_true', help='Get V1 supply current @1800mV (no load)', default=False, required=False)
    supplies_parser.add_argument('--200', dest="t200", action='store_true', help='set V2 supply, 1800, 2700 mV', default=False, required=False)
    supplies_parser.add_argument('--201', dest="t201", action='store_true', help='Get V2 supply current @1800mV (no load)', default=False, required=False)

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

    if all or args.t100:
        # This is an example of how to execute non-blocking, long running async task
        # using the server.cmd({}) interface
        did_something = True
        logging.info("T100: Toggle Red LED with raw commands...")

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

    if all or args.t101:
        did_something = True
        logging.info("T101: Toggle Red LED with wrapper API...")

        success, result = pyb.led_toggle(2, 200)
        logging.info("{} {}".format(success, result))
        if _success and not success: _success = False

        time.sleep(5)  # let the led toggle for a bit

        success, result = pyb.led_toggle(2, 0)
        logging.info("{} {}".format(success, result))
        if _success and not success: _success = False

    if all or args.t102:
        did_something = True
        logging.info("T102: Toggle Orange LED with wrapper API for 1.5 sec ON")

        success, result = pyb.led_toggle(3, 1500, once=True)
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

    if all or args.t100:
        did_something = True

        logging.info("T100: Get Jig Closed Detect...")
        success, result = pyb.jig_closed_detect()
        logging.info("{} {}".format(success, result))

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

    if all or args.t100:
        did_something = True
        logging.info("T100: Reading ADC...")
        success, result = pyb.adc_read("VREF")
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t200:
        did_something = True

        logging.info("T200: Reading (multi) ADC...")
        success, result = pyb.adc_read_multi(pins=["X19", "X20"])
        logging.info("{} {}".format(success, result))
        success, result = pyb.get_server_method("adc_read_multi_results")
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if did_something: return _success
    else: logging.error("No Tests were specified")
    return False


def test_pwm(args, pyb):
    did_something = False
    _all = False
    if args._cmd == "pwm": _all = args.all
    all = args.all_funcs or _all
    _success = True
    logging.info("test_pwm:")

    if all or args.t100:
        did_something = True
        logging.info("T100: PWM on Y1")
        success, result = pyb.init_gpio("foo", "Y1", PYB_PIN_OUT_PP, PYB_PIN_PULLNONE)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed")

        success, result = pyb.pwm("foo", "foo", 8, 1, 1000, 50)
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False


    if did_something: return _success
    else: logging.error("No Tests were specified")
    return False


def test_supplies(args, pyb):
    did_something = False
    _all = False
    if args._cmd == "supplies": _all = args.all
    all = args.all_funcs or _all
    _success = True
    logging.info("test_supplies:")

    if all or args.t100:
        did_something = True
        logging.info("T100: Setting V1 to 1800")
        success, result = pyb.supply_enable("V1", enable=True, voltage_mv=1800, cal=True)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to set voltage")

        logging.info("T100: Setting V1 to 2700")
        # this test should fail
        success, result = pyb.supply_enable("V1", voltage_mv=2700)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to set voltage")

        _, _ = pyb.supply_enable("V1", enable=False)
        if _success and not success: _success = False

    if all or args.t101:
        did_something = True
        logging.info("T101: Setting V1 to 1800")
        success, result = pyb.supply_enable("V1", enable=True, voltage_mv=1800, cal=True)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to set voltage")

        success, result = pyb.supply_current("V1")
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to measure current")

        _, _ = pyb.supply_enable("V1", enable=False)
        if _success and not success: _success = False

    if all or args.t200:
        did_something = True
        logging.info("T200: Setting V2 to 1800")
        success, result = pyb.supply_enable("V2", enable=True, voltage_mv=1800, cal=True)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to set voltage")

        logging.info("2100: Setting V2 to 2700")
        # this test should fail
        success, result = pyb.supply_enable("V2", voltage_mv=2700)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to set voltage")

        _, _ = pyb.supply_enable("V2", enable=False)
        if _success and not success: _success = False

    if all or args.t201:
        did_something = True
        logging.info("T101: Setting V2 to 1800")
        success, result = pyb.supply_enable("V2", enable=True, voltage_mv=1800, cal=True)
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to set voltage")

        success, result = pyb.supply_current("V2")
        logging.info("{} {}".format(success, result))
        if _success and not success:
            _success = False
            logging.error("failed to measure current")

        _, _ = pyb.supply_enable("V2", enable=False)
        if _success and not success: _success = False

    if did_something: return _success
    else: logging.error("No Tests were specified")
    return False


def test_misc(args, pyb):
    did_something = False
    _all = False
    if args._cmd == "adc": _all = args.all
    all = args.all_funcs or _all
    _success = True
    logging.info("test_misc:")

    if all or args.t100:
        did_something = True
        logging.info("T100: Reading unique id...")
        success, result = pyb.unique_id()
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t101:
        did_something = True
        logging.info("T101: Reading slot number...")
        success, result = pyb.slot()
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t200:
        did_something = True
        logging.info("T200: Reading version and uname...")
        success, result = pyb.version()
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t300:
        did_something = True
        logging.info("T300: Resetting...")
        success, result = pyb.reset()
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t400:
        did_something = True
        logging.info("T400: Toggle Relay V12...")
        success, result = pyb.relay_v12()
        logging.info("{} {}".format(success, result))
        success, result = pyb.relay_v12(connect=False)
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t401:
        did_something = True
        logging.info("T401: Toggle Relay VSYS...")
        success, result = pyb.relay_vsys()
        logging.info("{} {}".format(success, result))
        success, result = pyb.relay_vsys(connect=False)
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t402:
        did_something = True
        logging.info("T402: Toggle Relay VBAT...")
        success, result = pyb.relay_vbat()
        logging.info("{} {}".format(success, result))
        success, result = pyb.relay_vbat(connect=False)
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t500:
        did_something = True
        logging.info("T500: init GPIO Y1...")
        success, result = pyb.init_gpio("foo", "Y1", PYB_PIN_OUT_PP, PYB_PIN_PULLNONE)
        logging.info("{} {}".format(success, result))

        if _success and not success: _success = False

    if all or args.t501:
        did_something = True
        logging.info("T501: init GPIO X12...")
        success, result = pyb.init_gpio("X12", "X12", PYB_PIN_IN, PYB_PIN_PULLUP)
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
        logging.basicConfig(level=logging.INFO, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')

    pyb = IBA01(args.port, loggerIn=logging)

    success, result = pyb.start_server()
    if not success:
        logging.error("Unable to start server")
        pyb.close()
        exit(1)

    if args.debug:
        logging.info("Debug: enabling...")
        success, result = pyb.debug()
        logging.info("{} {}".format(success, result))
        if not success:
            logging.error("Failed to set debug mode")
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

    if args._cmd == "pwm" or all_funcs:
        success = test_pwm(args, pyb)
        if not success:
            logging.error("Failed testing adc")
            pyb.close()
            exit(1)

    if args._cmd == "misc" or all_funcs:
        success = test_misc(args, pyb)
        if not success:
            logging.error("Failed testing misc")
            pyb.close()
            exit(1)

    if args._cmd == "supplies" or all_funcs:
        success = test_supplies(args, pyb)
        if not success:
            logging.error("Failed testing supplies")
            pyb.close()
            exit(1)

    logging.info("all tests passed")
    pyb.close()

