#!/usr/bin/env python3
"""Honest metric-view parity check across all 80 installs.

For each install: count declared metric views in the fork repo (latest version dir)
vs physical views present in <catalog>._metrics. A physical < declared gap means
metrics were stripped/dropped (R2 lying-scoreboard). Reports every gap.
"""
from __future__ import annotations
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import install_marathon as im

REPO = Path.home() / "Documents/projects/lakehouse-business-data-models"
VIEW_BLOCK_RE = re.compile(r"CREATE OR REPLACE VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`", re.IGNORECASE)
STATE = Path.home() / "claude/vibe-agent/install_marathon_verify_state.json"
if len(sys.argv) > 1:
    STATE = Path(sys.argv[1])


def latest_version_dir(industry_dir: Path) -> Path | None:
    vers = sorted((d for d in industry_dir.iterdir()
                   if d.is_dir() and re.match(r"^v\d+$", d.name)),
                  key=lambda d: int(d.name[1:]))
    return vers[-1] if vers else None


def declared_views(industry: str, size: str) -> set[str]:
    ind_dir = REPO / "data-models" / industry
    ver = latest_version_dir(ind_dir)
    if not ver:
        return set()
    md = ver / size / "metrics"
    if not md.is_dir():
        return set()
    names: set[str] = set()
    for mf in md.glob("*.sql"):
        for m in VIEW_BLOCK_RE.findall(mf.read_text(errors="ignore")):
            names.add(m)
    return names


def physical_views(profile: str, catalog: str) -> int:
    q = (f"SELECT COUNT(*) AS n FROM `{catalog}`.information_schema.tables "
         f"WHERE table_schema = '_metrics'")
    st, err, rows = im.sql_exec(profile, q, timeout=120)
    if st != "SUCCEEDED":
        return -1
    try:
        return int(rows[0][0])
    except Exception:
        return -1


def check_one(item: dict) -> dict:
    profile = item["profile"]
    industry = item["industry"]
    size = item["size"]
    catalog = item["catalog"]
    decl = declared_views(industry, size)
    phys = physical_views(profile, catalog)
    return {
        "key": f"{profile}:{industry}:{size}",
        "declared": len(decl),
        "physical": phys,
        "gap": len(decl) - phys if phys >= 0 else None,
    }


def main() -> int:
    d = json.load(open(STATE))
    items = list(d["waves"]["pool"]["items"].values())
    results = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(check_one, it): it for it in items}
        for f in as_completed(futs):
            r = f.result()
            results.append(r)
            print(f"[{r['key']}] declared={r['declared']} physical={r['physical']} gap={r['gap']}", flush=True)
    results.sort(key=lambda r: r["key"])
    gaps = [r for r in results if r["gap"] is None or r["gap"] != 0]
    print("\n==== PARITY SUMMARY ====")
    print(f"total installs: {len(results)}")
    print(f"perfect parity (physical == declared): {sum(1 for r in results if r['gap'] == 0)}")
    print(f"gaps/errors: {len(gaps)}")
    for r in gaps:
        print(f"  GAP {r['key']}: declared={r['declared']} physical={r['physical']} gap={r['gap']}")
    out = Path.home() / "claude/vibe-agent/metric_parity_check.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"report: {out}")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
