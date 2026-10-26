Traceability
############

Traceability is being able to answer, for any unit, what was tested, when, where, how, and with
what result.  For example, a unit comes back from the field: which tests did it pass, which
firmware was loaded, which lot was it built in, and which version of the test was used?

Prism records some of this for you.  The rest your scripts and test code must record.
Plan it before production starts, because results that were not recorded can't be added later.

.. contents::
   :local:


Recorded Automatically
**********************

Every result has these fields in the Lente `record` table (see :doc:`Database <_database>`),

* `ruid`, a unique id for this result
* `info_product`, `info_bom`, `info_lot`, `info_location` and `info_config`, from the script
  :ref:`prism_scripts:info` section, often filled in from :ref:`prism_scripts:subs` or a
  :doc:`Traveller <prism_travellers>`
* `meta_script`, the path of the script that ran, for example
  `public/prism/scripts/mycompany/P001/P00100_T0100_SmokeTests.scr`
* `meta_git_public`, the version of your scripts repo (`public/VERSION`), see
  :ref:`_development:Create a Tag`
* `meta_git_prism`, the version of Prism
* `meta_uuid_getnode`, an id of the Prism computer, derived from its network interface
* `meta_channel`, the test channel (jig) that ran the test
* `meta_result`, `meta_start`, `meta_end` and `_duration`

Each test item and measurement is stored with its full name, which includes the module path and
the item `id`, for example `mycompany.P001.P00100_T0100_SmokeTests.TST0200_measVDD.vdd`.

The result JSON file also has the operator and the station IP address.  These are kept in the
result file backups (`public/result/.../bkup`), but they are not database columns.

Because `meta_git_public` is recorded, every file in your scripts repo is traceable: scripts,
test code, limits, and firmware images stored with the scripts (for example in an `assets`
folder).  Use the version to find the exact files with `git checkout`.


What You Record
***************

Serial Numbers and Unit Ids
===========================

Save the unit's serial number (or other unique id) in `key0`.  The Lente Throughput & Yield chart
uses `product` + `key0` to count each unit once,

::

    ctx.record.add_key("sn", serial_number, slot=0)

There are 5 key slots, `key0` to `key4`.  Each is an indexed database column, so searches on keys
are fast.  Use the other slots for ids you will search on, such as a microcontroller unique id, a
MAC address, or the serial number of a sub-assembly.

* A key is stored as `<name>:<value>`, for example `sn:A12345`.  Keep the whole string within
  64 characters, the size of the database column.  A longer key is not saved, `add_key()`
  returns `False` and logs an error.
* Use the same slot for the same id in every script of a product, and in every stage, see
  `Key Slot Plan` below.
* The serial number can be read from the DUT, scanned from a label (with `input_textbox()`),
  or created and programmed by the test.  When the test creates it, also print or program it
  onto the unit, otherwise the result can't be matched to the unit later.

Key Slot Plan
=============

Most products have more than one test stage.  A common plan is a Board Level Test (BLT) of the
PCBA, and a Final Assembly Test (FAT) of the assembled product, see
:ref:`_prodplan:Planning Your Test Stages`.  Use each key slot for the same id in every stage.
For example, when the microcontroller unique id identifies the unit, BLT saves it in `key0`, and
FAT saves it in `key0` too.  One query on `key0` then finds the BLT and FAT results of a unit,
and the Lente yield chart counts the unit once.

Do the same across products.  When every product uses `key0` for the unit id and `key1` for the
MAC address, the same queries, reports and MES integration work for all of them.

Make a table of the key slot usage for all your products, or for each product family, before
writing the scripts, and keep it with your scripts (for example in a README),

+-------+--------------------------------+-------------+-----+-----+-------------------------+
| Slot  | Id                             | Name        | BLT | FAT | Products                |
+=======+================================+=============+=====+=====+=========================+
| key0  | unit id, MCU unique id         | `sn`        | Y   | Y   | all                     |
+-------+--------------------------------+-------------+-----+-----+-------------------------+
| key1  | MAC address                    | `mac`       | Y   | Y   | products with a radio   |
+-------+--------------------------------+-------------+-----+-----+-------------------------+
| key2  | label serial number            | `label`     | \-  | Y   | all                     |
+-------+--------------------------------+-------------+-----+-----+-------------------------+
| key3  | sub-assembly serial number     | `sub_sn`    | \-  | Y   | family A                |
+-------+--------------------------------+-------------+-----+-----+-------------------------+
| key4  | reserved                       |             |     |     |                         |
+-------+--------------------------------+-------------+-----+-----+-------------------------+

* `key0` is the unit id in every product and every stage, it must be known at the first stage.
  An id that is only known later, like a label printed at FAT, gets its own slot, left empty in
  the earlier stages.
* Never use a slot for a different id in another stage or product, leave it empty instead.
  Reserve the last slots for product specific ids.
* Use the same key name for the same id everywhere, for example always `sn`, not `sn` in one
  script and `serial` in another.
* Put the table in your code as constants in a common module, used by every script,

  ::

      DBKEY_SERIAL_NUM = 0
      DBKEY_MAC = 1
      DBKEY_LABEL_SN = 2

      ctx.record.add_key("sn", mcu_uid, slot=DBKEY_SERIAL_NUM)

Firmware and Hardware Versions
==============================

Record versions read from the DUT as string measurements.  A string measurement always passes,
and is stored with the test item,

::

    success, _result, _bullet = ctx.record.measurement("fw_ver", fw_ver, ResultAPI.UNIT_STRING)

* Record the version the DUT reports, after programming, not only the file that was programmed.
* Record the bootloader, application and any co-processor versions separately.
* A hardware revision that the test writes to the DUT (for example from a `select` sub) should
  also be recorded as a measurement.
* String values are stored in a 128 character column.

Test Equipment
==============

To trace a fault to a jig or instrument, record the serial number of each piece of test
equipment as a string measurement in the setup item.  For example the scope, power supply and
programmer serial numbers, and the jig controller's id.  A unit tested on an instrument later
found out of calibration can then be found in the results.

A string measurement has no limits, it always passes and is only recorded.  Drivers often
return a `unique_id` from `discover_channels()` for this,

::

    drivers = self.shared_state.get_drivers(self.chan, type="AGILENT_DSO_USB_1")
    dso_sn = drivers[0]["obj"]["unique_id"]
    success, _result, _bullet = ctx.record.measurement("dso_sn", dso_sn, ResultAPI.UNIT_STRING)

* Record every instrument the test uses, including shared ones, in every result.
* For a shared instrument with several inputs, also record the input used by the channel.
* Use the same measurement name for the same instrument in all your scripts, so one query
  finds them all.
* If a driver does not give a `unique_id`, read the serial number from the instrument, for
  example its `*IDN?` reply.

Lots
====

`info_lot` (16 characters) is the lot or work order.  It usually comes from a sub, so the operator
enters it or a Traveller sets it.  Use a `regex` on the sub to enforce your lot format, see
:ref:`prism_scripts:subs`.  The Lente Throughput & Yield chart can group results by lot.

Test Versions
=============

The script records which test ran (`meta_script`), and the scripts version records the exact
files.  Decide how a change shows up in your searches,

* Changing a limit or a test item in place keeps the script name.  Searches by `meta_script`
  then mix results from both versions.  Use `meta_git_public` or the date to separate them.
* Making a new script version (for example `P00100_T0101_SmokeTests.scr`) keeps the versions
  separate in every search.  This is the better choice for changes made by an ECO.
* Measurement names include the module and item names.  Renaming either starts a new series
  in the database, which breaks trend charts and SQL queries across the change.

See :ref:`_prodplan:Naming Proposal` for a naming scheme that puts the stage and version in the
names.


Example Queries
***************

All results for one unit, in time order,

::

    select r.id, r.info_product, r.meta_script, r.meta_result, r.meta_start, r.meta_git_public
    from record r
    where r.key0 = 'sn:A12345'
    order by r.meta_start

The firmware version recorded for each unit of a lot,

::

    select r.key0, m.value, r.meta_start
    from measurement m join record r on m.record_id = r.id
    where m.name = 'mycompany.P001.P00100_T0100_SmokeTests.TST0100_connect.fw_ver'
          and r.info_lot = 'L2026-07'
    order by r.meta_start

See :ref:`_database:SQL Queries` for more queries and tools.


Checklist
*********

Before production, decide,

#. which id identifies a unit (`key0`), and where it comes from
#. which other ids are keys, and their slot numbers, in a key slot table shared by all your
   products or product family, see `Key Slot Plan`
#. which versions are recorded (firmware, bootloader, hardware revision)
#. which test equipment serial numbers are recorded, and their measurement names
#. the lot format, and who enters it (operator, Traveller)
#. how scripts and test items are named and versioned
#. how long results are kept, and where (Lente, upstream Lente, backups)
