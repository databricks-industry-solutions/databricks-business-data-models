# Documentation Phase Protocol — detailed execution

> **Detailed execution reference for `SKILL.md`.** This file holds the full per-step protocol for
> the 6-phase documentation run. `SKILL.md` carries the phase *summary* table and the orchestration
> contract (Overview, the Layer & ETL-type Gate, Checkpoint & Session Roles, Critical Rules,
> Maintenance & Re-Run, folder ownership). **Cross-file resolution:** "Checkpoint & Session Roles",
> the "Layer & ETL-type Gate", and every "Rule N" reference point to `SKILL.md`; the phase steps
> below are the how-to those summaries point at.

## 6-Phase Execution Model

> The 6 phases below are the *work*; the **Checkpoint & Session Roles** section (in `SKILL.md`) is
> *how to distribute it* across resumable sessions. Setup = Phases 1–2 + 4, Batch = Phase 3 + Phase 5
> query validation, Finalize = Genie-space creation + Phase 6.

## Conventions

**`createAsset` path rule:** When creating files with `createAsset`, always pass the
**project-relative path** (e.g. `docs/explanation/domain_narrative.md`), never a workspace-absolute
path. CWD is the project root; a full path (e.g. `/Workspace/Users/…/docs/explanation/…`) gets
re-rooted under the home directory and produces a doubled path plus a blank file at the wrong
location.

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

   **Hybrid gate — confirm gold artifacts exist before claiming hybrid:**

   ```
   IF conventions.yml says output_model: hybrid THEN
     CHECK docs/.pipeline/handoffs/gold/validation_summary.md exists
     CHECK a gold schema actually contains tables
     IF NEITHER → treat as silver-only; log:
       "conventions.yml declares hybrid but no gold artifacts found.
        Proceeding as silver-only. Gold documentation deferred."
   ```

   **Gold ownership gate — catalog existence ≠ project ownership:**

   ```
   IF gold tables are found in the catalog THEN
     CHECK they are declared in THIS project's databricks.yml / resources/*.pipeline.yml /
       src/gold/**/*.sql / docs/.pipeline/handoffs/gold/build_manifest.md
     IF NONE match → do NOT claim them; treat as silver-only; log:
       "Gold tables found in catalog but not owned by this project. Treating as silver-only."
   ```

   **Catalog existence ≠ project ownership** — multiple projects write to one catalog. Only
   document tables traceable to this project's build artifacts.

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
   left, it does not invent a parallel convention.) Source missing descriptions from (in order):
   the spec's `Metamodel description` (metamodel-native, primary), the DDL notebook, the S2T
   mapping, the domain narrative, or (last resort) column-name inference.
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

**Gate:** **Run the Model Guide notebook end-to-end** before declaring Phase 4 complete — execute
every cell and confirm zero errors. The reference cells query `INFORMATION_SCHEMA` live, so a broken
cell (wrong column, bad join) only surfaces on execution. Fix any failing cell and re-run until the
whole notebook is green. (A run shipped a Model Guide with cell bugs that had to be fixed manually
afterward.) Model Guide is self-contained. **Notebook-format read-back (Rule 13) passes:** the asset
was read back after `editAsset` and asserted SQL-shape — first line `-- Databricks notebook source`,
zero `# MAGIC` prefixes, asset `language == 'SQL'`. For `hybrid`, the guide carries the 4-widget
header and both silver + gold reference cells (see `model-guide.md` "Hybrid / multi-schema").

> **If running multi-session:** this is the end of the **Setup** session. Before stopping, write
> `docs/.pipeline/state/run/documentation_state.md` (one row per table, all `NOT_STARTED`, with `Assigned_Session`) per
> Checkpoint & Session Roles (in `SKILL.md`), then hand off to batch session(s) for Phase 3 + Phase 5 query
> validation. (Phase 3 is Batch work even though it appears earlier in linear order — a batch
> session runs it against its assigned tables.) A single-session run just continues.

### Phase 5: Generate Genie Space

> **If running multi-session:** step 3 (generate + validate sample queries) is **Batch** work and
> may be sliced by fact group; steps 1, 2, 4 (create the Genie space(s)) are **Finalize**
> work. **Finalize runs the completeness gate FIRST:** read `docs/.pipeline/state/run/documentation_state.md`, confirm
> every table is `VALIDATED` (UC comment present + fact-group sample queries re-run non-empty). If
> any table is `NOT_STARTED`/`ENRICHED`, report which still need a batch session and **STOP** — do
> NOT create the Genie space(s) on partial docs (Rule: one space per layer, created once).

1. **Create Genie space(s)** via `createAsset(assetType: "genie", tableIdentifiers: [...])` — ONE per
   layer, named `{Domain} Genie Agent` (single-layer), in the **project root folder, NOT the user home
   directory** (verify placement after creation; move it if it landed in home — see
   `genie-space-config.md` "Asset placement"). Include all model tables, exclude `_validation_*`.
   **For `hybrid`, create TWO separate spaces — one per schema:** `{Domain} Silver Genie Agent` over
   the silver 3NF tables and `{Domain} Gold Genie Agent` over the gold dims/facts, each with a one-line
   cross-pointer to the other (see `genie-space-config.md` "Hybrid / multi-schema"). Do NOT put both
   layers in one space.
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

#### Documentation Completion Self-Audit (MANDATORY — render unprompted before declaring the domain documented)

**Do not wait to be asked "are we done?"** This is documentation's instance of the `autonomous-validation`
gate-(a) contract, and — because this is the loop's terminal station — the list is named **"Remaining
before done"** (there is no downstream skill to hand off to). At the last phase, reconcile every closing
obligation and report that list unprompted. **An empty list is the ONLY state that lets you declare the
domain documented.** If any item is open, present the list and stop — do NOT call the domain documented.

| # | Closing obligation | Done when | Status |
| --- | --- | --- | --- |
| 1 | **All four Diátaxis quadrants authored** | Explanation (`domain_narrative.md`), Reference (Model Guide notebook), How-to (Genie sample queries), Tutorials (`docs/tutorials/`) all produced | ☐ |
| 2 | **Genie space(s) created + instructions exported** | Space(s) created via `createAsset` — `{Domain} Genie Agent` (single-layer) or `{Domain} Silver/Gold Genie Agent` (hybrid: both) — in the project root folder (NOT user home; placement verified); instruction text also written to `docs/.pipeline/handoffs/genie_space_instructions.md` | ☐ |
| 3 | **Model Guide at project root** | `{Domain} Model Guide` notebook created at the project root (NOT under `docs/`), reference cells live | ☐ |
| 4 | **UC enrichment + maintenance guide** | `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` produced; `docs/contributor/maintaining-this-domain.md` written (passes the link-out acceptance gate) | ☐ |
| 5 | **(large-domain) every table `VALIDATED`** | No `documentation_state.md` row is `NOT_STARTED` or `ENRICHED` | ☐ |
| 6 | **(hybrid) both layers covered** | Silver AND gold documented — two-schema Model Guide, **two Genie spaces (`{Domain} Silver Genie Agent` + `{Domain} Gold Genie Agent`)**, both narratives; no fabricated content for an unvalidated layer | ☐ |
| 7 | **Improvement-recommendations emitted** | `docs/commentary/documentation-improvement-recommendations.md` produced per `autonomous-validation/commentary-protocol.md` (always emitted; fold prior items forward) | ☐ |

Report as: **"Remaining before done: {list, or 'none — domain fully documented'}"**. Only on "none"
is the domain documented.

