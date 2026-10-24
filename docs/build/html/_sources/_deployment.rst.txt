Deployment
##########

Prism/Lente allows for various deployment strategies, and some diagrams
are shown :ref:`here <system_arch>`.

Lente deployment depends on your dashboarding and Prism station management strategy.
A Lente station can manage Prism stations directly below it, in the connection
hierarchy.

A deployment plan should be discussed with a Sistemi support engineer.


.. index:: Settings


System Requirements
*******************

* Computer Minimum

  * x86, 8GB RAM, 2+ Cores
  * 256GB Storage
  * USB ports
  * Display 1900x1280
  * Laptop is recommended because it has battery backup, otherwise a UPS is recommended.

* Host OS

  * Ubuntu 24.04



.. _deployment-ubuntu-filesystem:

Ubuntu File System and Users
****************************

* Install Ubuntu onto the computers
* OPTIONAL: enable file system encryption

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


  * Prism/Lente Admin account

    * hosts the Prism/Lente files


Installing Prism/Lente Stations
*******************************

Set up Lente first, then add the Prism stations.  A Prism station does not need a copy of
your scripts repo, it gets the scripts, drivers and license from its Lente.

.. _deployment-new-prism:

* Prism

  * Install Ubuntu and Docker per :ref:`Prism Full Install <prism-full-install>` (Requirements
    section only).  Git and a clone of the scripts repo are not needed.
  * Make a folder for the Prism files, this becomes Prism's `public` folder::

        mkdir -p ~/prism/public
        cd ~/prism/public

  * Get the Prism helper script `prism.sh` from Lente.  This works on networks without internet
    access, replace `192.168.0.10` with the IP address of your Lente::

        curl -O http://192.168.0.10:6595/prism.sh
        chmod +x prism.sh

  * Copy in the `settings.json` for this station, see `settings.json` details below.
    The file must be supplied, Prism does not start without it.

    * `site_key` and `prism_lente_pw` must be the same as on Lente.

  * Get the Prism Docker image (needs internet access, or load the image from a file with
    `docker load`)::

        docker pull sistemicorp/prismng

  * Start Prism.  The script must be run from the `public` folder, because that folder is
    mounted into the Prism container.  The `--server` flag is required, it is the IP address of
    the Lente this Prism reports to.  Use `--restart=always` so Prism starts every time the
    computer is turned on::

        ./prism.sh --server=192.168.0.10 --restart=always start

  * On its first start Prism downloads the scripts package from Lente, installs it into
    `public/prism`, and then starts as usual.  After that Lente keeps the scripts up to date,
    see `auto_sync_scripts` below.

    * If the download fails, Prism logs the reason in `public/log/prism.log`, also shown by
      `docker logs prism`, and exits.  Usual causes are Lente not reachable, a `prism_lente_pw`
      that does not match Lente (status code 403), or a `site_key` that does not match Lente
      (decrypt failed).  Fix `settings.json` and start Prism again.

  * For a Prism without a Lente, git clone your scripts repo and start Prism from its
    `public` folder with `--server=none`, as in the :ref:`Prism Full Install <prism-full-install>`.

* Lente

  * install "full" per :ref:`Lente Full Install <lente-full-install>` HOWEVER,
    change the git source to be your repo.
  * Use Lente Station management to push your repo to downstream Prism (and/or
    Lente) computers.
  * Lente serves `public/prism.sh` at `http://<lente>:6595/prism.sh`, for setting up new Prism
    stations.
  * use the helper script `public/lente.sh`, run from the `public` folder, with option
    `--restart=always` so that Lente will automatically start on every computer boot up::

        cd ~/git/scripts/public
        ./lente.sh --restart=always start

  * the Postgres container must also be set to restart, see :ref:`Postgres <lente-demo-postgres>`.
  * Optional: to let an admin update the Lente scripts from GitHub with the Station Manager
    `git pull` button, run `public/git_pull_watcher.sh` on the Lente host.
    The setup steps (deploy key, systemd service) are at the top of that script.


.. _deploy-settings-file:


Settings.JSON File
******************

* Each Lente/Prism computer will have its own (local) settings file.

  * When setting up a new Prism/Lente instance, this file must be manually edited or
    copied from a reference source to reflect this instances configuration.
  * In practice, most Prism computers can use the same file, and therefore the file
    should be stored in a separate place and used as a source when new Prism computers
    are added to the deployment.
  * The `settings.json` in your scripts repo should only be an example.  Do not commit the
    real deployment passwords to your repo.


* This file is NOT propagated within the deployment by Lente.
* This file contains passwords in plain text so it should be handled appropriately.
* `prism_lente_pw` (and `lente_lente_pw` for Lente to Lente) must be set, and must be the same on
  every computer in the deployment.  If they are not set, Prism/Lente refuse all station requests
  (pings, results, script and user syncs).
* `site_key` must be set, and must be the same on every computer in the deployment.  It encrypts
  the scripts package, the manifest, travellers and results.  The demo value only works with
  `"demo": true`.  Generate a key with `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`.
* To check `site_key`, each Prism/Lente logs a `site_key fingerprint` at startup, which is the same
  on every computer when the keys match.  The fingerprint does not reveal the key.  The Lente
  Station Manager `Site Key` column shows `Mismatch` or `Not set` in red, and a station with a
  different key shows a `site_key does not match Lente` notice.


::

        // This file is NOT propagated by Lente to Prism stations.
        // For each Prism/Lente install, this file should be modified as required.
        // See https://sistemicorp.github.io/scripts/build/html/_deployment.html#settings-json-file
        {
          // turn on demo mode.  Creates test user accounts, ...
          // remove line, or set to false to disable demo mode
          "demo": true,

          // On startup optionally specify to load a traveller
          //"load_traveller": "public/traveller/traveller_TZ6T.pdf",
          //"load_user": "operator@here.com",

          // Site key, must be the same on every Prism/Lente in the deployment
          // - encrypts the scripts package, manifest, travellers and results
          // - the demo value only works with "demo": true, generate a real one with
          //   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
          "site_key": "demo-site-key-change-me",

          // Result JSON file encryption, uses site_key
          // - a valid license file is required to encrypt results
          "result_encrypt": false,

          // By default results that are sent to Lente are backed up
          // locally, to disable this backup uncomment
          //"result_bkup_dir": null,

          // Result JSON files be backed up as encrypted, <true|false>,
          // If the results were not encrypted by Prism, they won't be ecrypted by Lente
          "results_bkup_encrypted": false,

          // Use https secure transport, requires public/cert.pem and public/key.pem files
          // For Lente & Prism stations, all must be configured the same,
          // with the same cert.pem/key.pem on every station
          "use_https": false,

          // Prism/Lente internal connection password
          "prism_lente_pw": "mysecret1",

          // Manifest (enable/disable) checking
          // Validates "public/prism" contents (sent by Lente)
          // create manifest.exclude to list file exclusions
          "manifest_check": false,

          // network interface to use, used by VPNs
          //"net_iface": "tun0",

          // Send log files on startup for diagnostic purposes
          "send_logs_on_startup": true,

          // Health checks
          // Levels: Warn, Error, Critical (case insensitive)
          // "Warn" and "Error" only appear in the notification log
          // "Critical" additionally prevents new test sessions from starting
          // First rule that matches for each health check is reported
          "health_checks": {
            "disk_space": {
              "enable": true,
              "rules": [
                // free format: <value> [MB|GB|%]
                {"free": "10%",    "level": "Critical"},
                {"free": "100 MB", "level": "Error"},
                {"free": "200 MB", "level": "Warn"}
              ]
            }
          },

          // OPCUA Configuration
          "opcua_server": {
            "enable": false,
            "security_policies":[
              "NoSecurity",
              "Basic256Sha256_Sign",
              "Basic256Sha256_SignAndEncrypt"
            ],
            "certificates": {
              "enable": false,
              // "path": "public",
              // "certificate_file": "cert.pem",
              // "private_key_file": "key.pem",
            }
          },

          // ------------------------------------------------------------------
          // Below are only used by Lente and can be removed for Prism stations

          // Lente/Lente internal connection password
          "lente_lente_pw": "mysecret3",

          // Enter IP Address:port, example "http://35.123.432.190:6595"
          // Use null to disable upstream sending.
          "result_server_url": null,

          // This Lente computer is pyramid root and creates manifest
          "root_authority": true,

          // automatically sync Prism clients scripts
          "auto_sync_scripts": true,

          // maximum size (MB, uncompressed) of the scripts package sent to stations,
          // see public/prism/scripts_zip.exclude to exclude files
          //"scripts_zip_max_mb": 100,

          "postgres": {
            // resultbasekeysv1 is the name of the dB and cannot be changed
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
* `health_checks` is used by Prism only, `results_bkup_encrypted` by Lente only
* On Prism, `result_server_url` is always set from the `--server` flag of `prism.sh`
* `auto_sync_scripts` also applies to Prism stations, keep it in the Prism file.  When it is
  `true` on a Prism, its Lente installs new scripts on it automatically.


Other Settings
==============

These optional settings are not in the example file, the defaults are shown.

::

    // seconds without activity before a logged in user is no longer reported as active,
    // an active user blocks Sync Users and Sync Script to that station (Prism and Lente)
    "session_inactive_timeout_s": 600,

    // hours before a browser login expires and the user must log in again (Prism and Lente)
    "browser_credentials_timeout_h": 168,

    // Prism only: Test Portal throughput chart, seconds per bar and number of bars
    "result_stats_time_bucket": 600,
    "result_stats_max_buckets": 20


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

By default the helper scripts use the `latest` image from Docker Hub.  To hold a deployment at a
version, pass the image with its tag using `--image=` (or `-i`), and use the same tag on every
`update` and `start`.  Leaving it off any of these commands goes back to `latest`::

    ./lente.sh --image=sistemicorp/lente:v0.8.21 update
    ./lente.sh --image=sistemicorp/lente:v0.8.21 --restart=always start

    ./prism.sh --image=sistemicorp/prismng:<tag> update
    ./prism.sh --image=sistemicorp/prismng:<tag> --server=192.168.0.10 --restart=always start

The available tags are listed on Docker Hub.  Both helper scripts also take these flags:

* `-n <number>`, instance number, appended to the container name and hostname, for example
  `-n 2` runs container `lente2`.  Use the same number for `update` and `stop`.
* `-b`, use the Docker bridge network instead of the host network.
* `-v`, Lente only, start Lente with verbose logging.

Run `./lente.sh --help` or `./prism.sh --help` for the full list.


.. _health-checks:

Health Checks
*************

When enabled/specified in `settings.json` (see example above) Prism will perform health checks on
boot up and when the test configuration changes.  Based on the health check item severity the system will
indicate the status in the GUI.  When the failure severity is `Critical` Prism will not allow testing
to begin.
