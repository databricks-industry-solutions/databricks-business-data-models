import json, os, types, logging

from notebook_source_util import agent_version_line, cell_containing

NB = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb")


def _full():
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"])


def _extract_func(src, name, end_anchor):
    start = "def " + name + "("
    i = src.index(start)
    j = src.index(end_anchor, i)
    return src[i:j]


def _load_helper(name, end_anchor):
    src = cell_containing("def " + name + "(")
    code = _extract_func(src, name, end_anchor)
    ns = {"logger": logging.getLogger("vov2-test")}
    exec(code, ns)
    return ns[name]


def _load_region(start_anchor, end_anchor, names):
    # extract a contiguous (possibly indented) source region, dedent, exec, return requested names
    import textwrap, ast as _ast
    src = cell_containing(start_anchor)
    i = src.index(start_anchor)
    j = src.index(end_anchor, i)
    code = textwrap.dedent(src[i:j])
    ns = {"logger": logging.getLogger("vov2-test"), "ast": _ast}
    exec(code, ns)
    return tuple(ns[n] for n in names)


def _batch(intent, targets):
    return types.SimpleNamespace(
        intent_summary=intent, target_entities=tuple(targets),
        batch_id="B0001", vreq_ids=("V1",),
    )


def _handler(summary=""):
    return types.SimpleNamespace(expected_changes_summary=summary)


def _model_with(domain, product, attrs):
    return {"domains": [{"name": domain, "data_products": [
        {"name": product, "attributes": attrs, "primary_key": "", "subdomain": "", "description": ""}
    ]}]}


# ============================================================
# FIX 1 (behavioral): deterministic already-satisfied credit
# ============================================================
def test_deterministic_satisfied_pk_present_credits():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("hr", "employee", [{"name": "employee_id", "is_primary_key": True}])
    ok, ev = fn(_batch("ensure primary key on hr.employee", [("hr", "employee")]), _handler(), m)
    assert ok is True, ev
    assert "class=pk" in ev


def test_deterministic_satisfied_pk_missing_does_not_credit():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("hr", "employee", [{"name": "name", "is_primary_key": False}])
    ok, ev = fn(_batch("ensure primary key on hr.employee", [("hr", "employee")]), _handler(), m)
    assert ok is False, ev
    assert "no primary key" in ev


def test_deterministic_satisfied_fk_isolated_does_not_credit():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("proj", "plan", [{"name": "id", "foreign_key_to": None}])
    ok, ev = fn(_batch("ensure proj.plan is not isolated (has a foreign key)", [("proj", "plan")]), _handler(), m)
    assert ok is False, ev
    assert "isolated" in ev


def test_deterministic_satisfied_fk_outbound_credits():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("proj", "plan", [{"name": "proj_id", "foreign_key_to": "proj.project.id"}])
    ok, ev = fn(_batch("ensure proj.plan is not isolated, add foreign key", [("proj", "plan")]), _handler(), m)
    assert ok is True, ev


def test_deterministic_satisfied_unknown_class_is_conservative():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("hr", "employee", [{"name": "x"}])
    ok, ev = fn(_batch("do something vague to hr.employee", [("hr", "employee")]), _handler(), m)
    assert ok is False, ev
    assert "not deterministically checkable" in ev


def test_deterministic_satisfied_missing_target_is_conservative():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("hr", "employee", [{"name": "employee_id", "is_primary_key": True}])
    ok, ev = fn(_batch("ensure primary key on sales.order", [("sales", "order")]), _handler(), m)
    assert ok is False, ev
    assert "not found" in ev


# ============================================================
# FIX 3 (behavioral): unescape literal \n one-line blobs only
# ============================================================
def test_unescape_fixes_literal_newline_blob():
    fn = _load_helper("_vov_unescape_literal_escapes", "\ndef _vov_deterministic_satisfied(")
    blob = "def mutator(model, data):\\n    model['x'] = 1\\n    return model"
    out = fn(blob)
    assert "\n" in out and "\\n" not in out
    # and it now parses as real python
    import ast as _ast
    _ast.parse(out)


def test_unescape_leaves_normal_multiline_code_untouched():
    fn = _load_helper("_vov_unescape_literal_escapes", "\ndef _vov_deterministic_satisfied(")
    real = "def mutator(model, data):\n    s = 'a\\nb'\n    return model"
    assert fn(real) == real  # >2 real newlines -> untouched, embedded \n in string preserved


# ============================================================
# FIX 4 (static): AST gate allows non-destructive introspection
# ============================================================
def test_ast_gate_allows_introspection_blocks_bypass():
    s = _full()
    i = s.index("if fn.id in (")
    tup = s[i:s.index(")", i) + 1]  # the forbidden-call tuple itself
    for allowed in ("globals", "locals", "vars", "dir"):
        assert '"%s"' % allowed not in tup, "introspection %s must NOT be forbidden" % allowed
    for blocked in ("eval", "exec", "compile", "__import__", "open"):
        assert '"%s"' % blocked in tup, "bypass %s must STAY forbidden" % blocked


# ============================================================
# FIX 2 (static): generated code passed via workdir file, not -c argv
# ============================================================
def test_sandbox_runs_code_from_file_not_argv():
    s = _full()
    assert '"-I", "-S", "-c", runner' not in s, "code still passed via -c argv (MAX_ARG_STRLEN risk)"
    assert '_runner_path = os.path.join(workdir, "_vov_runner.py")' in s
    assert '_rf.write(runner)' in s
    assert '[sys.executable, "-I", "-S", _runner_path]' in s
    assert "vov-sandbox-code-via-file FIRED" in s


# ============================================================
# FIX 1 (static): credit injection wired before the noop_failed branch
# ============================================================
def test_deterministic_credit_wired_before_noop():
    s = _full()
    assert "if _is_noop_diff and not _is_already_satisfied:" in s
    i = s.index("if _is_noop_diff and not _is_already_satisfied:")
    seg = s[i:i + 1400]
    assert "_vov_deterministic_satisfied(batch, current_handler, new_model)" in seg
    assert 'status="applied"' in seg
    assert "vov-noop-deterministic-credit FIRED" in seg


# ============================================================
# FIX 1 (static): named-target prompt no longer hard-raises
# ============================================================
def test_named_target_prompt_offers_already_satisfied():
    s = _full()
    assert "already-satisfied-in-model" in s
    assert "vov-verify-already-satisfied" in s
    assert "emit ONLY in case (b)" in s


# ============================================================
# FIX 5 (static): retry hints for no-mutator + list-attr bug
# ============================================================
def test_retry_hints_present():
    s = _full()
    assert "v393-hint-no-mutator" in s
    assert "v393-hint-list-attr" in s
    assert "MISSING MUTATOR" in s
    assert "LIST-vs-DICT BUG" in s


# ============================================================
# FIX 7 (static): sandbox dump relocated to logs folder
# ============================================================
def test_sandbox_dump_relocated_to_logs():
    s = _full()
    assert '_sandbox_dump_dir = config["TARGET_VOLUME"] + "/sandbox"' not in s
    assert '_sandbox_dump_dir = os.path.join(log_dir, "sandbox")' in s
    assert "vov-sandbox-dump-in-logs" in s


# ============================================================
# GAP A (behavioral): deterministic TYPE-credit class (live v3.9.2 ~25 retype raises)
# ============================================================
def test_deterministic_type_credit_all_correct_credits():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("site", "instruction", [
        {"name": "instruction_date", "type": "TIMESTAMP"},
        {"name": "is_active", "type": "BOOLEAN"},
        {"name": "unit_price", "type": "DECIMAL"},
    ])
    ok, ev = fn(_batch("retype temporal attribute on site.instruction", [("site", "instruction")]), _handler(), m)
    assert ok is True, ev
    assert "class=type" in ev


def test_deterministic_type_credit_string_mistype_does_not_credit():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("site", "instruction", [
        {"name": "instruction_date", "type": "STRING"},  # canonical-named but still STRING -> mistyped
    ])
    ok, ev = fn(_batch("retype temporal attribute on site.instruction", [("site", "instruction")]), _handler(), m)
    assert ok is False, ev
    assert "STRING-typed" in ev


def test_deterministic_type_credit_boolean_flag_string_blocks():
    fn = _load_helper("_vov_deterministic_satisfied", "\ndef _apply_handler_with_retry(")
    m = _model_with("hr", "employee", [{"name": "is_manager", "type": "STRING"}])
    ok, ev = fn(_batch("retype boolean-named attribute to boolean on hr.employee", [("hr", "employee")]), _handler(), m)
    assert ok is False, ev


# ============================================================
# GAP B (behavioral): aliased imports rebound to pre-injected modules
# ============================================================
def _strip_fn():
    (fn,) = _load_region("    _VOV_SAFE_PREINJECTED = frozenset(",
                         "    mutator_src = _vov_unescape_literal_escapes(mutator_src)",
                         ["_vov_strip_import_lines"])
    return fn


def test_rebind_aliased_import_re_module():
    fn = _strip_fn()
    out, dropped = fn("import re as re_module\ndef mutator(model, data):\n    re_module.sub('a','b','c')\n    return model")
    assert dropped == 1
    assert "re_module = re" in out
    assert "import re as re_module" not in out


def test_rebind_from_import_datetime_class():
    fn = _strip_fn()
    out, dropped = fn("from datetime import datetime\ndef mutator(model, data):\n    return model")
    assert "datetime = datetime.datetime" in out


def test_rebind_skips_unsafe_module():
    fn = _strip_fn()
    out, dropped = fn("import os as o\ndef mutator(model, data):\n    return model")
    assert dropped == 1
    assert "o = os" not in out  # os not pre-injected -> never rebound (no new capability)
    assert "import os" not in out


def test_rebind_plain_import_needs_no_rebind():
    fn = _strip_fn()
    out, dropped = fn("import re\ndef mutator(model, data):\n    re.sub('a','b','c')\n    return model")
    assert dropped == 1
    assert " = re" not in out  # bare name already pre-injected; no alias to rebind


# ============================================================
# GAP C (behavioral): yield/yield-from AST nodes allowed, eval still blocked
# ============================================================
def _validate_ast_fn():
    (vfn, exc) = _load_region("ALLOWED_AST_NODES = frozenset({",
                              "def required_function_present(",
                              ["validate_ast", "UnsafeCodeError"])
    return vfn, exc


def test_ast_allows_yield():
    vfn, exc = _validate_ast_fn()
    vfn("def gen(model):\n    for x in model:\n        yield x")  # must NOT raise


def test_ast_allows_yield_from():
    vfn, exc = _validate_ast_fn()
    vfn("def gen(model):\n    yield from model")  # must NOT raise


def test_ast_still_blocks_eval():
    vfn, exc = _validate_ast_fn()
    raised = False
    try:
        vfn("def mutator(model, data):\n    eval('1+1')\n    return model")
    except exc:
        raised = True
    assert raised, "eval must STILL be blocked"


# ============================================================
# GAP A/B/C (static): FIRED anchors present
# ============================================================
def test_gap_fired_anchors_present():
    s = _full()
    assert "vov-ast-allow-yield FIRED" in s
    assert "vov-rebind-aliased-import FIRED" in s
    assert "vov-deterministic-type-credit" in s
    assert "ast.Yield, ast.YieldFrom," in s


# ============================================================
# version
# ============================================================
def test_version_is_393():
    """The constant tracks the live release, so a bump cannot redden this file."""
    agent_version_line()


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fns:
        f(); print("PASS", f.__name__)
    print("ALL %d PASS" % len(fns))
