# Discovery Protocol — Phases 1 & 2

## Phase 1: Metamodel Inspection

Run ALL of these queries before touching a single bronze table.
The metamodel is the authoritative source of intent — richer than any brief.

> **Where `{catalog}.{schema}` resolves:** the vibe model is READ-ONLY and lives at
> `conventions.yml` → `vibe_model.catalog` / `vibe_model.schema`. Resolve every `{catalog}`
> and `{schema}` below from those keys — NOT from `catalogs.silver`. `catalogs.silver` is the
> SEPARATE location where the ETL framework later *lands* built tables; this skill never reads
> or writes there. Keeping them distinct is what stops a later build from writing into the
> model you are grading. (Bronze reads still resolve from `bronze_sources`; see Step 2.1.)

### 1.0 Locate the Metamodel (do this FIRST — do not assume the layout)

**The metamodel tables are NOT always where or what you expect.** Two layouts exist in the wild
and the skill must handle both:
- **Co-located, prefixed** — `vibe_metamodel_business` / `_product` / `_attribute` / `_domain`
  live in the SAME schema as the physical model tables (`{catalog}.{schema}.vibe_metamodel_*`).
- **Separate `_metamodel` schema, un-prefixed** — the metamodel tables are `business` / `product`
  / `attribute` / `domain` (NO `vibe_metamodel_` prefix) in a dedicated schema such as
  `{catalog}._metamodel`, while the physical model tables live in `{catalog}.{schema}`.

Do not guess. Resolve two variables before running any Phase 1 query:
- **`{metamodel_schema}`** — the schema holding the metamodel tables (may differ from the physical
  `{schema}`).
- **`{mm_prefix}`** — either `vibe_metamodel_` or empty (`''`).

**Fast path — honor `conventions.yml` if set.** If `vibe_model.metamodel_schema` and/or
`vibe_model.metamodel_prefix` are present, bind the variables from them and skip the probe.
Defaults when absent: `metamodel_schema` = `vibe_model.schema`; `metamodel_prefix` = `vibe_metamodel_`.

**Probe — when the keys are absent or you want to confirm.** The four metamodel tables always
travel as a **co-located set**, so match on the *set*, not on any single name — otherwise a
business dimension literally named `product` or a schema named `domain` (both plausible in an ECM
catalog) produces a false hit. Require the full set in a schema:
```sql
SELECT table_schema,
       COUNT(*)                                                        AS mm_tables,
       MAX(CASE WHEN table_name LIKE 'vibe_metamodel_%' THEN 1 ELSE 0 END) AS is_prefixed
FROM {catalog}.information_schema.tables
WHERE table_name IN ('business','product','attribute','domain')
   OR table_name LIKE 'vibe_metamodel_%'
GROUP BY table_schema
HAVING COUNT(*) >= 4          -- the metamodel schema carries the full set; a stray `product` won't
ORDER BY is_prefixed DESC, mm_tables DESC;
```
- Exactly one schema qualifies → that's `{metamodel_schema}`; `is_prefixed = 1` → `{mm_prefix}` =
  `vibe_metamodel_`, else `{mm_prefix}` = `''` (often a dedicated `_metamodel` schema).
- **More than one schema qualifies** → prefer the `vibe_metamodel_`-prefixed set, else the one
  matching `vibe_model.schema`. If still ambiguous, STOP and ask the user which schema holds the
  metamodel — do not pick arbitrarily.
- **No schema qualifies** → the metamodel isn't in this catalog (or isn't a full set). STOP and ask
  the user for the metamodel location; do not fall back to guessing schema names.

Template every metamodel query below as `{catalog}.{metamodel_schema}.{mm_prefix}{table}` (e.g.
`{catalog}.{metamodel_schema}.{mm_prefix}product`). Reads against `information_schema` for the
**physical** model tables (§1.4–1.6) still use the physical `{schema}` — those are different objects.

### 1.0b Domain Definition (metamodel `domain` table)
```sql
SELECT * FROM {catalog}.{metamodel_schema}.{mm_prefix}domain;
```
Captures the domain roster and (on a shared metamodel) the `domain_id` / domain name used to
scope `product` and `attribute` to a single domain — see §1.2. On a single-domain metamodel this
returns one row; on a shared enterprise metamodel it returns many, which is your first signal that
§1.2/§1.3 MUST be scoped.

### 1.1 Business Context
```sql
SELECT * FROM {catalog}.{metamodel_schema}.{mm_prefix}business;
```
Captures: business name, industry, source systems of record, common jargon, modelling conventions,
data_asset_naming_convention, primary_key_suffix, boolean_format, date/timestamp formats.
Record the `operational_systems_of_records` field — this lists every source system the domain
expects data from. Use it to scope your bronze search in Phase 2.

### 1.2 Target Table Inventory

> **SCOPE FIRST — the metamodel may be shared across domains AND versions.** A shared enterprise
> metamodel holds every domain's tables and every prior version of each. An UNSCOPED
> `SELECT … FROM …product` returns thousands of rows spanning domains and versions — that is NOT
> your target inventory. Before mapping anything, scope to (a) THIS domain and (b) a SINGLE
> resolved version. See "Version resolution" below. If a raw count looks inflated or you see the
> same `table_name` repeated, you have NOT scoped yet — do not proceed to mapping on unscoped rows.

```sql
SELECT p.product, p.table_name, p.type, p.subdomain, p.primary_key, p.description
FROM {catalog}.{metamodel_schema}.{mm_prefix}product p
JOIN {catalog}.{metamodel_schema}.{mm_prefix}domain d
  ON p.domain_id = d.domain_id          -- or p.domain = d.name — inspect the join key in §1.0b
WHERE d.name = '{domain}'               -- conventions.yml `domain`
  AND p.version = '{model_version}'     -- single resolved version — see below
ORDER BY p.product;
```
- `type`: Master | Transactional — determines dim vs fact classification
- `subdomain`: groups tables into FK tiers
- `description`: authoritative intent — quote this verbatim in S2T report

> **Adapt the scope columns to the actual schema.** The exact column names for domain and version
> vary by metamodel build (`domain_id` vs `domain` vs `model_scope`; `version` vs `model_version`).
> Inspect the `product`/`domain` columns via `information_schema.columns` first, then bind the
> predicates. If the metamodel genuinely carries no domain or version column (single-domain,
> single-version build), drop the corresponding predicate — but SAY SO in the report header, don't
> silently run unscoped.

**Version resolution.** If `product` (or `business`) carries a version column and
`conventions.yml` does not pin `vibe_model.version`, default `{model_version}` to the MAX version
present for this domain:
```sql
SELECT MAX(version) AS latest_version
FROM {catalog}.{metamodel_schema}.{mm_prefix}product p
JOIN {catalog}.{metamodel_schema}.{mm_prefix}domain d
  ON p.domain_id = d.domain_id
WHERE d.name = '{domain}';
```
> **`MAX(version)` assumes an orderable version column.** It's correct for integer/zero-padded
> versions. If `version` is a non-numeric label (`v2`, `V10`, `2.0`), lexical `MAX` can pick wrong
> (`'v10' < 'v2'`) — inspect distinct values first and resolve "latest" explicitly (e.g. cast the
> numeric part, or pick from the known set) rather than trusting `MAX()`.

**Record the resolved domain + version in the S2T report header** (e.g. "Metamodel: `…_metamodel`
(V2, sales_order scope)") so the reader knows exactly which slice was assessed.

### 1.3 Full Column Inventory (with FK and regex)

> **Same scoping applies** — filter to this domain + the resolved version, exactly as §1.2. An
> unscoped attribute pull on a shared metamodel returns every domain's columns across all versions.

```sql
SELECT a.product, a.attribute AS column_name, a.type, a.business_glossary_term,
       a.value_regex, a.foreign_key_to, a.description
FROM {catalog}.{metamodel_schema}.{mm_prefix}attribute a
JOIN {catalog}.{metamodel_schema}.{mm_prefix}domain d
  ON a.domain_id = d.domain_id          -- match the join key resolved in §1.2
WHERE d.name = '{domain}'
  AND a.version = '{model_version}'
ORDER BY a.product, column_name;
```
*(If `attribute` scopes only by `product` name rather than a domain/version column, scope it to the
product list resolved in §1.2 instead — `WHERE a.product IN (…)`.)*
Key fields:
- `foreign_key_to`: `{domain}.{table}.{pk_column}` — includes CROSS-DOMAIN references
  that have no physical FK in this schema. These are natural key join targets for discovery.
- `value_regex`: allowed value patterns / enum sets — use as validation rules in mapping

### 1.4 Physical Column List + Comments
```sql
SELECT table_name, column_name, full_data_type, comment
FROM {catalog}.information_schema.columns
WHERE table_schema = '{schema}'
ORDER BY table_name, ordinal_position;
```

### 1.5 FK Graph (Intra-Domain Referential Constraints)

> **`referential_constraints` alone does NOT give you the FK graph.** It lists constraint-name
> pairs — it has no `table_name`/`column_name` you can build tiers from. You MUST join it to
> `key_column_usage` (child side) and to the parent's key columns (via `unique_constraint_name`)
> to resolve which child column points at which parent table. Use the query below, not a bare
> `SELECT *`.

```sql
SELECT
  kcu.table_name        AS child_table,
  kcu.column_name       AS child_column,
  ccu.table_name        AS parent_table,
  ccu.column_name       AS parent_column
FROM {catalog}.information_schema.referential_constraints rc
JOIN {catalog}.information_schema.key_column_usage kcu
  ON  rc.constraint_name   = kcu.constraint_name
  AND rc.constraint_schema = kcu.constraint_schema
JOIN {catalog}.information_schema.key_column_usage ccu
  ON  rc.unique_constraint_name   = ccu.constraint_name
  AND rc.unique_constraint_schema = ccu.constraint_schema
WHERE rc.constraint_schema = '{schema}'
ORDER BY child_table, child_column;
```
Use this to build the load order (parents before children).
Tables with no inbound FKs are Tier 0 (roots). Build tiers iteratively.

> **Fallback — FKs declared only in the metamodel, not as physical UC constraints.** Many vibe
> models carry FK intent in `{mm_prefix}attribute.foreign_key_to` (`{domain}.{table}.{pk}`) WITHOUT
> emitting physical UC constraints. In that case `information_schema.referential_constraints` comes
> back **empty** and the query above yields a flat, tier-less graph — which is a false "no FKs,"
> not a real one. If the join returns nothing (or far fewer edges than the model has FK columns),
> build the tier graph from the `foreign_key_to` values pulled in §1.3 instead. Always cross-check:
> if §1.3 shows FK columns but §1.5 shows no physical constraints, trust §1.3.

### 1.6 Column Glossary Tags
```sql
SELECT table_name, column_name, tag_name, tag_value
FROM {catalog}.information_schema.column_tags
WHERE schema_name = '{schema}'
ORDER BY table_name, column_name;
```

### Degenerate Placeholder Detection
A degenerate placeholder is a table emitted by the vibe generator that has:
- A single column (`{table}_id`) with no other columns
- An empty or absent `description` in `{mm_prefix}product`
Flag it explicitly and exclude it from all mapping work.

---

## Phase 2: Bronze Source Profiling

### Step 2.1 — Identify Candidate Schemas
Cross-reference the `operational_systems_of_records` from the metamodel_business row
against the customer's **`bronze_sources` map in `conventions.yml`** (logical source name →
`catalog.schema` prefix). That map is the single source of truth for which bronze schemas a
source system lands in — do not hard-code schema names here. Read it and build the candidate
list from the entries whose source system matches the metamodel's systems of record.

> **Meridian example profile** (the values shipped in `templates/conventions.yml` — replace per
> customer). This table is illustrative; the live lookup is `conventions.yml`:
>
> | Source system | `bronze_sources` key → catalog.schema |
> | --- | --- |
> | SAP S/4HANA SD (ERP of record) | `src_sap_sd` → `meridian_bronze.sap_sd` |
> | Salesforce CRM | `src_salesforce_crm` → `meridian_bronze.salesforce_crm` |
> | Homegrown EDI middleware | `src_edi_gateway` → `meridian_bronze.edi_gateway` |
> | Bolt-on RMA / returns web app | `src_returns_portal` → `meridian_bronze.returns_portal` |
> | Field-service app | `src_fieldlink` → `meridian_bronze.fieldlink` |
>
> Meridian's five sources share ONE catalog (the common single-catalog case). When a customer's
> sources span multiple catalogs (e.g. ERP in one, HR in another, a gold platform in a third),
> each `src_{logical}` prefix simply carries its own `catalog.schema`, so cross-catalog joins
> need no structural change — keep the per-source prefix pattern regardless.
>
> Each logical source becomes a `src_{logical}` runtime widget/param in the generated ETL
> notebooks (see `etl-development-framework/merge-and-defensive-coding.md` "Runtime Parameters").
> Record, per entity, which sources it reads — the build skill needs that to wire `base_parameters`.

### Step 2.2 — Schema-Wide Table Search
For each candidate schema, search by business keyword:
```sql
SELECT table_schema, table_name
FROM {bronze_catalog}.information_schema.tables
WHERE table_schema = '{candidate_schema}'
  AND (
    LOWER(table_name) LIKE '%{keyword1}%'
    OR LOWER(table_name) LIKE '%{keyword2}%'
    OR LOWER(table_name) LIKE '%{keyword3}%'
  )
ORDER BY table_schema, table_name;
```
Run in batches: one query per 2–3 schemas. Use domain-relevant keywords drawn from the
entity group descriptions in the discovery brief (e.g., 'wip', 'bom', 'routing', 'serial',
'oee', 'schedule', 'lot', 'completion', 'move', 'operator').

### Step 2.3 — Row Count & Date Range Profiling
For every confirmed candidate table:
```sql
SELECT COUNT(*) AS row_count,
       MIN({date_col}) AS min_date,
       MAX({date_col}) AS max_date
FROM {catalog}.{schema}.{table};
```
Run in batch UNIONs (up to 10 tables per query) to avoid timeout:
```sql
SELECT 'table_a' AS tbl, COUNT(*) AS rows FROM {catalog}.{schema}.table_a
UNION ALL SELECT 'table_b', COUNT(*) FROM {catalog}.{schema}.table_b
...
```

> **Databricks-safe batching — `LIMIT` must live in a subquery, never bare before `UNION ALL`.**
> A bare `... LIMIT 3 UNION ALL SELECT ...` is a **syntax error** in Databricks SQL (the run hit
> this on its first attempt). When a batch branch needs a `LIMIT` (e.g. date-format sampling below),
> wrap each branch in a subquery so the `LIMIT` binds to that branch, not the whole UNION:
> ```sql
> SELECT '{schema}.{table}.{col}' AS col, {col} AS sample
> FROM (SELECT {col} FROM {catalog}.{schema}.{table} WHERE {col} IS NOT NULL LIMIT 3) t
> UNION ALL
> SELECT '{schema2}.{table2}.{col2}', {col2}
> FROM (SELECT {col2} FROM {catalog}.{schema2}.{table2} WHERE {col2} IS NOT NULL LIMIT 3) t2
> ```
> The plain `COUNT(*)` batch above needs no subquery (no `LIMIT`); this pattern is specifically for
> sampled batches.

### Step 2.4 — Column Structure for Top Candidates
For tables with confirmed row counts that match domain entities, run DESCRIBE:
```sql
DESCRIBE TABLE {catalog}.{schema}.{table};
-- OR for richer info:
SELECT column_name, data_type
FROM {catalog}.information_schema.columns
WHERE table_schema = '{schema}' AND table_name = '{table}'
ORDER BY ordinal_position;
```
Always use `information_schema.columns` (not DESCRIBE) when column names are unknown
and you want to avoid an UNRESOLVED_COLUMN error from specifying them in SELECT.

**Discover bronze types + date formats — do NOT assume them.** The `data_type` returned above is
the ground truth for each source. Some bronze extracts land everything as STRING (e.g. a stripped
SAP dump where dates are `yyyyMMdd` strings); others are properly typed (real DATE/TIMESTAMP/DECIMAL
columns). **These are per-source facts to discover, not a global assumption** — do not write "all
bronze is STRING" or "SAP dates are `yyyyMMdd`" into the S2T report or handoff spec unless the
profiled `data_type` (and a sample) confirm it for that source. When a column is STRING but holds a
date, sample it to confirm the format before choosing a `TO_DATE(...)` mask:
```sql
SELECT {date_col}, COUNT(*) AS n
FROM {catalog}.{schema}.{table}
WHERE {date_col} IS NOT NULL
GROUP BY {date_col} ORDER BY n DESC LIMIT 5;   -- confirms 'yyyyMMdd' vs 'yyyy-MM-dd' vs epoch, etc.
```
Record the observed type + format per source column in the S2T column mapping (it drives the CAST /
`TO_DATE` mask in the spec). A properly-typed source needs no CAST; a STRING source does — the spec
must reflect what you actually found, per source.

### Step 2.4b — Source Column Reconciliation (target attribute name ≠ bronze column name)

> **This is the single highest-value step for a clean downstream build.** The metamodel
> `attribute.attribute` field is the **TARGET** column name the vibe model *wants* (`credit_status`,
> `channel_code`, `unit_price`). It is **NOT** the bronze source column name — the actual bronze
> column is very often different (`result`, `vtweg`, `list_price`) or absent. Writing the target
> name into the S2T "Source" position is what caused **76% of files to be rewritten** at build time
> in the sales-order SDP run. Reconcile the two names here, once, against the real schema.

For every mapped entity, after Step 2.4 has the actual `information_schema.columns` list for its
source table(s):

1. Pull the metamodel attribute list (TARGET names) for the entity.
2. Pull the actual bronze source columns (from Step 2.4).
3. Match each target attribute to its best-fit source column — exact, then case-insensitive, then
   prefix/suffix/fuzzy (`unit_price`→`list_price`, `channel_code`→`vtweg` via domain knowledge).
   **Confirm every non-obvious match by sampling** — do not trust a name resemblance alone.
4. Classify each target attribute:
   - **Direct map** — a real bronze column populates it (record `source_table.source_col`).
   - **Derived** — computed from other sourced columns (record the expression, no single source col).
   - **GAP** — no plausible source column exists (flag; it becomes a gap-registry / ingestion ask,
     and the build emits `CAST(NULL AS <type>)` for it, not a guessed column).

Emit the reconciled mapping into the S2T report's per-entity column table (Step 2.4b feeds the
`Source table` + `Source column` columns of the format in `source-to-target-mapping.md`). **Never
write a target attribute name in the source-column position.** A target column with no confirmed
source column is a GAP, full stop — the downstream build must never see a bronze column name that
was not verified to exist here.

```sql
-- Reconcile: does each target attribute have a real bronze column? (per entity's source table)
SELECT column_name AS actual_bronze_column, data_type
FROM {catalog}.information_schema.columns
WHERE table_schema = '{schema}' AND table_name = '{source_table}'
ORDER BY ordinal_position;
-- Diff this list against the metamodel target attribute list; anything with no match = Derived or GAP.
```

**Carry the target TYPE, and probe every mapped column for all-null (feeds the typed handoff +
NULL_SOURCE).** For each reconciled target attribute, record its **metamodel declared type**
(already pulled in Phase 1.3) alongside the verified source column — this becomes the S2T
`Target Type` column and the handoff spec §2 `Type`. Then, for **every mapped non-key source
column** (not just keys), probe the null rate — batched per source table, one pass:

```sql
SELECT
  COUNT(*)                               AS n,
  COUNT({col_a})                         AS non_null_a,
  COUNT({col_b})                         AS non_null_b
  -- ... one COUNT({col}) per mapped column in this source table
FROM {src_table};
```

A column with `n > 0` and `non_null = 0` is **100% NULL** → set its S2T `Gap?` to **`NULL_SOURCE`**
and its `Null Disposition` from `conventions.yml` `null_columns.disposition` (blank in the S2T if it
matches the global default; explicit only when overridden). `n = 0` (empty table) is the existing
Blocked / 0-row case, NOT `NULL_SOURCE`. Record every `NULL_SOURCE` column in the Gap &
Enhancement Registry (see `iteration-loop.md`).

**Why non-key columns only:** a 100%-null **key** column is a harder failure than a NULL_SOURCE
business column — a natural/business key with no values cannot produce a usable surrogate and
collapses the grain. It is caught by the existing key-quality profiling (the key null-rate check)
and demotes the entity to **Blocked**, not classified `NULL_SOURCE` (which is a keep/drop-able
non-key finding). So an all-null key never silently becomes a kept all-null column — it blocks the
entity. (This is the harder-failure path the validation skill's kept-null note refers to.)

### Step 2.4c — Date Format Discovery (structured, per source system)

Date-format sampling (Step 2.4) should not stay scattered across tool-call results — collect it
into **one structured table per source system** that drops straight into the handoff spec's
type-casting section, so the build never re-samples or guesses a mask:

| Source system | Date columns | Observed format | Cast mask |
| --- | --- | --- | --- |
| `sap_sd` | `erdat`, `vdatu`, `edatu`, … | `yyyyMMdd` | `TRY_TO_DATE(col, 'yyyyMMdd')` |
| `salesforce_crm` | `quote_date`, `valid_until` | `yyyy-MM-dd` | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |
| `edi_gateway` | `transmission_ts` | `yyyy-MM-dd` | `TRY_TO_DATE(col, 'yyyy-MM-dd')` |

Sample each date-like column (Step 2.4's `GROUP BY col ORDER BY n DESC LIMIT 5` probe) once, record
the observed format, and derive the mask **per source system** (formats are usually uniform within a
system, mixed across systems). Emit this as a first-class S2T report section (see the Bronze Type
Profile in `source-to-target-mapping.md`).

> **All-STRING bronze fast path.** When EVERY column across ALL source tables profiles as `STRING`
> (common for stripped SAP dumps, flat-file / CDC ingestions), several steps change and you should
> say so once in the report header ("All-STRING bronze — full type casting required"):
> 1. Step 2.6's timestamp-divergence signal is moot — there are no typed timestamps, so the
>    load strategy resolves immediately (see Step 2.6.0 fast-exit).
> 2. Date-format sampling (Step 2.4c) is **mandatory** for every date-like column — you cannot infer
>    it from `data_type`.
> 3. Sample **numeric precision** for amount/quantity columns (is `netwr` a 2-decimal amount?) and
>    **boolean encoding** for flag columns (`'TRUE'/'FALSE'` vs `'X'/' '` vs `'1'/'0'`) so the spec's
>    casts are correct, not assumed.

### Step 2.5 — Gold Schema Check (Do This Before Any Ingestion Ask)
Before writing a gap/blocked entry, check the production gold catalog (`catalogs.gold`
from `conventions.yml` — `manufacturing_gold_vibe` in the Meridian profile):
```sql
SELECT table_schema, table_name, table_type
FROM {gold_catalog}.information_schema.tables   -- conventions.yml catalogs.gold
WHERE LOWER(table_schema) LIKE '%{domain}%'
   OR LOWER(table_name) LIKE '%{entity}%'
   OR LOWER(table_name) LIKE '%{keyword}%'
ORDER BY table_schema, table_name;
```
Gold tables frequently contain source data (o9 supply plans, aggregated actuals) that was
processed but never re-ingested to bronze. Finding a gold table can demote a Blocked grade
to Partial without any new ingestion work.

### Step 2.6 — Mutability Probe (drives the load strategy — run for EVERY fact)

**Step 2.6.0 — Timestamp existence fast-exit (check this FIRST).** Before running the three-signal
tree below, look at the profiled `data_type`s (Step 2.4) for the entity's source set. If **no
source column is a typed `TIMESTAMP`/`DATE`, and any date-looking columns are STRING business dates
(not audit/update timestamps)** — the common case for stripped SAP extracts and raw CSV/JSON
ingestions — then there is **no watermark to build and nothing to measure**:

> → **All such entities → `FULL_MERGE` (→ `MV` in `sdp_pipeline` mode). Skip Signals 1–3.**
> Record: "No update timestamps in any source → full recompute only." This is not a fallback; it is
> the definitive answer whenever no audit timestamp exists. Do not walk the multi-step tree for
> entities that can only resolve one way.

Only when at least one source carries a real creation/update timestamp do you continue to the
three signals below.

**This is the probe that decides `APPEND_ONLY` vs `INCREMENTAL_MERGE` vs `SDP`.** Row count
alone does NOT determine the strategy — *mutability after insert* does. You cannot pick a
load strategy without answering: **once a source row is written, does it ever change?** Answer
it from three signals, in this order:

**Signal 1 — Entity semantics (decide this first, from the metamodel `type` + name/grain).**
`vibe_metamodel_product.type = 'Transactional'` plus an event-grain name is the strongest
tell. A row that records *something that happened* is append-only by nature — the business
never edits a past event; corrections arrive as new reversing rows.

| Entity shape | Mutability | Default strategy |
| --- | --- | --- |
| Transaction / event / posting / movement / completion / reading / log line | **Append-only** (write-once) | `APPEND_ONLY` |
| Status / header / master / order / job / schedule (has a lifecycle) | **Mutable** (status, dates, qty change over time) | `INCREMENTAL_MERGE` or `FULL_MERGE` by size |

**Signal 2 — Timestamp divergence (confirm Signal 1 against the actual data).** If the source
carries both a creation timestamp and a last-update timestamp, one query settles it:

```sql
SELECT
  COUNT(*)                                                              AS total_rows,
  SUM(CASE WHEN {last_update_col} > {creation_col} THEN 1 ELSE 0 END)   AS mutated_rows,
  ROUND(100.0 * SUM(CASE WHEN {last_update_col} > {creation_col} THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2)                                       AS pct_mutated
FROM {catalog}.{schema}.{table};
```

Interpret:
- `pct_mutated ≈ 0` (creation == last-update for ~all rows) → **nothing is updated after
  insert → `APPEND_ONLY`.** The `{creation_col}` becomes the watermark used only to *skip
  re-reading history*, not to catch updates.
- `pct_mutated` meaningfully > 0 → **rows are mutated → `INCREMENTAL_MERGE`**, and
  `{last_update_col}` is the watermark column. Record it — the build skill wires it into the
  `WHERE {watermark} > (SELECT MAX(_source_updated_at) FROM tgt)` predicate.
- **Only one timestamp, or neither** → you cannot measure mutation and (for a mutable entity)
  cannot build a safe watermark. This is the escalation trigger — see Signal 3.

**Signal 3 — Watermark availability (gates whether incremental is even possible).** A mutable
fact with **no reliable update timestamp** (or one that isn't reset on updates) has no safe
watermark: a watermarked read would silently miss in-place edits. Per the skill's escalation
rule, **stamp these `SDP` (Lakeflow AUTO CDC)**, not a silent `FULL_MERGE` — and record it as a
cross-team dependency, because SDP's CDC path needs **Change Data Feed enabled on the bronze
source going forward** (see below). Do NOT downgrade to full MERGE just because it "works" — a
100M+ mutable fact on nightly full MERGE is the exact shape the ETL skill forbids.

> **Change Data Feed is NOT required for `APPEND_ONLY` or watermarked `INCREMENTAL_MERGE`.**
> Those read bronze as-is and filter on a timestamp column — no CDF, no streaming, no bronze
> reconfiguration. CDF (`table_changes(...)`, `delta.enableChangeDataFeed = true`) is needed
> ONLY to (a) capture **deletes**, or (b) drive **SDP / AUTO CDC** for a mutable fact with no
> usable watermark. CDF is not retroactive — it must be enabled on bronze *before* the changes
> occur — and it's owned by the bronze ingestion team, so flag it as a dependency, never assume
> it. **Most facts — event-ledger facts especially — need none of this.**

> **In `sdp_pipeline` mode, `SDP` is not automatically AUTO CDC.** The `SDP` label above means
> "escalate — a plain watermark MERGE won't do." In a Lakeflow pipeline that resolves to one of two
> primitives depending on how changes arrive: **AUTO CDC INTO** (a real per-row keyed change feed
> exists — needs CDF) or an **incremental `REPLACE WHERE` flow** (large fact with windowed / late-
> arriving corrections but *no* per-row CDC feed — needs no CDF). Pick per `sdp-strategy-mapping.md`
> "The large mutable fact"; do not assume CDF is required until you've confirmed which primitive fits.

Record the probe result per fact — it maps straight to `etl_detailed_spec.md` Section 5 and the
S2T report's per-table **Load strategy** line:

| Fact (shape) | Row tier | pct_mutated | Watermark col | → Strategy |
| --- | --- | --- | --- | --- |
| event ledger (completion / transaction) | high-volume | ≈ 0 | creation ts (history-skip only) | APPEND_ONLY |
| lifecycle record (job / order) | mid-volume, mutable | > 0 | last-update ts | INCREMENTAL_MERGE |
| lifecycle record, no update ts | high-volume, mutable | — (no update ts) | none | SDP (CDF dependency) |

---

## Step 2.7 — Model Assertion Validation (the surgical lens — run for EVERY entity)

Phase 2C (in `model-completeness-protocol.md`) is the **additive** lens ("what did the model
*omit*?"). Step 2.7 is the **surgical** lens: **"what did the model *assert* that the data
contradicts?"** The vibe model declares a
grain, a type, a primary key, and FK targets for every entity. Those declarations are hypotheses
until profiled bronze confirms them. A model can be perfectly *complete* yet *wrong* about a
grain or a key — Step 2C won't catch that; this step does.

Run these assertion probes per entity, in the same style as the Phase 2 queries (unqualified
names resolved via the `conventions.yml` `bronze_sources` map, batchable across entities).
Assertions (a)–(d) are intra-source; **(e) covers cross-source FKs** — run it whenever an FK's
declared parent lives in a different source system than the child.
**Never auto-correct** — every contradiction becomes a **decision** routed to the Step 2C.4 human
gate, each carrying either a **Suggested next_vibes.md action** (iterate upstream) or an in-place
Genie-Code `vibe_metamodel_*` edit (small correction).

**Assertion (a) — Grain uniqueness.** The model declares "one row per {X}". Test whether the
declared natural key actually holds at that grain in the best source, or whether the real grain
is finer (e.g. the model says one row per `job`, but the source is one row per `job`+`operation`):
```sql
SELECT COUNT(*)                                   AS source_rows,
       COUNT(DISTINCT {declared_natural_key})     AS distinct_at_declared_grain,
       COUNT(*) - COUNT(DISTINCT {declared_natural_key}) AS excess_rows
FROM {catalog}.{schema}.{best_source_table};
```
`distinct_at_declared_grain < source_rows` ⇒ the declared grain does NOT hold — the natural key
repeats. Either the real grain is finer, or the source carries duplicates to dedupe. Surface it.

**Assertion (b) — Type vs mutability cross-check** (reuse the Step 2.6 `pct_mutated` result — do
not re-query). The model declares `Master` or `Transactional`. Cross-check against mutability:
- Declared **`Master`** but the source is **append-only** (`pct_mutated ≈ 0`, event-shaped name)
  ⇒ contradiction — likely a transactional/event entity mislabeled as a master.
- Declared **`Transactional`** but the source is **mutable with a lifecycle** (`pct_mutated` > 0,
  status/date columns change) ⇒ contradiction — likely a lifecycle master mislabeled as a fact.
No new query — this is a table lookup against the Step 2.6 result per entity.

**Assertion (c) — PK duplicate count.** The declared natural key must be unique in the best
source. Quantify the violation directly:
```sql
SELECT COUNT(*) AS duplicate_key_groups
FROM (
  SELECT {declared_natural_key}
  FROM {catalog}.{schema}.{best_source_table}
  GROUP BY {declared_natural_key}
  HAVING COUNT(*) > 1
) dup_keys;
```
`duplicate_key_groups > 0` ⇒ the declared PK is not unique at source. Either the key is composite
(needs another column) or the grain assertion (a) is wrong. Surface with the count as evidence.

**Assertion (d) — FK cardinality probe.** The model declares an FK (`foreign_key_to`) that is
expected to resolve 1:many (each child points to exactly one parent). Two things can be wrong:
the child can be **unresolvable** (orphans), and the relationship can be **many:many** (the
"parent" key is not unique on the parent side). Test **both** — and note that a naive
`LEFT JOIN` count silently *under-reports* orphans when the parent key is non-unique, because the
join fans out and inflates the row count. So measure the orphan rate against the parent's
**distinct** key set, and probe parent-key uniqueness separately:
```sql
SELECT
  c.child_rows,
  c.unresolved_children,
  ROUND(100.0 * c.unresolved_children / NULLIF(c.child_rows, 0), 2) AS pct_unresolved,
  p.parent_rows,
  p.distinct_parent_keys,
  (p.parent_rows > p.distinct_parent_keys)                          AS parent_key_not_unique
FROM (
  -- orphan rate, fan-out-safe: compare child FK values to the DISTINCT parent key set
  SELECT
    COUNT(*)                                                        AS child_rows,
    SUM(CASE WHEN {child_fk_col} NOT IN (
          SELECT {parent_key} FROM {catalog}.{schema}.{parent_source}
          WHERE {parent_key} IS NOT NULL
        ) THEN 1 ELSE 0 END)                                        AS unresolved_children
  FROM {catalog}.{schema}.{child_source}
) c
CROSS JOIN (
  -- parent-key uniqueness: parent_rows > distinct_parent_keys ⇒ many:many
  SELECT COUNT(*) AS parent_rows, COUNT(DISTINCT {parent_key}) AS distinct_parent_keys
  FROM {catalog}.{schema}.{parent_source}
) p;
```
High `pct_unresolved` ⇒ the declared FK does not resolve (wrong join key or wrong parent).
`parent_key_not_unique = true` ⇒ the relationship is **many:many** and needs a bridge entity —
the declared 1:many FK is wrong. Surface either as a decision.

**Assertion (e) — Cross-source FK resolution (run when parent and child come from DIFFERENT source
systems).** Assertion (d) assumes parent and child sit in the same bronze schema. The FKs that
actually fail in production are **cross-source** — the child and parent are mastered in different
systems with different ID vocabularies, and the join runs through a *bridge column*, not a shared
key. In the sales-order run these were the real breakage points:
- `order.quotation_id` resolves via `quote.converted_order_number → vbak.vbeln` (CRM → SAP)
- `return_order.order_id` resolves via `rma_request.original_order_number → vbak.vbeln` (Portal → SAP)
- `edi_order_message.order_id` resolves via `edi_message_log.order_number → vbak.vbeln` (EDI → SAP)

Detect these from §1.3: an FK whose `foreign_key_to` target lives in a different source system than
the child (different `bronze_sources` entry), OR where the join needs a bridge column rather than a
same-named key. Probe resolution across the two systems explicitly:
```sql
-- Cross-source FK: {child_system}.{child_table}.{bridge_col} → {parent_system}.{parent_table}.{parent_key}
-- Fan-out-safe: test the child bridge value against the DISTINCT parent key set (no JOIN).
-- A LEFT JOIN here would multiply child rows whenever the parent bridge key is non-unique
-- (e.g. several quote rows share one converted_order_number), inflating BOTH counts and
-- corrupting pct_resolved. Membership-test instead so each child row is counted exactly once.
SELECT
  COUNT(*)                                                          AS child_rows,
  SUM(CASE WHEN c.{bridge_col} IN (
        SELECT {parent_key} FROM {parent_catalog}.{parent_schema}.{parent_table}
        WHERE {parent_key} IS NOT NULL
      ) THEN 1 ELSE 0 END)                                          AS resolved,
  ROUND(100.0 * SUM(CASE WHEN c.{bridge_col} IN (
        SELECT {parent_key} FROM {parent_catalog}.{parent_schema}.{parent_table}
        WHERE {parent_key} IS NOT NULL
      ) THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1)                AS pct_resolved
FROM {child_catalog}.{child_schema}.{child_table} c;
-- If the join needs a transform (e.g. c.converted_order_number = p.vbeln with a cast/trim),
-- apply it to {bridge_col} inside the IN-subquery's SELECT, keeping the single-row-per-child count.
```
Interpret cross-source resolution rates by *design intent*, not against a 100% bar:
- A **low** rate can be **expected and correct** — only ~20% of quotes convert to orders, so
  `order → quotation` resolving at ~20% is the business truth, not a defect. State the expected
  rate in the finding.
- A **0% / near-0%** rate on a relationship that *should* resolve is the real signal — usually a
  vocabulary gap (portal reason codes `DMG/WRONG/WARR` never map to SAP `augru`) or a wrong bridge
  column. That becomes a decision (accept NULL FK, or build a mapping table) at the Step 2C.4 gate.

Record each cross-source FK with its bridge column, the two systems, the observed `pct_resolved`,
and the expected rate — this feeds the S2T report's "Cross-Source FK Resolution Summary".

**Assertion (f) — Filter-column existence (run for any entity whose mapping carries a WHERE clause).**
When an entity is populated by *filtering* a shared source (e.g. `delivery_schedule` = `vbep` rows
`WHERE ettyp IN ('LP','LZ','LZE')`), the filter column MUST exist in the actual bronze table. If it
does not, the entity produces **0 rows always** — that is **Blocked (filter column absent)**, not
Partial. A "Partial" grade implies some columns populate; a missing filter column means the entity's
source selection is unapplicable. Validate the filter column against `information_schema.columns`
during Step 2.4:

```sql
SELECT COUNT(*) AS filter_col_present
FROM {catalog}.information_schema.columns
WHERE table_schema = '{schema}' AND table_name = '{source_table}'
  AND column_name = '{filter_column}';   -- 0 ⇒ the WHERE predicate can never match → Blocked
```

If `filter_col_present = 0`: grade the entity **Blocked (filter column absent)** and record:
"Expected filter column `{col}` not present in `{source}`. Entity requires either a different source
or the filter column added to the bronze extract." The build then emits a `WHERE FALSE` stub (with
that reason as a comment) rather than a WHERE clause on a column that does not exist.

### Step 2.7 output — Model Assertion Findings

Output a findings table; contradictions flow to the **same** human gate as Phase 2C (Step 2C.4 in
`model-completeness-protocol.md`).

| # | Entity | Assertion tested | Model declared | Data shows | Contradiction? | Suggested disposition (prompt or in-place edit) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | (example) `wip_job` | Grain (a) | one row per `WIP_ENTITY_ID` | `WIP_ENTITY_ID` repeats across `ORGANIZATION_ID` | Yes | vibe-model prompt: "Correct `wip_job` natural key to composite `WIP_ENTITY_ID + ORGANIZATION_ID`; grain is one row per job per org." |
| 2 | (example) `oee_record` | Type (b) | `Master` | append-only, `pct_mutated ≈ 0`, event-shaped | Yes | vibe-model prompt: "Reclassify `oee_record` from Master to Transactional — it is an append-only reading event." |
| 3 | (example) `routing_operation` | FK (d) | FK to `routing` resolves 1:many | 12% unresolved children | Yes | in-place Genie-Code edit: fix `foreign_key_to` join column, OR prompt if a bridge entity is needed |
| 4 | (example) `return_order` | Cross-source FK (e) | `order_reason_id` resolves to SAP `augru` | 0% — portal codes `DMG/WRONG/WARR` unmapped to SAP vocab | Yes (unexpected 0%) | decision: accept NULL FK (P1), or build a portal→SAP reason mapping table |
| 5 | (example) `order` | Cross-source FK (e) | `quotation_id` resolves CRM→SAP | ~20% resolved (only converted quotes) | No — expected | none; ~20% is the business conversion rate, record as expected |

**Do NOT auto-correct.** Present the evidence (counts, pct) and the suggested disposition; the
user decides at the Step 2C.4 gate whether to iterate upstream or edit in place via Genie Code.

---

## Step 2.8 — Cross-Domain FK Availability Check

The FK graph (§1.3 / §1.5) enumerates FKs whose parent lives in **another domain**
(`manufacturing.plant`, `customer.account`, `pricing.price_list`, …). Merely listing them is not
enough — the build needs to know, per parent, whether the FK can *ever* resolve. Grade each unique
cross-domain parent:

```sql
-- Per unique cross-domain target (parent_catalog.parent_schema.parent_table):
SELECT COUNT(*) AS parent_rows
FROM {parent_catalog}.{parent_schema}.{parent_table};   -- errors ⇒ table doesn't exist
```

| Grade | Condition | Build guidance |
| --- | --- | --- |
| **Resolvable** | Parent silver table exists **and is populated** | Soft `EXPECT (fk IS NOT NULL)` — track resolution rate in the event log |
| **Deferred** | Parent table exists but is **empty** (parent domain not built yet) | FK will be NULL until the parent domain loads — expected NULL, not a defect; do not gate on it |
| **Blocked** | Parent table **does not exist** at all | Structural gap — the FK cannot resolve; record as an ingestion/build dependency on the parent domain |

Record the grade per cross-domain FK in the S2T report so the build knows which FKs to EXPECT
(Resolvable), which to accept as NULL (Deferred), and which are a cross-domain dependency (Blocked).
This turns "43 cross-domain FKs noted and moved on" into an actionable, graded list. In `normalized`
mode all three are nullable by convention (no `-1` sentinel); the grade still tells the build and
the downstream validation skill what NULL rate is *expected* vs a real orphan.

> **Next — Phases 2B & 2C** continue in `model-completeness-protocol.md`: inventory any existing
> V1/MVP or sibling-variant build (2B), then run the reverse coverage check and the shared human
> gate (2C). Do that before drafting the S2T report.

---

## Parallel Query Strategy

Run independent queries in parallel (not sequentially) by issuing multiple `executeCode`
tool calls in the same turn:
- **Turn 1:** Metamodel queries 1.2 + 1.4 in parallel
- **Turn 2:** Schema-wide table search (all schemas) + V1/MVP inventory in parallel
  (inventory protocol: `model-completeness-protocol.md` Phase 2B)
- **Turn 3:** Row count batches + column DESCRIBE for top candidates in parallel
- **Turn 4:** Model completeness check (unmapped sources) after S2T mapping is drafted
  (`model-completeness-protocol.md` Phase 2C)

Never wait for one query to return before issuing the next if they are independent.
Typical discovery requires 4–6 turns of parallel queries before moving to Phase 3.
