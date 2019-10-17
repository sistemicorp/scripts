Drivers
=======

Drivers are listed in the `config` section of scripts.  For example::

      "config": {
        // fail_fast: if true (default), testing will stop on first failed test
        "fail_fast": false,
        // channel_hw_driver: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.fake.fake"]
      },

The python file specified MUST have a class called `HWDriver`.  See the `fake` example for
implementation details.

The purpose of this file/class is to instantiate your hardware into Prism.



VISA
----

Error: Found a device whose serial number cannot be read
See: https://stackoverflow.com/questions/52256123/unable-to-get-full-visa-address-that-includes-the-serial-number




Slot Number
-----------

When implementing python code to implement tests, there is a `channel (self.chan)` number and a `slot` number.
The channel is how Prism indexes the running threads, usually from 0 to a max of 3.  The slot number
is a number used to setup configuration of the physical system.  This distinction makes more sense with
an example.

Consider the case of a 4 channel scope connected to 4 test stations, like 4 IBA01s.  Each channel of the
scope is connected to a specific test station.  In development you may find that the 4 test stations always
assigned to the same USB tty port and thus, you figure out what channel of the scope goes
with which test station.  But in production, or even another developer, this will not be the case.  Or even
consider that a test station itself breaks, and can no longer used.  How will that affect the channel
assignments of the scope (the physical connections)?

The python code implementing the tests, won't know which scope channel is assigned to it.  This is where
the concept of the slot number comes in.

Consider again the IBA01, where the slot number is defined with a file that exists on the PyBoard on the
micro SD slot.  Thus the slot number is "pysically portable", it can be removed from one IBA01 to another.  The
slot number is assigned to a scope channel, with SLOT0 assigned to CH1, and SLOT1 assigned to CH2, and so on.

The slot number is determined by the `HWDriver` class for the IBA01, and is sent to the python code
implementing the tests as part of the shared state of that hardware.

Although one (possibly) could write software to configure the test station slots to test equipment channels,
and cover the cases of test stations being moved around, replaced, etc, that requires effort,
documentation and training.  If you develop your own test interface board, consider how you will identify
it, and consider a physical "thing" to assign the slot number.  For example, a dip switch could be used
to set the slot number.  Or a USB flash drive.

