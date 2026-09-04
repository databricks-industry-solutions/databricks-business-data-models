# Validation Schema — Metadata Tables

## Overview

The validation skill writes results to 5 metadata tables that live as sub-tables
within the same schema as the model (e.g., `{silver_schema}._validation_run`).

Naming convention: `_validation_*` prefix with leading underscore (system/metadata
convention from ETL naming standards). Columns use `Pascal_Snake_Case` for business
columns and `_lower_snake` for system columns.

---

## Runtime Parameters (validation notebooks promote dev→prod unchanged)

Validation notebooks run as `notebook_task`s in the validation job and touch exactly one
schema (the model schema). They use the **same runtime-param header as the ETL notebooks**
(`etl-development-framework/deployment-and-dab.md` "Runtime Parameters") — catalog/schema are
NEVER baked literals:

*(First line follows `etl_language` — `-- Databricks notebook source` for SQL, `# Databricks
notebook source` for Python; see "Notebook-format contract".)*

```sql
-- Databricks notebook source
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';

-- COMMAND ----------
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);

-- COMMAND ----------
```

After the header, every model table and `_validation_*`/`_gap_registry` table is referenced
**UNQUALIFIED** (session context resolves them). The validation job's tasks pass
`silver_catalog`/`silver_schema` via `base_parameters` wired to the same DAB variables as the
ETL job. The SQL templates below drop the `{silver_catalog}.{silver_schema}.` prefix for this
reason. (**Dashboards** are the exception — Lakeview datasets get catalog/schema from
dashboard-level parameters at deploy time, not widgets; see `dashboard-spec.md`.)

---

## Table 1: `_validation_run`

**Grain:** One row per validation execution (full suite run).

```sql
CREATE TABLE IF NOT EXISTS _validation_run (
  Run_Id                   STRING       NOT NULL  COMMENT 'UUID for this validation run',
  Run_Timestamp            TIMESTAMP    NOT NULL  COMMENT 'UTC start time of the validation run',
  Project_Name             STRING       NOT NULL  COMMENT 'Project identifier (e.g., meridian_sales_order)',
  Schema_Name              STRING       NOT NULL  COMMENT 'Target schema being validated',
  Triggered_By             STRING       NOT NULL  COMMENT 'How this run was triggered: SCHEDULED | MANUAL | PRE_DEPLOY | POST_FIX',
  Total_Entities           INT          NOT NULL  COMMENT 'Number of entities validated in this run',
  Entities_Grade_A         INT          NOT NULL  COMMENT 'Count of entities achieving Grade A',
  Entities_Grade_B_Plus    INT          NOT NULL  COMMENT 'Count of entities at Grade B+',
  Entities_Grade_B         INT          NOT NULL  COMMENT 'Count of entities at Grade B',
  Entities_Grade_C_Or_Below INT         NOT NULL  COMMENT 'Count of entities at Grade C or worse',
  Overall_Grade            STRING       NOT NULL  COMMENT 'Worst grade across all entities (determines run health)',
  Drift_Alerts_Count       INT          NOT NULL  COMMENT 'Number of columns with drift exceeding tolerance',
  Run_Duration_Seconds     INT                    COMMENT 'Wall-clock duration of the full validation suite',
  _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
  CONSTRAINT pk_validation_run PRIMARY KEY (Run_Id)
)
USING DELTA
CLUSTER BY (Run_Timestamp)
COMMENT 'Validation metadata. One row per validation suite execution. Tracks overall health over time.';
```

---

## Table 2: `_validation_table_result`

**Grain:** One row per entity per validation run.

```sql
CREATE TABLE IF NOT EXISTS _validation_table_result (
  Run_Id                   STRING       NOT NULL  COMMENT 'FK to _validation_run',
  Table_Name               STRING       NOT NULL  COMMENT 'Entity name (e.g., dim_focus_factory)',
  Table_Type               STRING       NOT NULL  COMMENT 'DIMENSION | FACT',
  Tier                     INT          NOT NULL  COMMENT 'Load order tier (0 = root dims, 4 = leaf facts)',
  Row_Count                BIGINT       NOT NULL  COMMENT 'Current row count at validation time',
  Row_Count_Delta          BIGINT                 COMMENT 'Change from previous run (NULL on first run)',
  Pk_Duplicate_Count       BIGINT       NOT NULL  COMMENT 'Number of duplicate PK values (0 = clean)',
  Fk_Orphan_Rate_Pct       DECIMAL(7,4)           COMMENT 'Worst FK orphan rate across all FKs (NULL for root dims)',
  Key_Column_Pop_Pct       DECIMAL(7,4) NOT NULL  COMMENT 'Lowest population % across key (NOT NULL) columns',
  Freshness_Hours          DECIMAL(10,2)          COMMENT 'Hours since most recent _loaded_at (NULL if no metadata col)',
  Drift_Columns_Count      INT          NOT NULL  COMMENT 'Number of columns with drift exceeding tolerance',
  Integration_Pass         BOOLEAN                COMMENT 'TRUE if all star schema integration checks pass (facts only)',
  Grade                    STRING       NOT NULL  COMMENT 'Computed grade: A | B+ | B | C | D | F',
  Grade_Delta              STRING                 COMMENT 'Change from previous run: IMPROVED | STABLE | DEGRADED | NEW',
  Known_Gaps_Count         INT          NOT NULL  COMMENT 'Number of documented known gaps for this entity',
  Accepted_Exceptions      INT          NOT NULL  COMMENT 'Number of checks excluded due to documented exceptions',
  Remediation_Status       STRING                 COMMENT 'NULL | DETECTED | TRIAGED | ESCALATED_TO_ETL | RESOLVED',
  _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
  CONSTRAINT pk_validation_table_result PRIMARY KEY (Run_Id, Table_Name)
)
USING DELTA
CLUSTER BY (Table_Name, Run_Id)
COMMENT 'Validation metadata. One row per entity per run. Core table for dashboard grading and trend analysis.';
```

---

## Table 3: `_validation_check_detail`

**Grain:** One row per individual check per entity per run.

```sql
CREATE TABLE IF NOT EXISTS _validation_check_detail (
  Run_Id                   STRING       NOT NULL  COMMENT 'FK to _validation_run',
  Table_Name               STRING       NOT NULL  COMMENT 'Entity being checked',
  Check_Name               STRING       NOT NULL  COMMENT 'Human-readable check name (e.g., PK_Uniqueness, FK_Plant_Key, Drift_Cost_Center_Null_Rate)',
  Check_Type               STRING       NOT NULL  COMMENT 'Category: PK | FK | POPULATION | BUSINESS_RULE | DRIFT | INTEGRATION | FRESHNESS',
  Status                   STRING       NOT NULL  COMMENT 'Result: PASS | FAIL | WARN | SKIP',
  Threshold_Value          STRING                 COMMENT 'Expected threshold (e.g., 0 for PK dups, 1.0 for FK orphan %)',
  Actual_Value             STRING                 COMMENT 'Measured value (e.g., 0 dups, 0.3% orphans)',
  Deviation_Pct            DECIMAL(10,4)          COMMENT 'How far actual is from threshold (negative = better than threshold)',
  Is_Accepted_Exception    BOOLEAN      NOT NULL  COMMENT 'TRUE if this check is excluded from grading due to documented exception',
  Exception_Reason         STRING                 COMMENT 'Why this check is accepted as exception (from progress.md or S2T mapping)',
  Message                  STRING                 COMMENT 'Human-readable result description',
  _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
  CONSTRAINT pk_validation_check_detail PRIMARY KEY (Run_Id, Table_Name, Check_Name)
)
USING DELTA
CLUSTER BY (Table_Name, Check_Type)
COMMENT 'Validation metadata. One row per check per entity per run. Detailed drill-down for failures and trends.';
```

---

## Table 4: `_data_drift_baseline`

**Grain:** One row per column per metric type. Set on first run, frozen until manual reset.

```sql
CREATE TABLE IF NOT EXISTS _data_drift_baseline (
  Table_Name               STRING       NOT NULL  COMMENT 'Entity this baseline applies to',
  Column_Name              STRING       NOT NULL  COMMENT 'Column being monitored',
  Metric_Type              STRING       NOT NULL  COMMENT 'What is measured: NULL_RATE | DISTINCT_COUNT | MIN_VALUE | MAX_VALUE | MEAN_VALUE | ROW_COUNT',
  Baseline_Value           STRING       NOT NULL  COMMENT 'Baseline measurement (stored as string for flexibility across metric types)',
  Tolerance_Pct            DECIMAL(7,4) NOT NULL  COMMENT 'Allowed deviation from baseline before alerting (e.g., 10.0 = 10%)',
  Tolerance_Direction      STRING       NOT NULL  COMMENT 'Which direction triggers alert: INCREASE | DECREASE | BOTH',
  Baseline_Set_Date        TIMESTAMP    NOT NULL  COMMENT 'When this baseline was established',
  Baseline_Run_Id          STRING       NOT NULL  COMMENT 'Run_Id that set this baseline',
  Last_Reset_Date          TIMESTAMP              COMMENT 'If manually reset, when (NULL = original baseline)',
  Reset_Reason             STRING                 COMMENT 'Why baseline was reset (e.g., intentional schema change)',
  Is_Active                BOOLEAN      NOT NULL  COMMENT 'FALSE to disable monitoring for this column without deleting history',
  _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
  CONSTRAINT pk_data_drift_baseline PRIMARY KEY (Table_Name, Column_Name, Metric_Type)
)
USING DELTA
CLUSTER BY (Table_Name)
COMMENT 'Validation metadata. Drift detection baselines — set on first run, frozen until manually reset. Columns exceeding tolerance trigger WARN/FAIL.';
```

### Baseline Metrics to Capture

For each entity, capture baselines for:

| Column Category | Metrics | Tolerance Default |
| --- | --- | --- |
| PK column | DISTINCT_COUNT (= row count) | 20% INCREASE (growth is normal; shrinkage is alarming) |
| FK columns | NULL_RATE | 5% BOTH |
| String business columns | NULL_RATE, DISTINCT_COUNT | 10% BOTH |
| Numeric business columns | NULL_RATE, MIN_VALUE, MAX_VALUE, MEAN_VALUE | 15% BOTH |
| Timestamp columns | NULL_RATE, MIN_VALUE, MAX_VALUE | 10% BOTH |
| Boolean columns | NULL_RATE | 5% BOTH |
| Row count (table-level) | ROW_COUNT | 20% INCREASE, 5% DECREASE |

**Tolerance override from S2T mapping:** If the S2T mapping documents expected characteristics
(e.g., "10% of rows have NULL WIP_ENTITY_ID — these are purchase order LPNs"), set the
baseline NULL_RATE tolerance accordingly (e.g., 15% INCREASE to allow natural growth but
alert on sudden jumps).

---

## Table 5: `_gap_registry`

**Grain:** One row per known gap or data quality issue.

```sql
CREATE TABLE IF NOT EXISTS _gap_registry (
  Gap_Id                   STRING       NOT NULL  COMMENT 'UUID for this gap entry',
  Table_Name               STRING       NOT NULL  COMMENT 'Entity affected by this gap',
  Column_Name              STRING                 COMMENT 'Specific column affected (NULL for table-level gaps)',
  Gap_Description          STRING       NOT NULL  COMMENT 'Human-readable description of the gap',
  Gap_Type                 STRING       NOT NULL  COMMENT 'Category: MISSING_SOURCE | FK_ORPHAN | PARTIAL_COVERAGE | CONSTRAINT_RELAXED | SYNTHETIC_KEY | DEFERRED_ENRICHMENT | NULL_SOURCE',
  Priority                 STRING       NOT NULL  COMMENT 'Priority: P0 (blocks production) | P1 (significant) | P2 (minor) | P3 (nice-to-have)',
  Status                   STRING       NOT NULL  COMMENT 'Lifecycle: OPEN | ACCEPTED | IN_PROGRESS | RESOLVED | DEFERRED',
  Remediation_Status       STRING                 COMMENT 'ETL handoff: NULL | DETECTED | TRIAGED | ESCALATED_TO_ETL | RESOLVED',
  Unblock_Action           STRING                 COMMENT 'What needs to happen to close this gap',
  Source_Document          STRING                 COMMENT 'Where this gap was first documented (e.g., S2T mapping, progress.md)',
  Created_Date             DATE         NOT NULL  COMMENT 'When this gap was first recorded',
  Resolved_Date            DATE                   COMMENT 'When this gap was closed (NULL if still open)',
  Impact_Description       STRING                 COMMENT 'Business impact of this gap remaining open',
  Assigned_To              STRING                 COMMENT 'Person or team responsible for resolution',
  _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
  CONSTRAINT pk_gap_registry PRIMARY KEY (Gap_Id)
)
USING DELTA
CLUSTER BY (Priority, Status)
COMMENT 'Validation metadata. Registry of known gaps and data quality issues. Seeded from S2T mapping, updated by validation runs and remediation cycles.';
```

---

## Write Patterns (PENDING→Claim)

The suite is stateless and decoupled: **narrative notebooks write check_detail rows tagged
`Run_Id = 'PENDING'`** (literal string, no temp views, no session coupling), and the
**scorecard runs LAST — it generates one `run_id`, claims all PENDING rows, then computes the
per-entity and run-level results.** Never use `CREATE OR REPLACE TEMPORARY VIEW _current_run`
or `(SELECT Run_Id FROM _current_run)` — that couples notebooks to a shared session and breaks
the parallel job (see `phase-protocol.md` "Deployment Architecture: PENDING→Claim Pattern" and
SKILL.md Rules 15/16). All SQL below is the `sql` shape; under `etl_language: python` these are `# MAGIC %sql`
cells or `spark.sql("...")` calls with the identical statements.

### Pattern 1: Write Check Detail (per-table notebook, after each assertion)

Narrative notebooks tag every check row with the literal `'PENDING'`. The cell first DELETEs
its own stale PENDING rows (safe re-run guard), then INSERTs:

```sql
-- Write Results cell (narrative notebook). DELETE guard, then INSERT literal 'PENDING'.
DELETE FROM _validation_check_detail
WHERE Run_Id = 'PENDING' AND Table_Name = '{table_name}';

INSERT INTO _validation_check_detail
SELECT
  'PENDING',                               -- claimed by the scorecard's run_id later
  '{table_name}',
  '{check_name}',
  '{check_type}',
  CASE WHEN {actual_expr} {comparison} {threshold} THEN 'PASS' ELSE 'FAIL' END,
  '{threshold}',
  CAST({actual_expr} AS STRING),
  ROUND(({actual_expr} - {threshold_numeric}) / NULLIF({threshold_numeric}, 0) * 100, 4),
  {is_accepted_exception},
  {exception_reason_or_null},
  CASE
    WHEN {actual_expr} {comparison} {threshold} THEN '{check_name}: PASS ({actual_expr_label})'
    ELSE '{check_name}: FAIL — expected {comparison} {threshold}, got ' || CAST({actual_expr} AS STRING)
  END,
  current_timestamp();
```

### Pattern 2: Claim PENDING Rows (scorecard notebook, first cell)

The scorecard generates one run_id and claims every PENDING check row in a single UPDATE — no
temp view, no cross-notebook session state:

```sql
-- Scorecard cell 1: generate run context and claim all PENDING rows.
DECLARE OR REPLACE VARIABLE run_id STRING DEFAULT uuid();
DECLARE OR REPLACE VARIABLE run_ts TIMESTAMP DEFAULT current_timestamp();

UPDATE _validation_check_detail
SET Run_Id = session.run_id          -- session. prefix REQUIRED: bare `run_id` resolves to the
WHERE Run_Id = 'PENDING';            -- Run_Id COLUMN, silently claiming 0 rows (see below)
```

🔴 **Reference the variable as `session.run_id`, never bare `run_id`, in this UPDATE.** The target
table has a `Run_Id` column; a bare `run_id` is resolved to that **column** (case-insensitive), so
the buggy `SET Run_Id = run_id` sets the column to itself and claims **zero** PENDING rows — no
error, a silent no-op that yields an empty scorecard. This bit the gold-validation run. The
`session.run_id` form above disambiguates to the variable. (Belt-and-suspenders: declare it
`v_run_id` so no column can ever match, and reference `session.v_run_id`.) See `phase-protocol.md`
Critical Databricks SQL Pitfalls §6.

**Every example in this file and in `table-narrative-template.md` / `remediation-protocol.md`
already uses `session.run_id` in any statement that has a `Run_Id`-bearing table in scope — copy
them verbatim.** The collision is NOT limited to the claim UPDATE: a bare `run_id` in a
`WHERE Run_Id = run_id` predicate (Patterns 3 and 5 below, the fail-gate SELECT, the remediation
join) resolves to the column too, making the predicate `Run_Id = Run_Id` — **always true**, so a
`DELETE` wipes ALL history and a `COUNT`/grade subquery aggregates across every past run. Use
`session.run_id` in every predicate and DML target; the SELECT-list projections below also use
`session.run_id`/`session.run_ts` for consistency (a bare name there is harmless — no FROM clause —
but uniform usage removes the trap).

`run_id` / `run_ts` are session variables (`phase-protocol.md` "DECLARE VARIABLE Scope") available to
every subsequent scorecard cell — they replace the old `_current_run` temp view.

### Pattern 3: Write Table Result (scorecard notebook, per-entity grades)

The scorecard — not the per-table notebook — computes `_validation_table_result` from the
now-claimed check rows. Delete-before-insert makes retries idempotent (Pitfall 4):

```sql
DELETE FROM _validation_table_result WHERE Run_Id = session.run_id;

INSERT INTO _validation_table_result
SELECT
  session.run_id,
  '{table_name}',
  '{table_type}',  -- DIMENSION | FACT
  {tier},
  (SELECT COUNT(*) FROM {table_name}),
  -- Row_Count_Delta vs the immediately previous run (NULL only on the genuine first run).
  -- Run_Id is a uuid() STRING, so MAX(Run_Id) is meaningless for recency — order by
  -- Run_Timestamp. The current run's _validation_run row is written LAST (Pattern 5), so the
  -- latest existing row IS the previous run.
  (SELECT COUNT(*) FROM {table_name}) - (
    SELECT r.Row_Count FROM _validation_table_result r
    JOIN _validation_run v ON r.Run_Id = v.Run_Id
    WHERE r.Table_Name = '{table_name}'
    ORDER BY v.Run_Timestamp DESC
    LIMIT 1
  ),
  -- pk_dups: exclude accepted-exception rows (Is_Accepted_Exception = FALSE) so a documented,
  -- accepted PK gap does NOT force Grade F — this is the filter Pattern 4 assumes on ALL
  -- check_detail-derived metrics (Pitfall §5). Every metric below carries the same filter.
  (SELECT COALESCE(SUM(CASE WHEN Status = 'FAIL' AND Check_Type = 'PK' THEN 1 ELSE 0 END), 0)
   FROM _validation_check_detail
   WHERE Run_Id = session.run_id AND Table_Name = '{table_name}'
     AND Is_Accepted_Exception = FALSE),
  -- ... (FK orphan rate, key column pop, freshness, drift, integration, Grade, Grade_Delta —
  --      each check_detail-derived metric filters `AND Is_Accepted_Exception = FALSE` exactly as
  --      the PK subquery above; Grade_Delta computed against the previous run per regression-and-drift.md)
  current_timestamp();
```

### Pattern 4: Compute Grade (the authoritative grading algorithm)

This CASE is the **single source of truth** for the grade — the SKILL.md Grading Rubric table is
its human-readable view; they must stay in step. Note the two edge-case guards up front (they were
learned by failing): an **accepted-empty** entity is not auto-F'd for 0 rows, and the
`_validation_check_detail`-derived orphan metrics are computed **after excluding known-gap /
accepted-exception rows** (`Is_Accepted_Exception = TRUE`, Pitfall §5) so a documented gap never
forces the grade down.

```sql
-- Inputs already computed for the entity:
--   pk_dups, pk_uniqueness_pct, fk_orphan_pct, key_pop_pct
--     ^ the check_detail-derived metrics — computed AFTER excluding Is_Accepted_Exception = TRUE
--       rows (the exclusion applies to these ONLY; it is meaningless for the two below).
--   row_count     := SELECT COUNT(*) FROM {entity} — the entity's physical row count (NOT from
--                    check_detail; accepted-exception exclusion does not apply).
--   drift_count   := count of drift alerts for this entity (NOT from check_detail orphan rows).
--   accepted_empty:= TRUE for a documented declared-empty table (manifest §5); default FALSE.
--                    MUST be a strict boolean — COALESCE(..., FALSE) so it is never NULL
--                    (a NULL would make `NOT accepted_empty` UNKNOWN and skip the empty-table F).
CASE
  WHEN pk_dups > 0 THEN 'F'                                   -- PK violation is always F
  WHEN row_count = 0 AND accepted_empty IS NOT TRUE THEN 'F'  -- empty & not declared-empty → F
  WHEN fk_orphan_pct > 20 THEN 'F'
  WHEN fk_orphan_pct > 10 OR pk_uniqueness_pct < 97 THEN 'D'
  WHEN fk_orphan_pct > 5  OR key_pop_pct < 80 THEN 'C'
  WHEN fk_orphan_pct > 3  OR key_pop_pct < 90 THEN 'B'
  WHEN fk_orphan_pct > 1  OR key_pop_pct < 95 OR drift_count > 0 THEN 'B+'
  ELSE 'A'
END AS Grade
```

*A `row_count = 0` on a NON-declared-empty entity is Grade F even with no other failing check — an
empty table that was supposed to have data is the SDP silent-0-row failure surfacing downstream.*

### Pattern 5: Write Run Summary (scorecard notebook, final cell)

Uses the same `run_id` / `run_ts` session variables from Pattern 2. `Triggered_By` /
`Project_Name` come from job parameters or widgets (not a temp view):

```sql
INSERT INTO _validation_run
SELECT
  session.run_id,
  session.run_ts,
  '{project_name}',                        -- from widget/job param
  :silver_schema,                          -- runtime param, not a literal
  '{triggered_by}',                        -- SCHEDULED | MANUAL | PRE_DEPLOY | POST_FIX
  (SELECT COUNT(*) FROM _validation_table_result
   WHERE Run_Id = session.run_id),
  (SELECT COUNT(*) FROM _validation_table_result
   WHERE Run_Id = session.run_id AND Grade = 'A'),
  (SELECT COUNT(*) FROM _validation_table_result
   WHERE Run_Id = session.run_id AND Grade = 'B+'),
  (SELECT COUNT(*) FROM _validation_table_result
   WHERE Run_Id = session.run_id AND Grade = 'B'),
  (SELECT COUNT(*) FROM _validation_table_result
   WHERE Run_Id = session.run_id AND Grade IN ('C', 'D', 'F')),
  -- Overall grade = worst grade
  (SELECT CASE
    WHEN COUNT(CASE WHEN Grade = 'F' THEN 1 END) > 0 THEN 'F'
    WHEN COUNT(CASE WHEN Grade = 'D' THEN 1 END) > 0 THEN 'D'
    WHEN COUNT(CASE WHEN Grade = 'C' THEN 1 END) > 0 THEN 'C'
    WHEN COUNT(CASE WHEN Grade = 'B' THEN 1 END) > 0 THEN 'B'
    WHEN COUNT(CASE WHEN Grade = 'B+' THEN 1 END) > 0 THEN 'B+'
    ELSE 'A'
   END FROM _validation_table_result
   WHERE Run_Id = session.run_id),
  (SELECT SUM(Drift_Columns_Count) FROM _validation_table_result
   WHERE Run_Id = session.run_id),
  NULL,  -- Run_Duration_Seconds (set by orchestrator if available)
  current_timestamp();
```

> **Note the ordering dependency.** Pattern 5 must run AFTER Pattern 3 has written this run's
> `_validation_table_result` rows, but the `Row_Count_Delta` / `Grade_Delta` sub-selects in
> Pattern 3 find the PREVIOUS run by `ORDER BY _validation_run.Run_Timestamp DESC LIMIT 1` — so
> Pattern 5 (which inserts the current run's `_validation_run` row) must run LAST. Because the
> current run's `_validation_run` row does not exist yet, the latest existing row IS the prior
> run. (Do NOT use `MAX(Run_Id)` — `Run_Id` is a `uuid()` string and its max is random, not the
> most recent run; recency comes from `Run_Timestamp`.)

---

## Seeding the Gap Registry

On first run, seed `_gap_registry` from:

1. **progress.md "Fixes Applied"** — each constraint fix or dedup trick = one entry (type: CONSTRAINT_RELAXED or SYNTHETIC_KEY)
2. **progress.md "Human Review Needed"** — each advisory = one entry
3. **S2T mapping "Gaps" column** — each blocked or partial gap = one entry
4. **progress.md "Decisions Made" (descoped entities)** — each descoped entity = one entry (status: DEFERRED)
5. **S2T mapping `NULL_SOURCE` columns** — each column whose only bronze source is 100% null
   = one entry (`Gap_Type = NULL_SOURCE`), carrying its keep/drop disposition. A **dropped** null
   column MUST have a row here (it is omitted from DDL only with this registry entry — see
   `etl-development-framework/ddl-and-modeling.md`). A **kept** null column is a documented
   all-null column: register it, and mark its downstream population/drift checks
   `Is_Accepted_Exception = TRUE` (with `Exception_Reason` citing the NULL_SOURCE gap) so a
   documented all-null *business* column does not drag the entity's **validation quality grade**
   down. (Key-column population grading is unaffected — an all-null key is a harder failure and
   stays graded.) This is NOT a conflict with the assessment: the assessment's **fit grade**
   (Full/Partial/Blocked) still counts a NULL_SOURCE column as a shortfall → **Partial** (it
   delivers no data), while this **quality grade** measures whether the load landed *as intended* —
   a kept all-null column landed exactly as the spec said it would, so it is an accepted exception
   here. The two grades measure different axes (does the model fit the data vs. did the build do
   what the spec asked) and are both correct.

Example seed from manufacturing V2:

> 🔴 **Use `INSERT … SELECT … UNION ALL`, NOT `INSERT … VALUES`.** `uuid()` and `current_timestamp()`
> are non-deterministic and **cannot appear in a `VALUES` inline table** — Databricks rejects it with
> `INVALID_INLINE_TABLE.CANNOT_EVALUATE_EXPRESSION_IN_INLINE_TABLE` (this failed the gold-validation
> DDL seed). The `SELECT … UNION ALL` form below evaluates them per-row and works. See `phase-protocol.md`
> Critical Databricks SQL Pitfalls §1.

```sql
INSERT INTO _gap_registry
SELECT uuid(), 'dim_routing_operation', 'Work_Center_Key', 'Work_Center_Key defaults to -1 — no cross-reference between Oracle routing operations and DFF work centers', 'FK_ORPHAN', 'P3', 'ACCEPTED', CAST(NULL AS STRING), 'Build a cross-reference mapping table between Oracle operation codes and DFF cell IDs', 'S2T Mapping Report', DATE'2026-07-12', CAST(NULL AS DATE), 'OEE analysis cannot drill from routing operation to work center without manual mapping', CAST(NULL AS STRING), current_timestamp()
UNION ALL
SELECT uuid(), 'fact_wip_job', 'Routing_Key', 'Routing_Key and Bom_Header_Key default to -1 — join requires ROUTING_REVISION_DATE logic not yet implemented', 'MISSING_SOURCE', 'P0', 'OPEN', CAST(NULL AS STRING), 'Implement point-in-time routing revision lookup in MERGE notebook', 'S2T Mapping Report', DATE'2026-07-12', CAST(NULL AS DATE), 'WIP jobs cannot be linked to their routing or BOM for cost/cycle analysis', CAST(NULL AS STRING), current_timestamp()
  -- ... additional entries (one `UNION ALL SELECT …` per gap) from progress.md
;
```

---

## Schema Relationship to Model Tables

The validation tables live in the SAME schema as the model:

```
{silver_catalog}.{silver_schema}.       (resolved at run time — e.g. the sandbox catalog + manufacturing_silver in dev)
  ├── dim_plant                    (model)
  ├── dim_focus_factory            (model)
  ├── ...                          (model)
  ├── fact_wip_job                 (model)
  ├── ...                          (model)
  ├── _validation_run              (metadata)
  ├── _validation_table_result     (metadata)
  ├── _validation_check_detail     (metadata)
  ├── _data_drift_baseline         (metadata)
  └── _gap_registry                (metadata)
```

The leading underscore visually separates metadata from model tables in catalog explorers
and sorts them to the top alphabetically (before `d` for dim, `f` for fact).

---

## Selectable columns per table (authoritative)

> **This is the single source of truth for metadata-table column names.** `dashboard-spec.md`,
> `SKILL.md`, and every dataset query defer here. **Rule:** these column names exist — reference
> them exactly as written and never invent a column not on this list. Spark SQL is
> case-insensitive, so casing need not match; existence must. `Run_Timestamp` (not `_loaded_at`)
> is the authoritative run-recency column — order runs by `Run_Timestamp DESC`.

**`_validation_run`:** `Run_Id`, `Run_Timestamp`, `Project_Name`, `Schema_Name`, `Triggered_By`, `Total_Entities`, `Entities_Grade_A`, `Entities_Grade_B_Plus`, `Entities_Grade_B`, `Entities_Grade_C_Or_Below`, `Overall_Grade`, `Drift_Alerts_Count`, `Run_Duration_Seconds`, `_loaded_at`

**`_validation_table_result`:** `Run_Id`, `Table_Name`, `Table_Type`, `Tier`, `Row_Count`, `Row_Count_Delta`, `Pk_Duplicate_Count`, `Fk_Orphan_Rate_Pct`, `Key_Column_Pop_Pct`, `Freshness_Hours`, `Drift_Columns_Count`, `Integration_Pass`, `Grade`, `Grade_Delta`, `Known_Gaps_Count`, `Accepted_Exceptions`, `Remediation_Status`, `_loaded_at`

**`_validation_check_detail`:** `Run_Id`, `Table_Name`, `Check_Name`, `Check_Type`, `Status`, `Threshold_Value`, `Actual_Value`, `Deviation_Pct`, `Is_Accepted_Exception`, `Exception_Reason`, `Message`, `_loaded_at`

**`_data_drift_baseline`:** `Table_Name`, `Column_Name`, `Metric_Type`, `Baseline_Value`, `Tolerance_Pct`, `Tolerance_Direction`, `Baseline_Set_Date`, `Baseline_Run_Id`, `Last_Reset_Date`, `Reset_Reason`, `Is_Active`, `_loaded_at`

**`_gap_registry`:** `Gap_Id`, `Table_Name`, `Column_Name`, `Gap_Description`, `Gap_Type`, `Priority`, `Status`, `Remediation_Status`, `Unblock_Action`, `Source_Document`, `Created_Date`, `Resolved_Date`, `Impact_Description`, `Assigned_To`, `_loaded_at`

---

## Critical SQL Pattern — Aggregate Isolation

**Never mix an aggregate function (`COUNT`, `SUM`, `MIN`, …) with non-aggregated columns from a `JOIN` in the same `SELECT` without `GROUP BY`.** Databricks raises `MISSING_GROUP_BY (SQLSTATE 42803)` for this pattern. Compute the aggregate in a subquery first, then join.

This is the single most common generated-SQL failure — apply it everywhere, not just drift checks.

```sql
-- ❌ BROKEN: bare COUNT(*) mixed with non-aggregated join columns → MISSING_GROUP_BY
SELECT 'order' AS table_name, CAST(COUNT(*) AS STRING) AS current_value,
       b.Baseline_Value, b.Tolerance_Pct
FROM `order` LEFT JOIN _data_drift_baseline b ON b.Table_Name = 'order'
                                               AND b.Column_Name = 'row_count';

-- ✅ CORRECT: aggregate isolated in a subquery; outer SELECT is a simple join, no aggregates
SELECT 'order' AS table_name, CAST(c.cnt AS STRING) AS current_value,
       b.Baseline_Value, b.Tolerance_Pct
FROM (SELECT COUNT(*) AS cnt FROM `order`) c
LEFT JOIN _data_drift_baseline b ON b.Table_Name = 'order'
                                 AND b.Column_Name = 'row_count';
```

See also the correlated-subquery variant in `dashboard-spec.md` "SQL Pitfalls for Dashboard Queries" — the same isolation rule applies to scorecard and dashboard aggregate contexts.
