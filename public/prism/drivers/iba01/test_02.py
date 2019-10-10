import pyb, micropython
import _thread

micropython.alloc_emergency_exception_buf(100)

class Foo():
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.bar_ref = self.bar  # Allocation occurs here
        self.x = 0.1
        self.items = []
        self.led = pyb.LED(1)
        self.pin = pyb.Pin("X1", pyb.Pin.IN, pyb.Pin.PULL_UP)
        tim = pyb.Timer(4)
        tim.init(freq=2)
        tim.callback(self.cb)

    def bar(self, _):
        #with self.lock:
        self.x *= 1.2
        #self.led.toggle()
        #print(self.x)
        pin_state = self.pin.value()
        if len(self.items) > 10:
            self.items.pop()
        self.items.append(pin_state)

    def cb(self, t):
        # Passing self.bar would cause allocation.
        micropython.schedule(self.bar_ref, 0)

    def get(self):
        #with self.lock:
        print("something {} {}".format(self.x, self.items))


foo = Foo()
