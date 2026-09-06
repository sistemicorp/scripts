#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

Development stub of the Prism core constants.  Only the names that shared
driver/script code is allowed to use are defined here, and they must match
core/const.py in a08-prismNG -- a name that exists here but not there dies
in the GUI (MetaConst.__getattr__ recurses instead of raising AttributeError).

Note: PUB is intentionally NOT stubbed.  Its pubsub topics are a GUI-internal
concern; drivers and test scripts talk to the sys log via pub_notice() only.
"""


class NOTICE_TYPE():
    """ Severity of a sys-log notice, passed as pub_notice(type=...) """
    NORMAL = "NORMAL"
    WARN = "WARN"
    ERROR = "ERROR"
