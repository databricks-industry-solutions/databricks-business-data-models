#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import install_marathon as im

# (profile, catalog, table_like) - find real schema + columns
QUERIES = [
    ("my-adp", "idx_construction_ecm", "physical_inventory"),
    ("my-adp", "idx_energy_utilities_ecm", "stock_transfer"),
    ("my-adp", "idx_grocery_ecm", "associate"),
    ("my-adp", "idx_media_broadcasting_ecm", "billing_line"),
    ("my-gcp", "idx_payments_fintech_mvm", "ecosystem_partner"),
    ("my-adp", "idx_semiconductors_ecm", "fab"),
]

for profile, cat, tbl in QUERIES:
    q = (f"SELECT table_schema, table_name, column_name "
         f"FROM `{cat}`.information_schema.columns "
         f"WHERE table_name = '{tbl}' ORDER BY table_schema, ordinal_position")
    st, err, rows = im.sql_exec(profile, q, timeout=90)
    print("=" * 80)
    schemas = sorted(set(r[0] for r in rows))
    print(f"{cat}.{tbl}  schemas={schemas}  ({len(rows)} cols)")
    cols = [r[2] for r in rows]
    print("  cols:", ", ".join(cols))
