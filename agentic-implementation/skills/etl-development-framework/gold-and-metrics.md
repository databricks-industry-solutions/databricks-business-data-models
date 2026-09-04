# Gold Layer & Metric Views

The gold arm turns validated **silver** into use-case BI: aggregate marts, denormalized wide
tables, and — the piece the first pass lacked — **governed metric views**. Load this when the
user asks to build gold, metrics, KPIs, or a dashboard/Genie serving layer, and a
`docs/design/gold_requirements.md` exists (graded B+).

> **Requirements filename — accept an assessment-produced equivalent.** The canonical input is
> `gold_requirements.md` (this skill's own template). A `domain-model-assessment` gold pass may instead
> hand off an equivalently-scoped doc under a different name (e.g. `gold_layer_assessment.md`) — same
> content (consumers, KPIs, grain/FK design, artifact-type choices), different filename. If
> `gold_requirements.md` is absent, check for an assessment gold-design doc and treat it as the input
> rather than assuming the requirements are missing or creating a duplicate. *(The assessment skill's
> gold output filename is being settled in a separate workstream; don't hard-code an expectation.)*

> **Building gold in SDP mode?** If `etl_type: sdp_pipeline`, the **authoritative gold recipe is
> `sdp-gold-star.md`** — gold
> objects are declarative MVs in the same pipeline as silver, schema-qualified to the gold schema, not
> `INSERT OVERWRITE` marts. Also apply the **inline schema type discipline** (DECIMAL CAST,
> TIMESTAMP-vs-DATE, serverless `WEEKDAY()+1` instead of `DAYOFWEEK_ISO`, source-format probe; defined in
> `sdp-pipeline-development.md`) and the **FK-resolution fan-out** rule (`sdp-templates.md`) to every gold
> object — those are the failure modes that most often
> break a first gold run. The metric-view / mart guidance below still applies on top of the SDP star.

**Golden rule of gold:** it is consumer-driven and built FROM silver, never from bronze. If
there's no dashboard/Genie/report/KPI consumer in mind, stop — build or finish silver first.

---

## Gold's role depends on `output_model`

| `output_model` | What gold is | Consumer path |
|---|---|---|
| **`dimensional`** | Use-case marts + metric views over the **dimensional silver star**. | silver `dim_/fact_` → gold marts/metrics |
| **`normalized`** | Use-case marts + metric views over **normalized silver**. Optional — a normalized silver isn't directly Genie-friendly, so most engagements add at least metric views here. | silver products → gold marts/metrics |
| **`hybrid`** | **Layered (not both-at-once):** normalized silver is built first, THEN gold is where the **dimensional star lives** (`dim_/fact_/bridge_` + any SCD2), built FROM that silver — plus the usual marts/metrics on top. | normalized silver → gold star → gold marts/metrics |

In `hybrid`, emit the `dim_/fact_/bridge_` DDL + MERGE (the templates in `ddl-and-modeling.md` /
`merge-and-defensive-coding.md`) into the **gold** layer, reading FROM the normalized silver
products — this is where surrogate keys and SCD Type-2 versioning belong. The metric-view / mart
guidance below then applies on top of that star. In `normalized`/`dimensional`, gold is just
marts + metric views as described.

---

## Pick the right gold tool (do NOT default to INSERT OVERWRITE tables)

| Tool | Use when | Build with |
| --- | --- | --- |
| **Metric view** (UC YAML) | A governed KPI reused across dashboards, Genie, and BI tools — one definition, many consumers | The `databricks-metric-views` skill (YAML) — see below |
| **Aggregate mart** (table) | A dashboard reads a pre-computed rollup directly; expensive aggregation you don't want recomputed per query | `INSERT OVERWRITE` from silver (existing gold template in `merge-and-defensive-coding.md`) |
| **Denormalized wide table** | One flat fact+dims table for a specific report or Genie space | `INSERT OVERWRITE` star join from silver |

Metric views are the default for **KPIs**. Marts/wide tables are for **pre-materialized shapes**.
The first pass only taught `INSERT OVERWRITE`, so every KPI would have become a hand-rolled
aggregate table — brittle and duplicated. Prefer a metric view for anything that's "a number
the business names."

---

## Metric View Pattern (wire in the `databricks-metric-views` skill)

**Do not reinvent metric-view YAML — invoke the `databricks-metric-views` skill** for the
authoritative syntax, creation via `manage_metric_views`, and query patterns. This section is
the bridge: how a metric view fits THIS motion.

- **Source:** a metric view sits over **silver** (a fact + its conformed dims), not bronze.
- **Definition source of truth:** `gold_requirements.md` Section 3 — each metric's
  numerator/denominator/filter and the grains it slices by become the YAML `measures` and
  `dimensions`.
- **Naming:** follow `conventions.yml` gold naming (business-friendly, no `dim_`/`fact_`
  prefix). Metric view name = the KPI set it serves (e.g. `manufacturing_oee_metrics`).
- **Unknown-member hygiene:** carry the silver convention into measures — exclude `-1` Unknown
  members from aggregations (`WHERE {Dim}_Key != -1`), exactly as the gold `INSERT OVERWRITE`
  template does.
- **One definition, many consumers:** a metric view is queryable from dashboards, Genie, and
  SQL identically — this is why it beats a per-dashboard aggregate table for KPIs.

**Handoff from silver:** the silver star schema + the FK-resolution attributes already recorded
in `etl_detailed_spec.md` Section 3 tell you exactly which dims join to the fact and on what —
reuse them; do not re-derive joins for the metric view.

---

## Metric Parity Validation (the strongest gold check)

When `gold_requirements.md` Section 3 records an **existing reference value** (a Power BI tile,
an existing report, a legacy KPI), the gold validation arm must confirm the generated metric
**matches that number within tolerance**. This is more convincing than any structural check —
it proves the metric means what the business thinks it means.

**Protocol (delegate the mechanics to `domain-model-validation`, parity mode):**
1. For each metric with a reference value, compute the generated metric at the same grain and
   filter as the reference (e.g. Plant OEE for Jun 2026).
2. Compare to the reference value; PASS if within the parity threshold (Section 5, e.g. ±1%).
3. Write the result as a `PARITY` check in `_validation_check_detail` (Check_Type = 'PARITY',
   Threshold_Value = reference, Actual_Value = generated, Deviation_Pct = diff).
4. A parity miss is a **HUMAN gate** — it means either the metric definition or the silver data
   differs from the trusted source; surface it with both numbers and the likely cause.

**Why this matters:** gold is where the business will trust or reject the whole motion. A metric
that's structurally valid but off by 4% from the number on someone's existing dashboard destroys
confidence. Parity-check every metric that has a reference.

---

## Gold build sequence (extends the 7-phase ETL workflow)

Gold reuses the silver phases with these deltas:
1. **Requirements** — `gold_requirements.md` graded B+ (not `business_requirements.md`).
2. **Model & DDL** — metric-view YAML and/or gold table DDL in `src/gold/ddl/`.
3. **Build** — metric views via `manage_metric_views`; marts via `INSERT OVERWRITE` in
   `src/gold/`. Batch ≤ 4 (Batching Discipline).
4. **Validate** — structural checks PLUS metric parity (above). Gold validation gate =
   `validate_gold.sql` + parity checks.
5. **Deploy** — gold tasks in the DAB job depend on silver completing (silver → gold → validate).
6. **Document** — metric views appear in the Model Guide and are exposed to the Genie space.

## Boundaries

- Deep BU-specific business logic still needs human definition — the skill accelerates it but
  does not invent KPIs. `gold_requirements.md` Section 3 is where the human supplies meaning.
- If a "metric" is really a complex multi-step transformation (allocations, waterfalls), it may
  belong in a gold **mart** built with staged SQL, not a single metric view — use judgment.
