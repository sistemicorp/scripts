#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2022
Martin Guthrie

"""


class StubLogger(object):
    """ stubb out logger if none is provided"""
    # TODO: support print to console.
    def info(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def debug(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def critical(self, *args, **kwargs): pass
    