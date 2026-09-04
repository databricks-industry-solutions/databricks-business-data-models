# Gold Derivation Protocol — Silver → Gold (Mode B)

The bronze → silver protocol (`discovery-protocol.md`) discovers whether *data supports the model*.
This protocol does the opposite job: the silver 3NF model is already built, typed, and documented —
now **derive a dimensional gold star from it**. There is no bronze to profile, no format detection,
no mutability probe. The hard part moves from *discovery* to *design*: which 3NF entity becomes a
dim, which becomes a fact, what grain, which dims conform.

> **When this protocol runs.** `output_model: hybrid` **only** — as the *second* assessment pass,
> after the silver 3NF build has landed as populated tables. The SKILL.md **Mode Gate** routes here.
> **`dimensional` does NOT enter this protocol** — a dimensional model's `dim_/fact_` star IS the
> silver target (built in one Mode A pass from bronze); its gold layer is marts + metric views over
> that star (see `etl-development-framework/gold-and-metrics.md`), not a re-derived star. See
> `source-to-target-mapping.md` "Mode-Specific Report Scope".

---

## Why the bronze phases don't apply (skip list)

For a silver → gold assessment, these Mode-A steps are **irrelevant** — do not run them:

| Mode-A step | Why it's skipped for gold |
| --- | --- |
| 2.1 Identify candidate schemas | Silver IS the source — one known schema |
| 2.2 Schema-wide table search | Silver tables are already inventoried in `etl_detailed_spec.md` |
| 2.6 Mutability probe (bronze *discovery* only) | Skip the bronze append-only *discovery* — gold reads typed silver, not raw bronze. **But do NOT skip the gold object-type decision**: `type_2` dims → AUTO CDC, and high-volume append-only *facts* → Streaming Table, not MV. Handled in Step G6, keyed on the already-known silver row counts + mutability. |
| 2.7 Model assertion validation | There is no declared gold model in the metamodel to validate against |
| Date-format detection | Silver is already typed (DATE/TIMESTAMP/DECIMAL) |

**What replaces them — Silver Source Profiling (3 queries, not 20):**
1. Row counts per silver table (sizes the facts, confirms dim cardinalities)
2. FK graph confirmation (the silver PK/FK edges become the star's join paths)
3. Cardinality + distinct-value probes on candidate dimension columns (confirms grain)

This is fast *because* silver is clean. Budget ~15 tool calls for a full gold assessment vs 20–30
for bronze.

---

## The metamodel has no gold representation — declare it, don't validate it

**Critical divergence from Mode A.** The vibe model emits only 3NF entities. There is **no gold
star in the metamodel** to quote as "intent" (Critical Rule #3 has no silver→gold analogue). So the
gold assessment is a **design OUTPUT, not a discovered reconciliation**. Consequences:

- Ground each gold object's intent in the **silver entity's** `description` + the **business KPIs**
  it serves (from `business_requirements.md`), not in a nonexistent gold metamodel row.
- The output is the authoritative gold spec. Downstream validation grades the build against *this
  document*, not against the metamodel.
- Do **not** write gold entities back to the metamodel. The metamodel stays 3NF; gold lives only in
  the assessment doc and the built schema. (This preserves Mode-A Critical Rule #2 — the metamodel
  is not edited outside the Phase 2C/2.7 gate.)

---

## Step G0 — Intake business-provided gold requirements (optional, preferred)

**Grain and dimensionality are business decisions, not purely derivable from silver structure.** A
business user or data engineer frequently knows concrete requirements the model can't infer — "OTD
at ship-to × week", "revenue by sales rep and region", "credit exposure snapshotted monthly". Before
deriving anything, **ask for a gold requirements brief** (or check whether one was handed in). This
seeds and *overrides* the derivation instead of forcing the agent to guess grains from silver alone.

**If a brief is provided**, treat each entry as an authoritative requirement:
- A requested **fact grain** → the target grain for Step G2 (overrides the "finest grain" default
  only if the user's grain is coarser *by intent* — still build the atomic fact underneath and add
  the requested summary fact on top; never lose drill-down).
- A requested **dimension / slice** → a required dim + FK in Step G3, even if no fact references it
  yet (flag as "requested, not yet used").
- A requested **measure / KPI** → a required column feeding Step G5's coverage matrix.

**Reconcile every requirement against silver — no silent descoping (MANDATORY, same as Mode A):**

| Requirement vs silver | Disposition |
| --- | --- |
| Silver fully supports it | Build it; mark **Supported** in the KPI matrix |
| Silver supports it partially (e.g. grain exists but a slice attr is missing) | Build what's possible; record the gap **Partial** with the missing attribute |
| Silver cannot support it (grain/dim/measure has no source) | **Never drop it** — record a gold gap using the canonical two-axis scheme (see Step G5: cause = *missing-data*/*missing-design*, priority P0–P2) with the unblock action |

**If no brief is provided**, fall back to KPI-inference from `business_requirements.md` + the domain
narrative (what the sales-order run did) — but say so explicitly in the assessment header, because an
inferred requirement set is weaker evidence than a stated one. Prompt the user once: *"Do you have
known gold grains/dimensions/KPIs the business needs? Providing them now produces a sharper star than
inferring from silver."*

> Use `templates/gold_requirements_brief.md` as the intake shell. It is a **human gate**, not a hard
> blocker — the protocol proceeds either way, but a provided brief is the strongest input it can get.

---

## Step G1 — Fact vs Dimension vs Bridge vs Absorbed (decision tree)

Classify every silver entity into exactly one gold role. Run top-to-bottom; first match wins.

```
For each silver entity E:

1. Does E have additive/semi-additive MEASURES at its grain
   (quantity, value, amount, count, duration)?
   YES → E is a FACT candidate. Go to Step G2 (grain selection).
   NO  → continue.

2. Is E a reference/lookup/master (customer, material, reason code,
   channel, contract, sales area, calendar)?
   YES → E is a DIMENSION. Go to Step G3 (conformed check).
   NO  → continue.

3. Is E a M:N associative table, OR a table that pivots >3 roles onto a
   parent (e.g. order_partner: Sold-To / Ship-To / Bill-To)?
   YES → E is a BRIDGE (or a pivot-to-wide onto the fact). Go to Step G4.
   NO  → continue.

4. Is E a subordinate detail whose columns are better carried as
   attributes on a parent fact/dim (e.g. a header table whose fields
   denormalize onto the line fact)?
   YES → E is ABSORBED. Record which parent absorbs it and which columns survive.
   NO  → E is a passthrough DIMENSION (small reference table, 1:1 to gold dim).
```

**Record the classification for every silver entity** — even ABSORBED ones — so the reader can see
nothing was silently dropped (the Mode-A "no silent descoping" rule applies to gold too: a silver
entity that becomes no gold object must be explicitly marked ABSORBED or OUT-OF-SCOPE, never
omitted).

---

## Step G2 — Fact grain selection

**A business-provided grain (Step G0) wins** — if the requirements brief names a grain for this
process, that is the target. Otherwise apply the default rule below. Either way, build the atomic
fact so drill-down is never lost; a requested coarser grain becomes an additional summary fact.

**Default rule (no brief): pick the finest grain that carries additive measures.** A line-grain fact
rolls up to header totals; a header-grain fact cannot drill down to lines. When in doubt, go finer.

| Silver shape | Gold fact grain | Rationale |
| --- | --- | --- |
| header + line tables | **line grain** | finest additive grain; header attrs denormalize down |
| schedule-line / delivery-line | **schedule-line grain** | OTD, fulfillment measured per schedule line |
| event log (credit check, status) | **event grain** | one row per event; measures are point-in-time |
| already-atomic single table | **that grain** | no finer grain exists |

**Wide-fact denormalization:** carry header attributes (Order_Type, Overall_Status, dates) ONTO the
line fact rather than forcing a runtime join to a header dim. Minimizes query-time joins. Document
which header columns are denormalized vs which become FK-to-dim.

**Additivity classification (required per measure):** label each measure `Additive` (sums across all
dims — quantity, value), `Semi-Additive` (sums across non-time dims, but only snapshots/averages
across time — on-hand balance, inventory level, headcount), or `Non-Additive` (ratios, percentages,
prices — never SUM; e.g. utilization %, margin %). This tells the metric layer how to
aggregate and prevents the #1 dashboard bug (SUM of a percentage).

**Consider a summary/aggregate fact** when a KPI is queried at a coarser grain than the atomic fact
(daily revenue, monthly OTD). Flag it as a candidate — do not auto-build — with the grain and the
dashboard query it accelerates. (The atomic fact is mandatory; the summary is an optimization.)

---

## Step G3 — Conformed dimension identification

A dimension is **conformed** when the same dim serves multiple facts with identical keys/attributes
(customer, material, date). Conformance is what makes the star drillable across processes.

**Checklist per candidate dimension:**
1. **Is it referenced by ≥2 facts?** If yes → conformed; build once, key consistently.
2. **Does a cross-domain authoritative source exist?** (customer master in a `customer` domain,
   material master in `product_catalog`.) Run the **Conformed Dimension Resolution** below.
3. **Role-playing?** One physical dim referenced under multiple names (dim_date as Order_Date,
   Requested_Delivery_Date, Quote_Date). Build the dim once; expose N FK roles on the facts.
   Document each role.
4. **Degenerate dimension?** A dimension with no attributes beyond its key (Order_Number,
   Line_Number) — carry it as a fact attribute, do NOT build a separate dim.

### Conformed Dimension Resolution (cross-domain)

Gold dims frequently need enrichment from *other* domains. Decide, per dim, using this framework —
and record the decision (this was the single most-improvised call in the sales-order run):

| Situation | Decision | Action |
| --- | --- | --- |
| Local silver has the key + enough attrs to be useful | **Skinny now** (default) | Build from local silver; record a DEFERRED cross-domain enrichment gap (P2) |
| Local silver has only the key; dim is useless without enrichment | **Wait** | Do not build; record the cross-domain dependency as a hard blocker (P1) |
| Cross-domain source already exists as a conformed dim | **Reuse** | FK to the existing conformed dim; do not rebuild |

Document every cross-domain dependency with: owning domain, expected attributes, and the join key.
A "skinny now, enrich later" dim (6–7 columns) is honest and correct for a first pass — but say so
explicitly, because a production conformed dim is usually 15–30 columns.

### Dimension construction — dedup grain + multi-source assembly (specify it, don't leave it to the build)

The fact side gets example JOIN SQL (output rule below); dimensions need the same rigor, because a
dim's silver source is often **not** 1:1 to the dim grain. These were the two most-improvised calls
on the sales-order gold build — the assessment must decide them, not the builder:

- **Dedup dimension (silver source coarser than the dim grain).** When the dim is sourced from a
  table that has *multiple rows per dim key* — `dim_customer` built from `order_partner` (many order
  lines per customer), any dim built from a transaction/line table — the spec MUST state the dedup
  key and recency tiebreaker: `ROW_NUMBER() OVER (PARTITION BY <natural_key> ORDER BY <tiebreaker>
  DESC) = 1`. Name the actual `<natural_key>` and the `<tiebreaker>` column (a load/update timestamp,
  or a deterministic fallback). Without this the builder guesses, and a wrong tiebreaker silently
  picks stale attribute values.
- **Multi-source / UNION dimension (assembled from >1 silver table).** When no single silver table
  holds the dim — `dim_material` UNION-ed from `order_line` + other line/reference tables — the spec
  MUST state: which silver tables are UNION-ed, the `UNION [ALL]` + post-union dedup (same
  `ROW_NUMBER` rule on the conformed key, since the same member appears in multiple sources), and
  **which attributes survive** (the conformed column set) vs which are source-local and dropped.
- **1:1 passthrough dim** (silver reference table already at dim grain) needs neither — say so, so the
  reader knows the omission is deliberate.

Record the chosen construction per dim in its spec (the "dim construction SQL" required by the output
rule below), exactly as facts record their JOIN SQL.

> **Every FK-resolution / lookup JOIN must be 1:1 on the lookup side — flag it when it isn't.** This
> is the general form of the bridge fan-out warning (Step G4) and the ETL build's Rule 3/11: a LEFT
> JOIN whose right side has duplicate join-key rows multiplies the fact (a real build fanned out
> `order` → 136 dup rows joining a non-unique `quote.converted_order_number`). For every fact→dim and
> dim-assembly join in the spec, **verify the join key is unique on the lookup side**; where it isn't,
> state the dedup CTE the build must apply. Surface non-unique join keys as an explicit note so the
> ETL build is warned in the spec, not by a failed grain check.

---

## Step G4 — Bridge tables

Use a bridge (vs denormalizing onto the fact) when:
- A parent pivots **>3 roles** onto children (order_partner → Sold-To/Ship-To/Bill-To), OR
- There is a genuine **M:N** relationship (order ↔ promotion).

**Grain-mismatch warning (learned the hard way):** if the bridge is at a *coarser* grain than the
fact (e.g. `bridge_order_partner` at order-header grain, `fact_sales_order_line` at line grain),
document the join key explicitly (`join on order_id, NOT line_id`) or the build will fan out the
fact. State the fan-out risk and the correct join in the bridge spec.

---

## Step G5 — Gold Completeness Assessment (KPI-oriented, replaces Phase 2C)

Mode-A Phase 2C scans bronze for unmapped tables. For gold, that question is meaningless — the
equivalent completeness check is **KPI-driven**:

1. Enumerate business KPIs from `business_requirements.md` + the domain narrative.
2. For each KPI, trace the required **fact grain + dimensions + measures**.
3. Grade each KPI **Supported / Partial / Unsupported** against the proposed star.
4. Classify every gap on **two orthogonal axes** — this is the canonical gap scheme for the whole
   protocol; every gap in the gold gap registry (and Steps G0/G3) uses it:
   - **Cause** — *missing-data (inherited)*: a silver-layer gap the gold layer inherits (e.g. no
     `likp/lips` → OTD is a proxy); cite the silver gap ID, do not re-litigate. Or *missing-design
     (gold)*: a gold structural gap (needs a new fact/dim/measure the star doesn't yet have).
   - **Priority** — **P0** blocks a requested/committed KPI outright; **P1** degrades a KPI to
     Partial (a slice or measure is missing); **P2** is enrichment / nice-to-have (e.g. a skinny
     conformed dim awaiting cross-domain attributes). *(No P3 at gold — gold gaps are business-
     visible; if it's truly negligible it isn't a gap.)*

This KPI-coverage matrix reuses the Step 3.8 oracle machinery (Supported/Partial/Unsupported), now
pointed forward at the star being designed rather than back at an existing gold model. It is the
single most useful artifact for communicating "what the gold layer can and cannot answer."

> **Metric-view alignment.** The ETL framework produces UC **metric views** at gold. The KPI matrix
> IS the metric-view requirements list — flag which KPIs become governed metric views vs ad-hoc
> queries, so the build doesn't have to re-derive them.

---

## Step G6 — Pipeline topology (hybrid + SDP)

When gold is built as SDP (`etl_type: sdp_pipeline`), decide where the gold objects live:

| Scenario | Recommendation |
| --- | --- |
| ≤ 20 gold objects, same catalog as silver | **Same pipeline** (single DAG; simplest) |
| > 20 gold objects, or cross-catalog | **Separate pipeline** |
| Gold has a different SLA / refresh schedule | **Separate pipeline** (decouple schedules) |
| Gold reads from **multiple** silver domains | **Separate pipeline** (blast-radius isolation) |

**Gold object type — DO NOT blanket-assume MV.** Two different rules apply, one for dimensions
(keyed on `scd_strategy`) and one for facts (keyed on volume + mutability, exactly like silver):

*Dimensions & bridges:*
- **`type_1` (default):** Materialized View, full recompute. Dimensions are small — full rebuild is
  cheap and idempotent. SDP resolves dependencies from the SQL references, so explicit tier ordering
  is documentation, not execution control.
- **`type_2` dimensions:** a versioned dim **cannot** be a full-recompute MV — full recompute
  destroys the `_effective_from`/`_effective_to`/`_is_current` history. Build it as a **Streaming
  Table with AUTO CDC … STORED AS SCD TYPE 2** (per `conventions.yml scd_strategy`). Record which
  dims are `type_2` from `conventions.yml` (or the per-entity override in `etl_detailed_spec.md`).

*Facts — run the full SDP object-type decision (`sdp-strategy-mapping.md` Part 1); MV is NOT
automatic:*
- A gold fact is **not** small by default. Size it (its silver source row count is already known) and
  route it through the same four-way decision as a silver fact — the tree lives in
  `sdp-strategy-mapping.md` "Streaming Table vs Materialized View vs REPLACE WHERE":
  - **Append-only, high-volume** ledger fact → **Streaming Table** (incremental append).
  - **Large + a real per-row CDC feed** (keyed change rows + sequence) → **Streaming Table with
    AUTO CDC INTO**.
  - **Large + windowed corrections / late-arriving data, no CDC feed** → **incremental `REPLACE
    WHERE` flow** (Enzyme rewrites only changed files). This is the right answer for a large mutable
    batch fact — *not* a full-recompute MV.
  - **Small, OR aggregations/joins that stay incrementalizable** → **Materialized View** (serverless
    MVs incrementally refresh; set `REFRESH POLICY INCREMENTAL[ STRICT]` if a surprise full recompute
    is unacceptable). A full-recompute MV over a billion-row fact every run is the exact anti-pattern
    the silver framework forbids — it applies at gold too.
- **State the fact's row tier + chosen object type in the assessment**, per fact — do not write "all
  gold facts are MVs." (For a *small* domain like the Meridian test — every fact < 25K rows — MV is
  the right answer for all of them; that's the low-volume case, not a general law.)

See `sdp-strategy-mapping.md` "Gold tier".

---

## Gold assessment output — required contents

Produce one `gold_layer_assessment.md` (or the gold section of the S2T report) with:

- **Assessment summary** — object counts (dims/facts/bridges), source layer, KPI coverage %, readiness
- **Star schema overview** — ASCII or list of the dim↔fact edges
- **Dimension specs** — per dim: intent, silver source(s), grain, surrogate PK derivation, cardinality, **enumerated column table (see below)**, and **dim construction SQL** when the source is not 1:1 to the dim grain (dedup or multi-source UNION — see Step G3 "Dimension construction")
- **Fact specs** — per fact: intent, silver source JOINs, grain, PK, measures with additivity labels, FK-to-dim list, **enumerated column table (see below)**, and **example JOIN SQL** (see below)
- **Bridge specs** — with the fan-out join warning, and the same **enumerated column table**
- **KPI coverage matrix** (Step G5) — Supported/Partial/Unsupported with per-KPI evidence
- **Gold gap registry** — every gap on the canonical two-axis scheme (Step G5): priority P0–P2 × cause *missing-data (inherited)* / *missing-design (gold)*
- **Human gates** — the debatable design calls (topology, key alignment, unknown-member handling)
- **Silver→gold entity mapping appendix** — every silver entity → its gold role (incl. ABSORBED)

### The column table must be an enumerable target-column contract (output-quality rule)

Every dim/fact/bridge spec carries a **flat column table keyed on the DEPLOYED gold column name** —
one row per gold column, so the ETL build and `domain-model-validation` get an enumerable contract
instead of having to parse column names out of the JOIN/construction SQL. Required columns:

| Gold column (as built) | Type | Role | Silver source col(s) | Transform |
| --- | --- | --- | --- | --- |
| `Sold_To_Number` | STRING | BK | `order_partner.customer_id` | dedup, Sold-To rows only |
| `Material_Key` | BIGINT | FK→dim_material | `order_line.material_number` | `SHA2(material_number,256)` |
| `Net_Value` | DECIMAL(15,2) | measure (additive) | `order_line.net_value` | `SUM(...)` at line grain |

- **Key on the gold name the table will actually ship** — the dimensional/Pascal name
  (`Material_Key`, `Sold_To_Number`), NOT the silver natural key it was sourced from. This is the
  exact contract that prevents the downstream validation skill from coding checks against
  `Material_Number`/`AG_Partner_Number` when the deployed table has `Material_Key`/`Sold_To_Number`.
- **Role** ∈ PK / BK / FK→{dim} / measure / attribute. Facts label measure additivity (additive /
  semi-additive / non-additive) — mirrors the Fact-spec measures list.
- The JOIN/construction SQL still ships (it defines *how*); the column table defines *what* — and it
  is the machine-readable part. This mirrors the Mode-A silver S2T "Per-Column Fields" table
  (`source-to-target-mapping.md`), so silver and gold hand off the same shape.

### Require example SQL per fact AND per non-trivial dim (output-quality rule)

The Mode-A S2T produces `CAST`/`CASE` expressions per column. The gold spec must produce, **at
minimum, the primary JOIN pattern for each fact** — which silver tables compose it, the join keys,
and the grain-preserving join order — **and the construction SQL for each dim that is not a 1:1
passthrough** (dedup or multi-source UNION, per Step G3). Prose descriptions force the ETL build to
reverse-engineer them; spell them out. Examples:

```sql
-- fact_sales_order_line — line grain
SELECT ol.order_line_id AS Order_Line_Key, o.Order_Number, ...
FROM   silver.order_line ol
JOIN   silver.order o        ON ol.order_id = o.order_id          -- header attrs (denormalized)
LEFT JOIN silver.order_partner ptr ON o.order_id = ptr.order_id
       AND ptr.Partner_Function = 'AG'                             -- Sold-To only; avoids fan-out

-- dim_customer — dedup: order_partner has many rows per customer, keep the most recent
SELECT customer_id AS Customer_Bk, customer_name, ...
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY _source_updated_at DESC) AS _rn
  FROM silver.order_partner WHERE Partner_Function = 'AG'          -- Sold-To rows only
) WHERE _rn = 1

-- dim_material — multi-source UNION + post-union dedup on the conformed key
SELECT material_id AS Material_Bk, material_desc, ...
FROM (
  SELECT material_id, material_desc, _source_updated_at,
         ROW_NUMBER() OVER (PARTITION BY material_id ORDER BY _source_updated_at DESC) AS _rn
  FROM (
    SELECT material_id, material_desc, _source_updated_at FROM silver.order_line
    UNION ALL
    SELECT material_id, material_desc, _source_updated_at FROM silver.quotation_line
  )
) WHERE _rn = 1                                                    -- same member across sources → dedup
```
