# Regression & Drift Detection

## Overview

This document defines assertion patterns, drift detection logic, threshold configuration,
and baseline management. The narrative notebooks serve as regression tests — they assert
expected conditions and fail visibly when those conditions are violated.

> **Runtime params.** All SQL below assumes the notebook's runtime-param header has set the
> session catalog/schema (`USE CATALOG/SCHEMA IDENTIFIER(:silver_catalog/:silver_schema)`), so
> model and `_validation_*` tables are referenced **unqualified** and bronze sources via
> `IDENTIFIER(:src_{logical} || '.{table}')`. Never hard-code catalog/schema. See
> `validation-schema.md` "Runtime Parameters".

---

## Assertion Philosophy

Every SQL assertion cell follows this contract:
- Returns a result set with a `Status` column: `PASS`, `FAIL`, `WARN`, or `SKIP`
- `PASS` = condition met, no action needed
- `FAIL` = condition violated, contributes to grade degradation
- `WARN` = condition borderline, does not degrade grade but surfaces in dashboard
- `SKIP` = check cannot run (e.g., baseline missing on first run)

The scorecard notebook reads all results and computes grades. Individual notebooks
do NOT fail the job — only the scorecard's fail gate does (Grade D or F).

---

## Threshold Configuration

### Source of Truth: S2T Mapping

Thresholds are seeded from the Source-to-Target Mapping Report. Specifically:

| S2T Field | Maps To | Example |
| --- | --- | --- |
| Fit Grade: Full | FK orphan threshold: 1% | "All source columns map cleanly" |
| Fit Grade: Partial with documented gap | FK orphan threshold: relaxed to gap % + 2% buffer | "8% BOM headers reference non-DFF plants" → threshold = 10% |
| Fit Grade: Partial (column population) | Key column population threshold: relaxed | "87% have WIP_ENTITY_ID" → threshold = 85% for that column |
| Expected row count | Row count drift baseline | progress.md Entity Status |
| Known filter | Business rule validation | "WHERE TRANS_TYPE = 'PROD'" → verify no other types leak in |

### Default Thresholds (when S2T mapping is silent)

| Check Type | Default Threshold | Grade Impact |
| --- | --- | --- |
| PK uniqueness | 0 duplicates | Any dups = immediate Grade F |
| FK orphan rate | ≤ 1% | >1% = B+, >3% = B, >5% = C, >10% = D, >20% = F |
| Key column population | ≥ 95% | <95% = B+, <90% = B, <80% = C, <50% = F |
| Row count (table-level) | Within 20% of baseline (increase), 5% (decrease) | Shrinkage = WARN at 5%, FAIL at 20% |
| Freshness | < 48 hours since last _loaded_at | >48h = WARN, >168h (7 days) = FAIL |

### Per-Entity Override Pattern

Overrides are embedded as SQL comments in the narrative notebook (self-documenting):

```sql
-- THRESHOLD OVERRIDE: FK_Plant_Key orphan rate
-- Default: 1.0%
-- Override: 10.0%
-- Reason: 8 Oracle orgs (335K rows) reference plants not in DFF dim_plant
-- Source: progress.md "Human Review Needed" + S2T mapping dim_manufacturing_bom_header
-- Approved: 2026-07-12 (initial build)
```

---

## Drift Detection Logic

### What Is Drift?

Drift = a column's statistical properties changed beyond expected tolerance compared
to a frozen baseline. Unlike assertions (which check absolute conditions), drift
detects relative change — "this used to be X, now it's significantly different."

### Metrics Captured Per Column

| Metric Type | Applies To | Formula | Example |
| --- | --- | --- | --- |
| NULL_RATE | All columns | `100 * (1 - COUNT(col) / COUNT(*))` | 12.7% nulls in WIP_ENTITY_ID |
| DISTINCT_COUNT | String, FK columns | `COUNT(DISTINCT col)` | 42 distinct plants |
| MIN_VALUE | Numeric, timestamp | `MIN(col)` | Earliest date: 2018-01-01 |
| MAX_VALUE | Numeric, timestamp | `MAX(col)` | Latest date: 2026-07-12 |
| MEAN_VALUE | Numeric only | `AVG(col)` | Average lot qty: 847.3 |
| ROW_COUNT | Table-level (PK column) | `COUNT(*)` | 10,450,922 rows |

### Drift Detection Algorithm

```
For each (table, column, metric) in _data_drift_baseline WHERE Is_Active = TRUE:
  1. Compute current_value from live table
  2. Compute deviation_pct = |current - baseline| / baseline * 100
  3. Check direction:
     - If Tolerance_Direction = 'INCREASE' and current < baseline: no alert
     - If Tolerance_Direction = 'DECREASE' and current > baseline: no alert
     - If Tolerance_Direction = 'BOTH': alert on either direction
  4. If deviation_pct > Tolerance_Pct: DRIFT_ALERT
  5. Write to _validation_check_detail with Check_Type = 'DRIFT'
```

### Tolerance Defaults by Column Category

| Category | Metric | Tolerance | Direction | Rationale |
| --- | --- | --- | --- | --- |
| PK / surrogate key | DISTINCT_COUNT (=row count) | 20% | INCREASE only | Tables grow; shrinkage is alarming |
| FK columns | NULL_RATE | 5% | BOTH | Sudden nulls = source issue; sudden population = new mapping |
| String business columns | NULL_RATE | 10% | BOTH | Moderate tolerance for optional fields |
| String business columns | DISTINCT_COUNT | 15% | BOTH | Cardinality changes slowly |
| Numeric measures | NULL_RATE | 5% | BOTH | Measures should be consistently populated |
| Numeric measures | MEAN_VALUE | 15% | BOTH | Business metrics can fluctuate |
| Numeric measures | MIN_VALUE | 25% | DECREASE | New minimums may be legitimate |
| Numeric measures | MAX_VALUE | 25% | INCREASE | New maximums may be legitimate |
| Timestamp columns | MAX_VALUE | N/A (special) | N/A | Use freshness check instead |
| Boolean columns | NULL_RATE | 5% | BOTH | Should be fully populated |
| Table row count | ROW_COUNT | 20% increase, 5% decrease | ASYMMETRIC | Growth normal; shrinkage suspicious |

### S2T Mapping Tolerance Overrides

When the S2T mapping documents expected characteristics, override defaults:

| S2T Documentation | Override |
| --- | --- |
| "12.7% of rows have NULL WIP_ENTITY_ID (purchase order LPNs)" | NULL_RATE baseline = 12.7%, tolerance = 15% INCREASE (allow growth, alert on sudden population) |
| "87.3% have PRODUCTION_COMPLETION_DATE" | NULL_RATE baseline = 12.7%, tolerance = 5% BOTH |
| "Row count expected ~10M (filtered from 26.8M)" | ROW_COUNT baseline = 10M, tolerance = 30% INCREASE (filter ratio may shift) |

---

## Baseline Management

### Baseline Establishment (First Run)

1. Execute all narrative notebooks
2. For each table, compute all applicable metrics
3. INSERT into `_data_drift_baseline` with:
   - `Baseline_Set_Date` = current_timestamp()
   - `Baseline_Run_Id` = current run UUID
   - `Is_Active` = TRUE
   - Tolerance values from S2T mapping overrides or defaults above

> **Write the baseline with `INSERT … WHERE NOT EXISTS`, NOT `MERGE`.** The baseline row must be
> written exactly once and never overwritten (Freeze Rule below), so the natural idempotent guard
> is a `WHERE NOT EXISTS` on the (Table_Name, Column_Name, Metric_Type) key. `MERGE` against this
> tiny table is also prone to a **client-side timeout even when the server commits** — on the
> Meridian run the baseline `MERGE` client-timed-out, the notebook re-ran, and the pattern had to
> be hand-patched to `INSERT … WHERE NOT EXISTS`. Prescribe the winning pattern from the start:
>
> ```sql
> -- Explicit column list — the table has 12 columns; an original baseline sets 9 and leaves
> -- Last_Reset_Date / Reset_Reason NULL (only a manual reset fills them). Baseline_Value is STRING.
> INSERT INTO _data_drift_baseline
>   (Table_Name, Column_Name, Metric_Type, Baseline_Value, Tolerance_Pct, Tolerance_Direction,
>    Baseline_Set_Date, Baseline_Run_Id, Is_Active, _loaded_at)
> SELECT '{table}', '{column}', '{metric}', CAST({value} AS STRING), {tolerance}, '{direction}',
>        current_timestamp(), :run_id, TRUE, current_timestamp()
> WHERE NOT EXISTS (
>   SELECT 1 FROM _data_drift_baseline
>   WHERE Table_Name = '{table}' AND Column_Name = '{column}' AND Metric_Type = '{metric}'
> );
> ```
>
> This is safe to re-run (a re-executed notebook is a no-op once the baseline exists) and honors
> the Freeze Rule — an existing baseline is never touched.

### Baseline Freeze Rule

**Baselines are NEVER auto-updated.** Even if drift is detected and accepted, the
baseline stays frozen. This ensures:
- Historical drift is always measurable from the same reference point
- Gradual drift is detected ("boiling frog" problem)
- Reset requires explicit human action

### Manual Baseline Reset

When a legitimate change occurs (e.g., new source added, schema change, intentional
data migration), reset the baseline:

```sql
-- Reset baseline for specific column
UPDATE _data_drift_baseline
SET
  Baseline_Value = '{new_value}',
  Last_Reset_Date = current_timestamp(),
  Reset_Reason = '{reason}',
  _loaded_at = current_timestamp()
WHERE Table_Name = '{table}'
  AND Column_Name = '{column}'
  AND Metric_Type = '{metric}';
```

### Baseline Deactivation

To stop monitoring a column without deleting history:

```sql
UPDATE _data_drift_baseline
SET Is_Active = FALSE, _loaded_at = current_timestamp()
WHERE Table_Name = '{table}' AND Column_Name = '{column}';
```

---

## Regression Test Patterns

### Pattern 1: Previous-Run Delta (canonical — used by the scorecard)

This is a **data-state** regression: compare this run's row count / grade to the immediately
previous run, on the LIVE loaded table. It is the seed the scorecard uses to compute
`Row_Count_Delta` and `Grade_Delta` (SKILL.md Rule 28) — these deltas MUST be computed, never
stubbed (`AS 0`, `NULL AS ..._Delta`, hard-coded `'NEW'`) except on the genuine first run.

> **Not to be confused with build-time idempotency.** Whether re-running the MERGE converges
> (identical row count + surrogate-key set on the same input) is proven at BUILD time by
> `etl-development-framework`'s twice-run recheck on the real load (`build_manifest.md` §8) — this
> skill does not re-run the load. Pattern 1 is the live-data run-over-run stability check across
> scheduled runs, a data-state drift signal, not a build-time recheck.

```sql
-- Previous-run delta: row count vs the immediately previous validation run
SELECT
  'Row_Count_Delta' AS Check_Name,
  prev.Row_Count AS Previous_Row_Count,
  curr_count AS Current_Row_Count,
  curr_count - prev.Row_Count AS Delta,
  CASE
    WHEN prev.Row_Count IS NULL THEN 'SKIP'                                   -- genuine first run
    WHEN ABS(curr_count - prev.Row_Count) <= prev.Row_Count * 0.001 THEN 'PASS'  -- <0.1% change
    ELSE 'WARN'  -- Legitimate growth or unexpected change
  END AS Status
FROM (
  -- Previous run = latest existing _validation_run row by Run_Timestamp. The current run's
  -- _validation_run row is written LAST by the scorecard (Pattern 5), so it is not present yet
  -- and no OFFSET is needed. Run_Id is a uuid() string — never order/max on it; recency is
  -- Run_Timestamp. See validation-schema.md Pattern 3/5 ordering.
  SELECT r.Row_Count FROM _validation_table_result r
  JOIN _validation_run v ON r.Run_Id = v.Run_Id
  WHERE r.Table_Name = '{table_name}'
  ORDER BY v.Run_Timestamp DESC LIMIT 1
) prev
RIGHT JOIN (SELECT COUNT(*) AS curr_count FROM {table_name}) curr
```

**`Grade_Delta` uses the same previous-run row.** Compare the entity's current computed grade
to `prev.Grade` and emit `IMPROVED | STABLE | DEGRADED`; emit `NEW` ONLY when no previous
`_validation_table_result` row exists for the entity (genuine first run). Do not default every
row to `'NEW'`.

### Pattern 2: Source Coverage Verification

Verify the MERGE isn't accidentally filtering out valid data:

```sql
-- Source coverage: silver row count vs source row count (with expected filter)
SELECT
  'Source_Coverage' AS Check_Name,
  source_count,
  silver_count,
  ROUND(100.0 * silver_count / NULLIF(source_count, 0), 2) AS Coverage_Pct,
  CASE
    WHEN silver_count >= source_count * {expected_coverage_pct} THEN 'PASS'
    ELSE 'WARN'
  END AS Status
FROM (
  SELECT
    (SELECT COUNT(*) FROM IDENTIFIER(:src_{logical} || '.{source_table}')
     WHERE {source_filter}) AS source_count,
    (SELECT COUNT(*) FROM {table_name}) AS silver_count   -- unqualified: session catalog.schema
)
```

### Pattern 3: Referential Completeness (Facts)

Verify all expected dimension values are represented:

```sql
-- Referential completeness: dimensions used by this fact
SELECT
  'Ref_Completeness_{dim}' AS Check_Name,
  dim_total,
  dim_referenced,
  ROUND(100.0 * dim_referenced / NULLIF(dim_total, 0), 2) AS Usage_Pct,
  CASE
    WHEN dim_referenced >= dim_total * 0.5 THEN 'PASS'  -- At least 50% of dim values appear in fact
    ELSE 'WARN'  -- Many dim values unused (might be fine for filtered facts)
  END AS Status
FROM (
  SELECT
    (SELECT COUNT(*) FROM {dim} WHERE {Dim}_Key != -1) AS dim_total,
    (SELECT COUNT(DISTINCT {Dim}_Key) FROM {fact}
     WHERE {Dim}_Key != -1) AS dim_referenced
)
```

### Pattern 4: Temporal Continuity

Verify no unexpected date gaps:

```sql
-- Temporal continuity: check for gaps in date coverage
WITH date_range AS (
  SELECT
    MIN(CAST({date_column} AS DATE)) AS min_date,
    MAX(CAST({date_column} AS DATE)) AS max_date,
    DATEDIFF(MAX(CAST({date_column} AS DATE)), MIN(CAST({date_column} AS DATE))) + 1 AS expected_days,
    COUNT(DISTINCT CAST({date_column} AS DATE)) AS actual_days
  FROM {table_name}
  WHERE {date_column} IS NOT NULL
)
SELECT
  'Temporal_Continuity' AS Check_Name,
  min_date, max_date,
  expected_days, actual_days,
  expected_days - actual_days AS Missing_Days,
  CASE
    WHEN actual_days >= expected_days * 0.95 THEN 'PASS'  -- 95% day coverage
    ELSE 'WARN'
  END AS Status
FROM date_range
```

### Pattern 5: Constraint Validation (Post-Relaxation)

For constraints that were relaxed during build, validate the relaxation is bounded:

```sql
-- Constraint validation: Lot_Qty allows negatives (relaxed from >= 0)
-- Verify negative values are bounded (not data corruption)
SELECT
  'Constraint_Lot_Qty_Negatives' AS Check_Name,
  COUNT(*) AS Total_Rows,
  SUM(CASE WHEN Lot_Qty < 0 THEN 1 ELSE 0 END) AS Negative_Count,
  ROUND(100.0 * SUM(CASE WHEN Lot_Qty < 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS Negative_Pct,
  MIN(Lot_Qty) AS Min_Qty,
  CASE
    WHEN SUM(CASE WHEN Lot_Qty < 0 THEN 1 ELSE 0 END) / COUNT(*) <= 0.05 THEN 'PASS'  -- <5% negatives
    ELSE 'WARN'  -- More negatives than expected
  END AS Status
FROM fact_production_lot
```

---

## Pre-Deploy Gate Pattern

The validation job can be wired as a pre-deploy gate in the DAB bundle:

```yaml
# In validation_job.yml
tasks:
  - task_key: pre_deploy_gate
    depends_on:
      - task_key: scorecard
    notebook_task:
      notebook_path: ../src/silver/validation/pre_deploy_gate
    # This task reads the scorecard results and fails if any entity < Grade B
```

The pre-deploy gate notebook:

```sql
-- Pre-deploy gate: block promotion if quality below threshold
SELECT
  CASE
    WHEN COUNT(*) > 0 THEN
      RAISE_ERROR(
        'PRE-DEPLOY GATE FAILED: ' || COUNT(*) || ' entities below Grade B. '
        || 'Fix before promoting to production. '
        || 'Entities: ' || CONCAT_WS(', ', COLLECT_LIST(Table_Name))
      )
    ELSE 'PRE-DEPLOY GATE PASSED: All entities at Grade B or better.'
  END AS Gate_Result
FROM _validation_table_result
-- Latest run by Run_Timestamp (Run_Id is a uuid() string — MAX(Run_Id) is random, not latest)
WHERE Run_Id = (SELECT Run_Id FROM _validation_run ORDER BY Run_Timestamp DESC LIMIT 1)
AND Grade IN ('C', 'D', 'F')
```

---

## Scheduling Strategy

| Trigger | When | Purpose |
| --- | --- | --- |
| SCHEDULED | Daily, after ETL job window (e.g., 8 AM if ETL runs at 6 AM) | Ongoing monitoring |
| PRE_DEPLOY | Before `databricks bundle deploy -t prod` | Promotion gate |
| POST_FIX | After a remediation cycle completes | Verify fix worked |
| MANUAL | On-demand by developer | Investigation or onboarding |

The `Triggered_By` value is passed to the scorecard via a job parameter or
widget, and recorded in `_validation_run` for audit trail.
