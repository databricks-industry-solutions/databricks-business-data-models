# [Project Name] — Gold / Metrics Requirements

*The handoff doc for the GOLD arm — analogous to `business_requirements.md` for silver, but
for use-case BI: marts, aggregates, and governed metrics. Fill this before building any gold
artifact. Graded **B+ or better** before the gold build fires — a higher bar than silver's B,
because gold serves named business KPIs where a wrong or vague definition is immediately visible
to consumers.*

*Gold is use-case-specific and built FROM silver. Unlike silver (which is a coherent
domain model), gold is driven by concrete consumption: a dashboard, a Genie space, a report,
or a governed KPI set. If you don't have a consumer in mind, you're not ready for gold.*

---

## Section 1 — Consumers (what is this gold FOR?)

| Consumer | Type (dashboard / Genie / report / metric API) | Audience | Key questions it answers |
| --- | --- | --- | --- |
| | | | |

---

## Section 2 — Gold Artifacts

Choose the right tool per artifact — **do not default everything to INSERT OVERWRITE tables**:

| Choose | When | Pattern |
| --- | --- | --- |
| **Metric view** (UC YAML) | Governed KPIs reused across dashboards/Genie/tools; single definition of a business metric | `databricks-metric-views` skill — YAML dimensions + measures over silver |
| **Aggregate mart** (table) | Pre-computed rollup a dashboard reads directly; heavy aggregation you don't want recomputed per query | `INSERT OVERWRITE` full recompute from silver |
| **Denormalized wide table** | One flat table joining a fact + its dims for a specific report/Genie space | `INSERT OVERWRITE` from silver star join |

| Artifact | Type (metric view / mart / wide table) | Grain | Source silver tables |
| --- | --- | --- | --- |
| | | | |

---

## Section 3 — Metrics / KPIs (the heart of gold)

*For each metric, define it precisely enough to build AND to grade against an existing number.*

| Metric name | Definition (numerator / denominator / filter) | Grain(s) it's sliced by | Existing reference value? (dashboard/report to match) |
| --- | --- | --- | --- |
| e.g. `OEE_Pct` | avg(Actual_Qty / Target_Qty) where Work_Center_Key != -1 | plant, shift, month | Existing "Plant OEE" Power BI tile = 78.4% for Jun 2026 |

**Metric-parity target:** where an existing dashboard/report already computes this KPI, record
its value(s) so the validation arm can confirm the generated metric MATCHES (within tolerance).
This is the strongest possible gold validation — parity against a number the business trusts.

---

## Section 4 — Refresh & Strategy

| Setting | Value | Rationale |
| --- | --- | --- |
| Refresh cadence | e.g. daily after silver job | |
| Metric view vs materialized | metric view (compute-on-read) unless a proven perf need for materialization | |
| Late-arriving data handling | full recompute (INSERT OVERWRITE) is safe for gold marts | |

---

## Section 5 — Data Quality / Parity Thresholds

| Check | Metric / table | Threshold | Action |
| --- | --- | --- | --- |
| Metric parity vs reference | | within ± X% of the reference value | fail if outside |
| Non-null coverage | | ≥ 95% | warn |
| Row count sanity | | > 0; within expected range | warn |
