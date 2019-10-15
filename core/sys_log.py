#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
from core.const import PUB
import logging
logger = logging.getLogger("sys_log")

def pub_notice(notice, sender, type=PUB.NOTICES_NORMAL, on_change_only=False, replace=False):
    logger.info(notice)

