#! /usr/bin/env python
# -*- coding: utf-8 -*-
import _thread
from machine import I2C

UPYB_I2C_HW_I2C1 = "X"   # on X9/10
UPYB_I2C_HW_I2C2 = "Y"   # on Y9/10

class UPYB_I2C(object):
    """ Wrapper Class for I2C on MicroPython
    - adds a lock to sequence clients

    How to use:
    1) myi2c = UPYB_I2C()
    2) success, msg = i2c.init(UPYB_I2C_HW_I2C1)
    3) myi2c.acquire()
    4) myi2c.i2c.write( ...)
    5) myi2c.release()

    """
    I2C_HW_IDs = [UPYB_I2C_HW_I2C1, UPYB_I2C_HW_I2C2]

    def __init__(self):
        """
        - see http://docs.micropython.org/en/latest/pyboard/quickref.html#i2c-bus
        - note that we want to use HW I2C, not software emulated, so have id=1 for X10/X9, and
          id=2 for Y9/10

        """
        self.lock = _thread.allocate_lock()
        self.i2c = None
        self.init_done = False

    def init(self, id, freq=400000):
        if id not in self.I2C_HW_IDs:
            return False, "Not a valid I2C port id"

        if self.init_done:
            return False, "Already inited"

        self.i2c = I2C(id, freq=freq)
        self.init_done = True
        return True, None

    def acquire(self):
        return self.lock.acquire()

    def release(self):
        return self.lock.release()
