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
      database searches and filtering on.  See :ref:`_prodplan:Naming Proposal`


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
            {"id": "TST020_meas_fail", "enable": true, "min": 0, "max": 10,
                                       "fail": [ {"fid": "TST020-1", "msg": "Component apple R1"},
                                                 {"fid": "TST020-2", "msg": "Component banana R1"}] },
          ]
        }
      ]
    }

* And lets assume we are in the ``TST020_meas_fail`` method, then we can access (print) anything that is relevent,

::

    def TST020_meas_fail(self):
        ctx = self.item_start()  # always first line of test

        print(ctx.item)              # = {"id": "TST020_meas_fail", "enable": True, "min": 0, "max": 10, "fail": [...]}
        print(ctx.item.max)          # = 10
        print(ctx.item.get("max", 5))  # = 10, 5 when the item has no "max"
        print(ctx.options)           # = { "fail_fast": False, "myVar": "something" }
        ...

        self.item_end() # always last line of test

* in Python, you can do ``print(dir(ctx))`` to get a list of everything available to you
* When designing your test script and program structure, consider what user configurable variables you want to be
  defined in the script, on each item, and which you want in the program.  Things like min/max limits may change
  over the product life cycle, and its better to make those things editable by a non-programmer.
  See :ref:`prism_scripts:Script Design`


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

    def TST100_log_progress(self):
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

The teardown item runs normally after an abort: ``self.sleep()``, ``self.check_abort()`` and
operator inputs work, and its own result is recorded.
Aborting again while the teardown runs stops the teardown too.

Exit Script Runner while a test is running asks to Abort-All.
Prism then waits for each channel to run its teardown item and write its result before the
script runner exits.
If an item never returns, press Exit Script Runner again to exit right away; the teardown is
skipped and no result is written.
Stopping Prism (``./prism.sh stop``) also aborts a running test and gives the teardown up to
5 seconds to finish.


Test Equipment Errors
---------------------

Drivers such as BOND, ST-LINK, nRF and Segger return a dict from each method,
``{"success": True, "method": "...", "result": {...}}``.  ``success`` means the method ran and
returned a value: it exists, its arguments were accepted and the equipment answered.  It is not
a pass or fail of the test: a value that is out of its limits comes back in ``result`` with
``success`` ``True``, and the item checks it with ``ctx.record.measurement()``.  ``success`` is
``False`` when the test equipment failed, for example BOND did not answer.  That is not a fail
of the DUT, the item ends as ``INTERNAL_ERROR``.

Pass the response to ``self.expect()``,

::

    response = self.expect(self.bond.bond_max_hdr_adc(1, 13))
    _, result, bullet = ctx.record.measurement("T105a_v3v_out", response["result"]["mV"],
                                               ResultAPI.UNIT_MILLIVOLTS,
                                               min=ctx.item.min, max=ctx.item.max)

    self.expect(self.bond.vdut_con(False))  # when the result is not needed

* when ``success`` is ``True``, ``self.expect()`` returns the response unchanged
* when ``success`` is ``False``, it logs the response, shows ``!<method> failed! <error>`` in the
  channel log and ends the item as ``INTERNAL_ERROR``, right there.  The rest of the item does not
  run, and Prism moves on to the teardown item.  Like ``self.check_abort()``, it raises an
  exception that ``except Exception`` does not catch, so release held resources with ``with`` or
  ``try/finally``, for example ``with self.shared_lock(...):``
* the teardown item puts the test equipment in a safe state, for example turns DUT power off,
  since an item that ends this way does not undo what it set up
* when something must be done before the item ends, for example sending the DUT a command, check
  ``response["success"]`` yourself, as below

Use ``self.expect()`` for driver responses, and for DUT commands sent through a DUT protocol
library that returns the same dict, see `DUT Command Errors`_.  Not for,

* ``self.input_button()`` and ``self.input_textbox()``: no answer from the operator is not an
  equipment error, handle ``success`` in the item
* a DUT command that a fault on the board can stop, see `DUT Command Errors`_
* a value the DUT or the equipment returned: check it with ``ctx.record.measurement()``
* driver methods that return ``True``/``False`` or a tuple, such as a driver's ``init()``

Older programs check each response by hand.  This still works,

::

    response = self.bond.bond_max_hdr_adc(1, 13)
    if not response["success"]:
        self.logger.error(response)
        self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
        return

To move to ``self.expect()``, replace each such block with one line,
``response = self.expect(self.bond.bond_max_hdr_adc(1, 13))``, or ``self.expect(...)`` without
``response =`` when the response is not used.  Keep the block when it does more than log and
end the item, such as releasing a lock (change it to ``with``) or sending the DUT a command.
Then run ``prism_dev.py --lint``.


DUT Command Errors
------------------

A program that sends commands to the DUT, for example to a test firmware on the DUT over a
serial link, keeps that protocol in a library module of its own, like a driver.  Each command
method of the library returns the same dict as a driver,

::

    {"success": True,  "method": "rail_3v3", "result": {...}}       # the command ran
    {"success": False, "method": "rail_3v3", "result": {"error": "no reply in 5.0 s"}}

* ``success`` means the command ran and returned a value: the DUT answered, and knew the command
  and its arguments.  ``success`` is ``False`` only when the command could not run: no reply,
  an unknown command, bad arguments
* the values the DUT returns are in ``result``.  A test result is a value, never ``success``
  ``False``: a sensor that doesn't answer on its bus comes back as, for example,
  ``{"ack": False}`` with ``success`` ``True``, and the item records it with
  ``ctx.record.measurement()``
* the error text is in ``result["error"]``, which ``self.expect()`` shows in the channel log
* when the DUT replies in its own format, the library converts it.  The DUT firmware doesn't
  change,

::

    def cmd(self, line, timeout=5.0):
        r = self._send_and_wait(line, timeout)     # the DUT's reply, {"cmd": ..., "done": ..., ...}
        return {"success": r["done"], "method": r["cmd"],
                "result": dict(r, error=r.get("why", ""))}

Pass the response to ``self.expect()`` when a failed command can only mean the station or the
test setup is wrong.  That is the usual case: the command and its arguments are written in the
program, and an earlier item has shown that the DUT answers.  The item ends as
``INTERNAL_ERROR``, the same as for a driver,

::

    self.expect(self.dut.cmd("rail_3v3 -e"))
    self.sleep(0.05)
    response = self.expect(self.bond.bond_max_hdr_adc(1, 13))
    _, result, bullet = ctx.record.measurement("v3v3", response["result"]["mV"] / 1000,
                                               ResultAPI.UNIT_VOLTS,
                                               min=ctx.item.min, max=ctx.item.max,
                                               fail=ctx.item.fail[0])
    self.log_bullet(bullet)

Don't use ``self.expect()`` when a fault on the board can stop the command, for example a missing
or badly soldered part gives no answer on a bus, and the DUT firmware can't report it as a
value.  The board is then the likely cause, so check ``success`` in the item and end it as
``FAIL`` with its ``fail`` message, for the repair technician.  Say why in the docstring,

::

    def TST330_sensor_id(self):
        """ Humidity sensor id over I2C.  Not expect(): with U12 missing or not soldered
        the DUT gets no I2C ack and the command fails, a board fault.

            {"id": "TST330_sensor_id", "enable": true,
             "fail": [{"fid": "TST330-1", "msg": "Humidity sensor id: check U12 R20 R21"}]},
        """
        ctx = self.item_start()  # always first line of test

        response = self.dut.cmd("sensor_id")
        if not response["success"]:
            self.logger.error(response)
            self.log_bullet(f"DUT sensor_id: {response['result']['error']}")
            ctx.record.fail_msg(ctx.item.fail[0])
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return
        _, result, bullet = ctx.record.measurement("dev_id", response["result"]["dev"],
                                                   ResultAPI.UNIT_INT, min=0x07d0, max=0x07d0,
                                                   fail=ctx.item.fail[0])
        self.log_bullet(bullet)
        self.item_end(result)  # always last line of test

The item that first opens the link to the DUT records whether the DUT answered as a
``UNIT_BOOLEAN`` measurement with a ``fail`` message, so a board that never answers, for example
one that doesn't power up or boot, ends as ``FAIL`` with a hint.  A DUT that stops answering
later in the test is unexpected, and ``INTERNAL_ERROR`` is the right result.

Older programs check each DUT reply by hand and end the item as ``FAIL``.  This still works.  To
move to ``self.expect()``, change the library to return the dict above, change each
``r["value"]`` in the test code to ``r["result"]["value"]``, and replace each block whose command
only the station or the setup can stop with ``self.expect(...)``.  Keep the blocks of the commands
a fault on the board can stop.


Errors in a Test Item
---------------------

Prism records a test item as ``INTERNAL_ERROR``, a fail, and moves on to the teardown item when,

* a driver or DUT library response passed to ``self.expect()`` failed, see
  `Test Equipment Errors`_ and `DUT Command Errors`_
* the item raises an exception that it does not catch
* the item returns without calling ``self.item_start()``
* the result passed to ``self.item_end()`` is not one of the ``ResultAPI.RECORD_RESULT_*`` constants,
  or a list of them
* ``self.item_end(_next="<id>")`` names an item that does not come later in the script

The error is shown in the channel log.  Other than a failed ``self.expect()``, which is an
equipment error and not a program error, it is also stored in the result ``errors`` list.

An item that calls ``self.item_start()`` and returns without ``self.item_end()`` is recorded as
``TIMEOUT`` when its timeout expires.

The script linter finds most of these mistakes before the script runs, see
:ref:`_development:Script Lint`.

The ``ResultAPI.BLOB_*`` dicts are templates.  Copy one with ``copy.deepcopy()`` before filling it in,
as the example does; changing the template itself changes it for every later test and channel.


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
For example, `example.prod_v0.tst00xx.TST010_meas.apples`.  As such the final test name is a unique
identifier, and it must be 128 characters or less.

.. note::

    It is important that test measurements have a unique `name` so that any particular measurement
    can be searched for in the SQL database.  If a duplicate `name` is used, `measurement()` will
    fail with RECORD_RESULT_INTERNAL_ERROR.


``value`` - the quantity to be tested.  The instance type of the value determines the behaviour
of the testing and the requirements of 'min' and 'max'.  Valid types are int, float, bool, and str.

.. note::

    For boolean type, `measurement()` will test that `value` is True.  If a `value` of False is
    a PASS, you will need to invert it before calling `measurement()`.  Record a pass/fail check
    this way, as a bool that is True when it passes with `ResultAPI.UNIT_BOOLEAN`, and name it after
    the passing state, for example `ctx.record.measurement("dsr_off", dsr is False, ResultAPI.UNIT_BOOLEAN)`,
    rather than as a string with `force_fail`.


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
                                                           ctx.item.min,
                                                           ctx.item.max)
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
example ``TST020_meas_fail`` above.  Repeated here.

Example Notes:

* Two measurements are taken
* The measurement results are stored in a list, ``measurement_results``.  This list will be passed
  to ``self.item_end()`` so that all the results are considered by the system.  If any one of these results
  is a FAIL, the test item will FAIL.
* There is a co-operation between the test script and the test code as per the index to the type of failure.
  This is coded in the constants ``FAIL_APPLE`` and ``FAIL_BANANNA``
* ``fail=ctx.item.fail[i]`` on ``ctx.record.measurement()`` sets the user facing "binning" message
  when that measurement fails.  Nothing is set when it passes
* The ``fid`` text represents the "binning" code
* The ``msg`` is there to provide a hint to the test engineer of where the problem might be,
  at most 64 characters (the script linter checks it)
* The ``fail`` list is only shown when the code passes an entry with ``fail=``, or calls
  ``ctx.record.fail_msg()``
* A test item records one binning message.  When more than one measurement with ``fail=`` fails,
  the last one is kept
* Use ``ctx.record.fail_msg(ctx.item.fail[i])`` yourself only when the failure is not decided by one
  measurement, for example picking the entry from which of several checks failed.  Older code that
  calls ``fail_msg()`` after each measurement keeps working, and can be moved to ``fail=`` by
  deleting the ``if _result == ResultAPI.RECORD_RESULT_FAIL:`` block and passing its entry with
  ``fail=``

::

    {"id": "TST020_meas_fail", "enable": true, "min": 0, "max": 10,
                               // fail: this is a list of 'fid' and 'msg' that get displayed and
                               //       recorded with the test record.  The python code for this
                               //       test item assigns which item in the list best represents
                               //       the failure mode.  This information is to assist repair.
                               "fail": [ {"fid": "TST020-1", "msg": "Component apple R1"},
                                         {"fid": "TST020-2", "msg": "Component banana R1"}] },

Program code,

::

    def TST020_meas_fail(self):
        """ Measurement example, with multiple failure messages
        - example of taking multiple measurements, and sending as a list of results
        - if any test fails, this test item fails

            {"id": "TST020_meas_fail", "enable": true, "min": 0, "max": 10,
                                       "fail": [ {"fid": "TST020-1", "msg": "Component apple R1"},
                                                 {"fid": "TST020-2", "msg": "Component banana R1"}] },
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
                                                           ctx.item.min,
                                                           ctx.item.max,
                                                           fail=ctx.item.fail[FAIL_APPLE])
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        # Bananas measurement...
        success, _result, _bullet = ctx.record.measurement("bananas",
                                                           random.randint(0, 10),
                                                           ResultAPI.UNIT_DB,
                                                           ctx.item.min,
                                                           ctx.item.max,
                                                           fail=ctx.item.fail[FAIL_BANANNA])
        if not success:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.log_bullet(_bullet)
        measurement_results.append(_result)

        # Note that we can send a list of measurements
        self.item_end(item_result_state=measurement_results)  # always last line of test


The idea is that over time, the failure codes and messages can become more accurate and meaningful as
production failures become understood.

