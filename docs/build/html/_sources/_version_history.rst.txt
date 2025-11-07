###############
Version History
###############

Version history and migration guide.  For each release changes may affect Prism, or Lente, or both.
A Migration Guide section is provided if any changes on the client side are required.

Some features are implemented in a previous version as experimental, and when that is the case it
is mentioned.  Note that not all cited versions are released as Docker images.



*********
Ver 0.8.x
*********

This is the first version where this type of information will be tracked.

The major feature released in `0.8` is support for OPCUA, which is a Manufacturing Execution System (MES)
to facilitate the monitoring of the Prism/Lente deployment by other OPCUA tools.

In addition new features have been added to make it easier to debug deployment issues, get logs, and
otherwise monitor the system.


Prism & Lente
-------------

* [BUGFIX] Fix/improve getting self IP address (implemented in 0.7.52)
* Support for UPCUA, see `OPCUA <_mes_integration.html#_Manufacturing>`__


Prism
-----

* Test portal layout supports up to 8 test channels (jigs per Prism PC) (implemented in 0.7.43)
* Index page shows time and date (implemented in 0.7.56)
* Auto config test on startup, see :ref:`settings.json <deploy-settings-file>` (implemented in 0.7.64)
* Test Portal layout includes script Info section in title bar
* Health Checks, see :ref:`Health Checks <health-checks>`
* [BUGFIX] Text entry box entry was incorrect when user timeout occurred (fixed in 0.7.73)


Lente
-----

* Station Management portal can remotely,

  * request Prism Log (implemented in 0.7.48)
  * reboot Prism computer (implemented in 0.7.66)


Migration Guide
---------------

* None
