# Table Narrative Template

## Overview

Each entity gets one SQL notebook in `src/silver/validation/` named `narrative_{entity}.sql`.

> **Notebook language follows `etl_language`.** These validation notebooks use the SAME shape
> as the ETL notebooks (`conventions.yml` `etl_language`). Under `sql` (default) they are
> **native SQL notebooks** — `-- Databricks notebook source`, `-- COMMAND ----------` cells,
> `-- %md` markdown, and NO `%sql` prefix on cells (they are already SQL). Under `python` they
> are Python notebooks: `# Databricks notebook source`, `# MAGIC %sql` / `# MAGIC %md` cells,
> and `spark.sql(f"...")` for any cell feeding a Python step. File extension follows suit
> (`narrative_{entity}.sql` vs `.py`). Full spec: `etl-development-framework/deployment-and-dab.md`
> "Notebook-format contract".
>
> **First-pass note:** the initial manufacturing run emitted Python-format notebooks with
> `# MAGIC %sql` on every cell and zero real Python even though the domain was SQL-native. That
> was the bug this inheritance rule fixes — SQL-native domains get native SQL notebooks.

The notebook serves **dual purposes**:
1. **Onboarding document** — a developer reads it top-to-bottom to understand the table
2. **Regression test** — when executed, it validates data quality and writes results to metadata tables

> **These are validation-owned per-table regression narratives** — one runnable notebook per
> entity, asserting that table's data state. They are distinct from the **domain-level
> narrative**, which is the prose Explanation document now owned by `domain-documentation`
> (`docs/explanation/domain_narrative.md`). This skill emits the per-table `narrative_{entity}` notebooks;
> it does NOT author the domain-wide storytelling document.

Two variants exist: **Dimension** (simpler — no integration section) and **Fact** (includes
star schema integration checks). Both follow the same cell structure with facts having
additional cells at the end.

**Runtime parameters:** these notebooks read catalog/schema from widgets — never bake literals
(see `validation-schema.md` "Runtime Parameters"). Every narrative notebook opens with:

```sql
-- Databricks notebook source
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';

-- COMMAND ----------
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);
```

All table references in the cells below are then **unqualified** (session context resolves
them), and the validation job passes `silver_catalog`/`silver_schema` via `base_parameters`.

> **Reserved-word entities — escape `{table_name}` at every `FROM`/`DESCRIBE` substitution.** The
> templates below write `FROM {table_name}` for readability; when the entity's physical name is a
> SQL reserved word (`order`, `group`, `user`, …), substitute it **backtick-quoted** — `` FROM `order` `` —
> or the cell is a syntax error. Backticks are always safe around any identifier, so a builder that
> is unsure can backtick every substituted `{table_name}`. This is the table-reference half of
> Pitfall §7 (`phase-protocol.md`); the metadata-literal half — store the **bare** name in `Table_Name`
> columns, never `` `order` `` inside a string — still applies to the Write Results cell.

---

## Cell Structure — Dimension Variant

> **Canonical cell order (SKILL.md Rule 27).** Cells are numbered to the canonical order and
> the number IS the position: (1) Narrative markdown, (2) Row Count/PK, (3) FK checks, (4) BK
> Null Check, (5) POPULATION, (6) INTEGRATION (facts only), (7) DRIFT, (8) Data Profile, (9)
> Sample Rows, (10) Write Results. The **dimension variant omits the fact-only cell (6)
> INTEGRATION but keeps the numbering scheme** — a dim's cells are 1,2,3,4,5,7,8,9,10 (plus the
> Cell 0 header). Profile (8) and Sample (9) come AFTER the validation checks and BEFORE Write
> Results (10). Business-rule checks (Check_Type = 'BUSINESS_RULE') are OPTIONAL and, when
> present, ride alongside Cell 5 (see "Cell 5b (optional)") — they are not one of the ten
> mandatory cells.

### Cell 0: Runtime-param header (see above) — `CREATE WIDGET` + `USE CATALOG/SCHEMA`

### Cell 1: Narrative Header (Markdown)

```sql
-- COMMAND ----------
-- %md
-- # dim_{entity} — Narrative & Validation
--
-- ## Purpose
-- {1-2 sentence purpose from DDL COMMENT + S2T mapping intent}
--
-- ## Grain
-- One row per {grain description}. Expected ~{row_count} rows.
--
-- ## Natural Key
-- {NK columns} → SHA2 → `{Entity}_Key` (BIGINT surrogate)
--
-- ## Source
-- `<src_{logical}>.{source_table}` ({source_row_count} rows; prefix is a runtime param)
-- {any filters applied in MERGE}
--
-- ## Relationships
-- - **Parent of:** {list of child tables that FK to this dim}
-- - **Child of:** {parent dim this FKs to, or "Root dimension (no parent)"}
--
-- ## Hierarchy Position
-- `{hierarchy path, e.g., plant → focus_factory → work_center}`
--
-- ## Known Gaps & Annotations
-- {List each known gap from gap_registry for this table}
-- {List each "why is it this way?" annotation from progress.md fixes}
--
-- ## Build History
-- - **Built:** {date from progress.md}
-- - **Grade at build:** {grade from progress.md}
-- - **Fixes applied:** {list constraint relaxations, dedup tricks}
```

### Cell 2: Row Count, Freshness & PK Uniqueness

*Rule 27 slot (2) "Row Count/PK" — both queries live here, run adjacently.*

```sql
-- COMMAND ----------
-- Row count and freshness check
SELECT
  '{entity}' AS Entity,
  COUNT(*) AS Row_Count,
  MAX(_loaded_at) AS Last_Load_Timestamp,
  ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load,
  MIN(_loaded_at) AS First_Load_Timestamp
FROM {table_name}

-- COMMAND ----------
-- PK uniqueness: expect 0 duplicates
SELECT
  '{entity}' AS Entity,
  'PK_Uniqueness' AS Check_Name,
  COUNT(*) AS Total_Rows,
  COUNT(DISTINCT {Entity}_Key) AS Distinct_Keys,
  COUNT(*) - COUNT(DISTINCT {Entity}_Key) AS Duplicate_Count,
  CASE
    WHEN COUNT(*) = COUNT(DISTINCT {Entity}_Key) THEN 'PASS'
    ELSE 'FAIL'
  END AS Status
FROM {table_name}
```

### Cell 3: FK Integrity (one query per FK)

> ## ⛔ MANDATORY FK CELL CHECKLIST — READ BEFORE WRITING THIS CELL
>
> **ONE dedicated cell per FK — never collapse multiple FKs into one cell.**
>
> Before writing Cell 3, complete this checklist:
> 1. Open the DDL notebook (`src/silver/ddl/`) for this entity and list every declared FK column
> 2. For each FK, read `build_manifest.md` §3 for that FK's **FK-resolution attribute** (the fact
>    source col ↔ dim join attribute the load actually used) and join the orphan check the SAME
>    way — never a re-derived inline SHA2. This carries the OEE-bug fix forward: validation
>    measures orphans against the real load path, not a rehashed key. The threshold is the
>    manifest §7 value, not an S2T guess.
> 3. For each FK, create one separate cell named `FK to {dim_name}` (or `FK to {fact_name}` for cross-fact)
> 4. Verify the cell count equals the FK count — no exceptions
> 5. P0 deferred FKs (all values = -1, source not ingested) **still need a cell** — mark `Status = 'KNOWN_GAP'`, `Is_Accepted_Exception = TRUE`, `Threshold_Value = NULL`
> 6. Wire every FK cell into Write Results as its own CTE + UNION ALL row
>
> **Common failure mode:** bundling multiple FK checks into one cell, then only extracting
> one when splitting. This causes silent gaps — FK integrity is never measured for the
> skipped dimensions, and the validation dashboard shows a falsely clean picture.
> This failure was observed in `narrative_fact_oee_record` (July 2026) where Work_Center_Key
> and Plant_Key FKs were silently omitted, hiding a P0 SHA2 hash mismatch across 156K rows.

```sql
-- COMMAND ----------
-- FK integrity: {Entity} -> {Parent_Dim}
-- Threshold: {threshold_pct}% (from build_manifest.md §7)
-- FK-resolution attribute: join on {fact_src_col} = {dim_join_attr} (build_manifest.md §3 — same as the load)
-- Known exception: {exception_note_or_none}
SELECT
  '{table_name} -> {parent_dim}' AS Check_Name,
  COUNT(*) AS Total_Rows,
  SUM(CASE WHEN p.{Parent_Entity}_Key IS NULL THEN 1 ELSE 0 END) AS Orphan_Count,
  ROUND(100.0 * SUM(CASE WHEN p.{Parent_Entity}_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4) AS Orphan_Pct,
  CASE
    WHEN ROUND(100.0 * SUM(CASE WHEN p.{Parent_Entity}_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4) <= {threshold_pct} THEN 'PASS'
    ELSE 'FAIL'
  END AS Status
FROM {table_name} c
LEFT JOIN {parent_dim} p
  ON c.{Parent_Entity}_Key = p.{Parent_Entity}_Key
WHERE c.{Parent_Entity}_Key != -1  -- Exclude intentional Unknown references
```

### Cell 4: Business Key Null / Dropped Data Check

> ## ⚠️ MANDATORY BK NULL CHECK — READ BEFORE WRITING THIS CELL
>
> Every table MUST have a BK Null Check cell that validates the natural key (NK) columns
> composing the surrogate key have no NULL or empty-string values. This catches:
> - Data dropped during ETL (source NULLs propagating through COALESCE gaps)
> - Empty strings masquerading as populated data (bypasses NOT NULL constraints)
> - Corrupted loads where business-critical columns lost their values
>
> **Column selection rules:**
> 1. Always include NK columns that compose the SHA2 surrogate key (from DDL COMMENT)
> 2. For STRING NK columns: check BOTH `IS NULL` AND `TRIM(col) = ''`
> 3. For BIGINT/INT/DATE NK columns: check `IS NULL` only (no empty-string concept)
> 4. Optionally include critical NOT NULL business attrs (e.g., Abl_Pn, Transaction_Type)
> 5. If no exposed NK column exists (source PK not surfaced), check critical business attrs
>
> **Threshold logic:**
> - NK columns NULL → immediate FAIL (0% tolerance)
> - Critical business attr NULL/empty → WARN if ≤ 0.01%, FAIL if > 0.01%
>
> **Exclude Unknown member:** Always add `WHERE {Entity}_Key != -1` to exclude the
> synthetic Unknown row (which legitimately has placeholder values).

```sql
-- COMMAND ----------
-- Business Key null/dropped data check
-- NK columns: {list from DDL COMMENT "SHA2 of ..."}
-- Critical NOT NULL business columns: {list additional NOT NULL STRING columns}
SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
  -- Per-column breakdown (one line per NK/critical column):
  SUM(CASE WHEN {NK_Col_1} IS NULL OR TRIM({NK_Col_1}) = '' THEN 1 ELSE 0 END) AS {NK_Col_1}_Dropped,
  SUM(CASE WHEN {NK_Col_2} IS NULL THEN 1 ELSE 0 END) AS {NK_Col_2}_Null,
  -- Aggregate: any NK/critical column null or empty
  SUM(CASE WHEN {NK_Col_1} IS NULL OR TRIM({NK_Col_1}) = ''
           OR {NK_Col_2} IS NULL THEN 1 ELSE 0 END) AS BK_Dropped_Total,
  ROUND(100.0 * SUM(CASE WHEN {NK_Col_1} IS NULL OR TRIM({NK_Col_1}) = ''
           OR {NK_Col_2} IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4) AS BK_Dropped_Pct,
  CASE
    -- NK null = hard FAIL (these compose the surrogate key)
    WHEN SUM(CASE WHEN {NK_Col_2} IS NULL THEN 1 ELSE 0 END) > 0 THEN 'FAIL'
    -- Critical attrs null/empty = PASS if 0, WARN if ≤ 0.01%, FAIL otherwise
    WHEN SUM(CASE WHEN {NK_Col_1} IS NULL OR TRIM({NK_Col_1}) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS'
    WHEN ROUND(100.0 * SUM(CASE WHEN {NK_Col_1} IS NULL OR TRIM({NK_Col_1}) = '' THEN 1 ELSE 0 END) / COUNT(*), 4) <= 0.01 THEN 'WARN'
    ELSE 'FAIL'
  END AS Status
FROM {table_name}
WHERE {Entity}_Key != -1  -- Exclude Unknown member
```

#### Write Results CTE Pattern for BK Check

In the Write Results cell, add a `bk_null` CTE and UNION ALL row:

```sql
-- Add to the CTE list:
bk_null AS (SELECT
  SUM(CASE WHEN {all_null_conditions} THEN 1 ELSE 0 END) AS dropped_cnt,
  ROUND(100.0 * SUM(CASE WHEN {all_null_conditions} THEN 1 ELSE 0 END) / COUNT(*), 4) AS dropped_pct
  FROM {table_name} WHERE {Entity}_Key != -1)

-- Add as final UNION ALL:
UNION ALL
SELECT 'PENDING', '{table_name}', 'BK_Null_Check', 'BK',
  CASE WHEN dropped_cnt = 0 THEN 'PASS' WHEN dropped_pct <= 0.01 THEN 'WARN' ELSE 'FAIL' END,
  '0', CAST(dropped_cnt AS STRING), NULL, FALSE, NULL,
  'BK null/dropped check: {col1}, {col2}, ...', current_timestamp() FROM bk_null
```

#### Alternative: Inline SELECT (No CTE)

For notebooks using inline SELECT in UNION ALL (no CTE), use this simpler pattern:

```sql
UNION ALL
SELECT 'PENDING', '{table_name}', 'BK_Null_Check', 'BK',
  CASE WHEN SUM(CASE WHEN {all_null_conditions} THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
  '0', CAST(SUM(CASE WHEN {all_null_conditions} THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
  'BK null/dropped check: {col_list}', current_timestamp()
FROM {table_name} WHERE {Entity}_Key != -1
```

#### Business Key Mapping Reference (Manufacturing V2)

| Table | NK Columns (compose SHA2 surrogate) | Critical Attrs |
| --- | --- | --- |
| dim_plant | Plant_Code | Plant_Name |
| dim_focus_factory | Focus_Factory_Name + Plant_Key | — |
| dim_work_center | Work_Center_Code + Plant_Key | — |
| dim_shift | Shift_Name | Shift_Type |
| dim_routing | Abl_Pn + Routing_Revision + Plant_Key | — |
| dim_kanban_card | Kanban_Card_Nbr + Plant_Key | — |
| dim_routing_operation | Routing_Key + Operation_Seq | — |
| dim_manufacturing_bom_header | Abl_Pn + Bom_Revision + Plant_Key | — |
| dim_manufacturing_bom_line | Manufacturing_Bom_Header_Key + Line_Nbr | Component_Abl_Pn |
| fact_wip_job | Wip_Entity_Name + Plant_Key | — |
| fact_production_lot | Lot_Nbr | Abl_Pn |
| fact_wip_completion | (no exposed NK) | Abl_Pn, Completion_Qty, Transaction_Dttm |
| fact_wip_material_transaction | Transaction_Id | Abl_Pn, Transaction_Type_Name |
| fact_wip_move_transaction | Transaction_Id | Transaction_Type |
| fact_production_schedule | Demand_Id + Schedule_Date + Plant_Key | Abl_Pn |
| fact_oee_record | Plant_Key + Work_Center_Key + Shift_Date + Shift_Nbr | — |

---

### Cell 5: Key Column Population (POPULATION)

*Rule 27 slot (5). Check_Type = 'POP'. Threshold from `build_manifest.md` §7.*

```sql
-- COMMAND ----------
-- Column population rates for NOT NULL and key business columns
SELECT
  Column_Name,
  Total_Rows,
  Non_Null_Count,
  ROUND(100.0 * Non_Null_Count / Total_Rows, 2) AS Population_Pct,
  CASE WHEN ROUND(100.0 * Non_Null_Count / Total_Rows, 2) >= 95.0 THEN 'PASS' ELSE 'WARN' END AS Status
FROM (
  SELECT COUNT(*) AS Total_Rows,
    -- Repeat for each key column:
    COUNT({Column_1}) AS {Column_1}_nn,
    COUNT({Column_2}) AS {Column_2}_nn
    -- ...
  FROM {table_name}
)
UNPIVOT (
  Non_Null_Count FOR Column_Name IN ({Column_1}_nn AS {Column_1}, {Column_2}_nn AS {Column_2})
)
```

*(UNPIVOT aliases are unquoted identifiers — quoted-string aliases fail in Job context. See
`phase-protocol.md` "Critical Databricks SQL Pitfalls" #3.)*

### Cell 5b (optional): Business Rule Validation

*Not one of the ten mandatory cells — include only when the entity has an entity-specific
invariant. Check_Type = 'BUSINESS_RULE'. Place adjacent to Cell 5.*

```sql
-- COMMAND ----------
-- Business rules specific to this entity
-- Rule 1: {description}
SELECT
  '{rule_name}' AS Check_Name,
  COUNT(*) AS Violations,
  CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
FROM {table_name}
WHERE {violation_condition}
-- e.g., WHERE Is_Active_Flag IS NULL
-- e.g., WHERE Created_Dttm > Last_Updated_Dttm
```

### Cell 7: Data Drift Detection (DRIFT)

*Rule 27 slot (7) — slot (6) INTEGRATION is fact-only, so a dim jumps from 5 to 7.
Check_Type = 'DRIFT'. On the first run the cell writes the baseline and reports DRIFT=BASELINE
(baseline seeded from `build_manifest.md` §6 row counts); subsequent runs compare.*

> **Aggregate isolation — mandatory pattern for all Drift Check SQL.** The most common generated-SQL failure in drift checks is mixing a `COUNT(*)` aggregate with non-aggregated columns from a `JOIN` in the same `SELECT`, which raises `MISSING_GROUP_BY (SQLSTATE 42803)`. Compute the aggregate in a subquery first, then join:
>
> ```sql
> -- ❌ BROKEN: COUNT(*) is aggregate, b.* columns are not → MISSING_GROUP_BY (SQLSTATE 42803)
> SELECT 'quotation' AS table_name, CAST(COUNT(*) AS STRING) AS current_value,
>        b.Baseline_Value, b.Tolerance_Pct, CASE ... END AS drift_status
> FROM quotation LEFT JOIN _data_drift_baseline b ON ...;
>
> -- ✅ CORRECT: aggregate isolated in a subquery; outer SELECT has no bare aggregates
> SELECT 'quotation' AS table_name, CAST(c.cnt AS STRING) AS current_value,
>        b.Baseline_Value, b.Tolerance_Pct, CASE ... END AS drift_status
> FROM (SELECT COUNT(*) AS cnt FROM quotation) c
> LEFT JOIN _data_drift_baseline b ON ...;
> ```
>
> This applies to BOTH the exploratory Drift Check cell and the Write Results cell — use identical column aliases (`table_name`, `current_value`) across all notebooks so a scan can compare them.

```sql
-- COMMAND ----------
-- Drift detection: compare current stats to baseline
WITH current_stats AS (
  SELECT
    '{table_name}' AS Table_Name,
    COUNT(*) AS current_row_count,
    -- Per-column metrics:
    ROUND(100.0 * (1 - COUNT({Col_1}) / COUNT(*)), 4) AS {Col_1}_null_rate,
    COUNT(DISTINCT {Col_2}) AS {Col_2}_distinct_count
    -- ...
  FROM {table_name}
),
baseline AS (
  SELECT Column_Name, Metric_Type, CAST(Baseline_Value AS DECIMAL(20,4)) AS Baseline_Value, Tolerance_Pct
  FROM _data_drift_baseline
  WHERE Table_Name = '{table_name}' AND Is_Active = TRUE
)
SELECT
  b.Column_Name,
  b.Metric_Type,
  b.Baseline_Value,
  c.current_value,
  b.Tolerance_Pct,
  ROUND(ABS(c.current_value - b.Baseline_Value) / NULLIF(b.Baseline_Value, 0) * 100, 2) AS Drift_Pct,
  CASE
    WHEN ABS(c.current_value - b.Baseline_Value) / NULLIF(b.Baseline_Value, 0) * 100 > b.Tolerance_Pct THEN 'DRIFT_ALERT'
    ELSE 'WITHIN_TOLERANCE'
  END AS Drift_Status
FROM baseline b
JOIN (...) c  -- unpivoted current_stats
  ON b.Column_Name = c.Column_Name AND b.Metric_Type = c.Metric_Type
WHERE Drift_Status = 'DRIFT_ALERT'
```

### Cell 8: Data Profile — Shape & Coverage

> **Purpose:** Give developers immediate quantitative understanding of the table's scope,
> coverage, and key business characteristics — answering "what is this table really?"
> without requiring them to write exploratory queries.

**Design principles:**
* Always include: `Total_Rows`, `Last_Load`, key dimension cardinalities
* Tailor to entity type (see patterns below)
* Include measure distributions for facts (min/avg/max, edge-case counts)
* Show data freshness (hours since load, date span)

#### Dimension Profile Pattern

```sql
-- COMMAND ----------
-- Data profile: understand the scope and health of this dimension
SELECT
  COUNT(*) AS Total_Rows,
  SUM(CASE WHEN Is_Active_Flag = TRUE THEN 1 ELSE 0 END) AS Active_Rows,
  SUM(CASE WHEN Is_Active_Flag = FALSE THEN 1 ELSE 0 END) AS Inactive_Rows,
  -- Hierarchy/FK coverage
  COUNT(DISTINCT {parent_fk_col}) AS Distinct_{Parent}s,
  -- Key column population gaps
  COUNT({important_col}) AS Has_{Important_Col},
  COUNT(*) - COUNT({important_col}) AS Missing_{Important_Col},
  MAX(_loaded_at) AS Last_Load
FROM {table_name}
WHERE {Entity}_Key != -1
```

**For compact dimensions (≤ 50 rows):** Consider showing ALL rows in the Sample cell.

#### Fact Profile Pattern

```sql
-- COMMAND ----------
-- Data profile: understand transaction volume and time span
SELECT
  COUNT(*) AS Total_Rows,
  COUNT(DISTINCT Plant_Key) AS Distinct_Plants,
  COUNT(DISTINCT {business_col}) AS Distinct_{Business_Entity},
  -- Date range and freshness
  MIN({date_col}) AS Earliest_Date,
  MAX({date_col}) AS Latest_Date,
  DATEDIFF(MAX({date_col}), MIN({date_col})) AS Date_Span_Days,
  -- Measure distributions (include edge cases that explain design annotations)
  ROUND(AVG({measure}), 2) AS Avg_{Measure},
  ROUND(MIN({measure}), 2) AS Min_{Measure},
  ROUND(MAX({measure}), 2) AS Max_{Measure},
  SUM(CASE WHEN {measure} < 0 THEN 1 ELSE 0 END) AS Negative_{Measure}_Rows,
  MAX(_loaded_at) AS Last_Load
FROM {table_name}
WHERE {Entity}_Key != -1
```

**Table-specific additions:**
* If the narrative has a Design Annotation (e.g., unbounded values), add columns
  that quantify the edge case (e.g., `SUM(CASE WHEN Oee_Pct > 100 ...)`)
* If there's a Known Gap, add columns that quantify its impact

### Cell 9: Sample Rows — Representative Records

> **Purpose:** Show developers what actual data looks like — not just schema, but real values.
> A curated sample is more useful than `SELECT * LIMIT 5` because it shows both typical
> records AND edge cases that explain design decisions.

**Design principles:**
* Always exclude Unknown member (`WHERE {Entity}_Key != -1`)
* Select meaningful columns (not all 20+ columns; omit audit cols like `_loaded_at`)
* Include edge cases when they exist (negative values, outliers, special statuses)
* For compact dimensions (≤ 50 rows): show all rows
* For large tables: use UNION ALL to combine typical + edge-case samples

#### Dimension Sample Pattern

```sql
-- COMMAND ----------
-- Representative sample: {context of what this shows}
SELECT {key_cols}, {business_cols}, Is_Active_Flag
FROM {table_name}
WHERE {Entity}_Key != -1
ORDER BY {meaningful_order}  -- e.g., _loaded_at DESC, or alphabetical for reference data
LIMIT 10
```

#### Fact Sample Pattern (with edge cases)

```sql
-- COMMAND ----------
-- Representative sample: recent records + edge cases
(
  SELECT {key_cols}, {measure_cols}, {date_col}
  FROM {table_name}
  WHERE {Entity}_Key != -1 AND {typical_filter}
  ORDER BY {date_col} DESC LIMIT 7
)
UNION ALL
(
  -- Edge cases: {describe what makes them special}
  SELECT {key_cols}, {measure_cols}, {date_col}
  FROM {table_name}
  WHERE {Entity}_Key != -1 AND {edge_case_filter}
  ORDER BY {measure} ASC LIMIT 3
)
```

**When to show edge cases:**
* Negative quantities (completions, returns, corrections)
* Values outside expected bounds (OEE > 100%, negative costs)
* Records with special statuses (On Hold, Expired, Cancelled)
* Synthetic/DFF-specific records (DFF_LABOR transaction types)

### Cell 10: Write Results to Metadata (PENDING→Claim)

Tag every check row with the literal `'PENDING'` — no temp views, no `_current_run`. The cell
DELETEs its own stale PENDING rows first (safe re-run guard), then INSERTs. The scorecard
claims all PENDING rows when it runs last. See `validation-schema.md` Pattern 1 and SKILL.md
Rules 15/16.

```sql
-- COMMAND ----------
-- Write validation results to metadata tables (PENDING→claim — see validation-schema.md)
DELETE FROM _validation_check_detail
WHERE Run_Id = 'PENDING' AND Table_Name = '{table_name}';

INSERT INTO _validation_check_detail
SELECT 'PENDING', '{table_name}', 'PK_Uniqueness', 'PK', ...
UNION ALL
SELECT 'PENDING', '{table_name}', 'FK_{Parent}_Key', 'FK', ...       -- one row per FK
UNION ALL
SELECT 'PENDING', '{table_name}', 'BK_Null_Check', 'BK', ...
UNION ALL
SELECT 'PENDING', '{table_name}', 'Population_{col}', 'POP', ...
UNION ALL
SELECT 'PENDING', '{table_name}', 'Drift_{col}_{metric}', 'DRIFT', ...;
```

---

## Cell Structure — Fact Variant (Additional Cells)

Fact notebooks include ALL dimension cells above PLUS the star-schema **INTEGRATION** cells,
which occupy **Rule 27 slot (6)** — between Cell 5 (POPULATION) and Cell 7 (DRIFT). A fact's
cell order is therefore: 1 (narrative), 2 (row count/PK), 3 (FK), 4 (BK), 5 (POPULATION),
**6a–6d (INTEGRATION)**, 7 (DRIFT), 8 (Data Profile), 9 (Sample Rows), 10 (Write Results). All
integration cells write Check_Type = 'INTEGRATION' and are wired into the Cell 10 Write Results
INSERT as their own UNION ALL rows (SKILL.md Rule 24 — a fact without INTEGRATION rows is
incomplete). FK-resolution joins here use the `build_manifest.md` §3 attribute, same as Cell 3.

> **SDP mode (`etl_type: sdp_pipeline`) — INTEGRATION semantics.** There are no runner/transform
> notebooks and no job-run-id to reference; entities are materialized views or streaming tables in
> a Lakeflow pipeline. The INTEGRATION cells validate the **materialized output**, not a re-run:
> - **Materialized View facts** — keep 6a (join preservation / no fan-out) and 6b–6d (cross-fact
>   consistency) exactly as below; they run against the already-materialized MV. Do NOT try to
>   "execute the transform" — the MV is the artifact.
> - **Streaming Table entities** — add a watermark/dedup check instead of a runner check: assert one
>   row per natural key (no duplicate late-arriving events survived dedup) and that the max
>   `SEQUENCE BY` / watermark column has advanced past the drift baseline's timestamp.
> - **Integration test reference** — cite the **pipeline update id** (from the pipeline event log)
>   in the run metadata where the batch path would cite a job run id.
> The check *taxonomy* (PK/BK/FK/POP/INTEGRATION/DRIFT) is unchanged — only the "what does INTEGRATION
> prove" wording differs. See `etl-development-framework/sdp-pipeline-development.md` for the SDP object model.

### Cell 6a: Star Schema Join Preservation

```sql
-- COMMAND ----------
-- %md
-- ## Star Schema Integration
--
-- This fact joins to the following dimensions:
-- {list all dims with FK column name and business meaning}
--
-- The checks below verify that joining does not alter grain (no fan-out)
-- and that cross-fact references are consistent.

-- COMMAND ----------
-- Join preservation: fact row count should be unchanged after LEFT JOIN to all dims
WITH base_count AS (
  SELECT COUNT(*) AS fact_rows FROM {fact_table}
),
joined_count AS (
  SELECT COUNT(*) AS joined_rows
  FROM {fact_table} f
  LEFT JOIN {dim_1} d1 ON f.{Dim1}_Key = d1.{Dim1}_Key
  LEFT JOIN {dim_2} d2 ON f.{Dim2}_Key = d2.{Dim2}_Key
  -- ... all dims
)
SELECT
  'Join_Preservation' AS Check_Name,
  b.fact_rows,
  j.joined_rows,
  j.joined_rows - b.fact_rows AS Fan_Out_Rows,
  CASE WHEN j.joined_rows = b.fact_rows THEN 'PASS' ELSE 'FAIL' END AS Status
FROM base_count b, joined_count j
```

### Cell 6b: Fan-Out Detection (Per Dimension)

```sql
-- COMMAND ----------
-- Per-dimension fan-out check
SELECT
  Dimension_Name,
  Fact_Rows,
  Joined_Rows,
  Joined_Rows - Fact_Rows AS Fan_Out,
  CASE WHEN Joined_Rows = Fact_Rows THEN 'PASS' ELSE 'FAIL' END AS Status
FROM (
  SELECT '{dim_1}' AS Dimension_Name,
    (SELECT COUNT(*) FROM {fact_table}) AS Fact_Rows,
    (SELECT COUNT(*) FROM {fact_table} f
     LEFT JOIN {dim_1} d ON f.{Dim1}_Key = d.{Dim1}_Key) AS Joined_Rows
  UNION ALL
  SELECT '{dim_2}',
    (SELECT COUNT(*) FROM {fact_table}),
    (SELECT COUNT(*) FROM {fact_table} f
     LEFT JOIN {dim_2} d ON f.{Dim2}_Key = d.{Dim2}_Key)
  -- ... repeat for all dims
)
```

### Cell 6c: Cross-Fact Consistency (where applicable)

```sql
-- COMMAND ----------
-- Cross-fact consistency: FK values in this fact should exist in related facts
-- Example: Wip_Job_Key values in fact_production_lot should exist in fact_wip_job
SELECT
  '{fact_table} -> {related_fact}' AS Check_Name,
  COUNT(DISTINCT f.{Shared_Key}) AS Keys_In_This_Fact,
  COUNT(DISTINCT r.{Shared_Key}) AS Keys_In_Related_Fact,
  COUNT(DISTINCT f.{Shared_Key}) - COUNT(DISTINCT CASE WHEN r.{Shared_Key} IS NOT NULL THEN f.{Shared_Key} END) AS Missing_In_Related,
  CASE
    WHEN COUNT(DISTINCT f.{Shared_Key}) = COUNT(DISTINCT CASE WHEN r.{Shared_Key} IS NOT NULL THEN f.{Shared_Key} END) THEN 'PASS'
    ELSE 'WARN'  -- WARN not FAIL: facts may have different filtering
  END AS Status
FROM {fact_table} f
LEFT JOIN {related_fact} r
  ON f.{Shared_Key} = r.{Shared_Key}
WHERE f.{Shared_Key} != -1
```

### Cell 6d: Metric Sanity Check

```sql
-- COMMAND ----------
-- Metric sanity: aggregate a known measure and verify reasonableness
SELECT
  'Metric_Sanity_{measure}' AS Check_Name,
  COUNT(*) AS Row_Count,
  ROUND(AVG({measure_column}), 4) AS Avg_Value,
  MIN({measure_column}) AS Min_Value,
  MAX({measure_column}) AS Max_Value,
  ROUND(STDDEV({measure_column}), 4) AS StdDev_Value,
  -- Sanity bounds (from S2T mapping or business knowledge)
  CASE
    WHEN AVG({measure_column}) BETWEEN {expected_min} AND {expected_max} THEN 'PASS'
    ELSE 'WARN'
  END AS Status
FROM {fact_table}
WHERE {measure_column} IS NOT NULL
```

---

## "Why Is It This Way?" Annotation Pattern

For every non-obvious design decision, include a markdown annotation cell:

```sql
-- COMMAND ----------
-- %md
-- ### ⚠️ Design Annotation: {short title}
--
-- **What:** {description of the unusual pattern}
-- **Why:** {root cause from progress.md or S2T mapping}
-- **Impact:** {what happens if this is "fixed" without understanding}
-- **Source:** {reference document, e.g., "progress.md — Constraint Fixes"}
--
-- Example:
-- **What:** `Lot_Qty` has no CHECK constraint (allows negative values)
-- **Why:** ABL has legitimate negative quantity adjustments for inventory corrections
-- **Impact:** Adding `Lot_Qty >= 0` would reject ~2% of valid production records
-- **Source:** progress.md — Constraint Fixes, fact_production_lot
```

Place annotation cells immediately BEFORE the assertion that relates to the documented behavior.

---

## Accepted Exception Pattern

When a check is known to "fail" by design (documented in progress.md):

```sql
-- FK integrity: dim_manufacturing_bom_header -> dim_plant
-- ACCEPTED EXCEPTION: 8 Oracle orgs (335K BOM headers) reference plants not in DFF dim_plant.
-- Threshold set to 10% (actual ~8%) to accommodate known cross-system gap.
-- Source: progress.md "Human Review Needed"
SELECT
  'FK_Plant_Key' AS Check_Name,
  ...
  CASE
    WHEN orphan_pct <= 10.0 THEN 'PASS'  -- Relaxed threshold
    ELSE 'FAIL'
  END AS Status,
  TRUE AS Is_Accepted_Exception  -- Flagged for metadata
FROM ...
```

---

## Scorecard Notebook Structure (`scorecard.sql`)

The scorecard runs LAST (depends on all entity notebooks) and:

1. **Claims** PENDING check rows into one `run_id` (validation-schema.md Pattern 2)
2. **Computes** per-entity grades — including real `Row_Count_Delta` / `Grade_Delta` vs the
   previous run (SKILL.md Rule 28; `regression-and-drift.md` Pattern 1). Never stub the deltas.
3. **Computes** overall run grade (writes to `_validation_run` LAST, so Pattern 3 deltas find
   the prior run as the latest existing row by `Run_Timestamp` — never `MAX(Run_Id)`, which is
   random on a `uuid()` string)
4. **Displays** summary table:

```sql
-- COMMAND ----------
-- Validation Scorecard
SELECT
  Table_Name,
  Table_Type,
  Tier,
  Row_Count,
  Grade,
  Grade_Delta,
  Pk_Duplicate_Count,
  Fk_Orphan_Rate_Pct,
  Key_Column_Pop_Pct,
  Drift_Columns_Count,
  Integration_Pass,
  Remediation_Status
FROM _validation_table_result
WHERE Run_Id = session.run_id  -- scorecard's claimed run_id (validation-schema.md Pattern 2)
ORDER BY Tier, Table_Name
```

5. **Fails the job** if any entity is Grade D or F:

```sql
-- COMMAND ----------
-- Fail gate: raise error if any critical failures
SELECT
  CASE
    WHEN COUNT(*) > 0 THEN
      RAISE_ERROR('VALIDATION FAILED: ' || COUNT(*) || ' entities at Grade D or F. See _validation_table_result for details.')
    ELSE 'ALL ENTITIES PASSING'
  END AS Gate_Result
FROM _validation_table_result
WHERE Run_Id = session.run_id  -- scorecard's claimed run_id (validation-schema.md Pattern 2)
AND Grade IN ('D', 'F')
```

---

## Naming Convention

| Entity Type | Notebook Name | Example |
| --- | --- | --- |
| Dimension | `narrative_dim_{entity}` | `narrative_dim_focus_factory` |
| Fact | `narrative_fact_{name}` | `narrative_fact_wip_job` |
| Scorecard | `scorecard` | `scorecard` |
| DDL | `ddl_validation_schema` | `ddl_validation_schema` |

Notebook format follows `etl_language` (see the note at the top of this file and the
"Notebook-format contract"). Default `sql`: native SQL notebooks — `-- Databricks notebook
source`, `-- COMMAND ----------` separators, `-- %md` markdown, no per-cell `%sql`. `python`:
`# Databricks notebook source`, `# COMMAND ----------`, `# MAGIC %sql`/`%md` cells.
