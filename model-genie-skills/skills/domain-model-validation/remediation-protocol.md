# Remediation Protocol

## Overview

When the validation skill detects grade degradation (Grade C or below), it produces
a **remediation brief** — a structured document that provides the ETL Development
Framework skill with enough context to diagnose and fix the issue without re-running
discovery.

This is a **human-in-the-loop** process:
1. Validation skill detects the problem and surfaces it
2. Developer reviews the remediation brief
3. Developer invokes the ETL skill with "fix these issues"
4. ETL skill diagnoses, proposes fix, tests, grades
5. Developer re-runs validation to confirm fix

---

## Remediation Status Flow

Each issue in `_gap_registry` and `_validation_table_result` follows this lifecycle:

```
NULL → DETECTED → TRIAGED → ESCALATED_TO_ETL → RESOLVED
  │                     │
  │                     └────────────────────────────────────→ ACCEPTED
  │                                                        (not a real issue)
  └──────────────────────────────────────────────────────→ DEFERRED
                                                             (known, not fixing now)
```

| Status | Meaning | Who Sets It |
| --- | --- | --- |
| NULL | No issue detected (healthy) | System |
| DETECTED | Validation found a problem (grade dropped) | Validation skill (automatic) |
| TRIAGED | Developer reviewed, confirmed it's a real issue | Developer (manual) |
| ESCALATED_TO_ETL | Remediation brief generated and handed to ETL skill | Validation skill + developer |
| RESOLVED | ETL skill fixed the issue, validation confirms grade restored | ETL skill + validation re-run |
| ACCEPTED | Reviewed and determined to be expected behavior (update threshold) | Developer |
| DEFERRED | Known issue, not fixing in current sprint | Developer |

---

## Automatic Detection Rules

The scorecard notebook automatically sets `Remediation_Status = 'DETECTED'` when:

| Condition | Trigger |
| --- | --- |
| Grade degradation | Current grade < previous grade (e.g., A → B) |
| New failure | A check that was PASS is now FAIL |
| Drift alert (critical) | Drift deviation > 2x tolerance |
| Row count anomaly | Row count decreased > 5% without explanation |
| PK violation (new) | PK duplicates appear where there were none |

Detection does NOT auto-escalate. A developer must review and decide:
- Is this a real problem? → Triage and escalate
- Is this expected? → Accept (update threshold or mark as exception)
- Is this not urgent? → Defer

---

## Remediation Brief Format

Generated as `docs/.pipeline/handoffs/{layer}/remediation_brief.md` (silver default; gold run → `docs/.pipeline/handoffs/gold/remediation_brief.md`; overwritten each time):

```markdown
# Remediation Brief — {Domain} {Date}

## Summary

| Metric | Value |
| --- | --- |
| Run ID | {run_id} |
| Run Timestamp | {timestamp} |
| Triggered By | {trigger} |
| Entities Degraded | {count} |
| Most Severe | {worst_grade} on {worst_entity} |

## Entities Requiring Remediation

### {entity_1} — Grade {grade} (was {previous_grade})

**Failing Checks:**

| Check | Type | Expected | Actual | Deviation |
|---|---|---|---|---|
| {check_name_1} | {type} | {threshold} | {actual} | {deviation}% |
| {check_name_2} | {type} | {threshold} | {actual} | {deviation}% |

**Root Cause Category:** {one of: SOURCE_DRIFT | CODE_REGRESSION | NEW_DATA_PATTERN | UPSTREAM_ISSUE | UNKNOWN}

**Evidence:**
- {Specific data points that suggest the root cause}
- {e.g., "NULL rate in WIP_ENTITY_ID jumped from 12.7% to 25.1% — suggests new non-WIP LPN types in source"}
- {e.g., "Row count dropped 15% — source table lost data (upstream issue?)"}

**Suggested Fix Category:** {one of: FIX_MERGE | ADD_FILTER | RELAX_CONSTRAINT | ADD_SOURCE | INVESTIGATE}

**Context for ETL Skill:**
- MERGE notebook: `src/silver/{entity}.sql`
- DDL notebook: `src/silver/ddl/ddl_{entity}.sql`
- Source table: `<src_{logical}>.{source_table}` (bronze prefix is a runtime param — see conventions.yml `bronze_sources`)
- Previous grade (at build): {grade_at_build}
- Known gaps that may be related: {gap_ids from _gap_registry}

---

### {entity_2} — Grade {grade} (was {previous_grade})
{... same structure ...}

---

## Drift Alerts (Non-Grade-Impacting)

These drifts haven't degraded grades yet but should be monitored:

| Entity | Column | Metric | Baseline | Current | Drift % | Direction |
|---|---|---|---|---|---|---|
| {entity} | {column} | {metric} | {baseline} | {current} | {drift}% | {increasing/decreasing} |

---

## Recommended Actions

1. **Immediate (Grade C or worse):** Invoke ETL skill with this brief
2. **Monitor (Grade B/B+):** Re-run validation in 24h; if not resolved, escalate
3. **Investigate (Drift):** Check source tables for upstream changes

## ETL Skill Handoff Command

> "Fix the following entities in the {project} project. Here is the
> remediation brief: [paste brief or reference path]. Use the ETL Development
> Framework skill to diagnose, fix, test, and grade each entity."
```

---

## Root Cause Classification

The remediation brief includes a suggested root cause category to help the ETL
skill prioritize its diagnosis:

| Category | Indicators | Typical Fix |
| --- | --- | --- |
| SOURCE_DRIFT | Drift alerts on source-mapped columns; row count grew/shrank; null rates changed | Add defensive filters, COALESCE, or update threshold |
| CODE_REGRESSION | Grade dropped after a code change; PK dups appeared suddenly | Revert or fix the MERGE notebook logic |
| NEW_DATA_PATTERN | New distinct values in FK columns; new enum values; new source records | Expand MERGE to handle new patterns |
| UPSTREAM_ISSUE | Source table row count changed dramatically; source schema changed | Escalate to data platform team |
| UNKNOWN | No clear pattern; multiple checks failed simultaneously | Manual investigation needed |

### Classification Logic

```
IF pk_duplicates_new > 0 AND previous_run_had_0:
  category = CODE_REGRESSION (likely MERGE dedup logic broke)

ELSE IF row_count_decreased > 5%:
  category = UPSTREAM_ISSUE (source lost data)

ELSE IF drift_alerts > 3 columns on same table:
  category = SOURCE_DRIFT (source characteristics changed broadly)

ELSE IF fk_orphan_rate_increased AND dim_row_count_stable:
  category = NEW_DATA_PATTERN (new FK values not in dim)

ELSE IF single_check_failed AND others_pass:
  category = SOURCE_DRIFT or NEW_DATA_PATTERN (localized)

ELSE:
  category = UNKNOWN
```

---

## Gap Registry Updates During Remediation

When the ETL skill resolves an issue:

1. ETL skill fixes the MERGE notebook and re-runs
2. Developer triggers validation with `Triggered_By = 'POST_FIX'`
3. Validation re-grades the entity
4. If grade restored to A or B+:
   - Update `_gap_registry.Remediation_Status = 'RESOLVED'` and `Status = 'RESOLVED'`
   - Update `_gap_registry.Resolved_Date = current_date()`
   - Update `_validation_table_result.Remediation_Status = 'RESOLVED'`
   - **Hand off to `domain-sync`** — a resolved gap makes the narrative FK cell, Genie
     caveats, Model Guide health, and `NEXT_STEPS.md` stale. Load the `domain-sync` skill
     ("propagate this fix") to scoped-regenerate exactly those artifacts and re-lint. Do NOT
     hand-patch the narrative comment to say "PASS" — regenerate from the fixed MERGE.
5. If grade still degraded:
   - Keep `Remediation_Status = 'ESCALATED_TO_ETL'`
   - Generate updated remediation brief with new evidence

---

## Acceptance Protocol

When a developer determines a "failure" is actually expected behavior:

1. Update `_gap_registry` entry: `Status = 'ACCEPTED'`
2. Update the narrative notebook's threshold comment to document the acceptance
3. Set `Is_Accepted_Exception = TRUE` in the check's metadata write
4. Optionally: update `_data_drift_baseline` if the new value should become the baseline
5. Re-run validation to confirm grade is now correct with the accepted exception

Example:
```sql
-- A developer determines that 8% FK orphans in dim_manufacturing_bom_header
-- is permanent (Oracle orgs will never be in DFF dim_plant)
UPDATE _gap_registry
SET Status = 'ACCEPTED',
    Remediation_Status = NULL,
    _loaded_at = current_timestamp()
WHERE Table_Name = 'dim_manufacturing_bom_header'
  AND Column_Name = 'Plant_Key'
  AND Gap_Type = 'FK_ORPHAN';
```

---

## Integration with Validation Job

The remediation brief is generated by the scorecard notebook when it detects
entities at Grade C or below:

This runs in the scorecard, after Pattern 2 has claimed the PENDING rows into the `run_id`
session variable (see `validation-schema.md` Pattern 2 — `DECLARE OR REPLACE VARIABLE run_id`).
It references `run_id`, never a `_current_run` temp view.

```sql
-- In scorecard.sql, after computing grades:
-- If any entity is Grade C or worse, collect remediation context (a subsequent formatting cell
-- renders it as markdown — a `%md`/`spark.sql`-fed Python cell under `etl_language: python`,
-- or a `-- %md` cell populated from this result under `sql`)
CREATE OR REPLACE TEMPORARY VIEW _remediation_needed AS
SELECT
  t.Table_Name,
  t.Grade,
  prev.Grade AS Previous_Grade,
  -- All failing checks for this entity
  COLLECT_LIST(NAMED_STRUCT(
    'check_name', cd.Check_Name,
    'check_type', cd.Check_Type,
    'threshold', cd.Threshold_Value,
    'actual', cd.Actual_Value,
    'deviation', cd.Deviation_Pct,
    'message', cd.Message
  )) AS Failing_Checks
FROM _validation_table_result t
JOIN _validation_check_detail cd
  ON t.Run_Id = cd.Run_Id AND t.Table_Name = cd.Table_Name
LEFT JOIN (
  SELECT Table_Name, Grade
  FROM _validation_table_result
  WHERE Run_Id = (SELECT Run_Id FROM _validation_run
                  ORDER BY Run_Timestamp DESC LIMIT 1 OFFSET 1)
) prev ON t.Table_Name = prev.Table_Name
WHERE t.Run_Id = session.run_id
AND t.Grade IN ('C', 'D', 'F')
AND cd.Status = 'FAIL'
GROUP BY t.Table_Name, t.Grade, prev.Grade;
```

*(`_remediation_needed` is a purely local formatting convenience within the scorecard session —
it is NOT the forbidden cross-notebook `_current_run` state; it never carries the run_id between
notebooks. The `run_id` session variable is the sole run correlator.)*

The scorecard then updates the remediation status:

```sql
-- Mark detected issues
MERGE INTO _validation_table_result t
USING _remediation_needed r
ON t.Table_Name = r.Table_Name
  AND t.Run_Id = session.run_id
WHEN MATCHED AND t.Grade IN ('C', 'D', 'F') THEN
  UPDATE SET Remediation_Status = 'DETECTED', _loaded_at = current_timestamp();
```
