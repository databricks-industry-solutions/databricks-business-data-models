# Domain Narrative — Generation Rules

## Overview

The domain narrative is this skill's **Explanation quadrant** (Diátaxis) — the one artifact
that is understanding-oriented rather than task- or learning-oriented. It is a single markdown
document (`docs/explanation/domain_narrative.md`) that tells the **story** of the data model. A developer
reading it should understand:
- What business domain this covers and why it was built
- How the tables relate to each other (hierarchy + star schema)
- What each table represents in plain language
- What source systems feed into it
- What's known to be incomplete or imperfect

This is NOT a technical spec, NOT a tutorial, and NOT a how-to. It is narrative — written in
paragraphs, not just tables. Think of it as the README a senior engineer would write for a new
team member. Documentation OWNS this artifact (see `SKILL.md` — all four Diátaxis quadrants are
produced by this skill); it is generated here, not by the validation skill.

**Hybrid models (`output_model: hybrid`) — narrate BOTH layers.** When the domain has a normalized
silver schema AND a dimensional gold schema, the narrative covers both and explains how they relate:
- Section 2 (Architecture) shows the two-layer flow: bronze → **silver 3NF** (SSOT) → **gold star**
  (analytics), and states that gold is derived downstream from silver, not built in parallel.
- Section 4/5 (Dimension/Fact stories) cover the **gold** dims and facts as the primary analytics
  entities, and summarize the **silver** 3NF entities as the operational-detail source they derive from
  (you need not write a full paragraph per silver table if gold conforms it — group and cross-link).
- Grades and gaps come from BOTH `docs/.pipeline/handoffs/silver/validation_summary.md` (silver) and
  `docs/.pipeline/handoffs/gold/validation_summary.md` (gold; fall back to `docs/.pipeline/state/gold/validation_state.md` if the summary
  is incomplete — see `SKILL.md` Layer & ETL-type Gate).
- Make the analytics-vs-operational split explicit: gold star = clean surrogate-key joins for analysis;
  silver 3NF = lineage / operational detail / entities gold doesn't model.

**Normalized models (`output_model: normalized`) — no dims or facts, so retitle Sections 4–6.** A
3NF model has neither dimension nor fact tables; the "Dimension Stories" / "Fact Stories" /
"Star Schema Cross-Reference" titles below do not apply. Use entity-relationship framing instead —
**do NOT use dim/fact terminology anywhere in a normalized narrative:**
- **Section 4 → "Reference Entities"** — the T0–T1 master/config data (paragraph per entity, same shape).
- **Section 5 → "Transactional Entities"** — the T2+ event/document data (paragraph per entity).
- **Section 6 → "Entity Relationship Matrix"** — parent/child FK relationships (not a star-schema matrix).

**Output:** `docs/explanation/domain_narrative.md` (a docs artifact — no longer under `docs/validation/`).

**Header stamp (mandatory):** the very first line of the file is a `synced-against` stamp, per
`domain-sync/staleness-linter.md`:

```markdown
<!-- synced-against: progress.md @ {date} (rev: {short git sha or run_id}) -->

# {Domain Name} — Domain Narrative
```

Without the stamp the staleness linter cannot tell whether the narrative is current; emit it on
every generation and re-generation.

---

## Document Structure

### Section 1: Executive Summary (3–5 sentences)

```markdown
# {Domain Name} — Domain Narrative

> {One paragraph: what domain, what business questions it answers, scale (row counts),
> when built, current status (dev/prod), architecture choice}
```

**Generation rule:** Pull from `docs/.pipeline/state/run/progress.md` Configuration + S2T mapping overview.
Include total row count, entity count, and the architecture decision.

### Section 2: Architecture Overview

```markdown
## Architecture

{ASCII diagram showing:
- Source systems (bronze) on the left
- Silver model in the center (with hierarchy)
- Downstream consumers on the right (if known)}

**Architecture pattern:** {Option A/B/C description from readiness summary}
**Load pattern:** Type 1 MERGE, daily batch
**Compute:** Serverless
**Schema:** `{catalog}.{schema}`
```

**Generation rule:** Adapt the architecture diagram from the Iteration 2 readiness summary.
Simplify for narrative readability — don't show every bronze table, group by system.

### Section 3: Organizational Hierarchy

```markdown
## Organizational Hierarchy

{Describe the dimensional hierarchy in plain language}

Plant ({N} rows)
  └─ Focus Factory ({N} rows)
       └─ Work Center ({N} rows)
            └─ [Station] (not modeled — P3 gap)

{Explain what each level represents in business terms}
```

**Generation rule:** Derive from FK graph + DDL comments. Show row counts.
Call out any hierarchy levels that are gaps.

### Section 4: Dimension Stories

> **`output_model: normalized`** → retitle to **"Reference Entities"** (T0–T1 master/config), no
> dim/fact terms. See the normalized-model note near the top of this file.

For each dimension (in load order), write a **paragraph** (not a table row):

```markdown
## Dimensions

### dim_{entity} — {human title}

{2–3 sentences: what it represents, how many rows, where it fits in the hierarchy,
what enrichment it provides when joined to a fact. End with one sentence on source
and any caveats.}

**Joins to:** {list of facts that FK to this dim}
**Key insight:** {one non-obvious thing about this dimension — e.g., "133 focus
factories but only 42 plants means some plants have many factories while others
have one"}
```

**Generation rules:**
- Purpose from DDL COMMENT on the table
- Row count from `docs/.pipeline/state/run/progress.md` Entity Status
- "Joins to" from FK graph (which facts reference this dim)
- "Key insight" from S2T mapping or data profiling — something that helps a developer
  form a mental model of the data distribution

### Section 5: Fact Stories

> **`output_model: normalized`** → retitle to **"Transactional Entities"** (T2+ event/document
> data), no dim/fact terms. See the normalized-model note near the top of this file.

For each fact (in load order), write a **richer paragraph**:

```markdown
## Facts

### fact_{name} — {human title}

{3–5 sentences: what business event this captures, at what granularity (one row = ?),
how many rows, which dimensions enrich it and what each adds. Mention the source
system and any significant filters applied (e.g., WHERE TRANS_TYPE = 'PROD').}

**Grain:** One row per {grain description}
**Dimensions:** {list each dim FK with what it adds}
  - `Plant_Key` → dim_plant: facility location and timezone
  - `Work_Center_Key` → dim_work_center: production cell and focus factory
  - ...
**Measures:** {list key numeric/metric columns and what they represent}
**Cross-fact relationships:** {which other facts share the same grain or reference
the same entities — e.g., "fact_production_lot and fact_wip_completion both reference
Wip_Job_Key — lots are created from jobs, completions confirm lot production"}
**Known limitations:** {gaps, partial coverage, synthetic keys}
```

**Generation rules:**
- Grain from S2T mapping or DDL COMMENT
- Dimensions from FK graph
- Measures from DDL columns with numeric types and business comments
- Cross-fact from shared FK columns across facts
- Known limitations from `docs/.pipeline/handoffs/silver/validation_summary.md` (open-gap deltas) + `docs/.pipeline/state/run/progress.md`

### Section 6: Cross-Reference Matrix

> **`output_model: normalized`** → retitle to **"Entity Relationship Matrix"** and render
> parent/child FK relationships instead of a fact × dim star matrix. See the normalized-model note
> near the top of this file.

```markdown
## Star Schema Cross-Reference

| Fact \ Dim | plant | focus_factory | work_center | shift | kanban_card | routing | routing_op | bom_header | bom_line |
|---|---|---|---|---|---|---|---|---|---|
| fact_wip_job | ✓ | | ✓ | | | -1* | | -1* | |
| fact_production_lot | ✓ | | | | ✓ | | | | |
| fact_wip_completion | ✓ | | ✓ | | | | | | |
| ... | | | | | | | | | |

*-1 = FK exists but defaults to Unknown (gap)*
```

**Generation rule:** Build from FK relationships in DDL. Mark with ✓ for active FKs,
-1* for FKs that exist but default to Unknown due to known gaps. This matrix + the Model
Guide's live FK-map cell (Cell 5) are the interim relationship views — there is no generated
ERD (a Databricks App owns comprehensive ERDs; see `SKILL.md`).

### Section 7: Source Systems

```markdown
## Source Systems

| System | Bronze Schema | What It Provides | Key Tables |
|---|---|---|---|
| Oracle EBS | `orcy_wip_curated`, `orcy_bom_curated` | WIP jobs, BOMs, routings, material transactions | wip_entities, bom_structures_b, mtl_material_transactions |
| DFF MES | `dff_curated` | OEE, labor, cells, shifts, focus factories | tbl_cells, tbl_shifts, tbl_focusfactories |
| ABL | `ablmerged` | LPNs, completions, kanban cards | abl_lpn_header, abl_lpn_transactions, mtl_kanban_cards |
| O9 Planning | `o9_gold` | Master production schedule (cross-domain, safe) | master_production_schedule |
```

**Generation rule:** Extract from `docs/.pipeline/handoffs/silver/build_manifest.md` source references + S2T mapping (fall
back to MERGE notebook FROM clauses only if the manifest predates a source).

### Section 8: Known Limitations & Roadmap

```markdown
## Known Limitations

### Active Gaps (prioritized)

| Priority | Entity | Gap | Impact | Unblock Action |
|---|---|---|---|---|
| P0 | fact_wip_job | Routing_Key/Bom_Header_Key = -1 | Can't link jobs to routings for cycle analysis | Implement point-in-time revision lookup |
| P1 | fact_wip_move_transaction | DFF labor only (partial) | Non-DFF plants have no move transactions | New bronze ingestion from Oracle WIP_MOVE_TRANSACTIONS |
| ... | | | | |

### Accepted Exceptions

{List items that look like failures but are by design}

### Deferred (status `DEFERRED`)

{Entities that were considered but postponed (contract_manufacturer, serial_unit, etc.).
Use the standardized status word `DEFERRED` — see `domain-sync/next-steps-generation.md`.}
```

**Generation rule:** Pull from `docs/.pipeline/handoffs/silver/validation_summary.md` — the validate→document handoff —
for the current gap deltas (resolved/open) and per-entity grades, NOT from raw `_gap_registry`.
The validation skill has already reconciled the registry against the latest run and recorded
Priority / Status / Unblock_Action there; read those. Cross-check against `docs/.pipeline/state/run/progress.md` Decisions
Made for narrative color.

### Section 9: How to Validate

```markdown
## Validation

This model includes a full regression suite in `src/silver/validation/`:

- **Per-table narratives:** `narrative_dim_*.sql`, `narrative_fact_*.sql` *(extension follows etl_language: .sql | .py)*
- **Scorecard:** `scorecard.sql` (aggregates all results)
- **Metadata tables:** `_validation_run`, `_validation_table_result`, `_validation_check_detail`
- **Dashboard:** {dashboard name/link}
- **Scheduled job:** {job name} (runs {schedule})

To run validation manually: execute the validation job or run individual
narrative notebooks.
```

**Generation rule:** These validation assets are owned by `domain-model-validation`; the
narrative links to them (it does not reproduce their logic). Grades and gap status shown
elsewhere in this narrative come from `docs/.pipeline/handoffs/silver/validation_summary.md`, not from re-reading the
`_validation_*` tables directly.

---

## Tone & Style Rules

1. **Narrative, not spec** — write in sentences, not bullet lists (except for structured references)
2. **Business language first, technical second** — say "production completion events" not "abl_lpn_transactions WHERE TRANS_TYPE='PROD'"
3. **Concrete numbers** — always include row counts, percentages, dates
4. **Honest about gaps** — never hide limitations; present them as engineering backlog, not failures
5. **Opinionated** — include "key insight" that helps form mental models (distribution, skew, surprising patterns)
6. **Cross-references** — link facts to each other, not just to dims. Show how the model tells a complete story.
7. **Scannable** — a developer should be able to read Section 1 in 30 seconds and know if this model is relevant to their question
8. **Understanding-oriented (Diátaxis Explanation)** — this is the *why* and *how it fits together*. Do NOT drift into step-by-step teaching (that is the tutorials) or task recipes (that is the Genie how-to layer). Keep the quadrant pure.

---

## Generation Input Sources

| Section | Primary Source | Fallback |
| --- | --- | --- |
| Executive Summary | `docs/.pipeline/state/run/progress.md` + S2T overview | DDL comments |
| Architecture | Readiness summary diagram | `docs/.pipeline/state/run/progress.md` Configuration |
| Hierarchy | FK graph from DDL | S2T mapping |
| Dimension stories | DDL comments + `docs/.pipeline/state/run/progress.md` Entity Status | S2T mapping per-table |
| Fact stories | DDL comments + `docs/.pipeline/handoffs/silver/build_manifest.md` (grain, filters, FK resolution) | S2T mapping + `docs/.pipeline/state/run/progress.md` |
| Cross-reference | FK relationships in DDL | `docs/.pipeline/handoffs/silver/build_manifest.md` FK-resolution attributes |
| Source systems | `docs/.pipeline/handoffs/silver/build_manifest.md` source references | S2T mapping / MERGE FROM clauses |
| Limitations & grades | `docs/.pipeline/handoffs/silver/validation_summary.md` (gap deltas + per-entity grades) | `docs/.pipeline/state/run/progress.md` fixes |
| Validation | Generated validation assets (self-referencing, links only) | N/A |

**Seams this artifact reads:** `docs/.pipeline/handoffs/silver/validation_summary.md` (from `domain-model-validation` —
grades, gap deltas, changed Genie caveats) and `docs/.pipeline/handoffs/silver/build_manifest.md` (from
`etl-development-framework` — grain, filters, FK resolution, source references). This narrative
is then consumed by `domain-sync` for staleness (its `synced-against` stamp is the clock check).
