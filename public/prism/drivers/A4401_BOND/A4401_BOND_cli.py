#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2025
Owen Li, Martin Guthrie

This CLI provides a linux CLI interface to Teensy4 SimpleRPC.

Example:  (note the starting folder)

(venv) martin@martin-ThinkPad-L13:~/git/scripts/public/prism/drivers/A4401_BOND$ python A4401_BOND_cli.py -p /dev/ttyACM0 version


"""
import os
import logging
import argparse
import time

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

    parser.add_argument("-n", '--no-init', dest='_skip_init', action='store_true', default=False,
                        help='Do not send the header definition to BOND (presumed previously '
                             'initialized), the file is still read for pin lookups')

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
                           help='name (V6V, V5V, V3V3A, V3V3D, V2V5NEG)',
                           default=None, required=True)

    vbat_read = subp.add_parser('vbat_read')
    vbat_set = subp.add_parser('vbat_set')
    vbat_set.add_argument('--mv',
                           dest="_mv",
                           action='store',
                           type=int,
                           help='voltage, 1500-5000 mV, 50 mV steps',
                           required=True,
                           default=500)

    vdut_read = subp.add_parser('vdut_read')
    vdut_set = subp.add_parser('vdut_set')
    vdut_set.add_argument('--mv',
                           dest="_mv",
                           action='store',
                           type=int,
                           help='voltage, 1000-9000 mV',
                           required=True,
                           default=500)

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

    vdut_en = subp.add_parser('vdut_en',
                                  description="Enable/Disable VDUT SMPS (TPS55289)")
    vdut_en.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert VDUTSMPS_EN',
                           default=False)

    vdut_con = subp.add_parser('vdut_con',
                               description="Connect/Disconnect VDUT to the DUT")
    vdut_con.add_argument('--enable',
                          dest="_enable",
                          action='store_true',
                          help='Assert VDUT_EN',
                          default=False)

    subp.add_parser('vdut_get_fault', description="Get VDUT TPS55289 faults")
    subp.add_parser('vdut_reset', description="Reset VDUT TPS55289")

    vbus_en = subp.add_parser('vbus_en',
                              description="Enable/Disable VBUS, External USB-C (HDR3 port 9)")
    vbus_en.add_argument('--enable',
                         dest="_enable",
                         action='store_true',
                         help='Assert VBUS',
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

    iox_selftest = subp.add_parser('iox_selftest',
                                  description="Enable/Disable SELFTEST")
    iox_selftest.add_argument('--enable',
                           dest="_enable",
                           action='store_true',
                           help='Assert SELFTEST',
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

    bond_max_hdr_gpo = subp.add_parser('bond_max_hdr_gpo',
                                       description="Write Header Pin GPO state")
    bond_max_hdr_gpo.add_argument('--header', dest="_hdr", action='store', type=int,
                                  help='header, 1-4', required=True)
    bond_max_hdr_gpo.add_argument('--pin', dest="_pin", action='store', type=int,
                                  help='pin, 1-20, but not all pins have function', required=True)
    bond_max_hdr_gpo.add_argument('--enable', dest="_enable", action='store_true',
                                  help='GPO high', default=False)

    bond_max_hdr_gpi = subp.add_parser('bond_max_hdr_gpi',
                                       description="Read Header Pin GPI state")
    bond_max_hdr_gpi.add_argument('--header', dest="_hdr", action='store', type=int,
                                  help='header, 1-4', required=True)
    bond_max_hdr_gpi.add_argument('--pin', dest="_pin", action='store', type=int,
                                  help='pin, 1-20, but not all pins have function', required=True)

    bond_ldo_set = subp.add_parser('bond_ldo_set', description="Set Header 1 LDO voltage")
    bond_ldo_set.add_argument('--mv', dest="_mv", action='store', type=int,
                              help='LDO voltage, 600-3900 mV', required=True)

    subp.add_parser('bond_batt_emu_cal', description="Recalibrate the battery emulator")
    subp.add_parser('list', description="List the BOND RPC methods")

    debug_batt_emu = subp.add_parser('debug_batt_emu',
                                     description="BOND debug battery emulator")

    status = subp.add_parser('status',
                                       description="Get status")

    sequence = subp.add_parser('sequence',
                                       description="Runs commands in sequence")

    temperature = subp.add_parser('temperature',
                                       description="Get temperature")

    # add new commands here...

    args = parser.parse_args()
    return args


def led(args):
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
    logging.info("uid: {}".format(args))

    response = teensy.unique_id()
    logging.info("{}".format(response))
    return response["success"]


def version(args):
    logging.info("version: {}".format(args))

    response = teensy.version()
    logging.info("{}".format(response))
    return response["success"]


def write_gpio(args):
    logging.info("write_gpio: {}".format(args))

    _state = True
    if args._state == '0': _state = False

    response = teensy.write_gpio(args._pin_number, _state)
    logging.info("{}".format(response))
    return response["success"]


def read_gpio(args):
    logging.info("read_gpio: {}".format(args))

    response = teensy.read_gpio(args._pin_number)
    logging.info("{}".format(response))
    return response["success"]


def read_adc(args):
    logging.info("read_adc: {}".format(args))

    response = teensy.read_adc(args._pin_number, args._sample_number, args._sample_rate)
    logging.info("{}".format(response))
    return response["success"]


def bist_voltage(args):
    logging.info("bist_voltage: {}".format(args))

    response = teensy.bist_voltage(args._name)
    logging.info("{}".format(response))
    return response["success"]


def vdut_read(args):
    logging.info("vdut_read: {}".format(args))

    response = teensy.vdut_read()
    logging.info("{}".format(response))
    return response["success"]


def vbat_read(args):
    logging.info("vbat_read: {}".format(args))

    response = teensy.vbat_read()
    logging.info("{}".format(response))
    return response["success"]


def iox_led_green(args):
    logging.info("iox_led_green: {}".format(args))

    response = teensy.iox_led_green(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_led_yellow(args):
    logging.info("iox_led_yellow: {}".format(args))

    response = teensy.iox_led_yellow(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_led_red(args):
    logging.info("iox_led_red: {}".format(args))

    response = teensy.iox_led_red(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_led_blue(args):
    logging.info("iox_led_blue: {}".format(args))

    response = teensy.iox_led_blue(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def vdut_en(args):
    logging.info("vdut_en: {}".format(args))

    response = teensy.vdut_en(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_vbat_en(args):
    logging.info("iox_vbat_en: {}".format(args))

    response = teensy.iox_vbat_en(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_vbat_con(args):
    logging.info("iox_vbat_con: {}".format(args))

    response = teensy.iox_vbat_con(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def iox_selftest(args):
    logging.info("iox_selftest_en: {}".format(args))

    response = teensy.iox_selftest(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_adc(args):
    logging.info("bond_max_hdr_adc: {}".format(args))

    response = teensy.bond_max_hdr_adc(args._hdr, args._pin)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_adc_cal(args):
    logging.info("bond_max_hdr_adc_cal: {}".format(args))

    response = teensy.bond_max_hdr_adc_cal(args._hdr)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_dac(args):
    logging.info("bond_max_hdr_dac: {}".format(args))

    response = teensy.bond_max_hdr_dac(args._hdr, args._pin, args._mv)
    logging.info("{}".format(response))
    return response["success"]


def vbat_set(args):
    logging.info("vbat_set: {}".format(args))

    response = teensy.vbat_set(args._mv)
    logging.info("{}".format(response))
    return response["success"]


def vdut_set(args):
    logging.info("vdut_set: {}".format(args))

    response = teensy.vdut_set(args._mv)
    logging.info("{}".format(response))
    return response["success"]


def debug_batt_emu(args):
    logging.info("debug_batt_emu: {}".format(args))

    response = teensy.bond_debug_batt_emu()
    logging.info("{}".format(response))
    return response["success"]


def status(args):
    logging.info("status: {}".format(args))

    response = teensy.status()
    logging.info("{}".format(response))
    return response["success"]


def temperature(args):
    logging.info("temperature: {}".format(args))

    response = teensy.temperature()
    logging.info("{}".format(response))
    return response["success"]


def vdut_con(args):
    logging.info("vdut_con: {}".format(args))

    response = teensy.vdut_con(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def vdut_get_fault(args):
    logging.info("vdut_get_fault: {}".format(args))

    response = teensy.vdut_get_fault()
    logging.info("{}".format(response))
    return response["success"]


def vdut_reset(args):
    logging.info("vdut_reset: {}".format(args))

    response = teensy.vdut_reset()
    logging.info("{}".format(response))
    return response["success"]


def vbus_en(args):
    logging.info("vbus_en: {}".format(args))

    response = teensy.vbus_en(args._enable)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_gpo(args):
    logging.info("bond_max_hdr_gpo: {}".format(args))

    response = teensy.bond_max_hdr_gpo(args._hdr, args._pin, args._enable)
    logging.info("{}".format(response))
    return response["success"]


def bond_max_hdr_gpi(args):
    logging.info("bond_max_hdr_gpi: {}".format(args))

    response = teensy.bond_max_hdr_gpi(args._hdr, args._pin)
    logging.info("{}".format(response))
    return response["success"]


def bond_ldo_set(args):
    logging.info("bond_ldo_set: {}".format(args))

    response = teensy.bond_ldo_set(args._mv)
    logging.info("{}".format(response))
    return response["success"]


def bond_batt_emu_cal(args):
    logging.info("bond_batt_emu_cal: {}".format(args))

    response = teensy.bond_batt_emu_cal()
    logging.info("{}".format(response))
    return response["success"]


def list_methods(args):
    logging.info("list: {}".format(args))

    for m in teensy.list():
        logging.info(m)
    return True


def sequence(args):
    logging.info("sequence: {}".format(args))

    # Create a sequence of commands to run

    response = teensy.vbat_set(2000)
    logging.info("{}".format(response))
    response = teensy.iox_vbat_con(True)
    logging.info("{}".format(response))
    #response = teensy.iox_selftest(True)
    #logging.info("{}".format(response))

    try:
        while True:
            time.sleep(1)
            response = teensy.vbat_read()
            logging.info("{}".format(response))

    except KeyboardInterrupt:
        logging.info("Exiting")

    response = teensy.iox_vbat_con(False)
    logging.info("{}".format(response))

    return response["success"]


if __name__ == '__main__':
    args = parse_args()
    exit_code = 0

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')

    header_def = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pogo_hdr_definition._json")
    teensy = A4401_BOND(args.port, loggerIn=logging, header_def_filename=header_def)

    success = teensy.init(configure_headers=not args._skip_init)
    if not success:
        logging.error("Failed to create teensy instance")
        teensy.close()
        exit(1)

    commands = {
        'led': led,
        'uid': uid,
        'version': version,
        'write_gpio': write_gpio,
        'read_gpio': read_gpio,
        'read_adc': read_adc,
        'bist_voltage': bist_voltage,
        'vbat_read': vbat_read,
        'vbat_set': vbat_set,
        'vdut_read': vdut_read,
        'vdut_set': vdut_set,
        'vdut_en': vdut_en,
        'vdut_con': vdut_con,
        'vdut_get_fault': vdut_get_fault,
        'vdut_reset': vdut_reset,
        'vbus_en': vbus_en,
        'iox_led_green': iox_led_green,
        'iox_led_yellow': iox_led_yellow,
        'iox_led_red': iox_led_red,
        'iox_led_blue': iox_led_blue,
        'iox_vbat_en': iox_vbat_en,
        'iox_vbat_con': iox_vbat_con,
        'iox_selftest': iox_selftest,
        'bond_max_hdr_adc_cal': bond_max_hdr_adc_cal,
        'bond_max_hdr_adc': bond_max_hdr_adc,
        'bond_max_hdr_dac': bond_max_hdr_dac,
        'bond_max_hdr_gpo': bond_max_hdr_gpo,
        'bond_max_hdr_gpi': bond_max_hdr_gpi,
        'bond_ldo_set': bond_ldo_set,
        'bond_batt_emu_cal': bond_batt_emu_cal,
        'debug_batt_emu': debug_batt_emu,
        'status': status,
        'sequence': sequence,
        'temperature': temperature,
        'list': list_methods,
    }
    if args._cmd in commands:
        success = commands[args._cmd](args)

    if success:
        logging.info("Success")

    else:
        logging.error("Failed")
        exit_code = 1

    teensy.close()
    exit(exit_code)
