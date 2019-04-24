Config
======

**Note:** Any change to this config file will require the manifest to be regenerated. See :ref:`prism_manifest:Manifest`.

Prism configuration is done through a (modified) json file here,

::

    public/station/prism.json

And its contents will be similar to,

::

    # NOTE: ANY changes made to this file requires the manifest to be regenerated.
    # Lente regenerates the manifest from the Tasks menu, and then sync scripts.
    {
      "config": {
        # manifest, locked or unlocked, when locked (true) Prism will only
        # operate if all files in public/station pass a hash check (are unchanged),
        # if unlocked (false) ONLY this file is checked against the manifest
        "manifest_locked": false,

        #, path to results waiting to be sent to Lente Server
        # must be named 'stage', must be under parent 'public'
        # DEFAULT: "public/result/stage",
        "result_stage_dir": "public/result/stage",

        # path to results for when they have been sent to Lente Server
        # (results are moved from stage to bkup after successfully sent to Lente)
        # (set to null for no backups)
        # DEFAULT: "public/result/bkup",
        "result_bkup_dir": "public/result/bkup",

        # How often to check for Lente Server connection, when
        # connection available, any results in stage directory are sent
        "result_server_retry_timer_sec": 10,

        # set result encryption (defaults to true)
        # - a valid license file is required to encrypt results
        "result_encrypt": false
      }
    }

This config file allows comments as lines with `#` as the first character.

Two settings in this file you are likely to need to change at some point in the future,

* manifest_locked

  * when you deploy to an insecure environment, you will be setting this to `true`, this will protect files
    from changes
  * see :ref:`prism_manifest:Manifest`

* result_encrypt

  * a valid license is required to encrypt results
