#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Owen Li

"""
import os
import logging
from core.sys_log import pub_notice
from public.prism.drivers.iba01.list_serial import serial_ports

from public.prism.drivers.teensy4.Teensy4 import Teensy4, DRIVER_TYPE


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.teensy4.hwdrv_teensy4"]
      },

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

           # optional
           "close": None},             # register a callback on closing the channel, or None
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
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        port_candidates = serial_ports()
        self.logger.info("Serial Ports to look for Teensy {}".format(port_candidates))

        for port in port_candidates:
            if "ttyACM" not in port:  # this does not work on Windows as only see "COM#"
                self.logger.info("skipping port {}...".format(port))
                continue

            _teensy = {"port": port}
            self.logger.info("Trying teensy at {}...".format(port))

            #https: // stackoverflow.com / questions / 21050671 / how - to - check - if -device - is -connected - pyserial / 49450813
            # test if this COM port is really a Teensy
            # create an instance of Teensy()
            _teensy['hwdrv'] = Teensy4(port, loggerIn=logging.getLogger("teensy.try"))
            success = _teensy['hwdrv'].init()
            if not success:
                self.logger.info("failed on {}...".format(port))
                continue

            # yes, its a Teensy, add it to the list...
            answer = _teensy['hwdrv'].slot()
            _teensy['id'] = answer['result']['id']
            success = answer['success']
            if not success:
                self.logger.info("failed on {}...".format('slot'))
                continue

            answer = _teensy['hwdrv'].unique_id()
            _teensy['unique_id'] = answer['result']['unique_id']
            success = answer['success']
            if not success:
                self.logger.info("failed on {}...".format('unique_id'))
                continue

            _teensy['close'] = _teensy['hwdrv'].close
            _teensy['play'] = _teensy['hwdrv'].jig_closed_detect
            _teensy['show_pass_fail'] = _teensy['hwdrv'].show_pass_fail

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
