# Sales Order Vibe V2 — Source-to-Target Mapping Report (SDP Pipeline)

**Customer:** Meridian Manufacturing 
**Domain:** sales_order 
**Output Model:** hybrid (normalized 3NF silver → dimensional gold star) 
**ETL Type:** sdp_pipeline (Lakeflow Spark Declarative Pipelines) 
**Metamodel:** `manufacturing_ecm_v1._metamodel` (V2, sales_order scope, bare-named tables) 
**Vibe Model (READ-ONLY):** `manufacturing_ecm_v1.sales_order` 
**Silver Target Schema:** `manufacturing_silver_vibe.sales_order_silver_sdp` 
**Gold Target Schema:** `manufacturing_silver_vibe.sales_order_gold_sdp` 
**Assessment Date:** 2026-07-28 
**Assessor:** Genie Code (domain-model-assessment skill)

---

## Executive Summary

| Metric | Value |
| --- | --- |
| Total V2 entities | 27 |
| Real entities (excl. degenerate) | 26 |
| Degenerate (excluded) | 1 (`sales_order_master_record`) |
| **Full** (buildable, <10% gaps) | **15** |
| **Partial** (buildable with known data gaps) | **2** |
| **Blocked** (primary source missing) | **9** |
| Phase 1 build scope | 17 entities (15 Full + 2 Partial) |
| Bronze sources confirmed | 5 schemas, 32 tables |
| Existing V1 model | 16 tables, 0 rows (unpopulated shell) |
| Existing merge-notebook build | 17 entities populated (proven mappings) |

---

## Model Completeness Assessment (Phase 2C)

### Unmapped Significant Tables

| Bronze Table | Rows | Purpose | Category | Disposition |
| --- | --- | --- | --- | --- |
| salesforce_crm.opportunity | 3,500 | Sales pipeline/funnel (pre-quote stage) | Candidate new entity | DEFERRED — pre-quote CRM stage; not in scope for order management domain |
| sap_sd.mara / makt | 400 | Material master + descriptions | Cross-domain: product_catalog | Out of scope |
| sap_sd.t001w | 4 | Plant master | Cross-domain: manufacturing | Out of scope |
| sap_sd.t052u / tinct | 4–5 | Payment terms / Incoterms text | Subordinate detail | Used as enrichment source |
| sap_sd.knvv | 300 | Customer-sales-area credit data | Source enrichment | Used as enrichment for channel/credit |
| edi_gateway.trading_partner | 34 | EDI partner registry | Subordinate detail | Enriches edi_order_message |
| returns_portal.rma_reason_code | 6 | Return reason reference | Subordinate detail | Enriches order_reason |
| fieldlink.* (4 tables) | 1,479–3,698 | Field service domain | Cross-domain: field_service | Out of scope |

### Business Process Coverage

| Business Process | V2 Entity Coverage | Status |
| --- | --- | --- |
| Quote-to-Order | quotation, quotation_line, order, order_line | Covered |
| Order Fulfillment | order_schedule_line, delivery_schedule, otd_record | Covered (partial: OTD lacks actuals) |
| Pricing & Conditions | order_header_condition, order_line_condition, channel_config | Blocked (PRCD_ELEMENTS) |
| Returns & RMA | return_order, return_order_line | Covered |
| Credit Management | order_credit_check | Covered |
| EDI Processing | edi_order_message | Covered |
| Contract Management | sales_contract, sales_contract_line | Covered |
| Order Lifecycle Events | order_status_event, order_change, order_block | Blocked (cdhdr/cdpos) |
| Sales Pipeline/Funnel | (none — opportunity deferred) | Gap (DEFERRED) |

---

## Model Assertion Validation (Step 2.7)

| # | Entity | Assertion | Model Declares | Data Shows | Contradiction? |
| --- | --- | --- | --- | --- | --- |
| 1 | All 9 entities tested | Grain (a) | Declared PKs | 0 excess rows — PK unique at source | No |
| 2 | order (vbak) | Type (b) | Transactional | Mutable lifecycle (6 statuses, no update ts) | Minor — SAP orders ARE transactional documents but mutable. Model correct. |
| 3 | zcredit_log | Type (b) | Transactional | Append-only (1:1 per order, no mutation) | No contradiction — event log |
| 4 | return_order | FK (d) | FK to order_reason | 0% resolution (vocab gap) | Yes — P1 gap |
| 5 | All intra-domain FKs | FK (d) | 1:many resolution | 100% resolved (order→sales_area, order_line→order, etc.) | No |

**No structural contradictions found.** The one FK assertion failure (return_order→order_reason) is a known vocabulary gap (returns portal uses DMG/WRONG/WARR vs SAP numeric 100/900/950 codes), not a grain or type error.

---

## Source-to-Target Mapping — Tier Summary

### Tier 0 (Roots — no intra-domain FK dependencies)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| sales_area | Reference | sap_sd.tvta | 4 | Full | Materialized View |
| order_reason | Reference | sap_sd.tvaut + salesforce_crm.loss_reason_ref | 8+4=12 (deduped→9) | Full | Materialized View |

### Tier 1 (depends on T0)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| channel_config | Reference | sap_sd.zsd_channel_config | 4 | Full | Materialized View |
| sales_contract | Master | sap_sd.veda | 120 | Full | Materialized View |

### Tier 2 (depends on T0/T1)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| sales_contract_line | Master | sap_sd.veda_item | 373 | Full | Materialized View |
| quotation | Transactional | salesforce_crm.quote | 4,000 | Full | Materialized View |

### Tier 3 (depends on T0–T2)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| order | Transactional | sap_sd.vbak | 5,000 | Full | Materialized View |
| quotation_line | Transactional | salesforce_crm.quote_line | 11,982 | Full | Materialized View |

### Tier 4 (depends on T3)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| order_line | Transactional | sap_sd.vbap | 14,762 | Full | Materialized View |
| order_partner | Transactional | sap_sd.vbpa | 15,000 | Full | Materialized View |

### Tier 5 (depends on T4)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| order_schedule_line | Transactional | sap_sd.vbep | 22,212 | Full | Materialized View |

### Tier 6 (depends on T3–T5)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| delivery_schedule | Master | sap_sd.vbep (scheduling EDI types) | 0 (expected) | Partial | Materialized View |
| edi_order_message | Transactional | edi_gateway.edi_message_log | 956 | Full | Streaming Table (append-only) |
| order_credit_check | Transactional | sap_sd.zcredit_log | 3,104 | Full | Streaming Table (append-only) |
| return_order | Transactional | returns_portal.rma_request | 227 | Full | Materialized View |
| otd_record | Transactional | sap_sd.vbep | 22,212 | Partial | Materialized View |

### Tier 7 (depends on T6)

| Entity | Type | Source(s) | Rows | Fit Grade | SDP Strategy |
| --- | --- | --- | --- | --- | --- |
| return_order_line | Transactional | returns_portal.rma_line | 329 | Full | Materialized View |

### Blocked (no primary source available)

| Entity | Type | Missing Source | Block Reason | Priority |
| --- | --- | --- | --- | --- |
| order_header_condition | Transactional | PRCD_ELEMENTS | Pricing conditions table not ingested | P0 |
| order_line_condition | Transactional | PRCD_ELEMENTS | Pricing conditions table not ingested | P0 |
| order_status_event | Transactional | cdhdr/cdpos | Change document tables not ingested | P0 |
| order_change | Transactional | cdhdr/cdpos | Change document tables not ingested | P0 |
| order_block | Transactional | cdhdr/cdpos | Change document tables not ingested | P0 |
| order_text | Transactional | stxh/stxl | SAPscript text tables not ingested | P1 |
| order_configuration | Transactional | CUOBJ/config tables | Variant configuration tables not ingested | P2 |
| order_fulfillment_block | Transactional | Export control tables | Compliance/sanctions tables not ingested | P2 |
| atp_check | Transactional | ATPLOG / ATP result tables | ATP logging tables not ingested | P2 |

---

## SDP Load Strategy Rationale

For the SDP pipeline variant, entities map to two SDP object types:

| Pattern | SDP Object | When to Use |
| --- | --- | --- |
| FULL_MERGE / INCREMENTAL_MERGE | **Materialized View** | Mutable entities or entities requiring dedup/transform logic; full refresh on each pipeline update |
| APPEND_ONLY | **Streaming Table** | Immutable event/log entities; append-only ingestion with watermark |

**Why Materialized View for most entities:** All entities are < 5M rows and the bronze extract lacks explicit update timestamps (no CDC). Materialized Views perform a full recompute on each pipeline update, which is safe and simple for this volume. SDP will handle dependency ordering automatically via the DAG.

**Why Streaming Table for credit_log and edi_message_log:** These are append-only event streams with no mutation. A Streaming Table reads new rows incrementally (via Auto Loader or Delta streaming source), making them more efficient for ongoing ingestion.

---

## Key Derivation (Hybrid Model)

Per `conventions.yml` (`output_model: hybrid`):
- **Silver layer** (3NF, `sales_order_silver_sdp`): Natural PKs from model (`{entity}_id`), generated as `SHA2(CONCAT(natural_key_parts), 256)` surrogate + natural key columns retained.
- **Gold layer** (dimensional, `sales_order_gold_sdp`): `dim_`/`fact_` prefixed tables with same SHA2 surrogates, conformed dimensions.

| Entity | Natural Key (Bronze) | Surrogate PK | Method |
| --- | --- | --- | --- |
| sales_area | vkorg + vtweg + spart | sales_area_id | SHA2 |
| order_reason | source_system + reason_code | order_reason_id | SHA2 |
| channel_config | vtweg | channel_config_id | SHA2 |
| sales_contract | vbeln | sales_contract_id | SHA2 |
| sales_contract_line | vbeln + posnr | sales_contract_line_id | SHA2 |
| quotation | quote_id (CRM UUID) | quotation_id | SHA2 |
| quotation_line | quote_line_id (CRM UUID) | quotation_line_id | SHA2 |
| order | vbeln | order_id | SHA2 |
| order_line | vbeln + posnr | order_line_id | SHA2 |
| order_partner | vbeln + parvw | order_partner_id | SHA2 |
| order_schedule_line | vbeln + posnr + etenr | order_schedule_line_id | SHA2 |
| edi_order_message | message_id | edi_order_message_id | SHA2 |
| order_credit_check | vbeln + check_ts | order_credit_check_id | SHA2 |
| return_order | rma_number | return_order_id | SHA2 |
| return_order_line | rma_line_id | return_order_line_id | SHA2 |
| delivery_schedule | vbeln + posnr + etenr (sched types) | delivery_schedule_id | SHA2 |
| otd_record | vbeln + posnr + etenr | otd_record_id | SHA2 |

---

## Bronze Data Type Summary

| Source System | Schema | Data Types | Date Format | Cast Pattern |
| --- | --- | --- | --- | --- |
| SAP S/4HANA SD | sap_sd | ALL STRING | yyyyMMdd | `TRY_TO_DATE(col, 'yyyyMMdd')` |
| Salesforce CRM | salesforce_crm | ALL STRING | yyyy-MM-dd | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |
| EDI Gateway | edi_gateway | ALL STRING | yyyy-MM-dd | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |
| Returns Portal | returns_portal | ALL STRING | yyyy-MM-dd | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |
| FieldLink | fieldlink | ALL STRING | yyyy-MM-dd | (cross-domain, not in scope) |

---

## Gap & Enhancement Registry

| # | Priority | Entity | Gap Description | Unblock Action | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | P0 | order_header_condition | No PRCD_ELEMENTS in bronze | Ingest sap_sd.prcd_elements | OPEN |
| 2 | P0 | order_line_condition | No PRCD_ELEMENTS in bronze | Ingest sap_sd.prcd_elements | OPEN |
| 3 | P0 | order_status_event | No cdhdr/cdpos in bronze | Ingest sap_sd.cdhdr + cdpos | OPEN |
| 4 | P0 | order_change | No cdhdr/cdpos in bronze | Ingest sap_sd.cdhdr + cdpos | OPEN |
| 5 | P0 | order_block | No cdhdr/cdpos in bronze | Ingest sap_sd.cdhdr + cdpos | OPEN |
| 6 | P0 | otd_record | actual_delivery_date NULL | Ingest sap_sd.likp + lips (delivery docs) | OPEN |
| 7 | P1 | order_text | No stxh/stxl in bronze | Ingest SAPscript text tables | OPEN |
| 8 | P1 | return_order / return_order_line | order_reason_id = 0% (vocab gap) | Map portal codes to SAP reason codes | OPEN |
| 9 | P2 | order_configuration | No config tables in bronze | Ingest CUOBJ / variant tables | OPEN |
| 10 | P2 | order_fulfillment_block | No compliance tables in bronze | Ingest export control tables | OPEN |
| 11 | P2 | atp_check | No ATPLOG in bronze | Ingest ATP result tables | OPEN |
| 12 | P3 | (enhancement) opportunity | Pre-quote pipeline not modeled | Model addition (sales_pipeline entity) | DEFERRED |

---

## Existing Model Integration Assessment (Phase 3)

### V1 Model (`manufacturing_mvm_v1.sales_order`)
- 16 tables, ALL 0 rows — unpopulated shell
- **Integration Option C: Ignore** — no data to fold in; V2 supersedes entirely

### Existing Merge-Notebook Build (`serverless_ss_dev_catalog.sales_order`)
- 17 entities fully populated and validated (Grade B+ overall)
- **Integration Option B: Use as source-mapping proof** — confirmed all source mappings, FK resolution rates, and transformation patterns. The SDP build reuses the same proven logic, expressed as streaming tables/materialized views instead of MERGE notebooks.

### Gold Models
- No sales_order gold model exists in `manufacturing_silver_vibe`
- Step 3.8 KPI Coverage: N/A (no existing gold to assess)

---

## Domain Readiness Summary

| Criterion | Status |
| --- | --- |
| All buildable entities have confirmed sources | PASS (17/17) |
| Natural keys identified for all entities | PASS |
| SHA2 formulas defined | PASS |
| Load order (tier) determined from FK graph | PASS (T0→T7) |
| SDP strategy assigned per entity | PASS |
| Blocked entities documented with unblock actions | PASS (9 blocked, P0–P2) |
| Model assertions validated | PASS (no contradictions) |
| Model completeness assessed | PASS (1 deferred enhancement) |
| Date formats profiled per source | PASS |
| Existing model integration decided | PASS |

**Recommendation:** Proceed to ETL build for Phase 1 scope (17 entities) using Lakeflow Spark Declarative Pipelines. The 9 blocked entities require bronze ingestion work before they can be built.

---

## Human Gate Decisions Required

1. **HG-SDP-1: Opportunity entity** — The `salesforce_crm.opportunity` table (3,500 rows) represents pre-quote sales pipeline tracking. Should it be:
   - (a) DEFERRED (recommended — belongs to a future CRM/pipeline domain extension)
   - (b) Added as a new entity via vibe-model prompt

2. **HG-SDP-2: 9 Blocked entities** — No bronze source available. Should they be:
   - (a) DEFERRED until ingestion asks are fulfilled (recommended)
   - (b) Partially built with stub/empty streaming tables

3. **HG-SDP-3: `sales_order_master_record` (degenerate)** — Single-column placeholder, null description. Should it be:
   - (a) EXCLUDED from build scope (recommended)
   - (b) Retained as a future placeholder

4. **HG-SDP-4: Returns portal vocab gap** — `return_order.order_reason_id` resolves 0% due to code mismatch (DMG/WRONG/WARR vs SAP 900/950/960). Should it be:
   - (a) ACCEPTED — load with NULL order_reason_id, document as P1 gap (recommended)
   - (b) Build a code-mapping table (requires business SME input)
