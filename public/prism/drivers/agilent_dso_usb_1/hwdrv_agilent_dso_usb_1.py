#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Martin Guthrie, copyright, all rights reserved, 2018-2021

"""
import os
import re
import logging
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice
import pyudev
import pyvisa


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example, one scope shared by all channels,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.fake.hwdrv_fake",
                    ["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1",
                     {"only_one": true}]]
      },

    or one scope per channel (the default), on USB in USB hub port order,

        "drivers": ["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1"]

    or on Ethernet, one IP per channel, in channel order,

        "drivers": [["public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1",
                     {"interface": "ethernet", "ip": ["192.168.1.100", "192.168.1.101"]}]]

    drivers is a list, so multiple HWDriver can be installed.

    Agilent DSO of "type 1"
    - presumably most Agilent scopes are compatible with each other...
    - those that are compatible can share the same driver...(presumably)
    - this driver supports USB (default) or Ethernet attached devices, found with VISA
    - Ethernet uses VXI-11, TCPIP0::<ip>::INSTR, set the scope's IP from its Utility menu
    - See https://pyvisa.readthedocs.io/en/1.8/names.html
    - USB[board]::manufacturer ID::model code::serial number[::USB interface number][::INSTR]
    - DSO Agilent DSO7104B, returns ('USB0::2391::5981::MY49520121::0::INSTR',)
    - therefore, assuming 2391::5981, means Agilent DSO7000 series (?)
    - query('*IDN?') returns
        AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003
    - each scope is reset (*RST) when it is found

    - see Agilent InfiniiVision 7000 Series Oscilloscopes Programmer's Guide,
      InfiniiVision7000_series_prog_guide.pdf

    USB permissions: (for the error, "Found a device whose serial number cannot be read")
    - https://stackoverflow.com/questions/52256123
      (unable to get full visa address that includes the serial number)
    - not needed for Prism in Docker, on the host run sudo ./udev-install-usbusers.sh,
      or for just the scope add a udev rule, /etc/udev/rules.d/99-agilent-dso.rules,
        SUBSYSTEM=="usb", ATTR{idVendor}=="0957", ATTR{idProduct}=="175d", MODE="0666"
      then, sudo udevadm control --reload-rules && sudo udevadm trigger, and re-plug the scope
    """
    SFN = os.path.basename(__file__)

    VERSION = "0.1.0"
    DRIVER_TYPE = "AGILENT_DSO_USB_1"
    QUERY_STRING = 'USB?::2391::5981::?*::?*::INSTR'  # look for USB Agilent scopes only...
    USB_VENDOR_ID = "0957"  # 2391
    USB_SERIAL_FIELD = 3  # USB0::2391::5981::<serial>::0::INSTR
    USB_PATH_UNKNOWN = (10_000,)  # sorts after every USB hub port path
    TCPIP_RESOURCE = 'TCPIP0::{}::INSTR'
    INTERFACES = ["usb", "ethernet"]
    OPEN_TIMEOUT_MS = 5000
    # list of DSOs that accept the same command set
    WHITE_LIST = ["DSO7104B"]

    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, self.SFN))
        self.logger.info("Start")
        self._num_chan = 0
        self.instrs = []

    def _usb_port_paths(self):
        """ USB hub port path of each Agilent USB device, by serial number
        - sys_name '1-2.3' -> (1, 2, 3)

        :return: {serial: (path numbers)}
        """
        paths = {}
        for dev in pyudev.Context().list_devices(subsystem="usb", DEVTYPE="usb_device"):
            attrs = dev.attributes
            vid = attrs.get("idVendor")
            serial = attrs.get("serial")
            if vid is None or serial is None:
                continue
            if vid.decode(errors="ignore").strip() != self.USB_VENDOR_ID:
                continue
            nums = tuple(int(x) for x in re.findall(r"\d+", dev.sys_name or ""))
            paths[serial.decode(errors="ignore").strip()] = nums or self.USB_PATH_UNKNOWN
        return paths

    def _usb_resources(self, rm):
        """ VISA resources of the USB Agilent scopes, in USB hub port order
        """
        self.logger.info(rm.list_resources())
        resources = rm.list_resources(query=self.QUERY_STRING)
        paths = self._usb_port_paths()

        def key(resource):
            fields = resource.split("::")
            serial = fields[self.USB_SERIAL_FIELD] if len(fields) > self.USB_SERIAL_FIELD else ""
            return paths.get(serial, self.USB_PATH_UNKNOWN), resource
        return sorted(resources, key=key)

    def _open(self, rm, resource):
        """ Open a scope, if it is in the WHITE_LIST

        :return: instr, idn, or None, None
        """
        try:
            instr = rm.open_resource(resource, open_timeout=self.OPEN_TIMEOUT_MS)
        except Exception as e:
            self.logger.error("{}: {}".format(resource, e))
            return None, None
        try:
            idn = instr.query('*IDN?').strip()
        except Exception as e:
            self.logger.error("{}: {}".format(resource, e))
            instr.close()
            return None, None

        # idn looks like: AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003
        if not any(scope in idn for scope in self.WHITE_LIST):
            self.logger.warning("{}: not supported: {}".format(resource, idn))
            instr.close()
            return None, None
        return instr, idn

    def _error(self, sender, msg):
        self.logger.error(msg)
        pub_notice("HWDriver:{}: Error {}".format(self.SFN, msg), sender=sender,
                   type=NOTICE_TYPE.ERROR)
        self.close()
        return -1, self.DRIVER_TYPE, []

    def discover_channels(self, scriptArgs=None):
        """ Determine the number of channels, and populate hw drivers into shared state

        :param scriptArgs: None, or {"only_one": true|false,
                                     "interface": "usb"|"ethernet",
                                     "ip": <ip address> | [<ip address>, ...]}
            only_one = true: one scope is shared by all channels (returns 0 channels),
                       finding more than one scope is an error
                       false (default): one scope per channel (returns the number found)
            interface = optional, default "usb"
            ip = required when interface is "ethernet", a list gives one scope per channel
                 in list order, every scope in the list must be found

        Multiple USB scopes are ordered by the USB hub port they are connected to, the
        first scope is channel 0, the next channel 1, etc.

        A scope does not use play, show_pass_fail, show_msg or jig_reset.

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
        only_one = bool(scriptArgs.get("only_one", False))

        interface = scriptArgs.get("interface", "usb")
        if interface not in self.INTERFACES:
            self.logger.error("Unknown interface: {}".format(interface))
            raise ValueError("Unknown driver argument interface: {}, use one of {}".format(
                interface, self.INTERFACES))

        ips = None
        if interface == "ethernet":
            ips = scriptArgs.get("ip")
            if isinstance(ips, str):
                ips = [ips]
            if not ips or not isinstance(ips, list) or \
                    not all(isinstance(ip, str) and ip for ip in ips):
                self.logger.error("Missing or invalid argument ip: {}".format(ips))
                raise ValueError("Missing or invalid driver argument ip, "
                                 "use an IP address or a list of them")

        pub_notice("HWDriver:{}: Scanning for {} on {}".format(self.SFN, self.DRIVER_TYPE,
                                                               interface), sender=sender)

        rm = pyvisa.ResourceManager()
        if ips is not None:
            if only_one and len(ips) > 1:
                return self._error(sender, "only_one, but {} IPs given".format(len(ips)))
            resources = [self.TCPIP_RESOURCE.format(ip) for ip in ips]
        else:
            resources = self._usb_resources(rm)

        drivers = []
        for resource in resources:
            instr, idn = self._open(rm, resource)
            if instr is None:
                if ips is not None:
                    # a missing scope would move the next scopes to the wrong channel
                    return self._error(sender, "scope not found at {}".format(resource))
                continue
            self.instrs.append(instr)
            self.logger.info("found: {} {}".format(resource, idn))

            # reset scope to a known state
            instr.write('*RST')

            drivers.append({"id": len(drivers),
                            "version": self.VERSION,
                            "close": instr.close,
                            "hwdrv": instr,
                            "unique_id": idn.split(",")[2] if idn.count(",") >= 2 else idn})

        if not drivers:
            # if no scope is found, the test fixture cannot operate, returning
            # an error here will indicate a system fail and won't proceed to testing
            return self._error(sender, "none found")

        if only_one and len(drivers) > 1:
            # can't know which scope is the shared one
            return self._error(sender, "only one scope expected, found {}".format(len(drivers)))

        pub_notice("HWDriver:{}: found {}".format(self.SFN, len(drivers)), sender=sender)

        # zero channels means the scope is shared across all test jigs,
        # otherwise one scope per jig (channel)
        self._num_chan = 0 if only_one else len(drivers)
        self.logger.info("{} channels found".format(self._num_chan))
        return self._num_chan, self.DRIVER_TYPE, drivers

    def num_channels(self):
        return self._num_chan

    def close(self):
        for instr in self.instrs:
            instr.close()
        self.instrs = []


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

    # USB is the default, for Ethernet give the scope IPs, for example,
    #     $ python -m public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1 192.168.1.100
    import sys
    args = {"interface": "ethernet", "ip": sys.argv[1:]} if len(sys.argv) > 1 else None

    d = HWDriver()
    num_channels, driver_type, drivers = d.discover_channels(args)
    logger.info("discover_channels: num channels {}, type {}, drivers {}".format(num_channels,
                                                                                 driver_type,
                                                                                 drivers))
    if drivers:
        d.close()
