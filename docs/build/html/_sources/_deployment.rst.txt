Deployment
##########

Prism/Lente allows for various deployment strategies, and some diagrams
are shown `here <_system.html#_system_arch>`__.

Prism deployment is straight foward.

Lente deployment depends on your dashboarding and Prism station management strategy.
A Lente station can manage Prism stations directly below it, in the connection
hierarchy.

.. index:: Settings

.. _deployment-ubuntu-filesystem:

Ubuntu File System and Users
****************************

* Install Ubuntu onto the computers and enable file system encryption

  * Note that enabling encryption will require a password to be entered for
    the computer to boot up.  Consider this for remote sites.

    * Alternatively the home directory of the Prism/Lente account could be encrypted,
      which is where the Prism/Lente files will be hosted.  The benefit of this
      approach is a password is not required to boot the computer.  And the Prism/Lente
      files are still protected.

* Set up at least two user accounts

  * Operator account,

    * should have very limited access
    * able to run Chrome


  * Prism/Lente setup account

    * hosts the Prism/Lente files


Installing Prism/Lente Stations
*******************************

For Prism/Lente stations, follow the Full "Demo" instructions, but note the following
changes,

* Prism

  * install "full" per :ref:`Prism Full Install <prism-full-install>`
  * git clone your "scripts" repo instead of the demo repo
  * modify `public/settings.json` to suite the deployment

    * see `settings.json` details below
  * use the Prism helper script at `public/prism.sh` to start Prism,

    * in order for Prism to run every time the computer is turned on use option `restart=always`

* Lente

  * install "full" per :ref:`Lente Full Install <lente-full-install>` HOWEVER,
    change the git source to be your repo.
  * Use Lente Station management to push your repo to downstream Prism (and/or
    Lente) computers.
  * use the helper script `public/lente.sh` and option `restart=always` so that
    Lente will automatically start on every computer boot up.


.. _deploy-settings-file:


Settings.JSON File
******************

Each Lente/Prism station instillation will have a local settings file, as
shown below and documented inline,

::

    // This file is NOT propagated by Lente to Prism stations.
    // For each Prism/Lente install, this file should be modified as required.
    {
      // turn on demo mode.  Creates test user accounts, ...
      // remove line, or set to false to disable demo mode
      "demo": true,

      // Result JSON file encryption
      // - a valid license file is required to encrypt results
      // - passwrd must be |<-  16  long  ->|
      "result_encrypt_pw": "mysecretkey01234",
      "result_encrypt": false,

      // By default results that are sent to Lente are backed up
      // locally, to disable this backup uncomment
      //"result_bkup_dir": null,

      // Result JSON files be backed up as encrypted, <true|false>,
      // If the results were not encrypted by Prism, they won't be ecrypted by Lente
      "results_bkup_encrypted": false,

      // Use https secure transport, requires public/cert/key.pem files
      // For Lente & Prism stations, all must be configured the same
      "use_https": false,

      // Prism/Lente internal connection password
      "prism_lente_pw": "mysecret",

      // Enter IP Address:port, example "http://35.123.432.190:6595"
      // Use null to disable upstream sending.
      "result_server_url": null,

      // ------------------------------------------------------------------
      // Below are only used by Lente and can be removed for Prism stations

      "postgres": {
        "resultbasekeysv1": {
          // !! Change "pw" to a real password for a real deployment,
          // !! This user/pw must match your postgres deployment too,
          "user": "postgres",
          "pw": "qwerty",

          // ip address of the postgres database, use `127.0.0.1` if locahost
          "ip": "127.0.0.1"
        }
      }
    }


For Prism stations, a number of items can be removed per the comments, which will make
the file smaller and easier to manage.

* see :ref:`HTTPS <https>` for creating necessary files if using HTTPS feature


As noted in the comments of the settings file, this file is NOT deployed as part of the
scripts synchronization that Lente does through station management.  The settings file is
to be configured for each computer (Lente or Prism) in the deployment.


Prism/Lente Docker Images
*************************

On computers that are deployed, you will want the Docker images to run (and restart)
every time the computer boots up.

The helper scripts to start Prism/Lente (see :ref:`Helpers <system-helper-docker>`),
have a `restart=always` option that should be used.  Once that is done, Prism/Lente will forever
startup.
