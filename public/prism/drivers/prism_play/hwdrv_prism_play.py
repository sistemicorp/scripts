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
from public.prism.drivers.prism_play.prism_play import PrismPlay

NUM_CHANNELS_DEFAULT = 1  # set this to simulate multiple channels, range 1-4


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.
    """
    SFN = os.path.basename(__file__)  # for logging path

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")

    def discover_channels(self, scriptArgs=None):
        """ determine the number of channels, and popultae hw drivers into shared state

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

        :return: <#>, <list> (use Zero for a device shared across all channels)
            where #: >0 number of channels,
                      0 does not indicate num channels, like a shared hardware driver
                     <0 error

                  list of drivers
        """
        drivers = []

        if "work_dir" not in scriptArgs:
            self.logger.error("Missing required argument: work_dir")
            raise ValueError("Missing required driver argument: work_dir")
        work_dir = scriptArgs["work_dir"]

        if "channels" in scriptArgs:
            self._num_channels = scriptArgs["channels"]
        else:
            self._num_channels = NUM_CHANNELS_DEFAULT

        # ------------------------------------------------------------------
        # Your specific driver discovery code goes here
        #

        for channel in range(self._num_channels):
            try:
                _driver = PrismPlay(
                    channel=channel, work_dir=work_dir, loggerIn=self.logger
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize PrismPlay driver for channel {channel}: {e}",
                    exc_info=True,
                )
                pub_notice(f"HWDriver: Failed to initialize driver for channel {channel}")
                raise

            # create the dict with keys expected by Prism
            _d = {'id': channel,
                  "version": _driver.version(),
                  "hwdrv": _driver,
                  "unique_id": _driver.unique_id(),
                  "play": _driver.jig_closed_detect,  # _driver.jig_closed_detect,
                  "show_pass_fail": _driver.show_pass_fail,
                  "show_msg": _driver.show_msg,
                  "close": _driver.close}  # good practice to have in place

            #
            # End of your specific driver code
            # -------------------------------------------------------------------

            drivers.append(_d)
            pub_notice("HWDriver:{}: Found channel {}".format(self.SFN, channel),
                       sender="{}.{}".format(self.SFN, __class__.__name__))

        self.logger.info("{} channels found".format(self._num_channels))
        return self._num_channels, PrismPlay.DRIVER_TYPE, drivers

    def num_channels(self):
        return self._num_channels


# ===============================================================================================
# Debugging code
# - Test your hardware discover here by running this file from a terminal
#
if __name__ == '__main__':
    logger = logging.getLogger()

    d = HWDriver()

    num_channels, driver_type, drivers = d.discover_channels()
    logger.info("discover_channels: num channels {}, type {}, drivers {}".format(num_channels,
                                                                                 driver_type,
                                                                                 drivers))
