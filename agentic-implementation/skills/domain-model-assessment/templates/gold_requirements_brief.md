---
project: {project}
customer: {customer}
use_case: {domain} Gold Layer — Business Requirements Brief
type: requirements
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
---

# {Domain} Gold Layer — Business Requirements Brief

> **Purpose.** Optional-but-preferred intake for the **silver → gold derivation** (Mode B,
> `gold-derivation-protocol.md` Step G0). Grain and dimensionality are *business* decisions — a
> business user or engineer often knows concrete requirements that can't be inferred from the silver
> structure alone. Fill in what you know; leave the rest blank and the protocol infers it from the
> silver model + KPIs. **Anything you request that silver can't support becomes a recorded gap — it
> is never silently dropped.**

---

## 1. Fact grains needed

One row per analytical process you need to measure. State the **grain** (what one row represents)
and the **measures** at that grain. If you need a coarser summary (daily/monthly rollup), name it —
the atomic fact is still built underneath so drill-down is preserved.

| # | Process / question | Requested grain | Measures at this grain | Coarser summary needed? |
| --- | --- | --- | --- | --- |
| 1 | e.g. "revenue analysis" | one row per order line | Order_Quantity, Net_Value | monthly by customer |
| 2 | e.g. "on-time delivery" | one row per ship-to × week | Is_On_Time, Days_Variance | — |
| … | | | | |

## 2. Dimensions / slices needed

The attributes you need to slice and filter by. Include ones you know you'll need even if you're not
sure silver has them (they become gap findings if not).

| # | Dimension / slice | Attributes you need to slice by | Notes |
| --- | --- | --- | --- |
| 1 | e.g. Customer | segment, region, industry | segment/industry may be cross-domain |
| 2 | e.g. Sales Rep | rep name, team | |
| … | | | |

## 3. KPIs / metrics that must be supported

The specific metrics the gold layer must answer — these seed the KPI coverage matrix (Step G5) and
flag which become governed **metric views**.

| # | KPI / metric | Definition (how it's computed today, if known) | Target dashboard/consumer |
| --- | --- | --- | --- |
| 1 | e.g. Quote conversion rate | converted quotes / total quotes | Sales pipeline dashboard |
| … | | | |

## 4. Known constraints / preferences (optional)

- **Refresh / SLA:** {e.g. daily by 07:00; near-real-time for credit}
- **Pipeline topology preference:** {same pipeline as silver / separate gold pipeline / no preference}
- **Unknown-member handling:** {NULL FK / explicit 'Unknown' dim member}
- **Anything else:** {conformed dims already standardized elsewhere, naming preferences, etc.}
