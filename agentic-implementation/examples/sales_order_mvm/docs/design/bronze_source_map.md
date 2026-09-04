# Bronze Source Coverage Map — `sales_order_mvm`

This document is the authoritative per-table source decision for the `sales_order_mvm` perfect-demo
bronze data generator. Tasks B2–B6 implement what is declared here.

## Deviation levers

The demo exercises three `model_deviation` levers so the generated assessment session demonstrates
all three paths in a single run:

- **DROP-table** — `order_header_condition` and `order_line_condition` receive **no bronze source**.
  The generator emits no `prcd_elements` / `konv`-equivalent tables; the assessment registers these
  as "Blocked" and the deviation block drops them from the target model.
- **TRIM-cols** — `delivery_schedule`, `atp_check`, and `order_configuration` are fully sourced but
  contain a small set of specialist columns (automotive JIT/JIS/Kanban fields; CTP capacity fields;
  deep CPQ characteristics) that the generator emits as present-but-100%-NULL. The assessment's
  null-rate scanner fires `drop_null_columns` on exactly these columns, producing a visible, loggable
  trim event.
- **ADD (net-new)** — `delivery` and `delivery_line` have **no counterpart in the
  pristine vibe model** (the SQL file intentionally omits them). The generator emits `sap_sd.likp`
  and `sap_sd.lips`; the assessment finds them as unmapped bronze sources and the deviation block
  adds both tables. They are the OTD-actuals source: goods-issue date versus confirmed date.

Cross-domain FKs (customer, product_catalog, manufacturing, supply_chain, billing, product_lifecycle)
are **out of scope for this demo** — they are retained as nullable business-key columns with no FK
constraint, exactly as the `model_setup.sql` DEFERRED comments document.

---

## Coverage table

All 16 model tables (from `model_setup.sql`) plus the two ADD tables appear below.

| model_table | bronze_source(s) | intra-domain FK parents | deviation_role | notes |
|---|---|---|---|---|
| `sales_contract` | `sap_sd.vbak` (AUART=MK/WK), `sap_sd.veda` | — | KEEP | Contract header; veda supplies validity/value columns |
| `sales_contract_line` | `sap_sd.vbap` (of contract), `sap_sd.veda_item` | `sales_contract` | KEEP | veda_item carries target_qty/value per line |
| `quotation` | `sap_sd.vbak` (AUART=QT/AG) | `sales_contract` | KEEP | Quotation header; same table as order, different AUART |
| `quotation_line` | `sap_sd.vbap` (of quotation) | `quotation`, `order_line` | KEEP | Line items of quotation docs |
| `order` | `sap_sd.vbak` (AUART=OR/ZOR) | `sales_contract`, `quotation` | KEEP | Core order header — primary demo entity |
| `order_line` | `sap_sd.vbap` | `order`, `sales_contract_line` | KEEP | Line items; most OTD metrics anchor here |
| `order_schedule_line` | `sap_sd.vbep` | `order_line` | KEEP | Confirmed delivery splits (schedule lines) |
| `order_partner` | `sap_sd.vbpa` | `order` | KEEP | Sold-to / ship-to / bill-to / payer partner functions |
| `return_order` | `sap_sd.vbak` (AUART=RE/ZRE) | `order` | KEEP | RMA header; same vbak table, returns doc type |
| `return_order_line` | `sap_sd.vbap` (of return) | `return_order`, `order_line`, `order_schedule_line` | KEEP | Return line items |
| `order_status_event` | `sap_sd.status_log` *(new)* | `order`, `order_line`, `order_schedule_line` | KEEP-NEW | Synthetic change-document log; drives OTD root-cause analytics |
| `atp_check` | `sap_sd.atp_log` *(new)* | `order`, `order_line`, `order_schedule_line` | KEEP-NEW + TRIM-cols | New synthetic ATP event log; CTP capacity columns emitted NULL (see §TRIM below) |
| `delivery_schedule` | `sap_sd.sched_agreement` *(new)* | `sales_contract`, `sales_contract_line`, `order`, `order_line`, `order_schedule_line` | KEEP-NEW + TRIM-cols | New scheduling-agreement log; JIS/Kanban/takt columns emitted NULL (see §TRIM below) |
| `order_configuration` | `sap_sd.cpq_config` *(new)* | `order`, `order_line`, `quotation_line` | KEEP-NEW + TRIM-cols | New CPQ variant-config log; deep characteristic columns emitted NULL (see §TRIM below) |
| `order_header_condition` | — *(no source)* | `order` | DROP-table | SAP KONV/prcd_elements pricing detail — out of demo scope; no bronze emitted |
| `order_line_condition` | — *(no source)* | `order_line` | DROP-table | SAP KONV/prcd_elements pricing detail — out of demo scope; no bronze emitted |
| `delivery` *(ADD)* | `sap_sd.likp` *(new)* | `order` | ADD | Net-new; goods-issue actuals for OTD measurement; LIKP = outbound delivery header |
| `delivery_line` *(ADD)* | `sap_sd.lips` *(new)* | `delivery`, `order_line`, `order_schedule_line` | ADD | Net-new; goods-issue line actuals; LIPS = outbound delivery item |

---

## TRIM column list

These columns exist in `model_setup.sql` for the three TRIM tables. The generator emits them as
present but always NULL. The assessment's null-rate scanner fires `drop_null_columns` on each.

### `delivery_schedule` — JIS / Kanban / takt group (6 columns)

| column | type | why trimmed |
|---|---|---|
| `is_jis` | BOOLEAN | Just-in-Sequence flag — automotive OEM only |
| `is_jit` | BOOLEAN | Just-in-Time flag — automotive OEM only |
| `is_kanban_triggered` | BOOLEAN | Kanban pull signal — automotive OEM only |
| `takt_time_seconds` | DECIMAL(18,2) | Customer takt time — automotive assembly rate |
| `cumulative_ordered_quantity` | DECIMAL(18,2) | Cumulative JIT call-off reconciliation — automotive only |
| `cumulative_delivered_quantity` | DECIMAL(18,2) | Cumulative delivery reconciliation — automotive only |

### `atp_check` — CTP capacity group (5 columns)

| column | type | why trimmed |
|---|---|---|
| `is_ctp_capacity_checked` | BOOLEAN | CTP work-center capacity check flag |
| `work_center_code` | STRING | Work center evaluated during CTP check |
| `replenishment_lead_time_days` | STRING | CTP replenishment lead time for make-to-order |
| `mrp_element_type` | STRING | MRP element type that confirmed ATP supply |
| `supply_source_reference` | STRING | Planned/production order reference from ATP confirmation |

### `order_configuration` — deep CPQ characteristics (5 columns)

| column | type | why trimmed |
|---|---|---|
| `cooling_type` | STRING | Thermal management characteristic — specialized products |
| `hazardous_area_classification` | STRING | ATEX/IECEx/NEC hazardous-area zone — oil & gas only |
| `communication_protocol` | STRING | Fieldbus protocol (PROFINET/EtherNet-IP/Modbus) — integration-specific |
| `software_version` | STRING | Firmware baseline at order time — service/traceability edge case |
| `certification_marks` | STRING | CE/UL/CSA/ATEX marks — compliance deep-cut, country-specific |

---

## New bronze sources required (B2–B6 implement these)

| new bronze table | target model table(s) | basis |
|---|---|---|
| `sap_sd.status_log` | `order_status_event` | Synthetic SAP change-document / status audit log |
| `sap_sd.atp_log` | `atp_check` | Synthetic ATP/CTP check result log |
| `sap_sd.sched_agreement` | `delivery_schedule` | Synthetic scheduling-agreement release log |
| `sap_sd.cpq_config` | `order_configuration` | Synthetic CPQ variant-configuration records |
| `sap_sd.likp` | `delivery` (ADD) | Synthetic outbound delivery header (LIKP) |
| `sap_sd.lips` | `delivery_line` (ADD) | Synthetic outbound delivery line (LIPS) |
