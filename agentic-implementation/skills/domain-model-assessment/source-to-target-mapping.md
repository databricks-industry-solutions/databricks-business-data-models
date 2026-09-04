# Source-to-Target Mapping — Phase 4

---

## Mode-Specific Report Scope (read first)

The scope of *this* report depends on `output_model` and which layer the assessment targets. Do not
leave it to the agent to guess (the sales-order run guessed correctly but unguided):

| `output_model` | Report scope | Gold handling |
| --- | --- | --- |
| `normalized` | **Single tier** — 3NF product-named tables only | none |
| `dimensional` | **Single tier** — the `dim_/fact_/bridge_` star only | the star IS the target |
| `hybrid` | **Silver tier now** (3NF), plus a **"Gold Downstream Notes"** section | gold is a *later, separate* pass — see below |

**Hybrid is layered, not both-at-once.** For a `hybrid` first pass, map the **silver 3NF** target
exactly as `normalized` mode, then add a short **Gold Downstream Notes** section listing which
silver entities are expected to become dims vs facts in the future gold star (a preview, not a
spec). The full gold star is assessed in a **second pass** using `gold-derivation-protocol.md`,
after the silver build lands — do NOT design the gold star in the silver S2T report.

> Trigger for the gold pass: silver is built + populated, and the user asks to "assess/build the
> gold layer." The SKILL.md **Mode Gate** routes it to Mode B (`gold-derivation-protocol.md`).

---

## Bronze Type Profile (report header section — before the per-entity mappings)

Open the report body with a **Bronze Type Profile** so the build knows up front how much type
casting is needed and which date masks to use. Two small tables, both filled from Step 2.4 / 2.4c:

```
### Bronze Type Profile

| Source system | Total columns | All STRING? | Typed dates | Typed numerics |
| sap_sd         | 81            | YES         | 0           | 0              |
| salesforce_crm | 39            | YES         | 0           | 0              |

### Date Formats (per source system)   ← from Step 2.4c
| Source system | Date columns        | Observed format | Cast mask                        |
| sap_sd        | erdat, vdatu, edatu | yyyyMMdd        | TRY_TO_DATE(col, 'yyyyMMdd')     |
| salesforce_crm| quote_date, valid_until | yyyy-MM-dd  | TRY_TO_DATE(col, 'yyyy-MM-dd')   |
```

If the profile is **All-STRING**, say so in the report header ("All-STRING bronze — full type
casting required") — it tells the build every column needs an explicit cast and every date needs a
sampled mask (Step 2.4c), and that the load strategy resolved via the Step 2.6.0 fast-exit.

---

## Report Structure

For each real target table (in load order, Tier 0 → Tier N), produce one section with:

```
### N. `{table_name}` — {One-line title from metamodel}

**Intent** *(from vibe_metamodel_product.description)*: {verbatim quote}

**Candidate sources**
| Source | Rows | Why it fits |

**Column mapping**
| Target (silver) column | Target Type | Source table | Source column | Transformation | FK Lookup | Null Disposition | Metamodel description | Glossary term | Gap? |

> **`Source column` is a VERIFIED bronze column name (from Step 2.4b reconciliation) — NEVER a
> repeat of the target name.** The metamodel attribute is the target name we *want*; the bronze
> column that populates it is frequently different or absent. If a target column has no confirmed
> source column, its `Source column` is blank and `Gap?` is `Derived` or `GAP` — do not invent a
> bronze column name. This split is what prevents the downstream build from guessing (the 76%-rewrite
> failure mode).

> **Carry the metamodel's own words forward.** `Metamodel description` = `vibe_metamodel_attribute.description`; `Glossary term` = `business_glossary_term` (both from the Phase 1.3 pull). These seed the built table's COMMENT + `glossary_term` tag downstream (`etl-development-framework/naming-standards.md` §5.6). A column with neither gets `—`, never blank — so the build can tell "none" from "forgotten".

**Key derivation**: {formula}

**Expected orphan rates** (for FK columns): {estimate per FK}

**FK resolution** (REQUIRED for every FK — normalized product FKs and fact FKs alike). This
per-entity table maps into spec Section 3 (which is ONE table for the whole spec): prepend this
entity as the §3 `Owning Entity` column, and the build adds a `Values verified equal?` column that
it populates and confirms during its confirmation pass:

| FK Column | Parent Entity | Domain (intra/cross) | Resolution (LEFT JOIN / NULL) | Join Condition |
| --- | --- | --- | --- | --- |

`Join Condition` MUST be the explicit, complete predicate — including every column of a composite
join (e.g. `vkorg = k.sales_org AND vtweg = k.dist_channel AND spart = k.division`) — so the build
never reverse-engineers it. Note name-vs-code / internal-vs-external mismatches in the condition.

**Cross-domain FK availability** (per cross-domain FK, from Step 2.8): {Resolvable / Deferred /
Blocked — parent domain populated / empty / absent. Tells the build which FKs to EXPECT, which to
accept as NULL, and which are a cross-domain dependency.}

**Load strategy**: {FULL_MERGE | INCREMENTAL_MERGE | APPEND_ONLY | SDP} — {source row count +
mutability → why. See "Load Strategy Recommendation" below.}

**Grade: {Full | Partial | Blocked}** — {one-sentence reason}
```

---

## Load Order Derivation

Before mapping any table, derive the load order from the FK graph (the resolved
`referential_constraints` + `key_column_usage` join from discovery-protocol §1.5 — or the
`foreign_key_to` fallback when the model declares FKs only in the metamodel, not as physical UC
constraints). Use this algorithm:

1. **Tier 0** — tables with no FK columns (root masters)
2. **Tier 1** — tables whose only FK columns point to Tier 0 tables
3. **Tier N** — tables whose FK columns point to Tier N-1 tables
4. **Skip** — degenerate placeholder and any Blocked table (no source)

State the full tier sequence at the top of the S2T report before the per-table sections.

---

## Grading Rubric

### Full
- Primary natural key is sourceable with a clear derivation
- <10% of named business columns are gaps (no source)
- No FK column left entirely unresolvable
- V1 proof exists (non-zero rows in MVP), OR column inspection confirms mapping

### Partial
- Primary natural key is sourceable
- At least one significant column group (e.g., all cost fields, all compliance flags,
  all scheduled-date fields) has no viable source
- OR: source exists but covers only a subset of the expected population
  (e.g., DFF plants only vs all ERP plants) — always state the coverage caveat explicitly

### Blocked
- Primary natural key (or its source system ID equivalent) has no bronze, silver, or gold source
- The entity simply cannot be populated without new ingestion
- OR: the only source is a SaaS platform (Windchill PLM, o9, etc.) that is not yet ingested

> **Blocked ≠ dropped.** A Blocked entity is recorded **DEFERRED** in the Gap & Enhancement
> Registry with a future-enhancement callout (the ingestion ask that would unblock it) — it is
> **never silently descoped**. This is knob-blind: an entity blocked for lack of data is blocked
> regardless of `output_model`. See `iteration-loop.md` gap disposition and the ETL skill's
> `discovery-and-gap-analysis.md` "No silent descoping".

**Important distinctions:**
- A column being derivable (computed from other columns) counts as sourced, not a gap
- A column whose only bronze source is 100% NULL is a **`NULL_SOURCE` gap**, NOT sourced — it
  delivers no data. It counts toward **Partial** exactly like a missing column group; an entity
  whose only shortfall is NULL_SOURCE columns is **Partial, not Full**. Every NULL_SOURCE column is
  recorded in the Gap & Enhancement Registry regardless of keep/drop disposition.
- A column in a missing EBS table (e.g., `wip_discrete_jobs` not in `orcy_wip_curated`)
  counts as a gap — note the missing table name as the ingestion ask
- A column that maps to a cross-domain FK (e.g., `abl_pn_registry_id` to componentmaster)
  counts as Partial if the natural key (`abl_pn`) is present and joinable

---

## Column Mapping Conventions

### Per-Column Fields
| Field | What to write |
| --- | --- |
| `Target (silver) column` | The TARGET column name the model declares (from `vibe_metamodel` attribute) |
| `Target Type` | The TARGET column's declared type from the metamodel attribute (Phase 1.3 pull) — carried through to the handoff spec §2 `Type`. Never omit; a derived/constant column states its computed result type. |
| `FK Lookup` | For a FK column, the parent entity + the join it resolves through (full condition goes in the FK-resolution table); `—` for a non-FK column. |
| `Null Disposition` | For a `NULL_SOURCE` column only: `keep` \| `drop`, or blank = the `conventions.yml` `null_columns.disposition` global default. Ignored for non-null-source columns. |
| `Source table` | `{catalog}.{schema}.{table}` the column comes from, or blank if Derived/Constant/GAP |
| `Source column` | The **verified** bronze column name (Step 2.4b), or blank for `Derived`/`Constant`/`GAP`. **Never the target name.** |
| `Transformation` | SQL expression: `CAST(...)`, `CASE WHEN ...`, `SHA2(...)`, `SUM(...)`, or `Constant` value |
| `Gap?` | `No` / `Partial` (exists but incomplete) / `Derived` (computed, no single source col) / **`GAP`** (no source) / **`NULL_SOURCE`** (source column exists but is 100% NULL across all rows) |

> **The `Source column` MUST be a real column returned by `information_schema.columns` for the
> `Source table` (Step 2.4b reconciled it). A target column with no confirmed bronze column is a
> `GAP` or `Derived` — leaving `Source column` blank — never a copy of the target name.**

### Key Derivation Standard  *(knob-aware — depends on `output_model`)*
Always state the natural key explicitly — it is the idempotent reload anchor in every mode.
- **`dimensional`** (+ `hybrid`-gold): the built PK is a BIGINT surrogate `{Entity}_Key`.
  Derivation: `SHA2(CAST({natural_key_column} AS STRING), 256)` cast to BIGINT; composite →
  `SHA2(CONCAT_WS('|', col1, col2, col3), 256)`. (`scd_strategy: type_2` adds `_effective_from`
  to the hash so each version gets a distinct key.)
- **`normalized`** (+ `hybrid`-silver): the built PK **follows the vibe model** — keep the
  model's `{product}_id` and type; do NOT overlay a `{Entity}_Key` SHA2 surrogate. Add a
  surrogate only where the model PK is composite/mutable or cross-source integration needs one.
  (The metamodel `{table}_id` is often already a BIGINT surrogate — preserve it as-is.)

Example:
```
**Key derivation**: SHA2(CAST(WIP_ENTITY_ID AS STRING) || '|' || CAST(ORGANIZATION_ID AS STRING), 256)
Natural key: WIP_ENTITY_ID + ORGANIZATION_ID
```

### FK Resolution Pattern
For each FK column, document:
1. The intra-domain join (if FK points within this schema)
2. The natural key join for cross-domain FKs (those in `foreign_key_to` pointing outside the schema)
3. The expected orphan rate (NULL or unmatched FKs as % of rows)

Example:
```
`plant_id` FK: JOIN org_organization_definitions ON ORGANIZATION_ID → SHA2(plant) lookup
Expected orphan rate: <1% (org codes that have been decommissioned since 2019)
```

---

## Load Strategy Recommendation (REQUIRED — you already have the row counts)

Discovery profiles row counts *and* mutability per source (Phase 2, Steps 2.3 + 2.6). Use both
to recommend a load strategy per entity so the ETL skill does not default everything to full
MERGE. This maps directly to `etl_detailed_spec.md` Section 5.

**Mutability, not row count, is the deciding axis** — run the Step 2.6 Mutability Probe
(entity semantics + creation-vs-update timestamp divergence) for every fact first. Row count
only chooses *between* the mutable strategies.

| Source rows | Mutable after insert? (Step 2.6) | Recommend |
| --- | --- | --- |
| any size | **append-only** ledger (transactions/moves/completions/postings; `pct_mutated ≈ 0`) | `APPEND_ONLY` |
| < ~5M | mutable | `FULL_MERGE` (full scan is cheap at this size) |
| 5M–100M | mutable, **has** update ts | `INCREMENTAL_MERGE` (name the watermark column) |
| > 100M mutable, OR mutable with **no** usable watermark, OR needs SCD2 / enforced DQ | — | `SDP` (flag as escalation + CDF dependency) |

State the chosen strategy and the evidence (row count + `pct_mutated` + watermark column) that
drove it in each table's **Load strategy** line. Two calls to make explicit:
- **Immutable transaction facts → `APPEND_ONLY` regardless of size.** The `WHEN MATCHED` branch
  and full-target rewrite are pure waste for write-once rows.
- **Mutable fact with no reliable update timestamp → `SDP`, never a silent `FULL_MERGE`.** A
  watermark can't be built, so record it as an escalation with a **Change Data Feed on bronze**
  dependency (owned by the ingestion team; must be enabled going forward). Note in the same
  breath that `APPEND_ONLY` and watermarked `INCREMENTAL_MERGE` need **no CDF** — only this
  no-watermark / delete-capture / SCD2 tier does.

---

## Naming: the S2T report stays in metamodel-native names (with a crosswalk)

**This report uses the RAW metamodel names** (`order`, `order_id`, `lower_snake`) — it is a
*discovery* artifact whose job is to map bronze columns to model attributes, so keeping
model-native names here is correct and keeps it 1:1 with the metamodel you profiled. The
downstream **handoff docs** (`business_requirements.md` / `etl_detailed_spec.md`) DO apply the
`conventions.yml` `naming:` block (`fact_order`, `Order_Key`, `Pascal_Snake` — see
`iteration-loop.md` handoff section). So the two artifacts intentionally use different vocabularies.

**To keep them reconcilable, the S2T report MUST carry the crosswalk** — do not leave the reader
to guess that S2T `order` == spec `fact_order`. Add a `Built Name (conventions)` column to the
Summary Scorecard (below) mapping each metamodel name to the built name the build will use. State
once, above the scorecard: "Target Table = metamodel-native name; Built Name = after
`conventions.yml` `naming:` + `output_model` — this is the name the ETL build/spec uses."

> **The Built Name is KNOB-AWARE — this is the one place `output_model` enters the S2T report.**
> The grades, sources, and gaps to its left are **knob-blind** (they describe whether the data
> supports the business entity, regardless of shape). Only the Built-Name crosswalk and the key
> derivation shift with the knob:
> - `dimensional` → `dim_/fact_/bridge_` prefix, `{Entity}_Key` surrogate.
> - `normalized` → the metamodel product name verbatim (`order`, not `fact_order`), `{product}_id`.
> - `hybrid` → normalized product name for silver; the `dim_/fact_` star name for the gold tier.

## Summary Scorecard Format

Always produce this table at the end of the S2T report. Everything except **Built Name** is
knob-blind. Fill `Built Name (conventions)` by applying `conventions.yml` `output_model` +
`naming:`: `dimensional` → Type-based `dim_/fact_/bridge_` prefix + `table_case` + `entity_form`;
`normalized` → metamodel product name unchanged; `hybrid` → note both (silver product / gold star).

| # | Target Table (metamodel) | Built Name (per output_model) | Grade | Primary Source(s) | Source Rows | Load Strategy | Key Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `plant` | dim: `dim_plant` · norm: `plant` | Partial | `dff_curated.tbl_plants` + `org_organization_definitions` | 120 | FULL_MERGE | Address, ISO cert |
| 2 | `wip_material_transaction` | dim: `fact_wip_material_transaction` · norm: `wip_material_transaction` | Full | `orcy_wip_curated.mtl_material_transactions` | 168M | APPEND_ONLY | — |
| ... | | | | | | | |

**Totals: X Full · Y Partial · Z Blocked**
**Load: A FULL_MERGE · B INCREMENTAL_MERGE · C APPEND_ONLY · D SDP-escalation**

---

## Ingestion Ask Table Format

Always produce this at the end of every report:

| Priority | Table to Ingest | System | Target Schema | Unblocks |
| --- | --- | --- | --- | --- |
| **P0** | `wip_discrete_jobs` | Oracle EBS WIP | `orcy_wip_curated` | `wip_job` qty, status, dates |
| **P1** | ... | | | |

Priority definitions:
- **P0**: Unblocks a Blocked entity OR unblocks the primary natural key of a Partial entity
- **P1**: Unblocks a significant column group (>3 columns) on an existing Partial entity
- **P2**: Unblocks one specific column (compliance flag, ECN ref, etc.) — high business value
- **P3**: Nice-to-have enrichment; low-volume table; not on critical path

---

## What Counts as "Sourced"

| Situation | Count as |
| --- | --- |
| Column maps directly from a bronze column | Sourced (No gap) |
| Column maps to a bronze column that is 100% NULL across all rows | **NULL_SOURCE** — a gap; register it, drives Partial (see grading). Disposition keep/drop per `conventions.yml` `null_columns` (+ per-column override) |
| Column is derivable from other sourced columns (CASE, arithmetic, date diff) | Sourced — note `Derived` in Source field |
| Column maps from a silver table (via Option B consume-as-source) | Sourced — note the silver table |
| Column maps from a gold table (e.g. an existing gold schema like `o9_gold`) | Sourced — note gold origin |
| Column exists in a bronze table that is IN the bronze catalog but NOT in the identified schema | GAP — state missing table name as ingestion ask |
| Column exists in a source system not yet ingested to any lake tier | Blocked — state the source system |
| Column is a cross-domain FK that resolves via natural key join | Sourced (Partial if high orphan rate expected) |
| Column is a cross-domain FK where the target domain is not in the lake | Blocked (state which domain) |
| Element was user-confirmed dropped at the Phase 2C gate (matching `model_deviation` toggle on) | **DROPPED (deviation)** — represent the element *present* in the S2T with this origin; never omit it silently. Record reason in Key Gap column. |
| Bronze reveals a table/column the model lacks; user confirms at Phase 2C gate (`allow_new_entities` on) | **NET-NEW (deviation)** — add an S2T row with origin `NET-NEW (deviation)` and a fit grade; ETL build CREATEs it (propose→build). |

---

## Deviation Rows in the Entity Scorecard

When `model_deviation` toggles are active, the Entity Scorecard may include these special rows.

> **Deviation column convention:** The **Grade** axis and the disposition/origin axis are
> orthogonal — deviation labels are **annotations**, not grade values. Never put `DROPPED (deviation)` or
> `NET-NEW (deviation)` in the Grade cell:
> - **`DROPPED (deviation)`** — record the entity's **real fit grade** in the Grade cell (typically
>   `Blocked` or `Partial` — that finding drove the drop). Put the disposition note in the **Key Gap**
>   column: `DROPPED (deviation) — {reason}`.
> - **`NET-NEW (deviation)`** — same pattern: a real fit grade in Grade, and `Origin: NET-NEW (deviation) — {reason}` prefixed in **Key Gap**.
>
> This mirrors the registry rule: `Gap_Type = DROPPED (deviation)` is an annotation on a row whose
> `gap_status = ACCEPTED` — the status field never holds `DROPPED (deviation)`.

| # | Target Table (metamodel) | Built Name (per output_model) | Grade | Primary Source(s) | Source Rows | Load Strategy | Key Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | `delivery_schedule` | dim: `dim_delivery_schedule` · norm: `delivery_schedule` | Blocked | *(none — `drop_no_process_tables` on)* | 0 | — | DROPPED (deviation) — no bronze process table; user confirmed drop at Phase 2C gate. Recovery breadcrumb emitted for next_vibes. |
| — | `field_event` | dim: `dim_field_event` · norm: `field_event` | Partial | `fieldlink.field_events` | 42K | FULL_MERGE | Origin: NET-NEW (deviation) — bronze table not in model; user confirmed propose→build at Phase 2C gate (`allow_new_entities` on). Recorded in Gap Registry + `business_requirements.md`. |

> **Rule:** A dropped element is always represented **present** in the S2T scorecard — never absent.
> Its Grade cell holds the **real fit grade**; `DROPPED (deviation)` appears only in Key Gap as a
> disposition annotation. A net-new element carries `Origin: NET-NEW (deviation)` prefixed in Key Gap
> and a fit grade like any other row. Neither is ever introduced silently; both require human
> confirmation at the Phase 2C / Step 2.7 gate.

---

## Report File Naming Convention

Save the S2T mapping report to `docs/design/` as a **stable snake_case filename**, matching the
sibling handoff artifacts (`business_requirements.md`, `etl_detailed_spec.md`, `next_vibes.md`):
```
{project_folder}/docs/design/s2t_map.md
```
Example: `meridian/sales_order_mvm/docs/design/s2t_map.md`

Do **not** use a dated title-case filename (e.g. `2026-07-12 - Sales Order Vibe V3 - Source-to-Target
Mapping Report.md`) — the date/version/domain belong in the report's H1 + header block, not the
filename. A stable name keeps the artifact re-findable across re-runs and consistent with every other
`docs/design/` doc. Use the `templates/s2t_map.md` shell to structure the output.
