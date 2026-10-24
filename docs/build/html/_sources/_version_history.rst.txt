###############
Version History
###############

Version history and migration guide.  For each release changes may affect Prism, or Lente, or both.
A Migration Guide section is provided if any changes on the client side are required.

Some features are implemented in a previous version as experimental, and when that is the case it
is mentioned.  Note that not all cited versions are released as Docker images.

Prism/Lente version should match major/minor version.  For example Prism/Lente version should match `0.8.x`,
where `x` can/will be different.  Do not use Prism 0.8.x with Lente 0.7.x, or vice versa.


*********
Ver 0.9.x
*********

The major change in `0.9` is a new user interface for both Prism and Lente, built on NiceGUI,
replacing the Flask/Bokeh interface.  See :doc:`Prism <prism_screenshots>` and :doc:`Lente <lente_screenshots>`
screenshots.

* Lente Results Analytics page, with yield, pareto and test runtime charts
* Lente Station Manager can automatically sync scripts to stations, `auto_sync_scripts`
* Lente Station Manager `git pull` button, see `public/git_pull_watcher.sh`
* Script sync sends all of `public/prism`, and the station replaces its whole `public/prism`
  folder, so files removed on Lente are also removed on the stations
* Script sync size limit and exclusions, see :ref:`Script Sync Exclusions <_security:Script Sync Exclusions>`
* DASHBOARD role (planned: read-only results viewer)


Migration Guide
---------------

* `prism_lente_pw` (and `lente_lente_pw`) must now be set in `settings.json`, otherwise
  all station requests are refused.  See :ref:`settings.json <deploy-settings-file>`.
* `manifest_pw` is no longer used and can be removed from `settings.json`.
* Vendor programming tools (Nordic `nrfjprog`, ST `STM32CubeProgrammer`) are no longer included
  in `public/prism/drivers`.  They will be installed on the host computer.
* Demo `@here.com` users are not removed when demo is turned off, see
  :ref:`Demo Users and the First Admin <first-admin>`.


*********
Ver 0.8.x
*********

This is the first version where this type of information will be tracked.

The major features released in `0.8` are,

* support for OPCUA, which is a Manufacturing Execution System (MES)
  to facilitate the monitoring of the Prism/Lente deployment by other OPCUA tools.
* Docker Image OS uses Ubuntu 24.04.
* Update to Python 3.12 for development and Docker Image.

In addition new features have been added to make it easier to debug deployment issues, get logs, and
otherwise monitor the system.


Prism
-----

0.8.37
~~~~~~

* [BUGFIX] Fix/improve getting self IP address (implemented in 0.7.52)
* Support for OPC UA, see :ref:`OPCUA <mes-integration>`
* Test portal layout supports up to 8 test channels (jigs per Prism PC) (implemented in 0.7.43)
* Index page shows time and date (implemented in 0.7.56)
* Auto config test on startup, see :ref:`settings.json <deploy-settings-file>` (implemented in 0.7.64)
* Test Portal layout includes script Info section in title bar
* Health Checks, see :ref:`Health Checks <health-checks>`
* [BUGFIX] Text entry box entry was incorrect when user timeout occurred (fixed in 0.7.73)


Lente
-----

0.8.21
~~~~~~

* [BUGFIX] Fix/improve getting self IP address
* Support for OPC UA, see :ref:`OPCUA <mes-integration>`
* Station Management portal can remotely,

  * request Prism Log (implemented in 0.7.48)
  * reboot Prism computer (implemented in 0.7.66)


Migration Guide
---------------

* None


*********
Ver 0.7.x
*********

Prism/Lente version 0.7.x are deprecated and no longer supported.  However the images are still available on Docker Hub
and can be used via the helper scripts `prism.sh/lente.sh`.


Prism
-----

0.7.40
~~~~~~

* the last build


Lente
-----

0.7.28
~~~~~~

* the last build