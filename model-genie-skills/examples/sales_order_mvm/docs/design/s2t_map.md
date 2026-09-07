# 2026-09-03 - Sales Order Vibe V3 - Source-to-Target Mapping Report

> **Fresh assessment — prior iterations ignored per user request.**
> Existing schemas (`sales_order_silver_sdp_v3`, `sales_order_gold_sdp`, etc.) noted but NOT
> integrated. No proven mappings inherited.

## Assessment Metadata

| Key | Value |
| --- | --- |
| Customer | Meridian Manufacturing |
| Domain | `sales_order` |
| Metamodel | `manufacturing_mvm_v1._metamodel` (un-prefixed, V3, mvm scope) |
| Output Model | `hybrid` (3NF silver first, dimensional gold downstream) |
| ETL Type | `sdp_pipeline` (Lakeflow Declarative Pipeline) |
| ETL Language | SQL |
| Model Edits | +3 NET-NEW (delivery, delivery_line, credit_check); -2 DROPPED (order_header_condition, order_line_condition) |
| Buildable Entities | 17 |

> Target Table = metamodel-native name; Built Name = after `conventions.yml` `output_model` —
> for `hybrid` silver, the built name equals the metamodel product name (normalized 3NF).

---

## Bronze Type Profile

**All-STRING bronze — full type casting required.**

| Source System | Schema | Tables | All STRING? |
| --- | --- | --- | --- |
| SAP S/4HANA SD | `sap_sd_mvm` | 24 | YES |
| Salesforce CRM | `salesforce_crm_mvm` | 5 | YES |
| Returns Portal | `returns_portal_mvm` | 3 | YES |

### Date Formats

| Source System | Date Columns | Observed Format | Cast Mask |
| --- | --- | --- | --- |
| `sap_sd_mvm` (traditional) | erdat, vdatu, edatu, vbegdat, venddat, lfdat | `yyyyMMdd` | `TRY_TO_DATE(col, 'yyyyMMdd')` |
| `sap_sd_mvm` (custom) | check_timestamp, event_timestamp | `yyyy-MM-dd` | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |
| `salesforce_crm_mvm` | quote_date, valid_until, created_date | `yyyy-MM-dd` | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |
| `returns_portal_mvm` | rma_date | `yyyy-MM-dd` | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |

### NULL_SOURCE Columns (20 total across 5 entities)

| Source Table | Columns | Count | Note |
| --- | --- | --- | --- |
| `vbap` | abgru, uepos, charg | 3 | No rejected/sub-items/batches |
| `vbep` | lifsp | 1 | No schedule line blocks |
| `atp_log` | is_ctp_capacity_checked, work_center_code, replenishment_lead_time_days, mrp_element_type, supply_source_reference | 5 | No CTP/MRP integration |
| `cpq_config` | cooling_type, hazardous_area_classification, communication_protocol, software_version, certification_marks | 5 | Industrial configs not populated |
| `sched_agreement` | is_jis, is_jit, is_kanban_triggered, takt_time_seconds, cumulative_ordered_quantity, cumulative_delivered_quantity | 6 | No JIT/cumulative data |

Null disposition: **keep** (global default). Keep/drop gate at Completion Self-Audit.

---

## Cross-Domain FK Availability

All 12 cross-domain parent domains modeled but not yet built → **all Deferred**.

| Domain | Parent Table | Referencing Entities | Grade |
| --- | --- | --- | --- |
| manufacturing | plant | order, order_line, atp_check, delivery_schedule, order_status_event, sales_contract_line | Deferred |
| customer | account | order, quotation, return_order, credit_check | Deferred |
| product_catalog | sku | atp_check, delivery_schedule, order_line, quotation_line, sales_contract_line, delivery_line | Deferred |
| product_lifecycle | part, bom, product_specification, ecn | order_configuration, order_line, quotation_line, return_order_line | Deferred |
| billing | contract | order | Deferred |
| pricing | price_list, list_price | order, quotation, quotation_line | Deferred |
| supply_chain | demand_plan | delivery_schedule | Deferred |
| workforce | employee | order_status_event | Deferred |

---

## Load Order

| Tier | Entities |
| --- | --- |
| 0 | sales_contract |
| 1 | sales_contract_line, quotation |
| 2 | order, quotation_line |
| 3 | order_line, order_partner, return_order, delivery, credit_check |
| 4 | order_schedule_line, order_configuration, return_order_line, delivery_line |
| 5 | atp_check, order_status_event, delivery_schedule |

All entities → **MV (Materialized View)** in SDP pipeline. All-STRING bronze, no typed
timestamps, Step 2.6.0 fast-exit → full recompute on each refresh.

---

## Per-Entity Source-to-Target Mapping

### Tier 0

#### 1. `sales_contract` — Master (contract_delivery)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.veda` (120 rows)
**Natural key**: `vbeln` — unique confirmed
**Key derivation**: `SHA2(CAST(vbeln AS STRING), 256)` → `sales_contract_id`

**Column mapping** (key columns):

| Target Column | Type | Source | Source Column | Transformation | Gap? |
| --- | --- | --- | --- | --- | --- |
| sales_contract_id | BIGINT | — | — | Surrogate PK | Derived |
| contract_number | STRING | veda | vbeln | Direct | No |
| customer_account_number | STRING | veda | kunnr | Direct | No |
| distribution_channel_code | STRING | veda | vtweg | Direct | No |
| contract_type_code | STRING | veda | kbtyp | Direct | No |
| valid_from | DATE | veda | vbegdat | TRY_TO_DATE(col,'yyyyMMdd') | No |
| valid_to | DATE | veda | venddat | TRY_TO_DATE(col,'yyyyMMdd') | No |
| target_quantity | DECIMAL(18,4) | veda | zmeng | CAST to decimal | No |
| target_value | DECIMAL(18,2) | veda | target_val | CAST to decimal | No |
| contract_status | STRING | veda | vstat | Direct | No |
| ~26 remaining | various | — | — | No bronze source | GAP |

**Load strategy**: MV — 120 rows, all-STRING.
**Grade: Partial** — 9/36 cols sourced. Core contract grain + dates + amounts covered.

---

### Tier 1

#### 2. `sales_contract_line` — Master (contract_delivery)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.veda_item` (373 rows)
**Natural key**: `vbeln + posnr` — unique confirmed
**Key derivation**: `SHA2(CONCAT_WS('|', vbeln, posnr), 256)` → `sales_contract_line_id`
**FK**: sales_contract_id → sales_contract via vbeln

**Column mapping** (key columns):

| Target Column | Type | Source | Source Column | Transformation | Gap? |
| --- | --- | --- | --- | --- | --- |
| sales_contract_line_id | BIGINT | — | — | Surrogate PK | Derived |
| sales_contract_id | BIGINT | — | — | FK → sales_contract | Derived |
| contract_number | STRING | veda_item | vbeln | Direct | No |
| line_number | STRING | veda_item | posnr | Direct | No |
| sku_code | STRING | veda_item | matnr | Direct | No |
| target_quantity | DECIMAL(18,4) | veda_item | zmeng | CAST | No |
| target_value | DECIMAL(18,2) | veda_item | target_val | CAST | No |
| unit_price | DECIMAL(18,4) | veda_item | netpr | CAST | No |
| ~29 remaining | various | — | — | No bronze source | GAP |

**Load strategy**: MV — 373 rows.
**Grade: Partial** — 6/37 cols sourced. Minimal item data.

---

#### 3. `quotation` — Transactional (pricing_management)

**Source**: `manufacturing_bronze_vibe.salesforce_crm_mvm.quote` (4,000 rows)
**Natural key**: `quote_id` — unique confirmed
**Key derivation**: `SHA2(CAST(quote_id AS STRING), 256)` → `quotation_id`
**FK**: sales_contract_id → sales_contract (if linked)

**Column mapping** (key columns):

| Target Column | Type | Source | Source Column | Transformation | Gap? |
| --- | --- | --- | --- | --- | --- |
| quotation_id | BIGINT | — | — | Surrogate PK | Derived |
| quotation_number | STRING | quote | quote_number | Direct | No |
| quote_date | DATE | quote | quote_date | TRY_TO_DATE(col,'yyyy-MM-dd') | No |
| valid_until | DATE | quote | valid_until | TRY_TO_DATE(col,'yyyy-MM-dd') | No |
| total_amount | DECIMAL(18,2) | quote | total_amount | CAST | No |
| currency_code | STRING | quote | currency | Direct | No |
| status | STRING | quote | status | Direct | No |
| conversion_probability | DECIMAL(5,2) | quote | conversion_probability | CAST | No |
| converted_order_number | STRING | quote | converted_order_number | Direct | No |
| sales_rep | STRING | quote | sales_rep | Direct | No |
| account_id | BIGINT | — | — | FK → customer.account via account_id | Derived |
| opportunity_id | STRING | quote | opportunity_id | Direct (SFDC ref) | No |
| ~26 remaining | various | — | — | No bronze source | GAP |

**Load strategy**: MV — 4,000 rows.
**Grade: Partial** — 12/38 cols sourced.

---

### Tier 2

#### 4. `order` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.vbak` (5,000 rows)
**Natural key**: `vbeln` — unique confirmed
**Key derivation**: `SHA2(CAST(vbeln AS STRING), 256)` → `order_id`

**Column mapping** (18 direct + 7 derived + ~13 GAP = 38 total):

| Target Column | Type | Source | Source Column | Transformation | Gap? |
| --- | --- | --- | --- | --- | --- |
| order_id | BIGINT | — | — | Surrogate PK | Derived |
| order_number | STRING | vbak | vbeln | Direct | No |
| order_date | DATE | vbak | erdat | TRY_TO_DATE(col,'yyyyMMdd') | No |
| requested_delivery_date | DATE | vbak | vdatu | TRY_TO_DATE(col,'yyyyMMdd') | No |
| document_date | DATE | vbak | audat | TRY_TO_DATE(col,'yyyyMMdd') | No |
| net_value | DECIMAL(18,2) | vbak | netwr | CAST | No |
| currency_code | STRING | vbak | waerk | Direct | No |
| order_type_code | STRING | vbak | auart | Direct | No |
| distribution_channel_code | STRING | vbak | vtweg | Direct | No |
| sales_organization_code | STRING | vbak | vkorg | Direct | No |
| division_code | STRING | vbak | spart | Direct | No |
| customer_account_number | STRING | vbak | kunnr | Direct | No |
| plant_code | STRING | vbak | werks | Direct | No |
| incoterms_code | STRING | vbak | inco1 | Direct | No |
| payment_terms_code | STRING | vbak | zterm | Direct | No |
| overall_status | STRING | vbak | gbstk | Direct | No |
| rejection_reason_code | STRING | vbak | augru | Direct | No |
| customer_po_number | STRING | vbak | bstnk | Direct | No |
| shipping_condition_code | STRING | vbak | vsbed | Direct | No |
| account_id | BIGINT | — | — | FK surrogate (Deferred) | Derived |
| plant_id | BIGINT | — | — | FK surrogate (Deferred) | Derived |
| quotation_id | BIGINT | — | — | FK intra-domain | Derived |
| sales_contract_id | BIGINT | — | — | FK intra-domain | Derived |
| channel_type | STRING | — | — | Enrichable from zsd_channel_config | GAP |
| ~9 remaining | various | — | — | No bronze source | GAP |

**FK resolution**:

| FK Column | Parent | Domain | Resolution |
| --- | --- | --- | --- |
| quotation_id | quotation | intra | LEFT JOIN on converted_order_number |
| sales_contract_id | sales_contract | intra | LEFT JOIN on contract ref |
| account_id | account | cross (customer) | Deferred |
| plant_id | plant | cross (manufacturing) | Deferred |

**Load strategy**: MV — 5,000 rows.
**Grade: Partial** — 18/38 cols sourced. Gap cols are enrichment and cross-system refs.

---

#### 5. `quotation_line` — Transactional (pricing_management)

**Source**: `manufacturing_bronze_vibe.salesforce_crm_mvm.quote_line` (11,982 rows)
**Natural key**: `quote_line_id` — unique confirmed
**Key derivation**: `SHA2(CAST(quote_line_id AS STRING), 256)` → `quotation_line_id`
**FKs**: quotation_id → quotation; converted_order_line_id → order_line

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| quotation_line_id | BIGINT | — | — | Derived |
| quotation_id | BIGINT | — | — | FK intra | 
| line_number | STRING | quote_line | line_number | No |
| sku_code | STRING | quote_line | sku_code | No |
| quantity | DECIMAL(18,4) | quote_line | quantity | No |
| uom | STRING | quote_line | uom | No |
| list_price | DECIMAL(18,4) | quote_line | list_price | No |
| discount_pct | DECIMAL(5,2) | quote_line | discount_pct | No |
| net_price | DECIMAL(18,4) | quote_line | net_price | No |
| net_value | DECIMAL(18,2) | quote_line | net_value | No |
| product_group | STRING | quote_line | product_group | No |
| ~29 remaining | various | — | — | GAP |

**Load strategy**: MV — 11,982 rows.
**Grade: Partial** — 12/41 cols sourced.

---

### Tier 3

#### 6. `order_line` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.vbap` (14,762 rows)
**Natural key**: `vbeln + posnr` — unique confirmed
**FKs**: order_id → order; sales_contract_line_id → sales_contract_line

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| order_line_id | BIGINT | — | — | Derived |
| order_id | BIGINT | — | — | FK intra |
| order_number | STRING | vbap | vbeln | No |
| line_number | STRING | vbap | posnr | No |
| sku_code | STRING | vbap | matnr | No |
| plant_code | STRING | vbap | werks | No |
| order_quantity | DECIMAL(18,4) | vbap | kwmeng | No |
| quantity_uom | STRING | vbap | vrkme | No |
| unit_price | DECIMAL(18,4) | vbap | netpr | No |
| net_value | DECIMAL(18,2) | vbap | netwr | No |
| item_category_code | STRING | vbap | pstyv | No |
| serial_number_profile | STRING | vbap | serail | No |
| rejection_reason_code | STRING | vbap | abgru | NULL_SOURCE |
| higher_level_item | STRING | vbap | uepos | NULL_SOURCE |
| batch_number | STRING | vbap | charg | NULL_SOURCE |
| ~27 remaining | various | — | — | GAP |

**Load strategy**: MV — 14,762 rows.
**Grade: Partial** — 13/42 cols; 3 NULL_SOURCE.

---

#### 7. `order_partner` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.vbpa` (15,000 rows)
**Natural key**: `vbeln + parvw` — unique confirmed

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| order_partner_id | BIGINT | — | — | Derived |
| order_id | BIGINT | — | — | FK intra |
| order_number | STRING | vbpa | vbeln | No |
| partner_function_code | STRING | vbpa | parvw | No |
| partner_customer_number | STRING | vbpa | kunnr | No |
| partner_name | STRING | vbpa | name1 | No |
| country_code | STRING | vbpa | land1 | No |
| city | STRING | vbpa | ort01 | No |
| postal_code | STRING | vbpa | pstlz | No |
| address_number | STRING | vbpa | adrnr | No |
| function_description | STRING | vbpa | func_desc | No |
| ~28 remaining | various | — | — | GAP |

**Load strategy**: MV — 15,000 rows.
**Grade: Partial** — 9/39 cols sourced.

---

#### 8. `return_order` — Transactional (contract_delivery)

**Source**: `manufacturing_bronze_vibe.returns_portal_mvm.rma_request` (227 rows)
**Natural key**: `rma_number` — unique confirmed
**FKs**: original_order_id → order

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| return_order_id | BIGINT | — | — | Derived |
| rma_number | STRING | rma_request | rma_number | No |
| original_order_number | STRING | rma_request | original_order_number | No |
| customer_account_number | STRING | rma_request | customer_kunnr | No |
| rma_date | DATE | rma_request | rma_date | No |
| reason_code | STRING | rma_request | reason_code | No |
| status | STRING | rma_request | status | No |
| return_plant_code | STRING | rma_request | return_plant | No |
| credit_memo_required | STRING | rma_request | credit_memo_required | No |
| inspection_required | STRING | rma_request | inspection_required | No |
| total_return_value | DECIMAL(18,2) | rma_request | total_return_value | No |
| ~29 remaining | various | — | — | GAP |

**Load strategy**: MV — 227 rows.
**Grade: Partial** — 10/40 cols sourced.

---

#### 9. `delivery` — Transactional (contract_delivery) — NET-NEW

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.likp` (3,244 rows)
**Natural key**: `vbeln_delivery` — unique confirmed
**Origin**: NET-NEW (deviation) — discovered from bronze, user confirmed at Phase 2C.

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| delivery_id | BIGINT | — | — | Derived |
| delivery_number | STRING | likp | vbeln_delivery | No |
| order_id | BIGINT | — | — | FK intra via vbeln_order |
| order_number | STRING | likp | vbeln_order | No |
| planned_delivery_date | DATE | likp | lfdat | No |
| actual_goods_issue_date | DATE | likp | wadat_ist | No |
| shipping_point_code | STRING | likp | vstel | No |
| transportation_type_code | STRING | likp | traty | No |
| route_code | STRING | likp | route | No |
| source_system | STRING | likp | source_system | No |

**Load strategy**: MV — 3,244 rows.
**Grade: Full** — All defined attributes have confirmed sources.

---

#### 10. `credit_check` — Transactional (order_processing) — NET-NEW

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.zcredit_log` (3,104 rows)
**Natural key**: `vbeln + check_ts` — unique confirmed
**Origin**: NET-NEW (deviation) — discovered from bronze, user confirmed at Phase 2C.

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| credit_check_id | BIGINT | — | — | Derived |
| order_id | BIGINT | — | — | FK intra via vbeln |
| order_number | STRING | zcredit_log | vbeln | No |
| customer_account_number | STRING | zcredit_log | kunnr | No |
| check_timestamp | TIMESTAMP | zcredit_log | check_ts | No |
| check_type | STRING | zcredit_log | check_type | No |
| credit_limit | DECIMAL(18,2) | zcredit_log | klimk | No |
| exposure_before | DECIMAL(18,2) | zcredit_log | exp_before | No |
| order_value | DECIMAL(18,2) | zcredit_log | order_val | No |
| exposure_after | DECIMAL(18,2) | zcredit_log | exp_after | No |
| check_result | STRING | zcredit_log | result | No |
| credit_control_area | STRING | zcredit_log | kkber | No |
| credit_control_point | STRING | zcredit_log | ctlpc | No |

**Load strategy**: MV — 3,104 rows.
**Grade: Full** — All defined attributes have confirmed sources.

---

### Tier 4

#### 11. `order_schedule_line` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.vbep` (22,212 rows)
**Natural key**: `vbeln + posnr + etenr` — unique confirmed
**FKs**: order_line_id → order_line

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| order_schedule_line_id | BIGINT | — | — | Derived |
| order_number | STRING | vbep | vbeln | No |
| line_number | STRING | vbep | posnr | No |
| schedule_line_number | STRING | vbep | etenr | No |
| scheduled_delivery_date | DATE | vbep | edatu | No |
| goods_issue_date | DATE | vbep | wadat | No |
| confirmed_quantity | DECIMAL(18,4) | vbep | bmeng | No |
| ordered_quantity | DECIMAL(18,4) | vbep | wmeng | No |
| delivery_block | STRING | vbep | lifsp | NULL_SOURCE |
| ~29 remaining | various | — | — | GAP |

**Load strategy**: MV — 22,212 rows.
**Grade: Partial** — 8/38 cols; 1 NULL_SOURCE.

---

#### 12. `order_configuration` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.cpq_config` (2,025 rows)
**Natural key**: `vbeln + posnr + configuration_key` — unique confirmed

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| order_configuration_id | BIGINT | — | — | Derived |
| order_number | STRING | cpq_config | vbeln | No |
| line_number | STRING | cpq_config | posnr | No |
| configuration_key | STRING | cpq_config | configuration_key | No |
| configuration_status | STRING | cpq_config | configuration_status | No |
| bom_explosion_status | STRING | cpq_config | bom_explosion_status | No |
| configuration_source | STRING | cpq_config | configuration_source | No |
| configuration_date | DATE | cpq_config | configuration_date | No |
| source_system | STRING | cpq_config | source_system | No |
| cooling_type | STRING | cpq_config | cooling_type | NULL_SOURCE |
| hazardous_area_classification | STRING | cpq_config | hazardous_area_classification | NULL_SOURCE |
| communication_protocol | STRING | cpq_config | communication_protocol | NULL_SOURCE |
| software_version | STRING | cpq_config | software_version | NULL_SOURCE |
| certification_marks | STRING | cpq_config | certification_marks | NULL_SOURCE |
| ~30 remaining | various | — | — | GAP |

**Load strategy**: MV — 2,025 rows.
**Grade: Partial** — 13/44 cols; 5 NULL_SOURCE.

---

#### 13. `return_order_line` — Transactional (contract_delivery)

**Source**: `manufacturing_bronze_vibe.returns_portal_mvm.rma_line` (329 rows)
**Natural key**: `rma_line_id` — unique confirmed
**FKs**: return_order_id → return_order; original_order_line_id → order_line

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| return_order_line_id | BIGINT | — | — | Derived |
| rma_line_id | STRING | rma_line | rma_line_id | No |
| rma_number | STRING | rma_line | rma_number | No |
| line_number | STRING | rma_line | line_number | No |
| sku_code | STRING | rma_line | sku_code | No |
| returned_quantity | DECIMAL(18,4) | rma_line | returned_quantity | No |
| uom | STRING | rma_line | uom | No |
| reason_code | STRING | rma_line | reason_code | No |
| inspection_result | STRING | rma_line | inspection_result | No |
| credit_value | DECIMAL(18,2) | rma_line | credit_value | No |
| restocking_fee | DECIMAL(18,2) | rma_line | restocking_fee | No |
| is_warranty | STRING | rma_line | is_warranty | No |
| ~26 remaining | various | — | — | GAP |

**Load strategy**: MV — 329 rows.
**Grade: Partial** — 11/38 cols sourced.

---

#### 14. `delivery_line` — Transactional (contract_delivery) — NET-NEW

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.lips` (9,605 rows)
**Natural key**: `vbeln_delivery + posnr` — unique confirmed
**Origin**: NET-NEW (deviation).
**FKs**: delivery_id → delivery; order_line_id → order_line

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| delivery_line_id | BIGINT | — | — | Derived |
| delivery_number | STRING | lips | vbeln_delivery | No |
| line_number | STRING | lips | posnr | No |
| order_number | STRING | lips | vbeln_order | No |
| order_line_number | STRING | lips | posnr_order | No |
| delivered_quantity | DECIMAL(18,4) | lips | lfimg | No |
| sku_code | STRING | lips | matnr | No |
| batch_number | STRING | lips | charg | No |
| serial_number | STRING | lips | serial | No |
| source_system | STRING | lips | source_system | No |

**Load strategy**: MV — 9,605 rows.
**Grade: Full** — All defined attributes have confirmed sources.

---

### Tier 5

#### 15. `atp_check` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.atp_log` (12,000 rows)
**Natural key**: `vbeln + posnr + check_number` — unique confirmed

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| atp_check_id | BIGINT | — | — | Derived |
| order_number | STRING | atp_log | vbeln | No |
| line_number | STRING | atp_log | posnr | No |
| check_number | STRING | atp_log | check_number | No |
| check_status | STRING | atp_log | check_status | No |
| requested_quantity | DECIMAL(18,4) | atp_log | requested_quantity | No |
| confirmed_quantity | DECIMAL(18,4) | atp_log | confirmed_quantity | No |
| earliest_confirmation_date | DATE | atp_log | earliest_confirmation_date | No |
| check_timestamp | TIMESTAMP | atp_log | check_timestamp | No |
| check_type | STRING | atp_log | check_type | No |
| source_system | STRING | atp_log | source_system | No |
| is_ctp_capacity_checked | BOOLEAN | atp_log | is_ctp_capacity_checked | NULL_SOURCE |
| work_center_code | STRING | atp_log | work_center_code | NULL_SOURCE |
| replenishment_lead_time_days | INT | atp_log | replenishment_lead_time_days | NULL_SOURCE |
| mrp_element_type | STRING | atp_log | mrp_element_type | NULL_SOURCE |
| supply_source_reference | STRING | atp_log | supply_source_reference | NULL_SOURCE |
| ~23 remaining | various | — | — | GAP |

**Load strategy**: MV — 12,000 rows.
**Grade: Partial** — 15/39 cols; 5 NULL_SOURCE.

---

#### 16. `order_status_event` — Transactional (order_processing)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.status_log` (18,512 rows)
**Natural key**: `vbeln + event_seq` — unique confirmed

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| order_status_event_id | BIGINT | — | — | Derived |
| order_number | STRING | status_log | vbeln | No |
| event_sequence | STRING | status_log | event_seq | No |
| event_type | STRING | status_log | event_type | No |
| event_timestamp | TIMESTAMP | status_log | event_timestamp | No |
| previous_status | STRING | status_log | previous_status | No |
| new_status | STRING | status_log | new_status | No |
| otd_flag | STRING | status_log | otd_flag | No |
| confirmed_delivery_date | DATE | status_log | confirmed_delivery_date | No |
| actual_goods_issue_date | DATE | status_log | actual_goods_issue_date | No |
| triggered_by_type | STRING | status_log | triggered_by_type | No |
| source_system | STRING | status_log | source_system | No |
| ~22 remaining | various | — | — | GAP |

**Load strategy**: MV — 18,512 rows.
**Grade: Partial** — 11/34 cols sourced. Event grain confirmed.

---

#### 17. `delivery_schedule` — Master (contract_delivery)

**Source**: `manufacturing_bronze_vibe.sap_sd_mvm.sched_agreement` (800 rows)
**Natural key**: `vbeln + schedule_number` — unique confirmed

| Target Column | Type | Source | Source Column | Gap? |
| --- | --- | --- | --- | --- |
| delivery_schedule_id | BIGINT | — | — | Derived |
| order_number | STRING | sched_agreement | vbeln | No |
| schedule_number | STRING | sched_agreement | schedule_number | No |
| contract_number | STRING | sched_agreement | contract_number | No |
| schedule_type | STRING | sched_agreement | schedule_type | No |
| schedule_status | STRING | sched_agreement | schedule_status | No |
| horizon_start_date | DATE | sched_agreement | horizon_start_date | No |
| horizon_end_date | DATE | sched_agreement | horizon_end_date | No |
| open_quantity | DECIMAL(18,4) | sched_agreement | open_quantity | No |
| quantity_unit | STRING | sched_agreement | quantity_unit | No |
| source_system | STRING | sched_agreement | source_system | No |
| is_jis | BOOLEAN | sched_agreement | is_jis | NULL_SOURCE |
| is_jit | BOOLEAN | sched_agreement | is_jit | NULL_SOURCE |
| is_kanban_triggered | BOOLEAN | sched_agreement | is_kanban_triggered | NULL_SOURCE |
| takt_time_seconds | INT | sched_agreement | takt_time_seconds | NULL_SOURCE |
| cumulative_ordered_quantity | DECIMAL(18,4) | sched_agreement | cumulative_ordered_quantity | NULL_SOURCE |
| cumulative_delivered_quantity | DECIMAL(18,4) | sched_agreement | cumulative_delivered_quantity | NULL_SOURCE |
| ~29 remaining | various | — | — | GAP |

**Load strategy**: MV — 800 rows.
**Grade: Partial** — 16/46 cols; 6 NULL_SOURCE.

---

### DROPPED Entities

#### `order_header_condition`
**Disposition**: DROPPED (deviation) — pricing conditions not part of business processes.
**Grade**: Blocked (no SAP KONV source). **Recovery**: Ingest SAP KONV if needed.

#### `order_line_condition`
**Disposition**: DROPPED (deviation) — pricing conditions not part of business processes.
**Grade**: Blocked (no SAP KONV source). **Recovery**: Ingest SAP KONV if needed.

---

## Summary Scorecard

| # | Target Table | Built Name (hybrid silver) | Grade | Primary Source | Rows | Load | Key Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | sales_contract | sales_contract | Partial | veda | 120 | MV | 9/36 cols |
| 2 | sales_contract_line | sales_contract_line | Partial | veda_item | 373 | MV | 6/37 cols |
| 3 | quotation | quotation | Partial | quote | 4,000 | MV | 12/38 cols |
| 4 | order | order | Partial | vbak | 5,000 | MV | 18/38 cols |
| 5 | quotation_line | quotation_line | Partial | quote_line | 11,982 | MV | 12/41 cols |
| 6 | order_line | order_line | Partial | vbap | 14,762 | MV | 13/42; 3 NULL_SOURCE |
| 7 | order_partner | order_partner | Partial | vbpa | 15,000 | MV | 9/39 cols |
| 8 | return_order | return_order | Partial | rma_request | 227 | MV | 10/40 cols |
| 9 | delivery | delivery | Full | likp | 3,244 | MV | NET-NEW (deviation) |
| 10 | credit_check | credit_check | Full | zcredit_log | 3,104 | MV | NET-NEW (deviation) |
| 11 | order_schedule_line | order_schedule_line | Partial | vbep | 22,212 | MV | 8/38; 1 NULL_SOURCE |
| 12 | order_configuration | order_configuration | Partial | cpq_config | 2,025 | MV | 13/44; 5 NULL_SOURCE |
| 13 | return_order_line | return_order_line | Partial | rma_line | 329 | MV | 11/38 cols |
| 14 | delivery_line | delivery_line | Full | lips | 9,605 | MV | NET-NEW (deviation) |
| 15 | atp_check | atp_check | Partial | atp_log | 12,000 | MV | 15/39; 5 NULL_SOURCE |
| 16 | order_status_event | order_status_event | Partial | status_log | 18,512 | MV | 11/34 cols |
| 17 | delivery_schedule | delivery_schedule | Partial | sched_agreement | 800 | MV | 16/46; 6 NULL_SOURCE |
| -- | order_header_condition | *(dropped)* | Blocked | -- | 0 | -- | DROPPED (deviation) |
| -- | order_line_condition | *(dropped)* | Blocked | -- | 0 | -- | DROPPED (deviation) |

**Totals: 3 Full, 14 Partial, 2 Blocked (DROPPED)**
**Load: 17 MV (Materialized View), 0 Streaming Table, 0 AUTO CDC**
**NULL_SOURCE: 20 columns across 5 entities (disposition: keep)**

---

## Ingestion Ask Table

No P0 ingestion asks. The two Blocked entities were DROPPED by business coherence.

| Priority | Table | System | Unblocks |
| --- | --- | --- | --- |
| *(none)* | | | |

Recovery: Ingest SAP KONV if pricing conditions become needed.

---

## Gold Downstream Notes (Hybrid Mode)

This is the **silver 3NF** assessment. The dimensional gold star will be designed in a
**separate Mode B pass** after the silver build lands.

**Preliminary fact/dim preview:**

| Silver Entity | Expected Gold Role |
| --- | --- |
| order | Fact header / degenerate dim |
| order_line | Fact (core grain) |
| order_schedule_line | Fact (sub-line) |
| order_partner | Bridge |
| order_status_event | Fact (event ledger) |
| order_configuration | Fact (config per line) |
| atp_check | Fact (ATP events) |
| quotation / quotation_line | Fact pair |
| return_order / return_order_line | Fact pair |
| sales_contract / sales_contract_line | Dim / Bridge |
| delivery_schedule | Dim / Bridge |
| delivery / delivery_line | Fact pair |
| credit_check | Fact |

**Conformed dimensions** (Mode B): dim_customer, dim_material, dim_plant, dim_date,
dim_sales_area, dim_channel.
