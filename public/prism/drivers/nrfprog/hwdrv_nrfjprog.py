#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022-2023
Martin guthrie

"""
import os
import logging
import pyudev
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice

from public.prism.drivers.nrfprog.NRFProg import NRFProg, DRIVER_TYPE, cli_version

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
# - more than one device is put in channel order by its USB path, which is set by the
#   USB hub port, so a jig keeps its channel number as long as it stays on the same port


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.nrfprog.hwdrv_nrfjprog"]
      },

    drivers is a list, so multiple HWDriver can be installed.

    Finds attached SEGGER J-Link debug probes (like on a Nordic nRF DK) by the USB
    manufacturer attribute, one channel per probe, in USB path order.  The probe serial
    number is the unique_id, and selects the probe for nrfjprog (--snr).

    The nRF Command Line Tools (nrfjprog) must be installed on the station.
    """
    SFN = os.path.basename(__file__)
    VERSION = "0.0.1"

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0
        self.seggers = []

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

        # nRF Command Line Tools are installed per station, check nrfjprog is there and runs
        success, version = cli_version()
        if not success:
            self.logger.error(version)
            pub_notice("HWDriver:{}: {}".format(self.SFN, version), sender=sender, type=NOTICE_TYPE.ERROR)
            return -1, DRIVER_TYPE, []
        self.logger.info(version)

        found_serial_nums = []
        context = pyudev.Context()

        for device in context.list_devices():
            if device.attributes.get("manufacturer", False):
                if "SEGGER" in str(device.attributes.get("manufacturer")):
                    sn = device.attributes.get("serial").decode("utf-8").lstrip("0")
                    if sn not in found_serial_nums:
                        _segger = {"id": 0}  # this will get re-indexed below
                        _segger['hwdrv'] = NRFProg(sn)
                        _segger['close'] = None
                        _segger['play'] = None
                        _segger['show_pass_fail'] = None
                        _segger['show_msg'] = None
                        _segger['unique_id'] = sn
                        _segger['usb_path'] = device.device_path
                        _segger['version'] = self.VERSION
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
# - Test your hardware discovery here by running this file from a terminal,
#     $ cd ~/git/scripts
#     $ python -m public.prism.drivers.nrfprog.hwdrv_nrfjprog
#   or from PyCharm (be sure to set the working directory as ~/git/scripts, else imports will fail)
# - the purpose is to validate discover_channels() is working
# - ~/git/scripts/core has stand-ins for the Prism core imports, pub_notice() only logs
#
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    d = HWDriver()
    d.discover_channels()
    logger.info("Number channels: {}".format(d.num_channels()))
