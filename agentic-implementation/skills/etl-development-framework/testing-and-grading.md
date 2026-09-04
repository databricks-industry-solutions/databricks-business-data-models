# Testing & Grading Protocol

## Requirements Gate (Rule 16)

**Never run any discovery queries until `business_requirements.md` is graded B or better** (source system confirmed at schema level + at least two named entities). Grade using the rubric in `discovery-and-gap-analysis.md` §2; re-prompt and block if below B.

---

## When to Use

After each entity's load notebook is authored (Phase 4), run the **real load** for EACH entity
individually and grade it before creating the DAB job. Follow load-order (Tier 0 first, then Tier
1, etc.) since later entities depend on earlier ones being populated. **This is the per-entity
gate** — an entity does not advance `BUILT → TESTED` (and the batch does not advance) until it
reaches Grade A on post-load DQ against the real table and passes the idempotency recheck below.
Comprehensive data-state validation across the whole domain is the separate downstream
`domain-model-validation` skill; this gate is the build-time "landed as intended" check.

> **`etl_type: sdp_pipeline` — this gate does NOT apply (Rule 17 / Rule 22).** SDP builds ship
> no build-time tests, no post-load validation notebook, and no TDD gate. The `TESTED` status
> in `etl_state.md` likewise does not apply to SDP entities — they advance on `AUTHORED` (the
> declarative source written and row-count verified). See `sdp-pipeline-development.md` intro.

> **This gate runs per entity, immediately after its own load** — not accumulated across
> a batch into one UNION ALL query. Each entity advances `BUILT → TESTED` on its own
> PK/FK/population/row-count pass (plus the idempotency recheck for the first entity of
> each strategy) before the next entity's load runs.
> The whole-domain UNION ALL belongs only to the recurring `validate_{layer}` gate
> (see the Validation Gate Notebook section below).

---

## Per-Notebook Test Cycle

```
For each notebook (in dependency order):
  1. RUN the notebook
  2. If ERROR → diagnose, fix, re-run (up to 5 attempts)
  3. If SUCCESS → run quality checks on the target table:
     - PK uniqueness (COUNT vs COUNT DISTINCT)
     - FK orphan rates (LEFT JOIN to parent, count nulls)
     - Column population rates (% non-null)
     - Row count sanity check
  4. IDEMPOTENCY RECHECK (first entity of each load strategy in the batch): run the load a
     SECOND time and assert row count + surrogate-key set are unchanged (see below)
  5. GRADE the table (A through F)
  6. If Grade A (and idempotency PASS where the recheck applies — first entity of each strategy;
     siblings inherit) → move to next notebook
  7. If not Grade A → classify issues and fix:
     - FIX: update notebook SQL, re-run
     - ENRICH: add source join, re-run
     - ACCEPT: document justification, consider this "done"
     - HUMAN NEEDED: flag for user review, move on
  8. Iterate until Grade A or HUMAN NEEDED (max 5 iterations per notebook)
```

---

## Quality Check Queries

### PK Uniqueness

```sql
SELECT
  '{entity}' AS entity,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT {Entity}_Key) AS distinct_keys,
  COUNT(*) - COUNT(DISTINCT {Entity}_Key) AS dup_pks
FROM {table};
```

Expect: `dup_pks = 0`

### FK Orphan Rate

```sql
SELECT
  '{fact} -> {dim}' AS check_name,
  COUNT(*) AS total_rows,
  SUM(CASE WHEN d.{Entity}_Key IS NULL THEN 1 ELSE 0 END) AS orphans,
  ROUND(100.0 * SUM(CASE WHEN d.{Entity}_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS orphan_pct
FROM {fact} f
LEFT JOIN {dim} d
  ON f.{Entity}_Key = d.{Entity}_Key
WHERE f.{Entity}_Key != -1;  -- Exclude intentional Unknown references
```

Expect: `orphan_pct <= 1%` for Grade A

Note: Rows where the fact FK = -1 are intentional Unknown references (join missed,
COALESCE defaulted to -1). They should NOT be counted as orphans. Only count rows
where the FK is a positive value that doesn't exist in the parent dim.

### Column Population

```sql
SELECT
  '{entity}.{Column_Name}' AS col,
  COUNT(*) AS total_rows,
  COUNT({Column_Name}) AS non_null,
  ROUND(100.0 * COUNT({Column_Name}) / COUNT(*), 2) AS pct_populated
FROM {table};
```

Expect: `pct_populated >= 95%` for key columns

### Row Count Sanity

```sql
SELECT
  '{entity}' AS entity,
  COUNT(*) AS target_rows,
  (SELECT COUNT(*) FROM IDENTIFIER(src_{logical} || '.{source_table}')) AS source_rows  -- session var; drop ':' if run inside the transform's context
FROM {table};   -- unqualified: session catalog.schema
```

Row count should be close to source (minus dedup). Significant differences indicate
a join fan-out or overly aggressive filtering.

---

## Idempotency recheck (the twice-run gate)

The one build-time correctness property that post-load DQ on a single run cannot see is
**idempotency**: does re-running the load on the same input converge, or does it duplicate/drift?
Prove it cheaply on real data — no fixtures — by running the load a **second time** and asserting
the target is unchanged.

**When:** run it on the **first entity of each load strategy** in a batch (one FULL_MERGE, one
INCREMENTAL_MERGE, one APPEND_ONLY, one Type-2 dim). Once a strategy's notebook shape is proven
idempotent, sibling entities using the same shape inherit the confidence — you need not re-run
every entity twice. Always run it on any entity whose dedup/grain you had to hand-tune.

**How:** snapshot the key set before the second run, re-run the load, then take a true set-diff —
not just aggregate counts (a count can stay equal while one key is swapped for another).

```sql
-- 1. Snapshot the current key set into a scratch table (or temp view persisted across the re-run)
CREATE OR REPLACE TABLE {table}__idem_snapshot AS
SELECT {Entity}_Key FROM {table};

-- 2. RE-RUN the same load notebook (same input, no source change)

-- 3. Set-diff both directions — BOTH counts MUST be 0 for idempotency to hold
SELECT
  (SELECT COUNT(*) FROM (SELECT {Entity}_Key FROM {table}
                         EXCEPT SELECT {Entity}_Key FROM {table}__idem_snapshot)) AS added_keys,
  (SELECT COUNT(*) FROM (SELECT {Entity}_Key FROM {table}__idem_snapshot
                         EXCEPT SELECT {Entity}_Key FROM {table})) AS dropped_keys,
  (SELECT COUNT(*) FROM {table})                 AS row_count_after,
  (SELECT COUNT(*) FROM {table}__idem_snapshot)  AS row_count_before;
-- Then drop the snapshot: DROP TABLE {table}__idem_snapshot;
```

Expect: `added_keys = 0`, `dropped_keys = 0`, and `row_count_after = row_count_before`. The
`EXCEPT` set-diff catches a swapped key that a `SUM(hash)` fingerprint could mask; the row-count
pair catches duplicate INSERTs even when the key set is unchanged.

- A **second-run failure** with `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`, or a
  **changed row count**, means the `ROW_NUMBER()` dedup PARTITION BY doesn't match the columns that
  build the surrogate key. Fix the notebook (see `deployment-and-dab.md` "MERGE Idempotency for
  Re-Runs") — not the check.
- APPEND_ONLY loads are idempotent only if the `WHEN NOT MATCHED` ON-key + watermark actually
  exclude already-loaded rows; a second run that grows the table by re-inserting is a real bug.
- Record the result (PASS/FAIL) per entity for `build_manifest.md` §8. **A batch does not advance
  until its idempotency recheck passes.**

> **Pre-loaded entities without a load notebook are graded BUILT (not TESTED).**
> `TESTED` requires the idempotency recheck, which re-runs the load — impossible with no
> notebook to re-run. A table that already holds data from a prior session passes the
> single-run DQ checks (→ `BUILT`) but advances to `TESTED` only after a load notebook is
> authored and the full DQ + twice-run idempotency gate runs. See progress-tracking.md
> "Cold Recovery".

---

## Grading Rubric

| Grade | PK Uniqueness | FK Orphan Rate | Key Column Population | Action |
| --- | --- | --- | --- | --- |
| **A** | 100% (0 dups) | ≤ 1% (or documented accepted) | ≥ 95% | ✓ Ready for job — move to next entity |
| **B+** | 100% | ≤ 3% | ≥ 90% | One more fix iteration |
| **B** | ≥ 99% | ≤ 5% | ≥ 90% | Fix before promoting |
| **C** | ≥ 97% | ≤ 10% | ≥ 80% | Multiple issues — revisit source mapping |
| **D** | < 97% | > 10% | ≥ 50% | Major structural issues |
| **F** | PK violations or load failures | > 20% or load failure | < 50% | Fundamental problems — redesign or HUMAN NEEDED |

### Grade Classification Actions

| Classification | When to use | Action |
| --- | --- | --- |
| **FIX** | SQL logic error, wrong column, missing TRY_CAST | Update notebook SQL, re-run, re-grade |
| **ENRICH** | Source data exists but isn't joined yet | Add source join to notebook, re-run |
| **ACCEPT** | Known business exception (documented orphans, expected nulls) | Document justification in progress.md, count as Grade A |
| **HUMAN NEEDED** | Ambiguous business logic, conflicting sources, unclear requirements | Flag for user review, move to next entity |

---

## Validation Gate Notebook

The validation notebook (`src/validate_{layer}.sql`) runs as the **final task** in every DAB job.
It checks ALL entities in a single notebook. If any check fails, it raises an error to fail the job.

### Template

```sql
-- Databricks notebook source
-- =============================================================================
-- Validation Gate: {layer} layer
-- Runs after all entity loads complete
-- Fails the job if any DQ check is violated
-- =============================================================================
-- Runtime-param header (own cells): CREATE WIDGET TEXT silver_catalog/silver_schema;
-- USE CATALOG IDENTIFIER(:silver_catalog); USE SCHEMA IDENTIFIER(:silver_schema);
-- All refs below are unqualified — the job passes catalog/schema via base_parameters.

-- 1. PK uniqueness across all entities
SELECT entity, dup_pks
FROM (
  SELECT '{entity_1}' AS entity, COUNT(*) - COUNT(DISTINCT {Entity1}_Key) AS dup_pks
  FROM {table_1}
  UNION ALL
  SELECT '{entity_2}' AS entity, COUNT(*) - COUNT(DISTINCT {Entity2}_Key) AS dup_pks
  FROM {table_2}
  -- ... repeat for all entities
)
WHERE dup_pks > 0;

-- 2. FK orphans across all fact → dim relationships
SELECT check_name, orphans
FROM (
  SELECT '{fact_1} -> {dim_1}' AS check_name, COUNT(*) AS orphans
  FROM {fact_1} f
  LEFT JOIN {dim_1} d ON f.{Dim1}_Key = d.{Dim1}_Key
  WHERE d.{Dim1}_Key IS NULL
  UNION ALL
  -- ... repeat for all FK relationships
  SELECT 'placeholder' AS check_name, 0 AS orphans
)
WHERE orphans > 0;

-- 3. Key column population
SELECT col, pct_populated
FROM (
  SELECT '{entity_1}.{Key_Col}' AS col,
    ROUND(100.0 * COUNT({Key_Col}) / COUNT(*), 2) AS pct_populated
  FROM {table_1}
  UNION ALL
  -- ... repeat for key columns
  SELECT 'placeholder' AS col, 100.0 AS pct_populated
)
WHERE pct_populated < 95;
```

Note: The validation notebook is intentionally a single SQL statement pattern.
If any result set returns rows, the DQ gate has identified violations.
To FAIL the job on violations, wrap in a conditional that raises an error:

```sql
-- Fail-on-violation pattern (use Python notebook wrapper if needed):
-- Option 1: Let the results speak — monitor via job alerts on non-empty output
-- Option 2: Use a Python wrapper notebook that checks these queries and raises
```

---

## Build Completion Self-Audit (Rule 27)

**Run unprompted from the Finalize session before declaring the build done.** Render the Phase 7
audit table in `SKILL.md` and report a single **"Remaining before handoff"** list. An **empty**
list is the only state that unlocks handoff to `domain-model-validation`. If anything is open
(entity not `TESTED`, no integration test, missing manifest), present the list and stop — do NOT
emit the build manifest as final.

| Closing obligation | Done when |
| --- | --- |
| Every entity `TESTED` | No `etl_state.md` row `NOT_STARTED` or `BUILT`; waves respected |
| DAB bundle authored + deployed | `databricks.yml` + `resources/*.job.yml` deployed cleanly |
| Build manifest emitted | `docs/.pipeline/handoffs/{layer}/build_manifest.md` written |
| Integration test passed | Full job ran end-to-end; validation notebooks passed |
| Root state docs present | `gap_analysis.md` + `data_quality_assessment.md` + `progress.md` current |

---

## Data Quality Assessment Report

After all entities are graded, write `data_quality_assessment.md` to the **project root** (NOT a bare `docs/`):

```markdown
# Data Quality Assessment

## Summary
| Metric | Value |
| --- | --- |
| Total entities | N |
| Grade A | X |
| Grade B | Y |
| HUMAN NEEDED | Z |
| Overall pass rate | X/N (%) |

## Per-Entity Grades
| Entity | Tier | Grade | Iterations | PK Dups | FK Orphan % | Key Pop % | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dim_{a} | 0 | A | 2 | 0 | n/a | 100% | ✓ Done |
| fact_{b} | 1 | A | 3 | 0 | 0.5% | 97% | ✓ Done |
| fact_{c} | 1 | B+ | 4 | 0 | 2.1% | 94% | ▶ Fixing |

## Accepted Exceptions
- {entity}: {description of accepted orphans/gaps and business justification}

## HUMAN NEEDED Items
- {entity}: {description of ambiguity requiring human decision}
```
