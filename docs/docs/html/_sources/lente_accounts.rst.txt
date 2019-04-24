Accounts
########

Lente has the concept of Users and Roles.



.. contents::
   :local:


Users
*****

Users should be added to the system, rather than using the Admin account.

Users need to have unique username.

Users are added by another user (Admin) who has Account role privileges.

A new User account must have the role `Enabled` in order to login.


Roles
*****

The following roles are defined,

::

    "roles": {
        # Framework Roles
        "ENABLED": "Enabled",
        "ACCOUNT": "Account",
        "ADMIN":   "Administrator",  # rights to do anything

        # App specific Roles
        "OPERATOR":   "Operator",
        "CONFIGMAN":  "Config Management",
        "DEVELOPER":  "Developer",
        "SERVERSYNC": "ServerSync",  # causes user to be pushed to all stations
    },


Enabled
=======

Without this role, the User cannot log into the system.  When a User is created,
this role is NOT set.  After a User is created, you must access the Roles menu
and add `Enabled` to the User for them to be able to login.

This allows you to disable a User without deleting their account.

Admin
=====

The Admin(istrator) role has access to all system functions and menus.

In general its good practice to have two Users with Admin role.

Account
=======

This role provides the User with Account functions, create user, edit user, edit roles.

Operator
========

PRISM ONLY

Basic role for operating Prism.

Operator allows the User to scan a traveller and run tests.
The User **cannot** use `Test Config` menu.

ConfigMan
=========

PRISM ONLY

Allows the User to use the `Test Config` menu, which allows the user to pick which
script to run, and fill in any parameters for the script, and also to be able to create
a Traveller.

Developer
=========

Currently this has no purpose.

ServerSync
==========

A User with this setting means their profile is controlled from Lente.  You
may edit the user here on Prism, but if Users are sync'd from Lente, your changes
will be overridden by the profile on Lente.

All changes to this User should be made on Lente.

More on ServerSync TBD (link)

