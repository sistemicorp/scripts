#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import os
import time
import logging
import datetime
import platform
import json
import uuid
from public.prism.api import ResultAPI


class ResultBaseClass(object):
    """
    Base Result Record for the whole test suite

    - private and internal APIs begin with "_", do not call these
    - public APIs are listed last

    """
    EPOCH_DECIMAL_PLACES = 2
    MAX_KEYS = 2  # !! must match fields in DB backend - can't change arbitrarily
                  # !! only increase in future versions

    def __init__(self, chan_num, operator="UNKNOWN", script_filename=None):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, chan_num))

        self._record = {    ## The result json record for the suite
            "meta": { # stuff that framework populates
                      "channel": chan_num,
                      "result": ResultAPI.RECORD_RESULT_UNKNOWN,
                      "processor": __class__.__name__.lower(),  #  processor is tied to db name, which must be lower case
                      "operator": operator,
                      "ip": "127.0.0.1",
                      "script": os.path.normpath(script_filename).replace("\\", "/"),
                    },
            "info": {},      # stuff customer populates
            "config": {},    # copied from the script input
            "items": [],     # list of results, see Result class
            "errors": [],    # list of errors, for crash logs
            "jsonb": {},     # custom JSONB dict
            "html_summary": None,
        }

        self._item = {}
        self.logger.info("DONE")

    def record_add_error(self, msg):
        if isinstance(msg, list):
            for m in msg:
                self._record["errors"].append(m)
        else:
            self._record["errors"].append(msg)

    def record_item_create(self, name):
        self._item = {
            "name": name,
            "result": ResultAPI.RECORD_RESULT_UNKNOWN,
            "timestamp_start": round(time.time(), self.EPOCH_DECIMAL_PLACES),
            "timestamp_end": 0,
            "measurements": [],
            "blobs": [],
            "fail_msg": {}  # like {"fid": "TST000-0", "msg": "Component R1"}
        }

    def record_meta_set_result(self, _result):
        self._record["meta"]["result"] = _result

    def record_meta_get_result(self):
        return self._record["meta"]["result"]

    def record_meta_get_duration(self):
        end = datetime.datetime.strptime(self._record["meta"]["end"], "%Y-%m-%dT%H:%M:%S.%f")
        start = datetime.datetime.strptime(self._record["meta"]["start"], "%Y-%m-%dT%H:%M:%S.%f")
        return (end - start).total_seconds()

    def record_test_set_result(self, _result):
        """
        :param _result: one of ResultAPI.RECORD_RESULT_*
        :return:
        """
        self._item["result"] = _result

        if self.record_meta_get_result() == ResultAPI.RECORD_RESULT_UNKNOWN:
            self.record_meta_set_result(_result)
        elif self.record_meta_get_result() == ResultAPI.RECORD_RESULT_PASS:
            self.record_meta_set_result(_result)
        elif self.record_meta_get_result() == ResultAPI.RECORD_RESULT_FAIL:
            pass
        else:
            self.record_meta_set_result(_result)

    def record_test_get_result(self):
        return self._item["result"]

    def record_test_get_duration(self):
        return self._item["timestamp_end"] - self._item["timestamp_start"]

    def record_item_end(self):
        self._item["timestamp_end"] = round(time.time(), self.EPOCH_DECIMAL_PLACES)
        self._record["items"].append(self._item)

    def record_items_get(self):
        return self._record["items"]

    def fail_msg(self, fail_msg):
        if isinstance(fail_msg, dict):
            self._item["fail_msg"] = fail_msg
            self.logger.info(fail_msg)
        else:
            self.logger.error("expected dict for fail_msg")

    def record_item_get(self): return self._item

    def __meta_add(self, m):
        self._record["meta"] = {**self._record["meta"], **m}

    def record_record_meta_init(self):
        _meta = {
            "version": "TBD-framework version",
            "start": datetime.datetime.utcnow().isoformat(),
            "end": "",
            "hostname": [i for i in platform.uname()],
            "result": ResultAPI.RECORD_RESULT_UNKNOWN,
        }
        self.__meta_add(_meta)

    def record_record_meta_fini(self, state=None):
        if state is None:
            _state = ResultAPI.RECORD_RESULT_PASS
            for test in self._record["items"]:
                # TODO: it might be easier to say if NOT in [PASS, SKIP]
                if test["result"] in [ResultAPI.RECORD_RESULT_FAIL,
                                      ResultAPI.RECORD_RESULT_TIMEOUT,
                                      ResultAPI.RECORD_RESULT_UNKNOWN,
                                      ResultAPI.RECORD_RESULT_INTERNAL_ERROR,
                                      ResultAPI.RECORD_RESULT_INCOMPLETE]:
                    _state = ResultAPI.RECORD_RESULT_FAIL
        else:
            _state = state
        _meta = {
            "end": datetime.datetime.utcnow().isoformat(),
            "result": _state,
        }
        self.__meta_add(_meta)

    def record_record_meta_set(self, _meta):
        self.__meta_add(_meta)

    def record_info_set(self, _info_dict):
        self._record["info"] = {**self._record["info"], **_info_dict}

    def record_record_html_summary(self, summary):
        """ Add View Log Summary to the record.  This used to be in HTML format, but it
        is no longer, but function name has not been updated.

        the log is in json format string, with lines like this, list of dicts,
            [ { "item": item, "log": log, "rowcolor": color, "fs": fs}, ... ]

        :param summary: a string json, list of dicts
        """
        self._record["html_summary"] = summary

    def record_publish(self, type="result"):
        ruid = str(uuid.uuid4())
        _file = type + "_" + ruid + ".json"
        self._record["meta"]["ruid"] = ruid

        # NOTE: this new 'd' becomes the record saved in the result json file!
        d = {"result": self._record,
             "file": _file,
             "processor": self._record["meta"]["processor"],
             "from": "{}.record_publish".format(__class__.__name__)}

        if "from" in d: d.pop("from")  # remove debugging key
        if "type" in d: d.pop("type")  # remove event key

        with open(_file, 'w') as fp:
            json.dump(d, fp, indent=2)
        self.logger.info("Result: {}, Created: {}".format(self._record["meta"]["result"], _file))

        return _file

    def __repr__(self): return str(self._record)
