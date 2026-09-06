"""v4.8.6: the physical prevalidator renames a drifted column ref instead of pruning it.

The prevalidator used to delete any dimension whose expr named a column the physical
source table does not have. That keeps the view installable but silently costs the
dimension, and it assumes the miss is a typo. Across the 24 published models repaired
this session the miss is a RENAME: the generator emits the logical column with its role
prefix while the DDL naming convention normalizes it away.

    origin_plant_id -> plant_id            member_identity_id -> identity_id
    dealer_account_id -> account_id        primary_x_customer_party_id -> party_id

Prevalidation is the last point where the physical columns are known, so it is the right
place to rename. These tests fail on pre-patch HEAD, where every case below is pruned.
"""
import re

from notebook_source_util import agent_version_line
from test_v345_behavioral import _exec_mv_prune


def stmt(dimensions, measures=None, source="hr.position"):
    measures = measures or [("Row Count", "COUNT(1)")]
    lines = ["CREATE OR REPLACE VIEW `c`.`_metrics`.`v`",
             "WITH METRICS", "LANGUAGE YAML", "AS $$",
             "version: 0.1", "source: `c`.`%s`" % source.replace(".", "`.`"),
             "  dimensions:"]
    for name, expr in dimensions:
        lines += ['    - name: "%s"' % name, "      expr: %s" % expr]
    lines.append("  measures:")
    for name, expr in measures:
        lines += ['    - name: "%s"' % name, "      expr: %s" % expr]
    lines.append("$$")
    return "\n".join(lines)


def run_one(dimensions, cols, measures=None):
    kept, drops, renames = _exec_mv_prune()(stmt(dimensions, measures), set(cols))
    assert len(kept) == 1, "the view itself must always survive"
    return kept[0], drops, renames


# --- the rename that used to be a prune ----------------------------------------

def test_a_role_prefixed_reference_is_renamed_onto_the_physical_column():
    out, drops, renames = run_one([("Plant", "origin_plant_id")],
                                  ["route_id", "plant_id", "carrier_id"])
    assert "expr: plant_id" in out
    assert "origin_plant_id" not in out
    assert drops == [], "nothing was unresolvable, so nothing may be pruned"
    assert renames and renames[0][1] == [("origin_plant_id", "plant_id")]


def test_the_dimension_survives_the_rename_instead_of_being_deleted():
    out, _drops, _renames = run_one([("Plant", "origin_plant_id"), ("Lane", "lane_id")],
                                    ["plant_id", "lane_id"])
    assert out.count("- name:") == 3  # both dimensions + the measure
    assert '"Plant"' in out and '"Lane"' in out


def test_a_reference_inside_an_aggregate_is_renamed_too():
    out, drops, renames = run_one([], ["party_id"],
                                  measures=[("Parties", "COUNT(DISTINCT primary_customer_party_id)")])
    assert "COUNT(DISTINCT party_id)" in out
    assert drops == [] and renames


def test_two_drifted_references_in_one_expression_both_resolve():
    out, drops, _ = run_one([], ["plant_id", "lane_id"],
                            measures=[("Mix", "COUNT(origin_plant_id) + COUNT(inbound_lane_id)")])
    assert "COUNT(plant_id) + COUNT(lane_id)" in out
    assert drops == []


# --- where renaming would be a guess, it still prunes --------------------------

def test_an_ambiguous_reference_is_not_guessed_and_still_prunes():
    # `order_status` could be line_status or header_status: two equally good tails.
    out, drops, renames = run_one([("Status", "order_status"), ("Keep", "line_id")],
                                  ["line_status", "header_status", "line_id"])
    assert "order_status" not in out
    assert "line_status" not in out and "header_status" not in out
    assert drops and "order_status" in str(drops)
    assert renames == []


def test_a_reference_with_no_candidate_at_all_still_prunes():
    out, drops, renames = run_one([("Ghost", "no_such_column"), ("Keep", "plant_id")],
                                  ["plant_id"])
    assert "no_such_column" not in out
    assert '"Keep"' in out
    assert drops and renames == []


def test_a_block_is_pruned_whole_when_only_some_of_its_refs_resolve():
    out, drops, renames = run_one([("Mixed", "origin_plant_id + no_such_column")],
                                  ["plant_id"])
    assert "origin_plant_id" not in out and "no_such_column" not in out
    assert "plant_id" not in out, "a half-resolvable block must not be half-rewritten"
    assert drops and renames == []


def test_matching_is_on_whole_segments_so_a_substring_is_not_a_rename():
    out, drops, renames = run_one([("Odd", "xplant_id")], ["plant_id"])
    assert "plant_id" not in out.replace("xplant_id", "")
    assert drops and renames == []


# --- the collision the rename itself can create --------------------------------

def test_a_rename_that_would_duplicate_a_healthy_dimension_yields_to_it():
    out, drops, renames = run_one([("profile_id", "profile_id"),
                                   ("guest_profile_id", "guest_profile_id")],
                                  ["profile_id"])
    assert out.count('- name: "profile_id"') == 1
    assert "guest_profile_id" not in out
    assert drops and renames == []


def test_two_logical_names_collapsing_onto_one_column_emit_one_dimension():
    out, _drops, _renames = run_one([("guest_profile_id", "guest_profile_id"),
                                     ("preference_guest_profile_id", "preference_guest_profile_id")],
                                    ["profile_id"])
    assert out.count('- name: "profile_id"') == 1


# --- non-tautology: a healthy view is untouched --------------------------------

def test_a_view_whose_columns_all_resolve_is_left_alone():
    out, drops, renames = run_one([("Plant", "plant_id")], ["plant_id"])
    assert "expr: plant_id" in out
    assert drops == [] and renames == []


def test_a_sql_keyword_is_never_renamed():
    out, drops, renames = run_one([], ["state"],
                                  measures=[("Open", "COUNT(CASE WHEN state = 'x' THEN 1 END)")])
    assert "COUNT(CASE WHEN state" in out
    assert drops == [] and renames == []


# --- self-reporting and version -------------------------------------------------

def test_the_rename_is_reported_so_a_live_run_can_be_audited():
    from notebook_source_util import notebook_concat_source
    src = notebook_concat_source()
    assert "[mv-column-rename-before-prune FIRED v4.8.6]" in src
    assert "alias=mv-column-rename-before-prune" in src


def test_the_agent_version_is_at_least_the_one_that_shipped_this_fix():
    m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', agent_version_line())
    assert m, agent_version_line()
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 6), agent_version_line()
