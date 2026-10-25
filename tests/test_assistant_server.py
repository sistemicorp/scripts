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
PROMPTS = {"migrate_version", "write_test_script", "use_bond", "plan_test_stages",
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
