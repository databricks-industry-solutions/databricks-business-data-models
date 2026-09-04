---
name: etl-development-framework
description: Build the ETL pipelines from an assessment handoff — the Build station of the loop. Use when turning business_requirements.md + etl_detailed_spec.md into DDL (PK/FK/CHECK/comments/CLUSTER BY), per-entity Type-1 MERGE load notebooks or a whole-domain Lakeflow Declarative Pipeline, a DQ validation notebook, and a DAB job, all to a customer's conventions.yml standards. Also fixes a degraded table from a remediation brief. Not for discovery (use domain-model-assessment) or grading a built model (use domain-model-validation).
---

# ETL Development Framework Skill

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

> **Why one notebook per entity (no runner/test trio).** Earlier versions of this skill split
> each entity into a transform (declares nothing) + a runner (declares params, `%run`s the
> transform) + a build-time fixture unit test that `%run`s the same transform. That split existed
> *only* so a test could `%run` the transform with swapped session variables pointing at fixtures.
> We removed the fixture unit-test framework (see rationale below), so the split lost its reason to
> exist — the load notebook now declares its own widgets and is run directly, which is what field
> teams actually write and eliminates the opaque `%run`-failure debugging problem. **Confidence
> that a load "landed as intended" comes from post-load DQ on the real table** (the Phase 5 gate,
> `testing-and-grading.md`) plus a cheap twice-run idempotency recheck — not from synthetic
> fixtures. Deep data-state validation is then the downstream `domain-model-validation` skill.
>
> *Rationale (July 2026):* no field team writes build-time fixture tests for hand-authored MERGE
> notebooks; the idempotency bug they guarded (`DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`)
> fails the MERGE **loudly at runtime** anyway; and the packaged unit-test investment is all going
> into Lakeflow SDP (which `sdp_pipeline` mode already uses). The `python-unit-tests` +
> workspace-files path was not adopted because it assumes transform logic extracted into importable
> `src/` modules — these transforms are deliberately notebook-native SQL, so there is nothing to
> `pytest` without a different architecture.

**Scope:** Moderate-volume batch, Type 1 SCD. **Load strategy is chosen PER ENTITY by
source volume + mutability — not globally.** Full-source MERGE is the default only for
small tables; large facts use incremental/append-only, and very large or SCD2/streaming-DQ
tables escalate to Lakeflow SDP. See the **Load Strategy Decision** in
`merge-and-defensive-coding.md` and the Boundaries section below. When `etl_type: sdp_pipeline`,
all entities are BUILT as a whole-domain Lakeflow Declarative Pipeline (see `sdp-pipeline-development.md`)
— that is a primary buildable mode, not an escalation.

---

## Reference Files

Load these for detailed guidance on specific topics:

| File | Content |
| --- | --- |
| `naming-standards.md` | **Authoritative** naming, column, DDL, modeling, validation, grading, and governance standards |
| `discovery-and-gap-analysis.md` | Data discovery protocol + gap analysis report format |
| `ddl-and-modeling.md` | DDL templates (dim, fact, bridge, gold) + modeling rules |
| `merge-and-defensive-coding.md` | MERGE notebook template + defensive coding patterns + **Load Strategy Decision** (full/incremental/append-only/SDP) |
| `sdp-pipeline-development.md` | **`etl_type: sdp_pipeline` only** — whole-domain Lakeflow Declarative Pipeline template pack: streaming-table / materialized-view / AUTO CDC (SCD1/SCD2) in both dialects, hardcoded bronze paths (no parameterization), inline `EXPECT`, FILE/glob model + `root_path` + source-linked deploy, event-log DQ reads. **No build-time testing** (validation is the downstream skill). Replaces the MERGE load notebook + daily job. Deliberately avoids the `parameters:` and `pyspark.pipelines.testing` betas. |
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
   - `docs/.pipeline/Kickoff` (Python notebook with parameter widgets — see widget list below)
   - `docs/design/business_requirements.md` (copy from `templates/business_requirements.md` in this skill)
   - `docs/design/etl_detailed_spec.md` (copy from `templates/etl_detailed_spec.md` in this skill)
   - `docs/.pipeline/state/run/progress.md` (initial phase tracker; `state/run/` = run-global checkpoints, `state/{silver,gold}/` = layer-scoped — see the README)
   - `databricks.yml` (DAB bundle stub with dev + prod targets)
   - `src/silver/ddl/` (DDL notebooks — created once as setup)
   - `src/silver/transformations/` (one load notebook per entity — declares its own widgets, holds the MERGE; what the DAB job references directly)
   - `src/gold/` (empty folder — gold notebooks go here, if layer_type includes gold)
   ```python
   # NOTE: catalog/schema are RUNTIME PARAMETERS. The Kickoff notebook captures the
   # DEFAULTS (which seed conventions.yml + DAB variables); the generated ETL/DDL/
   # validation notebooks each declare their OWN widgets and read values passed by the
   # job's base_parameters at run time — nothing is baked in. See deployment-and-dab.md.
   #
   # Source (bronze) configuration — a domain reads MANY bronze schemas, sometimes across
   # different catalogs. These map to conventions.yml `bronze_sources` (logical name →
   # catalog.schema). Do NOT collapse to one source_catalog/source_schema pair.
   dbutils.widgets.text("bronze_sources", "", "Bronze sources (logical=catalog.schema, comma-sep)")
   # Vibe model (READ-ONLY target structure being graded — conventions.yml vibe_model.*).
   # Captured as a default so discovery/gap analysis reads the model from here; the build
   # LANDS built tables into the SEPARATE silver target below, never into these.
   dbutils.widgets.text("vibe_model_catalog", "", "Vibe Model Catalog (read-only)")
   dbutils.widgets.text("vibe_model_schema", "", "Vibe Model Schema (read-only)")
   # Silver (dimensional model) LAND/WRITE target — distinct from the vibe model above
   dbutils.widgets.text("silver_catalog", "", "Silver Catalog (land target)")
   dbutils.widgets.text("silver_schema", "", "Silver Schema (land target)")
   # Gold (use-case BI) target
   dbutils.widgets.text("gold_catalog", "", "Gold Catalog")
   dbutils.widgets.text("gold_schema", "", "Gold Schema")
   # Sandbox (dev target catalog — dev DAB variable points silver/gold here)
   dbutils.widgets.text("sandbox_catalog", "", "Sandbox (Dev) Catalog")
   dbutils.widgets.dropdown("layer_type", "silver", ["silver", "gold", "both"], "Layer Type")
   # Output model shape (THE shape knob — seeds conventions.yml output_model)
   dbutils.widgets.dropdown("output_model", "dimensional", ["normalized", "dimensional", "hybrid"], "Output Model")
   dbutils.widgets.dropdown("scd_strategy", "type_1", ["type_1", "type_2"], "SCD Strategy (dims)")
   # Deployment configuration
   dbutils.widgets.text("bundle_name", "", "DAB Bundle Name")
   dbutils.widgets.text("job_name", "", "Job Name")
   dbutils.widgets.text("job_schedule", "0 0 10 * * ? *", "Job Schedule (Quartz Cron)")
   dbutils.widgets.text("job_timezone", "America/New_York", "Job Timezone")
   dbutils.widgets.text("alert_email", "", "Failure Alert Email")
   dbutils.widgets.text("workspace_path", "", "Output Workspace Path")
   # Strategy defaults
   dbutils.widgets.dropdown("merge_strategy", "auto", ["auto", "MERGE", "INSERT_OVERWRITE", "APPEND"], "Merge Strategy")
   dbutils.widgets.dropdown("surrogate_key_method", "auto", ["auto", "SHA2", "NONE"], "Surrogate Key Method")
   # auto -> resolve from output_model: dimensional/hybrid-gold=SHA2, normalized/hybrid-silver=NONE
   ```
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

**The single biggest scaling failure of this skill is context overflow on a long single session.**
Authoring every DDL + load notebook and loading every entity for a full 16–17-entity
domain in one pass overflows the context window near the end and the session hangs (the Meridian
failure mode). This section makes the build **resumable** (a fresh session reads a state file
instead of re-inferring what was done) and **parallelizable** (multiple sessions can own disjoint
tiers). It is the exact pattern `domain-model-validation` uses (`validation_state.md` + Setup/
Batch/Finalize) — kept aligned — plus **one addition ETL needs that validation does not: a wave
barrier** (facts depend on dim *tables* existing, so fact batches cannot start until dim batches
finish).

### The checkpoint file — `docs/.pipeline/state/silver/etl_state.md`

For a gold-layer build, substitute `silver/` → `gold/` in the state and handoff paths.

The **Setup** session writes it; every **Batch** session updates only its own rows; the
**Finalize** session reads it to confirm completeness before bundling. It is the single source of
truth for "what's built."

```markdown
# ETL State — {domain}
Updated: {YYYY-MM-DD HH:MM} · Setup run: {run stamp} · Total entities: {N}

| Entity | Tier | Type | Wave | Assigned_Session | Build_Status | Batch_Notes |
|---|---|---|---|---|---|---|
| dim_plant    | 0 | DIM  | 1 | setup      | TESTED      | Grade A, idempotency PASS |
| dim_customer | 0 | DIM  | 1 | session_A  | TESTED      | Grade A, idempotency PASS |
| fact_orders  | 1 | FACT | 2 | session_B  | BUILT       | needs post-load DQ gate |
| fact_returns | 1 | FACT | 2 | session_C  | NOT_STARTED | — |
```

- **`Build_Status` enum:** `NOT_STARTED → BUILT → TESTED`. Only the Phase 5 **post-load DQ gate**
  (real load + PK/FK/population/row-count at Grade A + twice-run idempotency PASS) may move a row to
  `TESTED` — an authored-but-not-loaded notebook is `BUILT`. A notebook can exist yet fail its load
  or DQ checks, so `BUILT` is not "done"; only `TESTED` is.
- **`Wave`** is the ETL-specific column: dims are `wave: 1`, facts `wave: 2`, gold (when in scope)
  `wave: 3`. **Rule: no wave-`N` entity starts until every wave-`<N` entity is `TESTED`** (facts
  need their parent dim *tables* loaded; gold reads from silver facts). In a single session this is
  just the normal dims-before-facts load order; across parallel sessions it is an explicit barrier
  the human enforces (launch wave-1 sessions, wait for all wave-1 `TESTED`, then launch wave-2).
- **`Assigned_Session`** is how two sessions avoid building the same entity — a batch session only
  touches rows assigned to it (or unassigned rows it claims by writing its id first).
- Writes are atomic full-file replacements (`readFile` → edit → write back), never blind-append —
  see `autonomous-validation` Known Limitation #6.

### The three session roles (the 7 phases split by singleton-ness)

Phases 1–3 (discovery, DDL-as-setup, gap analysis — including the model-approval PAUSE) and
Phases 6–7 (bundle/deploy, integration test) are **singletons**. Per-entity authoring + loading
(Phases 4–5) is the fan-out. So a large domain builds as:

| Role | Runs | Does | Stops when |
|---|---|---|---|
| **Setup** (once) | Phase 1 + 2 + 3 | Discovery (**model-approval PAUSE stays**), create tables as the one-time DDL setup, gap analysis, **write `etl_state.md` with every entity `NOT_STARTED` + tier + type + wave + session assignments** | State file written; tables exist |
| **Batch** (1..M, may be parallel within a wave) | Phase 4 + 5 for its assigned entities only | Author DDL + load notebook → real load → post-load DQ + idempotency recheck → grade, ≤4 per batch, flip its rows `BUILT`→`TESTED` | All its assigned rows `TESTED` |
| **Finalize** (once) | Phase 6 + 6.5 + 7 | Confirm **every** row is `TESTED` (else stop and report which aren't, respecting waves), bundle + deploy, emit `build_manifest.md`, run integration test | Bundle authored + manifest emitted |

- **Setup and Finalize are short** (no per-entity authoring) — they never overflow. **Batch
  sessions are bounded** to ≤4–6 entities. This is the structural fix for the overflow,
  independent of whether you run sessions in parallel.
- **Single-session runs still use this.** One session plays all three roles in sequence but writes
  `etl_state.md` at each transition, so if it *does* overflow the next session resumes from the
  state file instead of re-inferring. The wave barrier is just the normal load order.
- **Finalize is the sole bundler** — never author the DAB or run the integration test from a batch
  session; bundling a partial model produces a job that loads tables that were never tested.

> **Sibling skills hit the same wall.** `domain-model-validation` (`validation_state.md`) and
> `domain-documentation` (`documentation_state.md`) use the identical Setup/Batch/Finalize split.
> Keep the three patterns aligned; the wave column is the one ETL-specific addition.

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

### Phase 1: Discovery
- Profile bronze sources (INFORMATION_SCHEMA + DESCRIBE)
- Classify entities as DIMENSION or FACT
- Identify natural keys, conformed dimensions, grain
- Build load order: dims (Tier 0) → facts (Tier 1) → gold (Tier 2) → validation (Final)
- **PAUSE** — present proposed model for user approval
- See: `discovery-and-gap-analysis.md`

### Phase 2: Model & DDL
- Generate DDL notebooks in `src/silver/ddl/` (one `.sql` file per table: `ddl_dim_{entity}.sql`, `ddl_fact_{name}.sql`)
- Generate DDL notebooks in `src/gold/ddl/` if gold layer included (one `.sql` file per table: `ddl_{business_name}.sql`)
- Apply all rules from `naming-standards.md` per `output_model`: `dimensional` → Pascal_Snake_Case + `{Entity}_Key` surrogates + `dim_/fact_/bridge_`; `normalized`/`hybrid`-silver → the vibe model's product names + `{product}_id` keys (see the Normalized Product template in `ddl-and-modeling.md`). Metadata columns, constraints, CLUSTER BY, comments, UC tags apply in all modes.
- **Dimensional/hybrid-gold only:** seed the -1 Unknown member in every dimension. **Normalized mode does NOT seed -1** (FKs may be NULL when unresolved).
- **PAUSE** — present DDL for approval
- **After approval, create the tables as a one-time SETUP step** — run the DDL notebooks
  directly (Genie Code `runNotebookCells`/`executeCode`) or via a separate `{domain}_ddl_setup`
  bundle job. **DDL does NOT go in the daily load job.** Re-run only on schema change.
- See: `ddl-and-modeling.md`, `naming-standards.md`, `deployment-and-dab.md` ("DDL is SETUP")

### Phase 3: Gap Analysis
- Compare bronze sources to the approved target model
- **Source Column Reconciliation gate (mandatory, before any transformation SQL):** `DESCRIBE` /
  `information_schema.columns` every source, and confirm every referenced source column exists —
  SELECT columns, WHERE/filter columns, AND the natural-key expression. Re-map or `CAST(NULL AS
  <type>)` a spec column that isn't present; **halt** if >20% of an entity's columns are unresolved.
  The spec names TARGET columns — never emit SQL against a bronze column not verified here (this is
  the build-side half of the source↔target contract; prevents the 13/17-rewrite failure mode).
- Flag unmapped target columns as GAPS
- Flag unmapped source columns as enrichment opportunities
- Write `gap_analysis.md`
- **Write `docs/.pipeline/state/silver/etl_state.md`** — one row per entity, all `NOT_STARTED`, with tier, type
  (DIM/FACT), `Wave` (1=dims, 2=facts, 3=gold), and `Assigned_Session` (blank for single-session;
  assign tier/wave ranges when fanning out to parallel batch sessions). This closes the **Setup**
  role (see Checkpoint & Session Roles above).
- See: `discovery-and-gap-analysis.md`

### Phase 4: Scaffold (BATCHED — author ≤ 4, load + grade, then next)

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
- **Grade-gated batching loop (mandatory):** author in batches of **≤ 4 entities by load-order
  tier**, and for each batch run the **post-load DQ gate** below before authoring the next.
  Do NOT generate all DDL + all load notebooks in one pass — that overflows context and drifts silently.
  See `autonomous-validation` Batching Discipline (≤4); the DQ gate composes with the existing
  author→run→verify cap. Phase 4 and Phase 5 interleave per batch:
  ```
  For each batch of ≤ 4 entities (grouped by load-order tier):
    1. Author the DDL + load notebook for each entity in the batch.
       The load notebook declares its own widgets and holds the MERGE.
    2. Run the real load for each entity in load order (Phase 5).
    3. Run post-load DQ on the real table (PK/FK/population/row-count) + grade A–F, and — on the
       FIRST entity of each load strategy per batch — run the load a SECOND time and assert
       row-count + key-set stability (the idempotency recheck).
    4. The batch does not advance until every entity is Grade A (or HUMAN NEEDED) and its
       idempotency recheck passed. Record per-entity results toward the build manifest (Phase 6.5).
  ```
- Apply defensive coding patterns from `merge-and-defensive-coding.md`
- Follow naming standards for all generated code

### Phase 5: Load, DQ & Grade (the per-entity gate)
- Run each notebook individually in load order (the real load) — up to 5 fix attempts per notebook.
- **Post-load DQ on the real table:** PK uniqueness, FK orphan rates, column population, row-count
  sanity (see `testing-and-grading.md`). Grade A–F using the rubric.
- **Idempotency recheck (cheap, on real data):** for the first entity of each load strategy in the
  batch, run the load a SECOND time and assert the row count and surrogate-key set are unchanged.
  A second-run row-count change (or a `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`
  failure) means the dedup PARTITION BY doesn't match the surrogate-key columns — fix the notebook,
  not the check. See `testing-and-grading.md` "Idempotency recheck".
- Iterate to Grade A (up to 5 fix attempts per notebook); flag unresolvable issues as HUMAN NEEDED.
- Record per-entity results (Grade, idempotency PASS/FAIL, accepted exceptions) for the build
  manifest (Phase 6.5).
- **Update `docs/.pipeline/state/silver/etl_state.md`** — flip each entity's row `NOT_STARTED`→`BUILT` when its load
  notebook is authored, then `BUILT`→`TESTED` when the real load reaches Grade A **and** its
  idempotency recheck passes — where the recheck is run on the first entity of each load strategy
  and inherited (`n/a`) by siblings using the same shape, so a sibling reaches `TESTED` on Grade A
  alone. This is the per-batch checkpoint that makes a fresh session resumable and lets parallel
  batch sessions coordinate within a wave (see Checkpoint & Session Roles).
- See: `testing-and-grading.md`

### Phase 6: Bundle & Deploy (DABs are the core deploy pattern)
- **Finalize completeness gate (if multi-session):** before authoring the bundle, read
  `docs/.pipeline/state/silver/etl_state.md` and confirm **every** entity row is `TESTED` (all waves). If any row is
  `NOT_STARTED`/`BUILT`, report exactly which entities/waves still need a batch session and
  **STOP** — do NOT bundle/deploy a partial model. See Checkpoint & Session Roles.
- Only after ALL notebooks reach Grade A (or HUMAN NEEDED)
- Generate `databricks.yml` + `resources/{job_name}.job.yml`
- **Daily job = loads + validation only; DDL is NOT a task** (tables are created once as setup — see Phase 2). Task DAG: dims → facts → validate_silver → gold → validate_gold
- **Every serverless job needs a job-level `environments:` block** (`- environment_key: default` / `spec: {client: "1"}`) — without it the deploy 400s with "Job environment 'default' ... not defined in field 'environments'". Add it to the daily-load job. Omit only for classic `job_clusters`. See `deployment-and-dab.md` "Serverless jobs REQUIRE a job-level environments block".
- **notebook_path references the load notebook directly** (it declares its own widgets and takes `base_parameters`): `../src/silver/transformations/dim_{entity}`, `../src/gold/transformations/{name}`, `../src/silver/validate_silver`. See `deployment-and-dab.md`.
- **Deploy is environment-routed — detect WHERE you run before deploying (a hard gate).** On Genie Code's default **serverless notebook compute the CLI is BLOCKED** ("CLI only supported from web terminal"). Separate **author** (own it fully: write/validate `resources/*.yml`) from **deploy** (a gated handoff):
  - **Serverless / no CLI →** author + `bundle validate` (if available), then **hand off**: tell the user to open the **Deployments panel (🚀) → Deploy**. Do NOT run the deploy.
  - **Web terminal (x86) / local / CI →** `databricks bundle deploy -t dev`, then `databricks bundle run {job_name}`. The deploy uploads `src/**` sources as notebook objects (workflow A) or references existing workspace objects (workflow B) and owns the job identity.
- **NEVER (this stops the deploy spiral):** shell out to `databricks bundle deploy` from serverless; retry the same failed CLI command; reconstruct bundle resources via the SDK/REST (`w.workspace.import_()`, `w.jobs.reset`) — that causes state drift + orphans; or promise "just deploy one job" (deploy always applies the whole bundle). If the supported path is blocked, **STOP and tell the user the manual step.** One clean attempt + handoff beats twenty retries (also preserves session context).
- **After writing any DAB YAML, read it back (non-empty + parses); after deploy, verify the job exists** — never report success off the deploy command alone. Iterate on `bundle validate` → fix → re-validate; on deploy errors, diagnose the real error text, don't blindly retry.
- See: `deployment-and-dab.md` ("Deploy is environment-routed")

### Phase 6.5: Emit Build Manifest (typed build→validate handoff)
- After the pipeline is built + graded (all entities Grade A / HUMAN NEEDED, idempotency recheck passing),
  write `docs/.pipeline/handoffs/silver/build_manifest.md` from `templates/build_manifest.md` — the **as-built mirror** of
  `etl_detailed_spec.md` (confirmation-plus-deltas, NOT a restatement).
- Populate all sections from `progress.md`, the spec, the DDL, and the Phase-5 load run:
  strategy applied per entity (+ deviation from spec §5), recency column used, FK-resolution
  attribute per FK, **the as-built column inventory (§3.5 — the exact physical PK/FK/measure
  column names in the DEPLOYED table, using dimensional names for `dimensional`/`hybrid`-gold
  entities, NOT the silver natural keys they were sourced from)**, filters applied, accepted
  exceptions/relaxations, final row counts (drift baseline seed), threshold seeds applied
  (spec §6 as set), and per-entity post-load DQ grade + idempotency-recheck result.
- **§3.5 is the check contract `domain-model-validation` codes against** — populating it prevents
  the validation skill from guessing column names off the spec/source and failing its first job
  run (the recurring gold-validation failure mode). Take the names from the built table (a
  `DESCRIBE` of each deployed entity), not from the spec.
- This is the authoritative input for `domain-model-validation` — it reads the manifest instead
  of reverse-engineering intent from MERGE SQL.
- See: `templates/build_manifest.md`, `progress-tracking.md`

### Phase 7: Integration Test
- Run the full job end-to-end
- Validation notebooks run as the final recurring gates (one per layer)
- If cross-notebook issues surface: fix and re-run

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

## Critical Rules (Always Apply)

1. **Read `naming-standards.md` before generating ANY DDL, MERGE, or DAB artifact** — it is the authoritative standard; resolve customer-specific values (catalogs, source-system enum, casing, thresholds) from `conventions.yml`, not from Acuity literals
2. **Catalog/schema are RUNTIME PARAMETERS, not literals — carried by the load notebook's own widgets.** The load notebook (`transformations/{entity}`) declares its own widgets — `CREATE WIDGET TEXT silver_catalog DEFAULT ''`, `silver_schema`, `gold_*`, one `src_{logical}` per bronze source, `job_name` — and the DAB job passes them via `base_parameters`. In the **SQL shape** it sets the session via `USE CATALOG/SCHEMA IDENTIFIER(:silver_catalog)` (parameter marker `:name`), references target/silver tables **unqualified**, and reads bronze via `IDENTIFIER(:src_{logical} || '.{table}')`. In the **Python shape** `:param` markers do NOT auto-bind inside `spark.sql()` — read each widget and interpolate the name into `spark.sql(f"...")` instead (config-sourced values only; see `deployment-and-dab.md` Shape B). **No catalog/schema/host literals** — the same notebook promotes dev→prod unchanged; the DAB `variables` supply per-target values, defaults live in `conventions.yml`. See `deployment-and-dab.md` "Runtime Parameters".
3. **Never use `UPDATE SET *` or `INSERT *`** — always explicit column lists
4. **Always deduplicate source data** — `ROW_NUMBER()` on natural key
5. **Keys follow `output_model` (see `conventions.yml`).** In **`dimensional`** mode (+ `hybrid` gold): surrogate `{Entity}_Key` (BIGINT, SHA2 hash) — never `_sk`, never IDENTITY. In **`normalized`** mode (+ `hybrid` silver): **follow the vibe model's PKs** (keep its `{entity}_id` / whatever it defines; `surrogate_key_method: NONE`) — add a surrogate only where the model PK is composite/mutable or cross-source integration needs one. Method stays SHA2/BIGINT/no-IDENTITY wherever a surrogate IS used. `scd_strategy: type_2` forces surrogates on (dimensional/hybrid-gold only). See `naming-standards.md` "⚠️ Precedence & key strategy by mode".
6. **Business columns: `Pascal_Snake_Case` in `dimensional` mode** — system/metadata columns: `_lower_snake_case` with leading underscore (ALWAYS). In **`normalized`/`hybrid`-silver**: match the vibe model's business-column names + casing exactly (e.g. lowercase `snake_case`); do not re-case them. Metadata/audit columns stay `_lower_snake_case` in all modes. See `naming-standards.md` "⚠️ Precedence".
7. **FK columns use the same name as the parent dim's PK** — default to -1 via COALESCE, never NULL
8. **Every column and table gets a COMMENT**
9. **Notebook headers.** DDL notebooks (always SQL) and load notebooks both start with `-- Databricks notebook source` (or `# Databricks notebook source` for Python load notebooks), then `CREATE WIDGET TEXT` for catalog/schema (+ `src_*`, `job_name`) → `USE CATALOG/SCHEMA IDENTIFIER(:...)` in their own cells. Catalog/schema are NEVER hard-coded. See `deployment-and-dab.md` "Notebook-format contract".
10. **Extension-less notebooks, format follows `etl_language`.** Load notebooks and validation are **extension-less notebook objects** (the extension is what marks a plain FILE that a `notebook_task` can't execute). Format matches `conventions.yml` `etl_language`: `sql` → native SQL notebook (`-- Databricks notebook source`, `-- COMMAND ----------`); `python` → Python notebook (`# Databricks notebook source`, `# MAGIC %sql` cells). DDL stays a `.sql` file (deployed by a setup job). **Do not emit `.sql`/`.py` files in `transformations/`** — a lingering `.sql` twin next to the notebook is a bug (it's what broke the first Meridian pass).
11. **One notebook per table** — every dim, fact, bridge, and gold entity gets its own load notebook. Never combine multiple entities into one notebook.
12. **Per-layer, per-role subfolders** — `src/{layer}/ddl/`, `src/{layer}/transformations/`. Never mix layers or roles in the same folder. Validation notebooks (`validate_{layer}`) live directly under `src/{layer}/`.
13. **Phase gating** — never create DAB config until all notebooks are individually loaded and graded
14. **DABs are the core (and only) deploy pattern — but the deploy is environment-routed.** The bundle owns job + notebook identity. **Detect the environment first (Step 0):** on serverless the CLI is blocked — author + validate, then hand off to the Deployments panel (🚀); only in a web terminal / local / CI do you run `databricks bundle deploy` + `bundle run`. Never hand-import notebooks or create/reset jobs via the SDK, never write an imperative orchestrator, never subprocess the CLI on serverless, and never deploy a single job in isolation (deploy applies the whole bundle). DDL is NOT a daily-job task — it runs once as setup (Genie Code or a separate `{domain}_ddl_setup` bundle job); the daily job is loads + validation only. See `deployment-and-dab.md` "Deploy is environment-routed".
15. **Progress tracking** — maintain `progress.md` after every phase transition
16. **Requirements gate** — never run discovery queries until `business_requirements.md` is graded B or better
17. **Post-load DQ gate per entity — `merge_notebook` mode.** A batch does not advance until every entity in it reaches Grade A (or HUMAN NEEDED) on post-load DQ against the real table (PK/FK/population/row-count), and the first entity of each load strategy passes a twice-run idempotency recheck (row count + key set stable). This is the build-time "landed as intended" gate on real data; comprehensive data-state validation is a separate later skill (`domain-model-validation`). See `testing-and-grading.md`. **In `etl_type: sdp_pipeline` mode this gate does NOT apply** — SDP ships no build-time tests (rule 22); the `TESTED`-gating in rules 18–19 likewise applies only to the merge path.
18. **Emit the build manifest** — after the pipeline is built + graded, write `docs/.pipeline/handoffs/silver/build_manifest.md` (the typed build→validate handoff — as-built mirror of `etl_detailed_spec.md`, incl. per-entity post-load DQ grade + idempotency-recheck result). See `templates/build_manifest.md`
19. **`docs/.pipeline/state/silver/etl_state.md` is the checkpoint of record (large-domain builds)** — Setup writes it (every entity `NOT_STARTED` + tier + type + wave), only the Phase 5 post-load DQ gate flips a row to `TESTED`, and Finalize refuses to bundle until all rows are `TESTED`. A batch session touches only its assigned rows and honors the **wave barrier** (no wave-`N` entity starts until every wave-`<N` entity is `TESTED`: dims `wave:1` → facts `wave:2` → gold `wave:3`). This is what makes the build resumable after overflow and safe to fan out across parallel sessions within a wave. See Checkpoint & Session Roles. **In `etl_type: sdp_pipeline` mode there is no post-load DQ gate (rule 22), so this rule's `TESTED` requirement does NOT apply** — an SDP entity advances/finalizes on `AUTHORED` (its declarative source written); the wave barrier still applies on `AUTHORED`, and Finalize bundles once all rows are `AUTHORED`.
20. **`etl_type: sdp_pipeline` — DDL lives in the flow.** No separate DDL-setup step; schema
    (columns/types/COMMENT/`CONSTRAINT ... EXPECT`/CLUSTER BY) is inline in each
    `CREATE STREAMING TABLE`/`MATERIALIZED VIEW`. The "DDL is SETUP" rule does NOT apply in this mode.
    🔴 **A Materialized View column spec MUST NOT contain `PRIMARY KEY`/`FOREIGN KEY`** — it is a
    `PARSE_SYNTAX_ERROR` on SDP serverless (broke all 17 files in the sales-order run). The only
    inline constraint is `CONSTRAINT <name> EXPECT (...)`; enforce PK uniqueness with a grain
    `EXPECT ({natural_key} IS NOT NULL) ON VIOLATION DROP ROW`. (Merge-path DDL tables keep their
    `ALTER TABLE ADD CONSTRAINT PRIMARY KEY`; an AUTO CDC streaming table may declare a CDC
    `PRIMARY KEY`.) See `sdp-pipeline-development.md` "DDL lives inside the flow".
21. **`etl_type: sdp_pipeline` — NO parameterization; hardcode bronze paths.** The native LDP
    `parameters:` block is a beta that only half-works (breaks on `STREAM IDENTIFIER(:param)`), so
    SDP writes bronze paths as fully-qualified `catalog.schema.table` literals in each source (MV +
    ST, SQL + Python). Only the silver WRITE target is parameterized (DAB `${var}`). No
    `parameters:` block, `:param`, `IDENTIFIER(:param)`, `spark.conf.get`, or widget bridge. See `sdp-pipeline-development.md`.
22. **`etl_type: sdp_pipeline` — NO build-time testing at all.** Do NOT author the LDP unit-test
    framework (`pyspark.pipelines.testing`, a beta + Editor-only — no bundle/CLI run path), a
    post-load validation notebook, or any TDD gate. The SDP build ships no `tests/` folder and no
    validation artifact. Confidence = inline `EXPECT` + the event log while running, and the
    downstream `domain-model-validation` skill afterward. Revisit when the LDP testing framework
    leaves beta. See `sdp-pipeline-development.md`.
23. **`etl_type: sdp_pipeline` — FILE model for sources.** Pipeline sources are plain `.sql` files
    with NO `-- Databricks notebook source` header, included via a single `libraries: [glob: {include:
    ../src/silver/pipeline/**}]`, with `root_path:` set to the source tree. Never the notebook-source
    header, never per-entity `notebook:` libraries (extension-stripping deadlock). Dev target
    `source_linked_deployment: true`; prod `false`. See `sdp-pipeline-development.md`.
24. **Validate source columns before generating SQL (both modes).** The spec names TARGET columns;
    the bronze column that populates each is often different or absent. Before emitting any
    transformation SQL, `DESCRIBE`/`information_schema` every source and confirm every referenced
    column exists — SELECT columns, WHERE/filter columns, and the natural-key expression (which must
    use SOURCE column names, e.g. `TRIM(vtweg)`, not the target `channel_code`). Re-map or
    `CAST(NULL AS <type>)` a missing column; **halt** if >20% of an entity's columns are unresolved.
    A missing filter column → `WHERE FALSE -- PLACEHOLDER: <reason>`, not a guessed predicate. See
    `discovery-and-gap-analysis.md` "Source Column Reconciliation gate".
25. **Serverless type casts — never the `TRY(...)` wrapper.** `TRY(TO_DATE(...))` / `TRY(CAST(...))`
    are unsupported on serverless (recurring across 3 projects). Always use the builtins directly:
    `TRY_TO_DATE(col, fmt)`, `TRY_CAST(col AS type)`. See `sdp-pipeline-development.md` Rule B.
26. **`etl_type: sdp_pipeline` — build tier-by-tier, dry-run before the full deploy.** Do NOT author
    all sources then trigger one pipeline update ("write-all-then-test" — it surfaced 14 errors at
    once and cost ~45 min). Author by load-order tier (T0 dims first), dry-run each new source's
    `AS SELECT` body (schema/`EXPLAIN`) to catch UNRESOLVED_COLUMN / syntax / PK-constraint errors
    before deploy, and navigate to the SDP **pipeline editor** for authoring/fixing (better SDP
    tooling than the file editor). See `sdp-pipeline-development.md` "Incremental build loop".
