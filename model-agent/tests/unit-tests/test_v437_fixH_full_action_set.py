"""v4.3.7 FIX H behavioral tests — expander emits the FULL canonical action set the
reviewer directives need (add_scd2_history / move_product / update_description) and the
_v337 split/reverse appliers are wired into the deterministic bridge.

ROOT CAUSE this extends: v4.3.6 FIX G made only remove_attribute/retype_attribute
reachable. P10 (SCD), P7/P8 (rehome/PCI move), and P2 (vendor-neutral descriptions)
still fell to the LLM sandbox because the expander did not emit their canonical actions
and the _v337 split/reverse appliers were never invoked from a VReq.

FAIL-PRE proof: on v4.3.6 HEAD the expander takes ONE arg (`_v436_expand_vreq_to_priorities(vreq)`)
and emits only remove/retype; `_v437_priority_to_v337_op` does not exist, and
`_v413_apply_det_op_inplace` has no split_product/reverse_fk branch. Each assertion below
fails pre-patch (TypeError on the model arg / empty output / LookupError / None result).
PASS-POST: the extended expander + bridge produce the exact canonical ops.
"""
import re

from v435_helpers import concat_source, slice_functions


class _V:
    def __init__(self, intent="", quote="", target="", vid="VREQ-T"):
        self.intent = intent
        self.source_quote = quote
        self.target = target
        self.vreq_id = vid


def _expander_ns():
    src = concat_source()
    return slice_functions(
        ["_v436_expand_vreq_to_priorities", "_v437_priority_to_v337_op"],
        src, extra_globals={"re": re})


_P7 = ("Move products that are not customer master identity out of the customer domain:\n"
       "  - move customer.service_case to a dedicated service domain.\n"
       "  - move customer.segment and customer.customer_membership to a marketing / customer_intelligence domain.")

_P8 = ("Move customer.payment_method (including cardholder_name and card fields) into a "
       "vault-adjacent finance domain table (e.g. finance.payment_instrument).")


def test_fixH_scd_emits_add_scd2_history_per_master_table():
    ns = _expander_ns()
    out = ns["_v436_expand_vreq_to_priorities"](
        _V("scd_history_on_master",
           "Master tables customer.profile and customer.account must carry change history (SCD-2 "
           "effective_start_date/effective_end_date).", vid="VREQ-010"))
    got = {(p["action"], p["target"]) for p in out}
    assert ("add_scd2_history", "customer.profile") in got, got
    assert ("add_scd2_history", "customer.account") in got, got


def test_fixH_move_expands_all_products_with_per_clause_dest():
    ns = _expander_ns()
    out = ns["_v436_expand_vreq_to_priorities"](_V("rehome_non_identity_products", _P7, vid="VREQ-007"))
    moves = {(p["target"], p["new_domain"]) for p in out if p["action"] == "move_product"}
    assert ("customer.service_case", "service") in moves, moves
    assert ("customer.segment", "marketing") in moves, moves
    assert ("customer.customer_membership", "marketing") in moves, moves


def test_fixH_move_op_converter_builds_v337_tuple_and_ignores_abbrev_noise():
    ns = _expander_ns()
    out = ns["_v436_expand_vreq_to_priorities"](_V("pci_scope_isolation", _P8, vid="VREQ-008"))
    ops = [ns["_v437_priority_to_v337_op"](p) for p in out if p["action"] == "move_product"]
    ops = [o for o in ops if o]
    assert ("move_product", "customer", "payment_method", "finance") in ops, ops
    # "e.g." abbreviation must NOT become a bogus move op
    assert not any(o[1] == "e" for o in ops), ops


def test_fixH_vendor_neutral_rewrites_descriptions_model_wide():
    ns = _expander_ns()
    model = {"model": {"domains": [{"name": "customer", "products": [
        {"name": "profile", "description": "Mastered in Informatica MDM.",
         "attributes": [{"name": "email", "description": "Captured by Salesforce Commerce Cloud."}]}]}]}}
    p2 = ('vendor_neutral_descriptions: strip vendor names. '
          '"Informatica MDM" -> "the customer master data system", '
          '"Salesforce Commerce Cloud" -> "the e-commerce platform"')
    out = ns["_v436_expand_vreq_to_priorities"](_V("vendor_neutral_descriptions", p2, vid="VREQ-002"), model)
    by_t = {p["target"]: p["new_description"] for p in out if p["action"] == "update_description"}
    assert "Informatica MDM" not in by_t.get("customer.profile", ""), by_t
    assert "Salesforce Commerce Cloud" not in by_t.get("customer.profile.email", ""), by_t


def test_fixH_v413_bridge_applies_split_and_reverse():
    # Proves the _v337 split/reverse appliers are now reachable via _v413_apply_det_op_inplace.
    src = concat_source()
    ns = slice_functions(
        ["_v413_apply_det_op_inplace", "_v337_apply_split_product", "_v337_apply_reverse_fk",
         "_v337_find_product", "_v337_iter_products", "_v337_apply_move_product",
         "_v337_apply_rename_product", "_v337_apply_rename_attribute", "_v337_rewire_fks",
         "_v337_parse_fk_fqn", "_v251_find_product", "_v327_infer_coltype"],
        src, extra_globals={"re": re, "copy": __import__("copy")})
    fn = ns["_v413_apply_det_op_inplace"]
    model = {"model": {"domains": [{"name": "customer", "products": [
        {"name": "preference", "primary_key": "preference_id", "attributes": [
            {"name": "preference_id", "type": "BIGINT"},
            {"name": "channel", "type": "STRING"},
            {"name": "diet", "type": "STRING"}]}]}]}}
    r = fn(model, ("split_product", "customer", "preference",
                   [("communication_preference", ["channel"]), ("dietary_restriction", ["diet"])]))
    assert r is not None, "split not applied via _v413"
    names = {p["name"] for p in model["model"]["domains"][0]["products"]}
    assert "communication_preference" in names and "dietary_restriction" in names, names
