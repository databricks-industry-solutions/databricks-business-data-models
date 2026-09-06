"""v4.4.8 behavioral tests (fail-pre / pass-post, CLAUDE.md 8.10) for the 4 consolidated fixes:

  GAP-5  verifier-product-create-coverage  — authoritative deterministic verdict for generative
                                             add_product VREQs (a matching column/measure/flag is
                                             NEVER fulfillment; only an exact product-NAME match is).
  G7     v443-silo-inbound-relink          — wire INBOUND FKs from transactional tables into an
                                             isolated hierarchical/geographic reference dimension
                                             (self-FK is excluded from connectivity).
  Iss4   mv-boolean-agg-cast               — CAST a boolean aggregate argument to INT so the metric
                                             view builds (SUM(is_in_stock) / AVG(a <= b)).
  Iss6   selffixer-none-finding-guard      — drop None / non-dict / id-less queued reqs before the
                                             SelfFixer index comprehension crashes on None.get().

Pre-patch anchor is pinned to b1b5c35 (v4.4.7 HEAD, before these 4 fixes) so fail-pre is not a moving
target and cannot become tautological once v4.4.8 is committed.
"""
import json
import os
import re
import logging
import subprocess

import pytest

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
NB = os.path.join(REPO, "agent", "dbx_vibe_modelling_agent.ipynb")
_PREPATCH_SHA = "b1b5c35"  # v4.4.7 HEAD — none of the 4 fixes exist here
LOG = logging.getLogger("v448_test")


# ---------------- notebook cell loaders ----------------

def _nb(text=None):
    if text is None:
        with open(NB) as f:
            return json.load(f)
    return json.loads(text)


def _cell_src(nb, idx):
    c = nb["cells"][idx]
    return "".join(c["source"]) if isinstance(c["source"], list) else c["source"]


def _find_cell(nb, needle):
    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        if needle in _cell_src(nb, i):
            return i
    raise RuntimeError("cell not found: " + needle)


def _load_cell_ns(nb, needle):
    """Exec the whole cell containing `needle` (magics stripped) and return its namespace.
    Seed the namespace with the stdlib names notebook cells assume are already imported."""
    import collections
    import json as _json
    import math
    import copy
    import itertools
    import functools
    import datetime
    idx = _find_cell(nb, needle)
    src = "\n".join(l for l in _cell_src(nb, idx).splitlines()
                    if not l.strip().startswith(("%", "!", "display(")))
    ns = {
        "re": re, "json": _json, "math": math, "copy": copy, "itertools": itertools,
        "functools": functools, "datetime": datetime, "collections": collections,
        "defaultdict": collections.defaultdict, "OrderedDict": collections.OrderedDict,
        "Counter": collections.Counter, "logging": logging, "os": os,
    }
    exec(src, ns)
    return ns


def _prepatch_nb():
    txt = subprocess.check_output(
        ["git", "show", f"{_PREPATCH_SHA}:agent/dbx_vibe_modelling_agent.ipynb"], cwd=REPO).decode()
    return _nb(txt)


# ============================================================
# GAP-5 — verifier-product-create-coverage
# ============================================================

class _Req:
    def __init__(self, text, scope="", scope_targets=(), rid="VREQ-005"):
        self.original_text = text
        self.scope = scope
        self.scope_targets = list(scope_targets)
        self.id = rid


class _FakeSelf:
    logger = LOG


def _verifier(nb):
    """Slice the self-contained _verify_product_create_coverage method out of the VibeOrchestrator cell
    and exec it as a standalone function (it uses only `re` + self.logger). Returns None if absent
    (pre-patch), so fail-pre is non-tautological."""
    idx = next((i for i, c in enumerate(nb["cells"])
                if c.get("cell_type") == "code"
                and "def _verify_product_create_coverage" in _cell_src(nb, i)), None)
    if idx is None:
        return None
    lines = _cell_src(nb, idx).split("\n")
    start = next((i for i, l in enumerate(lines)
                  if l.strip().startswith("def _verify_product_create_coverage")), None)
    if start is None:
        return None
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip().startswith("def ")
                and (len(lines[i]) - len(lines[i].lstrip())) == indent), len(lines))
    body = "\n".join(l[indent:] if len(l) >= indent else l for l in lines[start:end])
    ns = {"re": re}
    # GAP-5 v4.4.9: the verifier now delegates create-target parsing to the shared
    # _vov_named_create_targets helper (CLAUDE.md 3d DRY) — inject it into the slice namespace.
    pidx = next((i for i, c in enumerate(nb["cells"])
                 if c.get("cell_type") == "code"
                 and "def _vov_named_create_targets" in _cell_src(nb, i)), None)
    if pidx is not None:
        plines = _cell_src(nb, pidx).split("\n")
        pstart = next((i for i, l in enumerate(plines)
                       if l.strip().startswith("def _vov_named_create_targets")), None)
        if pstart is not None:
            pindent = len(plines[pstart]) - len(plines[pstart].lstrip())
            pend = next((i for i in range(pstart + 1, len(plines))
                         if plines[i].strip().startswith(("def ", "class "))
                         and (len(plines[i]) - len(plines[i].lstrip())) == pindent), len(plines))
            pbody = "\n".join(l[pindent:] if len(l) >= pindent else l for l in plines[pstart:pend])
            exec(pbody, ns)
    exec(body, ns)
    return ns["_verify_product_create_coverage"]


_CREATE_REQ = _Req(
    "add_product: logistics.transhipment — model transhipment as a first-class product",
    scope="", scope_targets=["logistics.transhipment"])
# products with only a matching MEASURE/column token (transhipment_teu), NO transhipment PRODUCT
_PD_MISS = [{"domain": "logistics", "product": "container_move",
             "attributes": [{"name": "transhipment_teu"}, {"name": "vessel_id"}]}]
_PD_HIT = [{"domain": "logistics", "product": "transhipment", "attributes": []}]


def test_gap5_column_match_is_not_fulfillment_post():
    fn = _verifier(_nb())
    assert fn is not None, "v4.4.8 must add _verify_product_create_coverage"
    v = fn(_FakeSelf(), _CREATE_REQ, _PD_MISS)
    assert v and v["status"] == "failed", \
        "add_product must be FAILED when only a matching column/measure exists (not the product)"


def test_gap5_exact_product_is_fulfilled_post():
    fn = _verifier(_nb())
    v = fn(_FakeSelf(), _CREATE_REQ, _PD_HIT)
    assert v and v["status"] == "fulfilled", "add_product FULFILLED only when the exact product exists"


def test_gap5_non_create_falls_through_post():
    fn = _verifier(_nb())
    r = _Req("add a column foo to bar.baz", scope="", scope_targets=[])
    assert fn(_FakeSelf(), r, _PD_MISS) is None, "non-create VREQ must fall through (return None)"


def test_gap5_absent_on_prepatch():
    # v4.4.7 has no authoritative product-create verifier — the LLM fallback false-fulfilled these.
    assert _verifier(_prepatch_nb()) is None, \
        "PRE-PATCH SANITY: v4.4.7 must NOT have _verify_product_create_coverage (else tautology)"


# ============================================================
# G7 — v443-silo-inbound-relink
# ============================================================

def _make_silo_model():
    # geo.market is a hierarchical reference dim: ONLY a self-FK parent pointer, zero cross-table links.
    # sales.order is transactional and has an UNLINKED market_id column that should point at geo.market.
    return {"domains": [
        {"name": "geo", "data_products": [
            {"name": "market", "primary_key": "market_id", "attributes": [
                {"name": "market_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "parent_market_id", "type": "BIGINT", "foreign_key_to": "geo.market.market_id"},
                {"name": "market_name", "type": "STRING"}]}]},
        {"name": "sales", "data_products": [
            {"name": "order", "primary_key": "order_id", "attributes": [
                {"name": "order_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "market_id", "type": "BIGINT"},
                {"name": "amount", "type": "DECIMAL(18,2)"},
                {"name": "customer_id", "type": "BIGINT", "foreign_key_to": "cust.customer.customer_id"}]}]},
        {"name": "cust", "data_products": [
            {"name": "customer", "primary_key": "customer_id", "attributes": [
                {"name": "customer_id", "type": "BIGINT", "is_primary_key": True}]}]},
    ]}


def _order_market_fk(m):
    for d in m["domains"]:
        if d["name"] == "sales":
            for p in d["data_products"]:
                if p["name"] == "order":
                    for a in p["attributes"]:
                        if a["name"] == "market_id":
                            return a.get("foreign_key_to")
    return None


def _run_v443(nb, model):
    fn = _load_cell_ns(nb, "def _v443_structural_hardening")["_v443_structural_hardening"]
    fn(model, LOG)
    return model


def test_g7_inbound_relink_post():
    m = _run_v443(_nb(), _make_silo_model())
    assert _order_market_fk(m) == "geo.market.market_id", \
        "v4.4.8 must wire the INBOUND FK sales.order.market_id -> geo.market.market_id"


def test_g7_inbound_relink_absent_on_prepatch():
    m = _run_v443(_prepatch_nb(), _make_silo_model())
    assert _order_market_fk(m) is None, \
        "PRE-PATCH SANITY: v4.4.7 counts the self-FK as connectivity so it never relinks (else tautology)"


# ============================================================
# Issue 4 — mv-boolean-agg-cast
# ============================================================

def _sanitizer(nb):
    return _load_cell_ns(nb, "def _sanitize_metric_measure_expr")["_sanitize_metric_measure_expr"]


def test_iss4_boolean_column_cast_post():
    out = _sanitizer(_nb())("SUM(is_in_stock)")
    assert "CAST(is_in_stock AS INT)" in out, "SUM over a boolean-named column must be CAST to INT"


def test_iss4_comparison_cast_post():
    out = _sanitizer(_nb())("AVG(quantity_on_hand <= reorder_point)")
    assert "CAST(quantity_on_hand <= reorder_point AS INT)" in out, "AVG over a comparison must CAST to INT"


def test_iss4_numeric_untouched_post():
    out = _sanitizer(_nb())("SUM(revenue)")
    assert "AS INT" not in out.upper(), "a numeric aggregate arg must NOT be cast to INT by this pass"


def test_iss4_boolean_cast_absent_on_prepatch():
    out = _sanitizer(_prepatch_nb())("SUM(is_in_stock)")
    assert "CAST(is_in_stock AS INT)" not in out, \
        "PRE-PATCH SANITY: v4.4.7 leaves SUM(is_in_stock) uncast -> boolean build failure (else tautology)"


# ============================================================
# Issue 6 — selffixer-none-finding-guard
# ============================================================

class _StubFixer:
    """Reproduces the real crash mechanism: the per-req index comprehension does r.get('id') for every
    queued req, which raises AttributeError on a None finding."""
    def __init__(self, **kw):
        pass

    def fix_all_unfulfilled(self, model_dict, unfulfilled_reqs, **kw):
        index = {r.get("id"): r for r in unfulfilled_reqs}  # crashes on None pre-guard
        return {"skipped": False, "fixed_count": len(index), "remaining_count": 0, "rounds": 1}


def _run_selffixer(nb, queued):
    ns = _load_cell_ns(nb, "def run_selffixer_or_skip")
    ns["SelfFixer"] = _StubFixer  # inject the crash-reproducing stub
    return ns["run_selffixer_or_skip"]({}, {"_unfulfilled_for_next_vibe": queued}, None, LOG)


def test_iss6_none_finding_no_crash_post():
    r = _run_selffixer(_nb(), [None, {"id": "r1"}, "notadict", {"id": ""}])
    assert not r.get("error"), "v4.4.8 guard must drop None/invalid reqs so no NoneType crash occurs"
    assert r.get("skipped") is False and r.get("fixed_count") == 1, \
        "the one valid req must still reach the fixer"


def test_iss6_none_finding_crashes_on_prepatch():
    r = _run_selffixer(_prepatch_nb(), [None, {"id": "r1"}])
    # v4.4.7 has no guard: None reaches fix_all_unfulfilled -> AttributeError -> graceful-skip error dict.
    assert "NoneType" in str(r.get("error", "")), \
        "PRE-PATCH SANITY: v4.4.7 must crash on the None finding (else tautology)"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
