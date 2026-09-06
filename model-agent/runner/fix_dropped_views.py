#!/usr/bin/env python3
"""Probe/validate the 7 metric views the fork dropped, against their live idx_ catalogs.

Pulls each dropped view's block from upstream/main, retargets the catalog token to the
live idx_ catalog, and runs CREATE OR REPLACE VIEW to capture the real Spark error.
Reuses install_marathon.sql_exec for auth/warehouse handling.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import install_marathon as im

REPO = Path.home() / "Documents/projects/lakehouse-business-data-models"
VIEW_BLOCK_RE = re.compile(r"(CREATE OR REPLACE VIEW[\s\S]*?\$\$;)", re.IGNORECASE)
TOKEN_RE = re.compile(r"CREATE OR REPLACE VIEW\s+`([^`]+)`\.`_metrics`\.`([^`]+)`", re.IGNORECASE)

# view_name -> (repo-relative file, target idx catalog, profile)
TARGETS = {
    "material_physical_inventory": ("data-models/construction/v2/ecm/metrics/construction_material_metrics_v2_ecm.sql", "idx_construction_ecm", "my-adp"),
    "supply_stock_transfer": ("data-models/energy_utilities/v1/ecm/metrics/energy_utilities_supply_metrics_v1_ecm.sql", "idx_energy_utilities_ecm", "my-adp"),
    "workforce_associate_headcount": ("data-models/grocery/v1/ecm/metrics/grocery_workforce_metrics_v1_ecm.sql", "idx_grocery_ecm", "my-adp"),
    "workforce_associate_tenure_and_compensation": ("data-models/grocery/v1/ecm/metrics/grocery_workforce_metrics_v1_ecm.sql", "idx_grocery_ecm", "my-adp"),
    "content_billing_line": ("data-models/media_broadcasting/v2/ecm/metrics/media_broadcasting_content_metrics_v3_ecm.sql", "idx_media_broadcasting_ecm", "my-adp"),
    "partner_ecosystem_partner": ("data-models/payments_fintech/v1/mvm/metrics/payments_fintech_partner_metrics_v1_mvm.sql", "idx_payments_fintech_mvm", "my-gcp"),
    "shared_fab": ("data-models/semiconductors/v2/ecm/metrics/semiconductors_shared_metrics_v2_ecm.sql", "idx_semiconductors_ecm", "my-adp"),
}


def upstream_block(rel_file: str, view_name: str) -> str | None:
    txt = subprocess.check_output(["git", "-C", str(REPO), "show", f"upstream/main:{rel_file}"]).decode()
    for block in VIEW_BLOCK_RE.findall(txt):
        m = TOKEN_RE.search(block)
        if m and m.group(2) == view_name:
            return block
    return None


def retarget(block: str, target_cat: str) -> str:
    m = TOKEN_RE.search(block)
    token = m.group(1)
    return block.replace(f"`{token}`", f"`{target_cat}`")


import re as _re

# view -> list of (search, replace) applied to the retargeted upstream block.
# Renames use word-boundary regex; source/expr fixes use literal replace.
FIXES = {
    "material_physical_inventory": [(r"\bwarehouse_code\b", "warehouse_id", True)],
    "supply_stock_transfer": [(r"\breceiving_plant_id\b", "receiving_plant_code", True)],
    "workforce_associate_headcount": [(r"\bwork_location_id\b", "store_location_id", True)],
    "workforce_associate_tenure_and_compensation": [(r"\bwork_location_id\b", "store_location_id", True)],
    "content_billing_line": [("`content`.`billing_line`", "`billing`.`billing_line`", False)],
    "partner_ecosystem_partner": [("SUM(CAST((COUNT_IF(is_global_partner = TRUE)) AS DOUBLE))", "COUNT_IF(is_global_partner = TRUE)", False)],
    "shared_fab": [("`shared`.`fab`", "`equipment`.`fab`", False)],
}


def apply_fixes(view_name: str, block: str) -> str:
    for search, repl, is_regex in FIXES.get(view_name, []):
        if is_regex:
            block, n = _re.subn(search, repl, block)
        else:
            n = block.count(search)
            block = block.replace(search, repl)
        assert n >= 1, f"{view_name}: fix {search!r} matched 0 times"
    return block


def fixed_block(view_name: str) -> str:
    rel, target, _ = TARGETS[view_name]
    return apply_fixes(view_name, retarget(upstream_block(rel, view_name), target))


def probe(view_name: str, stmt_override: str | None = None) -> tuple[str, str]:
    rel, target, profile = TARGETS[view_name]
    block = stmt_override or retarget(upstream_block(rel, view_name), target)
    im.sql_exec(profile, f"CREATE SCHEMA IF NOT EXISTS `{target}`.`_metrics`", timeout=60)
    st, err, _ = im.sql_exec(profile, block, timeout=120)
    msg = (err or {}).get("message", "") if isinstance(err, dict) else str(err)
    return st, msg.strip()


def ordered_names(text: str) -> list[str]:
    out = []
    for b in VIEW_BLOCK_RE.findall(text):
        m = TOKEN_RE.search(b)
        out.append(m.group(2) if m else None)
    return out


def file_to_dropped_views() -> dict[str, list[str]]:
    """rel_file -> dropped view names, in upstream file order."""
    by_file: dict[str, list[str]] = {}
    for v, (rel, _, _) in TARGETS.items():
        by_file.setdefault(rel, []).append(v)
    for rel, views in by_file.items():
        up_txt = subprocess.check_output(["git", "-C", str(REPO), "show", f"upstream/main:{rel}"]).decode()
        order = ordered_names(up_txt)
        by_file[rel] = sorted(views, key=lambda v: order.index(v))
    return by_file


def insert_fixed_views():
    up_show = lambda rel: subprocess.check_output(["git", "-C", str(REPO), "show", f"upstream/main:{rel}"]).decode()
    for rel, dropped in file_to_dropped_views().items():
        up_txt = up_show(rel)
        up_names = ordered_names(up_txt)
        path = REPO / rel
        cur = path.read_text()
        for v in dropped:  # upstream order; predecessor already present after prior inserts
            fb = fixed_block(v)
            # retarget the fixed block BACK to this file's source token (undo probe retarget)
            up_blk = upstream_block(rel, v)
            src_token = TOKEN_RE.search(up_blk).group(1)
            _, target, _ = TARGETS[v]
            fb = fb.replace(f"`{target}`", f"`{src_token}`")
            i = up_names.index(v)
            if i == 0:
                first = cur.find("CREATE OR REPLACE VIEW")
                cur = cur[:first] + fb + "\n\n" + cur[first:]
            else:
                pred = up_names[i - 1]
                pm = _re.search(_re.escape(f"`{src_token}`.`_metrics`.`{pred}`"), cur)
                end = cur.index("$$;", pm.start()) + 3
                cur = cur[:end] + "\n\n" + fb + cur[end:]
        path.write_text(cur)
        print(f"inserted {dropped} into {rel}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "raw"
    if mode == "insert":
        insert_fixed_views()
        sys.exit(0)
    for v in TARGETS:
        stmt = fixed_block(v) if mode == "fixed" else None
        st, msg = probe(v, stmt_override=stmt)
        print("=" * 80)
        print(f"{v}  [{TARGETS[v][1]} @ {TARGETS[v][2]}]  ->  {st}")
        if msg:
            print("  ERR:", msg[:400].replace("\n", " "))
