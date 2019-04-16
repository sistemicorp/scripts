#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

https://stackoverflow.com/questions/2682745/how-do-i-create-a-constant-in-python
"""

class MetaConst(type):
    def __getattr__(cls, key):
        return cls[key]

    def __setattr__(cls, key, value):
        raise TypeError


class Const(object, metaclass=MetaConst):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        raise TypeError


class APP(Const):

    NOTICE_NRM = "NORMAL"
    NOTICE_ERR = "ERROR"
    NOTICE_WRN = "WARN"


class CHANNEL(Const):

    STATE_UNKNOWN = "STATE_UNKNOWN"
    STATE_READY = "STATE_READY"
    STATE_RUNNING = "STATE_RUNNING"
    STATE_STEPPING = "STATE_STEPPING"
    STATE_PAUSE = "STATE_PAUSE"
    STATE_ENDING = "STATE_ENDING"
    STATE_DONE = "STATE_DONE"
    STATE_INTERNAL_CRASH = "STATE_CRASH"  # TODO:

    EVENT_TYPE_INIT = "EVENT_TYPE_INIT"
    EVENT_TYPE_START = "EVENT_TYPE_START"
    EVENT_TYPE_RUN = "EVENT_TYPE_RUN"
    EVENT_TYPE_STEP = "EVENT_TYPE_STEP"
    EVENT_TYPE_RUN_ITEM_DONE = "EVENT_TYPE_RUN_ITEM_DONE"
    EVENT_TYPE_SKIP = "EVENT_TYPE_SKIP"
    EVENT_TYPE_REWIND = "EVENT_TYPE_REWIND"
    EVENT_TYPE_PAUSE = "EVENT_TYPE_PAUSE"
    EVENT_TYPE_ENDING = "EVENT_TYPE_ENDING"
    EVENT_TYPE_DONE = "EVENT_TYPE_DONE"
    EVENT_TYPE_CRASH = "EVENT_TYPE_CRASH"

    EVENT_THREAD_STOP = "EVENT_THREAD_STOP"

    GUI_TYPE_RESPONSE = "GUI_TYPE_RESPONSE"


class PUB(Const):

    SHUTDOWN         = "Shutdown"

    CHANNELS         = "ch_root"

    CHANNELS_SCRIPT  = CHANNELS + ".script"  # a new script is loaded

    FRAME            = "Frame"
    FRAME_STATUSLINE_RESULT_SERVER = FRAME + ".result_server"
    FRAME_SYSTEM_NOTICE = FRAME + ".system_notice"                 # {"notice": <msg>, ["toolbar": T/F,] "from": [msg]}
    FRAME_SYSTEM_NOTICE_DIALOG = FRAME + ".system_notice_dialog"
    FRAME_SYSTEM_NOTICE_TOOLBAREN = FRAME + ".toolbar_enable"

    CHANNELS_PLAY    = CHANNELS + ".play"
    CHANNELS_STEP    = CHANNELS + ".step"
    CHANNELS_STOP    = CHANNELS + ".stop"
    CHANNELS_PAUSE   = CHANNELS + ".pause"
    CHANNELS_FF      = CHANNELS + ".ff"      # skip ahead one
    CHANNELS_REWIND  = CHANNELS + ".rewind"  # go back one

    CHANNEL_STATE    = CHANNELS + ".state" # from ChanCon
                           # {"ch": #, "state": <state>, "from": 'ChanCon'}

    CHANNEL_RESULT       = CHANNELS + ".result" # from ChanCon
    CHANNEL_RESULT_CRASH = CHANNELS + ".result_crash"  # from ChanCon  TODO
    CHANNEL_VIEW_RESULT  = CHANNELS + ".view_result"

    CHANNEL_0         = CHANNELS + ".0"
    CHANNEL_0_BUTTON  = CHANNEL_0 + ".button" # from Channel gui to ChannelController, test_suite_class
    CHANNEL_0_TEXTBOX = CHANNEL_0 + ".textbox" # from Channel gui to ChannelController, test_suite_class
    CHANNEL_0_TOOL    = CHANNEL_0 + ".tool"   # from Channel gui to ChannelController, test_suite_class
    CHANNEL_0_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_1         = CHANNELS + ".1"
    CHANNEL_1_BUTTON  = CHANNEL_1 + ".button"
    CHANNEL_1_TEXTBOX = CHANNEL_1 + ".textbox"
    CHANNEL_1_TOOL    = CHANNEL_1 + ".tool"
    CHANNEL_1_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_2         = CHANNELS + ".2"
    CHANNEL_2_BUTTON  = CHANNEL_2 + ".button"
    CHANNEL_2_TEXTBOX = CHANNEL_2 + ".textbox"
    CHANNEL_2_TOOL    = CHANNEL_2 + ".tool"
    CHANNEL_2_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_3         = CHANNELS + ".3"
    CHANNEL_3_BUTTON  = CHANNEL_3 + ".button"
    CHANNEL_3_TEXTBOX = CHANNEL_3 + ".textbox"
    CHANNEL_3_TOOL    = CHANNEL_3 + ".tool"
    CHANNEL_3_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_4         = CHANNELS + ".4"
    CHANNEL_4_BUTTON  = CHANNEL_4 + ".button"
    CHANNEL_4_TEXTBOX = CHANNEL_4 + ".textbox"
    CHANNEL_4_TOOL    = CHANNEL_4 + ".tool"
    CHANNEL_4_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_5         = CHANNELS + ".5"
    CHANNEL_5_BUTTON  = CHANNEL_5 + ".button"
    CHANNEL_5_TEXTBOX = CHANNEL_5 + ".textbox"
    CHANNEL_5_TOOL    = CHANNEL_5 + ".tool"
    CHANNEL_5_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_6         = CHANNELS + ".6"
    CHANNEL_6_BUTTON  = CHANNEL_6 + ".button"
    CHANNEL_6_TEXTBOX = CHANNEL_6 + ".textbox"
    CHANNEL_6_TOOL    = CHANNEL_6 + ".tool"
    CHANNEL_6_PLAY    = CHANNEL_0 + ".play"   # play this channel

    CHANNEL_7         = CHANNELS + ".7"
    CHANNEL_7_BUTTON  = CHANNEL_7 + ".button"
    CHANNEL_7_TEXTBOX = CHANNEL_7 + ".textbox"
    CHANNEL_7_TOOL    = CHANNEL_7 + ".tool"
    CHANNEL_7_PLAY    = CHANNEL_0 + ".play"   # play this channel

    @staticmethod
    def get_channel_num_button(num):
        return getattr(PUB, "CHANNEL_{}_BUTTON".format(num))

    @staticmethod
    def get_channel_num_textbox(num):
        return getattr(PUB, "CHANNEL_{}_TEXTBOX".format(num))

    @staticmethod
    def get_channel_num_play(num):
        return getattr(PUB, "CHANNEL_{}_PLAY".format(num))
