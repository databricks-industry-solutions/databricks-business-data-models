"""v4.6.8 behavioral tests for the three root-cause fixes shipped after the WCB
Alberta v4.6.7 FAILED run (missing=['workforce_case_officer_assignment'] + R3 log
clobber + false-red FK ERROR spam).

FIX B (CRITICAL) -- bulletproof MV fallback source resolution:
  * mv-source-extract-robust: _extract_metric_view_source_from_statement now
    recovers an unquoted / backticked `source:` line, so the row-count fallback
    is never starved of a source just because the LLM emitted the YAML without
    surrounding quotes.
  * mv-source-derive-physical: _v468_derive_mv_source_from_target derives the real
    base table from the LIVE catalog by matching <schema>_<table> == mv-name, so a
    declared MV whose statement source is unrecoverable can STILL get a working
    fallback for any existing base table -> it can never be silently `missing` at
    the physical-parity gate.

FIX A (CRITICAL) -- log-retry-preserve: a platform retry must not clobber the
  prior attempt's volume log (R3). Structural proof the sidecar-preserve block is
  wired into step_setup_and_clean with attempt-scoped naming.

FIX C (HIGH) -- fk-skip-downgrade: an intentionally cycle-guard-blocked FK must not
  log `❌ FAILED to create FK` at ERROR (trips §10.6 zero-ERROR gate). Structural
  proof all three caller sites emit at INFO with the downgrade alias.

Each FIX B test derives its fail-pre baseline from the SAME working-tree source so
the proof does not depend on git HEAD.
"""
import re as _real_re

import pytest

from notebook_source_util import (
    agent_version_line,
    notebook_concat_source,
    slice_function_source,
)

EXTRACT_FN = "_extract_metric_view_source_from_statement"
DERIVE_FN = "_v468_derive_mv_source_from_target"


class _CapLogger:
    def __init__(self):
        self.lines = []

    def _rec(self, msg):
        self.lines.append(str(msg))

    info = warning = error = debug = lambda self, msg, *a, **k: self._rec(msg)


class _FakeRow(dict):
    def __getitem__(self, k):
        return dict.__getitem__(self, k)


class _FakeDF:
    def __init__(self, rows):
        self._rows = rows

    def collect(self):
        return self._rows


class _FakeSpark:
    def __init__(self, rows):
        self._rows = rows
        self.sql_calls = []

    def sql(self, q):
        self.sql_calls.append(q)
        return _FakeDF(self._rows)


def _exec(fn_name, extra=None, source=None):
    src = slice_function_source(fn_name, source=source)
    ns = {"__name__": f"_slice_{fn_name}", "re": _real_re}
    if extra:
        ns.update(extra)
    exec(compile(src, "<slice>", "exec"), ns)
    return ns[fn_name]


# --------------------------------------------------------------------------- #
# FIX B-1  mv-source-extract-robust                                            #
# --------------------------------------------------------------------------- #
def _strip_robust_branch(extract_src: str) -> str:
    """Remove ONLY the v4.6.8 last-resort branch to recreate the pre-patch shape."""
    lines = extract_src.splitlines(keepends=True)
    start = next(
        i for i, l in enumerate(lines)
        if "alias=mv-source-extract-robust" in l and l.lstrip().startswith("#")
    )
    end = next(
        i for i in range(start, len(lines))
        if lines[i].strip() == "return None"
    )
    stripped = "".join(lines[:start] + lines[end:])
    assert "mv-source-extract-robust" not in stripped
    assert stripped.rstrip().endswith("return None")
    return stripped


UNQUOTED_STMT = (
    "CREATE OR REPLACE VIEW `cat`.`_metrics`.`workforce_case_officer_assignment`\n"
    "WITH METRICS\nLANGUAGE YAML\nAS $$\n"
    "  version: 1.1\n"
    "  source: cat.workforce.case_officer_assignment\n"
    "  dimensions:\n    - name: All\n      expr: 1\n"
    "  measures:\n    - name: N\n      expr: COUNT(1)\n$$"
)
QUOTED_STMT = UNQUOTED_STMT.replace(
    "source: cat.workforce.case_officer_assignment",
    'source: "cat.workforce.case_officer_assignment"',
)


def test_extract_source_quoted_unchanged():
    """Regression guard: the two strict quoted patterns still win (no behaviour drift)."""
    extract = _exec(EXTRACT_FN)
    assert extract(QUOTED_STMT) == "cat.workforce.case_officer_assignment"


def test_extract_source_unquoted_passpost():
    """pass-post: robust branch recovers an UNQUOTED source line."""
    extract = _exec(EXTRACT_FN)
    assert extract(UNQUOTED_STMT) == "cat.workforce.case_officer_assignment"


def test_extract_source_unquoted_failpre():
    """fail-pre: with the robust branch removed, the unquoted source is lost (None)."""
    pre_src = _strip_robust_branch(slice_function_source(EXTRACT_FN))
    ns = {"__name__": "_pre", "re": _real_re}
    exec(compile(pre_src, "<pre>", "exec"), ns)
    assert ns[EXTRACT_FN](UNQUOTED_STMT) is None


# --------------------------------------------------------------------------- #
# FIX B-2  mv-source-derive-physical                                          #
# --------------------------------------------------------------------------- #
def test_derive_source_from_physical_catalog():
    """pass-post: the WCB failure MV name maps back to its real base table.

    The v4.6.7 fallback had NO way to find a source when extraction failed, so the
    MV stayed missing. The v4.6.8 derive helper matches <schema>_<table> == mv-name
    against information_schema and returns the backticked base-table triple.
    """
    derive = _exec(DERIVE_FN)
    spark = _FakeSpark([
        _FakeRow(table_schema="workforce", table_name="case_officer_assignment"),
        _FakeRow(table_schema="workforce", table_name="case_officer"),
        _FakeRow(table_schema="claims", table_name="claim"),
    ])
    log = _CapLogger()
    target = "`cat`.`_metrics`.`workforce_case_officer_assignment`"
    out = derive(spark, target, log)
    assert out == "`cat`.`workforce`.`case_officer_assignment`"
    assert any("mv-source-derive-physical FIRED" in l for l in log.lines)
    # queries the live catalog's information_schema for the owning catalog
    assert spark.sql_calls and "information_schema.tables" in spark.sql_calls[0]
    assert "`cat`.information_schema.tables" in spark.sql_calls[0]


def test_derive_source_prefers_longest_correct_split():
    """A schema/table split must reconstruct EXACTLY -- no false match on a shorter
    table whose schema+'_'+table only prefixes the mv-name."""
    derive = _exec(DERIVE_FN)
    spark = _FakeSpark([
        _FakeRow(table_schema="workforce", table_name="case"),  # workforce_case != target
        _FakeRow(table_schema="workforce", table_name="case_officer_assignment"),
    ])
    target = "`cat`.`_metrics`.`workforce_case_officer_assignment`"
    assert derive(spark, target, _CapLogger()) == "`cat`.`workforce`.`case_officer_assignment`"


def test_derive_source_returns_none_when_no_base_table():
    """No matching base table -> None (fallback then records an explicit failure, not
    a silent success)."""
    derive = _exec(DERIVE_FN)
    spark = _FakeSpark([_FakeRow(table_schema="claims", table_name="claim")])
    target = "`cat`.`_metrics`.`workforce_case_officer_assignment`"
    assert derive(spark, target, _CapLogger()) is None


def test_derive_source_malformed_target_none():
    derive = _exec(DERIVE_FN)
    spark = _FakeSpark([])
    assert derive(spark, "not-a-triple", _CapLogger()) is None
    assert derive(spark, None, _CapLogger()) is None


# --------------------------------------------------------------------------- #
# FIX B-3  fallback wires derive as a candidate source                        #
# --------------------------------------------------------------------------- #
def test_fallback_calls_derive_helper():
    """Structural: the fallback installer must try the physically-derived source in
    addition to the extracted one (mv-fallback-bulletproof)."""
    src = notebook_concat_source()
    assert "alias=mv-fallback-bulletproof" in src
    # derive helper is invoked inside the fallback and its result appended as a candidate
    assert "_fb_derived = _v468_derive_mv_source_from_target(spark, _fb_target, logger)" in src
    assert "for _fb_source in _fb_sources:" in src


# --------------------------------------------------------------------------- #
# FIX A  log-retry-preserve                                                    #
# --------------------------------------------------------------------------- #
def test_log_retry_preserve_wired_into_setup():
    setup_src = slice_function_source("step_setup_and_clean")
    assert "alias=log-retry-preserve" in setup_src
    # attempt-scoped sidecar naming keyed on the task run id -> a retry cannot collide
    assert ".attempt-{_lrp_marker}.log" in setup_src
    assert "databricks_task_run_id" in setup_src
    # preserves both the info and error volume logs, and only when non-empty
    assert "for _lrp_vol in (info_log_path, error_log_path):" in setup_src
    assert "os.path.getsize(_lrp_vol) > 0" in setup_src
    assert "[log-retry-preserve FIRED v4.6.8]" in setup_src


# --------------------------------------------------------------------------- #
# FIX C  fk-skip-downgrade                                                     #
# --------------------------------------------------------------------------- #
def test_fk_skip_downgrade_no_false_red_error():
    """All three cycle-guard-blocked FK sites log at INFO with the downgrade alias,
    and none of them emit the old `❌ FAILED to create FK` ERROR that trips §10.6."""
    src = notebook_concat_source()
    assert src.count("alias=fk-skip-downgrade-v4.6.8") == 3
    # the downgraded message text is present...
    assert "↳ FK not created (guard/validation reason logged above)" in src
    # ...and it is emitted via .info( at every downgrade site, never .error(
    for m in _real_re.finditer(r"fk-skip-downgrade-v4\.6\.8", src):
        head = src[max(0, m.start() - 260):m.start()]
        assert ".info(" in head, "downgrade site must log at INFO"
        assert "❌ FAILED to create FK" not in head


def test_agent_version_pinned_468():
    src = notebook_concat_source()
    assert agent_version_line() in src
