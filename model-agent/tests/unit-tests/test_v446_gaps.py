"""v4.4.6 behavioral tests for the generic agent capability gaps automotive surfaced (CLAUDE.md 8.10).

GAP-1 (HIGH): the surgical-VOV outcome-scope guard discarded an additive new-domain-with-products
batch as scope_mismatch because the batch summary omitted explicit "create domain" phrasing, even
though a USER-KING domain_creates / reviewer add_domain VREQ mandated the first-class domain. Fix:
`diff_within_summary_scope` now takes `allowed_new_domains` and whitelists additions named in the
batch's own VREQ text (`_vov446_allowed_new_domains`).

GAP-4 (LOW): `ai_query` returns SQL NULL -> None on timeout; `_call_ai_query` then called len() on it
and raised `TypeError: object of type 'NoneType' has no len()`. Fix: `_v446_coerce_ai_response`.

Fail-pre proof: on the committed v4.4.5 notebook `_vov446_allowed_new_domains` /
`_v446_coerce_ai_response` do not exist (slice raises LookupError) and `diff_within_summary_scope`
has no `allowed_new_domains` kwarg (TypeError) -> every test below errors. git-stash the notebook ->
FAIL; pop -> PASS.

Generic: uses a NON-automotive domain name ("field_services" is generic; the tests also use
"telemetry_ops") and never hardcodes an industry.
"""
import re

import pytest

from v435_helpers import concat_source, slice_functions


def _scope_ns():
    return slice_functions(
        ["diff_within_summary_scope", "_vov446_allowed_new_domains"],
        concat_source(), extra_globals={"re": re})


def _coerce_ns():
    return slice_functions(["_v446_coerce_ai_response"], concat_source())


def _empty_diff(**over):
    d = {"domains_added": set(), "domains_removed": set(), "products_added": [],
         "products_removed": [], "fks_removed": 0, "fks_added": 0, "metric_views_delta": 0}
    d.update(over)
    return d


class _Row:
    def __init__(self, val):
        self.ai_response = val


# ===================================================== GAP-1
def test_gap1_whitelisted_new_domain_is_in_scope():
    ns = _scope_ns()
    diff = _empty_diff(domains_added={"field_services"})
    # summary does NOT contain "create/add/new domain" -> pre-patch this rejected the batch
    ok, diag = ns["diff_within_summary_scope"](
        diff, "Populate field_services with its products and links.",
        allowed_new_domains={"field_services"})
    assert ok, "user-king new domain must be in scope: %s" % diag


def test_gap1_unauthorized_new_domain_still_rejected():
    """Anti-tautology: a domain NOT in the allow-set is still flagged out-of-scope."""
    ns = _scope_ns()
    diff = _empty_diff(domains_added={"hallucinated_domain"})
    ok, diag = ns["diff_within_summary_scope"](
        diff, "Populate field_services with its products.",
        allowed_new_domains={"field_services"})
    assert not ok and "domains_added" in diag, diag


def test_gap1_default_no_allowlist_preserves_old_behavior():
    """With no allow-set and no create phrasing, a domain add is still out-of-scope (backward-compat)."""
    ns = _scope_ns()
    diff = _empty_diff(domains_added={"whatever"})
    ok, diag = ns["diff_within_summary_scope"](diff, "some unrelated summary")
    assert not ok, diag


def test_gap1_helper_whitelists_domain_named_in_vreq_text():
    ns = _scope_ns()
    payload = ({"intent": "Add a first-class field_services domain with 12 products",
                "target": "field_services", "source_quote": "field_services should be its own domain"},)
    out = ns["_vov446_allowed_new_domains"](payload, "surgical batch", {"field_services"})
    assert out == {"field_services"}


def test_gap1_helper_excludes_domain_not_in_any_vreq():
    ns = _scope_ns()
    payload = ({"intent": "Add a first-class field_services domain", "target": "field_services",
                "source_quote": ""},)
    # LLM also invented 'marketing_extra' which no VREQ mentions -> must NOT be whitelisted
    out = ns["_vov446_allowed_new_domains"](payload, "", {"field_services", "marketing_extra"})
    assert out == {"field_services"}


def test_gap1_generic_second_domain_name():
    """Prove genericity with a different domain token."""
    ns = _scope_ns()
    payload = ({"intent": "create telemetry_ops domain", "target": "telemetry_ops", "source_quote": ""},)
    out = ns["_vov446_allowed_new_domains"](payload, "", {"telemetry_ops"})
    assert out == {"telemetry_ops"}
    diff = _empty_diff(domains_added={"telemetry_ops"})
    ok, _ = ns["diff_within_summary_scope"](diff, "no create phrase here", allowed_new_domains=out)
    assert ok


# ===================================================== GAP-4
def test_gap4_none_ai_response_coerced_to_empty_string():
    ns = _coerce_ns()
    raw, was_none = ns["_v446_coerce_ai_response"]([_Row(None)])
    assert raw == "" and was_none is True
    # the whole point: len() must not raise
    assert len(raw) == 0


def test_gap4_normal_response_passthrough():
    ns = _coerce_ns()
    raw, was_none = ns["_v446_coerce_ai_response"]([_Row('{"status":"fulfilled"}')])
    assert raw == '{"status":"fulfilled"}' and was_none is False


def test_gap4_empty_rows_safe():
    ns = _coerce_ns()
    raw, was_none = ns["_v446_coerce_ai_response"]([])
    assert raw == "" and was_none is False
    assert len(raw) == 0


# ===================================================== GAP-2
def _connect_ns():
    """Slice _v415_complete_connect_details plus every _v251_*/_v410_* helper it
    transitively calls, so the REAL connect-completion path executes end-to-end."""
    import ast as _ast
    src = concat_source()
    tree = _ast.parse(src)
    helpers = [n.name for n in tree.body
               if isinstance(n, _ast.FunctionDef)
               and (n.name.startswith("_v251_") or n.name.startswith("_v410_"))]
    names = list(dict.fromkeys(helpers + ["_v415_complete_connect_details"]))
    return slice_functions(names, src, extra_globals={"re": re})


def _automotive_connect_model():
    return {"model": {"domains": [
        {"name": "mobility", "products": [
            {"name": "predictive_maintenance_alert", "primary_key": "alert_id",
             "attributes": [{"name": "alert_id", "primary_key": True}]},
            {"name": "connected_vehicle", "primary_key": "connected_vehicle_id",
             "attributes": [{"name": "connected_vehicle_id", "primary_key": True}]}]},
        {"name": "product", "products": [
            {"name": "order_guide", "primary_key": "order_guide_id",
             "attributes": [{"name": "order_guide_id", "primary_key": True}]}]},
        {"name": "aftersales", "products": [
            {"name": "aftersales_repair_order", "primary_key": "repair_order_id",
             "attributes": [{"name": "repair_order_id", "primary_key": True}]},
            {"name": "aftersales_parts_order", "primary_key": "parts_order_id",
             "attributes": [{"name": "parts_order_id", "primary_key": True}]},
            {"name": "service_appointment", "primary_key": "appt_id",
             "attributes": [{"name": "appt_id", "primary_key": True}]}]}]}}


def test_gap2_misresolved_connect_rescoped_to_named_domain():
    """The FK column resolved to a same-word product in the WRONG domain (product.order_guide),
    but the directive explicitly names the aftersales domain as the FK target. The correction
    re-scopes to the reviewer-named domain. Fail-pre: v4.4.5 has no GAP-2 block -> stays 'product.*'."""
    ns = _connect_ns()
    f = ns["_v415_complete_connect_details"]
    pr = {"action": "connect_table", "target": "mobility.predictive_maintenance_alert",
          "intent": "add column service_order_id with FK to the aftersales service order table",
          "source_quote": "FK to the aftersales service order table", "reason": "integration"}
    out = f(pr, {"fk_target": "product.order_guide.order_guide_id", "column": "service_order_id"},
            _automotive_connect_model(), None)
    assert out["fk_target"].startswith("aftersales."), out["fk_target"]


def test_gap2_explicit_target_domain_never_disturbed():
    """When the resolved domain IS named in the directive (an explicit 'FK to mobility.connected_vehicle'),
    the correction must NOT fire even though another domain (aftersales, the source table) is in the text."""
    ns = _connect_ns()
    f = ns["_v415_complete_connect_details"]
    pr = {"action": "connect_table", "target": "aftersales.service_appointment",
          "intent": "add connected_vehicle_id to the aftersales service appointment table with FK to mobility.connected_vehicle",
          "source_quote": "FK to mobility.connected_vehicle", "reason": "link"}
    out = f(pr, {"fk_target": "mobility.connected_vehicle.connected_vehicle_id", "column": "connected_vehicle_id"},
            _automotive_connect_model(), None)
    assert out["fk_target"] == "mobility.connected_vehicle.connected_vehicle_id"


def test_gap2_correct_in_domain_resolution_left_alone():
    """A correctly in-domain-resolved FK (both the target and resolved domain are 'aftersales') must
    pass through untouched -- no spurious re-scope when the resolved domain is present in the text."""
    ns = _connect_ns()
    f = ns["_v415_complete_connect_details"]
    pr = {"action": "connect_table", "target": "aftersales.aftersales_parts_order",
          "intent": "add repair_order_id referencing aftersales.aftersales_repair_order",
          "source_quote": "reference aftersales.aftersales_repair_order", "reason": "link"}
    out = f(pr, {"fk_target": "aftersales.aftersales_repair_order.repair_order_id", "column": "repair_order_id"},
            _automotive_connect_model(), None)
    assert out["fk_target"] == "aftersales.aftersales_repair_order.repair_order_id"


# ===================================================== GAP-3
def _forcekeep_ns():
    return slice_functions(["_v446_force_keep_shrink"], concat_source(), extra_globals={"re": re})


_GAP3_REVIEWER = (
    "REVIEWER-PRIORITY 8 - strengthen Procurement and Mobility in the MVM: the MVM excludes "
    "Procurement and Mobility entirely, which is too aggressive. When shrinking the ECM to the MVM, "
    "keep basic Procurement in the MVM: purchase_order, purchase_order_line, purchase_requisition, "
    "supplier, scheduling_agreement, goods_receipt. Also keep the Mobility basics in the MVM: "
    "connected_vehicle, telemetry_event, predictive_maintenance_alert.")


def _gap3_products():
    prods = [{"domain": "procurement", "product": p} for p in
             ("purchase_order", "purchase_order_line", "purchase_requisition", "supplier",
              "scheduling_agreement", "goods_receipt", "rfq")]
    prods += [{"domain": "mobility", "product": p} for p in
              ("connected_vehicle", "telemetry_event", "predictive_maintenance_alert", "geofence")]
    prods += [{"domain": "sales", "product": p} for p in ("sales_order", "quote")]
    return prods


def test_gap3_forcekeep_readds_reviewer_named_mvm_products():
    """The shrink heuristic excluded procurement + mobility entirely; the USER-KING 'keep ... in the
    MVM: a, b, c' directive force-re-adds the 9 reviewer-named products. Fail-pre: v4.4.5 has no
    _v446_force_keep_shrink -> slice raises LookupError."""
    f = _forcekeep_ns()["_v446_force_keep_shrink"]
    ttk = {("sales", "sales_order"), ("sales", "quote")}
    out = f(ttk, _GAP3_REVIEWER, _gap3_products())
    kept = {p for (_d, p) in out}
    for must in ("purchase_order", "purchase_order_line", "purchase_requisition", "supplier",
                 "scheduling_agreement", "goods_receipt",
                 "connected_vehicle", "telemetry_event", "predictive_maintenance_alert"):
        assert must in kept, must


def test_gap3_does_not_add_products_outside_the_directive():
    """Products in those domains that the reviewer did NOT name (rfq, geofence) are NOT force-kept,
    and phantom names (not in products_data) are never invented."""
    f = _forcekeep_ns()["_v446_force_keep_shrink"]
    ttk = {("sales", "sales_order")}
    out = f(ttk, _GAP3_REVIEWER, _gap3_products())
    assert ("procurement", "rfq") not in out
    assert ("mobility", "geofence") not in out
    assert not any(p == "nonexistent_table" for (_d, p) in out)


def test_gap3_noop_when_no_keep_directive():
    """No 'keep ... in the MVM' phrasing -> tables_to_keep returned unchanged (retail/other industries)."""
    f = _forcekeep_ns()["_v446_force_keep_shrink"]
    ttk = {("sales", "sales_order"), ("sales", "quote")}
    out = f(ttk, "the customer domain should be minimal: profile plus address.", _gap3_products())
    assert set(out) == ttk


def test_gap3_preserves_input_container_type():
    """Set in -> set out; list in -> list out (call-site passes a set)."""
    f = _forcekeep_ns()["_v446_force_keep_shrink"]
    out_set = f({("sales", "sales_order")}, _GAP3_REVIEWER, _gap3_products())
    assert isinstance(out_set, set)
    out_list = f([("sales", "sales_order")], _GAP3_REVIEWER, _gap3_products())
    assert isinstance(out_list, list)
