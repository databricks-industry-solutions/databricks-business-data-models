# ETL Detailed Specification — Meridian Sales Order Silver (SDP Pipeline)

## 1. Pipeline Architecture

**Pipeline Type:** Lakeflow Spark Declarative Pipeline (SDP) 
**Language:** SQL 
**Target Catalog:** manufacturing_silver_vibe 
**Silver Schema:** sales_order_silver_sdp 
**Gold Schema:** sales_order_gold_sdp (downstream, Phase 2) 
**SCD:** Type 1 (overwrite on key match) 
**Refresh Mode:** TRIGGERED (scheduled daily 06:00 UTC)

### Pipeline DAG Structure

The pipeline defines 17 objects in tier order. SDP resolves dependencies automatically from table references in SQL definitions.

```
T0: sales_area (MV), order_reason (MV)
 │
T1: channel_config (MV), sales_contract (MV)
 │
T2: sales_contract_line (MV), quotation (MV)
 │
T3: order (MV), quotation_line (MV)
 │
T4: order_line (MV), order_partner (MV)
 │
T5: order_schedule_line (MV)
 │
T6: delivery_schedule (MV), edi_order_message (ST), order_credit_check (ST),
    return_order (MV), otd_record (MV)
 │
T7: return_order_line (MV)
```

MV = Materialized View | ST = Streaming Table

## 2. Naming Conventions

| Element | Convention | Example |
| --- | --- | --- |
| Table names | lower_snake, no prefix (silver 3NF) | `sales_area`, `order_line` |
| Business columns | Pascal_Snake | `Sales_Organization`, `Order_Number` |
| Metadata columns | _lower_snake (underscore prefix) | `_source_system`, `_loaded_at` |
| Surrogate PK | {entity}_id (SHA2) | `order_id`, `sales_area_id` |
| FK columns | same as parent PK name | `order_id` (on order_line) |

## 3. Audit Columns (all tables)

```sql
_source_system      STRING      -- Source system enum: SAP_S4, SALESFORCE, EDI, RETURNS_PORTAL
_loaded_at          TIMESTAMP   -- Pipeline execution timestamp (current_timestamp())
_created_by         STRING      -- Pipeline identity
_modified_by        STRING      -- Pipeline identity  
_source_updated_at  TIMESTAMP   -- Best-available source timestamp (creation date if no update ts)
```

## 4. Entity Specifications

### 4.1 sales_area (T0, Materialized View)

**Intent:** Sales organization structure defining org + channel + division combinations. 
**Source:** `manufacturing_bronze_vibe.sap_sd.tvta` (4 rows) 
**Natural Key:** vkorg + vtweg + spart 
**Surrogate PK:** `sales_area_id = SHA2(CONCAT(vkorg, '|', vtweg, '|', spart), 256)`

| Target Column | Source Column | Transform |
| --- | --- | --- |
| sales_area_id | (computed) | SHA2(CONCAT(vkorg,'\|',vtweg,'\|',spart), 256) |
| Sales_Organization | vkorg | TRIM |
| Distribution_Channel | vtweg | TRIM |
| Division | spart | TRIM |
| Currency_Code | waers | UPPER(TRIM) |
| Pricing_Procedure | kalks | TRIM |
| Sales_Area_Description | bezei | TRIM |

### 4.2 order_reason (T0, Materialized View)

**Intent:** Standardized reason/rejection code reference (UNION SAP + CRM sources). 
**Sources:** `sap_sd.tvaut` (8 rows) + `salesforce_crm.loss_reason_ref` (4 rows) 
**Natural Key:** source_system + reason_code 
**Surrogate PK:** `order_reason_id = SHA2(CONCAT(source_system, '|', reason_code), 256)` 
**Dedup:** UNION with ROW_NUMBER tiebreaker ORDER BY source_system DESC (SAP_S4 wins)

| Target Column | Source Column | Transform |
| --- | --- | --- |
| order_reason_id | (computed) | SHA2(CONCAT(source_system,'\|',reason_code), 256) |
| Reason_Code | augru / loss_reason_code | TRIM |
| Reason_Description | bezei / reason_name | TRIM |
| Reason_Category | category | TRIM |
| Source_System | (literal) | 'SAP_S4' or 'SALESFORCE' |

### 4.3 channel_config (T1, Materialized View)

**Intent:** Channel business rules and policies per distribution channel. 
**Source:** `sap_sd.zsd_channel_config` (4 rows) 
**Natural Key:** vtweg 
**Surrogate PK:** `channel_config_id = SHA2(vtweg, 256)`

| Target Column | Source Column | Transform |
| --- | --- | --- |
| channel_config_id | (computed) | SHA2(vtweg, 256) |
| Distribution_Channel | vtweg | TRIM |
| Channel_Name | chan_name | TRIM |
| Credit_Check_Required | credit_check_req | CAST to BOOLEAN |
| EDI_Capable | edi_capable | CAST to BOOLEAN |
| Minimum_Order_Value | min_order_val | CAST to DECIMAL(15,2) |
| Pricing_Procedure | pricing_proc | TRIM |
| Payment_Terms | pay_terms | TRIM |
| Incoterms | inco | TRIM |
| sales_area_id | (FK lookup) | SHA2(CONCAT(vkorg,'\|',vtweg,'\|',spart), 256) — NOTE: zsd_channel_config lacks vkorg/spart; FK may be NULL |

### 4.4 sales_contract (T1, Materialized View)

**Intent:** Framework/blanket purchase agreements with customers. 
**Source:** `sap_sd.veda` (120 rows) 
**Natural Key:** vbeln 
**Surrogate PK:** `sales_contract_id = SHA2(vbeln, 256)`

| Target Column | Source Column | Transform |
| --- | --- | --- |
| sales_contract_id | (computed) | SHA2(vbeln, 256) |
| Contract_Number | vbeln | TRIM |
| Customer_Number | kunnr | TRIM |
| Distribution_Channel | vtweg | TRIM |
| Contract_Type | kbtyp | TRIM |
| Valid_From | vbegdat | TRY_TO_DATE(col, 'yyyyMMdd') |
| Valid_To | venddat | TRY_TO_DATE(col, 'yyyyMMdd') |
| Target_Quantity | zmeng | CAST to DECIMAL(15,3) |
| Target_Value | target_val | CAST to DECIMAL(15,2) |
| Contract_Status | vstat | TRIM |
| sales_area_id | (FK) | SHA2(CONCAT(vkorg,'\|',vtweg,'\|',spart), 256) — vkorg/spart from vbak join or NULL |

### 4.5 sales_contract_line (T2, Materialized View)

**Intent:** Material-level commitments within contracts. 
**Source:** `sap_sd.veda_item` (373 rows) 
**Natural Key:** vbeln + posnr 
**Surrogate PK:** `sales_contract_line_id = SHA2(CONCAT(vbeln, '|', posnr), 256)`

### 4.6 quotation (T2, Materialized View)

**Intent:** Formal sales quotation from CRM. 
**Source:** `salesforce_crm.quote` (4,000 rows) 
**Natural Key:** quote_id (CRM UUID) 
**Surrogate PK:** `quotation_id = SHA2(quote_id, 256)`

### 4.7 order (T3, Materialized View)

**Intent:** Core confirmed B2B sales order headers. 
**Source:** `sap_sd.vbak` (5,000 rows) 
**Natural Key:** vbeln 
**Surrogate PK:** `order_id = SHA2(vbeln, 256)` 
**FK:** sales_area_id, order_reason_id, quotation_id (19.9% via quote.converted_order_number)

### 4.8 quotation_line (T3, Materialized View)

**Intent:** Line-item detail within quotations. 
**Source:** `salesforce_crm.quote_line` (11,982 rows) 
**Natural Key:** quote_line_id (CRM UUID) 
**Surrogate PK:** `quotation_line_id = SHA2(quote_line_id, 256)` 
**FK:** quotation_id = SHA2(quote_id, 256) — hash-identity safe (both CRM UUID)

### 4.9 order_line (T4, Materialized View)

**Intent:** Product-level line items within orders. 
**Source:** `sap_sd.vbap` (14,762 rows) 
**Natural Key:** vbeln + posnr 
**Surrogate PK:** `order_line_id = SHA2(CONCAT(vbeln, '|', posnr), 256)` 
**FK:** order_id = SHA2(vbeln, 256)

### 4.10 order_partner (T4, Materialized View)

**Intent:** Partner function assignments per order. 
**Source:** `sap_sd.vbpa` (15,000 rows) 
**Natural Key:** vbeln + parvw 
**Surrogate PK:** `order_partner_id = SHA2(CONCAT(vbeln, '|', parvw), 256)` 
**FK:** order_id = SHA2(vbeln, 256)

### 4.11 order_schedule_line (T5, Materialized View)

**Intent:** Confirmed delivery schedule per order line item. 
**Source:** `sap_sd.vbep` (22,212 rows) 
**Natural Key:** vbeln + posnr + etenr 
**Surrogate PK:** `order_schedule_line_id = SHA2(CONCAT(vbeln, '|', posnr, '|', etenr), 256)` 
**FK:** order_line_id = SHA2(CONCAT(vbeln, '|', posnr), 256)

### 4.12 delivery_schedule (T6, Materialized View)

**Intent:** Scheduling agreement delivery cadence records. 
**Source:** `sap_sd.vbep` WHERE message_type IN scheduling EDI types (0 rows expected) 
**Natural Key:** vbeln + posnr + etenr (for scheduling msg types) 
**Surrogate PK:** `delivery_schedule_id = SHA2(CONCAT(vbeln, '|', posnr, '|', etenr), 256)` 
**Note:** Partial grade — no scheduling EDI messages exist in current bronze.

### 4.13 edi_order_message (T6, Streaming Table)

**Intent:** Electronic order message log (append-only events). 
**Source:** `edi_gateway.edi_message_log` (956 rows) 
**Natural Key:** message_id 
**Surrogate PK:** `edi_order_message_id = SHA2(message_id, 256)` 
**FK:** order_id = SHA2(order_number, 256) 
**Watermark:** transmission_ts (append-only; excludes scheduling message types)

### 4.14 order_credit_check (T6, Streaming Table)

**Intent:** Credit limit check results (append-only log). 
**Source:** `sap_sd.zcredit_log` (3,104 rows) 
**Natural Key:** vbeln + check_ts 
**Surrogate PK:** `order_credit_check_id = SHA2(CONCAT(vbeln, '|', check_ts), 256)` 
**FK:** order_id = SHA2(vbeln, 256) 
**Watermark:** check_ts (append-only) 
**Computed:** credit_utilization_pct = ROUND(CAST(exp_after AS DECIMAL) / NULLIF(CAST(klimk AS DECIMAL), 0) * 100, 2)

### 4.15 return_order (T6, Materialized View)

**Intent:** RMA return order headers from returns portal. 
**Source:** `returns_portal.rma_request` (227 rows) 
**Natural Key:** rma_number 
**Surrogate PK:** `return_order_id = SHA2(rma_number, 256)` 
**FK:** order_id = SHA2(original_order_number, 256) [100% resolved]; order_reason_id = NULL [0% — vocab gap]

### 4.16 otd_record (T6, Materialized View)

**Intent:** On-time delivery tracking per schedule line (proxy). 
**Source:** `sap_sd.vbep` (22,212 rows) 
**Natural Key:** vbeln + posnr + etenr 
**Surrogate PK:** `otd_record_id = SHA2(CONCAT(vbeln, '|', posnr, '|', etenr), 256)` 
**FK:** order_line_id, order_schedule_line_id (hash-identity) 
**P0 Gap:** actual_delivery_date = NULL (requires likp/lips for real actuals) 
**OTD Proxy:** Compares edatu (requested) vs wadat (goods issue date) — ~45.8% ON_TIME / ~54.2% LATE

### 4.17 return_order_line (T7, Materialized View)

**Intent:** Line-item detail within return orders. 
**Source:** `returns_portal.rma_line` (329 rows) 
**Natural Key:** rma_line_id 
**Surrogate PK:** `return_order_line_id = SHA2(rma_line_id, 256)` 
**FK:** return_order_id = SHA2(rma_number, 256) [hash-identity; 100% resolved]

## 5. SDP-Specific Implementation Notes

### Materialized Views (15 entities)
```sql
CREATE OR REFRESH MATERIALIZED VIEW catalog.schema.entity_name
AS SELECT ...
```
- Full recompute on each pipeline update (TRIGGERED mode)
- SDP resolves inter-MV dependencies automatically from SQL references
- No explicit watermark needed — MV always reflects current bronze state

### Streaming Tables (2 entities: edi_order_message, order_credit_check)
```sql
CREATE OR REFRESH STREAMING TABLE catalog.schema.entity_name
AS SELECT ...
FROM STREAM(READ_FILES(...))
-- OR from a streaming source with Auto Loader
```
- Append-only: new rows added incrementally
- Watermark columns: transmission_ts (EDI), check_ts (credit)
- If bronze sources are Delta tables (not files), use `STREAM(bronze_table)` syntax

### Pipeline Configuration
```yaml
pipeline_name: meridian_sales_order_silver_sdp
catalog: manufacturing_silver_vibe
target_schema: sales_order_silver_sdp
mode: TRIGGERED
schedule: daily 06:00 UTC (PAUSED initially)
```

## 6. Data Quality Expectations (SDP CONSTRAINT syntax)

For each entity, define expectations:
```sql
CONSTRAINT pk_unique EXPECT (COUNT(*) = COUNT(DISTINCT {pk_col})) ON VIOLATION FAIL UPDATE
CONSTRAINT fk_resolved EXPECT ({fk_col} IS NULL OR {fk_col} IN (SELECT {pk} FROM parent)) ON VIOLATION DROP ROW
```

## 7. Source System Enum

Values written to `_source_system` column:
- `SAP_S4` — SAP S/4HANA SD module
- `SALESFORCE` — Salesforce CRM
- `EDI` — EDI Gateway middleware
- `RETURNS_PORTAL` — Returns/RMA web application

## 8. Blocked Entities (Deferred — Requires Bronze Ingestion)

| Entity | Missing Bronze | Ingestion Ask |
| --- | --- | --- |
| order_header_condition | PRCD_ELEMENTS | SAP pricing conditions |
| order_line_condition | PRCD_ELEMENTS | SAP pricing conditions |
| order_status_event | cdhdr + cdpos | SAP change documents |
| order_change | cdhdr + cdpos | SAP change documents |
| order_block | cdhdr + cdpos | SAP change documents |
| order_text | stxh + stxl | SAPscript text storage |
| order_configuration | CUOBJ / config | SAP variant configuration |
| order_fulfillment_block | Export ctrl tables | Trade compliance |
| atp_check | ATPLOG | ATP result logging |
