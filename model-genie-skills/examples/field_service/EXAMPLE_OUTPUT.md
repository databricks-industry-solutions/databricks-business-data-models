# EXAMPLE_OUTPUT — what a finished `field_service` run looks like

> **⚠️ Illustrative sample, not a live deployment.** This document is a **hand-authored picture**
> of the artifacts a completed run of the loop produces for `field_service`, so the
> [tutorial](../../docs/developer/tutorial.md) has a concrete destination and you can evaluate the
> suite's output *shape* without a Databricks workspace. The row counts, grades, and file tree
> reflect the domain's [known-good expected narrative](README.md#expected-narrative-grade-the-run-against-this),
> but the excerpts are representative, not captured from a specific execution. A real run writes the
> live, verified versions of these files into your project folder.

**Flow shown:** `conventions.field_service.sdp.normalized.yml` — **`sdp_pipeline` / `normalized`**
(the default flow). Reads `meridian_model.field_service_model` (5 entities) → lands a 3NF
single-source-of-truth port in `meridian_silver.field_service_silver_sdp_norm` as **one Lakeflow
Declarative Pipeline** — materialized views + one streaming table, with inline `CONSTRAINT … EXPECT`
for DQ (no MERGE trio, no daily job, no build-time DQ-gate notebook). Four entities built;
`technician` deferred (the planted gap). *(Swap `conventions.yml` for a `merge_notebook` variant or
the `dimensional`/`hybrid` shapes to rebuild the same model differently — see the
[`field_service` README](README.md).)*

---

## The output tree

A finished run organizes its output **by audience**, in three tiers, with `ARCHITECTURE.md` at the
root as the "you are here" map (because `docs/.pipeline/` is hidden):

```
field_service/                              # your project root
├── conventions.yml                         # the field_service normalized flow (input)
├── databricks.yml                          # DAB bundle (input + build-authored targets)
├── ARCHITECTURE.md                         # ← START HERE: Directory Guide, owned by domain-sync
├── Field Service Model Guide.py            # Model Guide notebook — the live reference front door
│
├── resources/
│   ├── field_service_silver_sdp.pipeline.yml  # the whole-domain Lakeflow Declarative Pipeline (replaces the daily job)
│   └── field_service_validation.job.yml       # downstream validation job (runs after the pipeline materializes)
│
├── src/
│   └── silver/
│       ├── pipeline/                       # one plain-.sql declarative source per entity (FILE model — NO notebook header)
│       │   ├── customer.sql                #   CREATE OR REFRESH MATERIALIZED VIEW + inline CONSTRAINT … EXPECT
│       │   ├── product.sql                 #   natural PKs, no dim_/fact_, no surrogates — schema is inline (no separate DDL)
│       │   ├── installed_asset.sql
│       │   └── service_order.sql           #   CREATE OR REFRESH STREAMING TABLE + append flow (ST-APPEND)
│       └── validation/                     # downstream regression notebooks (domain-model-validation, post-materialization)
│           ├── narrative_customer …        #   per-entity 0-orphan / 0-drop assertions against the live tables
│           └── scorecard                    #   the graded rollup
│
└── docs/
    ├── design/                             # DURABLE design record (assessment's output; you read these)
    │   ├── business_requirements.md
    │   ├── etl_detailed_spec.md
    │   ├── s2t_mapping_report.md           # incl. the fieldlink → sap_sd cross-source join
    │   └── gap_analysis.md                 # the one P-item: no technician master in bronze
    │
    ├── explanation/
    │   └── domain_narrative.md             # DELIVERABLE — the model's story (excerpt below)
    ├── tutorials/                          # DELIVERABLE — insight-showcase notebooks
    ├── contributor/
    │   └── maintaining-this-domain.md      # DELIVERABLE — slim per-domain maintenance guide
    │
    └── .pipeline/                          # TRANSIENT plumbing — hidden; safe to ignore day-to-day
        ├── README.md                       # in-folder manifest: what each file is, its seam, who writes/reads it
        ├── state/
        │   ├── run/                        # run-global checkpoints (layer-agnostic)
        │   │   └── progress.md
        │   └── silver/                     # layer-scoped checkpoints
        │       ├── etl_state.md
        │       └── validation_state.md
        └── handoffs/
            └── silver/                     # typed seams, keyed by seam + layer
                ├── build_manifest.md       # build → validate (excerpt below)
                └── validation_summary.md   # validate → document (excerpt below)
```

> `remediation_brief.md` would appear under `docs/.pipeline/handoffs/silver/` **only if** a grade
> degraded — the handoff back to the build skill. A clean run like this one doesn't produce one.

---

## Excerpt — `ARCHITECTURE.md` (Directory Guide)

```markdown
## Where things live

- **Start here** → the `Field Service Model Guide.py` notebook, `docs/tutorials/`, and the Genie space
- **Understand the model** → `docs/explanation/domain_narrative.md`
- **Why it's built this way / how we got here** → `docs/design/`
- **Maintaining it** → `docs/contributor/maintaining-this-domain.md`
- **Machine plumbing (safe to ignore)** → `docs/.pipeline/` — skill-to-skill handoffs, state
  checkpoints, and session commentary; its own `docs/.pipeline/README.md` maps the tier
  (`handoffs/{layer}/` typed seams · `state/run/` run-global + `state/{layer}/` layer-scoped)
```

---

## Excerpt — `docs/.pipeline/handoffs/silver/build_manifest.md`

```markdown
# Build Manifest — field_service (silver, normalized · sdp_pipeline)

Land target: meridian_silver.field_service_silver_sdp_norm
Read model:  meridian_model.field_service_model
Mechanism:   one Lakeflow Declarative Pipeline (FILE model, root_path ../src/silver/pipeline)
Built:       4 of 5 entities (technician deferred — see §7)

## §1 Per-entity as-built

| Entity          | Grain                     | Object                       | Rows   | Inline DQ (EXPECT) |
|-----------------|---------------------------|------------------------------|--------|--------------------|
| customer        | one row per customer       | MATERIALIZED VIEW           | ~300   | grain + FK EXPECT  |
| product         | one row per SKU            | MATERIALIZED VIEW           | ~40    | grain EXPECT       |
| installed_asset | one row per asset          | MATERIALIZED VIEW           | ~3,698 | grain + FK EXPECT  |
| service_order   | one row per service_order  | STREAMING TABLE (ST-APPEND) | ~1,479 | grain EXPECT       |

## §4 FK resolution (natural keys — 3NF; each edge is a single hop)
- installed_asset.customer_id → customer  (cross-source: FieldLink asset.customer_kunnr → SAP kna1.kunnr)  0 orphans
- installed_asset.product_id  → product   (FieldLink asset.sku_code)   0 orphans
- service_order.asset_id      → installed_asset (natural asset_id)      0 orphans
- service_order.technician_id → technician — UNRESOLVED (deferred gap; left unpopulated, see §7)
- No surrogate keys and no Unknown-member seeding: a normalized SSOT port keeps the model's natural
  PKs. Customer/product are reached *through* the asset, never copied onto service_order. FK
  completeness on the streaming table is asserted downstream by validation, not inline.

## §7 Deferred / gaps
- technician (P1): no employee master in bronze; service_order.technician is free text.
  Disposition: DEFERRED (accepted at assessment). `service_order.technician_id` stays unpopulated
  and the `technician` table is not built. Not a failure.

## §8 DQ mechanism (SDP)
- No build-time DQ-gate notebook and no twice-run idempotency recheck — that is the `merge_notebook`
  flow's gate. DQ is inline `CONSTRAINT … EXPECT`; violations surface in the pipeline event log.
  Data-state correctness (0 orphans / 0 drops) is proven downstream by `domain-model-validation`
  against the materialized tables.
```

---

## Excerpt — `docs/.pipeline/handoffs/silver/validation_summary.md`

```markdown
# Validation Summary — field_service (silver)

## Scorecard
| Entity          | Grade | FK orphans | Dropped rows | Silent nulls |
|-----------------|-------|-----------|--------------|--------------|
| customer        | A     | 0         | 0            | none         |
| product         | A     | 0         | 0            | none         |
| installed_asset | A     | 0         | 0            | none         |
| service_order   | A     | 0         | 0            | technician_id empty (by design — deferred gap, not silent) |

## Gap deltas
- technician (P1): OPEN → ACCEPTED (deferred). `service_order.technician_id` stays unpopulated until
  an employee master is ingested. Signed off as a known exception, not a defect.

## Genie caveats (for the documentation skill to carry)
- Technician is not modeled; `service_order.technician_id` is empty and the `technician` table is
  unbuilt (source has only a free-text name). Any "orders by technician" question must be answered
  with a caveat.
```

---

## Excerpt — `docs/explanation/domain_narrative.md` (opening)

```markdown
# Field Service — domain narrative

The field_service silver layer answers one question well: **what happened in the field, to which
asset, for which customer?** It is a **normalized, five-entity 3NF model** (four built) —
`service_order` referencing `installed_asset`, which in turn references `customer` and `product`.
Each fact is stated once, in one place: customer and product are reached *through* the asset rather
than copied onto the order.

The interesting join is cross-source. Service orders and installed assets come from **FieldLink**;
the customer master comes from **SAP** (`kna1`). An installed asset carries its customer number
(`customer_kunnr`), so the `installed_asset → customer` foreign key spans two systems — and
validation confirms **zero orphans** across it. A service order reaches its customer transitively:
service_order → installed_asset → customer.

**One honest caveat.** Every service order names a **technician**, but there is no technician master
in the source data — the field is free text upstream. Rather than invent one, the model **defers**
the `technician` table and leaves `service_order.technician_id` unpopulated, recording it as an
accepted gap. Ask Genie "orders by technician" and it will tell you the attribute is unmodeled.
Closing this gap means ingesting an employee master first.
```

---

## How this maps back to the tutorial

| Tutorial step | Produces (in this tree) |
|---|---|
| **1 Assess** | `docs/design/*` — requirements, spec, S2T mapping, the one-item gap analysis |
| **2 Build** | `src/silver/pipeline/*.sql` (the declarative pipeline), `resources/*.pipeline.yml`, `.pipeline/handoffs/silver/build_manifest.md` |
| **3 Validate** | `src/silver/validation/*`, `_validation_*` tables + dashboard (workspace-side), `.pipeline/handoffs/silver/validation_summary.md`. SDP has no build-time gate — DQ is inline `EXPECT` (event log) and data state is proven here, downstream. |
| **4 Document** | `Field Service Model Guide.py`, `docs/explanation/`, `docs/tutorials/`, `docs/contributor/`, the Genie space, `ARCHITECTURE.md` |

Some artifacts are **workspace-side and can't live in a file tree** — the Genie space, the quality
dashboard, the `_validation_*` metadata tables, and the executed notebook outputs (real row counts,
verified query results). Those only exist after a live run against the Meridian bronze.
