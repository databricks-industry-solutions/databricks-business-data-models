# Tutorial Generation

## Overview

Tutorials are **insight-oriented, executable notebooks** that showcase what this specific
domain's data reveals. The reader runs each cell and sees real numbers about the real operation.

Unlike how-to guides (Genie sample queries), tutorials are INSIGHT SHOWCASES, not SQL lessons.
The goal: the reader finishes understanding *what this manufacturing operation looks like and
what the data says about it* — NOT that they learned a new SQL pattern. So there is **no
"What is a star schema?" teaching cell, no "Step 1 — start with the fact" query build-up, and
no "now you try" prompt.** If a cell's purpose is to teach SQL mechanics, delete it.

### The one format: the observation triplet

Every tutorial is a sequence of **triplets**, 5–7 per notebook:

```
[md]  A business question, in the stakeholder's words ("Which plants run the most volume?")
[sql] ONE query that answers it — complete, not built up across cells
[md]  The observation: what the numbers say, in business language, WITH the concrete figures
      pulled from the result ("Three plants — Monterrey, Reynosa, El Paso — run 61% of all
      lots; the long tail of 39 plants splits the rest.")
```

The middle cell is a finished query, not a lesson step. The third cell is the payload — it is
where the tutorial earns its keep, so it must cite real numbers from the result and read like a
sentence an operations lead would say, not a description of the SQL. One finding per SQL cell.

---

## Tutorial Set (3 Notebooks)

The three notebooks form a **scale → performance → flow** arc:

| # | Name | Answers (theme) | Audience |
| --- | --- | --- | --- |
| 01 | Operations at a Glance | **Scale** — what does this operation look like? Portfolio, volume, OEE health | Any stakeholder |
| 02 | OEE Performance Intelligence | **Performance** — how efficient is it? Shift patterns, trends, top/bottom performers | Operations |
| 03 | Production and Supply Chain | **Flow** — how does production move? Volume trends, job complexity, BOM landscape | Supply chain |

Each lives in `docs/tutorials/` as a SQL notebook. Each notebook's **first markdown cell carries
a `synced-against` stamp** (`<!-- synced-against: progress.md @ {date} (rev: {sha|run_id}) -->`,
per `domain-sync/staleness-linter.md`) and each **ends with a "What's Next" cell** pointing to
the next tutorial → then to the Genie space (for ad-hoc questions) → then to the Model Guide
(for the full reference). The arc is the through-line: 01 sets the scale, 02 explains
performance within it, 03 shows how work flows through it.

---

## Tutorial 01: Operations at a Glance (theme: SCALE)

**Goal:** Reader finishes with a clear mental picture of the operation's *scale* — how many
plants, how much volume, how healthy OEE is overall. Business questions only; the reader never
has to know what a star schema is.

### Cell Structure — 5–7 observation triplets

```
Cell 0 (md): synced-against stamp + title
Cell 1 (md): One-paragraph orientation — "This notebook answers: how big is this operation,
             where does it run, and is it healthy?" (no SQL preamble, no schema tour)

--- Triplet 1: how many plants, and how concentrated? ---
Cell 2 (md):  Q: "How many plants do we run, and how is volume spread across them?"
Cell 3 (sql): plant count + lot volume per plant, ranked
Cell 4 (md):  Observation with real numbers ("42 plants; the top 3 run 61% of lots …")

--- Triplet 2: what's the total scale? ---
Cell 5 (md):  Q: "How much production and how many OEE records are we tracking?"
Cell 6 (sql): total lots, total OEE records, date span (MIN/MAX)
Cell 7 (md):  Observation ("2.1M lots across 18 months; OEE tracked since …")

--- Triplet 3: is the operation healthy at a glance? ---
Cell 8 (md):  Q: "What's the overall OEE, and how many cells are below target?"
Cell 9 (sql): AVG(Oee_Pct) overall + count of work centers under, say, 60%
Cell 10 (md): Observation ("Fleet OEE averages 71%; 14 of 133 cells sit below 60% …")

--- (2–4 more triplets: portfolio by focus factory, shift coverage, etc.) ---

Cell N (md): What's Next → Tutorial 02 (OEE performance) → Genie space → Model Guide
```

### Generation Rules

- Pick questions a plant manager would actually ask on day one — scale and health, not schema
- Each SQL cell is a COMPLETE query that answers its question; do NOT build a query up across
  cells and do NOT add a "now explore the table" cell
- The observation cell is mandatory and must quote concrete figures from the result (counts,
  percentages, date ranges) in business language
- Filter `!= -1` on any FK used in an aggregation; mention it once in the observation if it
  materially changes the number
- Keep result sets small (ranked top-N, LIMIT 10) so the reader can see the numbers behind the
  observation
- End with the "What's Next" cell (arc pointer), not a "try it yourself" prompt

---

## Tutorial 02: OEE Performance Intelligence (theme: PERFORMANCE)

**Goal:** Reader finishes with a clear picture of OEE *performance*: how it varies by focus
factory, by shift type, and over time — and who the top and bottom performers are. Same triplet
format; the queries here happen to use hierarchy joins, but they are presented as finished
answers, not as a join tutorial.

### Cell Structure — 5–7 observation triplets

```
Cell 0 (md): synced-against stamp + title
Cell 1 (md): Orientation — "This notebook answers: where is OEE strong or weak, and is it
             trending up or down?" (NOT "what is a star schema")

--- Triplet 1: OEE by focus factory ---
Cell 2 (md):  Q: "Which focus factories run the best and worst OEE?"
Cell 3 (sql): AVG(Oee_Pct) by focus factory (fact → dim_work_center → dim_focus_factory,
              WHERE Work_Center_Key != -1) — one complete query
Cell 4 (md):  Observation ("Focus factory A leads at 79%; D trails at 58% — a 21-pt spread …")

--- Triplet 2: OEE by shift type ---
Cell 5 (md):  Q: "Does OEE differ across shifts?"
Cell 6 (sql): AVG(Oee_Pct) by shift (fact → dim_shift)
Cell 7 (md):  Observation ("Nights run 6 pts below days — 68% vs 74% …")

--- Triplet 3: month-over-month trend ---
Cell 8 (md):  Q: "Is OEE improving or slipping?"
Cell 9 (sql): AVG(Oee_Pct) by month
Cell 10 (md): Observation ("Up 4 pts since January, flat the last two months …")

--- Triplet 4: top / bottom cells ---
Cell 11 (md): Q: "Which specific cells are our best and worst performers?"
Cell 12 (sql): ranked cells (RANK / ORDER BY), top 5 + bottom 5
Cell 13 (md): Observation naming the actual best/worst cells and their OEE

--- (1–3 more triplets as the data supports) ---

Cell N (md): What's Next → Tutorial 03 (production flow) → Genie space → Model Guide
```

### Generation Rules

- Each triplet is self-contained: one business question, one complete query, one observation
  with real numbers. Do NOT build a single query up across six cells.
- The queries use the plant → focus_factory → work_center hierarchy, but frame them as answers
  ("OEE by focus factory"), never as a lesson in how joins work
- Always filter `WHERE {Fk}_Key != -1` in aggregations; note the effect in the observation only
  if it changes the number materially — do not give the -1 pattern its own teaching cell
- Observations must quote the actual figures (spreads, deltas, named leaders/laggards) in the
  language an operations lead would use
- End with the "What's Next" cell, not a "now you try" practice cell

---

## Tutorial 03: Production and Supply Chain (theme: FLOW)

**Goal:** Reader finishes understanding how work *flows* through the operation — production
cadence, volume concentration, job complexity, and BOM structure. Same triplet format; this
notebook goes a little deeper (a cross-fact question, a time-series question) because the reader
has the scale and performance context from 01 and 02.

### Cell Structure — 5–7 observation triplets

```
Cell 0 (md): synced-against stamp + title
Cell 1 (md): Orientation — "This notebook answers: how does production flow, where does volume
             concentrate, and how complex are our jobs and BOMs?"

--- Triplet 1: WIP aging ---
Cell 2 (md):  Q: "How much WIP is aging, and which jobs are stuck?"
Cell 3 (sql): open WIP jobs bucketed by age (0–7 / 8–30 / 30+ days)
Cell 4 (md):  Observation ("38% of open jobs are past 30 days; oldest is 214 days …")

--- Triplet 2: cross-fact — lots per job ---
Cell 5 (md):  Q: "How do production lots relate to WIP jobs?" (a cross-fact question —
              proves the model is integrated)
Cell 6 (sql): lots per job distribution (fact_production_lot → fact_wip_job via Wip_Job_Key)
Cell 7 (md):  Observation naming the grain difference in business terms ("jobs average 4.2
              lots; a handful carry 40+ — these are the long campaigns …")

--- Triplet 3: production volume trend (time series) ---
Cell 8 (md):  Q: "How has production volume moved?"
Cell 9 (sql): daily lot count with a 7-day rolling average (window function)
Cell 10 (md): Observation ("Volume peaked in March at ~9K lots/day, then settled to ~6K …")

--- Triplet 4: BOM landscape ---
Cell 11 (md): Q: "How complex are our BOMs?"
Cell 12 (sql): components per BOM header (dim_manufacturing_bom_header → _bom_line)
Cell 13 (md): Observation ("Median BOM has 12 components; the largest has 143 …")

--- (1–3 more triplets as the data supports) ---

Cell N (md): What's Next → Genie space (ad-hoc questions) → Model Guide (full reference).
            "You've seen the scale (01), the performance (02), and the flow (03) — for anything
            else, ask Genie."
```

### Generation Rules

- Each triplet answers a REAL business question, derived from the fact-story narratives in
  `docs/explanation/domain_narrative.md`
- Include at least one cross-fact question (shows the model is integrated) and at least one
  window-function / time-series question — but present each as a finished answer, not an
  "advanced SQL" lesson; if a query is genuinely complex, keep the observation focused on the
  finding, not the technique
- Every SQL cell is followed by its observation cell with concrete numbers
- End with the arc-closing "What's Next" cell pointing to Genie, then the Model Guide

---

---

## Tutorial authoring is inherently two-pass

A tutorial's observation cells must "quote concrete figures from the result" — but the cells don't
exist to run until you've written them. So authoring is **two passes, and both are mandatory**:

1. **WRITE PASS** — author all triplets (question / query / observation) using figures you already know:
   row counts from `build_manifest.md`, FK rates from the validation summary, aggregate figures from
   quick scratchpad queries. Observation cells here may carry **approximate** figures ("the top few
   customers account for a large share").
2. **EXECUTION PASS** — run the notebook top-to-bottom, then **revise every observation cell to cite the
   exact figures the query returned** ("Customer 0001234 leads with $4.2M, 12% of total"). This is where
   the Query Validation Gate below fires: a 0-row result triggers diagnosis and a pivot, and an
   approximate observation becomes a precise one.

The write pass is not optional (you can't run cells that don't exist) and the execution pass is not
optional (an un-executed tutorial with approximate numbers has not passed the gate). Do not ship after
the write pass alone.

## MANDATORY: Query Validation Gate

**Every SQL cell in a tutorial MUST be executed and return non-empty results before the tutorial is
complete. A tutorial that compiles without errors but returns 0 rows has FAILED its goal. Do not
ship a tutorial without running it.**

### Validation Protocol (run before declaring Phase 6 done)

1. **Verify column names via `readTable` before writing SQL** — never rely on memory or DDL. The
   schema in the database is the ground truth. Date columns in particular differ by table
   (e.g., `Shift_Date` in `fact_oee_record`, NOT `Record_Date`).

2. **Probe every FK join path before building a tutorial around it**:
   ```python
   n = spark.sql("""
     SELECT COUNT(*) FROM catalog.schema.fact_table f
     JOIN catalog.schema.dim_table d ON f.Fk_Key = d.Pk_Key
   """).collect()[0][0]
   print(f"Join returns: {n:,} rows")
   ```
   A UC-registered FK does NOT guarantee the surrogate keys actually match at query time — 
   especially in sandbox environments where dim and fact tables may have been populated from
   different source runs. Treat a 0-row join as a **data gap**, not a SQL error.

3. **If a join returns 0 rows, diagnose before redesigning**:
   ```python
   # Sample both sides to see if keys overlap
   fact_keys = spark.sql("SELECT DISTINCT Fk_Key FROM fact LIMIT 10").collect()
   dim_keys  = spark.sql("SELECT DISTINCT Pk_Key  FROM dim  LIMIT 10").collect()
   print(set(r[0] for r in fact_keys) & set(r[0] for r in dim_keys))
   ```
   Test ALL FK paths in the model before choosing which to use in the tutorial. Some will work;
   others may not be populated yet.

4. **If the planned join path is broken, pivot the tutorial — do not fake it**:
   - Choose a different FK join that DOES return rows (e.g., `fact_oee_record → dim_shift`
     instead of `fact_oee_record → dim_work_center` when work_center keys are unmatched)
   - Update the tutorial question to match the working data
     (e.g., "OEE by shift type" instead of "OEE by focus factory")
   - Show the broken-path hierarchy as a **dimension-only query** to preserve the concept:
     `SELECT wc.Work_Center_Name, ff.Focus_Factory_Name FROM dim_work_center wc JOIN
     dim_focus_factory ff ON wc.Focus_Factory_Key = ff.Focus_Factory_Key WHERE ...`
   - DO NOT write a tutorial step that returns 0 rows — readers lose trust immediately

5. **After all cells are edited, run every SQL cell in sequence** and check:
   - No syntax errors
   - No 0-row results (except for steps that intentionally demonstrate empty results as part of
     the teaching narrative — and those must be followed by a step that adds the missing filter)
   - The data values shown are meaningful (not all NULLs, not all -1s)

6. **If results are wrong, iterate**:
   - Re-check column names, join keys, and filter predicates
   - Re-run the cell after each fix
   - Repeat until all cells return expected non-empty, meaningful results

---

## Universal Tutorial Rules

1. **Triplet format only** — [md: business question] → [sql: one complete answer] → [md:
   observation with concrete numbers]. 5–7 triplets per notebook.
2. **One finding per SQL cell** — each query answers exactly one business question; do not build
   a query up across cells and do not stack multiple findings in one result.
3. **The observation cell is the payload** — it must quote real figures from the result (counts,
   percentages, spreads, named leaders/laggards, date ranges) in the language a business
   stakeholder would use. No "this query joins X to Y" narration of the SQL.
4. **Insight showcase, not SQL lesson** — no "What is a star schema?", no "Step 1 — start with
   the fact", no "now you try". If a cell teaches SQL mechanics rather than revealing the
   operation, delete it.
5. **Scale → performance → flow arc** — 01 establishes scale, 02 explains performance, 03 shows
   flow; each notebook builds on the context of the prior.
6. **Real data, real results** — queries return actual data from the model (not mocked)
7. **Small results** — ranked top-N or LIMIT 10 so the reader sees the numbers behind the claim
8. **Filter -1 Unknown** — always `WHERE {Fk}_Key != -1` in aggregations; note the effect in the
   observation only if it changes the number materially (it does not get its own teaching cell)
9. **Explain the unexpected** — if a number looks surprising (OEE > 100%, high aging), say why in
   the observation
10. **`synced-against` stamp in Cell 0/1** — every tutorial's first markdown cell carries the
    stamp, per `domain-sync/staleness-linter.md`
11. **End with "What's Next"** — the last cell points to the next tutorial → Genie → Model Guide
12. **Runnable top-to-bottom** — tutorials work as sequential execution (no external state)
13. **SQL-shape notebook format (MANDATORY)** — tutorials are **SQL-shape** notebooks, always, and are
    language-invariant (independent of `conventions.yml` `etl_language`). The first pass shipped them as
    **Python-shape** (`# Databricks notebook source`, cells wrapped in `# MAGIC %sql`) — that is off-spec.
    Two steps: (1) `createAsset(assetType='notebook', name='...')` → returns `assetId`; (2)
    `editAsset(operation='update', ...)` to populate the cells and **set the asset `language` to
    `'SQL'`**. `createAsset` does NOT take a `language` argument — language is set on `editAsset` (the
    same mechanism the validation skill uses — see `domain-model-validation` SKILL.md). One difference
    from the validation notebooks: those set `language` to *match* `etl_language`; tutorials are ALWAYS
    `'SQL'` regardless of `etl_language` (a documentation artifact, not part of the ETL language choice —
    do NOT hard-code Python and do NOT follow `etl_language` here). First line
    `-- Databricks notebook source`; cell separator `-- COMMAND ----------`. See
    `etl-development-framework/deployment-and-dab.md` "Notebook-format contract" (tutorials are Shape A).
    **Read-back gate (this rule does not enforce itself):** after the `editAsset` that populates each
    tutorial, read the asset back and assert (a) first line `-- Databricks notebook source`, (b) **no
    `# MAGIC` prefix anywhere** in the source, (c) asset `language == 'SQL'`. A prior run reported
    compliance while shipping Python-shape tutorials — verify by read-back, don't trust recollection.
    Re-emit SQL-shape and re-check if any assertion fails.
14. **Markdown cells use `-- %md` prefix** (NOT `# MAGIC %md`); SQL cells are raw SQL (NOT wrapped in
    `# MAGIC %sql`) — consistent with SQL-shape notebook conventions.
15. **Execute every SQL cell before shipping** — see Query Validation Gate above. No exceptions.

---

## Generation Input Sources

| Triplet element | Source |
| --- | --- |
| Business questions (the md before each SQL) | `docs/explanation/domain_narrative.md` fact/dim stories |
| Scale figures (01) | `docs/.pipeline/state/run/progress.md` row counts + `docs/.pipeline/handoffs/silver/build_manifest.md` final counts |
| Performance queries (02) | FK relationships from DDL (framed as answers, not join lessons) |
| Cross-fact / flow questions (03) | `docs/explanation/domain_narrative.md` cross-reference matrix + fact stories |
| Observation numbers | the live query result (quote the actual figures returned) |
| Known caveats to note | `docs/.pipeline/handoffs/silver/validation_summary.md` gap deltas + `docs/.pipeline/state/run/progress.md` fixes |
| Time series | Fact tables with date columns (`build_manifest.md` names the date column) |

---

## Maintenance

For point updates after the model is built, do NOT hand-regenerate tutorials — load
`domain-sync`, which scopes the regeneration and re-stamps `synced-against`. Tutorials warrant
regeneration when:
- A new table adds a business question worth a triplet
- FK relationships change (a performance/flow query's join path changes)
- New business questions emerge from an updated narrative
- The hierarchy changes (focus-factory/cell framing shifts)

Regeneration is idempotent — full replacement of notebook cells; the first markdown cell's
`synced-against` stamp is refreshed on every regeneration.
