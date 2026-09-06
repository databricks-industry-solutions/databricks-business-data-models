<!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->

# Sales Order — Domain Narrative

> **Scope note:** `conventions.yml` declares `output_model: hybrid`. The dimensional gold star layer
> is **deferred (Mode B, not yet built)**. This narrative documents the normalized 3NF silver schema
> only: `manufacturing_silver_vibe.sales_order`. Gold documentation will be added once the gold
> pipeline is built and validated.

## Executive Summary

The Sales Order domain is Meridian Manufacturing's operational record of every commercial
commitment — from master sales contract through quotation, order confirmation, physical delivery,
and return. The silver schema (`manufacturing_silver_vibe.sales_order`) comprises 17 normalized
3NF entities totalling approximately 132,275 rows, sourced from three systems: SAP Sales &
Distribution (the dominant source), Salesforce CRM (quotation pipeline), and a Returns Portal
(reverse logistics). Built as a Lakeflow Spark Declarative Pipeline (Materialized Views, full
recompute, SCD Type 1) and deployed to the dev environment in September 2026, the domain
achieved Grade A across all 17 entities in its first validation run (99/99 checks passed).
The model answers questions about order volume and mix, contract coverage, delivery performance,
credit risk exposure, and return rates — as long as analysts remain within the sales domain;
cross-domain dimensions (customer, plant, product catalog, price list) are deferred pending
construction of those domains.

---

## Architecture

```
  Bronze (READ-ONLY)                 Silver 3NF                     Consumers
  ─────────────────────              ──────────────────────────     ──────────────────
  sap_sd_mvm           ──────────►  manufacturing_silver_vibe       Genie Space
    veda, veda_item                    .sales_order                 (natural language)
    vbak, vbap, vbpa                    ┌────────────────────┐
    vbep, likp, lips                    │ 17 Materialized    │      Model Guide
    zcredit_log, atp_log                │ Views (full        │      (live queries)
    status_log, sched_agreement         │ recompute, Type 1) │
    cpq_config                          └────────────────────┘      Validation Suite
                                                                     (17 narrative
  salesforce_crm_mvm   ──────────►      [gold star schema]           notebooks)
    quote, quote_line                    DEFERRED — Mode B

  returns_portal_mvm   ──────────►
    rma_request, rma_line
```

**Architecture pattern:** Normalized 3NF silver (Mode A phase of a planned A→B hybrid). All
entities are Materialized Views; the full dataset is < 25K rows per entity so full recompute on
every pipeline refresh is both safe and simple.

**Load pattern:** Full recompute Materialized View — no incremental merge bookkeeping.

**Schema:** `manufacturing_silver_vibe.sales_order`

**Pipeline:** `sales_order_silver_pipeline` (Lakeflow Spark Declarative Pipeline)

---

## Document Hierarchy

The domain models the end-to-end sales order lifecycle as a hierarchy of commercial documents.
Each tier depends on entities in the tier above for FK resolution.

```
  Tier 0  Sales Contract (120 rows)          — master commercial framework
            └─ Sales Contract Line (373 rows)  — individual commitment lines

  Tier 1  Quotation (4,000 rows)             — pre-sale proposal (Salesforce CRM)
            └─ Quotation Line (11,982 rows)    — individual quoted items

  Tier 2  Order (5,000 rows)                 — confirmed customer purchase order
  ┌──────    ├─ Order Partner (15,000 rows)   — sold-to / ship-to / bill-to roles
  │         └─ Order Line (14,762 rows)       — individual order line items
  │               ├─ Order Schedule Line (22,212 rows)  — split delivery schedules
  │               └─ Order Configuration (2,025 rows)   — CPQ variant config per line
  │
  ├──────  Delivery (3,244 rows)             — outbound shipment document (SAP LE)
  │           ├─ Delivery Line (9,605 rows)   — per-material shipment line
  │           └─ Delivery Schedule (800 rows) — scheduled delivery windows
  │
  ├──────  Return Order (227 rows)           — RMA / reverse logistics document
  │           └─ Return Order Line (329 rows) — individual returned items
  │
  ├──────  Credit Check (3,104 rows)         — credit evaluation event log
  ├──────  ATP Check (12,000 rows)           — availability-to-promise event log
  ├──────  Order Status Event (18,512 rows)  — lifecycle status change log
  └──────  [cross-domain FKs: account_id, plant_id, sku_id — NULL, deferred]
```

The quotation-to-order linkage is resolved intra-domain (quotation_id FK on order). The
quotation-to-sales-contract linkage (`quotation.sales_contract_id`) is deferred — the join
column is present but always NULL in the current load.

---

## Reference Entities

### sales_contract — Master Sales Agreement

The root entity of the domain: a standing commercial agreement between Meridian and a customer
defining total committed volume (`target_quantity`) and value (`target_value`) over a validity
period. With only 120 rows this is a concentrated table — Meridian operates under a small number
of long-running framework contracts against which release orders are placed. Each contract is
identified by a SAP SD contract document number (`contract_number`) and carries a lifecycle status
that gates order promising and ATP eligibility. Source: `sap_sd_mvm.veda`.

**Linked to:** `sales_contract_line`, `order`, `delivery_schedule`
**Key insight:** 120 contracts backing 373 contract lines and 5,000 orders means many orders draw
down against the same framework agreement — a query joining order to sales_contract will fan out
significantly if aggregated at the contract level rather than the order level.

### sales_contract_line — Contract Commitment Line

One row per material/SKU line within a sales contract, capturing the per-line committed quantity
and validity window. The 373 rows (avg ~3 lines per contract) represent the product-level
structure of Meridian's framework commitments. FK to `sales_contract` via direct SHA2 of
`contract_number` — 0% orphans validated. Order lines FK to `sales_contract_line` to track
release-order consumption against contracted commitments. Source: `sap_sd_mvm.veda_item`.

**Linked to:** `sales_contract`, `order_line`
**Key insight:** The ratio of 373 contract lines to 14,762 order lines implies each contract line
is fulfilled by ~40 release orders on average — useful context when aggregating order volume to
contract-line level.

### quotation — Sales Quotation

A pre-sale commercial proposal generated in Salesforce CRM, capturing the quoted price, validity,
and commitment details before a formal purchase order is received. With 4,000 quotations against
5,000 orders, the implied conversion rate is high — most quotations ultimately convert. Quotations
link downstream to orders (resolved via `quotation_id`) but do not yet link upstream to sales
contracts (`sales_contract_id` is present but deferred — always NULL in the current load).
Source: `salesforce_crm_mvm.quote`.

**Linked to:** `quotation_line`, `order`
**Key insight:** The deferred `quotation.sales_contract_id` FK means you cannot currently bridge
from a quotation back to the framework contract that governs it — use `order → sales_contract`
for that join path until the FK is resolved.

### quotation_line — Quoted Line Item

One row per product line within a quotation, capturing quantity, unit price, and discount for each
SKU proposed to the customer. The 11,982 rows (~3 lines per quotation) provide the pre-sale
product mix that can be compared against confirmed order lines to measure quoting accuracy.
FK to `quotation` via direct SHA2 of `quote_id` — 0% orphans validated. Cross-domain FK `sku_id`
(product catalog) is deferred — NULL in current load. Source: `salesforce_crm_mvm.quote_line`.

**Linked to:** `quotation`
**Key insight:** Comparing `quotation_line.unit_price` to `order_line` pricing (once order line
has a price column) will reveal discount drift between quote and confirmed order — a common
analysis the cross-domain product dimension will enable once `sku_id` is resolved.

### order_partner — Order Party Role

Captures the multiple party roles attached to each order: sold-to, ship-to, bill-to, and payer.
With 15,000 partner rows for 5,000 orders, each order averages three partner role records. The
`partner_function_code` (parvw) distinguishes the roles. Cross-domain FK `account_id` is deferred
— the full customer profile requires the Customer domain. Source: `sap_sd_mvm.vbpa`.

**Linked to:** `order`
**Key insight:** Filtering `WHERE partner_function_code = 'WE'` isolates ship-to parties for
delivery geography analysis — even before the Customer domain is built, the partner address
fields provide shipping-point level geographic segmentation.

---

## Transactional Entities

### order — Sales Order Header

The central transactional entity: one row per confirmed customer purchase order, capturing the
commitment date, requested delivery date, order type, total value, and FK linkages to the
quotation and sales contract that preceded it. The 5,000 orders are sourced from SAP SD VBAK
and represent the primary aggregation grain for revenue and volume reporting. FK to both
`quotation` (JOIN-resolved, 0% orphans) and `sales_contract` (JOIN-resolved, 0% orphans). Four
cross-domain FKs (`account_id`, `plant_id`, `contract_id`, `price_list_id`) are NULL pending
construction of those domains. Source: `sap_sd_mvm.vbak`.

**Grain:** One row per sales order (vbeln)
**Linked to:** `sales_contract`, `quotation`, `order_line`, `order_partner`, `delivery`,
`return_order`, `credit_check`, `atp_check`, `order_status_event`
**Measures:** order value, requested delivery date, order type classification
**Known limitations:** `account_id`, `plant_id`, `contract_id`, `price_list_id` are NULL —
no customer or plant drill-through until those domains are built.

### order_line — Sales Order Line Item

One row per product line within a sales order, capturing confirmed quantity, delivery date, and
fulfillment status. The 14,762 lines (~3 per order) are the grain for product-mix and fill-rate
analysis. FK to `order` (direct SHA2, 0% orphans) and to `sales_contract_line` (JOIN-resolved,
0% orphans) — enabling contract-release tracking at the line level. Two accepted NULL columns
(`abgru` rejection reason, `uepos` higher-level item, `charg` batch) were dropped per the gap
analysis (NULL_SOURCE in bronze). Cross-domain FKs `sku_id` (product) is deferred.
Source: `sap_sd_mvm.vbap`.

**Grain:** One row per order + line number (vbeln, posnr)
**Linked to:** `order`, `sales_contract_line`, `order_schedule_line`, `order_configuration`,
`atp_check`, `delivery_line`
**Known limitations:** `sku_id` NULL — no product dimension drill-through yet.

### order_schedule_line — Delivery Schedule Sub-Line

Captures the per-schedule-line split within each order line — SAP SD allows one order line to be
delivered in multiple tranches, each with its own confirmed quantity and scheduled delivery date.
The 22,212 schedule lines (avg 1.5 per order line) indicate that roughly half of all order lines
are split across multiple delivery windows. FK to `order_line` via JOIN-resolution (0% orphans).
The accepted NULL column `lifsp` (delivery block reason) was dropped — NULL_SOURCE in bronze.
Source: `sap_sd_mvm.vbep`.

**Grain:** One row per order + line + schedule number (vbeln, posnr, etenr)
**Linked to:** `order_line`
**Key insight:** Sum `order_schedule_line.confirmed_quantity` grouped by
`scheduled_delivery_date` to build a forward-looking delivery commitment calendar — the
most useful near-term demand signal in this domain.

### order_configuration — CPQ Variant Configuration

Records the CPQ (Configure-Price-Quote) configuration key and selected variant values for
configurable product order lines. The 2,025 rows (~14% of order lines) confirm that a
significant portion of Meridian's orders involve custom-configured products. FK to both
`order` and `order_line` (both JOIN-resolved, 0% orphans). Source: `sap_sd_mvm.cpq_config`.

**Grain:** One row per order + line + configuration key
**Linked to:** `order`, `order_line`
**Key insight:** Cross-reference `order_configuration` counts against `order_line` revenue to
quantify the revenue share of configurable vs. standard product — a useful input for margin
analysis once pricing data is available.

### delivery — Outbound Shipment Document

One row per SAP Logistics Execution delivery document, capturing the physical shipment of goods
against a sales order. The 3,244 deliveries for 5,000 orders implies ~65% of orders have at
least one delivery created — the remainder are likely open orders, future-dated commitments, or
orders blocked at credit or ATP. Key fields: `planned_delivery_date`, `actual_goods_issue_date`,
`shipping_point_code`, `route_code`. FK to `order` via JOIN (0% orphans). Source: `sap_sd_mvm.likp`.

**Grain:** One row per delivery number (vbeln_delivery)
**Linked to:** `order`, `delivery_line`, `delivery_schedule`
**Key insight:** `DATEDIFF(actual_goods_issue_date, planned_delivery_date)` is the primary
on-time delivery metric for this domain — negative values indicate early shipment, positive
values indicate lateness.

### delivery_line — Shipment Line Item

One row per material line within a delivery document, capturing the actual delivered quantity,
batch/lot, and serial number. The 9,605 delivery lines (avg ~3 per delivery) link back to
`order_line` (JOIN-resolved, 0% orphans) enabling order-to-delivery quantity reconciliation.
Cross-domain FK `sku_id` (product catalog) is deferred — NULL in current load.
Source: `sap_sd_mvm.lips`.

**Grain:** One row per delivery + line number (vbeln_delivery, posnr)
**Linked to:** `delivery`, `order_line`
**Key insight:** Comparing `order_line.order_quantity` (once added) to
`SUM(delivery_line.delivered_quantity)` grouped by `order_line_id` reveals under- and
over-delivery — the core fill-rate metric.

### delivery_schedule — Scheduled Delivery Agreement

Records scheduled delivery windows from SAP scheduling agreements, capturing the planned
delivery date, quantity, and route for future fulfilment tranches. The 800 rows link to both
`order` and `sales_contract` (both JOIN-resolved, 0% orphans) — rare dual FK resolution
that enables contract-level delivery commitment tracking. Source: `sap_sd_mvm.sched_agreement`.

**Grain:** One row per order + schedule number (vbeln, schedule_number)
**Linked to:** `order`, `sales_contract`
**Key insight:** `delivery_schedule` is the only transactional entity that directly bridges
order and contract without passing through `order → sales_contract` via the order header —
useful for contract-level forward delivery scheduling reports.

### return_order — Return Merchandise Authorization

Captures return/RMA requests originated through the Returns Portal, recording the return reason,
credit amount, and link to the original order. With 227 returns against ~5,000 orders the implied
return rate is ~4.5% at the order level. FK to `order` via JOIN-resolution (0% orphans).
Source: `returns_portal_mvm.rma_request`.

**Grain:** One row per RMA number
**Linked to:** `order`, `return_order_line`
**Key insight:** Returns Portal data (3 sources) feeds the reverse-logistics view — the Returns
Portal is a separate system from SAP SD, meaning return orders are not visible in the SAP
VBRK/VBRP billing tables; this entity is the only bridge to return credit data in the domain.

### return_order_line — Returned Line Item

One row per material line on a return order, capturing returned quantity and reason code. The
329 lines across 227 RMAs confirms that most returns are single-line. FK to `return_order` via
JOIN-resolution (0% orphans). Source: `returns_portal_mvm.rma_line`.

**Grain:** One row per return order + line
**Linked to:** `return_order`

### credit_check — Credit Evaluation Event

An event log of every credit management check performed during order processing, capturing the
credit limit, exposure before and after the check, order value, check result (pass/fail/override),
and credit control area. The 3,104 check events for 5,000 orders (62% coverage) indicates that
not all orders trigger a credit check — low-value or pre-approved customers may bypass the
check. FK to `order` (direct SHA2, 0% orphans). Cross-domain FK `account_id` is deferred.
Source: `sap_sd_mvm.zcredit_log`.

**Grain:** One row per order + check timestamp (vbeln, check_ts)
**Linked to:** `order`
**Key insight:** Orders with multiple credit check records indicate the order was initially
blocked (failed check), then manually overridden or re-evaluated — a useful signal for
credit risk monitoring.

### atp_check — Availability-to-Promise Event

An event log of ATP (Available-to-Promise) checks performed during order and order-line
processing, capturing the requested date, confirmed date, requested quantity, confirmed
quantity, and check result. The 12,000 ATP check records across order lines provide a rich
history of availability constraints. FK to both `order` and `order_line` (both JOIN-resolved,
0% orphans). Source: `sap_sd_mvm.atp_log`.

**Grain:** One row per order + line + check number (vbeln, posnr, check_number)
**Linked to:** `order`, `order_line`
**Key insight:** `DATEDIFF(confirmed_date, requested_date)` per `order_line_id` measures ATP
date slip — how far out Meridian had to push delivery dates due to material constraints. Grouped
by month this shows seasonal ATP pressure.

### order_status_event — Order Lifecycle Status Log

An event log of all status changes on a sales order — from initial entry through credit check,
delivery, billing, and closure. The 18,512 events across 5,000 orders (avg 3.7 transitions)
capture the full lifecycle of each order. FK to `order` via direct SHA2 (0% orphans).
Source: `sap_sd_mvm.status_log`.

**Grain:** One row per order + event sequence number (vbeln, event_seq)
**Linked to:** `order`
**Key insight:** The status sequence is the primary tool for order cycle time analysis —
`MIN(event_ts) WHERE status = 'ENTRY'` to `MAX(event_ts) WHERE status = 'CLOSED'` gives
end-to-end order cycle time per order.

---

## Entity Relationship Matrix

Parent → child FK relationships. ✓ = intra-domain FK resolved (0% orphans), ✗ = deferred
(cross-domain, NULL), D = deferred intra-domain.

| Child Entity | sales_contract | quotation | order | order_line | delivery | return_order | Notes |
|---|---|---|---|---|---|---|---|
| sales_contract_line | ✓ | | | | | | T0→T1 direct SHA2 |
| quotation_line | | ✓ | | | | | T1→T2 direct SHA2 |
| order | ✓ | ✓ | | | | | T2: JOIN-resolved |
| order_line | | | ✓ | | | | + sales_contract_line ✓ |
| order_partner | | | ✓ | | | | Direct SHA2 |
| order_schedule_line | | | | ✓ | | | JOIN-resolved |
| order_configuration | | | ✓ | ✓ | | | Both JOIN-resolved |
| delivery | | | ✓ | | | | JOIN-resolved |
| delivery_line | | | | ✓ | ✓ | | Both resolved |
| delivery_schedule | ✓ | | ✓ | | | | Both JOIN-resolved |
| return_order | | | ✓ | | | | JOIN-resolved |
| return_order_line | | | | | | ✓ | JOIN-resolved |
| credit_check | | | ✓ | | | | Direct SHA2 |
| atp_check | | | ✓ | ✓ | | | Both JOIN-resolved |
| order_status_event | | | ✓ | | | | Direct SHA2 |
| quotation.sales_contract_id | D | | | | | | Deferred — always NULL |

**Cross-domain FKs (all NULL — deferred):** `account_id`, `plant_id`, `sku_id`,
`contract_id`, `price_list_id` — present in multiple entities but always NULL until the
corresponding Customer, Plant, Product Catalog, and Pricing domains are built.

---

## Source Systems

| System | Bronze Schema | What It Provides | Key Tables |
|---|---|---|---|
| SAP Sales & Distribution | `manufacturing_bronze_vibe.sap_sd_mvm` | Sales contracts, orders, deliveries, credit checks, ATP checks, status events, schedule agreements, CPQ configs | veda, veda_item, vbak, vbap, vbpa, vbep, likp, lips, zcredit_log, atp_log, status_log, sched_agreement, cpq_config |
| Salesforce CRM | `manufacturing_bronze_vibe.salesforce_crm_mvm` | Quotations and quoted line items | quote, quote_line |
| Returns Portal | `manufacturing_bronze_vibe.returns_portal_mvm` | Return merchandise authorizations and return line items | rma_request, rma_line |

All three bronze schemas contain ALL-STRING columns (confirmed by bronze profiling in Phase 1).
Date parsing is mixed: SAP tables use `yyyyMMdd` format for dates (parsed with
`TRY_TO_DATE(col, 'yyyyMMdd')`); Salesforce and Returns Portal use `yyyy-MM-dd`.
The pipeline handles this per-column per-table.

---

## Known Limitations

### Deferred Cross-Domain FKs (P2 — 12 gaps)

Five FK columns are present in multiple entities but always NULL pending construction of the
corresponding domains:

| Column | Entities Affected | Unblocked By |
|---|---|---|
| `account_id` | order, order_partner, quotation, credit_check | Customer domain build |
| `plant_id` | order, order_line | Plant/Facility domain build |
| `sku_id` | order_line, quotation_line, delivery_line | Product Catalog domain build |
| `price_list_id` | quotation | Pricing domain build |
| `contract_id` | order | Resolved internally; may refer to external contract system |

Genie queries involving these columns will return NULL joins — see caveats in the Genie space
instructions.

### Deferred Intra-Domain FK (P3 — 1 gap)

`quotation.sales_contract_id` is present in the schema but always NULL. The join from quotation
back to its governing sales contract cannot be made until this FK is resolved. Use
`order → sales_contract` as the bridge path in the interim.

### Dropped Entities (2)

`order_header_condition` and `order_line_condition` (SAP KONV pricing condition tables) were
excluded from the domain — pricing condition analysis requires a separate ingestion effort for
the SAP KONV structure and was not in scope for the initial build.

### Accepted NULL Columns (4)

Four NULL_SOURCE columns were confirmed all-NULL in bronze and dropped from the DDL per the
gap analysis: `order_line.abgru` (rejection reason), `order_line.uepos` (higher-level item),
`order_line.charg` (batch number), `order_schedule_line.lifsp` (delivery block reason). These
are bronze data gaps, not silver build defects.

---

## Validation

This model includes a full regression suite in `src/silver/validation/`:

- **Per-entity narratives (17):** `src/silver/validation/narrative_{entity}` (SQL-shape notebooks)
- **Scorecard:** `src/silver/validation/scorecard` (aggregates all results)
- **Metadata tables:** `manufacturing_silver_vibe.sales_order._validation_run`,
  `_validation_table_result`, `_validation_check_detail`, `_validation_check_run`,
  `_gap_registry`
- **Dashboard:** Sales Order Validation Quality
  (ID: `01f1a757c2cd1aad8f0fdd33227b71f8`)
- **Scheduled job:** `resources/sales_order_validation.job.yml`

**Current status:** 17/17 Grade A · 99/99 checks PASS · 0 drift alerts (run: 2026-09-03)

All grades and gap deltas in this narrative are sourced from
`docs/.pipeline/handoffs/silver/validation_summary.md` (the typed validate→document handoff),
not from re-reading the live `_validation_*` tables.
