# How to fill out `conventions.yml` for a new customer/domain

**Goal:** take the annotated base template to a filled-in `conventions.yml` that the whole loop
(`domain-model-assessment` → `etl-development-framework` → `domain-model-validation` →
`domain-documentation`, plus `domain-sync`) reads — making the two shape/mechanism decisions
deliberately and getting the source map right the first time.

**Roughly:** 15–30 minutes, most of it spent on the source map.

> This is the *decision* guide. The base template
> [`templates/conventions.yml`](../../../templates/conventions.yml) is the *mechanical* reference —
> every knob is annotated inline with its rule and rationale. The
> [reference table](../reference.md#conventionsyml--the-single-config-surface) is the one-line-per-key
> summary. Read this when you're deciding *what to put*; read those when you need *what a key does*.

## Step 0 — Copy the base, fill the identifiers

Copy [`templates/conventions.yml`](../../../templates/conventions.yml) to your project root and set the
plain identifiers first — these are just facts about the engagement, no judgment call:

- `customer`, `domain` — short slugs.
- `vibe_model.catalog` / `.schema` — where the **read-only** graded vibe model lives (the
  `vibe_metamodel_*` tables + empty template DDL). The build reads this and **never writes to it**.
- `catalogs.silver` — the **separate** land/write target. Keep it distinct from `vibe_model.catalog`
  so a build never writes into the model it grades against. (Same rule for `bronze`, `gold`, `sandbox`.)
- `deployment.alert_email`, schedule cron, timezone — host is resolved per-target in `databricks.yml`,
  never baked here.

Everything below is a real decision.

## Step 1 — Pick `output_model` (the shape knob)

This decides *what shape* the build makes **from** the vibe model. It's the decision people most
often get wrong by reaching for the fancier option too early.

| Pick | When | What you get |
| --- | --- | --- |
| **`normalized`** *(default — start here)* | You want a coherent, documented, validated **silver** layer that faithfully ports the vibe model. This is the fast path and the right first move for almost every new domain. | 3NF SSOT: one table per vibe-model product, the model's natural lowercase PKs/FKs preserved, no `dim_`/`fact_`, no surrogates. |
| **`dimensional`** | The domain's real consumers are BI/star-schema-first and there's **no** need for a normalized SSOT underneath. | Kimball star: `dim_`/`fact_`/`bridge_`, SHA2 `*_Key` surrogates, conformed dims, explicit grain. The normalized model seeds it, then gets re-shaped. |
| **`hybrid`** | You need **both** a normalized SSOT **and** a dimensional star — i.e. you're delivering the silver **and** gold layers. | **Layered, not both-at-once:** normalized 3NF silver FIRST, then a Kimball star built **downstream from that silver** in gold. Gold reads silver, never bronze. |

**The rule of thumb: start `normalized`, add the gold star later.** The loop's fast path delivers
silver; the normalized silver you build first *is* the SSOT the hybrid gold layer would read from.
So `normalized` now and `hybrid` later isn't rework — the silver carries forward. Reach for `hybrid`
up front only when you already know a star is a committed deliverable for this domain (e.g. there are
existing dashboards/KPIs to grade generated gold metrics against). Reach for bare `dimensional` only
when a normalized SSOT genuinely has no consumer.

> **Deep gold/metrics logic still needs a human.** All three modes accelerate the build, but
> BU-specific business rules and metric definitions (gold) aren't auto-derived from the model — the
> skills speed up that layer, especially when you have existing KPIs to check against, but they don't
> invent the definitions. When you're ready to build that layer, see
> [extend-to-gold.md](extend-to-gold.md) for the gold requirements brief and the derive → build flow.

See the [variant matrix](../reference.md#the-etl_type--output_model-matrix-variant-templates) and
`etl-development-framework/naming-standards.md` "⚠️ Precedence & key strategy by mode" for how naming
and keys resolve per mode (and per layer, in `hybrid`).

## Step 2 — Pick `etl_type` (the mechanism knob)

Orthogonal to shape — it chooses *how* the build runs, and honors all three `output_model` values.

| Pick | When |
| --- | --- |
| **`sdp_pipeline`** *(default)* | You want one whole-domain Lakeflow Declarative Pipeline: DDL lives inside the flow (no separate DDL step), inline `CONSTRAINT EXPECT`, deployed as one `pipeline` DAB resource. |
| **`merge_notebook`** | You want the classic DDL + Type-1 MERGE trio per entity + a daily job, with DDL as a separate setup step. Choose this when the team prefers explicit notebooks or the environment isn't on Lakeflow SDP. |

The `output_model` × `etl_type` grid is 2 × 3 = six valid cells, each with a thin overlay template in
[`templates/conventions-variants/`](../../../templates/conventions-variants/README.md) and a runnable
instance in `examples/field_service/conventions.field_service.*.yml`. Assess is identical across all
six (same model); the flows diverge at Build.

## Step 3 — Get the source map right (this is the high-leverage step)

`bronze_sources` and `source_systems` are where a few minutes of care saves the most downstream pain.
**List every source system you know feeds this domain, to the best of your knowledge, and say exactly
where each one lives.** Assessment uses this map as its single source of truth for the schema search —
if a source isn't listed, the skill won't go looking for it, and the entities it would have fed get
recorded as `DEFERRED` gaps instead of being built.

**`bronze_sources`** — one entry per **logical** source, `src_{logical}: {catalog}.{schema}`:

```yaml
bronze_sources:
  src_sap_sd:         customer_bronze.sap_sd          # ERP of record (raw/cryptic)
  src_salesforce_crm: customer_bronze.salesforce_crm  # CRM (clean)
  src_edi_gateway:    customer_bronze.edi_gateway     # EDI middleware (semi-clean)
```

- **One prefix per source, each fully qualified.** A silver load often reads several bronze schemas —
  sometimes across **different catalogs** (ERP vs HR vs an existing gold layer). Don't try to force
  everything through a single source catalog/schema. Because each prefix carries its own catalog,
  cross-catalog joins just work. Keep the per-source pattern even when all sources happen to share one
  catalog (the common case) — a later mixed-catalog source then needs no structural change.
- **Fold in existing production silver/gold.** If the domain already has curated tables somewhere,
  list them here too — assessment folds existing production silver/gold into the domain rather than
  rebuilding from raw.
- **A comment on each line = data quality intel for the assessment.** "raw/cryptic", "clean",
  "net-new, no silver home yet" all steer how the skill profiles and trusts each source.
- **When you're unsure a source exists,** list your best guess anyway with a note. A listed-but-empty
  source surfaces as a finding; an unlisted source is invisible. The
  [no-silent-descope rule](../../../templates/conventions.yml) means a modeled entity with no bronze
  source is recorded as `DEFERRED` with an "unblocks when X lands" callout — never silently dropped —
  so over-listing is safe and under-listing hides work.

**`source_systems`** — the enum of values written into the `_source_system` audit column. Make it
match your real systems (`SAP_S4`, `SALESFORCE`, `EDI`, …); every built row is tagged with one, so
this is how lineage reads downstream.

> **`conventions.yml` is the structured map; prose context sharpens it further.** If you know *what's
> in* each source (which tables, universal identifiers, the domain narrative), hand that to the
> assessment as an input doc — see [prepare-assessment-inputs.md](prepare-assessment-inputs.md). The
> `bronze_sources` map says *where*; an input doc says *what and why*.

## Step 4 — The remaining knobs (usually leave the defaults)

| Key | Default | Change it when |
| --- | --- | --- |
| `etl_language` | `sql` | The team wants Python-hosted MERGE/validation notebooks. (DDL, Model Guide, Genie, dashboard are always SQL; validation inherits this value.) |
| `scd_strategy` | `type_1` | A dimension needs point-in-time history → `type_2`. **Dimensional/hybrid-gold only** — the skill errors on `normalized` + `type_2` and redirects you to `hybrid`. |
| `naming` | per-mode | Rarely — it resolves automatically from `output_model`. The generic best-practice values ship correct; only identifiers change. |
| `load_strategy` thresholds | 5M / 100M rows | The customer's volumes push the FULL_MERGE / INCREMENTAL_MERGE / SDP-escalation boundaries. |
| `audit_columns`, `gap_status_enum` | as shipped | Almost never — these are conventions the whole suite shares. |

## Sanity check before you run the loop

- [ ] `vibe_model.catalog` ≠ `catalogs.silver` (read/write separation — the build never writes to the model).
- [ ] `output_model` chosen deliberately (defaulted to `normalized` unless a star is a committed deliverable).
- [ ] Every source you know of is in `bronze_sources`, fully qualified, with a quality note.
- [ ] `source_systems` matches the real systems and covers every `bronze_sources` entry.
- [ ] No catalog/schema/host/email literals anywhere the skills will bake into SQL — these are runtime params.

## Done when

`conventions.yml` sits at the project root, both knobs are set with intent, and the source map lists
every known source with its fully-qualified location — so `domain-model-assessment` can resolve the
model location, search the right bronze schemas, and produce a gap registry that reflects *real*
missing data rather than sources you forgot to list.
