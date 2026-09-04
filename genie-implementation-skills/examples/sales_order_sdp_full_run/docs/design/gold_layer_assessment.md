# Gold Layer Assessment — Meridian Sales Order (SDP Hybrid Pipeline)

**Domain:** Sales Order Management  
**Output Model:** Hybrid — dimensional gold star downstream from normalized 3NF silver  
**Gold Schema:** `manufacturing_silver_vibe.sales_order_gold_sdp`  
**Silver Source:** `manufacturing_silver_vibe.sales_order_silver_sdp` (17 entities, Phase 1 complete)  
**Pipeline Type:** Lakeflow Spark Declarative Pipeline (SDP) — Materialized Views  
**Assessment Date:** 2026-07-28  
**Metamodel:** `manufacturing_ecm_v1._metamodel` (V2, sales_order scope — 3NF only; no gold entities defined)

---

## 1. Assessment Summary

The silver layer provides a complete normalized 3NF foundation covering the quote-to-cash lifecycle.
The gold dimensional star is derived entirely from silver — no additional bronze reads required.
All gold objects will be **Materialized Views** in the same SDP pipeline, downstream from silver MVs.

| Metric | Value |
| --- | --- |
| Fact tables proposed | 5 |
| Dimension tables proposed | 7 |
| Bridge tables proposed | 1 |
| Total gold objects | 13 |
| Source layer | Silver 3NF (17 tables) |
| Additional bronze needed | None |
| KPIs structurally supported | 12 / 14 (2 blocked by P0 gaps) |
| Overall readiness | **READY TO BUILD** |

---

## 2. Dimensional Model Design

### 2.1 Star Schema Overview

```
                    dim_date
                       │
        dim_customer───┼───dim_material
               │       │       │
               ├───fact_sales_order_line───dim_sales_area
               │       │                      │
               │       ├──────────────────dim_channel
               │       │
               ├───fact_otd
               │
               ├───fact_quotation_line
               │
               ├───fact_return_line────dim_order_reason
               │
               └───fact_credit_check
                       │
              dim_sales_contract
                       │
            bridge_order_partner
```

### 2.2 Design Principles

- **Conformed dimensions** — shared across all facts; single version of truth for customer, material, date
- **Surrogate keys** — `{Entity}_Key = SHA2(natural_key, 256)` (consistent with silver convention)
- **SCD Type 1** — overwrite on key match (mirrors silver strategy)
- **Wide facts** — denormalize header attributes onto line-grain facts to minimize joins at query time
- **Role-playing dimensions** — dim_date used as Order_Date, Requested_Delivery_Date, Quote_Date, RMA_Date
- **Degenerate dimensions** — Order_Number, Line_Number carried as fact attributes (no separate dim)

---

## 3. Dimension Specifications

### 3.1 dim_date (Generated Calendar)

**Intent:** Standard date dimension covering the full order date range.  
**Source:** Generated (no silver source table; built from `SEQUENCE` or date spine)  
**Grain:** One row per calendar date  
**Surrogate PK:** `Date_Key = date_value` (DATE type, self-keyed — no hash needed)  
**Cardinality:** ~730 rows (2024-07-01 to 2026-06-30)

| Column | Type | Description |
| --- | --- | --- |
| Date_Key | DATE | PK — the calendar date |
| Year | INT | Calendar year |
| Quarter | INT | Quarter number (1–4) |
| Month | INT | Month number (1–12) |
| Month_Name | STRING | Full month name |
| Week_Of_Year | INT | ISO week number |
| Day_Of_Week | INT | Day of week (1=Mon, 7=Sun) |
| Day_Name | STRING | Full day name |
| Is_Weekday | BOOLEAN | Mon–Fri flag |
| Fiscal_Year | INT | Fiscal year (Jul–Jun) |
| Fiscal_Quarter | INT | Fiscal quarter |
| Fiscal_Period | STRING | FY{YY}-Q{Q} label |

### 3.2 dim_customer

**Intent:** Conformed customer dimension — Sold-To party with geo attributes.  
**Source:** `silver.order_partner` (WHERE Partner_Function = 'AG') deduplicated by Partner_Number  
**Grain:** One row per unique customer (Sold-To Partner_Number)  
**Surrogate PK:** `Customer_Key = SHA2(Partner_Number, 256)`  
**Cardinality:** 300 customers

| Column | Type | Source |
| --- | --- | --- |
| Customer_Key | STRING | SHA2(Partner_Number, 256) |
| Customer_Number | STRING | Partner_Number |
| Customer_Name | STRING | Partner_Name |
| Country | STRING | Country |
| City | STRING | City |
| Postal_Code | STRING | Postal_Code |
| _source_system | STRING | 'SAP_S4' |
| _loaded_at | TIMESTAMP | current_timestamp() |

**Note:** Customer master enrichment (industry, segment, credit group) requires cross-domain join to `customer` domain — DEFERRED to Phase 3.

### 3.3 dim_material

**Intent:** Conformed material/product dimension.  
**Source:** `silver.order_line` deduplicated by Material_Number + `silver.quotation_line` by SKU_Code  
**Grain:** One row per unique material/SKU  
**Surrogate PK:** `Material_Key = SHA2(Material_Number, 256)`  
**Cardinality:** ~400 distinct materials

| Column | Type | Source |
| --- | --- | --- |
| Material_Key | STRING | SHA2(Material_Number, 256) |
| Material_Number | STRING | order_line.Material_Number |
| Item_Category | STRING | Most frequent Item_Category per material |
| Product_Group | STRING | quotation_line.Product_Group (where available) |
| _source_system | STRING | 'SAP_S4' |
| _loaded_at | TIMESTAMP | current_timestamp() |

**Note:** Material master enrichment (description, weight, dimensions, product hierarchy) requires cross-domain join to `product_catalog` domain — DEFERRED.

### 3.4 dim_sales_area

**Intent:** Sales organization structure dimension.  
**Source:** `silver.sales_area` (direct passthrough with key rename)  
**Grain:** One row per sales org + channel + division combination  
**Surrogate PK:** `Sales_Area_Key = sales_area_id` (identity — silver already has SHA2)  
**Cardinality:** 4 rows

| Column | Type | Source |
| --- | --- | --- |
| Sales_Area_Key | STRING | sales_area_id |
| Sales_Organization | STRING | Sales_Organization |
| Distribution_Channel | STRING | Distribution_Channel |
| Division | STRING | Division |
| Currency_Code | STRING | Currency_Code |
| Pricing_Procedure | STRING | Pricing_Procedure |
| Sales_Area_Description | STRING | Sales_Area_Description |

### 3.5 dim_channel

**Intent:** Distribution channel business rules dimension.  
**Source:** `silver.channel_config` (direct passthrough with key rename)  
**Grain:** One row per distribution channel  
**Surrogate PK:** `Channel_Key = channel_config_id` (identity)  
**Cardinality:** 4 rows

| Column | Type | Source |
| --- | --- | --- |
| Channel_Key | STRING | channel_config_id |
| Distribution_Channel | STRING | Distribution_Channel |
| Channel_Name | STRING | Channel_Name |
| Credit_Check_Required | BOOLEAN | Credit_Check_Required |
| EDI_Capable | BOOLEAN | EDI_Capable |
| Minimum_Order_Value | DECIMAL(15,2) | Minimum_Order_Value |

### 3.6 dim_order_reason

**Intent:** Reason/rejection code reference dimension.  
**Source:** `silver.order_reason` (direct passthrough with key rename)  
**Grain:** One row per source_system + reason_code  
**Surrogate PK:** `Order_Reason_Key = order_reason_id` (identity)  
**Cardinality:** 9 rows

| Column | Type | Source |
| --- | --- | --- |
| Order_Reason_Key | STRING | order_reason_id |
| Reason_Code | STRING | Reason_Code |
| Reason_Description | STRING | Reason_Description |
| Reason_Category | STRING | Reason_Category |
| Source_System | STRING | Source_System |

### 3.7 dim_sales_contract

**Intent:** Contract reference dimension for contract-linked order analysis.  
**Source:** `silver.sales_contract` (direct passthrough with key rename)  
**Grain:** One row per contract  
**Surrogate PK:** `Sales_Contract_Key = sales_contract_id` (identity)  
**Cardinality:** 120 rows

| Column | Type | Source |
| --- | --- | --- |
| Sales_Contract_Key | STRING | sales_contract_id |
| Contract_Number | STRING | Contract_Number |
| Customer_Number | STRING | Customer_Number |
| Contract_Type | STRING | Contract_Type |
| Valid_From | DATE | Valid_From |
| Valid_To | DATE | Valid_To |
| Target_Quantity | DECIMAL(15,3) | Target_Quantity |
| Target_Value | DECIMAL(15,2) | Target_Value |
| Contract_Status | STRING | Contract_Status |

---

## 4. Fact Specifications

### 4.1 fact_sales_order_line (Primary Fact)

**Intent:** Line-item grain fact for revenue, volume, and order analysis.  
**Source:** `silver.order_line` JOIN `silver.order` JOIN `silver.order_partner` (Sold-To)  
**Grain:** One row per order line item  
**Surrogate PK:** `Order_Line_Key = order_line_id` (identity from silver)  
**Row Count:** 14,762

| Column | Type | Role | Source |
| --- | --- | --- | --- |
| Order_Line_Key | STRING | PK | order_line_id |
| Order_Number | STRING | DD | order.Order_Number |
| Line_Number | STRING | DD | order_line.Line_Number |
| Order_Date_Key | DATE | FK→dim_date | order.Order_Date |
| Requested_Delivery_Date_Key | DATE | FK→dim_date | order.Requested_Delivery_Date |
| Customer_Key | STRING | FK→dim_customer | SHA2(order_partner[AG].Partner_Number, 256) |
| Material_Key | STRING | FK→dim_material | SHA2(order_line.Material_Number, 256) |
| Sales_Area_Key | STRING | FK→dim_sales_area | order.sales_area_id |
| Channel_Key | STRING | FK→dim_channel | SHA2(order.Distribution_Channel, 256) |
| Order_Reason_Key | STRING | FK→dim_order_reason | order.order_reason_id |
| Order_Type | STRING | Attr | order.Order_Type |
| Plant | STRING | Attr | order_line.Plant |
| Overall_Status | STRING | Attr | order.Overall_Status |
| Item_Category | STRING | Attr | order_line.Item_Category |
| PO_Number | STRING | DD | order.PO_Number |
| Order_Quantity | DECIMAL(15,3) | Measure | order_line.Order_Quantity |
| Net_Price | DECIMAL(15,2) | Measure | order_line.Net_Price |
| Net_Value | DECIMAL(15,2) | Measure | order_line.Net_Value |
| Currency | STRING | Attr | order.Currency |
| Is_Rejected | BOOLEAN | Flag | order_line.Rejection_Reason IS NOT NULL |
| _source_system | STRING | Audit | 'SAP_S4' |
| _loaded_at | TIMESTAMP | Audit | current_timestamp() |

**Additive Measures:** Order_Quantity, Net_Value  
**Semi-Additive:** Net_Price (average only)  
**Key KPIs:** Revenue by period/customer/material/channel, order volume, avg order value, rejection rate

### 4.2 fact_otd (On-Time Delivery)

**Intent:** Schedule-line grain fact for delivery performance analysis.  
**Source:** `silver.otd_record` JOIN `silver.order_line` JOIN `silver.order`  
**Grain:** One row per delivery schedule line  
**Surrogate PK:** `OTD_Key = otd_record_id` (identity)  
**Row Count:** 22,212

| Column | Type | Role | Source |
| --- | --- | --- | --- |
| OTD_Key | STRING | PK | otd_record_id |
| Order_Number | STRING | DD | otd_record.Order_Number |
| Line_Number | STRING | DD | otd_record.Line_Number |
| Requested_Delivery_Date_Key | DATE | FK→dim_date | Requested_Delivery_Date |
| Customer_Key | STRING | FK→dim_customer | via order→order_partner |
| Material_Key | STRING | FK→dim_material | via order_line.Material_Number |
| Sales_Area_Key | STRING | FK→dim_sales_area | via order.sales_area_id |
| OTD_Status | STRING | Attr | OTD_Status (ON_TIME / LATE) |
| Days_Variance | INT | Measure | Days_Variance |
| Is_On_Time | BOOLEAN | Flag | OTD_Status = 'ON_TIME' |
| Actual_Delivery_Date | DATE | Measure | NULL (P0 gap — requires likp/lips) |
| _source_system | STRING | Audit | 'SAP_S4' |
| _loaded_at | TIMESTAMP | Audit | current_timestamp() |

**Additive Measures:** Is_On_Time (countable flag), Days_Variance (SUM for total delay)  
**Key KPIs:** OTD % (COUNT(Is_On_Time=true)/COUNT(*)), avg days late, OTIF by customer/material  
**P0 Gap:** Actual_Delivery_Date = NULL; OTD computed as proxy from schedule dates only

### 4.3 fact_quotation_line (Quote-to-Cash Funnel)

**Intent:** Quote line grain fact for pipeline and conversion analysis.  
**Source:** `silver.quotation_line` JOIN `silver.quotation`  
**Grain:** One row per quotation line item  
**Surrogate PK:** `Quotation_Line_Key = quotation_line_id` (identity)  
**Row Count:** 11,982

| Column | Type | Role | Source |
| --- | --- | --- | --- |
| Quotation_Line_Key | STRING | PK | quotation_line_id |
| Quote_Number | STRING | DD | quotation.Quote_Number |
| Line_Number | STRING | DD | quotation_line.Line_Number |
| Quote_Date_Key | DATE | FK→dim_date | quotation.Quote_Date |
| Customer_Key | STRING | FK→dim_customer | SHA2(quotation.Account_Id, 256) |
| Material_Key | STRING | FK→dim_material | SHA2(quotation_line.SKU_Code, 256) |
| Quote_Status | STRING | Attr | quotation.Status |
| Is_Converted | BOOLEAN | Flag | quotation.Converted_Order_Number IS NOT NULL |
| Conversion_Probability | DECIMAL(5,2) | Measure | quotation.Conversion_Probability |
| Quantity | DECIMAL(15,3) | Measure | quotation_line.Quantity |
| List_Price | DECIMAL(15,2) | Measure | quotation_line.List_Price |
| Discount_Pct | DECIMAL(5,2) | Measure | quotation_line.Discount_Pct |
| Net_Price | DECIMAL(15,2) | Measure | quotation_line.Net_Price |
| Net_Value | DECIMAL(15,2) | Measure | quotation_line.Net_Value |
| Product_Group | STRING | Attr | quotation_line.Product_Group |
| Sales_Rep | STRING | Attr | quotation.Sales_Rep |
| _source_system | STRING | Audit | 'SALESFORCE' |
| _loaded_at | TIMESTAMP | Audit | current_timestamp() |

**Additive Measures:** Quantity, Net_Value  
**Key KPIs:** Quote conversion rate, pipeline value, avg discount, win/loss by rep/product

### 4.4 fact_return_line (Returns Analysis)

**Intent:** Return line grain fact for reverse logistics and quality analysis.  
**Source:** `silver.return_order_line` JOIN `silver.return_order`  
**Grain:** One row per return order line item  
**Surrogate PK:** `Return_Line_Key = return_order_line_id` (identity)  
**Row Count:** 329

| Column | Type | Role | Source |
| --- | --- | --- | --- |
| Return_Line_Key | STRING | PK | return_order_line_id |
| RMA_Number | STRING | DD | return_order.RMA_Number |
| Line_Number | STRING | DD | return_order_line.Line_Number |
| RMA_Date_Key | DATE | FK→dim_date | return_order.RMA_Date |
| Customer_Key | STRING | FK→dim_customer | SHA2(return_order.Customer_Number, 256) |
| Material_Key | STRING | FK→dim_material | SHA2(return_order_line.SKU_Code, 256) |
| Order_Reason_Key | STRING | FK→dim_order_reason | return_order.order_reason_id (NULL — P1 gap) |
| Original_Order_Number | STRING | DD | return_order.Original_Order_Number |
| Reason_Code | STRING | Attr | return_order_line.Reason_Code |
| Inspection_Result | STRING | Attr | return_order_line.Inspection_Result |
| Is_Warranty | BOOLEAN | Flag | return_order_line.Is_Warranty |
| Returned_Quantity | DECIMAL(15,3) | Measure | return_order_line.Returned_Quantity |
| Credit_Value | DECIMAL(15,2) | Measure | return_order_line.Credit_Value |
| Restocking_Fee | DECIMAL(15,2) | Measure | return_order_line.Restocking_Fee |
| Net_Return_Value | DECIMAL(15,2) | Computed | Credit_Value - Restocking_Fee |
| _source_system | STRING | Audit | 'RETURNS_PORTAL' |
| _loaded_at | TIMESTAMP | Audit | current_timestamp() |

**Additive Measures:** Returned_Quantity, Credit_Value, Restocking_Fee, Net_Return_Value  
**Key KPIs:** Return rate (vs orders), return value %, warranty vs non-warranty split, reason analysis  
**P1 Gap:** Order_Reason_Key = NULL (portal vocab gap — codes DMG/WRONG/WARR unmapped to SAP)

### 4.5 fact_credit_check (Credit Risk)

**Intent:** Credit check event grain fact for credit exposure and risk monitoring.  
**Source:** `silver.order_credit_check` JOIN `silver.order`  
**Grain:** One row per credit check event  
**Surrogate PK:** `Credit_Check_Key = order_credit_check_id` (identity)  
**Row Count:** 3,104

| Column | Type | Role | Source |
| --- | --- | --- | --- |
| Credit_Check_Key | STRING | PK | order_credit_check_id |
| Order_Number | STRING | DD | Order_Number |
| Check_Date_Key | DATE | FK→dim_date | CAST(Check_Timestamp AS DATE) |
| Customer_Key | STRING | FK→dim_customer | SHA2(Customer_Number, 256) |
| Sales_Area_Key | STRING | FK→dim_sales_area | via order.sales_area_id |
| Check_Type | STRING | Attr | Check_Type |
| Check_Result | STRING | Attr | Check_Result |
| Risk_Category | STRING | Attr | Risk_Category |
| Credit_Control_Area | STRING | Attr | Credit_Control_Area |
| Credit_Limit | DECIMAL(15,2) | Measure | Credit_Limit |
| Exposure_Before | DECIMAL(15,2) | Measure | Exposure_Before |
| Order_Value | DECIMAL(15,2) | Measure | Order_Value |
| Exposure_After | DECIMAL(15,2) | Measure | Exposure_After |
| Credit_Utilization_Pct | DECIMAL(7,2) | Measure | Credit_Utilization_Pct |
| Is_Approved | BOOLEAN | Flag | Check_Result = 'APPROVED' |
| _source_system | STRING | Audit | 'SAP_S4' |
| _loaded_at | TIMESTAMP | Audit | current_timestamp() |

**Additive Measures:** Order_Value, Credit_Limit (at check time)  
**Semi-Additive:** Credit_Utilization_Pct (average only)  
**Key KPIs:** Approval rate, avg utilization by customer/risk tier, exposure trend

---

## 5. Bridge Table

### 5.1 bridge_order_partner

**Intent:** Pivoted partner function lookup — enables Ship-To and Bill-To analysis on the order fact.  
**Source:** `silver.order_partner` pivoted by Partner_Function  
**Grain:** One row per order (pivoted from 3 rows per order in silver)  
**PK:** `order_id` (from silver; 1:1 with fact_sales_order_line at order-header grain)

| Column | Type | Source |
| --- | --- | --- |
| order_id | STRING | PK — links to fact via Order_Number |
| Sold_To_Number | STRING | WHERE Partner_Function = 'AG' |
| Sold_To_Name | STRING | AG.Partner_Name |
| Ship_To_Number | STRING | WHERE Partner_Function = 'WE' |
| Ship_To_Name | STRING | WE.Partner_Name |
| Ship_To_Country | STRING | WE.Country |
| Ship_To_City | STRING | WE.City |
| Bill_To_Number | STRING | WHERE Partner_Function = 'RE' |
| Bill_To_Name | STRING | RE.Partner_Name |

---

## 6. Pipeline Architecture (Gold Tier)

### 6.1 SDP Object Types

All gold objects are **Materialized Views** — they read from silver MVs and SDP resolves
dependencies automatically. No streaming tables needed at gold (event-grain facts like
credit_check are still MVs reading from silver streaming tables via snapshot semantics).

### 6.2 DAG Structure (Gold Tier)

```
Silver T0–T7 (existing)
  │
G0: dim_date (generated), dim_sales_area (MV), dim_channel (MV), dim_order_reason (MV)
  │
G1: dim_customer (MV), dim_material (MV), dim_sales_contract (MV), bridge_order_partner (MV)
  │
G2: fact_sales_order_line (MV), fact_otd (MV), fact_quotation_line (MV),
    fact_return_line (MV), fact_credit_check (MV)
```

### 6.3 Load Strategy

| Object | Type | Strategy | Rationale |
| --- | --- | --- | --- |
| All 13 gold objects | Materialized View | FULL recompute | All < 25K rows; source is silver MVs; no incremental needed |

### 6.4 Pipeline Configuration Additions

```yaml
# Appended to existing pipeline or separate gold pipeline
pipeline_name: meridian_sales_order_gold_sdp
catalog: manufacturing_silver_vibe
target_schema: sales_order_gold_sdp
mode: TRIGGERED
schedule: daily 07:00 UTC (after silver completes at 06:00)
```

---

## 7. KPI Coverage Matrix

| # | KPI / Metric | Fact Table | Supported | Notes |
| --- | --- | --- | --- | --- |
| 1 | Revenue by period/customer/channel | fact_sales_order_line | FULL | SUM(Net_Value) sliced by any dim |
| 2 | Order volume & avg order value | fact_sales_order_line | FULL | COUNT(DISTINCT Order_Number), AVG(Net_Value) |
| 3 | Revenue by material/product group | fact_sales_order_line + fact_quotation_line | FULL | Product_Group from quotes; Item_Category from orders |
| 4 | On-Time Delivery % | fact_otd | PARTIAL | Proxy only (schedule dates); actual_delivery_date = NULL (P0) |
| 5 | OTIF (On-Time In-Full) | fact_otd | PARTIAL | No confirmed qty vs delivered qty comparison without likp/lips |
| 6 | Quote conversion rate | fact_quotation_line | FULL | Is_Converted flag; COUNT(converted)/COUNT(*) |
| 7 | Quote pipeline value | fact_quotation_line | FULL | SUM(Net_Value) WHERE Status = 'open' |
| 8 | Return rate (% of orders) | fact_return_line vs fact_sales_order_line | FULL | Cross-fact ratio |
| 9 | Return value % | fact_return_line | FULL | SUM(Credit_Value) / SUM(order Net_Value) |
| 10 | Credit utilization trend | fact_credit_check | FULL | AVG(Credit_Utilization_Pct) by period |
| 11 | Credit approval rate | fact_credit_check | FULL | COUNT(Is_Approved=true)/COUNT(*) |
| 12 | Contract utilization | dim_sales_contract + fact_sales_order_line | PARTIAL | Needs contract↔order linkage (silver FK exists) |
| 13 | Pricing waterfall / margin | BLOCKED | BLOCKED | Requires PRCD_ELEMENTS (P0 gap) |
| 14 | Order lifecycle time | BLOCKED | BLOCKED | Requires cdhdr/cdpos (P0 gap) |

**Coverage Summary:** 10 FULL + 2 PARTIAL + 2 BLOCKED = **85.7% structural support**

---

## 8. Gap Analysis (Gold-Specific)

| # | Gap | Priority | Impact | Unblock Action |
| --- | --- | --- | --- | --- |
| G1 | dim_customer lacks industry/segment | P2 | Cannot slice revenue by customer segment | Cross-domain join to `customer` domain dim |
| G2 | dim_material lacks description/hierarchy | P2 | Material shown as code only, no product hierarchy | Cross-domain join to `product_catalog` domain |
| G3 | OTD actuals (actual_delivery_date = NULL) | P0 | OTD is proxy only; no true OTIF calculation | Ingest `sap_sd.likp` + `sap_sd.lips` to silver |
| G4 | Pricing conditions (margin analysis) | P0 | No pricing waterfall, no margin KPI | Ingest `sap_sd.PRCD_ELEMENTS` to silver |
| G5 | Order lifecycle (status changes) | P0 | No order cycle time, no status flow analysis | Ingest `sap_sd.cdhdr` + `cdpos` to silver |
| G6 | Return reason FK unresolved | P1 | Cannot slice returns by standardized reason | Map portal codes (DMG/WRONG/WARR) to order_reason |
| G7 | Quote→Customer FK (Account_Id mapping) | P2 | Quote customer is CRM Account_Id, not SAP kunnr | Cross-domain mapping table needed |
| G8 | Contract utilization linkage | P2 | Silver has contract→order FK but not at line grain | Add contract line → order line matching logic |

---

## 9. Data Quality Expectations (Gold Layer)

```sql
-- Applied to each gold MV via SDP CONSTRAINT syntax
CONSTRAINT pk_unique EXPECT (pk_col IS NOT NULL) ON VIOLATION FAIL UPDATE
CONSTRAINT dim_date_resolved EXPECT (Date_Key IS NOT NULL) ON VIOLATION DROP ROW
CONSTRAINT customer_resolved EXPECT (Customer_Key IS NOT NULL OR Customer_Key = SHA2('UNKNOWN', 256)) ON VIOLATION DROP ROW
CONSTRAINT material_resolved EXPECT (Material_Key IS NOT NULL) ON VIOLATION DROP ROW
CONSTRAINT net_value_positive EXPECT (Net_Value >= 0 OR Is_Rejected = true) ON VIOLATION WARN
```

---

## 10. Naming Conventions (Gold Layer)

| Element | Convention | Example |
| --- | --- | --- |
| Dimension tables | dim_{entity} (lower_snake) | `dim_customer`, `dim_material` |
| Fact tables | fact_{process}_{grain} (lower_snake) | `fact_sales_order_line` |
| Bridge tables | bridge_{entity} (lower_snake) | `bridge_order_partner` |
| Surrogate PK | {Entity}_Key (Pascal_Snake) | `Customer_Key`, `Material_Key` |
| FK columns | Same as parent PK name | `Customer_Key` (on fact) |
| Measures | Pascal_Snake | `Net_Value`, `Order_Quantity` |
| Flags | Is_{condition} (Pascal_Snake BOOLEAN) | `Is_On_Time`, `Is_Rejected` |
| Degenerate dims | Natural key name (Pascal_Snake) | `Order_Number`, `Line_Number` |

---

## 11. Load Order & Dependencies

| Tier | Objects | Depends On |
| --- | --- | --- |
| G0 | dim_date, dim_sales_area, dim_channel, dim_order_reason | Silver T0 only |
| G1 | dim_customer, dim_material, dim_sales_contract, bridge_order_partner | Silver T1–T4 |
| G2 | fact_sales_order_line, fact_otd, fact_quotation_line, fact_return_line, fact_credit_check | Silver all + G0/G1 dims |

**Note:** SDP resolves dependencies automatically from SQL references. Explicit tier ordering
is for documentation clarity; the pipeline engine handles execution order.

---

## 12. Human Gate Decisions Required

| ID | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| HG-GOLD-1 | dim_date generation method | (a) Generated calendar table as MV (b) Use existing shared dim_date if one exists | (a) — self-contained, no cross-domain dependency |
| HG-GOLD-2 | Customer key alignment (SAP kunnr vs CRM Account_Id) | (a) Two separate customer dims (b) Unified via mapping table (c) SAP-only for now | (c) — CRM mapping is P2; build SAP-sourced dim now |
| HG-GOLD-3 | Separate gold pipeline vs extend silver pipeline | (a) New pipeline `meridian_sales_order_gold_sdp` (b) Add gold MVs to existing silver pipeline | (a) — cleaner separation; gold schedules after silver |
| HG-GOLD-4 | EDI + credit check inclusion at gold | (a) Include as facts (b) Defer to Phase 3 (operational monitoring use case) | (a) — credit is core; EDI is useful but lower priority |
| HG-GOLD-5 | Unknown dimension handling | (a) NULL FK (no -1 sentinel) (b) Add 'Unknown' member row to each dim | (a) — consistent with silver 3NF convention |

---

## 13. Recommendations & Next Steps

1. **Confirm human gate decisions** (HG-GOLD-1 through HG-GOLD-5) before proceeding to build
2. **Create gold schema:** `CREATE SCHEMA IF NOT EXISTS manufacturing_silver_vibe.sales_order_gold_sdp`
3. **Build gold SDP pipeline** — 13 MVs in tier order (G0→G1→G2)
4. **Validate gold layer** — PK uniqueness, FK resolution rates, measure non-null rates
5. **Deploy as separate DAB job** — triggered daily at 07:00 UTC (1 hour after silver refresh)
6. **P0 gap remediation** — prioritize likp/lips ingestion to unlock true OTD at gold
7. **Cross-domain enrichment (Phase 3)** — customer master, material master from adjacent domains

---

## Appendix A: Silver → Gold Entity Mapping

| Gold Object | Silver Source Tables | Join Type |
| --- | --- | --- |
| dim_date | (generated) | N/A |
| dim_customer | order_partner (AG only) | DISTINCT |
| dim_material | order_line, quotation_line | UNION DISTINCT |
| dim_sales_area | sales_area | 1:1 passthrough |
| dim_channel | channel_config | 1:1 passthrough |
| dim_order_reason | order_reason | 1:1 passthrough |
| dim_sales_contract | sales_contract | 1:1 passthrough |
| bridge_order_partner | order_partner | PIVOT (3→1) |
| fact_sales_order_line | order_line + order + order_partner | LEFT JOINs |
| fact_otd | otd_record + order_line + order | LEFT JOINs |
| fact_quotation_line | quotation_line + quotation | INNER JOIN |
| fact_return_line | return_order_line + return_order | INNER JOIN |
| fact_credit_check | order_credit_check + order | LEFT JOIN |
