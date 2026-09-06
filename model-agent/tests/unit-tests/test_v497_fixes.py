# -*- coding: utf-8 -*-
"""v4.9.7 regression guards for three root-cause fixes found in the airline tester run.

Fix 1 (enlarge TIMEOUT): the resize dispatch (`_run_resize_model` for shrink/enlarge) ran
BEFORE `VibeOrchestrator.parse()` populated `widgets_values['sizing_directives']`, so the
USER-VIBE-CLAMP read an empty dict and enlarge ignored the user's "max N domains" model_vibes
cap, building an oversized ECM that exceeded the tester's 9000s timeout. The dispatch now runs
AFTER the orchestrator parse.

Fix 3 (domain-enrichment dict!=str): `validate_single_domain_wrapper` called
`json.loads(response_text)` unconditionally, but the worker loop already hands it a parsed dict
-> "the JSON object must be str, bytes or bytearray, not dict". The site now uses the same
`isinstance(..., str)` guard as the 9+ other parse sites.

Fix 2a (convention-score artifact): the tester convention average included guard-rail tests
(10_empty_vibes, 13_no_biz_name) that produce NO model and were scored against another test's
model. TestResult now carries `produced_model`; the audit loop skips non-producers.
"""
import json
import os

from notebook_source_util import (
    assert_agent_version_at_least,
    cell_containing,
    slice_function_source,
)

TESTER_NB = os.path.join(os.path.dirname(__file__), "..", "vibe_tester.ipynb")


def _tester_main_cell():
    nb = json.load(open(TESTER_NB))
    for c in nb["cells"]:
        if c.get("cell_type") == "code":
            s = "".join(c.get("source", []))
            if "_MODEL_PRODUCING_OPS" in s:
                return s
    raise AssertionError("tester main cell not found")


# ---------------- version ----------------
def test_agent_version_at_least_497():
    assert_agent_version_at_least("4.9.7")


# ---------------- Fix 1: resize ordering ----------------
def test_resize_dispatch_runs_after_vibe_orchestrator_parse():
    src = cell_containing("v497-resize-after-vibe-parse")
    lines = src.split("\n")
    parse_idx = [i for i, l in enumerate(lines) if "_vibe_orchestrator.parse()" in l]
    enlarge_idx = [i for i, l in enumerate(lines) if '_run_resize_model(widgets_values, "enlarge")' in l]
    assert parse_idx, "orchestrator parse() call missing"
    assert enlarge_idx, "enlarge resize dispatch missing"
    # every resize dispatch must come AFTER parse() populates sizing_directives (fail-pre: pre-patch it was before)
    assert min(enlarge_idx) > max(parse_idx), (
        "enlarge dispatch must run AFTER _vibe_orchestrator.parse(); "
        f"parse at {parse_idx}, enlarge at {enlarge_idx}"
    )


def test_resize_dispatch_moved_not_duplicated():
    src = cell_containing("v497-resize-after-vibe-parse")
    assert src.count('_run_resize_model(widgets_values, "enlarge")') == 1
    assert src.count('_run_resize_model(widgets_values, "shrink")') == 1


# ---------------- Fix 3: enrichment str/dict guard ----------------
def test_enrich_site_has_isinstance_guard():
    src = cell_containing('site="c156-enrich"')
    guarded = 'json.loads(response_text) if isinstance(response_text, str) else response_text, site="c156-enrich"'
    unguarded = '_v466_coerce_llm_obj(json.loads(response_text), site="c156-enrich")'
    assert guarded in src, "c156-enrich must guard str vs dict before json.loads"
    assert unguarded not in src, "pre-patch unguarded json.loads(dict) must be gone"


def test_enrich_guard_expression_handles_dict_and_str():
    # eval the EXACT expression shipped in the notebook against a dict (the bug) and a str
    src = cell_containing('site="c156-enrich"')
    line = next(l for l in src.split("\n") if 'site="c156-enrich"' in l)
    expr = "json.loads(response_text) if isinstance(response_text, str) else response_text"
    assert expr in line

    def run(response_text):
        return eval(expr, {"json": json}, {"response_text": response_text})

    assert run({"domains": [{"domain": "x"}]}) == {"domains": [{"domain": "x"}]}  # dict passes through
    assert run('{"domains": []}') == {"domains": []}  # str is parsed


# ---------------- Fix 2a: convention-score artifact ----------------
def test_testresult_has_produced_model_flag():
    src = slice_function_source("TestResult.__init__", source=_tester_main_cell())
    assert "produced_model=True" in src
    assert "self.produced_model = produced_model" in src


def test_negative_tests_marked_non_producing():
    src = _tester_main_cell()
    assert 'td_10["params"], produced_model=False))' in src, "10_empty_vibes must be produced_model=False"
    assert 'params=td_13["params"], produced_model=False))' in src, "13_no_biz_name must be produced_model=False"


def test_empty_vibes_passed_branch_marked_non_producing():
    # 10_empty_vibes has TWO append paths: the FAILED branch builds a TestResult with
    # produced_model=False, but the PASSED/exit_with_warning branch re-appends the raw
    # run_test result (produced_model defaults True) -> its snake_case no-op copy leaked
    # into the convention average (57.5% instead of 75.8%). Both branches must exclude it.
    src = _tester_main_cell()
    passed_branch = src.split('if r12.status == "PASSED":', 1)[1].split("elif r12.status", 1)[0]
    assert "r12.produced_model = False" in passed_branch, \
        "empty_vibes PASSED branch must mark produced_model=False before R.append(r12)"
    assert passed_branch.index("r12.produced_model = False") < passed_branch.index("R.append(r12)")


def test_audit_loop_skips_non_producing_tests():
    src = _tester_main_cell()
    assert "v497-conv-skip-nonproducing" in src
    assert 'if not getattr(tr, "produced_model", True):' in src


# ---------------- Fix 1b: resize/base builders inherit the session vibes cap ----------------
def test_model_producing_builders_inherit_session_vibes_cap():
    # ROOT CAUSE of the enlarge TIMEOUT: _build_resize passed bare w_model_vibes, so an empty
    # tester model_vibes widget meant enlarge got NO cap -> full 8-domain ECM -> 2.5h timeout,
    # while the base model already defaulted to "max 2 domains". Both builders must default now.
    src = _tester_main_cell()
    assert '_DEFAULT_TEST_VIBES = "maximum of 2 domains, and 8 tables for any model you generate"' in src
    # both org_pool builders (_build_base_model, _build_resize) + the base use the fallback
    assert src.count('"model_vibes": (w_model_vibes or _DEFAULT_TEST_VIBES),') == 3
    # fail-pre: the bare no-fallback form must be gone from the org_pool builders
    assert '"org_divisions": _pick(org_pool),\n                "model_vibes": w_model_vibes,\n' not in src


def test_default_vibes_fallback_expression_behaviour():
    default = "maximum of 2 domains, and 8 tables for any model you generate"
    assert ("" or default) == default            # empty widget -> cap applied (the fix)
    assert ("keep 5 domains" or default) == "keep 5 domains"  # explicit vibe wins


def test_testresult_produced_model_default_and_override():
    # exec the real TestResult class in isolation and prove the flag behaves
    import ast

    src = _tester_main_cell()
    tree = ast.parse(src)
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TestResult")
    class_src = "".join(src.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])
    ns = {}
    exec(compile(class_src, "TestResult", "exec"), ns)
    TestResult = ns["TestResult"]
    assert TestResult("t", "l", "PASSED", 1).produced_model is True
    assert TestResult("t", "l", "PASSED", 1, produced_model=False).produced_model is False
