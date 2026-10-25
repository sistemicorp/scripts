#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021-2026
Owen Li, Martin Guthrie

"""
import os
import logging
import pyudev
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice

from public.prism.drivers.A4401_BOND.A4401_BOND import A4401_BOND, DRIVER_TYPE


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": [["public.prism.drivers.A4401_BOND.hwdrv_A4401_BOND",
                     "<path to pogo_hdr_definition._json>"]]
      },

    """
    SFN = os.path.basename(__file__)
    VERSION = "0.0.1"

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0
        self.teensys = []  # holds a list of all objects found

    def discover_channels(self, scriptArgs=None):
        """ determine the number of channels, and populate hw drivers into shared state

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

        :return: <#>, <driver_type>, <list>
            where
                #:      >0 number of channels,
                        0 does not indicate num channels, like a shared hardware driver
                        <0 error
                driver_type: String constant identifying Installed drivers type
                list:   List of installed driver dicts
        """
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        port_candidates = []
        context = pyudev.Context()
        # Iterate through all available tty devices
        for device in context.list_devices(subsystem='tty'):
            # We are only interested in ttyACM devices
            if not device.device_node or 'ttyACM' not in device.device_node:
                continue
            # Walk up the device tree to find the parent USB device.
            usb_device = device.find_parent('usb', 'usb_device')
            if usb_device is None:
                continue
            manufacturer = usb_device.attributes.get('manufacturer')
            if manufacturer and manufacturer.decode('utf-8') == 'Teensyduino':
                self.logger.info(f"device node: {device.device_node}")
                # the USB path sets the slot order
                port_candidates.append((device.device_node, device.device_path))

        self.logger.info("Serial Ports to look for Teensy {}".format(port_candidates))
        for port, usb_path in port_candidates:
            self.logger.info(f"Trying teensy at {port}, using header pin definition {scriptArgs}")
            hwdrv = A4401_BOND(port,
                               loggerIn=logging.getLogger("teensy.try"),
                               header_def_filename=scriptArgs)
            if not hwdrv.init():
                self.logger.error("failed on {}...".format(port))
                hwdrv.close()
                continue

            answer = hwdrv.unique_id()
            if not answer['success']:
                self.logger.error("failed on {}...".format('unique_id'))
                hwdrv.close()
                continue

            _teensy = {"port": port,
                       "version": self.VERSION,
                       "hwdrv": hwdrv,
                       "unique_id": answer['result']['unique_id'],
                       "usb_path": usb_path,
                       "close": hwdrv.close,
                       # NOTE: !! If not using jig_closed_detect this should be NONE !!
                       "play": hwdrv.jig_closed_detect,
                       "show_pass_fail": hwdrv.show_pass_fail,
                       "jig_reset": hwdrv.jig_reset}

            self.logger.info(_teensy)
            self.teensys.append(_teensy)

        self._num_chan = len(self.teensys)
        if self._num_chan == 0:
            pub_notice("HWDriver:{}: no BOND found".format(self.SFN), sender=sender,
                       type=NOTICE_TYPE.ERROR)
            return -1, DRIVER_TYPE, []

        # sort based on USB path, slot 0, 1, 2, etc
        self.teensys = sorted(self.teensys, key=lambda d: d['usb_path'])
        # fix the slot IDs as the slot order is set by the USB path
        for idx, t in enumerate(self.teensys):
            t["id"] = idx

        self.logger.info(self.teensys)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, self.teensys

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
