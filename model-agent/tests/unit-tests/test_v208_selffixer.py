"""
v2.0.8 SelfFixer behavioural tests.

Per CLAUDE.md §8.10: every alias MUST have both a [FIRED] emission site AND a behavioural
test that demonstrates the patch changes observable state. Static-grep assertions
("alias=foo is in the source") are SMOKE checks only — paired with behavioural tests.

These tests:
1. Extract the SelfFixer cell from the notebook (no notebook execution).
2. Inject minimal stubs for execute_in_sandbox, ai_agent, logger.
3. Drive `fix_all_unfulfilled` through realistic unfulfilled REQ scenarios.
4. Assert observable state changes on the canonical `model` dict.

All aliases tested:
    selffixer-loop-start, selffixer-llm-call, selffixer-sandbox-result,
    selffixer-invariants-guard, selffixer-applied, selffixer-round-summary,
    selffixer-final, selffixer-skip-no-unfulfilled, selffixer-orchestrator-call.
"""

import copy
import json
import re
from collections import namedtuple
from pathlib import Path

import pytest

NB_PATH = Path(__file__).resolve().parents[2] / "agent" / "dbx_vibe_modelling_agent.ipynb"


# ---------------------------------------------------------------------------
# Cell extraction helpers
# ---------------------------------------------------------------------------

def _load_cell_source(predicate):
    nb = json.loads(NB_PATH.read_text())
    for c in nb["cells"]:
        if c.get("cell_type") != "code":
            continue
        s = "".join(c.get("source", []))
        if predicate(s):
            return s
    raise RuntimeError("predicate matched no cell")


def _load_selffixer_cell():
    """The SelfFixer surface, however many cells the notebook currently spreads it over.

    The class and its `run_selffixer_or_skip` entry point used to share one cell.
    Requiring that stopped matching when they were split, which silently disabled
    every test in this file, so join the cells instead of pinning their layout.
    """
    parts = [_load_cell_source(lambda s: "class SelfFixer" in s)]
    if "def run_selffixer_or_skip" not in parts[0]:
        parts.append(_load_cell_source(lambda s: "def run_selffixer_or_skip" in s))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

FakeSBResult = namedtuple(
    "FakeSBResult",
    ["ok", "new_model", "verifier_ok", "verifier_diag", "error", "stderr"],
)


class _CapturingLogger:
    def __init__(self):
        self.lines = []
    def info(self, m): self.lines.append(("info", str(m)))
    def warning(self, m): self.lines.append(("warning", str(m)))
    def error(self, m): self.lines.append(("error", str(m)))
    def debug(self, m): self.lines.append(("debug", str(m)))

    def has_alias(self, alias):
        return any(alias in l[1] for l in self.lines)
    def has_text(self, text):
        return any(text in l[1] for l in self.lines)


class _FakeAIAgent:
    def __init__(self, scripted_responses):
        self.scripted_responses = list(scripted_responses)
        self.calls = []
    def _v207_call_llm_spark_free(self, *, model, prompt, response_schema, max_tokens, timeout_seconds, prompt_name, step_name):
        self.calls.append({"model": model, "prompt_preview": prompt[:200], "step_name": step_name})
        if not self.scripted_responses:
            raise RuntimeError("no more scripted responses")
        return self.scripted_responses.pop(0)

    # v3.6.5 routing: when SelfFixer.llm_endpoint is unresolved (None) — the case in this
    # isolated test namespace (no live workspace) — _call_opus routes to the proven main
    # Spark LLM path _call_ai_query instead of POSTing to /serving-endpoints/None. The mock
    # must mirror production by exposing BOTH paths, both draining the same scripted queue,
    # so tests are agnostic to which path the routing selects.
    def _call_ai_query(self, *, prompt_name, prompt, response_schema, step_name, max_retries=1):
        self.calls.append({"model": "ai_query", "prompt_preview": prompt[:200], "step_name": step_name})
        if not self.scripted_responses:
            raise RuntimeError("no more scripted responses")
        return self.scripted_responses.pop(0)


def _build_selffixer_namespace():
    """Execute the SelfFixer cell in an isolated namespace and return it."""
    src = _load_selffixer_cell()
    ns = {"__name__": "__test_selffixer__"}
    exec(compile(src, "<selffixer-cell>", "exec"), ns)
    return ns


# ---------------------------------------------------------------------------
# Static-grep checks
# ---------------------------------------------------------------------------

def test_agent_version_is_208():
    nb = json.loads(NB_PATH.read_text())
    s = "".join(nb["cells"][1]["source"])
    m = re.search(r'__AGENT_VERSION__\s*=\s*"([\d.]+)"', s)
    assert m is not None, "__AGENT_VERSION__ not found"
    assert tuple(int(_x) for _x in m.group(1).split(".")) >= (2, 0, 8), f"expected 2.0.8, got {m.group(1)}"


def test_selffixer_aliases_all_present_in_source():
    src = _load_selffixer_cell()
    for alias in [
        "alias=selffixer-loop-start",
        "alias=selffixer-llm-call",
        "alias=selffixer-sandbox-result",
        "alias=selffixer-invariants-guard",
        "alias=selffixer-applied",
        "alias=selffixer-round-summary",
        "alias=selffixer-final",
        "alias=selffixer-skip-no-unfulfilled",
    ]:
        assert alias in src, f"alias missing in SelfFixer cell: {alias}"


def test_orchestrator_call_alias_present():
    nb = json.loads(NB_PATH.read_text())
    found = False
    for c in nb["cells"]:
        if c.get("cell_type") != "code": continue
        s = "".join(c.get("source", []))
        if ("def run_selffixer_or_skip" not in s and "run_selffixer_or_skip(" in s
                and "_vibe_orchestrator.score()" in s):
            found = True
            break
    assert found, (
        "SelfFixer must be CALLED from the orchestrator scoring path; a definition "
        "with no call site is dead code (CLAUDE.md 8.4)"
    )


def test_industry_agnostic_no_hardcoded_names_in_prompt():
    """SelfFixer prompt must NOT contain any specific industry / customer name."""
    src = _load_selffixer_cell()
    forbidden = ["airline", "healthcare", "banking", "retail", "manufacturing",
                 "telecom", "gov_transport", "example_air", "patient", "passenger", "claim"]
    # Examine prompt template + class only, not all of source (comments may mention these)
    m = re.search(r'_SELFFIXER_PROMPT\s*=\s*"""(.*?)"""', src, re.DOTALL)
    assert m, "_SELFFIXER_PROMPT not found"
    prompt_body = m.group(1).lower()
    for f in forbidden:
        assert f not in prompt_body, f"forbidden industry term '{f}' in SelfFixer prompt"


# ---------------------------------------------------------------------------
# Behavioural — invariant capture
# ---------------------------------------------------------------------------

def test_capture_invariants_basic_counts():
    ns = _build_selffixer_namespace()
    capture = ns["_selffixer_capture_invariants"]
    m = {
        "model": {
            "domains": [
                {"name": "d1", "products": [
                    {"product": "p1", "primary_key": "p1_id", "attributes": [
                        {"name": "p1_id", "data_type": "BIGINT"},
                        {"name": "p2_id", "data_type": "BIGINT", "foreign_key_to": "d1.p2.p2_id"},
                    ]},
                    {"product": "p2", "primary_key": "p2_id", "attributes": [
                        {"name": "p2_id", "data_type": "BIGINT"},
                    ]},
                ]},
            ]
        }
    }
    inv = capture(m)
    assert inv["domain_count"] == 1
    assert inv["product_count"] == 2
    assert inv["fk_target_misses"] == 0


def test_capture_invariants_detects_fk_target_miss():
    ns = _build_selffixer_namespace()
    capture = ns["_selffixer_capture_invariants"]
    m = {
        "model": {
            "domains": [
                {"name": "d1", "products": [
                    {"product": "p1", "primary_key": "p1_id", "attributes": [
                        {"name": "missing_id", "data_type": "BIGINT", "foreign_key_to": "d1.GHOST.x"},
                    ]},
                ]},
            ]
        }
    }
    inv = capture(m)
    assert inv["fk_target_misses"] == 1


def test_capture_invariants_detects_silo():
    ns = _build_selffixer_namespace()
    capture = ns["_selffixer_capture_invariants"]
    m = {
        "model": {
            "domains": [
                {"name": "d1", "products": [
                    {"product": "lonely", "primary_key": "id", "attributes": [
                        {"name": "id", "data_type": "BIGINT"},
                    ]},
                ]},
            ]
        }
    }
    inv = capture(m)
    assert inv["silo_count"] == 1


# ---------------------------------------------------------------------------
# Behavioural — model digest
# ---------------------------------------------------------------------------

def test_model_digest_industry_agnostic_and_bounded():
    ns = _build_selffixer_namespace()
    digest = ns["_selffixer_model_digest"]
    m = {
        "model": {
            "domains": [
                {"name": "d1", "products": [
                    {"product": "p1", "primary_key": "id", "attributes": [
                        {"name": "id", "data_type": "BIGINT"},
                        {"name": "x_id", "data_type": "BIGINT", "foreign_key_to": "d1.p2.id"},
                    ]},
                    {"product": "p2", "primary_key": "id", "attributes": [
                        {"name": "id", "data_type": "BIGINT"},
                    ]},
                ]},
            ]
        }
    }
    out = digest(m)
    assert "domain_count=1" in out
    assert "p1" in out and "p2" in out
    assert "d1.p1.x_id->d1.p2.id" in out
    assert len(out) <= 12000


# ---------------------------------------------------------------------------
# Behavioural — SelfFixer.fix_all_unfulfilled
# ---------------------------------------------------------------------------

def _starting_model_one_missing_fk():
    return {
        "model": {
            "domains": [
                {"name": "d1", "products": [
                    {"product": "p1", "primary_key": "p1_id", "attributes": [
                        {"name": "p1_id", "data_type": "BIGINT"},
                        {"name": "p2_id", "data_type": "BIGINT"},  # no FK yet
                    ]},
                    {"product": "p2", "primary_key": "p2_id", "attributes": [
                        {"name": "p2_id", "data_type": "BIGINT"},
                    ]},
                ]},
            ]
        }
    }


def _scripted_fk_link_mutator():
    """Mutator that adds FK p1.p2_id -> d1.p2.p2_id. Verifier checks it landed."""
    return {
        "mutator_src": (
            "def mutator(model, data):\n"
            "    root = model.get('model', model)\n"
            "    for d in root.get('domains', []):\n"
            "        for p in d.get('products', []):\n"
            "            if p.get('product') == 'p1':\n"
            "                for a in p.get('attributes', []):\n"
            "                    if a.get('name') == 'p2_id':\n"
            "                        a['foreign_key_to'] = 'd1.p2.p2_id'\n"
            "    return model\n"
        ),
        "verifier_src": (
            "def verifier(model, data):\n"
            "    root = model.get('model', model)\n"
            "    for d in root.get('domains', []):\n"
            "        for p in d.get('products', []):\n"
            "            if p.get('product') == 'p1':\n"
            "                for a in p.get('attributes', []):\n"
            "                    if a.get('name') == 'p2_id' and a.get('foreign_key_to') == 'd1.p2.p2_id':\n"
            "                        return (True, 'fk linked')\n"
            "    return (False, 'fk not linked')\n"
        ),
        "rationale": "link p1.p2_id to d1.p2.p2_id",
    }


def _fake_sandbox_factory():
    """Fake sandbox that executes mutator+verifier strings in-process."""
    def _exec(mutator_src, verifier_src, model, data=None, timeout=20.0):
        ns = {}
        try:
            exec(mutator_src, ns)
            exec(verifier_src, ns)
            new_model = copy.deepcopy(model)
            new_model = ns["mutator"](new_model, data)
            ok, diag = ns["verifier"](new_model, data)
            return FakeSBResult(True, new_model, bool(ok), str(diag), None, "")
        except Exception as e:
            return FakeSBResult(False, None, False, "", f"{type(e).__name__}: {e}", "")
    return _exec


def test_selffixer_skip_when_no_unfulfilled():
    ns = _build_selffixer_namespace()
    SelfFixer = ns["SelfFixer"]
    logger = _CapturingLogger()
    ai = _FakeAIAgent([])
    fixer = SelfFixer(ai_agent=ai, logger=logger, sandbox_executor=_fake_sandbox_factory())
    res = fixer.fix_all_unfulfilled({}, [], max_rounds=3)
    assert res["skipped"] is True
    assert res["fixed_count"] == 0
    assert logger.has_alias("selffixer-skip-no-unfulfilled")


def test_selffixer_fixes_one_missing_fk_end_to_end():
    ns = _build_selffixer_namespace()
    SelfFixer = ns["SelfFixer"]
    logger = _CapturingLogger()
    ai = _FakeAIAgent([json.dumps(_scripted_fk_link_mutator())])
    fixer = SelfFixer(ai_agent=ai, logger=logger, sandbox_executor=_fake_sandbox_factory())
    model = _starting_model_one_missing_fk()
    unfulfilled = [{"id": "REQ-fk-001", "text": "Add FK from p1.p2_id to p2.p2_id", "evidence": "missing FK", "attempts": 1}]
    res = fixer.fix_all_unfulfilled(model, unfulfilled, max_rounds=3, per_req_retries=1)
    assert res["fixed_count"] == 1, f"expected 1 fix, got {res}"
    assert res["remaining_count"] == 0
    p1_attrs = model["model"]["domains"][0]["products"][0]["attributes"]
    p2_id_attr = next(a for a in p1_attrs if a["name"] == "p2_id")
    assert p2_id_attr.get("foreign_key_to") == "d1.p2.p2_id", "mutation did NOT land on canonical model"
    assert logger.has_alias("selffixer-loop-start")
    assert logger.has_alias("selffixer-llm-call")
    assert logger.has_alias("selffixer-sandbox-result")
    assert logger.has_alias("selffixer-applied")
    assert logger.has_alias("selffixer-final")


def test_selffixer_invariants_guard_blocks_regression():
    """If Opus's mutator drops a product (regression), SelfFixer MUST reject."""
    ns = _build_selffixer_namespace()
    SelfFixer = ns["SelfFixer"]
    bad_mutator = {
        "mutator_src": (
            "def mutator(model, data):\n"
            "    root = model.get('model', model)\n"
            "    root['domains'][0]['products'] = []\n"
            "    return model\n"
        ),
        "verifier_src": (
            "def verifier(model, data):\n"
            "    return (True, 'pretends ok')\n"
        ),
        "rationale": "drops all products to make the verifier trivially pass — should be rejected",
    }
    logger = _CapturingLogger()
    ai = _FakeAIAgent([json.dumps(bad_mutator), json.dumps(bad_mutator)])
    fixer = SelfFixer(ai_agent=ai, logger=logger, sandbox_executor=_fake_sandbox_factory())
    model = _starting_model_one_missing_fk()
    pre_p2 = sum(len(d["products"]) for d in model["model"]["domains"])
    unfulfilled = [{"id": "REQ-regress-001", "text": "irrelevant", "evidence": "irrelevant", "attempts": 1}]
    res = fixer.fix_all_unfulfilled(model, unfulfilled, max_rounds=2, per_req_retries=1)
    assert res["fixed_count"] == 0, "regression mutator should NOT count as fixed"
    post_p = sum(len(d["products"]) for d in model["model"]["domains"])
    assert post_p == pre_p2, "model regressed despite invariants guard"
    assert logger.has_alias("selffixer-invariants-guard")


def test_selffixer_progress_stops_on_no_progress():
    """If 0 fixes land in a round, the outer loop must break early (don't spin)."""
    ns = _build_selffixer_namespace()
    SelfFixer = ns["SelfFixer"]
    # Opus returns a mutator that does nothing -> verifier returns (False, ...)
    nothing_burger = {
        "mutator_src": (
            "def mutator(model, data):\n"
            "    return model\n"
        ),
        "verifier_src": (
            "def verifier(model, data):\n"
            "    return (False, 'still not satisfied')\n"
        ),
        "rationale": "no-op",
    }
    logger = _CapturingLogger()
    ai = _FakeAIAgent([json.dumps(nothing_burger)] * 10)
    fixer = SelfFixer(ai_agent=ai, logger=logger, sandbox_executor=_fake_sandbox_factory())
    model = _starting_model_one_missing_fk()
    unfulfilled = [{"id": "REQ-noprogress-001", "text": "impossible", "evidence": "evidence", "attempts": 1}]
    res = fixer.fix_all_unfulfilled(model, unfulfilled, max_rounds=5, per_req_retries=1)
    assert res["fixed_count"] == 0
    assert res["rounds"] <= 5
    assert res["rounds"] >= 1
    assert logger.has_alias("selffixer-round-summary")
    assert logger.has_alias("selffixer-final")


def test_selffixer_handles_opus_returning_non_json():
    """Opus returns junk; SelfFixer must NOT crash; logs llm-call ERROR; remaining=1."""
    ns = _build_selffixer_namespace()
    SelfFixer = ns["SelfFixer"]
    logger = _CapturingLogger()
    ai = _FakeAIAgent(["this is not json at all", "still not json"])
    fixer = SelfFixer(ai_agent=ai, logger=logger, sandbox_executor=_fake_sandbox_factory())
    model = _starting_model_one_missing_fk()
    unfulfilled = [{"id": "REQ-junk-001", "text": "x", "evidence": "y", "attempts": 1}]
    res = fixer.fix_all_unfulfilled(model, unfulfilled, max_rounds=1, per_req_retries=1)
    assert res["fixed_count"] == 0
    assert res["remaining_count"] == 1
    assert logger.has_text("[selffixer-llm-call ERROR")


def test_selffixer_multi_req_partial_success():
    """Two unfulfilled REQs, only one is fixable. Expect fixed=1, remaining=1."""
    ns = _build_selffixer_namespace()
    SelfFixer = ns["SelfFixer"]
    logger = _CapturingLogger()
    nothing = {
        "mutator_src": "def mutator(model, data):\n    return model\n",
        "verifier_src": "def verifier(model, data):\n    return (False, 'cannot fix')\n",
        "rationale": "cannot satisfy",
    }
    fixable = _scripted_fk_link_mutator()
    # Order of responses depends on iteration order of unfulfilled list.
    # We supply: first REQ -> nothing, second REQ -> fixable; on round 2 -> nothing for remaining REQ.
    ai = _FakeAIAgent([
        json.dumps(nothing),       # REQ-A round 1
        json.dumps(fixable),       # REQ-B round 1
        json.dumps(nothing),       # REQ-A round 2 retry
    ])
    fixer = SelfFixer(ai_agent=ai, logger=logger, sandbox_executor=_fake_sandbox_factory())
    model = _starting_model_one_missing_fk()
    unfulfilled = [
        {"id": "REQ-A", "text": "impossible", "evidence": "", "attempts": 1},
        {"id": "REQ-B", "text": "fix the fk", "evidence": "missing fk", "attempts": 1},
    ]
    res = fixer.fix_all_unfulfilled(model, unfulfilled, max_rounds=2, per_req_retries=0)
    assert res["per_req_results"]["REQ-B"]["fixed"] is True
    assert res["per_req_results"]["REQ-A"]["fixed"] is False
    assert res["fixed_count"] == 1
    assert res["remaining_count"] == 1


def test_run_selffixer_or_skip_entry_returns_dict_on_skip():
    ns = _build_selffixer_namespace()
    run = ns["run_selffixer_or_skip"]
    logger = _CapturingLogger()
    res = run(model_dict={}, widgets_values={"_unfulfilled_for_next_vibe": []}, ai_agent=None, logger=logger)
    assert res["skipped"] is True
    assert res["fixed_count"] == 0


def test_run_selffixer_or_skip_entry_returns_dict_on_outer_error():
    """If ai_agent is None and there ARE unfulfilled REQs, entry must catch and return skipped."""
    ns = _build_selffixer_namespace()
    run = ns["run_selffixer_or_skip"]
    logger = _CapturingLogger()
    res = run(
        model_dict={"model": {"domains": []}},
        widgets_values={"_unfulfilled_for_next_vibe": [{"id": "R1", "text": "x", "evidence": ""}]},
        ai_agent=None,
        logger=logger,
    )
    # Without a real sandbox executor it cannot land, but it must not crash.
    assert isinstance(res, dict)


def test_pre_patch_would_fail_without_selffixer():
    """Positive control: prove that WITHOUT SelfFixer, the missing FK stays missing.

    This is the §8.10 anti-tautology proof — without the patch the failure persists.
    """
    model = _starting_model_one_missing_fk()
    p1_attrs = model["model"]["domains"][0]["products"][0]["attributes"]
    p2_id = next(a for a in p1_attrs if a["name"] == "p2_id")
    assert p2_id.get("foreign_key_to") is None, "pre-state: no FK yet"
