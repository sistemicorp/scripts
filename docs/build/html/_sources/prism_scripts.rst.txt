Scripts
=======

``Scripts``

* define the test sequence and operating modes of the test being run
* are in human readable JSON file format

  * JSON is used so that non-programmers may be able to read/edit [1]_ the script without requiring a
    programming background.  This is useful in development or emergency situations.

* extend JSON a little bit, by allowing comments, any line beginning with `//` is a comment.  This allows
  the script to be documented

The ``script`` has the following sections,

::

    {
      "subs": {
      },
      "info": {
      },
      "config": {
      },
      "tests": [
      ]
    }


subs
----

This is a section of User configurable substitutions for variables in the script.  For example, if there was a test
limit that could have two values, the values can be listed as a `subs` field and the user can select which one to use.

In a production environment, operators are not typically allowed to arbitrarily change values of test
limits or any other setup.  However, in an engineering lab, or new product ramp environment, having an easy method
to change some parameters might be useful.  This feature does not have to be used.

Only (logged in) users with a certain role privileges can access the `Test Configuration` page, and thus access to GUI controls that
use the `subs` feature.  Otherwise `subs` are used to create a `Traveller`, which stores the `subs` used.

`subs` are useful for generating :ref:`prism_travellers:Travellers`.

Here is a full example of what `subs` section could look like (taken from example `prod_1.scr`),

::

  "subs": {
    // Each item here is described by,
    // "<subs_name>":
    //   "title": "<title>",
    //   "type" : "<str|num>",
    //   "widget": "<textinput|select>",
    //   "regex": <"regex">,  // only for widget == textinput,
    //                           the field is valid when the regex is satisfied;
    //                           Validate enables once all fields are valid,
    //                           Start Testing enables after a successful Validate
    //   "choices": [<choice1>, <choice2>, ...],  // only for widget == select
    //   "default": <default>,
    //   "subs": // inner dependant subs
    //           { <key1> : { "subs_name1": {"val": <>, "type": "<str|num>" }, ...},
    //             <key2> : { "subs_name1": {"val": <>, "type": "<str|num>" }, ...}
    //           }
    // }
    //
    // Rules:
    // 1. key must not have any spaces or special characters
    //
    "Lot": {
      "title": "Lot (format #####)",
      "type" : "str", "widget": "textinput", "regex": "^\\d{5}$", "default": "95035"
    },
    "Loc": {
      "title": "Location",
      "type" : "str", "widget": "select", "choices": ["canada/ontario/milton",
                                                      "us/newyork/buffalo"],
      // inner dependant substitutions based on user input
      "subs" : {"canada/ontario/milton": { "TST000Min": { "val": 0.1, "type": "num" }},
                "us/newyork/buffalo":    { "TST000Min": { "val": 0.2, "type": "num" }}
      }
    },
    "TST000Max": {
      "title": "TST000 Max Attenuation (db)",
      "type" : "num", "widget": "select", "choices": [9.0, 10.0, 11.0]
    },
    "TST000Enable": {
      "title": "TST000_Meas Enable",
      "type" : "str", "widget": "select", "choices": ["true", "false"]
    }
  },

  // and how it looks in the test item,
  {"id": "TST000_Meas",     "enable": "%%TST000Enable", "args": {"min": "%%TST000Min", "max": "%%TST000Max"}},


``key``

* the name of the variable to be replaced somewhere else in the script, for example, the variable could be in
  the ``info`` section

  * the variable in other sections, would be named ``"%%key"``
  * the variable would be listed with double quotes, regardless of the variable type
* ``key`` should not have any special characters in it, else bad things happen
* keys are matched whole, so ``"%%Lot"`` and ``"%%LotSize"`` are two different subs

``title``

* this is the title of the field to be presented to the Operator in the Test Configuration page
* if there is a specific format of the variable expected, that should be indicated in the ``title``

``type``

* indicates type of variable that is ultimately required in the final JSON version of the script
* string (`str`) and number (`num`) (covers float and ints) are the only options
* a `num` value must be a number, for example ``9`` or ``-0.5``, otherwise `Validate` fails
* a `str` value is used as typed; quotes and other special characters are kept as text

``widget``

* the type of GUI widget to present to the Operator in the Test Configuration page
* `textinput` is a generic text input box, which will be populated by the ``default`` field
* `select` is a drop down selection menu

``regex``

* used only for `textinput` ``widget``
* used to validate the Operator entered correct information
* this is optional field
* when every field is valid the `Validate` button is enabled, and after a successful
  `Validate` the `Start Testing` button is enabled

``default``

* sets the default value for `textinput` ``widget``
* optional

Inner Subs
----------

Inner subs allow one User sub to be able to set multiple other subs.  An example is shown in the ``subs`` section
above.  In the above example, when `Location` is selected by the user, `TST000Min` is assigned a value
depending on the `Location` selected.

From the example,

::

    "Loc": {
      "title": "Location",
      "type" : "str", "widget": "select", "choices": ["canada/ontario/milton",
                                                      "us/newyork/buffalo"],
      "subs" : {"canada/ontario/milton": { "TST000Min": { "val": 0.1, "type": "num" }},
                "us/newyork/buffalo":    { "TST000Min": { "val": 0.2, "type": "num" }}
      }
    },

    // used in a test item
    {"id": "TST000_Meas", "args": {"min": "%%TST000Min", "max": "%%TST000Max"}},

* The keys of the inner ``subs`` (``canada/ontario/milton``, ``us/newyork/buffalo``) are the values
  the Operator can pick, and must match the ``choices`` exactly.
* Each value maps to one or more inner subs, given as ``"<key>": {"val": <value>, "type": "<str|num>"}``.

  * ``<key>`` is used in the script as ``"%%<key>"``, the same as any other sub.
  * ``type`` works as described for ``type`` above; for `num` the quotes around ``"%%<key>"`` are removed.

* Inner subs are not shown on the Test Configuration page; the Operator only picks `Location`.
  Here, picking ``us/newyork/buffalo`` makes the test item ``"args": {"min": 0.2, ...}``.
* An inner sub key must not also be a key of the top level ``subs`` section.
* Every choice should list every inner sub.  If the picked value has no entry, ``"%%TST000Min"`` is
  left in the script and `Validate` fails with `ERROR: script subs problem`.
* Only one level is supported, an inner sub cannot have its own ``subs``.
* A :ref:`prism_travellers:Travellers` stores only the Operator's picks; the inner subs are applied
  again when the Traveller is scanned.

info
----

This section is a list of fields that correspond to fields that exist in the backend database and are typically
used for database searches.

You cannot add or delete fields from this section.  If there are missing fields, an error will occur downstream as the
result record is checked to have these fields.  New fields can be added, but that requires a request to customize
the backend database.  See TBD.

Note that the example here, two fields are using the `subs` section to get their values from the Operator
in the Test Configuration page.

::

  "info": {
    "product": "widget_1",
    "bom": "B00012-001",
    // list fields present user choice or fill in
    "lot": "%%Lot",
    "location": "%%Loc",
    // "config": "optional"
  },

``product`` - 32 character length field.

``bom`` - 32 character length field. Note `bom` stands for Bill of Materials.

``lot`` - 16 character length field.

``location`` - 128 character length field.

``config`` - (optional) 16 character length field.

Defining rules and a naming convention for these fields will help you later when you need to make database searches
for specific sets of results.  This is important.

config
------

This section sets required variables that Prism uses to drive the test script.

::

  "config": {
    "fail_fast": true,
    "drivers": ["public.prism.drivers.fake.hwdrv_fake"]
  },


``fail_fast``

* this directive tells Prism whether to stop the test script on the first occurrence of a failed test
* this directive can be overridden by the directive in the ``options`` section of the ``tests`` section - in other
  words, here it has the least priority
* it is recommended ``fail_fast`` be set to `true`.

  * Often tests are interdependent, and if one test fails, it often means other tests will fail that depended on
    that particular function.  What happens then is a cascade of failed tests which might obscure the root failure.
  * If tests are mutually exclusive, it may be advantageous to set ``fail_fast`` to `false`.

``drivers``

* this is a list of ``drivers`` to start when the script it loaded
* the dot notation is specifying a directory path to the python file to read
* every script must have a driver.  A fake driver is available in the case where you don't want/need a real driver,
  for example, in development of code
* See :ref:`prism_drivers:Drivers`

tests
-----

This section has a list of test definitions

* each definition has fields ``module``, ``options``, ``items``
* ``items`` has fields ``id``, ``enable``, ``fail``, and ``args``

Consider the following ``test`` section, which only has ONE test definition in the JSON list.  An example of more than
one test definition will be shown later.

See ``public/prism/scripts/example/prod_v0/tst00xx.py`` for usage.

::

  "tests": [
    {
      "module": "public.prism.scripts.example.prod_v0.tst00xx",
      "options": {
        "fail_fast": false
        // add more key/value as required
      },
      "items": [
        {"id": "TST0xxSETUP",           "enable": true },
        {"id": "TST000_Meas",           "enable": true, "args": {"min": 0, "max": "%%TST000Max"},
                                        "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                                  {"fid": "TST000-1", "msg": "Component banana R1"}] },
        {"id": "TST002_Skip",           "enable": false },
        {"id": "TST0xxTEARDOWN",        "enable": true }
      ]
    }
  ]

``module``

* a dot notation path to the Python code that is associated with this test definition

``options``

* a list of fields assigned values that persist over the execution life of the test item definition
* Prism key words,

  * ``fail_fast`` overrides `fail_fast` in the ``config`` section
  * ``enable`` (defaults to `true`) when set to false, disables all tests in ``items``
  * ``timeout`` seconds allowed for each test item, default 10 seconds
    (`ResultAPI.TESTITEM_TIMEOUT` in `public/prism/api.py`).  A test item that runs longer
    is recorded as `TIMEOUT`, which is a fail.

* add fields here as your application requires
* these ``options`` fields are available programmatically to each test ``items``

  * for example, you could have a global value assigned here that any test ``items`` can access

``items``

* a list of test ``items``, at least one
* the system will execute these tests in order
* `Validate` checks that every ``id`` is a function in `module`, ``args`` and ``options`` are
  objects, and any ``timeout`` is a positive number

  * ``id`` - A unique identifier of the test, which is also the Python (class) function name in `module`.
  * ``enable`` - `true` or `false`, can be omitted if always enabled
  * ``timeout`` - seconds allowed for this test item, overrides ``options`` ``timeout``
  * ``args`` - a list of key/value pairs of any name/value required by your application

    * in the example shown, ``min`` and ``max`` keys are used and assigned values
    * note that ``max`` is using a ``subs`` entry
  * ``fail`` - a list of failure messages to present to the Operator and to store in the result database

    * These failure modes are accessed programmatically by your test code, see TBD
    * ``fid`` - a unique ID for this failure mode
    * ``msg`` - message to show operator
  * any other field your test code needs, for example ``"name": "V5V", "min": 4900, "max": 5100``,
    read in the program as ``ctx.item.min``.  Fields on the item itself are easier to read than
    fields inside ``args``, see :ref:`prism_scripts:Script Design`


Script Design
-------------

A script is a list of tests, with their limits.  Keep it readable by a person who is not a
programmer.

When a test fails in production, and only a limit has to change, a production or test
technician should be able to open the script, find the test, and change the limit.  They
should not need a programmer, and they should not need to read Python.

So,

* everything the test *does* is in the Python program: which BOND pin is read, the divider
  ratio, the order of the steps, the commands sent to the DUT, the settle times
* the script only says *which* tests run and with *what limits*: ``id``, ``enable``,
  ``timeout``, ``min``/``max``, ``fail``, and a few other values a technician may change, such as
  a firmware file name or a hardware version

A good script looks like this,

::

    "items": [
      {"id": "BLT000_SETUP",    "enable": true },
      {"id": "BLT100_voltage",  "enable": true, "name": "V5V",  "min": 4900, "max": 5100 },
      {"id": "BLT100_voltage",  "enable": true, "name": "V3V3", "min": 3200, "max": 3400 },
      {"id": "BLT100_voltage",  "enable": true, "name": "V1V8", "min": 1725, "max": 1875 },

      // disabled: Pogo board schematic error on VIN, see ECO-123
      {"id": "BLT100_voltage",  "enable": false, "name": "VIN", "min": 11800, "max": 12200 },

      {"id": "BLT200_program",  "enable": true, "file": "bootloader-1.2.hex", "timeout": 30 },
      {"id": "BLT300_fw_check", "enable": true, "version": "1.2" },
      {"id": "BLT990_TEARDOWN", "enable": true }
    ]

* each line is one test, and the limits are on the line
* put fields on the item itself (``"min": 4900``), not in ``args``, so the line is easy to read
* a comment says why a test is disabled
* the same test may run more than once, with a different ``name``, when only the limits change,
  ``BLT100_voltage`` above.  Each run must record a different measurement name, here the
  ``name``.  Only the first copy of a repeated ``id`` can be the target of ``_next``.

And its program keeps the details, written out plainly,

::

    # BOND header and pin of each rail, and the Pogo board divider (DUT mV = ADC mV * rdivf)
    VOLTAGE_MAP = {
        "V5V":  {"hdr": 2, "pin": 16, "rdivf": 1.0},
        "V3V3": {"hdr": 3, "pin": 13, "rdivf": 1.0},
        "V1V8": {"hdr": 2, "pin": 14, "rdivf": 1.0},
        "VIN":  {"hdr": 2, "pin": 15, "rdivf": 3.0},
    }

    def BLT100_voltage(self):
        """ Measure a rail voltage, see VOLTAGE_MAP

            {"id": "BLT100_voltage", "enable": true, "name": "V5V", "min": 4900, "max": 5100 },
        """
        ctx = self.item_start()  # always first line of test

        if ctx.item.name not in self.VOLTAGE_MAP:
            self.logger.error(f"invalid voltage name {ctx.item.name}")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        rail = self.VOLTAGE_MAP[ctx.item.name]
        response = self.bond.bond_max_hdr_adc(rail["hdr"], rail["pin"])
        if not response["success"]:
            self.logger.error(response)
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        value = response["result"]["mV"] * rail["rdivf"]
        _, result, bullet = ctx.record.measurement(ctx.item.name, value, ResultAPI.UNIT_MILLIVOLTS,
                                                   min=ctx.item.min, max=ctx.item.max)
        self.log_bullet(bullet)
        self.item_end(result)  # always last line of test

Keep the program simple
^^^^^^^^^^^^^^^^^^^^^^^

Production test code is maintained for the life of the product, often by people who did not
write it.  Code that is easy to follow is better than code that is short.

* write one test item method for each test, with its steps in order in the method
* call the driver (``self.bond.bond_max_hdr_adc(...)``) and ``ctx.record.measurement(...)``
  directly.  Don't wrap them in your own layer of helper classes or functions
* hard code what doesn't change in production, such as BOND pins, divider ratios, DUT commands
  and settle times, in the program, in a table like ``VOLTAGE_MAP`` or in the method
* some repeated code between test items is fine, when it keeps each test item readable on its
  own

Don't,

* put lists of steps or actions in the script, for example
  ``"actions": [{"dac": "J3", "mv": 1000}, {"sleep": 0.05}, {"adc": "J3", "min": 880, ...}]``.
  The script becomes a program, and the test code becomes an interpreter for it
* put expressions, formulas, DUT commands or BOND pin numbers in the script
* use one generic test item for unrelated tests, with the script choosing what it does
* generate the script from another program or repo.  The script in your scripts repo is the one
  that is changed, by hand, when a limit changes



.. [1] ``Scripts`` CAN BE LOCKED DOWN so that a production user cannot change them.  Locking down the Prism is covered TBD.


