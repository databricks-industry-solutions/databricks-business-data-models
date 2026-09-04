# Tutorial — run the loop on Meridian `field_service`

**What you'll do:** take one real domain — the **Meridian `field_service`** model that ships in
this repo — from an empty vibe model all the way to a validated, documented silver layer, by
running each of the four loop skills in turn and watching the document handoff carry your work
forward. `field_service` is a deliberately small **5-entity** domain, so the whole loop runs fast
and you get a concrete result you can check against a known-good outcome at every step.

**Who this is for:** a developer new to the suite who learns best by doing. This is a *learning*
exercise, not a reference — it walks one happy path start to finish. When you need to do a
specific task later (add a table, fix a grade), use the [how-to guides](how-to/); when you want to
know *why* the loop is shaped this way, read [explanation.md](explanation.md).

> **Want to see the destination first?** [`examples/field_service/EXAMPLE_OUTPUT.md`](../../examples/field_service/EXAMPLE_OUTPUT.md)
> is an illustrative picture of the full artifact tree this tutorial produces — skim it now if you
> like to know where you're headed, or come back to it after each step to compare.

## Before you begin

You need a **Databricks workspace** with the six skills available in Genie / Claude Code, and the
Meridian synthetic bronze ingested. Then do the two one-time setup steps from the
[`field_service` README](../../examples/field_service/README.md#how-to-run):

1. **Ingest the Meridian bronze** into `meridian_bronze` (`fieldlink` + `sap_sd`) if it
   isn't already — see `examples/setup/data_generator/README.md` and `examples/setup/ingest/ingest_bronze.sql`.
2. **Stand up the vibe model** — run `examples/field_service/model_setup.sql` once. It creates the
   `vibe_metamodel_*` tables and 5 empty normalized shells in
   `meridian_model.field_service_model`. The final cell should print 5 entities and
   **0 rows** in every shell.
3. **Choose the flow** — copy `examples/field_service/conventions.field_service.sdp.normalized.yml`
   to your project root as `conventions.yml`. This is the **`sdp_pipeline` / `normalized`** flow —
   **the suite default** — it reads the model in `meridian_model.field_service_model` and lands a
   3NF single-source-of-truth port in `meridian_silver.field_service_silver_sdp_norm` as one Lakeflow
   Declarative Pipeline.

> **Using your own domain instead?** The four steps below are identical for any domain — just
> point `conventions.yml` at your own vibe model, bronze sources, and land catalog. The concrete
> `field_service` values here (entities, grades, table names) are what *this* domain produces.

You do **not** need to write any SQL by hand. You drive the skills in natural language; they do
the authoring. Your job is to make decisions at the gates and read the handoff docs.

---

## Step 1 — Assess: "Can we build it?"

Load the **`domain-model-assessment`** skill:

> "I have a vibe model for `field_service` in `meridian_model.field_service_model`.
> Assess it against bronze."

The skill runs its lifecycle: inspect the empty metamodel → profile the bronze sources named in
`conventions.yml` (`fieldlink`, `sap_sd`) → produce a **source-to-target (S2T) mapping** → run a
gap-close iteration loop → generate handoff docs.

**What you'll see happen (for `field_service`, concretely):**
- **5 entities** discovered: `customer`, `product`, `installed_asset`, `service_order`,
  `technician`.
- **Fit grades:** `customer`, `product`, `installed_asset` = **Full**; `service_order` =
  **Partial** (everything maps except the technician FK); `technician` = **Blocked**.
- A **cross-source join** surfaced in the S2T mapping: FieldLink assets
  (`installed_asset.customer_kunnr`) join to the SAP customer master (`sap_sd.kna1.kunnr`).
- A **Gap Registry** with exactly **one P-item**: there is no technician master in bronze
  (`service_order.technician` is free text), so `technician` can't be sourced cleanly.

**Where you'll be asked to decide (true human gates):**
- **The technician gap** — accept deferring `technician` and building the other four entities, or
  choose to ingest an employee dimension first. (This tutorial defers it.)
- **Exit criteria** — confirm the domain is ready to build.

**The handoff you're producing:** when assessment exits, it has pre-filled
`docs/design/business_requirements.md` and `docs/design/etl_detailed_spec.md`. **Read them.**
These *are* the build's input — not the chat you just had. The durable design record lives under
`docs/design/`; skill-to-skill handoffs and state checkpoints live under the hidden
`docs/.pipeline/` tier, and `ARCHITECTURE.md` at the project root maps where everything lands.

✅ **You're done with Step 1 when** the readiness summary shows the four buildable entities graded
Full/Partial, the technician gap is registered as the single P-item, and the two design docs
exist and read correctly.

---

## Step 2 — Build: "Build it."

Load the **`etl-development-framework`** skill:

> "Start the build for `field_service`. Use the handoff docs from assessment."

The skill reads `docs/design/business_requirements.md` + `docs/design/etl_detailed_spec.md` and
authors the build to your `conventions.yml` standards. In this **`sdp_pipeline`** flow that is one
whole-domain **Lakeflow Declarative Pipeline**: a plain-`.sql` declarative source per entity — the
schema (columns, types, PK/FK, `COMMENT`, `CLUSTER BY`) and DQ (inline `CONSTRAINT … EXPECT`) all
live *in the object* — plus one `pipeline` DAB resource. No separate DDL step, no MERGE trio, no
recurring DQ notebook, and no daily job.

**What you'll see happen (for `field_service`, concretely):**
- Declarative sources proposed and (after your sign-off) created for the **3NF model** in
  `meridian_silver.field_service_silver_sdp_norm`: `customer`, `product`, `installed_asset` as
  `CREATE OR REFRESH MATERIALIZED VIEW` and `service_order` as `CREATE OR REFRESH STREAMING TABLE`
  (natural PKs — no surrogates; customer and product are reached *through* `installed_asset`, not
  copied onto the order). `technician` is **deferred** — the planted gap, not a failure.
- **DQ is inline, not a gate:** each object carries `CONSTRAINT … EXPECT` (grain + FK expectations),
  and violations surface in the **pipeline event log** — there is no build-time post-load DQ gate and
  no twice-run idempotency recheck (that is the `merge_notebook` flow). Deep data-state validation is
  Step 3, the validation skill.
- `gap_analysis.md`, `docs/.pipeline/state/run/progress.md`, and the typed
  **`docs/.pipeline/handoffs/silver/build_manifest.md`** written as it goes.

**Where you'll be asked to decide (true human gates):**
- **Approve the proposed model / DDL** before creation (Phase 1–2).

**The handoff you're producing:** `docs/.pipeline/handoffs/silver/build_manifest.md` — the
as-built mirror of `etl_detailed_spec.md`: grain, filters, FK resolution, final row counts, refresh
schedule, per-entity post-load DQ result. This is what the validation skill reads as authoritative.

> **Discipline note.** Between gates, the build runs autonomously — it will author the declarative
> sources, run the pipeline, and materialize the tables without prompting you each time. That's the intended
> behavior (see [explanation.md](explanation.md#2-human-at-the-decisions-agent-between-them)). If
> it's asking "should I continue?" after every notebook, that's a bug in how it's running, not the
> contract.

✅ **You're done with Step 2 when** the pipeline materializes the four built entities with a clean
event log (no `EXPECT` violations) and `docs/.pipeline/handoffs/silver/build_manifest.md` reflects
the as-built 3NF model.

---

## Step 3 — Validate: "Is it correct?"

Load the **`domain-model-validation`** skill:

> "Validate the `field_service` model. Generate narratives and establish baselines."

The skill proves the load landed as intended and makes quality legible: per-table regression
notebooks, `_validation_*` metadata tables that track grades over time, a scorecard, and a quality
dashboard.

**What you'll see happen (for `field_service`, concretely):**
- Per-entity `narrative_{entity}` regression notebooks that assert **0 FK orphans** and **0 dropped
  rows** — including the cross-source `installed_asset → customer` resolution (FieldLink asset → SAP
  `kna1`), through which each service order reaches its customer.
- A **scorecard** grading the **four built entities green**, written to the `_validation_*` tables.
  The **technician gap is recorded as accepted/deferred — not a failure**.
- A **quality dashboard** (current state, trend, priority backlog, integration health) that reads
  those tables — your at-a-glance surface for tracking gaps and bugs.
- A **validation DAB job** you can re-run any time — after a fix, a schema change, or on a schedule.
  Each run writes a new row to the `_validation_*` tables and computes grade/row-count deltas, so the
  dashboard's trend tab shows quality moving over time (a table climbing C → B → A as gaps close, or
  a regression the moment it appears). This is the persistent tracking system, not a one-shot check —
  see [reference.md](reference.md#the-validation-quality-tracking-system-tables--dashboard--job).

**Where you'll be asked to decide (true human gates):**
- **Accept a known exception** or **sign off a Grade D/F table** — the skill won't silently bless a
  failing table. (Here you confirm the deferred `technician` is an accepted gap, not a defect.)

**The handoff you're producing:** `docs/.pipeline/handoffs/silver/validation_summary.md` —
per-entity grades, the resolved/open gap deltas, and any changed Genie caveats. This is the
documentation skill's input. *(A `remediation_brief.md` is written alongside it under
`docs/.pipeline/handoffs/{layer}/` only when a grade degrades — the handoff back to the build
skill. On this happy path you won't produce one.)*

✅ **You're done with Step 3 when** the four built entities are at an acceptable grade (typically B
or better), the technician gap is signed off as deferred, and
`docs/.pipeline/handoffs/silver/validation_summary.md` exists.

---

## Step 4 — Document: "Make it usable."

Load the **`domain-documentation`** skill:

> "Generate documentation for `field_service`. Create the Model Guide and Genie space."

This produces the documentation layer **for your domain's data consumers** — the analysts and
stakeholders who will query the model. It owns all four Diátaxis quadrants *for the domain*:

- **Explanation** — a **domain narrative** (`docs/explanation/domain_narrative.md`): the model's
  story (the five-entity 3NF model — four built, the cross-source customer join, the honest
  technician caveat), authored from the validation summary + build manifest.
- **Reference** — a **Model Guide** notebook at the project root: a live front door with
  INFORMATION_SCHEMA queries (a column dictionary and FK map that can't go stale) and a health
  summary.
- **How-to** — a **Genie space** over `field_service_silver_sdp_norm`: instructions + 15–25 sample
  queries so the domain is queryable in natural language the moment it's built. Every sample query
  is validated against the live schema (non-empty results, verified column names).
- **Tutorials** — insight-showcase notebooks about *what this domain's data reveals* (e.g. service
  orders by asset, by customer region).

It also emits a **lightweight, co-located "maintaining this domain" guide**
(`docs/contributor/maintaining-this-domain.md`) for developers who later tend *this specific* model
— and that guide links back to these developer docs for the full suite explanation.

**Where you'll be asked to decide (true human gates):**
- **Review the Genie space config and the domain narrative** for accuracy — in particular that the
  narrative states the technician caveat honestly.

✅ **You're done with Step 4 when** the Model Guide runs clean, the Genie space answers a test
question (try *"how many service orders per customer region?"*), and the tutorials return real data
in every cell.

---

## What you built, and what you learned

You now have a validated four-entity 3NF silver layer for `field_service` with a live reference, a
natural-language query surface, and honest documentation (including the deferred-technician
caveat) — all traceable back through `validation_summary.md` → `build_manifest.md` →
`etl_detailed_spec.md` to the original assessment. Compare your output tree to
[`examples/field_service/EXAMPLE_OUTPUT.md`](../../examples/field_service/EXAMPLE_OUTPUT.md). More
importantly, you felt the loop's shape: **decisions at the gates, autonomy between them, and every
handoff on paper.**

### Next things to try

- **Run a different flow.** `field_service` ships all six `etl_type × output_model` variants — this
  walk used the default `sdp_pipeline` / `normalized`; swap `conventions.yml` for a `merge_notebook`
  variant or the `dimensional`/`hybrid` shapes and build again to compare shapes and mechanisms side
  by side. See the
  [`field_service` README](../../examples/field_service/README.md).
- **See it at realistic scale.** `field_service` is the fast 5-entity loop; the
  [`examples/sales_order_mvm/`](../../examples/sales_order_mvm/README.md) domain is the 16-table
  counterpart with a **committed real run** (silver — 17 tables, all Grade A; cross-domain FK
  deferral, SQL-reserved-word edge cases, all three `model_deviation` levers) — the same loop, at the
  scale of a real customer model.
- **Close the technician gap.** Ingest an employee master and [add the `technician`
  table](how-to/add-a-table.md).
- **Maintain it in steady state.** After the model exists, don't manually re-run skills for a point
  fix — see [how-to/re-sync-after-a-change.md](how-to/re-sync-after-a-change.md) (the `domain-sync`
  skill).
- **Understand the theory.** [explanation.md](explanation.md).
- **Look up the specifics.** [reference.md](reference.md).

> **Scope reminder.** This fast path delivers *silver*. Deep BU-specific metrics (gold) still need
> human definition — the skills accelerate it, but it's not push-button. See
> [explanation.md](explanation.md#scope-reality-the-fast-path-is-silver).
