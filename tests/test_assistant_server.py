"""Tests for assistant/prism_assistant.py, the Prism Assistant MCP server.

Needs the mcp package (pip install -r assistant/requirements.txt), skipped without it.
The server is connected in-process with the MCP client.
"""
import asyncio
import os
import sys

import pytest

pytest.importorskip("mcp")
from mcp import Client  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "assistant"))
import prism_assistant  # noqa: E402

TOOLS = {"list_docs", "read_doc", "search_docs", "read_file", "list_scripts", "lint_script",
         "check_settings", "list_drivers", "python_api", "repo_status"}
PROMPTS = {"migrate_version", "write_test_script", "review_test_script", "use_bond",
           "add_equipment", "plan_test_stages", "analyze_coverage",
           "plan_traceability", "plan_deployment", "setup_prism_computer"}


def run(coro_fn):
    async def main():
        async with Client(prism_assistant.create_server()) as client:
            return await coro_fn(client)
    return asyncio.run(main())


def test_lists_tools_and_prompts():
    async def go(c):
        return await c.list_tools(), await c.list_prompts()
    tools, prompts = run(go)
    assert {t.name for t in tools.tools} == TOOLS
    assert {p.name for p in prompts.prompts} == PROMPTS


def test_call_lint_tool():
    async def go(c):
        return await c.call_tool("lint_script",
                                 {"path": "public/prism/scripts/example/prod_v0/prod_1.scr"})
    r = run(go)
    assert not r.is_error
    assert "0 errors" in r.content[0].text


def test_refused_file_gives_reason():
    """[Unhappy] the model sees why a file is refused"""
    async def go(c):
        return await c.call_tool("read_file", {"path": "public/settings.json"})
    r = run(go)
    assert r.is_error
    assert "not readable by the assistant" in r.content[0].text


def test_migrate_prompt_has_versions():
    async def go(c):
        return await c.get_prompt("migrate_version", {"from_version": "0.8", "to_version": "0.9"})
    text = run(go).messages[0].content.text
    assert "from version 0.8 to 0.9" in text
    assert "_version_history.rst" in text


def test_add_equipment_prompt_reads_drivers_doc():
    async def go(c):
        return await c.get_prompt("add_equipment", {"equipment": "a power supply"})
    text = run(go).messages[0].content.text
    assert "add a power supply to my test jig" in text
    assert "prism_drivers.rst" in text
    assert "UNIT_STRING" in text  # equipment serial number is recorded


def test_analyze_coverage_prompt_reads_coverage_doc():
    async def go(c):
        return await c.get_prompt("analyze_coverage", {"board": "the main board"})
    text = run(go).messages[0].content.text
    assert "test coverage of the main board" in text
    assert "_coverage.rst" in text
    assert "test points to add" in text
    assert "Pin Budget" in text


def test_key_slot_table_in_instructions_and_prompts():
    assert "Key Slot Plan" in prism_assistant.INSTRUCTIONS
    for name in ("write_test_script", "plan_traceability"):
        async def go(c, name=name):
            return await c.get_prompt(name, {})
        assert "key slot table" in run(go).messages[0].content.text


def test_pogo_board_template_in_instructions_and_prompts():
    assert "a5800-BONDPogo" in prism_assistant.INSTRUCTIONS
    assert "a4402-SCH_05.pdf" in prism_assistant.INSTRUCTIONS
    for name in ("use_bond", "analyze_coverage"):
        async def go(c, name=name):
            return await c.get_prompt(name, {})
        assert "Designing the Pogo Board" in run(go).messages[0].content.text


def test_script_prompts_read_script_design():
    async def go(c):
        return (await c.get_prompt("write_test_script", {"product": "P1", "stage": "T01"}),
                await c.get_prompt("review_test_script", {"script": "P1/P1_T01.scr"}))
    for r in run(go):
        assert "Script Design" in r.messages[0].content.text


def test_flat_test_code_rules():
    assert "inheriting only from TestItem" in prism_assistant.INSTRUCTIONS
    assert "ResultAPI.UNIT_*" in prism_assistant.INSTRUCTIONS

    async def go(c):
        return (await c.get_prompt("write_test_script", {"product": "P1", "stage": "T01"}),
                await c.get_prompt("review_test_script", {"script": "P1/P1_T01.scr"}))
    for r in run(go):
        text = r.messages[0].content.text
        assert "public/prism/scripts/example" in text
        assert "unit map" in text
