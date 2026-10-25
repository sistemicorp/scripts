#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

Static checks of a Prism script (.scr) and the test item methods it runs.

The test modules are parsed with `ast`, never imported, so no driver or
hardware code runs.  Used by Prism (Validate) and prism_dev.py.

    findings = lint_script(script, subs_applied=True)
    errors = [f for f in findings if f.level == LEVEL_ERROR]

subs_applied: False for a raw .scr (the subs section is checked and "%%Key"
values are allowed), True for a script after substitution (any "%%Key"
left over is an error).
"""
import ast
import difflib
import os
import re
import sys
from dataclasses import dataclass

from public.prism.api import ResultAPI

LEVEL_ERROR = "ERROR"
LEVEL_WARN = "WARN"

SUB_MARK = "%%"
SUB_TOKEN_RE = r'"%%(\w+)"'
SUB_TYPES = ("str", "num")
SUB_WIDGETS = ("textinput", "select")
SUB_KEYS = ("title", "type", "widget", "regex", "choices", "default", "subs")
INNER_SUB_KEYS = ("val", "type")

# lengths of the Lente database columns
INFO_FIELDS = {"product": 32, "bom": 32, "lot": 16, "location": 128}
INFO_OPTIONAL_FIELDS = {"config": 16}

# items may carry other fields for the test code, ctx.item.<field>
ITEM_KEYS = ("id", "enable", "timeout", "args", "fail")
TYPO_CUTOFF = 0.8  # difflib ratio of an item field to a Prism item key
FAIL_KEYS = ("fid", "msg")
ENABLE_STRINGS = ("true", "false")

ITEM_RESULTS = (ResultAPI.RECORD_RESULT_PASS, ResultAPI.RECORD_RESULT_FAIL,
                ResultAPI.RECORD_RESULT_TIMEOUT, ResultAPI.RECORD_RESULT_INCOMPLETE,
                ResultAPI.RECORD_RESULT_INTERNAL_ERROR, ResultAPI.RECORD_RESULT_SKIP,
                ResultAPI.RECORD_RESULT_DISABLED)

# TestItem methods that let a timeout or abort stop a loop
STOPPABLE_CALLS = ("sleep", "check_abort", "input_button", "input_textbox")
DICT_METHODS = ("get", "keys", "items", "values")
ITEM_START = "item_start"
ITEM_END = "item_end"
NEXT_ARG = "_next"
NEXT_ARG_POS = 1


@dataclass
class Finding:
    level: str
    where: str
    msg: str

    def __str__(self):
        return "{} {}: {}".format(self.level, self.where, self.msg)


def errors(findings):
    return [f for f in findings if f.level == LEVEL_ERROR]


def warnings(findings):
    return [f for f in findings if f.level == LEVEL_WARN]


def lint_script(script, subs_applied=True, root=None):
    """Check a script and the test item methods it names.
    :param script: script dict
    :param subs_applied: True if substitutions have been applied
    :param root: directory module paths resolve from, default cwd, then sys.path
    :return: [Finding], errors before warnings
    """
    out = []
    if not isinstance(script, dict):
        return [Finding(LEVEL_ERROR, "script", "must be an object")]
    _lint_info(script, subs_applied, out)
    _lint_config(script, out)
    if subs_applied:
        _lint_leftover_subs(script, out)
    else:
        _lint_subs(script, out)
    if _lint_tests(script, out):
        _lint_code(script, root, out)
    unique = list({(f.level, f.where, f.msg): f for f in out}.values())
    return errors(unique) + warnings(unique)


# --- script sections ------------------------------------------------------

def _is_sub(value):
    return isinstance(value, str) and value.startswith(SUB_MARK)


def _lint_info(script, subs_applied, out):
    info = script.get("info")
    if not isinstance(info, dict):
        out.append(Finding(LEVEL_ERROR, "info", "section missing or not an object"))
        return
    fields = {**INFO_FIELDS, **INFO_OPTIONAL_FIELDS}
    for key in info:
        if key not in fields:
            out.append(Finding(LEVEL_ERROR, "info.{}".format(key),
                               "unknown field, Lente only stores {}".format(
                                   ", ".join(fields))))
    for key, max_len in fields.items():
        where = "info.{}".format(key)
        if key not in info:
            if key in INFO_FIELDS:
                out.append(Finding(LEVEL_ERROR, where, "missing"))
            continue
        value = info[key]
        if not isinstance(value, str):
            out.append(Finding(LEVEL_ERROR, where, "must be a string"))
        elif not (_is_sub(value) and not subs_applied) and len(value) > max_len:
            out.append(Finding(LEVEL_ERROR, where,
                               "longer than {} characters".format(max_len)))


def _lint_config(script, out):
    config = script.get("config")
    if not isinstance(config, dict):
        out.append(Finding(LEVEL_ERROR, "config", "section missing or not an object"))
        return
    if not isinstance(config.get("fail_fast", True), bool):
        out.append(Finding(LEVEL_ERROR, "config.fail_fast", "must be true or false"))
    drivers = config.get("drivers")
    if not isinstance(drivers, list) or not drivers:
        out.append(Finding(LEVEL_ERROR, "config.drivers", "must be a non-empty list"))
        return
    for idx, drv in enumerate(drivers):
        where = "config.drivers[{}]".format(idx)
        if isinstance(drv, list):
            if len(drv) != 2 or not isinstance(drv[0], str):
                out.append(Finding(LEVEL_ERROR, where,
                                   "must be a module string or [module, args]"))
                continue
            drv = drv[0]
        elif not isinstance(drv, str):
            out.append(Finding(LEVEL_ERROR, where,
                               "must be a module string or [module, args]"))
            continue
        if _module_file(drv, None) is None:
            out.append(Finding(LEVEL_ERROR, where, "driver module {} not found".format(drv)))


def _walk_values(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk_values(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_values(v)
    else:
        yield value


def _lint_leftover_subs(script, out):
    for key, value in script.items():
        if key == "subs":
            continue
        for v in _walk_values(value):
            if _is_sub(v):
                out.append(Finding(LEVEL_ERROR, key,
                                   "substitution {} was not replaced".format(v)))


def _lint_subs(script, out):
    """Check the subs section against the "%%Key" tokens used in the script."""
    subs = script.get("subs", {})
    if not isinstance(subs, dict):
        out.append(Finding(LEVEL_ERROR, "subs", "must be an object"))
        return
    defined = set(subs)
    inner_defined = set()
    for key, sub in subs.items():
        where = "subs.{}".format(key)
        if not re.fullmatch(r"\w+", key):
            out.append(Finding(LEVEL_ERROR, where, "key must be letters, digits or _"))
        if not isinstance(sub, dict):
            out.append(Finding(LEVEL_ERROR, where, "must be an object"))
            continue
        for k in sub:
            if k not in SUB_KEYS:
                out.append(Finding(LEVEL_WARN, where, "unknown field {}".format(k)))
        if sub.get("type") not in SUB_TYPES:
            out.append(Finding(LEVEL_ERROR, where, "type must be one of {}".format(SUB_TYPES)))
        widget = sub.get("widget")
        if widget not in SUB_WIDGETS:
            out.append(Finding(LEVEL_ERROR, where,
                               "widget must be one of {}".format(SUB_WIDGETS)))
        choices = sub.get("choices")
        if widget == "select" and (not isinstance(choices, list) or not choices):
            out.append(Finding(LEVEL_ERROR, where, "select needs a non-empty choices list"))
            choices = None
        regex = sub.get("regex")
        if regex is not None:
            try:
                compiled = re.compile(regex)
            except (re.error, TypeError) as e:
                out.append(Finding(LEVEL_ERROR, where, "regex does not compile: {}".format(e)))
            else:
                default = sub.get("default")
                if default is not None and not compiled.search(str(default)):
                    out.append(Finding(LEVEL_ERROR, where, "default does not match regex"))
        inner = sub.get("subs")
        if inner is None:
            continue
        if not isinstance(inner, dict):
            out.append(Finding(LEVEL_ERROR, where + ".subs", "must be an object"))
            continue
        if choices is not None:
            for choice in choices:
                if str(choice) not in inner:
                    out.append(Finding(LEVEL_ERROR, where + ".subs",
                                       "choice {} has no inner subs".format(choice)))
        for choice, inner_subs in inner.items():
            iwhere = "{}.subs.{}".format(where, choice)
            if choices is not None and choice not in [str(c) for c in choices]:
                out.append(Finding(LEVEL_ERROR, iwhere, "is not one of the choices"))
            if not isinstance(inner_subs, dict):
                out.append(Finding(LEVEL_ERROR, iwhere, "must be an object"))
                continue
            for ikey, ival in inner_subs.items():
                inner_defined.add(ikey)
                if ikey in defined:
                    out.append(Finding(LEVEL_ERROR, "{}.{}".format(iwhere, ikey),
                                       "inner sub is also a top level sub"))
                if not isinstance(ival, dict) or set(ival) != set(INNER_SUB_KEYS) \
                        or ival.get("type") not in SUB_TYPES:
                    out.append(Finding(LEVEL_ERROR, "{}.{}".format(iwhere, ikey),
                                       'must be {"val": <value>, "type": "str|num"}'))

    used = set()
    for key, value in script.items():
        if key == "subs":
            continue
        for v in _walk_values(value):
            if _is_sub(v):
                used.add(v[len(SUB_MARK):])
    for name in sorted(used - defined - inner_defined):
        out.append(Finding(LEVEL_ERROR, "subs", "%%{} is used but not defined".format(name)))
    for name in sorted((defined | inner_defined) - used):
        out.append(Finding(LEVEL_WARN, "subs.{}".format(name), "defined but not used"))


def _lint_tests(script, out):
    """:return: True if the tests section is sound enough to lint the code"""
    tests = script.get("tests")
    if not isinstance(tests, list) or not tests:
        out.append(Finding(LEVEL_ERROR, "tests", "must be a non-empty list"))
        return False
    sound = True
    for t_idx, test in enumerate(tests):
        where = "tests[{}]".format(t_idx)
        if not isinstance(test, dict) or not isinstance(test.get("module"), str):
            out.append(Finding(LEVEL_ERROR, where, "must be an object with a module string"))
            sound = False
            continue
        options = test.get("options", {})
        if not isinstance(options, dict):
            out.append(Finding(LEVEL_ERROR, where + ".options", "must be an object"))
            sound = False
        else:
            if not isinstance(options.get("fail_fast", True), bool):
                out.append(Finding(LEVEL_ERROR, where + ".options.fail_fast",
                                   "must be true or false"))
            _lint_timeout(options, where + ".options", out)
        items = test.get("items")
        if not isinstance(items, list) or not items:
            out.append(Finding(LEVEL_ERROR, where + ".items", "must be a non-empty list"))
            sound = False
            continue
        for i_idx, item in enumerate(items):
            iwhere = "{}.items[{}]".format(where, i_idx)
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                out.append(Finding(LEVEL_ERROR, iwhere, "must be an object with a string id"))
                sound = False
                continue
            iwhere = "{} {}".format(iwhere, item["id"])
            for k in item:
                close = difflib.get_close_matches(k, ITEM_KEYS, 1, TYPO_CUTOFF)
                if k not in ITEM_KEYS and close:
                    out.append(Finding(LEVEL_WARN, iwhere,
                                       "field {} looks like a typo of {}".format(k, close[0])))
            _lint_enable(item.get("enable", True), iwhere, out)
            _lint_timeout(item, iwhere, out)
            if not isinstance(item.get("args", {}), dict):
                out.append(Finding(LEVEL_ERROR, iwhere + " args", "must be an object"))
                sound = False
            fail = item.get("fail", [])
            if not isinstance(fail, list) or not all(
                    isinstance(f, dict) and set(f) == set(FAIL_KEYS) for f in fail):
                out.append(Finding(LEVEL_ERROR, iwhere + " fail",
                                   'must be a list of {"fid": ..., "msg": ...}'))
        last = items[-1]
        if isinstance(last, dict) and last.get("enable", True) in (False, "false"):
            out.append(Finding(LEVEL_WARN, "{}.items[{}]".format(where, len(items) - 1),
                               "last item is the teardown and should be enabled"))
    return sound


def _lint_enable(enable, where, out):
    if isinstance(enable, bool) or _is_sub(enable):
        return
    if isinstance(enable, str) and enable.lower() in ENABLE_STRINGS:
        return
    out.append(Finding(LEVEL_ERROR, where + " enable", "must be true or false"))


def _lint_timeout(d, where, out):
    timeout = d.get("timeout")
    if timeout is None or _is_sub(timeout):
        return
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        out.append(Finding(LEVEL_ERROR, where + " timeout", "must be a positive number"))


# --- test item code -------------------------------------------------------

def _module_file(module, root):
    """Find module's .py file without importing it, or None."""
    rel = os.path.join(*module.split(".")) + ".py"
    for base in [root or os.getcwd()] + sys.path:
        path = os.path.join(base, rel)
        if os.path.isfile(path):
            return path
    return None


def _lint_code(script, root, out):
    items_after = []  # (test_idx, item_idx, id) in run order, for _next
    for t_idx, test in enumerate(script["tests"]):
        for i_idx, item in enumerate(test["items"]):
            items_after.append((t_idx, i_idx, item["id"]))

    parsed = {}
    for t_idx, test in enumerate(script["tests"]):
        module = test["module"]
        where = "tests[{}].module".format(t_idx)
        if module not in parsed:
            parsed[module] = _parse_module(module, root, where, out)
        found = parsed[module]
        if found is None:
            continue
        path, methods = found
        for i_idx, item in enumerate(test["items"]):
            fn = methods.get(item["id"])
            iwhere = "tests[{}].items[{}] {}".format(t_idx, i_idx, item["id"])
            if fn is None:
                out.append(Finding(LEVEL_ERROR, iwhere,
                                   "no method {} in {}".format(item["id"], module)))
                continue
            later = {i for t, ii, i in items_after if (t, ii) > (t_idx, i_idx)}
            ctx = {"item": item, "options": test.get("options", {}),
                   "config": script["config"], "later": later}
            for line, level, msg in _MethodLint(fn, ctx).run():
                out.append(Finding(level, "{}:{} {}".format(_rel(path), line, item["id"]), msg))


def _rel(path):
    rel = os.path.relpath(path)
    return path if rel.startswith("..") else rel


def _parse_module(module, root, where, out):
    """:return: (path, {method name: FunctionDef}) or None"""
    path = _module_file(module, root)
    if path is None:
        out.append(Finding(LEVEL_ERROR, where, "module {} not found".format(module)))
        return None
    try:
        with open(path) as f:
            tree = ast.parse(f.read(), filename=path)
    except (OSError, SyntaxError, ValueError) as e:
        out.append(Finding(LEVEL_ERROR, where, "cannot parse {}: {}".format(path, e)))
        return None
    klass = module.split(".")[-1]
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass]
    if not classes:
        out.append(Finding(LEVEL_ERROR, where,
                           "{} has no class {} (file and class name must match)".format(
                               path, klass)))
        return None
    methods = {n.name: n for n in classes[0].body if isinstance(n, ast.FunctionDef)}
    return path, methods


def _self_call(node, name):
    """True if node is a call self.<name>(...)"""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == name and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self")


def _stmt_call(stmt):
    """The call made by an expression, assign or return statement, or None."""
    if isinstance(stmt, (ast.Expr, ast.Return, ast.Assign, ast.AnnAssign)):
        return stmt.value if isinstance(stmt.value, ast.Call) else None
    return None


def _own_nodes(fn):
    """Nodes of fn, not descending into nested functions, lambdas or classes."""
    todo = list(ast.iter_child_nodes(fn))
    while todo:
        node = todo.pop()
        yield node
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda,
                                 ast.ClassDef)):
            todo.extend(ast.iter_child_nodes(node))


class _MethodLint:
    """Lint one test item method.

    Paths are followed with the set of possible "item_end() called" states
    (False/True), so early returns and branches are checked.
    """

    def __init__(self, fn, ctx):
        self.fn = fn
        self.ctx = ctx
        self.found = {}
        self.loops = []  # [(break states, continue states)]

    def add(self, node, level, msg):
        self.found.setdefault((node.lineno, msg), level)

    def run(self):
        body = self.fn.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body = body[1:]
        ctx_name = self._lint_start(body)
        end = self._block(body, {False})
        if False in end:
            self.found.setdefault((self.fn.end_lineno, "can return without item_end()"),
                                  LEVEL_ERROR)
        self._lint_calls(ctx_name)
        found = [(line, level, msg) for (line, msg), level in self.found.items()]
        return sorted(found, key=lambda f: f[0])  # stable, keeps check order per line

    def _lint_start(self, body):
        """:return: name item_start() is assigned to, or None"""
        first = body[0] if body else self.fn
        call = _stmt_call(first) if body else None
        if call is None or not _self_call(call, ITEM_START):
            self.add(first, LEVEL_ERROR, "first statement must be ctx = self.item_start()")
        starts = [n for n in _own_nodes(self.fn) if _self_call(n, ITEM_START)]
        for extra in sorted(starts, key=lambda n: n.lineno)[1:]:
            self.add(extra, LEVEL_ERROR, "item_start() is called more than once")
        if isinstance(first, ast.Assign) and len(first.targets) == 1 \
                and isinstance(first.targets[0], ast.Name):
            return first.targets[0].id
        return None

    # path analysis: each returns the set of states that fall out the bottom

    def _block(self, stmts, states):
        for stmt in stmts:
            if not states:
                break
            states = self._stmt(stmt, states)
        return states

    def _stmt(self, stmt, states):
        call = _stmt_call(stmt)
        if call is not None and _self_call(call, ITEM_END):
            if True in states:
                self.add(stmt, LEVEL_ERROR, "item_end() may already have been called")
            self._lint_item_end(call)
            return set() if isinstance(stmt, ast.Return) else {True}
        if isinstance(stmt, ast.Return):
            if False in states:
                self.add(stmt, LEVEL_ERROR, "return before item_end()")
            return set()
        if isinstance(stmt, ast.Raise):
            return set()
        if isinstance(stmt, ast.If):
            return self._block(stmt.body, states) | self._block(stmt.orelse, states)
        if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            return self._loop(stmt, states)
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            return self._block(stmt.body, states)
        if isinstance(stmt, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            return self._try(stmt, states)
        if isinstance(stmt, ast.Match):
            out = set()
            for case in stmt.cases:
                out |= self._block(case.body, states)
            irrefutable = any(isinstance(c.pattern, ast.MatchAs) and c.pattern.pattern is None
                              and c.guard is None for c in stmt.cases)
            return out if irrefutable else out | states
        if isinstance(stmt, ast.Break) and self.loops:
            self.loops[-1][0].update(states)
            return set()
        if isinstance(stmt, ast.Continue) and self.loops:
            self.loops[-1][1].update(states)
            return set()
        return states

    def _loop(self, stmt, states):
        forever = isinstance(stmt, ast.While) and isinstance(stmt.test, ast.Constant) \
            and bool(stmt.test.value)
        if isinstance(stmt, ast.While) and not self._stoppable(stmt):
            self.add(stmt, LEVEL_WARN, "while loop cannot be stopped by a timeout, "
                                       "call self.sleep() or self.check_abort() in it")
        breaks, continues = set(), set()
        self.loops.append((breaks, continues))
        entry = set(states)
        for _ in range(2):  # two passes reach the fixed point of a 2 state set
            entry |= self._block(stmt.body, entry) | continues
        self.loops.pop()
        if forever:
            return breaks
        return self._block(stmt.orelse, entry) | breaks

    def _stoppable(self, loop):
        return any(_self_call(n, name) for n in ast.walk(loop) for name in STOPPABLE_CALLS)

    def _try(self, stmt, states):
        # an exception is raised before an item_end() call, not by it
        handler_in = set(states)
        mid = set(states)
        for s in stmt.body:
            if not mid:
                break
            call = _stmt_call(s)
            if call is None or not _self_call(call, ITEM_END):
                handler_in |= mid
            mid = self._stmt(s, mid)
        out = self._block(stmt.orelse, mid)
        for handler in stmt.handlers:
            self._lint_handler(handler)
            out |= self._block(handler.body, handler_in)
        if stmt.finalbody:
            # finally runs on every path, but only falls through if the try did
            final = self._block(stmt.finalbody, out | handler_in)
            out = final if out else set()
        return out

    def _lint_handler(self, handler):
        broad = handler.type is None or (isinstance(handler.type, ast.Name)
                                         and handler.type.id == "BaseException")
        reraises = any(isinstance(n, ast.Raise) and n.exc is None for n in ast.walk(handler))
        if broad and not reraises:
            self.add(handler, LEVEL_WARN, "bare except or BaseException catches the timeout "
                                          "stop, use except Exception")

    def _lint_item_end(self, call):
        result = call.args[0] if call.args else None
        for kw in call.keywords:
            if kw.arg == "item_result_state":
                result = kw.value
        if isinstance(result, ast.Constant) and result.value not in ITEM_RESULTS:
            self.add(call, LEVEL_ERROR, "item_end() result {!r} is not a ResultAPI."
                                        "RECORD_RESULT_* value".format(result.value))
        nxt = call.args[NEXT_ARG_POS] if len(call.args) > NEXT_ARG_POS else None
        for kw in call.keywords:
            if kw.arg == NEXT_ARG:
                nxt = kw.value
        if isinstance(nxt, ast.Constant) and isinstance(nxt.value, str) \
                and nxt.value not in self.ctx["later"]:
            self.add(call, LEVEL_ERROR,
                     "_next item {} is not after this item in the script".format(nxt.value))

    # calls and attribute use anywhere in the method

    def _lint_calls(self, ctx_name):
        for node in _own_nodes(self.fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "sleep" and isinstance(node.func.value, ast.Name) \
                    and node.func.value.id == "time":
                self.add(node, LEVEL_WARN, "time.sleep() cannot be stopped by a timeout, "
                                           "use self.sleep()")
            if ctx_name is not None:
                self._lint_ctx_use(node, ctx_name)

    def _ctx_path(self, node, ctx_name):
        """['item', 'args'] for ctx.item.args, None if node is not ctx.<...>"""
        path = []
        while isinstance(node, ast.Attribute):
            path.insert(0, node.attr)
            node = node.value
        if isinstance(node, ast.Name) and node.id == ctx_name:
            return path
        return None

    def _lint_ctx_use(self, node, ctx_name):
        if isinstance(node, ast.Attribute):
            path = self._ctx_path(node.value, ctx_name)
            key = node.attr
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            path = self._ctx_path(node.value, ctx_name)
            key = node.slice.value
        else:
            return
        if path is None or key in DICT_METHODS:
            return
        item = self.ctx["item"]
        sources = {("item", "args"): (item.get("args", {}), "args"),
                   ("options",): (self.ctx["options"], "options"),
                   ("config",): (self.ctx["config"], "config")}
        if tuple(path) in sources:
            d, name = sources[tuple(path)]
            if key not in d:
                self.add(node, LEVEL_ERROR, "ctx.{}.{} is not in the script item {}".format(
                    ".".join(path), key, name))
        elif path == ["item"] and key not in item:
            self.add(node, LEVEL_ERROR, "ctx.item.{} is not in the script item".format(key))
