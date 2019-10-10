import pyb, micropython
import _thread

micropython.alloc_emergency_exception_buf(100)


class Foo():
    MAX_SIZE = 10

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.bar_ref = self.bar  # Allocation occurs here
        tim = pyb.Timer(4)
        tim.callback(self.cb)
        tim.init(freq=1)

    def _add(self, item):
        # accessed by 'REPL' and via Timer callback thru micropython.schedule()
        with self.lock:
            i = 0
            while i < 10000:  # the longer this is the quicker fault occurs
                i += 1

    def bar(self, _):
        self._add(23)

    def cb(self, t):
        # Passing self.bar would cause allocation.
        micropython.schedule(self.bar_ref, 0)

    def ret(self, method=None, all=False):
        print("something {}".format(method))
        self._add(method)
        return True


foo = Foo()
