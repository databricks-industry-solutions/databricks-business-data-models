# SDP Templates (etl_type: sdp_pipeline)

> Part of the `sdp_pipeline` template pack. Overview + when-to-use + build loop:
> `sdp-pipeline-development.md`. Deployment: `sdp-deployment.md`. Hybrid gold star: `sdp-gold-star.md`.

## Templates — SQL dialect (`etl_language: sql`)

**Materialized view (recomputable dimension):**

```sql
-- Databricks notebook source
-- Declarative source: dim_plant (materialized view). Inline schema + EXPECT + query.
CREATE OR REFRESH MATERIALIZED VIEW dim_plant (
  Plant_Key      BIGINT      COMMENT 'Surrogate key (SHA2 of natural key)',
  Plant_Bk       STRING      COMMENT 'Natural/business key',
  Plant_Name     STRING      COMMENT 'Plant display name',
  _source_system STRING      COMMENT 'Originating system',
  CONSTRAINT valid_bk EXPECT (Plant_Bk IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Plant_Key)
COMMENT 'Conformed plant dimension'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(Code AS STRING),'~')),256),1,15),16,10) AS BIGINT) AS Plant_Key,
  Code AS Plant_Bk,
  NULLIF(TRIM(Name),'') AS Plant_Name,
  'SAP_S4' AS _source_system
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY Code ORDER BY LAST_UPDATE_DATE DESC) AS _rn
  FROM manufacturing_bronze.sap_sd.tbl_plants   -- hardcoded fully-qualified bronze path (see below)
) WHERE _rn = 1;
```

**Streaming table + AUTO CDC (SCD1 mutable dim / fact upsert):**

```sql
-- Databricks notebook source
-- Declarative source: dim_customer (streaming table + AUTO CDC, SCD type 1).
CREATE OR REFRESH STREAMING TABLE dim_customer (
  Customer_Key   BIGINT  COMMENT 'Surrogate key',
  Customer_Bk    STRING  COMMENT 'Natural key',
  Customer_Name  STRING  COMMENT 'Name',
  _source_system STRING,
  CONSTRAINT valid_bk EXPECT (Customer_Bk IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Customer_Key)
COMMENT 'Customer dimension (SCD1)';

CREATE FLOW customer_cdc AS AUTO CDC INTO dim_customer
FROM (
  SELECT
    CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',COALESCE(CAST(cust_id AS STRING),'~')),256),1,15),16,10) AS BIGINT) AS Customer_Key,
    cust_id AS Customer_Bk,
    NULLIF(TRIM(cust_name),'') AS Customer_Name,
    'SALESFORCE' AS _source_system,
    last_modified AS _source_updated_at
  FROM STREAM manufacturing_bronze.salesforce_crm.accounts   -- hardcoded fully-qualified bronze path
)
KEYS (Customer_Bk)
SEQUENCE BY _source_updated_at
STORED AS SCD TYPE 1;
```

**SCD Type 2** — identical to the SCD1 flow but `STORED AS SCD TYPE 2` (SDP manages
`__START_AT`/`__END_AT` version columns; declare them in the table spec per the current docs).
This REPLACES the two-statement versioning MERGE in `merge-and-defensive-coding.md`.

**Append-only ledger fact (streaming table, no CDC):**

```sql
CREATE OR REFRESH STREAMING TABLE fact_material_txn (
  Material_Txn_Key BIGINT,
  Txn_Bk           STRING,   -- degenerate natural key, retained so the grain EXPECT has a real column to test
  Plant_Key        BIGINT,
  Txn_Amt          DECIMAL(18,2),
  _source_system   STRING,
  -- Guard the GRAIN on the natural key, NOT the surrogate. The SHA2 surrogate is never NULL
  -- (COALESCE(..,'~') always hashes to a value), so a constraint on Material_Txn_Key can never
  -- fire -- a row with a NULL txn_id would slip through under a fabricated key. Test the source NK.
  CONSTRAINT valid_grain EXPECT (Txn_Bk IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Plant_Key)
AS SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',COALESCE(CAST(txn_id AS STRING),'~')),256),1,15),16,10) AS BIGINT) AS Material_Txn_Key,
  CAST(txn_id AS STRING) AS Txn_Bk,
  COALESCE(p.Plant_Key,-1) AS Plant_Key,
  TRY_CAST(s.amount AS DECIMAL(18,2)) AS Txn_Amt,
  'SAP_S4' AS _source_system
FROM STREAM manufacturing_bronze.sap_sd.material_txn s   -- hardcoded fully-qualified bronze path
LEFT JOIN dim_plant p ON p.Plant_Bk = TRIM(s.plant_code);
```

> 🔴 **Bronze source paths are HARDCODED as fully-qualified `catalog.schema.table` — SDP does not
> parameterize them.** The native LDP `parameters:` block is a **beta**, and it only half-works:
> `IDENTIFIER(:param)` resolves in a **materialized view** `AS SELECT`, but `STREAM
> IDENTIFIER(:param …)` in a `CREATE STREAMING TABLE`/`CREATE FLOW` fails at runtime with
> `[UNRESOLVABLE_TABLE_VALUED_FUNCTION]` (hit on a real build). Rather than carry a half-working
> beta and split MV-vs-ST parameterization rules, **SDP hardcodes every bronze path** — in both MV
> and ST sources, both SQL and Python. The bronze catalog/schema for a domain is a build-time
> constant from `conventions.yml` `bronze_sources:`; write it directly into each source. Do NOT
> emit a pipeline `parameters:` block, `:param` markers, `IDENTIFIER(:param)`, or `spark.conf.get`
> for bronze paths. (Revisit if/when native parameters leaves beta and supports streaming sources.)

> **FK resolution** still LEFT JOINs the already-defined dim (Rule 11 from
> `merge-and-defensive-coding.md`) and COALESCEs misses to -1 — never inline-recompute the FK
> surrogate from the fact source.
>
> 🔴 **Every FK-resolution LEFT JOIN must be 1:1 on the lookup side — or it fans out the fact.** If
> the parent table has more than one row per join key, the LEFT JOIN multiplies fact rows and breaks
> the grain. A real build hit this: the silver `order` entity LEFT JOINed `quote` on
> `converted_order_number`, but multiple quotes shared the same value → **136 duplicate order rows**.
> This is Rule 3 / Rule 11 from `merge-and-defensive-coding.md`, and it applies identically to SDP
> MVs and streaming tables. **Wherever the lookup side is not guaranteed unique on the join key**
> (especially cross-source joins, where the foreign system's schema gives you no uniqueness
> guarantee), dedup it in a subquery/CTE first:
> `... FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY join_key ORDER BY <recency> DESC) AS _rn FROM parent) WHERE _rn = 1`.
> Verify grain with a PK-count check after the first run (declared count == distinct-NK count).
>
> ⚠️ **Stream-static join permanence (append-only only).** In a `ST-APPEND` fact this LEFT JOIN
> is a **stream-static** join: each fact row's FK is resolved to whatever the dim held **at append
> time**. Because the fact is append-only (no CDC, no reprocessing), a row that arrives before its
> `dim_plant` row materializes — or whose plant key later changes — is written with `Plant_Key = -1`
> and **stays -1 forever**, even after the dimension catches up. Two mitigations: (a) enforce the
> **wave order** so all wave-1 dims materialize before wave-2 facts in the same pipeline update
> (declare the dim reference so SDP orders it first), and (b) if late-arriving dimension members are
> expected and FK completeness matters, make the fact a **materialized view** (recomputable) instead
> of `ST-APPEND`, trading incremental cost for correct re-resolution. Flag this trade-off in the spec.

## Templates — Python dialect (`etl_language: python`)

Same objects via the `@dlt` decorators. Bronze paths are **hardcoded** fully-qualified strings
(no `spark.conf.get`, no parameters — see the Parameterization note). **Confirm at implementation:**
the Python source module generation (`import dlt` — classic, vs `from pyspark.pipelines import dlt`
— newer) must match the installed runtime; verify against the target DBR/LDP runtime before
authoring.

```python
# Databricks notebook source
import dlt
from pyspark.sql import functions as F

# STEP 1 — a streaming view does the derivation (surrogate, renames, audit ts). The AUTO CDC
# flow's keys/sequence_by/expectations reference the DERIVED column names, so its source MUST be
# this transformed view — NOT the raw `accounts` table (raw has cust_id/cust_name/last_modified,
# not Customer_Bk/_source_updated_at). Pointing the flow straight at raw errors column-not-found.
@dlt.view(name="v_customer_src")
def v_customer_src():
    return (
        spark.readStream.table("manufacturing_bronze.salesforce_crm.accounts")  # hardcoded bronze path
        .select(
            F.expr(
                "CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',COALESCE(CAST(cust_id AS STRING),'~')),256),1,15),16,10) AS BIGINT)"
            ).alias("Customer_Key"),
            F.col("cust_id").alias("Customer_Bk"),
            F.nullif(F.trim(F.col("cust_name")), F.lit("")).alias("Customer_Name"),
            F.lit("SALESFORCE").alias("_source_system"),
            F.col("last_modified").alias("_source_updated_at"),
        )
    )

# STEP 2 — the streaming target + AUTO CDC flow reference the view's derived columns.
dlt.create_streaming_table(
    name="dim_customer",
    comment="Customer dimension (SCD1)",
    cluster_by=["Customer_Key"],
    expect_all_or_drop={"valid_bk": "Customer_Bk IS NOT NULL"},
)
dlt.create_auto_cdc_flow(
    target="dim_customer",
    source="v_customer_src",          # the DERIVED view, not the raw table
    keys=["Customer_Bk"],
    sequence_by=F.col("_source_updated_at"),
    stored_as_scd_type=1,
)
```

> Confirm `create_auto_cdc_flow(... stored_as_scd_type=2)` against the installed SDK when
> authoring SCD2. Bronze paths are hardcoded literals (see Parameterization) — never interpolate
> analyst/free-text into `spark.sql`/f-strings; the only interpolated values are build-time
> config constants.

## Normalized-mode templates (`output_model: normalized` / `hybrid`-silver)

The templates above are written in the **dimensional** shape (`dim_/fact_` names, BIGINT SHA2
`_Key` surrogates, `-1` Unknown members, `COALESCE(dim.Key,-1)`). In the default **`normalized`**
mode — and the **silver layer of `hybrid`** — objects instead **follow the vibe model**: product
names, **STRING** SHA2 PKs, `NULL` (never `-1`) as the FK sentinel, no Unknown-member seed. Use the
conventions below rather than re-deriving them per build.

**Canonical normalized MV:**

```sql
-- Databricks notebook source
CREATE OR REFRESH MATERIALIZED VIEW order_line (
  order_line_id           STRING COMMENT 'PK: SHA2(vbeln|posnr). {vibe-model comment}',
  order_id                STRING COMMENT 'FK to order via SHA2(vbeln) -- mandatory (part of grain). {vibe-model comment}',
  order_reason_id         STRING COMMENT 'Optional FK to order_reason; NULL when the source has no reason code. {vibe-model comment}',
  sku_id                  STRING COMMENT 'Cross-domain FK (NULL, product_lifecycle domain). {vibe-model comment}',
  line_number             STRING COMMENT 'SAP line item number (posnr). {vibe-model comment}',
  source_system           STRING COMMENT 'Originating system (model business column -- see source_system note)',
  source_system_line_key  STRING COMMENT 'Natural key from source (vbeln|posnr); NULL when a key part is missing -- the grain guard column',
  _loaded_at              TIMESTAMP COMMENT 'UTC load time (audit)',
  -- Grain guard: EXPECT on the NATURAL-KEY column, which is computed NULL when a key part is missing
  -- (NOT the SHA2 PK -- it hashes '~' and is never NULL; NOT a WHERE filter -- see note below).
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW,
  -- Soft FK-health: only meaningful on a FK computed NULL-on-missing (order_reason_id below).
  -- Do NOT put it on order_id -- a COALESCE(...,'~') hash is never NULL, so the EXPECT is a no-op.
  CONSTRAINT fk_order_reason EXPECT (order_reason_id IS NOT NULL)
)
CLUSTER BY (order_line_id)
COMMENT 'Order line (normalized silver). {table-level vibe-model description}'
AS SELECT
  SHA2(CONCAT_WS('|', COALESCE(CAST(vbeln AS STRING),'~'), COALESCE(CAST(posnr AS STRING),'~')), 256) AS order_line_id,
  SHA2(COALESCE(CAST(vbeln AS STRING),'~'), 256)  AS order_id,     -- direct SHA2: vbeln is in this source (mandatory)
  CASE WHEN abgru IS NULL THEN NULL                                -- optional FK: NULL when the source key is absent,
       ELSE SHA2(CONCAT_WS('|','SAP_S4', abgru), 256) END AS order_reason_id,   -- so fk_order_reason tracks a real rate
  CAST(NULL AS STRING)                            AS sku_id,       -- cross-domain, unresolved
  CAST(posnr AS STRING)                           AS line_number,
  'SAP_S4'                                        AS source_system,
  -- NK column computed NULL-preserving (NOT CONCAT_WS, which skips NULLs and returns '' -- never NULL)
  -- so valid_pk actually fires when either grain part is missing:
  CASE WHEN vbeln IS NULL OR posnr IS NULL THEN NULL
       ELSE CONCAT_WS('|', vbeln, posnr) END      AS source_system_line_key,
  current_timestamp()                             AS _loaded_at
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, posnr ORDER BY LAST_UPDATE_DATE DESC) AS _rn
  FROM manufacturing_bronze.sap_sd.vbap    -- hardcoded fully-qualified bronze path
) WHERE _rn = 1;
```

**Normalized-mode PK / FK computation.**

> **The PK type follows the model, not `etl_type`.** Read the model's declared PK type before
> emitting the hash. If STRING, use `conventions.yml` `surrogate_key_formula.string`:
> `SHA2(COALESCE(CAST(natural_key AS STRING), '~'), 256) AS entity_id`. If the model declares
> BIGINT PKs, use `surrogate_key_formula.bigint` instead — the SDP path must NOT hardcode STRING.
> `etl_type` never changes the key TYPE; only `output_model` + the model's declared types do. The
> STRING forms below are the `surrogate_key_formula.string` default; swap in `.bigint` when the
> model declares BIGINT.

```sql
-- PK (single natural key) -- surrogate_key_formula.string
SHA2(COALESCE(CAST(natural_key AS STRING), '~'), 256) AS entity_id

-- PK (composite natural key) -- surrogate_key_formula.string
SHA2(CONCAT_WS('|', COALESCE(CAST(key1 AS STRING),'~'), COALESCE(CAST(key2 AS STRING),'~')), 256) AS entity_id

-- FK (direct -- parent key columns exist in the child source; no join needed)
SHA2(COALESCE(CAST(parent_key AS STRING), '~'), 256) AS parent_id

-- FK (conditional -- only compute when the source col is present)
CASE WHEN source_col IS NOT NULL
  THEN SHA2(CONCAT_WS('|', 'SOURCE_SYSTEM', source_col), 256) ELSE NULL END AS reason_id

-- FK (cross-domain, unresolvable in this pipeline)
CAST(NULL AS STRING) AS cross_domain_fk_id
```

> **Grain constraint = inline EXPECT on the natural key, NOT a `WHERE` filter.** It is tempting to
> pre-filter (`... WHERE message_id IS NOT NULL`), but a WHERE drop happens **before the object
> sees the row**, so it never appears in the expectation event log — you lose the observability that
> is the whole point of SDP DQ. Guard the grain with
> `CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW` on the source
> **natural key** (never the SHA2 surrogate — it can't be NULL, see the append-only template note). A
> WHERE filter is acceptable only as a defense-in-depth *secondary* measure, never the primary gate.
>
> 🔴 **The NK column being tested must itself be NULL when a key part is missing.** Do NOT test a
> `CONCAT_WS('|', a, b)`-derived column: `CONCAT_WS` **skips NULL args and returns `''`**, so it is
> never NULL and the EXPECT never fires (rows with all-NULL keys survive and collide on the `'~'`
> hash). Compute the NK column as `CASE WHEN a IS NULL OR b IS NULL THEN NULL ELSE CONCAT_WS('|',a,b)
> END` (or test the raw source columns directly, as the `order_reason` example does on `reason_code`).
> The same trap applies to a soft FK-health `EXPECT (fk IS NOT NULL)`: it is only meaningful when the
> FK is computed NULL-on-missing (the "FK (conditional)" form above) — never on a `COALESCE(...,'~')`
> hash, which is never NULL.

### FK-resolution decision tree (normalized mode)

FK resolution takes one of three forms depending on where the key components live. Decide per FK:

```
FK resolution method:
├── FK key components ALL exist in the child source row?
│   ├── YES → Direct SHA2 computation (no join)
│   │        e.g. order_line.order_id = SHA2(vbeln) — vbeln is in vbap
│   └── NO → the link is indirect / cross-source
│       ├── Parent is in THIS pipeline → JOIN the pipeline MV + dedup CTE (1:1 on lookup side)
│       │    e.g. order.quotation_id via the quotation MV on converted_order_reference,
│       │    ROW_NUMBER() dedup because many quotes can reference one order
│       └── Parent is external / cross-domain → CAST(NULL AS STRING)
│            e.g. order_line.sku_id (product_lifecycle domain, not in this pipeline)
```

The JOIN branch is where the **1:1-on-the-lookup-side** rule (the 136-duplicate-order lesson in the
FK-resolution note above) bites — dedup the parent with
`ROW_NUMBER() OVER (PARTITION BY join_key ORDER BY <recency> DESC)` before joining, and verify grain
with a PK-count check after the first run.

### FK lookup source priority (which table to join)

When an FK needs a join (indirect link) or an attribute needs enrichment, pick the join target in
this order:

1. **FK points to an entity IN THIS PIPELINE** → join the **pipeline MV** (a fully-qualified /
   `LIVE`-style reference creates the dependency edge SDP uses for ordering, so the parent
   materializes first).
2. **FK points to a cross-domain entity NOT in this pipeline** → `CAST(NULL AS STRING)` (record the
   deferral; real resolution is a downstream/cross-domain concern).
3. **Enrichment data (descriptions, labels) lives in a bronze reference table that is NOT modeled as
   a pipeline entity** → join the **bronze table directly** by its hardcoded fully-qualified path
   (e.g. `sap_sd.tvakt` for an order-type description).

### Multi-source reference data (UNION ALL)

When one normalized entity conforms several bronze sources (e.g. `order_reason` from `sap_sd.tvaut`
+ `salesforce_crm.loss_reason_ref` + `returns_portal.rma_reason_code`), UNION them into one MV. The
PK hashes the **source-system label + the source's reason code** so codes never collide across
systems:

```sql
CREATE OR REFRESH MATERIALIZED VIEW order_reason (
  order_reason_id STRING COMMENT 'PK: SHA2(source_system|reason_code)',
  reason_code     STRING COMMENT '{vibe-model comment}',
  source_system   STRING COMMENT 'Originating system',
  CONSTRAINT valid_pk EXPECT (reason_code IS NOT NULL) ON VIOLATION DROP ROW
)
AS
SELECT SHA2(CONCAT_WS('|','SAP_S4', augru), 256) AS order_reason_id, augru AS reason_code, 'SAP_S4' AS source_system
FROM manufacturing_bronze.sap_sd.tvaut
UNION ALL
SELECT SHA2(CONCAT_WS('|','SALESFORCE', code), 256), code, 'SALESFORCE'
FROM manufacturing_bronze.salesforce_crm.loss_reason_ref
UNION ALL
SELECT SHA2(CONCAT_WS('|','RETURNS_PORTAL', reason_cd), 256), reason_cd, 'RETURNS_PORTAL'
FROM manufacturing_bronze.returns_portal.rma_reason_code;
```

> **Batch MVs only.** `UNION ALL` conforms sources inside a **materialized view**. For a **streaming
> table**, do NOT UNION — use one **Append Flow** (`CREATE FLOW … INSERT INTO … BY NAME`) per source
> into the shared target, which is the streaming-safe equivalent.

### `source_system`: model business column vs `_source_system` audit column

The vibe model frequently defines **`source_system`** as a *business* column (in the entity's column
list, comment like *"Originating system identifier"*). The dimensional templates also add
**`_source_system`** as an *audit* column. These are semantically identical, so emitting both is
redundant.

> **Rule:** when the vibe model already defines a `source_system` column, **map it directly and do
> NOT add a separate `_source_system` audit column** — the model's `source_system` IS the audit
> column. Add `_source_system` only when the model lacks a `source_system` column entirely.
>
> **The literal value** written into whichever column (`'SAP_S4'`, `'SALESFORCE'`, …) comes from
> `conventions.yml` `source_system_labels:` keyed by the logical bronze source — read it from there,
> do not derive it ad-hoc per entity.

### Deferred / known-empty entities

When an entity's source join legitimately produces **0 rows** because of a known data gap (not a
bug) — e.g. `delivery_schedule` from `veda` ⋈ `vbep` with no matches in this dataset — still author
the MV with the **full inline schema** (it validates the schema contract) and note the deferral in
the table COMMENT:

```sql
COMMENT '... [DEFERRED — {reason}]. Schema placeholder; will populate when {condition}.'
```

Include it in the pipeline, and mark it `DEFERRED` in the build manifest with the reason + resolution
condition (this is the SDP echo of the normalized-mode DEFERRED-table rule in `ddl-and-modeling.md`).
A declared-empty entity is the one exception to the silent-0-row exit gate — the row-count check
skips it **because** it is registered as deferred, not because 0 rows is ever silently acceptable.
