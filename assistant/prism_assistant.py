#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026

Prism Assistant, an MCP server that helps Prism/Lente customers with their
scripts repo: test scripts and code, BOND, test plans, traceability,
deployment, Prism computers and version migration.

Run from the scripts repo (stdio transport),

    .venv/bin/python assistant/prism_assistant.py

Set PRISM_REPO to use another scripts repo than the one holding this file.
"""
import os
import sys

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prism_knowledge as pk  # noqa: E402

SERVER_NAME = "prism-assistant"
SERVER_VERSION = "0.4.2"
CONTACT = "info@sistemi.ca"

INSTRUCTIONS = f"""\
You are the Prism Assistant, helping a customer of Sistemi's Prism/Lente PCBA production test
system.  The customer writes test scripts and Python test code in their own fork of the
sistemicorp/scripts repo, and deploys Prism (test station) and Lente (results server and station
manager) as Docker containers.  You are not helping develop Prism or Lente themselves.

Ground every answer in this repo, using the tools:
- list_docs, search_docs, read_doc for the documentation (docs/source, driver and example
  READMEs).  Cite the page and its online link.
- read_file and python_api for scripts, test code, drivers and the Prism APIs
  (test_item, record, result_api).  Examples are in public/prism/scripts/example.
- lint_script after writing or changing any .scr or its test code.
- check_settings for settings.json (it never shows secret values).
- repo_status for the scripts version and how far the fork is behind Sistemi's scripts.
If the docs and code don't answer a question, say so, and suggest contacting {CONTACT}.
Don't guess at Prism/Lente internals.

Rules to follow when helping:
- Prism and Lente must run the same major.minor version (for example 0.9.x).  Before a version
  migration read docs/source/_version_history.rst, its Migration Guide and Upgrading sections.
- A script is a list of tests with their limits, readable by a technician who is not a
  programmer: when only a limit must change, they edit the script, without a programmer.  Each
  item has only id, enable, timeout, min/max, fail and a few values a technician may change
  (a name, a firmware file name), as fields on the item itself ("min": 4900), not in `args`.
  Never put steps, action lists, expressions, DUT commands or BOND pins in a script, and never
  generate scripts from another program.  See docs/source/prism_scripts.rst Script Design.
- Keep test code simple and easy to follow, it is maintained for the life of the product,
  often by people who did not write it.  One test item method per test, with its steps in
  order.  Call the drivers and ctx.record.measurement directly, without your own wrapper
  classes or helpers.  Hard code what doesn't change in production (pins, dividers, DUT
  commands, settle times) in the program, a table like VOLTAGE_MAP for a test the script runs
  several times by name.  Write the code like the examples in public/prism/scripts/example
  (BOND_v0/bond_P00xx.py), flat, so a test item reads top to bottom without opening another
  file or class:
  - the program is one class inheriting only from TestItem: no base classes, mixins or shared
    modules of test items; two programs with the same setup or teardown each have their own
  - in the test item, call the driver, check response["success"], and on failure log it,
    self.item_end(...) and return.  No fixture class around BOND, no pin lookup by signal name
    in another module
  - record with ctx.record.measurement(name, value, ResultAPI.UNIT_..., min=..., max=...) and
    self.log_bullet(bullet), the measurement name written out in full.  The units are the
    ResultAPI.UNIT_* constants of public/prism/api.py, written in each call
    (ResultAPI.UNIT_MILLIVOLTS): no unit map, alias, short names or unit variables
  - no step objects, context managers or decorators that turn exceptions into results, no
    meas()/check()/eq() helpers, no exception classes of your own for control flow; use try
    only around the one call that can raise
  - small pure functions (a checksum, a conversion) are fine in the program if they don't
    call a driver or record anything; a library for the DUT's own command protocol can be a
    separate module, like a driver
  - an item using an earlier item's result checks it is there, else INTERNAL_ERROR naming the
    item it needs
  Repeated code between test items is fine: it keeps each item readable on its own.
- Fail messages: an item's "fail" entries are {{"fid": ..., "msg": ...}}, msg at most 64
  characters (lint_script errors on longer), a terse hint for the operator or repair
  technician, like "3V_OUT low: check U7 R49".  Never copy a coverage parts list into msg.
  The test code must call ctx.record.fail_msg(ctx.item.fail[i]) when a measurement fails,
  as public/prism/scripts/example/prod_v0/tst00xx.py does, or the message is never shown.
- Test items: the first statement is `ctx = self.item_start()`, every path ends with
  `self.item_end(...)`, and the module file name matches the class name.  Use self.sleep()
  and self.check_abort(), not time.sleep().
- Traceability: record the serial number of every piece of test equipment the test uses
  (scope, power supply, programmer, jig controller, shared or per jig) in the setup item, as
  a string measurement, `ctx.record.measurement("dso_sn", sn, ResultAPI.UNIT_STRING)`, which
  has no limits and is only recorded.  Use the driver's unique_id when it has one.
- Store the unit serial number in key0 (`ctx.record.add_key("sn", value, slot=0)`), keep each
  `name:value` key within 64 characters and string measurements within 128.
- Key slots: use each key slot for the same id, with the same key name, in every test stage
  (for example BLT and FAT) and every product.  Ask for the customer's key slot table, and if
  there isn't one, propose one for all their products or product family, see
  docs/source/_traceability.rst Key Slot Plan.
- Never ask the customer to paste passwords, site_key, license files or user databases.  Never
  suggest committing real passwords to their repo, settings.json is per computer.
- The customer's fork may be private: keep their code and data in this conversation.
- Drivers: every driver that sets the number of channels must report the same number, in the
  same jig order, and a driver that returns 0 channels is shared by all the jigs of one Prism
  computer.  Lock shared equipment with `with self.shared_lock(<name>):`.  Equipment shared
  between Prism computers is not supported.  Get drivers with
  `self.shared_state.get_drivers(self.chan, type=...)`.
- Test coverage: analyse each passive part for Short, Open and Value, and each IC pin for Short
  and Open, see docs/source/_coverage.rst.  A fault is only covered if it moves a measurement
  outside the limits; when it doesn't, mark it partly or not covered and say why.
  Never plan more test points than BOND has header pins for, and assign each to the nearest
  header.  Functions BOND doesn't have go on the Pogo board, controlled through header pins.
- Pogo board design: start from Sistemi's template https://github.com/sistemicorp/a5800-BONDPogo
  (Altium), which is not in this repo.  The customer clones it, renames it, and pushes it to a
  new private repo (a fork of it can't be private).  Never move the template's BOND headers,
  the board outline can change.
  BOND population options differ between BONDs, so don't predict them: say BOND has some
  flexibility, and ask the customer to check their BOND against the BOND schematic
  public/prism/drivers/A4401_BOND/a4402-SCH_05.pdf.  See docs/source/prism_bond.rst
  Designing the Pogo Board for the steps, the stack up STEP model and the mechanical guidance.
- Prefer small, reviewable changes to the customer's files, and explain what each change does.
- Number your questions so the customer can answer them easily.
"""

PROMPT_MIGRATE = """\
Help me migrate my Prism/Lente deployment from version {from_version} to {to_version}.

1. Run repo_status to see my scripts version and whether my fork can take Sistemi's updates.
2. Read docs/source/_version_history.rst: the Upgrading section, and the Migration Guide of
   every version after {from_version} up to {to_version}.
3. Ask me (numbered) how many Lente and Prism computers I have, whether Lente chains to an
   upstream Lente, whether I use HTTPS, and which drivers my scripts use.
4. Run check_settings on my settings.json files (public/settings.json and any under deploy/).
5. Lint each of my scripts with lint_script, skipping public/prism/scripts/example.
6. Give me an ordered checklist for my deployment: repo merge, settings changes per computer,
   vendor tools, licence, image tags, and the order to upgrade Lente and the Prisms.
"""

PROMPT_TEST_SCRIPT = """\
Help me write a Prism test script and its Python test code for {product}, test stage
{stage}.

1. Read docs/source/prism_scripts.rst (Script Design first) and prism_programs.rst, and look
   at public/prism/scripts/example/prod_v0 (prod_0.scr, tst00xx.py) for the test item APIs.
2. Use python_api for test_item and record to check each API you use.
3. Ask me (numbered) what the stage tests, which instruments and drivers it uses
   (list_drivers), the limits, and how the unit serial number is found.  Ask for my key slot
   table, and look at my other scripts for the slots and key names they use.
4. Propose the file names and folder (see docs/source/_prodplan.rst Naming Proposal), then
   write the .scr and .py with a setup item first and a teardown item last.  The setup item
   records the serial number of each piece of test equipment as a string measurement.  Save
   the keys in the slots of my key slot table, using its constants.
5. Write one test item method per test, its steps in order, calling the drivers and
   ctx.record.measurement directly, flat like public/prism/scripts/example/BOND_v0/bond_P00xx.py.
   The script only lists the tests, with their limits as fields on each item.
6. Before you finish, check: could a technician change every limit in the script without
   reading Python?  Does the script hold any steps, expressions, commands or pins?  Does the
   code have a base class, a wrapper around a driver or ctx.record.measurement, a step object
   or context manager, meas()/check() helpers, or a unit map?  Can each test item be read top
   to bottom without opening another file or class?  Is each fail msg at most 64 characters,
   and does the code call ctx.record.fail_msg() for it?  Fix it if not.
7. Run lint_script on the new script and fix every ERROR.  Tell me how to run it with
   `python prism_dev.py --script <path>`.
"""

PROMPT_REVIEW_SCRIPT = """\
Review my Prism test script {script} and its Python test code.

1. Read docs/source/prism_scripts.rst Script Design and docs/source/prism_programs.rst.
2. Read the script and each test module it runs, and run lint_script on it.
3. Check the script is a list of tests with their limits, readable by a technician who is not
   a programmer.  List each place where it is not: steps or action lists, expressions, DUT
   commands, BOND pins, limits hidden in nested objects or in the code, a generic item that does
   unrelated tests, a script generated from another program.
4. Check the test code is simple: one method per test with its steps in order, drivers and
   ctx.record.measurement called directly, easy to follow for someone who did not write it.
   List each layer a reader has to open another file or class to follow: base classes or
   mixins, fixture classes around BOND, pins looked up by signal name, step objects or
   context managers that turn exceptions into results, meas()/check() helpers, unit maps,
   measurement names built from a prefix.  Compare with public/prism/scripts/example.
   Check each fail msg is a terse hint of at most 64 characters, not a parts list, and that
   the code calls ctx.record.fail_msg() when the measurement it belongs to fails.
5. Check the traceability: the unit serial number in key0, the key slots and names of my key
   slot table, and the serial number of each piece of test equipment in the setup item.
6. Give me the findings, most important first, and propose the changes as small steps.  Ask me
   before changing my files.
"""

PROMPT_BOND = """\
Help me use BOND (the Sistemi Bed of Nails tester) for {product}.

1. Read docs/source/prism_bond.rst and public/prism/drivers/A4401_BOND/README.md.
2. Look at public/prism/scripts/example/BOND_v0 and use python_api on
   public/prism/drivers/A4401_BOND/A4401_BOND.py for the BOND methods.
3. Ask me (numbered) which DUT signals connect to which BOND headers and pins, and what each
   signal needs (ADC, DAC, GPO, GPI, DUT supply, battery emulator).
4. If the Pogo board is not designed yet, take me through docs/source/prism_bond.rst
   Designing the Pogo Board: the a5800-BONDPogo template, the schematic, the layout, the stack
   up STEP model and the mechanical checks.
5. Help me write the Pogo board header definition file, and the test items that use it.
6. Lint the script with lint_script.
"""

PROMPT_ADD_EQUIPMENT = """\
Help me add {equipment} to my test jig, for one jig per instrument or shared by the jigs.

1. Read docs/source/prism_drivers.rst, sections Discover Channels, Shared Drivers, Locking
   Shared Equipment and Adding Test Equipment.
2. Ask me (numbered) for the make and model, how it connects (USB, Ethernet, serial), how many
   jigs each Prism computer runs, whether each jig has its own instrument or one is shared,
   and how the jigs are wired to it.
3. Use list_drivers to pick the closest included driver, for example agilent_dso_usb_1 for a
   VISA instrument, and read its section in prism_drivers.rst and its hwdrv file.
4. Propose the new driver folder and write the driver: how instruments are found, ordered by
   jig, and identified (unique_id), with an error when one is missing.
5. Write the setup item that gets the driver with get_drivers(self.chan, type=...) and records
   the instrument serial number as a string measurement (ResultAPI.UNIT_STRING), for a shared
   instrument also the input used, see docs/source/_traceability.rst Test Equipment.  Lock a
   shared instrument with self.shared_lock.
6. Document the driver: its arguments in the discover_channels doc string, and a README.md in
   the driver folder with the equipment, connection, per jig or shared, and setup steps.
7. Lint the script with lint_script.  Tell me how to run the driver's __main__ check and
   `python prism_dev.py --script <path>`.
"""

PROMPT_TEST_PLAN = """\
Help me lay out the production test plan for {product}.

1. Read docs/source/_prodplan.rst (Stages, Planning Your Test Stages, Naming Proposal) and
   docs/source/_traceability.rst.
2. Ask me (numbered) about my process steps, where the product is assembled, programmed and
   shipped, the sub-contractors, test time targets, and the yearly volume.
3. Propose the test stages, what each one tests, the jig and drivers for each, and how many
   Prism stations each needs.  Explain why each stage is there.
4. Propose the folder and file names for the scripts, and what each stage records for
   traceability.
"""

PROMPT_TRACEABILITY = """\
Help me define the database tracking for {product}: serial numbers, lots, firmware versions,
and test versions.

1. Read docs/source/_traceability.rst and docs/source/_database.rst.
2. Ask me (numbered) how a unit is identified, which ids and versions I need to search on,
   which test equipment each stage uses, where the lot comes from, and how I version my test
   scripts.
3. Propose the key slot table, one for all my products or product family, with the same slot
   and key name for an id in every stage (see Key Slot Plan), then the measurement names for
   versions and for the test equipment serial numbers, the lot sub with its regex, and the
   script naming and versioning.
4. Give me example SQL queries for my most common searches.
"""

PROMPT_DEPLOY = """\
Help me plan and install my Prism/Lente deployment.

1. Read docs/source/_system.rst, _deployment.rst (including Typical Deployment and Settings),
   _security.rst and the IP Addressing section of _prodplan.rst.
2. Ask me (numbered) how many production lines, test stations and factories I have, whether
   results must reach a cloud or head office Lente, and whether the LAN has internet access.
3. Propose the computers, the Lente hierarchy, IP addresses, image tags, and which settings
   are the same on every computer (site_key, prism_lente_pw).
4. Give me the install steps for Lente, then for each Prism, and use check_settings on my
   settings files.
"""

PROMPT_PRISM_COMPUTER = """\
Help me set up a Prism computer for the production floor.

1. Read the Prism Computer Checklist and Installing Prism/Lente Stations in
   docs/source/_deployment.rst, and the requirements in docs/source/prism_demo.rst.
2. Ask me (numbered) which scripts this station runs, so you can find the drivers it needs
   (list_scripts, list_drivers) and any vendor tools that must be installed.
3. Give me the steps in order, with the commands, and check its settings.json with
   check_settings (role prism).
4. Finish with the checks that prove the station works.
"""

PROMPT_COVERAGE = """\
Help me analyse the test coverage of {board}: which assembly faults (Short, Open, Value) my
production test can detect on each part, and how to improve it.

1. Read docs/source/_coverage.rst and docs/source/prism_bond.rst.
2. Ask me (numbered) for the schematic, the BOM, which nets have test points (or the PCB
   layout), which connectors and programming header the jig reaches, the MCU and whether it can
   run test firmware, the other equipment in the jig, and whether the layout can still change.
   Ask for each test point's location on the PCB.
   Through hole connector pins can be test points.  Check first that the JTAG/SWD, reset,
   target supply and GND pins are reachable, the board must be programmable in the jig.
   I may share files from outside this repo, keep them in this conversation.
3. Build the Components list: one row per passive part and one row per IC, transistor and
   connector pin, with Short, Open and Value marked Y, P, N or -.  Start from Common Gaps.
4. Propose the tests block by block, in the Test Order, with test ids, the BOND resource, Pogo
   board circuit or test firmware command each uses, the nominal value calculated from the
   schematic, and initial limits.  Fill in the Tests column of each part.
   For a function BOND doesn't have, propose a Pogo board circuit that BOND controls through
   the header pins.
5. List the Gaps: the parts not fully covered, why, and a mitigation.
6. List the test points to add, ranked by the faults each would detect.  If the layout is
   fixed, say which of them would justify a board respin.
7. Build the Pin Map: assign each test point and Pogo board circuit to a BOND header pin,
   nearest header first, using each test point's location on the PCB.  Never use more pins
   than the Pin Budget, when over it drop or share the test points that detect the fewest faults.
   The Pogo board is drawn from the a5800-BONDPogo template, see docs/source/prism_bond.rst
   Designing the Pogo Board.
8. Summarise per board: parts Full, Partial and None, and pins used per header.  Give the four
   lists as CSV, and ask me before writing any file to my repo.
"""


def _call(fn, *args):
    """ Run a knowledge function, its expected errors reach the model as tool errors
    """
    try:
        return fn(*args)
    except pk.KnowledgeError as e:
        raise ToolError(str(e))


def create_server():
    mcp = MCPServer(SERVER_NAME, instructions=INSTRUCTIONS, version=SERVER_VERSION)

    @mcp.tool()
    def list_docs() -> str:
        """List the documentation pages and READMEs with their titles and online links."""
        return _call(pk.list_docs)

    @mcp.tool()
    def read_doc(path: str, section: str = "") -> str:
        """Read a documentation page, or one section of it by heading text.

        path: a path from list_docs, for example docs/source/_deployment.rst
        section: optional heading text, for example "Settings.JSON File"
        """
        return _call(pk.read_doc, path, section or None)

    @mcp.tool()
    def search_docs(query: str, scope: str = "docs", max_results: int = 10) -> str:
        """Search the documentation (scope "docs"), the code and scripts ("code"), or both
        ("all").  Returns the best matching sections with line numbers."""
        return _call(pk.search_docs, query, scope, max_results)

    @mcp.tool()
    def read_file(path: str, start_line: int = 1, max_lines: int = 400) -> str:
        """Read a text file (or list a directory) in the scripts repo, with line numbers.
        Secrets (settings.json, keys, license, user databases) and results are refused."""
        return _call(pk.read_file, path, start_line, max_lines)

    @mcp.tool()
    def list_scripts() -> str:
        """List the Prism scripts (.scr) with their product, drivers, test modules and subs."""
        return _call(pk.list_scripts)

    @mcp.tool()
    def lint_script(path: str) -> str:
        """Lint a Prism script and the test item code it runs, like prism_dev.py --lint.
        Fix every ERROR before running the script in Prism."""
        return _call(pk.lint_script, path)

    @mcp.tool()
    def check_settings(path: str = "", role: str = "") -> str:
        """Check a settings.json for the current Prism/Lente version: missing, obsolete and
        example values.  Secret values are never shown.

        path: default public/settings.json, may be outside the repo
        role: "prism" or "lente", default guessed from the keys
        """
        return _call(pk.check_settings, path or None, role or None)

    @mcp.tool()
    def list_drivers() -> str:
        """List the Prism hardware drivers, their module paths for a script, and their docs."""
        return _call(pk.list_drivers)

    @mcp.tool()
    def python_api(target: str, include_private: bool = False) -> str:
        """Outline a Python file: classes, method signatures and doc strings.

        target: test_item (self.* in test code), record (ctx.record.*), result_api
        (ResultAPI constants and units), script_lint, or a repo path such as
        public/prism/drivers/A4401_BOND/A4401_BOND.py
        """
        return _call(pk.python_api, target, include_private)

    @mcp.tool()
    def repo_status() -> str:
        """Scripts version, branch, remotes, and how far the repo is behind Sistemi's scripts
        (from the last fetch)."""
        return _call(pk.repo_status)

    @mcp.prompt(title="Migrate to a new version")
    def migrate_version(from_version: str = "0.8", to_version: str = "0.9") -> str:
        """Plan a Prism/Lente version migration for this deployment."""
        return PROMPT_MIGRATE.format(from_version=from_version, to_version=to_version)

    @mcp.prompt(title="Write a test script")
    def write_test_script(product: str = "my product", stage: str = "T01") -> str:
        """Write a Prism script and its Python test code for one test stage."""
        return PROMPT_TEST_SCRIPT.format(product=product, stage=stage)

    @mcp.prompt(title="Review a test script")
    def review_test_script(script: str = "my script") -> str:
        """Review a script and its test code: readable list of tests, simple code, traceability."""
        return PROMPT_REVIEW_SCRIPT.format(script=script)

    @mcp.prompt(title="Use BOND")
    def use_bond(product: str = "my product") -> str:
        """Set up BOND, its Pogo board header definition, and BOND test items."""
        return PROMPT_BOND.format(product=product)

    @mcp.prompt(title="Analyse test coverage")
    def analyze_coverage(board: str = "my board") -> str:
        """Analyse which Short, Open and Value faults the test detects on each part of a PCBA."""
        return PROMPT_COVERAGE.format(board=board)

    @mcp.prompt(title="Add test equipment")
    def add_equipment(equipment: str = "an instrument") -> str:
        """Add test equipment to a jig, one per jig or shared by the jigs, with its driver."""
        return PROMPT_ADD_EQUIPMENT.format(equipment=equipment)

    @mcp.prompt(title="Plan test stages")
    def plan_test_stages(product: str = "my product") -> str:
        """Lay out the test plan: how many stages, what each tests, jigs and stations."""
        return PROMPT_TEST_PLAN.format(product=product)

    @mcp.prompt(title="Plan traceability")
    def plan_traceability(product: str = "my product") -> str:
        """Define serial numbers, lots, firmware versions and test versioning in the results."""
        return PROMPT_TRACEABILITY.format(product=product)

    @mcp.prompt(title="Plan a deployment")
    def plan_deployment() -> str:
        """Plan and install Lente and Prism computers for production."""
        return PROMPT_DEPLOY

    @mcp.prompt(title="Set up a Prism computer")
    def setup_prism_computer() -> str:
        """Set up and check one Prism computer for the production floor."""
        return PROMPT_PRISM_COMPUTER

    return mcp


def main():
    create_server().run()


if __name__ == "__main__":
    main()
