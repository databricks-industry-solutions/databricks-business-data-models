#!/usr/bin/env python3
"""Batch-fix metric-view YAML SQL: resolve logical FK column names against schema DDL.

Walks lakehouse-industry-data-models data-models/*/{latest}/(ecm|mvm)/metrics/*.sql,
parses companion schemas/*.sql for physical column names, rewrites expr references,
and drops entire metric views that still reference unknown columns.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FK_COLUMN_RENAMES: dict[str, str] = {
    "member_identity_id": "identity_id",
    "member_subscriber_id": "subscriber_id",
    "plan_health_plan_id": "health_plan_id",
    "claim_header_id": "header_id",
    "member_group_id": "group_id",
    "risk_pool_id": "pool_id",
    "related_invoice_premium_invoice_id": "premium_invoice_id",
    "primary_pa_member_subscriber_id": "subscriber_id",
    "case_owner_employee_id": "employee_id",
    "primary_pa_provider_id": "provider_id",
    "primary_provider_id": "provider_id",
}

GENERIC_SUFFIX_FALLBACKS: dict[str, tuple[str, ...]] = {
    "description": ("_description",),
    "status": ("_status", "status_code", "record_status"),
    "category": ("_category", "category_code"),
    "code": ("_code",),
    "name": ("_name",),
    "type": ("_type", "type_code"),
}

TABLE_COL_RE = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+`[^`]+`\.`([^`]+)`\.`([^`]+)`\s*\(",
    re.IGNORECASE,
)
COL_LINE_RE = re.compile(r"^\s*`([^`]+)`\s+", re.MULTILINE)
VIEW_BLOCK_RE = re.compile(r"(CREATE OR REPLACE VIEW[\s\S]*?\$\$;)", re.IGNORECASE)
MV_NAME_RE = re.compile(
    r"CREATE OR REPLACE VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`",
    re.IGNORECASE,
)
SOURCE_RE = re.compile(r'source:\s*"`[^`]+`\.`([^`]+)`\.`([^`]+)`"', re.IGNORECASE)
EXPR_RE = re.compile(r"^\s*expr:\s*(.+)$", re.MULTILINE)
IDENT_RE = re.compile(r"\b([a-z][a-z0-9_]*)\b", re.IGNORECASE)

SQL_KEYWORDS = frozenset({
    "and", "or", "not", "as", "case", "when", "then", "else", "end", "in", "is",
    "null", "true", "false", "cast", "double", "decimal", "int", "bigint", "sum",
    "avg", "count", "min", "max", "round", "year", "quarter", "month", "day",
    "concat", "distinct", "nullif", "between", "like", "upper", "lower", "trim",
    "if", "coalesce", "abs", "sqrt", "ln", "log", "exp", "pow", "mod", "date",
    "timestamp", "string", "boolean", "float", "replace", "substring", "length",
    "q", "over", "partition", "by", "order", "desc", "asc", "limit", "offset",
    "from", "where", "group", "having", "select", "with", "metrics", "language",
    "yaml", "version", "comment", "source", "dimensions", "measures", "name",
    "expr", "create", "or", "view", "replace", "metric", "filter",
    "date_trunc", "current_date", "current_timestamp", "interval", "extract",
    "to_date", "to_timestamp", "datediff", "months_between", "add_months",
    "weekofyear", "dayofweek", "dayofmonth", "dayofyear", "hour", "minute",
    "second", "week", "try_cast", "try_to_timestamp", "nvl", "decode", "greatest",
    "least", "percentile", "stddev", "variance", "collect_list", "collect_set",
    "first", "last", "lag", "lead", "rank", "dense_rank", "row_number",
    "ntile", "cume_dist", "percent_rank", "approx_count_distinct", "any_value",
    "bool_and", "bool_or", "every", "some", "exists", "ilike", "rlike", "regexp",
    "split", "posexplode", "explode", "array", "struct", "map", "element_at",
    "size", "sort_array", "transform", "filter", "aggregate", "zip_with",
})

GENERIC_COLUMN_NAMES = frozenset(GENERIC_SUFFIX_FALLBACKS.keys())

DIM_EXPR_RE = re.compile(
    r'-\s*name:\s*"([^"]+)"\s*\n\s*expr:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\n|$)',
    re.MULTILINE,
)
NESTED_AGG_RE = re.compile(
    r"\b(?:SUM|AVG|COUNT|MIN|MAX)\s*\([^)]*\b(?:SUM|AVG|COUNT|MIN|MAX)\s*\(",
    re.IGNORECASE,
)
DATEDIFF_QUOTED_UNIT_RE = re.compile(
    r"DATEDIFF\(\s*'([^']+)'\s*,", re.IGNORECASE
)
DATEDIFF_ALLOWED_UNITS = frozenset({
    "YEAR", "QUARTER", "MONTH", "WEEK", "DAY", "DAYOFYEAR",
    "HOUR", "MINUTE", "SECOND", "MILLISECOND", "MICROSECOND",
})

COL_LIKE_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$", re.IGNORECASE
)


def dimension_expr_hints(block: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    for dim_name, expr in DIM_EXPR_RE.findall(block):
        hints[expr.lower()] = dim_name.lower()
    return hints


def fix_datediff_units(block: str) -> str:
    def repl(m: re.Match[str]) -> str:
        unit = m.group(1).strip().upper()
        if unit in DATEDIFF_ALLOWED_UNITS:
            return f"DATEDIFF({unit},"
        return m.group(0)

    return DATEDIFF_QUOTED_UNIT_RE.sub(repl, block)


def block_has_nested_aggregate(block: str) -> bool:
    for m in EXPR_RE.finditer(block):
        expr = m.group(1).strip().strip('"')
        if NESTED_AGG_RE.search(expr):
            return True
    return False


def latest_version_dir(industry_dir: Path) -> Path | None:
    vers = sorted(
        (d for d in industry_dir.iterdir() if d.is_dir() and re.match(r"^v\d+$", d.name)),
        key=lambda d: int(d.name[1:]),
    )
    return vers[-1] if vers else None


def parse_schema_columns(schema_dir: Path) -> dict[tuple[str, str], set[str]]:
    cols: dict[tuple[str, str], set[str]] = {}
    if not schema_dir.is_dir():
        return cols
    for sf in schema_dir.glob("*.sql"):
        text = sf.read_text(errors="ignore")
        for tm in TABLE_COL_RE.finditer(text):
            schema, table = tm.group(1), tm.group(2)
            key = (schema, table)
            start = tm.end()
            depth = 1
            i = start
            while i < len(text) and depth > 0:
                if text[i] == "(":
                    depth += 1
                elif text[i] == ")":
                    depth -= 1
                i += 1
            body = text[start : i - 1]
            names = set(COL_LINE_RE.findall(body))
            cols.setdefault(key, set()).update(names)
    return cols


def _table_prefixed(bad: str, valid: set[str], table: str) -> str | None:
    """Prefer the column qualified by the source table name, e.g. view on table
    `tier` referencing bare `code` -> `tier_code` (NOT the greedy-longest `color_code`).
    Also try the table's singular form (drop trailing 's')."""
    if not table:
        return None
    stems = [table]
    if table.endswith("s") and len(table) > 3:
        stems.append(table[:-1])
    for stem in stems:
        cand = f"{stem}_{bad}"
        if cand in valid:
            return cand
    return None


def resolve_column(bad: str, valid: set[str], table: str = "") -> str | None:
    if bad in valid:
        return bad
    mapped = FK_COLUMN_RENAMES.get(bad)
    if mapped and mapped in valid:
        return mapped
    tp = _table_prefixed(bad, valid, table)
    if tp:
        return tp
    for suffix in GENERIC_SUFFIX_FALLBACKS.get(bad, ()):
        if suffix.startswith("_"):
            matches = [c for c in valid if c.endswith(suffix)]
        else:
            matches = [c for c in valid if c == suffix or c.endswith(f"_{suffix}")]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            matches.sort(key=lambda c: (-len(c), c))
            return matches[0]
    parts = bad.split("_")
    for i in range(1, len(parts)):
        cand = "_".join(parts[i:])
        if cand in valid:
            return cand
    suffix_matches = [c for c in valid if c.endswith(bad) or c.endswith(f"_{bad}")]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        suffix_matches.sort(key=lambda c: (len(c), c))
        return suffix_matches[0]
    return None


def extract_source(block: str) -> tuple[str, str] | None:
    m = SOURCE_RE.search(block)
    if m:
        return m.group(1), m.group(2)
    return None


def strip_quoted_strings(expr: str) -> str:
    return re.sub(r"'[^']*'", "''", expr)


def collect_expr_idents(block: str) -> set[str]:
    idents: set[str] = set()
    for m in EXPR_RE.finditer(block):
        expr = strip_quoted_strings(m.group(1).strip().strip('"'))
        for ident in IDENT_RE.findall(expr):
            low = ident.lower()
            if low in GENERIC_COLUMN_NAMES:
                idents.add(low)
                continue
            if low in SQL_KEYWORDS or low.isdigit():
                continue
            if COL_LIKE_RE.match(low):
                idents.add(low)
    return idents


def apply_renames_to_block(block: str, renames: dict[str, str]) -> str:
    out = block
    for bad, good in sorted(renames.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf"\b{re.escape(bad)}\b", good, out, flags=re.IGNORECASE)
    return out


def fix_metric_file(
    path: Path,
    schema_cols: dict[tuple[str, str], set[str]],
) -> tuple[str, dict]:
    text = path.read_text(errors="ignore")
    stats = {"views_total": 0, "views_kept": 0, "views_dropped": 0, "renames": 0, "dropped": []}
    header_lines: list[str] = []
    blocks: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.strip().upper().startswith("CREATE OR REPLACE VIEW"):
            break
        header_lines.append(line)
    rest = text[len("".join(header_lines)) :]
    for block in VIEW_BLOCK_RE.findall(rest):
        stats["views_total"] += 1
        src = extract_source(block)
        if not src:
            blocks.append(block)
            stats["views_kept"] += 1
            continue
        valid = schema_cols.get(src, set())
        if not valid:
            mv = MV_NAME_RE.search(block)
            name = mv.group(1) if mv else "?"
            stats["views_dropped"] += 1
            stats["dropped"].append({"view": name, "unresolved": [f"missing_source:{src[0]}.{src[1]}"]})
            continue
        block = fix_datediff_units(block)
        if block_has_nested_aggregate(block):
            mv = MV_NAME_RE.search(block)
            name = mv.group(1) if mv else "?"
            stats["views_dropped"] += 1
            stats["dropped"].append({"view": name, "unresolved": ["nested_aggregate"]})
            continue
        hints = dimension_expr_hints(block)
        idents = collect_expr_idents(block)
        renames: dict[str, str] = {}
        unresolved: list[str] = []
        for ident in idents:
            if ident in valid:
                continue
            hint_col = hints.get(ident)
            if hint_col and hint_col in valid:
                renames[ident] = hint_col
                continue
            resolved = resolve_column(ident, valid, src[1])
            if resolved:
                renames[ident] = resolved
            else:
                unresolved.append(ident)
        if unresolved:
            mv = MV_NAME_RE.search(block)
            name = mv.group(1) if mv else "?"
            stats["views_dropped"] += 1
            stats["dropped"].append({"view": name, "unresolved": unresolved[:5]})
            continue
        if renames:
            block = apply_renames_to_block(block, renames)
            stats["renames"] += len(renames)
        blocks.append(block)
        stats["views_kept"] += 1
    new_text = "".join(header_lines) + "\n".join(b.strip() + "\n\n" for b in blocks)
    return new_text.rstrip() + "\n", stats


def process_repo(repo_root: Path, dry_run: bool = False) -> dict:
    data_models = repo_root / "data-models"
    summary: dict = {"industries": {}, "totals": {"files": 0, "renames": 0, "dropped_views": 0}}
    for industry_dir in sorted(data_models.iterdir()):
        if not industry_dir.is_dir():
            continue
        industry = industry_dir.name
        ver = latest_version_dir(industry_dir)
        if not ver:
            continue
        ind_stats = {"ecm": {}, "mvm": {}}
        for size in ("ecm", "mvm"):
            metrics_dir = ver / size / "metrics"
            schema_dir = ver / size / "schemas"
            if not metrics_dir.is_dir():
                continue
            schema_cols = parse_schema_columns(schema_dir)
            size_stats = {"files": 0, "renames": 0, "dropped_views": 0, "files_changed": []}
            for mf in sorted(metrics_dir.glob("*.sql")):
                new_text, st = fix_metric_file(mf, schema_cols)
                size_stats["files"] += 1
                summary["totals"]["files"] += 1
                size_stats["renames"] += st["renames"]
                size_stats["dropped_views"] += st["views_dropped"]
                summary["totals"]["renames"] += st["renames"]
                summary["totals"]["dropped_views"] += st["views_dropped"]
                if st["renames"] or st["views_dropped"]:
                    size_stats["files_changed"].append(
                        {"file": mf.name, "renames": st["renames"], "dropped": st["dropped"]}
                    )
                    if not dry_run:
                        mf.write_text(new_text)
            if size_stats["files"]:
                ind_stats[size] = size_stats
        if ind_stats["ecm"] or ind_stats["mvm"]:
            summary["industries"][industry] = ind_stats
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/tmp/lakehouse-industry-data-models")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default="/tmp/metric_fix_report.json")
    args = ap.parse_args()
    summary = process_repo(Path(args.repo), dry_run=args.dry_run)
    Path(args.report).write_text(json.dumps(summary, indent=2))
    t = summary["totals"]
    print(f"files={t['files']} renames={t['renames']} dropped_views={t['dropped_views']}")
    print(f"report: {args.report}")
    industries_changed = sum(
        1 for ind in summary["industries"].values()
        if any(s.get("files_changed") for s in ind.values() if isinstance(s, dict))
    )
    print(f"industries_with_changes: {industries_changed}")


if __name__ == "__main__":
    main()
