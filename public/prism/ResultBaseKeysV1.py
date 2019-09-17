#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import json
import copy
import logging
from core.resultBaseClass import ResultBaseClass
from public.prism.api import ResultAPI


class ResultBaseKeysV1(ResultBaseClass):
    """ ResultBaseKeysV1

  API:
  - see each function for API notes, here is a summary

    "add_key"
    - are meant to hold things like serial numbers, password keys, etc from the product
    - there are 4 key slots that can be used
    - are index in the backend SQL DB
    - The DB record holds key0, key1, key2, .. up to key{}.format(MAX_KEYS)
      The idea is that these keys would be mapped for specific purposes, and thus
      these key#s can serve arbitrary purposes.
    - The final dict will look like this:
       {
         "key0": "<keyName>:<value>",
         "key1": "<keyName>:<value>",
         ...
       }
       - because key# is general purpose, having keyName indicates its usage
       - each key# is an indexed column in the back end database

    "get_keys"
    - getter

    "get_key_num_slots"
    - get maximum number of key slots available (2)
    - this number will never be decreased in future versions

    "blob"
    - adds a blob of data to the backend database
    - the blob must be of a type, and pre-described dict format
    - see ResultAPI.BLOB_* types
    - blob is NOT a postgres JSONB type, these are just JSON

    "measurement"
    - add a measurement to the backend database

    "setCustomJSONB"
    - adds a postgres JSONB object to the database, which can be indexed
    - effectively allows any fields to be posted in the backend DB
    - this object is global scope from a test item pov, there is only ONE of these for all test items

    "getCustomJSONB"
    - getter
    """

    def __init__(self, chan_num, operator="UNKNOWN", script_filename="UNKNOWN"):
        super().__init__(chan_num, operator, script_filename)
        self.logger = logging.getLogger("SC.{}.{}".format(__class__.__name__, chan_num))
        self._record["meta"]["processor"] = __class__.__name__
        self._record["keys"] = {}
        self.logger.info("DONE")

    def add_key(self, key, value, slot=None):
        """ Adds a key value pair into a key# "slot"

        :param key:
        :param value:
        :param slot: if not specified, the next available slot is used
        :return: True if succeeded, False otherwise
        """
        if slot is None:
            num_keys = len(self._record["keys"])
            if num_keys >= self.MAX_KEYS:
                self.logger.error("recorded has exceeded maximum keys")
                return False

            # find the next empty slot (key#) and insert the key:value
            for i in range(self.MAX_KEYS):
                if not "key{}".format(i) in self._record["keys"]: break
            self._record["keys"]["key{}".format(i)] = key + ":" + str(value)

        else:
            if slot >= self.MAX_KEYS:
                self.logger.error("recorded has exceeded maximum keys")
                return False
            self._record["keys"]["key{}".format(slot)] = key + ":" + str(value)

        return True

    def get_keys(self):
        """ Get the existing Key dict
        - this is almost like a shared state cache, one test item can set a key, and
          another item read the key

        :return: current key dict
        """
        return self._record["keys"]

    def get_key_num_slots(self):
        return self.MAX_KEYS

    def blob(self, name, blob):
        """ store a data blob
        - blobs are associated with the test item
        - see example script programs

        :param name: name of the blob, must be unique per test item
        :param blob: a dict of the blob data, see ResultAPI.BLOB_
        :return: True|False, None|message
                 True - success, False - failed, msg is failure message
        """
        if not isinstance(blob, dict):
            msg = "blob must be of type dict"
            self.logger.error(msg)
            return False, msg

        if not blob["type"] in ResultAPI.BLOB_TYPES:
            msg = "Unknown blob type {} not in {}".format(blob["type"], ResultAPI.BLOB_TYPES)
            self.logger.error(msg)
            return False, msg

        lname = "{}.{}".format(self._item["name"], name)
        # check for duplicate name
        for b in self._item["blobs"]:
            if b["name"] == lname:
                msg = "Duplicate blob name {}".format(b["name"])
                self.logger.error(msg)
                return False, msg

        d = {"name": lname}
        d.update(blob)

        try:  # validate this can be turned into JSON
            _ = json.dumps(d)
        except Exception as e:
            self.logger.error(e)
            return False, e

        self._item["blobs"].append(d)
        self.logger.info("blob {} saved".format(d["name"]))
        return True, None

    def measurement(self, name, value, unit=ResultAPI.UNIT_NONE, min=None, max=None):
        """ Check and store a measurement
        - performs a check on the value, returning one of ResultAPI.RECORD_RESULT_*
        - all values are stored as strings in the dB, converted here

        :param name: must be unique per test item
        :param min:
        :param max:
        :param value:
        :param unit: one of self.UNIT_*
        :return: success, result, msg
            success: True: measurement accepted
                     False: a error occurred
            result: one of ResultAPI.RECORD_RESULT_*
                    (can be passed into self.item_end(), see examples)
            msg: if not success, this is error message
                 if success, this is human friendly message of the measurment
        """
        if name is None:
            lname = "{}".format(self._item["name"])
        else:
            lname = "{}.{}".format(self._item["name"], name)

        # check for duplicate name
        for m in self._item["measurements"]:
            if m["name"] == lname:
                msg = "Duplicate measurement name {}".format(m["name"])
                self.logger.error(msg)
                return False, ResultAPI.RECORD_RESULT_UNKNOWN, msg

        if min is not None and not isinstance(min, (int, float)):
            msg = "min must be of type int, float, got {}".format(type(min))
            self.logger.error(msg)
            return False, ResultAPI.RECORD_RESULT_UNKNOWN, msg

        if max is not None and not isinstance(max, (int, float)):
            msg = "max must be of type int, float, got {}".format(type(max))
            self.logger.error(msg)
            return False, ResultAPI.RECORD_RESULT_UNKNOWN, msg

        if unit not in ResultAPI.UNIT_ALL:
            msg = "Unknown unit {}, must be one of {}".format(unit, ResultAPI.UNIT_ALL)
            self.logger.error(msg)
            return False, ResultAPI.RECORD_RESULT_UNKNOWN, msg

        if not isinstance(value, (int, float, bool, str)):
            msg = "Unsupported value type {}".format(type(value))
            self.logger.error(msg)
            return False, ResultAPI.RECORD_RESULT_UNKNOWN, msg

        self.logger.info("{}: {} <= {} <= {} {} ??".format(name, min, value, max, unit))

        _pass = ResultAPI.RECORD_RESULT_UNKNOWN

        d = {"name": lname, "unit": unit}

        if isinstance(min, (int, float)) and isinstance(max, (int, float)) and isinstance(value, (int, float)):
            if min <= value <= max: _pass = ResultAPI.RECORD_RESULT_PASS
            else: _pass = ResultAPI.RECORD_RESULT_FAIL
            d["min"] = "{:32.16}".format(str(float(min))).rstrip()
            d["max"] = "{:32.16}".format(str(float(max))).rstrip()
            d["value"] = "{:64.16}".format(str(float(value))).rstrip()
            _bullet = "{}: {} <= {} <= {} {} :: {}".format(name, d["min"], d["value"], d["max"], unit, _pass)
            self.logger.info(_bullet)

        elif min is None and max is None and isinstance(value, (int, float, str)):
            _pass = ResultAPI.RECORD_RESULT_PASS
            d["min"] = None
            d["max"] = None
            if unit == ResultAPI.UNIT_INT:
                d["value"] = "{}".format(value)
            elif unit == ResultAPI.UNIT_FLOAT:
                d["value"] = "{}".format(value)
            elif unit == ResultAPI.UNIT_STRING:
                d["value"] = "{}".format(value)
            elif isinstance(value, (int, )):
                d["value"] = "{}".format(int(value))
            elif isinstance(value, (float, )):
                d["value"] = "{:64.16}".format(str(float(value))).rstrip()
            elif isinstance(value, str):
                d["value"] = "{:64}".format(value).rstrip()
            _bullet = "{}: {} {} :: {}".format(name, d["value"], unit, _pass)
            self.logger.info(_bullet)

        elif min is None and max is None and isinstance(value, bool):
            _pass = ResultAPI.RECORD_RESULT_PASS
            if not value: _pass = ResultAPI.RECORD_RESULT_FAIL
            d["value"] = value
            _bullet = "{}: {} {} :: {}".format(name, d["value"], unit, _pass)
            self.logger.info(_bullet)

        else:
            _pass = ResultAPI.RECORD_RESULT_INTERNAL_ERROR
            _bullet = "{}: {} <= {} <= {} {} ??".format(name, min, value, max, unit)
            self.logger.error(_bullet)
            return False, _pass, _bullet

        d["result"] = _pass
        self._item["measurements"].append(d)
        self.logger.info(d)
        return True, _pass, _bullet

    def setCustomJSONB(self, jsonb_dict):
        """ Set custom DB fields via postgres JSONB object

        - not an expert, but seems postgres indexes JSONB keys, so if you need
          fast lookup of various things, then use this to create a dict with the
          keys (and value) you need to search fast later
        - probably best if you keep this object as flat as possible, for example

          { "key0": value0,
            "key1": value1,
            ...
          }

        - best way to use Custom JSONB:
            my_jsonb = {"serialNum": 123456789}
            jsonb = ctx.record.getCustomJSONB()
            jsonb.update(my_jsonb)
            success, msg = ctx.record.setCustomJSONB(jsonb)
            # error handle here...

        :param jsonb_dict:
        :return: success, msg
            success: True, False on error
            msg: if not success, an error message, otherwise None
        """
        if not isinstance(jsonb_dict, dict):
            msg = "jsonb_dict must be of type dict"
            self.logger.error(msg)
            return False, msg

        try:  # validate this can be turned into JSON
            _ = json.dumps(jsonb_dict)
        except Exception as e:
            self.logger.error(e)
            return False, e

        self._record["jsonb"] = copy.deepcopy(jsonb_dict)
        self.logger.info("jsonb_dict saved")
        return True, None

    def getCustomJSONB(self):
        return copy.deepcopy(self._record["jsonb"])
