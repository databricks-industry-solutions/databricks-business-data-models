"""v4.6.7 behavioral test -- mv-abandoned-reconcile.

Root cause it guards: execute_metric_views_in_parallel_no_halt submits one future
per metric-view DDL, then iterates _safe_as_completed(futures, timeout=pool_timeout).
_safe_as_completed catches TimeoutError, cancels the still-unfinished futures, and
STOPS yielding. Any future unfinished at pool_timeout was therefore never installed,
never fallback-repaired, never appended to `failures` -- yet `succeeded =
total_statements - len(failures)` counted it as succeeded. The MV then surfaced as
`missing` at the physical-parity gate and hard-failed the whole run (WCB Alberta
v4.6.6 run 908193301348249, missing=['claim_cost_summary','claim_eligibility_determination']).

This test drives the REAL sliced function with a stubbed executor where exactly one
submitted future is never yielded by _safe_as_completed (i.e. abandoned at
pool_timeout). It proves:

  * pass-post (working tree): the abandoned MV is reconciled -- fallback is attempted,
    and because the fallback install is blocked in this harness it is recorded as an
    explicit failure, so `succeeded` drops to total-1 (no silent success).
  * fail-pre (same source with ONLY the reconcile block removed): the abandoned MV
    silently vanishes -- `failures` stays empty and `succeeded` == total (the bug).

The fail-pre baseline is derived by deterministically removing the reconcile block
from the SAME working-tree source (anchored on the v4.6.7 sentinel), so the proof
does not depend on git HEAD moving after the fix is committed.
"""
import contextlib
import re as _real_re
import time as _real_time

import pytest

from notebook_source_util import (
    agent_version_line,
    notebook_concat_source,
    slice_function_source,
)

MAIN_FN = "execute_metric_views_in_parallel_no_halt"
_EXTRACTORS = [
    "_extract_metric_view_name_from_statement",
    "_extract_metric_view_source_from_statement",
    "_extract_metric_view_target_from_statement",
]

ABANDONED = "claim_cost_summary"
YIELDED = ["claim_eligibility_determination", "premium_assessment_summary"]


def _stmt(view):
    return (
        f'CREATE OR REPLACE VIEW `cat`.`sch`.`{view}`\n'
        f'WITH METRICS\nLANGUAGE YAML\nAS $$\n'
        f'  version: 1.1\n'
        f'  source: "cat.sch.{view}_src"\n'
        f'  dimensions:\n    - name: All\n      expr: "1"\n'
        f'  measures:\n    - name: N\n      expr: COUNT(1)\n$$'
    )


class _FakeFuture:
    def __init__(self, outcome):
        self._outcome = outcome

    def result(self, timeout=None):
        return self._outcome

    def cancel(self):
        return True


class _FakeExecutor:
    """submit(fn, stmt) -> future whose .result() reports SUCCESS for that stmt."""

    def submit(self, fn, stmt):
        name = stmt.split("`sch`.`", 1)[1].split("`", 1)[0]
        return _FakeFuture(("SUCCESS", name, ""))


class _CapLogger:
    def __init__(self):
        self.lines = []

    def _rec(self, msg):
        self.lines.append(str(msg))

    info = warning = error = debug = lambda self, msg, *a, **k: self._rec(msg)


def _strip_reconcile(main_src: str) -> str:
    """Return main_src with ONLY the v4.6.7 reconcile block removed (pre-patch shape).

    Anchored on the sentinel comment through to the line that both shapes share
    (`_mv_total_elapsed = time.time() - _mv_op_start`), which is left intact.
    """
    lines = main_src.splitlines(keepends=True)
    # Anchor on the reconcile BLOCK comment specifically (the helper carries the same
    # alias in its own comment, so match the distinctive "_safe_as_completed cancels" text).
    start = next(
        i for i, l in enumerate(lines)
        if "alias=mv-abandoned-reconcile" in l
        and "_safe_as_completed cancels" in l
        and l.lstrip().startswith("#")
    )
    end = next(
        i for i in range(start, len(lines))
        if lines[i].strip() == "_mv_total_elapsed = time.time() - _mv_op_start"
    )
    stripped = "".join(lines[:start] + lines[end:])
    assert "mv-abandoned-reconcile FIRED v4.6.7" not in stripped
    assert "_mv_total_elapsed = time.time() - _mv_op_start" in stripped
    return stripped


def _build_ns(main_src: str):
    src = notebook_concat_source()
    cap = _CapLogger()

    @contextlib.contextmanager
    def _guarded_pool(max_workers, pool_name=None, logger=None):
        yield _FakeExecutor()

    def _safe_as_completed(futures, timeout=None, logger=None, label=None):
        # Simulate pool_timeout: yield every future EXCEPT the abandoned one.
        for fut, stmt in futures.items():
            if ABANDONED in stmt:
                continue
            yield fut

    def _blocked_execute_sql(spark, sql, logger=None, *a, **k):
        raise RuntimeError("fallback install blocked in harness")

    class _SparkStub:
        def sql(self, q):
            raise RuntimeError("DESCRIBE: view does not exist (harness)")

    stubs = {
        "re": _real_re,
        "time": _real_time,
        "_DEFAULT_FUTURE_TIMEOUT": 1000,
        "guarded_thread_pool_executor": _guarded_pool,
        "_safe_as_completed": _safe_as_completed,
        "execute_sql": _blocked_execute_sql,
        "_v458_metric_exception_detail": lambda e, *a, **k: f"detail:{e}",
        # incidental preprocessor -- not under test; identity keeps statements intact
        "_sanitize_metric_stmt_nested_agg": lambda s, logger=None: s,
        "_ts": lambda: "TS",
        "_flush_log_handlers": lambda logger=None: None,
        "_fmt_hms": lambda x: "0:00",
        "_format_eta": lambda *a, **k: "eta",
        "logger": cap,
    }
    blob = "\n\n".join(slice_function_source(n, source=src) for n in _EXTRACTORS)
    blob += "\n\n" + main_src
    ns = {"__name__": "_test_v467_slice"}
    ns.update(stubs)
    exec(compile(blob, "test_v467_mv_abandoned_reconcile", "exec"), ns)
    return ns, cap, _SparkStub()


def _run(main_src):
    ns, cap, spark = _build_ns(main_src)
    statements = [_stmt(YIELDED[0]), _stmt(ABANDONED), _stmt(YIELDED[1])]
    result = ns[MAIN_FN](spark, statements, cap, max_workers=20, concurrency_manager=None)
    failed_names = {f[0] for f in result["failed"]}
    return result, failed_names, cap.lines


def test_post_patch_reconciles_abandoned_future():
    """Working tree: abandoned MV is reconciled, not silently counted as succeeded."""
    main_src = slice_function_source(MAIN_FN)
    result, failed_names, log = _run(main_src)

    assert result["total"] == 3
    # The abandoned future's fallback is blocked in this harness, so it MUST be
    # recorded as a failure -- never silently dropped.
    assert ABANDONED in failed_names, (
        f"abandoned MV not reconciled into failures: {failed_names}"
    )
    assert result["succeeded"] == 2, (
        f"succeeded must exclude the abandoned MV, got {result['succeeded']}"
    )
    assert any("mv-abandoned-reconcile FIRED v4.6.7" in l for l in log)


def test_pre_patch_silently_drops_abandoned_future():
    """Reconcile block removed: the bug reappears -- abandoned MV vanishes silently."""
    main_src = slice_function_source(MAIN_FN)
    pre_src = _strip_reconcile(main_src)
    result, failed_names, log = _run(pre_src)

    assert result["total"] == 3
    assert ABANDONED not in failed_names
    # The bug: abandoned future counted as succeeded (would surface as `missing`).
    assert result["succeeded"] == 3
    assert not any("mv-abandoned-reconcile FIRED v4.6.7" in l for l in log)


def test_version_pinned_and_helper_present():
    src = notebook_concat_source()
    assert agent_version_line() in src
    assert src.count("def _v467_install_mv_fallback") == 1
    assert "mv-abandoned-reconcile FIRED v4.6.7" in src
