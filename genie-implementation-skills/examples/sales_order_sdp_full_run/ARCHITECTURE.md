# ARCHITECTURE.md — Meridian Sales Order (SDP Pipeline, Hybrid)

> **📸 Frozen reference snapshot.** This is a **real, captured run** of the full loop
> (assess → build → validate → document) on the `sdp_pipeline` / `hybrid` flow, kept as a
> browsable example of complete output. It was **captured against the skills as of 2026-08-09**;
> the directory layout has since been re-aligned to the current three-tier convention, but the
> *content* (naming, DDL patterns, validation approach) reflects that date and current skills may
> differ. It is **reference-only, not runnable** — the 27-table model is not self-contained (no
> `model_setup.sql`), so browse it to see artifact shape and cross-references rather than to
> reproduce it. For the runnable path, use the `field_service` tutorial.

## Where things live

- **Start here** → the `Sales Order Model Guide.py` notebook, `docs/tutorials/`, and the Genie space
- **Understand the model** → `docs/explanation/domain_narrative.md`
- **Why it's built this way / how we got here** → `docs/design/`
- **Maintaining it** → `docs/contributor/maintaining-this-domain.md`
- **Machine plumbing (safe to ignore)** → `docs/.pipeline/` — skill-to-skill handoffs, state
  checkpoints, and session commentary; its own `docs/.pipeline/README.md` maps the tier
  (`handoffs/{silver,gold}/` typed seams · `handoffs/genie_space_instructions.md` ·
  `state/run/` run-global + `state/{silver,gold}/` layer-scoped)

## Directory map

```
sales_order_sdp_full_run/                   # project root
├── databricks.yml                          # DAB bundle config
├── conventions.yml                         # Domain conventions (etl_type: sdp_pipeline, output_model: hybrid)
├── ARCHITECTURE.md                         # ← START HERE: this file (Directory Guide)
├── Sales Order Model Guide.py              # Model Guide notebook — the live reference front door
├── resources/
│   ├── meridian_sales_order_silver_sdp.pipeline.yml   # Pipeline resource (30 entities: 17 silver + 13 gold)
│   ├── meridian_sales_order_validation.job.yml        # Silver validation job (daily 07:00 UTC, PAUSED)
│   └── meridian_sales_order_gold_validation.job.yml   # Gold validation job
├── src/
│   ├── silver/
│   │   ├── pipeline/                           # Silver SDP SQL sources (15 MV + 2 ST)
│   │   │   ├── sales_area.sql · order_reason.sql · channel_config.sql
│   │   │   ├── sales_contract.sql · sales_contract_line.sql · quotation.sql
│   │   │   ├── order.sql · quotation_line.sql · order_line.sql · order_partner.sql
│   │   │   ├── order_schedule_line.sql · delivery_schedule.sql · edi_order_message.sql
│   │   │   └── order_credit_check.sql · return_order.sql · otd_record.sql · return_order_line.sql
│   │   └── validation/                         # Validation notebooks (domain-model-validation)
│   │       ├── ddl_validation_schema              # Creates 5 _validation_* tables
│   │       ├── narrative_<entity>                 # Per-entity narrative + regression
│   │       └── scorecard                          # Claims PENDING, grades, fail gate
│   └── gold/
│       ├── pipeline/                           # Gold SDP SQL sources (13 MV — dimensional star)
│       │   ├── dim_date.sql                    # G0: generated calendar (730 rows)
│       │   ├── dim_sales_area.sql              # G0: passthrough from silver (4 rows)
│       │   ├── dim_channel.sql                 # G0: passthrough from silver (4 rows)
│       │   ├── dim_order_reason.sql            # G0: passthrough from silver (9 rows)
│       │   ├── dim_customer.sql                # G1: AG partner dedup (300 rows)
│       │   ├── dim_material.sql                # G1: order_line UNION quotation_line (800 rows)
│       │   ├── dim_sales_contract.sql          # G1: passthrough from silver (120 rows)
│       │   ├── bridge_order_partner.sql        # G1: pivot AG/WE/RE per order (5000 rows)
│       │   ├── fact_sales_order_line.sql       # G2: revenue/volume fact (14762 rows)
│       │   ├── fact_otd.sql                    # G2: delivery performance fact (22212 rows)
│       │   ├── fact_quotation_line.sql         # G2: quote pipeline fact (11982 rows)
│       │   ├── fact_return_line.sql            # G2: returns/RMA fact (329 rows)
│       │   └── fact_credit_check.sql           # G2: credit exposure fact (3104 rows)
│       └── validation/                         # Gold validation notebooks (domain-model-validation)
└── docs/
    ├── design/                             # DURABLE design record (assessment output; you read these)
    │   ├── business_requirements.md           # Domain requirements (from assessment)
    │   ├── etl_detailed_spec.md               # ETL spec (from assessment)
    │   ├── s2t_mapping_report.md              # Source-to-target mapping
    │   ├── gap_analysis.md                    # Gap analysis (7 active + 9 blocked)
    │   └── gold_layer_assessment.md           # Gold layer design spec (consumers, KPIs, artifact choices)
    ├── explanation/
    │   └── domain_narrative.md                # DELIVERABLE — the model's story (Explanation quadrant)
    ├── tutorials/                          # DELIVERABLE — progressive insight-showcase notebooks
    │   ├── 01_sales_order_at_a_glance         # scale & portfolio
    │   ├── 02_delivery_and_risk_performance   # OTD, credit, returns
    │   └── 03_order_lifecycle_and_flow        # quote → order → delivery lifecycle
    ├── contributor/
    │   └── maintaining-this-domain.md         # DELIVERABLE — per-domain maintenance guide
    └── .pipeline/                          # TRANSIENT plumbing — hidden; safe to ignore day-to-day
        ├── README.md                          # in-folder manifest (what each file is, its seam, who writes/reads it)
        ├── handoffs/
        │   ├── genie_space_instructions.md     # Document — Genie space config + 15 sample queries
        │   ├── silver/
        │   │   ├── build_manifest.md           # Build → Validate
        │   │   ├── validation_summary.md       # Validate → Document
        │   │   └── enrich_uc_metadata.sql      # Document — UC comments/tags (silver)
        │   └── gold/
        │       ├── validation_summary.md       # Validate → Document (gold)
        │       └── enrich_uc_metadata.sql      # Document — UC comments/tags (gold)
        ├── state/
        │   ├── run/                            # run-global checkpoints (layer-agnostic)
        │   │   ├── progress.md                 # Build progress (Silver + Gold COMPLETE)
        │   │   └── documentation_state.md      # Documentation checkpoint (all VALIDATED)
        │   ├── silver/                         # layer-scoped checkpoints
        │   │   ├── etl_state.md                # Per-entity build state
        │   │   └── validation_state.md         # Per-entity validation checkpoint
        │   └── gold/
        │       └── validation_state.md         # Gold validation checkpoint
        └── commentary/                         # session build commentary (per station × layer)
```

## Ownership

| Path | Owner | Skill |
| --- | --- | --- |
| `src/silver/pipeline/` | etl-development-framework | SDP SQL sources (normalized 3NF silver) |
| `src/gold/pipeline/` | etl-development-framework | SDP SQL sources (dimensional gold star) |
| `src/{silver,gold}/validation/` | domain-model-validation | Regression + scorecard |
| `resources/` | etl-development-framework + validation | DAB resource configs |
| `docs/design/` | domain-model-assessment | Requirements, spec, S2T mapping, gap + gold assessment |
| `docs/.pipeline/handoffs/{layer}/build_manifest.md` | etl-development-framework | Build → Validate handoff |
| `docs/.pipeline/handoffs/{layer}/validation_summary.md` | domain-model-validation | Validate → Document handoff |
| `docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql` | domain-documentation | UC enrichment (comments/tags) |
| `docs/.pipeline/handoffs/genie_space_instructions.md` | domain-documentation | Genie space config |
| `docs/.pipeline/state/{run,silver,gold}/` | ETL / validation / documentation | Resumable checkpoints |
| `docs/explanation/domain_narrative.md` | domain-documentation | Explanation quadrant |
| `docs/tutorials/` | domain-documentation | Progressive tutorials |
| `docs/contributor/` | domain-documentation | Maintenance guide |
| `Sales Order Model Guide` | domain-documentation | Entry-point notebook (Reference) |
| Genie space (external) | domain-documentation | How-to layer (Sales Order Analytics) |

## Architecture

* **Output model:** `hybrid` — normalized 3NF silver SSOT, then dimensional star in gold
* **ETL type:** `sdp_pipeline` — Lakeflow Spark Declarative Pipeline (FILE model, plain .sql)
* **Pipeline:** Single pipeline with both silver + gold globs; silver=default schema, gold objects hardcoded to gold schema
* **Gold design:** NULL FK (no -1 sentinel); SHA2(natural_key, 256) surrogate keys; all MVs (recomputable from silver)
* **DQ:** Inline EXPECT constraints; no build-time validation gate; downstream domain-model-validation
