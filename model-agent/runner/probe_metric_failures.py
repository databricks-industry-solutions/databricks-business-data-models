#!/usr/bin/env python3
"""Test-compile metric views for the retry-stripped installs against their live catalogs
to capture the REAL Spark errors (UNRESOLVED_COLUMN etc.) without redoing full installs.

Tables/FKs/tags already exist in each marathon_<ind>_<size> catalog, so CREATE OR REPLACE
VIEW ... WITH METRICS reproduces the installer metric phase exactly.
"""
from __future__ import annotations
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import install_marathon as im

REPO = Path.home() / "Documents/projects/lakehouse-business-data-models"
VIEW_BLOCK_RE = re.compile(r"(CREATE OR REPLACE VIEW[\s\S]*?\$\$;)", re.IGNORECASE)
MV_NAME_RE = re.compile(r"CREATE OR REPLACE VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`", re.IGNORECASE)
CREATE_CAT_RE = re.compile(r"CREATE\s+CATALOG\s+(?:IF\s+NOT\s+EXISTS\s+)?`([^`]+)`", re.IGNORECASE)


def latest_version_dir(industry_dir: Path) -> Path | None:
    vers = sorted((d for d in industry_dir.iterdir()
                   if d.is_dir() and re.match(r"^v\d+$", d.name)),
                  key=lambda d: int(d.name[1:]))
    return vers[-1] if vers else None


def detect_src_token(size_dir: Path) -> str | None:
    for sf in sorted((size_dir / "schemas").glob("*catalog*.sql")):
        m = CREATE_CAT_RE.search(sf.read_text(errors="ignore"))
        if m:
            return m.group(1)
    for sf in sorted((size_dir / "schemas").glob("*.sql")):
        m = CREATE_CAT_RE.search(sf.read_text(errors="ignore"))
        if m:
            return m.group(1)
    return None


def probe_one(key: str) -> dict:
    profile, ind, size = key.split(":")
    target_cat = f"marathon_{ind}_{size}"
    industry_dir = REPO / "data-models" / ind
    ver = latest_version_dir(industry_dir)
    size_dir = ver / size
    metrics_dir = size_dir / "metrics"
    src_token = detect_src_token(size_dir)
    failures = []
    total = 0
    # ensure _metrics schema
    im.sql_exec(profile, f"CREATE SCHEMA IF NOT EXISTS `{target_cat}`.`_metrics`", timeout=60)
    for mf in sorted(metrics_dir.glob("*.sql")):
        text = mf.read_text(errors="ignore")
        if src_token and src_token != target_cat:
            text = text.replace(f"`{src_token}`", f"`{target_cat}`")
        for block in VIEW_BLOCK_RE.findall(text):
            total += 1
            mv = MV_NAME_RE.search(block)
            view = mv.group(1) if mv else "?"
            st, err, _ = im.sql_exec(profile, block.rstrip().rstrip(";"), timeout=120)
            if st != "SUCCEEDED":
                msg = err.get("message") if isinstance(err, dict) else str(err)
                failures.append({"file": mf.name, "view": view, "error": " ".join((msg or "").split())[:400]})
    return {"key": key, "total": total, "failures": failures}


def main():
    keys = sys.argv[1:]
    if not keys:
        print("usage: probe_metric_failures.py <key> ...")
        return
    results = {}
    with ThreadPoolExecutor(max_workers=min(12, len(keys))) as ex:
        futs = {ex.submit(probe_one, k): k for k in keys}
        for f in as_completed(futs):
            k = futs[f]
            try:
                r = f.result()
                results[k] = r
                print(f"[{k}] views={r['total']} failed={len(r['failures'])}", flush=True)
            except Exception as e:
                results[k] = {"key": k, "error": str(e)[:300]}
                print(f"[{k}] PROBE ERROR: {str(e)[:200]}", flush=True)
    out = Path.home() / "claude/vibe-agent/metric_probe_failures.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nreport: {out}")
    tot_fail = sum(len(r.get("failures", [])) for r in results.values())
    print(f"total failing views across {len(keys)} installs: {tot_fail}")


if __name__ == "__main__":
    main()
