Results Database
################

All things databse related.

.. contents::
   :local:


Database Schema
***************

This diagram shows the dB schema and relationships,

.. image:: static/db_schema_01.png

All of the tables are connected together thru the (foriegn key) `record_id`.


record
======
This represents the instance of a test that ran.  Its a top level record that captures
all the conditions of the test when it ran.

The `info_*` section are fields that are set via the Prism Configuration and are related
to the the `info` section of the script.

The `key#` items are indexed keys that your script can set via `add_key()` api.  These keys should be used
as high level identifiers for making SQL queries.  For example, a product serial number
should probably be a key so that you can find the test record for a product serial number.
Typically these `key#` fields are not known until the test is run and retrieves the information.
For example, a key might be a microcontroller UID (MAC address) which is read at test time.

test_item
=========
For each test `record` there will multiple `test_items` as directed by the script.

Note that the name of the test item should be treated like a serial number and should be "formatted".
See naming proposals.

measurement
===========
For each `test_item` there may be multiple `measurements`.  measurement has two foreign keys, `record`
and `test_item`.

Note that the name of the measurement should be treated like a serial number and should be "formatted".
See naming proposals.  Prism `measurement()` API enforces good naming.

blob
====
For each `test_item` there may be multiple JSON `blob`.  blob has two foreign keys, `record`
and `test_item`.

log
===
A large string that represents the `log_bullet()` messages that appear in the GUI.  This
represents what was shown to the operator during the test.

jsonb
=====
*NOTE this feature is experimental.*

A custom JSON object that will be stored as a `jsonb` object which Postgres treats special
(see Postgres documentation).

Using `jsonb` is provided to allow one to essentially create their own "tables" in JSON.


SQL Queries
***********

Lente provides only basic test result monitoring or "dashboarding".  Because all Prism results end up in
an SQL database, adding dashboarding relevant for your business is easy.  The difficult part is choosing
among the many 3rd party options.

There are two classes of tools, those for developing SQL scripts, exploring the database schema, and those for
creating dashboards.

An example of a dashboarding tool is,

* `Grafana <https://grafana.com/>`_

An example of an SQL Tool is,

* `dBeaver <https://dbeaver.io/>`_

Note that the Lente Details console page has an SQL window at the bottom which shows the SQL query that
Lente is using, and may provide a starting point for your own queries.


Stats For All Measurements
==========================

An SQL script that will list all the measurements for a given set of records that meet the filtering criteria,

::

    -- Measurement Stats for all test measurements
    select m.name,
           count(m.value) count_val,
           AVG(CAST(m.value as Float)) avg_val,
           stddev(CAST(m.value as Float)) std_val,
           min(CAST(m.value as Float)) min_val,
           max(CAST(m.value as Float)) max_val
    from measurement m join record on m.record_id = record.id
    where m.unit not in ('STR', 'Boolean', 'None')
           -- add/remove filters as required, see schema for fields
           AND record.info_product = 'myproduct'
           AND record.info_bom = 'mybom'
           AND record.info_lot = 'mylot'
           AND record.info_location = 'mylocation'
           AND record.meta_result = 'PASS'
           AND record.meta_script = 'public/prism/scripts/mystage/myname.scr'
           AND record.meta_start >= '2023-11-10'
           AND record.meta_start <= '2023-11-15'
           group by m.name
           order by m.name


Test Item Duration
==================

An SQL script that will list all the stats for Test Item durations (how long did the test take),

::

    -- Test Time for all test measurements
    select ti.name,
           count(ti._duration) count_val,
           AVG(CAST(ti._duration as Float)) avg_val,
           stddev(CAST(ti._duration as Float)) std_val,
           min(CAST(ti._duration as Float)) min_val,
           max(CAST(ti._duration as Float)) max_val
    from test_item ti join record on ti.record_id = record.id
    where record.info_product = 'myproduct'
           -- add/remove filters as required, see schema for fields
           AND record.info_bom = 'mybom'
           AND record.info_lot = 'mylot'
           AND record.info_location = 'mylocation'
           AND record.meta_result = 'PASS'
           AND record.meta_script = 'public/prism/scripts/mystage/myname.scr'
           AND record.meta_start >= '2023-11-10'
           AND record.meta_start <= '2023-11-15'
           and CAST(ti._duration as Float) > 0.2
           group by ti.name
           order by ti.name
