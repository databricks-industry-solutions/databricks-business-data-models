"""The repair that rewrites published metric views onto the columns their DDL declares.

The drift is a rename, not a typo: the metric-view generator wrote the logical column
name with its role prefix (`origin_plant_id`) while the DDL normalized it to `plant_id`.
So the honest repair is a rename, and the honest non-repair is removing the item rather
than guessing which of several candidates was meant.
"""
import importlib.util
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[2] / "runner"
sys.path.insert(0, str(RUNNER))

spec = importlib.util.spec_from_file_location(
    "repair_published_mv_drift", RUNNER / "repair_published_mv_drift.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def view(name, source, body):
    return (
        'CREATE OR REPLACE VIEW `cat`.`_metrics`.`%s`\n'
        'WITH METRICS\nLANGUAGE YAML\nAS $$\n'
        '  version: 1.1\n'
        '  source: "`cat`.`%s`"\n'
        '%s'
        '$$;\n' % (name, source, body))


DIMS = (
    '  dimensions:\n'
    '    - name: "%s"\n'
    '      expr: %s\n'
    '      comment: "a comment that must travel with its item"\n'
)


def write_model(tmp_path, ddl, metrics):
    (tmp_path / "schemas").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "schemas" / "s.sql").write_text(ddl)
    (tmp_path / "metrics" / "m.sql").write_text(metrics)
    return tmp_path / "metrics" / "m.sql"


def ddl_for(table, columns):
    cols = ",\n".join("  `%s` STRING" % c for c in columns)
    return "CREATE TABLE `cat`.`%s` (\n%s\n)\nUSING DELTA;\n" % (table, cols)


def run(tmp_path, ddl, metrics, apply_changes=True):
    path = write_model(tmp_path, ddl, metrics)
    tables = R.parse_ddl(tmp_path / "schemas")
    renamed, dropped, views = R.repair_file(path, tables, apply_changes)
    return path.read_text(), renamed, dropped, views


# --- the item boundary, which is what the first cut got wrong ------------------

def test_an_item_owns_its_expr_and_comment_not_just_its_name_line():
    block = DIMS % ("plant", "origin_plant_id") + "  measures:\n"
    spans = R.items(block)
    assert len(spans) == 1
    text = block[spans[0][0]:spans[0][1]]
    assert "expr: origin_plant_id" in text
    assert "comment:" in text
    assert "measures:" not in text


def test_two_sibling_items_do_not_bleed_into_each_other():
    block = DIMS % ("a", "col_a") + DIMS % ("b", "col_b")
    spans = R.items(block)
    assert len(spans) == 2
    assert "col_b" not in block[spans[0][0]:spans[0][1]]


# --- resolving a drifted reference --------------------------------------------

def test_a_role_prefix_that_the_ddl_stripped_resolves_to_the_one_real_column():
    assert R.resolve("origin_plant_id", {"plant_id", "route_id", "carrier_id"}) == "plant_id"


def test_the_longest_shared_tail_wins_over_a_bare_id():
    assert R.resolve("primary_customer_party_id", {"id", "party_id"}) == "party_id"


def test_two_equally_good_candidates_are_not_guessed():
    assert R.resolve("order_status", {"line_status", "header_status"}) is None


def test_a_reference_with_no_candidate_at_all_is_not_guessed():
    assert R.resolve("status", {"plant_id", "route_id"}) is None


def test_matching_is_on_whole_segments_so_a_substring_is_not_a_rename():
    # `installation_id` must not be reached from `nstallation_id`.
    assert R.resolve("meter_installation_id", {"installation_id"}) == "installation_id"
    assert R.resolve("xinstallation_id", {"installation_id"}) is None


# --- what the repair writes ----------------------------------------------------

def test_the_drifted_reference_is_rewritten_onto_the_physical_column(tmp_path):
    out, renamed, dropped, views = run(
        tmp_path,
        ddl_for("logistics.route", ["route_id", "plant_id"]),
        view("logistics_route", "logistics.route", DIMS % ("origin_plant_id", "origin_plant_id")))
    assert "expr: plant_id" in out
    assert "origin_plant_id" not in out
    assert sum(renamed.values()) == 1 and dropped == 0 and views == 1


def test_an_unresolvable_reference_removes_its_item_and_leaves_the_view(tmp_path):
    metrics = view("t", "s.t", DIMS % ("good", "real_col") + DIMS % ("bad", "no_such_thing"))
    out, renamed, dropped, _ = run(tmp_path, ddl_for("s.t", ["real_col"]), metrics)
    assert "no_such_thing" not in out
    assert "expr: real_col" in out
    assert dropped == 1 and sum(renamed.values()) == 0
    assert out.count("CREATE OR REPLACE VIEW") == 1


def test_a_healthy_view_is_left_byte_identical(tmp_path):
    metrics = view("t", "s.t", DIMS % ("real_col", "real_col"))
    out, renamed, dropped, views = run(tmp_path, ddl_for("s.t", ["real_col"]), metrics)
    assert out == metrics
    assert not renamed and dropped == 0 and views == 0


def test_a_dry_run_changes_nothing_on_disk(tmp_path):
    metrics = view("t", "s.t", DIMS % ("origin_plant_id", "origin_plant_id"))
    out, renamed, _, _ = run(tmp_path, ddl_for("s.t", ["plant_id"]), metrics, apply_changes=False)
    assert out == metrics
    assert sum(renamed.values()) == 1  # still reported


def test_a_string_literal_is_never_mistaken_for_a_column(tmp_path):
    body = ('  measures:\n'
            "    - name: \"open_count\"\n"
            "      expr: COUNT(CASE WHEN state = 'origin_plant_id' THEN 1 END)\n")
    metrics = view("t", "s.t", body)
    out, renamed, dropped, _ = run(tmp_path, ddl_for("s.t", ["state"]), metrics)
    assert out == metrics and not renamed and dropped == 0


# --- the collision the rename itself can create --------------------------------

def test_a_rename_that_would_duplicate_a_healthy_dimension_yields_to_it(tmp_path):
    metrics = view("t", "s.t",
                   DIMS % ("profile_id", "profile_id")
                   + DIMS % ("guest_profile_id", "guest_profile_id"))
    out, renamed, dropped, _ = run(tmp_path, ddl_for("s.t", ["profile_id"]), metrics)
    assert out.count('- name: "profile_id"') == 1
    assert "guest_profile_id" not in out
    assert dropped == 1 and sum(renamed.values()) == 0


def test_two_logical_names_collapsing_onto_one_column_emit_one_dimension(tmp_path):
    metrics = view("t", "s.t",
                   DIMS % ("guest_profile_id", "guest_profile_id")
                   + DIMS % ("preference_guest_profile_id", "preference_guest_profile_id"))
    out, renamed, dropped, _ = run(tmp_path, ddl_for("s.t", ["profile_id"]), metrics)
    assert out.count('- name: "profile_id"') == 1
    assert dropped == 1 and sum(renamed.values()) == 1


# --- multi-view files ----------------------------------------------------------

def test_only_the_drifted_view_in_a_file_is_touched(tmp_path):
    clean = view("clean", "s.a", DIMS % ("a_id", "a_id"))
    dirty = view("dirty", "s.b", DIMS % ("origin_b_id", "origin_b_id"))
    ddl = ddl_for("s.a", ["a_id"]) + ddl_for("s.b", ["b_id"])
    out, renamed, dropped, views = run(tmp_path, ddl, clean + dirty)
    assert out.startswith(clean)
    assert "expr: b_id" in out and "origin_b_id" not in out
    assert views == 1


def test_a_view_whose_source_table_is_not_in_this_ddl_is_left_alone(tmp_path):
    metrics = view("t", "other.table", DIMS % ("origin_plant_id", "origin_plant_id"))
    out, renamed, dropped, views = run(tmp_path, ddl_for("s.t", ["plant_id"]), metrics)
    assert out == metrics and views == 0
