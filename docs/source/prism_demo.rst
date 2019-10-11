Prism Demo
##########

**Prism**

Sistemi Lente/Prism programs are deployed as Docker containers, which allows the programs to run in a virtual
environment, and be independent of your host operating system.  This means, for example, that you don't have
to worry about python packages, versions of modules, etc..

This is the program that production operators would use, interfaces with test equipment and the Device Under Test (DUT)

The instructions are split into two catagories,

* Basic

  * Simplest and fastest way to see `Prism`

* Full

  * Uses `git` to clone a prescriptive directory structure used by `Prism`

.. contents::
   :local:


Requirements
************

* Operating System

  * The system was developed and tested on Ubuntu 18.04
  * All these instructions are for Ubuntu 18.04

* Outside Software Requirements

  * Google Chrome browser (other browsers are not tested)
  * install Docker CE (https://docs.docker.com/install/linux/docker-ce/ubuntu/)

    * Don't miss the step of adding the current user (its well hidden)::

        sudo usermod -aG docker your-user

Basic
*****

The Basic Demo is the easiest and fastest way to try out Prism.  However you will not be able to
edit or create new scripts, or send results to the Lente server.


* First the **Prism** Docker container must be `pulled` from docker hub

  * run this pull command to check for updates to **Prism**

::

    docker pull sistemicorp/prism


* Run **Prism** container

  * it doesn't matter which directory you are in


::

    docker run -d -p 6590:6590 sistemicorp/prism

* Open Google Chrome to

    http://127.0.0.1:6590

    * Note on slower computers, it may take 5-15 seconds for the Prism window to display

  * Prism login user/password is admin@here.com/password
  * Other users passwords are `password`


* Run your first script after logging in,

  * Select button `Test Configuration`
  * Select script `prod_0.scr` from the pulldown
  * Press button `Validate`
  * If everything checked out, the `Start Testing` button will turn Green, press it, and
    you should be on the test screen, press Start to test
  * **Note:** The tests have delays in them for demo effect.  The delays are not needed.

Full
****

The Full Demo assume you have followed the instructions for the basic_ demo.

The Full Demo works by creating a local file structure and telling the ``Prism`` Docker container to use that
local file system.

`Git <https://git-scm.com/>`_ and `Github <http://www.github.com>`_ are used.

Additional Requirements
=======================

* install git::

    sudo apt update
    sudo apt install git

  * if you are unfamiliar with `git`, in short it is a free cloud based software version control platform
  * `git` is an advanced tool, and although widely used, it can be an complicated tool.  There are
    GUI programs that try and make `git` easier for the novice user, and a quick google can point you to some for your host operating system.
  * these instructions (attempt to) only use the simple basic commands of `git`
  * the perscriptive way to setup is described TBD


Clone Sistemi Scripts
=====================

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

* Run Prism

  * You need to provide a Lente IP address

    * If you don't have Lente running, then it won't matter what IP address you use, use '127.0.0.1'
    * If Lente is running on this computer, use this computer IP address, don't use
      'localhost', or '127.0.0.1'

  * The last argument to the script, `no`, is for the `restart` setting.

::

    cd ~/git/scripts/public
    ./prism.sh --server=<lente_ip_address> --restart=no start


* Open Google Chrome to

        http://127.0.0.1:6590


* See additional :ref:`_jigs:Ubuntu Install` instructions if the MicroPython PyBoard will be used

.. [1] This is covered in section TBD

