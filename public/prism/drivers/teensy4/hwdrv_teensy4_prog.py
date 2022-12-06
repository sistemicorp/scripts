#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2022
Martin Guthrie

"""
import os
import logging
from core.sys_log import pub_notice
from public.prism.drivers.iba01.list_serial import serial_ports

DRIVER_TYPE = "TEENSY4_PROG"


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.teensy4.hwdrv_teensy4_prog"]
      },

    This driver is to find all attached Teensy4 instances for the purposes of programming them.
    So we only need to find the appropriate serial port interfaces.  We don't expect to see
    other devices with the same serial port name.  If that can occur, it would need to be handled...

    This is only used with script: teensy4_Prog_0.scr.

    !! NOTE: Only one Teensy should be connected, multiple Teensys are not supported !!
    !!       The teensy CLI programming utitilty cannot program a specific USB cpnnected Teensy,
    !!       it will scan USB, looking for any Teensy.

    """
    SFN = os.path.basename(__file__)
    VERSION = "0.0.1"

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0
        self.teensys = []

    def discover_channels(self):
        """ determine the number of channels, and populate hw drivers into shared state

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <foobar>,          # instance of your hardware driver
           "unique_id": <unique_id>,   # unique id of the hardware (for tracking purposes)

           # optional, related to Prism
           "close": None},             # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed
           "show_pass_fail": jig_led   # function for indicating pass/fail (like LED)

           # you may add your own key/values

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
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        # Fake - always report that one Teensy was found.
        _teensy = {}
        _teensy['id'] = 0
        _teensy['version'] = "0.0"
        _teensy['unique_id'] = "0.0"
        self.teensys.append(_teensy)

        self._num_chan = len(self.teensys)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, self.teensys

    def num_channels(self):
        return self._num_chan

    def close(self):
        self.logger.info("closed")


# ===============================================================================================
# Debugging code
# - Test your hardware discover here by running this file from a terminal
#
if __name__ == '__main__':
    logger = logging.getLogger()

    d = HWDriver()
    d.discover_channels()
    logger.info("Number channels: {}".format(d.num_channels()))
