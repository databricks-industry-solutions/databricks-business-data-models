# Meridian Fluid Controls — Bronze Sample Data Generator

## About Meridian Fluid Controls

Meridian Fluid Controls is a fictional manufacturer of industrial **valves, actuators, positioners, and flow instrumentation**. It sells B2B across three channels — **direct** (OEMs and end-users), **distributor**, and **dealer** — with a segment of **JIT/EDI** automotive and OEM accounts, and a global plant footprint across the US, EU, and APAC. The company is close enough to the silver model's "industrial automation" framing that the fit feels real, which makes the planted gaps land harder: an industry-standard generated model that is roughly 80% right for this business still misses things. Meridian's data is designed to demonstrate that divergence from a generated template is normal, not exceptional.

This synthetic bronze dataset covers 24 months of business activity (2024-07-01 through 2026-06-30), generated with a fixed seed (SEED=42) for reproducibility.

---

## Source-system landscape

| Schema | System | Fidelity | Feeds (silver) |
|---|---|---|---|
| `sap_sd` | SAP S/4HANA SD (ERP of record) | **Raw/cryptic** — SAP-style table names, code columns, dates as `YYYYMMDD` strings, amounts as strings; needs lookup tables | orders, lines, schedule lines, partners, contracts, credit, sales areas + master data |
| `salesforce_crm` | Salesforce CRM | **Clean** — readable snake_case, ISO dates, typed numerics | quotations, quote lines, order reasons (win/loss), account master |
| `edi_gateway` | Homegrown EDI middleware | **Semi-clean** | EDI order messages |
| `returns_portal` | Bolt-on RMA web app | **Own flavor**, semi-clean | returns, return lines |
| `fieldlink` | Field-service app | Clean | Net-new process — no silver home (installed assets, service orders, warranty) |

Note: the customer is mastered in both SAP (`kna1.kunnr`) and Salesforce (`account.sap_kunnr`), reconciled by a cross-reference field. Discovery should notice the dual master.

---

## What this generates

### Tables per schema

| Schema | Tables | Count |
|---|---|---|
| `sap_sd` | `vbak`, `vbap`, `vbep`, `vbpa`, `veda`, `veda_item`, `zcredit_log`, `tvta`, `zsd_channel_config`, `tvaut`, `kna1`, `knvv`, `mara`, `makt`, `t001w`, `tvakt`, `tinct`, `t052u` | 18 |
| `salesforce_crm` | `account`, `opportunity`, `quote`, `quote_line`, `loss_reason_ref` | 5 |
| `edi_gateway` | `edi_message_log`, `trading_partner` | 2 |
| `returns_portal` | `rma_request`, `rma_line`, `rma_reason_code` | 3 |
| `fieldlink` | `installed_asset`, `service_order`, `service_visit`, `warranty_claim` | 4 |
| **Total** | | **32** |

### Actual row counts (from generated output, SEED=42)

| Table | Rows |
|---|---|
| `sap_sd.vbak` (order headers) | 5,000 |
| `sap_sd.vbap` (order lines) | 14,762 |
| `sap_sd.vbep` (schedule lines) | 22,212 |
| `sap_sd.vbpa` (partners) | 15,000 |
| `sap_sd.veda` (contracts) | 120 |
| `sap_sd.veda_item` (contract lines) | 373 |
| `sap_sd.zcredit_log` (credit checks) | 3,104 |
| `sap_sd.kna1` (customer master) | 300 |
| `sap_sd.knvv` (customer sales view) | 300 |
| `sap_sd.mara` (material master) | 400 |
| `sap_sd.makt` (material text) | 400 |
| `sap_sd.t001w` (plants) | 4 |
| `sap_sd.tvta` (sales areas) | 4 |
| `sap_sd.tvakt` (order type text) | 5 |
| `sap_sd.tinct` (incoterms text) | 5 |
| `sap_sd.t052u` (payment terms) | 4 |
| `sap_sd.tvaut` (reason codes) | 8 |
| `sap_sd.zsd_channel_config` (channel config) | 4 |
| `salesforce_crm.account` | 300 |
| `salesforce_crm.opportunity` | 3,500 |
| `salesforce_crm.quote` | 4,000 |
| `salesforce_crm.quote_line` | 11,982 |
| `salesforce_crm.loss_reason_ref` | 4 |
| `edi_gateway.edi_message_log` | 956 |
| `edi_gateway.trading_partner` | 34 |
| `returns_portal.rma_request` | 227 |
| `returns_portal.rma_line` | 329 |
| `returns_portal.rma_reason_code` | 6 |
| `fieldlink.installed_asset` | 3,698 |
| `fieldlink.service_order` | 1,479 |
| `fieldlink.service_visit` | 1,788 |
| `fieldlink.warranty_claim` | 369 |

Realism baked in: order values follow a lognormal distribution; customer concentration follows a Pareto distribution (top ~20% of accounts hold ~60% of volume); OTD degrades in two seasonal crunch windows (late 2024 and late 2025); return rate ~5-8% of shipped orders; referential integrity enforced across all CSVs. SAP tables use raw SAP fidelity (YYYYMMDD string dates, string amounts, code columns requiring lookup joins); Salesforce and FieldLink use clean ISO dates and typed numerics.

---

## How to regenerate

From the `examples/` directory (requires Python 3.9+, pandas 2.x, numpy 2.x, Faker):

```bash
cd examples/setup
python3 -m data_generator.generate_bronze
```

This wipes and rebuilds `examples/setup/data_generator/output/`, then runs the full validation harness. Generation is deterministic — the same command always produces byte-identical CSVs (SEED=42 in `examples/setup/data_generator/config.py`).

> **Reproducibility note:** all numeric/ID/date values come from numpy's `default_rng` (PCG64), which is algorithmically stable across versions. Text values (customer/material names, cities) come from Faker, whose output *can* change between Faker releases. For byte-identical regeneration on a fresh environment, pin the text dependency: `Faker==37.12.0` (the version used to generate the committed data), alongside `pandas>=2,<3` and `numpy>=2,<3`.

To run only the integrity checks against an existing `output/`:

```bash
cd examples/setup
python3 -m data_generator.validate
```

---

## How it lands in Databricks

The ingest step (handled separately, after generation) does the following:

1. Creates a Unity Catalog volume: `meridian_bronze.default._landing`
2. Uploads all CSVs from `examples/setup/data_generator/output/` to `/Volumes/meridian_bronze/default/_landing/<schema>/`
3. Creates 5 source schemas under the catalog `meridian_bronze` (`sap_sd`, `salesforce_crm`, `edi_gateway`, `returns_portal`, `fieldlink`)
4. Runs one `CREATE TABLE AS SELECT * FROM read_files(...)` per CSV, with `inferSchema=false` so raw string quirks (YYYYMMDD dates, string amounts) survive intact into the bronze layer — exactly as a real raw landing zone would behave

The exact CTAS statements are recorded in `examples/setup/ingest/ingest_bronze.sql`.

---

## Target model

This bronze dataset is designed to feed the `meridian_sales_model.sales_order` domain in a later session via the loop skills (assess → build → validate → document). Do not modify the silver model (`meridian_sales_model`) as part of bronze generation.

---

## Related files

- Answer key (graders only — never feed to the loop skills): `examples/planted-divergences.md`
