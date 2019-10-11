#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019
"""
import _thread
import time
import pyb
import micropython
import array
import machine

from iba01_perphs import Peripherals
from iba01_queue import MicroPyQueue
from iba01_supply12 import Supply12
from iba01_const import *

micropython.alloc_emergency_exception_buf(100)
__DEBUG_FILE = "iba01_server"


class MicroPyServer(object):
    """ Async Worker MicroPython Worker
    - runs in its own thread

    How to use this:
        - copy this file over to micropython
        - import it, import iba01_server, this will cause it to "run"
        - send in a command via the q,
            iba01_server.server.cmd({"method":"toggle_led", "args":1})
            iba01_server.server.cmd({"method":"enable_jig_closed_detect", "args":True})
        - to get a result,
            iba01_server.server.ret()

    cmds: Are in this format: {"method": <class_method>, "args": <args>}

    ret: Are in this format: {"method": <class_method>, "value": <value>}

    Notes:
        1) you cannot use print(), Instead, use the self._debug() API.

        2) debug new code with rshell/REPL.  'import upyb_server'
           and then execute commands,
               >>> iba01_server.server.cmd({'method': 'version', 'args': {}})
               >>> iba01_server.server.ret()

    """
    VERSION = "0.2"
    SERVER_CMD_SLEEP_MS = 100  # polling time for processing new commands

    LED_RED    = 1
    LED_GREEN  = 2
    LED_YELLOW = 3
    LED_BLUE   = 4

    # Valid ADC pins to read voltage.
    # 1) X1 is NOT included because it its reserved for jig closed detection
    # 2)
    ADC_VALID_PINS = ["X2",  "X3",  "X4",  "X5",  "X6",  "X7",  "X8",
                      "X11", "X12", "X19", "X20", "X21", "X22", "Y11", "Y8"]
    ADC_VALID_INTERNALS = ["VBAT", "TEMP", "VREF", "VDD"]
    ADC_READ_MULTI_TIMER = 8
    ADC_MAX_FREQ = 10000
    ADC_MAX_SAMPLES = 1000

    JIG_CLOSED_TIMER = 4
    JIG_CLOSED_TIMER_FREQ = 1  # Hz
    JIG_CLOSED_PIN = "X1"

    SUPPLY_NAMES = ["V1", "V2"]

    def __init__(self, debug=False):
        self.lock = _thread.allocate_lock()
        self._cmd = MicroPyQueue()
        self._ret = MicroPyQueue()
        self._debug_flag = True  # set True to catch any class init errors
        self._ina01 = False

        # use dict to store static data
        self.ctx = {
            "threads": {},
            "gpio": {},            # gpios used are named here
            "timers": {},          # timers running are listed here
            "adc_read_multi": {},  # cache args
            "perphs": None,
            "V1": None,
            "V2": None,
            "VBAT": None,
        }

        self.ctx["perphs"] = Peripherals(debug_print=self._debug)
        self.is_ina01 = self.ctx["perphs"].is_iba01()

        if self.is_ina01:
            self.ctx['V1'] = Supply12(self.ctx["perphs"], V1_I2C_ADDR, "V1", debug_print=self._debug, type=0)
            self.ctx['V2'] = Supply12(self.ctx["perphs"], V2_I2C_ADDR, "V2", debug_print=self._debug, type=1)

        self._debug_flag = debug

    # ===================================================================================
    # Public API to send commands and get results from the MicroPy Server
    # NOTE: "results" must be print()'ed to be return values on the serial (repl) port

    def cmd(self, cmd):
        """ Send (Add) a command to the MicroPy Server command queue
        - commands are executed in the order they are received

        :param cmd: dict format {"method": <class_method>, "args": <args>}
        :return: success (True/False)
        """
        if not isinstance(cmd, dict):
            self._ret.put({"method": "cmd", "value": "cmd must be a dict", "success": False})
            return False

        if not cmd.get("method", False):
            self._ret.put({"method": "cmd", "value": "cmd dict must have method key", "success": False})
            return False

        if not getattr(self, cmd["method"], False):
            self._ret.put({"method": "cmd", "value": "'{}' invalid method".format(cmd["method"]), "success": False})
            return False

        self._cmd.put(cmd)
        return True

    def ret(self, method=None, all=False):
        """ return result(s) of command

        :param method: string, if specified, only results of that command are returned
        :param all: is set True, will return all commands, otherwise only ONE return result is retrieved
        :return:
        """
        _ret = self._ret.get(method, all)
        print(_ret)
        return True

    def peek(self, method=None, all=False):
        ret = self._ret.peek(method, all)
        print(ret)
        return True

    def update(self, item_update):
        return self._ret.update(item_update)

    # ===================================================================================
    # private

    def _run(self):
        # run on thread
        while True:
            item = self._cmd.get()
            if item:
                method = item[0]["method"]
                args = item[0]["args"]
                method = getattr(self, method, None)
                if method is not None:
                    method(args)
                    # methods should always be found because they are checked before being queued

            # allows other threads to run, but generally speaking there should be no other threads(?)
            time.sleep_ms(self.SERVER_CMD_SLEEP_MS)

    def _debug(self, msg, line=0, file=__DEBUG_FILE, name="unknown"):
        """ Add debug statement

        :param msg:
        :param line:
        :return:
        """
        if self._debug_flag:
            self._ret.put({"method": "_debug", "value": "{:15s}:{:10s}:{:4d}: {}".format(file, name, line, msg), "success": True})

    def _is_timer_running(self, timer_name):
        return timer_name in self.ctx["timer"]

    def _init_gpio(self, name, pin, mode, pull=pyb.Pin.PULL_NONE):
        self.ctx["gpio"][name] = pyb.Pin(pin, mode, pull)

    # ===================================================================================
    # Methods
    # NOTES:
    # 1. !! DON'T access public API, ret/peek/update/cmd, functions, access the queue's directly
    #    Else probably get into a lock lockup

    def unique_id(self, args):
        """ Get the Unique ID of the Micro Pyboard

        args: None
        :return:
        """
        id_bytes = machine.unique_id()
        res = ""
        for b in id_bytes[::-1]:
            res += "%02x" % b
        self._ret.put({"method": "unique_id", "value": {'value':res}, "success": True})

    def debug(self, args):
        """ enable debugging

        args: { 'enable': True/False }
        :param enable: boolean
        :return: self.VERSION
        """
        self._debug_flag = args.get("enable", False)
        self._ret.put({"method": "debug", "value": {'value': self._debug_flag}, "success": True})

    def version(self, args):
        """ version

        :param args: not used
        :return: self.VERSION
        """
        self._debug("testing message", 217)
        self._ret.put({"method": "version", "value": {'value': self.VERSION}, "success": True})

    def _toggle_led(self, led, on_ms, off_ms, once=False):
        thread_name = "led{}".format(led)
        while self.ctx["threads"][thread_name]:
            pyb.LED(led).on()
            time.sleep_ms(on_ms)
            if off_ms:
                pyb.LED(led).off()
                time.sleep_ms(off_ms)
            if once: break

        self.ctx["threads"][thread_name] = False
        pyb.LED(led).off()

    def led_toggle(self, args):
        """ Toggle LED on
        - a led is toggled on its own thread

        args: { 'led': <#>, 'on_ms': <#>, 'off_ms': <#> }
        :param led: one of LED_*
        :param on_ms: milli seconds on, if 0 the led will be turned off
        :param off_ms: milli seconds off
        :param once: if set, LED is toggled on for on_ms and then off, does not repeat
        :return: success (True/False)
        """
        led = args.get("led", None)
        on_ms = args.get("on_ms", 500)
        off_ms = args.get("off_ms", 500)
        once = args.get("once", False)
        if not led in [self.LED_BLUE, self.LED_GREEN, self.LED_RED, self.LED_YELLOW]:
            value = {'err': "unknown led {}".format(led)}
            self._ret.put({"method": "led_toggle", "value": value, "success": False})
            return

        thread_name = "led{}".format(led)
        if on_ms > 0:
            if thread_name not in self.ctx["threads"] or not self.ctx["threads"][thread_name]:
                self.ctx["threads"][thread_name] = True
                _thread.start_new_thread(self._toggle_led, (led, on_ms, off_ms, once))

            else:
                # thread appears to already be running... do nothing...
                pass

        else:
            if thread_name in self.ctx["threads"]:
                self.ctx["threads"][thread_name] = False

        self._ret.put({"method": "led_toggle", "value": {'value': True}, "success": True})

    def jig_closed_detect(self, args):
        """ Normal context ISR handler
        - scheduled by _isr_jig_closed_detect()
        - if there is a jig msg in the queue, then it hasn't been read yet,
          and we don't put in a new state unless the previous state has been read

        :param _:
        :return:
        """
        msgs = self._ret.peek("jig_closed_detect")
        # msg in queue still waiting to be processed
        if msgs: return

        if "jig_closed" not in self.ctx['gpio']:
            pin = args.get("pin", self.JIG_CLOSED_PIN)
            self._init_gpio("jig_closed", pin, pyb.Pin.IN, pyb.Pin.PULL_UP)

        # if the pin is HIGH, the jig is open
        jig_pin_state = self.ctx["gpio"]["jig_closed"].value()

        if jig_pin_state: value = {'value': "OPEN"}
        else: value = {'value': "CLOSED"}
        self._ret.put({"method": "jig_closed_detect", "value": value, "success": True})

    def init_gpio(self, args):
        """ init gpio
        - a gpio must be set before it can be used
        - see https://docs.micropython.org/en/latest/library/pyb.Pin.html#pyb-pin

        args:
        :param name: assign name to gpio for reference
        :param pin: pin name of gpio, X1,X2, ...
        :param mode: one of pyb.Pin.IN, Pin.OUT_PP, Pin.OUT_OD, ..
        :param pull: one of pyb.Pin.PULL_NONE, pyb.Pin.PULL_UP, pyb.Pin.PULL_DN
        :return: None
        """
        name = args.get("name", None)
        pin = args.get("pin", None)
        mode = args.get("mode")
        pull = args.get("pull", pyb.Pin.PULL_NONE)
        if None in [name, pin, mode]:
            self._ret.put({"method": "init_gpio", "value": "missing or None parameter", "success": False})
            return

        value = {}
        if name in self.ctx['gpio']: value["action"] = "updating previously created"
        else:  value["action"] = "creating"

        self._init_gpio(name, pin, mode, pull)
        self._ret.put({"method": "init_gpio", "value": value, "success": False})

    def get_gpio(self, name):
        if name not in self.ctx["gpio"]:
            self._ret.put({"method": "get_gpio", "value": "{} has not been init_gpio".format(name), "success": False})
            return

        value = self.ctx["gpio"][name].value()
        self._ret.put({"method": "get_gpio", "value": "{}".format(value), "success": True})

    def set_gpio(self, name, value):
        if name not in self.ctx["gpio"]:
            self._ret.put({"method": "set_gpio", "value": "{} has not been init_gpio".format(name), "success": False})
            return

        if value:
            self.ctx["gpio"][name].high()
        else:
            self.ctx["gpio"][name].low()

    def adc_read(self, args):
        """ (simple) read ADC on a pin
        - this is a blocking call

        args:
        :param pin: pin name of gpio, X1, X2, ... or VBAT, TEMP, VREF, VDD
        :param samples: number of samples to take and then calculate average, default 1
        :param sample_ms: number of milliseconds between samples, default 1
        :return:
        """
        pin = args.get("pin", None)
        if pin not in self.ADC_VALID_PINS and pin not in self.ADC_VALID_INTERNALS:
            value = {'err': "{} pin is not valid".format(pin)}
            self._ret.put({"method": "adc_read", "value": value, "success": False})
            return

        samples = args.get("samples", 1)
        sample_ms = args.get("sample_ms", 1)

        # print("DEBUG: test")

        adc = None
        adc_read = None
        if pin in self.ADC_VALID_PINS:
            adc = pyb.ADC(pyb.Pin('{}'.format(pin)))
            adc_read = adc.read

        else:
            adc = pyb.ADCAll(12, 0x70000)

            if pin == "TEMP":
                adc_read = adc.read_core_temp
            elif pin == "VBAT":
                adc_read = adc.read_core_vbat
            elif pin == "VREF":
                adc_read = adc.read_core_vref
            elif pin == "VDD":
                adc_read = adc.read_vref

        if adc is None or adc_read is None:
            value = {'err': "{} pin is not valid (internal error)".format(pin)}
            self._ret.put({"method": "adc_read", "value": value, "success": False})
            return

        results = []
        for i in range(samples):
            results.append(float(adc_read()))
            if sample_ms:
                time.sleep_ms(sample_ms)

        sum = 0
        for r in results: sum += r
        result = float(sum / len(results))

        value = {'value': result, "samples": samples}
        self._ret.put({"method": "adc_read", "value": value, "success": True})

    def _adc_read_multi(self, _):
        """ async callback for adc_read_multi
        - args for this function are cached in self.ctx["adc_read_multi"]

        :param _: not used
        :return:
        """
        args = self.ctx["adc_read_multi"]
        freq = args.get("freq", 100)
        samples = args.get("samples", 100)
        pins = args.get("pins", None)

        adcs = []
        results = []
        for pin in pins:
            adcs.append(pyb.ADC(pyb.Pin('{}'.format(pin))))
            results.append(array.array('H', (0 for i in range(samples))))

        tim = pyb.Timer(self.ADC_READ_MULTI_TIMER, freq=freq)  # Create timer
        pyb.ADC.read_timed_multi(adcs, results, tim)
        tim.deinit()

        # reformat results to be a simple list
        value = {"samples": samples, "freq": freq}
        for idx, result in enumerate(results):
            value[pins[idx]] = [r for r in result]

        self._ret.put({"method": "adc_read_multi_results", "value": value, "success": True})

    def adc_read_multi(self, args):
        """ ADC read multiple pins, multiple times, at a given frequency
        - this is non-blocking, the action is scheduled later

        args:
        :param pins: list of pins name of gpio, X1, X2, ... or vbat, temp, vref, core_vref
        :param freq: frequency of taking samples (1 - 10kHz), default 100 Hz
        :param samples: total samples to take (1 - 1000), default 100
        :return:
        """
        freq = args.get("freq", 100)
        if not (0 < freq <= self.ADC_MAX_FREQ):
            value = {'err': "freq not within range supported, 0 < f <= {}".format(self.ADC_MAX_FREQ)}
            self._ret.put({"method": "adc_read_multi", "value": value, "success": False})
            return

        samples = args.get("samples", 100)
        if not (0 < samples <= self.ADC_MAX_SAMPLES):
            value = {'err': "samples not within range supported, 0 < s <= {}".format(self.ADC_MAX_SAMPLES)}
            self._ret.put({"method": "adc_read_multi", "value": value, "success": False})
            return

        pins = args.get("pins", None)
        if not isinstance(pins, list):
            value = {'err': "pins must be a list"}
            self._ret.put({"method": "adc_read_multi", "value": value, "success": False})
            return
        for pin in pins:
            if pin not in self.ADC_VALID_PINS:
                value = {'err': "{} pin is not valid".format(pin)}
                self._ret.put({"method": "adc_read_multi", "value": value, "success": False})
                return

        # everything is good, store the params
        self.ctx["adc_read_multi"] = args

        # schedule adc multi to run later
        micropython.schedule(self._adc_read_multi, 0)
        self._ret.put({"method": "adc_read_multi", "value": {'value': 'scheduled'}, "success": True})

    # ===============================================================================================
    # IBA01 - Interface Board A01 APIs

    def supply_enable(self, args):
        """ Enable Supply,set Voltage, calibrate
        - voltage is set first
        - calibration only occurs if supply is enabled

        :param args: {"name": <"V1"|"V2">,
                      'enable': <True|False>,      # default: True
                      "voltage_mv": <voltage_mv>,  # if not specified, current setting and PG is returned
                      "cal": <True|False>}         # default: True
        return: {...}
        """
        if not self.is_ina01:
            value = {'err': "IBA01 not present"}
            self._ret.put({"method": "supply_current", "value": value, "success": False})
            return

        name = args.get('name', False)
        if name not in self.SUPPLY_NAMES:
            value = {'err': "supply name {} not in {}".format(name, self.SUPPLY_NAMES)}
            self._ret.put({"method": "supply_current", "value": value, "success": False})
            return

        enable = args.get('enable', True)
        voltage_mv = args.get('voltage_mv', False)
        calibrate = args.get('cal', True)

        if voltage_mv:
            success, pg_or_err = self.ctx[name].voltage_mv(voltage_mv=voltage_mv)
            if not success:
                value = "{} enable={}, voltage_mv={}, err {}".format(name, enable, voltage_mv, pg_or_err)
                self._ret.put({"method": "supply_enable", "value": value, "success": False})
                return

        else:
            _, voltage_mv = self.ctx[name].get_enable_voltage_mv()
            _, pg_or_err = self.ctx[name].power_good()

        success, en = self.ctx[name].enable(enable=enable)
        if not success:
            self._ret.put({"method": "supply_enable", "value": "{} enable failed".format(name), "success": False})
            return

        if en and calibrate:
            success, _ = self.ctx[name].calibrate()
            if not success:
                value = "{} failed self calibration".format(name)
                self._ret.put({"method": "supply_enable", "value": value, "success": False})
                return

        value = {
            'name': name,
            'enable': en,
            'voltage_mv': voltage_mv,
            'pg': pg_or_err,
        }
        self._ret.put({"method": "supply_enable", "value": value, "success": True})

    def supply_current(self, args):
        """ Measure Supply Current

        :param args: {"name": <"V1"|"V2">, }
        return: {...}
        """
        if not self.is_ina01:
            value = {'err': "IBA01 not present"}
            self._ret.put({"method": "supply_current", "value": value, "success": False})
            return

        name = args.get('name', False)
        if name not in self.SUPPLY_NAMES:
            value = {'err': "supply name {} not in {}".format(name, self.SUPPLY_NAMES)}
            self._ret.put({"method": "supply_current", "value": value, "success": False})
            return

        success, current_ua = self.ctx[name].current_ua()
        if not success:
            value = {'err': "{} failed current_ua".format(name)}
            self._ret.put({"method": "supply_current", "value": value, "success": False})
            return

        enable, voltage_mv = self.ctx[name].get_enable_voltage_mv()
        _, pg_or_err = self.ctx[name].power_good()

        value = {
            'name': name,
            'enable': enable,
            'voltage_mv': voltage_mv,
            'current_ua': current_ua,
            'pg': pg_or_err,
        }
        self._ret.put({"method": "supply_current", "value": value, "success": True})


server = MicroPyServer(debug=True)
_thread.start_new_thread(server._run, ())
