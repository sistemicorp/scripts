System
######

This section describes system related considerations to building your test system with
Prism and Lente.

.. contents::
   :local:


Architecture
************

This is a typical Sistemi system architecture layout.  More complex systems are possible and
shown later in this section.

.. image:: _static/Screenshot_system_network_01.png

Notes:

* Local wired LAN for Prisms and Lente (local)

  * Wired LANs are more reliable and secure than wireless
  * This LAN should NOT have a connection to the internet

* Prisms

  * only two are shown but there can be as many as needed
  * USB is used to connect to local test jigs and test equipment
  * Test equipment can be shared across test jigs at one Prism station

    * Support for sharing equipment across Prisms is not (yet) supported

  * Sends results to Lente

    * if a Lente is not online, testing can still continue, results will
      be staged for upload to Lente when it comes online

* Lente

  * there should only be ONE per LAN
  * this computer should have a fixed IP address as every Prism is configured
    to look for Lente
  * Lente can be configured to send its results upstream to another Lente
  * Lente can be run in the cloud

    * Local Lente can be configured to send their results upstream to a cloud
      based Lente, thus all you results can end up in one place
    * As noted above, you don't want to have your production LAN connected to the
      internet for security and reliablity reasons, therefore, at some regular
      interval you will remove a local Lente from the production LAN and connect it
      to the internet so it can find the upstream Lente and upload results to it


This is a more sophisticated Sistemi system plan.

.. image:: _static/Screenshot_system_network_03.png

Here two remote factories send their data to a cloud Lente so that Head Office can
monitor all Result data.

Note in Factory 1 there are three production lines.  Line 1 and 2 have their own local
Lente and a monitoring station for viewing the dashboard.  Line 3 does not have a
local Lente and is using the factory Lente.

Results Flow
************

This diagram also shows a possible architecture of a Sistemi system.  In this diagram the focus
is on what happens to DUT results.

This architecture shows how Lente can be stacked
on top of each other.  Each Lente is aggregating more results that come from below it.  In
this case, two factories are supplying results to a central Lente.

.. image:: _static/Screenshot_system_network_02.png

What follows is a description of lables A-F...

* A

  * Result JSON is created at Prism station and saved locally to a `stage` directory
* B

  * At some point, Prism will attempt to contact Lente and send the result
    JSON to it.
  * If Lente is not connected/reachable, the file remains in `stage`.
* C

  * If Lente indicates the file was received successfully, Prism result is moved from
    `stage` to the `bkup` folder.
* D

  * Lente processes the result JSON into its (postgres) database.
* Derr

  * If there was a processing error, the result JSON is stored in `quarantine` folder.
* E

  * result JSON is stored in `bkup` folder if it was processed without error.
* F

  * if this Lente is configured to have an upstream Lente, the result JSON is stored
    in `stage` folder

* At this point, the process B-F repeats itself.

Notes:

#. The Result JSON is backed up at each level.  These backups can be turned off if desired.
#. Any Lente dashboard can be accessed with web browser.  The results that can be seen
   will be that which is local to that Lente.
