# EXAMPLE_OUTPUT — sales_order (MVM) committed run (silver)

This is the **real committed run** (2026-09-03) — the actual assess→build→validate→document output,
not a mock-up. Scope: **normalized 3NF silver only.** The dimensional gold star is designed
(`docs/design/gold_layer_assessment.md`) but not built in this run.

## The output tree (silver, SDP)

```
examples/sales_order_mvm/
├── conventions.yml                            # as-run config (hybrid / sdp_pipeline; live catalogs)
├── databricks.yml                             # DAB bundle
├── model_setup.sql                            # (input) stands up the 16-table vibe model + 6 metric views
├── ingest/ingest_bronze_mvm.sql               # (input) loads the +6 MVM SAP SD sources
├── Sales Order Model Guide.py                 # entry-point notebook
├── Sales Order Validation Quality Dashboard.lvdash.json
├── resources/
│   ├── sales_order_silver.pipeline.yml        # one Lakeflow Declarative Pipeline (17 silver sources)
│   └── sales_order_validation.job.yml         # validation job (18 tasks)
├── src/silver/
│   ├── pipeline/                              # 17 normalized .sql declarative sources
│   └── validation/                            # per-entity narrative_* + scorecard
└── docs/
    ├── design/                                # s2t_map, business_requirements, etl_detailed_spec,
    │                                          #   next_vibes, gold_layer_assessment*, metric_views_requirements*
    ├── gap_analysis.md                        # the three deviations, logged
    ├── explanation/domain_narrative.md
    ├── tutorials/                             # 01 Scale · 02 Performance · 03 Flow
    ├── contributor/maintaining-this-domain.md
    └── .pipeline/                             # state + handoffs (build_manifest, validation_summary)
```
\* `gold_layer_assessment.md` + `metric_views_requirements.md` = the **designed, not-yet-built** gold layer.

## Headline numbers (real)

```
Model quality score (next_vibes):  82/100
Silver tables built:               17   (16 modeled − 2 dropped + 3 net-new)
Intra-domain FKs resolved:         20   (11 direct SHA2 + 9 JOIN) — 0 orphans
Cross-domain FKs deferred:         12   (NULL sentinel; parent domains not built)
Source rows read:                  ~132,275
Validation:                        17/17 Grade A · 99/99 checks PASS · 0 drift alerts
```

## Deviations applied at the Phase 2C gate (real)

```
DROPPED (deviation, drop_no_process_tables): order_header_condition, order_line_condition   [no KONV bronze]
TRIMMED (deviation, drop_null_columns): 20 NULL_SOURCE columns across order_line, order_schedule_line,
        order_configuration (×5), atp_check (×5), delivery_schedule (×6)
NET-NEW (deviation, allow_new_entities): delivery (likp), delivery_line (lips), credit_check (zcredit_log)
```

## Excerpt — validation scorecard (real)

```
Silver: 0 FK orphans (intra-domain), 0 dropped rows, 0 silent nulls on required cols → Grade A (17/17)
Tiers 0–5 all PASS; INTEGRATION checks preserve row counts through FK joins.
Gold star + otd_performance metric: designed (docs/design/), not built this run.
```

## How this maps back to the loop

Each station's output is checked in, so you can read a real assessment handoff
(`docs/design/`), a real build manifest and validation summary
(`docs/.pipeline/handoffs/silver/`), and the finished Diátaxis docs — the three `model_deviation`
decisions are the human-gate teaching moments. See [`README.md`](README.md) to reproduce it in your
own workspace.
