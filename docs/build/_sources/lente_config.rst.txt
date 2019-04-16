Config
======

Lente configuration is done through a (modified) json file here,

::

    public/lente.json

And its contents will be similar to,

::

    {
      "config": {
        # Should the result JSON files be stored as encrypted, true (default) or false,
        # If the results were not encrypted by Prism, they won't be ecrypted by Lente
        "results_bkup_encrypted": false
      },
      "postgres": {
        "ResultBaseKeysV1": {
          "user": "postgres",
          # !! Change "pw" to a real password for a real deployment
          # !! This pw must match your postgres deployment too
          "pw": "qwerty",
          "ip": "lentedb"
        }
      }
    }

This config file allows comments as lines with `#` as the first character.

`public/lente.json` is **NOT** deployed to Prism by the Lente sync scripts management function.
Prism will only have the demo version of this file.

Two settings in this file you are likely to need to change at some point in the future,

* postgres:ResultBaseKeysV1:pw

  * needs to be changed to a secure value before deployment

* results_bkup_encrypted

  * You may or may not want Lente backups stored encrypted or not

    * encrypted, they are difficult to do anything with, for example if you wanted to add your own
      post porocessing, you could not do that with encrypted results

  * You may decide that the Lente at the top of the deployment, is in the cloud, and on this node it
    makes sense to store results as plain text, as presumably your cloud node is secure

