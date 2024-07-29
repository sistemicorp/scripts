#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
import threading
from operator import itemgetter


class SharedState(object):
    """ shared state available to every channel
    """

    def __init__(self):
        self.logger = logging.getLogger("SC.{}".format(__name__))
        self.lock = threading.Lock()
        self._shared = {
            "common": {
                # common channel resources
                "rsrc_locks": [],          # list of resource locks, these locks are accessed by
                                           # name, and are presumably common across all channels
                                           # {"name": <name>, "lock": <threading.Lock()> }

            },
            "gui": {

            },

            # drivers are installed during the script initialization, from the script
            # field "channel_hw_driver".  That process creates a list of drivers that are
            # stores here, as a list of dicts, with the format,
            #    {"channel": idx, "type": type, "obj": d}
            # Channel python code can retrieve this list and search for their channel
            # and get the driver object.
            "drivers": [],

            "state": {},

            # "private" channel specific items are put here in format like
            # self._shared[ch_num] = { key: <value>, ... }
        }

        # TODO: maybe publish when items are posted?  then others can subscribe, thus sync events

    def register_teardown_cb(self, callback):
        pass

    def context_store(self, num, info):
        if not self._shared.get(num, False):
            self._shared[num] = {}
        self._shared[num]["context"] = info

    def context_get(self, num):
        return self._shared[num].get("context", None)

    def rsrc_lock_get(self, name):
        """ get/add a new resource to lock... if resource is already created, return existing obj
        - a rsrc entry looks like this,
          { "name": <name>
            "lock": <threading.Lock()>
          }
        - these locks will/can be applied to drivers that are shared resources
        :param name:
        :return: threading.Lock object, the client(s) that can call set/release on it
        """
        with self.lock:
            for r in self._shared["common"]["rsrc_locks"]:
                if r["name"] == name:
                    self.logger.debug("{} already created".format(name))
                    return r["lock"]

            # create the new lock
            _lock = threading.Lock()
            self._shared["common"]["rsrc_locks"].append({"name": name, "lock":_lock})
            self.logger.debug("created {}".format(name))
            return _lock

    def channel_set_kv(self, num, key, value):
        """ setter a key:value to channel area of shared state
        - could be used to talk to other channels
        - send values to self in other suite modules
        :param num: channel number
        :param key:
        :param value:
        """
        with self.lock:
            if not self._shared.get(num, False):
                self._shared[num] = {}
            self._shared[num][key] = value
        self.logger.info("{} {} {}".format(num, key, value))

    def channel_get_kv(self, num, key):
        """ getter
        :param num:
        :param key:
        :return: success, value
        """
        with self.lock:
            if not self._shared.get(num, False):
                self.logger.warn("No entry for channel %d" % num)
                return False, None
            if key not in self._shared[num]:
                self.logger.warn("key %r does not exist" % key)
                return False, None

            return True, self._shared[num][key]

    def add_drivers(self, type, drivers, shared=False):
        """ Add a driver

        The hw driver objects are expected to have an 'id' field, and
        possibly a 'slot' field.  The slot field is used to assign the slot
        of the HW.  IF slot is not present, then the lowest
        id is assigned to channel 0, the next highest to channel 1, etc

        [ {'id': <str>,           # id of the channel, like serial number of something
           'slot': <int>,         " 0,1,2,3, .... slot number
           "version": <VERSION>,  # version of the driver
           "close": False},       # register a callback on closing the channel
           "<foo>": <bar>,        # something that makes your HW work...
        ]
        :param type: Type of hardware (string)
        :param drivers: list of drivers to add
        :param shared: True if driver is shared among all channels
        :return: True on success, False otherwise
        """
        if not isinstance(drivers, list):
            self.logger.error("list required")
            return False

        if len(drivers) == 0:
            self.logger.error("no drivers in list, length zero")
            return False

        has_slot = False
        if drivers[0].get("slot", False): has_slot = True

        with self.lock:
            if not shared:
                if has_slot: drivers_sorted = sorted(drivers, key=itemgetter('slot'))
                else: drivers_sorted = sorted(drivers, key=itemgetter('id'))

                for idx, d in enumerate(drivers_sorted):
                    dd = {"channel": idx, "type": type, "obj": d}
                    self._shared["drivers"].append(dd)
            elif shared:
                for idx, d in enumerate(drivers):
                    dd = {"channel": None, "type": type, "obj": d}
                    self._shared["drivers"].append(dd)

        return True

    def get_drivers(self, channel, type=None):
        """  Gets all the drivers for channel
        :param channel: set to channel # to get drivers for that channel, set to None to
                       get drivers that are shared across all channels
        :param type: type of driver, None for any type
        :return: list of drivers
        """
        drivers = []
        with self.lock:
            for driver in self._shared["drivers"]:
                if driver["channel"] == channel and type in [None, driver["type"]]:
                    drivers.append(driver)

        return drivers

    def get(self):
        """ Get the whole shared state
        :return: self._shared dict
        """
        with self.lock: return self._shared

    def state_set_ch(self, ch, state):
        with self.lock:
            self._shared["state"][ch] = {"state": state}

    def state_get(self, ch=None):
        with self.lock:
            if ch is not None:
                if ch not in self._shared["state"]:
                    # probably the first time thru...
                    self.logger.warning("Ch {} not found in {}".format(ch, self._shared["state"]))
                return self._shared["state"].get(ch, {})
            return self._shared["state"]