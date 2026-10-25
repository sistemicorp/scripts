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
    cp hooks/pre-commit .git/hooks/

This githook will update `public/VERSION` file that Prism uses to display the version of the scripts.
A change to `public/VERSION` is also what makes Lente rebuild the scripts package for stations.
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

The version uses the most recent tag (`git describe --tags`).  For example, version `0.9.12` is
the 12th commit after tag `0.9`.  `scripts` already has tags (for example
`0.8`), you can remove them from your fork,

::

        git tag --delete 0.8
        git push origin --delete 0.8


Change README.md
================

Change this file to suit your needs.  For example, document your script/program naming strategy.


Installing Python
=================

Prism uses Python version 3.12 inside its Docker container, and therefore that specific version should
be used for development.  Ubuntu 24.04 includes Python 3.12.

Install dependencies from `requirements.txt` into a virtual environment,

::

        sudo apt install python3.12-dev python3.12-venv
        cd ~/git/scripts
        python3.12 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt


Command Line Development
************************

Initial development will be done in "headless" mode, whereupon coding is done outside of the GUI used in production.

A command line version of the core engine of the system is at the top of the `scripts` folder, called `prism_dev.py`.
The command line help,

::

        (.venv) martin@computer:~/git/scripts$ python prism_dev.py --help
        usage: prism_dev.py [-h] --script SCRIPT [--lint] [--result-scan]

        prism_dev

        options:
          -h, --help       show this help message and exit
          --script SCRIPT  Path to script file to run
          --lint           Only lint the script and its test code, exit 1 on errors
          --result-scan    Scan result file for correctness

        Usage examples:
            python prism_dev.py --script ./public/prism/scripts/example/prod_v0/prod_0.scr
            python prism_dev.py --script ./public/prism/scripts/example/pybrd_v0/pybrd_0.scr
            python prism_dev.py --lint --script ./public/prism/scripts/example/prod_v0/prod_1.scr

        Sistemi Corporation, copyright, all rights reserved, 2019-2025


Notes about the command line development environment,

* parallel, multi-threaded, multiple test jigs are not supported

  * script is run as a single thread - cannot test parallelism
  * however your code will run multiple jigs in parallel within the Prism GUI

* Results are NOT sent to the Lente Server, however a local Result file with the results
  will be created for inspection purposes.
* script substitutions are filled in without asking, each sub uses its `default`, or else its first
  `choices` entry, or else a placeholder (`prismdev`, or `0` for a `num` sub).  The values used
  are logged.  To try other values, change the defaults while developing, or use the helper
  script `prism_subs.py`, which needs to be modified per script it is used on.

* the script is linted before it runs, see :ref:`_development:Script Lint`

After your script is running in the command line mode, you can try it in the Prism GUI.


Script Lint
===========

The script linter, ``public/prism/script_lint.py``, checks a script and the Python test items it
runs, without running them.  It finds mistakes that would otherwise only show up on the production
floor, such as a test item that returns without calling ``self.item_end()``.

The test modules are read as source code and are not imported, so no driver or hardware code runs.
Only the methods named by the script's items are checked.

The linter runs,

* with ``python prism_dev.py --lint --script <script>``, which only lints and exits with 1 if there
  are errors.  The script may have a ``subs`` section, and its subs are checked too.
  This is a good step to add to your CI.
* before every ``prism_dev.py`` run.  An error stops the run.
* when you `Validate` a script in Prism, after substitutions.  An error rejects the script, and
  warnings are shown in the notices.

Findings are ``ERROR`` or ``WARN``, and each one names where it is.
A script problem names the script section, and a code problem names the file, line and item,

::

        ERROR info.lot: longer than 16 characters
        ERROR tests[0].items[3] TST003: no method TST003 in public.prism.scripts.my_v0.tst00xx
        ERROR public/prism/scripts/my_v0/tst00xx.py:212 TST001_Meas: return before item_end()
        WARN public/prism/scripts/my_v0/tst00xx.py:240 TST006_RsrcLock: time.sleep() cannot be stopped by a timeout, use self.sleep()


Test item checks
----------------

Every path through a test item method is followed, including early returns in ``if``, ``try``,
``with``, ``match`` and loops.

Errors,

* the first statement, after the doc string, must be ``ctx = self.item_start()``
* ``self.item_start()`` must be called only once
* every path must end with ``self.item_end()``, and every ``return`` must come right after it
  (or be ``return self.item_end(...)``).  Raising an exception is allowed; Prism ends the item
  as ``INTERNAL_ERROR``.
* ``self.item_end()`` must not be called twice on one path.  This usually means a missing
  ``return`` after an early ``self.item_end()``.
* a result passed as a string must be a ``ResultAPI.RECORD_RESULT_*`` value
* ``self.item_end(_next="<id>")`` must name an item that comes later in the script
* ``ctx.item.args.<name>``, ``ctx.item.args["<name>"]``, ``ctx.item.<field>``,
  ``ctx.options.<name>`` and ``ctx.config.<name>`` must exist in the script.
  Use ``ctx.item.args.get("<name>", <default>)`` for an optional value.
* the module file must exist, with a class of the same name as the file, and a method for every
  item ``id``

Warnings, for code that a timeout cannot stop (see :ref:`prism_programs:Timeouts and Aborts`),

* ``time.sleep()``, use ``self.sleep()``
* a ``while`` loop that never calls ``self.sleep()``, ``self.check_abort()`` or an input method
* a bare ``except:`` or ``except BaseException:`` that does not re-raise, use ``except Exception:``

The linter is strict: it does not follow calls into your own helper methods.
A helper that calls ``self.item_end()`` does not count as ending the item, so call
``self.item_end()`` in the test item method itself.


Script checks
-------------

Errors,

* ``info`` must have ``product``, ``bom``, ``lot`` and ``location`` (``config`` is optional), as
  strings no longer than the Lente database fields (see :ref:`prism_scripts:info`).
  Empty strings are allowed.  Other fields are errors, as Lente cannot store them.
* ``config.drivers`` must be a non-empty list of driver module names, or ``[module, args]``
  pairs, and each driver module must exist
* ``fail_fast`` must be ``true`` or ``false``
* ``tests``, each ``module`` and each ``items`` list must be present and non-empty
* an item ``enable`` must be ``true`` or ``false``, or the strings ``"true"`` / ``"false"`` from a
  `str` sub
* a ``timeout`` must be a positive number
* ``args`` and ``options`` must be objects
* ``fail`` must be a list of ``{"fid": ..., "msg": ...}``
* after substitution, no ``"%%<key>"`` may be left in the script

Checks of the ``subs`` section, when linting a script before substitution (see
:ref:`prism_scripts:subs`),

* each ``"%%<key>"`` in the script must be defined in ``subs``, or as an inner sub (error)
* each sub must have a ``type`` of `str` or `num`, and a ``widget`` of `textinput` or `select`;
  a `select` must have ``choices`` (error)
* a ``regex`` must compile, and the ``default`` must match it (error)
* inner subs must have an entry for every choice, given as ``{"val": ..., "type": ...}``, and
  must not reuse a top level key (error)
* a sub that is never used is a warning

Warnings,

* an item field that looks like a typo of ``enable``, ``timeout``, ``args`` or ``fail``, for
  example ``"timout"``.  Items may carry other fields for your code, read as ``ctx.item.<field>``.
* the last item of a test is disabled.  The last item is the teardown and should always run.

