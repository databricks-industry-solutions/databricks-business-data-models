#!/usr/bin/env python3
"""Audit the rows a live `generate sample data` run wrote into a catalog.

The offline harness proves the generators in isolation; this reads the PHYSICAL
tables so a defect that only appears after the DDL, the insert and the Phase-2 FK
MERGE (type rejection, 1:1 FK collapse, unresolved FK, placeholder strings,
reversed date pairs) cannot hide behind a green terminal state.

    python3 runner/audit_live_samples.py <catalog> [profile]
"""
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

M.WAREHOUSE.setdefault("my-adp", "2ad1b26db73a7c6f")

TEMPORAL_ORDER_PAIRS = [
    ("valid_from", "valid_to"), ("effective", "expir"), ("effective", "end"),
    ("start", "end"), ("begin", "end"), ("open", "close"), ("entry", "exit"),
    ("created", "updated"), ("created", "modified"), ("created", "closed"),
    ("order", "ship"), ("order", "deliver"), ("ship", "deliver"),
    ("issue", "expir"), ("issue", "due"), ("hire", "termination"),
    ("admission", "discharge"), ("depart", "arriv"), ("first", "last"),
]
PLACEHOLDER = re.compile(r"^sample_\d+$")


def _token_pos(parts, token):
    if "_" in token:
        return "_".join(parts).find(token)
    for i, part in enumerate(parts):
        if part == token or (len(token) >= 4 and part.startswith(token)):
            return i
    return -1


def _token_role(name, lo_token, hi_token):
    parts = [p for p in name.lower().split("_") if p]
    lo_at, hi_at = _token_pos(parts, lo_token), _token_pos(parts, hi_token)
    if lo_at < 0 and hi_at < 0:
        return None
    if hi_at < 0:
        return "lo"
    if lo_at < 0:
        return "hi"
    return "hi" if hi_at > lo_at else "lo"


def rows(profile, stmt):
    res = M.sql_exec(profile, stmt, timeout=300)
    data = (res.get("result", {}) or {}).get("data_array") or []
    cols = [c["name"] for c in
            ((res.get("manifest", {}) or {}).get("schema", {}) or {}).get("columns", [])]
    return [dict(zip(cols, r)) for r in data]


def main():
    catalog = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else "my-adp"
    findings = []

    schemas = [r["table_schema"] for r in rows(profile, f"""
        SELECT DISTINCT table_schema FROM `{catalog}`.information_schema.tables
        WHERE table_schema NOT LIKE '\\_%'
              AND table_schema <> 'information_schema' ORDER BY 1""")]
    print(f"catalog={catalog} schemas={schemas}")

    cols_by_table = defaultdict(list)
    for r in rows(profile, f"""
            SELECT table_schema, table_name, column_name, full_data_type
            FROM `{catalog}`.information_schema.columns
            WHERE table_schema NOT LIKE '\\_%'
              AND table_schema <> 'information_schema'
            ORDER BY table_schema, table_name, ordinal_position"""):
        cols_by_table[(r["table_schema"], r["table_name"])].append(
            (r["column_name"], r["full_data_type"]))

    pk_of = {}
    for r in rows(profile, f"""
            SELECT kcu.table_schema, kcu.table_name, kcu.column_name
            FROM `{catalog}`.information_schema.key_column_usage kcu
            JOIN `{catalog}`.information_schema.table_constraints tc
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND kcu.table_schema NOT LIKE '\\_%'
              AND kcu.table_schema <> 'information_schema'"""):
        pk_of.setdefault((r["table_schema"], r["table_name"]), []).append(r["column_name"])

    fks = rows(profile, f"""
        SELECT kcu.table_schema AS child_schema, kcu.table_name AS child_table,
               kcu.column_name AS child_column,
               ccu.table_schema AS parent_schema, ccu.table_name AS parent_table,
               ccu.column_name AS parent_column
        FROM `{catalog}`.information_schema.key_column_usage kcu
        JOIN `{catalog}`.information_schema.table_constraints tc
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN `{catalog}`.information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND kcu.table_schema NOT LIKE '\\_%'
          AND kcu.table_schema <> 'information_schema'""")

    tables = sorted(cols_by_table)
    print(f"tables={len(tables)} fk_constraints={len(fks)}")

    # ---------------- row counts + per-column content ---------------- #
    empty, placeholder_cols, constant_cols, temporal_bad = [], [], [], []
    pk_dupes, pk_values = [], {}
    for schema, table in tables:
        cols = cols_by_table[(schema, table)]
        n = int(rows(profile, f"SELECT COUNT(*) c FROM `{catalog}`.`{schema}`.`{table}`")[0]["c"])
        if n == 0:
            empty.append(f"{schema}.{table}")
            continue
        sample = rows(profile, f"SELECT * FROM `{catalog}`.`{schema}`.`{table}` LIMIT 400")

        for col, dtype in cols:
            values = [r.get(col) for r in sample]
            present = [v for v in values if v is not None]
            if not present:
                continue
            if any(PLACEHOLDER.match(str(v)) for v in present):
                placeholder_cols.append(f"{schema}.{table}.{col}")
            if len(present) >= 10 and len(set(present)) == 1:
                constant_cols.append(f"{schema}.{table}.{col}")

        temporal = [c for c, t in cols if t.upper().startswith(("DATE", "TIMESTAMP"))]
        for lo_t, hi_t in TEMPORAL_ORDER_PAIRS:
            los = [c for c in temporal if _token_role(c, lo_t, hi_t) == "lo"]
            his = [c for c in temporal if _token_role(c, lo_t, hi_t) == "hi"]
            for lo in los:
                for hi in his:
                    bad = sum(1 for r in sample
                              if r.get(lo) and r.get(hi) and str(r[hi]) < str(r[lo]))
                    if bad:
                        temporal_bad.append(f"{schema}.{table}: {hi} < {lo} in {bad} rows")

        pks = pk_of.get((schema, table), [])
        if pks:
            key = ", ".join(f"`{c}`" for c in pks)
            dup = rows(profile, f"""
                SELECT COUNT(*) c FROM (SELECT {key} FROM `{catalog}`.`{schema}`.`{table}`
                GROUP BY {key} HAVING COUNT(*) > 1)""")[0]["c"]
            if int(dup):
                pk_dupes.append(f"{schema}.{table} ({dup} duplicate keys)")
            if len(pks) == 1:
                pk_values[f"{schema}.{table}"] = {
                    str(r[pks[0]]) for r in rows(
                        profile,
                        f"SELECT `{pks[0]}` FROM `{catalog}`.`{schema}`.`{table}`")}
        print(f"  {schema}.{table:38} rows={n:5} cols={len(cols)} pk={pks or '-'}")

    # ---------------- FK integrity + fan-out ---------------- #
    unresolved, one_to_one, self_pointing, fanout_hist = [], [], [], Counter()
    for fk in fks:
        child = f"`{catalog}`.`{fk['child_schema']}`.`{fk['child_table']}`"
        parent = f"`{catalog}`.`{fk['parent_schema']}`.`{fk['parent_table']}`"
        label = (f"{fk['child_schema']}.{fk['child_table']}.{fk['child_column']}"
                 f" -> {fk['parent_table']}.{fk['parent_column']}")
        stat = rows(profile, f"""
            SELECT COUNT(*) total,
                   SUM(CASE WHEN c.`{fk['child_column']}` IS NULL THEN 1 ELSE 0 END) nulls,
                   SUM(CASE WHEN c.`{fk['child_column']}` IS NOT NULL
                             AND p.`{fk['parent_column']}` IS NULL THEN 1 ELSE 0 END) orphans,
                   COUNT(DISTINCT c.`{fk['child_column']}`) distinct_fk
            FROM {child} c LEFT JOIN {parent} p
              ON c.`{fk['child_column']}` = p.`{fk['parent_column']}`""")[0]
        total, nulls = int(stat["total"]), int(stat["nulls"] or 0)
        orphans, distinct_fk = int(stat["orphans"] or 0), int(stat["distinct_fk"] or 0)
        filled = total - nulls
        if orphans:
            unresolved.append(f"{label}: {orphans}/{filled} orphan values")
        if filled and distinct_fk == filled and filled > 3:
            one_to_one.append(f"{label}: {distinct_fk} distinct over {filled} rows")
        if filled:
            fanout_hist[round(filled / max(distinct_fk, 1), 1)] += 1
        if (fk["child_schema"], fk["child_table"]) == (fk["parent_schema"], fk["parent_table"]):
            loops = rows(profile, f"""
                SELECT COUNT(*) c FROM {child}
                WHERE `{fk['child_column']}` = `{fk['parent_column']}`""")[0]["c"]
            if int(loops):
                self_pointing.append(f"{label}: {loops} rows point at themselves")

    shared = []
    names = sorted(pk_values)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            common = pk_values[names[i]] & pk_values[names[j]]
            if common:
                shared.append(f"{names[i]} / {names[j]}: {len(common)} shared key values")

    print("\n--- findings ---")
    for label, items in [
        ("tables with zero rows", empty),
        ("placeholder 'sample_N' columns", placeholder_cols),
        ("single-valued columns", constant_cols),
        ("temporal order violations", temporal_bad),
        ("tables with duplicate PKs", pk_dupes),
        ("PK values shared across tables", shared),
        ("FKs with orphan values", unresolved),
        ("FKs collapsed to 1:1", one_to_one),
        ("self-FK rows pointing at self", self_pointing),
    ]:
        print(f"  {label:34} {len(items)}")
        for item in items[:8]:
            print(f"      - {item}")
        findings.append((label, len(items)))
    print(f"  fk fan-out (rows per parent): {dict(sorted(fanout_hist.items()))}")
    bad = sum(n for _, n in findings)
    print(f"\nTOTAL FINDINGS: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
