Deployment
##########

Prism/Lente allows for various deployment strategies, and some diagrams
are shown `here <_system.html#_system_arch>`__.

Prism deployment is straight foward.

Lente deployment depends on your dashboarding and Prism station management strategy.
A Lente station can manage Prism stations directly below it, in the connection
hierarchy.

.. index:: Settings

Settings File
*************

Each Lente/Prism station instillation will have a local settings file, as
shown below and documented inline,

::

    // This file is NOT propagated by Lente to Prism stations.
    // For each Prism/Lente install, this file should be modified as required.
    {
      // turn on demo mode.  Creates test user accounts, ...
      // remove line, or set to false to disable demo mode
      "demo": true,

      // How often to check for Lente connection
      "result_server_retry_timer_sec": 60,

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

      // ------------------------------------------------------------------
      // Below are only used by Lente and can be removed for Prism stations

      // Enter IP Address:port, example "http://35.123.432.190:6595"
      // Use null to disable upstream sending.
      "result_server_url": null,

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



Prism/Lente Docker Images
*************************

On computers that are deployed, you will want the Docker images to run (and restart)
every time the computer boots up.

The helper scripts to start Prism/Lente (see :ref:`Helpers <system-helper-docker>`),
have a `restart=always` option that should be used.  Once that is done, Prism/Lente will forever
startup.
