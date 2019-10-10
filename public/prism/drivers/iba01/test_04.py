import pyb, micropython
import _thread
import time

micropython.alloc_emergency_exception_buf(100)


class Foo():
    MAX_SIZE = 10

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.bar_ref = self.bar  # Allocation occurs here
        self.x = 0.1
        self.list =[]
        self.pin = pyb.Pin("X1", pyb.Pin.IN, pyb.Pin.PULL_UP)
        tim = pyb.Timer(4)
        tim.init(freq=1)
        tim.callback(self.cb)

    def _add(self, item):
        with self.lock:
            if len(self.list) > self.MAX_SIZE:
                self.list.pop()
            self.list.append(item)

    def bar(self, _):
        self.x *= 1.2
        if self.x > 100000: self.x = 0.1
        pin_state = self.pin.value()
        self._add(pin_state)

    def cb(self, t):
        # Passing self.bar would cause allocation.
        micropython.schedule(self.bar_ref, 0)

    def ret(self, method=None, all=False):
        #with self.lock:
        print("something {} {} {}".format(self.x, method, self.list))
        self._add(method)
        return True

    def put(self, thing):
        self._add(thing)

    def run(self, thing):
        self.x *= 1.2

    def _run(self):
        # run on thread
        while True:
            with self.lock:
                method = getattr(self, "run", None)
                thing = "test"
                if thing:
                    method(thing)

            # allows other threads to run, but generally speaking there should be no other threads(?)
            time.sleep_ms(100)


foo = Foo()
_thread.start_new_thread(foo._run, ())
