# sales_order — full-scale reference domain

The full **sales_order** domain over the Meridian bronze — the realistic, full-scale counterpart to
the `field_service` fast loop. Where `field_service` is 5 entities you can run end to end in
minutes, `sales_order` shows what the loop looks like at the scale of a real customer model: **27
tables** in **hybrid** shape (normalized 3NF silver → dimensional gold star), a gold layer,
cross-domain divergences, and SQL-reserved-word edge cases (the `order` entity).

> **⚠️ Reference example — not self-contained.** Unlike `field_service`, this domain ships **no
> `model_setup.sql`**, so there is **no script here to stand up its 27-table vibe model** — it
> assumes the model already exists at `meridian_sales_model.sales_order`. The synthetic *bronze* is
> reproducible from the shared [`setup/`](../setup/) (same generator as `field_service`), but to
> actually run the loop you would first have to author and deploy the sales_order vibe model
> yourself. **For a runnable, reproducible example, use
> [`field_service`](../field_service/README.md).** This domain is here to show the shape and scale
> of a realistic model, and to document the run the skills' guidance is hardened against.

The vibe model defines **27 tables**; only ~**17** are buildable from the current bronze (per the
grading key: 15 fully mapped + 2 partial, with 9 gaps and 1 derived). The assessment discovers that
split — the count you build is not the count in the model.

## Two flows (same model, same hybrid shape, different mechanism)

| Flow | Conventions file | `etl_type` / `output_model` | Lands in |
|---|---|---|---|
| **Hybrid (merge)** | `conventions.sales_order.hybrid.yml` | `merge_notebook` / `hybrid` | `..._silver_hyb` + `..._gold_hyb` |
| **Hybrid (SDP)** | `conventions.sales_order.sdp.yml` | `sdp_pipeline` / `hybrid` | `..._silver_sdp` + `..._gold_sdp` |

Both read `meridian_sales_model.sales_order` and land in distinct schemas under
`meridian_silver`, so you can build both and compare. Same hybrid shape by different
mechanism (MERGE trio vs one Lakeflow Declarative Pipeline) — the pair isolates the `etl_type` knob.

## How to run

### 0. Prereqs
- **You must supply the vibe model.** The sales_order 27-table model must already be deployed at
  `meridian_sales_model.sales_order` (READ-ONLY) — there is no `model_setup.sql` in this folder to
  create it (see the reference-only note above).
- Meridian bronze is ingested into `meridian_bronze` (all 5 source schemas) — reproducible from
  `examples/setup/data_generator/README.md` and `examples/setup/ingest/ingest_bronze.sql`.

### 1. Pick a flow
Copy ONE of these to your project root as `conventions.yml`:
- `conventions.sales_order.hybrid.yml` — **merge_notebook / hybrid**
- `conventions.sales_order.sdp.yml` — **sdp_pipeline / hybrid**

### 2. Run the loop
Load `domain-model-assessment` and point it at the model — **the assessment does the discovery**
(source-to-target mapping, gap registry, fit grades). Then hand off to `etl-development-framework`,
then `domain-model-validation`, then `domain-documentation`. Run once per flow to compare; Assess
is identical across both (same model), the flows diverge at Build.

> The grading answer key for this domain lives at `examples/planted-divergences.md` —
> **graders only; never feed it to the loop skills.**
