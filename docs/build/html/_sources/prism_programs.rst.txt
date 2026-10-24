Programs
========

Programs are Python code that implement :ref:`prism_scripts:tests` ``items``, and the location and name of the
program file is given in field ``module``.

A very minimalist ("hello world") (helloWorld.py) program file could look like this,

::

    #! /usr/bin/env python
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
        "drivers": ["public.prism.drivers.fake.hwdrv_fake"]
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

Lets take a more detailed look at the program structure,

::

    #! /usr/bin/env python
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

    ctx = self.item_start()  # always first line of test

* The last line of every method is

::

    self.item_end() # always last line of test

* more complex versions of the last line will be covered TBD-here

context
^^^^^^^

* ``ctx`` (context) is your programmatic view of the script, and retrieving it is the first line of every method
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
        "drivers": ["public.prism.drivers.fake.hwdrv_fake"]
      },
      "tests": [
        {
          "module": "public.prism.scripts.my_product.helloWorld",
          "options": { "fail_fast": false, "myVar": "something" },
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
        ctx = self.item_start()  # always first line of test

        print(ctx.item)          # = {"id": "TST000", "enable": True,  "args": {"min": 0, "max": 10}}
        print(ctx.item.args)     # = {"min": 0, "max": 10}
        print(ctx.item.args.max) # = 10
        print(ctx.options)       # = { "fail_fast": False, "myVar": "something" }
        ...

        self.item_end() # always last line of test

* in Python, you can do ``print(dir(ctx))`` to get a list of everything available to you
* When designing your test script and program structure, consider what user configurable variables you want to be
  defined in the script ``args`` section and which you want in the program.  Things like min/max limits may change
  over the product life cycle, and its better to make those things editable by a non-programmer. See TBS-Planning


Timeouts and Aborts
-------------------

Every test item is guarded by a timeout (see ``timeout`` in :ref:`prism_scripts:tests`).
An item can also be aborted, for example when the Operator presses Abort All.
When either happens, Prism records the result and moves on to the teardown item.

Prism cannot interrupt your Python code.
A ``time.sleep()``, a long loop or a blocking driver call keeps running until it finishes,
and the channel waits for it.
Write your waits and loops so they stop early,

* ``self.sleep(seconds)`` - use instead of ``time.sleep()``.  It returns ``True`` if the full time
  elapsed, or ``False`` as soon as the item times out or is aborted.
* ``self.check_abort()`` - call it in loops.  If the item timed out or was aborted, it ends the item
  right there, and Prism records ``TIMEOUT`` (or an error for an abort).  It raises an exception
  that ``except Exception`` does not catch, so release held resources with ``with`` or ``try/finally``.
* ``self.timeout`` - ``True`` once the item has timed out.

For example,

::

    def TST009_LogPctProgress(self):
        ctx = self.item_start()  # always first line of test

        percent = 0
        while percent <= 100:
            self.check_abort()  # ends the item here if it timed out or was aborted
            self.log_bullet("Completed {:3d}%".format(percent), ovrwrite_last_line=True)
            self.sleep(0.5)
            percent += 10

        self.item_end()  # always last line of test

A shared resource lock is released even when the item is stopped,

::

    with self.shared_lock("my_resource"):
        while hold_time:
            if not self.sleep(1): break  # item timed out or was aborted
            hold_time -= 1

The result you pass to ``self.item_end()`` after a timeout is ignored; the item is recorded as ``TIMEOUT``.

If an item is still running 5 seconds after its timeout, Prism forces it to stop.
This breaks a Python loop, but it cannot interrupt a blocked call such as ``time.sleep()`` or a driver
waiting on hardware; the item stops when that call returns.
If the item is still running 5 seconds later, Prism shows a "not responding" notice.
For a long blocking driver call, give the driver its own timeout shorter than the item ``timeout``.


Everything Example
------------------

Here is a fully documented program example that shows just about every feature of the Prism system.
It is the example distributed with the system, `public/prism/scripts/example/prod_v0/tst00xx.py`.

.. literalinclude:: ../../public/prism/scripts/example/prod_v0/tst00xx.py
   :language: python


And here is the script that drives the program, `public/prism/scripts/example/prod_v0/prod_0.scr`,

.. literalinclude:: ../../public/prism/scripts/example/prod_v0/prod_0.scr
   :language: javascript


Measurements
------------

Measurements are typically made by your test programs to decide on Pass/Fail.  Measurements are stored in
a results (JSON) file and sent to a backend `Lente` database.  What measurements to save are up to your requirements.
The Prism platform has an API to make storing measurements easy, and in a prescriptive way, so that these results
can be analyzed from the backend SQL database.

Example of measurement API is show in the example above, but are reviewed here in detail.

::

    def measurement(self, name, value, unit=ResultAPI.UNIT_NONE, min=None, max=None, force_fail=False):
        """ Check and store a measurement
        - performs a check on the value, returning one of ResultAPI.RECORD_RESULT_*
        - all values are stored as strings in the dB, converted here

        :param name: must be unique per test item
        :param force_fail: when set, forces measurement to fail
        :param min: min limit (int or float), None to ignore
        :param max: min limit (int or float), None to ignore
        :param value: any
        :param unit: one of self.UNIT_*
        :return: success, result, msg
            success: True: measurement accepted
                     False: a error occurred
            result: one of ResultAPI.RECORD_RESULT_*
                    (can be passed into self.item_end(), see examples)
            msg: if not success, this is error message
                 if success, this is human friendly message of the measurment
        """

``name`` - this will be appended to the full name of the test, which is the module path of the
program (without the leading `public.prism.scripts.`), the class method (item ``id``), and finally this name.
For example, `example.prod_v0.tst00xx.TST000_Meas.apples`.  As such the final test name is a unique
identifier, and it must be 128 characters or less.

.. note::

    It is important that test measurements have a unique `name` so that any particular measurement
    can be searched for in the SQL database.  If a duplicate `name` is used, `measurement()` will
    fail with RECORD_RESULT_INTERNAL_ERROR.


``value`` - the quantity to be tested.  The instance type of the value determines the behaviour
of the testing and the requirements of 'min' and 'max'.  Valid types are int, float, bool, and str.

.. note::

    For boolean type, `measurement()` will test that `value` is True.  If a `value` of False is
    a PASS, you will need to invert it before calling `measurement()`.


.. note::

    For integer and float types, `measurement()` will test `min <= value <= max`.
    Either set both `min` and `max`, or set both to None, one sided limits are not supported.

.. note::

    The types of `value`, `min` and `max` must agree.  A float `value` may use int or float limits
    (the limits are converted to float).  An int `value` requires int limits, an int `value` with float
    limits fails with RECORD_RESULT_INTERNAL_ERROR.  Values from ``subs`` of type `num` and from
    instruments are often floats, convert with `float()` or `int()` as needed.


.. note::

    For str (string) types, `measurement()` will always PASS.  `min` and `max` must be set to None.
    String types are useful for storing serial numbers in the database.


``min`` - minimum quantity to test on ``value``.  Can only be of type `int`, `float`, or `None`.
Type `None` is used for types of ``value`` that do not use `min` or `max`, for example, when ``value``
is a boolean or string type, `min` and `max` must be None.


``max`` - maximum quantity to test on ``value``.  Can only be of type `int`, `float`, or `None`.
Type `None` is used for types of ``value`` that do not use `min` or `max`, for example, when ``value``
is a boolean or string type, `min` and `max` must be None.


``units`` - the units of measurement to be stored in the result.  The units of measurement are not
used to determine the type of test to do on ``value``.  Valid units are the `ResultAPI.UNIT_*` constants
in `public/prism/api.py`, for example `UNIT_VOLTS`, `UNIT_MILLIAMPS`, `UNIT_HERTZ`, `UNIT_STRING`.
New units can be added there, and must also be added to `UNIT_ALL`.  An unknown unit fails with
RECORD_RESULT_INTERNAL_ERROR.


Measurements are called thru the ``ctx.record.measurement()`` API like this,

::

    def myTest(self):
        ctx = self.item_start()   # always first line of test

        value = <some_value_from_test_equipment>
        success, _result, _bullet = ctx.record.measurement("apples",
                                                           random.randint(0, 10),
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.args.min,
                                                           ctx.item.args.max)
        self.log_bullet(_bullet)
        self.item_end(_result)  # always last line of test

* calling ``ctx.record.measurement()`` means that this value will be in the backend database

  * The stored `name` of the test will be "<module>.myTest.apples", for example if the program is
    `public/prism/scripts/my_product/helloWorld.py`, the name is "my_product.helloWorld.myTest.apples".


* three parameters are returned, shown above as ``success, _result, _bullet``

  * ``success`` boolean indicating if the function was called successfully (not the result of the measurement).
  * ``_bullet`` string suitable for printing to the log via ``self.log_bullet()``
  * ``_result`` is meant to be sent to ``self.item_end()`` as shown and thus the state of the test is set (Pass or Fail)
  * ``_result`` may cause the program to take different action and not affect the state of the test item simply
    by not sending the result to ``self.item_end()``



Binning Failures
----------------

When a failure occurs in production, typically the DUTs are "binned" according to the failure type.  Then the
"bin" is bulk processed at a later time.  Given this typical process, Prism provides a means of indicating
a "binning code" when a failure occurs.

The "binning mechanism" is provided by the ``fail`` field for the test item in the script.  There is a list
of binning failure IDs (``fid``) with a corresponding ``msg`` for the user in the script.  This is shown in the
example ``TST001_Meas`` above.  Repeated here.

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

    {"id": "TST001_Meas",  "enable": true, "args": {"min": 0, "max": 10},
                           // fail: this is a list of 'fid' and 'msg' that get displayed and
                           //       recorded with the test record.  The python code for this
                           //       test item assigns which item in the list best represents
                           //       the failure mode.  This information is to assist repair.
                           "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                     {"fid": "TST000-1", "msg": "Component banana R1"}] },

Program code,

::

    def TST001_Meas(self):
        """ Measurement example, with multiple failure messages
        - example of taking multiple measurements, and sending as a list of results
        - if any test fails, this test item fails

            {"id": "TST001_Meas",    "enable": true, "args": {"min": 0, "max": 10},
                                     "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                               {"fid": "TST000-1", "msg": "Component banana R1"}] },
        """
        ctx = self.item_start()   # always first line of test

        self.sleep(self.DEMO_TIME_DELAY * random.random() * self.DEMO_TIME_RND_ENABLE)

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


The idea is that over time, the failure codes and messages can become more accurate and meaningful as
production failures become understood.

