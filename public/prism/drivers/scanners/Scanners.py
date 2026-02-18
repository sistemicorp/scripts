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
    - this driver actually does nothing (very little)

    """
    def __init__(self, loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self._stop_prism_player = False
        self._close = False

    def stop_prism_player(self):
        self._stop_prism_player = True
        self.logger.info("stop_prism_player")

    def jig_closed_always(self):
        """ "Auto" Jig Open/Close
        - NOTE: because Prism calls here every 1sec and because Prism needs to
                see the Jig Open/Close, it can take up to 2sec before Prism
                is ready to Scan again
        """
        if self._stop_prism_player:
            self.logger.info(False)
            return False

        # toggle response so that Prism thinks the jig is opening and closing.
        temp = self._close
        self._close = not temp

        return temp
