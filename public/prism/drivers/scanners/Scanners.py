#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


# this is the (example) version of the remote hardware
VERSION = "0.2.0"
DRIVER_TYPE = "SCANNER"


class Scanner(object):
    """ Scanners HW Driver
    - this driver actually does nothing

    """

    def __init__(self, loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

    def version(self):
        """ Version of this driver.  Typically this would be coming
        from the remote hardware.  The version of remote software/hardware
        should be something that is expected.

        :return:
        """
        return VERSION

    def close(self):
        """ Always called at the end of a test sequence by Prism
        - perform any reset, or closing of the hardware if the testing is done, or ended
        - note the result state (Pass|Fail) of the DUT is not known and should not be assumed,
          meaning that this hardware may be in an unknown state.  This close() function
          allows you to get back to a known state, if required.

        :return: None
        """
        self.logger.info("closing")
