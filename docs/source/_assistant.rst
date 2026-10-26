Prism Assistant
###############

The Prism Assistant is an `MCP <https://modelcontextprotocol.io>`_ server that lets an AI
assistant, such as Claude Code or Claude Desktop, help you with your Prism/Lente project.
It runs on your computer, in your scripts repo, and gives the AI assistant read-only tools for
this documentation, your scripts, the drivers and the Prism APIs.

It can help you,

* migrate to a new Prism/Lente version, for example `0.8` to `0.9`
* write test scripts and Python test code, and lint them
* use :doc:`BOND <prism_bond>`
* add test equipment to a jig, one per jig or shared by the jigs, see :doc:`Drivers <prism_drivers>`
* lay out your test plan and test stages
* plan :doc:`Traceability <_traceability>`: serial numbers, lots, firmware versions and test
  versions
* plan and install the Prism and Lente computers of your deployment

.. contents::
   :local:


Install
*******

The assistant is in the `assistant` folder of the scripts repo, and uses the Python virtual
environment from :ref:`_development:Installing Python`,

::

    cd ~/git/scripts
    source .venv/bin/activate
    pip install -r assistant/requirements.txt

Check the server starts, it waits for a client on stdin, stop it with `Ctrl-C`,

::

    python assistant/prism_assistant.py


Connect an AI Assistant
***********************

**Claude Code** reads `.mcp.json` at the top of the scripts repo, which starts the assistant
from `.venv`.  Start Claude Code in the repo, approve the `prism-assistant` server when asked,
and check it with `/mcp`.

**Claude Desktop** and other MCP clients need the full paths, for example in Claude Desktop's
`claude_desktop_config.json`,

::

    {
      "mcpServers": {
        "prism-assistant": {
          "command": "/home/me/git/scripts/.venv/bin/python",
          "args": ["/home/me/git/scripts/assistant/prism_assistant.py"]
        }
      }
    }

The assistant works on the scripts repo it is in.  To use it with another repo, set the
environment variable `PRISM_REPO` to that repo's folder.


Using It
********

Ask your question in the AI assistant, for example "how do I store the firmware version of my
DUT?", or "lint my BLT script".  The assistant looks up the answer in the documentation and
your repo.

The assistant also has prompts for longer tasks.  In Claude Code they are slash commands, for
example `/mcp__prism-assistant__migrate_version`,

* `migrate_version` - plan a version migration of your deployment
* `write_test_script` - write a script and its test code for one test stage
* `use_bond` - set up BOND and its Pogo board header definition
* `add_equipment` - add test equipment to a jig, one per jig or shared, with its driver
* `plan_test_stages` - lay out the test stages of a product
* `plan_traceability` - plan what your results record
* `plan_deployment` - plan and install Lente and the Prism computers
* `setup_prism_computer` - set up and check one Prism computer

The tools the AI assistant can use,

* `list_docs`, `read_doc`, `search_docs` - this documentation, and the driver and example
  READMEs
* `read_file` - read files in your scripts repo
* `list_scripts`, `lint_script` - your scripts, and the :ref:`_development:Script Lint`
* `check_settings` - check a `settings.json` for the current version, without showing any
  passwords or keys
* `list_drivers`, `python_api` - the drivers with their documentation, and the Prism APIs
  used by test code
* `repo_status` - your scripts version, and how far your fork is behind Sistemi's scripts


What the Assistant Is Told
**************************

When the AI assistant connects, the server gives it instructions.  In short, the AI
assistant,

* is helping you with your Prism/Lente project, not developing Prism or Lente
* answers from this documentation and your repo, cites the page, and says so when they don't
  have the answer, instead of guessing, suggesting you contact info@sistemi.ca
* lints any script or test code it writes or changes
* records the serial number of each piece of test equipment in the results, see
  :ref:`Test Equipment <_traceability:Test Equipment>`, and follows the
  :doc:`driver <prism_drivers>` rules for equipment per jig or shared
* follows the rules in this documentation, for example the
  :doc:`test item rules <prism_programs>`, the serial number in `key0`, and Prism and Lente
  running the same major.minor version
* never asks you for passwords, the `site_key`, license files or user databases, and never
  suggests committing real passwords to your repo
* keeps your code and data in the conversation, and proposes small changes it explains
* numbers its questions, so you can answer them easily

The full text is `INSTRUCTIONS` in `assistant/prism_assistant.py`.


Privacy
*******

* The assistant only reads files, it does not change your repo.  The AI assistant may still
  change files with its own tools, review those changes as you would any other.
* What the tools return is sent to your AI assistant's provider, like anything else you share
  with it.  Your scripts and test code are your own, check your company's policy before
  using an AI assistant with them.
* `settings.json` files, keys, certificates, the license file, user databases, results, logs
  and `public/tools` are never read.  `check_settings` reports problems without the values.

The AI assistant can be wrong.  Check its answers against this documentation, and test
changes with `prism_dev.py` before production.  For questions the documentation does not
answer, contact info@sistemi.ca.
