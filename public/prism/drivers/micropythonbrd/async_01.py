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


class MicroPyWorker(object):
    """ Async Worker MicroPython Worker
    - runs in its own thread

    How to use this:
        - copy this file over to micropython
        - import it, import async_01, this will cause it to "run"
        - send in a command via the q,
            async_01.w.cmd({"method":"toggle_led", "args":1})
            async_01.w.cmd({"method":"enable_jig_closed_detect", "args":True})
        - to get a result,
            async_01.w.get()

    cmds: Are in this format: {"method": <class_method>, "args": <args>}

    ret: Are in this format: {"method": <class_method>, "value": <value>}

    """

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self._cmd = MicroPyQueue()
        self._ret = MicroPyQueue()
        self.ctx = {'a':0}         # use dict to store static data
        self.timer = pyb.Timer(4)  # create a timer object using timer 4
        self.isr_jig_closed_detect_ref = self.jig_closed_detect

    def cmd(self, cmd):
        with self.lock:
            self._cmd.put(cmd)

    def ret(self, method=None):
        with self.lock:
            return self._ret.get(method)

    def peek(self, method=None, all=False):
        with self.lock:
            return self._ret.peek(method, all)

    def update(self, item_update):
        with self.lock:
            return self._ret.update(item_update)

    def run(self):
        # run on thread
        while True:
            item = self._cmd.get()
            if item is not None:
                method = item["method"]
                args = item["args"]
                method = getattr(self, method, None)
                if method is not None:
                    with self.lock:
                        result = method(args)
                        print(str(result) + "\n")

        # allows other threads to run, but generally speaking there should be none
        # timer isr was working before adding this.  But this seems to be the right thing to do.
        time.sleep(0.01)

    # ===================================================================================

    def _toggle_led(self, led, sleep=0.5):
        pyb.LED(led).on()
        time.sleep(sleep)
        pyb.LED(led).off()
        time.sleep(sleep)

    def toggle_led(self, led, sleep=0.5):
        self._toggle_led(led, sleep)
        self.ctx['a'] += 1
        print('Hello from MicroPyWorker {}'.format(self.ctx['a']))
        self._ret.put(str({"method": "toggle_led", "value": self.ctx['a']}))
        return True

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
        self._ret.put(str({"method": "jig_closed_detect", "value": True}))
        # in reality, if the jig opens, that open result
        # should not be replaces until the PC-side reads that result,
        # so, this code should peek at all messages, if there is a jig open
        # message, then don't post a jig closed message.


w = MicroPyWorker()
_thread.start_new_thread(w.run, ())

