"""v4.5.3 behavioral tests for the identical cross-domain reference SSOT collapse
(alias=v453-identical-ref-ssot-collapse).

ROOT CAUSE (fail-pre): the early flat `_v291_ssot_cross_domain_merge` (cell 168) runs ONCE
pre-VOV-synthesis and, by design, marks <3-business-attr thin lookup tables
"legitimately-distinct" (cannot confirm same-entity on thin overlap). VOV then synthesized
3 byte-identical `imdg_class_type` lookups (id+code+description) as FK targets for
dangerous-goods directives AFTER that pass, so they were never re-checked. The shipping
v4.5.2 ECM shipped `imdg_class_type` in cargo, intermodal, terminal -> G8 (no cross-domain
dup name) FAILED, 11/12 gates.

FIX (pass-post): at the AUTHORITATIVE serialization boundary (same true-last spot as
_v452/_v403), collapse cross-domain products that share the EXACT product name AND an
identical attribute-name set into one canonical keeper, repointing every FK that targeted a
dropped copy. Skips protected instances; leaves different-schema groups alone.

- test_v453_call_ordered_before_cycle_guard   -> static fail-pre/pass-post anchor.
- test_v453_collapses_identical_cross_domain_ref -> behavioral: 3 identical copies -> 1,
  FKs repointed, only the keeper survives.
- test_v453_leaves_different_schema_alone       -> negative: different columns => no merge.
- test_v453_skips_protected                     -> negative: a protected instance => no merge.
"""
import json
from collections import defaultdict
from pathlib import Path

import pytest

from v435_helpers import concat_source, slice_functions, NOTEBOOK_PATH

_SRC = concat_source()


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


def _guard():
    ns = slice_functions(
        ["_v453_collapse_identical_cross_domain_refs"],
        _SRC,
        extra_globals={"defaultdict": defaultdict},
    )
    return ns["_v453_collapse_identical_cross_domain_refs"]


class _Log:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


def test_v453_call_ordered_before_cycle_guard():
    """FAIL-PRE on HEAD (alias absent); PASS-POST (v453 call ordered BEFORE the v452 cycle guard)."""
    src = _cell188_source()
    assert "v453-identical-ref-ssot-collapse call-site" in src, (
        "v4.5.3 SSOT-collapse call-site missing from the model-json serialization cell (pre-patch state)"
    )
    lines = src.split("\n")
    v453_idx = next(i for i, l in enumerate(lines) if "_v453_collapse_identical_cross_domain_refs(data_model, logger)" in l)
    v452_idx = next(i for i, l in enumerate(lines) if "v452-post-finalize-cycle-guard FIRED" in l)
    assert v453_idx < v452_idx, (
        "the SSOT collapse must run BEFORE the cycle guard so the guard sees the deduped graph "
        f"(collapse@{v453_idx}, guard@{v452_idx})"
    )


def _lookup(name, dom):
    return {
        "name": name,
        "primary_key": name + "_id",
        "attributes": [
            {"name": name + "_id", "type": "BIGINT", "is_primary_key": True},
            {"name": "code", "type": "STRING"},
            {"name": "description", "type": "STRING"},
        ],
    }


def _txn(name, fk_col, fk_target):
    return {
        "name": name,
        "primary_key": name + "_id",
        "attributes": [
            {"name": name + "_id", "type": "BIGINT", "is_primary_key": True},
            {"name": fk_col, "type": "BIGINT", "foreign_key_to": fk_target},
        ],
    }


def _imdg_model():
    """Reproduce the exact shipping v4.5.2 shape: imdg_class_type byte-identical in 3 domains."""
    return {
        "domains": [
            {"name": "cargo", "products": [
                _lookup("imdg_class_type", "cargo"),
                _txn("shipment", "imdg_class", "cargo.imdg_class_type.imdg_class_type_id"),
                _txn("dangerous_goods_declaration", "imdg_class", "cargo.imdg_class_type.imdg_class_type_id"),
            ]},
            {"name": "terminal", "products": [
                _lookup("imdg_class_type", "terminal"),
                _txn("equipment_dispatch", "imdg_class", "terminal.imdg_class_type.imdg_class_type_id"),
                _txn("hazmat_declaration", "imdg_class", "terminal.imdg_class_type.imdg_class_type_id"),
            ]},
            {"name": "intermodal", "products": [
                _lookup("imdg_class_type", "intermodal"),
                _txn("intermodal_rail_wagon_load", "imdg_class", "intermodal.imdg_class_type.imdg_class_type_id"),
            ]},
        ]
    }


def _copies(dm, name):
    return [(d["name"], p) for d in dm["domains"] for p in d["products"] if p["name"] == name]


def test_v453_collapses_identical_cross_domain_ref():
    guard = _guard()
    dm = _imdg_model()
    assert len(_copies(dm, "imdg_class_type")) == 3, "fixture must start with 3 copies"

    dropped, repointed = guard(dm, _Log())
    assert dropped == 2, f"must drop 2 of the 3 identical copies, dropped={dropped}"
    assert repointed >= 3, f"must repoint the FKs of the dropped-domain txns, repointed={repointed}"

    survivors = _copies(dm, "imdg_class_type")
    assert len(survivors) == 1, f"exactly one canonical keeper must survive, got {len(survivors)}"
    keep_dn = survivors[0][0]
    # cargo has most inbound (2) tying terminal (2); alphabetical tiebreak => cargo
    assert keep_dn == "cargo", f"deterministic keeper should be 'cargo', got {keep_dn}"

    # every imdg FK now points at the single keeper domain
    targets = set()
    for d in dm["domains"]:
        for p in d["products"]:
            for a in p["attributes"]:
                fk = a.get("foreign_key_to") or ""
                if "imdg_class_type" in fk:
                    targets.add(fk.split(".")[0])
    assert targets == {"cargo"}, f"all imdg FKs must repoint to the keeper domain, got {targets}"


def test_v453_leaves_different_schema_alone():
    guard = _guard()
    dm = {
        "domains": [
            {"name": "cargo", "products": [{
                "name": "status_code", "attributes": [
                    {"name": "status_code_id"}, {"name": "code"}, {"name": "label"}]}]},
            {"name": "terminal", "products": [{
                "name": "status_code", "attributes": [
                    {"name": "status_code_id"}, {"name": "code"}, {"name": "severity"}]}]},
        ]
    }
    dropped, _ = guard(dm, _Log())
    assert dropped == 0, "different attribute sets must NOT be merged"
    assert len(_copies(dm, "status_code")) == 2


def test_v453_skips_protected():
    guard = _guard()
    dm = _imdg_model()
    # mark one instance reviewer-protected -> whole group must be skipped
    dm["domains"][1]["products"][0]["_reviewer_named"] = True
    dropped, _ = guard(dm, _Log())
    assert dropped == 0, "a protected instance must veto the whole-group collapse"
    assert len(_copies(dm, "imdg_class_type")) == 3


def test_v453_idempotent_on_clean_model():
    guard = _guard()
    dm = {"domains": [{"name": "cargo", "products": [_lookup("imdg_class_type", "cargo")]}]}
    dropped, repointed = guard(dm, _Log())
    assert (dropped, repointed) == (0, 0), "single-domain model must be a no-op"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
