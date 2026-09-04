# [Project Name] — ETL Detailed Spec

*Fill any section to make it authoritative for Genie Code. Leave a section blank to let
discovery determine it. Filled sections override discovery findings and skip re-profiling
for that part of the model.*

*This document is optional. If `business_requirements.md` is the only doc provided,
Genie Code will discover everything. Use this spec when you already know entity shapes,
column mappings, or key assignments and want to skip the discovery conversation for those parts.*

---

## Section 0 — Locations (READ vs WRITE — must be distinct)

> **These are two different places. Never make them equal.** The build READS the vibe model's
> structure from one location and WRITES/LANDS the built tables into another. If they resolve to
> the same `catalog.schema`, STOP — the build would MERGE into the model it is grading against.

| Role | `conventions.yml` key | Value | Notes |
| --- | --- | --- | --- |
| **Silver land target (WRITE)** | `catalogs.silver` + `schemas.silver_pattern` | `{silver_catalog}.{silver_schema}` | Where DDL CREATEs and MERGE writes. This is `silver_catalog`/`silver_schema` at runtime. |
| **Vibe model source (READ-ONLY)** | `vibe_model.catalog` / `vibe_model.schema` | `{vibe_model_catalog}.{vibe_model_schema}` | Where the graded model + `vibe_metamodel_*` live. Build reads structure here; NEVER writes here. |
| Bronze source(s) | `bronze_sources` | (see Section 7) | Read-only ingested source schemas. |

**Guard:** the land target MUST differ from the vibe model source. If a customer keeps both in
one catalog, the land *schema* must still differ from `vibe_model.schema`.

---

## Section 1 — Target Model

> **Entity/column names here are FINAL and authoritative — they must already reflect
> `conventions.yml` `naming:` AND `output_model` (see Section 7).** How to name depends on the mode:
> - **`dimensional`**: apply the `dim_/fact_/bridge_` prefix by Type, `table_case`,
>   `entity_form`, `business_column_case`, and `surrogate_key_suffix`. Write `dim_sales_area`,
>   `fact_order` — NOT bare `sales_area`, `order`.
> - **`normalized`** *(default)* (+ `hybrid`-silver): write the **vibe model's product names verbatim** —
>   bare `sales_area`, `order`, lowercase `order_id` PKs, no `dim_/fact_` prefix. The model's DDL
>   is authoritative; do not re-prefix or re-case.
> - **`hybrid`**: normalized product names for the silver rows; `dim_/fact_/bridge_` for the gold
>   star rows (Target layer = gold).
>
> A filled spec overrides discovery, so a name here becomes the literal built table name — use the
> form that matches the chosen `output_model`.

### Target shape
| Field | Value |
| --- | --- |
| **output_model** | normalized / dimensional / hybrid (from `conventions.yml`) |
| **scd_strategy (default)** | type_1 / type_2 (dimensional or hybrid-gold only; per-entity override in Section 5) |

### Entities
| Entity (named per `output_model`) | Type (product / dim / fact / gold) | Target layer | Source table(s) | Load order tier |
| --- | --- | --- | --- | --- |
| | | silver / gold | | 0 = dim/product, 1 = fact, 2 = gold |

### Grain (facts only)
| Fact entity | Grain — one row per... | Append-only? (immutable ledger rows) |
| --- | --- | --- |
| | | yes / no |

*Append-only = source rows are never updated after insert (transaction/event ledgers:
material moves, completions, postings). These use INSERT / `WHEN NOT MATCHED`-only loads,
never symmetric Type-1 MERGE — see Section 5.*

- **Metamodel description (→ table COMMENT):** `{vibe_metamodel_product.description verbatim}`

### Conformed Dimensions
*Dimensions shared across multiple facts — define once, FK from all facts.*
| Dimension | Shared by (fact entities) |
| --- | --- |
| | |

---

## Section 2 — Column Mappings

*REQUIRED in an assessment handoff: fill COMPLETELY for every buildable (Full/Partial)
entity — every target column, with its target `Type`, verified `Source column`, and
`FK Lookup`. Keys-only fill is not acceptable in a handoff; a complete typed map is what
makes the build's reconciliation gate (`discovery-and-gap-analysis.md` §2a/2b)
confirmation-only instead of re-discovery. Outside a handoff (hand-authored spec), fill any
entity you already know and leave the rest for discovery.*

> Fill `Metamodel description` from `vibe_metamodel_attribute.description` and `Glossary term` from `business_glossary_term` (both carried from assessment Phase 1.3). A column with neither gets `—`, never blank. The build sources the DDL COMMENT + `glossary_term` tag from these — see `etl-development-framework/naming-standards.md` §5.6.

> **`Source expression` uses VERIFIED bronze column names — never the target column name.** The
> assessment's Step 2.4b reconciled target attribute → actual bronze column; carry that here
> (`Source table` + `Source column`). The build re-validates every column against
> `information_schema` before generating SQL (SKILL.md rule 24). A target column with no confirmed
> bronze source has a blank `Source expression` and `CAST(NULL AS <type>)` in `Transform / cast`,
> flagged in Notes as a P1/P2 gap — do NOT invent a source column name.

### [Entity name]
| Target column | Type | Nullable | Source table | Source column | Transform / cast | FK Lookup | Null Disposition | Metamodel description | Glossary term | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | `{catalog}.{schema}.{table}` | `{verified_bronze_col}` | | `{parent entity + join, or —}` | `{keep\|drop, or blank}` | `{vibe_metamodel_attribute.description}` | `{business_glossary_term}` | |

> **`FK Lookup`** names the parent entity + the join a FK column resolves through (or `—` for a
> non-FK column); the full join condition lives in §3. **`Null Disposition`** applies only to a
> column whose `Source column` is 100% null (`Notes` = `NULL_SOURCE`): `keep` builds it as a
> documented all-null column, `drop` omits it from DDL with a `NULL_SOURCE` gap; **blank = the
> `conventions.yml` `null_columns.disposition` global default.** See `conventions.yml`
> `null_columns` and `ddl-and-modeling.md`.

---

## Section 3 — Keys & Constraints

| Entity | Natural key (SOURCE expression) | Surrogate key name | PK | FK references | CHECK constraints | Recency column (for dedup) |
| --- | --- | --- | --- | --- | --- | --- |
| | `TRIM(vtweg)` (source col, NOT target `channel_code`) | {Entity}_Key | | | | source col used in `ORDER BY ... DESC` |

*The **Natural key** is the SOURCE-column expression the SHA2 surrogate hashes — `TRIM(vtweg)`, not
the target attribute name (`channel_code`). Naming the target column here silently produces 100%
orphans or a build-time rewrite (the `channel_config` failure). Use verified bronze column names.*

*The **recency column** is the source column that resolves duplicates in
`ROW_NUMBER() OVER (PARTITION BY {nk} ORDER BY {recency} DESC)`. Prefer a **source event
timestamp** (e.g. `LAST_UPDATE_DATE`, `DF_Processing_Dttm`), NOT the target `_loaded_at`
(that is job-time, not event-time, and is identical across all rows in a run).*

### FK Resolution — join attribute per FK (REQUIRED for every FK — product FKs and fact FKs)

*The single highest-value handoff field. A fact's FK column often carries a DIFFERENT
representation of the natural key than the dimension was hashed on (name vs. code, external
vs. internal ID, padded vs. unpadded). Recompute-the-hash-inline SILENTLY produces 100%
orphans with no error. Always resolve FKs by LEFT JOIN to the loaded dim on the matching
attribute — never inline SHA2. See `merge-and-defensive-coding.md` Rule 11.*

| Owning Entity | FK Column | Parent Entity | Domain (intra/cross) | Resolution (LEFT JOIN / NULL) | Join Condition | Values verified equal? |
| --- | --- | --- | --- | --- | --- | --- |
| fact_order / order | {Dim}_Key / {parent}_id | dim_plant / plant | intra | LEFT JOIN | `f.Plant = p.Plant_Name` (NOT Plant_Code) | yes — sampled both |
| order | sales_area_id | sales_area | intra | LEFT JOIN | `vkorg = k.sales_org AND vtweg = k.dist_channel AND spart = k.division` (composite) | yes — sampled both |
| shipment | {cross}_id | {parent} | cross | NULL (parent domain not in lake) | — | n/a |

*Required for EVERY FK — normalized product FKs and dimensional fact FKs alike, not facts only.
This is ONE table for the whole spec, so **Owning Entity** (the child entity that declares the FK)
is mandatory on every row — without it two entities that share a FK column name (e.g. both `order`
and `shipment` carry `plant_id`) collide and the build cannot tell which join applies.
**Domain** = `intra` (parent in this domain) or `cross` (parent in another domain). **Resolution**
= `LEFT JOIN` (resolve to the loaded parent) or `NULL`/`-1` (unresolved — cross-domain parent
absent, or documented orphan). **Join Condition** MUST be the explicit, complete predicate,
including every column of a composite join — so the build never reverse-engineers it from schema
inspection.*

*"Values verified equal?" MUST be `yes` before build — sample both tables during discovery
(Phase 3/4) and confirm the fact source column and the chosen dim attribute contain the
exact same values. If they differ, that is the join attribute mismatch this table exists
to catch.*

> **PK generation AND FK resolution use the ONE canonical formula.** The surrogate a dimensional
> PK is hashed with, and the hash a FK column is resolved against, both come from
> `conventions.yml` `surrogate_key_formula` (`bigint` / `string` variant per the model's declared
> PK type) — do NOT restate a hash here or in §5. The build reads the formula from `conventions.yml`
> (`naming-standards.md` "key strategy by mode"); this spec only names the natural key it applies to.

---

## Section 4 — Load Order Override

*Only fill if you want to override the discovered dependency order.*

1.
2.

---

## Section 5 — Load Strategy (per entity — do NOT default everything to full MERGE)

*Full-source-scan Type-1 MERGE is correct only for small tables. Choose the strategy per
entity by **mutability first, then volume**. The assessment skill pre-fills this from the
Step 2.6 Mutability Probe (or the ETL skill runs the probe itself if the spec is authored
without an assessment); confirm before build. See `merge-and-defensive-coding.md` "Load
Strategy Decision".*

| Entity | Source row count | Mutable after insert? | pct_mutated (probe) | Watermark column | Chosen strategy | SCD (type_1/type_2) | Rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | yes / no | ≈ 0 (append-only) / > 0 (mutable) | col name or none | see table below | type_1 (default) | |

*The **SCD** column is a per-entity override of `conventions.yml scd_strategy` — set `type_2` on
the specific dimensions that need point-in-time history. Valid only in `output_model: dimensional`
or `hybrid`-gold; `type_2` on a `normalized`-silver entity is invalid (redirect to `hybrid`).
`type_2` uses the versioning MERGE (not full-refresh) and forces surrogate keys on.*

*`pct_mutated` = `100 * rows where last_update > creation / total` (Step 2.6 probe). ≈ 0 proves
append-only; > 0 proves the rows mutate and names the watermark. `—` = no update timestamp
exists (escalation trigger for mutable facts).*

**Strategy decision (pick per entity — mutability decides, size only chooses between the mutable options):**

| Condition | Strategy | Why |
| --- | --- | --- |
| Append-only ledger — `pct_mutated ≈ 0`, or event/transaction grain (any size) | `APPEND_ONLY` (`WHEN NOT MATCHED`-only / anti-join INSERT) | Rows never change; skip UPDATE branch AND full-target scan. Biggest cost win. |
| Mutable, < ~5M rows | `FULL_MERGE` (Type-1) | Full scan is cheap at this size; keep it simple. |
| Mutable, 5M–100M, **has** update ts | `INCREMENTAL_MERGE` (watermark) | `WHERE {update_ts} > (SELECT MAX(_source_updated_at) FROM tgt)` — only re-read changed rows. |
| Mutable > 100M, **or mutable with no usable watermark**, or SCD2/streaming DQ needed | `SDP` (escalate to Lakeflow) | Full MERGE won't survive / can't watermark; use AUTO CDC. **Needs CDF on bronze** — flag as cross-team dependency. |

*CDF footnote: `APPEND_ONLY` and `INCREMENTAL_MERGE` need **no** Change Data Feed — they're
filtered SELECTs on a timestamp. Only the `SDP` tier (deletes / SCD2 / mutable-no-watermark)
requires `delta.enableChangeDataFeed = true` on the bronze source, enabled going forward.*

*When `etl_type: sdp_pipeline`: the **Chosen strategy** column records the SDP object + flow
instead of a MERGE variant — `MV` (materialized view, recomputable dim), `ST-APPEND` (streaming
table, append-only fact), `ST-CDC1` / `ST-CDC2` (streaming table + AUTO CDC, SCD1/SCD2). The
mutability/volume classification is unchanged; see `sdp-pipeline-development.md`
"Load-strategy → SDP object mapping".*

*Global defaults (only used where the per-entity table is blank):*

| Setting | Value | Rationale |
| --- | --- | --- |
| `surrogate_key_method` | `SHA2` / `NONE` | |
| `merge_key_alignment` | cluster/partition target on the incremental predicate | A random SHA2 merge key defeats file-skipping — align cluster key or merge on business key + date. |

---

## Section 6 — Data Quality Thresholds

| Check | Entity | Threshold | Action (warn / fail) |
| --- | --- | --- | --- |
| PK uniqueness | all | 0 duplicates | fail |
| FK orphan rate | all | 0 orphans | fail |
| Column population | | ≥ 95% non-null | warn |
| Row count delta | | ≤ 10% drop vs prior run | warn |

---

## Section 7 — Conventions (from `conventions.yml`)

> **Copy the FULL `naming:` block from `conventions.yml` here verbatim** — not a hand-picked
> subset. The build applies these to every generated DDL/MERGE artifact (see
> `naming-standards.md`). Section 1/2/3 names above must ALREADY reflect them; this block is the
> reference the build validates against.

```yaml
etl_language:          # sql | python
surrogate_key_method:  # SHA2 | NONE
naming:
  table_case:            # e.g. lower_snake
  dim_prefix:            # e.g. "dim_"
  fact_prefix:           # e.g. "fact_"
  bridge_prefix:         # e.g. "bridge_"
  gold_prefix:           # e.g. "" (gold has no dim_/fact_ prefix)
  entity_form:           # singular | plural
  business_column_case:  # e.g. Pascal_Snake
  metadata_column_case:  # e.g. _lower_snake
  surrogate_key_suffix:  # e.g. "_Key"
  fk_naming:             # e.g. same_as_parent_pk
# Locations (Section 0) + bronze_sources map:
silver_catalog:        # WRITE target
silver_schema:         # WRITE target
vibe_model_catalog:    # READ-ONLY model source
vibe_model_schema:     # READ-ONLY model source
bronze_schemas:        # logical src_* -> catalog.schema
```
