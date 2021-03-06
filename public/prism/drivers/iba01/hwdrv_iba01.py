#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

This driver can be used for PyBoard only, OR can be used for IBA01,
OR can be used as a template for any design that embeds a PyBoard.

"""
import os
import logging
import threading
import time
import serial

from pubsub import pub
from public.prism.drivers.iba01.list_serial import serial_ports
from public.prism.drivers.iba01.IBA01 import IBA01
from public.prism.api import ResultAPI

from core.const import PUB, CHANNEL
from core.sys_log import pub_notice


class upybrdPlayPub(threading.Thread):
    """ Creates a thread per channel that will poll the switch
    on the upybrd, and if it is pressed, will pub the PLAY msg to
    start testing on that port.

    """
    POLL_TIMER_SEC = 1
    LED_RED    = 1
    LED_GREEN  = 2
    LED_YELLOW = 3
    LED_BLUE   = 4

    def __init__(self, ch, drv, shared_state):
        super(upybrdPlayPub, self).__init__()
        self._stop_event = threading.Event()
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, ch))

        self.ch = ch
        self.pyb_port = drv["obj"]["port"]
        self.pyb = drv["obj"]["pyb"]
        self.ch_state = CHANNEL.STATE_UNKNOWN
        self.ch_result = ResultAPI.RECORD_RESULT_UNKNOWN
        self.ch_pub = PUB.get_channel_num_play(ch)
        self.open_fixture = False  # assume fixture is closed
        self.shared_state = shared_state

        pub.subscribe(self.onSHUTDOWN,            PUB.SHUTDOWN)
        pub.subscribe(self.onCHANNEL_STATE,       PUB.CHANNEL_STATE)
        pub.subscribe(self.onCHANNEL_VIEW_RESULT, PUB.CHANNEL_VIEW_RESULT)

        self.start()

    def _unsubscribe(self):
        pub.unsubscribe(self.onSHUTDOWN,            PUB.SHUTDOWN)
        pub.unsubscribe(self.onCHANNEL_STATE,       PUB.CHANNEL_STATE)
        pub.unsubscribe(self.onCHANNEL_VIEW_RESULT, PUB.CHANNEL_VIEW_RESULT)

    def shutdown(self):
        self._unsubscribe()
        self._stop_event.set()
        self.join()

    def close(self):
        self.shutdown()

    def onSHUTDOWN(self, item_dict, topic=pub.AUTO_TOPIC):
        self.logger.info("{} - {}".format(topic.getName(), item_dict))
        self.shutdown()

    def onCHANNEL_STATE(self, item_dict, topic=pub.AUTO_TOPIC):
        # {"ch": #, "state": <state>, "from": 'ChanCon'}
        if item_dict["ch"] != self.ch: return
        self.logger.info("%r - %r" % (topic.getName(), item_dict))
        self.ch_state = item_dict["state"]

        # TODO: Note that public does NOT include the channel state, from const.CHANNEL.
        #       But, based on channel state, might be good to add LED indication...
        #       Either a copy of, or the STATE_* assignments would need to move to ResultAPI.
        #       (and copy is never a good idea)

    def onCHANNEL_VIEW_RESULT(self, item_dict, topic=pub.AUTO_TOPIC):
        if item_dict["ch"] != self.ch: return
        self.logger.info("%r - %r" % (topic.getName(), item_dict))
        # item_dict -> {'ch': 0, 'result': 'PASS', 'from': 'ChanCon._script_fini.ch0'}
        self.ch_result = item_dict['result']

        if self.ch_result == ResultAPI.RECORD_RESULT_PASS:
            set = [(self.LED_GREEN, True), (self.LED_RED, False), (self.LED_YELLOW, False)]
        elif self.ch_result == ResultAPI.RECORD_RESULT_FAIL:
            set = [(self.LED_GREEN, False), (self.LED_RED, True), (self.LED_YELLOW, False)]
        else:
            set = [(self.LED_GREEN, False), (self.LED_RED, False), (self.LED_YELLOW, True)]

        success, result = self.pyb.led(set)
        if not success: self.logger.error("failed to set LED")

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):

        self.logger.info("!!! run loop started !!!")

        pub_play = False
        while not self.stopped():
            time.sleep(self.POLL_TIMER_SEC)

            # this is a hack to deal with shutting down, the serial port
            # is closed and this process is still running...
            try:
                success, result = self.pyb.jig_closed_detect()
                self.logger.debug("{}, {}".format(success, result))

            except serial.serialutil.SerialException:
                continue

            except Exception as e:
                self.logger.error(e)

            if success and len(result):
                current_state = result["value"]["value"]
                # only if the fixture was in the previously opened state, then we play
                # in other words, once lid is closed, it must be opened again to trigger play
                if self.open_fixture and current_state == "CLOSED":
                    pub_play = True
                    self.open_fixture = False
                    self.logger.info("Channel {} PLAY".format(self.ch))

                elif current_state == "OPEN":
                    self.open_fixture = True

            else:
                self.logger.error("self.pyb.server_cmd: {}".format(result))
                pub_play = False

            if pub_play:
                self.logger.info("open_fixture: {}, play: {}".format(self.open_fixture, pub_play))
                pub_play = False
                d = {"channels": [self.ch], "from": "{}.{}".format(__class__.__name__, self.ch)}
                pub.sendMessage(self.ch_pub, item_dict=d)

        self.logger.info("!!! run loop stopped !!!")


class HWDriver(object):
    """ Determine MicroPyBoards attached to the system, and report them to the system shared state.
    """
    SFN = os.path.basename(__file__)

    DRIVER_TYPE = "IBA01"
    MICROPYTHON_FIRMWARE_RELEASE = "1.11.0"  # from os.uname() on pyboard
    IBA01_SERVER_VERSION = "0.2"

    def __init__(self, shared_state):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, self.SFN))
        self.logger.info("Start")
        self.shared_state = shared_state
        self.pybs = []
        self._num_chan = 0

    def discover_channels(self):
        """ determine the number of channels, and populate hw drivers into shared state

        shared_state: a list,
            self.shared_state.add_drivers(DRV_TYPE, [ {}, {}, ... ], shared=True/False)

        [ {'id': i,                 # slot id of the channel (see Note 1)
           "version": <VERSION>,    # version of the driver
           "close": PyBoard.close}, # register a callback on closing the channel
           "pyb": IBA01(),          # something that makes your HW work...
           "port": serial port
           "unique_id": unique_id   # cache this here so that it doesn't need to be retrieved for every test
        ]

        Note:
        1) The hw driver objects are expected to have an 'id' field, the lowest
        id is assigned to channel 0, the next highest to channel 1, etc

        :return: >0 number of channels,
                  0 does not indicate num channels, like a shared hardware driver
                 <0 error
        """
        self.pybs.clear()

        sender = "{}.{}".format(self.SFN, __class__.__name__)

        port_candidates = serial_ports()
        self.logger.info("Serial Ports to look for PyBoard {}".format(port_candidates))

        for port in port_candidates:
            if "ttyACM" not in port:
                self.logger.info("skipping port {}...".format(port))
                continue

            _pyb = { "port": port}
            self.logger.info("Trying pyboard at {}...".format(port))

            _pyb['pyb'] = pyb = IBA01(port, loggerIn=logging.getLogger("IBA01.try"))
            success, result = pyb.start_server()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("No pyboard at {}".format(port))
                continue

            success, result = pyb.unique_id()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("pyboard {} unique_id -> {}".format(port, result))
                continue
            _pyb["unique_id"] = result["value"]["value"]

            success, result = pyb.slot()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("pyboard {} slot -> {}".format(port, result))
                continue
            _pyb["id"] = result["value"]["value"]

            success, result = pyb.version()
            self.logger.info("{}, {}".format(success, result))
            if not success:
                self.logger.warning("pyboard {} uname -> {}".format(port, result))
                continue
            _pyb["uname"] = result["value"]["uname"]
            release = result["value"]["uname"].get("release", None)
            version = result["value"]["version"]

            # confirm the release
            if release != self.MICROPYTHON_FIRMWARE_RELEASE:
                self.logger.error("pyboard {}, slot {} -> Unsupported release {} (expecting {})".format(
                        _pyb["id"], _pyb["slot"], release, self.MICROPYTHON_FIRMWARE_RELEASE))
                msg = "HWDriver ERR: PyBoard slot {} FW release not supported".format(_pyb["slot"])
                pub_notice(msg, type=PUB.NOTICES_ERROR, sender=sender)
                continue

            # confirm the server version
            if version != self.IBA01_SERVER_VERSION:
                self.logger.error("pyboard {}, slot {} -> Unsupported version {} (expecting {})".format(
                        _pyb["id"], _pyb["slot"], version, self.IBA01_SERVER_VERSION))
                msg = "HWDriver ERR: PyBoard slot {} IBA01_SERVER_VERSION not supported".format(_pyb["slot"])
                pub_notice(msg, type=PUB.NOTICES_ERROR, sender=sender)
                continue
            _pyb["version"] = version

            # close, or else problems trying to re-open
            _pyb["close"] = pyb.close

            self.pybs.append(_pyb)
            msg = "HWDriver:{}: {}".format(self.SFN, _pyb)
            self.logger.info(msg)
            pub_notice(msg, sender=sender)

        self._num_chan = len(self.pybs)
        self.shared_state.add_drivers(self.DRIVER_TYPE, self.pybs, shared=False)

        pub_notice("HWDriver:{}: Found {}!".format(self.SFN, self._num_chan), sender=sender)
        self.logger.info("Done: {} channels".format(self._num_chan))
        return self._num_chan

    def close(self):
        self.logger.info("TBD?")

    def num_channels(self):
        return self._num_chan

    def init_play_pub(self):
        """ Function to instantiate a class/thread to trigger PLAY of script
        - this is called right after discover_channels
        """
        self.logger.info("Creating...")

        # Note that channels are mapped to 'id' in ascending order, which is done
        # by self.shared_state.add_drivers(), so to get the order right, we need to
        # get the drivers from self.shared_state.get_drivers()
        for ch in range(self._num_chan):
            drivers = self.shared_state.get_drivers(ch, type=self.DRIVER_TYPE)
            # there should only be one driver of our type!
            # TODO: move this check to shared_state
            if len(drivers) > 1:
                self.logger.error("Unexpected number of drivers: {}".format(drivers))
                continue

            self.logger.info("Adding 'play' support on channel {}".format(ch))
            play_pub = upybrdPlayPub(ch, drivers[0], self.shared_state)
            d = {"id": ch, "obj": play_pub, "close": play_pub.close}
            self.shared_state.add_drivers("upybrdPlayPub", [d])
