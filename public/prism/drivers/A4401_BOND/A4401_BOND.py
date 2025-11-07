#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023-2025
Owen Li, Martin Guthrie

"""
import os
import traceback
import json
import jstyleson
import threading
import re
from simple_rpc import Interface
from serial import SerialException

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


DRIVER_TYPE = "A4401_BOND"
DRIVER_TYPE_PROG = "A4401_BOND_PROG"


class A4401_BOND:
    """ teensy4 SimpleRPC based driver

    Adding new RPC calls...

    1) Write server code by adding a function in teensy4_server.ino (Look at existing functions as example)
    2) Export the function by adding a name and description in the loop() (Look at existing exports as example)
    3) Write function in Teensy4 Class (this one) to call your simpleRPC function (Look at existing
       functions as example).  Note the code is organized so that "on-board" Teensy functions are in one
       section, and off module functions are in another.
    4) Test your new API with the Teensy4_cli.py script.
    5) Write function in teensy400xx.py to call your Teensy4 Class function (Look at existing functions as example)
    6) Add your function call to the test script!

    version.h:
    ----------
    There is a version for teensy4_server.ino and for the python code. The version number must be
    the same for testing to run.

    """
    GPIO_MODE_INPUT = "INPUT"
    GPIO_MODE_OUTPUT = "OUTPUT"
    GPIO_MODE_INPUT_PULLUP = "INPUT_PULLUP"
    GPIO_MODE_LIST = [GPIO_MODE_INPUT, GPIO_MODE_OUTPUT, GPIO_MODE_INPUT_PULLUP]

    JIG_CLOSE_GPIO = 6  # BUTTON1 GPIO number for Jig Closed detect, set to None if not using (Active-Low)

    GPIO_NUMBER_MIN = 0
    GPIO_NUMBER_MAX = 41

    BIST_VOLTAGES = ["V6V", "V5V", "V3V3A", "V3V3D", "V2V5NEG"]

    # For Teensy FW version checking the SAME (c code) header file that created the Teensy4
    # firmware is used to check if that firmware is now running (deployed) on Teensy4.
    # if that FW is not running, there is probably a problem!  See method init().
    _version_file = os.path.join(os.path.dirname(__file__), "server/teensy4_server/version.h")

    def __init__(self, port, loggerIn=None):
        self.lock = threading.Lock()

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self._lock = threading.Lock()
        self.port = port
        self.rpc = None
        self.a44BOND_max_config = None
        self._is_battemu_calibrated = False  # calibrate only if used

        self.my_version = self._get_version()
        self.logger.info(f"version {self.my_version}")

    def set_port(self, port):
        self.port = port

    def init(self, header_def_filename=None):
        """ Init Teensy SimpleRPC connection

        :param skip_init: True/False, skips MAX11311 setup, assume thats already done
        :return: <True/False> whether Teensy SimpleRPC connection was created
        """
        self.logger.info(f"installing BOND on port {self.port} using {header_def_filename}")
        if header_def_filename is None:
            self.logger.error("MAX11311 port definition file must be specified")
            return False

        if self.rpc is None:
            try:
                self.rpc = Interface(self.port)

            except Exception as e:
                self.logger.error(e)
                return False

        version_response = self.version()
        if not version_response["success"]:
            self.logger.error("Unable to get version")
            return False

        if self.my_version != version_response["result"]["version"]:
            self.logger.error("version does not match, Python: {} Arduino: {}".format(self.my_version, version_response["result"]["version"]))
            return False

        status_response = self.status()
        if not status_response["success"]:
            self.logger.error("Unable to get status")
            return False
        if status_response["result"]["setup_fail_code"] != 0:
            self.logger.error(f'setup_fail_code {status_response["result"]["setup_fail_code"]}')
            return False

        # check if jig close has valid GPIOs
        self._jig_close_check()

        if header_def_filename is None:
            self.logger.error(f"Header pin definition filename not supplied")
            return False

        if not os.path.exists(header_def_filename):
            self.logger.error(f"Header pin definition filename {header_def_filename} does not exist")
            return False

        # init MAX11311 pins per the JSON defintion
        # also calibrates the battery emulator if needed
        success = self._init_maxs(header_def_filename)
        if not success:
            self.logger.error(f"Failed to init MAX11311 pins")
            return False

        status_response = self.iox_vbat_con(False)
        if not status_response["success"]:
            self.logger.error(f"iox_vbat_con {status_response}")
            return False

        status_response = self.iox_selftest(False)
        if not status_response["success"]:
            self.logger.error(f"iox_vbat_con {status_response}")
            return False

        # check bist voltages
        for _v in self.BIST_VOLTAGES:
            status_response = self.bist_voltage(_v)
            if not status_response["success"]:
                self.logger.error(f"bist_voltage {_v} {success}")
                return False

            if not status_response["result"]["pass"]:
                self.logger.error(f"bist_voltage {_v} {status_response}")
                return False

            self.logger.info(f"bist_voltage {_v} {status_response}")

        # finally, all is well
        self.logger.info("Installed A4401BOND on port {}".format(self.port))
        return True

    def close(self):
        """  Close connection
          
        :return:
        """
        if self.rpc is None:
            return True

        self.logger.info(f"closing {self.port}")
        self.rpc.close()
        self.rpc = None
        return True

    # ----------------------------------------------------------------------------------------------
    # Helper Functions
    #
    # - function names should all begin with "_"
    # - functions are all private to this class

    def _init_maxs(self, header_def_filename):
        # read the json-like header definition file
        self.logger.info(f"Attempting to read MAX11311 config from {header_def_filename}...")
        try:
            with open(header_def_filename) as f:
                json_data = f.read()

            self.a44BOND_max_config = jstyleson.loads(json_data)  # OK

        except Exception as e:
            self.logger.error(e)
            self.logger.error(traceback.format_exc())
            return False

        self.logger.info(self.a44BOND_max_config)
        for k, v in self.a44BOND_max_config.items():
            if not k.isdigit():
                continue

            ports_dac = []
            ports_adc = [11]  # all headers use MAX port11 for self test
            ports_gpo = []
            ports_gpi = []
            pins_configured = []
            for pin, config in v.items():
                # some items in the JSON are not pins, skip them
                if not pin.isdigit():
                    continue

                if pin in pins_configured:
                    self.logger.error(f"HDR {k}, DUPLICATE pin {pin}, config {config}")
                    return False
                pins_configured.append(pin)

                self.logger.info(f"HDR {k}, pin {pin}, config {config}")

                if config["mode"] is None: continue

                modes = [m for m in config["mode"].split(",")]
                ports = [int(p) for p in config["port"].split(",")]
                if len(ports) != len(modes):
                    self.logger.error(f"modes and ports must be equal lengths")
                    continue
                for m, p in zip(modes, ports):
                    if "DAC" == m:
                        ports_dac.append(p)

                    if "ADC" == m:
                        ports_adc.append(p)

                    if "GPO" == m:
                        ports_gpo.append(p)

                    if "GPI" == m:
                        ports_gpi.append(p)

            ports_dac.sort()
            ports_adc.sort()
            ports_gpo.sort()
            ports_gpi.sort()
            self.logger.info(f"ports_dac {ports_dac}")
            self.logger.info(f"ports_adc {ports_adc}")
            self.logger.info(f"ports_gpo {ports_gpo}")
            self.logger.info(f"ports_gpi {ports_gpi}")
            answer = self.rpc.call_method('bond_max_hdr_init',
                                          k,  # header MAX11311 number, 1-4
                                          ports_adc, len(ports_adc),
                                          ports_dac, len(ports_dac),
                                          ports_gpo, len(ports_gpo),
                                          ports_gpi, len(ports_gpi),
                                          v["gpo_mv"], v["gpi_mv"])
            answer = self._rpc_validate(answer)
            if not answer['success']:
                self.logger.error(f"failed to init: {answer}")
                return False

        if "calibrate_battery_emulator" in self.a44BOND_max_config and self.a44BOND_max_config['calibrate_battery_emulator']:
            self.logger.info("Calibrating Battery Emulator...")
            answer = self.rpc.call_method('bond_batt_emu_cal')
            answer = self._rpc_validate(answer)
            if not answer['success']:
                self.logger.error(f"bond_batt_emu_cal failed: {answer}")
                return False

            self._is_battemu_calibrated = True
            self.logger.info("Calibrating Battery Emulator completed")

        return True

    def _get_version(self):
        """ Get Version from version.h
        - The version of the "RPC server" running on Teensy, is expected to be the
          same version of this Python code.  If there is a difference, then
          something is out of sync.  init() will fail if the versions do not match.
        - The Teensy Arduino Code uses version.h to set its version.  This function
          reads that same file to get the expected version running on Teensy.

        Expected version.h file contents, no other pattern is accounted for,
        !!no other lines or comments are allowed!!
            #define VERSION "1.0.0"
        Extract "1.0.0"

        :return: <version>|"ERROR"
        """
        regex = r"\d+\.\d+\.\d+"

        with open(self._version_file) as f:
            s = f.read()

        m = re.findall(regex, s)
        if not m:
            self.logger.error(f"Unable to find version in {self._version_file}: {s}")
            return "ERROR"

        return m[0]

    def _jig_close_check(self):
        if self.JIG_CLOSE_GPIO is None:
            self.logger.info("Jig Closed Detector not defined (None)")
            return True
        elif self.GPIO_NUMBER_MIN < self.JIG_CLOSE_GPIO > self.GPIO_NUMBER_MAX:
            self.logger.error("Invalid GPIO")
            return False
        else:
            self.rpc.call_method('init_gpio', self.JIG_CLOSE_GPIO, self.GPIO_MODE_INPUT_PULLUP.encode())
            return True

    def _rpc_validate(self, answer, squelch=False):
        try:
            answer = json.loads(answer)
            if answer["success"]:
                if not squelch:
                    self.logger.info(answer)
            else:
                self.logger.error(answer)

        except Exception as e:
            self.logger.error(answer)
            self.logger.error(e)
            answer = {"success": False}

        return answer

    # Helper Functions
    # ----------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------
    # API (wrapper functions)
    #
    # - functions that are Teensy module functions (on-board)
    # - all RPC functions return dict: { "success": <True/False>, "result": { key: value, ... }}
    #

    def list(self):
        """ list
        :return: list of Teensy methods
        """
        return list(self.rpc.methods)

    def unique_id(self):
        """ unique id
        :return: success = True/False, method: unique_id, unique_id = MAC Address
        """
        with self._lock:
            self.logger.info(f"unique_id")
            answer = self.rpc.call_method('unique_id')
            return self._rpc_validate(answer)

    def slot(self):
        """ slot
        :return: success = True/False, method: slot, id = id
        """
        # TODO: implement arduino side
        with self._lock:
            self.logger.info(f"slot")
            answer = self.rpc.call_method('slot')
            return self._rpc_validate(answer)

    # def channel(self):
    #     c = {'method': 'slot', 'args': {}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def version(self):
        """ Version
        :return: success = True/False, method = version, version = version#
        """
        with self._lock:
            self.logger.info(f"version")
            answer = self.rpc.call_method('version')
            return self._rpc_validate(answer)

    def status(self):
        """ Status
        :return: success = True/False, method = version,
        """
        with self._lock:
            self.logger.info(f"status")
            answer = self.rpc.call_method('status')
            return self._rpc_validate(answer)

    def reset(self):
        """ reset
        :return: success = True/False, method = reset
        """
        with self._lock:
            self.logger.info(f"reset")
            answer = self.rpc.call_method('reset')
            return self._rpc_validate(answer)

    def reboot_to_bootloader(self):
        """ reboot
        :return: success = True/False, method = reset
        """
        try:
            with self._lock:
                self.logger.info(f"reboot_to_bootloader")
                self.rpc.call_method('reboot_to_bootloader')
                # reboot will not return, expect SerialException exception, fake the return success

        except SerialException:
            pass

        except Exception as e:
            self.logger.error(e)
            return json.loads("""{"success": false}""")  # json false is lower case

        return json.loads("""{"success": true}""")  # json true is lower case

    def led(self, set):
        """ LED on/off
        :param set: True/False
        :return: success = True/False, method = set_led, result = state = ON/OFF
        """
        with self._lock:
            self.logger.info(f"set_led {set}")
            answer = self.rpc.call_method('set_led', set)
            return self._rpc_validate(answer)

    # def led_toggle(self, led, on_ms=500, off_ms=500, once=False):
    #     """ toggle and LED ON and then OFF
    #     - this is a blocking command
    #
    #     :param led: # of LED, see self.LED_*
    #     :param on_ms: # of milliseconds to turn on LED
    #     :return:
    #     """
    #     c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_ms, 'off_ms': off_ms, 'once': once}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def read_adc(self, pin_number, sample_num=1, sample_rate_ms=1):
        """ Read an ADC pin
        - This is a BLOCKING function
        - result is raw ADC value, client needs to scale to VREF (3.3V)

        :param pin_number: (0 - 41)
        :param sample_num: Number of samples to average over
        :param sample_rate_ms: Millisecond delay between samples
        :return: success = True/False, method = read_adc, result = reading = *
        """
        with self._lock:
            self.logger.info(f"read_adc {pin_number} {sample_num} {sample_rate_ms}")
            answer = self.rpc.call_method('read_adc', pin_number, sample_num, sample_rate_ms)
            return self._rpc_validate(answer)

    def init_gpio(self, pin_number, mode):
        """ Init GPIO
        :param pin_number: (0 - 41)
        :param mode: Teensy4.MODE_*
        :return: success = True/False, method = init_gpio, result = init = Set pin (pin_number) to (mode)
        """
        if mode not in self.GPIO_MODE_LIST:
            err = "Invalid mode {} not in {}".format(mode, self.GPIO_MODE_LIST)
            self.logger.error(err)
            return {'success': False, 'value': {'err': err}}

        mode_b = mode.encode()
        with self._lock:
            self.logger.info(f"init_gpio {pin_number} {mode_b}")
            answer = self.rpc.call_method('init_gpio', pin_number, mode_b)
            return self._rpc_validate(answer)

    def read_gpio(self, pin_number):
        """ Get GPIO
        :param pin_number: (0 - 41)
        :return: success = True/False, method = read_gpio, result = state = 1/0
        """
        with self._lock:
            self.logger.info(f"read_gpio {pin_number}")
            answer = self.rpc.call_method('read_gpio', pin_number)
            return self._rpc_validate(answer)

    def write_gpio(self, pin_number, state: bool):
        """ Set GPIO
        :param pin_number: (0 - 41)
        :param state: 1/0
        :return: success = True/False, method = write_gpio, result = state = 1/0
        """
        with self._lock:
            self.logger.info(f"write_gpio {pin_number} {state}")
            answer = self.rpc.call_method('write_gpio', pin_number, state)
            return self._rpc_validate(answer)

    def bist_voltage(self, name):
        """ Read BIST voltage

        :param name: one of V6V, V5V, V3V3A, V3V3D, V2V5NEG (checked by teensy server side)
        :return: {'success': True, 'method': 'bist_voltage', 'result': {'name': 'V5V', 'mv': 0}}
        """
        with self._lock:
            self.logger.info(f"bist_voltage {name}")
            answer = self.rpc.call_method('bist_voltage', name.encode())
            return self._rpc_validate(answer)

    def vdut_read(self):
        """ Read INA220 for VDUT

        :return: {'success': True, 'method': 'vbus_read', 'result': {'v': 0, 'ima': 0.050000001}}
        """
        with self._lock:
            self.logger.info(f"vdut_read")
            answer = self.rpc.call_method('vbus_read')
            return self._rpc_validate(answer)

    def temperature(self):
        """ Read TMP1075

        :return: {'success': True, 'method': 'temperature', 'result': {'temp_degC': 30.3125}}
        """
        with self._lock:
            self.logger.info(f"temperature")
            answer = self.rpc.call_method('temperature')
            return self._rpc_validate(answer)

    def vdut_set(self, mv: int):
        """ Set VDUT Voltage in mV

        :return: {'success': True, 'method': 'vdut_set', 'result': {'v': 0, 'ima': 0.050000001}}
        """
        with self._lock:
            self.logger.info(f"vdut_set")
            answer = self.rpc.call_method('vdut_set', mv)
            return self._rpc_validate(answer)

    def vbat_read(self):
        """ Read INA220 for VBAT

        :return: {'success': True, 'method': 'vbat_read', 'result': {'v': 0, 'ima': 0.050000001}}
        """
        with self._lock:
            self.logger.info(f"vbat_read")
            answer = self.rpc.call_method('vbat_read')
            return self._rpc_validate(answer)

    def vbat_set(self, mv: int):
        """ Set VBAT (Battery emulator)

        :return: {'success': True, 'method': 'vbat_set',
                  'result': {'mV': <int>, 'measured_mv': <int> }
        """
        with self._lock:
            self.logger.info(f"vbat_set {mv}")
            answer = self.rpc.call_method('vbat_set', mv)
            return self._rpc_validate(answer)

    def vdut_en(self, state: bool):
        """ VDUT SMPS Enable/Disable

        :return: {'success': True, 'method': 'vdut_en',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"vdut_en {state}")
            answer = self.rpc.call_method('vdut_en', state)
            return self._rpc_validate(answer)

    def vdut_con(self, state: bool):
        """ VDUT SMPS Connect to DUT

        :return: {'success': True, 'method': 'vdut_con',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"vdut_con {state}")
            answer = self.rpc.call_method('vdut_con', state)
            return self._rpc_validate(answer)

    def iox_led_green(self, state: bool):
        """ MAX11311 IOX

        :return: {'success': True, 'method': 'iox_led_green',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"iox_led_green {state}")
            answer = self.rpc.call_method('iox_led_green', state)
            return self._rpc_validate(answer)

    def iox_led_yellow(self, state: bool):
        """ MAX11311 IOX

        :return: {'success': True, 'method': 'iox_led_yellow',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"iox_led_yellow {state}")
            answer = self.rpc.call_method('iox_led_yellow', state)
            return self._rpc_validate(answer)

    def iox_led_red(self, state: bool):
        """ MAX11311 IOX

        :return: {'success': True, 'method': 'iox_led_red',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"iox_led_red {state}")
            answer = self.rpc.call_method('iox_led_red', state)
            return self._rpc_validate(answer)

    def iox_led_blue(self, state: bool):
        """ MAX11311 IOX

        :return: {'success': True, 'method': 'iox_led_blue',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"iox_led_blue {state}")
            answer = self.rpc.call_method('iox_led_blue', state)
            return self._rpc_validate(answer)

    def iox_selftest(self, state: bool):
        """ MAX11311 IOX

        :return: {'success': True, 'method': 'iox_vbus_en',
                  'result': {'assert': False, 'level': False}
        """
        with self._lock:
            self.logger.info(f"iox_selftest {state}")
            answer = self.rpc.call_method('iox_selftest', state)
            return self._rpc_validate(answer)

    def iox_vbat_en(self, state: bool):
        """ Enable VBAT

        :return: {'success': True, 'method': 'iox_vbat_en',
                  'result': {'assert': False, 'level': False}
        """
        if not self._is_battemu_calibrated:
            self.logger.error("attempt to use Battery Emulator that is not calibrated")
            return {'success': False, 'method': 'iox_vbat_en', 'result': {'error': "not calibrated"}}

        with self._lock:
            self.logger.info(f"iox_vbat_en {state}")
            answer = self.rpc.call_method('iox_vbat_en', state)
            return self._rpc_validate(answer)

    def iox_vbat_con(self, state: bool):
        """ Connect VBAT to DUT

        :return: {'success': True, 'method': 'iox_vbat_con',
                  'result': {'assert': False, 'level': False}
        """
        if not self._is_battemu_calibrated:
            self.logger.error("attempt to use Battery Emulator that is not calibrated")
            return {'success': False, 'method': 'iox_vbat_en', 'result': {'error': "not calibrated"}}

        with self._lock:
            self.logger.info(f"iox_vbat_con {state}")
            answer = self.rpc.call_method('iox_vbat_con', state)
            return self._rpc_validate(answer)

    def bond_max_hdr_adc_cal(self, hdr: int):
        """ MAX11311 Header <1-4> read ADC CAL (port 11) voltage
        - expected result is always 2500 +/- error

        :return: {'success': True, 'method': 'bond_max_hdr_adc_cal',
                  'result': {'mV': <int> }
        """
        with self._lock:
            self.logger.info(f"bond_max_hdr_adc_cal {hdr}")
            answer = self.rpc.call_method('bond_max_hdr_adc_cal', hdr)
            return self._rpc_validate(answer)

    def _bond_check_hdr_pin(self, _hdr, _pin, mode):
        if self.a44BOND_max_config is None:
            self.logger.error(f"Attempt to use MAX11311 before configured")
            return False, None, {'success': False, 'method': 'bond_max_hdr_adc/dac',
                                 'result': {'error': f'MAX11311 not configured'}}

        hdr, pin = str(_hdr), str(_pin)
        if hdr not in self.a44BOND_max_config:
            self.logger.error(f'Invalid parameter hdr {hdr}')
            return False, None, {'success': False, 'method': 'bond_max_hdr_adc',
                                 'result': {'error': f'Invalid parameter hdr {hdr}'}}
        if pin not in self.a44BOND_max_config[hdr]:
            self.logger.error(f'Invalid parameter pin {pin}')
            return False, None, {'success': False, 'method': 'bond_max_hdr_adc',
                                 'result': {'error': f'Invalid parameter pin {pin}'}}

        config = self.a44BOND_max_config[hdr][pin]
        if config['mode'] != mode:
            self.logger.error(f'Invalid mode hdr {hdr} pin {pin} mode {config["mode"]}')
            return False, None, {'success': False, 'method': 'bond_max_hdr_adc',
                                'result': {'error': f'Invalid mode hdr {hdr} pin {pin} mode {config["mode"]}'}}

        port = config["port"]
        return True, port, None

    def bond_max_hdr_adc(self, hdr: int, pin: int):
        """ MAX11311 Header <1-4> read ADC Port <0-10> voltage
        - get port from pin, and also check mode

        :return: {'success': True, 'method': 'bond_max_hdr_adc',
                  'result': {'mV': <int> }
        """
        success, port, error = self._bond_check_hdr_pin(hdr, pin, "ADC")
        if not success:
            return error

        with self._lock:
            self.logger.info(f"bond_max_hdr_adc {hdr} {port}")
            answer = self.rpc.call_method('bond_max_hdr_adc', hdr, port)
            return self._rpc_validate(answer)

    def bond_max_hdr_dac(self, hdr: int, pin: int, mv: int):
        """ MAX11311 Header <1-4> write DAC Port <0-10> voltage <mv>
        - get port from pin, and also check mode
        - dac raw is mv / 2.5

        :return: {'success': True, 'method': 'bond_max_hdr_dac',
                  'result': {'mV': <int>, 'dac_raw': <int> }
        """
        success, port, error = self._bond_check_hdr_pin(hdr, pin, "DAC")
        if not success:
            return error

        if not (0 <= mv <= 10000):
            return {'success': False, 'method': 'bond_max_hdr_dac',
                    'result': {'error': f'Invalid parameter mv {mv}'}}

        with self._lock:
            self.logger.info(f"bond_max_hdr_dac {hdr} {port} {mv}")
            answer = self.rpc.call_method('bond_max_hdr_dac', hdr, port, mv)
            return self._rpc_validate(answer)

    # DEBUG APIs

    def bond_debug_batt_emu(self):
        """ DEBUG: Battery emulator
        :return: {'success': True, 'method': 'debug_batt_emu',
                  'result': {'mV': <int> }
        """
        with self._lock:
            self.logger.info(f"debug_batt_emu")
            answer = self.rpc.call_method('debug_batt_emu')
            return self._rpc_validate(answer)

    #
    # API (wrapper functions)
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Prism Player Callback functions
    #

    def jig_closed_detect(self):
        """ Read Jig Closed feature on Teensy
        This is used by Prism Player logic, and can only return True|False
        True - Jig Closed (testing will start)
        False - Jig Open
        None - Not implemented, or error

        # NOTE: !! if not using jig_closed_detect the play function should be None
        #          See hwdrv_teensy4.py:discover_channels():line 108

        return: <True|False|None>
        """
        if self.JIG_CLOSE_GPIO is None:
            self.logger.error("Jig Closed JIG_CLOSE_GPIO Detector not defined (None), returning None")
            # if not using jig_closed_detect feature see note above
            return None

        if self.rpc is None:
            self.logger.error("No rpc handler returning None")
            return None

        answer = json.loads(self.rpc.call_method('read_gpio', self.JIG_CLOSE_GPIO))
        if not answer['success']:
            self.logger.error("Failed to detect Jig Close GPIO")
            return None

        # Example uses an Active LOW for indicating jig is closed
        if answer['result']['state'] != 1:
            self.logger.info("Jig close detected")
        else:
            # squelched log line to avoid flooding log
            self.logger.debug("Jig close NOT detected")

        return not answer['result']['state']

    def show_pass_fail(self, p=False, f=False, o=False):
        """ Set pass/fail indicator

        :param p: <True|False>  set the Pass LED  GREEN
        :param f: <True|False>  set the Fail LED  RED
        :param o: <True|False>  "other" is set    YELLOW
        :return: None
        """
        self.logger.info(f"pass: {p}, fail: {f}, other: {o}")
        if self.rpc is None:
            return

        self.iox_led_green(p)
        self.iox_led_red(f)
        self.iox_led_yellow(o)

    def jig_reset(self):
        """ Called by Prism at the start and end of testing
        - use this callback to set the hardware to a known good reset state
        - should also be called on hardware discovery

        :return:
        """
        with self._lock:
            self.logger.info(f"reset")
            answer = self.rpc.call_method('reset')
            self._rpc_validate(answer)

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Teensy OFF-Module Functions
    #
    # - APIs to features that are off the Teensy module
    # - for example, I2C component APIs, etc
    #

