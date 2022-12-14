#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022
Martin guthrie

"""
import os
import logging
import pyudev
from core.sys_log import pub_notice

from public.prism.drivers.nrfprog.NRFProg import NRFProg, DRIVER_TYPE

# Information:
# USB Property Keys:
# DEVLINKS, DEVNAME, DEVPATH, ID_BUS, ID_MODEL, ID_MODEL_ENC, ID_MODEL_FROM_DATABASE, ID_MODEL_ID, ID_PATH
# ID_PATH_TAG, ID_REVISION, ID_SERIAL, ID_SERIAL_SHORT, ID_TYPE, ID_USB_CLASS_FROM_DATABASE, ID_USB_DRIVER
# ID_USB_INTERFACES, ID_USB_INTERFACE_NUM, ID_VENDOR, ID_VENDOR_ENC, ID_VENDOR_FROM_DATABASE, ID_VENDOR_ID
# MAJOR, MINOR, SUBSYSTEM, TAGS, USEC_INITIALIZED


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
        self.seggers = []

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

        found_serial_nums = []
        context = pyudev.Context()

        for device in context.list_devices():
            if device.attributes.get("manufacturer", False):
                if "SEGGER" in str(device.attributes.get("manufacturer")):
                    sn = device.attributes.get("serial").decode("utf-8").lstrip("0")
                    if sn not in found_serial_nums:
                        _segger = {"id": 0}  # this will get re-indexed below
                        _segger['usb_path'] = device.device_path
                        _segger['version'] = self.VERSION
                        _segger['hwdrv'] = NRFProg(sn)
                        _segger['unique_id'] = sn
                        self.seggers.append(_segger)
                        found_serial_nums.append(sn)

        # Note:
        # the nrf prog tool will be run as,
        #       $ nrfjprog --snr <serial> ...
        # in a subprocess when the script is running

        # sort based on USB path, slot 0, 1, 2, etc
        self.seggers = sorted(self.seggers, key=lambda d: d['usb_path'])
        # fix the slot IDs as the slot order is set by the USB path
        for idx, t in enumerate(self.seggers):
            t["id"] = idx

        self.logger.info(self.seggers)

        self._num_chan = len(self.seggers)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, self.seggers

    def num_channels(self):
        return self._num_chan

    def close(self):
        self.logger.info("closed")


# ===============================================================================================
# Debugging code
# - Test your hardware discover here by running this file from PyCharm (be sure to set the working
#   directory as ~/git/scripts, else imports will fail)
# - the purpose is to valid discover_channels() is working
#
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    d = HWDriver()
    d.discover_channels()
    logger.info("Number channels: {}".format(d.num_channels()))
