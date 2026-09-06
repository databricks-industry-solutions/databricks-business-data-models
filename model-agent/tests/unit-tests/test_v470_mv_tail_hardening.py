"""v4.7.0 behavioral tests: metric-view TAIL hardening from the full-code audit.

The last 3 WCB Alberta ECM runs (v4.6.7/8/9) all died in the MV-install/parity tail. A
line-by-line audit of that tail found 4 impactful latent bugs. These tests prove each fix
fail-pre/pass-post using the SAME working-tree source (no git dependency):

Finding #2 (CRITICAL, root cause) mv-extract-*-tolerant: name/target extraction only matched
  fully-backticked triples, so an unbackticked CREATE VIEW target returned 'unknown_metric_view'
  / None -> poisoned declared-vs-physical parity into a permanent missing+extra hard-fail.
Finding #1 (CRITICAL) mv-parity-extra-nonfatal: the gate hard-raised on any `extra` physical
  MV (e.g. orphan from a prior attempt); extra is harmless and must never kill the run.
Finding #3/#5 (CRITICAL) mv-invalid-absent-base-drop + mv-count-audit-nonfatal: one MV whose
  base table was never built hard-failed the whole 3h run; it is an invalid declaration to
  surface, not an install failure. A GENUINE failure (base table exists) still hard-fails.
Finding #4 (HIGH) mv-prevalidate-tables-fallback: a failed catalog-wide COLUMNS fetch disabled
  ALL existence gating; degrade to the smaller TABLES query so existence drops still fire.
"""
import re as _real_re

import pytest

from notebook_source_util import (
    agent_version_line,
    notebook_concat_source,
    slice_function_source,
)


# --------------------------------------------------------------------------- #
# harness                                                                      #
# --------------------------------------------------------------------------- #
class _CapLogger:
    def __init__(self):
        self.lines = []

    def _rec(self, msg):
        self.lines.append(str(msg))

    info = warning = error = debug = lambda self, msg, *a, **k: self._rec(msg)


class _FakeDF:
    def __init__(self, rows):
        self._rows = rows

    def collect(self):
        return self._rows


class _FakeSpark:
    """Returns a fixed row set for every .sql() (enough to drive existence-probe logic).
    Optionally raise from .sql() to simulate a failed information_schema query."""

    def __init__(self, rows=None, raise_on=None):
        self._rows = rows if rows is not None else []
        self._raise_on = raise_on

    def sql(self, q):
        if self._raise_on and self._raise_on in q:
            raise RuntimeError("simulated information_schema failure")
        return _FakeDF(list(self._rows))


def _ns_for(*fn_names, stubs=None):
    ns = {"re": _real_re}
    for fn in fn_names:
        exec(compile(slice_function_source(fn), "<slice>", "exec"), ns)
    if stubs:
        ns.update(stubs)
    return ns


# --------------------------------------------------------------------------- #
# Finding #2 — extraction tolerance (root cause)                               #
# --------------------------------------------------------------------------- #
BACKTICKED = "CREATE OR REPLACE VIEW `cat`.`_metrics`.`myview` WITH METRICS LANGUAGE YAML AS $$ x $$"
UNBACKTICKED = "CREATE OR REPLACE VIEW cat._metrics.myview WITH METRICS LANGUAGE YAML AS $$ x $$"
MIXED = "CREATE OR REPLACE VIEW `cat`._metrics.`myview` WITH METRICS LANGUAGE YAML AS $$ x $$"
SPACED = "CREATE OR REPLACE VIEW cat . _metrics . myview WITH METRICS LANGUAGE YAML AS $$ x $$"

# pre-patch behaviour reproduced inline (strict-backticked-only patterns) for the fail-pre proof
_OLD_NAME_PATTERNS = [
    r"CREATE\s+OR\s+REPLACE\s+VIEW\s+`[^`]+`\.`[^`]+`\.`([^`]+)`",
    r"CREATE\s+VIEW\s+`[^`]+`\.`[^`]+`\.`([^`]+)`",
]


def _old_extract_name(stmt):
    for p in _OLD_NAME_PATTERNS:
        m = _real_re.search(p, stmt, _real_re.IGNORECASE)
        if m:
            return m.group(1)
    return "unknown_metric_view"


def _name():
    return _ns_for("_extract_metric_view_name_from_statement")["_extract_metric_view_name_from_statement"]


def _target():
    return _ns_for("_extract_metric_view_target_from_statement")["_extract_metric_view_target_from_statement"]


def test_name_extract_failpre_unbackticked_returns_unknown():
    """fail-pre: the strict-backticked-only patterns return the poison sentinel on an
    unbackticked target — the exact input that produced missing=[unknown_metric_view]."""
    assert _old_extract_name(UNBACKTICKED) == "unknown_metric_view"
    assert _old_extract_name(MIXED) == "unknown_metric_view"


def test_name_extract_passpost_unbackticked_recovered():
    fn = _name()
    assert fn(UNBACKTICKED) == "myview"
    assert fn(MIXED) == "myview"
    assert fn(SPACED) == "myview"


def test_name_extract_backticked_regression_guard():
    """The tolerant pattern must NOT change behaviour for well-formed backticked targets."""
    assert _name()(BACKTICKED) == "myview"


def test_name_extract_still_unknown_on_junk():
    """A statement with no CREATE VIEW target at all still yields the sentinel (no false match)."""
    assert _name()("SELECT 1 FROM t") == "unknown_metric_view"


def test_target_extract_failpre_unbackticked_none():
    """fail-pre: pre-patch target extraction returned None on unbackticked targets, so
    self-heal/fallback could not rebuild them."""
    old = _real_re.search(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(`[^`]+`\.`[^`]+`\.`[^`]+`)", UNBACKTICKED, _real_re.IGNORECASE
    )
    assert old is None


def test_target_extract_passpost_normalized_backticked():
    fn = _target()
    assert fn(UNBACKTICKED) == "`cat`.`_metrics`.`myview`"
    assert fn(MIXED) == "`cat`.`_metrics`.`myview`"
    assert fn(SPACED) == "`cat`.`_metrics`.`myview`"
    # fully-backticked input is returned unchanged (first strict pattern still wins)
    assert fn(BACKTICKED) == "`cat`.`_metrics`.`myview`"


# --------------------------------------------------------------------------- #
# Finding #3/#5 — residual-missing classifier                                 #
# --------------------------------------------------------------------------- #
def _src_exists():
    return _ns_for("_v4610_source_table_exists")["_v4610_source_table_exists"]


def test_source_table_exists_true_when_row_returned():
    assert _src_exists()(_FakeSpark(rows=[(1,)]), "cat.schema.tbl") is True


def test_source_table_exists_false_when_empty():
    assert _src_exists()(_FakeSpark(rows=[]), "cat.schema.tbl") is False


def test_source_table_exists_false_on_bad_shape():
    fn = _src_exists()
    assert fn(_FakeSpark(rows=[(1,)]), None) is False
    assert fn(_FakeSpark(rows=[(1,)]), "only.two") is False


def test_source_table_exists_false_on_probe_exception():
    """A failed information_schema probe is treated as absent (conservative: an MV we cannot
    confirm has a base table is classified invalid, not genuine — never masks a real failure)."""
    assert _src_exists()(_FakeSpark(raise_on="information_schema"), "cat.schema.tbl") is False


def _classify(spark, derive_ret="`cat`.`schema`.`tbl`"):
    stubs = {
        "_v468_derive_mv_source_from_target": lambda sp, target, logger=None: derive_ret,
    }
    ns = _ns_for(
        "_extract_metric_view_source_from_statement",
        "_v4610_source_table_exists",
        "_v4610_classify_residual_missing",
        stubs=stubs,
    )
    return ns["_v4610_classify_residual_missing"]


_MV_WITH_SRC = (
    "CREATE OR REPLACE VIEW `cat`.`_metrics`.`m1`\nWITH METRICS\nLANGUAGE YAML\nAS $$\n"
    '  source: "cat.schema.tbl"\n  measures:\n    - name: c\n      expr: COUNT(1)\n$$'
)


def test_classify_genuine_when_base_table_exists():
    """base table present -> the MV is a GENUINE failure (real bug) and must be hard-failed."""
    genuine, invalid = _classify(_FakeSpark(rows=[(1,)]))(
        _FakeSpark(rows=[(1,)]), "cat", ["m1"], {"m1": _MV_WITH_SRC}, _CapLogger()
    )
    assert genuine == ["m1"] and invalid == []


def test_classify_invalid_when_base_table_absent():
    """base table absent -> INVALID declaration to surface, NOT a run-killer."""
    genuine, invalid = _classify(_FakeSpark(rows=[]))(
        _FakeSpark(rows=[]), "cat", ["m1"], {"m1": _MV_WITH_SRC}, _CapLogger()
    )
    assert genuine == [] and invalid == ["m1"]


def test_classify_invalid_when_no_source_derivable():
    """no original statement AND derive returns None -> cannot confirm a base table -> invalid."""
    genuine, invalid = _classify(_FakeSpark(rows=[]), derive_ret=None)(
        _FakeSpark(rows=[]), "cat", ["m1"], {}, _CapLogger()
    )
    assert genuine == [] and invalid == ["m1"]


def test_classify_empty_missing_noop():
    genuine, invalid = _classify(_FakeSpark(rows=[]))(_FakeSpark(rows=[]), "cat", [], {}, _CapLogger())
    assert genuine == [] and invalid == []


# --------------------------------------------------------------------------- #
# structural wiring — the gate must use the new classifier / non-fatal paths    #
# --------------------------------------------------------------------------- #
def test_gate_hardfails_only_on_genuine_missing():
    """Finding #1+#3: the physical-parity RAISE must be gated on _mv_genuine_missing, NOT on
    the raw parity flag or the extra set."""
    src = notebook_concat_source()
    assert "if _mv_genuine_missing:" in src
    raise_pos = src.find("Metric-view physical parity failed: genuine_missing=")
    assert raise_pos != -1, "hard-fail no longer references genuine_missing"
    # the OLD unconditional 'if not _mv_physical_audit[\"parity\"]:' raise must be gone
    assert 'if not _mv_physical_audit["parity"]:' not in src


def test_gate_classifies_before_hardfail():
    """classification must run BEFORE the genuine-missing raise."""
    src = notebook_concat_source()
    classify_pos = src.find("_v4610_classify_residual_missing(")
    genuine_raise_pos = src.find("if _mv_genuine_missing:")
    assert classify_pos != -1 and genuine_raise_pos != -1
    assert classify_pos < genuine_raise_pos


def test_gate_extra_is_nonfatal():
    """Finding #1: extra physical MVs are logged non-fatally, never raised."""
    src = notebook_concat_source()
    assert "mv-parity-extra-nonfatal FIRED" in src


def test_gate_invalid_absent_base_surfaced_not_raised():
    """Finding #3/#5: invalid (absent-base) MVs are surfaced to next_vibes, not raised."""
    src = notebook_concat_source()
    assert "mv-invalid-absent-base-drop FIRED" in src
    assert '_mv_dropped_invalid_absent_base' in src


def test_count_audit_demoted_no_raise():
    """Finding #3: the coarse count audit no longer calls the hard-raise; it is observability
    only (physical parity gate is authoritative)."""
    src = notebook_concat_source()
    assert "mv-count-audit-nonfatal FIRED" in src
    # the old fatal call in the count-audit block must be gone
    assert "_v458_require_metric_view_parity(_mv_audit)" not in src


def test_colfetch_failure_falls_back_to_tables():
    """Finding #4: a failed catalog-wide COLUMNS fetch degrades to a TABLES-only existence
    fetch (existence gating preserved) instead of disabling existence checks."""
    src = notebook_concat_source()
    assert "mv-prevalidate-tables-fallback FIRED" in src
    # the fallback must set existence-known True from the tables query
    fb_pos = src.find("mv-prevalidate-tables-fallback FIRED")
    known_pos = src.rfind("_mvcp_existence_known = True", 0, fb_pos)
    assert known_pos != -1 and known_pos < fb_pos
    # the old defeatist message ('existence checks disabled') must not be the primary path
    assert "falling back to keep-on-empty, existence checks disabled" not in src


def test_agent_version_pinned_470():
    assert agent_version_line() in notebook_concat_source()
