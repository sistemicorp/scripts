Security
########

Production security is important.  Sistemi Lente/Prism have features and suggestions to improve security.

.. contents::
   :local:


Settings.json
=============

Most of the security of the system is set by `settings.json <_deployment.html#_Settings File>`__.

`settings.json` file is unique to each Prism/Lente in the deployment.  It is common for
multiple Prism computers sitting below Lente to have the same `settings.json`, assuming the settings are the same.

`settings.json` is edited/created when Prism/Lente computer is configured.

Although `settings.json` is in the git repo, it is not the one used by the deployment, nor is it
sent between Lente/Prism computers.

Prism computers should remove the Lente section of the `settings.json` file.


Manifest Checking
=================

Enable Manifest checking in the `settings.json <_deployment.html#_Settings File>`__. file.

The Manifest (file) is created by Lente to ensure the integrity of the all the scripts and supporting files.
The manifest is a list of files and corresponding hashes, which Prism will use to validate there are no
changes to the files it will use to test.  The Manifest file itself is encrypted and cannot be viewed.

Only the Lente that is marked as `root_authority` in `settings.json` will create the Manifest.  All other
Lente's will pass along the Manifest.

If some files need to be excluded from Manifest checking, create `./public/prism/manifest.exclude` and list
the path names of the files to be excluded, for example,

::

    # comments are allowed, startswith #
    public/prism/scripts/example/prod_v0/prod_0.scr



Prism/Lente Files
=================

Prism/Lente "programs" are access via a browser.  Technically, the user could be on a different computer
and accessing Prism/Lente remotely. Remote access is common for Lente, and not common for Prism.

Because Prism/Lente are accessed via the browser, a Ubuntu (operator) account need only provide the Chrome
browser and access to `localhost` (127.0.0.1:6590).  One could create a boot script for the operator to run Chrome
automatically and point to Prism.

All the files that Prism/Lente use should be in another Ubuntu account, and not accessible by other accounts.
If the account home directory is encrypted, and/or the whole hard drive is encrypted, then the files are
protected.


Lente
=====

It is assumed that Lente are "physically secure", which means physical access to the computers is
restricted in some way, for example, locked in a secure room.

The following are further suggestions to improve security,

* encrypt the hard disk by the OS
* strong admin password
* use Account Roles for users
* Prism/Lente use ports 6590 & 6595, so other ports can be blocked


Prism
=====

Prism stations are considered insecure.  Presumably anyone on the production floor can access a Prism.
Often login names and passwords are common to a group of people, or shared among them to access the computer.

The following are further suggestions to improve security,

* encrypt the hard disk by the OS
* strong admin password
* enable result encryption
* regularly purge the backups from the disk, (or disable backups, not recommended)
* use Account Roles for users
* A Ubuntu Operator account could launch Chrome in kiosk mode and launch the Prism URL
* Prism/Lente use ports 6590 & 6595, so other ports can be blocked


Postgres DB
===========

* Change the default password!

  * Also remember to use the same password in `settings.json <_deployment.html#_Settings File>`__.


.. _https:

HTTPS and SSL Certificates
==========================

Please read this article: https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

The coles notes version is that Prism/Lente are not public domain servers and are considered private
internal servers.  Therefore we can avoid cost and complexity by using our own generated/signed keys.
These keys will still be using the same TLS protocol over the connection and are therefore just as secure.

However, since the (Chrome) browser is not able to authenticate the self signed keys/certificate it
will indicate that the connection is "untrusted" and will prompt the user to validate the connection.

With HTTPS the connection between Prism/Lente is now encrypted.  `settings.json <_deployment.html#_Settings File>`__
has `prism_lente_pw` which should also be set to something unique.  This setting needs to be the same
across all the Prism/Lente computers.

On deployed Prism/Lente computers the user account is presumed to be secure.  The Ubuntu filesystem should
be encrypted, and the user account that hosts the files for Prism/Lente should be password protected.  Operator
accounts do not need access to the Prism/Lente files. See `Ubuntu File System <_deployment-ubuntu-filesystem>`__

The same certificate and key files can be used to secure the OPC-UA server.

To generate the certificate and key, use the following commands.  Update openssl_req.ssl with
organization information, if desired.

::

    ~/git/scripts/public$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3650 -config ../openssl_gen.cnf

    ~/git/scripts/public$ ls -al
    total 84
    drwxrwxr-x 6 martin martin  4096 Jun 10 09:42 ./
    drwxrwxr-x 7 martin martin  4096 Jun 10 09:06 ../
    -rw-rw-r-- 1 martin martin  1968 Jun 10 09:42 cert.pem              <-- created
    -rw------- 1 martin martin  3272 Jun 10 09:41 key.pem               <-- created
    -rwxrwxr-x 1 martin martin  2954 May 28 11:35 lente.sh*
    drwxr-xr-x 2 root   root    4096 Jun  4 15:32 log/
    drwxrwxr-x 4 martin martin  4096 Jun 10 09:13 prism/
    -rwxrwxr-x 1 martin martin  4409 May 28 11:35 prism.sh*
    drwxr-xr-x 5 root   root    4096 May 29 16:11 result/
    -rw-rw-r-- 1 martin martin  1646 Jun 10 09:06 settings.json
    drwxr-xr-x 2 root   root    4096 May 29 16:18 traveller/
    -rw-r--r-- 1 root   root   28672 May 28 11:37 users.sqlite
    -rw-rw-r-- 1 martin martin   121 Jun 10 09:06 VERSION


* Generate the cert/key file on each Prism/Lente computer.
* See the `settings.json <_deployment.html#_Settings File>`__ to enable HTTPS and set the Prism/Lente password.
* In the browser, connect over HTTPs,

  * for Prism use `https://127.0.0.1:6590`
  * for Lente use `https://127.0.0.1:6595`

* Prism/Lente docker images will have to be restarted to use HTTPS.
