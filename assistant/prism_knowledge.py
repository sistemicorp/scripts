#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026

Read-only helpers behind the Prism Assistant MCP server.

Every function works on a scripts repo (a customer's fork of sistemicorp/scripts)
and returns plain text, so it can be tested without MCP.  Nothing here writes
files, and secrets (passwords, keys, license, users) are never returned.
"""
import ast
import fnmatch
import glob
import os
import re
import subprocess
import sys

import jstyleson

ASSISTANT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ENV = "PRISM_REPO"
DEFAULT_REPO = os.path.dirname(ASSISTANT_DIR)

DOCS_DIR = "docs/source"
SCRIPTS_DIR = "public/prism/scripts"
DRIVERS_DIR = "public/prism/drivers"
DRIVERS_DOC = "docs/source/prism_drivers.rst"
SETTINGS_FILE = "public/settings.json"
VERSION_FILE = "public/VERSION"
ONLINE_DOCS = "https://sistemicorp.github.io/scripts/build/html/{}.html"
SISTEMI_REMOTE_RE = r"sistemicorp/scripts(\.git)?$"
UPSTREAM_BRANCH = "master"

MAX_FILE_BYTES = 256 * 1024
DEFAULT_MAX_LINES = 400
DEFAULT_MAX_RESULTS = 10
SNIPPET_LINES = 3
GIT_TIMEOUT_S = 10
MIN_TERM_LEN = 2

# never returned by read_file, matched on the repo relative path
DENY_DIRS = (".git", ".venv", ".venv312", "venv", "log", "public/log", "public/result",
             "public/traveller", "public/postgdata", "public/tools", "public/.ssh",
             "docs/build", "__pycache__", ".idea", ".vscode")
DENY_NAMES = ("settings*.json", ".env", "*.pem", "*.key", "*.lic", "*.sqlite", "*.crypt",
              "id_*", "known_hosts", ".git_*", "*.pyc", "*.zip")

RST_UNDERLINE_RE = r"^([=\-*#^~+\"'`])\1{2,}\s*$"
MD_HEADING_RE = r"^(#{1,6})\s+(.*)$"
DOC_GLOBS = ("docs/source/*.rst", "public/prism/drivers/*/README.md",
             "public/prism/drivers/*/server/README.md", "public/prism/scripts/*/README.md",
             "public/prism/scripts/*/*/README.md", "README.md", "assistant/README.md")
CODE_EXTS = (".py", ".scr", ".sh", "._json")
CODE_DIRS = ("public/prism", "core", "hooks")
CODE_FILES = ("prism_dev.py", "prism_subs.py", "public/prism.sh", "public/lente.sh",
              "public/git_pull_watcher.sh")

API_ALIASES = {
    "test_item": "core/test_item.py",
    "record": "public/prism/ResultBaseKeysV1.py",
    "result_api": "public/prism/api.py",
    "script_lint": "public/prism/script_lint.py",
}

# settings.json checks
SECRET_KEYS = ("prism_lente_pw", "lente_lente_pw", "site_key", "manifest_pw",
               "result_encrypt_pw")
EXAMPLE_PASSWORDS = {"prism_lente_pw": "mysecret1", "lente_lente_pw": "mysecret3"}
EXAMPLE_POSTGRES_PW = "qwerty"
SITE_KEY_DEMO = "demo-site-key-change-me"
SITE_KEY_MIN_LEN = 16
OBSOLETE_KEYS = {
    "manifest_pw": "no longer used since 0.9, remove it",
    "result_encrypt_pw": "replaced by site_key in 0.9, remove it",
    "use_rpc_over_status_updates": "removed in 0.9, Lente sends actions in the ping reply",
}
HTTPS_FILES = ("cert.pem", "key.pem")
LENTE_ONLY_KEYS = ("postgres", "root_authority", "result_server_url", "lente_lente_pw")
LEVEL_ERROR = "ERROR"
LEVEL_WARN = "WARN"
LEVEL_INFO = "INFO"
LEVEL_OK = "OK"


class KnowledgeError(Exception):
    pass


def repo_root():
    return os.path.abspath(os.environ.get(REPO_ENV, DEFAULT_REPO))


def _rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def _denied(rel):
    parts = rel.split("/")
    for d in DENY_DIRS:
        d_parts = d.split("/")
        for i in range(len(parts) - len(d_parts) + 1):
            if parts[i:i + len(d_parts)] == d_parts:
                return True
    return any(fnmatch.fnmatch(parts[-1], n) for n in DENY_NAMES)


def resolve(path, root=None, check_deny=True):
    """ Repo path -> absolute path, refuses paths outside the repo and secrets
    """
    root = root or repo_root()
    full = os.path.realpath(os.path.join(root, path))
    if full != root and not full.startswith(root + os.sep):
        raise KnowledgeError(f"{path}: outside the scripts repo")
    rel = _rel(full, root)
    if check_deny and _denied(rel):
        raise KnowledgeError(f"{rel}: not readable by the assistant (secret or generated file)")
    if not os.path.exists(full):
        raise KnowledgeError(f"{rel}: does not exist")
    return full


def _read_text(full):
    if os.path.getsize(full) > MAX_FILE_BYTES:
        raise KnowledgeError(f"{os.path.basename(full)}: larger than {MAX_FILE_BYTES} bytes")
    try:
        with open(full, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        raise KnowledgeError(f"{os.path.basename(full)}: not a text file")


def _glob(root, patterns):
    found = []
    for pattern in patterns:
        for full in sorted(glob.glob(os.path.join(root, pattern))):
            rel = _rel(full, root)
            if not _denied(rel) and rel not in found:
                found.append(rel)
    return found


# --- docs -----------------------------------------------------------------


def _headings(lines, is_rst):
    """ [(line_idx, level, title)], level 0 is the highest
    - rst levels are in order of first use of each underline character
    """
    out = []
    if is_rst:
        chars = []
        for i in range(1, len(lines)):
            m = re.match(RST_UNDERLINE_RE, lines[i])
            title = lines[i - 1].strip()
            if not m or not title or re.match(RST_UNDERLINE_RE, lines[i - 1]):
                continue
            if len(lines[i].rstrip()) < len(title):
                continue
            if m.group(1) not in chars:
                chars.append(m.group(1))
            out.append((i - 1, chars.index(m.group(1)), title))
    else:
        in_code = False
        for i, line in enumerate(lines):
            if line.startswith("```"):
                in_code = not in_code
            m = re.match(MD_HEADING_RE, line)
            if m and not in_code:
                out.append((i, len(m.group(1)) - 1, m.group(2).strip()))
    return out


def _sections(text, is_rst):
    """ [(title, start_line, end_line)] covering the whole text
    """
    lines = text.splitlines()
    heads = _headings(lines, is_rst)
    out = []
    first = heads[0][0] if heads else len(lines)
    if first > 0:
        out.append(("(top)", 0, first))
    for n, (idx, _, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        out.append((title, idx, end))
    return out


def _doc_title(text, is_rst):
    heads = _headings(text.splitlines(), is_rst)
    return heads[0][2] if heads else ""


def _online_url(rel):
    if rel.startswith(DOCS_DIR + "/") and rel.endswith(".rst"):
        return ONLINE_DOCS.format(os.path.basename(rel)[:-len(".rst")])
    return None


def list_docs(root=None):
    """ The documentation pages and READMEs, with their titles
    """
    root = root or repo_root()
    out = ["Documentation (path - title):"]
    for rel in _glob(root, DOC_GLOBS):
        text = _read_text(os.path.join(root, rel))
        title = _doc_title(text, rel.endswith(".rst"))
        url = _online_url(rel)
        out.append(f"- {rel} - {title}" + (f" ({url})" if url else ""))
    return "\n".join(out)


def read_doc(path, section=None, root=None):
    """ A doc page, or one section of it (heading text, case insensitive)
    """
    root = root or repo_root()
    full = resolve(path, root)
    rel = _rel(full, root)
    text = _read_text(full)
    is_rst = rel.endswith(".rst")
    lines = text.splitlines()
    url = _online_url(rel)
    header = f"# {rel}" + (f"\nOnline: {url}" if url else "")
    if not section:
        return header + "\n\n" + text

    heads = _headings(lines, is_rst)
    want = section.strip().lower()
    for n, (idx, level, title) in enumerate(heads):
        if title.lower() != want and want not in title.lower():
            continue
        end = len(lines)
        for idx2, level2, _ in heads[n + 1:]:
            if level2 <= level:
                end = idx2
                break
        return header + f"\nSection: {title}\n\n" + "\n".join(lines[idx:end])

    titles = ", ".join(t for _, _, t in heads)
    raise KnowledgeError(f"{rel}: no section '{section}', sections are: {titles}")


def _terms(query):
    return [t for t in re.findall(r"[\w./-]+", query.lower()) if len(t) >= MIN_TERM_LEN]


def _code_files(root):
    found = []
    for d in CODE_DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, d)):
            dirnames[:] = sorted(x for x in dirnames
                                 if not _denied(_rel(os.path.join(dirpath, x), root)))
            for name in sorted(filenames):
                rel = _rel(os.path.join(dirpath, name), root)
                if name.endswith(CODE_EXTS) and not _denied(rel):
                    found.append(rel)
    found += [f for f in CODE_FILES if os.path.exists(os.path.join(root, f))]
    return found


def search_docs(query, scope="docs", max_results=DEFAULT_MAX_RESULTS, root=None):
    """ Rank doc sections (or code files) by how many query terms they contain
    :param scope: "docs", "code" or "all"
    """
    root = root or repo_root()
    terms = _terms(query)
    if not terms:
        raise KnowledgeError("query has no search terms")

    units = []  # (rel, title, start, lines)
    if scope in ("docs", "all"):
        for rel in _glob(root, DOC_GLOBS):
            text = _read_text(os.path.join(root, rel))
            lines = text.splitlines()
            for title, start, end in _sections(text, rel.endswith(".rst")):
                units.append((rel, title, start, lines[start:end]))
    if scope in ("code", "all"):
        for rel in _code_files(root):
            try:
                text = _read_text(os.path.join(root, rel))
            except KnowledgeError:
                continue
            units.append((rel, "", 0, text.splitlines()))
    if not units:
        raise KnowledgeError(f"unknown scope '{scope}', use docs, code or all")

    scored = []
    for rel, title, start, lines in units:
        body = "\n".join(lines).lower()
        hits = [t for t in terms if t in body]
        if not hits:
            continue
        score = len(hits) * 100 + sum(body.count(t) for t in hits)
        score += sum(50 for t in terms if t in title.lower())
        scored.append((score, rel, title, start, lines))
    scored.sort(key=lambda s: -s[0])

    out = [f"Results for '{query}' ({scope}):"]
    for score, rel, title, start, lines in scored[:max_results]:
        snippet = []
        for i, line in enumerate(lines):
            if any(t in line.lower() for t in terms):
                snippet.append(f"    {start + i + 1}: {line.strip()}")
            if len(snippet) >= SNIPPET_LINES:
                break
        where = f"{rel} [{title}]" if title else rel
        out.append(f"- {where}\n" + "\n".join(snippet))
    if len(out) == 1:
        out.append("no matches, try other words or scope='all'")
    return "\n".join(out)


def read_file(path, start_line=1, max_lines=DEFAULT_MAX_LINES, root=None):
    """ Lines of a text file in the repo, numbered
    """
    root = root or repo_root()
    full = resolve(path, root)
    if os.path.isdir(full):
        names = sorted(n for n in os.listdir(full)
                       if not _denied(_rel(os.path.join(full, n), root)))
        return f"# {_rel(full, root)}/ (directory)\n" + "\n".join(names)
    lines = _read_text(full).splitlines()
    first = max(start_line, 1)
    last = min(first - 1 + max_lines, len(lines))
    body = "\n".join(f"{i + 1:5d}  {lines[i]}" for i in range(first - 1, last))
    more = f"\n... {len(lines) - last} more lines" if last < len(lines) else ""
    return f"# {_rel(full, root)} lines {first}-{last} of {len(lines)}\n{body}{more}"


# --- scripts --------------------------------------------------------------


def _load_script(full):
    return jstyleson.loads(_read_text(full))


def list_scripts(root=None):
    """ The .scr files under public/prism/scripts, with product, drivers and modules
    """
    root = root or repo_root()
    base = os.path.join(root, SCRIPTS_DIR)
    out = ["Scripts:"]
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if not _denied(_rel(os.path.join(dirpath, d),
                                                                     root)))
        for name in sorted(filenames):
            if not name.endswith(".scr"):
                continue
            full = os.path.join(dirpath, name)
            rel = _rel(full, root)
            try:
                s = _load_script(full)
            except (ValueError, KnowledgeError) as e:
                out.append(f"- {rel}: cannot parse: {e}")
                continue
            info = s.get("info", {}) if isinstance(s, dict) else {}
            drivers = [d[0] if isinstance(d, list) else d
                       for d in s.get("config", {}).get("drivers", [])]
            tests = s.get("tests", [])
            modules = [t.get("module", "?") for t in tests if isinstance(t, dict)]
            n_items = sum(len(t.get("items", [])) for t in tests if isinstance(t, dict))
            subs = list(s.get("subs", {}).keys())
            out.append(f"- {rel}\n    product: {info.get('product')}, items: {n_items}"
                       f"\n    drivers: {', '.join(drivers)}\n    modules: {', '.join(modules)}"
                       + (f"\n    subs: {', '.join(subs)}" if subs else ""))
    return "\n".join(out)


def lint_script(path, root=None):
    """ Run the Prism script linter, like prism_dev.py --lint
    """
    root = root or repo_root()
    full = resolve(path, root)
    if root not in sys.path:
        sys.path.insert(0, root)
    from public.prism.script_lint import lint_script as _lint, errors

    try:
        script = _load_script(full)
    except ValueError as e:
        return f"{_rel(full, root)}: not valid JSON (comments allowed): {e}"
    findings = _lint(script, subs_applied=False, root=root)
    n_err = len(errors(findings))
    head = (f"{_rel(full, root)}: {n_err} errors, {len(findings) - n_err} warnings")
    return "\n".join([head] + [str(f) for f in findings])


# --- settings.json ----------------------------------------------------------


def _settings_path(path, root):
    if not path:
        path = SETTINGS_FILE
    full = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    if os.path.basename(full) != "settings.json" and not full.endswith(".json"):
        raise KnowledgeError(f"{path}: not a settings .json file")
    if not os.path.isfile(full):
        raise KnowledgeError(f"{path}: does not exist")
    return full


def check_settings(path=None, role=None, root=None):
    """ Check a settings.json for the current Prism/Lente version, values are not shown
    :param role: "prism" or "lente", default guessed from the keys
    """
    root = root or repo_root()
    full = _settings_path(path, root)
    try:
        s = jstyleson.loads(_read_text(full))
    except ValueError as e:
        return f"{full}: {LEVEL_ERROR} cannot parse (// comments are allowed): {e}"
    if not isinstance(s, dict):
        return f"{full}: {LEVEL_ERROR} must be a JSON object"

    if role not in ("prism", "lente"):
        role = "lente" if "postgres" in s or "root_authority" in s else "prism"
    demo = s.get("demo", False) is True
    out = []

    def add(level, msg):
        out.append(f"{level} {msg}")

    for key in ("prism_lente_pw",):
        if not s.get(key):
            add(LEVEL_ERROR, f"{key} is not set, all station requests are refused")
        elif s.get(key) == EXAMPLE_PASSWORDS[key] and not demo:
            add(LEVEL_WARN, f"{key} is the example value, set a real password")
        else:
            add(LEVEL_OK, f"{key} is set")

    site_key = s.get("site_key")
    if not isinstance(site_key, str) or not site_key:
        add(LEVEL_ERROR, "site_key is not set")
    elif site_key == SITE_KEY_DEMO and not demo:
        add(LEVEL_ERROR, "site_key is the demo value, which only works with \"demo\": true")
    elif len(site_key) < SITE_KEY_MIN_LEN:
        add(LEVEL_ERROR, f"site_key must be at least {SITE_KEY_MIN_LEN} characters")
    else:
        add(LEVEL_OK, "site_key is set (it must be the same on every computer)")

    if demo:
        add(LEVEL_WARN, "\"demo\": true, the demo users exist, turn it off for production")

    for key, why in OBSOLETE_KEYS.items():
        if key in s:
            add(LEVEL_INFO, f"{key}: {why}")

    if s.get("use_https"):
        folder = os.path.dirname(full)
        for name in HTTPS_FILES:
            if not os.path.isfile(os.path.join(folder, name)):
                add(LEVEL_ERROR, f"use_https is on but {name} is not next to settings.json")

    if role == "lente":
        pg = s.get("postgres", {}).get("resultbasekeysv1", {})
        if not pg:
            add(LEVEL_ERROR, "postgres.resultbasekeysv1 (user, pw, ip) is not set")
        elif pg.get("pw") == EXAMPLE_POSTGRES_PW and not demo:
            add(LEVEL_WARN, "postgres pw is the example value, set a real password")
        if s.get("result_server_url"):
            if not s.get("lente_lente_pw"):
                add(LEVEL_ERROR, "result_server_url is set but lente_lente_pw is not")
            elif s.get("lente_lente_pw") == EXAMPLE_PASSWORDS["lente_lente_pw"] and not demo:
                add(LEVEL_WARN, "lente_lente_pw is the example value, set a real password")
        if "root_authority" not in s:
            add(LEVEL_INFO, "root_authority is not set, true for the top Lente of your scripts")
    else:
        extra = [k for k in LENTE_ONLY_KEYS if k in s]
        if extra:
            add(LEVEL_INFO, f"Lente only keys can be removed on a Prism: {', '.join(extra)}")

    if "auto_sync_scripts" not in s:
        add(LEVEL_INFO, "auto_sync_scripts is not set, Lente will not sync scripts automatically")
    if "health_checks" not in s:
        add(LEVEL_INFO, "health_checks is not set, no disk space checks")

    head = (f"{full} (checked as {role}, values are not shown).  Also check the keys "
            "that must match Lente: site_key, prism_lente_pw.")
    return "\n".join([head] + out)


# --- drivers and APIs -------------------------------------------------------


def list_drivers(root=None):
    """ The drivers in public/prism/drivers, with their hwdrv modules and docs
    """
    root = root or repo_root()
    base = os.path.join(root, DRIVERS_DIR)
    doc = os.path.join(root, DRIVERS_DOC)
    sections = set()
    if os.path.isfile(doc):
        sections = {t for _, _, t in _headings(_read_text(doc).splitlines(), True)}
    out = ["Drivers (use the module path in the script config.drivers).  To add test "
           f"equipment, read {DRIVERS_DOC} section 'Adding Test Equipment':"]
    for name in sorted(os.listdir(base)):
        d = os.path.join(base, name)
        if not os.path.isdir(d) or _denied(_rel(d, root)):
            continue
        hwdrvs = sorted(f[:-3] for f in os.listdir(d)
                        if f.startswith("hwdrv_") and f.endswith(".py"))
        docs = [f for f in ("README.md",) if os.path.isfile(os.path.join(d, f))]
        pdfs = sorted(f for f in os.listdir(d) if f.endswith(".pdf"))
        line = f"- {name}"
        for h in hwdrvs:
            line += f"\n    module: public.prism.drivers.{name}.{h}"
        refs = [f"{DRIVERS_DOC} section '{name}'"] if name in sections else []
        refs += [f"{DRIVERS_DIR}/{name}/{f}" for f in docs + pdfs]
        if refs:
            line += "\n    docs: " + ", ".join(refs)
        out.append(line)
    return "\n".join(out)


def _signature(fn):
    args = [a.arg for a in fn.args.args]
    defaults = [ast.unparse(x) for x in fn.args.defaults]
    pos = len(args) - len(defaults)
    parts = [a if i < pos else f"{a}={defaults[i - pos]}" for i, a in enumerate(args)]
    return f"{fn.name}({', '.join(parts)})"


def python_api(target, include_private=False, root=None):
    """ Classes, methods, signatures and doc strings of a Python file
    :param target: a repo path, or test_item, record, result_api, script_lint
    """
    root = root or repo_root()
    path = API_ALIASES.get(target, target)
    full = resolve(path, root)
    tree = ast.parse(_read_text(full))
    out = [f"# {_rel(full, root)}"]

    def doc(node, indent):
        d = ast.get_docstring(node)
        if not d:
            return
        out.extend(indent + line for line in d.strip().splitlines())

    def public(name):
        return include_private or not name.startswith("_") or name == "__init__"

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.append(f"\nclass {node.name}:")
            doc(node, "    ")
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and public(item.name):
                    out.append(f"\n    def {_signature(item)}")
                    doc(item, "        ")
                elif isinstance(item, ast.Assign) and include_private:
                    out.append(f"    {ast.unparse(item)}")
                elif (isinstance(item, ast.Assign) and len(item.targets) == 1
                      and isinstance(item.targets[0], ast.Name)
                      and item.targets[0].id.isupper()):
                    out.append(f"    {ast.unparse(item)[:120]}")
        elif isinstance(node, ast.FunctionDef) and public(node.name):
            out.append(f"\ndef {_signature(node)}")
            doc(node, "    ")
    return "\n".join(out)


# --- repo -----------------------------------------------------------------


def _git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True,
                           timeout=GIT_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    if r.returncode != 0:
        return None, r.stderr.strip()
    return r.stdout.strip(), None


def _strip_credentials(url):
    return re.sub(r"//[^/@]+@", "//", url)


def repo_status(root=None):
    """ Scripts version, branch, remotes, and how far behind Sistemi's scripts it is
    - uses only what was last fetched, it does not fetch
    """
    root = root or repo_root()
    out = [f"Repo: {root}"]
    vf = os.path.join(root, VERSION_FILE)
    if os.path.isfile(vf):
        out.append(f"public/VERSION: {_read_text(vf).strip()}")
    describe, err = _git(root, "describe", "--tags", "--always")
    out.append(f"git describe: {describe or err}")
    branch, _ = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    out.append(f"branch: {branch}")
    status, _ = _git(root, "status", "--porcelain")
    if status is not None:
        out.append(f"uncommitted changes: {len(status.splitlines())} files")

    remotes, _ = _git(root, "remote", "-v")
    sistemi = None
    for line in (remotes or "").splitlines():
        if not line.endswith("(fetch)"):
            continue
        name, url = line.split()[:2]
        out.append(f"remote {name}: {_strip_credentials(url)}")
        if re.search(SISTEMI_REMOTE_RE, url):
            sistemi = name
    if sistemi is None:
        out.append("No remote points to sistemicorp/scripts, so Sistemi updates can't be "
                   "merged, see docs/source/_development.rst 'Getting Updates From Sistemi'.")
        return "\n".join(out)

    ref = f"{sistemi}/{UPSTREAM_BRANCH}"
    counts, err = _git(root, "rev-list", "--left-right", "--count", f"HEAD...{ref}")
    if counts:
        ahead, behind = counts.split()
        out.append(f"vs {ref} (last fetch): {ahead} commits ahead, {behind} behind")
        last, _ = _git(root, "log", "-1", "--format=%cs %s", ref)
        out.append(f"{ref} last commit: {last}")
    else:
        out.append(f"{ref}: {err}, run 'git fetch {sistemi}'")
    return "\n".join(out)
