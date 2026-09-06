"""v3.9.4 behavioral guards (§8.10 fail-pre/pass-post) for the two root-cause fixes from the
travel_hospitality + restaurants v3.9.2 independent VReq audits:

  FIX #1 (alias=vov-finalize-deterministic-cycle-break): the VOV review finalize ran the pre-SA
    autofix (no cycle/bidirectional breaker) but NEVER invoked the base-model Step 7D cycle-break,
    so LLM-applied SSOT cross-reference FKs forming A<->B (or longer) cycles shipped (restaurants: 5
    of its bidirectional pairs came straight from the SSOT cross-domain resolver). The new
    module-level helper `_v394_break_post_vov_cycles` reuses the EXISTING `_detect_cycles_dfs` +
    `_break_cycles_heuristic_internal` (no LLM => serverless-safe) and is called at finalize.

  FIX #2 (alias=verifier-structural-move-type-count): product-MOVE, attribute-TYPE-fix and
    stub/skeleton attribute-COUNT VReqs were NOT covered by the deterministic verifier, so they fell
    to the budget-starved LLM path and false-negatived (verifier-skipped-budget) -- the mission's #1
    lying-scoreboard lever. The new method `VibeOrchestrator._v394_verify_move_type_count` decides
    these three classes from the after-state dict with NO budget, FULFILLED-ONLY (can rescue a
    false-negative, can never inflate).

These tests do their own targeted AST extraction of the EXACT notebook symbols (no reimplementation)
and honour the VOV_NB env var so the suite can be run fail-pre against the v3.9.3 backup:
    VOV_NB=/tmp/agent_v393_backup.ipynb pytest tests/unit-tests/test_v394_cycle_and_verifier.py
    -> both new symbols are ABSENT => the dependent tests xfail/error (the §8.10 fail-pre proof).
"""
import ast
import json
import logging
import os
import textwrap
from collections import defaultdict

import pytest

NB = os.environ.get(
    "VOV_NB",
    "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb",
)

LG = logging.getLogger("t394")
LG.addHandler(logging.NullHandler())


def _src():
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")


def _extract_funcs(names):
    """Return {name: source} for top-level FunctionDefs whose name is in `names`."""
    src = _src()
    tree = ast.parse(src)
    lines = src.split("\n")
    out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            out[node.name] = "\n".join(lines[node.lineno - 1:node.end_lineno])
    return out


def _extract_const_deps(func_sources):
    """Pull top-level constant (literal) Assigns referenced-by-name in the extracted functions, so
    helpers like _heuristic_edge_break_score that close over module constants (_CONVENIENCE_FK_PREFIXES)
    resolve when exec'd in isolation. Only literal/tuple/list/set/dict-of-constants Assigns are kept
    (no spark-dependent expressions)."""
    src = _src()
    tree = ast.parse(src)
    lines = src.split("\n")
    used = set()
    for fs in func_sources:
        for n in ast.walk(ast.parse(fs)):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                used.add(n.id)
    LITERAL = (ast.Constant, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.UnaryOp)
    out = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in used and isinstance(node.value, LITERAL):
                out.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
    return out


def _extract_method(class_name, method_name):
    """Return the dedented source of one method, hoisted to a module-level def (self stays the
    first positional param but is otherwise inert in the methods we test)."""
    src = _src()
    tree = ast.parse(src)
    lines = src.split("\n")
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name == method_name:
                    return textwrap.dedent("\n".join(lines[sub.lineno - 1:sub.end_lineno]))
    return None


def _ns_with(func_sources):
    ns = {"defaultdict": defaultdict}
    blob = "\n\n".join(func_sources)
    exec(compile(blob, "<v394-extract>", "exec"), ns)
    return ns


# ---------------------------------------------------------------------------
# FIX #1 -- deterministic SSOT cycle/bidirectional break at VOV finalize
# ---------------------------------------------------------------------------
_CYCLE_DEPS = [
    "_detect_direct_bidirectional_links",
    "_detect_cycles_dfs",
    "_compute_edge_betweenness_for_cycles",
    "_heuristic_edge_break_score",
    "_is_convenience_fk",
    "_break_cycles_heuristic_internal",
    "_v394_break_post_vov_cycles",
]


@pytest.fixture(scope="module")
def cyc_ns():
    segs = _extract_funcs(set(_CYCLE_DEPS))
    if "_v394_break_post_vov_cycles" not in segs:
        pytest.fail("FAIL-PRE: _v394_break_post_vov_cycles ABSENT from notebook (expected pre-patch)")
    missing = [n for n in _CYCLE_DEPS if n not in segs]
    assert not missing, f"reused cycle helpers missing: {missing}"
    func_sources = [segs[n] for n in _CYCLE_DEPS]
    return _ns_with(_extract_const_deps(func_sources) + func_sources)


def _bidir_model():
    """Two products with a DIRECT bidirectional FK pair (operations.a <-> business.b). Flat-SSOT
    attribute shape (domain/product/attribute/type/foreign_key_to) used at VOV finalize."""
    products = [
        {"domain": "operations", "product": "a"},
        {"domain": "business", "product": "b"},
    ]
    attrs = [
        {"domain": "operations", "product": "a", "attribute": "a_id", "type": "BIGINT", "tags": "primary_key"},
        {"domain": "operations", "product": "a", "attribute": "b_ref", "type": "BIGINT",
         "foreign_key_to": "business.b.b_id"},
        {"domain": "business", "product": "b", "attribute": "b_id", "type": "BIGINT", "tags": "primary_key"},
        {"domain": "business", "product": "b", "attribute": "a_ref", "type": "BIGINT",
         "foreign_key_to": "operations.a.a_id"},
    ]
    return products, attrs


def test_bidirectional_pair_is_broken(cyc_ns):
    """A<->B bidirectional FK is detected and ONE edge deterministically removed; re-detection finds
    0 cycles afterward. Proves observable state change (cycle -> no cycle)."""
    fn = cyc_ns["_v394_break_post_vov_cycles"]
    detect = cyc_ns["_detect_cycles_dfs"]
    products, attrs = _bidir_model()
    assert len(detect(products, attrs, LG)) >= 1  # cycle present pre-break
    broken = fn(products, attrs, LG)
    assert broken >= 1
    assert len(detect(products, attrs, LG)) == 0  # cycle gone post-break
    # exactly one of the two cross FKs survives (edge-removal, not both-cleared)
    surviving_fks = [a for a in attrs if a.get("foreign_key_to")]
    assert len(surviving_fks) == 1


def test_clean_model_is_noop(cyc_ns):
    """A model with no cycle returns 0 and mutates nothing (idempotent backstop)."""
    fn = cyc_ns["_v394_break_post_vov_cycles"]
    products = [
        {"domain": "operations", "product": "a"},
        {"domain": "business", "product": "b"},
    ]
    attrs = [
        {"domain": "operations", "product": "a", "attribute": "a_id", "type": "BIGINT", "tags": "primary_key"},
        {"domain": "operations", "product": "a", "attribute": "b_ref", "type": "BIGINT",
         "foreign_key_to": "business.b.b_id"},
        {"domain": "business", "product": "b", "attribute": "b_id", "type": "BIGINT", "tags": "primary_key"},
    ]
    before = json.dumps(attrs, sort_keys=True)
    assert fn(products, attrs, LG) == 0
    assert json.dumps(attrs, sort_keys=True) == before


# ---------------------------------------------------------------------------
# FIX #2 -- deterministic MOVE / TYPE / COUNT verifier (FULFILLED-ONLY)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def mtc_fn():
    method_src = _extract_method("VibeOrchestrator", "_v394_verify_move_type_count")
    if method_src is None:
        pytest.fail("FAIL-PRE: VibeOrchestrator._v394_verify_move_type_count ABSENT (expected pre-patch)")
    ns = {"defaultdict": defaultdict}
    exec(compile(method_src, "<v394-method>", "exec"), ns)
    return ns["_v394_verify_move_type_count"]


class _Req:
    def __init__(self, text, scope_targets=None):
        self.original_text = text
        self.scope_targets = scope_targets or []
        self.id = "VREQ-T"


def _move_model(prod, domain):
    return ([{"domain": domain, "product": prod}],
            [{"domain": domain, "product": prod, "attribute": f"{prod}_id", "type": "BIGINT"}])


def test_move_fulfilled_when_in_target_absent_from_source(mtc_fn):
    """MOVE credited ONLY when product is in target domain AND absent from source."""
    products, attrs = _move_model("loyalty_program", "business")
    req = _Req("Move product loyalty_program from operations to business")
    res = mtc_fn(None, req, products, attrs)
    assert res and res["status"] == "fulfilled"


def test_move_not_credited_when_still_in_source(mtc_fn):
    """If the product ALSO still sits in the source domain (the travel duplicate-pair regression),
    MOVE is NOT credited -> None (no inflation)."""
    products = [
        {"domain": "operations", "product": "loyalty_program"},
        {"domain": "business", "product": "loyalty_program"},
    ]
    attrs = [{"domain": "business", "product": "loyalty_program", "attribute": "lp_id", "type": "BIGINT"}]
    req = _Req("Move product loyalty_program from operations to business")
    assert mtc_fn(None, req, products, attrs) is None


def test_type_fix_fulfilled(mtc_fn):
    products = [{"domain": "finance", "product": "invoice"}]
    attrs = [{"domain": "finance", "product": "invoice", "attribute": "total_amount", "type": "DECIMAL(18,2)"}]
    req = _Req("Fix finance.invoice.total_amount type, should be decimal not string")
    res = mtc_fn(None, req, products, attrs)
    assert res and res["status"] == "fulfilled"


def test_type_fix_not_credited_when_wrong(mtc_fn):
    products = [{"domain": "finance", "product": "invoice"}]
    attrs = [{"domain": "finance", "product": "invoice", "attribute": "total_amount", "type": "STRING"}]
    req = _Req("Fix finance.invoice.total_amount type, should be decimal not string")
    assert mtc_fn(None, req, products, attrs) is None


def test_count_fulfilled_at_threshold(mtc_fn):
    attrs = [{"domain": "ops", "product": "shipment", "attribute": f"c{i}", "type": "STRING"} for i in range(12)]
    products = [{"domain": "ops", "product": "shipment"}]
    req = _Req("Expand stub product ops.shipment to at least 10 attributes")
    res = mtc_fn(None, req, products, attrs)
    assert res and res["status"] == "fulfilled"


def test_count_not_credited_below_threshold(mtc_fn):
    attrs = [{"domain": "ops", "product": "shipment", "attribute": f"c{i}", "type": "STRING"} for i in range(4)]
    products = [{"domain": "ops", "product": "shipment"}]
    req = _Req("Expand stub product ops.shipment to at least 10 attributes")
    assert mtc_fn(None, req, products, attrs) is None


def test_count_uses_scope_targets_when_no_inline_fqn(mtc_fn):
    attrs = [{"domain": "ops", "product": "shipment", "attribute": f"c{i}", "type": "STRING"} for i in range(15)]
    products = [{"domain": "ops", "product": "shipment"}]
    req = _Req("Flesh out this thin skeleton table to >= 12 columns", scope_targets=["ops.shipment"])
    res = mtc_fn(None, req, products, attrs)
    assert res and res["status"] == "fulfilled"


def test_governance_vreq_returns_none(mtc_fn):
    """A non-move/type/count VReq must return None (no over-capture)."""
    products = [{"domain": "ops", "product": "shipment"}]
    attrs = [{"domain": "ops", "product": "shipment", "attribute": "s_id", "type": "BIGINT"}]
    req = _Req("Apply glossary tag to every attribute in ops.shipment")
    assert mtc_fn(None, req, products, attrs) is None
