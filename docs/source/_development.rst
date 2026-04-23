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

Command Line (Mirroring)
========================

Use this method to create a private copy of a public repository that includes all branches and tags.
(There are other approaches if you are familiar with git.)

1. Create a bare clone of the public repository
-----------------------------------------------

This pulls down the underlying git data without creating a working directory.

.. code-block:: bash

   git clone --bare https://github.com/sistemicorp/scripts

2. Create a new private repository on GitHub
--------------------------------------------

Go to GitHub and `create a new repository <https://github.com>`_.

.. important::
   * Do **not** initialize it with a README, .gitignore, or License.
   * Set the visibility to **Private**.

3. Mirror-push to your new private repository
---------------------------------------------

Move into the bare clone directory and push everything to your new private URL.

.. code-block:: bash

   cd scripts.git
   git push --mirror https://github.com/yourname/private-repo.git

4. Clean up and clone locally
-----------------------------

Remove the temporary bare clone folder and perform a standard clone of your new private repo to begin working.

.. code-block:: bash

   cd ..
   rm -rf scripts.git
   git clone https://github.com/yourname/private-repo.git



Install Git Hooks
=================

*Git Hooks are generally replaced by Git Actions and are beyond the scope of these instructions*

In the `scripts` repo, there is a folder called `hooks`.  The contents of this folder
needs to be copied to `./.git/hooks` folder of your repository.

Depending on your directory structure, this example command may work,

::

    cd ~/git/scripts
    cp hooks/* ./git/hooks

This githook will update `public/VERSION` file that Prism uses to display the version of the scripts.
By using this githook, or some other mechanism, the script version is tracked by Prism.  The version
number is derived from a tag.


Create a Tag
============

The Sistemi system reports the version of things to help keep you organized, including the version of your scripts.

On whatever branch you decide to "release" your scripts, for example, the "main" branch, create a
tag on that branch.  The tag **MUST** be of this format,

::

        V.v

        where:
            V - is major revision, manually increased by YOU, be making a new Tag
            v - is minor revision, manually increased by YOU, be making a new Tag

Example commands to create (and push) a tag,

::

        git checkout master
        git tag 1.0
        git push origin --tags

**There should only be one tag in effect at a time, and `scripts` has a tag already, remove that tag,**

::

        git checkout master
        git tag --delete 0.8
        git push origin --tags


Change README.md
================

Change this file to suit your needs.  For example, document your script/program naming strategy.


Installing Python
=================

Prism uses Python version 3.12 inside its Docker container, and therefore that specific version should
be used for development.  Research how to install Python on Ubuntu alongside the main global Python.

Install dependencies from `requirements.txt`

::

        sudo apt install python3.12-dev
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

