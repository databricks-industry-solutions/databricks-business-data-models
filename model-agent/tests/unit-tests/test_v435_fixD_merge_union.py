"""v4.3.5 FIX D behavioral test (alias=vov-merge-union-creates).

Root cause: _merge_partial is a SCOPED merge that only REPLACES products already named in
target_entities. A product the batch CREATED (split child) or MOVED cross-domain is absent
from target_entities (it did not exist at plan time), so the scoped merge silently DROPPED it
-> split/move directives never landed. FIX D unions candidate products missing from the
post-merge base and relocates cross-domain moves (mirroring the metric_view union already in
the function).

Fail-pre / pass-post: pre-patch the split child is dropped and the moved product stays under
its old domain -> the presence/relocation assertions raise. Post-patch the child is unioned in
and the moved product is relocated.
"""
import copy as _copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v435_helpers import concat_source, slice_functions


def _fn():
    src = concat_source()
    ns = slice_functions(["_merge_partial"], src, extra_globals={"copy": _copy})
    return ns["_merge_partial"]


def _base():
    return {"model": {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "profile_id",
             "attributes": [{"name": "profile_id", "type": "BIGINT"}]},
            {"name": "loyalty_card", "primary_key": "loyalty_card_id",
             "attributes": [{"name": "loyalty_card_id", "type": "BIGINT"}]},
        ]},
        {"name": "loyalty", "products": [
            {"name": "tier", "primary_key": "tier_id",
             "attributes": [{"name": "tier_id", "type": "BIGINT"}]},
        ]},
    ]}}


def _candidate():
    # A batch that split profile (created profile_preferences under customer) AND moved
    # loyalty_card into the loyalty domain.
    return {"model": {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "profile_id",
             "attributes": [{"name": "profile_id", "type": "BIGINT"}]},
            {"name": "profile_preferences", "primary_key": "profile_id",
             "attributes": [{"name": "profile_id", "type": "BIGINT"},
                            {"name": "pref_key", "type": "STRING"}]},
        ]},
        {"name": "loyalty", "products": [
            {"name": "tier", "primary_key": "tier_id",
             "attributes": [{"name": "tier_id", "type": "BIGINT"}]},
            {"name": "loyalty_card", "primary_key": "loyalty_card_id",
             "attributes": [{"name": "loyalty_card_id", "type": "BIGINT"}]},
        ]},
    ]}}


def _products(model, domain):
    for d in model["model"]["domains"]:
        if d["name"] == domain:
            return {p["name"] for p in d["products"]}
    return set()


def test_fixD_unions_created_child_and_relocates_moved_product():
    fn = _fn()
    # scope names ONLY customer.profile (the split source); the created child and the moved
    # product are out of scope, so the pre-patch scoped merge would drop them.
    out = fn(_base(), _candidate(), (("customer", "profile"),))
    cust = _products(out, "customer")
    loy = _products(out, "loyalty")
    assert "profile_preferences" in cust, "split child dropped (FIX D union missing)"
    assert "loyalty_card" in loy, "moved product not relocated to new domain"
    assert "loyalty_card" not in cust, "moved product left a stale copy (SSOT duplicate)"
