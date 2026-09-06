"""v4.6.9 behavioral tests: metric-view strict-parity SELF-HEAL + same-target DEDUP.

Root cause (WCB Alberta v4.6.8 FAILED, missing=['investment_custodian_reconciliation']):
two generated MV statements collided on the IDENTICAL physical target name, so the
declared-vs-physical parity set diverged into a phantom `missing` even though the base
table was fully built and the parallel installer reported 0 failed. The in-installer
fallback (_v467_install_mv_fallback) fires ONLY on an install EXCEPTION, so it never
covered this reported-success-but-absent class, and the strict gate hard-failed the run.

FIX 1 mv-dedup-by-target (_v469_dedup_mv_by_target): collapse same-physical-target
  statements BEFORE install so declared names == physical targets by construction.
FIX 2 mv-parity-selfheal (_v469_selfheal_missing_mvs): before hard-failing, reinstall
  each missing declared MV's ORIGINAL statement, else a derived row-count fallback;
  only hard-fail on names that STILL cannot be built.

Each fail-pre baseline is derived from the SAME working-tree source so the proof does
not depend on git HEAD.
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


class _FakeRow(dict):
    def __getitem__(self, k):
        return dict.__getitem__(self, k)


class _FakeDF:
    def __init__(self, rows):
        self._rows = rows

    def collect(self):
        return self._rows


class _FakeSpark:
    def __init__(self, rows=None):
        self._rows = rows or []

    def sql(self, q):
        return _FakeDF(self._rows)


class _ExecSqlStub:
    """Records every DDL and can be told to raise for statements matching a predicate."""

    def __init__(self, fail_on=None):
        self.calls = []
        self._fail_on = fail_on or (lambda sql: False)

    def __call__(self, spark, sql, logger=None):
        self.calls.append(sql)
        if self._fail_on(sql):
            raise RuntimeError("simulated DDL failure")
        return None


def _ns_for(*fn_names, stubs=None):
    """Exec the named notebook functions into a shared namespace, then apply stubs
    (stubs override sliced reals). Late binding means slice order is irrelevant."""
    ns = {"re": _real_re}
    for fn in fn_names:
        exec(compile(slice_function_source(fn), "<slice>", "exec"), ns)
    if stubs:
        ns.update(stubs)
    return ns


# statements colliding on the SAME physical target name (the v4.6.8 failure shape)
def _mv_stmt(view, source, measures):
    body = "".join(f"    - name: {m}\n      expr: COUNT(1)\n" for m in measures)
    return (
        f"CREATE OR REPLACE VIEW `cat`.`_metrics`.`{view}`\n"
        f"WITH METRICS\nLANGUAGE YAML\nAS $$\n"
        f"  version: 1.1\n"
        f'  source: "{source}"\n'
        f"  dimensions:\n    - name: All\n      expr: \"1\"\n"
        f"  measures:\n{body}$$"
    )


COLLIDE_A = _mv_stmt("investment_custodian_reconciliation", "cat.investment.custodian_reconciliation", ["m1"])
COLLIDE_B = _mv_stmt("investment_custodian_reconciliation", "cat.investment.custodian_reconciliation", ["m1", "m2", "m3"])
OTHER = _mv_stmt("finance_journal_entry", "cat.finance.journal_entry", ["n1"])
# same target but NO `source:` line -> forces the derive-from-physical path in self-heal
COLLIDE_NOSRC = (
    "CREATE OR REPLACE VIEW `cat`.`_metrics`.`investment_custodian_reconciliation`\n"
    "WITH METRICS\nLANGUAGE YAML\nAS $$\n"
    "  version: 1.1\n"
    "  dimensions:\n    - name: All\n      expr: \"1\"\n"
    "  measures:\n    - name: m1\n      expr: COUNT(1)\n$$"
)


# --------------------------------------------------------------------------- #
# FIX 1  mv-dedup-by-target                                                    #
# --------------------------------------------------------------------------- #
def _dedup():
    ns = _ns_for("_extract_metric_view_name_from_statement", "_v469_dedup_mv_by_target")
    return ns["_v469_dedup_mv_by_target"]


def test_dedup_collapses_same_target_passpost():
    """pass-post: two statements on the same physical target collapse to ONE, so the
    declared set can no longer exceed the physical set for that name."""
    log = _CapLogger()
    out = _dedup()([COLLIDE_A, COLLIDE_B, OTHER], log)
    assert len(out) == 2
    names = sorted(_ns_for("_extract_metric_view_name_from_statement")["_extract_metric_view_name_from_statement"](s) for s in out)
    assert names == ["finance_journal_entry", "investment_custodian_reconciliation"]
    assert any("mv-dedup-by-target FIRED" in l and "collapsed 1" in l for l in log.lines)


def test_dedup_keeps_richest():
    """The survivor of a collision is the RICHEST (longest) statement — more dims/measures."""
    out = _dedup()([COLLIDE_A, COLLIDE_B], _CapLogger())
    assert out == [COLLIDE_B]  # B has 3 measures, A has 1


def test_dedup_failpre_without_dedup_keeps_collision():
    """fail-pre: without dedup, both colliding statements survive and BOTH map to the
    same physical target name — exactly the state that produced the phantom missing."""
    extract = _ns_for("_extract_metric_view_name_from_statement")["_extract_metric_view_name_from_statement"]
    raw = [COLLIDE_A, COLLIDE_B, OTHER]
    names = [extract(s) for s in raw]
    assert names.count("investment_custodian_reconciliation") == 2  # collision present pre-dedup
    # post-dedup the duplicate is gone
    deduped_names = [extract(s) for s in _dedup()(raw, _CapLogger())]
    assert deduped_names.count("investment_custodian_reconciliation") == 1


def test_dedup_preserves_unknown_sentinel():
    """Statements whose CREATE target cannot be parsed ('unknown_metric_view') must NEVER
    be collapsed together — they are unrelated."""
    junk1 = "SELECT 1"
    junk2 = "SELECT 2"
    out = _dedup()([junk1, junk2, COLLIDE_A], _CapLogger())
    assert junk1 in out and junk2 in out and len(out) == 3


def test_dedup_noop_when_no_collision():
    out = _dedup()([COLLIDE_A, OTHER], _CapLogger())
    assert len(out) == 2


# --------------------------------------------------------------------------- #
# FIX 2  mv-parity-selfheal                                                    #
# --------------------------------------------------------------------------- #
def _selfheal(exec_stub, derive_ret="`cat`.`investment`.`custodian_reconciliation`"):
    stubs = {
        "execute_sql": exec_stub,
        "_v468_derive_mv_source_from_target": lambda spark, target, logger=None: derive_ret,
        "_v458_metric_exception_detail": lambda e, *a, **k: str(e),
    }
    ns = _ns_for(
        "_extract_metric_view_source_from_statement",
        "_v469_build_mv_rowcount_fallback",
        "_v469_selfheal_missing_mvs",
        stubs=stubs,
    )
    return ns["_v469_selfheal_missing_mvs"]


def test_selfheal_reinstalls_original_passpost():
    """pass-post: a missing declared MV whose ORIGINAL statement is available is healed by
    re-installing that exact statement (the rich MV is preserved, not a stripped fallback)."""
    ex = _ExecSqlStub()
    heal = _selfheal(ex)
    orig = {"investment_custodian_reconciliation": COLLIDE_B}
    healed = heal(_FakeSpark(), "cat", ["investment_custodian_reconciliation"], orig, _CapLogger())
    assert healed == ["investment_custodian_reconciliation"]
    assert ex.calls == [COLLIDE_B]  # the ORIGINAL statement was re-installed verbatim


def test_selfheal_falls_back_when_original_fails():
    """If the original re-install raises, self-heal installs a row-count fallback whose
    source is the derived physical base table, and still heals the name."""
    ex = _ExecSqlStub(fail_on=lambda sql: sql == COLLIDE_NOSRC)  # original fails; fallback (different SQL) succeeds
    heal = _selfheal(ex, derive_ret="`cat`.`investment`.`custodian_reconciliation`")
    orig = {"investment_custodian_reconciliation": COLLIDE_NOSRC}
    healed = heal(_FakeSpark(), "cat", ["investment_custodian_reconciliation"], orig, _CapLogger())
    assert healed == ["investment_custodian_reconciliation"]
    assert ex.calls[0] == COLLIDE_NOSRC  # original re-install attempted first
    # last call is the fallback YAML referencing the derived base table (no source: in orig)
    assert "Row Count" in ex.calls[-1]
    assert "`cat`.`investment`.`custodian_reconciliation`" in ex.calls[-1]


def test_selfheal_uses_derived_source_when_no_orig():
    """A declared MV with NO original statement (dropped upstream) is still healed via the
    derived row-count fallback as long as the base table physically exists."""
    ex = _ExecSqlStub()
    heal = _selfheal(ex, derive_ret="`cat`.`investment`.`custodian_reconciliation`")
    healed = heal(_FakeSpark(), "cat", ["investment_custodian_reconciliation"], {}, _CapLogger())
    assert healed == ["investment_custodian_reconciliation"]
    assert "Row Count" in ex.calls[-1]


def test_selfheal_unhealable_failpre_when_no_base_table():
    """fail-pre for the residual hard-fail: when there is NO original AND no base table to
    derive from, the name CANNOT be healed and stays missing (the gate then honestly
    hard-fails — self-heal never masks a genuinely unbuildable MV)."""
    ex = _ExecSqlStub()
    heal = _selfheal(ex, derive_ret=None)
    log = _CapLogger()
    healed = heal(_FakeSpark(), "cat", ["investment_custodian_reconciliation"], {}, log)
    assert healed == []
    assert ex.calls == []  # nothing installed
    assert any("could NOT heal" in l for l in log.lines)


def test_selfheal_empty_missing_noop():
    ex = _ExecSqlStub()
    assert _selfheal(ex)(_FakeSpark(), "cat", [], {}, _CapLogger()) == []
    assert ex.calls == []


# --------------------------------------------------------------------------- #
# structural wiring                                                            #
# --------------------------------------------------------------------------- #
def test_gate_calls_selfheal_before_hardfail():
    """The strict-parity gate must attempt self-heal BEFORE raising the hard-fail, so a
    healable missing MV never terminates the run."""
    src = notebook_concat_source()
    heal_pos = src.find("_v469_selfheal_missing_mvs(spark, _mv_physical_catalog")
    hardfail_pos = src.find("mv-strict-physical-parity-hard-fail FIRED")
    assert heal_pos != -1, "self-heal not wired into the gate"
    assert hardfail_pos != -1
    assert heal_pos < hardfail_pos, "self-heal must run before the hard-fail raise"
    # the audit is re-queried after healing so the verdict reflects the healed state
    assert "residual_missing" in src


def test_dedup_wired_before_install():
    """The dedup must run on metric_view_statements BEFORE the parallel install call."""
    src = notebook_concat_source()
    dedup_pos = src.find("_v469_dedup_mv_by_target(metric_view_statements, logger)")
    install_pos = src.find("metric_exec_result = execute_metric_views_in_parallel_no_halt(")
    assert dedup_pos != -1 and install_pos != -1
    assert dedup_pos < install_pos


def test_fallback_builder_is_dry_single_source():
    """Both the in-installer fallback and the parity self-heal use the ONE shared YAML
    builder (no drift between the two fallback sites)."""
    src = notebook_concat_source()
    assert src.count("def _v469_build_mv_rowcount_fallback(") == 1
    assert "_fb_yaml = _v469_build_mv_rowcount_fallback(_fb_target, _fb_source)" in src
    assert "_v469_build_mv_rowcount_fallback(_sh_target, _sh_src)" in src


def test_agent_version_pinned_469():
    assert agent_version_line() in notebook_concat_source()
