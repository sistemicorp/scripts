#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
from core.const import APP
import logging
logger = logging.getLogger("sys_log")

def pub_notice(notice, sender, type=APP.NOTICE_NRM, on_change_only=False, replace=False):
    logger.info(notice)
