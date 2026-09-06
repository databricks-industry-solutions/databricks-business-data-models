"""v4.5.4 behavioral tests for the duplicate-named-domain merge
(alias=v454-duplicate-domain-merge).

ROOT CAUSE (fail-pre): the automotive vov_v2 run 231173708245804 (v4.5.2) serialized the
'aftersales' domain TWICE in model.json: one entry with the real description + one stub
("The aftersales domain."), BOTH carrying the SAME 35 products. gates12 keys tables by
(domain, product) so the identical copies collapse invisibly -> G8/G1..G12 all PASS while
the harvested model.json is not production-clean. The physical build deduped to 1 schema,
so this is a model.json-only serialization defect.

FIX (pass-post): at the AUTHORITATIVE serialization boundary (same true-last spot as
_v452/_v403/_v453), merge domain dicts sharing a name into one canonical keeper (prefer a
non-stub description, else most products), union their products by product-name, drop the
extras. Runs BEFORE the product-level v453 collapse and the cycle guard.

- test_v454_call_ordered_before_v453_and_guard -> static fail-pre/pass-post anchor + order.
- test_v454_merges_duplicate_domain            -> behavioral: 2 aftersales -> 1, products unioned.
- test_v454_keeps_richer_description            -> keeper adopts the non-stub description.
- test_v454_unions_distinct_products            -> extra's unique products survive on the keeper.
- test_v454_idempotent_on_unique_domains        -> unique-named model must be a no-op.
"""
import json
from collections import OrderedDict
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


def _merge():
    ns = slice_functions(
        ["_v454_merge_duplicate_named_domains"],
        _SRC,
        extra_globals={"OrderedDict": OrderedDict},
    )
    return ns["_v454_merge_duplicate_named_domains"]


class _Log:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


def test_v454_call_ordered_before_v453_and_guard():
    src = _cell188_source()
    assert "v454-duplicate-domain-merge call-site" in src, (
        "v4.5.4 domain-merge call-site missing from the model-json serialization cell (pre-patch state)"
    )
    i454 = src.find("_v454_merge_duplicate_named_domains(data_model, logger)")
    i453 = src.find("_v453_collapse_identical_cross_domain_refs(data_model, logger)")
    i452 = src.find("v452-post-finalize-cycle-guard FIRED")
    assert 0 <= i454 < i453 < i452, (
        f"domain merge must run before product collapse before cycle guard "
        f"(v454@{i454}, v453@{i453}, guard@{i452})"
    )


def _prod(name):
    return {"name": name, "primary_key": name + "_id",
            "attributes": [{"name": name + "_id", "type": "BIGINT", "is_primary_key": True}]}


def _auto_dup_model():
    """Reproduce the automotive v4.5.2 shape: aftersales twice, one real desc + one stub, same products."""
    prods = [_prod("service_order"), _prod("warranty_claim"), _prod("parts_inventory")]
    return {"domains": [
        {"name": "customer", "description": "Customer master and accounts.", "products": [_prod("account")]},
        {"name": "aftersales", "description": "Aftersales service, warranty and parts operations across the dealer network.",
         "products": [dict(p) for p in prods]},
        {"name": "vehicle", "description": "Vehicle catalog and configuration.", "products": [_prod("model_variant")]},
        {"name": "aftersales", "description": "The aftersales domain.",
         "products": [dict(p) for p in prods]},
    ]}


def _dnames(dm):
    return [d["name"] for d in dm["domains"]]


def test_v454_merges_duplicate_domain():
    merge = _merge()
    dm = _auto_dup_model()
    assert _dnames(dm).count("aftersales") == 2, "fixture must start with 2 aftersales"
    merged = merge(dm, _Log())
    assert merged == 1, f"exactly one extra aftersales must be merged, merged={merged}"
    assert _dnames(dm).count("aftersales") == 1, "only one aftersales domain may survive"
    assert len(dm["domains"]) == 3, f"customer+aftersales+vehicle => 3 domains, got {len(dm['domains'])}"


def test_v454_keeps_richer_description():
    merge = _merge()
    dm = _auto_dup_model()
    merge(dm, _Log())
    after = next(d for d in dm["domains"] if d["name"] == "aftersales")
    assert after["description"] != "The aftersales domain.", "keeper must not carry the stub description"
    assert "warranty" in after["description"].lower(), "keeper must keep the rich description"


def test_v454_unions_distinct_products():
    merge = _merge()
    dm = _auto_dup_model()
    # give the stub duplicate one product the keeper lacks
    dm["domains"][3]["products"].append(_prod("recall_campaign"))
    merge(dm, _Log())
    after = next(d for d in dm["domains"] if d["name"] == "aftersales")
    names = {p["name"] for p in after["products"]}
    assert "recall_campaign" in names, "distinct product from the merged duplicate must survive"
    assert len(names) == 4, f"3 shared + 1 distinct = 4 unique products, got {sorted(names)}"


def test_v454_idempotent_on_unique_domains():
    merge = _merge()
    dm = {"domains": [
        {"name": "customer", "description": "Customer master.", "products": [_prod("account")]},
        {"name": "vehicle", "description": "Vehicle catalog.", "products": [_prod("model_variant")]},
    ]}
    merged = merge(dm, _Log())
    assert merged == 0, "unique-named model must be a no-op"
    assert len(dm["domains"]) == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
