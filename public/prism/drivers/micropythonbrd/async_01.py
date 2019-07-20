import _thread
import time
import pyb

lock = _thread.allocate_lock()


class MicroPyQueue(object):

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.items = []

    def put(self, item):
        with self.lock:
            self.items.append(item)

    def get(self):
        with self.lock:
            if self.items:
                return self.items.pop(0)

        return None


class MicroPyWorker(object):

    def __init__(self):
        self.ctx = {'a':0}
        self.lock = _thread.allocate_lock()

    def toggle_led(self, led):
        with self.lock:
            pyb.LED(led).on()
            print('Hello from MicroPyWorker {}'.format(self.ctx['a']))
            time.sleep(0.5)
            pyb.LED(1).off()
            time.sleep(0.5)
            self.ctx['a'] += 1


def testThread():

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


q = MicroPyQueue()

_thread.start_new_thread(testThread, ())
