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
        :return: return item
        """
        with self.lock:
            if self.items:
                if method is None:
                    return self.items.pop(0)

                for idx, item in iter(self.items):
                    if item["method"] == method:
                        return self.items.pop(idx)

            return None

    def peek(self, method=None, all=False):
        """ Peek at item(s) in the queue, does not remove item

        :param method: if set, returns first item matching method string
        :param all: returns all items, method param is ignored
        :return: None for no item, or item
        """
        with self.lock:
            if all:
                return self.items

            if self.items:
                if method is None:
                    return self.items[0]

                for idx, item in iter(self.items):
                    if item["method"] == method:
                        return self.items[idx]

            return None

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
        self.ctx = {'a': 0}         # use dict to store static data
        self.timer = pyb.Timer(4)  # create a timer object using timer 4
        self.isr_jig_closed_detect_ref = self.jig_closed_detect

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
            print('{"method": "cmd", "value": "cmd must be a dict", "success": false}')
            return False

        if not cmd.get("method", False):
            print('{"method": "cmd", "value": "cmd dict must have method key", "success": false}')
            return False

        if not getattr(self, cmd["method"], False):
            print('''{{"method": "cmd", "value": "cmd['{}'] invalid", "success": false}}'''.format(cmd["method"]))
            return False

        with self.lock:
            self._cmd.put(cmd)
            print('{"method": "cmd", "value": true, "success": true}')
            return True

    def ret(self, method=None):
        with self.lock:
            ret = self._ret.get(method)
            if ret:
                print(ret)
                return True
            print('{"method": "ret", "value": true}')
            return True

    def peek(self, method=None, all=False):
        with self.lock:
            ret = self._ret.peek(method, all)
            if ret:
                print(ret)
                return True
            print('{"method": "peek", "value": true}')
            return True

    def update(self, item_update):
        with self.lock:
            return self._ret.update(item_update)

    # ===================================================================================
    # private

    def _run(self):
        # run on thread
        while True:
            item = self._cmd.get()
            if item:
                method = item["method"]
                args = item["args"]
                method = getattr(self, method, None)
                if method is not None:
                    with self.lock:
                        method(args)
                        #result = method(args)
                        #print(str(result) + "\n")

        # allows other threads to run, but generally speaking there should be no other threads(?)
        time.sleep(0.01)

    # ===================================================================================

    def _toggle_led(self, led, sleep=0.5):
        pyb.LED(led).on()
        time.sleep(sleep)
        pyb.LED(led).off()
        time.sleep(sleep)

    def toggle_led(self, led, sleep=0.5):
        """ Toggle LED

        :param led: one of LED_*
        :param sleep: seconds between on/off
        :return: success (True/False)
        """
        if not led in [self.LED_BLUE, self.LED_GREEN, self.LED_RED, self.LED_YELLOW]:
            self._ret.put("""{"method": "toggle_led", "value": false}""")
            return

        self._toggle_led(led, sleep)
        ret = """{"method": "toggle_led", "value": true}"""
        self._ret.put(ret)

    def enable_jig_closed_detect(self, enable=True):
        print("setting jig_closed_detect: {}".format(enable))
        if enable:
            self.timer.init(freq=1)  # trigger at Hz
            self.timer.callback(self.isr_jig_closed_detect)
        else:
            self.timer.deinit()

    def isr_jig_closed_detect(self, _):
        # this method is not allowed to create memory or items in list
        micropython.schedule(self.isr_jig_closed_detect_ref, 0)

    def jig_closed_detect(self, _):
        self._toggle_led(3, sleep=0.1)
        self._ret.put(str({"method": "jig_closed_detect", "value": "true"}))
        # in reality, if the jig opens, that open result
        # should not be replaces until the PC-side reads that result,
        # so, this code should peek at all messages, if there is a jig open
        # message, then don't post a jig closed message.


server = MicroPyServer()
_thread.start_new_thread(server._run, ())

