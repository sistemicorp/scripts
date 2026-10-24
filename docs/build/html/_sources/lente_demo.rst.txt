Lente Demo
##########

.. _lente-full-install:

**Lente** is the dashboard and backend processing database program.

The backend database is Postgres, run as a Docker container, and it needs to be running before Lente can be started.

Sistemi Lente/Prism programs are deployed as Docker containers, which allows the programs to run in a virtual
environment, and be independent of your host operating system.  This means, for example, that you don't have
to worry about python packages, versions of modules, etc

.. contents::
   :local:


Requirements
************

* Operating System

  * All these instructions are for Ubuntu 24.04, which is also the OS of the Prism/Lente Docker images

* Outside Software Requirements

  * Google Chrome browser (other browsers are not tested)
  * install Docker CE (https://docs.docker.com/install/linux/docker-ce/ubuntu/)


.. _lente-demo-postgres:

Postgres
********

Lente needs a Postgres database to be running in order to work, which will be set up first.
Postgres is run as a Docker container, with its data stored in a folder on the host.

::

    mkdir -p ~/lente_postgres_data
    docker run --name lente_postgres --restart=always -p 5432:5432 \
        -v ~/lente_postgres_data/datadir:/var/lib/postgresql/data \
        -e POSTGRES_PASSWORD=qwerty -d postgres:16

* `--restart=always` starts Postgres every time the computer boots.
* The password (`qwerty` above) must match `postgres.resultbasekeysv1.pw` in `public/settings.json`.
  Use a real password for a deployment.
* Lente creates the `resultbasekeysv1` database and its tables on first start.
* Postgres logs: `docker logs -f lente_postgres`


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





* Get (or update) the **Lente** Docker image from Docker Hub, and run Lente.  The `lente.sh` script
  must be run from the `public` folder::

    cd ~/git/scripts/public
    ./lente.sh update
    ./lente.sh start



* Open Google Chrome to

           http://127.0.0.1:6595

  * Note on slower computers, it may take 5-15 seconds for the Lente window to display
  * Lente login user/password is `admin@here.com`/`password`
  * Other users passwords are `password`


.. _first-admin:

Demo Users and the First Admin
==============================

The `@here.com` users exist only because `public/settings.json` has `"demo": true`.  On a fresh install
with `"demo": false` there are no users, and nobody can log in.

For a real deployment, on Lente and on each Prism,

1. start with `"demo": true` and log in as `admin@here.com`
2. in Account Management, create your own admin account
3. log in as your admin, and delete all the `@here.com` accounts
4. set `"demo": false` and restart

Turning demo off does not remove the `@here.com` accounts, step 3 is required.
