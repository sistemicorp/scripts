#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2025
Owen Li, Martin Guthrie

This CLI provides a linux CLI interface to Teensy4 SimpleRPC.

Example:  (note the starting folder)

(venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 version


"""
import logging
import argparse

from A4401_BOND import A4401_BOND

# global teensy object
teensy = None


def parse_args():
    epilog = """
    Usage examples:
       python A4401_BOND_cli.py --port /dev/ttyACM0 led --on

    Port: Teensy4 when plugged into USB on Linux will show up as a ttyACM# device in /dev.
          Use 'ls -al /dev/ttyACM*' to find the port. 
          
    Getting Help for a command:
    $ python3 A4401_BOND_cli.py --port /dev/ttyACM0 write_gpio --help
        usage: A4401_BOND_cli.py write_gpio [-h] --pin-number _PIN_NUMBER --state {True,False}
    
        options:
        -h, --help            show this help message and exit
        --pin-number _PIN_NUMBER
                            GPIO number (0-41)
        --state {True,False}  True|False
      
    Examples:
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 version
    (venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 -n iox_led_green --enable
    """
    parser = argparse.ArgumentParser(description='A4401_BOND_cli',
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
    write_gpio.add_argument('--pin-number',
                            dest="_pin_number",
                            action='store',
                            type=int,
                            help='GPIO number (0-41)',
                            default=None, required=True)
    write_gpio.add_argument('--state', dest="_state", choices=('1', '0'), help='True|False', required=True)

    read_gpio = subp.add_parser('read_gpio')
    read_gpio.add_argument('--pin-number',
                           dest="_pin_number",
                           action='store',
                           type=int,
                           help='GPIO number (0-41)',
                           default=None, required=True)

    read_gpio = subp.add_parser('read_adc')
    read_gpio.add_argument('--pin-number',
                           dest="_pin_number",
                           action='store',
                           type=int,
                           help='GPIO number (0-41)',
                           default=None, required=True)
    read_gpio.add_argument('--sample-number',
                           dest="_sample_number",
                           action='store',
                           type=int,
                           help='Number of samples to take, 1-#',
                           default=None, required=True)
    read_gpio.add_argument('--sample-rate',
                           dest="_sample_rate",
                           action='store',
                           type=int,
                           help='Sample rate in milli-seconds, 0-#',
                           default=None, required=True)

    bist_voltage = subp.add_parser('bist_voltage')
    bist_voltage.add_argument('--name',
                           dest="_name",
                           action='store',
                           type=str,
                           help='name (V6V, V5V, V3V3A, V3V3D)',
                           default=None, required=True)

    vbat_read = subp.add_parser('vbat_read')
    vbat_set = subp.add_parser('vbat_set')
    vbat_set.add_argument('--mv',
                           dest="_mv",
                           action='store',
                           type=int,
                           help='voltage, 500-5000 mV',
                           required=True,
                           default=500)

    vbus_read = subp.add_parser('vbus_read')

    iox_led_green = subp.add_parser('iox_led_green',
                                    description="Enable/Disable Green LED (PASS indicator on Jig)")
    iox_led_green.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert LED GREEN',
                           default=False)

    iox_led_yellow = subp.add_parser('iox_led_yellow',
                                     description="Enable/Disable Yellow LED")
    iox_led_yellow.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert LED YELLOW',
                           default=False)

    iox_led_red = subp.add_parser('iox_led_red',
                                  description="Enable/Disable RED LED (FAIL indicator on Jig)")
    iox_led_red.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert LED RED',
                           default=False)

    iox_led_blue = subp.add_parser('iox_led_blue',
                                   description="Enable/Disable BLUE LED")
    iox_led_blue.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert LED BLUE',
                           default=False)

    iox_vbus_en = subp.add_parser('iox_vbus_en',
                                  description="Enable/Disable VBUS")
    iox_vbus_en.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert VBUS_EN',
                           default=False)

    iox_vbat_en = subp.add_parser('iox_vbat_en',
                                  description="Enable/Disable VBAT")
    iox_vbat_en.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert VBAT_EN',
                           default=False)

    iox_vbat_con = subp.add_parser('iox_vbat_con',
                                   description="Enable/Disable VBAT Connect to DUT")
    iox_vbat_con.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert VBAT_CON',
                           default=False)

    bond_max_hdr_adc_cal = subp.add_parser('bond_max_hdr_adc_cal',
                                           description="Read Header Calibration voltage, 2500mV")
    bond_max_hdr_adc_cal.add_argument('--header',
                           dest="_hdr",
                           action='store',
                           type=int,
                           help='header, 1-4',
                           required=True,
                           default=1)

    bond_max_hdr_adc = subp.add_parser('bond_max_hdr_adc',
                                       description="Read Header Pin ADC Voltage in mV")
    bond_max_hdr_adc.add_argument('--header',
                           dest="_hdr",
                           action='store',
                           type=int,
                           help='header, 1-4',
                           required=True,
                           default=1)
    bond_max_hdr_adc.add_argument('--pin',
                           dest="_pin",
                           action='store',
                           type=int,
                           help='pin, 1-20, but not all pins have function',
                           required=True,
                           default=1)

    bond_max_hdr_dac = subp.add_parser('bond_max_hdr_dac',
                                       description="Write Header Pin DAC Voltage in mV")
    bond_max_hdr_dac.add_argument('--header',
                           dest="_hdr",
                           action='store',
                           type=int,
                           help='header, 1-4',
                           required=True,
                           default=1)
    bond_max_hdr_dac.add_argument('--pin',
                           dest="_pin",
                           action='store',
                           type=int,
                           help='pin, 1-20, but not all pins have function',
                           required=True,
                           default=1)
    bond_max_hdr_dac.add_argument('--mv',
                           dest="_mv",
                           action='store',
                           type=int,
                           help='DAC output voltage 0-10000 mV',
                           required=True,
                           default=2500)

    # add new commands here...

    args = parser.parse_args()
    return args


def led(args):
    _success = True
    logging.info("led: {}".format(args))

    if args._on:
        logging.info("ON: turn on LED")
        response = teensy.led(True)

    else:
        logging.info("OFF: turn off LED")
        response = teensy.led(False)

    logging.info("{}".format(response))
    return response["success"]


def uid(args):
    _success = True
    logging.info("uid: {}".format(args))

    response = teensy.unique_id()
    logging.info("{}".format(response))
    return response["success"]


def version(args):
    _success = True
    logging.info("version: {}".format(args))

    response = teensy.version()
    logging.info("{}".format(response))
    return response["success"]


def write_gpio(args):
    _success = True
    logging.info("write_gpio: {}".format(args))

    _state = True
    if args._state == '0': _state = False

    response = teensy.write_gpio(args._pin_number, _state)
    logging.info("{}".format(response))
    return response["success"]


def read_gpio(args):
    _success = True
    logging.info("read_gpio: {}".format(args))

    response = teensy.read_gpio(args._pin_number)
    logging.info("{}".format(response))
    return response["success"]


def read_adc(args):
    _success = True
    logging.info("read_adc: {}".format(args))

    response = teensy.read_adc(args._pin_number, args._sample_number, args._sample_rate)
    logging.info("{}".format(response))
    return response["success"]


def bist_voltage(args):
    _success = True
    logging.info("bist_voltage: {}".format(args))

    response = teensy.bist_voltage(args._name)
    logging.info("{}".format(response))
    return response["success"]


def vbus_read(args):
    _success = True
    logging.info("vbus_read: {}".format(args))

    response = teensy.vbus_read()
    logging.info("{}".format(response))
    return response["success"]


def vbat_read(args):
    _success = True
    logging.info("vbat_read: {}".format(args))

    response = teensy.vbat_read()
    logging.info("{}".format(response))
    return response["success"]


def iox_led_green(args):
    _success = True
    logging.info("iox_led_green: {}".format(args))

    response = teensy.iox_led_green(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_led_yellow(args):
    _success = True
    logging.info("iox_led_yellow: {}".format(args))

    response = teensy.iox_led_yellow(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_led_red(args):
    _success = True
    logging.info("iox_led_yellow: {}".format(args))

    response = teensy.iox_led_red(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_led_blue(args):
    _success = True
    logging.info("iox_led_blue: {}".format(args))

    response = teensy.iox_led_blue(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_vbus_en(args):
    _success = True
    logging.info("iox_vbus_en: {}".format(args))

    response = teensy.iox_vbus_en(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_vbat_en(args):
    _success = True
    logging.info("iox_vbat_en: {}".format(args))

    response = teensy.iox_vbat_en(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_vbat_con(args):
    _success = True
    logging.info("iox_vbat_con: {}".format(args))

    response = teensy.iox_vbat_con(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_adc(args):
    _success = True
    logging.info("bond_max_hdr_adc: {}".format(args))

    response = teensy.bond_max_hdr_adc(args._hdr, args._pin)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_adc_cal(args):
    _success = True
    logging.info("bond_max_hdr_adc_cal: {}".format(args))

    response = teensy.bond_max_hdr_adc_cal(args._hdr)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_dac(args):
    _success = True
    logging.info("bond_max_hdr_dac: {}".format(args))

    response = teensy.bond_max_hdr_dac(args._hdr, args._pin, args._mv)
    logging.info("{}".format(response))
    return response["success"]

def vbat_set(args):
    _success = True
    logging.info("vbat_set: {}".format(args))

    response = teensy.vbat_set(args._mv)
    logging.info("{}".format(response))
    return response["success"]


if __name__ == '__main__':
    args = parse_args()
    exit_code = 0

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')

    teensy = A4401_BOND(args.port, loggerIn=logging)

    success = teensy.init(header_def_filename="pogo_hdr_definition._json")
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

    elif args._cmd == 'read_adc':
        success = read_adc(args)

    elif args._cmd == 'bist_voltage':
        success = bist_voltage(args)

    elif args._cmd == 'vbat_read':
        success = vbat_read(args)

    elif args._cmd == 'vbus_read':
        success = vbus_read(args)

    elif args._cmd == 'iox_led_green':
        success = iox_led_green(args)

    elif args._cmd == 'iox_led_yellow':
        success = iox_led_yellow(args)

    elif args._cmd == 'iox_led_red':
        success = iox_led_red(args)

    elif args._cmd == 'iox_led_blue':
        success = iox_led_blue(args)

    elif args._cmd == 'iox_vbus_en':
        success = iox_vbus_en(args)

    elif args._cmd == 'iox_vbat_en':
        success = iox_vbat_en(args)

    elif args._cmd == 'iox_vbat_con':
        success = iox_vbat_con(args)

    elif args._cmd == 'bond_max_hdr_adc_cal':
        success = bond_max_hdr_adc_cal(args)

    elif args._cmd == 'bond_max_hdr_adc':
        success = bond_max_hdr_adc(args)

    elif args._cmd == 'bond_max_hdr_dac':
        success = bond_max_hdr_dac(args)

    elif args._cmd == 'vbat_set':
        success = vbat_set(args)

    if success:
        logging.info("Success")

    else:
        logging.error("Failed")
        exit_code = 1

    teensy.close()
