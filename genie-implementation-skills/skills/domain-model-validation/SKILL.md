---
name: domain-model-validation
description: Validate and grade a built domain model — the Validate station of the loop. Use when proving a load landed as intended (0 FK orphans, 0 dropped rows, no silent nulls), writing per-table narrative and regression notebooks, establishing drift baselines and regression thresholds, building a quality scorecard and dashboard, onboarding to a built model, or diagnosing why a scheduled run's grades degraded. Runs after etl-development-framework. Not for building ETL or for discovery.
---

# Domain Model Validation Skill

## Overview

This skill produces the **understanding + validation layer** for a completed ETL domain model:
narrative documentation that explains what was built, per-table regression notebooks that
validate data quality, a metadata schema that tracks grades over time, and a dashboard
that surfaces quality and priority to engineering managers.

Designed to run AFTER the `etl-development-framework` skill has built and tested all
entities (Phase 7 integration test passed). Answers: "What exactly was built, and is
the data trustworthy?"

Proven on the Acuity Manufacturing Vibe V2 domain (July 2026). Reusable for any
Acuity domain model built by the ETL Development Framework.

**What this skill produces:**
- `src/silver/validation/narrative_{entity}.sql` — Per-table narrative + regression notebooks (one per entity) *(extension follows etl_language: .sql | .py)*
- `src/silver/validation/scorecard.sql` — Final rollup task that grades all entities and writes results
- Validation metadata tables (sub-tables in the model schema: `_validation_run`, `_validation_table_result`, `_validation_check_detail`, `_data_drift_baseline`, `_gap_registry`)
- DAB validation job (`resources/{domain}_validation.job.yml`, from `templates/validation_job.yml` — per-notebook tasks in load order, scorecard terminal)
- Quality dashboard (4 tabs: current state, trend, priority backlog, integration health)
- `docs/.pipeline/handoffs/silver/validation_summary.md` — Typed validate→document handoff: per-entity grades, resolved/open gap deltas, changed Genie caveats (consumed by `domain-documentation`). **Layer-scoped:** a gold-schema run emits `docs/.pipeline/handoffs/gold/validation_summary.md` in the same typed format (see Phase 5 D6) — the folder split guarantees the two layers' handoffs never collide.
- `docs/.pipeline/handoffs/{layer}/remediation_brief.md` — Structured handoff to ETL skill when grades degrade *(conditionally produced — only when a grade degrades; silver default, gold run → `gold/`)*
- `docs/.pipeline/state/silver/validation_state.md` — Per-entity checkpoint (tier, type, assigned session, `NOT_STARTED→AUTHORED→VERIFIED`) that makes the run resumable + parallelizable; gold run writes `docs/.pipeline/state/gold/validation_state.md` (see Checkpoint & Session Roles)

*Always produced: per-table notebooks + scorecard + metadata tables + job + dashboard +
`docs/.pipeline/handoffs/{layer}/validation_summary.md` + `docs/.pipeline/state/{layer}/validation_state.md`. Conditionally produced: `docs/.pipeline/handoffs/{layer}/remediation_brief.md` (on grade degradation).
The domain-level narrative is NOT produced here — it is owned by `domain-documentation` (the
Explanation quadrant). This skill emits the runnable per-table `narrative_{entity}` regression
notebooks, not the prose domain narrative.*

**Gold / metric-parity mode:** when validating a gold layer with metric views, this skill also
runs **PARITY checks** — comparing each generated metric to the reference value in
`gold_requirements.md` Section 3 (Check_Type = 'PARITY'). See `etl-development-framework/gold-and-metrics.md`.
A parity miss is a HUMAN gate. This is the strongest gold validation: the metric matches the
number the business already trusts.

**Scope:** Read-only validation + metadata writes to `_validation_*` tables only.
Never modifies the model tables themselves. Remediation is escalated to the
`etl-development-framework` skill via structured handoff.

**What this skill validates (and what it does NOT):** This skill asserts **DATA STATE**
(PK/FK/BK/POP/INTEG/DRIFT) against the **live loaded table**. **Idempotency** — whether re-running
a load converges — is owned by `etl-development-framework` as the build-time twice-run recheck on
the real load, and its PASS/FAIL arrives via `docs/.pipeline/handoffs/silver/build_manifest.md` §8 (gold runs read `docs/.pipeline/handoffs/gold/build_manifest.md`). This skill **references**
that result as confidence the load landed as intended; it does **not** re-run loads to test
idempotency. Its own run-over-run stability check (Pattern 1 in `regression-and-drift.md`) is a
data-state drift signal across scheduled runs, a different thing from build-time idempotency.

---

## Reference Files

| File | Content |
| --- | --- |
| `table-narrative-template.md` | Per-table notebook structure — dim variant and fact variant (with star schema integration section) |
| `validation-schema.md` | DDL for 5 metadata tables + INSERT/MERGE patterns for writing results from notebooks |
| `regression-and-drift.md` | Assertion patterns, drift detection logic, threshold config from S2T mapping, baseline management |
| `dashboard-spec.md` | Dashboard layout (4 tabs), dataset queries, widget specifications |
| `remediation-protocol.md` | Grade degradation flow, remediation brief format, ETL skill handoff protocol |
| `templates/validation_job.yml` | Canonical validation-job DAB skeleton (copy → fill; one `resources:` root, `source: WORKSPACE`, tier DAG, scorecard terminal) |

---

## When to Load This Skill

Load when:
- User asks to "validate the model", "understand what was built", "create regression tests"
- User asks for a "narrative" or "documentation" of a completed ETL project
- User wants to "check data quality" or "grade the tables" on an already-built model
- User asks to build a validation dashboard or quality monitoring
- User says "get me up to speed on this data model" or "onboard me"
- A scheduled validation job surfaces degraded grades and user asks "what happened?"
- User wants to establish drift baselines or regression thresholds

Do NOT load for:
- Building DDL or MERGE notebooks — use `etl-development-framework` instead
- Assessing source data or doing discovery — use `domain-model-assessment` instead
- General SQL profiling without a built model — use `data-sampling` instead
- Fixing ETL notebooks directly — escalate via remediation protocol to `etl-development-framework`

---

## Prerequisites

Before this skill can execute, the following must exist:
- A completed ETL project with `progress.md` showing Phase 7 passed (or at minimum Phase 5)
- `docs/.pipeline/handoffs/silver/build_manifest.md` — **required input**, the typed build→validate handoff produced by
  `etl-development-framework` (its final phase); gold runs read `docs/.pipeline/handoffs/gold/build_manifest.md`. Authoritative for per-entity strategy, recency
  column, FK-resolution attribute, filters, accepted exceptions, final row counts, threshold
  seeds, and post-load DQ grade + idempotency-recheck result. Without it, do not reverse-engineer
  intent from MERGE SQL — ask for the manifest.
- DDL notebooks in `src/silver/ddl/` (used to extract schema, FKs, comments)
- S2T mapping report in `docs/design/` (business context; the manifest — not S2T prose — is authoritative for the thresholds actually applied)
- Integration test passing (validates that tables are populated and joinable)

---

## Checkpoint & Session Roles (resumable + parallelizable execution)

**The single biggest scaling failure of this skill is context overflow on a long single session.**
On the Meridian run the session authored all 17 notebooks + scorecard + docs in one pass, hit the
Phase 5 deploy loop, and overflowed — a *second* session had to be opened to produce the handoff
docs, and it had to *infer* what the first session had finished by inspecting the `validation/`
folder and querying `_validation_check_detail`. That recovery is undesigned. This section makes the
skill **resumable** (a fresh session reads a state file instead of guessing) and **parallelizable**
(multiple sessions can own disjoint tiers).

### The checkpoint file — `docs/.pipeline/state/{layer}/validation_state.md`

The **Setup** session writes it (silver runs write `docs/.pipeline/state/silver/validation_state.md`; gold runs write `docs/.pipeline/state/gold/validation_state.md`); every **Batch** session updates its own rows; the **Finalize**
session reads it to confirm completeness. It is the single source of truth for "what's done."

```markdown
# Validation State — {domain}
Updated: {YYYY-MM-DD HH:MM} · Setup run: {run stamp} · Total entities: {N}

| Entity | Tier | Type | Assigned_Session | Notebook_Status | Batch_Notes |
|---|---|---|---|---|---|
| sales_area   | 0 | DIM  | setup      | VERIFIED     | 7/7 PASS, Grade A |
| order_reason | 0 | DIM  | setup      | VERIFIED     | 7/7 PASS, Grade A |
| quotation    | 2 | FACT | session_B  | AUTHORED     | needs Phase 4b coverage gate |
| otd_record   | 7 | FACT | session_C  | NOT_STARTED  | — |
```

- **`Notebook_Status` enum:** `NOT_STARTED → AUTHORED → VERIFIED`. Only the **coverage gate**
  (Phase 4b step 3) may move a row to `VERIFIED` — authoring alone is `AUTHORED`.
- **`Assigned_Session`** is how two sessions avoid authoring the same notebook. A batch session
  only touches rows assigned to it (or unassigned rows it claims by writing its id first).
- Writes are atomic full-file replacements (`readFile` → edit → write back) — never blind-append.

### The three session roles (the 5 phases split by singleton-ness)

Phases 2 (DDL schema) and the scorecard + Phase 5 (dashboard/docs) are **singletons** — they must
run exactly once. Authoring (Phase 3+4b) is the fan-out. So a large domain runs as:

| Role | Runs | Does | Stops when |
|---|---|---|---|
| **Setup** (once) | Phase 1 + Phase 2 | Gather context, create the 5 `_validation_*` tables, seed gaps + drift baselines, **write `docs/.pipeline/state/{layer}/validation_state.md` with every entity `NOT_STARTED` + tier + type + session assignments, reconciled against the deployed schema (Phase 2 step 6 — one row per live model table, not just per manifest entity)** | State file written & reconciled; tables exist |
| **Batch** (1..M, may be parallel) | Phase 3 + 4b for its assigned tiers only | Author ≤4 notebooks/batch, run the coverage gate, flip its rows to `VERIFIED` | All its assigned rows `VERIFIED` |
| **Finalize** (once) | scorecard + Phase 5 | Confirm **every** row is `VERIFIED` **and the row set still matches the live schema** (else stop and report which aren't / which tables are unlisted), run the scorecard, build dashboard, emit `docs/.pipeline/handoffs/{layer}/validation_summary.md` + remediation template | Handoff docs emitted |

- **Setup and Finalize are short** (no notebook authoring) — they never overflow. **Batch sessions
  are bounded** to ≤4–6 entities, well within context limits. This is the structural fix for the
  overflow, independent of whether you actually run sessions in parallel.
- **Single-session runs still use this.** One session plays all three roles in sequence, but writes
  `validation_state.md` at each transition — so if it *does* overflow, the next session resumes from
  the state file instead of re-inferring. Resumability is free once the checkpoint exists.
- **Parallelism is safe because the execution layer already is:** the PENDING→claim write pattern
  means narrative notebooks never collide in the metadata tables (each `DELETE … WHERE Run_Id =
  'PENDING' AND Table_Name = '{entity}'` then inserts only its own rows). The only thing that was
  missing was the *authoring-time* coordination the state file now provides.
- **Finalize is the sole scorecard runner** — never run the scorecard from a batch session (it
  claims ALL PENDING rows; running it early would grade an incomplete set).

> **Sibling skills hit the same wall.** `domain-documentation` overflows at the same entity count;
> the identical `docs/.pipeline/state/run/documentation_state.md` + setup/batch/finalize split applies there. Keep the
> two patterns aligned.

---

## 5-Phase Execution Model

> The 5 phases below are the *work*; the **Checkpoint & Session Roles** section above is *how to
> distribute that work* across resumable/parallel sessions. Setup = Phases 1–2, Batch = Phases
> 3–4b, Finalize = scorecard + Phase 5.

### Phase 1: Gather Context

Read the existing project to extract everything needed for validation generation:

1. **Read `progress.md`** — entity list, grades, row counts, known fixes, configuration
2. **Read DDL notebooks** — extract schema (columns, types, comments, FKs, constraints)
3. **Read `docs/.pipeline/handoffs/silver/build_manifest.md`** (gold runs read `docs/.pipeline/handoffs/gold/build_manifest.md`) — **authoritative** for per-entity strategy (§1), recency
   column (§2), FK-resolution attribute per FK (§3), filters applied (§4), accepted exceptions
   (§5), final row counts (§6), threshold seeds (§7), and post-load DQ grade + idempotency recheck (§8). Do NOT
   reverse-engineer intent by parsing MERGE SQL — the manifest is the as-built mirror the ETL
   skill emitted for exactly this handoff.
4. **Read S2T mapping report** from `docs/design/` — business context, fit grades, known caveats (the manifest §7,
   not S2T prose, is authoritative for the thresholds actually applied)
5. **Read `gap_analysis.md`** — extract unmapped columns, enrichment opportunities
6. **Derive load order** from FK graph (same as ETL: dims Tier 0 → facts last)
7. **Identify known gaps and "why" annotations** — from manifest §5 (accepted exceptions /
   relaxations) + progress.md (constraint relaxations, synthetic keys)
8. **Capture the column contract — `DESCRIBE` every entity you will validate (MANDATORY).** Read
   the manifest §3.5 As-Built Column Inventory if present, then run `DESCRIBE {catalog}.{schema}.{entity}`
   (or query `INFORMATION_SCHEMA.COLUMNS`) against the **deployed** table and store the exact
   physical column names as the check contract for that entity. **Every column any generated check
   SQL references MUST exist in this contract.** Do NOT infer column names from the spec, the S2T
   mapping, the silver source tables, or naming convention — the deployed name is authoritative.

   > 🔴 **This is the #1 validation authoring bug and it is not optional.** The gold-validation run
   > referenced `Material_Number`/`AG_Partner_Number` (silver natural keys) when the deployed gold
   > tables shipped `Material_Key`/`Sold_To_Number` (dimensional renames), costing multiple failed
   > job runs. In **`etl_type: sdp_pipeline` mode there are NO DDL notebooks to read** (step 2 above
   > yields nothing) — the deployed MV/ST is the *only* source of truth for column names, so this
   > `DESCRIBE` step is the sole way to get them right. Run it before authoring any narrative
   > notebook; a manifest §3.5 that disagrees with `DESCRIBE` means the manifest is stale — trust
   > `DESCRIBE`.

**How the manifest seeds the checks (autonomous — no guessing):**
- **FK orphan checks join using the manifest §3 FK-resolution attribute** — the SAME source
  col ↔ dim join attribute the load used (never a re-derived inline SHA2). This carries the
  OEE-bug fix forward instead of rediscovering it.
- **Threshold seeding reads manifest §7** (thresholds as actually set), not "read S2T prose and
  pick a number".
- **Drift baseline seed uses manifest §6 final row counts** as the baseline reference.
- **Accepted exceptions (manifest §5) are annotated and excluded from grading**, and the
  post-load DQ grade + idempotency-recheck result (manifest §8) are cited as build-time confidence
  — this skill does not re-run loads to test idempotency (see "What this skill validates" above).

**Gate (auto-check — verify and proceed):** All N project entities (N = the entity count from the
manifest; Meridian was 17, Acuity manufacturing was 16) identified with schema, FK-resolution
attributes, thresholds, and known issues — all sourced from `docs/.pipeline/handoffs/{layer}/build_manifest.md`, not parsed from MERGE SQL
— **AND every entity has a `DESCRIBE`-derived column contract (step 8)**. Do not begin Phase 3
authoring for an entity whose column contract has not been captured.

### Phase 2: Generate Validation Schema

Create DDL for the 5 metadata tables following `validation-schema.md`:

> **Runtime params (all validation notebooks).** Every generated notebook — the schema DDL,
> each `narrative_{entity}`, and the `scorecard` — opens with the runtime-param header
> (`CREATE WIDGET TEXT silver_catalog/silver_schema` → `USE CATALOG/SCHEMA IDENTIFIER(:...)`)
> and references all tables **unqualified**. Catalog/schema are never baked literals; the
> validation job passes them via `base_parameters` (same DAB variables as the ETL job). See
> `validation-schema.md` "Runtime Parameters".

1. Generate `src/silver/validation/ddl_validation_schema.sql` notebook
2. Run DDL to create tables in the model schema (resolves to `{silver_schema}._validation_run` etc.)
3. Seed `_gap_registry` from S2T mapping (`docs/design/`) + progress.md known gaps. **Seed rows that need `uuid()`
   (or any non-deterministic function) via `INSERT … SELECT`, never `INSERT … VALUES (uuid(), …)`**
   — the VALUES form fails with `INVALID_INLINE_TABLE` (see Critical Databricks SQL Pitfalls §1).
4. Seed `_data_drift_baseline` with current column stats (first run = baseline)
5. **Write `docs/.pipeline/state/{layer}/validation_state.md`** — one row per entity, all `NOT_STARTED`, with tier, type
   (DIM/FACT), and `Assigned_Session` (leave blank for single-session; assign tier ranges when
   fanning out to parallel batch sessions; silver runs write `silver/`, gold runs write `gold/`). This closes the **Setup** role (see Checkpoint &
   Session Roles above).
6. **Reconcile the state file against the deployed schema — MANDATORY. This is the coverage
   denominator.** `validation_state.md` must have one row per table that *actually exists* in the
   model schema — **not** one row per entity named in `progress.md`/the manifest. That list can be
   stale or incomplete, and an entity missing from it is exactly how a deployed table ends up with no
   notebook while the run still reports itself 100% complete. Query the live schema and diff it
   against the rows you just wrote:
   ```sql
   -- Every non-metadata table in the model schema MUST have a validation_state.md row.
   SELECT table_name
   FROM {silver_catalog}.information_schema.tables      -- gold runs: gold_catalog / gold_schema
   WHERE table_schema = '{silver_schema}'
     AND table_name NOT LIKE '\_%' ESCAPE '\'           -- exclude _validation_*, _gap_registry, _data_drift_baseline
     AND table_type <> 'VIEW';                          -- validate physical model tables (drop this line to include views)
   ```
   Any table in this result **without** a `validation_state.md` row → **STOP**: add the missing
   row(s) (`NOT_STARTED`, with tier + type) before closing Setup. The deployed schema is
   authoritative over the handoff docs — the same principle as the Phase 1 step-8 `DESCRIBE` (trust
   the deployment, not the spec). This query is **mode-independent** — it works identically in
   `merge_notebook` and `sdp_pipeline` mode, unlike anything derived from `src/{layer}/ddl/` or
   `transformations/` (which don't exist per-entity under SDP).
7. **Cross-check the deployed schema against `build_manifest.md` §6 (a finding, not a stop).** Diff
   the live table set (step 6) against the manifest's as-built entity list. A table in the manifest
   but **not** deployed is a build-completeness gap (the load never landed); a table deployed but
   **not** in the manifest is orphan/drift. Record either as a `_gap_registry` row (Gap_Type =
   `'BUILD_INCOMPLETE'` / `'UNTRACKED_TABLE'`) and note it in the Setup mini-report — do **not** stop
   (step 6 already guarantees coverage; this only surfaces build/manifest drift the schema-vs-state
   diff can't see on its own).

**Gate (auto-check — verify and proceed):** All 5 tables created and seedable; AND
`docs/.pipeline/state/{layer}/validation_state.md` has one `NOT_STARTED` row for **every non-metadata
table in the deployed model schema** (step 6 reconciliation passed — not merely every entity named in
`progress.md`); AND the step-7 manifest cross-check has been recorded.

### Phase 3: Generate + Verify Per-Table Narrative Notebooks (BATCHED)

> **Batching gate (mandatory — see `autonomous-validation` Batching Discipline).** Do NOT
> author all N narrative notebooks in one pass — that overflows context and produces silent
> column/PENDING errors that only surface when the scheduled job fails. **Author in batches of
> ≤ 4 (grouped by load-order tier), and run + verify each batch (Phase 4b protocol) before
> starting the next.** Phase 3 and Phase 4b are ONE interleaved loop, not two sequential
> phases. After each batch, emit a mini-scorecard and proceed automatically (HITL gate (a)).
>
> **Persist the checkpoint after EVERY batch, not just at the end.** The moment a batch's rows
> flip to `VERIFIED`, write them to `docs/.pipeline/state/{layer}/validation_state.md` **and**
> append a cumulative results line — this is your recovery point if the session is truncated
> mid-run (a real failure mode: 100+ checks across 17 entities overflows context between phases).
> The scorecard reads accumulated results from `_validation_check_detail`, **not** from
> conversation state, so a truncated session loses nothing it has already persisted. Append per
> batch:
> ```
> ## Batch {N} — {date}
> Entities: {list}
> Checks: {pass} PASS / {fail} FAIL / {warn} WARN
> Cumulative: {total_pass}/{total_checks}
> ```
> A state file that was written once at Setup and never updated is a stale-state defect — the next
> session cannot tell what actually completed.

These `narrative_{entity}` notebooks are **validation-owned regression tests** (a runnable,
per-table data-state check that doubles as a per-table read-me). They are distinct from the
domain-level narrative, which is now owned by `domain-documentation` (the Explanation quadrant).

Per batch, group by tier so FK targets exist when facts are validated: dims Tier 0–1 → later
dims → facts. For each entity in the batch, generate `src/silver/validation/narrative_{entity}`
as a **notebook** (NOT a file):

1. Follow dim or fact template from `table-narrative-template.md`
2. Populate markdown cells from DDL comments + manifest §1–§6 (strategy, recency, FK-resolution, filters, exceptions, row counts) + S2T mapping business context
3. Populate SQL assertion cells with thresholds seeded from manifest §7; FK orphan cells join on the manifest §3 FK-resolution attribute. **Every column referenced MUST be in the entity's Phase 1 step-8 column contract** — do not type a column name from memory, the spec, or the silver source; if a check needs a column not in the contract, re-`DESCRIBE` to confirm it exists before authoring (a missing column is an authoring error, not a data finding)
4. For facts: include star schema integration section (join preservation, fan-out, cross-fact)
5. Include "why is it this way?" annotations for any constraint fixes / accepted exceptions (manifest §5) or dedup tricks
6. Final cell ("Write Results"): DELETE stale PENDING rows for this entity, then INSERT results into `_validation_check_detail` with `Run_Id = 'PENDING'` (the PENDING→claim pattern — see Deployment Architecture below)
7. Generate `src/silver/validation/scorecard` notebook — claims PENDING rows, computes grades (including real previous-run deltas — see Rule 28), enforces fail gate. **The claim UPDATE MUST reference its run-id session variable as `session.run_id` (or a `v_`-prefixed name), never bare `run_id`** — a bare name collides with the `Run_Id` column and silently claims 0 rows (Critical Databricks SQL Pitfalls §6). If a scorecard run reports 0 claimed rows with no error, this is the cause.

#### Notebook Creation API Pattern (CRITICAL)

Databricks Jobs require **notebook objects**, not workspace files. Always use:

```
createAsset(assetType='notebook', name='project/path/notebook_name')
```

NEVER use `createAsset(assetType='file')` for job task notebooks — files are not executable by Jobs.

**Workflow to create and populate a notebook** (SQL or Python per `etl_language`):

1. `createAsset(assetType='notebook', name='...')` → returns `assetId`
2. `readAssetById(assetType='notebook', assetId='...')` → get the initial cell's `nuid`
3. `editAsset(operation='update', target=<first_cell_nuid>)` → populate first cell content + set `language` to match `etl_language` — `'SQL'` for the default SQL shape (native SQL notebook), `'PYTHON'` for the Python shape. Do NOT hard-code `'sql'`; a Python-language domain must create Python assets. See `deployment-and-dab.md` "Notebook-format contract".
4. `editAsset(operation='add', target=<first_cell_nuid>)` → add subsequent cells after it (they chain automatically)

#### Write Results Cell Pattern (PENDING→Claim)

Every narrative notebook's final cell follows this exact pattern:

```sql
-- Write validation results to metadata tables
DELETE FROM {schema}._validation_check_detail
WHERE Run_Id = 'PENDING' AND Table_Name = '{entity_name}';

INSERT INTO {schema}._validation_check_detail
SELECT 'PENDING', '{entity_name}', '{check_name}', '{check_type}', ...
```

The DELETE guard makes re-runs safe. The literal `'PENDING'` tag means:
- No temp views required
- No session coupling between notebooks
- Notebooks are fully independent and can run in any order
- The scorecard claims all PENDING rows atomically when it runs last

**Gate (auto-check — verify and proceed):** One notebook per entity + scorecard. All notebooks are actual notebook objects (not files).

### Phase 4: Baseline Run + Validation Job

1. Execute all narrative notebooks once (establishes drift baselines)
2. Verify all results written to metadata tables
3. Generate DAB job YAML (`resources/{domain}_validation.job.yml`) by **copying and filling
   `templates/validation_job.yml`** — do NOT hand-author from scratch (that is how the Meridian
   run ended up with two concatenated `resources:` blocks + two job ids).
   - **First, check for an existing bundle root.** List the project root and look for a
     `databricks.yml` **before** offering to create one — do not conclude "no bundle exists" from a
     keyword search that failed to match the filename (searching for the domain name matches folders,
     not `databricks.yml`). If a `databricks.yml` exists with `include: - resources/*.yml`, the job
     YAML is picked up automatically — just drop it in `resources/` and do nothing else to the root.
     Only author a new `databricks.yml` if the root genuinely has none.

   The template encodes the invariants:
   - Per-notebook tasks in load order (dims first, facts second)
   - Scorecard as final task (depends on all entity tasks)
   - Schedule: configurable (default: daily after ETL job completes; PAUSED until first green load)
   - `source: WORKSPACE` + absolute notebook paths (Rule 17 — validation notebooks are workspace
     objects, not bundle-managed local files)
   - **Exactly ONE `resources:` root and ONE job identity** — see the job-YAML gate below.
   - **If serverless (no `job_clusters`): add a job-level `environments:` block** (`- environment_key: default` / `spec: {client: "1"}`) or the deploy 400s with "Job environment 'default' ... not defined in field 'environments'". Classic `job_clusters` does not need it. See `etl-development-framework/deployment-and-dab.md` "Serverless jobs REQUIRE a job-level environments block".
4. Deploy validation job — **follow the environment-detect→route→handoff contract in
   `etl-development-framework/deployment-and-dab.md` "Deploy is environment-routed" (Step 0).**
   Author is distinct from deploy. On serverless Genie Code compute (the default), the agent does
   NOT deploy: author `resources/validation_job.yml`, `bundle validate` if available, then HAND OFF
   to the workspace Deployments panel (🚀) and tell the user to click Deploy. **The Databricks CLI
   is normally unavailable on serverless compute — `bundle validate`/`deploy` will fail via both
   `runDatabricksCli` and `subprocess`. Do not burn tool calls discovering this: if one CLI probe
   fails, treat the CLI as absent, note "deploy pending — run from the web terminal or local machine"
   in the state file, and hand off.** **NEVER** stand the
   job up via the Jobs API / `editAsset` task-by-task / SDK `w.jobs.create/reset`, **NEVER** shell
   out to `bundle deploy` on serverless, and **NEVER** bounce between the Jobs page and dashboard
   canvas to configure it — that is the loop that overflowed the Meridian run. One clean authored
   YAML + a handoff instruction, then move on.

**Gate (auto-check — verify and proceed):** All notebooks pass. Baseline metrics captured in
`_data_drift_baseline`. **Job-YAML gate:** `resources/validation_job.yml` contains exactly one
top-level `resources:` block and one job identity (no duplicated/concatenated bundle docs, no
mismatched job ids) — grep for `^resources:` and confirm a single match before advancing.

### Phase 4b: Check Your Work — Run and Verify Each Batch

**CRITICAL: This phase was missing in the original implementation and MUST be executed.
It runs PER BATCH inside the Phase 3 loop — not once at the end.**

After generating each batch of ≤ 4 narrative notebooks (Phase 3), you MUST run each one to verify:
1. **SQL syntax is correct** — no typos, invalid column names, or query errors
2. **Results are meaningful** — check passes return data, not empty results
3. **Metadata writes succeed** — `_validation_check_detail` rows are inserted
4. **Cell execution order is correct** — no dependencies on prior cells that don't exist

**Execution protocol (per batch):**
1. Batches are already in load order (dims before facts — Phase 3 groups by tier)
2. For EACH notebook in the batch:
   - Execute all cells sequentially
   - Check for errors in any cell
   - Verify the final "Write Results" cell inserts rows with `Run_Id = 'PENDING'`
   - If any cell fails: diagnose, fix the notebook via `editAsset`, re-run
3. **Run the coverage gate (executable — do NOT eyeball it).** Before closing the batch, run this
   query and assert the mandatory Check_Types are present for every entity in the batch. This is
   the machine enforcement of Rules 23–26 — the first pass "promised but did not produce"
   INTEGRATION on most facts (2/7, then 4/14 on Meridian) precisely because the gate was prose:

   ```sql
   -- Coverage gate: every entity must have BK, POP, DRIFT; every FACT must also have INTEGRATION.
   -- NOTE: _validation_check_detail has NO Table_Type column (that lives in
   -- _validation_table_result, unpopulated until the scorecard). So the gate reports counts by
   -- entity; you supply the batch's fact list (known from DDL/manifest) and assert integ>0 on it.
   SELECT Table_Name,
          SUM(CASE WHEN Check_Type='BK'          THEN 1 ELSE 0 END) AS bk,
          SUM(CASE WHEN Check_Type='POP'         THEN 1 ELSE 0 END) AS pop,
          SUM(CASE WHEN Check_Type='DRIFT'       THEN 1 ELSE 0 END) AS drift,
          SUM(CASE WHEN Check_Type='INTEGRATION' THEN 1 ELSE 0 END) AS integ
   FROM _validation_check_detail
   WHERE Run_Id = 'PENDING' AND Table_Name IN ({batch_entities})
   GROUP BY Table_Name;
   ```

   Any entity with `bk=0`, `pop=0`, or `drift=0` — or any entity **you know is a FACT** (from the
   DDL/manifest) with `integ=0` — **fails the batch**: fix the notebook (`editAsset`) and re-run
   before proceeding. A fact without INTEGRATION rows is falsely-clean; it must NOT be marked done.
4. **Update `docs/.pipeline/state/{layer}/validation_state.md`** — flip this batch's entity rows to `VERIFIED` (only the
   coverage gate may do this) with a one-line Batch_Notes result. This is the checkpoint that lets
   a fresh session resume and lets parallel batch sessions coordinate (see Checkpoint & Session
   Roles). `readFile` → edit rows → write back (atomic full replacement).
5. Emit the batch mini-scorecard (entities done, PASS/FAIL, KNOWN_GAP, + the coverage counts above)
   and proceed to the next Phase 3 batch — do not ask permission (HITL gate (a))
6. After ALL batches pass **and every `validation_state.md` row is `VERIFIED`**, run the scorecard
   notebook (Finalize role only — never from a batch session; it claims ALL PENDING rows)
7. Verify scorecard claims PENDING rows and writes to `_validation_table_result`

**Why this phase is mandatory:**
- Generated SQL often has column name mismatches (e.g., `Description` vs `Gap_Description`)
- UNPIVOT syntax varies between interactive and Job execution contexts
- FK checks may reference wrong key columns
- Without execution verification, the validation job will fail on first scheduled run

**Do NOT skip this phase.** Generating notebooks without running them leaves syntax errors and logic bugs undiscovered until the production job fails. **And do not batch-defer it** — each batch of ≤ 4 must be verified before the next batch is authored (Batching Discipline).

**Gate:** Every batch verified as it was authored; all narrative notebooks execute successfully. Scorecard runs and writes results to metadata tables.

### Phase 5: Dashboard + Remediation Setup + Handoff

> **Finalize-role precondition (auto-check).** Before running the scorecard or building the
> dashboard, read `docs/.pipeline/state/{layer}/validation_state.md` and confirm **every** entity row is `VERIFIED`. If any
> row is `NOT_STARTED`/`AUTHORED`, STOP and report which entities are unfinished — do not run the
> scorecard against an incomplete PENDING set (it claims ALL PENDING rows). This is what lets a
> fresh Finalize session safely pick up after a batch session overflowed.
> **AND re-run the Phase 2 step-6 schema reconciliation** — a table can be deployed *after* Setup
> seeded the state file (a late add, or a hybrid gold star built downstream), and it would have no
> row to be `VERIFIED`. Any non-metadata table in the model schema without a `VERIFIED` row → STOP
> and report it. "Every row `VERIFIED`" is only complete if the row set still matches the live schema.

0. **Schema self-check gate (before touching the dashboard).** Confirm the `_validation_*` tables
   have exactly the columns the template expects. Run once:
   ```sql
   SELECT table_name, column_name
   FROM {silver_catalog}.information_schema.columns
   WHERE table_schema = '{silver_schema}'
     AND table_name IN ('_validation_run','_validation_table_result',
                        '_validation_check_detail','_data_drift_baseline','_gap_registry')
   ORDER BY table_name, ordinal_position;
   ```
   Compare the result against `validation-schema.md` → "Selectable columns per table
   (authoritative)". **Match → import the template.** **Mismatch → STOP and report which
   table/column diverged** (the scorecard DDL is wrong, not the dashboard). Do NOT guess-and-rewrite
   dataset SQL — that was the field-service overflow loop this gate exists to prevent.

1. Generate the quality dashboard by **adapting the shipped template** — see
   `dashboard-spec.md` "Dashboard Generation Protocol (adapt the shipped template)":
   load `templates/validation_dashboard.lvdash.json`, replace `{silver_catalog}`/`{silver_schema}`,
   import as `{Domain} Validation Quality`, publish. The 4 tabs and 7 datasets come from the
   template — do not author them from scratch or re-derive column names.
   - **A persistent dashboard ASSET — never an inline chart.** The dashboard MUST end up as a
     saved, published dashboard asset. **NEVER use `renderChartV2` (or any inline-chart tool) —
     it renders a one-off preview into the conversation thread, not into a dashboard asset**, and
     leaves nothing for the user to open later. Two acceptable mechanisms, in order:
     (a) **preferred** — if a dashboard-import primitive is available, import
     `templates/validation_dashboard.lvdash.json` (token-swapped) directly as a new dashboard;
     (b) **otherwise** — `createAsset(assetType='dashboard', name='{Domain} Validation Quality')`
     → `openAsset` to navigate onto it → `editDataset` (one per template dataset) +
     `simpleCreateWidget` (one per template widget) → `publishDashboard`. In both cases the shipped
     template JSON is the authoritative source for datasets, widget layout, and column names — you
     are reproducing it as an asset, not re-designing it.
   - **Author, don't thrash.** Build all datasets + widgets on the dashboard canvas you are on;
     if a needed operation (e.g. `editAsset`) is only available on a different tool surface, do
     NOT ping-pong back and forth (this was the Meridian overflow loop). Author the artifact once
     on the surface you have, and if a surface is genuinely unavailable, record the dashboard
     definition to the repo and emit a one-line handoff for the user — never re-navigate more than
     once for the same artifact. Deploy/publish follows the same detect→route→handoff contract as
     the job (`etl-development-framework/deployment-and-dab.md` "Deploy is environment-routed").
2. Generate `docs/.pipeline/handoffs/{layer}/remediation_brief.md` template (silver default; gold run → `docs/.pipeline/handoffs/gold/remediation_brief.md`)
3. Configure remediation flow: if any entity drops below Grade B → generate the populated remediation brief at `docs/.pipeline/handoffs/{layer}/remediation_brief.md` (the path from step 2)
4. **Emit the typed validate→document handoff (D6) to `docs/.pipeline/handoffs/{layer}/validation_summary.md`** (silver → `handoffs/silver/`, gold → `handoffs/gold/`). This small markdown is the input
   `domain-documentation` reads to regenerate Genie caveats and Model Guide health, so it does not
   re-read `progress.md` + `_gap_registry` raw. Contents:
   - **Per-entity grades** (current run) — entity, grade, and the manifest's build-time grade
     for continuity (a table that was A at build should still be A if nothing changed).
   - **Gap deltas** — resolved vs. still-open gaps since the last run, each with the standardized
     status enum `OPEN | IN_PROGRESS | DEFERRED | ACCEPTED | RESOLVED` (from `_gap_registry`).
   - **Changed Genie caveats** — which known-gap caveats a consumer-facing Genie space should
     add/drop this run (e.g. a resolved P0 FK gap removes its "cannot drill to routing" caveat).
   - Header stamp so `domain-sync` staleness linting can tell when it was produced.

   **Path is layer-scoped — the folder split guarantees the two layers' handoffs never collide:**
   - Validating a **silver** schema → `docs/.pipeline/handoffs/silver/validation_summary.md`.
   - Validating a **gold** schema (the second run of a `hybrid` domain, or a standalone gold/
     `dimensional` model) → `docs/.pipeline/handoffs/gold/validation_summary.md`. **It uses the SAME typed format as the
     silver summary** — per-entity grade table, gap deltas, changed caveats, header stamp. It is NOT a
     progress checklist. A hybrid domain runs this skill twice (once per schema), producing both files;
     the documentation skill reads whichever it needs. Emitting the gold handoff as a "remaining steps"
     tracker instead of the typed format is a defect — `domain-documentation` cannot parse grades from it
     and must fall back to `docs/.pipeline/state/gold/validation_state.md`.

**Gate (auto-check — verify and proceed):** Dashboard deployed. Remediation template in place. The
layer-scoped summary (`docs/.pipeline/handoffs/silver/validation_summary.md` for silver, `docs/.pipeline/handoffs/gold/validation_summary.md` for gold) is
emitted **in the typed format** with per-entity grades + gap deltas + changed caveats — not left as a
progress checklist.

#### Phase 5 Implementation Guide (Proven Pattern)

**Dataset strategy:** Use raw SQL datasets (not metric views) for validation metadata tables — they are simple lookups/joins, not aggregation-heavy analytical models.

**Datasets + widgets:** fixed by `templates/validation_dashboard.lvdash.json` (7 datasets:
`validation_run`, `gap_registry`, `table_result`, `check_detail`, `current_summary`,
`scorecard`, `integration_checks`). Do not re-derive them here.

**Widget layout:** fixed by `templates/validation_dashboard.lvdash.json` (4 tabs). Do not
restate the per-tab widget breakdown here — the template is the authoritative layout.

**Known gotchas from production deployment:**

1. **`_validation_check_detail` empty until job runs** — The PENDING→claim pattern means check_detail rows only exist after the scorecard claims them. On a fresh dashboard with no prior job run, this table is empty. Don't filter by Run_Id JOIN _validation_run unless you've confirmed rows exist.

2. **Stale `loadState: error` after fixing SQL** — Dashboard dataset cache may show errors from a previous query version even after the SQL is corrected. Use `refreshData` and re-touch the dataset (`editDataset` with identical SQL) to force re-execution.

3. **Warehouse cold-start** — First render after creating all widgets often times out (15s poll). This is normal — the SQL warehouse needs to warm up. Retry verification after a pause.

4. **Counter widgets for KPIs** — Use `disaggregatedData: true` with a single-row dataset. Counter encodings: `{ value: { fieldName } }` — no period encoding needed for non-temporal counters.

5. **Bar charts for gap breakdown** — Use `disaggregatedData: false` with `COUNT(*)` expression. X = categorical dimension (Priority or Status), Y = count measure.

**Dashboard naming + tab titles:** authoritative in `dashboard-spec.md` (canonical banner) —
`{Domain} Validation Quality`, tabs Current State / Historical Trend / Priority Backlog /
Integration Health. Do not restate divergent names here; use those exact labels.

---

## Grading Rubric (Aligned with ETL Framework)

> **This table is the human-readable view of the grading algorithm; the authoritative,
> executable form is `validation-schema.md` Pattern 4 (the scorecard CASE).** They must stay in
> step. Two edge cases live in Pattern 4, not the table: a **declared-empty** entity (manifest §5)
> is not F'd for 0 rows, and all FK/PK metrics are computed **after excluding accepted-exception
> orphans** (`Is_Accepted_Exception = TRUE`) so a documented gap never drags the grade down.

| Grade | PK Uniqueness | FK Orphan Rate | Key Column Population | Drift Status | Action |
| --- | --- | --- | --- | --- | --- |
| **A** | 100% (0 dups) | ≤ 1% (or documented accepted) | ≥ 95% | Within baseline tolerance | ✓ Healthy |
| **B+** | 100% | ≤ 3% | ≥ 90% | Minor drift (1 metric) | Monitor — one more run |
| **B** | ≥ 99% | ≤ 5% | ≥ 90% | Moderate drift | Investigate within 24h |
| **C** | ≥ 97% | ≤ 10% | ≥ 80% | Multiple drift alerts | Escalate — generate remediation brief |
| **D** | < 97% | > 10% | ≥ 50% | Severe drift | Urgent — block promotion |
| **F** | PK violations or 0 rows | > 20% or table missing | < 50% | Baseline missing or catastrophic | Critical — immediate investigation |

### Grade Actions (Ongoing Monitoring)

| Grade | Automated Action |
| --- | --- |
| A | No action. Write to history. |
| B+ | Write to history. Dashboard shows amber. |
| B | Generate alert. Dashboard shows amber. |
| C | Generate remediation brief. Dashboard shows red. Notify eng manager. |
| D | Block prod promotion gate. Dashboard shows red. |
| F | Fail validation job. Trigger immediate alert. |

---

## Critical Rules (Always Apply)

1. **Read `progress.md` before generating anything** — it seeds the initial entity list, grades, fixes, and configuration. **But the deployed model schema — not `progress.md` — is the authoritative set of tables to validate** (Phase 2 step 6): a table missing from `progress.md`/the manifest still gets a notebook. Reconcile the state file against `information_schema.tables` at Setup and again at Finalize.
2. **Never modify model tables** — this skill is read-only against the dimensional model. Only writes to `_validation_*` metadata tables.
3. **Thresholds seed from S2T mapping** — never guess thresholds. If S2T mapping has "FK orphan rate 8% expected (cross-system gap)", set threshold to 10%, not 1%.
4. **Known gaps are NOT failures** — if progress.md documents an accepted exception (e.g., "8 Oracle orgs not in dim_plant"), the narrative notebook must annotate this and exclude from grading.
5. **"Why is it this way?" is mandatory** — every constraint relaxation, synthetic key, or dedup trick documented in progress.md MUST appear as an annotation in the relevant notebook.
6. **One notebook per table** — never combine multiple entities. Mirrors ETL framework convention.
7. **Load order for execution** — dims before facts, so FK checks have fresh data to validate against.
8. **Baseline on first run only** — drift baselines are set once and frozen until manually reset. Never auto-update baselines (that defeats drift detection).
9. **Remediation goes through ETL skill** — never attempt to fix MERGE notebooks from this skill. Generate the remediation brief and hand off.
10. **Dashboard queries read from metadata tables** — never query the model tables directly from the dashboard. The validation notebooks do the querying; the dashboard reads results.
11. **Grade continuity** — use the same A-F rubric as the ETL framework's `testing-and-grading.md`. A table that was Grade A at build time should remain Grade A if nothing changed.
12. **Notebooks, not files** — all generated artifacts MUST use `createAsset(assetType='notebook')`. NEVER `createAsset(assetType='file')` for anything that needs to run as a Job task. The `.sql` extension in paths is optional; notebooks created via the API don't need extensions.
13. **Pascal_Snake_Case for metadata tables** — validation table columns use the same naming standard as the model.
14. **Dual-purpose notebooks** — every narrative notebook is BOTH a readable onboarding document AND a runnable regression test. Design for both audiences.
15. **PENDING→claim for run correlation** — narrative notebooks write `Run_Id = 'PENDING'`; the scorecard claims them. Never use temp views for cross-notebook state. This enables full parallelism in the validation job.
16. **DELETE guard before INSERT** — every Write Results cell starts with `DELETE FROM ... WHERE Run_Id = 'PENDING' AND Table_Name = '{entity}'` to make re-runs idempotent.
17. **DAB uses `source: WORKSPACE`** — validation notebooks are workspace objects (not local bundle files), so the job YAML must specify `source: WORKSPACE` with absolute paths. Without this, DAB fails looking for local files with extensions.
18. **BK Null Check is mandatory** — every narrative notebook MUST include a `BK_Null_Check` cell that validates natural key columns (and critical NOT NULL business attrs) for NULL and empty-string values. Check_Type = 'BK'. NK columns use 0% threshold (FAIL on any NULL). STRING columns also check `TRIM(col) = ''` to catch empty-string surrogates for NULL. Always exclude the Unknown member row (`WHERE {Entity}_Key != -1`).
19. **BK column identification** — extract NK columns from the DDL COMMENT on the surrogate key (e.g., "SHA2 of Plant_Code" → NK = Plant_Code). For composite keys, ALL components must be checked. When no NK column is exposed (source PK used internally), check critical NOT NULL business attributes instead.
20. **Empty-string detection** — STRING NK columns must check BOTH `IS NULL` and `TRIM(col) = ''`. Empty strings bypass NOT NULL constraints but produce invalid SHA2 hashes and indicate dropped data. BIGINT/INT/DATE columns only need `IS NULL`.
21. **Data Profile is mandatory** — every narrative notebook MUST include a "Data Profile — Shape & Coverage" cell that quantifies the table's scope (row count, dimension cardinality, date range, measure distributions). Tailor to entity type: dimensions show active/inactive splits and hierarchy coverage; facts show date span, measure stats (min/avg/max), and edge-case counts. Always include `Last_Load` for freshness.
22. **Sample Rows is mandatory** — every narrative notebook MUST include a "Sample Rows — Representative Records" cell showing curated data (typical rows PLUS edge cases that explain design annotations). Use UNION ALL for facts to combine typical + edge-case samples. Select meaningful columns (not all 20+ audit columns).
23. **POPULATION check is mandatory** — every narrative notebook MUST include a `POPULATION` cell (Check_Type = 'POP') measuring non-null coverage of key business columns vs. the threshold from S2T mapping. The scorecard's `key_pop_pct` grade logic reads this; without it, population is silently NULL→100% and the B/B+/C thresholds never fire. First pass shipped POP in only 2 of 16 notebooks — this rule closes that.
24. **INTEGRATION check is mandatory for EVERY fact** — every fact narrative MUST include the star-schema integration cells (Check_Type = 'INTEGRATION'): join preservation (row count survives the dim joins), fan-out check (joins don't multiply rows), and cross-fact consistency where applicable. First pass shipped INTEGRATION in only 2 of 7 facts, producing a falsely-clean dashboard. A fact without INTEGRATION cells is incomplete — do not mark its batch done.
25. **DRIFT check is mandatory when a baseline exists** — every narrative notebook MUST include a `DRIFT` cell (Check_Type = 'DRIFT') comparing current column stats to `_data_drift_baseline`. The scorecard reads `Check_Type='DRIFT'`; if no notebook writes DRIFT rows, `drift_count` is permanently 0 and the whole drift subsystem is dead code (as in the first pass). On the first run (baseline being established) the cell writes the baseline and reports DRIFT=BASELINE; subsequent runs compare.
26. **These checks are enforced at the batch gate** — the Phase 4b per-batch verification MUST confirm each notebook wrote BK, POP, FK (facts), INTEGRATION (facts), and DRIFT rows. A notebook missing a mandatory Check_Type fails its batch and is fixed before proceeding. This is how "promised but not produced" checks are prevented from silently vanishing.
27. **Cell ordering** — canonical order: (1) Narrative markdown, (2) Row Count/PK, (3) FK checks, (4) BK Null Check, (5) POPULATION, (6) INTEGRATION (facts), (7) DRIFT, (8) Data Profile, (9) Sample Rows, (10) Write Results. Profile and Sample go AFTER validation checks and BEFORE Write Results.
28. **Regression deltas are computed, never stubbed** — the scorecard MUST compute `Row_Count_Delta` and `Grade_Delta` for each entity against the immediately previous run (the latest existing `_validation_run` row **by `Run_Timestamp`** — NOT `MAX(Run_Id)`, since `Run_Id` is a `uuid()` string whose max is random; the current run's row is written last so it isn't yet present), using the delta pattern in `regression-and-drift.md`. Stubbing (`AS 0`, `NULL AS ..._Delta`, or hard-coding `'NEW'`) is FORBIDDEN except on the genuine first run, when no prior `_validation_run` row exists — only then is `Grade_Delta = 'NEW'` and `Row_Count_Delta = NULL` correct. Otherwise the trend tab and remediation detection (Grade degradation) are dead.
29. **Validation asserts data state; build-time load correctness is ETL-owned** — this skill checks PK/FK/BK/POP/INTEG/DRIFT against the live loaded table. It never re-runs loads to test idempotency. That is `etl-development-framework`'s build-time twice-run recheck on the real load; its PASS/FAIL arrives via `docs/.pipeline/handoffs/{layer}/build_manifest.md` §8 and is cited as confidence, not re-run here.
30. **`docs/.pipeline/state/{layer}/validation_state.md` is the checkpoint of record** — Setup writes it (every entity `NOT_STARTED`), only the Phase 4b coverage gate flips a row to `VERIFIED`, and Finalize refuses to run the scorecard until all rows are `VERIFIED`. A batch session touches only its assigned rows. This is what makes the run resumable after overflow and safe to fan out across parallel sessions — never run the scorecard from a batch session (it claims ALL PENDING rows). See Checkpoint & Session Roles.
31. **Deploy is detect→route→handoff, never a retry loop** — the job and dashboard deploy via the environment-detection contract in `etl-development-framework/deployment-and-dab.md` "Deploy is environment-routed" (Step 0). On serverless Genie Code the agent authors YAML/dashboard and HANDS OFF to the Deployments panel; it NEVER shells out to `bundle deploy` on serverless, NEVER reconstructs bundle resources via Jobs API/SDK, and NEVER ping-pongs between the Jobs page and dashboard canvas. One clean authored artifact + a handoff line, then move on.

---

## Deployment Architecture: PENDING→Claim Pattern

The validation suite uses a **stateless decoupled architecture** where narrative notebooks
and the scorecard have zero session dependencies:

### How It Works

1. **Narrative notebooks** write check results with `Run_Id = 'PENDING'` (literal string)
2. Each notebook first DELETEs its own stale PENDING rows (safe re-run guard)
3. **Scorecard** runs LAST:
   - Generates a UUID: `DECLARE OR REPLACE VARIABLE run_id STRING DEFAULT uuid();`
   - Claims all PENDING rows: `UPDATE ... SET Run_Id = session.run_id WHERE Run_Id = 'PENDING'` (`session.` prefix required — Pitfall §6)
   - Computes grades from the claimed rows
   - Writes to `_validation_table_result` and `_validation_run`
   - Enforces fail gate (RAISE_ERROR if any Grade D/F)

### Why This Pattern (Not Temp Views)

| Concern | Temp View Pattern | PENDING→Claim Pattern |
| --- | --- | --- |
| Session coupling | Requires shared session (%run) | Fully independent |
| Parallelism | Sequential only | All narrative tasks run in parallel |
| Re-runnability | Temp view lost on error | DELETE guard makes re-runs safe |
| Job design | Single orchestrator notebook | N parallel tasks + 1 scorecard |
| Debugging | Must run full chain | Run individual notebooks anytime |

### Scorecard Cell Structure (5 cells)

1. **Claim PENDING** — `DECLARE VARIABLE run_id`, `DECLARE VARIABLE run_ts`, UPDATE check_detail
2. **Compute Grades** — INSERT into `_validation_table_result` with grade logic. **`Row_Count_Delta`
   and `Grade_Delta` MUST be computed here via the Previous-Run Delta CTE in `regression-and-drift.md`
   Pattern 1 — join to the latest prior `_validation_run` row by `Run_Timestamp` (NOT `MAX(Run_Id)`).**
   Do NOT emit `0 AS Row_Count_Delta` / `NULL AS Grade_Delta` literals (the Meridian scorecard did
   exactly this — Rule 28 violation — which kills the trend tab and degradation detection from run 2
   on). The ONLY sanctioned stub is the genuine first run (no prior `_validation_run` row): then
   `Grade_Delta='NEW'` and `Row_Count_Delta=NULL` are correct. Branch on prior-run existence; never
   hard-code the literals unconditionally.
3. **Display** — SELECT scorecard for human review
4. **Write Run Summary** — INSERT into `_validation_run` (aggregate stats)
5. **Fail Gate** — RAISE_ERROR if any Grade D or F

> **Anti-stub gate (auto-check after the scorecard runs).** If more than one `_validation_run` row
> now exists (i.e. this was NOT the first run), confirm `_validation_table_result` for the current
> `run_id` has non-NULL `Row_Count_Delta` and a `Grade_Delta` in `IMPROVED|STABLE|DEGRADED` for
> entities that also existed last run. All-`NULL`/all-`0`/all-`'NEW'` on a non-first run means the
> delta CTE was stubbed — fix before advancing.

### Race Condition Note

A small race window exists if two scorecard runs overlap (both claim the same PENDING rows).
In practice this never happens with `max_concurrent_runs: 1` on the validation job.
For extra safety, the scorecard could use a transaction or check that claimed row count > 0.

### Orchestrator Notebook (Optional)

The `run_validation` notebook provides a `%run`-based single-session alternative for
manual/interactive execution. It's NOT required for the job (the job uses parallel tasks).
Useful for local debugging: run all notebooks sequentially in one session without deploying.

---

## Critical Databricks SQL Pitfalls

### 1. `uuid()` Cannot Be Used in VALUES Clause

```sql
-- FAILS: INVALID_INLINE_TABLE.CANNOT_EVALUATE_EXPRESSION_IN_INLINE_TABLE
INSERT INTO table VALUES (uuid(), 'data');

-- WORKS: Use INSERT...SELECT instead
INSERT INTO table
SELECT uuid(), t.* FROM (SELECT 'data' AS col) t;
```

### 2. Multi-Statement Cells (DELETE + INSERT)

Databricks SQL notebook cells support multiple statements separated by `;`.
The Write Results cell uses this: DELETE (guard) then INSERT (data).

### 3. UNPIVOT Aliases Must Be Identifiers (Not Strings)

```sql
-- FAILS in Job context: single-quoted strings are not identifiers
UNPIVOT (val FOR col IN (Plant_Code_nn AS 'Plant_Code'))

-- WORKS: use unquoted identifiers
UNPIVOT (val FOR col IN (Plant_Code_nn AS Plant_Code))
```

This passes interactively but fails in Job execution. Always use unquoted or backtick-quoted identifiers.

### 4. Scorecard Must Be Idempotent (DELETE Before INSERT)

Jobs may retry failed tasks. The scorecard's grade computation cell MUST include:
```sql
DELETE FROM _validation_table_result WHERE Run_Id = session.run_id;  -- session. prefix (Pitfall §6): bare run_id → Run_Id = Run_Id → deletes ALL history
INSERT INTO _validation_table_result ...
```
Without this, retries create duplicate rows (e.g., 3×N entities instead of N). **Use `session.run_id`,
not bare `run_id`** — a bare name binds to the `Run_Id` column, making the predicate always true and
deleting every historical run instead of just the current one (Pitfall §6).

### 5. Accepted Exceptions Exclude from Grading

The scorecard filters on `Is_Accepted_Exception = FALSE` when computing grades:
```sql
MAX(CASE WHEN Check_Type = 'PK' AND Is_Accepted_Exception = FALSE
    THEN CAST(Actual_Value AS BIGINT) END) AS pk_dups
```
Pre-existing ETL dedup gaps should be marked `Is_Accepted_Exception = TRUE` with a reason string.
This prevents Grade F for known issues while still recording them in check_detail.

### 6. DECLARE VARIABLE Scope — and the session-variable ↔ column-name collision

Session variables declared with `DECLARE OR REPLACE VARIABLE` persist across cells
in the same notebook session. They replace temp views for cross-cell state:
- Lighter weight (no catalog resolution)
- Same session scope as temp views
- Can be referenced in any subsequent cell

🔴 **Collision trap (caused a silent scorecard no-op in the gold-validation run).** When a bare
variable name matches a **column** in the target of a DML statement (case-insensitive), the
**column wins** — Databricks resolves the identifier to the column, not your variable. The
scorecard's `DECLARE OR REPLACE VARIABLE run_id` collided with the `Run_Id` column, so
`UPDATE ... SET Run_Id = run_id` set the column *to itself* and silently claimed **zero** PENDING
rows — no error, just an empty scorecard. Two defenses (apply BOTH):
- **Prefix every session-variable reference with `session.`** in any DML (`UPDATE`/`DELETE`/`INSERT … SELECT`)
  that has a `FROM`/target introducing a same-named column: `SET Run_Id = session.run_id`, `WHERE Run_Id = session.run_id`.
- **Name variables so they cannot collide** — use a `v_` prefix (`DECLARE OR REPLACE VARIABLE v_run_id …`)
  that no validation/model column will ever match, and still reference as `session.v_run_id`.

The scorecard and remediation notebooks (`DECLARE OR REPLACE VARIABLE run_id` — see
`validation-schema.md` Pattern 2, `table-narrative-template.md`, `remediation-protocol.md`) must
follow this. A scorecard that "runs clean" but claims 0 rows is this bug, not a data condition.

### 7. Reserved-Word Entity Names (`order`, `group`, `user`, …)

An entity whose physical name is a SQL reserved word (the sales-order domain has `order`) needs
**backtick-escaping only where it is a table reference**, and must be stored **without backticks**
as a string literal in metadata tables:
- **Table references** in check SQL: escape — `` SELECT COUNT(*) FROM `order` ``.
- **Metadata string columns** (`_validation_check_detail.Table_Name`, `_data_drift_baseline.Table_Name`,
  `_gap_registry.Table_Name`): store the **bare name** `'order'`, NOT `` '`order`' ``. Storing the
  backticks inside the string makes every downstream `WHERE Table_Name = 'order'` filter miss, and
  forces fragile `` WHERE Table_Name = '`order`' `` clauses. Backticks are an *identifier-quoting*
  mechanism, not part of the name — they never belong inside a string literal.
- The drift-baseline seed and the scorecard's per-entity claim (`WHERE Table_Name = '{entity}'`)
  therefore use the bare name; only the `FROM {entity}` / `DESCRIBE {entity}` references escape it.

Detect reserved-word entities from the Phase 1 column contract step and apply this consistently
across all generated notebooks for that entity.

---

## Folder Ownership (ARCHITECTURE.md — owned by domain-sync)

`ARCHITECTURE.md` at the project root is generated and maintained by `domain-sync`. This skill's artifacts occupy the following paths within that ownership map:

| Folder / File | Skill Owner | Contents |
| --- | --- | --- |
| `src/silver/ddl/` | etl-development-framework | CREATE TABLE DDL notebooks |
| `src/silver/transformations/` (load notebooks) | etl-development-framework | Type 1 MERGE load notebooks |
| `src/silver/validation/` | **domain-model-validation** | Per-table regression narratives + scorecard |
| `docs/design/` | domain-model-assessment | S2T mapping, readiness summaries, design record |
| `docs/.pipeline/handoffs/silver/build_manifest.md` | etl-development-framework | Typed build→validate handoff (silver) |
| `docs/.pipeline/handoffs/gold/build_manifest.md` | etl-development-framework | Typed build→validate handoff (gold) |
| `docs/.pipeline/handoffs/silver/validation_summary.md` | **domain-model-validation** | Typed validate→document handoff (silver) — emitted here, read by docs |
| `docs/.pipeline/handoffs/gold/validation_summary.md` | **domain-model-validation** | Typed validate→document handoff (gold) — same format as silver |
| `docs/.pipeline/handoffs/{layer}/remediation_brief.md` | **domain-model-validation** | Structured ETL handoff when grades degrade (conditionally produced) |
| `docs/.pipeline/state/silver/validation_state.md` | **domain-model-validation** | Per-entity checkpoint (resume + parallel-session coordination) — Setup writes, Batch updates, Finalize reads |
| `docs/.pipeline/state/gold/validation_state.md` | **domain-model-validation** | Same checkpoint for gold-layer runs |
| `docs/explanation/domain_narrative.md` | domain-documentation | Domain-level Explanation narrative (owned by docs, NOT validation) |
| `resources/` | etl-development-framework + domain-model-validation | DAB job YAML files (ETL job + validation job) |

---

## Interaction with Other Skills

### Reads from `domain-model-assessment` outputs:
- S2T mapping report (fit grades, gap registry seed, business context)
- Integration assessment (known cross-system boundaries)
- Discovery brief (business context)

### Reads from `etl-development-framework` outputs:
- `docs/.pipeline/handoffs/{layer}/build_manifest.md` — **the typed build→validate seam** (required input): per-entity
  strategy, recency column, FK-resolution attribute, filters, accepted exceptions, final row
  counts, threshold seeds, and post-load DQ grade + idempotency-recheck result. Authoritative —
  validation does NOT parse MERGE SQL to reconstruct intent.
- `progress.md` (entity list, grades, row counts, fixes, configuration)
- DDL notebooks (schema, FKs, constraints, comments)
- `gap_analysis.md` (unmapped columns)
- `validate_silver.sql` (existing lightweight DQ gate — this skill supersedes it for comprehensive checks; when `etl_type: sdp_pipeline` there is no `validate_silver` notebook — DQ lives in inline `CONSTRAINT … EXPECT` read from the pipeline event log, but this skill still validates data state against the materialized silver tables via `docs/.pipeline/handoffs/{layer}/build_manifest.md`, dialect-agnostically)

### Hands off to `etl-development-framework`:
- Remediation briefs (when grades degrade below B)
- Structured as: table name, failing checks, threshold vs actual, suggested root cause, priority

### Hands off to `domain-documentation`:
- `docs/.pipeline/handoffs/{layer}/validation_summary.md` — **the typed validate→document seam**: per-entity grades,
  resolved/open gap deltas (standardized status enum), and changed Genie caveats. Docs reads
  this to regenerate Genie caveats + Model Guide health rather than re-reading `progress.md` +
  `_gap_registry` raw. The domain-level Explanation narrative is authored in `domain-documentation`,
  not here.

---

## Configuration (Inherited from ETL Project)

The validation skill reads configuration from the ETL project's `progress.md` and Kickoff widgets:

| Parameter | Source | Used For |
| --- | --- | --- |
| `silver_catalog` | progress.md Configuration | Target schema for metadata tables |
| `silver_schema` | progress.md Configuration | Schema containing model + validation tables |
| Entity list | **`information_schema.tables` (authoritative)**, seeded from progress.md Entity Status | Which tables to generate notebooks for — reconciled against the deployed schema at Setup + Finalize (Phase 2 step 6) |
| Load order | progress.md Load Order | Execution sequence for validation job |
| Known fixes | progress.md Fixes Applied + manifest §5 | "Why" annotations in narrative notebooks |
| Thresholds | `docs/.pipeline/handoffs/{layer}/build_manifest.md` §7 | FK orphan rate + population thresholds per entity (as actually set) |
| FK-resolution attributes | `docs/.pipeline/handoffs/{layer}/build_manifest.md` §3 | How each FK orphan check joins (same as the load) |
| `etl_language` | conventions.yml / progress.md | Notebook shape for generated validation notebooks (SQL vs Python) |
| Job schedule | Configurable | Default: daily, after ETL job window |
