---
name: domain-documentation
description: Document a built domain model for its data consumers — the Document station of the loop. Use when generating Diátaxis docs (tutorials, how-to, reference, explanation), a Model Guide entry-point notebook, a column dictionary/reference, insight tutorials, a per-domain maintenance guide, or an auto-generated Genie space so the domain is queryable in natural language the moment it is built. Not for validating data quality (use domain-model-validation) or building ETL (use etl-development-framework).
---

# Domain Documentation Skill

> **⚙️ Load `autonomous-validation` alongside this skill — it is NOT pulled in automatically; nothing wires the two together, so load it explicitly at the session start.** (See its `When to Load` for the execution-discipline contract.) — it also hosts `commentary-protocol.md`, the closeout this skill emits.
> This skill validates sample queries across the domain, does atomic full-file writes, and runs the once-only Genie-space finalizer; the Documentation Completion Self-Audit (Critical Rule 16) leans on its gate.

## Overview

This skill produces the **documentation layer** for a completed ETL domain model,
following the Diátaxis framework (Tutorials, How-to Guides, Reference, Explanation).
Its four Diátaxis quadrants document **the domain that was built, for that domain's data
consumers** (analysts and stakeholders who will query the model) — not the skill suite. It
**owns all four quadrants**: it authors the domain narrative (Explanation), creates a
unified entry point (Model Guide notebook — Reference), auto-generates Genie space
configuration (How-to: sample queries + instructions), and builds tutorial notebooks (Tutorials).

It additionally emits **one auxiliary, non-Diátaxis artifact**: a lightweight, co-located
`docs/contributor/maintaining-this-domain.md` for the *developers* who later tend this specific
model (how to add/fix/re-sync THIS domain's tables via the skills). That maintenance guide
**links out** to the repo-level developer docs (`docs/developer/`) for the full skill-suite
explanation, decision tree, and cross-domain recipes rather than restating them here. Do not
confuse this auxiliary guide with a fifth Diátaxis quadrant — the four quadrants are for the
domain's data consumers; the maintenance guide is a pointer for the domain's maintainers.

Designed to run AFTER `domain-model-validation` has graded the model and emitted its
validate→document handoff (`docs/.pipeline/handoffs/silver/validation_summary.md`). This skill authors the domain
narrative here and links to it from the Model Guide rather than restating it
(links-over-duplication holds WITHIN the skill).

**What this skill produces:**
- Domain narrative (`docs/explanation/domain_narrative.md`) — Explanation quadrant; the model's story
- `Model Guide` notebook — Entry point with live reference queries. Named `{Domain} Model Guide` (or `Model Guide`), created at the **project root** (NOT under `docs/`)
- Genie space — a Databricks **asset** (created via `createAsset`, not a file), named `{Domain} Genie Agent` (single-layer) — `hybrid` creates TWO: `{Domain} Silver Genie Agent` + `{Domain} Gold Genie Agent`; created in the **project root folder** (NOT the user home directory), with its instruction text also exported to `docs/.pipeline/handoffs/genie_space_instructions.md` (for the staleness linter). See `genie-space-config.md`.
- Tutorial notebooks (`docs/tutorials/`) — Progressive, executable insight showcases for the domain
- Maintenance guide (`docs/contributor/maintaining-this-domain.md`) — *auxiliary, non-Diátaxis*: a
  lightweight per-domain "how to add/fix/re-sync THIS model via the skills" pointer for maintainers,
  linking out to the repo `docs/developer/` docs for the full suite explanation
- UC comment enrichment script (`docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`) — Audit and fill gaps in table/column COMMENTs and FK definitions
- `docs/.pipeline/state/run/documentation_state.md` — *(large-domain runs only)* per-table checkpoint (assigned session, `NOT_STARTED→ENRICHED→VALIDATED`) that makes UC enrichment + sample-query validation resumable across sessions (see Checkpoint & Session Roles)
- Optional `docs/reference/glossary.md` — standalone data dictionary if the term list outgrows the Model Guide's Glossary cell
- `docs/commentary/documentation-improvement-recommendations.md` — session closeout feedback per `autonomous-validation/commentary-protocol.md` (always emitted; folded forward from prior runs)

**Diátaxis mapping:**

| Quadrant | Artifact | Discovery Mechanism |
| --- | --- | --- |
| **Tutorials** | Executable notebooks | Linked from Model Guide; browsable in `docs/tutorials/` |
| **How-to Guides** | Genie space sample queries | Genie space = primary interface for analysts |
| **Reference** | Live INFORMATION_SCHEMA queries in Model Guide | Always current; can't go stale |
| **Reference** | *(optional)* `docs/reference/glossary.md` — data dictionary / glossary | Linked from Model Guide Cell 9 when the term list outgrows inline |
| **Explanation** | Domain narrative (**produced by this skill** — `docs/explanation/domain_narrative.md`) | Linked from Model Guide |

The four quadrants above are all **for the domain's data consumers**. Separately, this skill
emits one **auxiliary (non-Diátaxis)** artifact for the domain's *maintainers*:

| Not a quadrant | Artifact | Purpose |
| --- | --- | --- |
| **Maintenance pointer** | `docs/contributor/maintaining-this-domain.md` | Lightweight per-domain "add/fix/re-sync THIS model via the skills" guide; links out to repo `docs/developer/` for the full suite explanation |

**Scope:** Documentation generation only. Does not modify model tables or validation
metadata. Reads from INFORMATION_SCHEMA, DDL notebooks, `docs/.pipeline/handoffs/silver/validation_summary.md`,
`docs/.pipeline/handoffs/silver/build_manifest.md`, and `docs/.pipeline/state/run/progress.md` to generate documentation artifacts (the domain
narrative among them).

---

## Reference Files

| File | Content |
| --- | --- |
| `phase-protocol.md` | **Detailed 6-phase execution** — full per-step protocol for Phases 1–6. `SKILL.md` carries the phase summary; this is the how-to. |
| `domain-narrative.md` | Generation rules for the domain narrative (`docs/explanation/domain_narrative.md`) — the Explanation quadrant |
| `model-guide.md` | Template and generation rules for the entry-point Model Guide notebook |
| `genie-space-config.md` | Auto-generation rules for Genie space: sample queries, instructions, UC enrichment |
| `tutorials.md` | Tutorial notebook generation: progressive learning paths, executable examples |
| `contributor-guide.md` | Generation rules for the slim, per-domain `docs/contributor/maintaining-this-domain.md` (domain-local maintenance recipes + link out to repo `docs/developer/`) |

---

## Layer & ETL-type Gate (read FIRST — it reshapes the templates)

The default templates in the reference files were authored for the common case: a
**single-schema silver** model built by **merge notebooks**. Two `conventions.yml` knobs change
the shape of what this skill produces, and you MUST resolve them from `docs/.pipeline/state/run/progress.md` /
`conventions.yml` before generating anything:

| Knob | Value | What changes |
| --- | --- | --- |
| `output_model` | `normalized` \| `dimensional` | **Single-schema path** — one catalog/schema; the default templates apply as-written. |
| `output_model` | `hybrid` | **Dual-schema path** — a normalized silver schema AND a dimensional gold schema. Documentation covers BOTH layers: 4-widget Model Guide, **two Genie spaces (one per layer: `{Domain} Silver Genie Agent` + `{Domain} Gold Genie Agent`)**, two validation summaries. See the "Hybrid / multi-schema" variant blocks in `model-guide.md`, `genie-space-config.md`, and `domain-narrative.md`. |
| `etl_type` | `merge_notebook` | DDL, transforms, and loads are **separate** notebooks; `src/silver/ddl/ddl_{entity}.sql` is the COMMENT write-target (Rule 8 as-written). |
| `etl_type` | `sdp_pipeline` | **There are NO separate DDL files.** The `CREATE OR REFRESH MATERIALIZED VIEW/STREAMING TABLE` statements in `src/{layer}/pipeline/*.sql` ARE both the transform and the schema definition; COMMENTs are inline in the column list and applied atomically when the pipeline runs. Phase 3 audits the **pipeline** files, not a `ddl/` dir — see the SDP EXCEPTION in Phase 3. |

**Hybrid path — what "cover both layers" means concretely:**
- **The gold artifacts come from a SECOND validation run.** `domain-model-validation` has no
  built-in two-schema mode — a hybrid domain is validated by running that skill **once per layer**:
  once against the silver schema (emits `docs/.pipeline/handoffs/silver/validation_summary.md` + its `_validation_*` tables in
  the silver schema) and once against the gold schema (emits the gold handoff + its `_validation_*`
  tables in the gold schema). The gold handoff is conventionally named `docs/.pipeline/handoffs/gold/validation_summary.md`
  / `docs/.pipeline/state/gold/validation_state.md` to avoid clobbering the silver ones. **Confirm both runs happened
  before starting** — if only silver was validated, the gold layer is unvalidated and you cannot
  document gold health honestly; stop and report that the gold validation run is missing.
- **Read the gold handoff with a graded fallback** (do not silently ship empty gold data):
  1. `docs/.pipeline/handoffs/gold/validation_summary.md` — the typed handoff, if complete.
  2. If it is incomplete/missing sections (no per-entity grade table, stale "remaining steps") →
     `docs/.pipeline/state/gold/validation_state.md` for per-entity grades + gap details. (An incomplete gold summary
     is a known upstream validation-skill formatting defect — note it in the run log.)
  3. If BOTH are absent or unusable → read the gold schema's own `_validation_table_result` /
     `_validation_run` **live** (the gold validation run created them in the gold schema) to recover
     grades. Only if there is no gold `_validation_*` table either has the gold layer genuinely not
     been validated → **stop and report**, don't ship a hybrid narrative/Model Guide with fabricated
     or blank gold health.
- **Schema resolution.** Silver and gold live in separate schemas (e.g.
  `..._silver_sdp` and `..._gold_sdp`), **each with its own `_validation_*` tables** (from its own
  validation run). Every template that hard-codes `{silver_catalog}.{silver_schema}` needs a gold
  counterpart; the variant blocks show how.
- **Analytics framing.** In Genie and the narrative, the **gold star is the preferred analytics
  surface** (clean star joins); **silver 3NF is for operational detail / lineage** or entities
  gold doesn't cover.

> `dimensional` is NOT the hybrid path — a pure Kimball star already IS the single documented
> schema, so it uses the single-schema templates with dim/fact framing. Only `hybrid` triggers
> the two-schema variants.

---

## When to Load This Skill

Load when:
- User asks to "document the model", "create a Genie space", "build tutorials"
- User asks for a "Model Guide" or "entry point" to a data model
- User asks "how do I onboard someone to this model?"
- User wants to generate sample queries or enrich UC metadata
- User asks for a per-domain "how do I maintain/update THIS model" guide
- User asks to set up a Genie space for a completed silver schema
- User asks for a "reference doc" or "column dictionary" for their model

Do NOT load for:
- Validating data quality — use `domain-model-validation`
- Building ETL — use `etl-development-framework`
- Discovering sources — use `domain-model-assessment`
- Answering one-off questions about the data (just query it directly)
- "How do I use the skill suite?" / the full decision tree + cross-domain recipes — that is the
  repo-level developer documentation (`docs/developer/`), not a generated per-domain artifact.
  This skill only emits a *slim* per-domain maintenance pointer that links to those docs.

---

## Prerequisites

Before this skill can execute, the following must exist:
- A completed ETL project with `docs/.pipeline/state/run/progress.md` showing Phase 5+ passed
- `docs/.pipeline/handoffs/silver/validation_summary.md` — the validate→document handoff (per-entity grades, resolved/open
  gap deltas, changed Genie caveats), produced by `domain-model-validation`
- `docs/.pipeline/handoffs/silver/build_manifest.md` — the build→validate manifest (grain, filters, FK resolution, final
  row counts, refresh schedule), produced by `etl-development-framework`; source for freshness/
  coverage and narrative source-system detail
- Schema source-of-truth files carrying COMMENTs on tables and columns (the ETL skill mandates this);
  Phase 3 audits them and fills any gaps **into those files**, treating them as the write-target, not
  just a source. **Which files depends on `etl_type`:** `merge_notebook` → DDL notebooks
  (`src/silver/ddl/`); `sdp_pipeline` → the pipeline `.sql` files (`src/{layer}/pipeline/`), which carry
  inline COMMENTs and ARE the schema (no separate `ddl/` dir). For `hybrid`, both the silver and gold
  layer directories.
- Validation suite (narrative notebooks) — for linking from Model Guide
- Known gaps / accepted exceptions documented (for honest Genie instructions)

The domain narrative (`docs/explanation/domain_narrative.md`) is **produced by this skill** (Phase 2), not a
prerequisite input — it is authored from `validation_summary.md` + `build_manifest.md` +
`docs/.pipeline/state/run/progress.md` + DDL.

---

## Checkpoint & Session Roles (resumable execution)

Documentation is **mostly singleton synthesis** — one narrative, one Model Guide, one Genie space
per layer (Rule: one space per schema; `hybrid` → silver + gold) — so unlike ETL/validation its parallel value is low. But on a full
16–17-entity domain the genuinely per-entity, context-eroding work — **Phase 3 UC enrichment**
(per table) and **Phase 5 sample-query validation** (15–25 queries) — can still overflow a single
session. The primary win here is **resume after overflow**, using the same Setup/Batch/Finalize
split and mutable checkpoint file that `domain-model-validation` (`validation_state.md`) and
`etl-development-framework` (`etl_state.md`) use — kept aligned.

### The checkpoint file — `docs/.pipeline/state/run/documentation_state.md`

The **Setup** session writes it; every **Batch** session updates only its own rows; the
**Finalize** session reads it to confirm completeness before creating the Genie space(s).

```markdown
# Documentation State — {domain}
Updated: {YYYY-MM-DD HH:MM} · Setup run: {run stamp} · Total tables: {N}

| Table | Assigned_Session | Doc_Status | Notes |
|---|---|---|---|
| dim_plant   | setup     | VALIDATED   | comment present; 3 sample queries non-empty |
| fact_orders | session_A | ENRICHED    | comment written; queries not yet re-run |
| fact_returns| session_B | NOT_STARTED | — |
```

- **`Doc_Status` enum:** `NOT_STARTED → ENRICHED → VALIDATED`. `ENRICHED` = the table's UC
  COMMENT is written (verifiable in `INFORMATION_SCHEMA`); `VALIDATED` = its fact-group sample
  queries were also executed non-empty. Sample-query "done-ness" is **not** naturally persisted as
  queryable state, so on resume/finalize the fact group's queries are simply **re-run** (they are
  cheap and are the same queries the Genie space will hold) rather than trusted from the file alone.
- Writes are atomic full-file replacements (`readFile` → edit → write back) — `autonomous-validation`
  Known Limitation #6.

### The three session roles (the 6 phases split by singleton-ness)

> Phase numbers below map to the summary table under **6-Phase Execution Model** and the full
> per-step protocol in `phase-protocol.md`.

Phases 1, 2, 4 (context, narrative, Model Guide) and Phase 6 (tutorials, maintenance guide) are
**singletons**; the Genie space in Phase 5 is a singleton too (exactly one space). Only Phase 3
(UC enrichment) and Phase 5's *query validation* are per-table fan-out.

| Role | Runs | Does | Stops when |
|---|---|---|---|
| **Setup** (once) | Phase 1 + 2 + 4 | Gather context, author domain narrative + Model Guide, **write `documentation_state.md` with every table `NOT_STARTED`** | State file written; synthesis singletons done |
| **Batch** (1..M) | Phase 3 + Phase 5 query **validation** for its assigned tables only | Enrich UC comments, run + verify sample queries, flip its rows `ENRICHED`→`VALIDATED` | All its assigned rows `VALIDATED` |
| **Finalize** (once) | Completeness gate → **create the Genie space(s)** + Phase 6 | Confirm every table is `VALIDATED` (else stop and report which aren't), create the Genie space (ONE per layer — single-layer: one; `hybrid`: silver + gold), tutorials, maintenance guide, update `ARCHITECTURE.md` **if it exists** (else defer to domain-sync) | Docs emitted |

- **Genie space creation is deferred to Finalize** (Rule: one space) — a batch session runs
  Phase 5's query *validation* only and must NOT create a space.
- **Single-session runs still use this** — one session plays all three roles in order; parallel
  launch is optional and low-value here because the synthesis singletons dominate wall-clock.
- **Small, clean domains can skip the checkpoint file entirely** — when UC metadata is already
  complete (every table + business column already carries a COMMENT, verifiable in
  `INFORMATION_SCHEMA`) AND the total table count is small enough to document in one session
  (roughly < 35, including both layers for `hybrid`), the Setup/Batch/Finalize ceremony buys
  nothing. Run all 6 phases in one pass and skip writing `documentation_state.md`. The 6-phase
  model below is session-agnostic; the checkpoint file exists for *resume after overflow*, not as
  a mandatory audit. (The Sales Order SDP hybrid run — 30 tables, all comments inline from the SDP
  pipelines — was exactly this case.)

---

## 6-Phase Execution Model (summary — full protocol in `phase-protocol.md`)

> The 6 phases are the *work*; **Checkpoint & Session Roles** above is *how to distribute it*
> across resumable sessions. Setup = Phases 1–2 + 4, Batch = Phase 3 + Phase 5 query validation,
> Finalize = Genie-space creation + Phase 6. **The full per-step protocol lives in
> `phase-protocol.md`.** Every "Phase N" reference elsewhere in this file resolves there; the
> **Layer & ETL-type Gate** (above) reshapes several phases and is cited throughout.

| Phase | Role | Does | Gate |
|---|---|---|---|
| **1 · Gather Context** | Setup | Discover where handoffs actually landed (canonical path → `docs/` root fallback); read `progress.md` (stale — cross-check), `validation_summary.md` (grades + gap deltas + caveats), `build_manifest.md` (grain/filters/FK-resolution/counts), DDL, `INFORMATION_SCHEMA`; identify comment/FK gaps | Full schema mapped with comments, FKs, relationships; `validation_summary.md` + `build_manifest.md` read |
| **2 · Domain Narrative (Explanation)** | Setup | Author `docs/explanation/domain_narrative.md` (the 9 sections in `domain-narrative.md`) from the Phase-1 sources; stamp `synced-against`. Understanding-oriented — distinct from tutorials and Genie how-to | Narrative written, stamped, honest about gaps (matches `validation_summary.md`); downstream cells link to it, don't restate |
| **3 · UC Metadata Enrichment** | Batch | **Fix the DDL first** (write COMMENTs into `ddl_{entity}.sql` — the deploy source of truth), then reconcile live tables via `ALTER` (catch-up only); verify FK registration; add UC tags. **SDP: the pipeline `.sql` is the write-target; skip FK registration** (MVs reject FK constraints) | Every table + business column has a COMMENT **in its DDL file**; live tables reconciled; FK graph complete in UC; `enrich_uc_metadata.sql` is a runnable idempotent ALTER script |
| **4 · Model Guide** | Setup | Produce the `{Domain} Model Guide` notebook at **project root** (not `docs/`): markdown overview, live `INFORMATION_SCHEMA` reference cells, links, quick-start queries, health summary from `_validation_table_result`. Ends the Setup session (write `documentation_state.md`) | Self-contained; **notebook-format read-back (Rule 13) passes** (SQL-shape); `hybrid` carries both silver + gold reference cells |
| **5 · Genie Space** | Finalize (space) / Batch (queries) | **Finalize runs the completeness gate first** (every table `VALIDATED` else STOP). Create **one Genie space per layer** — single-layer: one (`{Domain} Genie Agent`); `hybrid`: two, one per schema (`{Domain} Silver Genie Agent` + `{Domain} Gold Genie Agent`) — in the **project root folder** (not user home); write instructions from the narrative (+ export to handoff); generate 15–25 sample queries per space (cross-reference strategy per `output_model` — star vs 3NF-relationship); document in Model Guide | Space(s) created with instructions + sample queries; **every sample query passed the Sample Query Validation Gate** (live, non-empty, columns verified) |
| **6 · Tutorials + Maintenance Guide** | Finalize | Tutorial notebooks in `docs/tutorials/` (observation-triplet insight showcases, not SQL lessons); slim domain-local maintenance guide at `docs/contributor/` that **links out** to `docs/developer/`; update `ARCHITECTURE.md` only if it exists (creation is domain-sync's). Render the **Completion Self-Audit** unprompted | Tutorials run top-to-bottom with **non-empty results in every SQL cell**; Rule-13 read-back passes; maintenance guide passes the link-out acceptance gate; Self-Audit "Remaining before done" list empty |

---

## Relationship to Other Skills

### Reads from `domain-model-validation` outputs:
- `docs/.pipeline/handoffs/silver/validation_summary.md` — the typed validate→document handoff: per-entity grades,
  resolved/open gap deltas, changed Genie caveats. Read this instead of raw `_validation_*`
  tables and `_gap_registry` for grades/gaps (the narrative, Model Guide health, and Genie
  caveats all source from it).
- `_validation_table_result` — read live only for the Model Guide's always-current health cells
  (Cells 2–3), which query it directly by design; the *authored* grades come from the summary.

### Reads from `etl-development-framework` outputs:
- `docs/.pipeline/handoffs/silver/build_manifest.md` — grain, filters, FK-resolution attributes, final row counts, refresh
  schedule (feeds the narrative source detail + the Model Guide freshness/coverage lines)
- `docs/.pipeline/state/run/progress.md` — entity list, configuration, source systems
- DDL notebooks — schema, constraints, COMMENTs
- MERGE notebooks — source tables and join logic (for tutorial examples)

### Reads from `domain-model-assessment` outputs:
- S2T mapping — business context for Genie instructions
- Discovery brief — domain-level business context

### Produces (owns) — all four Diátaxis quadrants (for the domain's data consumers):
- Domain narrative (`docs/explanation/domain_narrative.md`) — Explanation; authored here (Phase 2)
- Model Guide — Reference; Genie space — How-to; tutorials — Tutorials
- Plus one **auxiliary, non-Diátaxis** artifact for the domain's *maintainers*:
  `docs/contributor/maintaining-this-domain.md` (slim per-domain maintenance guide that links
  out to the repo-level `docs/developer/` docs — see `contributor-guide.md`)

### Does NOT duplicate:
- The domain narrative is authored ONCE (Phase 2); the Model Guide and Genie instructions LINK
  to it rather than restating it (links-over-duplication holds within the skill)
- Validation notebooks — links to them
- DDL/MERGE code — references them for context, doesn't reproduce them

---

## Maintenance & Re-Run Protocol

**For point updates after the model is built, do NOT manually re-run this skill.** Load
`domain-sync` instead: it reads each artifact's `synced-against` stamp, scopes regeneration to
the changed entity via its change-impact matrix, and re-stamps — far cheaper than a full
documentation re-run and it keeps stamps honest. This skill's job is the *initial* full
generation (all four quadrants + stamps); `domain-sync` owns steady-state drift.

Full re-run of this skill is warranted only for wholesale changes (many entities added, a
domain restructure, a new skill in the suite) — otherwise route the point fix through
`domain-sync`.

The artifacts are idempotent so either path is safe to repeat:

| Artifact | On Re-Run |
| --- | --- |
| Domain narrative (`docs/explanation/domain_narrative.md`) | Regenerated (full replacement) + re-stamped |
| Model Guide notebook | Regenerated (replaces all cells) + re-stamped |
| Genie space instructions | Regenerated (full text replacement) + re-stamped (footer) |
| Genie sample queries | Regenerated (add new, update existing, remove orphaned) |
| UC comment enrichment | Re-audit (only generates ALTER for gaps) |
| Tutorial notebooks | Regenerated only if model structure changed + re-stamped |
| Maintenance guide (`maintaining-this-domain.md`) | Regenerated if this domain's entities/paths changed; suite-level content is not here (it lives in repo `docs/developer/`) |

---

## Critical Rules (Always Apply)

1. **Model Guide must be live** — reference cells query INFORMATION_SCHEMA, not static text. Running the notebook always produces current truth.
2. **Documentation OWNS explanation** — this skill authors the domain narrative (`docs/explanation/domain_narrative.md`), the Explanation quadrant, and owns all four Diátaxis quadrants **for the domain's data consumers**. Author the narrative ONCE (Phase 2); the Model Guide and Genie instructions LINK to it rather than restating it (links-over-duplication holds within the skill). Suite-level "how to use the skills" is NOT this skill's job — it lives in the repo `docs/developer/` docs; this skill only links to them from the per-domain maintenance guide.
3. **Every docs artifact carries a `synced-against` stamp** — the domain narrative (first line), Model Guide (Cell 1 markdown), tutorials (first markdown cell), and the Genie space (instruction-text footer + `docs/.pipeline/handoffs/genie_space_instructions.md`) each write `<!-- synced-against: progress.md @ {date} (rev: {sha|run_id}) -->` per `domain-sync/staleness-linter.md`. An unstamped artifact is flagged stale by the linter and cannot be trusted current.
4. **Genie instructions must include caveats** — encode known gaps ("Work_Center_Key on dim_routing_operation is always -1") so analysts aren't confused by unexpected results.
5. **Sample queries exclude -1 Unknown** — every WHERE clause in sample queries should filter out FK = -1 for aggregations.
6. **Tutorials are progressive** — Tutorial 01 assumes zero knowledge; Tutorial 03 assumes completion of 01 and 02.
7. **Maintenance guide is slim and domain-local** — it covers only THIS domain's entities/paths and its "add/fix/re-sync via the skills" recipes (invocation patterns like "ask the ETL skill to add `dim_{x}`", not low-level edits). It **links out** to the repo `docs/developer/` docs for the full suite decision tree and cross-domain recipes; it does NOT restate them. If you find yourself writing a suite-wide decision tree, a numbered "how to add a table" recipe, or low-level SQL edits here, stop — that belongs in `docs/developer/`. Enforce the `contributor-guide.md` acceptance gate (must link out, must not restate, ~1 screen); the first pass shipped 194 lines with 0 link-outs.
8. **DDL is the COMMENT write-target; live ALTER is catch-up** — UC enrichment (Phase 3) must land
   COMMENTs in the `ddl_{entity}.sql` files, which are the deployment source of truth; applying a comment
   only to a live table loses it on the next fresh deploy. Fix the DDL first, then reconcile live tables
   via a runnable `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`. Complete this before Genie creation — Genie reads UC
   metadata. **SDP EXCEPTION (`etl_type: sdp_pipeline`):** there are no separate DDL files — the pipeline
   `src/{layer}/pipeline/{entity}.sql` file IS the schema (inline COMMENTs, applied atomically on pipeline
   run). Treat that file as the write-target; no live-ALTER catch-up is needed for a freshly-run pipeline.
   See the Phase 3 SDP EXCEPTION.
9. **Tutorial SQL cells must return real data** — run every SQL cell before shipping a tutorial.
   A tutorial that compiles but returns 0 rows has failed. If a UC-registered FK join returns 0
   rows, diagnose the surrogate key overlap (sandbox data gaps are common), then pivot to a
   working join path. See `tutorials.md` Query Validation Gate.
10. **One Genie space PER LAYER** — exactly one space per schema, with comprehensive instructions; never multiple spaces for the *same* schema. Single-layer models get one space; `hybrid` gets two (silver + gold), each scoped to its own schema. Name `{Domain} [Silver/Gold ]Genie Agent`; create in the project root folder, not the user home directory.
11. **Idempotent re-generation** — every artifact can be safely regenerated without manual cleanup.
12. **NO ERD is generated** — a Databricks App provides comprehensive ERDs; the interim relationship views are the Model Guide's live FK-map cell (Cell 5) + the narrative's cross-reference matrix. Do not add an ERD generator.
13. **SQL-shape notebook format for the Model Guide AND tutorials** — both are SQL-shape notebooks,
    always, language-invariant (independent of `etl_language`). Two steps:
    `createAsset(assetType='notebook', name='...')` then `editAsset(operation='update', ...)` to
    populate cells and **set the asset `language` to `'SQL'`** — `createAsset` does NOT take a
    `language` argument. **Mechanism: set `language: 'sql'` on the FIRST cell edit (the `update` on
    the initial cell). That first edit is what flips the notebook's asset-level language from the
    platform default (Python) to SQL; every subsequent `add` inherits it.** Setting language only on
    later cells leaves the asset-level language — and thus the serialization format (`# Databricks
    notebook source` vs `-- Databricks notebook source`) — as Python. Confirm the flip via the
    read-back gate below. Unlike the validation notebooks (which set `language` to match `etl_language`),
    these docs artifacts are ALWAYS `'SQL'` regardless of `etl_language` (do NOT hard-code Python, do NOT
    follow `etl_language`). First line `-- Databricks notebook source`, cell separator
    `-- COMMAND ----------`, markdown `-- %md` (NOT `# MAGIC %md`), SQL cells raw (NOT `# MAGIC %sql`).
    The first pass shipped both as Python-shape — off-spec. See `model-guide.md` / `tutorials.md`
    format contracts and `etl-development-framework/deployment-and-dab.md` "Notebook-format contract".
    **This rule is not self-enforcing — verify it by read-back, do not trust your own recollection of
    complying.** A prior run's self-assessment reported "Rule 13 caught the Python-shape default" while
    the shipped Model Guide and tutorials were in fact Python-shape (`# MAGIC %sql` / `# MAGIC %md`, 17
    MAGIC cells). Prose prohibition is not a gate. **After every `editAsset` that creates or updates a
    Model Guide or tutorial notebook, read the asset back (`readNotebook` / export the source) and assert
    ALL of:** (a) first line is exactly `-- Databricks notebook source`; (b) **no `# MAGIC` prefix appears
    anywhere** in the source; (c) the asset `language` is `'SQL'`. If any assertion fails, the notebook is
    off-spec — re-emit it SQL-shape and re-check before the Phase 4 / Phase 6 gate can pass.
14. **Docs artifacts are language-invariant** — Model Guide, Genie config, dashboard config, and the narrative are always SQL/markdown; they do NOT follow `etl_language`.
15. **`docs/.pipeline/state/run/documentation_state.md` is the checkpoint of record (large-domain runs)** — Setup writes it (every table `NOT_STARTED`), a batch session flips its tables `ENRICHED`→`VALIDATED`, and Finalize refuses to create the Genie space(s) until all rows are `VALIDATED`. UC-enrichment done-ness is confirmed via `INFORMATION_SCHEMA` (table COMMENT present); sample-query done-ness is recovered by **re-running** the queries, not trusting the file. Parallel launch is optional here — the synthesis singletons dominate, so the win is resume, not speed. See Checkpoint & Session Roles.
16. **Run the Documentation Completion Self-Audit before declaring done — unprompted.** Render the
    Phase 6 Documentation Completion Self-Audit table and report a single **"Remaining before done"**
    list before calling the domain documented. An **empty** list is the only state that unlocks
    "done"; if anything is open (a missing quadrant, no Genie space, an undocumented hybrid layer),
    present it and stop. This is the terminal station — the list is "before done", not "before handoff".

---

## Folder Ownership

| Folder | Skill Owner | Contents |
| --- | --- | --- |
| Project root (`Model Guide` notebook) | **domain-documentation** | Entry-point notebook (Reference; includes glossary + capability-index cells) |
| `docs/explanation/domain_narrative.md` | **domain-documentation** | Domain narrative (Explanation) — moved out of `docs/validation/`; authored here |
| `docs/tutorials/` | **domain-documentation** | Progressive tutorial notebooks |
| `docs/reference/` | **domain-documentation** | *(optional)* `glossary.md` — data dictionary / glossary when term list outgrows inline |
| `docs/contributor/` | **domain-documentation** | `maintaining-this-domain.md` — slim per-domain maintenance guide (auxiliary; links out to repo `docs/developer/`) |
| `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` | **domain-documentation** | UC comment/FK enrichment notebook |
| `docs/.pipeline/state/run/documentation_state.md` | **domain-documentation** | *(large-domain runs)* per-table checkpoint (resume) — Setup writes, Batch updates, Finalize reads |
| Genie space (external asset) | **domain-documentation** | Configuration, sample queries |

---

## Configuration

Inherited from the ETL project's `docs/.pipeline/state/run/progress.md`:

| Parameter | Used For |
| --- | --- |
| `silver_catalog.silver_schema` | Target for INFORMATION_SCHEMA queries, Genie space table list |
| Entity list + load order | Model Guide structure, tutorial progression |
| Source systems | Genie instruction context |
| Known gaps | Genie caveat instructions |
| Domain narrative path (`docs/explanation/domain_narrative.md`) | Authored in Phase 2; linked from Model Guide |
| Validation dashboard | Link in Model Guide |
