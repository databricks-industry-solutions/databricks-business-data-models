# Data Discovery & Gap Analysis Protocol

## When to Use

Execute this protocol when:
- The user asks to build a new ETL pipeline and has not provided a filled `etl_detailed_spec.md`
- Section 3 (Target Model) is left blank or partially blank
- The user says "discover", "profile", "explore sources", or "what's in bronze"

If an `etl_detailed_spec.md` is present with filled sections, treat those sections as authoritative and only discover what's left blank.

---

## Pre-Discovery Gate: Business Requirements

### Step 0 — Verify land target ≠ vibe model (HARD STOP)

**Before anything else, confirm where the build will WRITE.** Resolve the silver land target
from `conventions.yml` `catalogs.silver` + `schemas.silver_pattern`, and the vibe model source
from `vibe_model.catalog`/`vibe_model.schema`. If a handoff `etl_detailed_spec.md` is provided,
read its **Section 0 — Locations**.

- If the land target `catalog.schema` **equals** the vibe model `catalog.schema`, **STOP** and
  ask the user for the silver land target. Do NOT generate DDL or MERGE — writing there would
  populate the model the assessment graded against. This is the single most common handoff bug:
  the assessment read the model from `meridian_sales_model.sales_order` and the spec re-used that
  as the target. It must not.
- A spec that names a "Target catalog/schema" equal to `vibe_model.*` is **rejected** — treat it
  as a blank land target and prompt for the real one.

**Also verify naming conventions were applied to the spec.** A filled `etl_detailed_spec.md` is
authoritative — its entity/column names become the literal built objects, so the build must NOT
"fix them up" silently, and must NOT accept raw model names either. Before generating DDL, check
Section 1 entity names against `conventions.yml` `naming:`:

- If DIM entities lack the `dim_prefix`, FACT entities lack the `fact_prefix`, names violate
  `table_case`/`entity_form`, or surrogate keys use `_id`/`_sk` instead of `surrogate_key_suffix`,
  **STOP and reconcile with the user** — do not build the un-prefixed names, and do not rename
  unilaterally. The common cause: the assessment passed through raw `vibe_metamodel_product`
  names (e.g. `sales_area`, `order`) instead of transforming them to `dim_sales_area`,
  `fact_order`. Confirm the corrected names, then proceed.
- If Section 7 is missing the `naming:` block, pull it from `conventions.yml` and apply it.

### Step 1 — Collect Requirements

**Do not run any discovery queries until this gate passes.**

Before kicking off Phase 1, verify the user has filled Section 1 of the Kickoff notebook (or otherwise provided requirements in the conversation). If Section 1 is blank or contains only placeholder text, STOP and prompt:

> "Before I run discovery queries against the source schemas, I need the business requirements filled in. Please provide:
> - Source systems and schemas (e.g. SAP EHS module → `{bronze_catalog}.ehs_curated`; add each to `conventions.yml` `bronze_sources`)
> - Known business entities (e.g. incidents, inspections, corrective actions)
> - Key metrics or facts you need to report on
> - Who will consume this data (named dashboard, Genie space, or report)
> - Refresh cadence and any SLA (e.g. data available by 8 AM ET daily)
>
> The more specific you are, the less I'll need to assume."

Do not proceed until at least **source system + source schema** and **one or more business entities** are named.

---

### Step 2 — Grade the Requirements

Once the user provides requirements, evaluate them against the rubric below and **present the grade table before running any queries**. Call out every dimension graded C or F explicitly.

#### Requirements Grading Rubric

| Dimension | A | B | C | F |
| --- | --- | --- | --- | --- |
| **Source systems** | Named system + `catalog.schema` path confirmed | Named system, schema not yet confirmed | Vague ("some database", "our EHS system") | Not provided |
| **Business entities** | Named entities with dim/fact classification hint | Named entities, no classification | Generic area ("EHS data", "safety stuff") | Not provided |
| **Key metrics / facts** | Specific KPIs or measures named (e.g. "OSHA incident rate by site") | General area named (e.g. "safety metrics") | Vague ("things we track") | Not provided |
| **Consumers** | Named dashboard, Genie space, or report with owner | Named team or person | "Someone in the EHS group" | Not provided |
| **Refresh cadence** | Specific schedule (e.g. "daily at 6 AM ET") | Frequency only (e.g. "daily") | Vague ("frequently", "as needed") | Not provided |
| **SLA** | Specific deadline (e.g. "available by 8 AM ET") | Relative ("before business hours") | No constraint stated | Not provided |

**Overall grade:** Average of all six dimensions (A=4, B=3, C=2, F=0).

**Minimum bar to proceed:** Overall B or better — source systems confirmed at schema level, at least two named entities. If below B, re-prompt and do not run queries.

For each dimension graded C or F, include an explicit callout in your response:

> "**Gap — [Dimension]:** I'm missing [what]. Without it I'll assume [assumption]. Please confirm or correct before I proceed."

---

## Phase 1: Data Discovery

### Prerequisite

Requirements gate (above) must pass before executing any step in this phase.

### Discovery Sequence

1. **Profile sources** — Query `INFORMATION_SCHEMA.TABLES` + run `DESCRIBE` on each bronze source table:
   - Row counts
   - Column list with types
   - Null rates for key columns
   - Distinct value counts for candidate keys
   - Date range coverage (min/max of date columns)

2. **Classify each target entity** as DIMENSION or FACT:
   - Dimensions: reference data, low cardinality, descriptive attributes, slowly changing
   - Facts: transactional/event data, high cardinality, measures, foreign keys to dimensions
   - For facts, propose an **explicit GRAIN statement** ("one row per...")

3. **Identify natural keys and conformed dimensions:**
   - Natural keys: columns with high uniqueness, no nulls, stable over time
   - Conformed dimensions: entities shared across multiple facts (define once, reference everywhere)
   - Look for code/ID columns that appear in multiple source tables as join candidates

3b. **Run the Mutability Probe for every fact (fills Section 5 load strategy).** Row count does
    NOT decide the strategy — *mutability after insert* does. For each fact:
   - **Entity semantics:** transaction/event/completion/move/posting grain → append-only;
     status/header/order/job/schedule with a lifecycle → mutable.
   - **Timestamp divergence** (confirm against data): if the source has both a creation and a
     last-update timestamp, run
     `SELECT COUNT(*), SUM(CASE WHEN {last_update} > {creation} THEN 1 ELSE 0 END) FROM {src}`.
     `pct_mutated ≈ 0` → `APPEND_ONLY`; `> 0` → `INCREMENTAL_MERGE` with `{last_update}` as the
     watermark column.
   - **No usable watermark on a mutable fact** → `SDP` escalation (needs Change Data Feed on
     bronze, a cross-team dependency), never a silent `FULL_MERGE`.
   - **CDF is NOT needed** for `APPEND_ONLY` or watermarked `INCREMENTAL_MERGE` — those are just
     filtered SELECTs on a timestamp. Only deletes / SCD2 / mutable-no-watermark need it.
   - Record row count + `pct_mutated` + watermark column + chosen strategy in
     `etl_detailed_spec.md` **Section 5**. This is the same Step 2.6 probe the assessment skill
     runs — do it here whenever the spec arrives without a prior assessment pass. Full detail:
     `domain-model-assessment/discovery-protocol.md` Step 2.6 and
     `merge-and-defensive-coding.md` Load Strategy Decision.

4. **Map to Section 3 Target Model** if filled; otherwise propose the full model.
   The target model's structure is READ from `conventions.yml` → `vibe_model.catalog` /
   `vibe_model.schema` (the graded vibe model), NOT from the silver land target. Build output
   lands in `catalogs.silver`; the two are deliberately separate.

5. **Post-Discovery Requirements Reassessment** — Before building load order or choosing strategies, cross-check discovery findings against the stated requirements and surface every ambiguity. Present findings to the user and **PAUSE for confirmation** before proceeding to step 6.

   Check each of the following:

   - **Entities in requirements NOT found in bronze:**
     > "You mentioned `[entity]` but I don't see a matching table in `[source_schema]`. Did you mean `[closest_table]`? Or is this data not yet ingested?"

   - **Tables found in bronze NOT in requirements:**
     > "I found `[table]` which looks like it could map to `[entity_type]`. Should I include it in the model, or is it out of scope?"

   - **Metric definitions that need precision:**
     For any measure named in requirements (e.g. "incident count"), confirm grain and filter:
     > "When you say `[metric]` — is that per site, per month? All statuses or only open/closed? Is there a standard calculation I should follow?"

   - **Grain ambiguities:**
     For any fact candidate where the grain is unclear:
     > "Is the grain for `[fact]` one row per `[proposed_grain]`? Or could it be `[alternative_grain]`?"

   - **Conformed dimension decisions:**
     For any dimension appearing in multiple fact sources:
     > "Both `[source_a]` and `[source_b]` reference `[entity]`. Should I build one conformed `dim_[entity]` shared across all facts, or separate per-fact lookups?"

   - **Source system conflicts:**
     For any entity found in more than one source schema:
     > "`[entity]` exists in both `[source_a]` and `[source_b]`. Which is the system of record, or should I union them?"

   - **Requirements covered by no source at all:**
     Flag as a pre-gap (before formal gap analysis in Phase 3):
     > "Nothing in `[source_schema]` maps to `[requirement]`. This looks like a HARD GAP. Do you want to proceed without it, or do you know of another source?"

   Do not proceed to step 6 until the user has responded to all material ambiguities. For any item the user does not address, record a FLAGGED ASSUMPTION in `discovery_summary.md`.

6. **Build load order:**
   - Tier 0: Dimensions (no dependencies)
   - Tier 1: Facts (depend on Tier 0 dims being populated)
   - Tier 2: Gold tables (depend on Tier 1 facts + Tier 0 dims)
   - Final: Validation notebook (runs after all loads complete)

7. **PAUSE** — Present to user for approval:
   - Proposed entity list with classifications (dim/fact/gold)
   - Grain statements for each fact
   - Natural key assignments
   - Conformed dimension identifications
   - Load order with dependency rationale
   - Chosen `merge_strategy` and `surrogate_key_method` (with one-line rationale each)
   - Any risky assumptions flagged for review

### Discovery Output

Write `discovery_summary.md` to the **project root** (NOT a bare `docs/`; alongside `gap_analysis.md` + `data_quality_assessment.md` per the layout tree in `deployment-and-dab.md`):

```markdown
# Discovery Summary

## Requirements Grade

| Dimension | Grade | Notes |
| --- | --- | --- |
| Source systems | | |
| Business entities | | |
| Key metrics / facts | | |
| Consumers | | |
| Refresh cadence | | |
| SLA | | |
| **Overall** | | |

## Requirement Gaps Called Out
- [Dimension]: [gap description] — Assumed: [assumption]

## Proposed Model

### Dimensions (Tier 0)
| Entity | Natural Key | Source Table | Row Count | Notes |
| --- | --- | --- | --- | --- |

### Facts (Tier 1)
| Entity | Grain (one row per...) | Dimension FKs | Source Table | Row Count | Notes |
| --- | --- | --- | --- | --- | --- |

### Gold Tables (Tier 2)
| Entity | Purpose | Built From | Grain/Aggregation |
| --- | --- | --- | --- |

## Post-Discovery Reassessment

### Ambiguities Resolved
- {question}: {user's answer}

### Flagged Assumptions (user did not respond)
- {assumption}: {why it was made} — FLAGGED FOR REVIEW

### Pre-Gaps Identified
- {requirement}: {status — HARD GAP / deferred / new source needed}

## Load Order
1. dim_a (Tier 0, no dependencies)
2. dim_b (Tier 0, no dependencies)
3. fact_x (Tier 1, depends on dim_a, dim_b)
4. gold_y (Tier 2, depends on fact_x + dim_a)
5. validate_{layer} (Final, runs after all loads)

## Strategy Decisions
- Merge strategy: {value} — {rationale}
- Surrogate key method: {value} — {rationale}

## Risky Assumptions (>10% chance of being wrong)
- {assumption}: {why it's risky} — FLAGGED FOR REVIEW
```

### Discovery Profiling Queries

Use these query patterns:

```sql
-- Table inventory
SELECT table_name, table_type
FROM {source_catalog}.information_schema.tables
WHERE table_schema = '{source_schema}'
ORDER BY table_name;

-- Column profiling
DESCRIBE {source_catalog}.{source_schema}.{table};

-- Row count + basic stats
SELECT
  COUNT(*) AS row_count,
  COUNT(DISTINCT {candidate_key}) AS distinct_keys,
  COUNT(*) - COUNT({candidate_key}) AS null_count,
  MIN({date_col}) AS min_date,
  MAX({date_col}) AS max_date
FROM {source_catalog}.{source_schema}.{table};

-- Candidate key uniqueness check
SELECT {candidate_key}, COUNT(*) AS cnt
FROM {source_catalog}.{source_schema}.{table}
GROUP BY {candidate_key}
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 10;
```

---

## Phase 3: Gap Analysis

### When to Run

After discovery is approved (Phase 1 complete) and DDL is generated (Phase 2 complete), before scaffolding MERGE notebooks (Phase 4).

### Gap Analysis Instructions

1. **Profile each source table** listed in the approved model:
   - Row count
   - Column list with types
   - Null rates for key columns
   - Distinct value counts for potential join keys
   - Date range coverage

> **When a complete typed handoff spec is present, this gate is CONFIRMATION-ONLY.** A handoff
> `etl_detailed_spec.md` with a full §2 (every column typed, verified source column, FK Lookup) and
> a filled §3 per-FK table has already done the discovery. Do NOT re-derive mappings — **verify**
> each spec-named source and target column + type against `information_schema`, halting only on a
> genuine mismatch (the halt semantics below are unchanged). Re-run discovery/profiling ONLY for
> sections the handoff left genuinely blank (a hand-authored spec, or an entity the assessment could
> not map).

2. **Source↔Target Column Reconciliation gate (MANDATORY — run before generating ANY transformation
   SQL).** This gate is **bilateral**: the source side (2a) confirms every column the build READS
   exists in bronze; the target side (2b) confirms every column the build WRITES exists in the
   silver target. Both use `information_schema.columns`, both **halt** on mismatch. Historically only
   the source side was enforced, and the missing target side let MERGEs reference columns the DDL
   never created (`DELTA_MERGE_UNRESOLVED_EXPRESSION` on `quote_number` when the model column was
   `number`, `customer_id` vs `account_id`, `total_amount` vs `quoted_value`) — 6 target-column
   mismatches across two entities in one Batch A build.

**2a. Source Column Reconciliation (columns the build READS):**
   The spec (`etl_detailed_spec.md` §2) names TARGET columns; the assessment *should* have supplied
   the verified bronze source column per target (Step 2.4b), but the build **must re-validate** —
   defense in depth. For **every** source column the build is about to reference:
   - Run `information_schema.columns` (or `DESCRIBE TABLE`) on each source and capture the ACTUAL
     column list. Do this ONCE per source, up front.
   - Confirm every referenced source column **actually exists** — including columns in `WHERE`
     predicates/filters and the natural-key expression, not just SELECT columns.
   - When a spec-named column does not exist: (a) find the closest real column and re-map, or (b) if
     no match, emit `CAST(NULL AS <type>)` with a `P1/P2 gap` comment — **never** emit SQL against a
     column that was not confirmed present.
   - **Halt gate:** if **>20% of an entity's referenced columns are unresolved**, STOP and present a
     reconciliation table ("spec says X, bronze has Y — confirm") before scaffolding that entity.
   - This single step would have prevented 13/17 file rewrites in the sales-order SDP build. It is
     the build-side half of the source↔target contract (assessment Step 2.4b is the other half).
   - Flag unmapped target columns as **GAP**; flag unmapped source columns as **AVAILABLE** enrichment.

   > **WHERE / filter columns and natural keys are validated too.** A filter like
   > `WHERE ettyp IN (...)` on a column the bronze table lacks silently produces the wrong population
   > (or an error). If a spec filter column is absent, emit
   > `WHERE FALSE  -- PLACEHOLDER: <col> absent in <source>; entity is a known-0-row gap` rather than
   > guessing. The **natural key** must be expressed in **verified SOURCE column names**
   > (`TRIM(vtweg)`), never the target attribute name (`channel_code`) — the SHA2 input is a source
   > expression.

**2b. Target Column Reconciliation (columns the build WRITES) — the mirror gate:**
   In `normalized` mode the vibe model gives each entity 30–45 columns with domain-specific names
   that are easy to mis-remember (`number` not `quote_number`, `account_id` not `customer_id`,
   `converted_order_reference` not `converted_order_number`). **Never derive target column names from
   business understanding of the source — always read the actual target schema.** For **every**
   entity, before authoring its MERGE/transformation SQL:
   - Run, once per entity, and capture the result as that entity's **target column manifest**
     (catalog-qualify `information_schema` — an **unqualified** `FROM information_schema.columns`
     resolves against the session's CURRENT catalog, so if it isn't the silver catalog the query
     returns an empty/wrong manifest and this gate silently passes with nothing to compare against):
     ```sql
     SELECT column_name, data_type, is_nullable
     FROM {silver_catalog}.information_schema.columns
     WHERE table_schema = '{silver_schema}' AND table_name = '{entity}'
     ORDER BY ordinal_position;
     ```
   - After authoring the SQL, cross-reference **every** target column it writes against that
     manifest: the `ON`/merge-key columns, the `WHEN MATCHED THEN UPDATE SET` list, and the
     `WHEN NOT MATCHED THEN INSERT (…)` column list. (Source-side `VALUES`/expressions are covered
     by 2a.)
   - **Halt** if any authored target column is not in the manifest — re-map to the real column name
     before proceeding.
   - This is preventive, not reactive: it replaces the "run → `UNRESOLVED_COLUMN` → DESCRIBE → fix →
     re-run" loop with a "read → author → run" one. See `merge-and-defensive-coding.md` Critical
     Rule 12 and the MERGE pre-flight `EXPLAIN` check.

3. **Identify enrichment opportunities:**
   - Related tables in the same source schema that could provide additional context
   - Columns in existing mapped sources that aren't currently used
   - Cross-reference or lookup tables that could resolve currently-null FK columns

4. **Write `gap_analysis.md`** to the **project root** (NOT a bare `docs/`; format below)

### Gap Analysis Report Format

```markdown
# Bronze Data Gap Analysis

## Summary
- Total source tables profiled: N
- Target columns fully mapped: X/Y (Z%)
- Gaps requiring new sources: N
- Enrichment opportunities identified: N

## Per-Entity Gap Detail

### {entity_name}
**Source:** {source_table} ({row_count} rows)
**Mapped columns:** X/Y target columns have source data
**Gaps:**
- `Target_Col_A`: No source found — requires [new source / business decision]
- `Target_Col_B`: Source exists in {other_table}.{column} but not currently joined

**Enrichment opportunities:**
- {other_table}.{column} could populate {target_col} (join on {key})
- {source_table}.{unused_col} is available but not mapped

## Recommended Actions
1. [Priority] {action description}
2. ...

## Data Quality Notes
- {table}: {column} has {X}% null rate — may need TRY_CAST or NULLIF handling
- {table}: {column} has {N} distinct values (expected: enum/code column)
```

### Gap Classification

| Gap Type | Definition | Resolution |
| --- | --- | --- |
| **HARD GAP** | Target column/entity has no source anywhere in available bronze | Record as **DEFERRED** future-enhancement — **NEVER silently drop** (see rule below) |
| **SOFT GAP** | Source exists but in a different table, requires additional join | Add join to MERGE notebook; document in gap_analysis.md |
| **ENRICHMENT** | Source data available but not in current model | Propose as **model addition** (see below); user decides whether to include |
| **QUALITY GAP** | Source exists but data quality is poor (high nulls, dirty values) | Document; apply TRY_CAST/NULLIF; may affect grade |
| **NULL_SOURCE** | Source column exists but is 100% NULL across all rows | Register (`Gap_Type = NULL_SOURCE`); disposition per `conventions.yml` `null_columns` (+ per-column §2 override): `keep` → build as documented all-null; `drop` → omit from DDL **with** the registry row (`ddl-and-modeling.md`). Never silently drop. |
| **DROPPED (deviation)** | A modeled entity/column the user explicitly confirmed dropping at the assessment Phase 2C deviation gate (`model_deviation` toggle required) | **Accept as intentionally absent — do NOT re-flag as a HARD GAP.** The `_gap_registry` row (`Gap_Type = DROPPED (deviation)`, `gap_status = ACCEPTED`) carries the reason and a `next_vibes` recovery breadcrumb. Never create a placeholder table. See `domain-model-assessment/iteration-loop.md`. |
| **NET-NEW (deviation)** | A table/column bronze reveals that is NOT in the vibe model; the user confirmed the proposal at the assessment Phase 2C gate (`allow_new_entities` on) | **Build CREATEs it as a normal target (propose→build).** Origin is recorded in the `_gap_registry` and `business_requirements.md` Section 3 Notes (`Origin: NET-NEW (deviation)`). Apply the same DDL/MERGE/DQ treatment as any other spec entity — no special handling. See `domain-model-assessment/model-completeness-protocol.md`. |

### No silent descoping (MANDATORY — knob-blind)

**"The data isn't here yet" is a FINDING, not a decision.** A modeled entity or attribute with
no bronze source is **NEVER dropped from the build**. This rule is **knob-blind** — it does not
depend on `output_model`; the reconciliation reasons about business entities and whether data
supports them, identically in all modes. (The knob only shapes the *target* the mapped columns
land in — see `naming-standards.md` and the assessment skill's source-to-target mapping.)
(A `NULL_SOURCE` column — source present but 100% null — is a distinct case: it may be dropped
under `null_columns.disposition: drop`, but only WITH a `NULL_SOURCE` gap-registry row; see the
Gap Classification table and `ddl-and-modeling.md`. Never a silent drop.)

**Exception — `DROPPED (deviation)`:** An entity/column the user explicitly confirmed dropping at
the assessment Phase 2C deviation gate (see Gap Classification above) is intentionally absent from
the build scope. Its `_gap_registry` row IS the record; do not re-flag it as a HARD GAP, do not
create a placeholder table. This is NOT a silent descope — it is a logged, human-confirmed build
decision with a recovery breadcrumb in the domain's `docs/design/next_vibes.md` (format per `domain-model-assessment/templates/next_vibes.md`).

Both reconciliation directions land in the **Gap & Enhancement Registry** (`_gap_registry`;
`gap_status_enum: [OPEN, IN_PROGRESS, DEFERRED, ACCEPTED, RESOLVED]` — legacy `Descoped/Backlog`
is banned):

- **Model wants data bronze doesn't have (HARD GAP)** → status **`DEFERRED`** with a
  future-enhancement callout: *"entity/attribute needs bronze data {X}; build unblocks when {X}
  lands."* The build may **skip building** it, but the registry + per-domain review artifact must
  **report** it. Never resolve a no-source entity to "dropped."
  - In `normalized`/`hybrid`-silver, a DEFERRED entity is still CREATEd as an **unpopulated table**
    with `COMMENT 'DEFERRED — needs bronze {X}; see gap registry'`, so it's visible in the catalog.
  - In pure `dimensional`, a DEFERRED entity has no physical home — the callout lives in the
    registry + review artifact only (not a placeholder table).
- **Bronze has meaning the model missed (ENRICHMENT)** → surface as a **proposed model addition**
  (new entity / attribute / grain / hierarchy level) for the DE team's per-domain review.
  Optionally emit a **Vibe-Model Prompt** for it (a natural-language instruction to re-run the
  agent upstream) — this is a **byproduct, not a gate**; the registry is the primary artifact.

The per-domain human-review pause is where this pays off: the reviewer sees "here are N entities
your bronze can't fill yet" and "here are M things bronze has that the model doesn't capture" —
neither silently actioned.
