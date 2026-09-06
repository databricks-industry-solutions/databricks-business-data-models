"""v4.3.6 FIX G behavioral tests — directive normalizer + multi-target expander.

ROOT CAUSE this fixes: human reviewer directives arrive as DESCRIPTIVE, MULTI-TARGET
VReqs (intent="deduplicate_consent", body="remove customer.profile.email_opt_in_flag,
..."). Their intent first-word is not a canonical verb, so `_vov_vreq_to_priority`
returns None and the whole directive falls to the empty-diff-prone LLM sandbox — which
is exactly why the v4.3.5 cell-60 remove_attribute/retype handlers fired 0 times on the
live retail VOV run. `_v436_expand_vreq_to_priorities` classifies the canonical action
from the body verb and expands into one canonical single-target priority per explicit
FQN, feeding the SAME cell-60 handlers.

FAIL-PRE proof: on pre-patch HEAD the module-level def `_v436_expand_vreq_to_priorities`
does not exist, so `slice_functions` raises LookupError and every test below fails.
PASS-POST: the def exists and the expansions are exact.
"""
import re

from v435_helpers import concat_source, slice_functions


class _V:
    def __init__(self, intent="", quote="", target="", vid="VREQ-T"):
        self.intent = intent
        self.source_quote = quote
        self.target = target
        self.vreq_id = vid


def _expander():
    src = concat_source()
    ns = slice_functions(["_v436_expand_vreq_to_priorities"], src, extra_globals={"re": re})
    return ns["_v436_expand_vreq_to_priorities"]


_P4 = ("Make customer.consent the SINGLE SOURCE OF TRUTH. remove "
       "customer.profile.email_opt_in_flag, customer.profile.sms_opt_in_flag, "
       "customer.profile.marketing_consent_flag, customer.profile.gdpr_consent_flag, "
       "customer.profile.ccpa_opt_out_flag, customer.account.marketing_opt_in, "
       "customer.account.data_sharing_consent, customer.account.marketing_opt_in_date, "
       "customer.account.marketing_opt_out_date, customer.contact.opt_in_marketing, "
       "customer.contact.opt_in_transactional, customer.contact.opt_in_date, "
       "customer.contact.opt_out_date")

_P1 = ("fix data-type correctness bugs. "
       "customer.contact.contact_value -> STRING, customer.preference.preference_value -> STRING, "
       "customer.profile.nps_score -> INT, customer.contact.bounce_count -> INT, "
       "customer.payment_method.expiry_month -> SMALLINT, customer.payment_method.expiry_year -> SMALLINT")


def test_fixG_p4_expands_to_13_remove_attribute_priorities():
    fn = _expander()
    out = fn(_V("deduplicate_consent", _P4, vid="VREQ-004"))
    assert len(out) == 13, "expected 13 removes, got %d" % len(out)
    assert {p["action"] for p in out} == {"remove_attribute"}
    assert "customer.profile.email_opt_in_flag" in {p["target"] for p in out}
    assert all(p["vreq_id"] == "VREQ-004" for p in out)


def test_fixG_p1_expands_to_retype_with_correct_types():
    fn = _expander()
    out = fn(_V("retype_attribute", _P1, vid="VREQ-001"))
    assert {p["action"] for p in out} == {"retype_attribute"}
    by_t = {p["target"]: p["target_state"] for p in out}
    assert by_t["customer.contact.contact_value"] == "STRING"
    assert by_t["customer.profile.nps_score"] == "INT"
    assert by_t["customer.payment_method.expiry_month"] == "SMALLINT"


def test_fixG_fk_removal_directive_is_not_expanded():
    # An FK-removal directive must NOT be turned into remove_attribute (would drop a
    # real business column). Guard keeps it on the existing remove_fk path.
    fn = _expander()
    out = fn(_V("remove_fk", "remove the foreign key customer.order.customer_id", vid="VREQ-X"))
    assert out == [], "FK-removal must not expand to remove_attribute: %r" % out


def test_fixG_holistic_description_directive_is_not_expanded():
    # No removal/retype verb + no explicit FQN -> stays on the LLM path (returns []).
    fn = _expander()
    out = fn(_V("vendor_neutral_descriptions",
               "strip vendor and product names from all column and table descriptions", vid="VREQ-002"))
    assert out == [], "holistic description directive must not expand: %r" % out
