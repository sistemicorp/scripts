Scripts
=======

``Scripts``

* define the test sequence and operating modes of the test being run
* are in human readable JSON file format

  * JSON is used so that non-programmers may be able to read/edit [1]_ the script without requiring a
    programming background.  This is useful in development or emergency situations.

* extend JSON a little bit, by allowing comments, any line begining with `#` is a comment.  This allows
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

Obviously, in a production environment, operators are not typically allowed to arbitrarily change values of test
limits or any other setup.  However, in an engineering lab, or new product ramp environment, having an easy method
to change some parameters might be useful.  This feature does not have to be used.

`subs` are also useful for generating :ref:`prism_travellers:Travellers`.

Here is a full example of what `subs` section could look like,

::

  "subs": {
    # Each item here is described by,
    # "key":
    #   "title": "<title>",
    #   "type" : "<str|num>", "widget": "<textinput|select>",
    #   "regex": <"regex"|null|omit>, "default": <default>
    #
    # Rules:
    # 1. key must not have any spaces or special characters
    # 2. regex can be omitted if not applicable
    #
    "Lot": {
      "title": "Lot (format #####)",
      "type" : "str", "widget": "textinput", "regex": "^\\d{5}$", "default": "95035"
    },
    "Loc": {
      "title": "Location",
      "type" : "str", "widget": "select", "choices": ["canada/ontario/milton", "us/newyork/bufalo"]
    },
    "TST000Max": {
      "title": "TST000 Max Attenuation (db)",
      "type" : "num", "widget": "select", "choices": [9, 10, 11]
    }
  },

``key``

* the name of the variable to be replaced somewhere else in the script, for example, the variable could be in
  the ``info`` section

  * the variable in other sections, would be named ``"%%key"``
  * the variable would be listed with double quotes, regardless of the variable type
* ``key`` should not have any special characters in it, else bad things happen

``title``

* this is the title of the field to be presented to the Operator in the Test Config view
* if there is a specific format of the variable expected, that should be indicated in the ``title``

``type``

* indicates type of variable that is ultimately required in the final JSON version of the script
* string (`str`) and number (`num`) (covers float and ints) are the only options

``widget``

* the type of GUI widget to present to the Operator in the Test Config view
* `textinput` is a generic text input box, which will be populated by the ``default`` field
* `select` is a drop down selection menu

``regex``

* used only for `textinput` ``widget``
* used to validate the Operator entered correct information
* this is optional field

``default``

* sets the default value for `textinput` ``widget``
* optional

info
----

This section is a list of fields that correspond to fields that exist in the backend database and are typically
used for database searches.

You cannot add or delete fields from this section.  If there are missing fields, an error will occur downstream as the
result record is check to have these fields.  New fields can be added, but that requires a request to customize
the backend database.  See TBD.

Note that the example here, two fields are using the `subs` section to get their values from the Operator
in the Test Config view.

::

  "info": {
    "product": "widget_1",
    "bom": "B00012-001",
    # list fields present user choice or fill in
    "lot": "%%Lot",
    "location": "%%Loc"
  },

``product``, ``bom``, ``lot``, ``location`` are fields that you define a meaning specific to your operation.

Defining rules and a naming convention for these fields will help you later when you need to make database searches
for specific sets of results.  This is important.

config
------

This section sets required variables that Prism uses to drive the test script.

::

  "config": {
    "result": "public.prism.result.ResultBaseV1",
    "fail_fast": false,
    "drivers": ["public.prism.drivers.fake.fake"]
  },

``result``

* sets the result record type
* this is related to the back end database processing
* the dot notation is specifying a directory path to the python file to read
* its possible to extend the backend database to incorporate new fields for your application. See TBD

``fail_fast``

* this directive tells Prism whether to stop the test script on the first occurrance of a failed test
* this directive can be overridden by the directive in the ``options`` section of the ``tests`` section - in other
  words, here it has the least priority

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

::

  "tests": [
    {
      "module": "public.prism.scripts.prod_v0.tst00xx",
      "options": {
        "fail_fast": false
        # add more key/value as required
      },
      "items": [
        {"id": "TST0xxSETUP",           "enable": true },
        {"id": "TST000_Meas",           "enable": true, "args": {"min": 0, "max": "%%TST000Max"},
                                        "fail": [ {"fid": "TST000-0", "msg": "Component apple R1"},
                                                  {"fid": "TST000-1", "msg": "Component banana R1"}] },
        {"id": "TST001_Skip",           "enable": false },
        {"id": "TST0xxTRDN",            "enable": true }
      ]
    }
  ]

``module``

* a dot notation path to the python code that is associated with this test definition

``options``

* a list of fields assigned values that persist over the execution life of the test definition
* only ``fail_fast`` is used by the system, which overrides the value used in the ``config`` section
* you may add fields here as your application requires
* these ``options`` fields are available programmatically to each test ``items``

  * for example, you could have a global value assigned here that any test ``items`` can access

``items``

* a list of test ``items``
* the system will execute these tests in order

  * ``id`` - A unique identifier of the test
  * ``enable`` - `true` or `false`, can be omitted if always enabled
  * ``args`` - a list of key/value pairs of any name/value required by your application

    * in the example shown, ``min`` and ``max`` keys are used and assigned values
    * note that ``max`` is using a ``subs`` entry
  * ``fail`` - a list of failure messages to present to the Operator and to store in the result database

    * These failure modes are accessed programmatically by your test code, see TBD
    * ``fid`` - a unique ID for this failure mode
    * ``msg`` - message to show operator



.. [1] ``Scripts`` CAN BE LOCKED DOWN so that a production user cannot change them.  Locking down the Prism is covered TBD.


