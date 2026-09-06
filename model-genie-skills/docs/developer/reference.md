# Reference — the skill suite, its handoffs, and its knobs

Information-oriented lookup. This doc states *what is* — it doesn't teach (see
[tutorial.md](tutorial.md)) or walk tasks (see [how-to/](how-to/)) or argue *why* (see
[explanation.md](explanation.md)). Scan for the fact you need.

## Skill catalog

Six skills. Four form the loop (one domain at a time); two are cross-cutting.

| # | Skill | Station | One-liner | Read/Write |
| --- | --- | --- | --- | --- |
| 1 | `domain-model-assessment` | **Assess** | Inspect the empty vibe model, profile bronze, fold in existing silver/gold, produce S2T mapping + gap registry + fit grades, pre-fill build handoff docs. | Read-only (+ scoped metamodel edits) |
| 2 | `etl-development-framework` | **Build** | Turn the assessment handoff into pipelines: DDL, per-entity load notebooks (gated by a post-load DQ check on the real table), a DQ validation notebook, a DAB job. *(SDP mode: one whole-domain Lakeflow Declarative Pipeline, no build-time test.)* | Writes model + code |
| 3 | `domain-model-validation` | **Validate** | Prove the load landed (0 FK orphans, 0 dropped rows, no silent nulls); per-table regression notebooks, `_validation_*` tables, scorecard, dashboard. | Read-only + `_validation_*` writes |
| 4 | `domain-documentation` | **Document** | Diátaxis docs *for the domain's consumers*: domain narrative, Model Guide, auto-generated Genie space, insight tutorials. | Writes docs + Genie space |
| — | `autonomous-validation` | *cross-cutting* | Execution discipline for agents at scale: scratchpad-validate → confirm → persist; batching; the human-in-the-loop contract. Loaded alongside the loop skills. | Guidance only |
| — | `domain-sync` | *steady-state* | After the model exists, keep artifacts in sync after a point fix: change-impact matrix, `synced-against` stamps + staleness linter, scoped regeneration, generates `ARCHITECTURE.md` + `NEXT_STEPS.md`. | Orchestrates + writes stamps/maps |

## The handoff-artifact chain

Handoff between stations is through **documents, not chat**. Discovery runs once (assessment)
and everything downstream inherits it.

```
assessment ──▶ etl_detailed_spec.md  ──▶ build
               business_requirements.md
build      ──▶ build_manifest.md      ──▶ validate
validate   ──▶ validation_summary.md  ──▶ document
validate   ──▶ remediation_brief.md   ──▶ build   (only when a grade degrades)
```

| From → To | Handoff artifact | Contents |
| --- | --- | --- |
| Assessment → Build | `business_requirements.md` + `etl_detailed_spec.md` | Pre-filled requirements + model/mapping spec (build's input) |
| Build → Validate | `build_manifest.md` | As-built mirror of the spec: grain, filters, FK resolution, final row counts, refresh schedule, per-entity post-load DQ result |
| Validate → Document | `validation_summary.md` | Per-entity grades, resolved/open gap deltas, changed Genie caveats |
| Validate → Build | `remediation_brief.md` | Failing checks, root-cause category, suggested fix — generated only when a grade drops below B |

> **Where these files live.** The per-domain output is organized by audience.
> - **Durable design record** (assessment's output): `docs/design/` — `business_requirements.md`,
>   `etl_detailed_spec.md`, `s2t_mapping_report.md`, `gap_analysis.md`, `gold_layer_assessment.md`.
> - **Skill-to-skill handoffs + state** (transient plumbing, hidden): `docs/.pipeline/` —
>   `handoffs/{silver,gold}/build_manifest.md`, `handoffs/{silver,gold}/validation_summary.md`,
>   `handoffs/{silver,gold}/remediation_brief.md`, `state/run/progress.md`, `state/{silver,gold}/*_state.md`.
> - **Consumer deliverable** (documentation's output): `docs/tutorials/`, `docs/reference/`,
>   `docs/explanation/` (`domain_narrative.md`), `docs/contributor/`.
> - `ARCHITECTURE.md` at the project root (owned by `domain-sync`) opens with a Directory Guide
>   that maps all of the above, since `docs/.pipeline/` is hidden.

## Input / output at a glance

| Skill | Required input | Key outputs | Consumed by |
| --- | --- | --- | --- |
| assessment | Vibe model (empty tables + comments) + bronze catalog(s) | S2T mapping, gap registry, `business_requirements.md`, `etl_detailed_spec.md` | build |
| build | `docs/design/business_requirements.md` (Grade B+) + `docs/design/etl_detailed_spec.md` | DDL, MERGE/load notebooks, DAB job, DQ notebook, `gap_analysis.md`, `.pipeline/state/run/progress.md`, `.pipeline/handoffs/{layer}/build_manifest.md` | validate |
| validation | Completed project (`.pipeline/state/run/progress.md` Phase 5+) | Per-table narrative notebooks, `_validation_*` tables, dashboard, `.pipeline/handoffs/{layer}/validation_summary.md`, (cond.) `.pipeline/handoffs/{layer}/remediation_brief.md` | document, build (via remediation) |
| documentation | `validation_summary.md` + `build_manifest.md` + `progress.md` + DDL (from `.pipeline/`) | Domain narrative (`docs/explanation/`), Model Guide, Genie space, tutorials, slim per-domain maintenance guide | domain data consumers + maintainers |

## Worked examples — seeing the output assembled

Two examples in `examples/` show the full artifact set, one per flow:

| Example | Flow | Kind | Use it to |
| --- | --- | --- | --- |
| [`field_service/EXAMPLE_OUTPUT.md`](../../examples/field_service/EXAMPLE_OUTPUT.md) | `sdp_pipeline` / `normalized` (the default flow) | Illustrative, hand-authored | See what *your* tutorial run produces — the three-tier tree + sample handoff/narrative excerpts. `field_service` is self-contained and runnable. |
| [`sales_order_mvm/`](../../examples/sales_order_mvm/) | `sdp_pipeline` / `hybrid` (silver built) | **Real captured run**, checked in | Browse a complete, real run at realistic scale (17 silver tables, all Grade A) with all three `model_deviation` levers as gated decisions. Start at its [`README.md`](../../examples/sales_order_mvm/README.md) / [`EXAMPLE_OUTPUT.md`](../../examples/sales_order_mvm/EXAMPLE_OUTPUT.md). |

> The `sales_order_mvm/` run built and validated **silver only** — the dimensional gold star is
> *designed* (`docs/design/gold_layer_assessment.md`) but not built. It was executed against
> Meridian's live workspace, so its generated artifacts carry that workspace's catalog names; the
> model itself is self-contained (`model_setup.sql` + an MVM bronze generator), so you can reproduce
> the run in your own workspace by swapping catalogs. It's the concrete referent for the "sales-order
> run" cited as a hardening example across the skill files.

## The validation quality-tracking system (tables → dashboard → job)

The `domain-model-validation` skill doesn't just run checks once and print a grade — it stands up a
**persistent quality-tracking system** in the model schema so gaps, bugs, and grades stay visible
and trend over time. Three parts, all shipped by the skill:

| Part | What it is | Why it's there |
| --- | --- | --- |
| **Metadata tables** (`_validation_*`) | Five tables written into the model schema: `_validation_run` (one row per run), `_validation_table_result` (per-entity grade + row-count/grade deltas), `_validation_check_detail` (every individual check), `_data_drift_baseline` (frozen first-run stats), `_gap_registry` (every known gap/bug with a status: `OPEN \| IN_PROGRESS \| DEFERRED \| ACCEPTED \| RESOLVED`) | The durable record. Grades, gaps, and drift are *data*, queryable and diffable — not a transcript that scrolls away. |
| **Quality dashboard** | A 4-tab Lakeview dashboard (`{Domain} Validation Quality`): **Current State** (today's grades), **Historical Trend** (grades/row counts run-over-run), **Priority Backlog** (open gaps & bugs by priority/status from `_gap_registry`), **Integration Health** (fact→dim join integrity) | The at-a-glance surface for tracking gaps and bugs and watching quality move. Reads only from the `_validation_*` tables. |
| **Validation DAB job** | `resources/{domain}_validation.job.yml` — per-entity narrative tasks in load order + a terminal scorecard, deployable on a schedule (default: daily after the ETL job) | Re-run it any time — after a fix, a schema change, or on a schedule — to re-grade the model and see the improvement (or regression) land as a new row on the trend tab. |

**How improvement-over-time works:** each job run inserts a new `_validation_run` and per-entity
`_validation_table_result` rows, and the scorecard computes `Row_Count_Delta` and `Grade_Delta`
against the previous run. So the trend tab shows a table climbing from C → B → A as gaps close, and
a degradation (a grade dropping below B) automatically generates a `remediation_brief.md` handoff
back to the build skill. Run the job as part of any change to prove the change helped — and to catch
a regression the moment it happens.

> A gap opened in `_gap_registry` (say a deferred FK or an unmapped column) shows on the Priority
> Backlog tab until someone resolves it and its status flips to `RESOLVED` — the dashboard is the
> shared to-do list for the model's data-quality debt.

## Decision tree — "which skill do I use?"

```
I need to…
│
├─ Build a NEW domain model from scratch
│   └─ Start: domain-model-assessment  → etl-development-framework → validation → documentation
│      (this is the full loop — see tutorial.md)
│
├─ Add a NEW TABLE to an existing model
│   ├─ Source known?  Yes → etl-development-framework (single entity)
│   └─ Source known?  No  → domain-model-assessment (scoped to one entity) → etl-development-framework
│      (recipe: how-to/add-a-table.md)
│
├─ FIX a degraded table (grade dropped)
│   └─ domain-model-validation (remediation brief) → etl-development-framework (fix, re-test)
│      → domain-model-validation (POST_FIX confirm)
│      (recipe: how-to/fix-a-degraded-table.md)
│
├─ Check DATA QUALITY / run regression tests
│   └─ domain-model-validation (run the validation job)
│
├─ Set up a GENIE SPACE / create consumer docs
│   └─ domain-documentation
│
├─ Promote to PRODUCTION
│   └─ domain-model-validation (pre-deploy gate) → etl-development-framework (repoint catalogs, deploy)
│      (recipe: how-to/promote-to-production.md)
│
├─ Investigate a DATA DRIFT alert
│   └─ domain-model-validation (narrative notebook + drift detail) → accept baseline OR escalate to build
│      (recipe: how-to/investigate-drift.md)
│
└─ Apply a POINT FIX to a built model (close a gap, fix an FK, add a column) and keep docs honest
    └─ domain-sync (scoped regeneration + re-stamp) — do NOT hand-re-run each skill
       (recipe: how-to/re-sync-after-a-change.md)
```

## Human gates vs. auto-checks

The skills run **autonomously between gates**. Most "Gate:" lines in the SKILL.md phases are
**auto-checks** — the agent verifies the condition, reports a scorecard, and proceeds without
asking. You are pulled in only at a small number of **true human gates**.

**True human gates (the agent stops and asks):**
- Approve/reject proposed **model changes** and gap dispositions (assessment)
- Approve the **proposed model/DDL** before creation (build, Phase 1–2)
- Confirm **discovery exit criteria** before build (assessment)
- Accept a **known exception** or sign off a **Grade D/F** table (validation)
- A **metric PARITY miss** in gold (validation)
- Approve **prod promotion** / any destructive or irreversible action
- Review the **Genie space config** and the **domain narrative** for accuracy (documentation)

**Auto-checks (verify and continue — no prompt):** per-batch notebook execution, PENDING-row
landing, row-count/PK/FK assertions at build time, load-order sequencing, idempotent re-runs.

Expect roughly **4–6 true human gates per full lifecycle run** — not a prompt at every entity
or batch. If the agent asks "should I continue?" between notebooks, that violates the
human-in-the-loop contract; the correct behavior is report-and-proceed. This contract is
codified in the `autonomous-validation` skill.

## Providing context to a skill

Skills load automatically from your intent (below). They work best when you provide:

- **Project path** — where is the project folder?
- **Schema** — what `{catalog}.{schema}` are we targeting?
- **Scope** — full model, single entity, or specific issue?
- **Previous skill output** — reference the handoff doc or remediation brief by name.

| What you say | Skill loaded |
| --- | --- |
| "Assess this model against bronze" | domain-model-assessment |
| "Start the build" / "Build the ETL" | etl-development-framework |
| "Validate the model" / "Create regression tests" | domain-model-validation |
| "Generate documentation" / "Create a Genie space" | domain-documentation |
| "Fix `fact_…`" / "The grade dropped" | domain-model-validation → etl-development-framework |
| "I closed a gap / added a column — re-sync the docs" | domain-sync |

## conventions.yml — the single config surface

One file at the project root that all four loop skills + `domain-sync` read. Copy
`templates/conventions.yml`, fill it in, and the skills resolve naming, catalogs, source-system
tags, and thresholds from it instead of hard-coded literals. This table is the per-key
*mechanical* summary; for *how to choose* the knobs (which `output_model` to start with, why the
source map matters) see the decision guide
[how-to/fill-out-conventions.md](how-to/fill-out-conventions.md).

| Key | What it drives |
| --- | --- |
| `customer`, `domain` | Project/skill context, schema pattern substitution |
| `output_model` (`normalized` \| `dimensional` \| `hybrid`) | **The model SHAPE knob.** `normalized` (default) = 3NF SSOT port of the vibe model; `dimensional` = Kimball star; `hybrid` = normalized silver THEN a dimensional gold star downstream. See the variant matrix below. |
| `etl_type` (`merge_notebook` \| `sdp_pipeline`) | **The build MECHANISM knob** (orthogonal to `output_model`). `sdp_pipeline` (default) = one whole-domain Lakeflow Declarative Pipeline; `merge_notebook` = DDL + Type-1 MERGE trio + daily job. |
| `catalogs` (bronze/silver/gold/sandbox) | **Defaults** for runtime widgets + DAB `base_parameters`. Skills never CREATE catalogs; catalog/schema are runtime params, not authoring-time literals. |
| `schemas` (silver/gold/sandbox patterns) | Naming of generated schemas |
| `etl_language` (`sql` \| `python`) | Source-language of MERGE + validation notebooks. **DDL, Model Guide, Genie, dashboard are always SQL.** Validation inherits ETL's value. |
| `bronze_sources` (logical name → `catalog.schema`) | Per-source fully-qualified prefixes for multi-source (and cross-catalog) loads; also the single source of truth for assessment's schema search |
| `naming` | Table/column case, dim/fact/bridge prefixes, surrogate-key method (SHA2), FK naming |
| `audit_columns` | The `_source_system`, `_loaded_at`, … columns added to every table; event-time column for incremental facts |
| `source_systems` | Enum written into `_source_system` |
| `load_strategy` (thresholds) | Drives the per-entity FULL_MERGE / INCREMENTAL_MERGE / APPEND_ONLY / SDP decision |
| `gap_status_enum` | Shared statuses for `_gap_registry`, dashboard, Genie, `NEXT_STEPS.md` |
| `deployment` | Alert email, schedule cron, timezone — host resolved per-target in `databricks.yml`, never baked into SQL |

> **Invariant:** catalogs/schemas/hosts/emails are **never** baked into generated SQL. Generated
> notebooks declare widgets and read them at runtime; the DAB passes per-target values. The same
> notebook object promotes dev→prod unchanged.

### The `etl_type` × `output_model` matrix (variant templates)

`output_model` (shape) and `etl_type` (mechanism) are orthogonal — 2 × 3 = **six** valid
combinations. `templates/conventions.yml` is the single fully-annotated base; the six thin
**overlay templates** in [`templates/conventions-variants/`](../../templates/conventions-variants/README.md)
show only the blocks (`etl_type`, `output_model`, `schemas`, `naming`, `scd_strategy`) that change
per cell:

| | `normalized` | `dimensional` | `hybrid` |
|---|---|---|---|
| **`merge_notebook`** | `merge.normalized.yml` | `merge.dimensional.yml` | `merge.hybrid.yml` |
| **`sdp_pipeline`** | `sdp.normalized.yml` *(default cell)* | `sdp.dimensional.yml` | `sdp.hybrid.yml` |

A worked, runnable instance of all six against one real model is
`examples/field_service/conventions.field_service.*.yml` (the fast-loop bench domain). Key rules:
`hybrid` is layered (normalized silver → dimensional gold, gold reads silver never bronze);
`scd_strategy: type_2` is dimensional/hybrid-gold only; SDP mode swaps the mechanism, not the
shape (DDL in-flow, hardcoded bronze paths, no build-time test artifact).

## Troubleshooting

| Problem | Likely cause | Fix |
| --- | --- | --- |
| Skill not loading | Intent not recognized | Say explicitly: "Load the `{skill-name}` skill" |
| Build skipping discovery | `etl_detailed_spec.md` is fully filled | Clear the sections you want the skill to (re)discover |
| Validation shows Grade F | Table empty or PK dups | Run the load notebook first; check the ETL job ran |
| Genie giving wrong joins | UC FKs not registered | Re-run documentation UC-enrichment phase |
| Assessment finds no sources | Bronze schema names mismatch | Fix `bronze_sources` in `conventions.yml`; provide exact schema names |
| Dashboard empty | No validation runs yet | Run the validation job at least once |
| Docs contradict the data after a fix | Artifacts stale, not re-synced | Run `domain-sync` (don't hand-edit) — see how-to/re-sync-after-a-change.md |

## See also

- The bench charter (why this repo exists): [`../../CLAUDE.md`](../../CLAUDE.md)
- Repo layout + skills-layout rules: [`../../README.md`](../../README.md)
- Each skill's authoritative detail: `skills/{skill-name}/SKILL.md` and its reference files
