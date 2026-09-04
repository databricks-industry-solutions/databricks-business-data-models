"""B5 — the three model_deviation demo signals live in the bronze.

TRIM columns exist but are 100% empty (-> drop_null_columns fires); the
pricing-condition source is absent (-> the two condition tables have no source).
"""
import pandas as pd, pathlib
OUT = pathlib.Path(__file__).parents[1] / "output" / "sap_sd"

_SCHED_TRIM = ["is_jis", "is_jit", "is_kanban_triggered", "takt_time_seconds",
               "cumulative_ordered_quantity", "cumulative_delivered_quantity"]
_ATP_TRIM = ["is_ctp_capacity_checked", "work_center_code", "replenishment_lead_time_days",
             "mrp_element_type", "supply_source_reference"]
_CPQ_TRIM = ["cooling_type", "hazardous_area_classification", "communication_protocol",
             "software_version", "certification_marks"]


def _all_empty(table, cols):
    df = pd.read_csv(OUT / f"{table}.csv", dtype=str)
    for c in cols:
        assert c in df.columns, f"{table}.{c} missing"
        assert df[c].fillna("").eq("").all(), f"{table}.{c} not all-empty"


def test_sched_trim_columns_present_but_null():
    _all_empty("sched_agreement", _SCHED_TRIM)


def test_atp_trim_columns_present_but_null():
    _all_empty("atp_log", _ATP_TRIM)


def test_cpq_trim_columns_present_but_null():
    _all_empty("cpq_config", _CPQ_TRIM)


def test_no_pricing_condition_source():
    assert not (OUT / "prcd_elements.csv").exists()
    assert not (OUT / "konv.csv").exists()
