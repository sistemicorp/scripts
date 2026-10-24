Accounts
########

Lente has the concept of Users and Roles.



.. contents::
   :local:


Users
*****

Users should be added to the system, rather than using the Admin account.

Users need to have a unique username.

Users are added by another user (Admin) who has Account role privileges.

A new User account must be set `Active` in order to login.


Roles
*****

The following roles are defined,

::

    "roles": {
        # Framework Roles
        "ACCOUNT": "Account Admin, Add/Edit Roles & Users",
        "ADMIN":   "Administrator",  # rights to do anything

        # App specific Roles
        "OPERATOR":   "Operator",
        "CONFIGMAN":  "Configuration Management",
        "DEVELOPER":  "Developer",
        "SERVERSYNC": "ServerSync",  # causes user to be pushed to all stations
    },


Active
======

`Active` is not a Role.  It is a separate setting on the Account Management page.

Without `Active` set, the User cannot log into the system.

This allows you to disable a User without deleting their account.

Admin
=====

The Admin(istrator) role has access to all system functions and menus.

In general it's good practice to have two Users with Admin role.

Account
=======

This role provides the User with Account functions, create user, edit user, edit roles.

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

