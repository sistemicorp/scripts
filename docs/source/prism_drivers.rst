Drivers
=======

Drivers are listed in the `config` section of scripts.  For example::

      "config": {
        // fail_fast: if true (default), testing will stop on first failed test
        "fail_fast": false,
        // channel_hw_driver: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.fake.hwdrv_fake"]
      },



The purpose of this file and class is to instantiate your hardware into Prism.  The Drivers files are stored
in a separate path relative to scripts in order to isolate them.

The python file specified *MUST* have a class called `HWDriver`.  See the `fake` example for
implementation details and documentation.

By convention, the driver filename has prefix is `hwdrv_<name>.py`.


Discover Channels
-----------------

The important method of the `HWDriver` class is `discover_channels`.

`discover_channels` method returns a list of dictionaries that represent the connected hardware used in
the test system.  That list may contain one item that is shared among all the attached test jigs, or it
might be one item per test jig.

If there are multiple hardware items, the list of those items must be in the same order across the
different hardware types.  For example, if each test jig has a Teensy4 and a Segger programmer, the list
of Teensy4s and Seggers must be in the same order.  In this example, both Segger and the Teensy4s are
connected via USB, and if a prescribed USB (cabling) setup is used (one hub per test jig) then the USB
path can be used to synchronize the two lists.  This is done in the examples provided.

Per the code documentation, `discover_channels` must return a dictionary with prescribed keys.


::

    def discover_channels(self):
        """ determine the number of channels, and popultae hw drivers into shared state

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <object>,          # instance of your hardware driver

           # optional
           "close": None,              # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed
           "show_pass_fail": jig_led   # function for indicating pass/fail (like LED)

           # not part of the required block
           "unique_id": <unique_id>,   # unique id of the hardware (for tracking purposes)
           ...
          }, ...
        ]

        Note:
        1) The hw driver objects are expected to have an 'slot' field, the lowest
           id is assigned to channel 0, the next highest to channel 1, etc

        :return: <#>, <list>
            where #: >0 number of channels,
                      0 does not indicate num channels, like a shared hardware driver
                     <0 error

                  list of drivers
        """



Slot Number
-----------

When implementing python code to implement tests, there is a `channel (self.chan)` number and a `slot` number.
The channel is how Prism indexes the running threads, usually from 0 to a max of 3.  The slot number
is a number used to setup configuration of the physical system.



VISA
====

An example of VISA driver based hardware is provided in the `agilent_dso_usb_1` driver example.

Error: Found a device whose serial number cannot be read
See: https://stackoverflow.com/questions/52256123/unable-to-get-full-visa-address-that-includes-the-serial-number


