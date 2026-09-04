# DDL Templates & Modeling Rules

## When to Use

After discovery is approved (Phase 1), generate all DDL before any MERGE notebooks.
Targets must exist before load. Apply the naming standards from `naming-standards.md`.

---

## Which templates apply — `output_model` decides

The templates in this file are **mode-conditional**. Read `conventions.yml` → `output_model`
first and use the matching set:

| `output_model` | Silver templates to use | Notes |
|---|---|---|
| **`dimensional`** | **Silver Dimension / Fact / Bridge** (below) — `dim_/fact_/bridge_`, `{Entity}_Key` SHA2 surrogates | The vibe model's products are the SEED; you re-shape into a star. Kimball rules apply. |
| **`normalized`** *(default)* | **Normalized Product template** (below) — one table per vibe-model product, 3NF, the model's PK/FK, no `dim_/fact_` prefix | Inherits the model's structure; NO Kimball rules, NO re-validation of the agent's rules. Keys follow the model. |
| **`hybrid`** | **Layered (not both-at-once):** **Normalized Product** for silver, THEN Dimension/Fact/Bridge emitted into the **gold** layer downstream from that silver | Silver = the normalized SSOT (built first); the star (surrogates, any SCD2) reads silver and lives in gold. |

`scd_strategy: type_2` (dimensional / hybrid-gold only) swaps the plain dimension template for
the **SCD Type-2 Dimension** template below. See `merge-and-defensive-coding.md` for the matching
versioning MERGE.

> **All modes CREATE fresh into `catalogs.silver`** and never write to the vibe model — the model
> is a read-only logical spec (`SKILL.md` "Layering Contract"). `{Entity}_Key`/`{entity}_id` fills
> below resolve per the mode's key strategy (`naming-standards.md` "key strategy by mode").

---

## Runtime Parameters (target catalog/schema are NOT literals)

**Every generated notebook reads its target catalog + schema from widgets at run time**
so the same notebook object promotes dev→prod unchanged — the DAB job passes the values in
per target (see `deployment-and-dab.md` "Runtime Parameters"). Do NOT bake catalog/schema
literals into DDL.

The pattern: declare widgets, set the **session** catalog + schema from them, then reference
target tables **UNQUALIFIED** (they resolve to the session `catalog.schema`). This keeps the
env-specific surface to a two-line header — every table/constraint below is env-agnostic.

Every silver DDL notebook starts with this header block (gold uses `gold_catalog`/`gold_schema`). DDL notebooks are **ALWAYS SQL** regardless of `etl_language` — the first line is always `-- Databricks notebook source`:

```sql
-- Databricks notebook source
-- Runtime params — defaults come from conventions.yml; the job overrides per target.
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';

-- COMMAND ----------
-- Set session context so all UNQUALIFIED refs below resolve to the target env.
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);

-- COMMAND ----------
```

> `{placeholder}` tokens that remain in the templates below (`{entity}`, `{Natural_Key}`,
> `{type}`, `{domain}`, …) are **authoring-time** structural fills resolved by the generator.
> Only catalog/schema are runtime params. `{silver_schema}` inside `SET TAGS` values etc. is
> fine as a literal *tag value*, but table **references** are always unqualified.

---

## Silver Dimension DDL Template

Header block above, then:

```sql
CREATE TABLE IF NOT EXISTS dim_{entity} (
  {Entity}_Key     BIGINT    NOT NULL COMMENT 'Surrogate key — SHA2 of {natural_key}',
  {Natural_Key}    {type}    NOT NULL COMMENT '{Business description of natural key}',
  {Attr_Col_1}     {type}             COMMENT '{Description}',
  {Attr_Col_2}     {type}             COMMENT '{Description}',
  _source_system   STRING    NOT NULL COMMENT 'Originating source system (e.g. SAP_SF, ORACLE_EBS)',
  _loaded_at       TIMESTAMP NOT NULL COMMENT 'UTC timestamp of last load',
  _created_by      STRING             COMMENT 'DAB job name that first created this row',
  _modified_by     STRING             COMMENT 'DAB job name that last modified this row',
  _batch_id        STRING             COMMENT 'Job run ID for traceability',
  CONSTRAINT pk_dim_{entity} PRIMARY KEY ({Entity}_Key)
)
USING DELTA
CLUSTER BY ({Natural_Key})
COMMENT 'Silver dimension. One row per {grain}. Source: {source_table}.';

-- Apply UC tags
ALTER TABLE dim_{entity} SET TAGS (
  'domain' = '{domain}', 'layer' = 'silver',
  'subject_area' = '{subject_area}', 'pii_present' = '{true|false}'
);

-- Seed -1 Unknown member
MERGE INTO dim_{entity} AS t
USING (SELECT CAST(-1 AS BIGINT) AS {Entity}_Key) s
ON t.{Entity}_Key = s.{Entity}_Key
WHEN NOT MATCHED THEN INSERT ({Entity}_Key, {Natural_Key}, _source_system, _loaded_at)
  VALUES (-1, 'UNKNOWN', 'SYSTEM', current_timestamp());
```

---

## Normalized Product DDL Template  *(output_model: normalized / hybrid-silver)*

One table per **vibe-model product**, named exactly as the model names it (no `dim_/fact_`
prefix), preserving the model's PK and FK graph. This is the "materialize the spec + engineering
scaffolding" path — no surrogate keys unless the model's PK is composite/mutable, no Kimball
re-shaping. Header block above, then:

```sql
CREATE TABLE IF NOT EXISTS {product} (            -- model's product name verbatim (e.g. customer, order)
  {product}_id     {type}    NOT NULL COMMENT '{PK per the vibe model — keep the model''s name/type}',
  {parent}_id      {type}             COMMENT 'FK to {parent} per the model''s FK graph; NULL if unresolved',
  {Attr_Col_1}     {type}             COMMENT '{Description — column name/casing follows the model}',
  {Attr_Col_2}     {type}             COMMENT '{Description}',
  _source_system   STRING    NOT NULL COMMENT 'Originating source system',
  _loaded_at       TIMESTAMP NOT NULL COMMENT 'UTC timestamp of last load',
  _created_by      STRING             COMMENT 'DAB job name that first created this row',
  _modified_by     STRING             COMMENT 'DAB job name that last modified this row',
  _batch_id        STRING             COMMENT 'Job run ID for traceability',
  CONSTRAINT pk_{product} PRIMARY KEY ({product}_id),
  CONSTRAINT fk_{product}_{parent} FOREIGN KEY ({parent}_id)
    REFERENCES {parent}({parent}_id)              -- FK graph mirrors the model's DAG
)
USING DELTA
CLUSTER BY ({product}_id)
COMMENT 'Silver (normalized). One row per {grain}. Seeded by vibe model product `{product}`.';

-- Apply UC tags (same governance as dimensional)
ALTER TABLE {product} SET TAGS (
  'domain' = '{domain}', 'layer' = 'silver',
  'subject_area' = '{subject_area}', 'pii_present' = '{true|false}'
);
```

**Normalized-mode rules:**
- **Keys follow the model** — keep `{product}_id` (or whatever the model declares); do NOT
  overlay `{Entity}_Key` SHA2 surrogates. Add a surrogate ONLY where the model PK is
  composite/mutable or cross-source integration requires one (`naming-standards.md`).
- **No `-1` Unknown member seeding** — that is a dimensional-join convention. Normalized FKs may
  be `NULL` when unresolved (record the unresolved-FK count as a DQ metric, not a `-1` sentinel).
- **FK graph mirrors the model's DAG** — child→parent, no cycles; same SSOT the agent enforced.
- **Do NOT re-litigate the agent's 3NF/SSOT rules** — the spec already passed them. Validate
  reconciliation-to-bronze + build quality only.
- A **DEFERRED** product (no bronze source) is still CREATEd here as an unpopulated table with a
  `COMMENT 'DEFERRED — needs bronze {X}; see gap registry'`, so the future-enhancement is visible
  in the catalog (see `discovery-and-gap-analysis.md`).

---

## SCD Type-2 Dimension DDL Template  *(scd_strategy: type_2 — dimensional / hybrid-gold only)*

Versioned history: a **new surrogate per version**, natural key stable across versions, current
row flagged. Facts join to the version current at event time. **Invalid in `normalized` mode** —
error early if `output_model: normalized` + `scd_strategy: type_2` (redirect to `hybrid`).

```sql
CREATE TABLE IF NOT EXISTS dim_{entity} (
  {Entity}_Key      BIGINT    NOT NULL COMMENT 'Surrogate key — SHA2 of natural key + _effective_from (one per version)',
  {Natural_Key}     {type}    NOT NULL COMMENT '{Business natural key — STABLE across versions}',
  {Attr_Col_1}      {type}             COMMENT '{Description}',
  _effective_from   TIMESTAMP NOT NULL COMMENT 'UTC start of this version''s validity',
  _effective_to     TIMESTAMP          COMMENT 'UTC end of validity; NULL = open/current',
  _is_current       BOOLEAN   NOT NULL COMMENT 'TRUE for the current version of this natural key',
  _source_system    STRING    NOT NULL COMMENT 'Originating source system',
  _loaded_at        TIMESTAMP NOT NULL COMMENT 'UTC timestamp of last load',
  _created_by       STRING             COMMENT 'DAB job name that first created this row',
  _modified_by      STRING             COMMENT 'DAB job name that last modified this row',
  _batch_id         STRING             COMMENT 'Job run ID for traceability',
  CONSTRAINT pk_dim_{entity} PRIMARY KEY ({Entity}_Key)
)
USING DELTA
CLUSTER BY ({Natural_Key})
COMMENT 'Silver SCD Type-2 dimension. One row per version of {grain}. Source: {source_table}.';

-- Apply UC tags
ALTER TABLE dim_{entity} SET TAGS (
  'domain' = '{domain}', 'layer' = 'silver',
  'subject_area' = '{subject_area}', 'pii_present' = '{true|false}', 'scd' = 'type_2'
);

-- Seed -1 Unknown member (current, open-ended)
MERGE INTO dim_{entity} AS t
USING (SELECT CAST(-1 AS BIGINT) AS {Entity}_Key) s
ON t.{Entity}_Key = s.{Entity}_Key
WHEN NOT MATCHED THEN INSERT ({Entity}_Key, {Natural_Key}, _effective_from, _effective_to, _is_current, _source_system, _loaded_at)
  VALUES (-1, 'UNKNOWN', TIMESTAMP'1900-01-01', NULL, TRUE, 'SYSTEM', current_timestamp());
```

> The surrogate hash MUST include `_effective_from` (or a version discriminator) so each version
> gets a distinct key. Facts resolve the FK by joining on natural key AND
> `event_ts BETWEEN _effective_from AND COALESCE(_effective_to, TIMESTAMP'9999-12-31')`. See the
> Type-2 versioning MERGE in `merge-and-defensive-coding.md`.

---

## Silver Fact DDL Template

Header block (silver widgets + `USE CATALOG`/`USE SCHEMA`) above, then:

```sql
CREATE TABLE IF NOT EXISTS fact_{name} (
  {Name}_Key      BIGINT       NOT NULL COMMENT 'Surrogate key — SHA2 of grain natural keys',
  {DimA}_Key      BIGINT       NOT NULL COMMENT 'FK to dim_{A} — -1 = Unknown',
  {DimB}_Key      BIGINT       NOT NULL COMMENT 'FK to dim_{B} — -1 = Unknown',
  {Natural_Key}   {type}       NOT NULL COMMENT '{Business description of natural key}',
  {Degenerate}    STRING                COMMENT 'Degenerate dimension (e.g. transaction number)',
  {Measure_Amt}   DECIMAL(18,2)         COMMENT '{Measure description}',
  {Measure_Cnt}   BIGINT                COMMENT '{Count description}',
  _source_system  STRING       NOT NULL COMMENT 'Originating source system',
  _loaded_at      TIMESTAMP    NOT NULL COMMENT 'UTC timestamp of last load',
  _created_by     STRING                COMMENT 'DAB job name that first created this row',
  _modified_by    STRING                COMMENT 'DAB job name that last modified this row',
  _batch_id       STRING                COMMENT 'Job run ID for traceability',
  CONSTRAINT pk_fact_{name} PRIMARY KEY ({Name}_Key),
  CONSTRAINT fk_fact_{name}_{A} FOREIGN KEY ({DimA}_Key)
    REFERENCES dim_{A}({A}_Key),
  CONSTRAINT fk_fact_{name}_{B} FOREIGN KEY ({DimB}_Key)
    REFERENCES dim_{B}({B}_Key)
)
USING DELTA
CLUSTER BY ({DimA}_Key)
COMMENT 'Silver fact. GRAIN: one row per {explicit grain statement}.';

-- Apply UC tags
ALTER TABLE fact_{name} SET TAGS (
  'domain' = '{domain}', 'layer' = 'silver',
  'subject_area' = '{subject_area}', 'pii_present' = '{true|false}'
);

-- Add CHECK constraints after table creation
ALTER TABLE fact_{name}
  ADD CONSTRAINT chk_fact_{name}_{measure} CHECK ({Measure_Amt} >= 0);
```

---

## Silver Bridge Table DDL Template

Header block (silver widgets + `USE CATALOG`/`USE SCHEMA`) above, then:

```sql
CREATE TABLE IF NOT EXISTS bridge_{dim_a}_{dim_b} (
  {DimA}_{DimB}_Key   BIGINT    NOT NULL COMMENT 'Surrogate key — SHA2 of {NKa} + {NKb}',
  {DimA}_Key          BIGINT    NOT NULL COMMENT 'FK to dim_{a}; -1 = Unknown',
  {DimB}_Key          BIGINT    NOT NULL COMMENT 'FK to dim_{b}; -1 = Unknown',
  Allocation_Pct      DECIMAL(5,2)       COMMENT 'Percentage allocation (if applicable)',
  Effective_Date      DATE               COMMENT 'Date this association became active',
  _source_system      STRING    NOT NULL COMMENT 'Originating source system',
  _loaded_at          TIMESTAMP NOT NULL COMMENT 'UTC timestamp of last load',
  _created_by         STRING             COMMENT 'DAB job name that first created this row',
  _modified_by        STRING             COMMENT 'DAB job name that last modified this row',
  _batch_id           STRING             COMMENT 'Job run ID for traceability',
  CONSTRAINT pk_bridge_{dim_a}_{dim_b} PRIMARY KEY ({DimA}_{DimB}_Key),
  CONSTRAINT fk_bridge_{dim_a}_{dim_b}_{a} FOREIGN KEY ({DimA}_Key)
    REFERENCES dim_{a}({A}_Key),
  CONSTRAINT fk_bridge_{dim_a}_{dim_b}_{b} FOREIGN KEY ({DimB}_Key)
    REFERENCES dim_{b}({B}_Key)
)
USING DELTA
CLUSTER BY ({DimA}_Key)
COMMENT 'Silver bridge. GRAIN: one row per ({NKa}, {NKb}) assignment.';

-- Seed -1 Unknown member
MERGE INTO bridge_{dim_a}_{dim_b} AS t
USING (SELECT CAST(-1 AS BIGINT) AS {DimA}_{DimB}_Key) s
ON t.{DimA}_{DimB}_Key = s.{DimA}_{DimB}_Key
WHEN NOT MATCHED THEN INSERT ({DimA}_{DimB}_Key, {DimA}_Key, {DimB}_Key, _source_system, _loaded_at)
  VALUES (-1, -1, -1, 'SYSTEM', current_timestamp());
```

---

## Gold Table DDL Template

Header block using the **gold** widgets (`CREATE WIDGET TEXT gold_catalog` / `gold_schema`,
then `USE CATALOG IDENTIFIER(:gold_catalog); USE SCHEMA IDENTIFIER(:gold_schema);`), then:

```sql
CREATE TABLE IF NOT EXISTS {business_name} (
  {Business_Col_1}  {type}       COMMENT '{Description}',
  {Business_Col_2}  {type}       COMMENT '{Description}',
  {Measure_Amt}     DECIMAL(18,2) COMMENT '{Description}',
  _source_system    STRING        COMMENT 'Source system inherited from silver',
  _inserted_at      TIMESTAMP NOT NULL COMMENT 'UTC timestamp of initial row creation',
  _updated_at       TIMESTAMP NOT NULL COMMENT 'UTC timestamp of last refresh',
  _created_by       STRING        COMMENT 'DAB job name that first created this row',
  _modified_by      STRING        COMMENT 'DAB job name that last refreshed this row'
)
USING DELTA
CLUSTER BY ({primary_bi_filter_column})
COMMENT 'Gold table. {Business purpose}. GRAIN: {grain statement}.';

-- Apply UC tags
ALTER TABLE {business_name} SET TAGS (
  'domain' = '{domain}', 'layer' = 'gold',
  'subject_area' = '{subject_area}', 'pii_present' = '{true|false}'
);
```

> Gold tables do NOT use `dim_` or `fact_` prefixes. They are use-case tables.
> Gold tables may omit PK/FK constraints unless a primary key on the grain is meaningful.

---

## Modeling Rules Summary

Rules 1–4 are **Kimball rules — `dimensional` mode (and `hybrid` gold) only.** In `normalized`
mode they DO NOT apply (see the Normalized-mode rules under the Normalized Product template);
rules 5–10 apply in all modes.

1. **Grain first** — every fact's CREATE comment states its grain explicitly
2. **Conformed dims** — one `dim_customer` shared across facts, never per-fact copies
3. **Surrogate keys** — deterministic SHA2 of the natural key, never IDENTITY
4. **-1 Unknown member** — seed every dim so missing FKs map to -1 instead of orphaning
5. **Constraints** — informational PK/FK for BI tooling; enforced NOT NULL on keys; enforced CHECK on safe invariants. CHECK via ALTER TABLE (not inline).
6. **Comments** — table + every column commented. **The `COMMENT` in `ddl/*.sql` is the SOURCE OF
   TRUTH for table/column descriptions.** Any later metadata enrichment (the documentation loop, a
   Genie-space description pass, UC comment polish) MUST round-trip back into the `ddl/*.sql` file —
   never apply comments only via `COMMENT ON` / `ALTER TABLE ... SET TBLPROPERTIES` against the live
   table, or the DDL silently drifts from the deployed schema and the next `bundle deploy` / re-run
   reverts them. If a downstream skill authors better descriptions, it edits the DDL and re-runs it as
   the setup step; live-table-only comment edits are a drift bug. (Flagged from the Meridian run: the
   doc loop edited comments in place instead of the DDL.)
7. **Column ordering** — SK → FK(s) → NK → business attrs → degenerate dims → measures → metadata
8. **UC Tags** — applied immediately after CREATE TABLE
9. **Gold builds from silver** — never re-reads bronze
10. **PAUSE** — present the full DDL set for approval before scaffolding MERGE logic

---

## DDL File Naming & Organization

DDL notebooks are organized in **per-layer subfolders**:

- Silver DDL (`dimensional`): `src/silver/ddl/ddl_dim_{entity}.sql`, `ddl_fact_{name}.sql`, `ddl_bridge_{a}_{b}.sql`
- Silver DDL (`normalized` / `hybrid`-silver): `src/silver/ddl/ddl_{product}.sql` — product-named, no `dim_/fact_` prefix
- Gold DDL: `src/gold/ddl/ddl_{business_name}.sql` (+ in `hybrid`, the `ddl_dim_/ddl_fact_/ddl_bridge_` star lands under `src/gold/ddl/`)

**One DDL notebook per table** — never combine multiple tables into a single DDL file.

Each DDL file contains (in order):
1. `-- Databricks notebook source` (required first line — **DDL notebooks are ALWAYS SQL**, regardless of `etl_language`)
2. **Runtime-param header** — `CREATE WIDGET TEXT {layer}_catalog/{layer}_schema` then
   `USE CATALOG IDENTIFIER(:...)` / `USE SCHEMA IDENTIFIER(:...)` (own cells). This is what
   lets the notebook promote dev→prod unchanged — never hard-code the catalog/schema.
3. `CREATE TABLE IF NOT EXISTS {unqualified_table}` with full column definitions
4. `ALTER TABLE {unqualified_table} SET TAGS` for UC governance
5. `ALTER TABLE {unqualified_table} ADD CONSTRAINT ... CHECK` for safe invariants (facts)
6. `MERGE INTO {unqualified_table} USING (SELECT -1 ...)` for Unknown member seeding (dims and bridges only)

All sections are in a single DDL notebook file per table, separated by `-- COMMAND ----------`
cells. They run sequentially as one notebook_task. Because the session catalog/schema are set
in the header, every table reference below it is **unqualified** — the only env-specific lines
are the two `USE` statements.
