# How to extend a built silver model to gold

**Goal:** you have a validated **silver** layer and now want a **gold** serving layer — a dimensional
star and/or governed metric views — driven by the KPIs the business actually names. This guide covers
*when* you're ready, *how* the gold path differs by `output_model`, and — the part people ask for — **what
the gold business-requirements input actually looks like filled in.**

**Roughly:** the brief is 30–60 minutes with a business stakeholder; the derive → build → validate loop
is a normal build cycle on top of it.

> **The golden rule of gold: it is consumer-driven and built FROM silver, never from bronze.** If there's
> no dashboard, Genie space, report, or named KPI in mind, stop — you're not ready for gold. Finish silver
> first. Gold is graded to a **higher bar than silver (B+ vs B)** because it serves numbers consumers see
> directly, where a vague definition is immediately visible.

## Are you ready for gold?

- [ ] Silver is built **and validated** (grades acceptable, 0 FK orphans, populated).
- [ ] You have at least one concrete **consumer** — a dashboard, a Genie space, a report, a KPI set.
- [ ] Ideally, you have **reference values** for some KPIs (an existing dashboard tile, a report number)
      to grade the generated metric against. Parity against a number the business trusts is the strongest
      gold validation there is.

## How gold differs by `output_model`

Gold's *shape* depends on the knob you set in `conventions.yml` (see
[fill-out-conventions.md](fill-out-conventions.md)):

| `output_model` | What "gold" is | Path |
| --- | --- | --- |
| **`hybrid`** | The **dimensional Kimball star itself** (`dim_`/`fact_`/`bridge_` + SHA2 `*_Key`, any SCD2) built **downstream from** normalized silver — plus marts/metric views on top. This is the case this guide walks through. | normalized silver → **derive the star** (assessment Mode B) → build → metrics |
| **`dimensional`** | The star already **is** silver. Gold is just use-case marts + metric views over it — **no star to re-derive.** | silver `dim_/fact_` → marts/metric views |
| **`normalized`** | Gold is marts + metric views over normalized silver. Usually at least metric views, since a 3NF silver isn't directly Genie-friendly. | silver products → marts/metric views |

So in `hybrid` you run a full derive → build; in `normalized`/`dimensional` you skip straight to the
metric-views/marts build. Either way, **Step 1 (the requirements brief) is the same** — gold is only as
good as the KPI definitions you feed it.

## Step 1 — Write the gold business-requirements brief

This is the key human input, and the thing that can't be inferred from silver structure alone: **grain
and dimensionality are business decisions.** Use
[`skills/domain-model-assessment/templates/gold_requirements_brief.md`](../../../skills/domain-model-assessment/templates/gold_requirements_brief.md)
as the shell. Fill in what you know; leave the rest blank and the derivation infers it from silver + the
silver `business_requirements.md`. **Anything you request that silver can't support becomes a recorded gap
— it is never silently dropped.**

### Worked example — Meridian Sales Order → gold

Here's the brief filled in for the Meridian `sales_order` domain (`hybrid`), the same domain whose
silver run is captured in [`examples/sales_order_mvm/`](../../../examples/sales_order_mvm/) and whose
gold star is *designed* in
[`docs/design/gold_layer_assessment.md`](../../../examples/sales_order_mvm/docs/design/gold_layer_assessment.md).
It's deliberately realistic: most requirements are supported, and some are **deferred** — shown as
gaps, not dropped.

```markdown
---
project: meridian_sales_order
customer: Meridian Manufacturing
use_case: sales_order Gold Layer — Business Requirements Brief
type: requirements
created: 2026-07-28
updated: 2026-07-28
---

# Sales Order Gold Layer — Business Requirements Brief

## 1. Fact grains needed

| # | Process / question              | Requested grain                  | Measures at this grain                          | Coarser summary needed?    |
| - | ------------------------------- | -------------------------------- | ----------------------------------------------- | -------------------------- |
| 1 | Revenue & bookings analysis     | one row per order line           | Order_Quantity, Net_Value, Discount_Value       | monthly by customer × rep  |
| 2 | On-time delivery                | one row per schedule line        | Is_On_Time, Days_Variance, Confirmed_Qty        | weekly by ship-to          |
| 3 | Quote conversion                | one row per quotation line       | Quoted_Value, Is_Converted, Loss_Reason         | monthly by channel         |
| 4 | Returns / RMA                   | one row per return line          | Return_Quantity, Return_Value, Reason           | monthly by product group   |
| 5 | Credit exposure                 | one row per credit check         | Exposure_Amount, Is_Held                        | daily snapshot             |

## 2. Dimensions / slices needed

| # | Dimension / slice | Attributes you need to slice by                | Notes                                  |
| - | ----------------- | ---------------------------------------------- | -------------------------------------- |
| 1 | Customer          | segment, region, industry, sold-to vs ship-to  | partner roles → bridge_order_partner   |
| 2 | Material          | product group, division                        |                                        |
| 3 | Sales area        | sales org, channel, division                   |                                        |
| 4 | Channel           | OE / distributor / dealer / e-comm / interco   | drives pricing + credit rules          |
| 5 | Order reason      | rejection / loss reason                        | UNION of SAP + CRM reason codes        |
| 6 | Sales rep         | rep name, team, **quota**                      | quota attribute is uncertain in silver |
| 7 | Date              | order / requested-delivery / quote / RMA date  | role-playing                           |

## 3. KPIs / metrics that must be supported

| # | KPI / metric              | Definition (how it's computed today, if known)                 | Target dashboard/consumer   |
| - | ------------------------- | -------------------------------------------------------------- | --------------------------- |
| 1 | On-Time Delivery %        | on-time schedule lines / total schedule lines                  | Ops OTD dashboard (= 94.2% Jun-26) |
| 2 | Quote Conversion Rate     | converted quote lines / total quote lines                      | Sales pipeline dashboard    |
| 3 | Net Bookings              | sum(Net_Value) at order-line grain, excl. rejected             | Revenue dashboard (= $48.3M Q2-26) |
| 4 | Return Rate               | return qty / shipped qty, by product group                     | Quality dashboard           |
| 5 | Credit Hold Exposure      | sum(Exposure_Amount) where Is_Held, snapshot daily             | Finance credit dashboard    |
| 6 | Gross Margin %            | (Net_Value − Cost) / Net_Value                                 | Revenue dashboard           |
| 7 | Rep Quota Attainment %    | Net_Bookings by rep / rep quota                                | Sales leadership review     |

## 4. Known constraints / preferences (optional)

- **Refresh / SLA:** daily by 07:00; credit exposure near-real-time if feasible.
- **Pipeline topology preference:** same SDP pipeline as silver (gold MVs downstream of silver MVs).
- **Unknown-member handling:** explicit `-1` / 'Unknown' dim member (matches silver FK default).
- **Metric-parity targets:** OTD 94.2% (Jun-26), Net Bookings $48.3M (Q2-26) — grade generated metrics
  against these.
```

Two requirements above **cannot be met from the current silver**, and that's the point — they surface as
gaps, never as silent omissions:

- **KPI #6 Gross Margin %** needs a **cost** measure. Silver carries `Net_Value` but no cost/COGS source.
  → recorded as a gap (*cause: missing-data*): "needs product cost from bronze; unblocks when a cost
  source lands."
- **KPI #7 Rep Quota Attainment** (and the Sales-rep `quota` attribute in §2) needs a **quota** source.
  Silver has rep *identity* but no quota target. → recorded as a gap (*cause: missing-data*): "needs a
  quota/target feed."

Everything else maps cleanly, which is why the designed gold star for that domain lands at **6 facts,
8 dims** (with cross-domain conformed masters deferred to business-key dims) — see its
[`docs/design/gold_layer_assessment.md`](../../../examples/sales_order_mvm/docs/design/gold_layer_assessment.md).
That gold layer is designed but **not yet built** in the committed run (which built silver only).

> **The brief is a human gate, not a hard blocker.** If you hand one in, the derivation treats each row
> as an authoritative requirement (a requested grain overrides the inferred default; a requested slice
> becomes a required dim even if no fact uses it yet). If you *don't*, the protocol infers KPIs from the
> silver `business_requirements.md` + narrative and says so in its header — a weaker, inferred requirement
> set. A stated brief always produces a sharper star.

## Step 2 — Derive the star (`hybrid` only; `dimensional`/`normalized` skip to Step 3)

Load `domain-model-assessment` against the built, populated silver:

> "Derive the gold layer for the `{domain}` model. Here's the gold requirements brief."

The **Mode Gate** routes to the silver → gold derivation (`gold-derivation-protocol.md`). Because silver
is already clean and typed, this is a *design* pass, not a discovery one (~15 tool calls, not 30): it
confirms row counts + the FK graph, then decides which 3NF entity becomes a **dim** vs a **fact**, the
grain of each fact, which dims **conform**, and where surrogate keys / SCD2 belong. It reconciles every
brief requirement against silver and emits a **gold design doc** (the example calls it
`gold_layer_assessment.md`) plus a KPI coverage matrix with any gaps. That doc — not the metamodel — is
what the gold build and validation grade against.

## Step 3 — Build the gold layer

Load `etl-development-framework` — it reads the gold design doc (or an equivalently-scoped
`gold_requirements.md`) and applies
[`gold-and-metrics.md`](../../../skills/etl-development-framework/gold-and-metrics.md). **Pick the right
tool per artifact — do not default everything to `INSERT OVERWRITE` tables:**

| Choose | When |
| --- | --- |
| **Metric view** (UC YAML) | A governed KPI reused across dashboards, Genie, and BI tools — one definition, many consumers. **Default for anything the business names as "a number."** |
| **Aggregate mart** (table) | A dashboard reads a pre-computed rollup directly; heavy aggregation you don't want recomputed per query. |
| **Denormalized wide table** | One flat fact+dims table for a specific report or Genie space. |

In `hybrid`, the `dim_/fact_/bridge_` DDL + load emits into the **gold** schema, reading FROM normalized
silver (this is where surrogate keys and SCD Type-2 live) — then metric views/marts sit on top. In SDP
mode (`etl_type: sdp_pipeline`), gold objects are declarative MVs in the **same pipeline** as silver,
schema-qualified to gold — the authoritative recipe is the "Hybrid mode: the downstream gold star layer"
section of `sdp-pipeline-development.md`, not `INSERT OVERWRITE` marts.

## Step 4 — Validate, with metric parity

Load `domain-model-validation`. Beyond the usual structural checks, gold gets **metric-parity mode**:
where the brief gave a reference value (OTD 94.2%, Net Bookings $48.3M), validation confirms the generated
metric **matches within tolerance**. Parity against a number the business already trusts is the strongest
gold validation — a passing star with a metric that's 8% off its known value is still a failure.

## Step 5 — Re-sync docs and Genie

Route the new gold objects through `domain-sync` (don't hand-re-run documentation): it regenerates the
Model Guide's gold section, adds the metric views to the Genie space so the KPIs are queryable in natural
language, and re-stamps the artifacts. See [re-sync-after-a-change.md](re-sync-after-a-change.md).

## Done when

The gold star (or marts/metric views) loads from silver, every brief requirement is either **built** or
**recorded as a gap** with an unblock action (no silent descoping), the named KPIs pass metric-parity
validation at B+ or better, and the metrics are queryable through the Genie space. The two example gaps
(margin, quota attainment) stay visible in the gap registry as "unblocks when {cost, quota} data lands."
