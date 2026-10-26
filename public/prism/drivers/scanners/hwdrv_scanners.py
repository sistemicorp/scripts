#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
import os
import pyudev
import logging
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice

# import your hardware driver class, and details
from public.prism.drivers.scanners.Scanners import Scanner, VERSION, DRIVER_TYPE, PLAY_POLL_SEC

# Information:
# USB devices are found with pyudev, see https://pyudev.readthedocs.io
# - device.properties are the udev properties, USB Property Keys:
#   DEVLINKS, DEVNAME, DEVPATH, ID_BUS, ID_MODEL, ID_MODEL_ENC, ID_MODEL_FROM_DATABASE, ID_MODEL_ID
#   ID_PATH, ID_PATH_TAG, ID_REVISION, ID_SERIAL, ID_SERIAL_SHORT, ID_TYPE,
#   ID_USB_CLASS_FROM_DATABASE, ID_USB_DRIVER, ID_USB_INTERFACES, ID_USB_INTERFACE_NUM, ID_VENDOR,
#   ID_VENDOR_ENC, ID_VENDOR_FROM_DATABASE, ID_VENDOR_ID, MAJOR, MINOR, SUBSYSTEM, TAGS,
#   USEC_INITIALIZED
# - device.attributes are the sysfs attributes (bytes), useful ones are
#   manufacturer, product, serial, idVendor, idProduct
# - to see everything a device has, from a terminal,
#     $ udevadm info -q property -n /dev/ttyACM0   (properties)
#     $ udevadm info -a -n /dev/ttyACM0            (attributes, of the device and its parents)
#   or in code,
#     for a in device.attributes.available_attributes:
#         print(a, device.attributes.get(a))
# - USB permissions: Prism in Docker runs as root, a user account (like when developing)
#   needs a udev rule, see ~/git/scripts/udev-install-usbusers.sh


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.scanners.hwdrv_scanners"]
      },

    drivers is a list, so multiple HWDriver can be installed.

    Finds a USB barcode scanner in keyboard mode and installs one channel.
    A scanner in keyboard mode types into whatever has focus, so scans cannot
    be told apart by scanner, and more scanners still make one channel.
    """
    SFN = os.path.basename(__file__)  # for logging path

    # USB manufacturer strings of supported scanners, add as required
    SCANNER_MANUFACTURERS = ["Datalogic", ]

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0

    def find_scanners(self):
        """ Find attached USB barcode scanners
        :return: list of USB device paths, sorted
        """
        found = []
        context = pyudev.Context()
        for device in context.list_devices(subsystem="usb", DEVTYPE="usb_device"):
            manufacturer = device.attributes.get("manufacturer")
            if manufacturer is None:
                continue
            manufacturer = manufacturer.decode(errors="replace")
            if any(m in manufacturer for m in self.SCANNER_MANUFACTURERS):
                self.logger.info("{}: {}".format(manufacturer, device.device_path))
                found.append(device.device_path)
        return sorted(found)

    def discover_channels(self):
        """ Determine the number of channels, and populate hw drivers into shared state

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <object>,          # instance of your hardware driver

           # optional
           "close": None,              # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed, returns True|False
           "play_poll_sec": 1          # seconds between play calls, 0.2 to 2, default 1
           "show_pass_fail": jig_led   # function for indicating pass/fail (like LED)
           "show_msg": jig_display     # function for indicating test status (like display)
           "jig_reset": jig_reset      # function to reset the jig when the channel is DONE/READY

           # not part of the required block
           "unique_id": <unique_id>,   # unique id of the hardware (for tracking purposes)
           ...                         # you may add your own key/values
          }, ...
        ]

        Note:
        1) The hw driver objects are expected to have an 'id' field, the lowest
           id is assigned to channel 0, the next highest to channel 1, etc.
           A shared driver (returns 0 channels) is not assigned a channel, all channels use it.

        :return: <#>, <driver_type>, <list> (use Zero for a device shared across all channels)
            where
                #:      >0 number of channels,
                        0 does not indicate num channels, like a shared hardware driver
                        <0 error
                driver_type: String constant identifying Installed drivers type
                list:   List of installed driver dicts
        """
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        # ------------------------------------------------------------------
        # Your specific driver discovery code goes here
        #
        scanners = self.find_scanners()
        if not scanners:
            msg = "No barcode scanner found, supported: {}".format(self.SCANNER_MANUFACTURERS)
            self.logger.error(msg)
            pub_notice("HWDriver:{}: {}".format(self.SFN, msg), sender=sender,
                       type=NOTICE_TYPE.ERROR)
            return -1, DRIVER_TYPE, []

        if len(scanners) > 1:
            msg = "Found {} scanners, keyboard mode uses one channel".format(len(scanners))
            self.logger.warning(msg)
            pub_notice("HWDriver:{}: {}".format(self.SFN, msg), sender=sender,
                       type=NOTICE_TYPE.WARN)

        _scanner = Scanner(loggerIn=self.logger)
        _d = {"id": 0,
              "hwdrv": _scanner,
              "unique_id": scanners[0],
              "version": VERSION,
              "play": _scanner.jig_closed_always,
              "play_poll_sec": PLAY_POLL_SEC,
              "show_pass_fail": None,
              "show_msg": None,
              "close": None}

        #
        # End of your specific driver code
        # -------------------------------------------------------------------

        self._num_chan = 1
        pub_notice("HWDriver:{}: Found channel {}".format(self.SFN, 0), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, [_d]

    def num_channels(self):
        return self._num_chan


# ===============================================================================================
# Debugging code
# - Test your hardware discovery here by running this file from a terminal,
#     $ cd ~/git/scripts
#     $ python -m public.prism.drivers.scanners.hwdrv_scanners
#   or from PyCharm (be sure to set the working directory as ~/git/scripts, else imports will fail)
# - the purpose is to validate discover_channels() is working
# - ~/git/scripts/core has stand-ins for the Prism core imports, pub_notice() only logs
#
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    d = HWDriver()
    num_channels, driver_type, drivers = d.discover_channels()
    logger.info("discover_channels: num channels {}, type {}, drivers {}".format(num_channels,
                                                                                 driver_type,
                                                                                 drivers))
