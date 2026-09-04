<!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->

# Sales Order — Domain Narrative

> The Sales Order domain models the complete order-to-delivery lifecycle for B2B sales in
> a manufacturing enterprise. It spans quotation creation, order confirmation, line-item
> scheduling, delivery tracking, credit checks, EDI messaging, and returns processing.
> The model contains **30 governed entities** across two layers — a normalized 3NF silver
> (17 tables, 100,294 rows) and a dimensional star gold (13 tables, 58,354 rows) — built
> as a Lakeflow Spark Declarative Pipeline (SDP). All entities are Grade A. The pipeline
> runs in development on `manufacturing_silver_vibe`.

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────────────────────┐     ┌──────────────────┐
│   BRONZE SOURCES    │     │          SILVER (3NF Normalized)         │     │   GOLD (Star)    │
│                     │     │   manufacturing_silver_vibe              │     │                  │
│ sap_sd (SAP S/4)    │────▶│   .sales_order_silver_sdp                │────▶│ .sales_order_    │
│ salesforce_crm      │     │                                          │     │  gold_sdp        │
│ edi_gateway         │     │   17 entities (15 MV + 2 ST)             │     │                  │
│ returns_portal      │     │   100,294 rows                           │     │ 13 entities      │
│                     │     │                                          │     │ (7 dim + 1       │
│                     │     │   Tier 0: sales_area, order_reason       │     │  bridge + 5      │
│                     │     │   Tier 1–7: contracts → orders →         │     │  fact)            │
│                     │     │     lines → schedule → delivery          │     │ 58,354 rows      │
└─────────────────────┘     └──────────────────────────────────────────┘     └──────────────────┘
```

**Architecture pattern:** Hybrid (normalized silver SSOT + dimensional gold for analytics)  
**Pipeline type:** Lakeflow Spark Declarative Pipeline (single pipeline, two layer globs)  
**Load pattern:** Materialized Views (full recompute) + Streaming Tables (append-only events)  
**Compute:** Serverless  
**Silver schema:** `manufacturing_silver_vibe.sales_order_silver_sdp`  
**Gold schema:** `manufacturing_silver_vibe.sales_order_gold_sdp`  
**Pipeline ID:** `1b57fa65-f8d3-434b-b5cd-9beeba43e872`

---

## Organizational Hierarchy

The sales order domain follows a document hierarchy rather than an organizational one:

```
Sales Area (4)                             ← org structure anchor (org + channel + division)
  └─ Channel Config (4)                    ← business rules per channel
  └─ Sales Contract (120)                  ← framework/blanket agreements
       └─ Sales Contract Line (373)        ← material commitments within contracts
  └─ Quotation (4,000)                     ← formal proposals (CRM)
       └─ Quotation Line (11,982)          ← line-item detail
  └─ Order (5,000)                         ← confirmed B2B orders
       ├─ Order Line (14,762)              ← product-level items
       │    └─ Order Schedule Line (22,212)← delivery dates/quantities
       │    └─ OTD Record (22,212)         ← on-time delivery tracking
       ├─ Order Partner (15,000)           ← partner functions (AG/WE/RE)
       ├─ EDI Order Message (956)          ← electronic transactions
       ├─ Order Credit Check (3,104)       ← credit risk events
       └─ Return Order (227)               ← RMA headers
            └─ Return Order Line (329)     ← return line items
```

The gold layer reshapes this into a star schema with conformed dimensions and line-item-grain facts.

---

## Silver Layer — Entity Stories

### sales_area — Sales Organization Structure

The foundational reference entity defining the valid combinations of sales organization,
distribution channel, and division. With only 4 rows, it represents the enterprise's
complete go-to-market structure. Every downstream order inherits its sales area assignment
through its organizational codes.

**Source:** SAP SD tvta | **Rows:** 4 | **Grade:** A

### order_reason — Rejection/Reason Code Reference

A multi-source standardized lookup of reason and rejection codes, combining SAP S/4 reason
codes with Salesforce CRM loss reasons. SAP takes priority in deduplication (ORDER BY
source_system DESC gives SAP_S4 row-number 1). Contains 9 distinct reason codes used
across orders and returns.

**Source:** SAP SD tvaut + Salesforce loss_reason_ref | **Rows:** 9 | **Grade:** A

### channel_config — Distribution Channel Business Rules

Captures per-channel pricing procedures, credit requirements, and business rule
configuration. The sales_area_id FK is NULL (the source table lacks the organization/division
fields to resolve it) — a known accepted gap.

**Source:** SAP SD zsd_channel_config | **Rows:** 4 | **Grade:** A  
**Known gap:** sales_area_id = NULL (P3, accepted)

### sales_contract — Framework Purchase Agreements

Blanket/framework agreements defining customer purchasing commitments over time.
Each contract has validity dates, target values, and terms. Like channel_config,
the sales_area_id FK cannot be resolved from the source (veda lacks org fields).

**Source:** SAP SD veda | **Rows:** 120 | **Grade:** A  
**Known gap:** sales_area_id = NULL (P3, accepted)

### sales_contract_line — Material Commitments Within Contracts

Line-level detail within framework agreements specifying the materials, quantities, and
prices committed. Resolves 100% to its parent sales_contract via hash-identity FK.

**Source:** SAP SD veda_item | **Rows:** 373 | **Grade:** A

### quotation — Formal Customer Proposals

Formal price/availability proposals from the Salesforce CRM pipeline. Each quotation
represents a sales opportunity that may convert to a confirmed order (approximately
19.9% of orders trace back to a quotation via the converted_order_number field).

**Source:** Salesforce CRM quote | **Rows:** 4,000 | **Grade:** A

### order — Confirmed B2B Sales Orders

The core transaction entity — confirmed sales order headers from SAP. Contains pricing,
shipping terms, customer references, and status. Three FK relationships connect each order:
sales_area (100%), order_reason (when a rejection exists), and quotation (~19.9% for
converted quotes). The quotation join uses a deduped subquery to prevent fan-out.

**Source:** SAP SD vbak | **Rows:** 5,000 | **Grade:** A  
**Key insight:** Only 1 in 5 orders originated from a formal CRM quotation — the rest entered SAP directly.

### quotation_line — CRM Quote Line Items

Line-item detail within CRM quotations. Uses a hash-identity FK (SHA2 of the same
quote_id) to resolve to its parent quotation at 100%. Contains SKU, quantities,
and pricing at the quote-line level.

**Source:** Salesforce CRM quote_line | **Rows:** 11,982 | **Grade:** A

### order_line — Product-Level Order Items

Product-level line items within sales orders, carrying material numbers, quantities,
net values, and item categories. The primary grain table for revenue analysis.
Resolves 100% to its parent order via order_id.

**Source:** SAP SD vbap | **Rows:** 14,762 | **Grade:** A  
**Key insight:** Average ~3 lines per order — a typical manufacturing B2B pattern.

### order_partner — Partner Function Assignments

Partner functions (Sold-To AG, Ship-To WE, Bill-To RE, Payer RG) assigned per
sales order. Multiple partners per order is normal. The gold layer pivots the AG
(Sold-To) function into a conformed customer dimension.

**Source:** SAP SD vbpa | **Rows:** 15,000 | **Grade:** A  
**Key insight:** 3 partner records per order on average — exactly 3 functions (AG/WE/RE) for most.

### order_schedule_line — Delivery Schedule Commitments

Confirmed delivery dates and quantities per order line item. Each schedule line
represents a committed delivery tranche. This is the most voluminous silver entity
(22,212 rows) because many order lines have multiple delivery dates.

**Source:** SAP SD vbep | **Rows:** 22,212 | **Grade:** A

### delivery_schedule — Scheduling Agreement Deliveries

Scheduling agreement (SA) delivery records — a specialized subset of vbep for long-term
replenishment cadences. Currently 0 rows because the bronze source contains no SA-type
documents. This is expected and accepted.

**Source:** SAP SD vbep (SA types only) | **Rows:** 0 | **Grade:** A (Partial)  
**Note:** Will populate when SA document types appear in bronze ingestion.

### edi_order_message — Electronic Order Transactions

An append-only streaming table capturing inbound and outbound EDI messages related to
orders. Watermarked on transmission_ts for incremental processing. Excludes scheduling
message types (those route to delivery_schedule).

**Source:** EDI Gateway edi_message_log | **Rows:** 956 | **Grade:** A  
**Load pattern:** Streaming Table (APPEND_ONLY)

### order_credit_check — Credit Risk Events

An append-only streaming table recording credit limit check results per order. Each row
represents a point-in-time credit exposure check with utilization percentage computed inline.
Watermarked on check_ts.

**Source:** SAP SD zcredit_log | **Rows:** 3,104 | **Grade:** A  
**Load pattern:** Streaming Table (APPEND_ONLY)

### return_order — RMA Return Headers

Return merchandise authorization (RMA) headers from the returns portal. Each return
references its originating order at 100% FK resolution. The order_reason_id is NULL
because the portal's reason vocabulary (DMG/WRONG/WARR) doesn't map to the SAP/CRM
reason codes — a P1 gap accepted at human gate.

**Source:** Returns Portal rma_request | **Rows:** 227 | **Grade:** A  
**Known gap:** order_reason_id = NULL (P1, portal vocab gap — HG-SDP-4 accepted)

### otd_record — On-Time Delivery Tracking

On-time delivery proxy records derived from schedule lines. Compares scheduled delivery
dates against a threshold to compute OTD_Status (ON_TIME / LATE). The actual_delivery_date
is NULL (P0 gap — requires likp/lips ingestion for true delivery confirmation). Current
proxy: 45.8% ON_TIME / 54.2% LATE based on schedule adherence.

**Source:** SAP SD vbep | **Rows:** 22,212 | **Grade:** A  
**Known gap:** actual_delivery_date = NULL (P0, requires likp/lips bronze ingestion)

### return_order_line — RMA Line Items

Line-item detail within RMA returns. Inherits the order_reason_id vocab gap from its
parent return_order. Resolves 100% to return_order via hash-identity FK.

**Source:** Returns Portal rma_line | **Rows:** 329 | **Grade:** A

---

## Gold Layer — Entity Stories

### dim_date — Calendar Dimension

A generated calendar dimension spanning 2024-07-01 to 2026-06-30 (fiscal year Jul-Jun).
Provides day-of-week, month, quarter, year, fiscal attributes, and weekend/holiday flags
for all date-keyed facts.

**Rows:** 730 | **Grain:** One row per calendar day

### dim_sales_area — Sales Organization Dimension

Passthrough from silver sales_area. Provides organization name, channel description,
and division description for star-schema joins.

**Rows:** 4 | **Grain:** One row per org+channel+division combination

### dim_channel — Distribution Channel Dimension

Passthrough from silver channel_config. Supplies pricing procedure, credit policy,
and channel business rules as dimension attributes.

**Rows:** 4 | **Grain:** One row per distribution channel

### dim_order_reason — Reason Code Dimension

Passthrough from silver order_reason. Standardized rejection and reason codes across
source systems.

**Rows:** 9 | **Grain:** One row per reason code

### dim_customer — Conformed Customer Dimension

Deduped from silver order_partner (AG / Sold-To function). Represents the 300 distinct
customers who have placed orders. Key attributes: customer number, name, city, region.

**Rows:** 300 | **Grain:** One row per unique Sold-To customer  
**Key insight:** Derived from partner function aggregation, not a master data source.

### dim_material — Conformed Material Dimension

Union of materials from order_line and quotation_line (both silver). Represents the
800 distinct products/materials across the sales portfolio.

**Rows:** 800 | **Grain:** One row per unique material number

### dim_sales_contract — Contract Dimension

Passthrough from silver sales_contract. Framework agreement attributes for contract-based
order analysis.

**Rows:** 120 | **Grain:** One row per framework agreement

### bridge_order_partner — Partner Function Bridge

Pivoted from silver order_partner to provide Sold-To, Ship-To, and Bill-To partner
numbers per order in a single row. Enables multi-role partner analysis without
self-joining the partner table.

**Rows:** 5,000 | **Grain:** One row per order (pivoted partner functions)

### fact_sales_order_line — Revenue & Volume Fact

The primary analytical fact table. One row per order line item with full dimensional
context: customer (via AG partner), material, sales area, channel, date, and order reason.
Supports revenue analysis (Net_Value, Net_Price), volume (Order_Quantity), and order
composition questions.

**Grain:** One row per order line item  
**Rows:** 14,762  
**Dimensions:** Customer (100%), Material (100%), SalesArea (100%), Channel, Date, OrderReason  
**Measures:** Order_Quantity, Net_Price, Net_Value, Is_Rejected

### fact_otd — On-Time Delivery Fact

Schedule-line grain fact tracking delivery performance. Each row represents a committed
delivery tranche with scheduled date, OTD status, and variance days. The
actual_delivery_date remains NULL (P0 gap) — OTD is currently a schedule-adherence proxy.

**Grain:** One row per order schedule line  
**Rows:** 22,212  
**Dimensions:** Customer (via order), Material (via line), Date  
**Measures:** OTD_Status, Variance_Days, Scheduled_Quantity  
**Known gap:** Actual_Delivery_Date NULL (P0)

### fact_quotation_line — Pipeline & Conversion Fact

Quotation line-item fact for pipeline value, win/loss analysis, and discount tracking.
Customer FK uses Account_Id (cross-source — P2 gap: no Account→Partner cross-reference
exists yet).

**Grain:** One row per quotation line item  
**Rows:** 11,982  
**Dimensions:** Customer (P2 gap), Material, Date  
**Measures:** Quoted_Quantity, Unit_Price, Line_Value, Discount_Percent

### fact_return_line — Reverse Logistics Fact

Return order line-item fact for quality, warranty, and reverse-logistics analysis.
Inherits the order_reason_id vocab gap from silver (P1 — portal DMG/WRONG/WARR codes
don't map to SAP/CRM reason codes).

**Grain:** One row per return line item  
**Rows:** 329  
**Dimensions:** Customer (100%), Date, OrderReason (NULL — P1 gap)  
**Measures:** Return_Quantity, Return_Value, Is_Warranty

### fact_credit_check — Credit Risk Fact

Credit check event fact recording exposure, limits, and approval decisions per order.
Supports credit risk trend analysis and approval-rate monitoring.

**Grain:** One row per credit check event  
**Rows:** 3,104  
**Dimensions:** Customer (100%), SalesArea (via order), Date  
**Measures:** Credit_Limit, Credit_Exposure, Credit_Utilization_Pct, Check_Result

---

## Star Schema Cross-Reference

| Fact \ Dim | dim_date | dim_sales_area | dim_channel | dim_order_reason | dim_customer | dim_material | dim_sales_contract | bridge_order_partner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fact_sales_order_line | ✓ | ✓ | ✓ | ✓* | ✓ | ✓ | | ✓ |
| fact_otd | ✓ | | | | ✓ | ✓ | | |
| fact_quotation_line | ✓ | | | | P2** | ✓ | | |
| fact_return_line | ✓ | | | NULL*** | ✓ | | | |
| fact_credit_check | ✓ | ✓ | | | ✓ | | | |

*\* Order_Reason_Key is NULL when no rejection exists*  
*\*\* Customer_Key cross-source gap (Account_Id vs Partner_Number)*  
*\*\*\* P1 vocab gap — portal reason codes don't map to SAP/CRM*

---

## Source Systems

| System | Bronze Schema | What It Provides | Key Tables |
| --- | --- | --- | --- |
| SAP S/4 (SD module) | `manufacturing_bronze_vibe.sap_sd` | Orders, contracts, schedule lines, credit, OTD | vbak, vbap, vbpa, vbep, veda, veda_item, tvta, tvaut, zcredit_log, zsd_channel_config |
| Salesforce CRM | `manufacturing_bronze_vibe.salesforce_crm` | Quotations, loss reasons | quote, quote_line, loss_reason_ref |
| EDI Gateway | `manufacturing_bronze_vibe.edi_gateway` | Electronic order messages | edi_message_log |
| Returns Portal | `manufacturing_bronze_vibe.returns_portal` | RMA returns | rma_request, rma_line |

---

## Known Limitations

### Active Gaps (prioritized)

| Priority | Entity | Gap | Impact | Unblock Action |
| --- | --- | --- | --- | --- |
| P0 | otd_record / fact_otd | actual_delivery_date = NULL | OTD is schedule-adherence proxy only | Ingest likp/lips from SAP SD |
| P1 | return_order, return_order_line, fact_return_line | order_reason_id = NULL | Can't classify return reasons | Build portal↔SAP/CRM reason code mapping |
| P2 | fact_quotation_line | Customer_Key (cross-source) | Quote→Customer link unresolvable | Build Account_Id↔Partner_Number cross-reference |
| P3 | channel_config, sales_contract | sales_area_id = NULL | Can't link these refs to sales area | Source lacks org/division fields (unfixable without enrichment) |
| P3 | delivery_schedule | 0 rows | No SA-type documents in bronze | Populate when SA documents appear |
| P3 | order | quotation_id ~19.9% | Only converted quotes resolve | Cross-source design (expected) |

### Accepted Exceptions

* **delivery_schedule (0 rows):** The scheduling-agreement document types don't exist in the current bronze source. The entity is correctly defined and will populate when those document types arrive.
* **OTD proxy calculation:** The 45.8% ON_TIME / 54.2% LATE split uses schedule date vs. current date as a proxy. True OTD requires goods-issue confirmation (likp/lips).
* **order_reason_id on returns:** The returns portal vocabulary (DMG, WRONG, WARR) is semantically different from SAP's augru reason codes. A mapping table would resolve this but is out of current scope (HG-SDP-4).

### Deferred Entities (9 blocked)

| Entity | Block Reason |
| --- | --- |
| order_header_condition, order_line_condition | Requires PRCD_ELEMENTS (pricing conditions) |
| order_status_event, order_change, order_block | Requires cdhdr/cdpos (change documents) |
| delivery, delivery_item, shipment, shipment_stage | Requires likp/lips/vttk (delivery/transport) |

---

## Validation

This model includes full validation suites for both layers:

**Silver validation:**
* Per-table narratives: `src/silver/validation/` (17 notebooks)
* Metadata tables: `manufacturing_silver_vibe.sales_order_silver_sdp._validation_*`
* Overall Grade: A (17/17 entities)

**Gold validation:**
* Per-table narratives: `src/gold/validation/` (13 notebooks + scorecard)
* Metadata tables: `manufacturing_silver_vibe.sales_order_gold_sdp._validation_*`
* Job ID: 74728959503728 (deployed, daily)
* Overall Grade: A (13/13 entities, 70 checks — 67 PASS + 3 accepted exceptions)

**Total validated:** 100,294 silver rows + 58,354 gold rows = **158,648 governed rows**
