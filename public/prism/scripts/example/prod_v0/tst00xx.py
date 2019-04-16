#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI
import time
import random
import string
import copy

# file and class name must match
class tst00xx(TestItem):

    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("SC.{}.{}".format(__name__, self.chan))

        # ------------------------------------------------------------------------
        # API Reference:
        #
        # from prod_0.scr:
        #         {"id": "TST000_Meas",  "enable": true, "args": {"min": 0, "max": 10},
        #                                "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
        #                                          {"fid": "TST000-1", "msg": "Component banana R1"}] },
        #
        # ctx = self.item_start()  # always first line of test
        #  - use ctx (context) to extract information to drive the test program (see above)
        #  - ctx (context) is a namespace of content from the test script
        #  - ctx.item = {"id": "TST000", "enable": True,  "args": {"min": 0, "max": 10}}
        #  - ctx.item.args = {"min": 0, "max": 10}
        #  - ctx.item.args.max = 10
        #  - ctx.options = { "fail_fast": False }
        #  - ctx.options.fail_fast = False
        #
        #  - record functions
        #    - ctx.record.measurement(name, value, unit, min=None, max=None)
        #      - name: name of the measurement, should be unique per test item
        #      - unit: from ResultAPI.UNIT_*
        #    - result extensions
        #      - the result base class can be extended, as it has in this example
        #      - class ResultBaseKeysV1(ResultBaseClass)
        #      - two functions were added, and used in this example,
        #        - add_key(key, value, slot=None)
        #        - get_keys()
        #
        # self.chan  # this channel
        #
        # self.item_end([result[s]]) # always last line of test
        #  - result is one of ResultAPI.RECORD_* constants
        #  - result may be a list or a single instance
        #  - called without arguments, the result is ResultAPI.RECORD_RESULT_PASS
        #
        # Usage Reference
        #
        # 1) Test Item Timeout
        #    - every test time is guarded by a timeout which has a default of ResultAPI.TESTITEM_TIMEOUT Sec.
        #    - this value can be overridden by adding '"timeout": <value>' to the test item in the script
        #    - if the timeout expires, it is considered a Fail, even if it is
        #      on a user input item.  The test script will fail.
        #

    def TST0xxSETUP(self):
        ctx = self.item_start()  # always first line of test
        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

        self.item_end()  # always last line of test

    def TST0xxTRDN(self):
        ctx = self.item_start()  # always first line of test
        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)
        self.item_end()  # always last line of test

    def TST000_Meas(self):
        """ Measurement example, with multiple failure messages
        - example of taking multiple measurements, and sending as a list of results
        - if any test fails, this test item fails

            {"id": "TST000_Meas",    "enable": true, "args": {"min": 0, "max": 10},
                                     "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                               {"fid": "TST000-1", "msg": "Component banana R1"}] },
        """
        ctx = self.item_start()   # always first line of test

        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

        FAIL_APPLE   = 0  # indexes into the "fail" list, just for code readability
        FAIL_BANANNA = 1

        measurement_results = []  # list for all the coming measurements...

        # Apples measurement...
        success, _result, _bullet = ctx.record.measurement("apples",
                                                           random.randint(0, 10),
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.args.min,
                                                           ctx.item.args.max)
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        # if failed, there is a msg in script to attach to the record, for repair purposes
        if _result == ResultAPI.RECORD_RESULT_FAIL:
            msg = ctx.item.fail[FAIL_APPLE]
            ctx.record.fail_msg(msg)

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        # Bananas measurement...
        success, _result, _bullet = ctx.record.measurement("bananas",
                                                           random.randint(0, 10),
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.args.min,
                                                           ctx.item.args.max)
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        # if failed, there is a msg in script to attach to the record, for repair purposes
        if _result == ResultAPI.RECORD_RESULT_FAIL:
            msg = ctx.item.fail[FAIL_BANANNA]
            ctx.record.fail_msg(msg)

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        # Note that we can send a list of measurements
        self.item_end(item_result_state=measurement_results)  # always last line of test

    def TST001_Skip(self):
        """ Example of an item that is skipped

            {"id": "TST001_Skip",           "enable": false },
        """
        ctx = self.item_start()   # always first line of test
        # this is a skipped test for testing, in some scripts

        self.log_bullet("Was I skipped?")

        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

        self.item_end()  # always last line of test

    def TST002_Buttons(self):
        """ Select one of three buttons
        - capture the button index in the test record

            {"id": "TST002_Buttons",        "enable": true, "timeout": 10 },
        """
        ctx = self.item_start()   # always first line of test

        self.log_bullet("Please press a button!")

        buttons = ["one", "two", "three"]
        user_select = self.input_button(buttons)
        if user_select["success"]:
            b_idx = user_select["button"]
            self.log_bullet("{} was pressed!".format(buttons[b_idx]))
            _, _result, _bullet = ctx.record.measurement("button", b_idx, ResultAPI.UNIT_INT)
            self.log_bullet(_bullet)
        else:
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet(user_select.get("err", "UNKNOWN ERROR"))

        self.item_end(_result)  # always last line of test

    def TST003_KeyAdd(self):
        """ How use of keys: keys are things like serial numbers.
        - every call to self.add_key(k,v) adds the "k:v" to the next available
          key# in the record, you can force the slot though.  It depends how you will
          manage the keys in the final database; either by convention force every slot
          to represent a specific thing (preferred), or search all keys for the 'k' you want.

            {"id": "TST003_KeyAdd",         "enable": true },
        """
        ctx = self.item_start()   # always first line of test

        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

        value = random.randint(0, 100)
        ctx.record.add_key("value", value, slot=0)
        self.log_bullet("added key value: {}".format(value))

        self.item_end()  # always last line of test

    def TST004_KeyGet(self):
        """ How use of keys works
        - retrieve a previous key, otherwise fail test

            {"id": "TST004_KeyGet",         "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

        keys = ctx.record.get_keys()
        if not keys.get("key0", False):
            self.log_bullet("ERROR key[0]: {}".format("NOT FOUND!"))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        self.log_bullet("got key[0]: {}".format(keys.get("key0", "NOT FOUND!")))
        self.item_end()  # always last line of test

    def TST005_RsrcLock(self):
        """ Demonstrate locking of a resource in shared_state
        - lock a resource for some time, and then release
        - note the hold time comes from the test script
        - this is useful for a piece of test equipment that is shared across channels

            {"id": "TST005_RsrcLock",       "enable": true, "args": {"holdTime": 1}, "timeout": 60 },
        """
        ctx = self.item_start()  # always first line of test

        hold_time = ctx.item.args.get("holdTime", 5)  # a safe way to get parms, a default backup

        self.log_bullet("waiting for my_resource...")
        self.shared_lock("my_resource").acquire()
        while hold_time:
            self.log_bullet("my_resource is locked for {} seconds".format(hold_time), ovrwrite_last_line=True)
            time.sleep(1)
            hold_time -= 1
        self.shared_lock("my_resource").release()
        self.log_bullet("my_resource is free")

        self.item_end()  # always last line of test

    def TST006_HWDriver(self):
        """ How to get a driver that was initialized when script was loaded
        - when the script is loaded, HW driver are initialized and stored in the shared
          state.  The format of the return data is,

          {"channel": idx, "type": type, "obj": d}
          where d:  {'id': <int>, "version": <version>, <"key": "value">, ...}

        - how the "obj" field depends on the HW driver
        """
        ctx = self.item_start()  # always first line of test

        time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

        drivers = self.shared_get_drivers()
        for driver in drivers:
            self.log_bullet("found driver: {} {} {}".format(driver["type"],
                                                            driver["obj"]["id"],
                                                            driver["obj"]["version"]))

        self.item_end()  # always last line of test

    def TST007_LogPctProgress(self):
        """ Demo a log bullet with increasing percent
        """
        ctx = self.item_start()  # always first line of test

        percent = 0
        while percent <= 100:
            bar = "#" * int(40 * percent / 100)
            msg = "Completed {:3d}% {}".format(percent, bar)
            self.log_bullet(msg, ovrwrite_last_line=True)
            time.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)
            percent += 10

        self.item_end()  # always last line of test

    def TST008_TextInput(self):
        """ Text Input Box

            {"id": "TST008_TextInput",      "enable": true, "timeout": 10 },
        """
        ctx = self.item_start()   # always first line of test

        self.log_bullet("Please Enter Text!")

        user_text = self.input_textbox("Enter Some Text:", "change")
        if user_text["success"]:
            self.log_bullet("Text: {}".format(user_text["textbox"]))
            # Note: ResultAPI.UNIT_STRING is used to format the measurement correctly in JSON
            _, _result, _bullet = ctx.record.measurement("input", user_text["textbox"], ResultAPI.UNIT_STRING)
            # qualify the text here, and override _result if required

        else:
            # operator probably times out...
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet(user_text.get("err", "UNKNOWN ERROR"))

        self.item_end(_result)  # always last line of test

    def TST009_BlobUnknown(self):
        """ Blob Unknown

            {"id": "TST009_BlobUnknown",    "enable": true },
        """
        ctx = self.item_start()   # always first line of test

        # create a string of random characters to represent a blob
        myBlob = ResultAPI.BLOB_UNKNOWN
        myBlob["data"] = ''.join(random.choice(string.ascii_lowercase) for x in range(1000))
        success, msg = ctx.record.blob("random", myBlob)
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test

    def TST010_BlobXY(self):
        """ Blob XY Plots

        An example of creating a waveform, with a template to fit
        - testing wave fitting the template is beyond the scope of this example

            {"id": "TST010_BlobXY",    "enable": true },
        """
        ctx = self.item_start()   # always first line of test
        from numpy import sin, arange

        myBlob = ResultAPI.BLOB_PLOTXY

        # this is the waveform, could come from a scope, artificially generated example
        myPlot = ResultAPI.BLOB_PLOTXY_PLOT
        myPlot["x"] = arange(0, 3.2, 0.05).tolist()  # hundreds of data points...
        myPlot["y"] = sin(myPlot["x"]).tolist()
        myBlob["plots"].append(copy.deepcopy(myPlot))

        # upper template
        myPlot = ResultAPI.BLOB_PLOTXY_PLOT
        myPlot["x"] = [0.0, 1.0, 2.2, 3.2]
        myPlot["y"] = [0.1, 1.1, 1.1, 0.1]
        myBlob["plots"].append(copy.deepcopy(myPlot))

        # lower template
        myPlot = ResultAPI.BLOB_PLOTXY_PLOT
        myPlot["x"] = [0.1, 1.3, 1.8, 3.0]
        myPlot["y"] = [0.0, 0.9, 0.9, 0.0]
        myBlob["plots"].append(copy.deepcopy(myPlot))

        # save the blob of data
        success, msg = ctx.record.blob("sin", myBlob)
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        # here (the measurement) would be code to determine if waveform fits into template
        within_template = True  # or False

        # store measurement result
        success, _result, _bullet = ctx.record.measurement("template", within_template, ResultAPI.UNIT_BOOLEAN)
        self.log_bullet(_bullet)
        if not success:
            self.item_end(_result)
            return

        self.item_end()  # always last line of test

    def TST011_JSONB(self):
        """ postgres JSONB object example

            {"id": "TST009_BlobUnknown",    "enable": true },
        """
        ctx = self.item_start()   # always first line of test

        my_jsonb = {"serialNum": 123456789}
        jsonb = ctx.record.getCustomJSONB()
        jsonb.update(my_jsonb)
        success, msg = ctx.record.setCustomJSONB(jsonb)
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.item_end()  # always last line of test
