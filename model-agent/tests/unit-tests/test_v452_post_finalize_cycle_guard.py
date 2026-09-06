"""v4.5.2 behavioral tests for the post-finalize cycle guard (alias=v452-post-finalize-cycle-guard).

ROOT CAUSE (fail-pre): the reviewer finalizer `_v441_reviewer_finalization` materializes
reviewer-named products and stubs their FK columns at the model-json serialization cell, AFTER the `_v403`
serialize cycle guard runs at line ~517. Two sibling products created by one reviewer
directive each received an FK to the other (A.b_id->B and B.a_id->A), shipping a 2-cycle /
bidirectional pair that failed G4 (no FK cycles) and G6 (no bidirectional FK). The shipping
v4.5.0 ECM shipped exactly 3 such pairs (transhipment<->transhipment_leg,
container_condition_report<->container_depot, dg_positioning_constraint<->dg_segregation_rule).

FIX (pass-post): re-run the SAME deterministic guard at the TRUE-last mutator boundary
(after finalize + structural hardening, immediately before serialization). DRY reuse of
_v403; no second breaker; idempotent no-op on a clean model.

- test_v452_guard_alias_ordered_after_finalizer  -> static fail-pre/pass-post anchor
  (alias absent on pre-patch HEAD; present AND after the finalizer call post-patch).
- test_v452_guard_clears_mutual_fk_2cycles        -> behavioral: the guard, run on the exact
  shipped-shape nested model, mutates 3 mutual-FK 2-cycles down to 0 residual cycles.
"""
import ast
import json
import re
import itertools
from collections import defaultdict, Counter, OrderedDict
from pathlib import Path

import pytest

from v435_helpers import concat_source, slice_functions, NOTEBOOK_PATH

_SRC = concat_source()


def _module_consts(names, source=_SRC):
    """Exec module-level constant assignments (tuples/lists/sets) by name, faithful to source."""
    tree = ast.parse(source)
    out = {}
    wanted = set(names)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in wanted:
                    seg = ast.get_source_segment(source, node)
                    ns = {}
                    exec(compile(seg, "<const>", "exec"), ns)
                    out[tgt.id] = ns[tgt.id]
    return out


def _cell188_source():
    nb = json.loads(Path(NOTEBOOK_PATH).read_text(encoding="utf-8"))
    for c in nb["cells"]:
        if c.get("cell_type") != "code":
            continue
        s = c["source"]
        s = "".join(s) if isinstance(s, list) else s
        if "def step_generate_data_model_json(" in s:
            return s
    raise AssertionError("step_generate_data_model_json cell not found")


def test_v452_guard_alias_ordered_after_finalizer():
    """FAIL-PRE on HEAD (alias absent); PASS-POST (guard call ordered after the finalizer)."""
    src = _cell188_source()
    assert "v452-post-finalize-cycle-guard FIRED" in src, (
        "v4.5.2 post-finalize guard alias missing from the model-json serialization cell (pre-patch state)"
    )
    lines = src.split("\n")
    fin_idx = next(i for i, l in enumerate(lines) if "_v441_reviewer_finalization(data_model" in l)
    grd_idx = next(i for i, l in enumerate(lines) if "v452-post-finalize-cycle-guard FIRED" in l)
    assert grd_idx > fin_idx, (
        "the post-finalize cycle guard must be invoked AFTER _v441_reviewer_finalization "
        f"(finalizer@{fin_idx}, guard@{grd_idx})"
    )
    # the guard call itself (not just the log line) must be present after the finalizer
    call_idx = next(
        i for i, l in enumerate(lines)
        if "_v403_break_cycles_in_serialized_model(data_model, logger)" in l and i > fin_idx
    )
    assert call_idx > fin_idx


def _shipped_shape_model():
    """Nested data_model reproducing the exact 3 mutual-FK pairs the v4.5.0 shipping ECM shipped."""
    def prod(name, fk_col, fk_target):
        return {
            "name": name,
            "primary_key": name + "_id",
            "attributes": [
                {"name": name + "_id", "type": "BIGINT", "is_primary_key": True, "tags": "primary_key"},
                {"name": fk_col, "type": "BIGINT", "foreign_key_to": fk_target, "tags": "foreign_key"},
            ],
        }

    return {
        "domains": [
            {
                "name": "cargo",
                "products": [
                    prod("transhipment", "transhipment_leg_id", "cargo.transhipment_leg.transhipment_leg_id"),
                    prod("transhipment_leg", "transhipment_id", "cargo.transhipment.transhipment_id"),
                    prod("container_condition_report", "container_depot_id", "cargo.container_depot.container_depot_id"),
                    prod("container_depot", "container_condition_report_id", "cargo.container_condition_report.container_condition_report_id"),
                    prod("dg_positioning_constraint", "dg_segregation_rule_id", "cargo.dg_segregation_rule.dg_segregation_rule_id"),
                    prod("dg_segregation_rule", "dg_positioning_constraint_id", "cargo.dg_positioning_constraint.dg_positioning_constraint_id"),
                ],
            }
        ]
    }


class _Log:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


def test_v452_guard_clears_mutual_fk_2cycles():
    """Behavioral: the production guard mutates the shipped 3 mutual-FK 2-cycles down to 0."""
    ns = slice_functions(
        ["_is_convenience_fk", "_heuristic_edge_break_score", "_compute_edge_betweenness_for_cycles",
         "_detect_direct_bidirectional_links", "_detect_cycles_dfs", "_break_cycles_heuristic_internal",
         "_v403_break_cycles_in_serialized_model"],
        _SRC,
        extra_globals={"defaultdict": defaultdict, "Counter": Counter, "OrderedDict": OrderedDict,
                       "re": re, "json": json, "itertools": itertools,
                       **_module_consts(["_CONVENIENCE_FK_PREFIXES"])},
    )
    detect = ns["_detect_cycles_dfs"]
    guard = ns["_v403_break_cycles_in_serialized_model"]
    log = _Log()

    dm = _shipped_shape_model()

    def flatten(model):
        pd, ad = [], []
        for d in model["domains"]:
            for p in d["products"]:
                pd.append({"domain": d["name"], "product": p["name"]})
                for a in p["attributes"]:
                    ad.append({"domain": d["name"], "product": p["name"], "attribute": a["name"],
                               "name": a["name"], "tags": a.get("tags", ""),
                               "foreign_key_to": a.get("foreign_key_to") or ""})
        return pd, ad

    pd, ad = flatten(dm)
    before = detect(pd, ad, log)
    assert len(before) >= 3, f"fixture must contain the 3 shipped 2-cycles, found {len(before)}"

    cleared = guard(dm, log)
    assert cleared >= 3, f"guard should clear >=3 FK edges, cleared={cleared}"

    pd2, ad2 = flatten(dm)
    after = detect(pd2, ad2, log)
    assert len(after) == 0, f"guard must eliminate all cycles at the boundary, remaining={after}"

    # each pair now carries at most one surviving FK direction (bidirectional gone)
    fk_by_prod = {}
    for d in dm["domains"]:
        for p in d["products"]:
            fk_by_prod[p["name"]] = [a for a in p["attributes"] if (a.get("foreign_key_to") or "")]
    for a, b in [("transhipment", "transhipment_leg"),
                 ("container_condition_report", "container_depot"),
                 ("dg_positioning_constraint", "dg_segregation_rule")]:
        assert not (fk_by_prod[a] and fk_by_prod[b]), (
            f"mutual FK between {a} and {b} still present after guard"
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
