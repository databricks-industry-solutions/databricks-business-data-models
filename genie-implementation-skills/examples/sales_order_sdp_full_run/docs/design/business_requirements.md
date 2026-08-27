# Business Requirements — Meridian Sales Order Silver (SDP Pipeline)

## 1. Business Context

**Customer:** Meridian Manufacturing 
**Domain:** Sales Order Management 
**Industry:** Industrial Manufacturing (automation systems, electrification, smart infrastructure) 
**ETL Pattern:** Lakeflow Spark Declarative Pipelines (SDP) 
**Output Model:** Hybrid (normalized 3NF silver → dimensional gold star downstream)

Meridian operates a multi-channel B2B sales operation spanning direct OE (Original Equipment), distributor, dealer, e-commerce, and intercompany channels. The sales order domain manages the complete quote-to-cash lifecycle from quotation through order entry, fulfillment scheduling, credit management, returns processing, and on-time delivery tracking.

## 2. Source Systems of Record

| System | Role | Bronze Schema | Key Tables |
| --- | --- | --- | --- |
| SAP S/4HANA SD | ERP of record — orders, scheduling, contracts, credit | manufacturing_bronze_vibe.sap_sd | vbak, vbap, vbep, vbpa, veda, veda_item, zcredit_log, tvta, tvaut, zsd_channel_config |
| Salesforce CRM | Quotation & opportunity management | manufacturing_bronze_vibe.salesforce_crm | quote, quote_line, account, loss_reason_ref |
| EDI Gateway | Electronic order messaging | manufacturing_bronze_vibe.edi_gateway | edi_message_log, trading_partner |
| Returns Portal | RMA / return order management | manufacturing_bronze_vibe.returns_portal | rma_request, rma_line, rma_reason_code |

## 3. Target Schema

- **Silver (3NF):** `manufacturing_silver_vibe.sales_order_silver_sdp`
- **Gold (dimensional):** `manufacturing_silver_vibe.sales_order_gold_sdp` (future downstream)
- **SCD Strategy:** Type 1 (overwrite)
- **Surrogate Keys:** SHA2(natural_key_parts) → `{entity}_id`

## 4. Entity Scope (Phase 1 — 17 Entities)

### Tier 0 — Reference Masters (no dependencies)
1. **sales_area** — Sales organization structure (org + channel + division)
2. **order_reason** — Standardized reason/rejection code reference (UNION SAP + CRM)

### Tier 1 — Reference/Master (depends on T0)
3. **channel_config** — Channel business rules, pricing procedures, credit requirements
4. **sales_contract** — Framework agreements with customers

### Tier 2 — Contract Details + Quotations (depends on T0/T1)
5. **sales_contract_line** — Material-level contract commitments
6. **quotation** — Formal price/availability proposals to customers

### Tier 3 — Orders + Quote Lines (depends on T0–T2)
7. **order** — Core confirmed sales order headers
8. **quotation_line** — Line-item detail within quotations

### Tier 4 — Order Details (depends on T3)
9. **order_line** — Product-level line items within orders
10. **order_partner** — Partner function assignments (sold-to, ship-to, bill-to, payer)

### Tier 5 — Schedule Lines (depends on T4)
11. **order_schedule_line** — Confirmed delivery dates and quantities per line item

### Tier 6 — Events + Returns (depends on T3–T5)
12. **delivery_schedule** — Scheduling agreement cadence records (EDI schedule types)
13. **edi_order_message** — Inbound/outbound electronic order transactions
14. **order_credit_check** — Credit limit check results per order
15. **return_order** — RMA headers from returns portal
16. **otd_record** — On-time delivery tracking per schedule line

### Tier 7 — Return Details (depends on T6)
17. **return_order_line** — Line-item detail within return orders

## 5. Load Strategy (SDP-Specific)

| Strategy | SDP Object | Entities | Rationale |
| --- | --- | --- | --- |
| FULL_MERGE | Materialized View | 15 entities (all except edi + credit) | All < 5M rows; no CDC/watermark; MV full-recomputes the transform on each pipeline update |
| APPEND_ONLY | Streaming Table | edi_order_message, order_credit_check | Immutable event logs; append-only ingestion |

## 6. Key Business Rules

- **Multi-source dedup:** order_reason UNIONs SAP tvaut + CRM loss_reason_ref; tiebreaker = ORDER BY source_system DESC (SAP wins over CRM alphabetically)
- **Cross-source FK:** order.quotation_id resolves via quote.converted_order_number matching vbak.vbeln (~19.9% of orders have a quotation reference)
- **Channel discriminator:** order.channel_type derived from vtweg (distribution channel code)
- **OTD proxy:** otd_record uses schedule line dates as proxy; actual_delivery_date = NULL (P0 gap, requires likp/lips)
- **Returns vocab gap:** return_order.order_reason_id = NULL (portal codes DMG/WRONG/WARR don't match SAP numeric codes) — accepted P1 gap
- **Credit utilization:** order_credit_check.credit_utilization_pct computed inline as (exp_after / klimk * 100)

## 7. Data Quality Requirements

- 0 PK duplicates across all entities (validated)
- 100% intra-domain FK resolution for core relationships
- All date columns properly cast from STRING (SAP: yyyyMMdd; CRM/EDI/Portal: yyyy-MM-dd)
- Audit columns on every table: `_source_system`, `_loaded_at`, `_created_by`, `_modified_by`, `_source_updated_at`

## 8. Known Gaps & Constraints

- **P0:** PRCD_ELEMENTS not ingested (blocks pricing conditions)
- **P0:** cdhdr/cdpos not ingested (blocks order lifecycle events)
- **P0:** likp/lips not ingested (blocks true OTD actuals)
- **P1:** Returns portal reason codes not mapped to SAP vocabulary
- **delivery_schedule:** 0 rows expected (no EDI scheduling messages in current bronze)

## 9. Human Gate Decisions (Confirmed)

| ID | Decision | Disposition |
| --- | --- | --- |
| HG-SDP-1 | Opportunity entity | DEFERRED (CRM pipeline, out of scope) |
| HG-SDP-2 | 9 Blocked entities | DEFERRED until bronze ingestion |
| HG-SDP-3 | sales_order_master_record (degenerate) | EXCLUDED |
| HG-SDP-4 | Returns vocab gap | ACCEPTED (NULL order_reason_id, P1) |
