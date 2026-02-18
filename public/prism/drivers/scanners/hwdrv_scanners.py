#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
import os
import pyudev
import logging
from core.sys_log import pub_notice

# import your hardware driver class, and details
from public.prism.drivers.scanners.Scanners import Scanner, VERSION, DRIVER_TYPE

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

    # add as required
    SCANNER_MANUFACTURERS = ["Datalogic", ]

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0
        self.scanners = []

    def discover_channels(self):
        """ determine the number of channels, and popultae hw drivers into shared state

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <object>,          # instance of your hardware driver

           # optional
           "close": None,              # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed
           "show_pass_fail": jig_led   # function for indicating pass/fail (like LED)
           "show_msg": jig_display     # function for indicating test status (like display)

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
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        # ------------------------------------------------------------------
        # Your specific driver discovery code goes here
        #
        # Scan attached USB devices and look for scanners
        context = pyudev.Context()
        for device in context.list_devices():
            _manu = str(device.attributes.get("manufacturer"))
            if _manu == "None": continue

            self.logger.info(_manu)
            for m in self.SCANNER_MANUFACTURERS:
                if m in str(device.attributes.get("manufacturer")):
                    _scanner = {"id": 0} # this will get re-indexed below
                    _scanner['hwdrv'] = Scanner()
                    _scanner['version'] = None
                    _scanner['close'] = None
                    _scanner['play'] = _scanner['hwdrv'].jig_closed_always
                    _scanner['show_pass_fail'] = None
                    _scanner['show_msg'] = None
                    _scanner['usb_path'] = device.device_path
                    self.scanners.append(_scanner)

        # sort based on USB path, slot 0, 1, 2, etc
        self.scanners = sorted(self.scanners, key=lambda d: d['usb_path'])

        # fix the slot IDs as the slot order set by the USB path
        for idx, t in enumerate(self.scanners):
            t["id"] = idx

        self.logger.info(self.scanners)
        self._num_chan = len(self.scanners)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, self.scanners

    def num_channels(self):
        return self._num_chan


# ===============================================================================================
# Debugging code
# - Test your hardware discover here by running this file from PyCharm (be sure to set the working
#   directory as ~/git/scripts, else imports will fail)
# - the purpose is to valid discover_channels() is working
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    d = HWDriver()
    num_channels, driver_type, drivers = d.discover_channels()
    logger.info("discover_channels: num channels {}, type {}, drivers {}".format(num_channels,
                                                                                 driver_type,
                                                                                 drivers))
