# Validation Summary — Sales Order Domain (Silver)

> Typed validate→document handoff · Generated 2026-09-03
> Consumed by `domain-documentation` for Genie caveats and Model Guide health.

## Per-Entity Grades (Current Run)

| Entity | Tier | Type | Grade | Build Grade | Checks | Notes |
|---|---|---|---|---|---|---|
| sales_contract | 0 | DIM | A | N/A (SDP) | 4/4 PASS | Root entity, 120 rows |
| sales_contract_line | 1 | DIM | A | N/A | 5/5 PASS | FK to sales_contract 0% orphans |
| quotation | 1 | DIM | A | N/A | 4/4 PASS | No intra-domain FKs to validate |
| order | 2 | FACT | A | N/A | 7/7 PASS | INTEGRATION pass, FK joins preserve row count |
| quotation_line | 2 | DIM | A | N/A | 5/5 PASS | FK to quotation 0% orphans |
| order_line | 3 | FACT | A | N/A | 7/7 PASS | FKs to order + sales_contract_line both clean |
| order_partner | 3 | DIM | A | N/A | 5/5 PASS | FK to order 0% orphans |
| return_order | 3 | FACT | A | N/A | 6/6 PASS | INTEGRATION pass |
| delivery | 3 | FACT | A | N/A | 6/6 PASS | INTEGRATION pass |
| credit_check | 3 | FACT | A | N/A | 6/6 PASS | INTEGRATION pass |
| order_schedule_line | 4 | FACT | A | N/A | 6/6 PASS | FK to order_line 0% orphans |
| order_configuration | 4 | FACT | A | N/A | 6/6 PASS | FK to order 0% orphans |
| return_order_line | 4 | FACT | A | N/A | 6/6 PASS | FK to return_order 0% orphans |
| delivery_line | 4 | FACT | A | N/A | 6/6 PASS | FK to delivery 0% orphans |
| atp_check | 5 | FACT | A | N/A | 7/7 PASS | FKs to order + order_line both clean |
| order_status_event | 5 | FACT | A | N/A | 6/6 PASS | INTEGRATION pass |
| delivery_schedule | 5 | FACT | A | N/A | 7/7 PASS | FKs to order + sales_contract both clean |

## Overall: 17/17 Grade A · 99/99 checks PASS · 0 drift alerts

## Gap Deltas

| Status | Count | Description |
|---|---|---|
| DEFERRED | 15 | 12 cross-domain FK gaps (P2) + 2 dropped entities + 1 deferred quotation.sales_contract_id (P3) |
| ACCEPTED | 4 | NULL_SOURCE columns dropped per gap analysis: order_line.abgru, order_line.uepos, order_line.charg, order_schedule_line.lifsp |
| RESOLVED | 0 | No gaps resolved this run (first run) |

## Changed Genie Caveats

- **Cross-domain FKs (12 P2):** account_id, plant_id, sku_id, contract_id, price_list_id are NULL across multiple entities — Genie space should caveat "Cannot drill to customer, plant, product, or pricing dimensions until those domains are built."
- **Deferred intra-domain FK (1 P3):** quotation.sales_contract_id — Genie caveat: "Quotation-to-contract linkage is deferred; queries joining quotation to sales_contract via this FK return no matches."
- **Dropped entities (2 P3):** order_header_condition and order_line_condition not available — caveat "Pricing condition analysis requires SAP KONV ingestion."
- **NULL_SOURCE columns (4 P3, ACCEPTED):** order_line.abgru/uepos/charg, order_schedule_line.lifsp — no Genie caveat needed (columns omitted from DDL).

## Artifacts

| Artifact | Location |
|---|---|
| Validation notebooks (17) | `src/silver/validation/narrative_*` |
| Scorecard notebook | `src/silver/validation/scorecard` |
| Metadata tables (5) | `manufacturing_silver_vibe.sales_order._validation_*`, `_gap_registry` |
| Job YAML | `resources/sales_order_validation.job.yml` (18 tasks, PAUSED) |
| Dashboard | Sales Order Validation Quality (ID: 01f1a757c2cd1aad8f0fdd33227b71f8) |
| State checkpoint | `docs/.pipeline/state/silver/validation_state.md` |
