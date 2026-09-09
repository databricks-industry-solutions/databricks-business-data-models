"""Widget-driven Uninstall of a CUSTOM (non-shipped) model must be authoritative.

Live repro (coffee_roastery, runs 975728446412601 / 1000670035526542): an Uninstall of a
model not in INDUSTRIES, launched from the widget with no `local_install`, returned SUCCESS
but dropped nothing. The main() first-run guard fired for the uninstall and returned before
resolve_config ran, so the manifest was never consulted. These tests bind to the shipped
notebook cells, not to a copy of the logic, and each fails on the pre-patch notebook.
"""
import glob as _glob_mod
import json
import re

import pytest

from installer_harness import (FakeMetastore, FakeResult, find_cell, load_uninstall,
                               uninstall_config)


# ------------------------------------------------------------------ Fix A: main() guard

def _run_guard(operation, model, local_install, industries=("airlines",)):
    """Exec main()'s body and run it with a resolve_config that raises a sentinel, so a
    test can tell whether the first-run guard let the operation through (sentinel raised)
    or short-circuited with the 'please select an industry' return (no sentinel)."""
    src = find_cell("def main()").rstrip()
    assert src.endswith("main()")
    body = src[:-len("main()")]
    logs = []

    class _ReachedResolveConfig(Exception):
        pass

    widgets = {"operation": operation, "model": model, "local_install": local_install}
    ns = {
        "__name__": "guard_probe",
        "_wget": lambda k, d="": widgets.get(k, d),
        "INDUSTRIES": list(industries),
        "log": lambda m: logs.append(str(m)),
        "resolve_config": lambda: (_ for _ in ()).throw(_ReachedResolveConfig()),
    }
    exec(compile(body, "<main-cell>", "exec"), ns)
    reached = False
    try:
        ns["main"]()
    except _ReachedResolveConfig:
        reached = True
    return reached, logs


def test_the_run_all_guard_lets_an_uninstall_of_a_custom_model_through():
    reached, logs = _run_guard("Uninstall", "coffee_roastery", "")
    assert reached, "uninstall must proceed to resolve_config, not early-return as a no-op"
    assert not any("Please select an industry" in l for l in logs)


def test_the_guard_still_blocks_an_install_of_an_unknown_model_without_local_install():
    reached, logs = _run_guard("Install", "coffee_roastery", "")
    assert not reached
    assert any("Please select an industry" in l for l in logs)


def test_the_guard_lets_an_install_of_a_shipped_model_through():
    reached, _ = _run_guard("Install", "airlines", "")
    assert reached


def test_the_guard_lets_a_local_install_through_regardless_of_operation():
    reached, _ = _run_guard("Install", "coffee_roastery", "/Volumes/x/model")
    assert reached


# ------------------------------------------------------------------ Fix C: manifest scan

def _load_cell9_real_io():
    """Exec the uninstall cell with real filesystem I/O so the catalog scan can be driven
    off a temp directory via a monkeypatched glob."""
    import datetime as _datetime
    import os as _os
    import time as _time

    ns = {
        "__name__": "uninstall_cell_real_io",
        "spark": FakeMetastore({}), "log": lambda m: None,
        "json": json, "os": _os, "time": _time, "datetime": _datetime, "_re": re,
        "open": open, "run_phase": lambda *a, **k: [],
        "retry_failed": lambda f, passes=3: f,
        "build_plan": lambda cfg: {"schema": []},
        "_flush_log_durable": lambda: None, "_SINK": {"path": None},
    }
    exec(compile(find_cell("def uninstall(cfg)"), "<uninstall-cell>", "exec"), ns)
    return ns


def test_read_install_manifest_recovers_a_manifest_by_scanning_the_catalog(tmp_path, monkeypatch):
    ns = _load_cell9_real_io()
    recovered = tmp_path / "manifest_custom_label_mvm.json"
    recovered.write_text(json.dumps(
        {"industry": "custom_label", "model_size": "mvm",
         "schemas": [["c", "s"]], "catalogs": []}))
    # exact path is absent, so the by-catalog scan is the only way to find the manifest
    ns["_manifest_path"] = lambda cfg: str(tmp_path / "not_here.json")
    monkeypatch.setattr(_glob_mod, "glob", lambda pattern: [str(recovered)])
    body = ns["read_install_manifest"]({"catalog": "c", "industry": "x", "model_size": "mvm"})
    assert body is not None and body["industry"] == "custom_label"


def test_read_install_manifest_prefers_the_exact_path_over_the_scan(tmp_path):
    ns = _load_cell9_real_io()
    exact = tmp_path / "exact.json"
    exact.write_text(json.dumps({"industry": "exact_hit"}))
    ns["_manifest_path"] = lambda cfg: str(exact)
    body = ns["read_install_manifest"]({"catalog": "c", "industry": "x", "model_size": "mvm"})
    assert body["industry"] == "exact_hit"


# ------------------------------------------------------------------ Fix D: loud zero-op

def test_uninstall_fails_loud_when_it_resolves_no_schemas_but_the_catalog_has_content():
    # The exact silent-no-op the live run hit: nothing to drop, catalog still full, SUCCESS.
    spark = FakeMetastore({"cust_cat": {"orders", "_install"}})
    ns = load_uninstall(spark, manifest=None, plan={"schema": []})
    with pytest.raises(Exception, match="still holds"):
        ns["uninstall"](uninstall_config(catalog="cust_cat", target_catalogs=["cust_cat"],
                                         include_metrics=False))
    assert "orders" in spark.schemas["cust_cat"], "nothing may be dropped before we bail"


def test_uninstall_with_a_real_plan_does_not_trip_the_zero_schema_guard():
    spark = FakeMetastore({"cust_cat": {"orders", "_install"}})
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `cust_cat`.`orders`"]}
    ns = load_uninstall(spark, manifest=None, plan=plan)
    failures, _ = ns["uninstall"](uninstall_config(
        catalog="cust_cat", target_catalogs=["cust_cat"], include_metrics=False))
    assert failures == []
    assert spark.schemas["cust_cat"] == set()


def test_a_clean_catalog_with_no_recorded_schemas_is_a_quiet_success():
    # 0 schemas AND nothing left in the catalog is a legitimate no-op, not an error.
    spark = FakeMetastore({"cust_cat": {"_install"}})
    ns = load_uninstall(spark, manifest=None, plan={"schema": []})
    failures, _ = ns["uninstall"](uninstall_config(
        catalog="cust_cat", target_catalogs=["cust_cat"], include_metrics=False))
    assert failures == []
    assert any("already clean" in l for l in ns["_log_lines"])


# ------------------------------------------------------------------ wiring (smoke)

def test_the_manifest_catalog_scan_alias_is_wired():
    assert "uninstall-manifest-catalog-scan FIRED" in find_cell("def read_install_manifest")


def test_the_zero_schema_guard_alias_is_wired():
    assert "uninstall-zero-schema-guard" in find_cell("def uninstall(cfg)")


def test_resolve_config_treats_industry_as_a_label_on_uninstall():
    assert 'assert industry in INDUSTRIES or cfg["operation"] == "uninstall"' \
        in find_cell("def resolve_config")


def test_the_guard_carveout_for_uninstall_is_in_main():
    assert '_wget("operation", "Install").strip().lower() != "uninstall"' \
        in find_cell("def main()")
