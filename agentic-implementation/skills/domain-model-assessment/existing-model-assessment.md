# Existing Model Assessment — Phase 3

This phase answers: **can an existing production silver or gold model be folded into V2?**
Run this for every schema discovered in or adjacent to the target domain.

---

## Step 3.0 — Early-exit gate (is there anything to integrate?)

**Run this ONE check before the rest of Phase 3.** Phase 3 is heavy (grain analysis, purpose
classification, integration options A/B/C, Step 3.8 KPI oracle), but on a green-field domain it
collapses to nothing — and forcing the full protocol over an empty result set is wasted motion (the
sales-order run had no existing sales_order silver/gold and still walked the whole phase).

Confirm whether any existing model exists to integrate. Scan **every catalog that could hold one** —
the gold catalog AND the silver/sandbox catalog (they are often different). Run one probe per
catalog (union the results mentally; UC `information_schema` is per-catalog, so you cannot cross-join
catalogs in a single query):
```sql
-- Repeat this for EACH of: {gold_catalog} (conventions.yml catalogs.gold) and
-- {silver_catalog} / {sandbox_catalog} (where a V1/MVP silver model would live).
-- {domain} MUST be substituted lowercase (the columns are lowercased; the literal must match).
SELECT '{this_catalog}' AS catalog, table_schema, table_name
FROM {this_catalog}.information_schema.tables
WHERE LOWER(table_schema) LIKE '%' || LOWER('{domain}') || '%'
   OR LOWER(table_name)  LIKE '%' || LOWER('{domain}') || '%';
```
- **Every probed catalog returns 0 tables** AND the Phase 2B V1/MVP inventory found no populated
  shell → **Phase 3 = "No existing model to integrate."** Record that one line in the report and
  **skip to Phase 4.** Do NOT fabricate integration options for a model that doesn't exist.
- **Any catalog returns tables** → proceed with Step 3.1 onward as normal.

> **Do not early-exit on the gold catalog alone.** A V1/MVP silver model frequently lives in a
> different catalog than gold; skipping the silver/sandbox probe would wrongly declare "nothing to
> integrate" over a real existing model. If you cannot resolve the silver/sandbox catalog, do NOT
> early-exit — fall through to Step 3.1 and let Phase 2B's inventory be the authority.

> Keep the Step 2.5 gold-as-source check (discovery-protocol §2.5) separate — that runs per-entity
> during Phase 2 to demote Blocked grades and is unaffected by this gate. Step 3.0 only decides
> whether the *integration* analysis (3.1–3.8) has a subject.

---

## Step 3.1 — Inventory the Existing Model

Collect:
- All table names + types (BASE TABLE vs MATERIALIZED VIEW vs VIEW)
- Row counts
- Source system(s) each table reads from
- Grain description (what is one row?)

```sql
SELECT t.table_name, t.table_type, t.comment
FROM {catalog}.information_schema.tables t
WHERE t.table_schema = '{schema}'
ORDER BY t.table_name;
```

Then batch row counts:
```sql
SELECT '{t}' AS tbl, COUNT(*) AS rows FROM {catalog}.{schema}.{t}
UNION ALL ...
```

Also check for any MATERIALIZED VIEW definitions (capture their SQL):
```sql
SHOW CREATE TABLE {catalog}.{schema}.{mv_name};
```

### Step 3.1.1 — Proven-mapping inheritance (default depth — skip only under a fresh-start declaration)

A populated prior build (a V1/MVP, or a sibling ETL variant per `model-completeness-protocol.md` Phase 2B.1)
is **proven ground truth**, not just an inventory line. Unless the user declared a fresh start
(SKILL.md Phase 0), mine it — a shallow "17 MVs exist, moving on" pass throws away confirmed
mappings you would otherwise re-derive:

1. **Row-count comparison** — prior-build table vs current bronze (detect drift/regression: a prior
   entity that loaded N rows against a bronze that now has ~N is a confirmed, still-valid load).
2. **Column intersection** — which prior-build columns have no counterpart in the V2 metamodel
   (dropped), and which V2 attributes the prior build already sourced (carried).
3. **Proven-mapping inheritance** — if the prior build successfully loaded entity X from source Y on
   column Z, that source→target mapping is **CONFIRMED**: inherit it into Step 2.4b rather than
   re-validating grain/FK from scratch. Cite it as "prior-build proof: N rows via `{source.col}`".

This is the deeper default that a fresh-start declaration deliberately turns off (it says "don't
inherit conclusions"). When Phase 2B.1's abbreviated path applies, this inheritance IS the port.

---

## Step 3.2 — Grain Analysis (Critical)

For each fact table in the existing model, determine its grain:
- **What is one row?** (one event? one daily aggregate? one demand line? one LPN?)
- **What is the coverage scope?** (all plants? only DFF-connected? only one source system?)
- **How does this grain compare to the V2 target entity?**

Grain mismatch types:
| Mismatch | Description | Implication |
| --- | --- | --- |
| Scope mismatch | Existing covers a subset of the domain (e.g., DFF plants only vs all EBS plants) | V2 needs additional source to fill the gap; existing model is a partial feed only |
| Level mismatch | Existing is at a finer or coarser grain than V2 target | Aggregation or explosion required; complex transformation, not a simple copy |
| Entity mismatch | Existing uses a different primary entity (e.g., LPN vs WIP job) | Not a fold-in; the two models answer different questions |
| Full overlap | Existing covers the same population at the same grain | Clean fold-in candidate — proceed to Step 3.3 |

**Rule:** Only proceed toward fold-in recommendation if grain is Full Overlap.
For Scope or Entity mismatch, recommend consume-as-source or downstream instead.

---

## Step 3.3 — Naming & Structural Convention Comparison

Compare the existing model against the V2 (framework) standards:

| Dimension | Check | Pass / Fail |
| --- | --- | --- |
| Column case | Business columns in `Pascal_Snake_Case`? | |
| Metadata prefix | Uses `_lower_snake_case` with leading `_`? (not `DF_` legacy ADF prefix) | |
| Surrogate keys | `{Entity}_Key` BIGINT pattern? | |
| PK/FK constraints | Informational UC constraints declared? | |
| Column comments | All columns have meaningful business comments? | |
| UC tags | `dbx_data_type`, `dbx_subdomain`, `dbx_business_glossary_term` applied? | |
| Source system column | `_source_system` present (not `Source_System` or absent)? | |
| Metadata columns | `_loaded_at`, `_batch_id` present (not `DF_Processing_Dttm`, `DF_Created_On`)? | |

Scoring: 0–3 Pass = Incompatible (refactor required); 4–5 Pass = Partial refactor; 6–8 Pass = Compatible

---

## Step 3.4 — Purpose Classification

Classify the existing model as one of:

**Semantic Contract (Silver-appropriate):**
- Generic, multi-use-case design
- No computed KPIs or window functions in base tables
- No single-use-case joins baked in
- Applies to multiple dashboards / Genie spaces / consumers
- Columns match business entities, not report requirements

**Gold-pattern (misclassified as Silver):**
- Designed for one use case or one report
- Contains computed KPIs (compliance flags, efficiency scores, on-time flags)
- Denormalised for one consumer
- Uses window functions in base table definitions
- References a specific downstream report schema

If classified as Gold-pattern: recommend re-homing to gold schema as part of the V2 transition.
The business does not lose the output — it just gets served from a better-governed Silver layer.

---

## Step 3.5 — Integration Option Selection

Based on Steps 3.2–3.4, select one of three integration options:

### Option A — Fold-In (V2 replaces existing)
**Use when:** Full grain overlap + naming conventions compatible + semantic contract purpose.
**Process:**
1. V2 entities absorb the existing model's entities
2. Existing ETL re-pointed at V2 Silver schema
3. Gold consumers continue unchanged (same output schema)
4. Existing silver schema deprecated after parallel run

**Risks:** Migration effort; downstream dashboards must be re-validated.

### Option B — Consume-As-Source (short-term)
**Use when:** Existing model is trusted, validated, and provides cleaner data than re-reading bronze,
but grain/naming mismatch makes direct fold-in impractical.
**Process:**
1. V2 MERGE notebooks read from existing silver tables (not bronze) for affected entities
2. Column remapping applied in the MERGE SELECT (old naming → V2 naming)
3. No changes to existing production model
4. Dependency documented; V2 breaks if existing schema changes

**Risks:** Silver-reads-from-Silver dependency chain; schema change fragility.
**Mitigate by:** Adding an explicit source contract test in the V2 validation notebook.

### Option C — Downstream (V2 as upstream, existing as consumer)
**Use when:** Existing model is Gold-pattern; V2 Silver becomes its upstream source.
**Process:**
1. V2 Silver built independently (no dependency on existing model)
2. Existing model's MV/view SQL is re-written to read from V2 entities
3. Output schema of existing model preserved (no downstream impact)
4. Existing ETL job updated to refresh V2 first, then existing model

**Risks:** Re-writing the existing model's ETL; parallel run required to confirm parity.
**This is the correct long-term architecture** when the existing model is Gold-pattern.

---

## Step 3.6 — Source Quality Uplift Table

For every DFF silver table that maps to a V2 entity under Option B (consume-as-source),
document the quality uplift vs re-reading bronze:

| Existing table | V2 entity | Quality uplift | Coverage caveat |
| --- | --- | --- | --- |
| (example) `fact_material_transaction` | `wip_material_transaction` | Pre-filtered to ABL orgs; already deduped; has surrogate keys. Saves re-reading 992M bronze rows | None — full org coverage |
| (example) `fact_lpn_header` | `production_lot` | LPN-to-WIP linkage pre-joined; production dates computed | DFF-connected plants only; non-DFF plants have no LPN records |

---

## Step 3.7 — Produce Grade Amendments

After completing Steps 3.1–3.6, produce a table of revised S2T grades:

| V2 Entity | Previous grade | Revised grade | Reason |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

**Revised summary: X Full · Y Partial · Z Blocked** (was A/B/C)

Append this table to the S2T Mapping Report under "Updated Discovery Report Amendments".

---

## Step 3.8 — Existing Gold / Dashboard KPI Coverage (the comprehensiveness oracle)

The prior steps treat existing models as *fold-in / consume / downstream* candidates. This step
treats **legitimately-gold models — and the dashboards they feed — as the coverage oracle**: the
best evidence for whether the new silver model is *comprehensive enough* is whether it can
support the KPIs the business already computes. If an existing gold layer computes a metric the
new silver cannot feed, the silver has a real gap — surfaced here, not discovered at build time.

**Keep this role distinct from the two other gold checks (they do not overlap):**

| Step | Gold's role | Question it answers |
| --- | --- | --- |
| **2.5** — Gold as **source** | Gold table used as an *input* | "Can a processed gold table populate a Blocked entity and demote its grade?" |
| **3.4** — Gold-shaped **mis-homed silver** | A table *labeled* silver that is really gold | "Is this 'silver' model actually a use-case-specific gold pattern to re-home?" |
| **3.8** — Gold as **coverage oracle** (this step) | A *legitimately-gold* model as a *grading target* | "Does the new silver model *support* every KPI existing gold/dashboards compute?" |

### Step 3.8.1 — Discover legitimately-gold models and their KPIs

Identify the production gold models in/adjacent to the domain (from the Step 2.5 gold check and
the `catalogs.gold` catalog in `conventions.yml`) that are **legitimately gold** — computed
KPIs, denormalised for consumers, window functions, report-shaped (the Step 3.4 signature, but
here correctly homed in gold). For each, enumerate the KPIs / metrics it computes. Sources:
- Metric-view definitions and gold MV / view SQL (`SHOW CREATE TABLE` — capture the aggregations)
- Dashboard datasets / tiles the gold model feeds (compliance %, OEE %, on-time %, monthly qty)
- Business-glossary metric terms already tagged in the domain

### Step 3.8.2 — Grade silver support for each KPI

For each KPI, decide whether the **new silver model can feed it** and grade the coverage:

| Grade | Definition |
| --- | --- |
| **Supported** | Every input the KPI needs (grain, measures, dimensions, join keys) exists in a buildable silver entity |
| **Partial** | The KPI can be *approximated* but a dimension/measure/grain it needs is missing or coarser (state exactly what) |
| **Unsupported** | A structural input is absent — the silver model cannot feed this KPI without a model change |

Output the KPI-coverage table:

| # | KPI / Metric | Computed by (gold/dashboard) | Inputs it needs (grain · measures · dims) | Silver support | Missing input | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | (example) Schedule Compliance % | `o9_gold` compliance MV + DFF dashboard | job grain · scheduled vs actual completion date · plant, focus_factory | Partial | `focus_factory` dimension absent | vibe-model prompt (structural) |
| 2 | (example) OEE % | DFF OEE dashboard | shift grain · availability × performance × quality · line, shift | Unsupported | `shift` dimension absent | vibe-model prompt (structural) |
| 3 | (example) Monthly Production Actuals | gold `production_actuals` MV | month × plant · completed qty | Supported | — | — |

### Step 3.8.3 — Route gaps to the human gate

- **Unsupported / Partial KPIs whose missing input is structural** (a missing entity, dimension,
  hierarchy level, or grain) → add a **P-item** to the Gap Registry **and** emit a **vibe-model
  prompt** to iterate the model upstream. These route to the **same human gate as Phase 2C /
  Step 2.7** (`model-completeness-protocol.md` Step 2C.4) — the two disposition paths apply unchanged:
  **iterate upstream** (recommended for structural KPI gaps) or **edit in place via Genie Code**
  (if a small metamodel add — e.g. one attribute — closes the gap).
- **Partial KPIs whose gap is an ingestion ask** (source not yet landed, model shape is fine) →
  add the P-item to the Ingestion Ask table; no model change needed.

Append the KPI-coverage table to the S2T Mapping Report alongside the grade amendments. A silver
model that supports every existing gold KPI is the strongest signal it is comprehensive; each
Unsupported KPI is a concrete, evidence-backed comprehensiveness gap.
