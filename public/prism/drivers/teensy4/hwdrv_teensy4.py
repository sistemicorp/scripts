#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import os
import logging
import argparse
from core.sys_log import pub_notice
from public.prism.drivers.iba01.list_serial import serial_ports

from Teensy4 import Teensy4

DRIVER_TYPE = "TEENSY4"


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    When a script is loaded, there is a config section that lists all the HWDriver
    to call, for example,

      "config": {
        # drivers: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.teensy4.hwdrv_teensy4"]
      },

    """
    SFN = os.path.basename(__file__)
    VERSION = "0.0.1"

    def __init__(self, shared_state):
        self.logger = logging.getLogger("SC.{}.{}".format(__class__.__name__, self.SFN))
        self.logger.info("Start")
        self.shared_state = shared_state
        self._num_chan = 0
        self.teensys = []

    def discover_channels(self):
        """ determine the number of channels, and populate hw drivers into shared state

        shared_state: a list,
            self.shared_state.add_drivers(DRV_TYPE, [ {}, {}, ... ], shared=True/False)

        [ {'id': i,                 # slot id of the channel (see Note 1)
           "version": <VERSION>,    # version of the driver
           "close": Teensy4.close}, # register a callback on closing the channel
           "teensy4": Teensy4(),    # class that makes your HW work...
           "port": serial port
           "unique_id": unique_id   # cache this here so that it doesn't need to be retrieved for every test
        ]

        Note:
        1) The hw driver objects are expected to have an 'id' field, the lowest
           id is assigned to channel 0, the next highest to channel 1, etc

        :return: >0 number of channels,
                  0 does not indicate num channels, like a shared hardware driver
                 <0 error
        """
        sender = "{}.{}".format(self.SFN, __class__.__name__)  # for debug purposes

        port_candidates = serial_ports()
        self.logger.info("Serial Ports to look for PyBoard {}".format(port_candidates))

        for port in port_candidates:
            if "ttyACM" not in port:
                self.logger.info("skipping port {}...".format(port))
                continue

            _teensy = { "port": port}
            self.logger.info("Trying teensy at {}...".format(port))

            # test if this COM port is really a Teensy
            # create an instance of Teensy()
            _teensy['teensy4'] = Teensy4(port, loggerIn=logging.getLogger("teensy.try"))
            success = _teensy['teensy'].init()
            if not success:
                self.logger.info("failed on {}...".format(port))
                continue

            # yes, its a Teensy, add it to the list...

            # TODO: get (channel) id
            # TODO: get unique_id... this is for test tracking purposes

            _teensy['close'] = _teensy['teensy'].close

            self.teensys.append(_teensy)

        self._num_chan = len(self.teensys)
        self.shared_state.add_drivers(DRIVER_TYPE, self.teensys, shared=False)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan

    def num_channels(self):
        return self._num_chan

    def init_play_pub(self):
        """ Function to instantiate a class/thread to trigger PLAY of script
        - this is called right after discover_channels
        """
        self.logger.info("HWDriver:{}: does not support 'play' messaging".format(self.SFN))

    def close(self):
        self.logger.info("closed")


# -----------------------------------------------------------------------------------------------------
# CLI interface example to test the driver


def parse_args():
    epilog = """
    Usage examples:
    """
    parser = argparse.ArgumentParser(description='fake',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')
    parser.add_argument("--version", dest="show_version", action='store_true', help='Show version and exit')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    logger = logging.getLogger()
    args = parse_args()

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)6s %(lineno)4s %(message)s')

    d = HWDriver()
    logger.info("Number channels: {}".format(d.num_channels()))
