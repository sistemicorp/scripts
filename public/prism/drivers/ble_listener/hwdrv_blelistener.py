#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

"""
import os
import logging
from core.sys_log import pub_notice

# import your hardware driver class, and details
from public.prism.drivers.ble_listener.BLEListener import BLEListener, VERSION, DRIVER_TYPE


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.fake.hwdrv_fake"]
      },

    drivers is a list, so multiple HWDriver can be installed.

    This is a fake HW driver to simulate and show what a HWDriver is required to do.
    """
    SFN = os.path.basename(__file__)  # for logging path

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = None

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

        :return: <#>, <list> (use Zero for a device shared across all channels)
            where #: >0 number of channels,
                      0 does not indicate num channels, like a shared hardware driver
                     <0 error

                  list of drivers
        """
        drivers = []

        # ------------------------------------------------------------------
        # Your specific driver discovery code goes here
        #

        # There is only ONE BLE Listener
        _driver = BLEListener(loggerIn=self.logger)
        _driver.start_scanner()

        # create the dict with keys expected by Prism
        _d = {'id': _driver.id(),
              "version": VERSION,
              "hwdrv": _driver,
              "unique_id": _driver.unique_id(),
              "version": _driver.version(),
              "play": None,
              "show_pass_fail": None,
              "close": _driver.close}  # good practice to have in place

        #
        # End of your specific driver code
        # -------------------------------------------------------------------

        drivers.append(_d)
        pub_notice("HWDriver:{}: Found channel {}".format(self.SFN, 0),
                   sender="{}.{}".format(self.SFN, __class__.__name__))

        self._num_chan = len(drivers)
        self.logger.info("{} channels found".format(self._num_chan))
        return 0, DRIVER_TYPE, drivers

    def num_channels(self):
        return self._num_chan


# ===============================================================================================
# Debugging code
# - Test your hardware discover here by running this file from a terminal
#
if __name__ == '__main__':
    logger = logging.getLogger()

    d = HWDriver()
    d.discover_channels()
    logger.info("Number channels: {}".format(d.num_channels()))
