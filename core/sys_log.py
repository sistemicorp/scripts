#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
from core.const import NOTICE_TYPE
import logging
logger = logging.getLogger("sys_log")


def pub_notice(notice, sender, type=NOTICE_TYPE.NORMAL, on_change_only=False, replace=False, clear=False):
    logger.info(notice)
