import pyb, micropython
import _thread
import time

micropython.alloc_emergency_exception_buf(100)

class MicroPyQueue(object):
    """ Special Queue for sending commands and getting return items from a MicroPython Process

    """
    MAX_ITEMS = 10

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.items = []

    def put(self, item):
        """ Put an item into the queue

        :param item: dict of format, {"method": <class_method>, "args": <args>}
        :return: True on queue, False on error or too many items
        """
        ret = True
        with self.lock:
            if len(self.items) >= self.MAX_ITEMS:
                self.items.pop()
                ret = False
            self.items.append(item)
        return ret

    def get(self, method=None, all=False):
        """ Get an item from the queue

        :param method: set to class_method to return a specific result
        :param all: when set return all
        :return: return item(s) in list
        """
        with self.lock:
            if method is None:
                if all:
                    ret = self.items
                    self.items = []
                    return ret

                if self.items: return [self.items.pop(0)]
                else: return []

            items = []
            for idx, item in enumerate(self.items):
                if item["method"] == method or item["method"] == "_debug":
                    items.append(self.items.pop(idx))
                    if not all:
                        break

            return items

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

                if self.items: return [self.items[0]]
                else: return []

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
                for idx, item in enumerate(self.items):
                    if item["method"] == item_update["method"]:
                        self.items[idx] = item_update
                        return

            # if no matching, append this item
            self.items.append(item)


class Foo():
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.bar_ref = self.bar  # Allocation occurs here
        self.x = 0.1
        self.q = MicroPyQueue()
        self.q1 = MicroPyQueue()
        self.led = pyb.LED(1)
        self.pin = pyb.Pin("X1", pyb.Pin.IN, pyb.Pin.PULL_UP)
        tim = pyb.Timer(4)
        tim.init(freq=1)
        tim.callback(self.cb)

    def bar(self, _):
        #with self.lock:
        self.x *= 1.2
        #self.led.toggle()
        #print(self.x)
        msgs = self.q.peek("bar")
        if msgs: return

        pin_state = self.pin.value()
        self.q.put({"method": "bar", "state": pin_state})

    def cb(self, t):
        # Passing self.bar would cause allocation.
        micropython.schedule(self.bar_ref, 0)

    def ret(self, method=None, all=False):
        #with self.lock:
        thing = self.q.get(method)
        print(thing)
        print("something {} {}".format(self.x, thing))
        return True

    def put(self, thing):
        self.q1.put(thing)

    def run(self, thing):
        self.x *= 1.2
        self.q.put({"method": "run", "state": thing})

    def _run(self):
        # run on thread
        while True:
            with self.lock:
                method = getattr(self, "run", None)
                thing = self.q1.get()
                if thing:
                    method(thing)

            # allows other threads to run, but generally speaking there should be no other threads(?)
            time.sleep_ms(100)


foo = Foo()
_thread.start_new_thread(foo._run, ())
