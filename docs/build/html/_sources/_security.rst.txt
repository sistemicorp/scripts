Security
########

Production security is important.  Sistemi Lente/Prism have features and suggestions to improve security.

.. contents::
   :local:


Lente
=====

It is assumed that Lente are "physically secure", which means physical access to the computers is
restricted in some way, for example, locked in a secure room.

The following are further suggestions to improve security,

* encrypt the hard disk by the OS
* strong admin password
* use Sistemi Account Roles for users


Prism
=====

Prism stations are considered insecure.  Presumably anyone on the production floor can access a Prism.
Often login names and passwords are common to a group of people, or shared amoung them to access the computer.

The following are further suggestions to improve security,

* encrypt the hard disk by the OS
* strong admin password
* enable result encryption
* regularly purge the backups from the disk, (or disable backups, not recommended)
* use Lente Account Roles for users


Postgres DB
===========

* Change the default password!

  * Also remember to use the same password in the settings.json, see `here <_deployment.html#_Settings File>`__.


.. _https:

HTTPS
=====

Please read this article: https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

The coles notes version is that Prism/Lente are not public domain servers and are considered private
internal servers.  Therefore we can avoid cost and complexity by using our own generated/signed keys.
These keys will still be using the same TLS protocol over the connection and are therefore just as secure.

However, since the (Chrome) browser is not able to authenticate the self signed keys/certificate it
will indicate that the connection is "untrusted" and will prompt the user to validate the connection.

With HTTPS the connection between Prism/Lente is now encrypted.  The :ref:`settings.json file <deploy-settings-file>`
has `prism_lente_pw` which should also be set to something unique.  This setting needs to be the same
across all the Prism/Lente computers.

On deployed Prism/Lente computers the user account is presumed to be secure.  The Ubuntu filesystem should
be encrypted, and the user account that hosts the files for Prism/Lente should be password protected.  Operator
accounts do not need access to the Prism/Lente files. See :ref:`Ubuntu File System <deployment-ubuntu-filesystem>`

To generate the certificate and key,

::

    ~/git/scripts/public$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3650
    ... you will be promoted to answer some questions, the answers are not important
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
* See the :ref:`settings.json file <deploy-settings-file>` to enable HTTPS and set the Prism/Lente password.
* In the browser, connect over HTTPs,

  * for Prism use `https://127.0.0.1:6590`
  * for Lente use `https://127.0.0.1:6595`

* Prism/Lente docker images will have to be restarted to use HTTPS.
