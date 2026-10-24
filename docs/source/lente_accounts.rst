Accounts
########

Lente has the concept of Users and Roles.



.. contents::
   :local:


Users
*****

Users should be added to the system, rather than using the Admin account.

Users are identified by a unique email address.

Users are added by an Admin user in Account Management.

A new User account must be set `Active` in order to login.


Roles
*****

The following roles are defined,

::

    ADMIN       Administrator, rights to do anything
    OPERATOR    Operator
    CONFIGMAN   Configuration Management
    DEVELOPER   Developer
    SERVERSYNC  ServerSync, causes user to be pushed to all stations
    DASHBOARD   Dashboard, read-only results viewer (planned)


The `ACCOUNT` role is shown in Account Management but is not used, accounts are managed by Admin users.


Active
======

`Active` is not a Role.  It is a separate setting on the Account Management page.

Without `Active` set, the User cannot log into the system.

This allows you to disable a User without deleting their account.

Admin
=====

The Admin(istrator) role has access to all system functions and menus.

In general it's good practice to have two Users with Admin role.

Operator
========

PRISM ONLY

Basic role for operating Prism.

Operator allows the User to scan a traveller and run tests.
The User **cannot** use `Test Configuration` page.

ConfigMan
=========

PRISM ONLY

Allows the User to use the `Test Configuration` page, which allows the user to pick which
script to run, and fill in any parameters for the script, and also to be able to create
a Traveller.

Developer
=========

Same as Administrator, except without access to the account management pages.

ServerSync
==========

A User with this setting means their profile is controlled from Lente.  You
may edit the user on a Prism station, but if Users are sync'd from Lente, your changes
will be overridden by the profile on Lente.

All changes to this User should be made on Lente.

More on ServerSync TBD (link)

