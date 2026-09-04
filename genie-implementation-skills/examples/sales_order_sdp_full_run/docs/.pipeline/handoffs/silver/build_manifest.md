# Build Manifest — Meridian Sales Order Silver SDP Pipeline

**Build Date:** 2026-07-28 
**Pipeline:** meridian_sales_order_silver_sdp 
**ETL Type:** sdp_pipeline (Lakeflow Spark Declarative Pipelines) 
**Output Model:** hybrid (normalized 3NF silver) 
**Silver Schema:** `manufacturing_silver_vibe.sales_order_silver_sdp` 
**Gold Schema:** `manufacturing_silver_vibe.sales_order_gold_sdp`

---

## 1. Entity Inventory

| # | Entity | Tier | SDP Object | Source(s) | Expected Rows | FK Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | sales_area | 0 | MV | sap_sd.tvta | 4 | N/A (root) |
| 2 | order_reason | 0 | MV | sap_sd.tvaut + salesforce_crm.loss_reason_ref | ~9 (deduped) | N/A (root) |
| 3 | channel_config | 1 | MV | sap_sd.zsd_channel_config | 4 | sales_area_id=NULL (source gap) |
| 4 | sales_contract | 1 | MV | sap_sd.veda | 120 | sales_area_id=NULL (source gap) |
| 5 | sales_contract_line | 2 | MV | sap_sd.veda_item | 373 | sales_contract_id 100% |
| 6 | quotation | 2 | MV | salesforce_crm.quote | 4,000 | N/A |
| 7 | order | 3 | MV | sap_sd.vbak + quote JOIN | 5,000 | sales_area 100%, quotation ~19.9% |
| 8 | quotation_line | 3 | MV | salesforce_crm.quote_line | 11,982 | quotation_id 100% (hash-identity) |
| 9 | order_line | 4 | MV | sap_sd.vbap | 14,762 | order_id 100% |
| 10 | order_partner | 4 | MV | sap_sd.vbpa | 15,000 | order_id 100% |
| 11 | order_schedule_line | 5 | MV | sap_sd.vbep | 22,212 | order_line_id 100% |
| 12 | delivery_schedule | 6 | MV | sap_sd.vbep (SA types) | 0 | order_line_id 100% (when rows exist) |
| 13 | edi_order_message | 6 | ST | edi_gateway.edi_message_log | 956 | order_id 100% |
| 14 | order_credit_check | 6 | ST | sap_sd.zcredit_log | 3,104 | order_id 100% |
| 15 | return_order | 6 | MV | returns_portal.rma_request | 227 | order_id 100%, order_reason_id=0% (vocab gap) |
| 16 | otd_record | 6 | MV | sap_sd.vbep | 22,212 | order_line_id 100%, schedule_line 100% |
| 17 | return_order_line | 7 | MV | returns_portal.rma_line | 329 | return_order_id 100% (hash-identity) |

---

## 2. Load Strategy

| Strategy | SDP Object | Count | Entities |
| --- | --- | --- | --- |
| FULL_MERGE | Materialized View | 15 | All except edi_order_message, order_credit_check |
| APPEND_ONLY | Streaming Table | 2 | edi_order_message (watermark: transmission_ts), order_credit_check (watermark: check_ts) |

**Rationale:** All entities < 5M rows. Bronze lacks explicit CDC/update timestamps. MVs full-recompute on each triggered update. Streaming tables for immutable event logs gain incremental efficiency.

---

## 3. Key Derivation

| Pattern | Formula | Type |
| --- | --- | --- |
| Single-column NK | `SHA2(TRIM(col), 256)` | STRING |
| Multi-column NK | `SHA2(CONCAT(TRIM(col1), '\|', TRIM(col2), ...), 256)` | STRING |
| Hash-identity FK | Same SHA2 formula as parent PK (both sides hash the same source value) | STRING |

---

## 4. DQ Strategy (Inline EXPECT)

| Check | Constraint Pattern | Enforcement |
| --- | --- | --- |
| PK grain | `EXPECT ({natural_key_parts} IS NOT NULL) ON VIOLATION DROP ROW` | Hard (drops nulls) |
| FK populated | `EXPECT ({fk_col} IS NOT NULL)` | Soft (tracked in event log) |
| Computed field | `credit_utilization_pct` inline, `OTD_Status` inline | N/A |

---

## 5. Bronze Source Map

| Logical Name | Catalog.Schema | Tables Used |
| --- | --- | --- |
| src_sap_sd | manufacturing_bronze_vibe.sap_sd | tvta, tvaut, zsd_channel_config, veda, veda_item, vbak, vbap, vbpa, vbep, zcredit_log |
| src_salesforce_crm | manufacturing_bronze_vibe.salesforce_crm | quote, quote_line, loss_reason_ref |
| src_edi_gateway | manufacturing_bronze_vibe.edi_gateway | edi_message_log |
| src_returns_portal | manufacturing_bronze_vibe.returns_portal | rma_request, rma_line |

---

## 6. Known Gaps & Accepted Constraints

| # | Entity | Gap | Severity | Disposition |
| --- | --- | --- | --- | --- |
| 1 | channel_config | sales_area_id = NULL (source lacks vkorg/spart) | WARN | Accepted |
| 2 | sales_contract | sales_area_id = NULL (veda lacks vkorg/spart) | WARN | Accepted |
| 3 | return_order | order_reason_id = NULL (portal vocab gap) | P1 | HG-SDP-4 ACCEPTED |
| 4 | return_order_line | order_reason_id = NULL (same vocab gap) | P1 | HG-SDP-4 ACCEPTED |
| 5 | otd_record | actual_delivery_date = NULL | P0 | Requires likp/lips ingestion |
| 6 | delivery_schedule | 0 rows (no SA document types in bronze) | Expected | Partial grade accepted |
| 7 | order | quotation_id ~19.9% (only converted quotes resolve) | Expected | Cross-source design |

---

## 7. DAB Bundle Structure

```
meridian/sales-order/sdp/hybrid/
├── conventions.yml
├── databricks.yml
├── resources/
│   └── meridian_sales_order_silver_sdp.pipeline.yml
├── src/
│   └── silver/
│       └── pipeline/
│           ├── sales_area.sql
│           ├── order_reason.sql
│           ├── channel_config.sql
│           ├── sales_contract.sql
│           ├── sales_contract_line.sql
│           ├── quotation.sql
│           ├── order.sql
│           ├── quotation_line.sql
│           ├── order_line.sql
│           ├── order_partner.sql
│           ├── order_schedule_line.sql
│           ├── delivery_schedule.sql
│           ├── edi_order_message.sql
│           ├── order_credit_check.sql
│           ├── return_order.sql
│           ├── otd_record.sql
│           └── return_order_line.sql
└── docs/
    ├── business_requirements.md
    ├── etl_detailed_spec.md
    ├── s2t_mapping_report.md
    ├── progress.md
    ├── etl_state.md
    └── build_manifest.md
```

---

## 8. Deployment & Next Steps

**Deploy command:**
```bash
cd /Workspace/Users/stuart.swartz@databricks.com/vibe-modeling-skills-testing/vibe-model-skills-testing/meridian/sales-order/sdp/hybrid
databricks bundle deploy -t dev
```

**Post-deploy:**
1. Trigger pipeline update (UI → Start, or `databricks pipelines start-update <pipeline_id>`)
2. Inspect event-log EXPECT pass-rates (PK grain, FK resolution)
3. Confirm DAG ordering (all T0→T7 dependencies resolved)
4. Run `domain-model-validation` skill for full scorecard

**Gold layer:** COMPLETE (2026-08-08) — 13 MVs deployed, pipeline COMPLETED successfully
**Gold validation:** COMPLETE (2026-08-09) — 13/13 Grade A; 70 checks (67 PASS + 3 accepted exceptions); 0 PK dups; 0% FK orphans; all integration-join-preservation PASS; quality gate PASS

---

## 9. Handoff to domain-model-validation

This manifest is the typed build→validate handoff. The validation skill reads:
- Entity inventory (section 1) for scope
- Expected row counts and FK resolution rates as baseline thresholds
- Known gaps (section 6) to distinguish expected failures from regressions
- DQ strategy (section 4) for event-log inspection targets

---

## 10. Gold Layer Build (2026-08-08)

### Entity Inventory (Gold — Dimensional Star)

| # | Entity | Tier | Object | Source (silver) | Rows | FK Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | dim_date | G0 | MV | Generated (SEQUENCE) | 730 | N/A (root) |
| 2 | dim_sales_area | G0 | MV | sales_area | 4 | N/A (passthrough) |
| 3 | dim_channel | G0 | MV | channel_config | 4 | N/A (passthrough) |
| 4 | dim_order_reason | G0 | MV | order_reason | 9 | N/A (passthrough) |
| 5 | dim_customer | G1 | MV | order_partner (AG) | 300 | N/A (root dedup) |
| 6 | dim_material | G1 | MV | order_line ∪ quotation_line | 800 | N/A (root union) |
| 7 | dim_sales_contract | G1 | MV | sales_contract | 120 | N/A (passthrough) |
| 8 | bridge_order_partner | G1 | MV | order_partner (pivot) | 5,000 | order_id 100% |
| 9 | fact_sales_order_line | G2 | MV | order_line + order + order_partner | 14,762 | Customer 100%, Material 100%, SalesArea 100% |
| 10 | fact_otd | G2 | MV | otd_record + order_line + order | 22,212 | Customer via order, Material via line |
| 11 | fact_quotation_line | G2 | MV | quotation_line + quotation | 11,982 | Customer via Account_Id, Material via SKU |
| 12 | fact_return_line | G2 | MV | return_order_line + return_order | 329 | Customer 100%, OrderReason=NULL (P1 gap) |
| 13 | fact_credit_check | G2 | MV | order_credit_check + order | 3,104 | Customer 100%, SalesArea via order |

### Design Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| FK handling | NULL (no -1 sentinel) | Consistent with silver 3NF convention (HG-GOLD-5) |
| Surrogate keys | SHA2(natural_key, 256) STRING | Same method as silver; identity passthrough where possible |
| All objects | Materialized View | All < 25K rows; fully recomputable from silver |
| Source references | Fully-qualified catalog.schema.table | SDP no-parameterization stance; no LIVE.* |
| dim_date range | 2024-07-01 to 2026-06-30 | Covers full order date range; fiscal Jul-Jun |
| dim_customer source | order_partner WHERE AG | Deduped by Partner_Number (latest order wins) |
| dim_material source | order_line UNION quotation_line | Covers both SAP and CRM product codes |
| bridge_order_partner | PIVOT (AG/WE/RE) per order | Enables Ship-To and Bill-To analysis without role-play |

### DQ Strategy (Inline EXPECT)

| Constraint Type | Pattern | Enforcement |
| --- | --- | --- |
| PK/grain not null | `EXPECT (PK IS NOT NULL) ON VIOLATION DROP ROW` | All 13 objects |
| FK resolved (soft) | `EXPECT (FK IS NOT NULL)` | Facts: track NULL FK rate in event log |
| Material resolved | `EXPECT (Material_Key IS NOT NULL)` | fact_sales_order_line, fact_otd |
| Customer resolved | `EXPECT (Customer_Key IS NOT NULL)` | All 5 facts |

### Pipeline Run Results

| Update ID | Status | Issues | Resolution |
| --- | --- | --- | --- |
| a17b8aa1 | FAILED | DAYOFWEEK_ISO unresolved; fact_return_line DECIMAL(16,2) mismatch | WEEKDAY()+1; CAST AS DECIMAL(15,2) |
| 93aea6b7 | COMPLETED | None | All 30 entities materialized (17 silver + 13 gold) |
