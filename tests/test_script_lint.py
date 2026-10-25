"""Tests for public/prism/script_lint.py.

Run from the scripts repo root: python -m pytest tests
Each test writes a small test module to tmp_path and lints a script for it.
"""
import copy
import glob
import textwrap

import jstyleson
import pytest

from public.prism.script_lint import lint_script, errors, warnings

MODULE = "lintpkg.lintmod"
DRIVER = "public.prism.drivers.fake.hwdrv_fake"
EXAMPLES = "public/prism/scripts/example/**/*.scr"

GOOD_METHODS = '''
    def SETUP(self):
        """doc string is allowed before item_start"""
        ctx = self.item_start()
        self.item_end()

    def EARLY(self):
        ctx = self.item_start()
        if ctx.item.args.min > 1:
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return
        try:
            go()
        except Exception:
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        self.item_end()

    def BRANCHES(self):
        ctx = self.item_start()
        if a:
            self.item_end()
        elif b:
            return self.item_end(ResultAPI.RECORD_RESULT_FAIL)
        else:
            raise RuntimeError("Prism ends the item as INTERNAL_ERROR")

    def LOOP(self):
        ctx = self.item_start()
        while True:
            if not self.sleep(1):
                break
        self.item_end(_next="TEARDOWN")

    def TEARDOWN(self):
        ctx = self.item_start()
        self.item_end()
'''

SCRIPT = {
    "info": {"product": "p", "bom": "b", "lot": "1", "location": "here"},
    "config": {"fail_fast": True, "drivers": [DRIVER]},
    "tests": [{"module": MODULE, "options": {},
               "items": [{"id": "SETUP"},
                         {"id": "EARLY", "args": {"min": 0}},
                         {"id": "BRANCHES"},
                         {"id": "LOOP"},
                         {"id": "TEARDOWN"}]}],
}


def _module_src(methods, klass):
    head = textwrap.dedent('''
        from core.test_item import TestItem
        from public.prism.api import ResultAPI


        class {}(TestItem):
    ''').format(klass)
    return head + textwrap.indent(textwrap.dedent(methods), "    ")


@pytest.fixture
def lint(tmp_path):
    """lint(methods, script=None, subs_applied=True, klass) -> findings"""
    def _lint(methods=GOOD_METHODS, script=None, subs_applied=True, klass="lintmod"):
        pkg = tmp_path / "lintpkg"
        pkg.mkdir(exist_ok=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "lintmod.py").write_text(_module_src(methods, klass))
        script = copy.deepcopy(SCRIPT) if script is None else script
        return lint_script(script, subs_applied=subs_applied, root=str(tmp_path))
    return _lint


def _one_item(item_id, **item):
    script = copy.deepcopy(SCRIPT)
    script["tests"][0]["items"] = [dict(id=item_id, **item), {"id": "TEARDOWN"}]
    return script


def _msgs(findings):
    return [f.msg for f in findings]


def _method(name, body):
    """methods source: TEARDOWN plus one method `name` with `body`"""
    return "def {}(self):\n{}\n".format(name, textwrap.indent(textwrap.dedent(body), "    ")) \
        + "def TEARDOWN(self):\n    ctx = self.item_start()\n    self.item_end()\n"


# === good code and the shipped examples =====================================

def test_good_module_has_no_findings(lint):
    assert lint() == []


@pytest.mark.parametrize("scr", sorted(glob.glob(EXAMPLES, recursive=True)))
def test_example_scripts_have_no_errors(scr):
    with open(scr) as f:
        script = jstyleson.loads(f.read())
    assert [str(f) for f in errors(lint_script(script, subs_applied=False))] == []


# === test item code: item_start / item_end ===================================

@pytest.mark.parametrize("body, expect", [
    # [Unhappy] code before item_start
    ("x = 1\nctx = self.item_start()\nself.item_end()",
     "first statement must be ctx = self.item_start()"),
    # [Unhappy] no item_start at all
    ("self.item_end()", "first statement must be ctx = self.item_start()"),
    # [Unhappy] item_start twice
    ("ctx = self.item_start()\nself.item_start()\nself.item_end()",
     "item_start() is called more than once"),
    # [Unhappy] no item_end
    ("ctx = self.item_start()\nself.log_bullet('x')", "can return without item_end()"),
    # [Unhappy] early return skips item_end
    ("ctx = self.item_start()\nif a:\n    return\nself.item_end()",
     "return before item_end()"),
    # [Unhappy] return in a loop skips item_end
    ("ctx = self.item_start()\nfor i in x:\n    if i:\n        return\nself.item_end()",
     "return before item_end()"),
    # [Unhappy] one branch falls off the end
    ("ctx = self.item_start()\nif a:\n    self.item_end()\nelse:\n    pass",
     "can return without item_end()"),
    # [Unhappy] item_end in a branch without return, then again at the end
    ("ctx = self.item_start()\nif a:\n    self.item_end('FAIL')\nself.item_end()",
     "item_end() may already have been called"),
    # [Unhappy] exception handler swallows the error and skips item_end
    ("ctx = self.item_start()\ntry:\n    go()\n    self.item_end()\n"
     "except Exception:\n    self.log_bullet('x')", "can return without item_end()"),
    # [Unhappy] code after item_end in the try can raise into a handler that ends again
    ("ctx = self.item_start()\ntry:\n    self.item_end()\n    go()\n"
     "except Exception:\n    self.item_end('FAIL')", "item_end() may already have been called"),
    # [Unhappy] a loop that may not run leaves item_end unreached
    ("ctx = self.item_start()\nfor i in x:\n    self.item_end()\n    return",
     "can return without item_end()"),
])
def test_item_start_end_paths(lint, body, expect):
    # Every path must start with item_start and end with exactly one item_end
    findings = lint(_method("A", body), _one_item("A"))
    assert expect in _msgs(errors(findings))


@pytest.mark.parametrize("body", [
    # [Edge] item_end in try and in the handler
    "ctx = self.item_start()\ntry:\n    go()\n    self.item_end()\n"
    "except Exception:\n    self.item_end('FAIL')",
    # [Edge] item_end in finally
    "ctx = self.item_start()\ntry:\n    go()\nfinally:\n    self.item_end()",
    # [Edge] a while True loop only leaves by return
    "ctx = self.item_start()\nwhile True:\n    if self.sleep(1):\n        self.item_end()\n"
    "        return",
    # [Edge] inside a with block
    "ctx = self.item_start()\nwith self.shared_lock('r'):\n    self.item_end()",
    # [Edge] match with a wildcard case
    "ctx = self.item_start()\nmatch x:\n    case 1:\n        self.item_end()\n"
    "    case _:\n        self.item_end('FAIL')",
    # [Edge] a nested function is not part of the item's paths
    "ctx = self.item_start()\ndef cb():\n    return 1\nself.item_end()",
])
def test_item_end_path_edges_are_accepted(lint, body):
    assert errors(lint(_method("A", body), _one_item("A"))) == []


@pytest.mark.parametrize("body, expect", [
    # [Unhappy] result string that Prism does not accept
    ("ctx = self.item_start()\nself.item_end('OK')", "is not a ResultAPI"),
    # [Unhappy] _next to an item that is not later in the script
    ("ctx = self.item_start()\nself.item_end(_next='NOPE')", "_next item NOPE"),
])
def test_item_end_arguments(lint, body, expect):
    findings = lint(_method("A", body), _one_item("A"))
    assert any(expect in m for m in _msgs(errors(findings)))


# === test item code: script and code agree ===================================

@pytest.mark.parametrize("use, expect", [
    # [Unhappy] arg not in the script item
    ("ctx.item.args.max", "ctx.item.args.max is not in the script item args"),
    ("ctx.item.args['max']", "ctx.item.args.max is not in the script item args"),
    # [Unhappy] item field not in the script item
    ("ctx.item.fail[0]", "ctx.item.fail is not in the script item"),
    # [Unhappy] option not in the test options
    ("ctx.options.holdTime", "ctx.options.holdTime is not in the script item options"),
])
def test_ctx_use_must_match_script(lint, use, expect):
    body = "ctx = self.item_start()\nx = {}\nself.item_end()".format(use)
    findings = lint(_method("A", body), _one_item("A", args={"min": 0}))
    assert expect in _msgs(errors(findings))


def test_ctx_get_with_default_is_accepted(lint):
    # [Edge] .get() with a default is the safe way to read an optional arg
    body = "ctx = self.item_start()\nx = ctx.item.args.get('max', 5)\nself.item_end()"
    assert errors(lint(_method("A", body), _one_item("A", args={"min": 0}))) == []


@pytest.mark.parametrize("body, expect", [
    ("ctx = self.item_start()\ntime.sleep(1)\nself.item_end()", "time.sleep()"),
    ("ctx = self.item_start()\nwhile go():\n    pass\nself.item_end()", "while loop"),
    ("ctx = self.item_start()\ntry:\n    go()\nexcept:\n    pass\nself.item_end()",
     "bare except"),
])
def test_unstoppable_code_warns(lint, body, expect):
    # [Unhappy] code a timeout cannot stop is a warning, not an error
    findings = lint(_method("A", body), _one_item("A"))
    assert errors(findings) == []
    assert any(expect in m for m in _msgs(warnings(findings)))


def test_missing_method_and_module(lint):
    # [Unhappy] item id with no method, and a module that does not exist
    script = _one_item("NO_SUCH_METHOD")
    assert "no method NO_SUCH_METHOD in lintpkg.lintmod" in _msgs(lint(script=script))
    script["tests"][0]["module"] = "lintpkg.nosuch"
    assert "module lintpkg.nosuch not found" in _msgs(lint(script=script))


def test_class_name_must_match_file(lint):
    # [Unhappy] file and class name must match
    findings = lint(klass="LintMod")
    assert any("has no class lintmod" in m for m in _msgs(errors(findings)))


# === script sections ========================================================

@pytest.mark.parametrize("info, expect", [
    ({"product": "p", "bom": "b", "lot": "1"}, "missing"),  # [Unhappy] Lente needs location
    ({"product": "p", "bom": "b", "lot": "x" * 17, "location": ""},
     "longer than 16 characters"),  # [Unhappy] Lente column is String(16)
    ({"product": "p", "bom": "b", "lot": "1", "location": "", "colour": "red"},
     "unknown field, Lente only stores product, bom, lot, location, config"),
])
def test_info_matches_lente(lint, info, expect):
    script = copy.deepcopy(SCRIPT)
    script["info"] = info
    assert expect in _msgs(errors(lint(script=script)))


def test_info_sub_length_checked_after_subs(lint):
    # [Edge] "%%Lot" is longer than nothing but is only a placeholder before subs
    script = copy.deepcopy(SCRIPT)
    script["info"]["lot"] = "%%LotNumberFromOperator"
    script["subs"] = {"LotNumberFromOperator": {"title": "t", "type": "str",
                                                "widget": "textinput"}}
    assert errors(lint(script=script, subs_applied=False)) == []
    assert "substitution %%LotNumberFromOperator was not replaced" in \
        _msgs(errors(lint(script=script, subs_applied=True)))


@pytest.mark.parametrize("item, expect, level", [
    ({"enable": "yes"}, "must be true or false", "ERROR"),   # [Unhappy] string enable
    ({"timeout": -1}, "must be a positive number", "ERROR"),  # [Unhappy]
    ({"fail": [{"fid": "x"}]}, 'must be a list of {"fid": ..., "msg": ...}', "ERROR"),
    ({"timout": 5}, "field timout looks like a typo of timeout", "WARN"),  # [Unhappy]
])
def test_item_fields(lint, item, expect, level):
    findings = lint(script=_one_item("SETUP", **item))
    assert [f.level for f in findings if f.msg == expect] == [level]


def test_item_custom_fields_are_allowed(lint):
    # [Edge] items may carry fields for the code, read as ctx.item.<field>
    body = "ctx = self.item_start()\nx = ctx.item.file\nself.item_end()"
    assert lint(_method("A", body), _one_item("A", file="fw.hex", enable="false")) == []


def test_disabled_teardown_warns(lint):
    # [Unhappy] the last item runs as teardown, so it should be enabled
    script = _one_item("SETUP")
    script["tests"][0]["items"][-1]["enable"] = False
    msgs = _msgs(warnings(lint(script=script)))
    assert "last item is the teardown and should be enabled" in msgs


@pytest.mark.parametrize("drivers, expect", [
    ([], "must be a non-empty list"),
    ([["a", "b", "c"]], "must be a module string or [module, args]"),
    (["public.prism.drivers.nosuch"], "driver module public.prism.drivers.nosuch not found"),
])
def test_drivers(lint, drivers, expect):
    # [Unhappy] driver entries
    script = copy.deepcopy(SCRIPT)
    script["config"]["drivers"] = drivers
    assert expect in _msgs(errors(lint(script=script)))


# === subs ===================================================================

SUBS = {
    "Loc": {"title": "Location", "type": "str", "widget": "select",
            "choices": ["a", "b"],
            "subs": {"a": {"Min": {"val": 1, "type": "num"}},
                     "b": {"Min": {"val": 2, "type": "num"}}}},
}


def _subs_script(subs, location="%%Loc", min_arg="%%Min"):
    script = _one_item("EARLY", args={"min": min_arg})
    script["info"]["location"] = location
    script["subs"] = subs
    return script


def test_subs_good(lint):
    assert lint(script=_subs_script(copy.deepcopy(SUBS)), subs_applied=False) == []


@pytest.mark.parametrize("change, expect", [
    # [Unhappy] a choice without inner subs leaves %%Min in the script
    (lambda s: s["Loc"]["subs"].pop("b"), "choice b has no inner subs"),
    # [Unhappy] bad type and widget
    (lambda s: s["Loc"].update(type="int"), "type must be one of ('str', 'num')"),
    (lambda s: s["Loc"].update(widget="radio"),
     "widget must be one of ('textinput', 'select')"),
    # [Unhappy] select without choices
    (lambda s: s["Loc"].pop("choices"), "select needs a non-empty choices list"),
    # [Unhappy] regex that does not compile, default that does not match
    (lambda s: s["Loc"].update(widget="textinput", regex="("), "regex does not compile"),
    (lambda s: s["Loc"].update(widget="textinput", regex=r"^\d+$", default="x"),
     "default does not match regex"),
])
def test_subs_definitions(lint, change, expect):
    subs = copy.deepcopy(SUBS)
    change(subs)
    msgs = _msgs(errors(lint(script=_subs_script(subs), subs_applied=False)))
    assert any(m.startswith(expect) for m in msgs), msgs


def test_subs_used_and_defined(lint):
    # [Unhappy] %%Lot is used but not defined; Loc is defined but not used
    script = _subs_script(copy.deepcopy(SUBS), location="%%Lot")
    findings = lint(script=script, subs_applied=False)
    assert "%%Lot is used but not defined" in _msgs(errors(findings))
    assert "defined but not used" in _msgs(warnings(findings))
