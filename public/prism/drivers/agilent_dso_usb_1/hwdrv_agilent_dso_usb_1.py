#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Martin Guthrie, copyright, all rights reserved, 2018-2021

"""
import os
import logging
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice
import pyvisa


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.fake.hwdrv_fake",
                    "public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1"]
      },

    or, for a scope on Ethernet,

        "drivers": ["public.prism.drivers.fake.hwdrv_fake",
                    ["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1",
                     {"interface": "ethernet", "ip": "192.168.1.100"}]]

    drivers is a list, so multiple HWDriver can be installed.

    Create a single instance of an Agilent DSO of "type 1"
    - presumably most Agilent scopes are compatible with each other...
    - those that are compatible can share the same driver...(presumably)
    - this driver supports USB (default) or Ethernet attached devices, found with VISA,
      not pyudev
    - Ethernet uses VXI-11, TCPIP0::<ip>::INSTR, set the scope's IP from its Utility menu
    - See https://pyvisa.readthedocs.io/en/1.8/names.html
    - USB[board]::manufacturer ID::model code::serial number[::USB interface number][::INSTR]
    - DSO Agilent DSO7104B, returns ('USB0::2391::5981::MY49520121::0::INSTR',)
    - therefore, assuming 2391::5981, means Agilent DSO7000 series (?)
    - query('*IDN?') returns
        AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003

    - see Agilent InfiniiVision 7000 Series Oscilloscopes Programmer's Guide,
      InfiniiVision7000_series_prog_guide.pdf

    USB permissions: (for the error, "Found a device whose serial number cannot be read")
    - https://stackoverflow.com/questions/52256123
      (unable to get full visa address that includes the serial number)
    - not needed for Prism in Docker, on the host run sudo ./udev-install-usbusers.sh,
      or for just the scope add a udev rule, /etc/udev/rules.d/99-agilent-dso.rules,
        SUBSYSTEM=="usb", ATTR{idVendor}=="0957", ATTR{idProduct}=="175d", MODE="0666"
      then, sudo udevadm control --reload-rules && sudo udevadm trigger, and re-plug the scope

    NOTE: This driver assumes only one scope is attached to the PC
          and this scope is shared among the channels
    """
    SFN = os.path.basename(__file__)

    VERSION = "0.0.1"
    DRIVER_TYPE = "AGILENT_DSO_USB_1"
    QUERY_STRING = 'USB?::2391::5981::?*::?*::INSTR'  # look for USB Agilent scopes only...
    TCPIP_RESOURCE = 'TCPIP0::{}::INSTR'
    INTERFACES = ["usb", "ethernet"]
    OPEN_TIMEOUT_MS = 5000
    # list of DSOs that accept the same command set
    WHITE_LIST = ["DSO7104B"]

    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, self.SFN))
        self.logger.info("Start")
        self.drivers = []
        self._num_chan = 0  # not used in this driver
        self.instr = None

    def discover_channels(self, scriptArgs=None):
        """ Determine the number of channels, and populate hw drivers into shared state

        :param scriptArgs: None, or {"interface": "usb"|"ethernet", "ip": <ip address>}
            interface = optional, default "usb"
            ip = required when interface is "ethernet"

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
        sender = "{}.{}".format(self.SFN, __class__.__name__)
        scriptArgs = scriptArgs or {}

        interface = scriptArgs.get("interface", "usb")
        if interface not in self.INTERFACES:
            self.logger.error("Unknown interface: {}".format(interface))
            raise ValueError("Unknown driver argument interface: {}, use one of {}".format(
                interface, self.INTERFACES))

        if interface == "ethernet":
            if "ip" not in scriptArgs:
                self.logger.error("Missing required argument: ip")
                raise ValueError("Missing required driver argument: ip")
            resources = [self.TCPIP_RESOURCE.format(scriptArgs["ip"])]
        else:
            resources = None  # scanned below

        pub_notice("HWDriver:{}: Scanning for {} on {}".format(self.SFN, self.DRIVER_TYPE,
                                                               interface), sender=sender)

        rm = pyvisa.ResourceManager()
        if resources is None:
            self.logger.info(rm.list_resources())
            resources = rm.list_resources(query=self.QUERY_STRING)

        # find the first scope
        found = False
        for dso in resources:
            try:
                instr = rm.open_resource(dso, open_timeout=self.OPEN_TIMEOUT_MS)
                deets = instr.query('*IDN?').strip()
            except Exception as e:
                self.logger.error("{}: {}".format(dso, e))
                continue

            for scope in self.WHITE_LIST:
                # deets looks like: AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003
                if scope in deets:
                    found = True
                    break

            if found:
                self.instr = instr
                self.logger.info("found: {} {}".format(dso, deets))
                break
            instr.close()

        if not found:
            self.logger.error("No matching {} VISA instrument found".format(
                resources if interface == "ethernet" else self.QUERY_STRING))
            pub_notice("HWDriver:{}: Error none found".format(
                self.SFN), sender=sender, type=NOTICE_TYPE.ERROR)

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


# ===============================================================================================
# Debugging code
# - Test your hardware discovery here by running this file from a terminal,
#     $ cd ~/git/scripts
#     $ python -m public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1
#   or from PyCharm (be sure to set the working directory as ~/git/scripts, else imports will fail)
# - the purpose is to validate discover_channels() is working
# - ~/git/scripts/core has stand-ins for the Prism core imports, pub_notice() only logs
#
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # USB is the default, for Ethernet give the scope's IP, for example,
    #     $ python -m public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1 192.168.1.100
    import sys
    args = {"interface": "ethernet", "ip": sys.argv[1]} if len(sys.argv) > 1 else None

    d = HWDriver()
    num_channels, driver_type, drivers = d.discover_channels(args)
    logger.info("discover_channels: num channels {}, type {}, drivers {}".format(num_channels,
                                                                                 driver_type,
                                                                                 drivers))
    if drivers:
        d.close()
