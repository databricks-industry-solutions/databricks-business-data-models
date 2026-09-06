"""v4.8.7 - an attribute rename must carry its physical column_name along.

Pre-patch, a rename rewrote `attribute`/`name` and left `column_name` on the old
value. The DDL emitter prefers `column_name`, so the physical table kept the old
column while model.json, the metric views and the tags all shipped the new one.
That is the drift that put 1538 divergent attributes into the published models.

Each test drives production notebook source, not a reimplementation.
"""
import re

import pytest
from notebook_source_util import assert_agent_version_at_least, cell_containing


def _ddl_resync_source():
    """The resync block from step_create_physical_schema_stage1, as runnable code."""
    src = cell_containing("[DDL Diagnostics] Fixed {_attrs_case_fixed}")
    start = src.index("    _v487_desync = []")
    end = src.index("alias=v487-colname-rename-sync", start)
    end = src.index("\n", end) + 1
    body = src[start:end]
    return "\n".join(line[4:] if line.startswith("    ") else line
                     for line in body.split("\n"))


class _Log:
    def __init__(self):
        self.warnings = []

    def warning(self, msg):
        self.warnings.append(str(msg))

    def info(self, msg):
        pass


def _run_resync(attributes):
    ns = {"attributes": attributes, "logger": _Log()}
    exec(_ddl_resync_source(), ns)
    return ns["logger"].warnings


def test_a_stale_column_name_is_resynced_to_the_renamed_attribute():
    attrs = [{"domain": "roasting", "product": "roast_batch",
              "attribute": "assigned_roaster_id", "column_name": "roaster_id"}]
    warnings = _run_resync(attrs)
    assert attrs[0]["column_name"] == "assigned_roaster_id"
    assert any("v487-colname-rename-sync FIRED" in w for w in warnings)
    assert any("roaster_id -> assigned_roaster_id" in w for w in warnings)


def test_an_attribute_already_in_step_is_left_alone_and_stays_silent():
    attrs = [{"domain": "d", "product": "p",
              "attribute": "customer_id", "column_name": "customer_id"}]
    warnings = _run_resync(attrs)
    assert attrs[0]["column_name"] == "customer_id"
    assert warnings == []


def test_an_attribute_with_no_column_name_is_not_invented():
    attrs = [{"domain": "d", "product": "p", "attribute": "customer_id"}]
    _run_resync(attrs)
    assert "column_name" not in attrs[0]


def test_an_attribute_with_no_logical_name_is_left_untouched():
    attrs = [{"domain": "d", "product": "p", "column_name": "orphan_id"}]
    warnings = _run_resync(attrs)
    assert attrs[0]["column_name"] == "orphan_id"
    assert warnings == []


def test_the_name_key_is_honoured_when_attribute_is_absent():
    attrs = [{"domain": "d", "product": "p",
              "name": "issued_by_sales_rep_id", "column_name": "sales_rep_id"}]
    _run_resync(attrs)
    assert attrs[0]["column_name"] == "issued_by_sales_rep_id"


def test_non_dict_rows_do_not_crash_the_pass():
    attrs = ["not-a-dict", None,
             {"domain": "d", "product": "p", "attribute": "a_id", "column_name": "b_id"}]
    _run_resync(attrs)
    assert attrs[2]["column_name"] == "a_id"


def test_every_divergent_attribute_is_reported_even_when_only_eight_are_shown():
    attrs = [{"domain": "d", "product": "p%d" % i,
              "attribute": "new_%d_id" % i, "column_name": "old_%d_id" % i}
             for i in range(12)]
    warnings = _run_resync(attrs)
    assert all(a["column_name"] == a["attribute"] for a in attrs)
    assert re.search(r"resynced 12 stale column_name", warnings[0])


def test_the_pass_is_idempotent():
    attrs = [{"domain": "d", "product": "p",
              "attribute": "assigned_roaster_id", "column_name": "roaster_id"}]
    _run_resync(attrs)
    second = _run_resync(attrs)
    assert attrs[0]["column_name"] == "assigned_roaster_id"
    assert second == []


@pytest.mark.parametrize("needle", [
    'if _attrs[_old_idx].get("column_name"):',
    '_attrs[_old_idx]["column_name"] = _new_name',
])
def test_the_nested_rename_site_carries_column_name(needle):
    src = cell_containing('_attrs[_old_idx]["name"] = _new_name')
    assert needle in src


@pytest.mark.parametrize("needle", [
    "if a.get('column_name'):",
    "a['column_name'] = new_value",
])
def test_the_flat_rename_site_carries_column_name(needle):
    src = cell_containing("_attribute_rename[_old_key] = _new_key")
    assert needle in src


def test_the_running_version_is_487_or_later():
    assert_agent_version_at_least("4.8.7")


def test_the_resync_runs_before_any_ddl_is_emitted():
    """Ordering is the whole point: repairing after CREATE TABLE fixes nothing."""
    src = cell_containing("[DDL Diagnostics] Fixed {_attrs_case_fixed}")
    assert src.index("_v487_desync") < src.index("[DDL FK CHECK]")
    assert src.index("_v487_desync") < src.index("[DDL CREATED]")


def test_the_resync_reads_the_same_rows_the_ddl_emitter_reads():
    """It must mutate `attributes`, which is what attrs_map holds references into."""
    src = cell_containing("[DDL Diagnostics] Fixed {_attrs_case_fixed}")
    assert "for _v487_a in attributes:" in src
    assert src.index("attrs_map[(domain, product)].append(attr)") < src.index("_v487_desync")
