import concurrent.futures
import re
import time

import pytest

from notebook_source_util import exec_function_namespace, exec_functions_namespace


class Logger:
    def __init__(self):
        self.info_lines = []
        self.warning_lines = []
        self.error_lines = []

    def info(self, message):
        self.info_lines.append(message)

    def warning(self, message):
        self.warning_lines.append(message)

    def error(self, message):
        self.error_lines.append(message)

    def debug(self, message):
        pass


class EmptySparkError(Exception):
    def __str__(self):
        return ""

    def getErrorClass(self):
        return "UNRESOLVED_COLUMN"

    def getSqlState(self):
        return "42703"


STATEMENT = """CREATE OR REPLACE VIEW `cat`.`_metrics`.`orders`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  source: "`cat`.`sales`.`orders`"
  measures:
    - name: Broken
      expr: "missing_column"
$$"""


def _executor_namespace(execute):
    def pool(max_workers, **kwargs):
        return concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def view_name(statement):
        match = re.search(r"`_metrics`\.`([^`]+)`", statement)
        return match.group(1) if match else "unknown_metric_view"

    return exec_functions_namespace(
        [
            "_v458_metric_exception_detail",
            "_v469_build_mv_rowcount_fallback",
            "execute_metric_views_in_parallel_no_halt",
        ],
        {
            # v4.6.8 widened the fallback to a candidate list; the derivation probe needs a
            # live catalog, so the extracted source stays the only candidate here.
            "_v468_derive_mv_source_from_target": lambda spark, target, logger: None,
            "re": re,
            "time": time,
            "_sanitize_metric_stmt_nested_agg": lambda statement, logger: statement,
            "_extract_metric_view_name_from_statement": view_name,
            "_extract_metric_view_target_from_statement": lambda statement: "`cat`.`_metrics`.`orders`",
            "_extract_metric_view_source_from_statement": lambda statement: "`cat`.`sales`.`orders`",
            "execute_sql": execute,
            "guarded_thread_pool_executor": pool,
            "_safe_as_completed": lambda futures, **kwargs: concurrent.futures.as_completed(
                futures
            ),
            "_DEFAULT_FUTURE_TIMEOUT": 30,
            "_ts": lambda: "now",
            "_flush_log_handlers": lambda logger: None,
            "_format_eta": lambda *args: "0s",
            "_fmt_hms": lambda seconds: f"{seconds:.2f}s",
        },
    )


def test_empty_metric_exception_preserves_actionable_diagnostics():
    helper = exec_function_namespace("_v458_metric_exception_detail")[
        "_v458_metric_exception_detail"
    ]
    detail = helper(EmptySparkError(), ["first attempt"])

    assert "EmptySparkError" in detail
    assert "repr=EmptySparkError()" in detail
    assert "error_class=UNRESOLVED_COLUMN" in detail
    assert "sqlstate=42703" in detail
    assert "retry_history=[first attempt]" in detail


def test_fallback_success_has_zero_final_failures_and_parity():
    calls = []

    def execute(spark, statement, logger):
        calls.append(statement)
        if "FALLBACK:" not in statement:
            raise EmptySparkError()

    ns = _executor_namespace(execute)
    logger = Logger()
    result = ns["execute_metric_views_in_parallel_no_halt"](
        object(), [STATEMENT], logger, max_workers=1, timeout_per_stmt=5
    )

    assert result["failed"] == []
    assert result["succeeded"] == 1
    assert result["fallback_repaired"] == ["orders"]
    assert "FALLBACK:" in result["fallback_statements"]["orders"]
    assert any("mv-fallback-emit-live FIRED" in line for line in logger.info_lines)
    assert any(
        "mv-strict-parity-repair FIRED v4.5.8" in line
        for line in logger.info_lines
    )
    assert logger.error_lines == []

    count_ns = exec_functions_namespace(
        [
            "_validate_metric_view_count",
            "_v458_metric_physical_parity",
            "_v458_require_metric_view_parity",
        ]
    )
    audit = count_ns["_validate_metric_view_count"](1, 0, len(result["failed"]))
    assert count_ns["_v458_require_metric_view_parity"](audit) is audit
    assert audit["installed_count"] == audit["declared_metric_view_count"] == 1
    physical = count_ns["_v458_metric_physical_parity"](["orders"], ["orders"])
    assert physical["parity"] is True
    assert physical["missing"] == physical["extra"] == []


def test_fallback_failure_is_a_hard_parity_failure():
    def execute(spark, statement, logger):
        raise EmptySparkError()

    ns = _executor_namespace(execute)
    result = ns["execute_metric_views_in_parallel_no_halt"](
        object(), [STATEMENT], Logger(), max_workers=1, timeout_per_stmt=5
    )

    assert len(result["failed"]) == 1
    assert "EmptySparkError" in result["failed"][0][1]
    assert "retry_history=" in result["failed"][0][1]

    count_ns = exec_functions_namespace(
        [
            "_validate_metric_view_count",
            "_v458_metric_physical_parity",
            "_v458_require_metric_view_parity",
        ]
    )
    audit = count_ns["_validate_metric_view_count"](1, 0, len(result["failed"]))
    with pytest.raises(RuntimeError, match="declared=1, installed=0"):
        count_ns["_v458_require_metric_view_parity"](audit)
    physical = count_ns["_v458_metric_physical_parity"](["orders"], [])
    assert physical["parity"] is False
    assert physical["missing"] == ["orders"]
