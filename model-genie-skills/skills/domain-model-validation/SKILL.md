---
name: domain-model-validation
description: Validate and grade a built domain model — the Validate station of the loop. Use when proving a load landed as intended (0 FK orphans, 0 dropped rows, no silent nulls), writing per-table narrative and regression notebooks, establishing drift baselines and regression thresholds, building a quality scorecard and dashboard, onboarding to a built model, or diagnosing why a scheduled run's grades degraded. Runs after etl-development-framework. Not for building ETL or for discovery.
---

# Domain Model Validation Skill

> **⚙️ Load `autonomous-validation` alongside this skill — it is NOT pulled in automatically; nothing wires the two together, so load it explicitly at the session start — it also hosts `commentary-protocol.md`, the closeout this skill emits.** (See its `When to Load` for the execution-discipline contract.)
> This skill authors and runs a regression notebook per entity plus the singleton scorecard, so the batching gate (referenced below) and the Validation Completion Self-Audit (Critical Rule 32) depend on it.

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
- `docs/commentary/validation-improvement-recommendations.md` — Skill-improvement commentary emitted at closeout per `autonomous-validation/commentary-protocol.md` (always produced; prior items folded forward)

*Always produced: per-table notebooks + scorecard + metadata tables + job + dashboard +
`docs/.pipeline/handoffs/{layer}/validation_summary.md` + `docs/.pipeline/state/{layer}/validation_state.md` + `docs/commentary/validation-improvement-recommendations.md`. Conditionally produced: `docs/.pipeline/handoffs/{layer}/remediation_brief.md` (on grade degradation).
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
| `phase-protocol.md` | **Detailed 5-phase execution** — full per-step protocol for Phases 1–5, the PENDING→Claim deployment architecture, and the Critical Databricks SQL Pitfalls. `SKILL.md` carries the phase summary; this is the how-to. |
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

> Phase numbers below map to the summary table under **5-Phase Execution Model** and the full
> per-step protocol in `phase-protocol.md`.

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

## 5-Phase Execution Model (summary — full protocol in `phase-protocol.md`)

> The 5 phases are the *work*; **Checkpoint & Session Roles** above is *how to distribute it*
> across resumable/parallel sessions. Setup = Phases 1–2, Batch = Phases 3–4b, Finalize =
> scorecard + Phase 5. **The full per-step protocol — plus the PENDING→Claim deployment
> architecture and the Critical Databricks SQL Pitfalls the steps depend on — lives in
> `phase-protocol.md`.** Every "Phase N", "Deployment Architecture", and "Pitfall §N" reference
> elsewhere in this file resolves there.

| Phase | Role | Does | Gate (auto-check unless noted) |
|---|---|---|---|
| **1 · Gather Context** | Setup | Read `progress.md`, DDL, `build_manifest.md` (authoritative for strategy/recency/FK-resolution/filters/exceptions/counts/thresholds/DQ), S2T, `gap_analysis.md`; derive load order; **`DESCRIBE` every entity to capture the physical column contract** (the #1 authoring bug — trust the deployment, not the spec) | All N entities identified with schema, FK-resolution attrs, thresholds, known issues — **and** each has a `DESCRIBE`-derived column contract |
| **2 · Generate Validation Schema** | Setup | Create the 5 `_validation_*` tables; seed `_gap_registry` (via `INSERT…SELECT`, never `VALUES(uuid())` — Pitfall §1) + `_data_drift_baseline`; write `validation_state.md` (every entity `NOT_STARTED`); **reconcile it against the live schema — one row per deployed table, not per manifest entity** (the coverage denominator) | 5 tables created; state file has a `NOT_STARTED` row for every non-metadata table in the deployed schema (reconciliation passed); manifest cross-check recorded |
| **3 · Per-Table Narrative Notebooks** | Batch | Author `narrative_{entity}` notebooks in **batches of ≤4 by tier** (dims before facts); each carries BK/POP/FK/INTEGRATION(facts)/DRIFT checks + profile + samples + a PENDING Write-Results cell. Interleaved with Phase 4b — **persist each notebook asset immediately after its checks pass** (before starting the next entity) and **persist the checkpoint after every batch** | One notebook per entity + scorecard; all are notebook objects (not files) |
| **4 · Baseline Run + Validation Job** | Batch | Run notebooks once (sets baselines); author the DAB job by **filling `templates/validation_job.yml`** (one `resources:` root, scorecard terminal, `source: WORKSPACE`); deploy via the environment-routed detect→route→**handoff** contract — never a retry loop | All notebooks pass; baselines captured; job-YAML gate: exactly one `resources:` block + one job identity |
| **4b · Check Your Work (per batch)** | Batch | Run + verify each batch as authored; run the **executable coverage gate** (every entity has BK/POP/DRIFT, every fact also INTEGRATION); flip its rows to `VERIFIED`; emit a mini-scorecard and proceed. Scorecard runs **only** after all rows `VERIFIED` (Finalize only — it claims ALL PENDING rows) | Every batch verified as authored; all notebooks execute; scorecard writes results |
| **5 · Dashboard + Remediation + Handoff** | Finalize | Precondition: **every** row `VERIFIED` + re-run the Phase 2 step-6 schema reconciliation. Schema self-check gate → adapt `templates/validation_dashboard.lvdash.json` into a published dashboard asset named `{Domain} Validation Quality Dashboard` (hybrid: `{Domain} {Silver|Gold} Validation Quality Dashboard`), created in the **project root folder, not the user home directory** (never `renderChartV2`); emit the typed **`validation_summary.md`** handoff (per-entity grades, gap deltas, changed Genie caveats); populate `remediation_brief.md` only if a grade degraded. Render the **Completion Self-Audit** unprompted | Dashboard deployed; remediation template in place; layer-scoped summary emitted **in the typed format**; Self-Audit "Remaining before handoff" list empty |

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
32. **Run the Validation Completion Self-Audit before declaring done — unprompted.** From the Finalize
    session, render the Phase 5 Validation Completion Self-Audit table and report a single **"Remaining
    before handoff"** list before calling validation complete or handing off to `domain-documentation`.
    An **empty** list is the only state that unlocks handoff; if anything is open (an entity not
    `VERIFIED`, scorecard not run, no validation summary), present it and stop.

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
