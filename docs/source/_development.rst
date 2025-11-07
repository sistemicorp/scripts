Development
###########

This section describes how to get started with your own development.

.. contents::
   :local:


Your Own Git Repo
*****************

You will want to begin with setting up your own Git repo.  If you are unfamiliar with Git,
then you should read up on it, and/or do some tutorials.  It is beyond the scope
of this documentation to teach Git.

There are some 3rd party Git GUI tools that you could use to help, especially if you don't like
the command line interface of Git.  Consider these,

    https://www.gitkraken.com/git-client (not free, works everywhere)

    https://www.sourcetreeapp.com (free, Windows/Max only)

    https://git-scm.com/download/gui/linux  (list of others)

To get started, create yourself a guthub account.

There are two ways to being using Sistemi Lente/Prism with Git,

The first way, is to fork the `scripts` repo to your own github repo.  This is the
easiest way to get started, but it has the draw back that all git forks must be
public, and its very unlikely that you want that.  So the forking method will not be used
below.

The second way is to clone scripts and push it to your own repo.  Detailed instructions
are shown below

* Create a new repository at github.com. (this is **your** repository)

  * Give it the same name as Sistemi repository, `scripts`
  * Don't initialize it with a README, .gitignore, or license.

* Clone the `scripts` repository repository to your local machine. (if you haven't done so already)

::

        git clone https://github.com/sistemicorp/scripts.git

* Note that the `scripts` clone will be created under your current directory.
  Some prefer all their (git) repositories to be under a common directory, so you might actually
  do something like this,

::

        mkdir ~/git
        cd ~/git
        git clone https://github.com/sistemicorp/scripts.git
        cd scripts
        sudo pip3 install -f requirements.txt

* Pip install will install all the Python modules needed to run Prism

  * **NOTE:** Do not use/install any other Python modules.
  * If another module is needed, contact Sistemi to have it added to Prism.

* Rename the local repository's current 'origin' to 'upstream'

::

        git remote rename origin upstream

* Give the local repository an 'origin' that points to your repository

::

        git remote add origin https://github.com/your-account/scripts.git

* Push the local repository to your repository on github

::

        git push origin master

* Now 'origin' points to your repository & 'upstream' points to the other repository

* Create a new branch for your changes with

::

        git checkout -b my-feature-branch

* You can git commit as usual to your repository

* To pull changes from Sistemi `scripts` to your master branch use,

::

        git pull upstream master

* You want to be able to pull from Sistemi `scripts` occasionally to get Sistemi updates to scripts, and/or
  examples, drivers, etc.


Repo Setup
**********

Additional steps.


Install Git Hooks
=================

*Git Hooks are generally replaced by Git Actions and are beyond the scope of these instructions*

In the `scripts` repo, there is a folder called `hooks`.  The contents of this folder
needs to be copied to `./.git/hooks` folder of your repository.

Depending on your directory structure, this example command may work,

::

    cd ~/git/scripts
    cp hooks/* ./git/hooks


Create a Tag
============

The Sistemi system reports the version of things to help keep you organized, including the version of your scripts.

On whatever branch you decide to "release" your scripts, for example, the "master" branch, create a
tag on that branch.  The tag **MUST** be of this format,

::

        Name-V.v

        where:
            Name - is anything you want, keep it short, say <8 characters
            V - is major revision, manually increased by YOU, be making a new Tag
            v - is minor revision, manually increased by YOU, be making a new Tag

Example commands to create (and push) a tag,

::

        git checkout master
        git tag MyTest-1.0
        git push origin --tags

**There should only be one tag in effect at a time, and `scripts` has a tag already, remove that tag,**

::

        git checkout master
        git tag --delete Scripts-0.1
        git push origin --tags


There should only be one tag in effect at a time, so remove a previous tag.  Here is the sequence to change
the minor version,

::

        git checkout master
        git tag --delete MyTest-1.0
        git tag MyTest-1.1
        git push origin --tags


Change README.md
================

Change this file to suit your needs.  For example, document your script/program naming strategy.


Installing Python
=================

Prism uses Python version 3.10 (see `Here <https://www.python.org/downloads/release/python-31017/>`_) inside its Docker container, and therefor that specific version should be used
for development.  Research how to install Python on Ubuntu alongside the main global Python. Install dependancies
from `requirements.txt`

::

        sudo apt install python3.10-dev
        python -m pip install -r requirements.txt


Command Line Development
************************

Initial development will be done in "headless" mode, whereupon coding is done outside of the GUI used in production.

A command line version of the core engine of the system is at the top of the `scripts` folder, called `prism_dev.py`.
The command line help,

::

        (.venv) martin@computer:~/git/scripts$ python prism_dev.py --help
        usage: prism_dev.py [-h] --script SCRIPT [--result-scan]

        prism_dev

        options:
          -h, --help       show this help message and exit
          --script SCRIPT  Path to script file to run
          --result-scan    Scan result file for correctness

        Usage examples:
            python prism_dev.py --script ./public/prism/scripts/example/prod_v0/prod_0.scr
            python prism_dev.py --script ./public/prism/scripts/example/pybrd_v0/pybrd_0.scr

        Sistemi Corporation, copyright, all rights reserved, 2019-2025


Notes about the command line development environment,

* parallel, multi-threaded, multiple test jigs are not supported

  * script is run as a single thread - cannot test parallelism
  * however your code will run multiple jigs in parallel within the Prism GUI

* Results are NOT sent to the Lente Server, however a local Result file with the results
  will be created for inspection purposes.
* script substitutions are not supported, leaving two options for developers,

  * rename script `subs` section to something else and populate the subs manually, save this
    script to a new name while developing.  Revert after everything is working.
  * use helper script `prism_subs.py`, which will perform the substitutions.  This helper needs
    to be modified per script it is used on.

After your script is running in the command line mode, you can try it in the Prism GUI.

