#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
from public.prism.api import ResultAPI

class TestItem(object):

    BULLET_TEXT_MAX_LENGTH = 50

    def __init__(self, controller, ch_num, shared_state):
        self.logger = logging.getLogger("SC.{}.{}".format("TestItem", ch_num))
        self.chan = ch_num
        self.con = controller
        self.shared_state = shared_state

        self._record = None
        self.logger.info("DONE")

    # --------------------------------------------------------------------------
    # ------------ Script APIs wrapped by TestItem -----------------------------

    def log_bullet(self, text, ovrwrite_last_line=False):
        if len(text) > self.BULLET_TEXT_MAX_LENGTH:
            self.logger.warning("bullet text max length exceeded, truncating")
            text = text[0:self.BULLET_TEXT_MAX_LENGTH]

        self.con.log_bullet(text, ovrwrite_last_line)

    def input_button(self, buttons, timeout=10):
        """ Create a row of buttons horizontally for user selection
        - each button entry looks like,
             {"value": "one",   "callback":"_TST005_button_handler", ["name": <unique_name>]}
        :param timeout: seconds
        :param buttons: list of button dicts
        :return {'success': True/False, 'button': <#>, ['err': <msg>]}
                where # is the index of the button selected by user
        """
        self.logger.info(buttons)
        button_idx = int(input("Press Button (0-{}):".format(len(buttons) - 1)))
        if not (0 <= button_idx < len(buttons)):
            # fake a timeout if the range is wrong... a wrong index is not possible in the GUI
            return {'success': False, 'button': None, 'err': "Timeout"}
        return {'success': True, 'button': button_idx, 'err': None}

    def input_textbox(self, title, placeholder="", timeout=10):
        """ Get text input
        :param title:
        :param placeholder:
        :param timeout:
        :return: {'success': True/False, 'textbox': <string>, ['err': <msg>]}
        """
        tb = {"title": title, "placeholder": placeholder}
        self.logger.debug(tb)
        usr_input = input("Enter({}):".format(placeholder))
        return {'success': True, 'textbox': usr_input, 'err': None}
        # a failure looks like this...
        #return {'success': False, 'textbox': None, 'err': "Timeout"}

    def add_key(self, key, value, slot=None):
        """ Add keys to the suite test record
        - keys are things that the backend database would create keys on
        :param key:
        :param value:
        """
        self._record.add_key(key, value, slot)

    def item_start(self):
        return self.con.item_start()

    def item_end(self, item_result_state=ResultAPI.RECORD_RESULT_PASS, _next=None):
        self.con.item_end(item_result_state, _next)

    def shared_set_kv(self, key, value):
        self.shared_state.channel_set_kv(self.chan, key, value)

    def shared_get_kv(self, key):
        return self.shared_state.channel_get_kv(self.chan, key)

    def shared_lock(self, name):
        return self.shared_state.rsrc_lock_get(name)

    def shared_get_context(self):
        return self.shared_state.context_get(self.chan)

    def shared_get_drivers(self):
        return self.shared_state.get_drivers(self.chan)


