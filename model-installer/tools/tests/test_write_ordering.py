"""A failed write must never leave a child pointing at a parent row that does not exist.

The live coffee_roastery install found this the hard way: roasting.postroast_cupping
failed to write, roasting.finished_package had already landed referencing its 20 planned
keys, and the audit found 20 orphans in a run the installer called a warning.
"""
import pytest

from installer_harness import FakeSpark, load_engine, sample_config, shop_fixture


@pytest.fixture(scope="module")
def ns():
    return load_engine()


def _entity(fqn, parents):
    return type("E", (), {"fqn": fqn, "fks": [{"parent": p} for p in parents]})()


def _graph(ns, spec):
    return ns["write_order"](dict((k, _entity(k, v)) for k, v in spec.items()))


def _wave_of(waves, name):
    return next(i for i, wave in enumerate(waves) if name in wave)


# ------------------------------------------------------------------ write_order

def test_a_parent_is_written_in_an_earlier_wave_than_its_child(ns):
    waves = _graph(ns, {"a": [], "b": ["a"], "c": ["b"]})
    assert _wave_of(waves, "a") < _wave_of(waves, "b") < _wave_of(waves, "c")


def test_independent_tables_share_a_wave_so_writing_stays_parallel(ns):
    waves = _graph(ns, {"a": [], "b": ["a"], "d": ["a"]})
    assert _wave_of(waves, "b") == _wave_of(waves, "d")


def test_a_self_reference_does_not_delay_its_own_table(ns):
    # A self FK points at an earlier row of the same write, so it imposes no order.
    waves = _graph(ns, {"a": [], "e": ["e"]})
    assert waves == [["a", "e"]]


def test_tables_in_a_cycle_share_one_wave(ns):
    waves = _graph(ns, {"x": ["y"], "y": ["x"], "z": []})
    assert _wave_of(waves, "x") == _wave_of(waves, "y")


def test_a_cycle_does_not_drag_its_downstream_into_the_cycle_wave(ns):
    # The naive Kahn version put order_line and line_event in with the cycle, which
    # silently gave up ordering for most of the model.
    waves = _graph(ns, {"customer": ["order"], "order": ["customer"],
                        "order_line": ["order"], "line_event": ["order_line"]})
    assert _wave_of(waves, "order") < _wave_of(waves, "order_line") \
        < _wave_of(waves, "line_event")


def test_every_table_appears_exactly_once(ns):
    spec = {"customer": ["order"], "order": ["customer"], "order_line": ["order"],
            "employee": ["employee"], "shipment": ["order"],
            "line_event": ["order_line"], "reference_country": []}
    flat = [t for wave in _graph(ns, spec) for t in wave]
    assert sorted(flat) == sorted(spec)
    assert len(flat) == len(set(flat))


def test_a_foreign_key_to_a_table_outside_the_model_is_ignored(ns):
    # information_schema can name a parent the sample pass is not populating.
    waves = _graph(ns, {"a": ["not_installed"], "b": ["a"]})
    assert _wave_of(waves, "a") < _wave_of(waves, "b")


# ------------------------------------------------------- abort on a failed wave

def test_a_child_is_not_written_when_its_parent_fails(ns):
    spark = FakeSpark(shop_fixture(), write_error=[("sales", "order_line")])
    summary = ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"],
                                         lambda m: None)
    assert "demo.sales.order_line" in summary["failed"]
    assert "demo.ops.line_event" not in spark.written
    assert "demo.ops.line_event" in summary["skipped"]


def test_the_parent_that_succeeded_still_keeps_its_rows(ns):
    # Aborting must not throw away work that is already referentially sound.
    spark = FakeSpark(shop_fixture(), write_error=[("sales", "order_line")])
    ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"], lambda m: None)
    assert spark.written.get("demo.sales.order")


def test_nothing_written_references_a_table_that_was_not_written(ns):
    spark = FakeSpark(shop_fixture(), write_error=[("sales", "order_line")])
    ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"], lambda m: None)
    written = set(spark.written)
    fixture = shop_fixture()
    for (schema, table), spec in fixture["tables"].items():
        fqn = "demo.%s.%s" % (schema, table)
        if fqn not in written:
            continue
        for fk in spec.get("fks", []):
            parent = "demo.%s.%s" % fk["parent"]
            assert parent == fqn or parent in written, \
                "%s was written but its parent %s was not" % (fqn, parent)


def test_the_skip_is_reported_so_the_operator_is_not_told_it_is_fine(ns):
    lines = []
    spark = FakeSpark(shop_fixture(), write_error=[("sales", "order_line")])
    ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"], lines.append)
    text = "\n".join(lines)
    assert "skipping" in text and "reference them" in text
    assert "order_line" in text
    assert "1 skipped" in text


def test_a_clean_run_writes_every_table_and_reports_no_skips(ns):
    # Guard against an abort path that fires when nothing is wrong.
    spark = FakeSpark(shop_fixture())
    summary = ns["generate_sample_data"](spark, sample_config(rows=5), ["demo"],
                                         lambda m: None)
    assert summary["failed"] == []
    assert summary["skipped"] == []
    assert len(spark.written) == len(shop_fixture()["tables"])
