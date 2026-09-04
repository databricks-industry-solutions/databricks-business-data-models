# field_service — ETL Detailed Spec

> **Flow shown:** `conventions.field_service.sdp.normalized.yml` — `sdp_pipeline` / `normalized`
> (the default field_service demonstration flow). This is a hand-authored example populated with
> real metamodel values from `model_setup.sql` — it demonstrates the end-to-end comment-enrichment
> feature: `Metamodel description` → table/column `COMMENT`, `Glossary term` → `glossary_term` tag.
> The column mappings for `service_order` and `installed_asset` are shown in full; `customer`,
> `product`, and `technician` are abbreviated since they are simpler or deferred.

---

## Section 0 — Locations (READ vs WRITE — must be distinct)

| Role | `conventions.yml` key | Value | Notes |
| --- | --- | --- | --- |
| **Silver land target (WRITE)** | `catalogs.silver` + `schemas.silver_pattern` | `meridian_silver.field_service_silver_sdp_norm` | DDL CREATEs and pipeline materializes here |
| **Vibe model source (READ-ONLY)** | `vibe_model.catalog` / `vibe_model.schema` | `meridian_model.field_service_model` | `vibe_metamodel_*` tables + empty shells live here; build never writes here |
| Bronze sources | `bronze_sources` | `meridian_bronze.fieldlink`, `meridian_bronze.sap_sd` | Read-only ingested source schemas |

---

## Section 1 — Target Model

### Target shape
| Field | Value |
| --- | --- |
| **output_model** | `normalized` |
| **etl_type** | `sdp_pipeline` |
| **scd_strategy** | `type_1` (surrogate keys: `NONE`) |

### Entities
| Entity | Type | Target layer | Source table(s) | Load order tier |
| --- | --- | --- | --- | --- |
| `customer` | Master | silver | `meridian_bronze.sap_sd.kna1` | 0 |
| `product` | Master | silver | `meridian_bronze.fieldlink.installed_asset` (distinct SKU attrs) | 0 |
| `installed_asset` | Master | silver | `meridian_bronze.fieldlink.installed_asset` | 1 |
| `service_order` | Transactional | silver | `meridian_bronze.fieldlink.service_order` | 2 |
| `technician` | Master | — | **DEFERRED — no bronze source** | — |

### Grain (facts / streaming tables)
| Entity | Grain — one row per... | Append-only? |
| --- | --- | --- |
| `service_order` | `service_order_id` | yes (ST-APPEND) |

- **Metamodel description (→ table COMMENT):** `One row per dispatched field-service job on an installed asset. Grain: service_order_id. FKs to installed_asset and technician; customer and product are reached transitively through the asset.`

  *(Source: `vibe_metamodel_product` row for `service_order`, `examples/field_service/model_setup.sql` line 98–99)*

---

## Section 2 — Column Mappings

> `Metamodel description` sourced from `vibe_metamodel_attribute.description`; `Glossary term` from
> `business_glossary_term`. Both from `model_setup.sql` INSERT into `vibe_metamodel_attribute`
> (lines 125–154). A column with neither carries `—`. The build sources the DDL `COMMENT` + the
> `glossary_term` column tag from these two cells — see `etl-development-framework/naming-standards.md` §5.6.

### service_order

| Target column | Type | Nullable | Source table | Source column | Transform / cast | Metamodel description | Glossary term | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `service_order_id` | STRING | NO | `meridian_bronze.fieldlink.service_order` | `service_order_id` | none | `PK — natural key, FieldLink service_order_id` | `Service Order Number` | PK; value_regex `^SO[0-9]{8}$` |
| `asset_id` | STRING | YES | `meridian_bronze.fieldlink.service_order` | `asset_id` | none | `FK to installed_asset` | `Asset Number` | NULL until asset resolved |
| `technician_id` | STRING | YES | — | — | `CAST(NULL AS STRING)` | `FK to technician — NO clean bronze source (only a free-text name on service_order.technician). Gap.` | `Technician Id` | P1 gap; deferred |
| `order_type` | STRING | YES | `meridian_bronze.fieldlink.service_order` | `order_type` | none | `Type of field job` | `Service Order Type` | enum: preventive\|corrective\|inspection\|calibration |
| `opened_date` | DATE | YES | `meridian_bronze.fieldlink.service_order` | `opened_date` | `CAST(… AS DATE)` | `Date the job was opened` | `Service Order Opened Date` | |
| `status` | STRING | YES | `meridian_bronze.fieldlink.service_order` | `status` | none | `Lifecycle status` | `Service Order Status` | enum: open\|dispatched\|completed\|closed |
| `priority` | STRING | YES | `meridian_bronze.fieldlink.service_order` | `priority` | none | `Dispatch priority` | `Service Order Priority` | enum: low\|medium\|high\|critical |

### installed_asset

| Target column | Type | Nullable | Source table | Source column | Transform / cast | Metamodel description | Glossary term | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `asset_id` | STRING | NO | `meridian_bronze.fieldlink.installed_asset` | `asset_id` | none | `PK — natural key, FieldLink asset_id` | `Asset Number` | PK; value_regex `^AST[0-9]{8}$` |
| `serial_number` | STRING | YES | `meridian_bronze.fieldlink.installed_asset` | `serial_number` | none | `Unit serial number` | `Serial Number` | |
| `customer_id` | STRING | YES | `meridian_bronze.fieldlink.installed_asset` | `customer_kunnr` | `TRIM(customer_kunnr)` | `FK to customer (bronze installed_asset.customer_kunnr)` | `Customer Id` | cross-source join: FieldLink → SAP kna1.kunnr |
| `product_id` | STRING | YES | `meridian_bronze.fieldlink.installed_asset` | `sku_code` | none | `FK to product (bronze installed_asset.sku_code)` | `Product Id` | |
| `commissioning_status` | STRING | YES | `meridian_bronze.fieldlink.installed_asset` | `commissioning_status` | none | `First-install outcome` | `Commissioning Status` | enum: commissioned\|pending\|failed |
| `install_date` | DATE | YES | `meridian_bronze.fieldlink.installed_asset` | `install_date` | `CAST(… AS DATE)` | `Date the asset was installed` | `Install Date` | |
| `warranty_end_date` | DATE | YES | `meridian_bronze.fieldlink.installed_asset` | `warranty_end_date` | `CAST(… AS DATE)` | `Warranty expiry` | `Warranty End Date` | |
| `site_country` | STRING | YES | `meridian_bronze.fieldlink.installed_asset` | `site_country` | `UPPER(TRIM(site_country))` | `ISO-2 country of the install site` | `Site Country` | |

---

## Resulting DDL — comment-enrichment demonstration

The snippet below shows how the two spec columns flow into the built DDL, using the
**merge_notebook / plain Delta table** form where inline column COMMENTs and trailing
`ALTER TABLE … SET TAGS` statements are both valid. (In the SDP pipeline form, column COMMENTs
go inline in the streaming-table definition and `SET TAGS` are applied post-refresh by the
documentation enrich step — see `etl-development-framework/naming-standards.md` §5.6.)
- **Table `COMMENT`** = `vibe_metamodel_product.description` (Section 1 "Metamodel description")
- **Column `COMMENT`** = spec `Metamodel description` + a lineage note (source table/column) when
  material — per `etl-development-framework/naming-standards.md` §5.6
- **`ALTER … SET TAGS ('glossary_term' = …)`** — one statement per column whose spec
  `Glossary term` is not `—`

```sql
-- ─────────────────────────────────────────────────────────────────────────────
-- service_order  (merge_notebook / normalized — field_service example)
-- Note: the field_service pipeline uses sdp_pipeline, but the DDL below is shown
-- in merge_notebook / plain Delta form so that inline column COMMENTs and trailing
-- ALTER TABLE … SET TAGS statements are both valid.  In the actual SDP pipeline,
-- column COMMENTs go inline in the streaming-table definition and SET TAGS are
-- applied post-refresh by the documentation enrich step — see naming-standards.md §5.6.
-- ─────────────────────────────────────────────────────────────────────────────
-- Table COMMENT sourced from vibe_metamodel_product.description (model_setup.sql line 98-99)
CREATE TABLE IF NOT EXISTS service_order (
  service_order_id STRING NOT NULL
    COMMENT 'PK — natural key, FieldLink service_order_id. (Source: fieldlink.service_order.service_order_id)',
  asset_id         STRING
    COMMENT 'FK to installed_asset. (fieldlink.service_order.asset_id; NULL until asset resolved.)',
  technician_id    STRING
    COMMENT 'FK to technician — NO clean bronze source (only a free-text name on service_order.technician). Gap. (CAST(NULL AS STRING) — P1 gap, deferred.)',
  order_type       STRING
    COMMENT 'Type of field job. (fieldlink.service_order.order_type; enum: preventive|corrective|inspection|calibration)',
  opened_date      DATE
    COMMENT 'Date the job was opened. (fieldlink.service_order.opened_date)',
  status           STRING
    COMMENT 'Lifecycle status. (fieldlink.service_order.status; enum: open|dispatched|completed|closed)',
  priority         STRING
    COMMENT 'Dispatch priority. (fieldlink.service_order.priority; enum: low|medium|high|critical)',
  CONSTRAINT pk_service_order PRIMARY KEY (service_order_id)
)
USING DELTA
COMMENT 'One row per dispatched field-service job on an installed asset. Grain: service_order_id. FKs to installed_asset and technician; customer and product are reached transitively through the asset.';

-- Glossary tags — one per column where spec `Glossary term` is not `—`
-- Terms sourced from vibe_metamodel_attribute.business_glossary_term (model_setup.sql lines 127-133)
ALTER TABLE service_order ALTER COLUMN service_order_id SET TAGS ('glossary_term' = 'Service Order Number');
ALTER TABLE service_order ALTER COLUMN asset_id         SET TAGS ('glossary_term' = 'Asset Number');
ALTER TABLE service_order ALTER COLUMN technician_id    SET TAGS ('glossary_term' = 'Technician Id');
ALTER TABLE service_order ALTER COLUMN order_type       SET TAGS ('glossary_term' = 'Service Order Type');
ALTER TABLE service_order ALTER COLUMN opened_date      SET TAGS ('glossary_term' = 'Service Order Opened Date');
ALTER TABLE service_order ALTER COLUMN status           SET TAGS ('glossary_term' = 'Service Order Status');
ALTER TABLE service_order ALTER COLUMN priority         SET TAGS ('glossary_term' = 'Service Order Priority');
```

**Verification:** the two key glossary terms above match the metamodel source exactly —
`grep -nE "Service Order Number|Asset Number" examples/field_service/model_setup.sql` returns:

```
127:  ('service_order','service_order_id','STRING','Service Order Number', ...
128:  ('service_order','asset_id','STRING','Asset Number', ...
135:  ('installed_asset','asset_id','STRING','Asset Number', ...
216: ALTER TABLE installed_asset ALTER COLUMN asset_id         SET TAGS ('glossary_term' = 'Asset Number');
217: ALTER TABLE service_order   ALTER COLUMN service_order_id SET TAGS ('glossary_term' = 'Service Order Number');
```

No glossary term in this spec was invented — every term is read directly from `model_setup.sql`.

---

## Section 3 — Keys & Constraints

| Entity | Natural key (source expression) | Surrogate key | PK | FK references | Recency column |
| --- | --- | --- | --- | --- | --- |
| `customer` | `TRIM(kunnr)` | NONE | `customer_id` | — | `— ` |
| `product` | `TRIM(sku_code)` | NONE | `product_id` | — | `—` |
| `installed_asset` | `TRIM(asset_id)` | NONE | `asset_id` | `customer_id → customer`, `product_id → product` | `—` |
| `service_order` | `TRIM(service_order_id)` | NONE | `service_order_id` | `asset_id → installed_asset` | `opened_date` |

---

## Section 5 — Load Strategy

| Entity | Mutable? | Chosen strategy (SDP) | Rationale |
| --- | --- | --- | --- |
| `customer` | yes | `MV` (MATERIALIZED VIEW) | Small (~300 rows), fully recomputable |
| `product` | yes | `MV` | Small (~40 rows), fully recomputable |
| `installed_asset` | yes | `MV` | ~3,698 rows, fully recomputable |
| `service_order` | append-only ledger | `ST-APPEND` (STREAMING TABLE) | Transaction grain; rows never change after dispatch |
| `technician` | — | DEFERRED | No bronze source; shell table omitted from build |

---

## Section 7 — Conventions (from `conventions.field_service.sdp.normalized.yml`)

```yaml
etl_language:          sql
surrogate_key_method:  NONE
naming:
  table_case:            lower_snake
  dim_prefix:            ""
  fact_prefix:           ""
  bridge_prefix:         ""
  gold_prefix:           ""
  entity_form:           singular
  business_column_case:  follow_model
  metadata_column_case:  _lower_snake
  surrogate_key_suffix:  ""
  fk_naming:             same_as_parent_pk
silver_catalog:        meridian_silver
silver_schema:         field_service_silver_sdp_norm
vibe_model_catalog:    meridian_model
vibe_model_schema:     field_service_model
bronze_schemas:
  src_fieldlink: meridian_bronze.fieldlink
  src_sap_sd:    meridian_bronze.sap_sd
```
