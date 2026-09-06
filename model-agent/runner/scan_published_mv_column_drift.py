#!/usr/bin/env python3
"""How many already-published models ship a metric view that cannot install?

This is the blast-radius question behind the v4.8.5 fix. coffee_roastery shipped
retail_loyalty_account referencing `preferred_store_id` while its own DDL had renamed the
column to `store_id`: the agent pruned the column in memory, built the view, and published
the UNPRUNED SQL. Any consumer replaying that artifact hits UNRESOLVED_COLUMN.

The same drift can be detected offline, with no warehouse: a published metric view names
its source table, and the DDL that ships beside it declares that table's columns. A column
referenced by a view but absent from the DDL is a view that cannot install.

    python3 scan_published_mv_column_drift.py [repo_root] [--verbose]

Reports one line per model with drift, then a total. Exit 1 when any drift is found.

Known limits (deliberate, to keep false positives at zero rather than to be exhaustive):
  - `expr:` values spanning multiple lines are read to end-of-line only.
  - Identifiers are matched against a SQL keyword/function denylist; an unknown function
    name would surface as a missing column, so new findings are printed with their expr
    for eyeballing rather than trusted blindly.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

CREATE_TABLE = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+([`\w.]+)\s*\((.*?)\n\)",
    re.S | re.I)
COLUMN = re.compile(r"^\s{2,}`([a-z_][a-z0-9_]*)`\s+[A-Za-z]", re.M)
VIEW = re.compile(r"CREATE\s+OR\s+REPLACE\s+VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`", re.I)
SOURCE = re.compile(r"^\s*source:\s*\"?`?([^\"\n]+?)`?\"?\s*$", re.M)
EXPR = re.compile(r"^\s*expr:\s*(.+)$", re.M)
LITERAL = re.compile(r"'[^']*'|\"[^\"]*\"")
IDENT = re.compile(r"[a-z_][a-z0-9_]*")

# SQL surface that appears inside expr: and is not a column reference.
NOT_A_COLUMN = {
    "sum", "count", "distinct", "avg", "min", "max", "abs", "round", "floor", "ceil",
    "case", "when", "then", "else", "end", "cast", "as", "is", "not", "null", "and",
    "or", "in", "like", "between", "coalesce", "nullif", "greatest", "least",
    "date_trunc", "datediff", "date_add", "date_sub", "months_between", "current_date",
    "current_timestamp", "extract", "interval", "year", "month", "day", "quarter",
    "week", "hour", "minute", "second", "true", "false", "decimal", "int", "integer",
    "bigint", "smallint", "double", "float", "string", "boolean", "date", "timestamp",
    "try_divide", "divide", "if", "ifnull", "nvl", "lower", "upper", "trim", "concat",
    "substring", "length", "size", "array", "map", "struct", "explode", "percentile",
    "percentile_approx", "stddev", "variance", "median", "approx_count_distinct",
    "row_number", "rank", "dense_rank", "over", "partition", "by", "order", "desc",
    "asc", "filter", "where", "unix_timestamp", "to_date", "to_timestamp", "sqrt",
    # string / regex
    "regexp_replace", "regexp_extract", "regexp_like", "split", "instr", "locate",
    "lpad", "rpad", "replace", "translate", "ltrim", "rtrim", "initcap", "reverse",
    "left", "right", "repeat", "ascii", "format_string", "format_number", "sha2",
    "md5", "hash", "base64", "unbase64", "encode", "decode", "printf", "elt",
    # date / time
    "add_months", "timestampdiff", "timestampadd", "date_format", "from_unixtime",
    "to_unix_timestamp", "last_day", "next_day", "trunc", "dayofweek", "dayofmonth",
    "dayofyear", "weekofyear", "weekday", "make_date", "make_timestamp", "sequence",
    "date_part", "datepart", "now", "localtimestamp", "current_timezone",
    # math
    "sign", "exp", "ln", "log", "log10", "log2", "power", "pow", "mod", "pmod",
    "bround", "ceiling", "radians", "degrees", "rand", "randn", "positive", "negative",
    # aggregate / window
    "count_if", "bool_and", "bool_or", "any_value", "mode", "corr", "covar_pop",
    "covar_samp", "skewness", "kurtosis", "stddev_pop", "stddev_samp", "var_pop",
    "var_samp", "approx_percentile", "ntile", "lag", "lead", "first", "first_value",
    "last", "last_value", "cume_dist", "percent_rank", "nth_value", "collect_set",
    "collect_list", "grouping", "grouping_id",
    # collections / misc
    "cardinality", "element_at", "array_contains", "sort_array", "transform",
    "aggregate", "exists", "flatten", "slice", "zip_with", "map_keys", "map_values",
    "nvl2", "typeof", "uuid", "current_user", "input_file_name", "monotonically_increasing_id",
    "distinct_count", "try_cast", "try_add", "try_subtract", "try_multiply", "try_element_at",
}


def parse_ddl(schema_dir):
    """table (schema.table, lowercased) -> set of column names."""
    tables = {}
    for sql in sorted(schema_dir.glob("*.sql")):
        text = sql.read_text(encoding="utf-8", errors="ignore")
        for raw_name, body in CREATE_TABLE.findall(text):
            parts = [p for p in raw_name.replace("`", "").split(".") if p]
            if len(parts) < 2:
                continue
            key = ".".join(parts[-2:]).lower()
            tables.setdefault(key, set()).update(c.lower() for c in COLUMN.findall(body))
    return tables


def view_blocks(text):
    """(view_name, block_text) for every CREATE OR REPLACE VIEW in a metrics file."""
    starts = [(m.start(), m.group(1)) for m in VIEW.finditer(text)]
    for i, (at, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        yield name, text[at:end]


def referenced_columns(block):
    """Columns an expr: names, with SQL surface and string literals removed."""
    found = set()
    for expr in EXPR.findall(block):
        for token in IDENT.findall(LITERAL.sub(" ", expr.lower())):
            if token not in NOT_A_COLUMN:
                found.add(token)
    return found


def scan_model(model_dir):
    """[(view, table, sorted missing columns, sample expr)] for one <industry>/<vN>/<size>."""
    schema_dir, metrics_dir = model_dir / "schemas", model_dir / "metrics"
    if not schema_dir.is_dir() or not metrics_dir.is_dir():
        return []
    tables = parse_ddl(schema_dir)
    drift = []
    for sql in sorted(metrics_dir.glob("*.sql")):
        text = sql.read_text(encoding="utf-8", errors="ignore")
        for name, block in view_blocks(text):
            src = SOURCE.search(block)
            if not src:
                continue
            parts = [p for p in src.group(1).replace("`", "").split(".") if p]
            if len(parts) < 2:
                continue
            key = ".".join(parts[-2:]).lower()
            if key not in tables:
                continue  # the table is not in this model's DDL; not a column question
            missing = sorted(referenced_columns(block) - tables[key])
            if missing:
                sample = next((e for e in EXPR.findall(block)
                               if any(m in e.lower() for m in missing)), "")
                drift.append((name, key, missing, sample.strip()[:110]))
    return drift


def main(argv):
    verbose = "--verbose" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    root = Path(args[0]) if args else Path.home() / "Documents/projects/lakehouse-business-data-models"
    models = root / "data-models"
    if not models.is_dir():
        print("no data-models directory under %s" % root)
        return 2

    dirty, checked, by_column = 0, 0, defaultdict(int)
    for industry in sorted(p for p in models.iterdir() if p.is_dir()):
        for version in sorted(p for p in industry.iterdir()
                              if p.is_dir() and re.match(r"^v\d+$", p.name)):
            for size in sorted(p for p in version.iterdir() if p.is_dir()):
                if not (size / "metrics").is_dir():
                    continue
                checked += 1
                drift = scan_model(size)
                if not drift:
                    continue
                dirty += 1
                print("\n%s/%s/%s: %d view(s) reference a column their DDL does not declare"
                      % (industry.name, version.name, size.name, len(drift)))
                for name, table, missing, sample in drift:
                    for col in missing:
                        by_column[col] += 1
                    print("    %-42s %-30s missing=%s" % (name, table, ",".join(missing)))
                    if verbose and sample:
                        print("        expr: %s" % sample)

    print("\n" + "=" * 72)
    print("models scanned : %d" % checked)
    print("models w/ drift: %d" % dirty)
    if by_column:
        top = sorted(by_column.items(), key=lambda kv: -kv[1])[:15]
        print("most common missing columns: %s"
              % ", ".join("%s(%d)" % (c, n) for c, n in top))
    print("=" * 72)
    return 1 if dirty else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
