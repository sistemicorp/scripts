Security
########

Production security is important.  Sistemi Lente/Prism have features and suggestions to improve security.

.. contents::
   :local:


Lente
=====

It is assumed that Lente are "physically secure", which means physical access to the computers is
restricted in some way, for example, locked in a secure room.

The following are further suggestions to improve security,

* encrypt the hard disk by the OS
* strong admin password
* use Sistemi Account Roles for users


Prism
=====

Prism stations are considered insecure.  Presumably anyone on the production floor can access a Prism.
Often login names and passwords are common to a group of people, or shared amoung them to access the computer.

The following are further suggestions to improve security,

* encrypt the hard disk by the OS
* strong admin password
* enable Sistemi Manifest locking, see :ref:`prism_manifest:Manifest`
* enable result encryption
* regularly purge the backups from the disk, (or disable backups, not recommended)
* use Lente Account Roles for users


Postgres DB
===========

* Change the default password!

  * See the pstgres starter script `public\postg.sh --help`
  * Also remember to use the same password in the Lente config json, `public\lente.json`
  * `public\lente.json` is not deployed to Prism by Lente
