"""v4.4.7 behavioral tests: deterministic reviewer-NAMED-artifact enforcement in
_v441_reviewer_finalization (P8 pci vault table, P10 SCD-2 named columns, P1 rehome/rename-aware
retype). These are the fix for the retail v4.4.6 P8/P10 regression: the reviewer NAMED
finance.payment_instrument + effective_start_date/effective_end_date, but the non-deterministic LLM
VOV loop landed them run-to-run (v4.4.5 yes, v4.4.6 no). §8.10: each test FAILS on pre-patch HEAD
(the v4.4.6 function has no P1/P8/P10 blocks) and PASSES post-patch (working tree).
"""
import json
import os
import re
import subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
NB = os.path.join(REPO, "agent", "dbx_vibe_modelling_agent.ipynb")
REV = os.path.join(REPO, "tests", "unit-tests", "fixtures", "retail_reviewer_directives.txt")


def _extract_v441(nb_json_text):
    nb = json.loads(nb_json_text)
    for c in nb["cells"]:
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source") or [])
        if "def _v441_reviewer_finalization" in src:
            lines = src.split("\n")
            start = next(i for i, l in enumerate(lines) if l.startswith("def _v441_reviewer_finalization"))
            end = next((i for i, l in enumerate(lines) if i > start and l.startswith("def ") and not l.startswith("    ")), len(lines))
            ns = {"re": re}
            exec("\n".join(lines[start:end]), ns)
            return ns["_v441_reviewer_finalization"]
    raise RuntimeError("_v441_reviewer_finalization not found")


def _fn_working_tree():
    with open(NB, "r") as f:
        return _extract_v441(f.read())


# Pre-patch reference is pinned to the v4.4.6 commit (766c3f6) that shipped the retail P8/P10
# regression, NOT to a moving HEAD: once v4.4.7 is committed HEAD becomes the PATCHED function and
# the fail-pre check would compare the fix against itself (tautology). 766c3f6 is the durable anchor.
_V446_SHA = "766c3f6"


def _fn_prepatch():
    txt = subprocess.check_output(
        ["git", "show", f"{_V446_SHA}:agent/dbx_vibe_modelling_agent.ipynb"], cwd=REPO).decode()
    return _extract_v441(txt)


REVIEWER_TEXT = (
    "REVIEWER-PRIORITY 1 - retype_attribute: fix data-type correctness bugs in the customer domain.\n"
    "  - customer.contact.contact_value -> STRING (currently DECIMAL)\n"
    "  - customer.preference.preference_value -> STRING (currently DECIMAL)\n"
    "  - customer.payment_method.usage_count -> INT\n"
    "REVIEWER-PRIORITY 8 - pci_scope_isolation: tokenized payment instruments must not sit on customer master tables.\n"
    "Move customer.payment_method (including cardholder_name and card fields) into a vault-adjacent finance domain table (e.g. finance.payment_instrument) so non-payment workloads stay out of PCI scope.\n"
    "REVIEWER-PRIORITY 10 - scd_history_on_master: master tables customer.profile and customer.account must carry change history (SCD-2 effective_start_date/effective_end_date/status or CDC).\n"
)


def _fixture():
    """Model dict mimicking the v4.4.6 MISS state: payment_method (not payment_instrument) in finance,
    SCD from/to (not start/end) on masters, DECIMAL free-text cols."""
    return {"model": {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "profile_id", "attributes": [
                {"name": "profile_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "effective_from", "type": "DATE"}, {"name": "effective_to", "type": "DATE"},
                {"name": "is_current", "type": "BOOLEAN"}, {"name": "profile_status", "type": "STRING"},
                {"name": "payment_method_id", "type": "BIGINT",
                 "foreign_key_to": "finance.payment_method.payment_method_id", "tags": "foreign_key"}]},
            {"name": "account", "primary_key": "account_id", "attributes": [
                {"name": "account_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "effective_from", "type": "DATE"}, {"name": "effective_to", "type": "DATE"},
                {"name": "account_status", "type": "STRING"}]},
            {"name": "contact", "primary_key": "contact_id", "attributes": [
                {"name": "contact_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "value", "type": "DECIMAL(18,2)"}]},
            {"name": "communication_preference", "primary_key": "communication_preference_id", "attributes": [
                {"name": "communication_preference_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "preference_value", "type": "DECIMAL(18,2)"}]},
        ]},
        {"name": "finance", "products": [
            {"name": "payment_method", "primary_key": "payment_method_id", "attributes": [
                {"name": "payment_method_id", "type": "BIGINT", "is_primary_key": True},
                {"name": "cardholder_name", "type": "STRING"},
                {"name": "card_brand", "type": "STRING", "value_regex": "visa|mc"},
                {"name": "usage_count", "type": "DECIMAL(18,2)"}]},
        ]},
    ]}}


def _find(model, dom, prod):
    for d in model["model"]["domains"]:
        if d["name"] == dom:
            for p in (d.get("products") or []):
                if p["name"] == prod:
                    return p
    return None


def _cols(p):
    return {a["name"].upper(): (a.get("type") or "").upper() for a in (p.get("attributes") or [])} if p else {}


def _measure(fn):
    m = _fixture()
    fn(m, REVIEWER_TEXT, None)
    pi = _find(m, "finance", "payment_instrument")
    prof = _find(m, "customer", "profile")
    acct = _find(m, "customer", "account")
    contact = _find(m, "customer", "contact")
    cp = _find(m, "customer", "communication_preference")
    return {
        "p8_vault": bool(pi) and _find(m, "finance", "payment_method") is None,
        "p10_profile": "EFFECTIVE_START_DATE" in _cols(prof) and "EFFECTIVE_END_DATE" in _cols(prof),
        "p10_account": "EFFECTIVE_START_DATE" in _cols(acct) and "EFFECTIVE_END_DATE" in _cols(acct),
        "p1_contact": _cols(contact).get("VALUE", "").startswith("STRING"),
        "p1_pref": _cols(cp).get("PREFERENCE_VALUE", "").startswith("STRING"),
        "p1_usage": (_cols(pi).get("USAGE_COUNT", "") if pi else "").startswith("INT"),
    }


# ---------------- pass-post (working tree = v4.4.7) ----------------

def test_p8_pci_vault_named_post():
    assert _measure(_fn_working_tree())["p8_vault"], "v4.4.7 must rename the finance vault table to reviewer-named payment_instrument"


def test_p10_scd_named_columns_post():
    r = _measure(_fn_working_tree())
    assert r["p10_profile"] and r["p10_account"], "v4.4.7 must materialize reviewer-named effective_start_date/effective_end_date on both masters"


def test_p1_rehome_rename_aware_retype_post():
    r = _measure(_fn_working_tree())
    assert r["p1_contact"] and r["p1_pref"] and r["p1_usage"], "v4.4.7 must retype renamed/rehomed reviewer columns to STRING/INT"


# ---------------- fail-pre (v4.4.6 @ 766c3f6 has no P1/P8/P10 blocks) ----------------

def test_regression_absent_on_prepatch():
    r = _measure(_fn_prepatch())
    # the v4.4.6 function lacks all three enforcement blocks: none of the reviewer-named artifacts land
    assert not r["p8_vault"], "PRE-PATCH SANITY: v4.4.6 must NOT rename to payment_instrument (else test is tautological)"
    assert not (r["p10_profile"] and r["p10_account"]), "PRE-PATCH SANITY: v4.4.6 must NOT add named SCD cols"
    assert not (r["p1_contact"] and r["p1_pref"]), "PRE-PATCH SANITY: v4.4.6 must NOT retype the DECIMAL free-text cols"
