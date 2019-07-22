import _thread
import time
import pyb
import micropython


class MicroPyQueue(object):
    """ Special Queue for sending commands and getting return items from a MicroPython Process

    """

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.items = []

    def put(self, item):
        """ Put an item into the queue

        :param item: dict of format, {"method": <class_method>, "args": <args>}
        :return: None
        """
        with self.lock:
            self.items.append(item)

    def get(self, method=None):
        """ Get an item from the queue

        :param method: set to class_method to return a specific result
        :return: return (ONE) item
        """
        with self.lock:
            if self.items:
                if method is None:
                    return [self.items.pop(0)]

                for idx, item in enumerate(self.items):
                    if item["method"] == method:
                        return [self.items.pop(idx)]

            return []

    def peek(self, method=None, all=False):
        """ Peek at item(s) in the queue, does not remove item(s)

        :param method: if set, returns first item matching method string
        :param all: if set returns all items, if method is set, then all items with method returned
        :return: None for no item, or [item(s)]
        """
        with self.lock:
            if method is None:
                if all:
                    return self.items

                return [self.items[0]]

            items = []
            for idx, item in enumerate(self.items):
                if item["method"] == method:
                    items.append(self.items[idx])
                    if not all:
                        break

            return items

    def update(self, item_update):
        """ Update an item in queue, or append item if it doesn't exist

        :param item_update: new item, of format, {"method": <class_method>, "args": <args>}
        :return:
        """
        with self.lock:
            if self.items:
                for idx, item in iter(self.items):
                    if item["method"] == item_update["method"]:
                        self.items[idx] = item_update
                        return

            # if no matching, append this item
            self.items.append(item)


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

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self._cmd = MicroPyQueue()
        self._ret = MicroPyQueue()
        self.ctx = {'a': 0,
                    "gpio": {},
                   }         # use dict to store static data
        self.timer = pyb.Timer(4)  # create a timer object using timer 4
        self._isr_jig_closed_detect_ref = self._jig_closed_detect

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

    def ret(self, method=None):
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
            time.sleep(0.01)

    # ===================================================================================

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
        # this method is not allowed to create memory or items in list
        # see http://docs.micropython.org/en/latest/reference/isr_rules.html
        micropython.schedule(self._isr_jig_closed_detect_ref, 0)

    def _jig_closed_detect(self, _):
        # this is not in ISR context

        # if there is a jig msg in the queue, then it hasn't been read yet,
        # and we don't put in a new state unless the previous state has been read
        msgs = self.peek(method="jig_closed_detect", all=True)
        if msgs:
            return

        # if the pin is HIGH, the jig is open
        #self._toggle_led(3, sleep=0.1) # just for debug
        jig_pin_state = self.ctx["gpio"]["jig_closed"].value()

        if jig_pin_state:
            self._ret.put({"method": "jig_closed_detect", "value": "OPEN", "success": True})
        else:
            self._ret.put({"method": "jig_closed_detect", "value": "CLOSED", "success": True})

    def enable_jig_closed_detect(self, args):
        enable = args.get("enable", True)
        pin = args.get("pin", "X1")
        self._ret.put({"method": "enable_jig_closed_detect", "value": enable, "success": True})
        if enable:
            self.timer.init(freq=1)  # trigger at Hz
            self.timer.callback(self._isr_jig_closed_detect)
            self._init_gpio("jig_closed", pin, pyb.Pin.IN, pyb.Pin.PULL_UP)

        else:
            self.timer.deinit()

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


server = MicroPyServer()
_thread.start_new_thread(server._run, ())

