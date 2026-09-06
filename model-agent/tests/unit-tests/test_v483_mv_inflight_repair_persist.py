"""v4.8.3 — an in-flight metric-view repair must reach the shipped artifact.

When a metric view fails with UNRESOLVED_COLUMN the executor repairs it in the
worker (stale-column rewrite, DESCRIBE-driven rewrite, entry strip, safe
measures) and returns SUCCESS. Before this change the repaired SQL existed only
inside that worker: the statement written to metrics/*.sql and model.json stayed
the broken original. The agent's own catalog therefore had the view while every
consumer installing the published artifact lost it.

Live evidence: coffee_roastery v4.8.2 reported 24/24 views created; the
installer replaying the same artifact created 22/24, losing retail_order and
retail_loyalty_account to UNRESOLVED_COLUMN on `pickup_store_id`. A repo-wide
scan found 271 of 14904 shipped metric views in the same state.

`fallback_statements` is the channel the existing `mv-strict-parity-repair`
consumer already persists into the authoritative artifacts, so the repair sites
record into it rather than growing a second write path.
"""
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notebook_source_util import notebook_concat_source  # noqa: E402

FN = "execute_metric_views_in_parallel_no_halt"

UNRESOLVED = (
    "[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter "
    "with name `pickup_store_id` cannot be resolved. Did you mean one of the "
    "following? [`store_id`, `customer_email`]"
)

STMT = (
    "CREATE OR REPLACE VIEW `c`.`_metrics`.`retail_order`\n"
    "WITH METRICS\nLANGUAGE YAML\nAS $$\n  version: 1.1\n"
    '  source: "`c`.`retail`.`order`"\n'
    '  dimensions:\n    - name: "pickup_store"\n      expr: pickup_store_id\n'
    '  measures:\n    - name: "orders"\n      expr: COUNT(1)\n$$'
)


def _source():
    return notebook_concat_source()


def _slice_function(src, name):
    lines = src.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("def %s(" % name))
    end = start + 1
    while end < len(lines) and not (lines[end][:1] not in ("", " ", "\t")
                                    and lines[end].startswith("def ")):
        end += 1
    return "\n".join(lines[start:end])


class _Spark:
    """Stands in for Spark: rejects any statement still naming the stale column."""

    def __init__(self, heals_when):
        self.heals_when = heals_when
        self.executed = []

    def __call__(self, spark, stmt, logger, *a, **k):
        self.executed.append(stmt)
        if self.heals_when(stmt):
            return None
        raise Exception(UNRESOLVED)


def _run(execute_sql, statements=(STMT,)):
    """Execute the real production function against the smallest believable stubs."""
    ns = {
        "re": re,
        "time": __import__("time"),
        "logging": logging,
        "logger": logging.getLogger("v483"),
        "TimeoutError": TimeoutError,
        "_DEFAULT_FUTURE_TIMEOUT": 600,
        "execute_sql": execute_sql,
        "_extract_metric_view_name_from_statement": lambda s: "retail_order",
        "_ts": lambda: "00:00:00",
        "_fmt_hms": lambda s: "0s",
        "_format_eta": lambda *a, **k: "0s",
        "_flush_log_handlers": lambda *a, **k: None,
        "_sanitize_metric_stmt_nested_agg": lambda x=None, *a, **k: x,
        "_v458_metric_exception_detail": lambda e, hist=None: str(e),
    }

    class _Pool:
        def __init__(self, max_workers):
            self._e = ThreadPoolExecutor(max_workers=max_workers)

        def __enter__(self):
            return self._e

        def __exit__(self, *a):
            self._e.shutdown(wait=True)
            return False

    ns["guarded_thread_pool_executor"] = lambda mw, **kw: _Pool(mw)
    ns["_safe_as_completed"] = lambda f, timeout=None, logger=None, label=None: as_completed(f)
    exec(compile(_slice_function(_source(), FN), "<agent:%s>" % FN, "exec"), ns, ns)
    return ns[FN](None, list(statements), logging.getLogger("v483"), 2, None)


def _needs_repair():
    return _Spark(heals_when=lambda s: "pickup_store_id" not in s)


def test_a_view_repaired_in_flight_is_persisted_for_the_artifact():
    """The whole point: the SQL that worked is the SQL that ships."""
    spark = _needs_repair()
    result = _run(spark)

    assert result["failed"] == [], result["failed"]
    persisted = result["fallback_statements"]
    assert "retail_order" in persisted, (
        "the view was repaired in flight and reported SUCCESS, but nothing was "
        "recorded, so the broken original is what ships: %r" % (persisted,))
    assert "pickup_store_id" not in persisted["retail_order"]


def test_the_persisted_statement_is_one_that_actually_executed():
    """Guards against recording a reconstruction rather than the accepted text."""
    spark = _needs_repair()
    result = _run(spark)
    persisted = result["fallback_statements"]["retail_order"].rstrip().rstrip(";")
    accepted = [s.rstrip().rstrip(";") for s in spark.executed if "pickup_store_id" not in s]
    assert persisted in accepted, "persisted statement was never executed successfully"


def test_a_repaired_view_is_named_in_the_repaired_list():
    result = _run(_needs_repair())
    assert "retail_order" in result["fallback_repaired"]


def test_a_view_that_needs_no_repair_records_nothing():
    """Guard: blanket-recording every view would make the channel meaningless."""
    result = _run(_Spark(heals_when=lambda s: True))
    assert result["failed"] == []
    assert result["fallback_statements"] == {}, result["fallback_statements"]
    assert result["fallback_repaired"] == []


def test_the_persisted_statement_carries_no_trailing_semicolon():
    """The artifact writer joins on ';', so a stored ';' would double it."""
    result = _run(_needs_repair())
    assert not result["fallback_statements"]["retail_order"].rstrip().endswith(";")


def test_an_unrepairable_view_is_still_reported_failed():
    """Guard: the repair channel must not launder a genuine failure into success."""
    result = _run(_Spark(heals_when=lambda s: False))
    assert result["failed"], "an unrepairable view must surface as failed"


def test_every_repair_path_records_its_statement():
    """Backstop: a repair path added later without recording is the same bug again.

    The first success return is the untouched happy path -- it executes the original
    `stmt`, so recording there would be wrong (and is pinned against by
    test_a_view_that_needs_no_repair_records_nothing). Every OTHER success return is
    reached only after the ladder rewrote the statement, so each must record.
    """
    body = _slice_function(_source(), FN)
    ladder = body[body.index("def _tracked_sql("):]
    successes = [m.start() for m in re.finditer(r'return \("SUCCESS"', ladder)]
    assert len(successes) >= 7, "expected the happy path plus the repair ladder"

    unrecorded = []
    for pos in successes:
        window = ladder[max(0, pos - 700):pos]
        executed = re.findall(r"execute_sql\(spark,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,", window)
        if not executed or executed[-1] == "stmt":
            continue  # happy path: the original statement is already what ships
        if "_v483_record_repair(" not in window:
            unrecorded.append(ladder[max(0, pos - 240):pos + 60])
    assert not unrecorded, (
        "%d repair path(s) return SUCCESS without recording the repaired statement:"
        "\n%s" % (len(unrecorded), "\n---\n".join(unrecorded)))


def test_the_happy_path_is_not_treated_as_a_repair():
    """Pins the exclusion above so it cannot silently swallow a real repair site."""
    body = _slice_function(_source(), FN)
    ladder = body[body.index("def _tracked_sql("):]
    first = ladder.index('return ("SUCCESS"')
    window = ladder[max(0, first - 700):first]
    assert re.findall(r"execute_sql\(spark,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,", window)[-1] == "stmt"
    assert "_v483_record_repair(" not in window


def _apply_step_source():
    """The body of step_apply_metric_views, where the artifact rewrite is decided."""
    src = _source()
    body = _slice_function(src, "step_apply_metric_views")
    assert "_mv_fallback_statements" in body, "wrong function sliced"
    return body


def _gate_index(body):
    """Locate the artifact-rewrite gate, in whichever form currently ships.

    v4.8.3 opened it on `_mv_failed_ct > 0 or _mv_fallback_statements`; v4.8.5 widened it
    to mirror the executed statements unconditionally. Both satisfy this module's intent,
    so the tests match on position rather than on one literal condition.
    """
    for gate in ("\n    if metric_view_statements:\n", "\n    if _mv_failed_ct > 0"):
        at = body.find(gate)
        if at >= 0:
            return at + 1
    raise AssertionError("the artifact-rewrite gate was not found")


def test_the_artifact_rewrite_also_fires_when_only_repairs_happened():
    """A run with 0 failures and N repairs must still rewrite metrics/*.sql.

    The in-memory substitution reaches model.json, but the .sql file on the volume is
    what a consumer replays. Gating the rewrite on failures alone is how
    coffee_roastery shipped 2 broken views while reporting 0 failures.
    """
    body = _apply_step_source()
    gate_line = body[_gate_index(body):body.index("\n", _gate_index(body))]
    assert "_mv_failed_ct > 0" not in gate_line or "_mv_fallback_statements" in gate_line, (
        "the rewrite is gated on failures only, so a repair-only run ships the "
        "original broken SQL: %r" % gate_line.strip())


def test_the_repaired_statements_are_substituted_before_the_files_are_written():
    """Order matters: substituting after the write would persist the broken text."""
    body = _apply_step_source()
    substitution = body.index("mv-strict-parity-repair FIRED")
    gate = _gate_index(body)
    assert substitution < gate, (
        "the repaired statements are substituted after the artifact rewrite, so the "
        "files are written from the pre-repair list")


def test_the_files_are_written_from_the_substituted_statement_list():
    """Pins the data path: the rewrite must read the list the substitution updated."""
    body = _apply_step_source()
    block = body[_gate_index(body):]
    assert "for _stmt in metric_view_statements:" in block, (
        "the rewrite no longer iterates the substituted list")
    assert "_surviving_by_domain.setdefault(_domain_key, []).append(_stmt)" in block
    assert '";\\n\\n".join(_domain_stmts)' in block, "the file content is built elsewhere now"


def test_the_agent_version_is_at_least_the_one_that_shipped_this_fix():
    m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', _source())
    assert m, "no __AGENT_VERSION__ found"
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 3), m.group(0)
