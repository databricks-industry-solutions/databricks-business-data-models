# field_service — fast-loop test domain

A minimal **5-entity** domain over the **existing FieldLink bronze**, built to run the
assess → build → validate → document loop **end-to-end fast** for skill iteration. ~4–5 built
tables instead of the 27 in `sales_order`.

It reuses the meridian synthetic bronze already in this repo — **no data generation needed**.
FieldLink is described in the generator README as "net-new process — no silver home yet," which
makes it the ideal fresh-model target.

---

## The vibe model is NORMALIZED (3NF) — and drives SIX flows (the etl_type × output_model matrix)

The deployed vibe model is a **normalized, 3NF, single-source-of-truth spec** — one table per
business entity, natural business keys as PKs, snake_case product names, **no `dim_`/`fact_`
prefixes, no surrogate keys**. That is what a vibe model is. The `output_model` (shape) and
`etl_type` (mechanism) knobs (`conventions.yml`) then decide what the build makes FROM that seed,
and by which mechanism. The two knobs are orthogonal — 2 × 3 = **six** cells — and this domain
ships **all six matched conventions files** so you can test every cell against the same model:

| Flow | Conventions file | `etl_type` / `output_model` | Builds | Lands in |
|---|---|---|---|---|
| **Dimensional (merge)** | `conventions.field_service.yml` | `merge_notebook` / `dimensional` | Kimball star (`dim_`/`fact_`, SHA2 `_Key`) via MERGE trio | `..._silver_dim` |
| **Normalized (merge)** | `conventions.field_service.normalized.yml` | `merge_notebook` / `normalized` | 1:1 3NF port (product names, natural PKs) via MERGE trio | `..._silver_norm` |
| **Hybrid (merge)** | `conventions.field_service.hybrid.yml` | `merge_notebook` / `hybrid` | **Normalized 3NF silver → dimensional Kimball gold**, both layers via the MERGE trio (DDL + Type-1 MERGE; gold star MERGE reads silver) | `..._silver_hyb` + `..._gold_hyb` |
| **Normalized (SDP)** | `conventions.field_service.sdp.normalized.yml` | `sdp_pipeline` / `normalized` | Single-layer 3NF port (MVs + ST-APPEND) as ONE Lakeflow Declarative Pipeline | `..._silver_sdp_norm` |
| **Dimensional (SDP)** | `conventions.field_service.sdp.dimensional.yml` | `sdp_pipeline` / `dimensional` | Single-layer Kimball star (dim MVs + ST-APPEND fact, reads bronze) as ONE Lakeflow Declarative Pipeline | `..._silver_sdp_dim` |
| **Hybrid (SDP)** | `conventions.field_service.sdp.yml` | `sdp_pipeline` / `hybrid` | **Normalized 3NF silver → dimensional Kimball gold**, both layers built as ONE Lakeflow Declarative Pipeline (MV + streaming-table) | `..._silver_sdp` + `..._gold_sdp` |

All six read the SAME model (`meridian_model.field_service_model`) and land in
**different schemas** (all under `meridian_silver`), so you can build them and compare
side by side. Each **merge/SDP pair at the same `output_model`** builds the same *shape* by a
different *mechanism* (MERGE trio vs one declarative pipeline), isolating the `etl_type` knob;
each **row across `output_model`** isolates the shape knob at a fixed mechanism. This is the same
matrix documented generically in [`templates/conventions-variants/`](../../templates/conventions-variants/README.md).

> **What `output_model: hybrid` means here (read this — the word is misleading).** `hybrid` does
> NOT mean "normalized and dimensional at the same time." It means **two LAYERS, built in
> sequence**: a **normalized 3NF silver** layer (the SSOT, follows the vibe model — natural PKs, no
> `dim_`/`fact_`, no surrogates), and THEN a **dimensional Kimball gold** star built *downstream
> from that silver* (`dim_`/`fact_` + SHA2 `_Key` surrogates). Silver first; gold reads silver. In
> this SDP fixture both layers are declarative objects in the **same pipeline** (silver MVs/ST →
> gold MVs), so one pipeline update materializes 3NF silver then the star on top of it.
>
> **SDP smoke-test scope.** The SDP flow exercises the MATERIALIZED VIEW + STREAMING-TABLE-APPEND
> templates in **both layers**, inline `CONSTRAINT EXPECT`, and the FILE/glob deployment model. It
> **deliberately avoids two SDP betas and ships no build-time testing** (updated after the first real run,
> 2026-08-08): **native `parameters:`** (bronze paths are hardcoded literals — the beta breaks on
> `STREAM IDENTIFIER(:param)`) and the **LDP unit-test framework** (`pyspark.pipelines.testing` is
> beta + Editor-only, so it can't gate a bundle flow). There is **no build-time test or validation
> artifact** — validation is the downstream `domain-model-validation` skill. It does **NOT**
> exercise the AUTO CDC / SCD2 path (unverified `stored_as_scd_type=2` SDK flag + needs CDF on
> bronze) — cover SCD2 with a dedicated mutable-dimension fixture. See the "Expected narrative —
> SDP flow" section below.

### Model shape (normalized 3NF — what's deployed)

```
service_order       one row per service_order_id   (~1,479)   PK service_order_id
  ├─ asset_id       → installed_asset               (~3,698)   PK asset_id
  │     ├─ customer_id → customer                   (~300, from SAP kna1)   ← cross-source
  │     └─ product_id  → product                    (distinct SKUs on assets)
  └─ technician_id  → technician                     — NO bronze source     (planted gap)
```

In the **dimensional** flow these become `fact_service_order` + `dim_installed_asset` /
`dim_customer` / `dim_product` (customer/product denormalized onto the fact via the asset, 2-hop),
with SHA2 `*_Key` surrogates. In the **normalized** flow they build 1:1 with the names above.

### Source mapping (what a correct assessment should find)

| Model table | Bronze source | Natural key (PK) | Notes |
|---|---|---|---|
| `customer` | `sap_sd.kna1` | `kunnr` | `name1`→customer_name, `land1`→country_code, `regio`→region, `brsch`→industry_code |
| `product` | `fieldlink.installed_asset` (distinct SKU attrs) | `sku_code` | `product_group`; **no clean `sku_code → matnr` bridge to SAP `mara`** — source from the asset |
| `installed_asset` | `fieldlink.installed_asset` | `asset_id` | `customer_kunnr`→customer_id, `sku_code`→product_id |
| `service_order` | `fieldlink.service_order` | `service_order_id` | `asset_id` FK; `technician` is free text → the gap |
| `technician` | **none** | `technician_id` | planted gap — see below |

### The planted gap (single, deliberate)

`fieldlink.service_order.technician` is a **free-text employee name**. The employee master exists
in the generator (`masters.py`) but is **never written to bronze**. So `technician` has no clean
source. A correct assessment should:

- grade `service_order` **Partial** (everything maps except the technician FK),
- grade `technician` **Blocked**,
- register **one P-item**: "no technician master in bronze — ingest an employee dim or accept the
  free-text technician name as a degenerate attribute on `service_order`,"
- defer `technician` and build the other 4 entities.

---

## How to run

### 0. Prereqs
- Meridian bronze is ingested into `meridian_bronze` (`fieldlink` + `sap_sd`). If not,
  see `examples/setup/data_generator/README.md` and `examples/setup/ingest/ingest_bronze.sql`.
- READ (vibe model) and WRITE (silver land) are in different catalogs, already set in both
  conventions files: READ `meridian_model.field_service_model`, WRITE
  `meridian_silver.field_service_silver_{dim,norm}`.

### 1. Stand up the vibe model (once — shared by both flows)
Run `examples/field_service/model_setup.sql` as a Databricks SQL notebook. Widgets default to
`vibe_model_catalog=meridian_model`, `vibe_model_schema=field_service_model`.

It CREATE-OR-REPLACEs the `vibe_metamodel_*` tables and (re)creates 5 empty normalized shells. The
final cell prints row counts — expect: business=1, product=5, **attribute=24**, and **0 rows** in
every shell.

### 2. Pick a flow and point the skills at it
Copy ONE of these to your project root as `conventions.yml`:
- `conventions.field_service.yml` — **merge_notebook / dimensional** flow → `*_silver_dim`
- `conventions.field_service.normalized.yml` — **merge_notebook / normalized** flow → `*_silver_norm`
- `conventions.field_service.hybrid.yml` — **merge_notebook / hybrid** flow → `*_silver_hyb` (3NF) + `*_gold_hyb` (star)
- `conventions.field_service.sdp.normalized.yml` — **sdp_pipeline / normalized** flow → `*_silver_sdp_norm` (3NF)
- `conventions.field_service.sdp.dimensional.yml` — **sdp_pipeline / dimensional** flow → `*_silver_sdp_dim` (star)
- `conventions.field_service.sdp.yml` — **sdp_pipeline / hybrid** flow → `*_silver_sdp` (3NF) + `*_gold_sdp` (star)

All read the same model; only `etl_type`/`output_model`, naming, the build mechanism, and the
land schema differ.

### 3. Run the loop
Load `domain-model-assessment` and point it at the model. Then hand off to
`etl-development-framework`, then `domain-model-validation`, then `domain-documentation`.
Run it once per flow to compare the builds. Assess is identical across all six (same model);
the flows diverge at Build.

---

## Expected narrative (grade the run against this)

### Assess (identical across all six flows — same model)
- Inspects `field_service_model`; finds **5** entities (`service_order`, `installed_asset`,
  `customer`, `product`, `technician`).
- **Grades:** `customer`, `product`, `installed_asset` = **Full**; `service_order` = **Partial**;
  `technician` = **Blocked**.
- **Gap registry:** exactly **1 P-item** — the technician master.
- **S2T mapping:** shows the `installed_asset.customer_kunnr → kna1.kunnr` cross-source join.
- **Handoff docs:** `business_requirements.md` + `etl_detailed_spec.md` whose Section 1 names match
  the chosen `output_model` (see below), and a **land target ≠ vibe model** (Section 0 distinct).

> **Regression watch — naming by flow.** The `sales_order` run failed twice: bare names in
> dimensional mode, and landing into the vibe model. Eyeball the spec's Section 1:
> - **dimensional** → names MUST carry `dim_`/`fact_` and `*_Key` surrogates
>   (`dim_installed_asset`, `fact_service_order`, `Asset_Key`).
> - **normalized** → names MUST be the bare model products with natural PKs
>   (`installed_asset`, `service_order`, `asset_id`) — NOT re-prefixed.
> - **hybrid** (merge or SDP) → the spec must show BOTH layers: bare model products + natural
>   PKs in the *silver* schema (`installed_asset`, `asset_id`), AND `dim_`/`fact_` + `*_Key`
>   surrogates in the *gold* schema (`dim_installed_asset`, `fact_service_order`, `Asset_Key`),
>   with gold reading silver — never bronze.
> In all, Section 0 land schema ≠ read schema.

### Build (MERGE flows — dimensional, normalized, hybrid)
- **Dimensional flow** → `meridian_silver.field_service_silver_dim`: `dim_customer`,
  `dim_product`, `dim_installed_asset`, `fact_service_order` (SHA2 `*_Key`, customer/product
  denormalized onto the fact). `dim_technician` deferred.
- **Normalized flow** → `meridian_silver.field_service_silver_norm`: `customer`,
  `product`, `installed_asset`, `service_order` (natural PKs, 3NF, FKs preserved). `technician` deferred.
- **Hybrid (merge) flow** → TWO layers via the MERGE trio:
  - *silver* `..._silver_hyb` (3NF SSOT, reads bronze): `customer`, `product`, `installed_asset`,
    `service_order` — natural PKs, no `dim_`/`fact_`, no surrogates. Identical to the normalized flow's
    silver. `technician` deferred.
  - *gold* `..._gold_hyb` (dimensional star, reads **silver** not bronze): `dim_customer`, `dim_product`,
    `dim_installed_asset`, `fact_service_order` — SHA2 `*_Key`, `-1` Unknown members seeded, each fact FK
    resolved by `LEFT JOIN` to the built gold dim + `COALESCE(...Key, -1)` (Rule 11 — never inline-recompute
    the surrogate). 🔴 A gold table that re-reads `meridian_bronze.*` is a bug.
  - DAB job orders silver tasks → gold star tasks → validate (gold depends on silver completing).
- Type-1 **FULL_MERGE**; every built entity clears its post-load DQ gate on the real table; DAB
  job scaffolded.

### Validate
- **0 FK orphans**, **0 dropped rows**; scorecard green for the 4 built entities. In hybrid, check
  orphans in **both** the silver 3NF layer and the gold star.
- Technician gap recorded as accepted/deferred, **not** a failure.

### Document
- Diátaxis docs + Model Guide notebook + auto Genie space over the built silver schema.

---

## Expected narrative — SDP flows (`conventions.field_service.sdp*.yml`)

Grade the SDP runs against THIS — the artifacts differ from the MERGE flows even though the
model, grades, and gap are identical. SDP is a different **build mechanism**, so the Build,
Validate, and (partly) Document expectations change; Assess does not.

> **Three SDP variants — the section below details `sdp.yml` (hybrid).** The other two are the
> **single-layer** SDP flows:
> - **`sdp.normalized.yml`** (`sdp_pipeline` / `normalized`) — silver ONLY (`..._silver_sdp_norm`):
>   product-named MVs + ST-APPEND, natural PKs, no `dim_`/`fact_`, no surrogates. **No `src/gold/`,
>   no gold glob**; `root_path: ../src/silver/pipeline`. It is the hybrid flow's silver layer, built alone.
> - **`sdp.dimensional.yml`** (`sdp_pipeline` / `dimensional`) — silver ONLY (`..._silver_sdp_dim`):
>   the Kimball star (dim MVs + ST-APPEND fact) as the silver output, **reading bronze directly** (no
>   normalized SSOT underneath). Same FK-resolution + `LIVE.*`-trap rules as the hybrid gold layer, but
>   over bronze. **No `src/gold/`, no gold glob**; `root_path: ../src/silver/pipeline`.
>
> All three SDP variants share the mechanism invariants below (FILE-model `.sql` sources, hardcoded
> bronze paths, no build-time test/validation artifact, one `pipeline` DAB resource). The hybrid detail
> that follows is the superset — for the single-layer variants, ignore the gold layer + second glob.

### Build (the part that differs most)
This fixture is **`output_model: hybrid`** — a **two-layer** build (NOT "both shapes at once"):
**normalized 3NF silver** in `..._silver_sdp`, then a **dimensional Kimball gold** star in
`..._gold_sdp` built *downstream from* that silver. Both layers are declarative objects in the
**same pipeline**, so one update materializes silver then gold-on-silver. Expect:

- **ONE plain-`.sql` declarative source per entity per layer** — silver sources under
  `src/silver/pipeline/`, gold star sources under `src/gold/pipeline/` (gold object names
  schema-qualified to the gold schema). NOT the transform/runner/test trio, and **NO `ddl/`,
  `transformations/`, `runners/` subfolders**. The schema (columns, types, COMMENT,
  `CONSTRAINT EXPECT`, PK/FK) is **inline in the declarative object** — no separate DDL-setup step.
  - 🔴 **Sources carry NO `-- Databricks notebook source` header** (FILE model). If they do — and
    are then referenced as per-entity `notebook:` libraries — that's the exact deadlock the first
    run hit (`NO_TABLES_IN_PIPELINE` / extension-stripping). Flag it.
- **SILVER layer — normalized 3NF (SSOT, reads bronze), type_1:**
  - `customer`, `product`, `installed_asset` → `CREATE OR REFRESH MATERIALIZED VIEW` (small, fully
    recomputable). Natural PKs (`customer_id`, `product_id`, `asset_id`) — **no** SHA2 surrogates,
    **no** `dim_`/`fact_` prefix. Follows the vibe model.
  - `service_order` → `CREATE OR REFRESH STREAMING TABLE` + append flow (**ST-APPEND**), FKs left
    as natural keys; completeness checked downstream (`domain-model-validation`), not inline.
  - `technician` **deferred** (the planted gap) — same as the MERGE flows. *(Note: the first real
    run instead derived a name-slug `technician` MV from `service_order` rather than deferring —
    either is defensible, but grade whether the run states its choice.)*
- **GOLD layer — dimensional Kimball star (reads SILVER, not bronze):**
  - `dim_customer`, `dim_product`, `dim_installed_asset` → `MATERIALIZED VIEW` over the matching
    silver table, adding the SHA2 `*_Key` surrogate (e.g. `Customer_Key`) + `dim_`/`fact_` naming
    and Pascal_Snake business columns.
  - `fact_service_order` → `MATERIALIZED VIEW` (small) over silver `service_order`, resolving each
    FK by `LEFT JOIN` to the gold dim on the natural key and `COALESCE(dim.Key, -1)` on misses
    (Rule 11 — never inline-recompute the FK surrogate; join to the already-built dim).
  - 🔴 **Gold reads silver, never bronze.** A gold object that re-reads `meridian_bronze.*`
    instead of the silver table is a bug — the whole point of hybrid is that gold sits on the SSOT.
- **NO `AUTO CDC` / SCD2 objects** — `scd_strategy: type_1` (type_2 would be a gold-only concept;
  not exercised here). An `AUTO CDC … STORED AS SCD TYPE 2` flow is a bug in this fixture.
- 🔴 **NO parameterization.** Bronze paths are **hardcoded fully-qualified literals**
  (`meridian_bronze.fieldlink.service_order`) in every source — MV and ST. **No pipeline
  `parameters:` block, no `:param`, no `IDENTIFIER(:param)`.** (The native-parameters beta breaks on
  `STREAM IDENTIFIER(:param)`.) Only the silver WRITE target (`catalog:`/`schema:`) is a DAB `${var}`.
- **Inline DQ (EXPECT):** silver grain/PK not-null on the **natural key** → `FAIL UPDATE` or
  `DROP ROW`; regex/enum value checks as soft `EXPECT`; **FK completeness is a soft
  `EXPECT (fk IS NOT NULL)` only** — real orphan detection is downstream (`domain-model-validation`).
  - 🔴 **In gold, guard the grain on the natural/degenerate key, NOT the SHA2 `_Key` surrogate** —
    the surrogate is never NULL (COALESCE always hashes to a value), so a constraint on it can never
    fire.
  - 🔴 **No cross-table subquery in a constraint.** `EXPECT (customer_id IN (SELECT … FROM
    LIVE.customer))` fails (`LIVE.*` doesn't resolve in constraints). The first run improvised this
    and hit the wall — the build must NOT emit it. Gold FK resolution is a `LEFT JOIN` in the
    defining query, not an EXPECT subquery.
- 🔴 **NO build-time testing artifact.** The build ships **no `tests/` folder, no
  `pyspark.pipelines.testing`/`TestPipeline` file, and no post-load validation notebook.** If it
  authors any of these, flag it — LDP testing is beta + Editor-only (never runs from a bundle), and
  the removal is deliberate. Confidence comes from inline `EXPECT` + the event log; real validation
  is the downstream `domain-model-validation` skill.
- **Deploy = ONE `pipeline` DAB resource** carrying **both layers** in one DAG
  (`resources.pipelines.field_service_silver_pipeline`, `continuous: false`, `serverless: true`,
  `root_path: ../src`, two globs — `../src/silver/pipeline/**` and `../src/gold/pipeline/**`) — **NOT** a `job`,
  and **NOT** per-entity `notebook:` entries. Pipeline default `schema:` = silver; gold objects are
  schema-qualified to the gold schema. Silver objects order before their gold consumers in the DAG
  automatically (gold reads silver by fully-qualified `catalog.schema.object`, NOT bare `LIVE.*`).
  Dev target
  `source_linked_deployment: true`; prod `false`.

### Validate — downstream, not in the SDP build
- The SDP build itself produces **no validation artifact**. After the pipeline update succeeds,
  confidence is the inline `EXPECT` pass-rates in the **pipeline event log** (`flow_progress` events'
  `data_quality.expectations`).
- The real data-state proof (**0 FK orphans** in **both** silver 3NF and the gold star,
  **0 unexpected dropped rows**, scorecard; technician gap accepted/deferred, not a failure) is the
  job of the downstream `domain-model-validation` skill — run it after the build, same as any flow.

### Document
- Diátaxis docs + Model Guide notebook + auto Genie space over **both** `field_service_silver_sdp`
  (3NF) and `field_service_gold_sdp` (star), same as the MERGE flows — the documentation skill is
  build-mechanism-agnostic.

### Regression watch — SDP-specific traps (all seen or fixed in the first real run)
- **Notebook-source header on `.sql` sources** → notebook-object/extension-stripping deadlock. Sources
  must be plain `.sql`, glob-included, `root_path` set. This is the #1 trap.
- **A pipeline `parameters:` block or `IDENTIFIER(:param)`** — removed on purpose; hardcode bronze paths.
- **Any build-time test/validation artifact** (`pyspark.pipelines.testing`, `TestPipeline`, or a
  post-load validation notebook) — removed on purpose; validation is the downstream skill.
- **`LIVE.*` subquery inside a `CONSTRAINT EXPECT`** — unsupported; FK completeness is downstream.
- **MV↔ST type change without full refresh** — if `service_order` flips object type, a full refresh
  is required (and may be blocked by tool safety policy on serverless → hand off to UI Start ▸ Full
  refresh, don't spiral on CLI/SDK).
- **AUTO CDC / SCD2** — not exercised here (`type_1`); the `stored_as_scd_type=2` SDK flag still needs
  its own fixture to verify.

---

## What this exercises (why it's a good fast loop)

- **output_model knob** — same normalized model → three shapes: dimensional star, 3NF port, and
  the **layered** normalized-silver→dimensional-gold `hybrid`, each landing in a separate schema
  for side-by-side comparison.
- **etl_type knob** — MERGE trio vs one Lakeflow Declarative Pipeline as the build mechanism.
- **The full 2 × 3 matrix** — both knobs are exercised together across all six shipped flows
  (dimensional/normalized/hybrid × merge/SDP), so each merge↔SDP pair isolates the mechanism at a
  fixed shape and each row isolates the shape at a fixed mechanism.
- **Layered `hybrid` (silver → gold)** — the SDP flow proves a 3NF SSOT silver AND a dimensional
  gold star built downstream from it, both in ONE pipeline DAG (silver objects ordered before their
  gold consumers). This is "normalized then dimensional," NOT both-at-once.
- **Read/write separation** — distinct `vibe_model.*` vs `catalogs.silver`; the build must not
  MERGE into the model.
- **Naming handoff, all modes** — dimensional (+ hybrid gold) applies `dim_`/`fact_` + `*_Key` SHA2
  surrogates; normalized (+ hybrid silver) preserves the model's product names + natural PKs.
- **SDP declarative path** — MATERIALIZED VIEW + STREAMING-TABLE-APPEND in both layers, hardcoded
  bronze paths (no parameterization), inline `EXPECT`, FILE/glob + `root_path` + source-linked
  deploy, one `pipeline` DAB resource (SQL + type_1 only). No beta dependencies, no build-time testing.
- **Cross-source join** — FieldLink asset → SAP customer master.
- **Gap registry / fit grading** — one real Partial/Blocked via the technician gap.
- **FK tiering** — customer/product → installed_asset → service_order.

## Non-goals
- Not customer output; a skill-bench fixture. Does not modify `sales_order`,
  `meridian_sales_model`'s sales model, or the meridian generator.
- The setup SQL is written from the generator source; run it once and confirm the row counts.
