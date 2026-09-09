#!/usr/bin/env python3
"""Snapshot the metastore, and diff two snapshots.

An uninstall is only correct if the metastore returns to exactly the state it was in
before the install. Asserting that requires a before/after record, so this captures
catalogs, schemas, tables and volumes through the Unity Catalog API (no SQL warehouse
needed) and prints a diff.

    python3 metastore_snapshot.py capture <profile> <out.json> [catalog ...]
    python3 metastore_snapshot.py diff <before.json> <after.json>
"""
import json
import subprocess
import sys

SYSTEM_CATALOGS = {"system", "samples", "hive_metastore", "__databricks_internal"}


def cli(args, profile):
    proc = subprocess.run(["databricks"] + args + ["--profile", profile, "-o", "json"],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(" ".join(args) + " -> " + (proc.stderr or "")[:300])
    body = json.loads(proc.stdout or "[]")
    if isinstance(body, dict):
        for key in ("catalogs", "schemas", "tables", "volumes"):
            if key in body:
                return body[key] or []
        return []
    return body or []


def capture(profile, only=()):
    """Catalogs -> schemas -> (tables, volumes). Restricted to `only` when given, so a
    snapshot of a busy workspace stays fast and is not perturbed by unrelated activity."""
    snapshot = {}
    for catalog in cli(["catalogs", "list"], profile):
        name = catalog.get("name")
        if not name or name in SYSTEM_CATALOGS:
            continue
        if catalog.get("catalog_type") == "SYSTEM_CATALOG":
            continue
        if only and name not in only:
            continue
        entry = {"schemas": {}}
        try:
            schemas = cli(["schemas", "list", name], profile)
        except Exception as exc:
            entry["error"] = str(exc)[:200]
            snapshot[name] = entry
            continue
        for schema in schemas:
            sname = schema.get("name")
            if not sname or sname == "information_schema":
                continue
            tables, volumes = [], []
            try:
                tables = sorted(t.get("name") for t in cli(["tables", "list", name, sname],
                                                           profile) if t.get("name"))
            except Exception:
                pass
            try:
                volumes = sorted(v.get("name") for v in cli(["volumes", "list", name, sname],
                                                            profile) if v.get("name"))
            except Exception:
                pass
            entry["schemas"][sname] = {"tables": tables, "volumes": volumes}
        snapshot[name] = entry
    return snapshot


def diff(before, after):
    """Return a list of human-readable differences. Empty list == identical."""
    out = []
    for catalog in sorted(set(before) | set(after)):
        if catalog not in after:
            out.append("catalog REMOVED: %s" % catalog)
            continue
        if catalog not in before:
            out.append("catalog ADDED: %s (%d schemas)"
                       % (catalog, len(after[catalog].get("schemas", {}))))
            continue
        b = before[catalog].get("schemas", {})
        a = after[catalog].get("schemas", {})
        for schema in sorted(set(b) | set(a)):
            if schema not in a:
                out.append("schema REMOVED: %s.%s (%d tables)"
                           % (catalog, schema, len(b[schema]["tables"])))
            elif schema not in b:
                out.append("schema ADDED: %s.%s (%d tables)"
                           % (catalog, schema, len(a[schema]["tables"])))
            else:
                gone = set(b[schema]["tables"]) - set(a[schema]["tables"])
                new = set(a[schema]["tables"]) - set(b[schema]["tables"])
                if gone:
                    out.append("tables REMOVED in %s.%s: %s"
                               % (catalog, schema, ", ".join(sorted(gone)[:8])))
                if new:
                    out.append("tables ADDED in %s.%s: %s"
                               % (catalog, schema, ", ".join(sorted(new)[:8])))
                vgone = set(b[schema]["volumes"]) - set(a[schema]["volumes"])
                vnew = set(a[schema]["volumes"]) - set(b[schema]["volumes"])
                if vgone:
                    out.append("volumes REMOVED in %s.%s: %s"
                               % (catalog, schema, ", ".join(sorted(vgone))))
                if vnew:
                    out.append("volumes ADDED in %s.%s: %s"
                               % (catalog, schema, ", ".join(sorted(vnew))))
    return out


def summarize(snapshot):
    schemas = sum(len(c.get("schemas", {})) for c in snapshot.values())
    tables = sum(len(s["tables"]) for c in snapshot.values()
                 for s in c.get("schemas", {}).values())
    return "%d catalog(s), %d schema(s), %d table(s)" % (len(snapshot), schemas, tables)


def main(argv):
    if len(argv) >= 4 and argv[1] == "capture":
        snapshot = capture(argv[2], only=set(argv[4:]) if len(argv) > 4 else ())
        with open(argv[3], "w") as f:
            json.dump(snapshot, f, indent=1, sort_keys=True)
        print("captured %s -> %s" % (summarize(snapshot), argv[3]))
        return 0
    if len(argv) == 4 and argv[1] == "diff":
        before = json.load(open(argv[2]))
        after = json.load(open(argv[3]))
        print("before: %s" % summarize(before))
        print("after : %s" % summarize(after))
        rows = diff(before, after)
        if not rows:
            print("IDENTICAL - the metastore returned to its pre-install state")
            return 0
        print("DIFFERENCES (%d):" % len(rows))
        for row in rows:
            print("  " + row)
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
