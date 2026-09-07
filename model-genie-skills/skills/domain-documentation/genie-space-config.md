# Genie Space Configuration

## Overview

The Genie space is the **how-to guide** layer of the documentation. Analysts ask
business questions in natural language; Genie generates correct SQL using the
model's UC metadata (COMMENTs, FKs) plus curated instructions and sample queries.

This document defines how to auto-generate the Genie space configuration from
existing project artifacts.

---

## Genie Space Creation

```python
# Create via tool:
createAsset(
  asset={
    "assetType": "genie",
    "name": "{Domain} Genie Agent",   # naming convention below (single-layer: no layer word)
    # Place the asset in the PROJECT ROOT folder, NOT the user home directory — see
    # "Asset placement" below. Pass the project folder via createAsset's parent/folder
    # parameter if it exposes one, then VERIFY placement after creation.
    "tableIdentifiers": [
      "{silver_catalog}.{silver_schema}.dim_plant",
      "{silver_catalog}.{silver_schema}.dim_focus_factory",
      "{silver_catalog}.{silver_schema}.dim_work_center",
      # ... all dims and facts
      # EXCLUDE _validation_* metadata tables
    ]
  }
)
```

**Naming convention (one Genie space PER LAYER):**
- **Single-layer model (`normalized` or `dimensional`)** → ONE space, **no layer word**:
  `{Domain} Genie Agent` (e.g. "Sales Order Genie Agent").
- **`hybrid`** → **TWO** spaces, layer word included:
  `{Domain} Silver Genie Agent` (over the 3NF silver schema) **and**
  `{Domain} Gold Genie Agent` (over the dimensional gold star). See the Hybrid variant below.
- The old `{Domain} Analytics` pattern is retired.

**Asset placement — project root, not the user home directory:**
- Create the space in the **project root folder** — the workspace folder that holds this domain's
  project (its `databricks.yml`, `docs/`, `src/`; the same root the DAB deploys into), **not** the
  bare user home (`/Workspace/Users/<you>@…/`). Assets dropped in the home directory are hard to find
  and don't travel with the project.
- Pass the project folder via `createAsset`'s parent/target-folder parameter if it exposes one.
- **Verify after creation** (same discipline as the SDP `root_path` check): read back the created
  asset's path; if it landed in the user home directory instead of the project root, **move it into
  the project folder** before recording its link. A space sitting in the home dir is a placement bug.

**Other rules:**
- Include ALL dim and fact tables
- EXCLUDE `_validation_*` metadata tables (those are for the quality dashboard, not analyst queries)
- **`createAsset` may append a timestamp to the space name** — a call with
  `name="Sales Order Genie Agent"` may create the space as "Sales Order Genie Agent 2026-08-09 04:14:59".
  Do not assume the name you passed is the name that stuck.
- **Link by UUID, not by name — the UUID is the stable reference and never mutates.** In the Model
  Guide, narrative, and any other doc that points at the space, build the link from the space **UUID**
  (`/genie/rooms/{uuid}`), and record the display name only as an adjacent note/comment. This keeps
  documentation correct even if the display name has a timestamp appended or is renamed later — link
  text tied to the passed name will silently mismatch the actual space.
- **Genie space name — timestamp handling.** After `createAsset(assetType='genie')`:
  (1) **Attempt a rename** via the available API (if the platform exposes a rename endpoint at
  creation time, call it immediately to set the clean name);
  (2) **If no rename API is available**, reference the space by **UUID only** everywhere
  downstream (documentation, Model Guide, maintenance guide links) and add a prominent
  `## Pending Manual Step` block to BOTH the maintenance guide
  (`docs/contributor/maintaining-this-domain.md`) AND `docs/.pipeline/handoffs/genie_space_instructions.md`
  with the exact rename instruction (e.g., "In the Genie UI, rename the space from
  'Sales Order Genie Agent 2026-08-09 04:14:59' to 'Sales Order Genie Agent'");
  (3) **Prefer a short base name** (domain word only — e.g., "Sales Order Genie Agent",
  not "Sales Order Analytics Genie Agent") to minimize visual damage from the appended timestamp.
  The docs already resolve via UUID, so a not-yet-renamed space does not break any reference.

### Hybrid / multi-schema variant (`output_model: hybrid`)

A `hybrid` model has tables in **two schemas** (normalized silver + dimensional gold). Create **TWO
separate Genie spaces — one per layer** (this replaces the earlier "one space spanning both schemas"
design):
- **`{Domain} Silver Genie Agent`** — `tableIdentifiers` = all silver tables from
  `{silver_catalog}.{silver_schema}`, EXCLUDING `_validation_*`. Instructions describe the 3NF model
  for operational detail, lineage, and entities the gold star doesn't model.
- **`{Domain} Gold Genie Agent`** — `tableIdentifiers` = all gold dims + facts from
  `{gold_catalog}.{gold_schema}`, EXCLUDING `_validation_*`. Instructions describe the Kimball star as
  the primary analytics surface (clean star joins, conformed dims, surrogate keys).
- **Why two spaces, not one:** keeping each space scoped to a single layer stops Genie mixing silver
  natural keys with gold surrogate keys in the same query. Each space's instruction text should include
  a one-line cross-pointer to the other ("for the dimensional star, use {Domain} Gold Genie Agent";
  "for operational/3NF detail, use {Domain} Silver Genie Agent") so analysts can hop between them.
- Both spaces follow the **Asset placement** rule above (project root, not home) and are created once,
  at Finalize, over their fully `VALIDATED` layer.
- **Catalog/schema here are DEPLOY-TIME values, not notebook widgets.** A Genie space is created
  against one specific environment, so `{silver_catalog}.{silver_schema}` resolves from the
  target's `conventions.yml`/DAB variables at `createAsset` time (same model as dashboards — the
  asset is bound to an env, not promoted as a notebook). To stand up a Genie space in prod, run
  `createAsset` with the prod catalog/schema.
- **Genie space config and the quality dashboard are language-invariant** — unaffected by
  `conventions.yml` `etl_language`. They are deploy-time assets, not generated MERGE/validation
  notebooks.

---

## Instruction Text Generation

Genie space instructions are limited (~4000 chars). Prioritize in this order.

**`synced-against` stamp (mandatory):** the instruction text ends with a stamp footer, and the
same stamp is recorded at the top of the exported `docs/.pipeline/handoffs/genie_space_instructions.md`, per
`domain-sync/staleness-linter.md`:

```
<!-- synced-against: progress.md @ {date} (rev: {short git sha or run_id}) -->
```

For the Genie space, the stamp goes in BOTH places (the instruction-text footer inside the space
AND `docs/.pipeline/handoffs/genie_space_instructions.md`) so the staleness linter can check the space without querying
the live asset. Refresh it on every regeneration.

### Priority 1: Hierarchy & Joins (most important)

```
This is the Manufacturing Silver dimensional model.

Organizational hierarchy: dim_plant → dim_focus_factory → dim_work_center.
To drill down geographically, join through this chain.

Key join patterns:
- OEE analysis: fact_oee_record JOIN dim_work_center ON Work_Center_Key, JOIN dim_shift ON Shift_Key
- Production lots: fact_production_lot JOIN dim_kanban_card ON Kanban_Card_Key, JOIN dim_plant ON Plant_Key
- WIP jobs: fact_wip_job JOIN dim_plant ON Plant_Key, JOIN dim_work_center ON Work_Center_Key
- Completions: fact_wip_completion JOIN dim_work_center ON Work_Center_Key
- Material transactions: fact_wip_material_transaction JOIN dim_plant ON Plant_Key
- Move transactions: fact_wip_move_transaction JOIN dim_routing_operation ON Routing_Operation_Key
- Production schedule: fact_production_schedule JOIN dim_plant ON Plant_Key
```

**Generation rule:** Derive from DDL FK definitions + domain narrative cross-reference matrix.
One line per fact showing its primary dimension joins.

**Hybrid two-layer preamble (prepend to Priority 1 when `output_model: hybrid`):**

```
This domain has TWO layers in separate schemas:
- GOLD ({gold_schema}) — a dimensional star. PREFER this for analytical questions: clean
  surrogate-key joins between facts (fact_sales_order_line, fact_otd, ...) and conformed dims
  (dim_customer, dim_material, dim_date, ...). Default here unless the question needs raw detail.
- SILVER ({silver_schema}) — the normalized 3NF model. Use for operational detail, lineage, or
  entities the gold star does not model. Silver uses natural/business keys, NOT gold surrogate keys.
Do NOT join silver tables to gold tables in one query — the key systems differ (natural vs surrogate).
```

Then list the gold star's fact→dim joins (as above), and — if silver tables answer questions gold
doesn't — a short second block of the key silver join paths, clearly under a "SILVER (operational
detail)" heading so the two key systems stay separate.

### Priority 2: Business Term Definitions

```
Business terms:
- "OEE" or "efficiency" = fact_oee_record.Oee_Pct (percentage, can exceed 100%)
- "aging" or "WIP age" = DATEDIFF(DAY, fact_wip_job.Release_Date, current_date()) WHERE Status not complete
- "cell" = work_center (DFF terminology)
- "focus factory" = organizational unit between plant and cell
- "kanban" = pull-signal card that triggers production of a lot
- "LPN" = License Plate Number = production lot identifier
- "routing" = sequence of operations to produce a part
- "BOM" = Bill of Materials (components needed)
```

**Generation rule:** This term list is the SAME vocabulary authored in the Model Guide Glossary
cell (`model-guide.md` Cell 9) — author it once there and reuse it here so the Genie space and
the Model Guide never diverge. Source terms from `docs/explanation/domain_narrative.md` fact/dim stories +
DDL column COMMENTs; focus on terms an analyst would use that differ from column names. (The
Model Guide cell exists so non-Genie users see these definitions too.)

### Priority 3: Caveats & Known Gaps

```
Important caveats:
- FK values of -1 mean "Unknown" (no match found). ALWAYS filter WHERE {Key} != -1 for aggregations.
- fact_wip_move_transaction has DFF labor data only (not all plants).
- fact_wip_job.Routing_Key and Bom_Header_Key are always -1 (gap: revision lookup not implemented).
- dim_routing_operation.Work_Center_Key is always -1 (no cross-reference between Oracle ops and DFF cells).
- OEE values can exceed 100% or be negative (not capped — reflects real operational data).
```

**Generation rule:** Pull from `docs/.pipeline/handoffs/silver/validation_summary.md` — specifically its "changed Genie
caveats" and gap deltas — surfacing caveats whose Status IN ('OPEN', 'IN_PROGRESS', 'DEFERRED',
'ACCEPTED'), plus `docs/.pipeline/state/run/progress.md` constraint fixes. (The validation skill has already reconciled the
gap registry against the latest run and recorded which caveats changed; read that rather than
raw `_gap_registry`.) Only include caveats that would confuse an analyst getting unexpected
results — an unpopulated column is confusing whether the gap is OPEN, DEFERRED, or ACCEPTED; all
three surface as caveats, only RESOLVED is dropped. Status enum is defined in
`domain-sync/next-steps-generation.md`.

### Priority 4: Grain Descriptions (if space permits)

```
Table grains:
- fact_oee_record: one row per work_center per shift per day (hourly aggregated to shift)
- fact_wip_job: one row per WIP job (work order)
- fact_production_lot: one row per LPN (physical container produced)
- fact_wip_completion: one row per production completion event (LPN transaction)
- fact_wip_material_transaction: one row per material issue/return event
- fact_wip_move_transaction: one row per labor move between operations
- fact_production_schedule: one row per demand line (planned production)
```

**Generation rule:** Pull from domain narrative fact stories (grain section).

---

## Sample Query Generation

### Mandatory Pre-Step: Read the Column Dictionary

Before writing ANY sample query, read the actual column dictionary for every table it
references — from `information_schema.columns` (if the Model Guide has run) or the pipeline
SQL. **Copy column names from the schema; never infer them from business semantics.** A prior
run invented `atp_check.requested_date` / `atp_check.confirmed_date` — columns that don't
exist; the real columns are `requested_quantity`, `confirmed_quantity`,
`earliest_confirmation_date`, `check_timestamp`. Every invented column name becomes a syntax
error when the query runs.

```sql
-- Read the column list for a table before drafting any query that references it
SELECT column_name, data_type, comment
FROM IDENTIFIER(:silver_catalog || '.information_schema.columns')
WHERE table_schema = :silver_schema
  AND table_name = '{target_table}'
ORDER BY ordinal_position
```

**FK column names are NOT always `{parent_entity}_id`.** Read the column COMMENTs (which
document FK targets) before writing JOINs — e.g., `return_order` joins its parent via
`original_order_id`, not `order_id`. If the join column name is unclear, read the COMMENTs
directly:

```sql
-- Read column comments to identify FK join columns before writing JOINs
SELECT column_name, comment
FROM IDENTIFIER(:silver_catalog || '.information_schema.columns')
WHERE table_schema = :silver_schema
  AND table_name = '{table_name}'
ORDER BY ordinal_position
```

### Strategy: Star Schema Cross-Reference

> **Applies to star-shaped models** (`output_model: dimensional`, the gold layer of `hybrid`, or any
> fact/dim schema). **A `normalized` 3NF model has no facts/dims** — for it, generate sample queries
> from the narrative's entity relationships instead (core entity + its parent/child joins, e.g.
> "orders by customer", "order lines by order and material"), not from a fact × dim cross-reference.
> See `phase-protocol.md` Phase 5 step 3 for the per-`output_model` breakdown. The rest of this section
> assumes the star case.

For each fact, generate sample queries by combining it with its primary dimensions.
The pattern:

```
For each fact F:
  For each dimension D that F joins to (WHERE FK != -1 is common):
    Generate: "[measure] by [dimension attribute]" query
```

### Sample Query Format

Each sample query needs:
- **Title:** Natural language question (what an analyst would type)
- **SQL:** Correct query with proper joins, filters, and aggregations
- **Description:** Brief explanation of what it returns

### Auto-Generated Sample Queries (Template)

| # | Question (Title) | Fact | Dimensions | Measure |
| --- | --- | --- | --- | --- |
| 1 | Average OEE by focus factory | fact_oee_record | dim_work_center → dim_focus_factory | AVG(Oee_Pct) |
| 2 | OEE trend by shift over time | fact_oee_record | dim_shift | AVG(Oee_Pct) by Record_Date |
| 3 | Open WIP jobs by plant | fact_wip_job | dim_plant | COUNT(*) WHERE status = open |
| 4 | WIP aging (days) by work center | fact_wip_job | dim_work_center | AVG(DATEDIFF) |
| 5 | Production lot volume by month | fact_production_lot | (date) | SUM(Lot_Qty) |
| 6 | Production lots by kanban card | fact_production_lot | dim_kanban_card | COUNT(*) |
| 7 | Completion rate by plant | fact_wip_completion | dim_plant | COUNT(*) per day |
| 8 | Material consumption by plant | fact_wip_material_transaction | dim_plant | SUM(Transaction_Qty) |
| 9 | Labor moves by routing operation | fact_wip_move_transaction | dim_routing_operation | COUNT(*) |
| 10 | Planned vs actual production | fact_production_schedule + fact_production_lot | dim_plant | Scheduled_Qty vs Lot_Qty |
| 11 | Top work centers by OEE | fact_oee_record | dim_work_center | AVG(Oee_Pct) TOP N |
| 12 | BOM component count by header | dim_manufacturing_bom_line | dim_manufacturing_bom_header | COUNT(components) |
| 13 | Routing operations per routing | dim_routing_operation | dim_routing | COUNT(ops) |
| 14 | Plants by production volume | fact_production_lot | dim_plant | COUNT(lots) |
| 15 | Kanban card utilization | fact_production_lot | dim_kanban_card | COUNT(lots) per card |

### Sample Query SQL Template

```sql
-- Title: Average OEE by focus factory
-- Description: Shows average OEE percentage grouped by focus factory, excluding unknown work centers.
SELECT
  ff.Focus_Factory_Name,
  ROUND(AVG(o.Oee_Pct), 2) AS Avg_OEE,
  COUNT(*) AS Record_Count
FROM {silver_catalog}.{silver_schema}.fact_oee_record o
JOIN {silver_catalog}.{silver_schema}.dim_work_center wc
  ON o.Work_Center_Key = wc.Work_Center_Key
JOIN {silver_catalog}.{silver_schema}.dim_focus_factory ff
  ON wc.Focus_Factory_Key = ff.Focus_Factory_Key
WHERE o.Work_Center_Key != -1
  AND o.Shift_Date >= DATEADD(DAY, -30, current_date())   -- NOT Record_Date — verify column names against live schema
GROUP BY ff.Focus_Factory_Name
ORDER BY Avg_OEE DESC
```

---

## MANDATORY: Sample Query Validation Gate (shared with tutorials)

**Every generated Genie sample query MUST be executed against the live schema and return
non-empty, correct results BEFORE it ships in the space.** This is the *same* gate the
tutorials use (`tutorials.md` "Query Validation Gate") — apply it identically here. A Genie
space that ships an unvalidated query hands analysts SQL that errors or returns 0 rows, which
is worse than no sample.

The first pass shipped `o.Record_Date` in 8 Genie queries when the schema column is
`Shift_Date` — the tutorials' gate caught it, but the Genie generator didn't inherit the fix.
This gate closes that seam.

**Protocol (per sample query):**
1. **Resolve column names against the live schema first** — `readTable` / INFORMATION_SCHEMA,
   not from memory or from the S2T doc (which may name a source column, not the silver column).
2. **Run the query** in scratchpad (`executeCode`). It must return non-empty rows.
3. **If it errors** (unknown column, bad join) → fix against the live schema, re-run.
4. **If it returns 0 rows** → diagnose exactly as the tutorials gate says (probe FK overlap,
   sandbox data gaps); pivot to a working join path. Treat 0-row as a data gap, not success.
5. Only queries that pass steps 2–4 go into the space.

**Sandbox / dev data gaps:** When validating sample queries against sandbox or dev data,
expect NULL FK columns (e.g. 100% NULL `sales_contract_id`) and date-range gaps (all data
historical, no rows matching `>= current_date()`). Document these as caveats in the Genie
instruction text (Priority 3: Caveats & Known Gaps); remove production-scale date filters
(e.g. `>= current_date()`) from sample queries; do not treat empty results from those filters
as query bugs.

**Gate:** all sample queries executed non-empty; the space is verified with at least one test
question (Phase 5 gate). Do not create the space with unvalidated queries.

---

## UC Comment Enrichment Protocol

Before creating the Genie space, ensure UC metadata is complete. **The `ddl_{entity}.sql` files are
the source of truth for COMMENTs, not the live tables** — a comment applied only to a live table is
lost the next time the model deploys to a fresh environment (`CREATE TABLE IF NOT EXISTS` re-runs from
the DDL). So enrichment is a two-step, DDL-first process:

1. **Write the comment into the DDL file** (primary). Add/repair the inline `COMMENT '...'` clause on
   each column and the table-level `COMMENT` in `src/silver/ddl/ddl_{entity}.sql`. When the model next
   deploys, the comments are created atomically with the schema — no post-deploy enrichment needed.
   If a DDL file is missing or is a placeholder that won't write cleanly, that is a build-skill defect —
   flag it, and author the full `CREATE TABLE` from the live schema so it round-trips.
2. **Reconcile the live tables** (catch-up). For already-deployed tables, apply the same comments to the
   live schema with `ALTER ... COMMENT` so UC/Genie reflect them immediately. Emit these as the runnable
   `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` (see below). This mirrors the DDL; it is never the source of truth.

> **SDP EXCEPTION (`etl_type: sdp_pipeline`):** there are no `ddl_{entity}.sql` files — the pipeline
> `src/{layer}/pipeline/{entity}.sql` file carries the COMMENTs inline and IS the schema. Write comment
> fixes into the **pipeline file** (step 1's write-target), and note that re-running the pipeline
> re-applies them atomically — a fresh deploy does NOT lose them, so the step-2 live-ALTER catch-up is
> only needed when you want the comments visible before the next pipeline run. `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`
> for SDP therefore holds mainly `SET TAGS` and any post-materialization FK constraints, not a full
> column-comment ALTER set. For `hybrid`, audit both the silver and gold pipeline directories.

Run the live ALTERs against the target env — set the session first (`USE CATALOG
IDENTIFIER(:silver_catalog); USE SCHEMA IDENTIFIER(:silver_schema);`) so ALTER refs are unqualified and
the audit query reads the right catalog; never hard-code catalog/schema.

### Audit Query

Audit both the **DDL files** (the deploy source) and the **live schema** (what UC currently shows).
The live audit below finds tables/columns UC is missing; a DDL that lacks a COMMENT clause is the
actual gap to fix (step 1), even if the live table happens to already have the comment.

```sql
-- Find tables/columns missing COMMENTs
SELECT
  table_name,
  column_name,
  data_type,
  comment,
  CASE WHEN comment IS NULL OR TRIM(comment) = '' THEN 'MISSING' ELSE 'OK' END AS Status
FROM IDENTIFIER(:silver_catalog || '.information_schema.columns')
WHERE table_schema = :silver_schema
  AND table_name NOT LIKE '\\_%' ESCAPE '\\'
ORDER BY Status DESC, table_name, ordinal_position
```

### Enrichment Pattern

For any column missing a COMMENT:

1. **Fix the DDL** — add the inline clause in `ddl_{entity}.sql`:
   ```sql
   {column_name}  {type}  COMMENT '{description}',   -- inline in the CREATE TABLE column list
   ```
2. **Reconcile the live table** — the catch-up ALTER (also written to `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`):
   ```sql
   ALTER TABLE {table_name}
     ALTER COLUMN {column_name} COMMENT '{description}';
   ```

Source the description from (in priority order):
1. **Spec `Metamodel description`** (from `vibe_metamodel_attribute.description`) / table-level `Metamodel description` — the primary source
2. DDL notebook (if a COMMENT was defined but not applied)
3. S2T mapping column descriptions
4. Domain narrative (entity stories)
5. Column name inference (last resort: `Plant_Key` → "Foreign key to dim_plant")

### `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` — runnable, not a log

This file is the **idempotent catch-up script** that reproduces every COMMENT and TAG applied to the
live schema, so a fresh already-deployed environment can be brought to parity by running it. It is a
runnable artifact, **not a prose summary**.

- Emit the **actual** `ALTER TABLE ... ALTER COLUMN ... COMMENT '...'` statements — one per enriched
  column — plus the `ALTER TABLE ... SET TAGS (...)` statements. Do **not** collapse the column comments
  into a "-- Example of the pattern used" note; write every statement out.
- Emit the per-column `ALTER ... ALTER COLUMN ... SET TAGS ('glossary_term' = '...')` statements too, and have the audit query flag columns in the **built tables** (the tables this build creates in the silver/gold catalog+schema) whose spec carries a `Glossary term` but whose live `glossary_term` column tag is missing. Scope the audit to the `glossary_term` key on built tables only — do not audit incoming model shells (which may use a different key and would generate false-positive "missing" flags).
- Escape single quotes in comment text (`''`) so the script parses.
- Idempotent: re-running it only re-asserts current comments/tags (safe to run repeatedly). Re-audit on
  regeneration and only add ALTERs for genuinely new gaps.
- Because the DDL now carries the same comments (step 1), this script is the *deployed-env* convenience,
  not the source of truth. Note that duality in the file header.

### Tag Enrichment

Add UC tags for discoverability:

```sql
ALTER TABLE {table_name}
  SET TAGS ('domain' = '{domain_name}', 'entity_type' = '{dim|fact}', 'tier' = '{0-4}');
```

**Glossary tags (per column).** For every column carrying a `Glossary term` in the spec, emit a
column tag alongside the table governance tags:
```sql
ALTER TABLE {table_name} ALTER COLUMN {column_name} SET TAGS ('glossary_term' = '{term}');
```
Key is exactly `glossary_term` (`naming-standards.md` §5.6). Governed-vocabulary probing (below) applies to ALL tag keys including `glossary_term` — some workspaces govern it too. Probe and handle `glossary_term` the same way: attempt in scratchpad; on a governed-tag rejection, skip + record the skip, do not fail the phase.

**Governed tag vocabularies — probe before you apply.** Some workspaces enforce an allowed-values list
on tag keys (governed tags). A `domain='{domain_name}'` apply will be *rejected* if `{domain_name}` is
not in the workspace's allowed vocabulary for the `domain` key (this happened on the Meridian run —
`sales_order` was not allowed). Do not discover this at apply-time:

1. Probe the allowed values for the `domain` key first — concretely, either:
   ```sql
   -- Option A: read the governed-tag allowed-values catalog (if the workspace exposes it)
   SELECT tag_value
   FROM system.information_schema.tag_allowed_values   -- name varies by workspace/UC version
   WHERE tag_name = 'domain';
   -- empty result   → no governance on this key → apply freely
   -- non-empty      → your value must be in the list, else it will be rejected
   -- query ERRORS (object not found — this catalog isn't exposed here) → DON'T assume "no
   --   governance"; the object being absent tells you nothing about whether the tag is governed.
   --   Fall through to Option B, which probes the actual apply behavior.
   ```
   ```sql
   -- Option B (portable fallback): attempt one SET TAGS in scratchpad on a single table and catch it
   ALTER TABLE {one_table} SET TAGS ('domain' = '{domain_name}');
   -- succeeds → allowed; errors with a governed-tag/allowed-values violation → rejected, skip it
   ```
2. If the value is allowed → apply `domain` along with `entity_type` and `tier`.
3. If it is rejected → **skip the `domain` tag, apply `entity_type` + `tier` (always safe), and record
   the skip** in `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` (a comment noting the restricted vocabulary) and in the
   maintenance guide. Do not fail the phase over a governed-tag rejection. (On the Meridian run,
   `domain='sales_order'` was rejected — this is the expected, non-fatal path.)

---

## Maintenance on Re-Run

For point updates after the space exists, do NOT hand-regenerate — load `domain-sync`, which
scopes the change (e.g. a single new caveat) and re-stamps `synced-against`. A full
documentation re-run is warranted only for wholesale changes. Either way:

1. **Instructions:** Regenerate full text (replace existing) and refresh the `synced-against`
   footer + `docs/.pipeline/handoffs/genie_space_instructions.md` stamp. Changes propagate immediately.
2. **Sample queries:** Compare generated set against existing:
   - New tables → add sample queries
   - Removed tables → remove sample queries
   - Changed FKs → update affected queries
3. **UC COMMENTs:** Re-audit. Only generate ALTERs for new gaps (don't overwrite existing comments).
4. **Genie space tables:** Update table list if model expanded.

---

## What Genie Handles vs. What Needs a Tutorial

| Complexity | Example | Handled By |
| --- | --- | --- |
| Single-fact + 1–2 dims | "OEE by shift" | Genie (directly) |
| Multi-dim drill | "OEE by plant then focus factory" | Genie (with hierarchy instruction) |
| Time series | "WIP trend this month" | Genie (standard date filter) |
| Cross-fact join | "Planned vs actual by plant" | Genie (with sample query as guide) |
| Multi-step analysis | "BOM cost rollup across 3 levels" | Tutorial notebook |
| What-if / parameterized | "Show me this for plant X" | Genie + parameterized sample |
| Complex aggregation | "Rolling 7-day OEE with shift normalization" | Tutorial notebook |

The **80/20 rule:** Genie handles 80% of analyst questions. The 20% that require
multi-step logic, complex CTEs, or domain explanation get routed to tutorials.
