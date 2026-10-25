# Prism Assistant

An MCP server that helps an AI assistant (Claude Code, Claude Desktop, or another MCP client)
answer questions about your Prism/Lente project: version migration, test scripts and code,
BOND, test plans, traceability, deployment and Prism computers.

It is read-only, and never reads `settings.json`, keys, the license or user databases.

    cd ~/git/scripts
    source .venv/bin/activate
    pip install -r assistant/requirements.txt

Claude Code uses `.mcp.json` at the top of the repo.  See the documentation page
`docs/source/_assistant.rst` (online: Prism Assistant) for other clients and the tools.

- `prism_assistant.py` - the MCP server, its instructions and prompts
- `prism_knowledge.py` - the tools, plain Python, tested in `tests/test_assistant_*.py`
