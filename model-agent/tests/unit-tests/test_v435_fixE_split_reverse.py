"""v4.3.5 FIX E behavioral test (alias=vov-split-product / vov-reverse-fk).

Root cause: split_product and reverse_fk did not exist as deterministic VOV actions, so
reviewer P6 (split the preference god-table) and P9 (reverse a wrong-direction FK) fell to the
LLM sandbox and churned. FIX E adds explicit-spec parsers, classify branches, and nested-model
appliers.

Fail-pre / pass-post: pre-patch _v337_classify_op returns None for split/reverse (routed to
LLM) and the appliers do not exist. Post-patch classify returns the deterministic tuple and the
appliers mutate the model (child tables created + source columns moved; source FK dropped +
counterpart FK added).
"""
import copy as _copy
import re as _re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v435_helpers import concat_source, slice_functions

_FNS = [
    "_v337_iter_products", "_v337_find_product", "_v337_parse_fk_fqn", "_v327_infer_coltype",
    "_v301_extract_rename_target", "_v337_extract_move_target", "_v337_extract_col_rename",
    "_v337_extract_split", "_v337_extract_reverse_fk", "_v337_classify_op",
    "_v337_apply_split_product", "_v337_apply_reverse_fk",
]


def _ns():
    src = concat_source()
    return slice_functions(_FNS, src, extra_globals={"re": _re, "copy": _copy})


def test_fixE_classify_split_and_reverse_route_deterministically():
    ns = _ns()
    classify = ns["_v337_classify_op"]
    sp = classify("split_product", "customer.preference",
                  "split customer.preference into preference_core(preference_id, customer_id), "
                  "preference_value(preference_id, attr_key, attr_value)", "")
    assert sp is not None and sp[0] == "split_product", sp
    rf = classify("reverse_fk", "sales.order_line",
                  "reverse the fk on customer_id so the master is referenced by the line", "")
    assert rf is not None and rf[0] == "reverse_fk", rf


def test_fixE_apply_split_product_creates_children_and_moves_columns():
    ns = _ns()
    apply_split = ns["_v337_apply_split_product"]
    mdl = {"domains": [
        {"name": "customer", "products": [
            {"name": "preference", "primary_key": "preference_id", "attributes": [
                {"name": "preference_id", "type": "BIGINT"},
                {"name": "customer_id", "type": "BIGINT"},
                {"name": "attr_key", "type": "STRING"},
                {"name": "attr_value", "type": "STRING"},
            ]},
        ]},
    ]}
    spec = [("preference_core", ["preference_id", "customer_id"]),
            ("preference_value", ["preference_id", "attr_key", "attr_value"])]
    r = apply_split(mdl, "customer", "preference", spec)
    assert r is not None, "split applier returned None"
    prods = {p["name"]: p for p in mdl["domains"][0]["products"]}
    assert "preference_core" in prods and "preference_value" in prods
    src_cols = {a["name"] for a in prods["preference"]["attributes"]}
    # attr_key/attr_value moved out of the source god-table; PK stays
    assert "attr_key" not in src_cols and "attr_value" not in src_cols
    assert "preference_id" in src_cols
    val_cols = {a["name"] for a in prods["preference_value"]["attributes"]}
    assert {"attr_key", "attr_value"}.issubset(val_cols)


def test_fixE_apply_reverse_fk_flips_direction():
    ns = _ns()
    apply_rev = ns["_v337_apply_reverse_fk"]
    mdl = {"domains": [
        {"name": "sales", "products": [
            {"name": "order_line", "primary_key": "order_line_id", "attributes": [
                {"name": "order_line_id", "type": "BIGINT"},
                {"name": "customer_id", "type": "BIGINT",
                 "foreign_key_to": "customer.master.customer_id"},
            ]},
        ]},
        {"name": "customer", "products": [
            {"name": "master", "primary_key": "customer_id",
             "attributes": [{"name": "customer_id", "type": "BIGINT"}]},
        ]},
    ]}
    r = apply_rev(mdl, "sales", "order_line", ("customer_id", None))
    assert r is not None, "reverse_fk applier returned None"
    # source FK dropped
    ol = mdl["domains"][0]["products"][0]
    src = next(a for a in ol["attributes"] if a["name"] == "customer_id")
    assert not src.get("foreign_key_to"), "source FK not dropped"
    # counterpart FK added on customer.master pointing back to sales.order_line PK
    master = mdl["domains"][1]["products"][0]
    back = [a for a in master["attributes"] if a.get("foreign_key_to", "").startswith("sales.order_line.")]
    assert back, "counterpart FK not added on customer.master"
