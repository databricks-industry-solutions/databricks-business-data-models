import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_source_util import notebook_concat_source  # noqa: E402

SRC = notebook_concat_source()

GATE_OLD = "if _mv_failed_ct > 0 or _mv_fallback_statements:"
GATE_NEW = "if metric_view_statements:"
END = 'print(f"   \U0001f9f9 Metric cleanup:'


def rewrite_block():
    """The metric-artifact rewrite block, lifted out of the notebook and dedented."""
    anchor = SRC.find("_mv_failed_ct = len(metric_exec_result")
    start = SRC.find(GATE_NEW, anchor)
    if start < 0:
        start = SRC.find(GATE_OLD, anchor)
    assert start >= 0, "could not locate the metric-artifact rewrite gate"
    start = SRC.rfind("\n", 0, start) + 1  # keep the gate's own indentation
    end = SRC.find(END, start)
    assert end > start, "could not locate the end of the rewrite block"
    end = SRC.find("\n", end)
    return textwrap.dedent(SRC[start:end])


def run_block(statements, failed=(), fallback=None, domains=("retail",)):
    """Execute the real block; return the files it wrote to the volume."""
    written = {}

    def write_to_dbfs(content, path, _logger=None):
        written[path] = content

    ns = {
        "metric_view_statements": list(statements),
        "metric_exec_result": {"failed": list(failed), "total": len(statements)},
        "_mv_failed_ct": len(failed),
        "_mv_fallback_statements": dict(fallback or {}),
        "widgets_values": {
            "current_version": "1",
            "model_scope": "mvm",
            "domains": [{"domain": d} for d in domains],
            "_metric_view_to_domain_map": {},
        },
        "config": {"TARGET_VOLUME": "/Volumes/cat/_metamodel/vol_root"},
        "business_name": "coffee_roastery",
        "logger": type("L", (), {"info": lambda *a, **k: None,
                                 "warning": lambda *a, **k: None})(),
        "datetime": datetime,
        "write_to_dbfs": write_to_dbfs,
        "sanitize_name": lambda s: str(s).strip().lower().replace(" ", "_"),
        "_get_file_sql_name": lambda *a, **k: "coffee_roastery",
        "_extract_metric_view_name_from_statement": lambda s: (
            re.search(r"VIEW\s+`?[\w.`]*?`?\.?`?(\w+)`?\s", s + " ").group(1)
        ),
    }
    exec(compile(rewrite_block(), "<rewrite_block>", "exec"), ns)
    return written, ns["widgets_values"]


def mv(name, column):
    return (
        "CREATE OR REPLACE VIEW `cat`.`_metrics`.`%s` "
        "WITH METRICS LANGUAGE YAML AS $$ measures: - name: n expr: SUM(%s) $$" % (name, column)
    )


def test_a_pruned_view_reaches_the_artifact_even_though_nothing_failed():
    """The coffee_roastery regression, in miniature.

    mv-column-prevalidate-prune rewrote retail_loyalty_account in memory (dropping the
    renamed preferred_store_id), the view then built cleanly, and nothing failed. Before
    v4.8.5 the gate needed a failure or a ladder fallback to open, so the volume kept the
    unpruned SQL and every consumer that installed the published model hit
    UNRESOLVED_COLUMN on a view the agent itself never executed.
    """
    executed = mv("retail_loyalty_account", "store_id")
    written, _ = run_block([executed], failed=(), fallback=None)

    assert written, "no artifact written: the pruned statement never reached the volume"
    content = "".join(written.values())
    assert "store_id" in content
    assert "preferred_store_id" not in content


def test_the_artifact_is_written_from_the_statements_that_executed():
    executed = [mv("retail_orders", "amount"), mv("retail_loyalty_account", "store_id")]
    written, _ = run_block(executed)
    content = "".join(written.values())
    for stmt in executed:
        assert stmt in content


def test_a_failed_view_is_still_stripped_from_the_artifact():
    """v4.8.3's behaviour must survive: a view that failed does not ship."""
    good, bad = mv("retail_orders", "amount"), mv("retail_broken", "ghost_col")
    written, wv = run_block([good, bad], failed=[("retail_broken", "UNRESOLVED_COLUMN")])
    content = "".join(written.values())
    assert "retail_orders" in content
    assert "retail_broken" not in content
    assert wv["metric_view_count"] == 1


def test_a_ladder_repair_is_still_persisted():
    """v4.8.3's other path: the repaired statement is what gets written."""
    repaired = mv("retail_orders", "net_amount")
    written, _ = run_block([repaired], fallback={"retail_orders": repaired})
    assert "net_amount" in "".join(written.values())


def test_an_unmutated_run_writes_the_same_bytes_it_would_have_shipped():
    """Mirroring unconditionally is only safe if the no-mutation case is a no-op in
    content terms. Two identical runs must produce identical files."""
    stmts = [mv("retail_orders", "amount")]
    first, _ = run_block(stmts)
    second, _ = run_block(stmts)
    strip = lambda d: {k: re.sub(r"Generated on: [\d\-: ]+", "", v) for k, v in d.items()}
    assert strip(first) == strip(second)


def test_a_domain_whose_views_all_failed_gets_an_emptied_file_not_a_stale_one():
    bad = mv("retail_broken", "ghost_col")
    written, _ = run_block([bad], failed=[("retail_broken", "UNRESOLVED_COLUMN")])
    assert written, "the stale file was left on the volume"
    assert "retail_broken" not in "".join(written.values())


def test_the_gate_no_longer_waits_for_a_failure_or_a_fallback():
    """Pins the root-cause shape, so a future edit cannot quietly re-narrow the gate."""
    assert GATE_OLD not in SRC, "the rewrite is gated on failure/fallback again"
    assert GATE_NEW in SRC


def test_the_block_reports_itself_so_a_live_run_can_be_audited():
    assert "mv-artifact-mirrors-executed FIRED v4.8.5" in SRC
    assert "alias=mv-artifact-mirrors-executed" in SRC


def test_the_agent_version_is_at_least_the_one_that_shipped_this_fix():
    m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', SRC)
    assert m, "no agent version literal found"
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 5), m.group(0)
