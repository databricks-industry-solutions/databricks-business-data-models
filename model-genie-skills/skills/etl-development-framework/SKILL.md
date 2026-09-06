---
name: etl-development-framework
description: Build the ETL pipelines from an assessment handoff — the Build station of the loop. Use when turning business_requirements.md + etl_detailed_spec.md into DDL (PK/FK/CHECK/comments/CLUSTER BY), per-entity Type-1 MERGE load notebooks or a whole-domain Lakeflow Declarative Pipeline, a DQ validation notebook, and a DAB job, all to a customer's conventions.yml standards. Also fixes a degraded table from a remediation brief. Not for discovery (use domain-model-assessment) or grading a built model (use domain-model-validation).
---

# ETL Development Framework Skill

> **⚙️ Load `autonomous-validation` alongside this skill — it is NOT pulled in automatically; nothing wires the two together, so load it explicitly at the session start.** (See its `When to Load` for the execution-discipline contract.) — it also hosts `commentary-protocol.md`, the closeout this skill emits.
> A build authors, loads, and tests many notebooks across a domain, so the discipline is load-bearing; the reference files' pointers to it (Batching Discipline in `gold-and-metrics.md`, Known Limitation #6 in `progress-tracking.md`) and the Build Completion Self-Audit (Critical Rule 27) assume it is loaded.

## Overview

This skill provides the complete knowledge base for building batch ETL pipelines
in the Acuity BI Lakehouse. It replaces the clone-and-prompt notebook template
with auto-loaded guidance that Genie Code applies whenever ETL work is requested.

**What this skill produces:**
- SQL DDL notebooks (`CREATE TABLE` with PK/FK, NOT NULL, CHECK, comments, CLUSTER BY)
- Per entity, **one load notebook** (extension-less) in `src/silver/transformations/{entity}`: a
  standard notebook that declares its own parameter widgets (`CREATE WIDGET` → `USE CATALOG
  IDENTIFIER(:silver_catalog)`) and holds the MERGE. This is what the DAB job runs directly.
  Strategy per entity: Type-1 MERGE / incremental / append-only.
- **Gold (when in scope):** metric-view YAML (governed KPIs) + `INSERT OVERWRITE` marts/wide tables
- A validation notebook (recurring DQ gate); gold adds metric-parity checks
- A DAB **daily-load job** (`databricks.yml` + `resources/*.job.yml`) referencing the load notebooks directly
- `docs/.pipeline/state/run/progress.md`; `gap_analysis.md` + `data_quality_assessment.md` (**project root** — see the layout tree in `deployment-and-dab.md`)
- `docs/.pipeline/state/silver/etl_state.md` — per-entity checkpoint (tier, type, wave, assigned session, `NOT_STARTED→BUILT→TESTED`) that makes a large-domain build resumable + parallelizable (see Checkpoint & Session Roles)
- `docs/.pipeline/handoffs/silver/build_manifest.md` — typed build→validate handoff (as-built mirror of `etl_detailed_spec.md`)
- `docs/design/business_requirements.md` (silver, graded before discovery fires)
- `docs/design/gold_requirements.md` (gold arm — consumers + metrics/KPIs with parity targets; an equivalently-scoped gold-design doc from a `domain-model-assessment` gold pass is accepted in its place)
- `docs/design/etl_detailed_spec.md` (optional model/mapping override)
- **When `etl_type: sdp_pipeline`:** instead of the DDL + load-notebook artifacts above, a
  whole-domain Lakeflow Declarative Pipeline — one plain-`.sql` declarative source per entity
  (inline schema + `EXPECT` + query/`AUTO CDC`, hardcoded bronze paths, no `parameters:`), and one
  `pipeline` DAB resource (file/glob model, `root_path`, source-linked dev). **No build-time test
  or validation artifact** (LDP testing is beta + Editor-only — deferred; validation is the
  downstream `domain-model-validation` skill). See `sdp-pipeline-development.md`.
- `docs/commentary/build-improvement-recommendations.md` — **emitted at closeout every run** (skill-improvement recommendations, following `autonomous-validation/commentary-protocol.md`). Always written — a clean run records what worked.

> **One load notebook per entity** — no transform/runner/test trio. The notebook declares its own widgets and is run directly; "landed as intended" is proven by post-load DQ on the real table (Phase 5), not synthetic fixtures. *Rationale: `merge-and-defensive-coding.md` "Why one notebook per entity".*

**Scope:** Moderate-volume batch, Type 1 SCD. **Load strategy is chosen PER ENTITY by
source volume + mutability — not globally.** Full-source MERGE is the default only for
small tables; large facts use incremental/append-only, and very large or SCD2/streaming-DQ
tables escalate to Lakeflow SDP. See the **Load Strategy Decision** in
`merge-and-defensive-coding.md` and the Boundaries section below. When `etl_type: sdp_pipeline`,
all entities are BUILT as a whole-domain Lakeflow Declarative Pipeline (see `sdp-pipeline-development.md`)
— that is a primary buildable mode, not an escalation.

---

## Critical Rules (Always Apply)

1. **Read `naming-standards.md` before generating ANY DDL, MERGE, or DAB artifact.** Customer-specific values (catalogs, casing, thresholds) come from `conventions.yml`, not Acuity literals. *Detail: `naming-standards.md` "About This Document".*
2. **Catalog/schema are RUNTIME PARAMETERS, never literals.** The load notebook declares its own widgets (`silver_catalog`, `silver_schema`, one `src_{logical}` per bronze source, `job_name`), sets session via `USE CATALOG IDENTIFIER(:silver_catalog)`, references target tables unqualified, and reads bronze via `IDENTIFIER(:src_{logical} || '.{table}')`. Python shape interpolates read widgets (markers don't auto-bind). *Detail: `deployment-and-dab.md` "Runtime Parameters" + Shape B.*
3. **Never use `UPDATE SET *` or `INSERT *`** — always explicit column lists. *Detail: `merge-and-defensive-coding.md`.*
4. **Always deduplicate source data** — `ROW_NUMBER() OVER (PARTITION BY {natural_key} ORDER BY {recency} DESC)`, filter `WHERE _rn = 1`. *Detail: `merge-and-defensive-coding.md` "Defensive Coding Rules".*
5. **Keys follow `output_model`.** `dimensional`/`hybrid`-gold → surrogate `{Entity}_Key` (SHA2, never `_sk`/IDENTITY); `normalized`/`hybrid`-silver → the vibe model's PKs (`surrogate_key_method: NONE`), surrogate only by exception. Hash EXPRESSION from `conventions.yml surrogate_key_formula`; pick `bigint`/`string` by the model's declared PK type. `scd_strategy: type_2` forces surrogates (dim/hybrid-gold). *Detail + precedence: `naming-standards.md` "⚠️ Precedence & key strategy by mode".*
6. **Business columns: `Pascal_Snake_Case` (`dimensional`); match model casing exactly (`normalized`/`hybrid`-silver).** Metadata/audit columns always `_lower_snake_case` with leading `_` in all modes. *Detail: `naming-standards.md` §3.1 + "⚠️ Precedence".*
7. **FK columns carry the same name as the parent dim's PK** (`dimensional`/`hybrid`-gold); default to `-1` via `COALESCE`, never `NULL`. *Detail: `naming-standards.md` §3.3.*
8. **Every table and column gets a `COMMENT` sourced from the spec's metamodel description** (never invented); columns with a spec `Glossary term` also get a `glossary_term` UC tag. *Detail: `naming-standards.md` §5.6.*
9. **Notebook headers:** start with `-- Databricks notebook source` (SQL) or `# Databricks notebook source` (Python), then `CREATE WIDGET TEXT` for `silver_catalog`, `silver_schema`, `src_*`, `job_name`, then `USE CATALOG/SCHEMA IDENTIFIER(:...)` in their own cells; catalog/schema never hard-coded. *Detail: `deployment-and-dab.md` "Notebook-format contract".*
10. **Load notebooks and validation are extension-less notebook objects** (never `.sql`/`.py` in `transformations/`); format follows `etl_language`. A stray `.sql` twin in `transformations/` breaks `notebook_task` execution. *Detail: `deployment-and-dab.md` "Notebook-format contract".*
11. **One notebook per table** — every dim, fact, bridge, and gold entity gets its own load notebook; never combine entities. *Detail: `ddl-and-modeling.md` "DDL File Naming & Organization".*
12. **Per-layer, per-role subfolders** — `src/{layer}/ddl/`, `src/{layer}/transformations/`; `validate_{layer}` directly under `src/{layer}/`. Never mix layers or roles. *Detail: `ddl-and-modeling.md` "DDL File Naming & Organization".*
13. **Phase gate** — never author the DAB bundle until every entity's `progress.md` row shows Grade A (or HUMAN NEEDED). *Detail: `progress-tracking.md` "Phase Gate".*
14. **DABs are the only deploy pattern — detect environment first (Step 0).** On serverless the CLI is blocked: author + validate, then hand off to the Deployments panel (🚀). DDL is never a daily-job task (runs once as setup). *Detail: `deployment-and-dab.md` "Deploy is environment-routed" + "DDL is SETUP".*
15. **Maintain `progress.md` after every phase transition and entity load/grade iteration.** *Detail: `progress-tracking.md` "Update Triggers".*
16. **Requirements gate** — never run discovery queries until `business_requirements.md` is graded B or better. *Detail: `testing-and-grading.md` "Requirements Gate" + `discovery-and-gap-analysis.md` §2 rubric.*
17. **Post-load DQ gate per entity (`merge_notebook` mode only).** Grade A (PK/FK/population/row-count) + twice-run idempotency recheck required before a batch advances; `sdp_pipeline` skips this gate entirely (rule 22). *Detail: `testing-and-grading.md` "Per-Notebook Test Cycle" + "Idempotency recheck".*
18. **Emit `docs/.pipeline/handoffs/silver/build_manifest.md` (build→validate handoff)** after all entities pass post-load DQ — fill from `progress.md`, the spec, DDL, and Phase-5 run. *Detail: `progress-tracking.md` "Update Triggers" + `templates/build_manifest.md`.*
19. **`etl_state.md` is the checkpoint of record.** Setup writes it (`NOT_STARTED` for all); only Phase 5 DQ gate flips to `TESTED` (SDP entities advance on `AUTHORED`); Finalize refuses to bundle until all rows reach terminal status; wave barrier enforced (dims `wave:1` → facts `wave:2` → gold `wave:3`). *Detail: `progress-tracking.md` "Multi-Session Resume".*
20. **`sdp_pipeline` — DDL lives in the flow** (inline schema in each `CREATE STREAMING TABLE`/`MATERIALIZED VIEW`). 🔴 Never put `PRIMARY KEY`/`FOREIGN KEY` in an MV column spec — `PARSE_SYNTAX_ERROR`; enforce grain via `CONSTRAINT ... EXPECT`. *Detail: `sdp-pipeline-development.md` intro.*
21. **`sdp_pipeline` — NO parameterization; hardcode bronze paths** as `catalog.schema.table` literals. The native `parameters:` block is a half-working beta (breaks on `STREAM IDENTIFIER(:param)`); only the silver write target varies via DAB `${var}`. *Detail: `sdp-pipeline-development.md` "Parameterization".*
22. **`sdp_pipeline` — NO build-time testing.** Do not author `pyspark.pipelines.testing` (beta, Editor-only), a post-load validation notebook, or any TDD gate. Confidence = inline `EXPECT` + event log + downstream `domain-model-validation`. *Detail: `sdp-pipeline-development.md` intro.*
23. **`sdp_pipeline` — FILE model + scheduler job:** sources are plain `.sql` files (no notebook header), scoped into the graph via `libraries: [glob: {include: ../src/silver/pipeline/**}]`; set `root_path: ..` (the PROJECT root, so the editor exposes the whole project for Genie Code while `libraries` keeps the graph scoped). Emit a companion scheduler `job` with a `pipeline_task` (a `continuous: false` pipeline has no schedule of its own). Dev `source_linked_deployment: true`, prod `false`. *Detail: `sdp-deployment.md`.*
24. **Reconcile columns bilaterally before generating SQL (both modes).** Confirm every column the build READS (source: `DESCRIBE` each bronze; natural-key expression uses SOURCE names) and every column it WRITES (target: `information_schema.columns` on silver) actually exists — never guess a target name. `EXPLAIN` the MERGE as pre-flight. Halt if >20% of an entity's columns are unresolved on either side. *Detail: `discovery-and-gap-analysis.md` "Source↔Target Column Reconciliation gate" + `merge-and-defensive-coding.md` Critical Rule 12.*
25. **Never the `TRY(...)` wrapper for casts** — unsupported on serverless (recurring across 3 projects). Use `TRY_TO_DATE(col, fmt)` and `TRY_CAST(col AS type)` directly. *Detail: `sdp-pipeline-development.md` Rule B.*
26. **`sdp_pipeline` — build tier-by-tier, dry-run before the full deploy.** Author by T0 → T1 → T2; dry-run each source's `AS SELECT` body (schema/`EXPLAIN`) before triggering a pipeline update (write-all-then-test surfaced 14 errors at once). *Detail: `sdp-pipeline-development.md` "Incremental build loop".*
27. **Run the Build Completion Self-Audit unprompted before declaring done** — from the Finalize session, render the Phase 7 audit table; an empty "Remaining before handoff" list is the only state that unlocks handoff. *Detail: `testing-and-grading.md` "Build Completion Self-Audit".*
28. **Per-entity commit contract:** three artifacts persist atomically before the next entity starts: (1) load notebook in `src/…`, (2) `etl_state.md` row flipped to terminal, (3) `progress.md` row updated. Missing any on session loss = work not recoverable. *Detail: `progress-tracking.md` "Per-Entity Commit Contract".*
29. **Validate `conventions.yml` at session start (fail fast).** Before any SQL, confirm `catalogs.silver`, each `bronze_sources` entry, `vibe_model.*`, and `schemas.silver_pattern` all resolve; a miss is a HITL gate — stop and report. *Detail: `progress-tracking.md` "conventions.yml Validation Gate".*

## Reference Files

Load these for detailed guidance on specific topics:

| File | Content |
| --- | --- |
| `naming-standards.md` | **Authoritative** naming, column, DDL, modeling, validation, grading, and governance standards |
| `discovery-and-gap-analysis.md` | Data discovery protocol + gap analysis report format |
| `ddl-and-modeling.md` | DDL templates (dim, fact, bridge, gold) + modeling rules |
| `merge-and-defensive-coding.md` | MERGE notebook template + defensive coding patterns + **Load Strategy Decision** (full/incremental/append-only/SDP) |
| `sdp-pipeline-development.md` | **`sdp_pipeline` pack overview/router** — load-strategy→SDP object mapping, incremental build loop, parameterization rules, inline-schema contract; routes to the sub-files below |
| `sdp-templates.md` | **`sdp_pipeline` pack** — SQL + Python + normalized-mode source templates; FK-resolution trees |
| `sdp-gold-star.md` | **`sdp_pipeline` pack** — `output_model: hybrid` downstream dimensional gold star |
| `sdp-deployment.md` | **`sdp_pipeline` pack** — the `pipeline` DAB resource (FILE/glob model, `root_path`) |
| `gold-and-metrics.md` | **Gold arm**: metric-view pattern (wires in `databricks-metric-views`), mart vs wide-table vs metric-view choice, metric-parity validation |
| `testing-and-grading.md` | **The Phase 5 per-entity gate** — run the real load, post-load DQ checks (PK/FK/population/row-count) + twice-run idempotency recheck, grading rubric (A–F). This is what advances an entity `BUILT → TESTED`. |
| `deployment-and-dab.md` | DAB layout, job YAML template, phase gating, deploy sequence |
| `progress-tracking.md` | progress.md format + resume protocol |
| `templates/business_requirements.md` | **Required** fillable requirements doc (silver) — created during scaffolding, graded before discovery |
| `templates/etl_detailed_spec.md` | Optional fillable spec override — any filled section overrides discovery |
| `templates/build_manifest.md` | **Build output** — the typed build→validate handoff (as-built mirror of the spec: strategy/recency/FK-resolution/filters/exceptions/row-counts/thresholds + post-load DQ grade + idempotency-recheck result); emitted Phase 6.5 |
| `templates/gold_requirements.md` | **Required for the gold arm** — consumers, metrics/KPIs with parity targets, artifact-type choice; graded B+ before gold build. **Filled copy → `docs/design/gold_requirements.md`** (alongside `business_requirements.md`; an assessment gold-design doc is accepted in its place). |
| `templates/conventions.yml` | *(repo root)* Single per-customer config surface — catalogs, naming, source enum, load-strategy thresholds |

---

## What this skill builds

This skill builds **a buildable, per-domain schema SEEDED BY the vibe model and reconciled
against bronze** — NOT a "faithful port" of the model. The vibe model (Amr Ali's agent) is a
normalized, 3NF, single-source-of-truth **logical spec** that never saw the customer's bronze;
it is a 1–2 shot starting point. This skill morphs each domain into something a data-engineering
team can actually build and run. **Drift from the model is expected and fine** — teams build
domain by domain and are not obligated to keep the whole model coherent as one entity.

**The output SHAPE is a customer choice** — `conventions.yml` → `output_model`:

| `output_model` | Silver shape | Keys | Gold |
|---|---|---|---|
| **`normalized`** *(default)* | Table-per-product, 3NF, model's PK/FK preserved (SSOT). Product names (`customer`, `order`), lowercase model PKs (`order_id`). No `dim_/fact_` prefixes. | Follow the model's PKs (`surrogate_key_method: NONE`); surrogate only by exception | Optional use-case marts/metrics |
| **`dimensional`** | Kimball star: `dim_/fact_/bridge_`, conformed dims, explicit grain. Model is the SEED, then dimensionalized. | Surrogate `{Entity}_Key` (SHA2), `-1` unknown | Use-case marts + metric views |
| **`hybrid`** | **Layered (not both-at-once):** normalized 3NF SSOT silver, THEN a dimensional star built downstream from it in gold | Model keys in silver; surrogates in gold | The star lives here |

> **Rule ownership.** The agent's ~250 *modeling* rules (naming, 3NF, FK-DAG, SSOT — in
> `vibe-modelling-agent/rules/`) already produced the spec and are **Kimball-agnostic**. This
> skill's **Kimball** rules (grain, conformed dims, surrogates, fact/dim/bridge, SCD) fire ONLY
> in `dimensional` mode (and `hybrid`'s gold). In `normalized` mode the build **inherits** the
> model's structure — it does NOT re-run or re-litigate the agent's rules, and applies NO Kimball
> rules; it materializes the model + engineering scaffolding (load strategy, DQ, keys-follow-model,
> audit columns) and validates only reconciliation-to-bronze + build quality.

## Layering Contract

The table below shows the **`dimensional`** shape (the fullest case, shown for reference — it is no
longer the default). For the default `normalized` (and `hybrid`), read the Silver row per the mode
table above (Silver = the normalized product tables; the dimensional star moves to Gold in `hybrid`).

| Layer | Definition | Target | Pattern |
| --- | --- | --- | --- |
| **Bronze** | Already-cleaned, ingested data (upstream). READ-ONLY — never create bronze. | source only | `SELECT FROM bronze` |
| **Silver** | `dimensional`: generic conformed dimensional model (`dim_*`/`fact_*`), surrogate keys, PK/FK, Type 1 default. `normalized`/`hybrid`: table-per-product 3NF model, model keys. Not use-case-specific. | `{silver_catalog}.{silver_schema}` | `dimensional`: Type 1 (or Type 2, see `scd_strategy`) MERGE on surrogate key. `normalized`: MERGE on model PK |
| **Gold** | Use-case-specific BI serving built FROM silver — denormalized marts, aggregates, or **governed metric views** for one dashboard/Genie space/report. In `hybrid`, gold is ALSO where the dimensional star (`dim_/fact_/bridge_` + any SCD2) lives. Pick the tool per artifact (see `gold-and-metrics.md`) — do NOT default all KPIs to tables. | `{gold_catalog}.{gold_schema}` | Marts: `INSERT OVERWRITE`. KPIs: **metric view** (UC YAML via `databricks-metric-views`) |

If building both layers, build silver first, then gold reads from silver.

> **Silver land target ≠ vibe model.** `{silver_catalog}.{silver_schema}` above is the
> **write/land** target — where this skill CREATEs and MERGEs built tables (resolves from
> `conventions.yml` `catalogs.silver` + `schemas.silver_pattern`). The **vibe model** you map
> sources against — the empty target structure + `vibe_metamodel_*` — is READ-ONLY and lives at
> `conventions.yml` → `vibe_model.catalog` / `vibe_model.schema` (a discovery/authoring-time
> read, not a runtime widget). These are deliberately distinct so a build never writes into the
> model it is grading against. **The model is a logical spec** — every mode CREATEs fresh tables
> in `catalogs.silver` and rebuilds from the current model version; there is no in-place MERGE
> into model tables and no model-version migration logic. Read the model structure from
> `vibe_model`; land built silver into `catalogs.silver`. They may be different catalogs entirely.

---

## Kickoff Protocol

When a user asks to start a new ETL project (or says "start a new ETL project",
"build a silver layer for X", etc.):

1. **Create a project folder** in the user's workspace (ask for location or use their current folder)
2. **Scaffold the project** — create all of the following inside the project folder:
   - `conventions.yml` (copy from `templates/conventions.yml` at the repo root — the single
     config surface: catalogs, naming, source-system enum, `bronze_sources` map, load-strategy
     thresholds. Fill it for this customer BEFORE generating any SQL. It supplies the runtime
     DEFAULTS + the bronze source→prefix map; generated notebooks read catalog/schema from
     widgets/job params at run time, never from baked-in literals.)
   - `docs/.pipeline/README.md` (copy verbatim from `templates/pipeline_readme.md` in this skill — the in-folder manifest of the handoff/state tier; this skill is the first to create `.pipeline/`, so it drops the README once)
   - `docs/.pipeline/Kickoff` (Python notebook with parameter widgets — the full widget list is in `deployment-and-dab.md` "Kickoff notebook — parameter widgets")
   - `docs/design/business_requirements.md` (copy from `templates/business_requirements.md` in this skill)
   - `docs/design/etl_detailed_spec.md` (copy from `templates/etl_detailed_spec.md` in this skill)
   - `docs/.pipeline/state/run/progress.md` (initial phase tracker; `state/run/` = run-global checkpoints, `state/{silver,gold}/` = layer-scoped — see the README)
   - `databricks.yml` (DAB bundle stub with dev + prod targets)
   - `src/silver/ddl/` (DDL notebooks — created once as setup)
   - `src/silver/transformations/` (one load notebook per entity — declares its own widgets, holds the MERGE; what the DAB job references directly)
   - `src/gold/` (empty folder — gold notebooks go here, if layer_type includes gold)
3. **Tell the user** once scaffolding is complete:
   > "Project scaffolded. Before I can run discovery, please complete two things:
   > 1. **`docs/design/business_requirements.md`** — required. I grade this before running any queries. The more specific you are, the fewer assumptions I make.
   > 2. **`Kickoff` notebook widgets** — fill in the bronze sources (logical=catalog.schema), silver/gold + sandbox targets, job name, and alert email.
   >
   > Optionally, fill `docs/design/etl_detailed_spec.md` for any entities, column mappings, or keys you already know — any filled section overrides discovery for that part of the model and skips the corresponding questions."
4. **Wait** for the user to provide requirements before proceeding. Do not run any discovery queries until the requirements gate in `discovery-and-gap-analysis.md` passes (overall grade B or better).
5. **Begin the execution workflow** (see below)

---

## Checkpoint & Session Roles (resumable + parallelizable build)

A full-domain build overflows one session, so it runs in three roles against a state file:
**Setup** (Phases 1–3, writes `docs/.pipeline/state/silver/etl_state.md` with every entity `NOT_STARTED` + tier + type + wave) → **Batch** (Phases 4–5 for its assigned entities, ≤4–6, flips rows `BUILT`→`TESTED`) → **Finalize** (Phases 6–7, refuses to bundle until all rows `TESTED`). `Build_Status`: `NOT_STARTED → BUILT → TESTED` (only the Phase-5 post-load DQ gate flips to `TESTED`). **Wave barrier:** no wave-`N` entity starts until every wave-`<N` entity is `TESTED` (dims wave 1 → facts wave 2 → gold wave 3). Single-session runs still write the state file at each transition so a fresh session resumes. *Detail (state-file schema, role table, atomic-write rule): `progress-tracking.md` "Checkpoint & Session Roles".*

---

## Execution Workflow (7 Phases)

> **`etl_type` routing (read `conventions.yml` first).** `merge_notebook` → the 7 phases
> below as written. `sdp_pipeline` (default) → phases 1 and 3 are unchanged; phase 2 captures the inline
> schema contract but does NOT emit a separate DDL-setup step (DDL lives in the flow); phases 4–5
> author the declarative sources (plain `.sql`, hardcoded bronze paths) — **auto-load
> `sdp-pipeline-development.md` and translate each entity's spec §5 strategy to an SDP object type
> (MV / ST-APPEND / ST-CDC1 / ST-CDC2) via its "Load-strategy → SDP object mapping" before
> authoring** (MERGE-era labels don't map 1:1), tier-by-tier with a per-source dry-run (rule 26) —
> with **no build-time test or validation artifact** (the LDP test framework is beta + Editor-only — deferred); phase 6
> emits a `pipeline` resource (file/glob model, `root_path`, source-linked dev) instead of a daily
> job; phase 7 is the downstream `domain-model-validation` skill (plus inspecting event-log EXPECT
> pass-rates after a run). All SDP specifics are in `sdp-pipeline-development.md`.

> The 7 phases below are the *work*; the **Checkpoint & Session Roles** section above is *how to
> distribute that work* across resumable/parallel sessions. Setup = Phases 1–3, Batch = Phases
> 4–5, Finalize = Phases 6–7.

> **Plan TODOs at ENTITY granularity — one TODO item per entity, not per batch.** Each item
> tracks the full lifecycle (introspect → author → persist → load → DQ → checkpoint).
> The load-order tier sets the SEQUENCE of items, never their grouping.

### Phase 1: Discovery
Validate `conventions.yml` (fail fast, Rule 29), profile bronze, classify DIM/FACT, identify natural keys + grain, build load order, then **PAUSE for model approval**. *See: `discovery-and-gap-analysis.md`.*

### Phase 2: Model & DDL
Generate DDL notebooks per `naming-standards.md` and `output_model`, introspect vibe model columns verbatim, write DDL files first then execute as one-time SETUP, then **PAUSE for DDL approval**. *See: `ddl-and-modeling.md`, `naming-standards.md`, `deployment-and-dab.md` ("DDL is SETUP").*

### Phase 3: Gap Analysis
Compare bronze to the approved model, reconcile source columns bilaterally (halt >20% unresolved), flag GAPS and enrichment opportunities, write `gap_analysis.md`, initialize `etl_state.md` (all `NOT_STARTED`). *See: `discovery-and-gap-analysis.md`.*

### Phase 4: Scaffold (ENTITY-FIRST — one entity end-to-end, ≤N per session)

> **One load notebook per entity.** Each entity is a single **extension-less notebook** in
> `src/silver/transformations/{entity}` that declares its own parameter widgets
> (`CREATE WIDGET TEXT silver_catalog DEFAULT ''`, one `src_{logical}` per bronze source,
> `job_name`), sets its session with `USE CATALOG IDENTIFIER(:silver_catalog)`, and holds the
> MERGE — referencing target/silver tables unqualified and bronze via
> `IDENTIFIER(:src_{logical} || '.{table}')`. The DAB daily job runs this notebook directly via
> `notebook_task` + `base_parameters` — no runner, no separate test notebook. See
> `merge-and-defensive-coding.md` "Notebook Format" and `deployment-and-dab.md`
> "Notebook-format contract" for the full shape.

- Generate load notebooks in `src/silver/transformations/` — one **extension-less notebook**
  per entity (`dim_{entity}`, `fact_{name}`; format follows `conventions.yml` `etl_language` —
  SQL notebook or Python notebook, never a `.sql`/`.py` plain FILE), using the **per-entity load
  strategy** from `etl_detailed_spec.md` Section 5 (FULL_MERGE / INCREMENTAL_MERGE / APPEND_ONLY /
  SDP — see `merge-and-defensive-coding.md` Load Strategy Decision). Do NOT default every fact to
  full MERGE.
  - **If Section 5 is blank** (spec authored here, no upstream assessment): run the Step 2.6
    Mutability Probe from `domain-model-assessment/discovery-protocol.md` yourself during
    discovery and fill Section 5 before scaffolding — the strategy decision cannot be skipped
    just because there was no assessment pass.
  - **Soft gate — WARN on likely mis-classification (do not block).** Emit the strategy the spec
    stamps, but surface a `⚠️ LOAD STRATEGY` warning to the user when a stamp looks wrong so they
    can correct the spec:
    - entity named `*_transaction` / `*_completion` / `*_move` / `*_posting` / event-grain but
      stamped `FULL_MERGE` or `INCREMENTAL_MERGE` (likely should be `APPEND_ONLY`);
    - source `> 5M` rows stamped `FULL_MERGE` with no rationale in the Rationale column;
    - `INCREMENTAL_MERGE` stamped with no watermark column named;
    - mutable fact `> 100M` (or mutable with no watermark) stamped anything other than `SDP`.
    The warning is advisory — proceed with the spec's stamp; the human owns the correction.
- Generate INSERT OVERWRITE load notebooks in `src/gold/transformations/` if gold layer included
  (one extension-less notebook per table: `{business_name}`).
- Generate `src/silver/validate_silver` (recurring DQ gate for all silver entities)
- Generate `src/gold/validate_gold` if gold layer included (recurring DQ gate for all gold entities)
- **One notebook per table** — never combine multiple entities into one file
- **Entity-first build loop (mandatory).** The atomic unit is ONE entity, built
  end-to-end and checkpointed before the next starts. Do NOT author a group of
  notebooks then load the group — that is the durability hole (a session drop can
  leave a landed load with no notebook to reproduce it). The ≤4 cap bounds how many
  entities a SESSION attempts, not how many it authors before running. Phase 4 and
  Phase 5 interleave PER ENTITY:
  ```
  For each entity (in load-order tier sequence, ≤4 per session to bound context):
    1. Introspect the model table + bronze source (bilateral column reconciliation, Rule 24).
    2. Author the DDL (if not already created as setup) + the load notebook;
       validate its SQL in scratchpad first (Golden Rule).
    3. PERSIST the notebook to the workspace immediately — createAsset/editAsset —
       BEFORE running the real load. This is a gate: on session drop the worst case
       is "notebook exists, load not yet run" (recoverable), never "load landed, no
       notebook" (not recoverable).
    4. Run the real load (Phase 5).
    5. Post-load DQ on the real table (PK/FK/population/row-count) + grade A–F; on the
       FIRST entity of each load strategy, run the load a SECOND time and assert
       row-count + key-set stability (idempotency recheck).
    6. Flip this entity's etl_state.md row NOT_STARTED→BUILT→TESTED and update its
       progress.md row (the per-entity commit contract, Critical Rule 28) BEFORE
       starting the next entity.
    7. Only then: next entity.
  ```
- Apply defensive coding patterns from `merge-and-defensive-coding.md`
- Follow naming standards for all generated code

### Phase 5: Load, DQ & Grade (the per-entity gate)
Run each notebook in load order (real load, ≤5 fix attempts/entity), post-load DQ per entity (PK/FK/population/row-count), idempotency recheck on first of each strategy, grade A–F, flip `etl_state.md` rows to `TESTED`. *See: `testing-and-grading.md`.*

### Phase 6: Bundle & Deploy (DABs are the core deploy pattern)
Confirm all entities `TESTED`, generate `databricks.yml` + `resources/*.job.yml` (loads + validation only; DDL is SETUP), detect environment (serverless → Deployments panel handoff; web terminal → `bundle deploy`). *See: `deployment-and-dab.md` ("Deploy is environment-routed").*

### Phase 6.5: Emit Build Manifest (typed build→validate handoff)
After all entities pass (Grade A/HUMAN NEEDED + idempotency recheck), write `docs/.pipeline/handoffs/silver/build_manifest.md` — as-built mirror of the spec (strategy/recency/FK-resolution/§3.5 column inventory/row counts/DQ grades); §3.5 is what `domain-model-validation` codes against. *See: `templates/build_manifest.md`, `progress-tracking.md`.*

### Phase 7: Integration Test
Run the full job end-to-end; validation notebooks pass as the final recurring gates (one per layer); fix and re-run if cross-notebook issues surface. *See: `testing-and-grading.md`.*

#### Build Completion Self-Audit (MANDATORY — render unprompted before declaring the build done)

**Do not wait to be asked "are we done?"** This is the build's instance of the `autonomous-validation`
gate-(a) contract: at the last phase, reconcile every closing obligation and report a single
**"Remaining before handoff"** list, unprompted. **An empty list is the ONLY state that lets you
declare the build complete / hand off to `domain-model-validation`.** If any item is open, present
the list and stop — do NOT emit the build manifest as final or call the build done. Run this from the
**Finalize** session only (never a batch session).

| # | Closing obligation | Done when | Status |
| --- | --- | --- | --- |
| 1 | **Every entity is `TESTED`** | No `etl_state.md` row is `NOT_STARTED` or `BUILT` — each passed its post-load DQ + idempotency gate; waves respected | ☐ |
| 2 | **DAB bundle authored + deployed** | Phase 6 complete: `databricks.yml` + `resources/*.job.yml` reference the load notebooks and deploy cleanly | ☐ |
| 3 | **Build manifest emitted** | Phase 6.5: `docs/.pipeline/handoffs/{layer}/build_manifest.md` written as the as-built mirror of the spec | ☐ |
| 4 | **Integration test passed** | Phase 7: full job ran end-to-end; validation notebooks passed as final gates | ☐ |
| 5 | **Root state docs present** | `gap_analysis.md` + `data_quality_assessment.md` written; `progress.md` current | ☐ |
| 6 | **Improvement recommendations emitted** | `docs/commentary/build-improvement-recommendations.md` written per `autonomous-validation/commentary-protocol.md` (always, even on a clean run) | ☐ |

The improvement-recommendations file is the final artifact of the run — write it after every other obligation is ☑, following `autonomous-validation/commentary-protocol.md`.

Report as: **"Remaining before handoff: {list, or 'none — ready for validation'}"**. Only on "none"
is the build done.

---

## Boundaries — When to Escalate

This framework produces Type 1 MERGE silver dims/facts and INSERT OVERWRITE
gold tables. **Choose the load strategy per entity first** (see Load Strategy Decision in
`merge-and-defensive-coding.md`): FULL_MERGE < ~5M rows, INCREMENTAL_MERGE 5M–100M mutable,
APPEND_ONLY for immutable ledgers. The following conditions are **built** (not escalated) when
`etl_type: sdp_pipeline` — see `sdp-pipeline-development.md`. They are **HUMAN NEEDED escalation
points** in `merge_notebook` mode only:

- **(a) Volume makes full MERGE reloads costly** — hard trigger: a mutable fact source
  **> 100M rows** where a nightly full-target MERGE shuffle is uneconomic, and the table
  can't be reduced to APPEND_ONLY. Streaming ingestion is materially cheaper.
- **(b) Some dims need SCD Type 2 history** — point-in-time snapshots require streaming with `_change_type` tracking
- **(c) Always-on enforced DQ via expectations** — hard/soft constraint enforcement with quarantine semantics

> **Do not silently full-MERGE a 100M+ row fact because "it's the default."** If discovery
> profiled a fact above the thresholds above and no incremental/append path was chosen, that
> is a HUMAN NEEDED flag in `merge_notebook` mode, not an auto-proceed. In `sdp_pipeline` mode,
> these are the expected build targets — proceed with `sdp-pipeline-development.md`.

---
