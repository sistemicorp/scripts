Manifest
########

A method by which your scripts and programs are protected from changes (hacks) in the production environment.

Prism will not operate if the Manifest is not validated.

The manifest is an encrypted file at this location,

::

    public/prism/manifest.sistemi

This file holds a list of files from `pubic/prism` along with a hash of each file, which is used
by Prism to check if any changes have been made to any of the files.  If a file has been changed,
Prism will not operate.

To enable manifest checking, the `prism.json` file must have this setting,

::

    "manifest_locked": true,


If `manifest_locked` is `false`, which it is in demo and development scenarios, ONLY the `prism.json` itself is
in the manifest.  Therefore, `prism.json` file can never be changed without updating the manifest file.

**Lente is required to update the manifest file.**


Exclusions
**********

When `manifest_locked` is `true` every file in the `pubic/prism` path is added to the manifest, and therefore
becomes locked.  Any changes, Prism will not operate.

In the case that you have files that change content during testing, you may exclude those files by listing them
in,

::

    public/prism/manifest.exc



Update Manifest
***************

Lente can update the manifest.  See main drop down menu, Station Management.

In a deployed production environment, Lente deploys scripts/programs to the attached Prisms. This
process includes an automatic update of the Manifest.
