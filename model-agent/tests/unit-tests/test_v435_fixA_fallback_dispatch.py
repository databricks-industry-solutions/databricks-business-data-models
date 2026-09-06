"""v4.3.5 FIX A behavioral test (alias=vov-fallback-dispatch).

Root cause: VOV's deterministic pass _v251_apply_priority_deterministic whitelisted only
connect_table/add_attribute/fk/rename/retype. Reviewer directives for description rewrites
(P2 vendor-neutral) and SCD-2 history columns (P10) fell through to
`unsupported-deterministic-action`, then churned on the LLM path. FIX A routes them through
the EXISTING mutation-registry DATA (_COLUMN_TEMPLATES / _LEGACY_ACTION_MAP + apply_mutation_command
semantics) so they land deterministically.

Fail-pre / pass-post: on pre-patch HEAD both actions return unsupported and the model is
unchanged -> the state assertions raise. Post-patch the description is set and the 4 scd2
columns are appended.
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
                 {"name": "profile_id", "type": "BIGINT", "description": ""},
                 {"name": "email", "type": "STRING", "description": "old vendor-specific note"},
             ]},
        ]},
        {"name": "sales", "products": [
            {"name": "order", "primary_key": "order_id",
             "attributes": [{"name": "order_id", "type": "BIGINT", "description": ""}]},
        ]},
    ]}}


def test_fixA_update_description_sets_description():
    ns = _ns()
    fn = ns["_v251_apply_priority_deterministic"]
    m = _model()
    ok, status = fn(
        {"action": "update_description", "target": "customer.profile.email"},
        {"new_description": "Primary contact email address (vendor-neutral)."},
        m, _NullLogger())
    assert ok is True, status
    attr = m["model"]["domains"][0]["products"][0]["attributes"][1]
    assert attr["description"] == "Primary contact email address (vendor-neutral)."


def test_fixA_add_scd2_history_appends_template_columns():
    ns = _ns()
    fn = ns["_v251_apply_priority_deterministic"]
    m = _model()
    ok, status = fn(
        {"action": "add_scd2_history", "target": "sales.order"},
        {}, m, _NullLogger())
    assert ok is True, status
    cols = {a["name"] for a in m["model"]["domains"][1]["products"][0]["attributes"]}
    for expected in ("effective_from", "effective_to", "is_current", "row_hash"):
        assert expected in cols, "scd2 column %r not appended" % expected
