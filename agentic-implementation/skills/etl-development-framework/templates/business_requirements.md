# [Project Name] — Business Requirements

*Fill this document before Genie Code runs any discovery queries. Requirements are graded
(A–F) against the rubric in `discovery-and-gap-analysis.md`. The more specific you are,
the fewer assumptions get made and the less rework you get in Phase 2.*

---

## 1. Project Context

| Field | Value |
| --- | --- |
| **Project name** | |
| **Domain / business area** | |
| **Project owner** | |
| **Target completion** | |
| **Layer(s) to build** | Silver / Gold / Both |
| **Output model** | **normalized** (default) / dimensional / hybrid — see note below |
| **SCD strategy (dims)** | **type_1** (default) / type_2 — type_2 needs dimensional or hybrid |

> **Output model** decides the shape of the built schema (drives `conventions.yml output_model`):
> **`normalized`** = one table per vibe-model product, 3NF, model's keys (faithful-ish, close to
> the model); **`dimensional`** = Kimball star (`dim_/fact_`, surrogate keys, conformed dims) —
> the default; **`hybrid`** = **layered (not both-at-once)** — normalized 3NF silver first, THEN a
> dimensional gold star built downstream from that silver. The vibe model is always
> the *seed*; drift to fit your data is expected. If you want SCD Type-2 history but chose
> `normalized`, that's a signal you want `hybrid` (history belongs in the dimensional layer).

**Background / problem statement:**
> What business problem does this ETL solve? What decisions or reports will it enable?

---

## 2. Source Systems

| System name | Type | Catalog | Schema | Access confirmed? |
| --- | --- | --- | --- | --- |
| | (Oracle EBS / SAP SF / SQL Server / flat file / etc.) | | | Yes / No / Unknown |

**Known limitations or data quality issues:**
-

---

## 3. Business Entities

List every entity you know you need. Mark Type as DIM (reference / descriptive / slowly-changing)
or FACT (transactional / event / high-volume). Leave Source Table blank if unknown.

| Entity | Type (DIM / FACT) | Natural key | Source table (best guess) | Notes |
| --- | --- | --- | --- | --- |
| | | | | |

---

## 4. Key Metrics & KPIs

Be precise — grain, filter, and formula matter. Vague metrics ("safety metrics") require
assumptions that may be wrong.

| Metric name | Formula / definition | Grain | Filter / scope | Priority |
| --- | --- | --- | --- | --- |
| | | (e.g. per site per month) | (e.g. open status only) | P1 / P2 / P3 |

---

## 5. Consumers

| Consumer name | Type | Owner / team | Notes |
| --- | --- | --- | --- |
| | Dashboard / Genie Space / Report / API / Other | | |

---

## 6. Refresh & SLA

| Field | Value |
| --- | --- |
| **Refresh cadence** | (e.g. daily, hourly, weekly) |
| **Preferred run time** | (e.g. 6:00 AM ET) |
| **Data available by (SLA)** | (e.g. 8:00 AM ET) |
| **Timezone** | (e.g. America/New_York) |
| **Failure alert email** | |

---

## 7. Non-Functional Requirements

| Requirement | Detail |
| --- | --- |
| **PII / data sensitivity** | Any columns requiring masking or row-level security? |
| **Data residency** | |
| **Row-level security** | Who can see what subset of rows? |
| **Retention** | How long to keep history? |
| **Volume estimate** | Approximate row counts and growth rate per entity |

---

## 8. Out of Scope

*Explicitly list what this project does NOT cover. Prevents scope creep during discovery.*

-

---

## 9. Open Questions

*Questions that need answers before or during discovery. Genie Code will flag these as
ambiguities if not resolved before Phase 1.*

| # | Question | Owner | Status |
| --- | --- | --- | --- |
| 1 | | | Open / Resolved |
