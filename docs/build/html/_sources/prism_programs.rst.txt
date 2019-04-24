Programs
========

Programs are Python code that implement :ref:`prism_scripts:tests` ``items``, and the location and name of the
program file is given in field ``module``.

A very minimalist ("hello world") (helloWorld.py) program file could look like this,

::

    ! /usr/bin/env python
    # -*- coding: utf-8 -*-

    import logging
    from core.test_item import TestItem
    from public.prism.api import ResultAPI

    # file name and class name must match
    class helloWorld(TestItem):

        def __init__(self, controller, chan, shared_state):
            super().__init__(controller, chan, shared_state)
            self.logger = logging.getLogger("SC.{}.{}".format(__name__, self.chan))

        def sayHello(self):
            ctx = self.item_start()  # always first line of test
            self.log_bullet("Hello World!")
            self.item_end() # always last line of test


And, a minimalist script file that uses this program code, could look like this,

::

    {
      "info": {
        "product": "widget_1",
        "bom": "BOM1-1",
        "lot": "MYLOT1",
        "location": "FACTORY1"
      },
      "config": {
        "drivers": ["public.prism.drivers.fake.fake"]
      },
      "tests": [
        {
          "module": "public.prism.scripts.my_product.helloWorld",
          "options": {},
          "items": [
            {"id": "sayHello"},
          ]
        }
      ]
    }

Lets make some general comments about the above script/program before diving into the details,

* script

  * ``options`` has no key/value assignments.  This means that ``fail_fast`` is assumed to be true. See :ref:`prism_scripts:config`
  * the ``module`` value ``public.prism.scripts.my_product.helloWorld`` **matches the class name and the program file name**
  * has no (optional) ``subs`` section

* Program

  * there is no requirement for method names, the above uses ``sayHello`` for example

    * However, you should plan to have a test naming structure, as these test names is what you will be doing backend
      database searches and filtering on.  See TBD-Planning


Program Class Structure
-----------------------

Lets take a more detailed look at the program structrure,

::

    ! /usr/bin/env python
    # -*- coding: utf-8 -*-

    import logging
    from core.test_item import TestItem
    from public.prism.api import ResultAPI

    # file name and class name must match
    class helloWorld(TestItem):

        def __init__(self, controller, chan, shared_state):
            super().__init__(controller, chan, shared_state)
            self.logger = logging.getLogger("SC.{}.{}".format(__name__, self.chan))

        def sayHello(self):
            context = self.item_start()  # always first line of test
            self.log_bullet("Hello World!")
            self.item_end() # always last line of test

methods
^^^^^^^

* if you are not already familiar with Python Classes, you should quickly take an online tutorial

  * for Prism programs you don't need to know a lot about Python Class methods and fancy things that you
    can do with them
* there are two methods shown in the example program, ``__init__`` and ``sayHello``
* From a Prism point of view, a method in the class is called IF it is referenced in the script ``tests`` ``items``
  ``id`` field - if you reference the above simple script, ``sayHello`` is referenced

  * **``__init__`` is NOT to be referenced by the script in anyway**
  * ``__init__`` is called automatically when the script is loaded by the system.  You should not have any test
    code in the ``__init__`` method.  You can add more self.variable_name as required

* Methods that you add that are called by the script, will NOT have any additional arguments, only ``self``
* The first line of every method is

::

    context = self.item_start()  # always first line of test

* The last line of every method is

::

    self.item_end() # always last line of test

* more complex versions of the last line will be covered TBD-here

context
^^^^^^^

* ``context`` is your programmatic view of the script, and retrieving it is the first line of every method
* consider a little more complicated script,

::

    {
      "info": {
        "product": "widget_1",
        "bom": "BOM1-1",
        "lot": "MYLOT1",
        "location": "FACTORY1"
      },
      "config": {
        "drivers": ["public.prism.drivers.fake.fake"]
      },
      "tests": [
        {
          "module": "public.prims.scripts.my_product.helloWorld",
          "options": { "fail_fast": False, "myVar": "something" },
          "items": [
            {"id": "sayHello"},
            {"id": "TST000_Meas",  "enable": true, "args": {"min": 0, "max": 10},
                                   "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                             {"fid": "TST000-1", "msg": "Component banana R1"}] },
          ]
        }
      ]
    }

* And lets assume we are in the ``TST000_Meas`` method, then we can access (print) anything that is relevent,

::

    def TST000_Meas(self):
        context = self.item_start()  # always first line of test

        print(ctx.item)          # = {"id": "TST000", "enable": True,  "args": {"min": 0, "max": 10}}
        print(ctx.item.args)     # = {"min": 0, "max": 10}
        print(ctx.item.args.max) # = 10
        print(ctx.options)       # = { "fail_fast": False, "myVar": "something" }
        ...

        self.item_end() # always last line of test

* in Python, you can do ``print(dir(ctx))`` to get a list of everything available to you
* When designing your test script and program structure, consider what user configurable variables you want to be
  defined in the script ``args`` section and which you want in the program.  Things like min/max limits may change
  overt he product life cycle, and its better to make those things editable by a non-programmer. See TBS-Planning


Everything Example
------------------

Here is a fully documented program example that shows just about every feature of the Lente system.  This
example program is distributed with the system, and may be more up to date than here, so please consult that example.

::

    #! /usr/bin/env python
    # -*- coding: utf-8 -*-
    import logging
    from core.test_item import TestItem
    from public.prims.api import ResultAPI
    import time
    from random import randint, random


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
            #      - class ResultBaseClassKeysV1(ResultBaseClass)
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
            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

            self.item_end()  # always last line of test

        def TST0xxTRDN(self):
            ctx = self.item_start()  # always first line of test
            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)
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

            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

            FAIL_APPLE   = 0  # indexes into the "fail" list, just for code readability
            FAIL_BANANNA = 1

            measurement_results = []  # list for all the coming measurements...

            # Apples measurement...
            _result, _bullet = ctx.record.measurement("apples",
                                                      randint(0, 10),
                                                      ResultAPI.UNIT_DB,
                                                      ctx.item.args.min,
                                                      ctx.item.args.max)
            # if failed, there is a msg in script to attach to the record, for repair purposes
            if _result == ResultAPI.RECORD_RESULT_FAIL:
                msg = ctx.item.fail[FAIL_APPLE]
                ctx.record.fail_msg(msg)

            self.log_bullet(_bullet)
            measurement_results.append(_result)

            # Bananas measurement...
            _result, _bullet = ctx.record.measurement("bananas",
                                                      randint(0, 10),
                                                      ResultAPI.UNIT_DB,
                                                      ctx.item.args.min,
                                                      ctx.item.args.max)

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

            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

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
                _result, _bullet = ctx.record.measurement("button", b_idx, ResultAPI.UNIT_INT)
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

            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

            value = randint(0, 100)
            ctx.record.add_key("value", value, slot=0)
            self.log_bullet("added key value: {}".format(value))

            self.item_end()  # always last line of test

        def TST004_KeyGet(self):
            """ How use of keys works
            - retrieve a previous key, otherwise fail test

                {"id": "TST004_KeyGet",         "enable": true },
            """
            ctx = self.item_start()  # always first line of test

            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

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

            time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

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
                time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)
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

                # qualify the text here, and either if the text is invalid, re-ask
                # Note: ResultAPI.UNIT_STRING is used to format the measurement correctly in JSON
                ctx.record.measurement("input", user_text["textbox"], ResultAPI.UNIT_STRING)
                _result = ResultAPI.RECORD_RESULT_PASS
            else:
                # operator probably times out...
                _result = ResultAPI.RECORD_RESULT_FAIL
                self.log_bullet(user_text.get("err", "UNKNOWN ERROR"))

            self.item_end(_result)  # always last line of test

And here is the script that drives the program,

::

    # Example: Shows most of all the features of test portal UI
    {
      "info": {
        # info is captured in the result record and can be searched/filtered
        # Cannot add fields here without updating the result record handler and backend database
        "product": "widget_1",
        "bom": "B00012-001",
        "lot": "95035",
        "location": "canada/ontario/milton"
      },
      "config": {
        # -- These items can override those from prism.json, defaults are shown as example
        # result_*_dir - the 'stage' directory MUST be named stage.
        #              - any path must be under 'public'
        #"result_stage_dir": "public/result/stage",
        #"result_bkup_dir" : "public/result/bkup",
        #"result_server_url": "http://127.0.0.1:6600",
        #"result_server_retry_timer_sec": 10,
        #"result_encrypt": false,
        # --
        # fail_fast: if true (default), testing will stop on first failed test
        "fail_fast": false,
        # channel_hw_driver: list of code to initialize the test environment, must be specified
        "drivers": ["public.prism.drivers.fake.fake"]
      },
      "tests": [
        {
          # module is path to python code supporting this test
          "module": "public.prism.scripts.prod_v0.tst00xx",
          "options": {
            # fail_fast: if true (default), testing will stop on first failed test, overrides config section
            "fail_fast": false
            # timeout: defaults to 10 seconds, but can be overridden here, or in a test item (below)
            #"timeout": 20
            #
            # Other options may be added here for your specific use cases.
            # Options here are available to each item python coded implementation.
            # Think of these options like global variable to all test items in this module.
          },
          "items": [
            {"id": "TST0xxSETUP",           "enable": true },
            {"id": "TST000_Meas",           "enable": true, "args": {"min": 0, "max": 10},
                                            # fail: this is a list of 'fid' and 'msg' that get displayed and
                                            #       recorded with the test record.  The python code for this
                                            #       test item assigns which item in the list best represents
                                            #       the failure mode.  This information is to assist repair.
                                            "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                                      {"fid": "TST000-1", "msg": "Component banana R1"}] },
            {"id": "TST001_Skip",           "enable": false },
            {"id": "TST002_Buttons",        "enable": true, "timeout": 10 },
            {"id": "TST003_KeyAdd",         "enable": true },
            {"id": "TST004_KeyGet",         "enable": true },
            {"id": "TST005_RsrcLock",       "enable": true, "args": {"holdTime": 1}, "timeout": 60 },
            {"id": "TST006_HWDriver",       "enable": true },
            {"id": "TST008_TextInput",      "enable": true, "timeout": 10 },
            {"id": "TST007_LogPctProgress", "enable": true, "timeout": 15 },
            {"id": "TST0xxTRDN",            "enable": true }
          ]
        }
      ]
    }



Measurements
------------

Measurements are typically made by your test programs to decide on Pass/Fail.  Measurements can also be stored in
a results (JSON) file and sent to a backend database.  What measurements to save are up to your requirements.  The
Prism platform has an API to make storing measurements easy, and in a prescriptive way, so that these results
can be analyzed from the backend database.

Example of measurement API is show in the example above, but are reviewed here in detail.

::

    def measurement(self, name, value, unit, min=None, max=None):
        """
        :param name: name of measurement
        :param min: minimum value, None for ignore
        :param max: maximum value, None for ignore
        :param value: value
        :param unit: one of self.UNIT_*
        :return: result, msg
            where:
                result: one of <ResultAPI.RECORD_*>
                msg: string, string of measurement result, suitable for humans
        """

``name`` - this will be appended to the full name of the test, which is the path to the python
program, the program filename, the class method, and finally this name.  As such the final test
name is a unique identifier

``units`` - from,

::

    class ResultAPI(Const):

        # More types can be created for your specific application needs
        # These items will be in the result record and backend database

        TESTITEM_TIMEOUT = 10.0  # default test item timeout in seconds

        RECORD_RESULT_UNKNOWN = "UNKNOWN" # this is an error if not changed
        RECORD_RESULT_PASS = "PASS"
        RECORD_RESULT_FAIL = "FAIL"
        RECORD_RESULT_TIMEOUT = "TIMEOUT"
        RECORD_RESULT_INCOMPLETE = "INC"
        RECORD_RESULT_INTERNAL_ERROR = "INTERNAL_ERROR"
        RECORD_RESULT_SKIP = "SKIP"
        RECORD_RESULT_DISABLED = "DISABLED"

        UNIT_OHMS = "Ohms"
        UNIT_DB = "dB"
        UNIT_VOLTS = "Volts"
        UNIT_CURRENT = "Amps"
        UNIT_STRING = "STR"
        UNIT_INT = "Integer"
        UNIT_FLOAT = "Float"
        UNIT_CELCIUS = "Celcius"
        UNIT_BOOLEAN = "Boolean"
        UNIT_NONE = None
        UNIT_ALL = [UNIT_OHMS, UNIT_BOOLEAN, UNIT_NONE, UNIT_STRING, UNIT_VOLTS, UNIT_CELCIUS, UNIT_CURRENT,
                    UNIT_DB, UNIT_FLOAT, UNIT_INT]


        # ===================================================================================
        # BLOB data types
        #
        # BLOB_UNKNOWN
        # - unknown type of blob
        # - Lente will not try and plot/analyse blobs of this type, they are unknown
        BLOB_UNKNOWN = {
            "type": "BLOB_UNKNOWN",
            "data": None,              # replace with your data, must be JSON serializable
        }

        # Blobs that can be plotted
        # - Lente can plot blob data given the blob data type
        # - blobs that can be plotted, use BLOB_BOKEH_* dicts to define the plot
        # - there are a billion options to plotting with Bokeh, Lente only does bare minimum
        BLOB_BOKEH_FIGURE = {
            "title": "Title",
            "x_axis_type": "auto",  # auto, linear, log, datetime, mercator
            "x_axis_label": "X-Axis",
            "y_axis_type": "auto",  # auto, linear, log, datetime, mercator
            "y_axis_label": "Y-Axis",
        }

        # BLOB_PLOTXY
        # - XY plots
        # - 1 or more lines can be plotted
        # - use this type for plotting waves that fit a template (for example)
        BLOB_PLOTXY_PLOT = {
            "legend": None,  # change to string
            "line_width": 1,
            "x": [],         # x/y list lengths must be the same
            "y": [],
        }
        BLOB_PLOTXY = {
            "type": "BLOB_DICTXY",
            "BLOB_BOKEH_FIGURE": BLOB_BOKEH_FIGURE,
            "plots": [],   # append BLOB_DICTXY_PLOTs here as required...
        }

        # add any new types created here for the purposes of validating
        BLOB_TYPES = [BLOB_UNKNOWN["type"], BLOB_PLOTXY["type"]]


Measurements are called thru the ``ctx.record.measurement()`` API like this,

::

    def myTest(self):
        ctx = self.item_start()   # always first line of test

        value = <some_value_from_test_equipment>
        _result, _bullet = ctx.record.measurement("apples",
                                                  value,
                                                  ResultAPI.UNIT_DB,
                                                  ctx.item.args.min,
                                                  ctx.item.args.max)
        self.log_bullet(_bullet)
        self.item_end(_result)  # always last line of test

* two results are returned, shown above as ``_result, _bullet``
* ``_bullet`` string (second variable returned) is suitable for printing to the log via ``self.log_bullet()``
* ``_result`` is meant to be sent to ``self.item_end()`` as shown and thus the state of the test is set (Pass or Fail)
* ``_result`` may cause the program to take different action and not affect the state of the test item simply
  by not sending the result to ``self.item_end()``
* calling ``ctx.record.measurement()`` means that this value will be in the backend database


Binning Failures
----------------

When a failure occurs in production, typically the DUTs are "binned" according to the failure type.  Then the
"bin" is bulk processed at a later time.  Given this typical process, Prism provides a means of indicating
a "binning code" when a failure occurs.

The "binning mechanism" is provided by the ``fail`` field for the test item in the script.  There is a list
of binning failure IDs (``fid``) with a corresponding ``msg`` for the user in the script.  This is shown in the
example ``TST000_Meas`` above.  Repeated here.

Example Notes:

* Two measurements are taken
* The measurement results are stored in a list, ``measurement_results``.  This list will be passed
  to ``self.item_end()`` so that all the results are considered by the system.  If any one of these results
  is a FAIL, the test item will FAIL.
* There is a co-operation between the test script and the test code as per the index to the type of failure.
  This is coded in the constants ``FAIL_APPLE`` and ``FAIL_BANANNA``
* ``ctx.record.fail_msg()`` is used to set the user facing "binning" message
* The ``fid`` text represents the "binning" code
* The ``msg`` is there to provide a hint to the test engineer of where the problem might be

::

    {"id": "TST000_Meas",  "enable": true, "args": {"min": 0, "max": 10},
                           # fail: this is a list of 'fid' and 'msg' that get displayed and
                           #       recorded with the test record.  The python code for this
                           #       test item assigns which item in the list best represents
                           #       the failure mode.  This information is to assist repair.
                           "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                     {"fid": "TST000-1", "msg": "Component banana R1"}] },

Program code,

::

    def TST000_Meas(self):
        """ Measurement example, with multiple failure messages
        - example of taking multiple measurements, and sending as a list of results
        - if any test fails, this test item fails

            {"id": "TST000_Meas",    "enable": true, "args": {"min": 0, "max": 10},
                                     "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                               {"fid": "TST000-1", "msg": "Component banana R1"}] },
        """
        ctx = self.item_start()   # always first line of test

        time.sleep(self.DEMO_TIME_DELAY * random() * self.DEMO_TIME_RND_ENABLE)

        FAIL_APPLE   = 0  # indexes into the "fail" list, just for code readability
        FAIL_BANANNA = 1

        measurement_results = []  # list for all the coming measurements...

        # Apples measurement...
        _result, _bullet = ctx.record.measurement("apples",
                                                  randint(0, 10),
                                                  ResultAPI.UNIT_DB,
                                                  ctx.item.args.min,
                                                  ctx.item.args.max)
        # if failed, there is a msg in script to attach to the record, for repair purposes
        if _result == ResultAPI.RECORD_RESULT_FAIL:
            msg = ctx.item.fail[FAIL_APPLE]
            ctx.record.fail_msg(msg)

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        # Bananas measurement...
        _result, _bullet = ctx.record.measurement("bananas",
                                                  randint(0, 10),
                                                  ResultAPI.UNIT_DB,
                                                  ctx.item.args.min,
                                                  ctx.item.args.max)

        # if failed, there is a msg in script to attach to the record, for repair purposes
        if _result == ResultAPI.RECORD_RESULT_FAIL:
            msg = ctx.item.fail[FAIL_BANANNA]
            ctx.record.fail_msg(msg)

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        # Note that we can send a list of measurements
        self.item_end(item_result_state=measurement_results)  # always last line of test

The idea is that over time, the failure codes and messages can become more accurate and meaningful as
production failures become understood.

