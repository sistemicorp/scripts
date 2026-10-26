#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

"""
import os
import logging
from core.const import NOTICE_TYPE
from core.sys_log import pub_notice

# import your hardware driver class, and details
from public.prism.drivers.ble_listener.BLEListener import BLEListener, DRIVER_TYPE


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.ble_listener.hwdrv_blelistener"]
      },

    drivers is a list, so multiple HWDriver can be installed.

    Installs the BLE Listener, a shared resource across all channels.
    It uses the BLE adapter of the station (bleak, over D-Bus), it does not scan USB.
    Returns 0 channels, so another driver must set the number of channels.
    """
    SFN = os.path.basename(__file__)  # for logging path

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = None

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
        drivers = []
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        # ------------------------------------------------------------------
        # Your specific driver discovery code goes here
        #

        # There is only ONE BLE Listener
        _driver = BLEListener(loggerIn=self.logger)
        if not _driver.start_scanner():
            msg = "BLE scanner failed to start, check the adapter is on and D-Bus is mounted"
            self.logger.error(msg)
            pub_notice("HWDriver:{}: {}".format(self.SFN, msg), sender=sender,
                       type=NOTICE_TYPE.ERROR)
            return -1, DRIVER_TYPE, []

        # create the dict with keys expected by Prism
        _d = {'id': _driver.id(),
              "hwdrv": _driver,
              "unique_id": _driver.unique_id(),
              "version": _driver.version(),
              "play": None,
              "show_pass_fail": None,
              "show_msg": None,
              "close": _driver.close}  # good practice to have in place

        #
        # End of your specific driver code
        # -------------------------------------------------------------------

        drivers.append(_d)
        pub_notice("HWDriver:{}: Found channel {}".format(self.SFN, 0), sender=sender)

        self._num_chan = len(drivers)
        self.logger.info("{} channels found".format(self._num_chan))
        return 0, DRIVER_TYPE, drivers

    def num_channels(self):
        return self._num_chan


# ===============================================================================================
# Debugging code
# - Test your hardware discovery here by running this file from a terminal,
#     $ cd ~/git/scripts
#     $ python -m public.prism.drivers.ble_listener.hwdrv_blelistener
#   or from PyCharm (be sure to set the working directory as ~/git/scripts, else imports will fail)
# - the purpose is to validate discover_channels() is working
# - ~/git/scripts/core has stand-ins for the Prism core imports, pub_notice() only logs
#
if __name__ == '__main__':
    logger = logging.getLogger()

    d = HWDriver()
    d.discover_channels()
    logger.info("Number channels: {}".format(d.num_channels()))
