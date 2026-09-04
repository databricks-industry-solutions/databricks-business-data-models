# SDP Hybrid Gold Star (etl_type: sdp_pipeline, output_model: hybrid)

> Part of the `sdp_pipeline` template pack — the downstream dimensional star built from normalized
> silver. Overview: `sdp-pipeline-development.md`. Templates: `sdp-templates.md`.

## Hybrid mode: the downstream gold star layer (`output_model: hybrid`)

**This is the authoritative SDP recipe for `hybrid`.** In `hybrid`, the build produces TWO layers
**in sequence, in ONE pipeline** — normalized 3NF silver FIRST, THEN a dimensional Kimball gold
star built **downstream from that silver** (not from bronze, not both-at-once):

- **Silver layer** — build exactly as `normalized`: product-named MVs / ST-APPEND, natural PKs, no
  surrogates, hardcoded bronze paths. Lands in the **silver** schema. Nothing new here.
- **Gold layer** — one declarative object per star table, reading **the silver tables** (`LIVE`
  references to the silver objects in the same pipeline), adding the SHA2 `{Entity}_Key` surrogate,
  `dim_/fact_` naming, and Pascal_Snake business columns. Lands in the **gold** schema.

> **Gold discovery step — read the silver sources before authoring gold.** The gold requirements
> handoff is a **design** spec (grain, FK targets, source tables, column lists), not a **build** spec
> — it does not give you the exact silver column names, the SHA2 surrogate composition, or the join
> keys between silver tables. Before writing any gold source, **read every silver pipeline file the
> requirements reference** (the `.sql` under `src/silver/pipeline/`) to capture: exact physical column
> names + types, which column is each dim's natural key (to hash on), and the FK columns that join a
> fact to its dims. Budget a handful of reads up front; it is far cheaper than guessing a column name
> and failing the update. The silver sources are the implementation contract; the requirements doc is
> the intent. *(An upstream `domain-model-assessment` gold pass may supply a machine-readable gold S2T
> that pre-answers most of this — if present, use it and skip the manual reads.)*

**Same pipeline, two schemas.** A single LDP pipeline has ONE default `schema:`. Put the silver
sources under `src/silver/pipeline/` (unqualified names → default schema = silver) and the gold
sources under `src/gold/pipeline/` with **fully schema-qualified object names**
(`catalog.gold_schema.dim_customer`) so they land in the gold schema regardless of the pipeline
default. **Hardcode the gold `catalog.schema` literal** in each gold source, exactly as bronze paths
are hardcoded — do NOT use `${var}`/`:param` substitution (SDP avoids parameterization, and DAB does
not reliably substitute into plain `.sql` pipeline sources). Reference silver objects from gold by
their **fully-qualified `catalog.schema.object`** name, NOT bare `LIVE.<name>` (which resolves only
against the pipeline default schema — see the fact template note). Both folders are globbed into the
one `pipeline` resource (see the DAB block in `sdp-deployment.md`), so the silver→gold dependency graph resolves in
one update: a gold MV that selects from the silver `customer` object orders automatically after it.

**Gold dimension (MV over the silver product):**

```sql
-- src/gold/pipeline/dim_customer.sql   (plain .sql, NO notebook-source header)
-- gold catalog.schema is a HARDCODED literal (no ${var}/:param) -- from conventions gold_pattern
CREATE OR REFRESH MATERIALIZED VIEW meridian_silver.field_service_gold_sdp.dim_customer (
  Customer_Key   BIGINT  COMMENT 'Surrogate key (SHA2 of natural key)',
  Customer_Bk    STRING  COMMENT 'Natural/business key (silver customer_id)',
  Customer_Name  STRING,
  _source_system STRING,
  CONSTRAINT valid_bk EXPECT (Customer_Bk IS NOT NULL) ON VIOLATION DROP ROW  -- grain on NK, not surrogate
)
CLUSTER BY (Customer_Key)
COMMENT 'Conformed customer dimension (gold star, built from silver SSOT)'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',COALESCE(CAST(customer_id AS STRING),'~')),256),1,15),16,10) AS BIGINT) AS Customer_Key,
  customer_id    AS Customer_Bk,
  customer_name  AS Customer_Name,
  _source_system
FROM meridian_silver.field_service_silver_sdp.customer   -- SILVER object, fully-qualified (see refs note)
UNION ALL
-- -1 Unknown member: an MV is fully recomputed (no INSERT), so the seed MUST be a UNION ALL row
-- in the defining query -- this is what the fact's COALESCE(...,-1) points at.
SELECT CAST(-1 AS BIGINT), '__UNKNOWN__', 'Unknown', '__UNKNOWN__';
```

**Gold fact (MV over the silver fact, FK-resolved against the gold dims):**

```sql
-- src/gold/pipeline/fact_service_order.sql   (gold catalog.schema hardcoded, no ${var}/:param)
CREATE OR REFRESH MATERIALIZED VIEW meridian_silver.field_service_gold_sdp.fact_service_order (
  Service_Order_Key BIGINT,
  Service_Order_Bk  STRING,   -- degenerate NK, retained so the grain EXPECT has a real column
  Customer_Key      BIGINT,
  Asset_Key         BIGINT,
  _source_system    STRING,
  CONSTRAINT valid_grain EXPECT (Service_Order_Bk IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_customer_resolved EXPECT (Customer_Key != -1),   -- soft: track orphan-to-Unknown rate
  CONSTRAINT fk_asset_resolved    EXPECT (Asset_Key != -1)
)
CLUSTER BY (Customer_Key)
AS SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',COALESCE(CAST(s.service_order_id AS STRING),'~')),256),1,15),16,10) AS BIGINT) AS Service_Order_Key,
  s.service_order_id AS Service_Order_Bk,
  COALESCE(c.Customer_Key,-1) AS Customer_Key,   -- Rule 11: LEFT JOIN the gold dim, COALESCE miss to -1
  COALESCE(a.Asset_Key,-1)    AS Asset_Key,
  s._source_system
FROM meridian_silver.field_service_silver_sdp.service_order s   -- SILVER fact (fully-qualified)
LEFT JOIN meridian_silver.field_service_gold_sdp.dim_customer        c ON c.Customer_Bk = s.customer_id
LEFT JOIN meridian_silver.field_service_gold_sdp.dim_installed_asset a ON a.Asset_Bk   = s.asset_id;
```

> 🔴 **Cross-schema references must be fully qualified — do NOT use bare `LIVE.<name>`.** In a
> multi-schema pipeline the `LIVE.*` virtual schema resolves against the pipeline's **default**
> (silver) schema, so `LIVE.dim_customer` would fail to find a dim that actually lives in the gold
> schema (and `LIVE.*` is being deprecated in favor of direct references). Reference every silver and
> gold object by its full `catalog.schema.object` name.
>
> ⚠️ **EXIT GATE — verify DAG ordering on the first hybrid run (do not assume it).** The two-layer
> flow depends on SDP registering an **intra-pipeline dependency** from a gold MV's fully-qualified
> `FROM catalog.silver_schema.<object>` reference, so silver materializes before its gold consumer.
> This is expected on current LDP but is **NOT runtime-verified here.** On the first hybrid run you
> MUST confirm, from the pipeline graph / event log, that each gold object shows an upstream edge to
> its silver source (not an external-table read). **If ordering does NOT register** (gold fails
> "silver not found" on first update, or reads empty/stale silver), the fix is a documented fallback,
> not a silent failure: wrap the silver reference so SDP recognizes it as a pipeline dependency
> (`FROM STREAM catalog.silver_schema.<object>` for a streaming read, or the runtime's dependency-
> declaring form) while keeping it schema-qualified — then re-run and re-check the graph. Treat
> "DAG edges confirmed silver→gold" as a required checkpoint before the hybrid build is called done.

**Rules for the gold layer:**
- 🔴 **Gold reads SILVER, never bronze.** A gold object that re-reads `catalog.bronze_schema.*`
  instead of the fully-qualified `catalog.silver_schema.<object>` defeats the SSOT — flag it.
- **FK resolution is Rule 11:** `LEFT JOIN` the already-defined gold dim on the natural key and
  `COALESCE(dim.Key, -1)`. Never inline-recompute a parent's surrogate from the fact source.
- **Guard the grain on the natural/degenerate key**, never the SHA2 surrogate (it can't be NULL).
- **`scd_strategy: type_2`** is a gold-only concept — the SCD2 `AUTO CDC` template applies to the
  gold dim, and needs CDF on the **silver** source. (Out of scope for the `type_1` field_service
  fixture.)
- **Seed the `-1` Unknown member** in each gold dim exactly as the dimensional MERGE path does, so
  the fact's `COALESCE(...,-1)` points at a real row.
- **FK-resolution joins must be 1:1 on the dim side** (see the fan-out rule in the FK-resolution note
  in `sdp-templates.md`). Bridge tables are the sharp edge: a `bridge_*` at **header** grain LEFT JOINed to a fact at
  **line** grain fans out — join on the header key (e.g. `order_id`), never the line key, or the fact
  row count multiplies. Confirm grain with a PK-count check on the first run.
- **`dim_date` / calendar dims:** use the serverless-safe date functions from Rule B (`WEEKDAY()+1`
  for ISO weekday, not `DAYOFWEEK_ISO`). CAST computed date-part columns to their declared types
  (Rule A). These are the two things that most often fail a gold `dim_date` on the first run.
- **Pipeline resource naming.** When gold is added to a silver pipeline in `hybrid`, the one pipeline
  now contains both layers. Naming it `{domain}_silver_pipeline` is then misleading — prefer
  `{domain}_sdp_pipeline` (drop the `silver_` qualifier). Keeping the original name is functionally
  harmless, but rename it when you add gold so the resource reflects its contents.
