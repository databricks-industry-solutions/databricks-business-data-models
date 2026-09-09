"""The Uninstall operation must remove exactly what its install created, and nothing
else. These tests bind to the shipped notebook cell, not to a copy of the logic.
"""
import json

import pytest

from installer_harness import (FakeMetastore, find_cell, load_uninstall,
                               run_main_cell, uninstall_config)


def manifest(**overrides):
    body = {
        "industry": "banking", "model_size": "mvm", "version": "v1",
        "catalog": "bank_cat", "cataloging_style": "One Catalog",
        "include_metrics": True, "installed_at": "2026-08-02T10:00:00",
        "catalogs": [{"name": "bank_cat", "created_by_installer": True}],
        "schemas": [["bank_cat", "customer"], ["bank_cat", "account"],
                    ["bank_cat", "_metrics"]],
        "samples": {"enabled": True, "rows": 10, "tables": 12, "written": 120},
    }
    body.update(overrides)
    return body


# ------------------------------------------------------------------ plan reading

def test_the_schema_list_is_read_off_the_plans_create_schema_statements():
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `bank_cat`.`customer`",
                       "CREATE SCHEMA `bank_cat`.`account`",
                       "create schema if not exists `other_cat`.`risk`"]}
    assert ns["plan_schemas"](plan) == [("bank_cat", "customer"),
                                        ("bank_cat", "account"),
                                        ("other_cat", "risk")]


def test_the_shipped_models_create_database_spelling_is_read():
    # Every model in data-models/ says CREATE DATABASE, not CREATE SCHEMA. Reading only
    # the latter made an uninstall drop `_metrics` and leave the whole model standing.
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": [
        "CREATE DATABASE IF NOT EXISTS `bank_cat`.`account` COMMENT 'Deposit accounts.'",
        "CREATE DATABASE IF NOT EXISTS `bank_cat`.`customer` COMMENT 'Parties.'"]}
    assert ns["plan_schemas"](plan) == [("bank_cat", "account"), ("bank_cat", "customer")]


def test_a_schema_statement_without_a_catalog_takes_the_target_catalog():
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": ["CREATE DATABASE IF NOT EXISTS `account`"]}
    assert ns["plan_schemas"](plan, "bank_cat") == [("bank_cat", "account")]


def test_a_schema_phase_that_parses_to_nothing_raises_instead_of_dropping_nothing():
    # The silent-no-op is the dangerous outcome: the job reports SUCCESS while the model
    # is still installed. Refusing loudly is the only safe answer.
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": ["CREATE SOMETHINGELSE `c`.`s`"]}
    with pytest.raises(Exception, match="refusing to continue"):
        ns["plan_schemas"](plan)


def test_a_repeated_create_schema_is_only_listed_once():
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `c`.`s`",
                       "CREATE SCHEMA IF NOT EXISTS `c`.`s`"]}
    assert ns["plan_schemas"](plan) == [("c", "s")]


def test_the_metrics_schema_is_included_only_when_metric_views_are_on():
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `c`.`s`"]}
    with_metrics = ns["installed_schemas"](
        uninstall_config(catalog="c", target_catalogs=["c"], include_metrics=True), plan)
    without = ns["installed_schemas"](
        uninstall_config(catalog="c", target_catalogs=["c"], include_metrics=False), plan)
    assert ("c", "_metrics") in with_metrics
    assert ("c", "_metrics") not in without


def test_the_install_schema_is_never_in_the_bulk_drop_list():
    # `_install` holds the live log sink, so it has to be dropped last, by hand.
    ns = load_uninstall(FakeMetastore({}))
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `c`.`s`"]}
    schemas = ns["installed_schemas"](uninstall_config(catalog="c",
                                                       target_catalogs=["c"]), plan)
    assert all(s != "_install" for _, s in schemas)


# ------------------------------------------------------------------ manifest

def test_the_manifest_records_which_catalogs_the_install_created():
    ns = load_uninstall(FakeMetastore({}))
    cfg = uninstall_config(catalog="new_cat", target_catalogs=["new_cat", "old_cat"])
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `new_cat`.`s`"]}
    body = ns["write_install_manifest"](cfg, plan, pre_existing={"old_cat"})
    created = {c["name"]: c["created_by_installer"] for c in body["catalogs"]}
    assert created == {"new_cat": True, "old_cat": False}


def test_the_manifest_is_written_to_the_install_volume_as_json():
    ns = load_uninstall(FakeMetastore({}))
    cfg = uninstall_config(catalog="c", industry="banking", model_size="mvm",
                           target_catalogs=["c"])
    ns["write_install_manifest"](cfg, {"schema": []}, pre_existing=set())
    path = "/Volumes/c/_install/logs/manifest_banking_mvm.json"
    assert path in ns["_written_files"]
    assert json.loads(ns["_written_files"][path])["industry"] == "banking"


def test_the_manifest_carries_the_sample_summary():
    ns = load_uninstall(FakeMetastore({}))
    body = ns["write_install_manifest"](
        uninstall_config(catalog="c", target_catalogs=["c"]), {"schema": []}, set(),
        {"enabled": True, "rows": 10, "tables": 12, "written": 120})
    assert body["samples"]["written"] == 120


def test_a_catalog_created_by_this_install_is_recorded_as_created_by_this_install():
    # setup_log_sink puts the log volume inside the target catalog, creating the catalog
    # when it is missing. Probing after that made every catalog look pre-existing, so the
    # uninstall kept catalogs the install had made.
    calls = {}
    recorded = {}

    def catalog_exists(catalog):
        # The catalog springs into existence the moment the log sink is set up.
        return "setup_log_sink" in calls.get("order", [])

    def on_manifest(cfg, plan, pre_existing, samples=None):
        recorded["pre_existing"] = set(pre_existing)

    run_main_cell({"enabled": False, "rows": 10}, calls=calls,
                  catalog_exists=catalog_exists, on_manifest=on_manifest)
    assert recorded["pre_existing"] == set(), \
        "the catalog did not exist before the run, so it must not be recorded as such"


# ------------------------------------------------------------------ uninstall

def test_uninstall_drops_exactly_the_schemas_the_manifest_records():
    spark = FakeMetastore({"bank_cat": {"customer", "account", "_metrics", "_install"}})
    ns = load_uninstall(spark, manifest=manifest())
    failures, _ = ns["uninstall"](uninstall_config())
    assert failures == []
    assert "bank_cat" not in spark.schemas   # catalog was created here, so it goes too


def test_a_schema_the_install_did_not_create_survives_the_uninstall():
    spark = FakeMetastore({"bank_cat": {"customer", "account", "_metrics", "_install",
                                        "my_own_work"}})
    ns = load_uninstall(spark, manifest=manifest())
    failures, _ = ns["uninstall"](uninstall_config())
    assert spark.schemas["bank_cat"] == {"my_own_work"}
    # The catalog cannot be dropped without taking that schema with it, so uninstall
    # refuses and says why rather than destroying the user's data.
    assert [f for f in failures if f[0] == "drop-catalog"]
    assert "my_own_work" in failures[0][2]


def test_a_catalog_that_existed_before_the_install_is_left_in_place():
    spark = FakeMetastore({"bank_cat": {"customer", "account", "_metrics", "_install"}})
    ns = load_uninstall(spark, manifest=manifest(
        catalogs=[{"name": "bank_cat", "created_by_installer": False}]))
    failures, _ = ns["uninstall"](uninstall_config())
    assert failures == []
    assert "bank_cat" in spark.schemas          # catalog kept
    assert spark.schemas["bank_cat"] == set()   # but emptied of what we installed


def test_without_a_manifest_the_plan_is_the_fallback_and_no_catalog_is_dropped():
    spark = FakeMetastore({"bank_cat": {"customer", "_metrics", "_install"}})
    plan = {"schema": ["CREATE SCHEMA IF NOT EXISTS `bank_cat`.`customer`"]}
    ns = load_uninstall(spark, manifest=None, plan=plan)
    failures, _ = ns["uninstall"](uninstall_config())
    assert failures == []
    assert "bank_cat" in spark.schemas
    assert spark.schemas["bank_cat"] == set()
    assert any("falling back to the model plan" in line for line in ns["_log_lines"])


def test_the_fallback_clears_a_real_model_whose_ddl_says_create_database():
    # The live failure: banking/mvm uninstalled with no manifest left all 18 domain
    # schemas standing and still reported SUCCESS, because the plan reader only knew
    # the CREATE SCHEMA spelling.
    domains = ["account", "customer", "ledger", "payment", "risk"]
    spark = FakeMetastore({"bank_cat": set(domains) | {"_metrics", "_install"}})
    plan = {"schema": ["CREATE DATABASE IF NOT EXISTS `bank_cat`.`%s` COMMENT 'x'" % d
                       for d in domains]}
    ns = load_uninstall(spark, manifest=None, plan=plan)
    failures, _ = ns["uninstall"](uninstall_config(catalog="bank_cat",
                                                   target_catalogs=["bank_cat"]))
    assert failures == []
    assert spark.schemas["bank_cat"] == set()


def test_multi_catalog_layouts_drop_every_catalog_they_created():
    spark = FakeMetastore({"cat_ops": {"sourcing", "_install"},
                           "cat_biz": {"retail", "_metrics"}})
    ns = load_uninstall(spark, manifest=manifest(
        catalog="cat_ops",
        catalogs=[{"name": "cat_ops", "created_by_installer": True},
                  {"name": "cat_biz", "created_by_installer": True}],
        schemas=[["cat_ops", "sourcing"], ["cat_biz", "retail"],
                 ["cat_biz", "_metrics"]]))
    failures, _ = ns["uninstall"](uninstall_config(
        catalog="cat_ops", target_catalogs=["cat_ops", "cat_biz"]))
    assert failures == []
    assert spark.schemas == {}


def test_a_schema_that_refuses_to_drop_is_reported_not_swallowed():
    spark = FakeMetastore({"bank_cat": {"customer", "account", "_metrics", "_install"}},
                          fail_on=["DROP SCHEMA IF EXISTS `bank_cat`.`account`"])
    ns = load_uninstall(spark, manifest=manifest())
    failures, _ = ns["uninstall"](uninstall_config())
    assert any(f[0] == "drop-schema" and "account" in f[1] for f in failures)


def test_a_schema_left_behind_is_caught_by_the_post_uninstall_check():
    # The DROP is accepted but the schema is still there: a silent no-op must not pass.
    class Stubborn(FakeMetastore):
        def sql(self, query):
            flat = " ".join(query.split())
            if flat.startswith("DROP SCHEMA IF EXISTS `bank_cat`.`customer`"):
                self.statements.append(flat)
                return FakeMetastore({}).sql("SELECT 1")
            return FakeMetastore.sql(self, query)

    spark = Stubborn({"bank_cat": {"customer", "account", "_metrics", "_install"}})
    ns = load_uninstall(spark, manifest=manifest(
        catalogs=[{"name": "bank_cat", "created_by_installer": False}]))
    failures, _ = ns["uninstall"](uninstall_config())
    assert any(f[0] == "verify" and "customer" in f[2] for f in failures)


def test_the_install_schema_is_dropped_after_the_model_schemas():
    spark = FakeMetastore({"bank_cat": {"customer", "account", "_metrics", "_install"}})
    ns = load_uninstall(spark, manifest=manifest())
    ns["uninstall"](uninstall_config())
    drops = [s for s in spark.statements if s.startswith("DROP SCHEMA")]
    assert drops[-1].endswith("`bank_cat`.`_install` CASCADE")


def test_information_schema_never_counts_as_leftover_content():
    # A catalog holding only information_schema is empty as far as the user is concerned.
    spark = FakeMetastore({"bank_cat": {"customer", "_install"}})
    ns = load_uninstall(spark, manifest=manifest(
        schemas=[["bank_cat", "customer"]],
        catalogs=[{"name": "bank_cat", "created_by_installer": True}]))
    failures, _ = ns["uninstall"](uninstall_config())
    assert failures == []
    assert "bank_cat" not in spark.schemas


# ------------------------------------------------------------------ wiring

def test_the_operation_widget_offers_install_and_uninstall():
    src = find_cell("dbutils.widgets.dropdown(\"operation\"")
    assert '"operation", "Install", ["Install", "Uninstall"]' in src


def test_a_local_install_does_not_have_to_name_a_repo_industry():
    # Installing a freshly generated model is the whole point of local_install, and no
    # repo folder describes it yet, so the industry list must not gate it.
    src = find_cell("def resolve_config")
    # On uninstall the industry is a manifest label, so the shipped-model assert now
    # carries an `or cfg["operation"] == "uninstall"` carve-out; install still asserts.
    assert 'assert industry in INDUSTRIES or cfg["operation"] == "uninstall"' in src
    guarded = src.split('if cfg["local_install"]:', 1)[1]
    assert "assert industry in INDUSTRIES" in guarded.split("else:", 1)[1]


def test_the_run_all_guard_lets_a_local_install_through():
    src = find_cell("def main()")
    assert 'not _wget("local_install", "").strip()' in src


def test_the_operation_is_forwarded_to_the_launched_job():
    src = find_cell("def launch_and_wait")
    assert '"operation": "Uninstall" if cfg["operation"] == "uninstall" else "Install"' in src


def test_the_uninstall_path_never_issues_an_unconditional_drop_catalog():
    src = find_cell("def uninstall(cfg)")
    for line in src.split("\n"):
        if "DROP CATALOG" in line and "spark.sql" in line:
            # the only executed DROP CATALOG must sit behind the created_by_installer gate
            assert "IF EXISTS" in line
    assert 'if not entry.get("created_by_installer"):' in src


@pytest.mark.parametrize("style,catalogs", [
    ("One Catalog", ["one"]),
    ("Catalog per Division", ["cat_operations", "cat_business"]),
    ("Catalog per Domain", ["cat_a", "cat_b", "cat_c"]),
])
def test_every_cataloging_style_round_trips_through_the_manifest(style, catalogs):
    spark = FakeMetastore({c: {"s%d" % i, "_install"} for i, c in enumerate(catalogs)})
    ns = load_uninstall(spark, manifest=manifest(
        catalog=catalogs[0], cataloging_style=style,
        catalogs=[{"name": c, "created_by_installer": True} for c in catalogs],
        schemas=[[c, "s%d" % i] for i, c in enumerate(catalogs)]))
    failures, _ = ns["uninstall"](uninstall_config(catalog=catalogs[0],
                                                   target_catalogs=catalogs))
    assert failures == []
    assert spark.schemas == {}
