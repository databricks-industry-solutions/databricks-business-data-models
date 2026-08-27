---
name: domain-documentation
description: Document a built domain model for its data consumers — the Document station of the loop. Use when generating Diátaxis docs (tutorials, how-to, reference, explanation), a Model Guide entry-point notebook, a column dictionary/reference, insight tutorials, a per-domain maintenance guide, or an auto-generated Genie space so the domain is queryable in natural language the moment it is built. Not for validating data quality (use domain-model-validation) or building ETL (use etl-development-framework).
---

# Domain Documentation Skill

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
- Genie space — a Databricks **asset** (created via `createAsset`, not a file), with its instruction text also exported to `docs/.pipeline/handoffs/genie_space_instructions.md` (for the staleness linter)
- Tutorial notebooks (`docs/tutorials/`) — Progressive, executable insight showcases for the domain
- Maintenance guide (`docs/contributor/maintaining-this-domain.md`) — *auxiliary, non-Diátaxis*: a
  lightweight per-domain "how to add/fix/re-sync THIS model via the skills" pointer for maintainers,
  linking out to the repo `docs/developer/` docs for the full suite explanation
- UC comment enrichment script (`docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`) — Audit and fill gaps in table/column COMMENTs and FK definitions
- `docs/.pipeline/state/run/documentation_state.md` — *(large-domain runs only)* per-table checkpoint (assigned session, `NOT_STARTED→ENRICHED→VALIDATED`) that makes UC enrichment + sample-query validation resumable across sessions (see Checkpoint & Session Roles)
- Optional `docs/reference/glossary.md` — standalone data dictionary if the term list outgrows the Model Guide's Glossary cell

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
| `output_model` | `hybrid` | **Dual-schema path** — a normalized silver schema AND a dimensional gold schema. Documentation covers BOTH layers: 4-widget Model Guide, two-schema Genie space, two validation summaries. See the "Hybrid / multi-schema" variant blocks in `model-guide.md`, `genie-space-config.md`, and `domain-narrative.md`. |
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
(Rule: exactly one space) — so unlike ETL/validation its parallel value is low. But on a full
16–17-entity domain the genuinely per-entity, context-eroding work — **Phase 3 UC enrichment**
(per table) and **Phase 5 sample-query validation** (15–25 queries) — can still overflow a single
session. The primary win here is **resume after overflow**, using the same Setup/Batch/Finalize
split and mutable checkpoint file that `domain-model-validation` (`validation_state.md`) and
`etl-development-framework` (`etl_state.md`) use — kept aligned.

### The checkpoint file — `docs/.pipeline/state/run/documentation_state.md`

The **Setup** session writes it; every **Batch** session updates only its own rows; the
**Finalize** session reads it to confirm completeness before creating the single Genie space.

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

Phases 1, 2, 4 (context, narrative, Model Guide) and Phase 6 (tutorials, maintenance guide) are
**singletons**; the Genie space in Phase 5 is a singleton too (exactly one space). Only Phase 3
(UC enrichment) and Phase 5's *query validation* are per-table fan-out.

| Role | Runs | Does | Stops when |
|---|---|---|---|
| **Setup** (once) | Phase 1 + 2 + 4 | Gather context, author domain narrative + Model Guide, **write `documentation_state.md` with every table `NOT_STARTED`** | State file written; synthesis singletons done |
| **Batch** (1..M) | Phase 3 + Phase 5 query **validation** for its assigned tables only | Enrich UC comments, run + verify sample queries, flip its rows `ENRICHED`→`VALIDATED` | All its assigned rows `VALIDATED` |
| **Finalize** (once) | Completeness gate → **create the one Genie space** + Phase 6 | Confirm every table is `VALIDATED` (else stop and report which aren't), create the single Genie space, tutorials, maintenance guide, update `ARCHITECTURE.md` **if it exists** (else defer to domain-sync) | Docs emitted |

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

## 6-Phase Execution Model

> The 6 phases below are the *work*; the **Checkpoint & Session Roles** section above is *how to
> distribute it* across resumable sessions. Setup = Phases 1–2 + 4, Batch = Phase 3 + Phase 5
> query validation, Finalize = Genie-space creation + Phase 6.

### Phase 1: Gather Context

> **Step 0 — resolve where the handoffs actually landed (don't assume the canonical path exists).**
> The contract is that upstream skills emit `build_manifest.md` and `validation_summary.md` under
> `docs/.pipeline/handoffs/{layer}/`, and that is the path this skill writes and documents. But a
> given run may have emitted them elsewhere (e.g. an earlier ETL/validation session wrote them to
> the `docs/` root without creating the nested folder). Before reading, **discover the real
> location**: check `docs/.pipeline/handoffs/{layer}/` first, then fall back to `docs/` root
> (`docs/build_manifest.md`, `docs/validation_summary.md`). Use whichever you find, log which path
> was used, and — if you found them at a non-canonical path — create the canonical
> `docs/.pipeline/handoffs/{layer}/` folder and note the discrepancy so `domain-sync` can normalize
> it. Never conclude "no handoff exists" from a single canonical-path miss.

1. **Read `docs/.pipeline/state/run/progress.md`** — entity list, load order, configuration, row
   counts. **`progress.md` is frequently stale — cross-check it against the typed handoff docs, which
   are authoritative.** If `build_manifest.md` exists with deployment results, treat the build phases
   as COMPLETE regardless of what `progress.md` says; if `validation_summary.md` exists with a quality
   gate result, treat validation as COMPLETE. Flag the discrepancy in your context notes and proceed —
   do not stall or re-run upstream work because a status line reads `NOT_STARTED`.
2. **Read `docs/.pipeline/handoffs/silver/validation_summary.md`** — per-entity grades, resolved/open gap deltas, changed
   Genie caveats (the validate→document handoff; use it instead of raw `_gap_registry`). **For
   `hybrid`, also read `docs/.pipeline/handoffs/gold/validation_summary.md`** (the gold layer's handoff); if it is
   incomplete or missing sections, fall back to `docs/.pipeline/state/gold/validation_state.md` for gold per-entity
   grades + gap details (see the Layer & ETL-type Gate)
3. **Read `docs/.pipeline/handoffs/silver/build_manifest.md`** — grain, filters, FK-resolution attributes, final row
   counts, refresh schedule (feeds narrative source detail + freshness/coverage lines)
4. **Read DDL notebooks** — schema, FKs, COMMENTs, constraints
5. **Query INFORMATION_SCHEMA** — current table/column comments, FK definitions, tags
6. **Identify gaps** — tables/columns missing COMMENTs, FKs not registered in UC

**Gate:** Full model schema available with comments, FKs, and entity relationships mapped;
`validation_summary.md` + `build_manifest.md` read.

### Phase 2: Generate Domain Narrative (Explanation)

Author the domain narrative — this skill's Explanation quadrant — following
`domain-narrative.md`. It is understanding-oriented discourse (the *why* and *how it fits
together*), kept distinct from tutorials (learning) and Genie how-to (task).

1. **Assemble the story** from `validation_summary.md` (grades + gap deltas), `build_manifest.md`
   (grain, filters, FK resolution, sources), `docs/.pipeline/state/run/progress.md` (configuration, decisions), and DDL
   COMMENTs — the same sources Phase 1 gathered
2. **Write `docs/explanation/domain_narrative.md`** (a docs artifact — NOT under `docs/validation/`) with the
   nine sections in `domain-narrative.md`: exec summary, architecture, hierarchy, dimension
   stories, fact stories, cross-reference matrix, source systems, known limitations, validation
3. **Stamp it** — the first line is `<!-- synced-against: progress.md @ {date} (rev: {sha}) -->`
   (see Critical Rules and `domain-sync/staleness-linter.md`)

**Gate:** `docs/explanation/domain_narrative.md` written, stamped, and honest about gaps (grades + gap status
match `validation_summary.md`). Downstream cells (Model Guide, Genie instructions) link to it
rather than restating it.

### Phase 3: UC Metadata Enrichment

Before building documentation, ensure the UC metadata is complete **and captured in the DDL files**,
which are the deployment source of truth. **The DDL is the write target, not just a source to read
from.** A COMMENT applied only to a live table is lost the next time the model is deployed to a fresh
environment (`CREATE TABLE IF NOT EXISTS` re-runs from the DDL). So the rule is: **fix the DDL, then
reconcile the live tables** — never the reverse.

> **SDP EXCEPTION (`etl_type: sdp_pipeline`) — there is no `src/{layer}/ddl/` directory.** In an SDP
> pipeline the `src/{layer}/pipeline/{entity}.sql` file (a `CREATE OR REFRESH MATERIALIZED VIEW` /
> `STREAMING TABLE`) IS both the transform and the schema definition, and COMMENTs are declared
> **inline in the column list** and applied atomically when the pipeline runs. So for SDP:
> - The **pipeline `.sql` file** is the COMMENT write-target (substitute it everywhere this phase says
>   `ddl_{entity}.sql`). Audit that each pipeline file carries a table `COMMENT` and an inline
>   `COMMENT '...'` on every business column.
> - There is **no separate live-ALTER catch-up needed** for a freshly-run pipeline — re-running the
>   pipeline re-applies the inline comments. `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` for SDP holds only the
>   pieces UC metadata can't express inline (chiefly `SET TAGS`).
> - **FK constraints are NOT supported on Materialized Views** — `ALTER TABLE … ADD CONSTRAINT … FOREIGN
>   KEY` fails on an MV. So **skip FK-registration verification for SDP pipelines** (Phase 3 step 4's
>   "all FKs registered in UC" check does not apply). FK relationships in an SDP model are documented in
>   column COMMENTs and enforced by inline `CONSTRAINT … EXPECT` only; do not attempt to add them post-
>   materialization and do not flag their absence as a gap.
> - If every column already has an inline COMMENT in the pipeline files AND `INFORMATION_SCHEMA` agrees,
>   **Phase 3 is a fast-path audit + tag enrichment only** — do not go looking for a `ddl/` directory to
>   fix. In `hybrid`, run this audit against BOTH the silver and gold pipeline directories.

1. **Audit the DDL first** — for every table, does its `src/silver/ddl/ddl_{entity}.sql` file carry a
   table COMMENT and an inline `COMMENT '...'` on every business column? (The ETL skill's
   `etl-development-framework/ddl-and-modeling.md` already mandates this — Phase 3 fills any gaps it
   left, it does not invent a parallel convention.) Source missing descriptions from the S2T mapping,
   the domain narrative entity stories, or (last resort) column-name inference.
2. **Write the comments into the DDL files** — add/repair the inline `COMMENT` clauses in each
   `ddl_{entity}.sql`. This is the primary deliverable of Phase 3. If a DDL file is missing or is a
   placeholder (an empty/near-empty file that fails to write is a build-skill defect — flag it), author
   the full `CREATE TABLE` from the live schema (`INFORMATION_SCHEMA`) so it round-trips.
3. **Reconcile live tables (catch-up only)** — for tables already deployed, apply the same comments to
   the live schema via `ALTER ... COMMENT` so UC/Genie see them now. This is a *catch-up* pass that
   mirrors the DDL; it is never the source of truth. Emit these statements as `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`
   (see Phase 3 gate + `genie-space-config.md`) — a **runnable, idempotent ALTER script**, not a prose log.
4. **Verify FK registration** — all FK relationships defined in DDL should be registered in UC.
   **Skip this step entirely for `etl_type: sdp_pipeline`** — MVs do not support FK constraints (see
   the SDP EXCEPTION above); their FK relationships live in COMMENTs + EXPECT, not UC constraints.
5. **Add UC tags** — `domain`, `entity_type` (dim/fact), `tier`, `source_system` where missing. Probe
   the governed tag vocabulary first (see `genie-space-config.md` Tag Enrichment) — a workspace may
   restrict allowed values (e.g. reject `domain='sales_order'`); treat a rejection as a documented skip,
   not a failure.

**Gate:** Every table + business column has a COMMENT **in its `ddl_{entity}.sql` file** (audit the DDL,
not just the live schema — the DDL is what deploys). Live tables reconciled to match. FK graph complete
in UC. `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` is a runnable ALTER script that reproduces the applied comments/tags.

> **Multi-session:** this is **Batch** work. After enriching each assigned table's COMMENTs, flip
> its row in `docs/.pipeline/state/run/documentation_state.md` to `ENRICHED`, then to `VALIDATED` once its fact-group
> sample queries (Phase 5 step 3) run non-empty. A batch session touches only its assigned tables.

### Phase 4: Generate Model Guide

Produce the `Model Guide` notebook — named `{Domain} Model Guide` (or `Model Guide`) — at the **project root** (NOT under `docs/`), following `model-guide.md`:

1. Markdown overview (architecture, hierarchy, what this model answers)
2. Live reference cells (INFORMATION_SCHEMA queries for column dictionary, FK map)
3. Links section (domain narrative, tutorials, Genie space, validation dashboard)
4. Quick-start examples (3–5 common queries analysts would run)
5. Current health summary (reads latest `_validation_table_result`)

**Gate:** Model Guide is self-contained. Running it produces a complete reference. **Notebook-format
read-back (Rule 13) passes:** the asset was read back after `editAsset` and asserted SQL-shape — first
line `-- Databricks notebook source`, zero `# MAGIC` prefixes, asset `language == 'SQL'`. For `hybrid`,
the guide carries the 4-widget header and both silver + gold reference cells (see `model-guide.md`
"Hybrid / multi-schema").

> **If running multi-session:** this is the end of the **Setup** session. Before stopping, write
> `docs/.pipeline/state/run/documentation_state.md` (one row per table, all `NOT_STARTED`, with `Assigned_Session`) per
> Checkpoint & Session Roles, then hand off to batch session(s) for Phase 3 + Phase 5 query
> validation. (Phase 3 is Batch work even though it appears earlier in linear order — a batch
> session runs it against its assigned tables.) A single-session run just continues.

### Phase 5: Generate Genie Space

> **If running multi-session:** step 3 (generate + validate sample queries) is **Batch** work and
> may be sliced by fact group; steps 1, 2, 4 (create the single Genie space) are **Finalize**
> work. **Finalize runs the completeness gate FIRST:** read `docs/.pipeline/state/run/documentation_state.md`, confirm
> every table is `VALIDATED` (UC comment present + fact-group sample queries re-run non-empty). If
> any table is `NOT_STARTED`/`ENRICHED`, report which still need a batch session and **STOP** — do
> NOT create the Genie space on partial docs (Rule: exactly one space, created once).

1. **Create Genie space** via `createAsset(assetType: "genie", tableIdentifiers: [...])` with all
   model tables (exclude `_validation_*`). **For `hybrid`, include tables from BOTH schemas** — all
   gold dims/facts + all silver tables — and frame the instruction text so analysts prefer the gold
   star for analytics and drop to silver for operational detail (see `genie-space-config.md` "Hybrid /
   multi-schema")
2. **Generate instruction text** from domain narrative (hierarchy, caveats, business terms), written
   into the space's instruction footer **and** exported to `docs/.pipeline/handoffs/genie_space_instructions.md` (both carry the `synced-against` stamp so the staleness linter can check the space without querying it)
3. **Generate sample queries** (15–25). The cross-reference strategy depends on `output_model`:
   - **`dimensional`, `hybrid` gold, or any star** — from **star schema cross-reference**: one per
     fact × primary-dim combination ("OEE by shift", "WIP jobs by plant").
   - **`normalized` (3NF, no facts/dims)** — a 3NF model has no fact/dim tables, so there is nothing
     to cross-reference as "fact × dim". Instead derive queries from the **entity relationships in the
     narrative**: one per core business entity + its key parent/child joins (e.g. "orders by customer",
     "order lines by order and material"), and one per common business question from the entity stories.
     Do NOT force a star framing onto a normalized model.
   - **`hybrid`** — generate the star-based set against the **gold** schema (the analytics surface) and,
     where silver answers questions gold doesn't, a smaller 3NF-relationship set against silver.
   - One per common business question (derived from the narrative's entity/fact stories)
   - Include known caveats in comments ("excludes Unknown -1 references")
4. **Document Genie space** in Model Guide links section

**Gate:** Genie space created with instructions + sample queries. **Every sample query passed
the Sample Query Validation Gate** (`genie-space-config.md`) — executed against the live schema,
non-empty results, column names verified (this is the same gate tutorials use; it catches the
`Record_Date`→`Shift_Date` class of bug). Verified with a test question.

### Phase 6: Generate Tutorials + Maintenance Guide

1. **Tutorial notebooks** in `docs/tutorials/` (insight showcases for the domain's consumers —
   the observation-triplet format in `tutorials.md`, NOT SQL lessons):
   - `01_*.sql` — Scale: what does this operation/domain look like? (portfolio, volume, health)
   - `02_*.sql` — Performance: how is it doing? (trends, top/bottom performers)
   - `03_*.sql` — Flow: how does it move? (volume trends, complexity, downstream landscape)
   - Each tutorial: markdown cells posing a business question, one finished SQL cell, a
     markdown observation citing the real numbers

2. **Maintenance guide** (auxiliary, per-domain) at `docs/contributor/maintaining-this-domain.md`:
   - Generated from `contributor-guide.md` — a **slim, domain-local** guide: this domain's
     entities + project paths, and "add a table / fix a degraded table / re-sync after a point
     change" recipes scoped to THIS model
   - **Links out** to the repo-level `docs/developer/` docs for the full suite explanation,
     decision tree, and cross-domain recipes — does NOT restate them
   - This is for the domain's *maintainers* (developers), distinct from the four consumer-facing
     Diátaxis quadrants above

3. **Update `ARCHITECTURE.md` if it already exists** — the map lives in `ARCHITECTURE.md` (owned by
   `domain-sync`); this skill's outputs appear in its Directory Guide. **If `ARCHITECTURE.md` does NOT
   exist yet (a brand-new project), do NOT create it here — its creation is owned by the first
   `domain-sync` run.** Do not fail or stall over a missing `ARCHITECTURE.md`; note it as a pending
   domain-sync task and move on.

**Gate:** Tutorials executable top-to-bottom with **non-empty results in every SQL cell**.
Every SQL cell must be run and verified before this gate passes. See `tutorials.md` Query
Validation Gate for the full protocol (probe FK joins, diagnose 0-row results, pivot to working
join paths if needed). **Notebook-format read-back (Rule 13) passes** for each tutorial — read back
after `editAsset` and assert SQL-shape (first line `-- Databricks notebook source`, zero `# MAGIC`
prefixes, `language == 'SQL'`). Maintenance guide passes the `contributor-guide.md` **acceptance gate** — it
links out to `docs/developer/how-to/`, does NOT restate the general add-a-table/close-a-gap/staleness
procedures, and stays ~1 screen (the first pass shipped 194 lines with 0 link-outs — a fail).

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
10. **One Genie space for analysts** — don't create multiple spaces for the same schema. One space, comprehensive instructions.
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
15. **`docs/.pipeline/state/run/documentation_state.md` is the checkpoint of record (large-domain runs)** — Setup writes it (every table `NOT_STARTED`), a batch session flips its tables `ENRICHED`→`VALIDATED`, and Finalize refuses to create the single Genie space until all rows are `VALIDATED`. UC-enrichment done-ness is confirmed via `INFORMATION_SCHEMA` (table COMMENT present); sample-query done-ness is recovered by **re-running** the queries, not trusting the file. Parallel launch is optional here — the synthesis singletons dominate, so the win is resume, not speed. See Checkpoint & Session Roles.

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
