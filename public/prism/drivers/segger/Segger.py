#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2022
Martin Guthrie

"""
import threading

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


DRIVER_TYPE = "SEGGER"


class Segger:
    """ Segger driver

    """

    def __init__(self, port, loggerIn=None):
        self.lock = threading.Lock()

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.port = port
        self.rpc = None

        self.my_version = self._get_version()

    def init(self):
        """ Segger connection
        :return: <True/False>
        """

        return True

    def close(self):
        """  Close connection
          
        :return:
        """
        return True

    # ----------------------------------------------------------------------------------------------
    # Helper Functions



    # Helper Functions
    # ----------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------
    # API (wrapper functions)
    # these are the important functions
    #
    # all functions return dict: { "success": <True/False>, "result": { key: value, ... }}


    #
    # API (wrapper functions)
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    #


    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------


