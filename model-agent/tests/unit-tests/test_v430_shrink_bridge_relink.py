import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notebook_source_util import exec_function_namespace


def _load():
    ns = exec_function_namespace("_shrink_relink_or_drop_orphan_fks")
    return ns["_shrink_relink_or_drop_orphan_fks"]


def _old_orphan_drop(final_attributes, surviving_pk_set_lower):
    """Pre-v4.3.0 behaviour: drop EVERY survivor FK whose target product was
    removed, with no re-link. Reproduced here so the test proves the new helper
    changes observable state (density) vs the old code path (§8.10 fail-pre)."""
    kept = 0
    for a in final_attributes:
        fk = (a.get("foreign_key_to") or "").strip()
        if not fk or "." not in fk:
            continue
        key = ".".join(fk.split(".")[:2]).lower()
        if key in surviving_pk_set_lower:
            kept += 1
    return kept


def _survivor_fk_count(final_attributes, dropped_idx, surviving_pk_set_lower):
    n = 0
    for i, a in enumerate(final_attributes):
        if i in dropped_idx:
            continue
        fk = (a.get("foreign_key_to") or "").strip()
        if not fk or "." not in fk:
            continue
        if ".".join(fk.split(".")[:2]).lower() in surviving_pk_set_lower:
            n += 1
    return n


def test_bridge_relink_preserves_density_through_removed_junction():
    """Survivor A -> removed junction R -> survivor S. The old code dropped A's FK
    (A->R target removed) leaving 0 survivor edges. The fix collapses the junction:
    A is re-pointed to S, so the real relationship survives and density is preserved."""
    fn = _load()
    surviving = {"sales.a", "ops.s"}  # A and S survive; R (junction) removed
    # final_attributes only carries SURVIVOR products' attributes (R's rows are gone)
    final_attributes = [
        {"domain": "sales", "product": "a", "attribute": "a_id", "foreign_key_to": ""},
        {"domain": "sales", "product": "a", "attribute": "r_id", "foreign_key_to": "junction.r.r_id"},
        {"domain": "ops", "product": "s", "attribute": "s_id", "foreign_key_to": ""},
    ]
    # full ECM includes the removed junction R which itself referenced surviving S
    source_attributes = final_attributes + [
        {"domain": "junction", "product": "r", "attribute": "r_id", "foreign_key_to": ""},
        {"domain": "junction", "product": "r", "attribute": "s_id", "foreign_key_to": "ops.s.s_id"},
    ]

    # FAIL-PRE: the old drop-all path leaves ZERO survivor edges.
    assert _old_orphan_drop(final_attributes, surviving) == 0

    res = fn(final_attributes, source_attributes, surviving, "_id")

    # PASS-POST: the FK is re-pointed, not dropped.
    assert res["relinked"] == 1
    assert res["dropped_idx"] == set()
    relinked_attr = next(a for a in final_attributes if a["product"] == "a" and a["attribute"] != "a_id")
    assert relinked_attr["foreign_key_to"] == "ops.s.s_id"
    assert relinked_attr["attribute"] == "s_id"  # renamed to the bridge target's fk column
    assert _survivor_fk_count(final_attributes, res["dropped_idx"], surviving) == 1


def test_drop_when_removed_product_has_no_surviving_bridge():
    """Survivor A2 -> removed leaf R2 (R2 references nothing surviving). No bridge
    exists, so the FK is dropped exactly as before (no fabricated edge)."""
    fn = _load()
    surviving = {"sales.a2"}
    final_attributes = [
        {"domain": "sales", "product": "a2", "attribute": "a2_id", "foreign_key_to": ""},
        {"domain": "sales", "product": "a2", "attribute": "r2_id", "foreign_key_to": "gone.r2.r2_id"},
    ]
    source_attributes = final_attributes + [
        {"domain": "gone", "product": "r2", "attribute": "r2_id", "foreign_key_to": ""},
    ]
    res = fn(final_attributes, source_attributes, surviving, "_id")
    assert res["relinked"] == 0
    assert res["dropped_idx"] == {1}


def test_no_duplicate_edge_created():
    """If A already links to S, re-linking A->R->S would duplicate the edge; the
    orphan FK is dropped instead of creating a parallel FK."""
    fn = _load()
    surviving = {"sales.a", "ops.s"}
    final_attributes = [
        {"domain": "sales", "product": "a", "attribute": "s_id", "foreign_key_to": "ops.s.s_id"},
        {"domain": "sales", "product": "a", "attribute": "r_id", "foreign_key_to": "junction.r.r_id"},
    ]
    source_attributes = final_attributes + [
        {"domain": "junction", "product": "r", "attribute": "s_id", "foreign_key_to": "ops.s.s_id"},
    ]
    res = fn(final_attributes, source_attributes, surviving, "_id")
    assert res["relinked"] == 0
    assert res["dropped_idx"] == {1}


def test_no_bidirectional_link_created():
    """If S already links to A, re-linking A->S would create a bidirectional pair;
    the orphan FK is dropped instead."""
    fn = _load()
    surviving = {"sales.a", "ops.s"}
    final_attributes = [
        {"domain": "sales", "product": "a", "attribute": "r_id", "foreign_key_to": "junction.r.r_id"},
        {"domain": "ops", "product": "s", "attribute": "a_id", "foreign_key_to": "sales.a.a_id"},
    ]
    source_attributes = final_attributes + [
        {"domain": "junction", "product": "r", "attribute": "s_id", "foreign_key_to": "ops.s.s_id"},
    ]
    res = fn(final_attributes, source_attributes, surviving, "_id")
    assert res["relinked"] == 0
    assert res["dropped_idx"] == {0}


def test_surviving_fk_untouched():
    """An FK whose target already survives must be left completely alone."""
    fn = _load()
    surviving = {"sales.a", "ops.s"}
    final_attributes = [
        {"domain": "sales", "product": "a", "attribute": "s_id", "foreign_key_to": "ops.s.s_id"},
    ]
    res = fn(final_attributes, list(final_attributes), surviving, "_id")
    assert res["relinked"] == 0
    assert res["dropped_idx"] == set()
    assert final_attributes[0]["foreign_key_to"] == "ops.s.s_id"
