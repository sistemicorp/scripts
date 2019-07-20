import _thread
import time
import pyb
import micropython


class MicroPyQueue(object):

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.items = []

    def put(self, item):
        with self.lock:
            self.items.append(item)

    def get(self, method=None):
        with self.lock:
            if self.items:
                if method is None:
                    return self.items.pop(0)

                for idx, item in iter(self.items):
                    if item["method"] == method:
                        return self.items.pop(idx)

            return None

    def peek(self, method=None, all=False):
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
        with self.lock:
            if self.items:
                for idx, item in iter(self.items):
                    if item["method"] == item_update["method"]:
                        self.items[idx] = item_update
                        return

            # if no matching, append this item
            self.items.append(item)


q = MicroPyQueue()
q_ret = MicroPyQueue()


class MicroPyWorker(object):

    def __init__(self):
        self.ctx = {'a':0}
        self.timer = pyb.Timer(4)  # create a timer object using timer 4
        self.isr_jig_closed_detect_ref = self.jig_closed_detect

    def _toggle_led(self, led, sleep=0.5):
        pyb.LED(led).on()
        time.sleep(sleep)
        pyb.LED(led).off()
        time.sleep(sleep)

    def toggle_led(self, led, sleep=0.5):
        self._toggle_led(led, sleep)
        self.ctx['a'] += 1
        print('Hello from MicroPyWorker {}'.format(self.ctx['a']))
        q_ret.put(str({"method": "toggle_led", "value": self.ctx['a']}))
        return True

    def enable_jig_closed_detect(self, enable=True):
        print("setting jig_closed_detect: {}".format(enable))
        if enable:
            self.timer.init(freq=2)  # trigger at Hz
            self.timer.callback(self.isr_jig_closed_detect)
        else:
            self.timer.deinit()

    def isr_jig_closed_detect(self, _):
        # this method is not allowed to create memory or items in list
        micropython.schedule(self.isr_jig_closed_detect_ref, 0)

    def jig_closed_detect(self, _):
        self._toggle_led(3, sleep=0.1)
        q_ret.put(str({"method": "jig_closed_detect", "value": True}))
        # in reality, if the jig opens, that open result
        # should not be replaces until the PC-side reads that result,
        # so, this code should peek at all messages, if there is a jig open
        # message, then don't post a jig closed message.


def testThread():
    lock = _thread.allocate_lock()
    w = MicroPyWorker()

    while True:
        with lock:
            item = q.get()
            if item is not None:
                w_method = item["method"]
                w_args = item["args"]
                method = getattr(w,w_method, None)
                if method is not None:
                    result = method(w_args)
                    print(result)


_thread.start_new_thread(testThread, ())

# How to use this:
# - copy this file over to micropython
# - import it, import async_01, this will cause it to "run"
# - send in a command via the q,
#   async_01.q.put({"method":"toggle_led", "args":1})
#   async_01.q.put({"method":"enable_jig_closed_detect", "args":True})
# - to get a result,
#   async_01.q_ret.get()



