#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2021
Martin Guthrie

This driver can be used for PyBoard only, OR can be used for IBA01,
OR can be used as a template for any design that embeds a PyBoard.

"""
import os
import logging

from public.prism.drivers.iba01.list_serial import serial_ports
from public.prism.drivers.iba01.IBA01 import IBA01, VERSION, DRIVER_TYPE

from core.const import PUB
from core.sys_log import pub_notice


class HWDriver(object):
    """ Determine MicroPyBoards attached to the system, and report them to the system shared state.
    """
    SFN = os.path.basename(__file__)

    MICROPYTHON_FIRMWARE_RELEASE = "1.11.0"  # from os.uname() on pyboard
    IBA01_SERVER_VERSION = "0.2"

    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, self.SFN))
        self.logger.info("Start")
        self.drivers = []
        self._num_chan = 0

    def discover_channels(self):
        """ determine the number of channels, and populate hw drivers into shared state

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <foobar>,          # instance of your hardware driver

           # optional
           "close": None},             # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed

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
        self.drivers.clear()

        sender = "{}.{}".format(self.SFN, __class__.__name__)

        port_candidates = serial_ports()
        self.logger.info("Serial Ports to look for PyBoard {}".format(port_candidates))

        if len(port_candidates) == 0:
            self.logger.error("No serial port candidates found")
            return -1, DRIVER_TYPE, []

        for port in port_candidates:
            if "ttyACM" not in port:
                self.logger.info("skipping port {}...".format(port))
                continue

            _pyb = { "port": port}
            self.logger.info("Trying pyboard at {}...".format(port))

            _pyb['pyb'] = pyb = IBA01(port, loggerIn=logging.getLogger("IBA01.try"))
            success, result = pyb.start_server()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("No pyboard at {}".format(port))
                continue

            success, result = pyb.unique_id()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("pyboard {} unique_id -> {}".format(port, result))
                continue
            _pyb["unique_id"] = result["value"]["value"]

            success, result = pyb.slot()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("pyboard {} slot -> {}".format(port, result))
                continue
            _pyb["id"] = result["value"]["value"]

            success, result = pyb.version()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("pyboard {} uname -> {}".format(port, result))
                continue
            _pyb["uname"] = result["value"]["uname"]
            release = result["value"]["uname"].get("release", None)
            version = result["value"]["version"]

            # TODO: add version check.  the VERSION used in ./sd_image should be the same as remote
            #       Otherwise the remote code is not up to date!

            # confirm the release
            if release != self.MICROPYTHON_FIRMWARE_RELEASE:
                self.logger.error("pyboard {}, slot {} -> Unsupported release {} (expecting {})".format(
                        _pyb["id"], _pyb["slot"], release, self.MICROPYTHON_FIRMWARE_RELEASE))
                msg = "HWDriver ERR: PyBoard slot {} FW release not supported".format(_pyb["slot"])
                pub_notice(msg, type=PUB.NOTICES_ERROR, sender=sender)
                continue

            # confirm the server version
            if version != self.IBA01_SERVER_VERSION:
                self.logger.error("pyboard {}, slot {} -> Unsupported version {} (expecting {})".format(
                        _pyb["id"], _pyb["slot"], version, self.IBA01_SERVER_VERSION))
                msg = "HWDriver ERR: PyBoard slot {} IBA01_SERVER_VERSION not supported".format(_pyb["slot"])
                pub_notice(msg, type=PUB.NOTICES_ERROR, sender=sender)
                continue
            _pyb["version"] = version

            # close, or else problems trying to re-open
            _pyb["close"] = pyb.close

            # install play callback
            _pyb["play"] = pyb.jig_closed_detect

            self.drivers.append(_pyb)
            msg = "HWDriver:{}: {}".format(self.SFN, _pyb)
            self.logger.info(msg)
            pub_notice(msg, sender=sender)

        self._num_chan = len(self.drivers)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, self.drivers

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
