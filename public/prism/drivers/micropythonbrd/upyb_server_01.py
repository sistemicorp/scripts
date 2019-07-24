import _thread
import time
import pyb
import micropython
import array
import upyb_queue

micropython.alloc_emergency_exception_buf(100)


class MicroPyServer(object):
    """ Async Worker MicroPython Worker
    - runs in its own thread

    How to use this:
        - copy this file over to micropython
        - import it, import async_01, this will cause it to "run"
        - send in a command via the q,
            upybrd_server_01.server.cmd({"method":"toggle_led", "args":1})
            upybrd_server_01.server.cmd({"method":"enable_jig_closed_detect", "args":True})
        - to get a result,
            upybrd_server_01.server.get()

    cmds: Are in this format: {"method": <class_method>, "args": <args>}

    ret: Are in this format: {"method": <class_method>, "value": <value>}

    """

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

    JIG_CLOSED_TIMER = 4

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self._cmd = upyb_queue.MicroPyQueue()
        self._ret = upyb_queue.MicroPyQueue()

        # use dict to store static data
        self.ctx = {'a': 0,                # dummy for testing
                    "gpio": {},            # gpios used are named here
                    "timer": {},           # timers running are listed here
                    "adc_read_multi": {},  # cache args
                    }

        self.timer_jig_closed = pyb.Timer(self.JIG_CLOSED_TIMER)  # create a timer object using timer
        self._isr_jig_closed_detect_ref = self._jig_closed_detect # used to create memory before ISR

    # ===================================================================================
    # Public API to send commands and get results from the MicroPy Server
    # NOTE: "results" must be print()'ed to be return values on the serial (repl) port

    def cmd(self, cmd):
        """ Send (Add) a command to the MicroPy Server command queue
        - commands are executed in the order they are received

        :param cmd: dict format {"method": <class_method>, "args": <args>}
        :return: success (True/False)
        """
        with self.lock:
            if not isinstance(cmd, dict):
                self._ret.put({"method": "cmd", "value": "cmd must be a dict", "success": False})
                return False

            if not cmd.get("method", False):
                self._ret.put({"method": "cmd", "value": "cmd dict must have method key", "success": False})
                return False

            if not getattr(self, cmd["method"], False):
                self._ret.put({"method": "cmd", "value": "cmd['{}'] invalid".format(cmd["method"]), "success": False})
                return False

            self._cmd.put(cmd)
            return True

    def ret(self, method=None, all=False):
        with self.lock:
            _ret = self._ret.get(method)
            print(_ret)
            return True

    def peek(self, method=None, all=False):
        with self.lock:
            ret = self._ret.peek(method, all)
            print(ret)
            return True

    def update(self, item_update):
        with self.lock:
            return self._ret.update(item_update)

    # ===================================================================================
    # private

    def _run(self):
        # run on thread
        while True:
            with self.lock:
                item = self._cmd.get()
                if item:
                    method = item[0]["method"]
                    args = item[0]["args"]
                    method = getattr(self, method, None)
                    if method is not None:
                        method(args)

            # allows other threads to run, but generally speaking there should be no other threads(?)
            time.sleep_ms(100)

    # ===================================================================================
    # Methods
    # NOTES:
    # 1. !! DON'T access public API, ret/peek/update/cmd, functions, access the queue's directly
    #    Else probably get into a lock lockup

    def _toggle_led(self, led, on_ms=500):
        pyb.LED(led).on()
        time.sleep_ms(on_ms)
        pyb.LED(led).off()

    def _led_cycle(self, ):
        pass

    def led_cycle(self, args):
        en = args.get("enable", True)
        led = args.get("led", None)
        on_ms = args.get("on_ms", 500)
        off_ms = args.get("off_ms", 500)
        if not led in [self.LED_BLUE, self.LED_GREEN, self.LED_RED, self.LED_YELLOW]:
            self._ret.put({"method": "led_toggle", "value": "unknown led {}".format(led), "success": False})
            return

        self._ret.put({"method": "led_toggle", "value": True, "success": True})

    def led_toggle(self, args):
        """ Toggle LED on, does so only once

        cmds = ["upybrd_server_01.server.cmd({{'method': 'led_toggle', 'args': {{ 'led': {}, 'on_ms': {} }} }})".format(lednum, ontime_ms)]

        args:
        :param led: one of LED_*
        :param on_ms: milli seconds on
        :return: success (True/False)
        """
        led = args.get("led", None)
        on_ms = args.get("on_ms", 500)
        if not led in [self.LED_BLUE, self.LED_GREEN, self.LED_RED, self.LED_YELLOW]:
            self._ret.put({"method": "led_toggle", "value": "unknown led {}".format(led), "success": False})
            return

        self._toggle_led(led, on_ms)
        self._ret.put({"method": "led_toggle", "value": True, "success": True})

    def _isr_jig_closed_detect(self, _):
        # run in ISR context
        # this method is not allowed to create memory or items in list
        # see http://docs.micropython.org/en/latest/reference/isr_rules.html
        micropython.schedule(self._isr_jig_closed_detect_ref, 0)

    def _jig_closed_detect(self, _):
        # this is not in ISR context
        # if there is a jig msg in the queue, then it hasn't been read yet,
        # and we don't put in a new state unless the previous state has been read
        msgs = self._ret.peek("jig_closed_detect")
        if msgs:
            return

        # if the pin is HIGH, the jig is open
        self._toggle_led(3, on_ms=100) # just for debug
        jig_pin_state = self.ctx["gpio"]["jig_closed"].value()

        if jig_pin_state:
            self._ret.put({"method": "jig_closed_detect", "value": "OPEN", "success": True})
        else:
            self._ret.put({"method": "jig_closed_detect", "value": "CLOSED", "success": True})

    def enable_jig_closed_detect(self, args):
        enable = args.get("enable", True)

        if enable and "timer_jig_closed" in self.ctx["timer"]:
            self._ret.put({"method": "enable_jig_closed_detect", "value": "ALREADY_RUNNING", "success": True})
            return

        self._ret.put({"method": "enable_jig_closed_detect", "value": enable, "success": True})
        if enable:
            self.timer_jig_closed.init(freq=1)  # trigger at Hz
            self.timer_jig_closed.callback(self._isr_jig_closed_detect)
            pin = args.get("pin", "X1")
            self._init_gpio("jig_closed", pin, pyb.Pin.IN, pyb.Pin.PULL_UP)
            self.ctx["timer"]["timer_jig_closed"] = True

        else:
            self.timer_jig_closed.deinit()
            self.ctx["timer"].pop("timer_jig_closed", None)

    def _init_gpio(self, name, pin, mode, pull=pyb.Pin.PULL_NONE):
        self.ctx["gpio"][name] = pyb.Pin(pin, mode, pull)

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

        self._init_gpio(name, pin, mode, pull)

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
            self._ret.put({"method": "adc_read", "value": "{} pin is not valid".format(pin), "success": False})
            return

        samples = args.get("samples", 1)
        sample_ms = args.get("sample_ms", 1)

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
            self._ret.put({"method": "adc_read", "value": "{} pin is not valid (internal error)".format(pin), "success": False})
            return

        results = []
        for i in range(samples):
            results.append(float(adc_read()))
            if sample_ms:
                time.sleep_ms(sample_ms)

        sum = 0
        for r in results: sum += r
        result = float(sum / len(results))

        #self._ret.put({"method": "adc_read", "value": "{:.4f}".format(result), "success": True})
        self._ret.put({"method": "adc_read", "value": result, "success": True})

    def _adc_read_multi(self, _):
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

        # reformat results to be a simple list  TODO: is there a better way to do this?
        r = []
        for result in results:
            r.append([r for r in result])

        self._ret.put({"method": "adc_read_multi_results", "value": r, "success": True})

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
        if not (0 < freq < 10001):
            self._ret.put({"method": "adc_read_multi", "value": "freq not within range supported", "success": False})
            return

        samples = args.get("samples", 100)
        if not (0 < samples < 1001):
            self._ret.put({"method": "adc_read_multi", "value": "samples not within range supported", "success": False})
            return

        pins = args.get("pins", None)
        if not isinstance(pins, list):
            self._ret.put({"method": "adc_read_multi", "value": "pins must be a list", "success": False})
            return
        for pin in pins:
            if pin not in self.ADC_VALID_PINS:
                self._ret.put({"method": "adc_read_multi", "value": "{} pin is not valid".format(pin), "success": False})
                return

        # everything is good, store the params
        self.ctx["adc_read_multi"] = args

        # schedule adc multi to run later
        micropython.schedule(self._adc_read_multi, 0)

        self._ret.put({"method": "adc_read_multi", "value": "scheduled", "success": True})


server = MicroPyServer()
_thread.start_new_thread(server._run, ())

