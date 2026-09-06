"""v4.3.2 behavioral tests for RC3/RC4/RC5 (fail-pre HEAD / pass-post per CLAUDE.md 8.10).

RC3 rc3-v403-nested-sync: _detect_direct_bidirectional_links auto-resolves the pointer-side
    FK by clearing it in the THROWAWAY flat copy _v403 builds; the clear was never mirrored to
    the authoritative nested data_model, so the bidirectional link shipped in model.json. The fix
    mirrors flat FK-clears back to the nested attribute via a _nested reference.
RC4 rc4-malformed-tag-drop: an LLM build-directive annotation ([enum-ref-candidate: a|b - promote...])
    leaked into the tags string and tokenized into junk physical tags (dbx_[enum_ref_candidate,
    dbx_class_2, ...). The finalize tag-scope sanitizer now drops any token carrying structural
    markers ([ ] | em/en-dash) that can never be a valid physical tag key.
RC5 rc5-silo-self-fk-exclude: build_fk_graph counted a self-referential FK (parent-hierarchy) as
    both incoming AND outgoing, so a table connected ONLY to itself was never flagged as siloed by
    the remediation, while the acceptance gate (which excludes self-loops) flagged it. Silo
    detection now passes exclude_self=True so its verdict matches the gate.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notebook_source_util import exec_function_namespace, exec_functions_namespace


class _L:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


# --------------------------------------------------------------------------- RC5
def _stub_parse_fk_reference(fk):
    parts = str(fk or "").split(".")
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], None
    return None, None, None


def _load_fk_graph():
    ns = exec_function_namespace(
        "build_fk_graph",
        extra_globals={
            "defaultdict": __import__("collections").defaultdict,
            "_ensure_dict": (lambda x: x if isinstance(x, dict) else {}),
            "parse_fk_reference": _stub_parse_fk_reference,
            "_disk_cached_call": (lambda name, key, fn: fn()),
        },
    )
    return ns["build_fk_graph"]


def _self_fk_model():
    prods = [{"domain": "vendor", "product": "spend_category"}]
    attrs = [
        {"domain": "vendor", "product": "spend_category", "attribute": "spend_category_id",
         "foreign_key_to": ""},
        {"domain": "vendor", "product": "spend_category", "attribute": "parent_spend_category_id",
         "foreign_key_to": "vendor.spend_category.spend_category_id"},
    ]
    return prods, attrs


def test_rc5_self_fk_not_counted_as_connectivity():
    """A table whose ONLY FK is a self-referential parent pointer must count as siloed when
    exclude_self=True (matching the gate), and connected when exclude_self=False (legacy)."""
    build_fk_graph = _load_fk_graph()
    prods, attrs = _self_fk_model()

    inc, out, _ = build_fk_graph(attrs, prods)  # legacy: self-loop counts
    assert inc["vendor.spend_category"] == 1 and out["vendor.spend_category"] == 1

    inc2, out2, _ = build_fk_graph(attrs, prods, exclude_self=True)  # fix: self-loop dropped
    assert inc2["vendor.spend_category"] == 0 and out2["vendor.spend_category"] == 0


def test_rc5_cross_product_fk_still_counted_with_exclude_self():
    """exclude_self must NOT drop a genuine cross-product FK (no false silo)."""
    build_fk_graph = _load_fk_graph()
    prods = [{"domain": "vendor", "product": "spend_category"},
             {"domain": "vendor", "product": "spend"}]
    attrs = [
        {"domain": "vendor", "product": "spend", "attribute": "spend_category_id",
         "foreign_key_to": "vendor.spend_category.spend_category_id"},
    ]
    inc, out, _ = build_fk_graph(attrs, prods, exclude_self=True)
    assert inc["vendor.spend_category"] == 1  # referenced by vendor.spend
    assert out["vendor.spend"] == 1


def test_rc5_siloed_list_flags_self_only_table():
    """_get_siloed_products_list must now flag a self-only reference table as siloed."""
    ns = exec_functions_namespace(
        ["build_fk_graph", "build_product_keys_set", "_get_siloed_products_list"],
        extra_globals={
            "defaultdict": __import__("collections").defaultdict,
            "_ensure_dict": (lambda x: x if isinstance(x, dict) else {}),
            "parse_fk_reference": _stub_parse_fk_reference,
            "_disk_cached_call": (lambda name, key, fn: fn()),
        },
    )
    prods, attrs = _self_fk_model()
    siloed = ns["_get_siloed_products_list"](attrs, prods, _L())
    assert "vendor.spend_category" in siloed


# --------------------------------------------------------------------------- RC4
def _load_sanitizer():
    stubs = {
        "re": re,
        "_V432_MALFORMED_TAG_RE": re.compile(r"[\[\]\|\u2014\u2013]"),
        "_v381_scope_conflict": (lambda entity_scope, tag_scope: False),
        "_v381_tag_scope": (lambda k, tp="", tsx="": "attribute"),
        "_v381_is_placeholder_tag_value": (lambda v: False),
        "_v381_bare_key": (lambda k, tp="", tsx="": k),
        "_v381_filter_tagset": (lambda ts, scope, tp="", tsx="": ts),
    }
    ns = exec_function_namespace("_v381_sanitize_tag_scopes", extra_globals=stubs)
    return ns["_v381_sanitize_tag_scopes"]


def test_rc4_malformed_build_directive_blob_dropped():
    """The exact semiconductors leak: an [enum-ref-candidate: ...] annotation in the tags field
    must be dropped so it cannot tokenize into junk physical tags."""
    fn = _load_sanitizer()
    attr = {"domain": "supply", "product": "inbound_shipment", "attribute": "incoterms",
            "tags": "[enum-ref-candidate: exw|fca|fob|cif|ddp \u2014 promote to reference product]"}
    stats = fn([], [attr], config={}, logger=_L())
    assert stats.get("malformed", 0) == 1
    assert attr["tags"] == ""


def test_rc4_clean_tags_preserved():
    """Well-formed tags (no structural markers) must survive untouched."""
    fn = _load_sanitizer()
    attr = {"domain": "supply", "product": "inbound_shipment", "attribute": "incoterms",
            "tags": "pii=false,glossary_term=incoterms"}
    stats = fn([], [attr], config={}, logger=_L())
    assert stats.get("malformed", 0) == 0
    assert "glossary_term=incoterms" in attr["tags"]
    assert "pii=false" in attr["tags"]


def test_rc4_mixed_drops_only_malformed_token():
    """A tags string mixing a clean token and a malformed blob drops only the blob."""
    fn = _load_sanitizer()
    attr = {"domain": "d", "product": "p", "attribute": "a",
            "tags": "pii=true,[enum-ref-candidate: a|b]"}
    fn([], [attr], config={}, logger=_L())
    assert "pii=true" in attr["tags"]
    assert "enum-ref-candidate" not in attr["tags"]
    assert "[" not in attr["tags"] and "|" not in attr["tags"]


# --------------------------------------------------------------------------- RC3
def _load_v403():
    ns = exec_functions_namespace(
        ["_detect_direct_bidirectional_links", "_detect_cycles_dfs",
         "_v403_break_cycles_in_serialized_model"],
        extra_globals={
            "defaultdict": __import__("collections").defaultdict,
            "_break_cycles_heuristic_internal": (lambda *a, **k: ([], [])),
        },
    )
    return ns["_v403_break_cycles_in_serialized_model"]


def _bidirectional_model():
    """Reproduces the real semiconductors customer.account <-> customer.address bidirectional pair:
    account.primary_address_id -> address (pointer: 'primary_' prefix, auto-resolved) and
    address.address_account_id -> account (ownership, kept)."""
    return {
        "domains": [{
            "name": "customer",
            "products": [
                {"name": "account", "attributes": [
                    {"name": "account_id", "foreign_key_to": ""},
                    {"name": "primary_address_id",
                     "foreign_key_to": "customer.address.address_id"},
                ]},
                {"name": "address", "attributes": [
                    {"name": "address_id", "foreign_key_to": ""},
                    {"name": "address_account_id",
                     "foreign_key_to": "customer.account.account_id"},
                ]},
            ],
        }]
    }


def _nested_fk(dm, product, attr):
    for d in dm["domains"]:
        for p in d["products"]:
            if p["name"] == product:
                for a in p["attributes"]:
                    if a["name"] == attr:
                        return a["foreign_key_to"]
    return None


def test_rc3_bidirectional_pointer_clear_mirrored_to_nested():
    """FAIL-PRE (HEAD _v403 has no nested sync): the pointer-side FK is cleared only in the flat
    copy, so the nested model still ships the bidirectional link. PASS-POST: _v403 mirrors the
    clear into the nested data_model and reports >=1 cleared."""
    fn = _load_v403()
    dm = _bidirectional_model()
    assert _nested_fk(dm, "account", "primary_address_id") == "customer.address.address_id"

    cleared = fn(dm, _L())

    assert cleared >= 1
    # pointer side cleared in the AUTHORITATIVE nested dict
    assert _nested_fk(dm, "account", "primary_address_id") == ""
    # ownership side preserved
    assert _nested_fk(dm, "address", "address_account_id") == "customer.account.account_id"


def test_rc3_clean_model_is_noop():
    """A model with no bidirectional/cycle must be an idempotent no-op (0 cleared)."""
    fn = _load_v403()
    dm = {
        "domains": [{
            "name": "customer",
            "products": [
                {"name": "account", "attributes": [
                    {"name": "account_id", "foreign_key_to": ""}]},
                {"name": "address", "attributes": [
                    {"name": "address_id", "foreign_key_to": ""},
                    {"name": "address_account_id",
                     "foreign_key_to": "customer.account.account_id"}]},
            ],
        }]
    }
    cleared = fn(dm, _L())
    assert cleared == 0
    assert _nested_fk(dm, "address", "address_account_id") == "customer.account.account_id"
