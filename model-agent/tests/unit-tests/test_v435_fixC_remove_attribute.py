"""v4.3.5 FIX C behavioral test (alias=vov-remove-attribute).

Root cause: no deterministic path removed a named attribute, so reviewer "remove
redundant/derived/duplicated column" directives (P4/P5) never landed. FIX C adds a
remove_attribute branch that drops the column and scrubs inbound FK refs, refusing to drop
the PK and idempotent when already absent.

Fail-pre / pass-post: pre-patch remove_attribute returns unsupported and the column stays
present (and any inbound FK stays), failing the assertions. Post-patch the column is gone and
the inbound FK is scrubbed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v435_helpers import concat_source, slice_functions, module_dicts, _NullLogger

_FNS = [
    "_v251_model_root", "_v251_find_domain", "_v251_product_list",
    "_v251_find_product", "_v251_find_attribute_row", "_v251_iter_attribute_rows",
    "_v327_infer_coltype", "_v251_apply_priority_deterministic",
]


def _ns():
    src = concat_source()
    dicts = module_dicts(["_COLUMN_TEMPLATES", "_LEGACY_ACTION_MAP"], src)
    return slice_functions(_FNS, src, extra_globals=dict(dicts))


def _model():
    return {"model": {"domains": [
        {"name": "customer", "products": [
            {"name": "profile", "primary_key": "profile_id",
             "attributes": [
                 {"name": "profile_id", "type": "BIGINT"},
                 {"name": "email_opt_in_flag", "type": "BOOLEAN"},
                 {"name": "consent_id", "type": "BIGINT", "foreign_key_to": "customer.consent.consent_id"},
             ]},
            {"name": "consent", "primary_key": "consent_id",
             "attributes": [{"name": "consent_id", "type": "BIGINT"}]},
        ]},
        {"name": "sales", "products": [
            {"name": "order", "primary_key": "order_id",
             "attributes": [
                 {"name": "order_id", "type": "BIGINT"},
                 # inbound FK that points at the column we will remove
                 {"name": "opt_in_ref", "type": "BOOLEAN",
                  "foreign_key_to": "customer.profile.email_opt_in_flag"},
             ]},
        ]},
    ]}}


def test_fixC_remove_attribute_drops_column_and_scrubs_inbound_fk():
    ns = _ns()
    fn = ns["_v251_apply_priority_deterministic"]
    m = _model()
    ok, status = fn(
        {"action": "remove_attribute", "target": "customer.profile.email_opt_in_flag"},
        {}, m, _NullLogger())
    assert ok is True and status == "applied", status
    prof_cols = {a["name"] for a in m["model"]["domains"][0]["products"][0]["attributes"]}
    assert "email_opt_in_flag" not in prof_cols, "column not removed"
    inbound = m["model"]["domains"][1]["products"][0]["attributes"][1]
    assert not inbound.get("foreign_key_to"), "inbound FK not scrubbed"


def test_fixC_refuses_to_drop_primary_key():
    ns = _ns()
    fn = ns["_v251_apply_priority_deterministic"]
    m = _model()
    ok, status = fn(
        {"action": "remove_attribute", "target": "customer.profile.profile_id"},
        {}, m, _NullLogger())
    assert ok is False and status == "refuse-remove-pk", status
