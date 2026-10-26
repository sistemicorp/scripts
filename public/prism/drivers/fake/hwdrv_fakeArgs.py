#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2024
Martin Guthrie

"""
import os
import logging
from core.sys_log import pub_notice

# import your hardware driver class, and details
from public.prism.drivers.fake.Fake import Fake, VERSION

NUM_CHANNELS = 1  # set this to simulate multiple channels, range 1-4
DRIVER_TYPE = "FakeWithArgs"


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": [ ["public.prism.drivers.fake.hwdrv_fakeArgs", "my_args"] ]
      },

    drivers is a list, so multiple HWDriver can be installed.

    This example shows how to make a hardware driver with arguments.
    The arguments are the 2nd item in the list specifying the driver.

    Other examples,
        "drivers": [ ["public.prism.drivers.fake.hwdrv_fakeArgs", {"k0": val1, "k1": val2, ...}] ]
        "drivers": [ ["public.prism.drivers.fake.hwdrv_fakeArgs", ["a", 1, "b", 2, ...]] ]

    Argument format is up to the driver, and needs to be handled in discover_channels()

    This is a fake HW driver to simulate and show what a HWDriver is required to do.
    """
    SFN = os.path.basename(__file__)  # for logging path

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")

    def discover_channels(self, scriptArgs):
        """ Determine the number of channels, and populate hw drivers into shared state

        :param scriptArgs: the 2nd item of the driver spec in the script, any format,
                           this example only logs it

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

        # ------------------------------------------------------------------
        # Your specific driver discovery code goes here
        #
        self.logger.info(f"script args: {scriptArgs}")

        for i in range(NUM_CHANNELS):  # NUM_CHANNELS is used to fake more than one test jig
            _driver = Fake(self.logger)

            remote_version = _driver.version()

            _id = _driver.id()

            if remote_version != VERSION:
                self.logger.error("{} has unexpected version {} != {}".format(
                    _id, remote_version, VERSION))
                continue

            # ... perform any other validation of the remote hardware as required here

            # create the dict with keys expected by Prism
            _d = {'id': _id,
                  "hwdrv": _driver,
                  "unique_id": _driver.unique_id(),
                  "version": _driver.version(),
                  "play": None,  # _driver.jig_closed_detect,
                  "play_poll_sec": 1,  # seconds between play calls, 0.2 to 2, default 1
                  "show_pass_fail": _driver.show_pass_fail,

                  "close": _driver.close}  # good practice to have in place

            #
            # End of your specific driver code
            # -------------------------------------------------------------------

            drivers.append(_d)
            pub_notice("HWDriver:{}: Found channel {}".format(self.SFN, i),
                       sender="{}.{}".format(self.SFN, __class__.__name__))

        self._num_chan = 0  # this example driver is a shared driver
        self.logger.info("{} channels found".format(self._num_chan))
        return self._num_chan, DRIVER_TYPE, drivers

    def num_channels(self):
        return self._num_chan


# ===============================================================================================
# Debugging code
# - Test your hardware discovery here by running this file from a terminal,
#     $ cd ~/git/scripts
#     $ python -m public.prism.drivers.fake.hwdrv_fakeArgs
#   or from PyCharm (be sure to set the working directory as ~/git/scripts, else imports will fail)
# - the purpose is to validate discover_channels() is working
# - ~/git/scripts/core has stand-ins for the Prism core imports, pub_notice() only logs
#
if __name__ == '__main__':
    logger = logging.getLogger()

    d = HWDriver()

    args = {"k0": 0, "k1": 1}
    num_channels, driver_type, drivers = d.discover_channels(args)
    logger.info("discover_channels: num channels {}, type {}, drivers {}".format(num_channels,
                                                                                 driver_type,
                                                                                 drivers))
