#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

"""
from public.prism.drivers.common.stublogger import StubLogger


# this is the (example) version of the remote hardware
VERSION = "0.3.0"
DRIVER_TYPE = "SCANNER"


class Scanner(object):
    """ Barcode Scanner HW Driver

    The scanner is in USB keyboard mode, so scans arrive in the Prism textbox,
    not through this driver.  The driver restarts the script after each scan,
    so the operator just keeps scanning.
    """
    def __init__(self, loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self._player_stopped = False
        self._close = False

    # TODO: function to send a command to the scanner to alert the User
    #       that prism is ready for the user to scan.  Scanners
    #       support this feature.

    def stop_player(self):
        """ Stop restarting the script, until start_player() """
        self._player_stopped = True
        self.logger.info("stop_player")

    def start_player(self):
        """ Restart the script after each scan """
        if self._player_stopped: self.logger.info("start_player")
        self._player_stopped = False

    def player_stopped(self):
        return self._player_stopped

    def jig_closed_always(self):
        """ "Auto" Jig Open/Close
        - NOTE: because Prism calls here every 1sec and because Prism needs to
                see the Jig Open/Close, it can take up to 2sec before Prism
                is ready to Scan again
        """
        if self._player_stopped:
            return False

        # toggle response so that Prism thinks the jig is opening and closing.
        temp = self._close
        self._close = not temp
        return temp
