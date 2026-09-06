"""v4.4.0 behavioral tests — the five deterministic reviewer-directive fixes, each exercising the
REAL notebook code path (CLAUDE.md 8.10), each proven fail-pre on the v4.3.9 HEAD (git stash the
v4.4.0 edits) and pass-post:

  P6 split_preference_god_table  — vov-split-godtable: the expander emits a split_product op whose
     split_spec keyword-routes EVERY source column into a reviewer-named child (no column dropped);
     the reused _v337 split applier then materializes the 3 child tables. Pre-patch: no split_product.
  P9 fk_direction_correctness    — vov-prune-root-fks: cell-60 handler prunes the ROOT domain's
     OUTBOUND cross-domain FKs EXCEPT those to reference/dimension tables. Pre-patch: unsupported action.
  P12 glossary_and_regex_tag_cleanup — vov-tag-cleanup: cell-60 handler clears junk glossary
     (term==TitleCase(col)) + redundant value_regex, in field AND tag_set, KEEPING pii. Pre-patch: unsupported.
  P2 vendor_neutral_descriptions — vov-vendor-neutral-residual: the expander strips brand-root
     VARIANTS ("Salesforce Marketing Cloud") + brand examples ("Nike") the exact-pair pass missed.
     Pre-patch: variant survives -> no update_description emitted for that description.
  P13 ensure_household_and_mvm_minimalism — vov-shrink-domain-restrict: _v440_restrict_shrink_domain
     restricts a reviewer-named domain to its reviewer-named MVM tables. Pre-patch: def not found.
"""
import re
import copy

from v435_helpers import concat_source, slice_functions


class _StubVREQ:
    def __init__(self, vreq_id="", intent="", target="", source_quote="", priority_id=9999):
        self.vreq_id = vreq_id
        self.intent = intent
        self.target = target
        self.source_quote = source_quote
        self.severity = "critical"
        self.is_user_directive = True
        self.priority_id = priority_id


class _Log:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def debug(self, *a, **k):
        pass


def _expander_ns():
    return slice_functions(["_v436_expand_vreq_to_priorities"], concat_source(),
                           extra_globals={"re": re})


# ============================================================ P6 split god-table
P6_BLOCK = (
    "REVIEWER-PRIORITY 6 \u2014 split_preference_god_table: customer.preference crams 12 unrelated "
    "concepts into one EAV-style table. Split it into focused tables: customer.communication_preference, "
    "customer.dietary_restriction, and a small generic customer.customer_attribute(key, value) "
    "extensibility table for the long tail. Do not keep a single catch-all preference_category table.\n"
)


def _pref_model():
    return {"domains": [
        {"name": "customer", "products": [
            {"name": "preference", "primary_key": "preference_id", "attributes": [
                {"name": "preference_id", "type": "BIGINT"},
                {"name": "channel_captured", "type": "STRING"},
                {"name": "consent_given", "type": "BOOLEAN"},
                {"name": "opt_out_flag", "type": "BOOLEAN"},
                {"name": "language", "type": "STRING"},
                {"name": "allergy_info", "type": "STRING"},
                {"name": "dietary_restriction_note", "type": "STRING"},
                {"name": "favorite_color", "type": "STRING"},
                {"name": "shoe_size", "type": "STRING"},
            ]},
        ]},
    ]}


def test_p6_expander_emits_split_spec_routing_all_columns():
    ns = _expander_ns()
    vreq = _StubVREQ(vreq_id="REVIEWER-6", intent="split_preference_god_table",
                     source_quote=P6_BLOCK, priority_id=6)
    out = ns["_v436_expand_vreq_to_priorities"](vreq, _pref_model())
    splits = [p for p in out if p["action"] == "split_product"]
    assert len(splits) == 1, out
    sp = splits[0]
    assert sp["target"] == "customer.preference", sp
    spec = dict(sp["split_spec"])
    assert set(spec) == {"communication_preference", "dietary_restriction", "customer_attribute"}, spec
    # keyword routing: comm keywords -> communication_preference
    assert set(spec["communication_preference"]) == {
        "channel_captured", "consent_given", "opt_out_flag", "language"}, spec
    # diet keywords -> dietary_restriction
    assert set(spec["dietary_restriction"]) == {"allergy_info", "dietary_restriction_note"}, spec
    # everything else -> catch-all customer_attribute (NO column dropped)
    assert set(spec["customer_attribute"]) == {"favorite_color", "shoe_size"}, spec
    # union of routed cols == all non-PK source cols (nothing dropped)
    routed = set().union(*spec.values())
    assert routed == {"channel_captured", "consent_given", "opt_out_flag", "language",
                      "allergy_info", "dietary_restriction_note", "favorite_color", "shoe_size"}, routed


def test_p6_split_applier_materializes_child_tables():
    # exercise the REAL reused _v337 split applier on the expander's spec
    exp = _expander_ns()
    vreq = _StubVREQ(vreq_id="REVIEWER-6", intent="split_preference_god_table",
                     source_quote=P6_BLOCK, priority_id=6)
    spec = dict([p for p in exp["_v436_expand_vreq_to_priorities"](vreq, _pref_model())
                 if p["action"] == "split_product"][0]["split_spec"])
    ns = slice_functions(
        ["_v337_apply_split_product", "_v337_find_product", "_v337_iter_products",
         "_v337_rewire_fks", "_v337_parse_fk_fqn", "_v327_infer_coltype"],
        concat_source(), extra_globals={"re": re, "copy": copy})
    mdl = _pref_model()
    res = ns["_v337_apply_split_product"](mdl, "customer", "preference",
                                          [(k, spec[k]) for k in spec])
    assert res is not None, "split should apply"
    prods = {p["name"]: p for p in mdl["domains"][0]["products"]}
    for child in ("communication_preference", "dietary_restriction", "customer_attribute"):
        assert child in prods, prods.keys()
        # each child carries the source PK so it links back
        assert any(a["name"] == "preference_id" for a in prods[child]["attributes"]), child


# ============================================================ P9 prune root outbound FKs
def _handler_ns():
    return slice_functions(
        ["_v251_apply_priority_deterministic", "_v251_model_root",
         "_v251_find_attribute_row", "_v251_find_product"],
        concat_source(), extra_globals={"re": re, "copy": copy})


def _fk_model():
    return {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "profile_id", "attributes": [
                {"name": "profile_id", "type": "BIGINT"},
                {"name": "location_id", "type": "BIGINT", "tags": "foreign_key",
                 "foreign_key_to": "store.location.location_id",
                 "tag_set": [{"key": "foreign_key", "value": ""}]},
                {"name": "order_id", "type": "BIGINT", "tags": "foreign_key",
                 "foreign_key_to": "order.header.order_id",
                 "tag_set": [{"key": "foreign_key", "value": ""}]},
                {"name": "household_id", "type": "BIGINT", "tags": "foreign_key",
                 "foreign_key_to": "customer.household.household_id",
                 "tag_set": [{"key": "foreign_key", "value": ""}]},
            ]},
        ]},
    ]}


def test_p9_prune_handler_keeps_ref_prunes_transaction_keeps_intra():
    ns = _handler_ns()
    mdl = _fk_model()
    ok, diag = ns["_v251_apply_priority_deterministic"](
        {"action": "prune_root_outbound_fks", "target": "customer"}, {}, mdl, _Log())
    assert ok and diag == "applied", (ok, diag)
    attrs = {a["name"]: a for a in mdl["domains"][0]["products"][0]["attributes"]}
    # reference/dimension target kept
    assert attrs["location_id"]["foreign_key_to"] == "store.location.location_id"
    # transaction target pruned (FK + label removed)
    assert attrs["order_id"]["foreign_key_to"] == ""
    assert attrs["order_id"]["tags"] == ""
    # intra-domain FK untouched
    assert attrs["household_id"]["foreign_key_to"] == "customer.household.household_id"


def test_p9_expander_emits_prune_priority():
    ns = _expander_ns()
    block = ("REVIEWER-PRIORITY 9 \u2014 fk_direction_correctness: the customer domain is a ROOT and "
             "should depend on almost nothing. Prune the ~49 outbound cross-domain FKs.\n")
    vreq = _StubVREQ(vreq_id="REVIEWER-9", intent="fk_direction_correctness",
                     source_quote=block, priority_id=9)
    out = ns["_v436_expand_vreq_to_priorities"](vreq, _fk_model())
    prunes = [p for p in out if p["action"] == "prune_root_outbound_fks"]
    assert len(prunes) == 1 and prunes[0]["target"] == "customer", out


# ============================================================ P12 glossary/regex tag cleanup
def _tag_model():
    return {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "account_id", "attributes": [
                # junk glossary: term == TitleCase(column)
                {"name": "account_id", "type": "BIGINT", "business_glossary_term": "Account ID",
                 "value_regex": "",
                 "tag_set": [{"key": "dbx_business_glossary_term", "value": "Account ID"}]},
                # genuine glossary term (NOT titlecase of column) -> keep
                {"name": "cltv_score", "type": "DECIMAL(18,2)",
                 "business_glossary_term": "Customer Lifetime Value",
                 "value_regex": "",
                 "tag_set": [{"key": "dbx_business_glossary_term", "value": "Customer Lifetime Value"}]},
                # value_regex duplicating the description -> clear
                {"name": "status_code", "type": "STRING", "business_glossary_term": "",
                 "value_regex": "active|inactive",
                 "description": "one of active|inactive",
                 "tag_set": [{"key": "dbx_value_regex", "value": "active|inactive"}]},
                # pii tag -> KEEP untouched
                {"name": "email", "type": "STRING", "business_glossary_term": "Email",
                 "value_regex": "",
                 "tag_set": [{"key": "dbx_business_glossary_term", "value": "Email"},
                             {"key": "dbx_pii_email", "value": "true"}]},
            ]},
        ]},
    ]}


def test_p12_cleanup_clears_junk_keeps_genuine_and_pii():
    ns = _handler_ns()
    mdl = _tag_model()
    ok, diag = ns["_v251_apply_priority_deterministic"](
        {"action": "cleanup_glossary_regex_tags", "target": "*"}, {}, mdl, _Log())
    assert ok and diag == "applied", (ok, diag)
    attrs = {a["name"]: a for a in mdl["domains"][0]["products"][0]["attributes"]}
    # junk glossary cleared in BOTH field and tag_set
    assert attrs["account_id"]["business_glossary_term"] == ""
    assert all(t["key"] != "dbx_business_glossary_term" for t in attrs["account_id"]["tag_set"])
    # genuine glossary preserved
    assert attrs["cltv_score"]["business_glossary_term"] == "Customer Lifetime Value"
    # dup value_regex cleared
    assert attrs["status_code"]["value_regex"] == ""
    assert all(t["key"] != "dbx_value_regex" for t in attrs["status_code"]["tag_set"])
    # pii tag KEPT even though its glossary junk ("Email") was cleared
    assert attrs["email"]["business_glossary_term"] == ""
    assert any(t["key"] == "dbx_pii_email" for t in attrs["email"]["tag_set"])


# ============================================================ P2 vendor-neutral residual
def _vendor_model():
    return {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "profile_id",
             "description": "Identity sourced from Salesforce Marketing Cloud and Nike loyalty feeds.",
             "attributes": [
                {"name": "profile_id", "type": "BIGINT",
                 "description": "Primary key managed in Salesforce."},
             ]},
        ]},
    ]}


P2_BLOCK = (
    "REVIEWER-PRIORITY 2 \u2014 vendor_neutral_descriptions: strip specific vendor/product names from "
    "ALL descriptions; replace with neutral role descriptors:\n"
    "  - \"Informatica MDM\" -> \"the customer master data system\"\n"
    "  - \"Salesforce Commerce Cloud\" -> \"the e-commerce platform\"\n"
    "  - \"Salesforce Service Cloud\" -> \"the case management system\"\n"
    "  - remove brand examples such as \"Nike\" and specific store names from descriptions.\n"
)


def test_p2_strips_brand_root_variant_and_examples():
    ns = _expander_ns()
    vreq = _StubVREQ(vreq_id="REVIEWER-2", intent="vendor_neutral_descriptions",
                     source_quote=P2_BLOCK, priority_id=2)
    out = ns["_v436_expand_vreq_to_priorities"](vreq, _vendor_model())
    updates = {p["target"]: p["new_description"] for p in out if p["action"] == "update_description"}
    # the god-table description (variant "Salesforce Marketing Cloud" + example "Nike") must be rewritten
    assert "customer.profile" in updates, updates
    new_desc = updates["customer.profile"]
    assert "Salesforce" not in new_desc, new_desc
    assert "Nike" not in new_desc, new_desc
    # the bare-"Salesforce" attribute description must also be rewritten
    assert "customer.profile.profile_id" in updates, updates
    assert "Salesforce" not in updates["customer.profile.profile_id"], updates


# ============================================================ P13 shrink domain restrict
def _p13_ns():
    return slice_functions(["_v440_restrict_shrink_domain"], concat_source(),
                           extra_globals={"re": re})


P13_BLOCK = (
    "REVIEWER-PRIORITY 13 \u2014 ensure_household_and_mvm_minimalism: keep a real customer.household "
    "table. For the MVM (shrink) specifically, the customer domain should be genuinely minimal: "
    "essentially profile + address + contact + consent (+ optional account for B2B). Do not carry the "
    "full CDP/MDM/CRM breadth into the MVM.\n"
)


def test_p13_restricts_reviewer_domain_to_named_tables():
    ns = _p13_ns()
    keep = {("customer", "profile"), ("customer", "address"), ("customer", "contact"),
            ("customer", "consent"), ("customer", "account"), ("customer", "preference"),
            ("customer", "household"), ("customer", "segment"),
            ("order", "header"), ("store", "location")}
    out = ns["_v440_restrict_shrink_domain"](keep, P13_BLOCK, None)
    cust = {p for (d, p) in out if d == "customer"}
    assert cust == {"profile", "address", "contact", "consent", "account"}, cust
    # other domains untouched
    assert ("order", "header") in out and ("store", "location") in out, out


def test_p13_safety_noop_when_no_directive():
    ns = _p13_ns()
    keep = {("customer", "profile"), ("order", "header")}
    assert ns["_v440_restrict_shrink_domain"](keep, "no minimalism directive here", None) == keep


def test_p13_safety_never_empties_domain_when_no_match():
    ns = _p13_ns()
    # kept customer products share NONE of the reviewer keep-list -> must return input unchanged
    keep = {("customer", "loyalty_profile"), ("customer", "cdp_segment"), ("order", "header")}
    assert ns["_v440_restrict_shrink_domain"](keep, P13_BLOCK, None) == keep
