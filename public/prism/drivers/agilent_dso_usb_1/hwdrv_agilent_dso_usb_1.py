#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Martin Guthrie, copyright, all rights reserved, 2018-2021

"""
import os
import logging
from core.const import PUB
from core.sys_log import pub_notice
import visa


class HWDriver(object):
    """
    Create a single instance of an Agilent DSO of "type 1"
    - presumably most Agilent scopes are compatible with each other...
    - those that are compatible can share the same driver...(presumably)
    - this driver supports USB attached devices
    - See https://pyvisa.readthedocs.io/en/1.8/names.html
    - SB[board]::manufacturer ID::model code::serial number[::USB interface number][::INSTR]
    - DSO Agilent DSO7104B, returns ('USB0::2391::5981::MY49520121::0::INSTR',)
    - therefore, assuming 2391::5981, means Agilent DSO7000 series (?)
    - query('*IDN?') returns
        AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003

    - see http://ridl.cfd.rit.edu/products/manuals/Agilent/oscilloscopes/InfiniiVision7000/InfiniiVision7000_series_prog_guide.pdf

    USB permissions: (for the error, "Found a device whose serial number cannot be read")
    - https://stackoverflow.com/questions/52256123/unable-to-get-full-visa-address-that-includes-the-serial-number

    NOTE: This driver assumes only one scope is attached to the PC via USB
          and this scope is shared among the channels
    """
    SFN = os.path.basename(__file__)

    VERSION = "0.0.1"
    DRIVER_TYPE = "AGILENT_DSO_USB_1"
    QUERY_STRING = 'USB?::2391::5981::?*::?*::INSTR'  # look for USB Agilent scopes only...
    # list of DSOs that accept the same command set
    WHITE_LIST = ["DSO7104B"]

    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, self.SFN))
        self.logger.info("Start")
        self.drivers = []
        self._num_chan = 0  # not used in this driver
        self.instr = None

    def discover_channels(self):
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

        :return: <#>, <list>
            where #: >0 number of channels,
                      0 does not indicate num channels, like a shared hardware driver
                     <0 error

                  list of drivers
        """
        sender = "{}.{}".format(self.SFN, __class__.__name__)
        pub_notice("HWDriver:{}: Scanning for {}".format(self.SFN, self.DRIVER_TYPE), sender=sender)

        rm = visa.ResourceManager()
        self.logger.info(rm.list_resources())
        dso_agilent_usb_list = rm.list_resources(query=self.QUERY_STRING)

        # find the first scope
        found = False
        for dso in dso_agilent_usb_list:
            self.instr = rm.open_resource(dso)
            deets = self.instr.query('*IDN?').strip()
            for scope in self.WHITE_LIST:
                # deets looks like: AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003
                if scope in deets:
                    found = True
                    break

            if found:
                self.logger.info("found: {} {}".format(found, deets))
                break

        if not found:
            self.logger.error("No matching {} VISA instrument found".format(self.QUERY_STRING))
            pub_notice("HWDriver:{}: Error none found".format(self.SFN), sender=sender, type=PUB.NOTICES_ERROR)

            # if no scope is found, the test fixture cannot operate, returning
            # an error here will indicate a system fail and won't proceed to testing
            return -1, self.DRIVER_TYPE, []

        # reset scope to a known state
        self.instr.write('*RST')

        # this is the data required by shared_state to register the driver
        d = {
            "id": 0,
            "version": self.VERSION,
            "close": self.close,
            "hwdrv": self.instr,
        }

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self.instr), sender=sender)
        self.logger.info("{} channels found".format(self._num_chan))

        # by returning 0, it means this return values DOES not represent number of channels
        return 0, self.DRIVER_TYPE, [d]

    def num_channels(self):
        return self._num_chan

    def close(self):
        self.instr.close()
