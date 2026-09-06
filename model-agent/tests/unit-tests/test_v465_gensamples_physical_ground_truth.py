"""v4.6.5 — behavioral tests for the gensamples physical-ground-truth resolver.

ROOT CAUSE (tester 05 Catalog-per-Domain + 08 One-Catalog, both FAILED at ~3.5min
with "Workload failed" and no volume info log): the standalone 'generate sample
data' op resolved each product's target schema from the STORED database_name +
resolver conventions, then DESCRIBE'd that single derived name. When the physical
schema install actually created differed by prefix/suffix/subdomain/casing from the
derived name, every DESCRIBE failed, every INSERT was skipped, and the op landed 0
rows across ALL tables — which v4.6.4's landing-hardfail gate then (correctly) raised
as a hard failure. The gate was right; the WRITE resolution was wrong.

FIX (v4.6.5 alias=gensamples-physical-ground-truth): both the sample WRITE path and
the landing verification now resolve the ACTUAL physical table via
`_resolve_existing_physical_table` — DESCRIBE candidates first, then an
`information_schema.tables` fallback per candidate catalog that locates WHERE the
table physically lives regardless of naming drift. This grounds sample landing in
the real catalog and cannot false-target.

These tests slice the REAL helper from the agent notebook and drive it with a fake
Spark. They FAIL on pre-patch HEAD (the helper does not exist -> LookupError) and
PASS post-patch.
"""
import ast
import json
import re as _re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _concat_source():
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    return "\n\n".join(parts)


SOURCE = _concat_source()


def _slice_named(name, kinds):
    lines = SOURCE.splitlines(keepends=True)
    tree = ast.parse(SOURCE)
    target = None
    for node in tree.body:
        if isinstance(node, kinds) and getattr(node, "name", None) == name:
            target = node
    if target is None:
        raise LookupError(f"{name!r} not found at module level")
    return "".join(lines[target.lineno - 1: target.end_lineno])


def _load_helper():
    blob = _slice_named("_resolve_existing_physical_table", (ast.FunctionDef,))
    ns = {"__name__": "_test_gensamples_gt", "re": _re}
    exec(compile(blob, str(NOTEBOOK_PATH), "exec"), ns)
    return ns["_resolve_existing_physical_table"]


class _FakeRow:
    def __init__(self, v):
        self._v = v

    def __getitem__(self, i):
        return self._v


class _FakeDF:
    def __init__(self, rows):
        self._rows = rows

    def collect(self):
        return self._rows


class _FakeSpark:
    """describe_ok: set of 'cat.schema.table' where DESCRIBE succeeds.
    is_tables: {catalog: {table_name_lower: physical_schema}}."""

    def __init__(self, describe_ok=None, is_tables=None):
        self.describe_ok = set(describe_ok or [])
        self.is_tables = is_tables or {}
        self.calls = []

    def sql(self, q):
        self.calls.append(q)
        if q.startswith("DESCRIBE TABLE"):
            fqn = q[len("DESCRIBE TABLE "):].strip().replace("`", "")
            if fqn in self.describe_ok:
                return _FakeDF([])
            raise Exception(f"[TABLE_OR_VIEW_NOT_FOUND] {fqn}")
        if "information_schema.tables" in q:
            m = _re.search(r"FROM `([^`]+)`\.information_schema\.tables", q)
            cat = m.group(1)
            mt = _re.search(r"lower\('([^']+)'\)", q)
            tname = mt.group(1).lower()
            sch = self.is_tables.get(cat, {}).get(tname)
            return _FakeDF([_FakeRow(sch)] if sch else [])
        raise Exception("unexpected query: " + q)


def test_information_schema_fallback_locates_schema_drift():
    """The exact 05/08 failure mode: resolver-derived schema ('dw_customer') does
    NOT exist physically ('dw_customer_layer' does). DESCRIBE misses; the helper must
    fall back to information_schema and return the TRUE physical location."""
    helper = _load_helper()
    spark = _FakeSpark(
        describe_ok=set(),  # no candidate schema exists -> every DESCRIBE fails
        is_tables={"the_cat": {"cust_table": "dw_customer_layer"}},
    )
    fqn, cat, sch = helper(spark, ["the_cat"], ["dw_customer"], "cust_table")
    assert fqn == "`the_cat`.`dw_customer_layer`.`cust_table`", fqn
    assert cat == "the_cat"
    assert sch == "dw_customer_layer"


def test_describe_candidate_hit_short_circuits_before_information_schema():
    """When a candidate (catalog, schema) DESCRIBE succeeds, return it and do NOT
    query information_schema (fast path preserved)."""
    helper = _load_helper()
    spark = _FakeSpark(describe_ok={"the_cat.dw_customer.cust_table"})
    fqn, cat, sch = helper(spark, ["the_cat"], ["dw_customer"], "cust_table")
    assert fqn == "`the_cat`.`dw_customer`.`cust_table`"
    assert not any("information_schema" in q for q in spark.calls), spark.calls


def test_truly_absent_table_returns_none():
    """If the table exists in NO candidate catalog, return (None, None, None) so the
    caller skips the insert and the landing-hardfail gate raises a TRUE 0-row failure."""
    helper = _load_helper()
    spark = _FakeSpark(describe_ok=set(), is_tables={})
    assert helper(spark, ["c1", "c2"], ["s1", "s2"], "ghost") == (None, None, None)


def test_catalog_fallback_finds_table_in_second_catalog():
    """Catalog-per-Domain: the stored catalog may be stale; the helper must try the
    resolver catalog too and locate the table wherever it physically lives."""
    helper = _load_helper()
    spark = _FakeSpark(describe_ok=set(), is_tables={"cat2": {"t": "s_phys"}})
    fqn, cat, sch = helper(spark, ["cat1", "cat2"], ["s"], "t")
    assert (fqn, cat, sch) == ("`cat2`.`s_phys`.`t`", "cat2", "s_phys")


def test_prefers_candidate_schema_when_multiple_physical_matches():
    """When information_schema returns several schemas hosting the table, prefer one
    that matches a resolver candidate (deterministic, avoids grabbing a stray copy)."""
    helper = _load_helper()

    class _MultiSpark(_FakeSpark):
        def sql(self, q):
            self.calls.append(q)
            if q.startswith("DESCRIBE TABLE"):
                raise Exception("miss")
            if "information_schema.tables" in q:
                return _FakeDF([_FakeRow("other_schema"), _FakeRow("src_customer")])
            raise Exception("unexpected")

    spark = _MultiSpark()
    fqn, cat, sch = helper(spark, ["cat"], ["src_customer"], "t")
    assert sch == "src_customer", fqn


def test_empty_inputs_return_none():
    helper = _load_helper()
    spark = _FakeSpark()
    assert helper(spark, [], ["s"], "t") == (None, None, None)
    assert helper(spark, ["c"], ["s"], "") == (None, None, None)
    assert not spark.calls  # no SQL issued on degenerate input


