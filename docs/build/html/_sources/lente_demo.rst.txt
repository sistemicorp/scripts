Lente Demo
##########

**Lente**

This is the dashboard and backend processing database program.

The backend processor is a postgres Docker container, and it needs to be running before Lente can be started.

The instructions are split into two catagories,

* Basic

  * Simplest and fastest way to see `Lente`

* Full

  * Uses `git` to clone a prescriptive directory structure used by `Lente`

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
  * All these instructions are for Ubuntu 18.04

* Outside Software Requirements

  * Google Chrome browser (other browsers are not tested)
  * install Docker CE (https://docs.docker.com/install/linux/docker-ce/ubuntu/)


Postgres
********

Lente needs a postgresql backend to be running in order to work, which will be installed first.

* postgresql server

  * make a new directory in your home directory, change into it, create a data directory, and run Docker
    postgres command (this will pull postgres container)

::

    mkdir ~/postgres
    cd ~/postgres
    mkdir datadir
    docker network create lentenet
    docker run --net lentenet --name lentedb -v $(pwd)/datadir:/var/lib/postgresql/data -e POSTGRES_PASSWORD=qwerty -d postgres:11

  * add `--restart=always` to the docker run command to have this container run every time the computer boots up;
    only do this if you plan on using/evaluating Sistemi Lente/Prism for an extended time, otherwise remember to issue the above docker run
    command

* now create the required databases - you only need to do this **ONCE**

::

    docker exec -it lentedb createdb -U postgres resultbasekeysv1


Basic
*****

Run Basic
=========

* First the **Lente** Docker container must be `pulled` from docker hub

::

    docker pull sistemicorp/lente


* Run **Lente** container - it doesn't matter which directory you are in

::

    docker run -d --net lentenet -p 6595:6595 sistemicorp/lente


* Open Google Chrome to

           http://127.0.0.1:6595

  * Note on slower computers, it may take 5-15 seconds for the Lente window to display
  * Lente login user/password is admin/admin
  * Other users passwords are `qwerty`
  * To **update** lente use `docker pull sistemicorp/lente` before running it.


Full
****

The Full Demo assume you have followed the instructions for the basic_ demo.

The Full Demo works by creating a local file structure and telling the ``lente`` Docker container to use that
local file system.  This requires a more advanced `docker run` command.

`Git <https://git-scm.com/>`_ and `Github <http://www.github.com>`_ are used.


* Follow these instructions :ref:`prism_demo:Additional Requirements`


Clone Sistemi Scripts
=====================

* If you have already cloned ``scripts`` from the Prism instructions, you do not need to do this again here.
* There is a prescriptive directory structure to use, and that is stored on `github` in a project called ``scripts``
* This `github` repo is where you would ultimately store and version control your own scripts

  * Instead of cloning the repo, you would *fork* [1]_ (copy) it, making it your own, and then add your own code
* The instructions below will create a folder called *git/scripts* which `git` will copy the required files into

* Clone ``scripts``::

    mkdir ~/git
    cd ~/git
    git clone https://github.com/sistemicorp/scripts.git


Run Full
========

* Run postgres::

    cd ~/git/scripts/public
    ./postg.sh start

* Run Lente::

    cd ~/git/scripts/public
    ./lente.sh start

* Open Google Chrome to

        http://127.0.0.1:6595


.. [1] This is covered in section TBD



