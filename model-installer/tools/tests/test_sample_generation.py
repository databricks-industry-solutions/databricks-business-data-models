"""Behavioural tests for sample installation through the model installer.

Every test binds to the notebook's own sample cell, so a passing suite is evidence
about what the installer ships, not about a copy of it.
"""
import datetime
import decimal
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from installer_harness import (  # noqa: E402
    ENGINE, FakeSpark, cell_source, find_cell, load_engine, notebook_cells,
    run_main_cell, sample_config, shop_fixture)

HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def ns():
    return load_engine()


@pytest.fixture
def spark():
    return FakeSpark(shop_fixture())


@pytest.fixture
def populated(ns, spark):
    cfg = sample_config()
    entities = ns["read_installed_model"](spark, ["demo"], None)
    ns["generate_all_keys"](entities, cfg["rows"], cfg["seed"])
    for entity in entities.values():
        ns["generate_rows"](entity, entities, cfg["rows"], cfg["seed"])
    return entities


def entity_of(entities, schema, table):
    return entities["demo.%s.%s" % (schema, table)]


# =====================================================================================
# the two widgets the operator sees
# =====================================================================================

def test_generate_samples_widget_defaults_to_no():
    source = find_cell("INSTALLER_DEFAULTS")
    match = re.search(r'dbutils\.widgets\.dropdown\(\s*"generate_samples",\s*"([^"]+)",'
                      r'\s*\[([^\]]+)\]', source)
    assert match, "the installer must expose a generate_samples dropdown"
    assert match.group(1) == "No"
    assert [v.strip().strip('"') for v in match.group(2).split(",")] == ["No", "Yes"]


def test_sample_rows_widget_offers_the_five_choices_and_defaults_to_10():
    source = find_cell("INSTALLER_DEFAULTS")
    match = re.search(r'dbutils\.widgets\.dropdown\(\s*"sample_rows",\s*"([^"]+)",'
                      r'\s*\[([^\]]+)\]', source)
    assert match, "the installer must expose a sample_rows dropdown"
    assert match.group(1) == "10"
    assert [v.strip().strip('"') for v in match.group(2).split(",")] == \
        ["5", "10", "20", "50", "100"]


def test_the_widgets_are_forwarded_to_the_launched_job():
    """The install runs as a job, so a widget the launcher drops is a widget ignored."""
    source = find_cell("def main()")
    forwarded = source[source.index("    widgets = {"):source.index("    p = INSTALLER_TAG_PREFIX")]
    for key in ("generate_samples", "sample_rows", "sample_seed", "sample_llm"):
        assert '"%s"' % key in forwarded, "%s is not forwarded to the job" % key


def test_config_reads_no_as_disabled_and_yes_with_the_chosen_rows(ns):
    widgets = {"generate_samples": "No", "sample_rows": "50"}
    cfg = ns["resolve_sample_config"](lambda k, d="": widgets.get(k, d))
    assert cfg["enabled"] is False

    widgets["generate_samples"] = "Yes"
    cfg = ns["resolve_sample_config"](lambda k, d="": widgets.get(k, d))
    assert cfg["enabled"] is True and cfg["rows"] == 50


def test_an_unusable_row_count_falls_back_to_ten(ns):
    for bad in ("", "abc", "0", "-5"):
        cfg = ns["resolve_sample_config"](
            lambda k, d="", b=bad: {"generate_samples": "Yes", "sample_rows": b}.get(k, d))
        assert cfg["rows"] == 10, bad


# =====================================================================================
# reading the installed model back out of information_schema
# =====================================================================================

def test_the_installed_keys_and_relationships_are_read_from_the_catalog(ns, spark):
    entities = ns["read_installed_model"](spark, ["demo"], None)
    assert len(entities) == len(shop_fixture()["tables"])
    order = entity_of(entities, "sales", "order")
    assert order.pk == ["order_id"]
    assert [c["name"] for c in order.columns][0] == "order_id"
    assert order.fks[0]["parent"] == "demo.sales.customer"

    line_event = entity_of(entities, "ops", "line_event")
    composite = line_event.fks[0]
    assert composite["columns"] == ["order_id", "line_no"]
    assert composite["parent_columns"] == ["order_id", "line_no"]


def test_a_cross_schema_foreign_key_is_discovered(ns, spark):
    """The read must not lose a foreign key whose parent lives in another schema.

    Unity Catalog reports constraint_column_usage.constraint_schema as the REFERENCED
    table's schema, so a read that correlates it with the foreign key's own schema drops
    every cross-schema relationship (338 of 506 on the restaurants model) and the
    generator then invents values for those columns instead of borrowing real keys.
    """
    entities = ns["read_installed_model"](spark, ["demo"], None)
    shipment = entity_of(entities, "ops", "shipment")
    assert [fk["parent"] for fk in shipment.fks] == ["demo.sales.order"]
    declared = sum(len(spec.get("fks", [])) for spec in shop_fixture()["tables"].values())
    assert sum(len(e.fks) for e in entities.values()) == declared


def test_the_foreign_key_read_does_not_correlate_constraint_column_usage(ns, spark):
    ns["read_installed_model"](spark, ["demo"], None)
    joined = " ".join(" ".join(q.split()) for q in spark.queries)
    assert "referential_constraints" in joined
    assert "constraint_column_usage" not in joined


def test_views_and_internal_schemas_are_never_populated(ns, spark):
    ns["read_installed_model"](spark, ["demo"], None)
    columns_query = next(q for q in spark.queries if "information_schema.columns" in q)
    assert "t.table_type <> 'VIEW'" in " ".join(columns_query.split())
    for schema in ("information_schema", "_metrics", "_install", "_metamodel"):
        assert "'%s'" % schema in columns_query


# =====================================================================================
# keys
# =====================================================================================

def test_every_table_gets_unique_keys_in_its_own_block(ns, spark):
    entities = ns["read_installed_model"](spark, ["demo"], None)
    seen = {}
    for entity in entities.values():
        keys = ns["generate_keys"](entity, 20, 20260801)
        assert len(set(keys)) == 20, "%s repeats a key" % entity.fqn
        numeric = [k[0] for k in keys if isinstance(k[0], int)]
        for value in numeric:
            assert value not in seen, \
                "%s reuses key %s already issued to %s" % (entity.fqn, value, seen.get(value))
        for value in numeric:
            seen[value] = entity.fqn


def test_a_composite_key_is_unique_as_a_tuple(ns, spark):
    entities = ns["read_installed_model"](spark, ["demo"], None)
    line = entity_of(entities, "sales", "order_line")
    keys = ns["generate_keys"](line, 25, 20260801)
    assert len(keys[0]) == 2
    assert len(set(keys)) == 25


def test_widening_a_colliding_composite_key_keeps_the_declared_type(ns):
    """A composite key whose leading columns repeat gets its last part widened.

    The replacement has to stay in the column's declared type. Substituting a
    string into a DATE or DECIMAL key column makes Spark reject the table on
    write, so the collision would surface as a failed install rather than as a
    duplicate key.
    """
    SampleEntity = ns["SampleEntity"]
    for dtype, expected in (("DATE", datetime.date),
                            ("TIMESTAMP", datetime.datetime),
                            ("DECIMAL(12,2)", decimal.Decimal),
                            ("DOUBLE", float),
                            ("BIGINT", int),
                            ("STRING", str)):
        entity = SampleEntity("demo", "sales", "reading")
        entity.columns = [
            {"name": "sensor_id", "type": "INT", "nullable": False, "position": 1},
            {"name": "taken_at", "type": dtype, "nullable": False, "position": 2},
        ]
        # Two columns, both blocked into repeats, so the widener has to fire.
        entity.pk = ["sensor_id", "taken_at"]
        keys = ns["generate_keys"](entity, 30, 20260801)
        assert len(set(keys)) == 30, "%s: widening left duplicate keys" % dtype
        for key in keys:
            assert isinstance(key[1], expected), \
                "%s: widened part is %s, not %s" % (dtype, type(key[1]).__name__,
                                                    expected.__name__)


def test_widening_a_key_column_that_cannot_be_widened_terminates(ns):
    """A BOOLEAN key column holds two values, so 30 unique keys are impossible.

    The widener must give up rather than spin, and let the integrity gate report
    the duplicates honestly.
    """
    SampleEntity = ns["SampleEntity"]
    entity = SampleEntity("demo", "sales", "flagged")
    entity.columns = [
        {"name": "batch_no", "type": "INT", "nullable": False, "position": 1},
        {"name": "is_open", "type": "BOOLEAN", "nullable": False, "position": 2},
    ]
    entity.pk = ["batch_no", "is_open"]
    keys = ns["generate_keys"](entity, 30, 20260801)
    assert len(keys) == 30
    assert all(isinstance(k[1], bool) for k in keys)


def test_a_narrow_numeric_key_column_stays_inside_its_declared_range(ns):
    """A SMALLINT or DECIMAL(5,0) key cannot hold this table's key block.

    An out-of-range key value fails the write for the entire table, so the key part
    is folded into the declared range instead.
    """
    SampleEntity = ns["SampleEntity"]
    for dtype, ceiling in (("SMALLINT", 32767),
                           ("TINYINT", 127),
                           ("DECIMAL(5,0)", 99999)):
        entity = SampleEntity("demo", "sales", "ticket")
        entity.columns = [{"name": "ticket_no", "type": dtype,
                           "nullable": False, "position": 1}]
        entity.pk = ["ticket_no"]
        keys = ns["generate_keys"](entity, 10, 20260801)
        assert len(keys) == 10
        for key in keys:
            assert abs(int(key[0])) <= ceiling, \
                "%s: key %s exceeds the declared range" % (dtype, key[0])


def test_a_key_takes_the_type_its_column_declares(ns, spark):
    entities = ns["read_installed_model"](spark, ["demo"], None)
    assert isinstance(ns["generate_keys"](entity_of(entities, "sales", "order"),
                                          5, 1)[0][0], int)
    assert isinstance(ns["generate_keys"](entity_of(entities, "ops", "shipment"),
                                          5, 1)[0][0], str)


# =====================================================================================
# referential integrity - the property the whole design exists for
# =====================================================================================

def test_every_foreign_key_value_exists_in_its_parent(ns, populated):
    problems = []
    for entity in populated.values():
        for fk in entity.fks:
            parent = populated[fk["parent"]]
            positions = [parent.pk.index(c) for c in fk["parent_columns"]]
            pool = set(tuple(key[p] for p in positions) for key in parent.keys)
            for row in entity.rows:
                values = tuple(row[c] for c in fk["columns"])
                if all(v is None for v in values):
                    continue
                if values not in pool:
                    problems.append("%s %s -> %s" % (entity.fqn, values, parent.fqn))
    assert problems == []


def test_a_foreign_key_cycle_between_two_tables_still_resolves_both_sides(ns, populated):
    """customer -> order -> customer: keys exist before references, so neither side waits."""
    customer = entity_of(populated, "sales", "customer")
    order = entity_of(populated, "sales", "order")
    order_keys = set(k[0] for k in order.keys)
    customer_keys = set(k[0] for k in customer.keys)
    assert all(r["primary_order_id"] in order_keys for r in customer.rows)
    assert all(r["customer_id"] in customer_keys for r in order.rows)


def test_a_composite_foreign_key_copies_a_whole_parent_key(ns, populated):
    line = entity_of(populated, "sales", "order_line")
    event = entity_of(populated, "ops", "line_event")
    pool = set(line.keys)
    assert all((r["order_id"], r["line_no"]) in pool for r in event.rows)


def test_a_child_keyed_by_its_parent_borrows_a_real_parent_key(ns, populated):
    """order_line's key is (order_id, line_no): order_id must be an order that exists."""
    line = entity_of(populated, "sales", "order_line")
    order_keys = set(k[0] for k in entity_of(populated, "sales", "order").keys)
    assert all(row["order_id"] in order_keys for row in line.rows)
    assert len(set((r["order_id"], r["line_no"]) for r in line.rows)) == len(line.rows)


def test_a_one_to_one_extension_never_outgrows_its_parent(ns):
    """When the key IS the parent's key, a second row would duplicate that key."""
    fixture = {"catalog": "demo", "tables": {
        ("core", "account"): {"columns": [("account_id", "BIGINT", False),
                                          ("account_name", "STRING", False)],
                              "pk": ["account_id"], "fks": []},
        ("core", "account_detail"): {"columns": [("account_id", "BIGINT", False),
                                                 ("credit_limit", "DECIMAL(12,2)", True)],
                                     "pk": ["account_id"],
                                     "fks": [{"columns": ["account_id"],
                                              "parent": ("core", "account"),
                                              "parent_columns": ["account_id"]}]}}}
    spark = FakeSpark(fixture)
    ns["generate_sample_data"](spark, sample_config(rows=10), ["demo"], lambda m: None)
    parents = set(r[0] for r in spark.written["demo.core.account"])
    children = [r[0] for r in spark.written["demo.core.account_detail"]]
    assert len(children) == len(set(children)) == 10
    assert set(children) == parents


def test_a_self_reference_points_backwards_so_the_data_has_no_cycle(ns, populated):
    employee = entity_of(populated, "hr", "employee")
    ids = [r["employee_id"] for r in employee.rows]
    position = dict((v, i) for i, v in enumerate(ids))
    assert employee.rows[0]["manager_id"] is None
    for index, row in enumerate(employee.rows[1:], start=1):
        assert position[row["manager_id"]] < index


def test_foreign_keys_fan_out_instead_of_collapsing_onto_one_parent(ns, populated):
    """A single repeated parent makes every demo join look like a 1:1 table."""
    order = entity_of(populated, "sales", "order")
    distinct = set(r["customer_id"] for r in order.rows)
    assert len(distinct) > 1, "all orders point at one customer"
    customer_keys = set(k[0] for k in entity_of(populated, "sales", "customer").keys)
    assert distinct == customer_keys, "some parents are never referenced"


def test_a_three_level_chain_resolves_at_every_level(ns):
    """grandparent <- parent <- child: depth must not degrade into invented keys."""
    fixture = {"catalog": "demo", "tables": {
        ("y", "region"): {"columns": [("region_id", "BIGINT", False),
                                      ("region_name", "STRING", False)],
                          "pk": ["region_id"], "fks": []},
        ("y", "store"): {"columns": [("store_id", "BIGINT", False),
                                     ("region_id", "BIGINT", False)],
                         "pk": ["store_id"],
                         "fks": [{"columns": ["region_id"], "parent": ("y", "region"),
                                  "parent_columns": ["region_id"]}]},
        ("y", "till"): {"columns": [("till_id", "BIGINT", False),
                                    ("store_id", "BIGINT", False)],
                        "pk": ["till_id"],
                        "fks": [{"columns": ["store_id"], "parent": ("y", "store"),
                                 "parent_columns": ["store_id"]}]}}}
    spark = FakeSpark(fixture)
    ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
    regions = set(r[0] for r in spark.written["demo.y.region"])
    stores = set(r[0] for r in spark.written["demo.y.store"])
    assert all(r[1] in regions for r in spark.written["demo.y.store"])
    assert all(r[1] in stores for r in spark.written["demo.y.till"])


def test_two_roles_pointing_at_the_same_parent_both_resolve(ns):
    """origin and destination are separate draws, not one value copied into both."""
    fixture = {"catalog": "demo", "tables": {
        ("g", "location"): {"columns": [("location_id", "BIGINT", False),
                                        ("city_name", "STRING", False)],
                            "pk": ["location_id"], "fks": []},
        ("g", "trip"): {"columns": [("trip_id", "BIGINT", False),
                                    ("origin_id", "BIGINT", False),
                                    ("destination_id", "BIGINT", False)],
                        "pk": ["trip_id"],
                        "fks": [{"columns": ["origin_id"], "parent": ("g", "location"),
                                 "parent_columns": ["location_id"]},
                                {"columns": ["destination_id"], "parent": ("g", "location"),
                                 "parent_columns": ["location_id"]}]}}}
    spark = FakeSpark(fixture)
    ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
    locations = set(r[0] for r in spark.written["demo.g.location"])
    trips = spark.written["demo.g.trip"]
    assert all(r[1] in locations and r[2] in locations for r in trips)
    assert len(set(r[1] for r in trips)) > 1 and len(set(r[2] for r in trips)) > 1


def test_a_three_table_foreign_key_cycle_resolves_every_side(ns):
    """A 2-table cycle can be luck; a 3-table cycle needs the keys-before-references order."""
    def table(name, points_at):
        return {"columns": [("%s_id" % name, "BIGINT", False),
                            ("%s_name" % name, "STRING", False),
                            ("%s_id" % points_at, "BIGINT", True)],
                "pk": ["%s_id" % name],
                "fks": [{"columns": ["%s_id" % points_at], "parent": ("x", points_at),
                         "parent_columns": ["%s_id" % points_at]}]}
    fixture = {"catalog": "demo", "tables": {("x", "a"): table("a", "b"),
                                             ("x", "b"): table("b", "c"),
                                             ("x", "c"): table("c", "a")}}
    spark = FakeSpark(fixture)
    ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
    for child, parent in (("a", "b"), ("b", "c"), ("c", "a")):
        keys = set(r[0] for r in spark.written["demo.x.%s" % parent])
        assert all(r[2] in keys for r in spark.written["demo.x.%s" % child]), child


def test_a_table_with_no_relationships_still_gets_a_full_unique_block(ns, populated):
    country = entity_of(populated, "ops", "reference_country")
    codes = [r["country_code"] for r in country.rows]
    assert country.fks == [] and len(codes) == 10 == len(set(codes))


def test_a_foreign_key_that_cannot_carry_its_parents_type_is_refused_not_orphaned(ns):
    """Unity Catalog rejects such a key at DDL time, so reaching the gate means the
    catalog is inconsistent: fail closed rather than write rows that never join."""
    fixture = {"catalog": "demo", "tables": {
        ("c", "parent"): {"columns": [("parent_id", "BIGINT", False),
                                      ("parent_name", "STRING", False)],
                          "pk": ["parent_id"], "fks": []},
        ("c", "child"): {"columns": [("child_id", "BIGINT", False),
                                     ("parent_id", "STRING", True)],
                         "pk": ["child_id"],
                         "fks": [{"columns": ["parent_id"], "parent": ("c", "parent"),
                                  "parent_columns": ["parent_id"]}]}}}
    spark = FakeSpark(fixture)
    with pytest.raises(Exception) as err:
        ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
    assert "no parent key" in str(err.value)
    assert spark.written == {}


@pytest.mark.parametrize("rows", [5, 10, 20, 50, 100])
def test_every_offered_row_count_keeps_keys_unique_and_every_link_resolved(ns, rows):
    """The row widget's five choices, each checked end to end on the written rows."""
    fixture = shop_fixture()
    spark = FakeSpark(fixture)
    ns["generate_sample_data"](spark, sample_config(rows=rows), ["demo"], lambda m: None)
    order = {}
    for (schema, table), spec in fixture["tables"].items():
        fqn = "demo.%s.%s" % (schema, table)
        assert len(spark.written[fqn]) == rows, fqn
        order[fqn] = [c[0] for c in spec["columns"]]
        keys = [tuple(r[order[fqn].index(c)] for c in spec["pk"])
                for r in spark.written[fqn]]
        assert len(set(keys)) == rows, "%s repeats a key at %d rows" % (fqn, rows)
    for (schema, table), spec in fixture["tables"].items():
        child = "demo.%s.%s" % (schema, table)
        for fk in spec["fks"]:
            parent = "demo.%s.%s" % fk["parent"]
            pool = set(tuple(r[order[parent].index(c)] for c in fk["parent_columns"])
                       for r in spark.written[parent])
            for row in spark.written[child]:
                value = tuple(row[order[child].index(c)] for c in fk["columns"])
                assert all(v is None for v in value) or value in pool, \
                    "%s %s has no parent in %s at %d rows" % (child, value, parent, rows)


# =====================================================================================
# the integrity gate must actually reject
# =====================================================================================

def test_the_gate_passes_a_correctly_generated_model(ns, populated):
    assert ns["assert_integrity"](populated) == []


def test_the_gate_rejects_a_duplicated_primary_key(ns, populated):
    order = entity_of(populated, "sales", "order")
    order.rows[1]["order_id"] = order.rows[0]["order_id"]
    problems = ns["assert_integrity"](populated)
    assert any("primary key" in p and "duplicate" in p for p in problems)


def test_the_gate_rejects_a_foreign_key_with_no_parent(ns, populated):
    order = entity_of(populated, "sales", "order")
    order.rows[0]["customer_id"] = -999
    problems = ns["assert_integrity"](populated)
    assert any("no parent key" in p for p in problems)


def test_the_gate_rejects_a_null_in_a_not_null_column(ns, populated):
    customer = entity_of(populated, "sales", "customer")
    customer.rows[0]["status"] = None
    problems = ns["assert_integrity"](populated)
    assert any("NOT NULL" in p and "status" in p for p in problems)


def test_nothing_is_written_when_the_gate_fails(ns, monkeypatch):
    spark = FakeSpark(shop_fixture())
    real = ns["generate_rows"]

    def corrupt(entity, entities, rows, seed, pools=None):
        out = real(entity, entities, rows, seed, pools)
        if entity.table == "order":
            out[1]["order_id"] = out[0]["order_id"]
        return out

    ns_copy = dict(ns)
    ns_copy["generate_rows"] = corrupt
    with pytest.raises(Exception) as err:
        ns["generate_sample_data"].__globals__.update(generate_rows=corrupt)
        ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
    ns["generate_sample_data"].__globals__.update(generate_rows=real)
    assert "integrity check failed" in str(err.value).lower()
    assert spark.written == {}


# =====================================================================================
# value quality
# =====================================================================================

def test_no_column_is_filled_with_a_placeholder(ns, populated):
    placeholder = re.compile(r"^(sample|value|string|test)[_ ]?\d*$", re.IGNORECASE)
    for entity in populated.values():
        for row in entity.rows:
            for name, value in row.items():
                if isinstance(value, str):
                    assert not placeholder.match(value), "%s.%s = %r" % (entity.fqn, name, value)


def test_a_narrow_decimal_is_not_saturated_at_its_ceiling(ns, populated):
    values = [r["loyalty_score"] for r in entity_of(populated, "sales", "customer").rows]
    assert all(isinstance(v, decimal.Decimal) for v in values)
    assert all(abs(v) <= decimal.Decimal("9.9999") for v in values)
    assert len(set(values)) > 1, "DECIMAL(5,4) collapsed onto a single value"


def test_a_decimal_never_exceeds_its_declared_scale(ns, populated):
    for entity in populated.values():
        for column in entity.columns:
            if not column["type"].upper().startswith("DECIMAL"):
                continue
            scale = int(column["type"].split(",")[1].rstrip(")"))
            for row in entity.rows:
                value = row[column["name"]]
                if value is not None:
                    assert -value.as_tuple().exponent <= scale


def test_a_decimal_value_is_clamped_to_its_declared_precision(ns):
    # An LLM value pool does not pass through numeric_range's type_ceiling clamp, so an
    # out-of-range magnitude reaches _coerce; unclamped it overflows DECIMAL(p,s) and Spark
    # rejects the whole write, emptying every table that references it (live repro:
    # coffee_roastery wholesale.sales_rep failed, 7 FK dependents skipped).
    coerce = ns["_coerce"]
    # 1234567.89 is 9 digits; DECIMAL(6,2) holds at most 4 integer + 2 fractional digits.
    assert coerce(1234567.89, "DECIMAL(6,2)") == decimal.Decimal("9999.99")
    assert coerce(-99999999, "DECIMAL(6,2)") == decimal.Decimal("-9999.99")
    # an in-range value is only quantized to scale, never clamped
    assert coerce(12.5, "DECIMAL(6,2)") == decimal.Decimal("12.50")
    # too many fractional digits round to scale; magnitude is untouched
    assert coerce(3.14159, "DECIMAL(6,2)") == decimal.Decimal("3.14")
    # a wide-but-in-range value fits exactly at the precision boundary
    assert coerce(999999, "DECIMAL(6,0)") == decimal.Decimal("999999")


def test_a_percentage_stays_within_a_believable_range(ns):
    low, high, places = ns["numeric_range"]("completion_pct", "DOUBLE")
    assert (low, high) == (0.0, 100.0) and places == 2


def test_a_code_column_draws_from_its_own_vocabulary(ns, populated):
    codes = set(r["country_code"] for r in entity_of(populated, "sales", "customer").rows)
    assert codes, "no country codes generated"
    assert all(re.match(r"^[A-Z]{2}$", c) for c in codes), sorted(codes)


def test_a_name_column_is_not_turned_into_a_code(ns, populated):
    names = [r["country_name"] for r in entity_of(populated, "ops", "reference_country").rows]
    assert all(not re.match(r"^[A-Z]{2,3}-\d+$", n) for n in names), names


def test_an_email_looks_like_an_email(ns, populated):
    for row in entity_of(populated, "sales", "customer").rows:
        assert re.match(r"^[^@\s]+@[^@\s]+\.[a-z]+$", row["email"]), row["email"]


def test_dates_that_name_an_order_are_in_that_order(ns, populated):
    for row in entity_of(populated, "sales", "order").rows:
        assert row["order_date"] <= row["ship_date"]
    for row in entity_of(populated, "hr", "employee").rows:
        assert row["hire_date"] <= row["termination_date"]


def test_a_naming_cycle_is_left_alone_rather_than_repaired_arbitrarily(ns):
    """start->end says A precedes B while created->updated says B precedes A."""
    names = ["start_updated_date", "end_created_date"]
    assert len(ns["temporal_edges"](names)) == 2, "the fixture must be a real cycle"
    assert ns["temporal_order_plan"](names) == []


def test_the_same_seed_produces_the_same_rows(ns):
    def run():
        spark = FakeSpark(shop_fixture())
        ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
        return spark.written

    first, second = run(), run()
    assert first == second and first, "sample generation is not reproducible"


# =====================================================================================
# the optional LLM pass may improve values but may never break the run
# =====================================================================================

def test_llm_pools_are_used_for_free_text_columns(ns):
    response = json.dumps({"carrier_name": ["Maersk", "DHL Express", "Kuehne+Nagel",
                                            "DB Schenker", "Hapag-Lloyd"]})
    spark = FakeSpark(shop_fixture(), ai_response=response)
    ns["generate_sample_data"](spark, sample_config(llm=True, llm_endpoints=["ep"]),
                               ["demo"], lambda m: None)
    carriers = set(r[2] for r in spark.written["demo.ops.shipment"])
    assert carriers <= {"Maersk", "DHL Express", "Kuehne+Nagel", "DB Schenker", "Hapag-Lloyd"}


def test_a_dead_llm_endpoint_falls_back_instead_of_failing(ns):
    spark = FakeSpark(shop_fixture(), ai_error=True)
    summary = ns["generate_sample_data"](spark, sample_config(llm=True, llm_endpoints=["dead"]),
                                         ["demo"], lambda m: None)
    assert summary["written"] > 0
    assert spark.written["demo.ops.shipment"], "fallback produced no rows"


def test_llm_garbage_is_ignored_rather_than_written(ns):
    spark = FakeSpark(shop_fixture(), ai_response="I'm sorry, I cannot help with that.")
    summary = ns["generate_sample_data"](spark, sample_config(llm=True, llm_endpoints=["ep"]),
                                         ["demo"], lambda m: None)
    assert summary["written"] > 0


def test_a_single_llm_failure_does_not_retire_the_endpoint(ns):
    """One rate-limited table must not cost every other table its realistic values."""
    spark = FakeSpark(shop_fixture(), ai_error=True)
    entities = ns["read_installed_model"](spark, ["demo"], None)
    entity = entity_of(entities, "ops", "shipment")
    tolerated = ns["SAMPLE_LLM_MAX_ENDPOINT_ERRORS"]
    broken = ns["_LLM_STATE"]["broken"]
    ns["_LLM_STATE"]["errors"].pop("flaky", None)
    broken.discard("flaky")
    try:
        for attempt in range(1, tolerated + 1):
            ns["llm_value_pools"](spark, entity, ["carrier_name"], ["flaky"], 10, None)
            assert ("flaky" in broken) == (attempt >= tolerated), \
                "endpoint retired after %d of %d tolerated failures" % (attempt, tolerated)
    finally:
        broken.discard("flaky")
        ns["_LLM_STATE"]["errors"].pop("flaky", None)


def test_a_hung_llm_endpoint_does_not_hold_up_the_install(ns):
    """The realism pass is optional, so its budget bounds it and the rows still land."""
    spark = FakeSpark(shop_fixture(), ai_response=json.dumps({"carrier_name": ["A"] * 8}),
                      ai_delay=30.0)
    original = ns["SAMPLE_LLM_TIMEOUT_S"]
    ns["SAMPLE_LLM_TIMEOUT_S"] = 1
    started = time.time()
    try:
        summary = ns["generate_sample_data"](
            spark, sample_config(llm=True, llm_endpoints=["slow"], threads=8),
            ["demo"], lambda m: None)
    finally:
        ns["SAMPLE_LLM_TIMEOUT_S"] = original
    elapsed = time.time() - started
    assert elapsed < 20, "the LLM pass did not respect its budget (%.1fs)" % elapsed
    assert summary["written"] > 0, "deterministic rows must still be written"


def test_the_llm_is_never_asked_to_invent_a_key(ns, spark):
    entities = ns["read_installed_model"](spark, ["demo"], None)
    for entity in entities.values():
        candidates = ns["_llm_candidate_columns"](entity)
        keys = set(entity.pk)
        for fk in entity.fks:
            keys.update(fk["columns"])
        assert not (set(candidates) & keys), entity.fqn


# =====================================================================================
# writing
# =====================================================================================

def test_rows_are_written_in_the_tables_own_column_order(ns):
    spark = FakeSpark(shop_fixture())
    ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"], lambda m: None)
    rows = spark.written["demo.sales.order"]
    assert len(rows) == 5
    names = [c[0] for c in shop_fixture()["tables"][("sales", "order")]["columns"]]
    assert len(rows[0]) == len(names)
    assert isinstance(rows[0][names.index("order_id")], int)


def test_every_table_receives_the_requested_row_count(ns):
    spark = FakeSpark(shop_fixture())
    summary = ns["generate_sample_data"](spark, sample_config(rows=20), ["demo"], lambda m: None)
    assert summary["written"] == 20 * len(shop_fixture()["tables"])
    assert all(len(v) == 20 for v in spark.written.values())


def test_one_unwritable_table_does_not_lose_the_rest(ns):
    spark = FakeSpark(shop_fixture(), write_error=[("ops", "shipment")])
    summary = ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"], lambda m: None)
    assert summary["failed"] == ["demo.ops.shipment"]
    assert "demo.ops.shipment" not in spark.written
    assert len(spark.written) == len(shop_fixture()["tables"]) - 1


def test_an_empty_catalog_is_reported_rather_than_crashing(ns):
    spark = FakeSpark({"catalog": "demo", "tables": {}})
    summary = ns["generate_sample_data"](spark, sample_config(), ["demo"], lambda m: None)
    assert summary == {"tables": 0, "rows": 0, "problems": [], "written": 0}


# =====================================================================================
# how main() decides to call the engine
# =====================================================================================

def _run_main(sample_cfg, failures, calls):
    return run_main_cell(sample_cfg, failures, calls)


def test_the_installer_does_not_generate_samples_unless_asked():
    calls = _run_main({"enabled": False, "rows": 10}, [], {})
    assert "samples" not in calls
    assert "samples" not in (calls.get("exit") or "")


def test_asking_for_samples_runs_the_engine_on_the_target_catalogs():
    cfg = {"enabled": True, "rows": 20, "seed": 1, "threads": 2, "llm": False,
           "llm_endpoints": []}
    calls = _run_main(cfg, [], {})
    assert calls["samples"] == [(cfg, ["demo"])]
    assert "samples: 42 rows in 7 tables" in calls["exit"]


def test_samples_are_skipped_when_the_install_left_structural_failures():
    """Rows written against tables whose keys failed to apply cannot be joined."""
    calls = {}
    with pytest.raises(Exception, match="Install FAILED"):
        _run_main({"enabled": True, "rows": 10}, [("table", "CREATE TABLE t", "boom")], calls)
    assert "samples" not in calls
    assert any("Samples skipped" in m for m in calls["log"])


def test_a_metric_view_defect_alone_does_not_block_samples():
    cfg = {"enabled": True, "rows": 10, "seed": 1, "threads": 2, "llm": False,
           "llm_endpoints": []}
    calls = _run_main(cfg, [("metric", "CREATE VIEW v", "bad column")], {})
    assert calls["samples"], "a metric-view source defect is not a structural failure"


# =====================================================================================
# the notebook and the engine file may never drift
# =====================================================================================

def test_the_shipped_cell_is_exactly_the_engine_file():
    assert find_cell("def generate_sample_data") == ENGINE.read_text()


def test_the_sync_script_reports_no_drift():
    result = subprocess.run([sys.executable, str(HERE.parent / "sync_sample_cell.py"), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_sample_cell_runs_before_main():
    cells = [cell_source(c) for c in notebook_cells() if c.get("cell_type") == "code"]
    engine_at = next(i for i, s in enumerate(cells) if "def generate_sample_data" in s)
    main_at = next(i for i, s in enumerate(cells) if "def main()" in s)
    assert engine_at < main_at


def test_the_engine_imports_nothing_from_the_modelling_agent():
    source = ENGINE.read_text()
    for banned in ("vibe", "VibeOrchestrator", "AIAgent", "ai_agent", "dbx_vibe"):
        assert banned not in source, "sample generation must stand alone (%s)" % banned
    imports = re.findall(r"^(?:from|import)\s+([a-zA-Z_][\w.]*)", source, re.MULTILINE)
    allowed = {"datetime", "decimal", "json", "random", "re", "threading", "time",
               "concurrent.futures"}
    assert set(imports) <= allowed, set(imports) - allowed
