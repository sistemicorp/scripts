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

  * The system was developed and tested on Ubuntu 22.04
  * All these instructions are for Ubuntu 22.04
  * The Docker Prism image is based on Ubuntu 22.04

* Outside Software Requirements

  * Google Chrome browser (other browsers are not tested)
  * install Docker CE (https://docs.docker.com/install/linux/docker-ce/ubuntu/)

    * Several instillation methods are described.  The "convenience script" works well.

::

    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh


* Don't miss the step of adding the current user (its well hidden in their instructions)

::

        sudo usermod -aG docker ${USER}


* reboot Ubuntu

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

    docker run -d -p 6590:6590 --name prism sistemicorp/prism

* Open Google Chrome to

    http://127.0.0.1:6590

  * **Do Not use the browser BACK button, always use the page controls for navigation**
  * Note on slower computers (RPi), it may take 5-15 seconds for the Prism window to display
  * The Prism landing page should appear,

.. image:: static/Screenshot_prism_demo_2.png


* Press the Login button (upper left corner)

  * Prism login user/password is admin@here.com/password
  * Other users passwords are `password`

* Its a good idea to bookmark this URL, and display bookmark bar in the browser.
* This is the Main page, the starting point to begin testing.

  * In real production environment, the operator would scan a traveller to
    configure Prism to test a product.  Since this is a demo, we will select a
    test manually.
  * Select button `Test Configuration` (1)

.. image:: static/Screenshot_prism_demo_1.png

* Run your first script after logging in,

  * Select Group select `Example` (1)
  * Select Script select `prod_0.scr` (2)
  * Press button `Validate` (3)
  * If everything checked out, the `Start Testing` button will turn Green. (4)
  * The script that will be run is shown (5)

.. image:: static/Screenshot_prism_demo_3.png

* Press `Start Testing` (4) to proceed to the testing view.

.. image:: static/Screenshot_prism_demo_4.png

* Press the `TEST` (1) button to begin the test.
* Logging from the test will be shown in the table (2).
* Historical stats of your testing will be shown in the plot (3).
* **Note:** Example tests have delays in them for demo effect.
* `prod_0.scr` test script, demonstrates many features

  * the user will be shown buttons to press, any button will pass.
  * the user will have to enter some text, any text will pass

* this Demo shows only one active "Jig", if you want to display more,

  * Access the Main menu and select Demo (Main->Demo)
  * Change the number of "fake" jigs between 1-4.
  * Go back to the Main page (Menu->Main)
  * Repeat the steps above to re-run the demo test.



* Shut down Prism Demo

  * On the Linux command line,

::

    docker stop prism


Full Demo and/or Instillation
*****************************

The Full Demo (or Instillation) assumes you have followed the instructions for the basic_ demo.

The Full Demo works by creating a local file structure and telling the ``Prism`` Docker container to use that
local file system.

`Git <https://git-scm.com/>`_ and `Github <http://www.github.com>`_ are used.

Additional Requirements
=======================

* install additional packages

::

    sudo apt update
    sudo apt install git build-essential python3-dev

* if you are unfamiliar with `git`, in short it is a free cloud based software version control platform
* `git` is an advanced tool, and although widely used, it can be an complicated tool.  There are
  GUI programs that try and make `git` easier for the novice user, and a quick google can point you to some for your host operating system.
* these instructions (attempt to) only use the simple basic commands of `git`


Clone Sistemi Scripts
=====================

* There is a prescriptive directory structure to use, and that is stored on `github` in a project called ``scripts``
* This `github` repo is where you would ultimately store and version control your own scripts

  * To make the repo your own, instead of cloning the repo, you would *fork* (copy) it,
    making it your own, and then add your own code

* The instructions below will create a folder called *git/scripts* which `git` will copy the required files into

* Clone ``scripts`` and install Python requirements,

::

    mkdir ~/git
    cd ~/git
    git clone https://github.com/sistemicorp/scripts.git
    cd scripts
    pip3 install -f requirements.txt



Run Full Demo
=============

* The difference between the basic Demo and this full install, is that the Basic Demo
  used the same files just cloned from scripts, but they were "inside" the docker Prism image
  and not accessible.
* Now Prism will use the scripts you just cloned.
* Run Prism

::

    cd ~/git/scripts/public
    ./prism.sh --server=none --restart=no start


* Open Google Chrome to

        http://127.0.0.1:6590

* Follow the same steps above from the Basic Demo and re-run the same test.
* Prism can be stopped with this command,

::

./prism.sh stop
