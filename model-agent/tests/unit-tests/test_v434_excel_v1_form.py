import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notebook_source_util import (
    exec_function_namespace,
    notebook_concat_source,
    slice_function_source,
)

# Exact v1 per-domain data-sheet column form (13 columns, in order).
V1_COLUMNS = [
    "subdomain", "product", "attribute", "business_glossary_term", "type",
    "tags", "value_regex", "foreign_key_to", "description", "reference",
    "is_primary_key", "llm_fk_skip", "llm_fk_skip_reason",
]

# The 9 keys the v2 exporter drift appended to the per-domain data sheets.
DRIFT_COLUMNS = [
    "nullable", "is_nullable", "default_value", "pii_subtype", "data_type",
    "sample_values", "classification", "is_natural_key", "value_range",
]


class FakeDF:
    """A minimal column-oriented table modelling ONLY the DataFrame operations the
    exporter helper relies on: .copy(), .columns, `col in .columns`, df[col]=scalar
    (append/broadcast), and df[[cols]] (ordered projection). The suite runs without
    pandas (PEP 668), so this stand-in exercises the helper's column-form contract
    faithfully and deterministically."""

    def __init__(self, rows):
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        self._cols = cols
        self._rows = [dict(r) for r in rows]

    def copy(self):
        return FakeDF([dict(r) for r in self._rows])

    @property
    def columns(self):
        return list(self._cols)

    def __setitem__(self, key, value):
        if key not in self._cols:
            self._cols.append(key)
        for r in self._rows:
            r[key] = value

    def __getitem__(self, key):
        if isinstance(key, list):
            out = FakeDF([])
            out._cols = list(key)
            out._rows = [{c: r.get(c, "") for c in key} for r in self._rows]
            return out
        return [r.get(key, "") for r in self._rows]


def _load_helper():
    return exec_function_namespace("_excel_v1_form_dataframe")["_excel_v1_form_dataframe"]


def _drifted_frame():
    """A per-domain attribute frame carrying the v2 runtime keys (base + drift +
    the two fk-skip fields) plus columns the exporter drops (business/domain/_x)."""
    row = {
        "business": "acme", "domain": "sales", "column_name": "order_id",
        "subdomain": "orders", "product": "order", "attribute": "order_id",
        "business_glossary_term": "Order ID", "type": "BIGINT",
        "tags": "primary_key,dbx_x=1", "value_regex": "", "foreign_key_to": "",
        "description": "PK", "reference": "ISO", "is_primary_key": "Y",
        "llm_fk_skip": "true", "llm_fk_skip_reason": "lookup",
        "nullable": "N", "is_nullable": False, "default_value": "",
        "pii_subtype": "", "data_type": "delta", "sample_values": "1|2|3",
        "classification": "internal", "is_natural_key": "N", "value_range": "",
        "_sort_key": "(0,)", "version": "2", "model_scope": "ecm",
    }
    return FakeDF([row, dict(row, attribute="amount", is_primary_key="")])


def _old_dynamic_columns(group_df_copy):
    """Reproduce the pre-v4.3.4 column derivation verbatim so the test proves the
    old path drifts to >13 columns (§8.10 fail-pre-patch)."""
    preferred_column_order = [
        "subdomain", "product", "attribute", "business_glossary_term", "type",
        "tags", "value_regex", "foreign_key_to", "description", "reference",
    ]
    all_available_columns = list(group_df_copy.columns)
    columns_to_exclude = [
        "business", "domain", "column_name", "version", "model_scope",
        "operations", "functions", "function",
    ]
    columns_to_exclude.extend([c for c in all_available_columns if c.startswith("_")])
    for c in columns_to_exclude:
        if c in all_available_columns:
            all_available_columns.remove(c)
    final = [c for c in preferred_column_order if c in all_available_columns]
    final.extend([c for c in all_available_columns if c not in final])
    return final


def test_prepatch_dynamic_derivation_drifts_beyond_13_cols():
    """The old exporter appended every non-excluded runtime key, so a v2 frame
    produced far more than the 13-col v1 form and leaked the drift columns."""
    cols = _old_dynamic_columns(_drifted_frame())
    assert len(cols) > 13, cols
    leaked = [c for c in DRIFT_COLUMNS if c in cols]
    assert leaked, "expected drift columns to leak in the pre-patch derivation"


def test_patched_helper_emits_exactly_13_col_v1_form_in_order():
    helper = _load_helper()
    out = helper(_drifted_frame())
    assert list(out.columns) == V1_COLUMNS, list(out.columns)
    assert len(out.columns) == 13
    assert not [c for c in DRIFT_COLUMNS if c in out.columns]
    # real data preserved for the 13 kept columns
    assert list(out["attribute"]) == ["order_id", "amount"]
    assert list(out["llm_fk_skip"]) == ["true", "true"]


def test_patched_helper_fills_missing_target_columns_empty():
    """An 11-col scope (no llm_fk_skip / llm_fk_skip_reason) is still lifted to
    exactly the 13-col form with the missing columns created empty."""
    helper = _load_helper()
    df = FakeDF([{
        "subdomain": "orders", "product": "order", "attribute": "order_id",
        "business_glossary_term": "Order ID", "type": "BIGINT", "tags": "",
        "value_regex": "", "foreign_key_to": "", "description": "PK",
        "reference": "", "is_primary_key": "Y",
    }])
    out = helper(df)
    assert list(out.columns) == V1_COLUMNS
    assert list(out["llm_fk_skip"]) == [""]
    assert list(out["llm_fk_skip_reason"]) == [""]


def test_helper_emits_fired_log_line():
    helper = _load_helper()
    seen = []

    class _L:
        def info(self, m):
            seen.append(m)

    helper(_drifted_frame(), logger=_L(), label="acme orders")
    assert any(
        "[excel-v1-form-restore FIRED v4.3.4]" in m
        and "emitted 13-col v1 form" in m
        and "acme orders" in m
        for m in seen
    ), seen


def test_exporter_calls_helper_not_dynamic_extend():
    """Guard against the fix regressing to dead code (§8.4): the production
    exporter must call the helper and must no longer build the dynamic
    final_ordered_cols column list."""
    exporter_src = slice_function_source("step_save_to_excel")
    assert "_excel_v1_form_dataframe(" in exporter_src
    assert "final_ordered_cols" not in exporter_src
    assert "def _excel_v1_form_dataframe(" in notebook_concat_source()
