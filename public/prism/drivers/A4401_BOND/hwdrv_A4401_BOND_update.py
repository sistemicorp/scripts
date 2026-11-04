#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
import os
import logging
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice

from public.prism.drivers.A4401_BOND.A4401_BOND import A4401_BOND, DRIVER_TYPE_UPDATE
from public.prism.drivers.A4401_BOND.hwdrv_A4401_BOND import teensy_ports

DRIVER_TYPE = DRIVER_TYPE_UPDATE


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.A4401_BOND.hwdrv_A4401_BOND_update"]
      },

    drivers is a list, so multiple HWDriver can be installed.

    This driver is for updating the firmware of BONDs that are already programmed,
    only used with script: bond_update_0.scr.

    Unlike hwdrv_A4401_BOND, it only connects to each BOND and reads its unique id and
    firmware version.  The firmware version is NOT checked, so a BOND running an older
    (or newer) firmware is found and can be updated.  No header definition file is
    used, the jig does not need to be closed, and the BOND self test is not run.
    UPD020_verify checks the new firmware with the full driver init.
    """
    SFN = os.path.basename(__file__)
    VERSION = "0.0.1"

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0
        self.teensys = []  # holds a list of all objects found

    def discover_channels(self, scriptArgs=None):
        """ Determine the number of channels, and populate hw drivers into shared state

        :param scriptArgs: not used

        [ {"id": i,                    # slot number of the channel, USB path order
           "version": <VERSION>,       # version of this hwdrv
           "hwdrv": <object>,          # A4401_BOND instance, connected only (see connect())
           "close": <callback>,
           "unique_id": <unique_id>,   # Teensy MAC
           "usb_path": <path>,         # USB device path, finds the port after the update
           "port": <port>,
           "fw_version": <version>,    # firmware version running before the update
          }, ...
        ]

        :return: <#>, <driver_type>, <list>
            where
                #:      >0 number of channels, <0 error
                driver_type: String constant identifying Installed drivers type
                list:   List of installed driver dicts
        """
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        port_candidates = teensy_ports()
        self.logger.info("Serial Ports to look for Teensy {}".format(port_candidates))
        for port, usb_path in port_candidates:
            self.logger.info(f"Trying teensy at {port}")
            hwdrv = A4401_BOND(port, loggerIn=logging.getLogger("teensy.try"))
            if not hwdrv.connect():
                self.logger.error("failed on {}...".format(port))
                hwdrv.close()
                continue

            version = hwdrv.version()
            answer = hwdrv.unique_id()
            if not version['success'] or not answer['success']:
                self.logger.error(f"failed on {port}, version {version}, unique_id {answer}")
                hwdrv.close()
                continue

            _teensy = {"port": port,
                       "version": self.VERSION,
                       "hwdrv": hwdrv,
                       "unique_id": answer['result']['unique_id'],
                       "usb_path": usb_path,
                       "fw_version": version['result']['version'],
                       "close": hwdrv.close}

            self.logger.info(_teensy)
            self.teensys.append(_teensy)

        self._num_chan = len(self.teensys)
        if self._num_chan == 0:
            pub_notice("HWDriver:{}: no BOND found".format(self.SFN), sender=sender,
                       type=NOTICE_TYPE.ERROR)
            return -1, DRIVER_TYPE, []

        # sort based on USB path, slot 0, 1, 2, etc
        self.teensys = sorted(self.teensys, key=lambda d: d['usb_path'])
        for idx, t in enumerate(self.teensys):
            t["id"] = idx

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, self.teensys

    def num_channels(self):
        return self._num_chan

    def close(self):
        self.logger.info("closed")


# ===============================================================================================
# Debugging code
# - Test your hardware discovery here by running this file from a terminal,
#     $ cd ~/git/scripts
#     $ python -m public.prism.drivers.A4401_BOND.hwdrv_A4401_BOND_update
#
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    d = HWDriver()
    d.discover_channels()
    logger.info("Number channels: {}".format(d.num_channels()))
