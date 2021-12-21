#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import random

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.iba01.stublogger import StubLogger


# this is the (example) version of the remote hardware
VERSION = "0.2.0"
DRIVER_TYPE = "FAKE"


class Fake(object):
    """ Example of a hardware driver class

    """

    def __init__(self, loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        # create an instance of the hardware driver...
        # this might be a serial port,
        #                 arduino-simpe-rpc Instance,
        #                 VISA, etc
        self._hwdrv = None

        self._uniqie_id = random.randint(0, 999)
        self._id = random.randint(0, 999)

    def version(self):
        """ Version of this driver.  Typically this would be coming
        from the remote hardware.  The version of remote software/hardware
        should be something that is expected.

        :return:
        """
        # remote_version = self._hwdrv.version()
        return VERSION

    def unique_id(self):
        """ A string that uniquely identifies this piece of hardware.
        Used for tracking purposes.

        :return: string
        """
        return "{:04}".format(self._uniqie_id)

    def id(self):
        """ The id is related to the channel/slot number which is related
        to the physical locations of the test jigs.  Prism will arrange the
        slots such that the lowest id is channel/slot 0, etc

        :return: integer
        """
        return self._id

    def close(self):
        pass

    def jig_closed_detect(self):
        self.logger.info("False")
        return False

    def show_pass_fail(self, p, f, o):
        self.logger.info("{} {} {}".format(p, f, o))

