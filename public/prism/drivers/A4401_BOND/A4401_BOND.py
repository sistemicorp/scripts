#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023-2026
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
except ImportError:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger

DRIVER_TYPE = "A4401_BOND"
DRIVER_TYPE_PROG = "A4401_BOND_PROG"


class A4401_BOND:
    """ BOND (a4401) Teensy 4.1 simpleRPC based driver

    Adding new RPC calls...

    1) Write the RPC function in the matching server/teensy4_server module (*.cpp), and
       declare it in the module header. See rpc_helpers.h for the shape of an RPC function.
    2) Export the function by adding a name and description to interface() in loop(),
       teensy4_server.ino.
    3) Write a method in this class that calls it with self._call().
    4) Add the command to A4401_BOND_cli.py and test it there.
    5) Call it from your test script, see scripts/example/BOND_v0/bond_P00xx.py

    version.h:
    ----------
    There is a version for teensy4_server.ino and for the python code. The version number must be
    the same for testing to run.

    Header definition file:
    -----------------------
    A JSON-like file (// comments allowed) maps each DUT header pin to a MAX11311 port and mode,
    see pogo_hdr_definition._json. A pin may have several modes on different ports, for example
    {"mode": "ADC,GPO", "port": "6,9"}. The header APIs take a header and pin, and look up the
    port for the requested mode.

    """
    GPIO_MODE_INPUT = "INPUT"
    GPIO_MODE_OUTPUT = "OUTPUT"
    GPIO_MODE_INPUT_PULLUP = "INPUT_PULLUP"
    GPIO_MODE_LIST = [GPIO_MODE_INPUT, GPIO_MODE_OUTPUT, GPIO_MODE_INPUT_PULLUP]

    JIG_CLOSE_GPIO = 6  # BUTTON1 GPIO number for Jig Closed detect, set to None if not using
    JIG_CLOSED_STATE = 1  # BUTTON1 reads 1 when the jig is closed

    GPIO_NUMBER_MIN = 0
    GPIO_NUMBER_MAX = 41

    BIST_VOLTAGES = ["V6V", "V5V", "V3V3A", "V3V3D", "V2V5NEG"]

    HDR_NUMBERS = [1, 2, 3, 4]
    HDR_PORT_MIN = 0
    HDR_PORT_MAX = 10  # port 11 is reserved for the self test reference
    HDR_PORT_CAL = 11
    HDR_VBUS = 3
    HDR_VBUS_PORT = 9
    # ports the driver always configures, they are not in the header definition file
    # - port 11 of every header reads the 2.5V reference for self test
    # - HDR3 port 9 drives the VBUS relay for the External USB-C, see vbus_en()
    HDR_FIXED_PORTS = {1: {"ADC": [HDR_PORT_CAL]},
                       2: {"ADC": [HDR_PORT_CAL]},
                       3: {"ADC": [HDR_PORT_CAL], "GPO": [HDR_VBUS_PORT]},
                       4: {"ADC": [HDR_PORT_CAL]}}
    HDR_MODES = ["ADC", "DAC", "GPO", "GPI"]
    HDR_MODES_NONE = [None, "null", "None", "none"]
    HDR_DAC_MV_MAX = 10000
    HDR_GPI_MV_MAX = 2500

    LDO_MV_MIN = 600
    LDO_MV_MAX = 3900

    VBAT_MV_MIN = 1500
    VBAT_MV_MAX = 5000
    VBAT_MV_STEP = 50

    # For Teensy FW version checking the SAME (c code) header file that created the Teensy4
    # firmware is used to check if that firmware is now running (deployed) on Teensy4.
    # if that FW is not running, there is probably a problem!  See method init().
    _version_file = os.path.join(os.path.dirname(__file__), "server/teensy4_server/version.h")

    def __init__(self, port, loggerIn=None, header_def_filename=None):

        if loggerIn:
            self.logger = loggerIn
        else:
            self.logger = StubLogger()

        self._header_def_filename = header_def_filename

        self._lock = threading.Lock()
        self.port = port
        self.rpc = None
        self.a44BOND_max_config = None
        self._hdr_pins = {}  # {hdr: {pin: {mode: port}}}, from the header definition file
        self._jig_closed_last = None

        self.my_version = self._get_version()
        self.logger.info(f"version {self.my_version}")

    def set_port(self, port):
        self.port = port

    def init(self, skip_max11311=False, configure_headers=True):
        """ Init Teensy SimpleRPC connection

        :param skip_max11311: True/False, skips the header definition file entirely.
                              Allows access to other functions (used after FW update)
        :param configure_headers: False reads and checks the header definition file, but does
                              not send it to BOND, BOND keeps its previous configuration
        :return: <True/False> whether Teensy SimpleRPC connection was created
        """
        self.logger.info(f"installing BOND on port {self.port} using {self._header_def_filename}")
        if not skip_max11311 and self._header_def_filename is None:
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
            self.logger.error("version does not match, "
                              f"Python: {self.my_version} "
                              f"Arduino: {version_response['result']['version']}")
            return False

        status_response = self.status()
        if not status_response["success"]:
            self.logger.error("Unable to get status")
            return False
        if status_response["result"]["setup_fail_code"] != 0:
            self.logger.error(f'setup_fail_code {status_response["result"]["setup_fail_code"]}')
            return False

        if not self._jig_close_check():
            return False

        if not skip_max11311:
            if not self._load_config(self._header_def_filename):
                return False

            if configure_headers and not self._init_maxs():
                self.logger.error("Failed to init MAX11311 pins")
                return False

        # check bist voltages
        for _v in self.BIST_VOLTAGES:
            status_response = self.bist_voltage(_v)
            if not status_response["success"]:
                self.logger.error(f"bist_voltage {_v} {status_response}")
                return False

            if not status_response["result"]["pass"]:
                self.logger.error(f"bist_voltage {_v} {status_response}")
                return False

        status_response = self.reset()
        if not status_response["success"]:
            self.logger.error(f"reset {status_response}")
            return False

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
        try:
            self.rpc.close()
        except (SerialException, OSError) as e:
            self.logger.error(e)
        self.rpc = None
        return True

    # ----------------------------------------------------------------------------------------------
    # Helper Functions
    #
    # - function names should all begin with "_"
    # - functions are all private to this class

    def _call(self, method, *args, squelch=False):
        """ Call an RPC method on BOND

        :param method: RPC method name
        :param args: RPC arguments
        :param squelch: True does not log the call or a successful answer
        :return: {'success': <True/False>, 'method': <method>, 'result': {...}}
        """
        with self._lock:
            if not squelch:
                self.logger.info(f"{method} {args}" if args else method)

            if self.rpc is None:
                return self._error(method, "not connected")

            try:
                answer = self.rpc.call_method(method, *args)

            except (SerialException, OSError, ValueError, TypeError) as e:
                self.logger.error(f"{method}: {e}")
                return self._error(method, str(e))

            return self._rpc_validate(answer, squelch)

    def _error(self, method, error):
        return {'success': False, 'method': method, 'result': {'error': error}}

    def _load_config(self, header_def_filename):
        """ Read and check the json-like header definition file

        Sets self.a44BOND_max_config and self._hdr_pins
        :return: True/False
        """
        self.logger.info(f"Attempting to read MAX11311 config from {header_def_filename}...")
        if not os.path.exists(header_def_filename):
            self.logger.error(f"Header pin definition filename {header_def_filename} "
                              "does not exist")
            return False

        try:
            with open(header_def_filename) as f:
                config = jstyleson.loads(f.read())

        except Exception as e:
            self.logger.error(e)
            self.logger.error(traceback.format_exc())
            return False

        hdr_pins = {}
        for k, v in config.items():
            if not k.isdigit():
                continue

            hdr = int(k)
            if hdr not in self.HDR_NUMBERS:
                self.logger.error(f"HDR {k}, invalid header number")
                return False

            for key, limit in [("gpo_mv", self.HDR_DAC_MV_MAX), ("gpi_mv", self.HDR_GPI_MV_MAX)]:
                if not isinstance(v.get(key), int) or not (0 <= v[key] <= limit):
                    self.logger.error(f"HDR {k}, {key} must be an int 0 to {limit}")
                    return False

            pins = {}
            ports_used = {}
            for pin, pin_config in v.items():
                # some items in the JSON are not pins, skip them
                if not pin.isdigit():
                    continue

                pins[int(pin)] = {}
                mode, port = pin_config.get("mode"), pin_config.get("port")
                if mode in self.HDR_MODES_NONE:
                    continue

                modes = [m.strip() for m in str(mode).split(",")]
                try:
                    ports = [int(p) for p in str(port).split(",")]
                except ValueError:
                    self.logger.error(f"HDR {k}, pin {pin}, invalid port {port}")
                    return False

                if len(ports) != len(modes):
                    self.logger.error(f"HDR {k}, pin {pin}, modes and ports must be equal lengths")
                    return False

                for m, p in zip(modes, ports):
                    if m not in self.HDR_MODES:
                        self.logger.error(f"HDR {k}, pin {pin}, invalid mode {m}")
                        return False
                    if not (self.HDR_PORT_MIN <= p <= self.HDR_PORT_MAX):
                        self.logger.error(f"HDR {k}, pin {pin}, port {p} not "
                                          f"{self.HDR_PORT_MIN}-{self.HDR_PORT_MAX}")
                        return False
                    if p in sum(self.HDR_FIXED_PORTS[hdr].values(), []):
                        self.logger.error(f"HDR {k}, pin {pin}, port {p} is reserved for BOND")
                        return False
                    if p in ports_used:
                        self.logger.error(f"HDR {k}, pin {pin}, port {p} already used by "
                                          f"pin {ports_used[p]}")
                        return False
                    if m in pins[int(pin)]:
                        self.logger.error(f"HDR {k}, pin {pin}, mode {m} used twice")
                        return False
                    ports_used[p] = pin
                    pins[int(pin)][m] = p

            hdr_pins[hdr] = pins

        self.a44BOND_max_config = config
        self._hdr_pins = hdr_pins
        return True

    def _init_maxs(self):
        """ Send the header definition to BOND, and optionally recalibrate the battery emulator

        :return: True/False
        """
        for hdr, pins in self._hdr_pins.items():
            ports = {m: list(self.HDR_FIXED_PORTS[hdr].get(m, [])) for m in self.HDR_MODES}
            for pin, modes in pins.items():
                for m, p in modes.items():
                    ports[m].append(p)
            for m in ports:
                ports[m].sort()
            self.logger.info(f"HDR {hdr} ports {ports}")

            config = self.a44BOND_max_config[str(hdr)]
            answer = self._call('bond_max_hdr_init', hdr,
                                ports["ADC"], len(ports["ADC"]),
                                ports["DAC"], len(ports["DAC"]),
                                ports["GPO"], len(ports["GPO"]),
                                ports["GPI"], len(ports["GPI"]),
                                config["gpo_mv"], config["gpi_mv"])
            if not answer['success']:
                self.logger.error(f"failed to init: {answer}")
                return False

        # BOND calibrates the battery emulator at power up, this repeats it
        if self.a44BOND_max_config.get('calibrate_battery_emulator', False):
            self.logger.info("Calibrating Battery Emulator...")
            answer = self._call('bond_batt_emu_cal')
            if not answer['success']:
                self.logger.error(f"bond_batt_emu_cal failed: {answer}")
                return False
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

        if not (self.GPIO_NUMBER_MIN <= self.JIG_CLOSE_GPIO <= self.GPIO_NUMBER_MAX):
            self.logger.error(f"Invalid Jig Closed GPIO {self.JIG_CLOSE_GPIO}")
            return False

        answer = self.init_gpio(self.JIG_CLOSE_GPIO, self.GPIO_MODE_INPUT_PULLUP)
        if not answer['success']:
            self.logger.error(f"Jig Closed GPIO init failed {answer}")
            return False
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
            answer = {"success": False, "result": {"error": f"invalid response: {e}"}}

        return answer

    def _bond_check_hdr_pin(self, method, hdr, pin, mode):
        """ Find the MAX11311 port for a header pin in a mode

        :return: <port>, None | None, <error response>
        """
        if self.a44BOND_max_config is None:
            self.logger.error("Attempt to use MAX11311 before configured")
            return None, self._error(method, "MAX11311 not configured")

        try:
            hdr, pin = int(hdr), int(pin)
        except (TypeError, ValueError):
            return None, self._error(method, f'Invalid parameter hdr {hdr} pin {pin}')

        if hdr not in self._hdr_pins:
            self.logger.error(f'Invalid parameter hdr {hdr}')
            return None, self._error(method, f'Invalid parameter hdr {hdr}')

        if pin not in self._hdr_pins[hdr]:
            self.logger.error(f'Invalid parameter pin {pin}')
            return None, self._error(method, f'Invalid parameter pin {pin}')

        modes = self._hdr_pins[hdr][pin]
        if mode not in modes:
            err = f'Invalid mode hdr {hdr} pin {pin} mode {mode} not in {list(modes)}'
            self.logger.error(err)
            return None, self._error(method, err)

        return modes[mode], None

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
        return list(self.rpc.device['methods'])

    def unique_id(self):
        """ unique id
        :return: {'success': True, 'method': 'unique_id', 'result': {'unique_id': <MAC>}}
        """
        return self._call('unique_id')

    def slot(self):
        """ slot (deprecated, slots are ordered by USB path)
        :return: {'success': True, 'method': 'slot', 'result': {'id': <int>}}
        """
        return self._call('slot')

    def version(self):
        """ Version
        :return: {'success': True, 'method': 'version', 'result': {'version': '0.2.0'}}
        """
        return self._call('version')

    def status(self):
        """ Status
        :return: {'success': True, 'method': 'status',
                  'result': {'setup_fail_code': 0, 'stack_kb': <>, 'heap_kb': <>, 'psram_kb': <>}}
        """
        return self._call('status')

    def reset(self):
        """ reset BOND to the DUT safe state (not a Teensy reset)
        - VDUT and VBAT disconnected, self test off, header DACs 0V, header GPOs idle
        :return: {'success': True, 'method': 'reset', 'result': {}}
        """
        return self._call('reset')

    def reboot_to_bootloader(self):
        """ reboot
        :return: success = True/False, method = reset
        """
        try:
            with self._lock:
                self.logger.info("reboot_to_bootloader")
                self.rpc.call_method('reboot_to_bootloader')
                # reboot will not return, expect SerialException exception, fake the return success

        except SerialException:
            pass

        except Exception as e:
            self.logger.error(e)
            return {"success": False, "method": "reboot_to_bootloader", "result": {}}

        return {"success": True, "method": "reboot_to_bootloader", "result": {}}

    def led(self, set):
        """ Teensy module LED on/off
        :param set: True/False
        :return: {'success': True, 'method': 'set_led', 'result': {'state': 'on'|'off'}}
        """
        return self._call('set_led', set)

    def read_adc(self, pin_number, sample_num=1, sample_rate_ms=1):
        """ Read an ADC pin
        - This is a BLOCKING function
        - result is raw ADC value, client needs to scale to VREF (3.3V)

        :param pin_number: (0 - 41)
        :param sample_num: Number of samples to average over, 1-1000
        :param sample_rate_ms: Millisecond delay between samples
        :return: {'success': True, 'method': 'read_adc', 'result': {'reading': <int>}}
        """
        return self._call('read_adc', pin_number, sample_num, sample_rate_ms)

    def init_gpio(self, pin_number, mode):
        """ Init GPIO
        :param pin_number: (0 - 41)
        :param mode: A4401_BOND.GPIO_MODE_*
        :return: {'success': True, 'method': 'init_gpio', 'result': {'mode': <mode>}}
        """
        if mode not in self.GPIO_MODE_LIST:
            err = "Invalid mode {} not in {}".format(mode, self.GPIO_MODE_LIST)
            self.logger.error(err)
            return self._error('init_gpio', err)

        return self._call('init_gpio', pin_number, mode.encode())

    def read_gpio(self, pin_number):
        """ Get GPIO
        :param pin_number: (0 - 41)
        :return: {'success': True, 'method': 'read_gpio', 'result': {'state': 1|0}}
        """
        squelch = pin_number == self.JIG_CLOSE_GPIO  # squelch jig closed polling
        return self._call('read_gpio', pin_number, squelch=squelch)

    def write_gpio(self, pin_number, state: bool):
        """ Set GPIO
        :param pin_number: (0 - 41)
        :param state: True/False
        :return: {'success': True, 'method': 'write_gpio', 'result': {'state': True|False}}
        """
        return self._call('write_gpio', pin_number, state)

    def bist_voltage(self, name):
        """ Read BIST voltage

        :param name: one of BIST_VOLTAGES (checked by teensy server side)
        :return: {'success': True, 'method': 'bist_voltage',
                  'result': {'name': 'V5V', 'mv': 5008, 'tol_mv': 200, 'pass': True}}
        """
        return self._call('bist_voltage', name.encode())

    def temperature(self):
        """ Read TMP1075

        :return: {'success': True, 'method': 'temperature', 'result': {'temp_degC': 30.3125}}
        """
        return self._call('temperature')

    def vdut_read(self):
        """ Read INA226 for VDUT

        :return: {'success': True, 'method': 'vdut_read', 'result': {'v': 3.0, 'ima': 0.05}}
        """
        return self._call('vdut_read')

    def vdut_set(self, mv: int):
        """ Set VDUT Voltage in mV, 1000-9000
        - BOND has a 10ms internal settling time, and checks the measured voltage

        :return: {'success': True, 'method': 'vdut_set',
                  'result': {'mv': 3000, 'measured_mv': 3001}}
        """
        return self._call('vdut_set', mv)

    def vdut_get_fault(self):
        """ VDUT TPS55289 faults

        :return: {'success': True, 'method': 'vdut_get_fault',
                  'result': {'short_protection': False, 'over_current_protection': False,
                             'over_voltage_protection': False, 'mode': 'buck'}}
        """
        return self._call('vdut_get_fault')

    def vdut_reset(self):
        """ VDUT TPS55289 reset and re-init
        - the VDUT voltage must be set again after this

        :return: {'success': True, 'method': 'vdut_reset', 'result': {}}
        """
        return self._call('vdut_reset')

    def vbat_read(self):
        """ Read INA226 for VBAT

        :return: {'success': True, 'method': 'vbat_read',
                  'result': {'v': 3.99875, 'ima': 20.50781}}
        """
        return self._call('vbat_read')

    def vbat_set(self, mv: int):
        """ Set VBAT (Battery emulator), 1500-5000 mV in 50 mV steps
        - BOND has a 50ms internal settling time, and checks the measured voltage

        :return: {'success': True, 'method': 'vbat_set',
                  'result': {'mv': <int>, 'measured_mv': <int>}}
        """
        return self._call('vbat_set', mv)

    def vdut_en(self, state: bool):
        """ VDUT SMPS Enable/Disable

        :return: {'success': True, 'method': 'vdut_en',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('vdut_en', state)

    def vdut_con(self, state: bool):
        """ VDUT SMPS Connect to DUT
        - there is no delay on BOND for voltages to settle

        :return: {'success': True, 'method': 'vdut_con',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('vdut_con', state)

    def vbus_en(self, state: bool):
        """ VBUS on the External USB-C connector, relay driven by header 3 port 9

        :return: {'success': True, 'method': 'vbus_en', 'result': {'assert': True, 'level': False}}
        """
        return self._call('vbus_en', state)

    def bond_ldo_set(self, mv: int):
        """ Header 1 LDO output voltage (header 1 pin 1), 600-3900 mV
        - set by the IOX LDO_ADJ DAC, the LDO is enabled by the header 1 pin 1 GPO,
          see bond_max_hdr_gpo(1, 1, True)
        - header 1 pin 9 is the LDO output feedback, read it with bond_max_hdr_adc(1, 9)

        :return: {'success': True, 'method': 'bond_ldo_set',
                  'result': {'mv': <int>, 'dac_raw': <int>}}
        """
        if not (self.LDO_MV_MIN <= mv <= self.LDO_MV_MAX):
            return self._error('bond_ldo_set', f'Invalid parameter mv {mv}')
        return self._call('bond_ldo_set', mv)

    def iox_led_green(self, state: bool):
        """ MAX11311 IOX, green LED (PASS)

        :return: {'success': True, 'method': 'iox_led_green',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_led_green', state)

    def iox_led_yellow(self, state: bool):
        """ MAX11311 IOX, yellow LED

        :return: {'success': True, 'method': 'iox_led_yellow',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_led_yellow', state)

    def iox_led_red(self, state: bool):
        """ MAX11311 IOX, red LED (FAIL)

        :return: {'success': True, 'method': 'iox_led_red',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_led_red', state)

    def iox_led_blue(self, state: bool):
        """ MAX11311 IOX, blue LED

        :return: {'success': True, 'method': 'iox_led_blue',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_led_blue', state)

    def iox_selftest(self, state: bool):
        """ MAX11311 IOX, connect the self test load

        :return: {'success': True, 'method': 'iox_selftest',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_selftest', state)

    def iox_vbat_en(self, state: bool):
        """ Enable VBAT (battery emulator)

        :return: {'success': True, 'method': 'iox_vbat_en',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_vbat_en', state)

    def iox_vbat_con(self, state: bool):
        """ Connect VBAT to DUT
        - there is no delay on BOND for voltages to settle

        :return: {'success': True, 'method': 'iox_vbat_con',
                  'result': {'assert': False, 'level': False}}
        """
        return self._call('iox_vbat_con', state)

    def bond_batt_emu_cal(self):
        """ Recalibrate the battery emulator (BOND calibrates it at power up)

        :return: {'success': True, 'method': 'bond_batt_emu_cal', 'result': {}}
        """
        return self._call('bond_batt_emu_cal')

    def bond_max_hdr_adc_cal(self, hdr: int):
        """ MAX11311 Header <1-4> read ADC CAL (port 11) voltage
        - expected result is always 2500 +/- error

        :return: {'success': True, 'method': 'bond_max_hdr_adc_cal', 'result': {'mV': <int>}}
        """
        return self._call('bond_max_hdr_adc_cal', hdr)

    def bond_max_hdr_adc(self, hdr: int, pin: int):
        """ MAX11311 Header <1-4> pin read ADC voltage, 0-10000 mV
        - get port from pin, and also check mode

        :return: {'success': True, 'method': 'bond_max_hdr_adc', 'result': {'mV': <int>}}
        """
        port, error = self._bond_check_hdr_pin('bond_max_hdr_adc', hdr, pin, "ADC")
        if error:
            return error
        return self._call('bond_max_hdr_adc', hdr, port)

    def bond_max_hdr_dac(self, hdr: int, pin: int, mv: int):
        """ MAX11311 Header <1-4> pin write DAC voltage <mv>, 0-10000 mV
        - get port from pin, and also check mode
        - dac raw is mv * 4096 / 10000, max 4095

        :return: {'success': True, 'method': 'bond_max_hdr_dac',
                  'result': {'mV': <int>, 'dac_raw': <int>}}
        """
        port, error = self._bond_check_hdr_pin('bond_max_hdr_dac', hdr, pin, "DAC")
        if error:
            return error

        if not (0 <= mv <= self.HDR_DAC_MV_MAX):
            return self._error('bond_max_hdr_dac', f'Invalid parameter mv {mv}')

        return self._call('bond_max_hdr_dac', hdr, port, mv)

    def bond_max_hdr_gpo(self, hdr: int, pin: int, state: bool):
        """ MAX11311 Header <1-4> pin write GPO state
        - logic high level is the header "gpo_mv"

        :return: {'success': True, 'method': 'bond_max_hdr_gpo', 'result': {'state': True|False}}
        """
        port, error = self._bond_check_hdr_pin('bond_max_hdr_gpo', hdr, pin, "GPO")
        if error:
            return error
        return self._call('bond_max_hdr_gpo', hdr, port, state)

    def bond_max_hdr_gpi(self, hdr: int, pin: int):
        """ MAX11311 Header <1-4> pin read GPI state
        - threshold is the header "gpi_mv"

        :return: {'success': True, 'method': 'bond_max_hdr_gpi', 'result': {'state': 1|0}}
        """
        port, error = self._bond_check_hdr_pin('bond_max_hdr_gpi', hdr, pin, "GPI")
        if error:
            return error
        return self._call('bond_max_hdr_gpi', hdr, port)

    # DEBUG APIs

    def bond_debug_batt_emu(self):
        """ DEBUG: Battery emulator LUT, first 10 entries
        :return: {'success': True, 'method': 'debug_batt_emu',
                  'result': {'vbat': [<mV>, ...], 'dac': [<int>, ...]}}
        """
        return self._call('debug_batt_emu')

    #
    # API (wrapper functions)
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Prism Player Callback functions
    #

    def jig_closed_detect(self):
        """ Read Jig Closed feature on Teensy
        This is used by Prism Player logic
        True - Jig Closed (testing will start)
        False - Jig Open
        None - Not implemented, or error

        # NOTE: !! if not using jig_closed_detect the play function should be None
        #          See hwdrv_A4401_BOND.py:discover_channels()

        return: <True|False|None>
        """
        if self.JIG_CLOSE_GPIO is None:
            self.logger.error("Jig Closed JIG_CLOSE_GPIO not defined (None), returning None")
            # if not using jig_closed_detect feature see note above
            return None

        if self.rpc is None:
            self.logger.error("No rpc handler returning None")
            return None

        answer = self.read_gpio(self.JIG_CLOSE_GPIO)
        if not answer['success']:
            self.logger.error("Failed to detect Jig Close GPIO")
            return None

        closed = answer['result']['state'] == self.JIG_CLOSED_STATE
        if closed != self._jig_closed_last:  # log changes only, this is polled
            self.logger.info(f"Jig closed: {closed}")
            self._jig_closed_last = closed

        return closed

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

        :return: reset() response
        """
        return self.reset()

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------
