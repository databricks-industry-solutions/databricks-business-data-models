"""v4.9.8 — SCREAMING_CASE regular attributes stayed snake_case in model.json.

Root cause: the PRE-FIX attribute rename loop (_pre_static_analysis_autofix) seeds a
per-table set with each attribute's OWN lowercased name, then skips a rename when the
converted name's lowercased form is already in that set. For a case-only rename
(snake_case -> SCREAMING_CASE) new_an.lower() == the attribute's own seeded name, so the
attribute was treated as a self-collision and skipped, leaving it snake_case. camelCase /
PascalCase escaped the bug only because apply_convention strips underscores, so their
lowercased form differed from the seeded snake name. The fix excludes the self case.
"""
import re

from notebook_source_util import (
    assert_agent_version_at_least,
    cell_containing,
    exec_function_namespace,
)


def test_agent_version_at_least_498():
    assert_agent_version_at_least("4.9.8")


def test_prefix_guard_excludes_self_collision():
    """Structural fail-pre/pass-post: the guard must exclude the attribute's own name."""
    src = cell_containing("_attr_names_by_table = defaultdict(set)")
    guard = "if new_an.lower() in _attr_names_by_table.get(table_key, set()) and new_an.lower() != old_an.lower():"
    assert guard in src, "PRE-FIX attribute guard missing the self-collision exclusion"
    # the old buggy form must be gone
    assert "if new_an.lower() in _attr_names_by_table.get(table_key, set()):\n" not in src


def _skip(new_an, old_an, existing_lower, *, fixed):
    """Replicates the PRE-FIX guard decision. True => rename skipped."""
    cond = new_an.lower() in existing_lower
    if fixed:
        cond = cond and new_an.lower() != old_an.lower()
    return cond


def test_guard_self_rename_proceeds_but_real_collision_still_blocks():
    # SCREAMING case-only rename: the set is seeded with the attribute's own snake name.
    seeded_self = {"actual_arrival_timestamp"}
    # fail-pre: old logic wrongly skips the case-only rename
    assert _skip("ACTUAL_ARRIVAL_TIMESTAMP", "actual_arrival_timestamp", seeded_self, fixed=False) is True
    # pass-post: fixed logic proceeds
    assert _skip("ACTUAL_ARRIVAL_TIMESTAMP", "actual_arrival_timestamp", seeded_self, fixed=True) is False
    # a genuine cross-attribute collision (another attr already occupies the target) still blocks
    real_collision = {"foo_bar"}
    assert _skip("FOO_BAR", "fooBar", real_collision, fixed=True) is True


def test_apply_convention_screaming_uppercases_snake_attrs():
    ns = exec_function_namespace("apply_convention", extra_globals={"re": re})
    apply_convention = ns["apply_convention"]
    assert apply_convention("actual_arrival_timestamp", "SCREAMING_CASE") == "ACTUAL_ARRIVAL_TIMESTAMP"
    assert apply_convention("aircraft_type_icao", "SCREAMING_CASE") == "AIRCRAFT_TYPE_ICAO"
    # do not regress the conventions that already worked
    assert apply_convention("actual_arrival_timestamp", "camelCase") == "actualArrivalTimestamp"
    assert apply_convention("actual_arrival_timestamp", "PascalCase") == "ActualArrivalTimestamp"
    assert apply_convention("Actual_Arrival_Timestamp", "snake_case") == "actual_arrival_timestamp"
