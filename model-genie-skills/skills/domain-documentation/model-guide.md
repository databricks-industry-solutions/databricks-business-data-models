# Model Guide — Entry Point Notebook

## Overview

The Model Guide is a single notebook at the project root that serves as the **front door**
for anyone encountering this data model. It combines:
- Static markdown (architecture overview, links, quick orientation)
- Live SQL queries (reference data from INFORMATION_SCHEMA — always current)
- Health summary (reads validation metadata — instantly shows if the model is healthy)

Running the notebook produces a complete, up-to-date reference document.
Browsing it without running shows the last execution results (still useful).

---

## Notebook Name & Location

- **Name:** `Model Guide` (or `{Domain} Model Guide`, e.g., "Sales Order Model Guide")
- **Location:** Project root (e.g., `/Users/.../meridian_sales_order/Model Guide`)
- **Language:** SQL (always SQL — the Model Guide is language-invariant, independent of `etl_language`)
- **Format:** **SQL-shape notebook** (per `etl-development-framework/deployment-and-dab.md`
  "Notebook-format contract" — the Model Guide is always Shape A)

### Notebook-format contract (MANDATORY — do not ship a Python-shape guide)

The first pass shipped the Model Guide as a **Python-shape** notebook (`# Databricks notebook source`
with every cell wrapped in `# MAGIC %sql`). That is off-spec. The Model Guide is a **SQL-shape**
notebook:

- Create it in two steps: `createAsset(assetType='notebook', name='{Domain} Model Guide')` → returns
  `assetId`; then `editAsset(operation='update', ...)` to populate cells and **set the asset `language`
  to `'SQL'`**. `createAsset` does NOT take a `language` argument — language is set on `editAsset` (same
  mechanism the validation skill uses — see `domain-model-validation` SKILL.md). **Set `language: 'sql'`
  on the FIRST cell edit — that flips the asset-level language from the Python default; subsequent cell
  adds inherit it. Confirm via read-back (Rule 13).** Unlike the validation
  notebooks (which set `language` to match `etl_language`), the Model Guide is ALWAYS `'SQL'` regardless
  of `etl_language` — do NOT hard-code Python and do NOT follow `etl_language`.
- **First line:** `-- Databricks notebook source`
- **Cell separator:** `-- COMMAND ----------`
- **Markdown cells:** `-- %md` (NOT `# MAGIC %md`)
- **SQL cells:** raw SQL (NOT wrapped in `# MAGIC %sql`)

This is language-invariant: even when `conventions.yml` `etl_language: python`, the Model Guide stays
SQL-shape (it is a reference/documentation artifact, not part of the ETL language choice).

**Design decision — why SQL as the default language:** The Model Guide contains zero Python.
Using SQL as the default language eliminates the Rule 13 `# MAGIC`-prefix compliance concern
for all SQL and markdown cells — no cell in a SQL-shape notebook ever needs a `# MAGIC` prefix.
If a future widget requirement forces a Python notebook default, document the reason here and
update the read-back gate assertions to account for `# MAGIC %sql` cells under that justified
exception.

**Read-back gate (MANDATORY — this rule does not enforce itself).** A prior run's self-assessment
reported the format rule as "caught" while the Model Guide actually shipped Python-shape (`# MAGIC %sql`
cells). Do not trust recollection — verify. **After the `editAsset` that populates the guide, read the
asset back (`readNotebook` / export source) and assert ALL of:**
1. First line is exactly `-- Databricks notebook source`
2. **No `# MAGIC` prefix appears anywhere** in the source (grep it — a single `# MAGIC %sql`/`# MAGIC %md`
   means it serialized Python-shape)
3. The asset `language` is `'SQL'`

If any assertion fails, re-emit the notebook SQL-shape and re-check. The Phase 4 gate cannot pass until
the read-back is clean.

---

## Runtime Parameters

The Model Guide is a runnable notebook, so it uses the **same runtime-param header** as the ETL
and validation notebooks — catalog/schema are never baked literals (see
`etl-development-framework/deployment-and-dab.md` "Runtime Parameters"). The Model Guide is
ALWAYS a SQL notebook regardless of `conventions.yml` `etl_language` — it is a
reference/documentation artifact, not part of the ETL/validation language choice. Cell 0:

```sql
-- Databricks notebook source
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';

-- COMMAND ----------
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);
```

Model and `_validation_*` tables are then referenced **unqualified**. INFORMATION_SCHEMA queries
are the one exception — they need a catalog-qualified path, so use
`IDENTIFIER(:silver_catalog || '.information_schema.columns')` and filter
`WHERE table_schema = :silver_schema`. Run it interactively by filling the widgets; if it's
scheduled/refreshed by a job, wire `base_parameters` like any other task.

### Hybrid / multi-schema variant (`output_model: hybrid`)

A `hybrid` model spans **two schemas** — a normalized silver schema and a dimensional gold schema
(e.g. `..._silver_sdp` and `..._gold_sdp`). The single-schema header above cannot reference both, so
the Model Guide emits a **4-widget header** and every schema-scoped cell is authored per-layer:

```sql
-- Databricks notebook source
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';
CREATE WIDGET TEXT gold_catalog   DEFAULT '';
CREATE WIDGET TEXT gold_schema    DEFAULT '';

-- COMMAND ----------
-- Gold is the primary analytics surface; set it as the active schema.
USE CATALOG IDENTIFIER(:gold_catalog);
USE SCHEMA  IDENTIFIER(:gold_schema);
```

Rules for the hybrid guide:
- **Set the active schema to GOLD** (the analytics surface). Silver tables are then referenced with an
  explicit `IDENTIFIER(:silver_catalog || '.' || :silver_schema || '.<table>')` path when needed.
- **Duplicate the reference cells per layer.** Cell 4 (Column Dictionary) and Cell 5 (FK map) each get a
  **Gold** and a **Silver** copy — either two cells (labelled "— Gold" / "— Silver") or one cell with a
  `UNION ALL` and a `Layer` column. INFORMATION_SCHEMA queries filter on the matching `:*_schema` widget.
- **Health cells (2–3) read BOTH validation result sets.** Each schema has its **own** `_validation_*`
  tables, created by that layer's validation run (silver run → silver schema; gold run → gold schema —
  `domain-model-validation` is run once per layer, it has no two-schema mode). Query
  `_validation_table_result` in each schema and `UNION ALL` them with a `Layer` column, or show two
  health tables. Cell 2's overall grade reflects both layers. **Guard the gold side:** if the gold
  schema has no `_validation_table_result` (the gold validation run never happened), do not let the
  cell throw `TABLE_OR_VIEW_NOT_FOUND` — this is the "gold unvalidated" stop condition from `SKILL.md`
  (Layer & ETL-type Gate), surface it as a documented gap rather than a broken notebook cell.
- **Entity Overview** lists gold dims/facts and silver 3NF tables, tagged by layer, so a reader sees the
  whole model in one place.
- **Architecture/orientation (Cell 1)** states the two-layer story explicitly: gold star = analytics
  (clean joins), silver 3NF = operational detail / lineage / entities gold doesn't cover.
- **Links / navigation cell carries BOTH per-layer assets.** Hybrid creates two Genie spaces
  (`{Domain} Silver Genie Agent` + `{Domain} Gold Genie Agent`) and two quality dashboards
  (`{Domain} Silver Validation Quality Dashboard` + `{Domain} Gold Validation Quality Dashboard`) —
  the "Ask a business question" and "Check data quality" rows each get a **Gold** and a **Silver**
  link (link by Genie space UUID, per `genie-space-config.md`), not a single link.

The `synced-against` stamp, glossary, and capability index cells are unchanged (singletons); the
links cell is per-layer for hybrid (see above), single-layer otherwise.

---

## Cell Structure

### Cell 0: Runtime-param header (see above) — `CREATE WIDGET` + `USE CATALOG/SCHEMA`

### Cell 1: Welcome & Orientation (Markdown)

```sql
-- COMMAND ----------
-- %md
-- <!-- synced-against: progress.md @ {date} (rev: {short git sha or run_id}) -->
-- # {Domain Name} — Model Guide
--
-- **What is this?** A governed Silver dimensional model for {business domain description}.
--
-- **Schema:** `{silver_catalog}.{silver_schema}`
-- **Entities:** {N} tables ({dim_count} dimensions, {fact_count} facts)
-- **Total rows:** ~{total_rows}
-- **Status:** {DEVELOPMENT | PRODUCTION}
-- **Last validated:** {reads from _validation_run}
--
-- ## Quick Navigation
--
-- | What you need | Where to go |
-- |---|---|
-- | Understand the model (why, architecture, decisions) | [Domain Narrative](docs/explanation/domain_narrative.md) |
-- | Business terms / vocabulary | Glossary (Cell 9 below) |
-- | What questions can this domain answer? | Capability Index (Cell 10 below) |
-- | Ask a business question interactively | [Genie Space](link) |
-- | Learn progressively (tutorials) | [Getting Started](link) |
-- | Check data quality / grades | [Quality Dashboard](link) |
-- | Validate data (regression tests) | `src/silver/validation/` |
-- | Contribute (add tables, fix issues) | [Contributor Guide](link) |
--
-- ## Architecture
--
-- ```
-- {Simplified architecture diagram from domain narrative}
-- ```
--
-- ## Organizational Hierarchy
--
-- ```
-- {hierarchy diagram, e.g., plant → focus_factory → work_center}
-- ```
```

**Generation rules:**
- The first `-- %md` line is the `synced-against` stamp (per `domain-sync/staleness-linter.md`);
  every re-generation refreshes its date/rev. This is the notebook's stamp for the whole guide.
- Pull from domain narrative Section 1 (Executive Summary) and Section 2 (Architecture)
- Links point to actual notebook paths / Genie space URL / dashboard URL; the Domain Narrative
  link is `docs/explanation/domain_narrative.md` (authored by this skill — Explanation quadrant)
- Keep concise — this is orientation, not the full narrative

### Cell 2: Current Health Summary (SQL)

```sql
-- COMMAND ----------
-- Current model health (from most recent validation run)
SELECT
  r.Overall_Grade AS Model_Health,
  r.Run_Timestamp AS Last_Validated,
  r.Entities_Grade_A AS Grade_A_Count,
  r.Total_Entities,
  r.Drift_Alerts_Count AS Active_Drift_Alerts,
  ROUND(TIMESTAMPDIFF(HOUR, r.Run_Timestamp, current_timestamp()), 1) AS Hours_Since_Validation
FROM _validation_run r
ORDER BY r.Run_Timestamp DESC
LIMIT 1
```

**Purpose:** Instantly shows if the model is healthy. If `Hours_Since_Validation` is
large, validation job may have stopped running.

### Cell 3: Entity Overview (SQL)

```sql
-- COMMAND ----------
-- All entities with current grades and row counts
SELECT
  t.Table_Name,
  t.Table_Type,
  t.Tier,
  t.Row_Count,
  t.Grade,
  t.Known_Gaps_Count,
  t.Fk_Orphan_Rate_Pct,
  t.Drift_Columns_Count
FROM _validation_table_result t
WHERE t.Run_Id = (
  SELECT Run_Id FROM _validation_run
  ORDER BY Run_Timestamp DESC LIMIT 1
)
ORDER BY t.Tier, t.Table_Name
```

**Purpose:** At-a-glance entity list with quality grades. Developer immediately
sees which tables exist, their type/tier, and whether anything is degraded.

### Cell 4: Column Dictionary (SQL — Live Reference)

```sql
-- COMMAND ----------
-- Complete column dictionary (live from UC metadata)
SELECT
  t.table_name AS Table_Name,
  c.column_name AS Column_Name,
  c.data_type AS Data_Type,
  CASE WHEN c.is_nullable = 'NO' THEN '✗' ELSE '' END AS Required,
  c.comment AS Description
FROM IDENTIFIER(:silver_catalog || '.information_schema.columns') c
JOIN IDENTIFIER(:silver_catalog || '.information_schema.tables') t
  ON c.table_catalog = t.table_catalog
  AND c.table_schema = t.table_schema
  AND c.table_name = t.table_name
WHERE c.table_schema = :silver_schema
  AND c.table_name NOT LIKE '\\_%' ESCAPE '\\'  -- exclude _validation_*/_gap_registry metadata tables
  AND c.table_name NOT LIKE 'event_log_%'  -- exclude SDP pipeline event-log tables (runtime artifacts, not model tables)
ORDER BY
  CASE
    WHEN t.table_name LIKE 'dim_%' THEN 0
    WHEN t.table_name LIKE 'fact_%' THEN 1
    ELSE 2
  END,
  t.table_name,
  c.ordinal_position
```

**Purpose:** This IS the reference documentation. Live, always current. A developer
can ctrl+F for any column name and see its type, nullability, and description.

### Cell 5: Foreign Key Relationships (SQL — Live Reference)

```sql
-- COMMAND ----------
-- FK relationship map (live from UC metadata)
SELECT
  tc.table_name AS Child_Table,
  kcu.column_name AS FK_Column,
  ccu.table_name AS Parent_Table,
  ccu.column_name AS Parent_Column,
  tc.constraint_name
FROM IDENTIFIER(:silver_catalog || '.information_schema.table_constraints') tc
JOIN IDENTIFIER(:silver_catalog || '.information_schema.key_column_usage') kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN IDENTIFIER(:silver_catalog || '.information_schema.constraint_column_usage') ccu
  ON tc.constraint_name = ccu.constraint_name
  AND tc.table_schema = ccu.table_schema
WHERE tc.table_schema = :silver_schema
  AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY Child_Table, FK_Column
```

**Purpose:** Visual FK map. Shows all join paths without reading DDL files.
Combined with Cell 4, this is the complete schema reference.

### Cell 6: Table Statistics (SQL)

```sql
-- COMMAND ----------
-- Table row counts and sizes (live)
SELECT
  table_name AS Table_Name,
  CASE
    WHEN table_name LIKE 'dim_%' THEN 'DIMENSION'
    WHEN table_name LIKE 'fact_%' THEN 'FACT'
    ELSE 'METADATA'
  END AS Type,
  -- Row count from table properties
  CAST(NULL AS BIGINT) AS Row_Count,  -- placeholder; actual uses DESCRIBE DETAIL or validation data
  comment AS Table_Description
FROM IDENTIFIER(:silver_catalog || '.information_schema.tables')
WHERE table_schema = :silver_schema
  AND table_name NOT LIKE '\\_%' ESCAPE '\\'
ORDER BY
  CASE
    WHEN table_name LIKE 'dim_%' THEN 0
    WHEN table_name LIKE 'fact_%' THEN 1
    ELSE 2
  END,
  table_name
```

**Note:** For actual row counts, prefer reading from `_validation_table_result`
(Cell 3) since INFORMATION_SCHEMA doesn't always have precise counts.
Alternatively, use DESCRIBE DETAIL per table.

**Freshness & coverage (Markdown sub-cell, authored from `build_manifest.md`):** follow the
statistics table with a short markdown cell giving a per-table freshness/coverage line so a
cold-start reader knows how current and complete each table is:

```sql
-- COMMAND ----------
-- %md
-- ### Freshness & Coverage
--
-- | Table | Spans | Refreshes | Coverage |
-- |---|---|---|---|
-- | fact_oee_record | 2025-01-01 – 2026-07-15 | daily 06:00 UTC | 1.82M of 1.82M source rows (100%) |
-- | fact_wip_move_transaction | 2025-03-01 – 2026-07-15 | daily 06:00 UTC | 410K of ~1.1M (DFF plants only — see caveats) |
-- | ... | | | |
```

**Generation rules for the freshness/coverage line:**
- **Spans** = MIN/MAX of the table's date column (the column named in `build_manifest.md`)
- **Refreshes** = the job schedule from `build_manifest.md` (the daily-load DAB job cadence)
- **Coverage** = `{final row count} of {expected source rows} (N%)` from `build_manifest.md`
  §final-row-counts and any filters applied (e.g. `WHERE TRANS_TYPE='PROD'`); when coverage is
  partial, point to the caveat in the narrative / Known Limitations rather than restating it
- This is a static markdown cell (authored at generation time from the manifest), NOT a live
  query — the manifest is the as-built source of truth for coverage.

### Cell 7: Quick-Start Examples (Markdown + SQL)

```sql
-- COMMAND ----------
-- %md
-- ## Quick-Start Queries
--
-- These are the 5 most common questions analysts ask of this model.
-- Copy and modify them for your use case.

-- COMMAND ----------
-- Example 1: OEE by focus factory (last 30 days)
SELECT
  ff.Focus_Factory_Name,
  AVG(o.Oee_Pct) AS Avg_OEE,
  COUNT(*) AS Record_Count
FROM fact_oee_record o
JOIN dim_work_center wc ON o.Work_Center_Key = wc.Work_Center_Key
JOIN dim_focus_factory ff ON wc.Focus_Factory_Key = ff.Focus_Factory_Key
WHERE o.Record_Date >= DATEADD(DAY, -30, current_date())
  AND o.Work_Center_Key != -1
GROUP BY ff.Focus_Factory_Name
ORDER BY Avg_OEE DESC

-- COMMAND ----------
-- Example 2: WIP aging by plant (open jobs)
-- ... (generated from fact stories)

-- COMMAND ----------
-- Example 3: Production lot volume by kanban card
-- ... (generated from fact stories)
```

**Generation rules:**
- 3–5 examples, derived from fact story narratives
- Each answers a real business question
- Exclude -1 Unknown keys in WHERE clauses
- Include comments explaining the join logic

### Cell 8: Known Limitations (Markdown)

```sql
-- COMMAND ----------
-- %md
-- ## Known Limitations
--
-- | Priority | Entity | Gap | Status |
-- |---|---|---|---|
-- | P0 | fact_wip_job | Routing_Key/Bom_Header_Key = -1 | OPEN |
-- | P1 | fact_wip_move_transaction | DFF labor only (partial) | OPEN |
-- | ... | | | |
--
-- For full gap registry, see the [Quality Dashboard](link).
-- For explanation of why each gap exists, see the [Domain Narrative](docs/explanation/domain_narrative.md).
```

**Generation rules:**
- Pull from `docs/.pipeline/handoffs/silver/validation_summary.md` (the validate→document handoff — open/resolved gap
  deltas + status), NOT raw `_gap_registry`. Surface Status IN ('OPEN', 'IN_PROGRESS',
  'DEFERRED') — DEFERRED stays visible; enum in `domain-sync/next-steps-generation.md`.
- Keep to top 5–7 gaps by priority
- Link to full registry in dashboard

### Cell 9: Glossary (Markdown — cold-start business terms)

```sql
-- COMMAND ----------
-- %md
-- ## Glossary
--
-- Business vocabulary an analyst uses that differs from the column names. (These same
-- definitions seed the Genie space instructions; this cell makes them visible to non-Genie
-- users — reading the notebook is enough.)
--
-- | Term | Means | In the model |
-- |---|---|---|
-- | OEE / efficiency | Overall Equipment Effectiveness (can exceed 100%) | `fact_oee_record.Oee_Pct` |
-- | cell | Work center (DFF shop-floor terminology) | `dim_work_center` |
-- | focus factory | Organizational unit between plant and cell | `dim_focus_factory` |
-- | kanban | Pull-signal card that triggers production of a lot | `dim_kanban_card` |
-- | LPN | License Plate Number = production lot identifier | `fact_production_lot` |
-- | routing | Sequence of operations to produce a part | `dim_routing` / `dim_routing_operation` |
-- | BOM | Bill of Materials (components needed) | `dim_manufacturing_bom_header` / `_bom_line` |
-- | WIP aging | Days a job has been open | `DATEDIFF(DAY, Release_Date, current_date())` |
```

**Generation rules:**
- This is the FIRST-CLASS home of the business glossary. The identical term list is used to
  generate `genie-space-config.md` Priority-2 "Business Term Definitions" — author it here and
  reuse it there, so the two never diverge (single source of vocabulary).
- Extract terms from `docs/explanation/domain_narrative.md` fact/dim stories + DDL column COMMENTs; include
  only terms an analyst would use that differ from column names.
- Alternative placement: if the term list is long, author `docs/reference/glossary.md` and link it here
  instead of inlining. A cell is preferred for cold-start visibility; a file only when it would
  bloat the guide.

### Cell 10: Capability Index (Markdown — what questions can this domain answer?)

```sql
-- COMMAND ----------
-- %md
-- ## What Questions Can This Domain Answer?
--
-- Analytical themes this model supports, so a newcomer can see its reach before writing a query
-- or opening Genie.
--
-- | Theme | Example questions | Where to answer it |
-- |---|---|---|
-- | Scale & portfolio | "How many plants? How is volume spread?" | Tutorial 01 / Genie |
-- | OEE performance | "OEE by focus factory / shift / month? Best & worst cells?" | Tutorial 02 / Genie |
-- | WIP flow & aging | "Which jobs are stuck? What's the aging distribution?" | Tutorial 03 / Genie |
-- | Production cadence | "Daily lot volume trend, 7-day rolling average" | Tutorial 03 / Genie |
-- | Cross-fact (lots ↔ jobs) | "How many lots per job? Where do campaigns concentrate?" | Tutorial 03 |
-- | BOM structure | "Components per BOM, multi-level explosion" | Tutorial 03 / Genie |
--
-- Not yet answerable (see Known Limitations, Cell 8): {e.g., job → routing cycle-time
-- analysis (Routing_Key = -1); non-DFF move transactions}.
```

**Generation rules:**
- Derive themes from the Genie sample-query set (`genie-space-config.md`) and the fact stories in
  `docs/explanation/domain_narrative.md` — each theme groups several sample questions.
- The "Not yet answerable" line is sourced from the open gaps in `docs/.pipeline/handoffs/silver/validation_summary.md` —
  it tells a cold-start reader the edges of the model, not just its reach.

### Cell 11: Documentation Map (Markdown)

```sql
-- COMMAND ----------
-- %md
-- ## Full Documentation Map
--
-- | Category | Artifact | Location | What It Answers |
-- |---|---|---|---|
-- | Explanation | Domain Narrative | `docs/explanation/domain_narrative.md` | Why was this built? How do tables relate? |
-- | Reference | This notebook (Cells 4–6) | _(you're here)_ | What columns, types, FKs exist? |
-- | Glossary | This notebook (Cell 9) | _(you're here)_ | What does this business term mean? |
-- | Capability index | This notebook (Cell 10) | _(you're here)_ | What questions can this domain answer? |
-- | How-to | Genie Space | [link] | How do I answer business question X? |
-- | Tutorials | Getting Started | `docs/tutorials/01_getting_started.sql` | How do I learn this model from scratch? |
-- | Validation | Narrative notebooks | `src/silver/validation/narrative_*.sql` | Is the data quality good? |
-- | Quality | Dashboard | [link] | What's the current health at a glance? |
-- | Maintaining | Maintain This Domain | `docs/contributor/maintaining-this-domain.md` | How do I add/fix/re-sync THIS model's tables? (links to repo `docs/developer/` for the full suite) |
--
-- **No ERD is generated here.** Comprehensive entity-relationship diagrams are provided by the
-- Databricks App; the interim relationship views are Cell 5 (live FK map) above and the
-- cross-reference matrix in the Domain Narrative.
```

---

## Generation Protocol

1. Author (or read, if already authored this run) `docs/explanation/domain_narrative.md` — Phase 2 produces
   it; the Model Guide links to it and pulls the architecture/hierarchy summary from it
2. Read `docs/.pipeline/handoffs/silver/validation_summary.md` for grades + gap deltas (Known Limitations, capability
   "not yet answerable"); read `_validation_run`/`_validation_table_result` live only for the
   always-current health cells (Cells 2–3)
3. Read `docs/.pipeline/handoffs/silver/build_manifest.md` for freshness/coverage (Cell 6 sub-cell) — spans, schedule,
   coverage
4. Read `docs/.pipeline/state/run/progress.md` for configuration (catalog, schema, entity list)
5. Assemble the notebook following cell structure above
6. Replace all `{placeholders}` with actual values; write the `synced-against` stamp in Cell 1
7. For quick-start examples: pick the 3–5 most "universal" business questions
   from fact stories (prefer facts with most dimension relationships)
8. NO ERD generation — relationship views are Cell 5 (live FK map) + the narrative
   cross-reference matrix; the Databricks App owns comprehensive ERDs

---

## Cross-File Link Protocol (Dual Links)

Maintain a `{filename → assetId}` registry as files are created in Phases 2–3. When generating
the Model Guide (Phase 4), emit **dual links** for every cross-file reference — the relative
path (Git portability) AND the Databricks browser path:

```markdown
[Domain Narrative](docs/explanation/domain_narrative.md) · [open in browser](/editor/files/{assetId})
```

Relative markdown links do NOT resolve when clicked from a Databricks-rendered notebook; the
`/editor/files/{id}` form does. Both links are emitted so the artifact works in both contexts.

Apply dual links to all cross-references in Cell 1 (Quick Navigation table), Cell 8 (Known
Limitations), Cell 11 (Documentation Map), and any other cell that links to another artifact
by path. Record the registry in the run's handoff output (e.g., in
`docs/.pipeline/handoffs/documentation/asset_registry.md`) so the IDs are available for later
re-runs and the `domain-sync` skill can refresh stale links.

---

## Design Principles

1. **Live over static** — anything that can be a query SHOULD be a query (Cells 2–6)
2. **Links over duplication** — don't restate the domain narrative; link to `docs/explanation/domain_narrative.md`
3. **Scannable in 2 minutes** — developer reads Cell 1 markdown + glances at Cell 3 table = oriented
4. **Runnable for depth** — executing the notebook populates all reference cells with current data
5. **Front door, not deep dive** — this notebook routes people to the right place; it doesn't try to be everything
6. **Cold-start friendly** — the Glossary (Cell 9) and Capability Index (Cell 10) mean a reader
   who has never seen the domain can get oriented without opening Genie or the narrative
7. **No ERD** — the live FK map (Cell 5) + the narrative cross-reference matrix are the interim
   relationship views; comprehensive ERDs come from the Databricks App, not a generated diagram
8. **Stamped** — Cell 1 carries the `synced-against` stamp so `domain-sync` can detect drift
