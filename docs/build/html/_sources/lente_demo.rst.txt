Lente Demo
##########

.. _lente-full-install:

**Lente** is the dashboard and backend processing database program.

The backend processor is a postgres Docker container, and it needs to be running before Lente can be started.

Sistemi Lente/Prism programs are deployed as Docker containers, which allows the programs to run in a virtual
environment, and be independent of your host operating system.  This means, for example, that you don't have
to worry about python packages, versions of modules, etc

.. contents::
   :local:


Requirements
************

* Operating System

  * The system was developed on both Windows 10 and Ubuntu 18.04
  * Most testing occurs on Ubuntu given its the expected OS used in the factory because of cost (its free)
  * All these instructions are for Ubuntu 22.04

* Outside Software Requirements

  * Google Chrome browser (other browsers are not tested)
  * install Docker CE (https://docs.docker.com/install/linux/docker-ce/ubuntu/)


Postgres
********

Lente needs a postgresql backend to be running in order to work, which will be installed first.
Instructions for setting up Postgres on Ubuntu are given as an example.

::

    $ sudo apt install postgresql postgresql-contrib
    $ sudo systemctl start postgresql.service
    $ sudo -u postgres psql
    psql (14.7 (Ubuntu 14.7-0ubuntu0.22.04.1))
    Type "help" for help.

    postgres=# ALTER USER postgres PASSWORD 'qwerty';
    ALTER ROLE
    postgres=# \q
    $ sudo -u postgres createdb resultbasekeysv1


Note that the postgres service is not `enabled`, only started.  If you want the service to start
every time the computer is booted, also run,

::

    $ sudo systemctl enable postgresql.service


Clone Sistemi Scripts
=====================

* If you are using the same computer for Lente as you did for Prism and have already cloned ``scripts`` from
  the Prism instructions, you do not need to do this again here.
* There is a prescriptive directory structure to use, and that is stored on `github` in a project called ``scripts``
* This `github` repo is where you would ultimately store and version control your own scripts

  * Instead of cloning the repo, you would *fork* the `scripts` repo (copy it), making it your own, and then add your own code

* The instructions below will create a folder called *git/scripts* which `git` will copy the required files into
* If this is a Lente deployment, on a dedicated computer, then you want to clone the scripts repo you created.

* Clone ``scripts``::

    mkdir ~/git
    cd ~/git
    git clone https://github.com/sistemicorp/scripts.git





* the **Lente** Docker container must be `pulled` from docker hub

::

    docker pull sistemicorp/lente


* Run Lente::

    cd ~/git/scripts/public
    ./lente.sh start



* Open Google Chrome to

           http://127.0.0.1:6595

  * Note on slower computers, it may take 5-15 seconds for the Lente window to display
  * Lente login user/password is `admin@here.com`/`password`
  * Other users passwords are `password`
