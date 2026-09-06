#!/usr/bin/env python3
"""Fix metric-view YAML SQL where logical FK column names diverge from physical DDL.

Root cause (lakehouse industry models): metric generators emit domain-prefixed FK
names (member_identity_id) while schema DDL keeps short PK/FK names (identity_id).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from pathlib import Path

# Logical FK name in metrics -> physical column on installed tables (verified via IS).
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

_COL_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(FK_COLUMN_RENAMES, key=len, reverse=True)) + r")\b"
)
_VIEW_SPLIT_RE = re.compile(
    r"(CREATE OR REPLACE VIEW[\s\S]*?\$\$;)",
    re.IGNORECASE,
)
_MV_NAME_RE = re.compile(
    r"CREATE OR REPLACE VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`",
    re.IGNORECASE,
)


def rename_metric_sql(sql: str, catalog: str | None = None) -> str:
    out = sql
    if catalog:
        out = re.sub(r"`vibe_[^`]+`", f"`{catalog}`", out)
        out = re.sub(r"`marathon_[^`]+`", f"`{catalog}`", out)

    def _sub(m: re.Match[str]) -> str:
        return FK_COLUMN_RENAMES[m.group(1)]

    return _COL_RE.sub(_sub, out)


def split_metric_views(sql_text: str) -> dict[str, str]:
    views: dict[str, str] = {}
    for block in _VIEW_SPLIT_RE.findall(sql_text):
        m = _MV_NAME_RE.search(block)
        if m:
            views[m.group(1)] = block
    return views


def load_failures(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def failed_metric_names(failures: list[dict]) -> list[str]:
    names: list[str] = []
    for row in failures:
        if row.get("phase") != "metric":
            continue
        err = row.get("error") or ""
        m = re.search(r"MetricView `[^`]+`\.`_metrics`\.`([^`]+)`", err)
        if m:
            names.append(m.group(1))
        elif row.get("sql"):
            m2 = _MV_NAME_RE.search(row["sql"])
            if m2:
                names.append(m2.group(1))
    return sorted(set(names))


def sql_execute(profile: str, warehouse_id: str, statement: str, timeout: str = "50s") -> dict:
    payload = json.dumps(
        {"statement": statement, "warehouse_id": warehouse_id, "wait_timeout": timeout}
    )
    proc = subprocess.run(
        [
            "databricks",
            "api",
            "post",
            "/api/2.0/sql/statements/",
            f"--profile={profile}",
            f"--json={payload}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def download_metrics(industry: str, size: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    api = (
        "https://api.github.com/repos/databricks-industry-solutions/"
        f"lakehouse-industry-data-models/contents/data-models/{industry}/v2/{size}/metrics?ref=main"
    )
    items = json.loads(urllib.request.urlopen(api, timeout=60).read())
    for it in items:
        if it.get("type") != "file" or not it["name"].endswith(".sql"):
            continue
        data = urllib.request.urlopen(it["download_url"], timeout=60).read()
        (dest / it["name"]).write_bytes(data)


def main() -> None:
    ap = argparse.ArgumentParser(description="Fix metric-view FK column names and optionally test deploy")
    ap.add_argument("--failures", required=True, help="Path to failures_*.json from install volume")
    ap.add_argument("--industry", default="health_insurance")
    ap.add_argument("--size", default="ecm")
    ap.add_argument("--catalog", default="marathon_health_insurance_ecm")
    ap.add_argument("--profile", default="fe-adp")
    ap.add_argument("--warehouse-id", default="148ccb90800933a1")
    ap.add_argument("--metrics-dir", default="/tmp/hi_metrics")
    ap.add_argument("--out-dir", default="/tmp/hi_metrics_fixed")
    ap.add_argument("--test-deploy", action="store_true")
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()

    failures = load_failures(Path(args.failures))
    targets = failed_metric_names(failures)
    metrics_dir = Path(args.metrics_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.download or not any(metrics_dir.glob("*.sql")):
        download_metrics(args.industry, args.size, metrics_dir)

    all_views: dict[str, str] = {}
    for f in metrics_dir.glob("*.sql"):
        fixed_file = rename_metric_sql(f.read_text(errors="ignore"), catalog=args.catalog)
        out_path = out_dir / f.name
        out_path.write_text(fixed_file)
        all_views.update(split_metric_views(fixed_file))

    missing = [n for n in targets if n not in all_views]
    results = {"fixed": [], "still_failed": [], "removed": [], "missing_sql": missing}

    if args.test_deploy:
        for name in targets:
            if name not in all_views:
                continue
            stmt = all_views[name]
            try:
                resp = sql_execute(args.profile, args.warehouse_id, stmt)
                st = resp.get("status", {}).get("state")
                if st == "SUCCEEDED":
                    results["fixed"].append(name)
                else:
                    err = resp.get("status", {}).get("error", {})
                    results["still_failed"].append(
                        {"name": name, "error": (err.get("message") or str(err))[:400]}
                    )
            except Exception as e:
                results["still_failed"].append({"name": name, "error": str(e)[:400]})

    report_path = out_dir / "poc_report.json"
    report_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nFixed SQL written to {out_dir}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
