"""Tests for assistant/prism_knowledge.py, the Prism Assistant MCP server's tools.

Run from the scripts repo root: python -m pytest tests
Most tests build a small scripts repo in tmp_path, so they don't depend on the docs.
"""
import os
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "assistant"))
import prism_knowledge as pk  # noqa: E402

DOC_RST = """\
Deployment
##########

Intro text.

Settings
********

The site_key must match.

Other Settings
==============

session_inactive_timeout_s

Docker
******

docker ps
"""

DOC_MD = """\
# Driver Guide

```
# not a heading
```

## Install

tools folder
"""

SCRIPT = """\
// a comment
{
  "subs": {"Lot": {"title": "Lot", "type": "str", "widget": "textinput", "default": "1"}},
  "info": {"product": "widget", "bom": "B1", "lot": "%%Lot", "location": "here"},
  "config": {"fail_fast": true, "drivers": ["public.prism.drivers.fake.hwdrv_fake"]},
  "tests": [{"module": "public.prism.scripts.mine.tst", "options": {},
             "items": [{"id": "SETUP"}, {"id": "TRDN"}]}]
}
"""

SETTINGS_GOOD = """\
{
  // comment
  "demo": false,
  "site_key": "0123456789abcdefXYZ",
  "prism_lente_pw": "a-real-password",
  "auto_sync_scripts": true,
  "health_checks": {}
}
"""


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(text))
    return path


@pytest.fixture
def repo(tmp_path):
    root = str(tmp_path)
    write(root, "docs/source/_deployment.rst", DOC_RST)
    write(root, "public/prism/drivers/fake/README.md", DOC_MD)
    write(root, "public/prism/drivers/fake/hwdrv_fake.py", "class HWDriver:\n    pass\n")
    write(root, "public/prism/scripts/mine/tst_0.scr", SCRIPT)
    write(root, "public/settings.json", SETTINGS_GOOD)
    write(root, "public/sistemi.lic", "secret")
    write(root, "public/.ssh/id_ed25519", "secret")
    write(root, "deploy/lente/settings.json", SETTINGS_GOOD)
    write(root, "public/prism/api.py", '"""api"""\nclass ResultAPI:\n    PASS = "PASS"\n')
    return root


# --- docs -----------------------------------------------------------------


def test_list_docs_titles_and_links(repo):
    out = pk.list_docs(root=repo)
    assert "docs/source/_deployment.rst - Deployment" in out
    assert "build/html/_deployment.html" in out
    assert "public/prism/drivers/fake/README.md - Driver Guide" in out


def test_read_doc_section_stops_at_same_level(repo):
    out = pk.read_doc("docs/source/_deployment.rst", "settings", root=repo)
    assert "The site_key must match." in out
    assert "session_inactive_timeout_s" in out  # sub section is included
    assert "docker ps" not in out


def test_read_doc_markdown_skips_code_block_headings(repo):
    """[Edge] a '#' line inside a code block is not a heading"""
    out = pk.read_doc("public/prism/drivers/fake/README.md", "install", root=repo)
    assert "tools folder" in out


def test_read_doc_unknown_section_lists_sections(repo):
    """[Unhappy]"""
    with pytest.raises(pk.KnowledgeError, match="Settings, Other Settings"):
        pk.read_doc("docs/source/_deployment.rst", "nope", root=repo)


def test_search_docs_ranks_section(repo):
    out = pk.search_docs("site_key", root=repo)
    assert "_deployment.rst [Settings]" in out
    assert "The site_key must match." in out


def test_search_docs_no_terms(repo):
    """[Unhappy] a query with only short words"""
    with pytest.raises(pk.KnowledgeError, match="no search terms"):
        pk.search_docs("a", root=repo)


def test_search_code_scope(repo):
    out = pk.search_docs("HWDriver", scope="code", root=repo)
    assert "public/prism/drivers/fake/hwdrv_fake.py" in out


# --- read_file ------------------------------------------------------------


@pytest.mark.parametrize("path", ["public/settings.json", "deploy/lente/settings.json",
                                  "public/sistemi.lic", "public/.ssh/id_ed25519"])
def test_read_file_refuses_secrets(repo, path):
    """[Unhappy]"""
    with pytest.raises(pk.KnowledgeError, match="not readable"):
        pk.read_file(path, root=repo)


def test_read_file_refuses_outside_repo(repo):
    """[Unhappy]"""
    with pytest.raises(pk.KnowledgeError, match="outside"):
        pk.read_file("../x", root=repo)


def test_read_file_refuses_symlink_out_of_repo(repo, tmp_path_factory):
    """[Unhappy] a link inside the repo to a file outside it"""
    outside = tmp_path_factory.mktemp("outside")
    target = write(str(outside), "x.txt", "secret")
    os.symlink(target, os.path.join(repo, "link.txt"))
    with pytest.raises(pk.KnowledgeError, match="outside"):
        pk.read_file("link.txt", root=repo)


def test_read_file_lines(repo):
    out = pk.read_file("public/prism/scripts/mine/tst_0.scr", start_line=2, max_lines=1,
                       root=repo)
    assert "lines 2-2 of" in out
    assert "    2  {" in out
    assert "more lines" in out


def test_read_file_directory_hides_secrets(repo):
    """[Edge] a directory listing leaves out the secret files"""
    out = pk.read_file("public", root=repo)
    assert "prism" in out
    assert "settings.json" not in out and "sistemi.lic" not in out


# --- scripts and settings ---------------------------------------------------


def test_list_scripts(repo):
    out = pk.list_scripts(root=repo)
    assert "public/prism/scripts/mine/tst_0.scr" in out
    assert "product: widget, items: 2" in out
    assert "subs: Lot" in out


def test_list_scripts_bad_json(repo):
    """[Unhappy]"""
    write(repo, "public/prism/scripts/mine/bad.scr", "{ nope")
    assert "bad.scr: cannot parse" in pk.list_scripts(root=repo)


def test_lint_example_script():
    """Lints a real example with the real linter"""
    out = pk.lint_script("public/prism/scripts/example/prod_v0/prod_1.scr")
    assert out.endswith("0 errors, 0 warnings")


def test_lint_reports_missing_module(repo):
    """[Unhappy] the test module file does not exist"""
    out = pk.lint_script("public/prism/scripts/mine/tst_0.scr", root=repo)
    assert "ERROR" in out


def test_check_settings_good(repo):
    out = pk.check_settings(root=repo)
    assert "ERROR" not in out and "WARN" not in out
    assert "checked as prism" in out


def test_check_settings_never_shows_values(repo):
    out = pk.check_settings(root=repo)
    assert "0123456789abcdefXYZ" not in out
    assert "a-real-password" not in out


@pytest.mark.parametrize("settings, expect", [
    ('{"demo": false, "prism_lente_pw": "x"}', "ERROR site_key is not set"),
    ('{"demo": false, "site_key": "demo-site-key-change-me", "prism_lente_pw": "x"}',
     "ERROR site_key is the demo value"),
    ('{"site_key": "short", "prism_lente_pw": "x"}', "at least 16"),
    ('{"site_key": "0123456789abcdefX"}', "ERROR prism_lente_pw is not set"),
    ('{"site_key": "0123456789abcdefX", "prism_lente_pw": "mysecret1"}',
     "WARN prism_lente_pw is the example value"),
    ('{"manifest_pw": "x"}', "INFO manifest_pw: no longer used"),
    ('{"use_https": true}', "ERROR use_https is on but cert.pem"),
    ('{"postgres": {}, "result_server_url": "http://x"}', "lente_lente_pw is not"),
])
def test_check_settings_problems(repo, settings, expect):
    """[Unhappy]"""
    write(repo, "public/settings.json", settings)
    assert expect in pk.check_settings(root=repo)


def test_check_settings_demo_allows_examples(repo):
    """[Edge] the demo values are accepted with demo on, with a warning about demo"""
    write(repo, "public/settings.json",
          '{"demo": true, "site_key": "demo-site-key-change-me", "prism_lente_pw": "mysecret1"}')
    out = pk.check_settings(root=repo)
    assert "ERROR" not in out
    assert 'WARN "demo": true' in out


def test_check_settings_bad_json(repo):
    """[Unhappy]"""
    write(repo, "public/settings.json", "{ nope")
    assert "cannot parse" in pk.check_settings(root=repo)


def test_check_settings_not_json(repo):
    """[Unhappy] only .json files are checked"""
    with pytest.raises(pk.KnowledgeError, match="not a settings"):
        pk.check_settings("public/sistemi.lic", root=repo)


# --- drivers, APIs, repo ----------------------------------------------------


def test_list_drivers(repo):
    out = pk.list_drivers(root=repo)
    assert "module: public.prism.drivers.fake.hwdrv_fake" in out
    assert "public/prism/drivers/fake/README.md" in out


def test_python_api_alias():
    out = pk.python_api("record")
    assert "def add_key(self, key, value, slot=None)" in out
    assert "def measurement(" in out


def test_python_api_constants(repo):
    out = pk.python_api("result_api", root=repo)
    assert "PASS = 'PASS'" in out


def test_repo_status_without_sistemi_remote(repo):
    """[Edge] a repo that is not a git repo, or has no sistemicorp remote"""
    out = pk.repo_status(root=repo)
    assert "No remote points to sistemicorp/scripts" in out


def test_strip_credentials():
    assert pk._strip_credentials("https://user:tok@github.com/a/b") == "https://github.com/a/b"
