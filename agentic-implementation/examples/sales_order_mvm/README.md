# sales_order (MVM) — the worked end-to-end example (silver)

The **showcase** domain: a tight, 16-table `sales_order` vibe model where the Meridian bronze
**nearly fully fits** the model, so the assess → build → validate → document loop runs clean. This
folder ships **both** the self-contained inputs (so you can reproduce it) **and a committed real
run** — the actual assess→build→validate→document output, checked in under `docs/`, `src/`,
`resources/`, and the Model Guide + dashboard.

**Scope of the committed run: silver only.** The run built and validated the normalized 3NF silver
layer — **17 tables, all Grade A, 99/99 checks PASS, 0 FK orphans**. The dimensional **gold star is
*assessed and designed* but not built** in this run (see
[`docs/design/gold_layer_assessment.md`](docs/design/gold_layer_assessment.md) and
[`docs/design/metric_views_requirements.md`](docs/design/metric_views_requirements.md)) — it's left
as a future pass. `conventions.yml` is `output_model: hybrid`, so the same conventions carry the
gold build whenever it's run.

Unlike a gap-finding stress test, this domain is tuned to demo **a complete, disciplined run** — and
to exercise the `model_deviation` levers **deliberately**, as gated + logged human decisions.

## Model shape (16 modeled tables, normalized 3NF)

`order`, `order_line`, `order_schedule_line`, `order_partner`, `order_status_event`, `atp_check`,
`delivery_schedule`, `order_configuration`, `order_header_condition`, `order_line_condition`,
`quotation`, `quotation_line`, `return_order`, `return_order_line`, `sales_contract`,
`sales_contract_line` — ported verbatim (columns, comments, PKs) from a real generated vibe model,
plus its 6 metric views. **Intra-`sales_order` FKs** are declared constraints; **cross-domain FKs**
(customer / product_catalog / product_lifecycle / manufacturing / pricing / billing / supply_chain)
are **deferred** — kept as plain columns with business keys retained, so gold dims stay buildable.

## The three deliberate deviations (the demo's teaching moment)

The bronze is built so all three `model_deviation` levers fire as **gated, logged** decisions at the
Phase 2C human gate (recorded in [`docs/gap_analysis.md`](docs/gap_analysis.md) and
[`docs/design/next_vibes.md`](docs/design/next_vibes.md)):

| Lever | Toggle | What happened in the run | Why |
|---|---|---|---|
| **Drop 2 tables** | `drop_no_process_tables` | `order_header_condition` + `order_line_condition` DROPPED | no pricing-condition bronze source (SAP KONV not extracted) → out of demo scope |
| **Trim columns** | `drop_null_columns` | **20 always-NULL columns** dropped across `order_line` / `order_schedule_line` / `order_configuration` / `atp_check` / `delivery_schedule` | automotive-JIT / CTP-capacity / deep-CPQ fields Meridian doesn't populate |
| **Add capabilities** | `allow_new_entities` | net-new **`delivery`, `delivery_line`, `credit_check`** PROPOSED & built | bronze `likp`/`lips` reveal the outbound-delivery fulfilment step (the true OTD-actuals source); `zcredit_log` reveals per-order credit checks |

Net: 16 modeled − 2 dropped + 3 net-new = **17 normalized silver tables**.

## What the committed run produced

| Artifact | Location |
|---|---|
| Assessment handoff | `docs/design/` — `s2t_map.md`, `business_requirements.md`, `etl_detailed_spec.md`, `next_vibes.md` |
| Gap analysis | `docs/gap_analysis.md` |
| Silver pipeline (SDP) | `src/silver/pipeline/*.sql` (17 declarative sources) + `resources/sales_order_silver.pipeline.yml` |
| Validation | `src/silver/validation/narrative_*` + `scorecard`; `resources/sales_order_validation.job.yml` |
| Build/validate handoffs | `docs/.pipeline/handoffs/silver/` — `build_manifest.md`, `validation_summary.md`, `enrich_uc_metadata.sql` |
| Documentation | `docs/explanation/domain_narrative.md`, `docs/tutorials/`, `docs/contributor/`, `Sales Order Model Guide.py` |
| Dashboard | `Sales Order Validation Quality Dashboard.lvdash.json` |
| Gold design (not built) | `docs/design/gold_layer_assessment.md`, `docs/design/metric_views_requirements.md` |

See [`EXAMPLE_OUTPUT.md`](EXAMPLE_OUTPUT.md) for the annotated tree and the real headline numbers.

## Reproducing it

This domain is self-contained like [`field_service`](../field_service/README.md): it ships its own
`model_setup.sql` and a bronze generator profile, so you can run the whole loop in an empty
workspace.

> **Catalog note.** The committed run was executed against Meridian's live workspace — its
> `conventions.yml`, `databricks.yml`, and generated SQL carry that workspace's catalogs
> (`manufacturing_mvm_v1` for the model, `manufacturing_*_vibe` for bronze/silver). To reproduce
> from scratch, **swap those catalog names for your own** (the repo's standard "catalogs are
> placeholders" stance — see [`examples/README.md`](../README.md)).

### 0. Prereqs
An empty workspace with catalogs you can write for the model, bronze, and silver.

### 1. Generate + ingest the MVM bronze (once)
```bash
cd examples/setup
python3 -m data_generator.generate_bronze --profile mvm     # deterministic (SEED=42); +6 SAP SD sources
```
Upload `examples/setup/data_generator/output/**` to the landing volume, then run
`examples/setup/ingest/ingest_bronze.sql` **and**
[`ingest/ingest_bronze_mvm.sql`](ingest/ingest_bronze_mvm.sql).

### 2. Stand up the vibe model (once)
Run [`model_setup.sql`](model_setup.sql) into your model catalog/schema (16 shells + FKs + 6 metric
views).

### 3. Run the loop
Copy [`conventions.yml`](conventions.yml) to your project root, point `vibe_model` /`catalogs`
/`bronze_sources` at your own catalogs, then run **assess → build → validate → document**.
`model_deviation` is ON — approve the three deviations at the Phase 2C gate.

## Expected narrative (grade a fresh run against this)

- **Assess** — 14 tables map cleanly; 2 condition tables DROPPED (deviation), 20 columns TRIMMED
  (deviation), `delivery` / `delivery_line` / `credit_check` PROPOSED (deviation). 12 cross-domain
  FKs deferred. `next_vibes.md` scores the model **82/100** and records the drop/trim/add breadcrumbs.
- **Build** — 17 normalized silver tables (SDP materialized views); 20 intra-domain FKs resolved
  (11 direct SHA2 + 9 JOIN), 12 cross-domain deferred as NULL sentinels. ~132K source rows.
- **Validate** — **17/17 Grade A, 99/99 checks PASS, 0 FK orphans, 0 drift alerts.**
- **Document** — Diátaxis docs + Model Guide + Genie space + validation dashboard.

## Non-goals / not in this run
- **The gold layer** (dimensional star + the 5 metric views incl. `otd_performance`) — assessed and
  designed here, but not built. A future gold pass builds it from the silver.
- Cross-domain conformed masters (deferred with the cross-domain FKs).
