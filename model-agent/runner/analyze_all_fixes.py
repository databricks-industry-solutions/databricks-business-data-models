#!/usr/bin/env python3
"""Enumerate EVERY metric-view fix on the branch vs upstream/main.

For each changed metric SQL file, diff each CREATE VIEW block (upstream vs HEAD)
and classify the change: column rename (expr/name), source-schema fix,
expression rewrite, or restored (added) view. Emits per-industry rollups,
distinct rename pairs with counts, and the special-case lists.
"""
from __future__ import annotations
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path.home() / "Documents/projects/lakehouse-business-data-models"
VIEW_BLOCK_RE = re.compile(r"(CREATE OR REPLACE VIEW[\s\S]*?\$\$;)", re.IGNORECASE)
NAME_RE = re.compile(r"CREATE OR REPLACE VIEW\s+`([^`]+)`\.`_metrics`\.`([^`]+)`", re.IGNORECASE)


def git_show(ref_path: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "show", ref_path]).decode()
    except subprocess.CalledProcessError:
        return ""


def blocks(text: str) -> dict[str, str]:
    out = {}
    for b in VIEW_BLOCK_RE.findall(text):
        m = NAME_RE.search(b)
        if m:
            out[m.group(2)] = b
    return out


def changed_metric_files() -> list[str]:
    diff = subprocess.check_output(
        ["git", "-C", str(REPO), "diff", "--name-only", "upstream/main..HEAD"]
    ).decode().splitlines()
    return [f for f in diff if "/metrics/" in f and f.endswith(".sql")]


def industry(path: str) -> str:
    return path.split("data-models/")[1].split("/")[0]


def line_map(block: str) -> dict[str, str]:
    """map dim/measure name -> expr, plus special 'source' key."""
    d = {}
    cur = None
    for ln in block.splitlines():
        s = ln.strip()
        if s.startswith("source:"):
            d["__source__"] = s.split("source:", 1)[1].strip()
        elif s.startswith("- name:"):
            cur = s.split("- name:", 1)[1].strip().strip('"')
        elif s.startswith("name:"):
            cur = s.split("name:", 1)[1].strip().strip('"')
        elif s.startswith("expr:") and cur is not None:
            d[f"expr::{cur}"] = s.split("expr:", 1)[1].strip()
            cur = None
    return d


def main():
    files = changed_metric_files()
    per_ind = defaultdict(lambda: {"files": set(), "views_changed": set(), "ref_fixes": 0, "restored": []})
    rename_pairs = Counter()      # (old_col, new_col) column renames (incl inside expressions)
    source_fixes = []             # (file, view, old, new)
    expr_rewrites = []            # (file, view, old, new) genuine restructures
    restored_views = []           # (file, view)
    total_ref_fixes = 0
    per_view_log = defaultdict(list)  # industry -> [(view, [(old,new)...])]

    SQL_KW = {"COUNT", "SUM", "AVG", "MIN", "MAX", "CASE", "WHEN", "THEN", "END", "DISTINCT",
              "CAST", "AS", "DOUBLE", "BIGINT", "INT", "DECIMAL", "STRING", "DATE", "TIMESTAMP",
              "YEAR", "MONTH", "DAY", "DATEDIFF", "DATE_TRUNC", "CURRENT_DATE", "TRUE", "FALSE",
              "NULL", "IS", "NOT", "ELSE", "AND", "OR", "COUNT_IF", "COALESCE", "ROUND", "ABS",
              "IF", "IN", "LIKE", "SUBSTR", "CONCAT", "LOWER", "UPPER", "NULLIF", "GREATEST",
              "LEAST", "FLOOR", "CEIL", "MOD", "STDDEV", "VARIANCE", "PERCENTILE", "APPROX",
              "FIRST", "LAST", "ARRAY", "SIZE", "TRIM", "LENGTH", "TO_DATE", "UNIX_TIMESTAMP"}

    def idents(expr: str) -> set[str]:
        toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)
        return {t for t in toks if t.upper() not in SQL_KW}

    for f in files:
        ind = industry(f)
        per_ind[ind]["files"].add(f)
        up = blocks(git_show(f"upstream/main:{f}"))
        hd = blocks((REPO / f).read_text(errors="ignore"))
        for name in hd:
            if name not in up:
                restored_views.append((f, name))
                per_ind[ind]["restored"].append(name)
                per_ind[ind]["views_changed"].add(name)
                continue
            if up[name] == hd[name]:
                continue
            per_ind[ind]["views_changed"].add(name)
            um, hm = line_map(up[name]), line_map(hd[name])
            view_changes = []
            for k in set(um) | set(hm):
                o, n = um.get(k), hm.get(k)
                if o is None or n is None or o == n:
                    continue
                total_ref_fixes += 1
                per_ind[ind]["ref_fixes"] += 1
                view_changes.append((o.strip(), n.strip()))
                if k == "__source__":
                    source_fixes.append((f, name, o, n))
                    continue
                removed = idents(o) - idents(n)
                added = idents(n) - idents(o)
                if len(removed) == 1 and len(added) == 1:
                    rename_pairs[(removed.pop(), added.pop())] += 1
                else:
                    expr_rewrites.append((f, name, o.strip(), n.strip()))
            if view_changes:
                per_view_log[ind].append((name, view_changes))

    result = {
        "files_changed": len(files),
        "industries": len(per_ind),
        "total_ref_fixes": total_ref_fixes,
        "distinct_rename_pairs": len(rename_pairs),
        "source_fixes": source_fixes,
        "expr_rewrites": expr_rewrites,
        "restored_views": restored_views,
        "per_industry": {k: {"files": len(v["files"]), "views_changed": len(v["views_changed"]),
                              "ref_fixes": v["ref_fixes"], "restored": v["restored"]}
                         for k, v in sorted(per_ind.items())},
        "rename_pairs": sorted(((f"{o} -> {n}", c) for (o, n), c in rename_pairs.items()),
                               key=lambda x: -x[1]),
        "per_view_log": {k: v for k, v in sorted(per_view_log.items())},
    }
    Path("/tmp/all_fixes.json").write_text(json.dumps(result, indent=2))
    print("files_changed:", result["files_changed"])
    print("industries:", result["industries"])
    print("total_ref_fixes:", result["total_ref_fixes"])
    print("distinct_rename_pairs:", result["distinct_rename_pairs"])
    print("source_fixes:", len(source_fixes))
    print("expr_rewrites:", len(expr_rewrites))
    print("restored_views:", len(restored_views))
    print("\nper-industry (files / views_changed / ref_fixes / restored):")
    for k, v in result["per_industry"].items():
        print(f"  {k:<24} {v['files']:>3} {v['views_changed']:>4} {v['ref_fixes']:>4}  {v['restored'] or ''}")


if __name__ == "__main__":
    main()
