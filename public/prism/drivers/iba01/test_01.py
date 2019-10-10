import pyb, micropython
micropython.alloc_emergency_exception_buf(100)

class Foo():
    def __init__(self):
        self.bar_ref = self.bar  # Allocation occurs here
        self.x = 0.1
        self.led = pyb.LED(1)
        tim = pyb.Timer(4)
        tim.init(freq=2)
        tim.callback(self.cb)

    def bar(self, _):
        self.x *= 1.2
        self.led.toggle()
        #print(self.x)

    def cb(self, t):
        # Passing self.bar would cause allocation.
        micropython.schedule(self.bar_ref, 0)

    def get(self):
        print("something")


foo = Foo()
