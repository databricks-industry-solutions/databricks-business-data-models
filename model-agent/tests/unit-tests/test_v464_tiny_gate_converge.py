"""v4.6.4 — behavioral tests for tiny-scoped trust/support gate convergence.

ROOT CAUSE (v4.6.3 Test-00 audit): _tier_aware_architect_gate_keys skipped only the two
ASPIRATIONAL gates (recommend_to_industry_peers, propose_for_global_standard) on tiny models,
keeping trust_in_production/support_in_production as HARD gates. Those two auto-"No" on
"weak coverage / incomplete domain" — which for an INTENTIONALLY tiny (test/smoke) model is
by design — so the domain + global architect reviews never converged, burned the full 8-iter
ceiling, emitted `⚠️ failed gates` WARNINGs, and queued "add more products" required_actions
that directly contradict the user's explicit tiny vibe (§3c heuristic-overrides-user).

FIX (v4.6.4 alias=tiny-trust-support-converge):
  - _tier_aware_architect_gate_keys skips ALL FOUR production-readiness gates on tiny scope
    (structural correctness stays enforced by the authoritative deterministic SA gates + the
    23 architect structural TESTS).
  - both early-exit checks (domain cell + global cell) scope the required-gate set to the
    ACTIVE tier-aware gates, so `all([]) == True` => the review converges on tiny.

These tests slice the REAL module-level function from the notebook and assert observable
behavior. The tiny cases FAIL on pre-patch HEAD (trust/support kept active -> never converge)
and PASS post-patch (all 4 skipped -> converge).
"""
import ast
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _concat_source():
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    return "\n\n".join(parts)


SOURCE = _concat_source()


def _tier_ns():
    lines = SOURCE.splitlines(keepends=True)
    tree = ast.parse(SOURCE)
    wanted = {}
    for node in tree.body:
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    name = t.id
        if name in ("_GATE_ORDER", "_V463_GATE_MARKERS", "_tier_aware_architect_gate_keys"):
            wanted[name] = "".join(lines[node.lineno - 1: node.end_lineno])
    missing = {"_GATE_ORDER", "_V463_GATE_MARKERS", "_tier_aware_architect_gate_keys"} - set(wanted)
    if missing:
        raise LookupError(f"missing: {missing}")
    blob = "\n\n".join([wanted["_GATE_ORDER"], wanted["_V463_GATE_MARKERS"], wanted["_tier_aware_architect_gate_keys"]])
    ns = {"__name__": "_test_tier"}
    exec(compile(blob, str(NOTEBOOK_PATH), "exec"), ns)
    return ns


ALL_FOUR = ("trust_in_production", "support_in_production",
            "recommend_to_industry_peers", "propose_for_global_standard")


def test_tiny_by_products_skips_all_four_gates():
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, skipped = f({"max_total_products": 15, "max_domains": 3})
    assert active == ()
    assert set(skipped) == set(ALL_FOUR)


def test_tiny_by_domains_only_skips_all_four_gates():
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, skipped = f({"max_domains": 4})  # <=5 -> tiny even with no product cap
    assert active == ()
    assert set(skipped) == set(ALL_FOUR)


def test_full_tier_keeps_all_four_gates():
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, skipped = f({"max_total_products": 160, "max_domains": 12})
    assert set(active) == set(ALL_FOUR)
    assert skipped == ()


def test_no_directives_keeps_all_four_gates():
    """No sizing directives (no-vibe full run) => not tiny => full production bar."""
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, skipped = f({})
    assert set(active) == set(ALL_FOUR)
    assert skipped == ()


def _converges(active_gates, snapshot):
    """Replicate the post-patch early-exit rule: required = active ∩ {trust,support};
    converge iff all required answered 'yes'. all([]) is True."""
    required = tuple(g for g in ("trust_in_production", "support_in_production") if g in active_gates)
    return all(str(snapshot.get(g, "")).strip().lower() == "yes" for g in required)


def test_tiny_converges_even_when_trust_support_are_no():
    """The exact non-convergence scenario: LLM answers trust/support = No on a tiny model.
    Pre-patch (required = trust+support) => never converges. Post-patch (tiny skips them,
    required = ()) => converges."""
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, _ = f({"max_total_products": 15})
    snapshot = {"trust_in_production": "No", "support_in_production": "No"}
    assert _converges(active, snapshot) is True


def test_full_tier_does_not_converge_when_trust_support_are_no():
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, _ = f({"max_total_products": 160})
    snapshot = {"trust_in_production": "No", "support_in_production": "Yes"}
    assert _converges(active, snapshot) is False


def test_full_tier_converges_when_trust_support_yes():
    ns = _tier_ns()
    f = ns["_tier_aware_architect_gate_keys"]
    active, _ = f({"max_total_products": 160})
    snapshot = {"trust_in_production": "Yes", "support_in_production": "Yes"}
    assert _converges(active, snapshot) is True


def test_aliases_and_scoped_early_exit_in_source():
    assert "tiny-trust-support-converge FIRED v4.6.4" in SOURCE
    # both early-exit sites now intersect with the active-gate list (no unconditional tuple)
    assert "_gn for _gn in (\"trust_in_production\", \"support_in_production\") if _gn in _gate_names" in SOURCE
    assert "_gk for _gk in (\"trust_in_production\", \"support_in_production\") if _gk in _ee_active" in SOURCE
    # tier-aware func skips the whole gate order on tiny
    assert "skipped = tuple(_GATE_ORDER) if is_tiny else ()" in SOURCE
