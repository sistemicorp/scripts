Accounts
########

Prism has the concept of Users and Roles.

The User logged in and performing tests will be noted in the Result JSON.

You may decide on one global operator User, or a User for each individual.

.. contents::
   :local:


Users
*****

Users should be added to the system, rather than using the Admin account.

Users are identified by a unique email address.

Users are added by an Admin user in Account Management.

A User account must be set `Active` in order to login.

Only one User can be logged in to Prism at a time.

Logging out exits the Script Runner.  If channels are still testing, the tests finish first, then
the Script Runner exits, unless a User logs in before then.  A User logged out for being idle
leaves the Script Runner loaded.


Roles
*****

The following roles are defined,

::

    ADMIN       Administrator, rights to do anything
    OPERATOR    Operator
    CONFIGMAN   Configuration Management
    DEVELOPER   Developer
    SERVERSYNC  ServerSync, causes user to be pushed to all stations


The `ACCOUNT` role is shown in Account Management but is not used, accounts are managed by Admin users.



Admin
=====

The Admin(istrator) role has access to all system functions and menus.

In general it's good practice to have two Users with Admin role.

Operator
========

Prism ONLY

Basic role for operating Prism.

Operator allows the User to scan a traveller and run tests.
The User **cannot** use `Test Configuration` page.

ConfigMan
=========

Prism ONLY

Allows the User to use the `Test Configuration` page, which allows the user to pick which
script to run, and fill in any parameters for the script, and also to be able to create
a Traveller.

Developer
=========

Same as Administrator, except without access to the account management pages.

ServerSync
==========

A User with this setting means their profile is controlled from Lente.  You
may edit the user here on Prism, but if Users are sync'd from Lente, your changes
will be overridden by the profile on Lente the next time there is a sync with Lente.

All changes to this User should be made on Lente.

More on ServerSync TBD (link)

