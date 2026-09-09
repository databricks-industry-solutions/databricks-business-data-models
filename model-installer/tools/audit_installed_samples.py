"""Audit sample data in a catalog that has actually been installed.

The engine asserts integrity in memory before writing; this asserts it again against
the physical tables, so a claim about referential integrity rests on what Unity
Catalog holds rather than on what the generator believed it produced.

    python3 audit_installed_samples.py <catalog> [--profile P] [--warehouse ID]
"""
import argparse
import json
import subprocess
import sys
import time

INTERNAL = ("information_schema", "_metrics", "_install", "_metamodel", "default")


def run_sql(sql, profile, warehouse):
    body = {"warehouse_id": warehouse, "statement": sql, "wait_timeout": "50s",
            "format": "JSON_ARRAY", "disposition": "INLINE"}
    proc = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", profile,
         "--json", json.dumps(body)],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("statement call failed: %s" % proc.stderr[:400])
    payload = json.loads(proc.stdout)
    while payload.get("status", {}).get("state") in ("PENDING", "RUNNING"):
        time.sleep(2)
        follow = subprocess.run(
            ["databricks", "api", "get",
             "/api/2.0/sql/statements/%s" % payload["statement_id"], "--profile", profile],
            capture_output=True, text=True)
        payload = json.loads(follow.stdout)
    state = payload.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise SystemExit("%s: %s\n%s" % (state, payload.get("status", {}).get("error"),
                                         sql[:300]))
    return payload.get("result", {}).get("data_array") or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("catalog")
    ap.add_argument("--profile", default="my-uae")
    ap.add_argument("--warehouse", default="0ece1cdc84e98661")
    ap.add_argument("--expect-rows", type=int, default=None)
    args = ap.parse_args()
    cat, prof, wh = args.catalog, args.profile, args.warehouse
    skip = ", ".join("'%s'" % s for s in INTERNAL)

    tables = [(r[0], r[1]) for r in run_sql(
        "SELECT table_schema, table_name FROM %s.information_schema.tables "
        "WHERE table_schema NOT IN (%s) AND table_type = 'MANAGED' "
        "ORDER BY 1, 2" % (cat, skip), prof, wh)]
    print("tables: %d" % len(tables))

    # One pass for every table's row count, so this is a single statement rather than
    # one round trip per table.
    counts = dict((r[0] + "." + r[1], int(r[2])) for r in run_sql(
        " UNION ALL ".join(
            "SELECT '%s' s, '%s' t, COUNT(*) n FROM `%s`.`%s`.`%s`"
            % (s, t, cat, s, t) for s, t in tables), prof, wh))
    empty = sorted(k for k, v in counts.items() if v == 0)
    wrong = sorted((k, v) for k, v in counts.items()
                   if args.expect_rows and v != args.expect_rows)
    print("rows: total=%d  min=%d  max=%d  empty=%d"
          % (sum(counts.values()), min(counts.values()), max(counts.values()), len(empty)))
    if empty:
        print("  EMPTY: %s" % ", ".join(empty[:20]))
    if wrong:
        print("  OFF-COUNT (expected %d): %s"
              % (args.expect_rows, ", ".join("%s=%d" % kv for kv in wrong[:20])))

    pk_rows = run_sql(
        "SELECT k.table_schema, k.table_name, k.column_name, k.ordinal_position "
        "FROM %s.information_schema.key_column_usage k "
        "JOIN %s.information_schema.table_constraints c "
        "  ON k.constraint_name = c.constraint_name "
        " AND k.table_schema = c.table_schema AND k.table_name = c.table_name "
        "WHERE c.constraint_type = 'PRIMARY KEY' AND k.table_schema NOT IN (%s) "
        "ORDER BY 1, 2, 4" % (cat, cat, skip), prof, wh)
    pks = {}
    for schema, table, column, _pos in pk_rows:
        pks.setdefault((schema, table), []).append(column)
    print("primary keys: %d table(s)" % len(pks))

    dup_checks = [
        "SELECT '%s.%s' k, COUNT(*) - COUNT(DISTINCT %s) d FROM `%s`.`%s`.`%s`"
        % (s, t, ", ".join("`%s`" % c for c in cols), cat, s, t)
        for (s, t), cols in sorted(pks.items())]
    dups = [(r[0], int(r[1])) for r in run_sql(" UNION ALL ".join(dup_checks), prof, wh)
            if int(r[1]) != 0]
    print("duplicate keys: %d table(s)%s"
          % (len(dups), "  " + ", ".join("%s=%d" % d for d in dups[:20]) if dups else ""))

    # referential_constraints -> the parent's unique constraint; key_column_usage on both
    # sides, matched by ordinal_position. constraint_column_usage is not used: its
    # constraint_schema is the referenced table's schema, so correlating on it drops
    # every cross-schema foreign key.
    fk_rows = run_sql(
        "SELECT rc.constraint_schema, rc.constraint_name, "
        "       ck.table_schema, ck.table_name, ck.column_name, ck.ordinal_position, "
        "       pk.table_schema, pk.table_name, pk.column_name "
        "FROM %s.information_schema.referential_constraints rc "
        "JOIN %s.information_schema.key_column_usage ck "
        "  ON ck.constraint_catalog = rc.constraint_catalog "
        " AND ck.constraint_schema = rc.constraint_schema "
        " AND ck.constraint_name = rc.constraint_name "
        "JOIN %s.information_schema.key_column_usage pk "
        "  ON pk.constraint_catalog = rc.unique_constraint_catalog "
        " AND pk.constraint_schema = rc.unique_constraint_schema "
        " AND pk.constraint_name = rc.unique_constraint_name "
        " AND pk.ordinal_position = ck.ordinal_position "
        "WHERE ck.table_schema NOT IN (%s) "
        "ORDER BY 1, 2, 6" % (cat, cat, cat, skip), prof, wh)
    fks = {}
    for cschema, name, cs, ct, col, _pos, ps, pt, pcol in fk_rows:
        fk = fks.setdefault((cschema, name), {"child": (cs, ct), "parent": (ps, pt),
                                             "cols": [], "pcols": []})
        fk["cols"].append(col)
        fk["pcols"].append(pcol)
    print("foreign keys: %d" % len(fks))

    orphan_checks = []
    for (_cschema, name), fk in sorted(fks.items()):
        cs, ct = fk["child"]
        ps, pt = fk["parent"]
        cols, pcols = fk["cols"], fk["pcols"]
        if not cols or len(pcols) != len(cols):
            continue
        on = " AND ".join("p.`%s` = c.`%s`" % (p, c) for p, c in zip(pcols, cols))
        notnull = " AND ".join("c.`%s` IS NOT NULL" % c for c in cols)
        orphan_checks.append(
            "SELECT '%s' fk, COUNT(*) n FROM `%s`.`%s`.`%s` c "
            "LEFT JOIN `%s`.`%s`.`%s` p ON %s "
            "WHERE %s AND p.`%s` IS NULL"
            % (name, cat, cs, ct, cat, ps, pt, on, notnull, pcols[0]))
    orphans = []
    for start in range(0, len(orphan_checks), 40):
        chunk = orphan_checks[start:start + 40]
        orphans += [(r[0], int(r[1])) for r in run_sql(" UNION ALL ".join(chunk), prof, wh)
                    if int(r[1]) != 0]
    print("orphan foreign keys: %d constraint(s)%s"
          % (len(orphans),
             "  " + ", ".join("%s=%d" % o for o in orphans[:20]) if orphans else ""))

    verdict = not (empty or wrong or dups or orphans)
    print("VERDICT: %s" % ("PASS" if verdict else "FAIL"))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
