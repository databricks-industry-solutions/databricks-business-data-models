#!/usr/bin/env python3
"""Render the comprehensive PR body for PR #20 from /tmp/all_fixes.json."""
import json
from pathlib import Path

d = json.load(open("/tmp/all_fixes.json"))
ARROW = " \u2192 "
out = []
w = out.append

total_views = sum(v["views_changed"] for v in d["per_industry"].values())

w("## Summary\n")
w(f"Corrects the metric-view `UNRESOLVED_COLUMN` install failures across the industry ECM/MVM "
  f"models so every metric view installs cleanly. This branch applies **{d['total_ref_fixes']} "
  f"reference corrections** across **{d['files_changed']} metric SQL files** and "
  f"**{total_views} views** in **{d['industries']} industries**. All 80 models (40 ECM + 40 MVM) "
  f"now install with zero metric-view errors, validated end to end on live Databricks catalogs. "
  f"No metric views are dropped: the branch is at full parity with `main` (14,904 metric views).\n")

w("## Root cause\n")
w("Generated metric YAML referenced logical, FK-prefixed, or generic column names, while the "
  "physical schema DDL uses the canonical physical names. At install time "
  "`CREATE VIEW ... WITH METRICS` failed with `UNRESOLVED_COLUMN`. Three families of mismatch:\n")
w("1. **FK / relationship-prefixed names** in metric expressions that resolve to the plain PK on "
  "the source table, for example `member_identity_id`" + ARROW + "`identity_id`, "
  "`pax_profile_id`" + ARROW + "`profile_id`, `awarded_vendor_id`" + ARROW + "`vendor_id`.")
w("2. **Generic single-word names** (`status`, `code`, `name`, `category`, `description`) that "
  "needed the table-qualified physical column, for example `status`" + ARROW + "`requisition_status`, "
  "`code`" + ARROW + "`warehouse_code`, `name`" + ARROW + "`department_name`.")
w("3. **Wrong source schema** on two views, and **one nested aggregate** that is invalid SQL.\n")

w("## Fix breakdown\n")
w(f"- **{d['total_ref_fixes']}** total reference corrections")
w(f"- **{d['distinct_rename_pairs']}** distinct column renames (applied only inside `expr:` / `name:` "
  f"lines, so comments and display metadata are preserved)")
w(f"- **{len(d['source_fixes'])}** source-schema corrections")
w(f"- **{len(d['expr_rewrites'])}** expression rewrites (including one nested-aggregate fix)")
w("- **0** views dropped (full parity with `main`)\n")

w("## Most common corrections\n")
w("| Count | Correction |")
w("|---:|---|")
for s, c in d["rename_pairs"][:30]:
    w(f"| {c} | `{s.replace(' -> ', '` ' + ARROW.strip() + ' `')}` |")
w("")

w("## Per-industry breakdown\n")
w("| Industry | Files | Views fixed | Reference fixes |")
w("|---|---:|---:|---:|")
for k, v in d["per_industry"].items():
    w(f"| {k} | {v['files']} | {v['views_changed']} | {v['ref_fixes']} |")
w(f"| **Total** | **{d['files_changed']}** | **{total_views}** | **{d['total_ref_fixes']}** |")
w("")

w("## Source-schema corrections\n")
for f, v, o, n in d["source_fixes"]:
    w(f"- `{v}`: source {o} " + ARROW.strip() + f" {n}")
w("")

w("## Expression rewrites\n")
labels = {
    "partner_ecosystem_partner": "removes a nested aggregate (an aggregate inside another aggregate is invalid SQL)",
    "donor_wealth_screening": "replaces a non-existent `net_worth_range` column with a CASE band over `estimated_net_worth`",
    "security_derivative": "quotes the DATEDIFF unit argument correctly",
}
for f, v, o, n in d["expr_rewrites"]:
    w(f"- `{v}` " + ARROW.strip() + f" {labels.get(v, 'expression corrected')}:")
    w("```sql")
    w(f"- {o}")
    w(f"+ {n}")
    w("```")
w("")

w("## Documentation\n")
w("- README widgets table now lists all seven installer widgets (added `cataloging_style`, "
  "`catalog_prefix`, `catalog_suffix`; `session_id` moved to an advanced / job-injected note). "
  "The \"some metric views will fail\" limitation is updated because it no longer holds.")
w("- Installer notebook ECM/MVM legend corrected from \"Minimal Viable Model\" to the canonical "
  "\"Minimum Viable Model\".\n")

w("## Adjacent change (not a metric view)\n")
w("One construction schema file drops a duplicate `project.site` DDL stub (commit `16abfc3`). It is "
  "a small structural dedup in the same model family, called out here for transparency and kept in "
  "this branch rather than split into a separate PR.\n")

w("## Validation\n")
w("- All 80 models install with zero metric-view errors, across 40 ECM catalogs and 40 MVM catalogs "
  "on live Databricks.")
w("- Views whose references were corrected were test-compiled "
  "(`CREATE OR REPLACE VIEW ... WITH METRICS`) against live catalogs and returned `SUCCEEDED`.")
w("- Metric-view count is at parity with `main`: 14,904 views, 0 dropped.")
w("- Branch is rebased on the latest `main`, so the diff is limited to the changes above.\n")

# Full per-view log inside a collapsible section
w("## Complete per-view fix log\n")
w(f"<details><summary>Every view corrected, grouped by industry ({total_views} views, "
  f"{d['total_ref_fixes']} fixes)</summary>\n")
for ind, views in d["per_view_log"].items():
    w(f"\n**{ind}**\n")
    for name, changes in views:
        parts = "; ".join(f"`{o}`{ARROW}`{n}`" if len(o) < 110 and len(n) < 110
                          else "expr rewritten" for o, n in changes)
        w(f"- `{name}`: {parts}")
w("\n</details>\n")

body = "\n".join(out)
Path("/tmp/pr20_body.md").write_text(body)
print("body chars:", len(body))
print("total views:", total_views)
assert "\u2014" not in body and "\u2013" not in body, "em/en dash present"
print("no em/en dashes: OK")
print("GitHub 65536 limit:", "OK" if len(body) < 65000 else "TOO BIG")
