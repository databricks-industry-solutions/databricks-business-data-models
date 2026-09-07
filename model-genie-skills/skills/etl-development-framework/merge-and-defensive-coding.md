# MERGE Notebook Template & Defensive Coding

## When to Use

After DDL is generated and approved (Phase 2), scaffold **one load notebook per entity** in
`src/{layer}/transformations/{entity}` — an extension-less notebook, SQL or Python per
`conventions.yml` `etl_language` (see the "Notebook Format" section below and
`deployment-and-dab.md` "Notebook-format contract"). The notebook declares its own parameter
widgets and holds the MERGE; the DAB job runs it directly.

---

## Load Strategy Decision (DO THIS BEFORE PICKING A TEMPLATE)

**The single most important ETL decision. Full-source-scan Type-1 MERGE is the default in
this skill, but it is only correct for SMALL tables. A full MERGE with no watermark forces
Delta to consider the *entire target* for matches every run — a full source↔target shuffle
join on the surrogate key. On a 100M+ row fact, run nightly, that is the most expensive
possible shape.** Choose per entity, from `etl_detailed_spec.md` Section 5 (the assessment
skill pre-fills it from profiled row counts):

| Condition | Strategy | Pattern |
| --- | --- | --- |
| Dimension, or fact < ~5M source rows | **FULL_MERGE** (Type-1) | Templates below as-is. Full scan is cheap. |
| Fact 5M–100M, mutable, has a source update timestamp | **INCREMENTAL_MERGE** | Uncomment + wire the watermark (below). |
| Append-only ledger (transactions, moves, completions, postings) — any size | **APPEND_ONLY** | `WHEN NOT MATCHED`-only MERGE (below) — skips the UPDATE/rewrite. For big targets add a date-partition prune predicate so you skip the target scan too. |
| Fact 5M–100M **mutable with no reliable update timestamp** | **SDP** | When `etl_type: sdp_pipeline`, this is a BUILDABLE path — build the whole domain as a declarative pipeline per `sdp-pipeline-development.md` (streaming table + AUTO CDC). Needs CDF on bronze for deletes/SCD2/mutable-no-watermark. In `etl_type: merge_notebook` this remains a HUMAN NEEDED escalation. |
| Fact > 100M mutable, SCD2 history, or always-on enforced DQ | **SDP** | When `etl_type: sdp_pipeline`, this is a BUILDABLE path — build the whole domain as a declarative pipeline per `sdp-pipeline-development.md` (streaming table + AUTO CDC). Needs CDF on bronze for deletes/SCD2/mutable-no-watermark. In `etl_type: merge_notebook` this remains a HUMAN NEEDED escalation. |

> **`output_model` + `scd_strategy` interaction.** The templates below default to Type-1 MERGE.
> In **`normalized`** mode, MERGE on the model's PK (`{product}_id`), not a surrogate `{Entity}_Key`
> — otherwise identical. When **`scd_strategy: type_2`** (dimensional / hybrid-gold only), the
> plain dimension MERGE is replaced by the **SCD Type-2 Versioning MERGE** below; a Type-2 entity
> never uses plain FULL_MERGE overwrite, and a very large / high-churn Type-2 dim escalates to SDP.
> `normalized` + `type_2` is invalid — error early, redirect to `hybrid`.

**Which strategy needs Change Data Feed on bronze? (common misconception — answer it up front)**

| Strategy | Needs CDF on bronze? | What it actually reads |
| --- | --- | --- |
| FULL_MERGE | **No** | Full bronze table, as-is |
| APPEND_ONLY | **No** | Full bronze (or `WHERE {event_ts} > watermark` to skip history) — just a filtered SELECT |
| INCREMENTAL_MERGE | **No** | `WHERE {update_ts} > watermark` — filtered SELECT on a timestamp column |
| SDP / AUTO CDC (SCD2, deletes, or mutable-no-watermark) | **Yes** | `table_changes(...)` — the Delta change log |

*Watermark-based incremental needs only a **timestamp column** (or monotonic ID), not CDF.
CDF (`delta.enableChangeDataFeed = true`) is required only to capture **deletes**, build
**SCD2**, or handle a **mutable fact with no usable update timestamp**. CDF is not retroactive
(must be enabled on bronze before the changes happen) and is owned by the bronze ingestion
team — treat it as a cross-team dependency to flag, never a switch silver flips for itself.
Most manufacturing / operational fact sets are entirely append-only or timestamp-watermarkable
→ none need CDF; reach for it only in the narrow cases above.*

**Two rules that apply to every large-table strategy:**

1. **Carry the source *event* timestamp as a real column** (e.g. `_source_updated_at` from
   `LAST_UPDATE_DATE` / `DF_Processing_Dttm`). The watermark reads it; `_loaded_at` is
   job-time and identical across a run, so it cannot drive incremental logic.
2. **Align the merge key with the cluster/partition key.** The surrogate is a *random* SHA2
   BIGINT, so `CLUSTER BY (Some_Dim_Key)` does NOT let Delta skip files on the merge
   predicate — every run rewrites broadly. Either cluster the target on the same key you
   MERGE on, or (better for big facts) merge on the **business key + event date** and
   partition/cluster the target on the date so the MERGE can prune.

### Incremental MERGE (watermarked) — for 5M–100M mutable facts

```sql
USING (
  WITH deduped AS (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY {grain_columns} ORDER BY {recency_column} DESC
    ) AS _rn
    FROM IDENTIFIER(:src_{logical} || '.{source_table}')
    -- WATERMARK: only re-read source rows changed since the last successful load.
    WHERE {source_update_ts} > (
      SELECT COALESCE(MAX(_source_updated_at), TIMESTAMP '1900-01-01')
      FROM fact_{name}          -- unqualified: session catalog.schema
    )
  )
  SELECT ..., {source_update_ts} AS _source_updated_at, ...
  FROM deduped src ... WHERE src._rn = 1
) AS src
ON tgt.{Name}_Key = src.{Name}_Key
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;
```

**Target-side pruning — the safe way.** A watermarked *source* still forces Delta to scan the
whole *target* unless the ON clause can prune target files. It is tempting to add
`AND tgt.{Event_Date} >= {watermark}` — **do NOT prune on a business/event date when the source
watermark is an update-timestamp.** For a mutable fact, a late correction to an old-dated row
has a recent `_source_updated_at` but an old `{Event_Date}`; that target row then fails the
`Event_Date >=` predicate, the incoming row is classified NOT MATCHED, and you **INSERT a
duplicate PK** — silently breaking Type-1. Prune only on a column that is *monotonic with the
watermark*:

- **Correct:** partition/cluster the target on `_source_updated_at` (or a derived
  `_source_updated_date`) and prune on that same column:
  `AND tgt._source_updated_date >= (SELECT COALESCE(MAX(_source_updated_at)::DATE, DATE '1900-01-01') FROM {target})`.
  Because both source filter and target prune use the *same* change signal, a late edit's target
  row is inside the pruned window and MATCHES correctly.
- **Also fine:** no target-side predicate at all — correct, just less file-skipping (acceptable
  when the target isn't huge).
- **Only safe on insert-mostly facts:** pruning on `{Event_Date}` is safe *only* when event date
  and update time are tightly correlated (rows are never corrected after their event date). If
  you can guarantee that, the fact is really append-only — use the pattern below instead.

### Append-Only load — for immutable ledger facts (any size)

Transaction/event facts (material transactions, move transactions, completions, GL postings)
are **never updated after insert**. Do not use symmetric Type-1 MERGE — drop the UPDATE branch
so matched rows are never re-written:

```sql
MERGE INTO fact_{name} AS tgt          -- unqualified: session catalog.schema
USING ( ...deduped + FK-resolved source, with a watermark on {source_update_ts}... ) AS src
ON tgt.{Name}_Key = src.{Name}_Key
   -- Prune the target so you also skip the SCAN, not just the rewrite (see note):
   AND tgt.{Event_Date} >= (SELECT COALESCE(MAX({Event_Date}), DATE '1900-01-01')
                            FROM fact_{name})
WHEN NOT MATCHED THEN INSERT (...);   -- no WHEN MATCHED — rows are immutable
```

**What this actually saves.** The `WHEN NOT MATCHED`-only branch avoids the UPDATE/**rewrite** of
matched rows. It does **not**, by itself, avoid the target **scan**: to classify each source row
as matched/not-matched Delta must probe the target on the ON key, and since `{Name}_Key` is a
*random SHA2* surrogate there is nothing to prune on — so a bare ON clause still reads the whole
target. Because these rows are immutable, event date IS monotonic here, so the
`AND tgt.{Event_Date} >= {max event date}` predicate is **safe** (no late edits to old dates)
and lets Delta skip target files — this is exactly the pruning that is *unsafe* for a mutable
incremental fact above. Partition/cluster the target on `{Event_Date}` for it to bite.

*Equivalent anti-join INSERT (`INSERT ... SELECT ... WHERE NOT EXISTS (... AND tgt.{Event_Date} >= ...)`)
is also fine; the point is to prune the target on the immutable event date so you skip both the
scan and the rewrite.*

---

## Notebook Format — one load notebook per entity

Each entity is authored as ONE extension-less notebook object (format per `conventions.yml`
`etl_language`) in `src/{layer}/transformations/{entity}`. It **declares its own parameter
widgets** and holds the MERGE; the DAB job runs it directly via `notebook_task` + `base_parameters`.

Catalog/schema are **runtime parameters**, never literals. Target and source are handled
asymmetrically:

- **Target (writes to ONE place):** set the session catalog + schema from the `silver_catalog`
  /`silver_schema` widgets via `USE CATALOG IDENTIFIER(:silver_catalog)`, then reference the
  target and all sibling silver tables (dim lookups, watermark subqueries) **UNQUALIFIED**.
- **Sources (may read MANY bronze schemas, across DIFFERENT catalogs):** declare one
  `src_{logical}` widget per bronze source the notebook reads (from `conventions.yml`
  `bronze_sources`), each holding a `{catalog}.{schema}` prefix, and read via
  `IDENTIFIER(:src_{logical} || '.{table}')`. Each prefix carries its own catalog, so a notebook
  that joins DFF + WIP (or bronze + HR + gold) needs no special case.

The notebook's first cells declare the widgets and set the session context:

```sql
-- Databricks notebook source
-- Load notebook: dim_plant — declares its own widgets, holds the MERGE. Run directly by the DAB job.
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';
CREATE WIDGET TEXT src_orcy_wip   DEFAULT '';   -- one per bronze source this notebook reads
CREATE WIDGET TEXT job_name       DEFAULT '';
-- COMMAND ----------
USE CATALOG IDENTIFIER(:silver_catalog);   -- unqualified target/silver refs resolve here
USE SCHEMA  IDENTIFIER(:silver_schema);
-- COMMAND ----------
MERGE INTO dim_plant AS tgt          -- unqualified: session catalog.schema
USING (SELECT ... FROM IDENTIFIER(:src_orcy_wip || '.tbl')) AS src
...
```

> `job_name` for the `_created_by`/`_modified_by` audit columns is also a widget — reference it as
> `:job_name`, never hard-code the literal job name.

> An empty widget default means a mis-wired job task fails fast (`IDENTIFIER('')` errors) rather
> than silently writing to the wrong place — the desired behavior. The DAB task passes exactly
> the `src_*` prefixes the notebook reads (discovery records this per entity).

> **Persist the notebook to the workspace BEFORE running the real load** (not after).
> Always persist the notebook to the workspace before running the real load — the
> correct order is: validate SQL in scratchpad → create the notebook asset + write the
> validated SQL → run the real load → DQ → checkpoint. Authoring the notebook after
> the load lands is the durability bug: a session drop between load and create leaves a
> populated table with no artifact to reproduce it. See SKILL.md Phase 4 entity-first
> loop + Critical Rule 28.

In the MERGE templates below, `{silver_catalog}.{silver_schema}.` prefixes are dropped (session
context) and `{source_catalog}.{source_schema}.{source_table}` becomes
`IDENTIFIER(:src_{logical} || '.{source_table}')`. The templates are the MERGE body that follows
the widget/`USE` header above.

## Why one notebook per entity (no runner/test trio) — rationale

> **Why one notebook per entity (no runner/test trio).** Earlier versions of this skill split
> each entity into a transform (declares nothing) + a runner (declares params, `%run`s the
> transform) + a build-time fixture unit test that `%run`s the same transform. That split existed
> *only* so a test could `%run` the transform with swapped session variables pointing at fixtures.
> We removed the fixture unit-test framework (see rationale below), so the split lost its reason to
> exist — the load notebook now declares its own widgets and is run directly, which is what field
> teams actually write and eliminates the opaque `%run`-failure debugging problem. **Confidence
> that a load "landed as intended" comes from post-load DQ on the real table** (the Phase 5 gate,
> `testing-and-grading.md`) plus a cheap twice-run idempotency recheck — not from synthetic
> fixtures. Deep data-state validation is then the downstream `domain-model-validation` skill.
>
> *Rationale (July 2026):* no field team writes build-time fixture tests for hand-authored MERGE
> notebooks; the idempotency bug they guarded (`DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`)
> fails the MERGE **loudly at runtime** anyway; and the packaged unit-test investment is all going
> into Lakeflow SDP (which `sdp_pipeline` mode already uses). The `python-unit-tests` +
> workspace-files path was not adopted because it assumes transform logic extracted into importable
> `src/` modules — these transforms are deliberately notebook-native SQL, so there is nothing to
> `pytest` without a different architecture.

### Python variant (`etl_language: python`)

Same shape. The notebook reads its widgets and runs the MERGE via `spark.sql(f"...")`, interpolating
the catalog/schema/source names directly (no `IDENTIFIER()`). First substitute the authoring-time
placeholders (`{entity}`, `{source_table}`, key names, …) with real values — those are metavariables
the generator fills, NOT runtime braces.

> **Why interpolation, not `IDENTIFIER(:param)`+`args=`.** In a SQL cell `IDENTIFIER(:silver_catalog)`
> binds the widget automatically, but `spark.sql("... :name ...")` in Python does NOT auto-bind widgets
> — it would raise `UNBOUND_SQL_PARAMETER`. Rather than thread an `args=` dict through every call, the
> Python shape uses the normal Databricks idiom: read the widget, interpolate the name. This is safe
> here because every interpolated value is config-sourced (widgets ← job `base_parameters` ← DAB
> variables ← conventions.yml) — never analyst / free-text input.

```python
# Databricks notebook source
# Load notebook: dim_plant — declares its own widgets, holds the MERGE. Run directly by the DAB job.
for v in ["silver_catalog", "silver_schema", "src_orcy_wip", "job_name"]:
    dbutils.widgets.text(v, "")
cat = dbutils.widgets.get("silver_catalog"); sch = dbutils.widgets.get("silver_schema")
src_orcy_wip = dbutils.widgets.get("src_orcy_wip"); job_name = dbutils.widgets.get("job_name")
# COMMAND ----------
spark.sql(f"USE CATALOG {cat}")
spark.sql(f"USE SCHEMA  {sch}")
# COMMAND ----------
spark.sql(f"""
  MERGE INTO dim_plant AS tgt
  USING (SELECT ... FROM {src_orcy_wip}.plants) AS src
  ON tgt.Plant_Bk = src.Plant_Bk
  ...
""")
```

> **Safety:** interpolate ONLY config-sourced values (widgets ← job `base_parameters` ← DAB
> variables ← conventions.yml). NEVER interpolate analyst / free-text input into `spark.sql(f"...")`.
> An empty widget DEFAULT still fails fast — `USE CATALOG ` with a blank name errors rather than
> writing to the wrong place.
>
> **Brace escaping (only after substitution):** substitute the `{placeholder}` metavariables first.
> If the *resulting* SQL still contains a genuine literal `{`/`}` that must survive to runtime (e.g.
> a Spark complex-type / map / struct literal), double it to `{{`/`}}` inside the f-string. Do NOT
> double the template placeholders themselves.

---

## Silver Dimension MERGE Template

```sql
-- Databricks notebook source
-- =============================================================================
-- Load notebook: dim_{entity} — declares its own widgets, holds the MERGE. Run directly by the DAB job.
-- Target: <silver_catalog>.<silver_schema>.dim_{entity}   (widgets)
-- Source: <src_{logical}>.{source_table}                  (widget prefix)
-- Natural Key: {Natural_Key}
-- Strategy: Type 1 MERGE
-- =============================================================================
-- Header cells declare widgets, then set session context:
--   CREATE WIDGET TEXT silver_catalog/silver_schema/src_*; USE CATALOG IDENTIFIER(:silver_catalog); USE SCHEMA IDENTIFIER(:silver_schema);

MERGE INTO dim_{entity} AS tgt          -- unqualified: session catalog.schema
USING (
  WITH deduped AS (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY {Natural_Key}
      ORDER BY {recency_column} DESC
    ) AS _rn
    FROM IDENTIFIER(:src_{logical} || '.{source_table}')
  )
  SELECT
    -- Surrogate key: deterministic, null-safe
    CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',
      COALESCE(CAST({Natural_Key} AS STRING), '~')
    ), 256), 1, 15), 16, 10) AS BIGINT) AS {Entity}_Key,
    -- Natural key
    src.{Natural_Key},
    -- Business attributes (apply TRY_CAST and NULLIF as needed)
    NULLIF(TRIM(src.{attr_col}), '') AS {Attr_Col},
    TRY_CAST(src.{date_col} AS DATE) AS {Date_Col},
    -- Metadata
    '{source_system}' AS _source_system
  FROM deduped src
  WHERE src._rn = 1
) AS src
ON tgt.{Entity}_Key = src.{Entity}_Key
WHEN MATCHED THEN UPDATE SET
    tgt.{Natural_Key} = src.{Natural_Key},
    tgt.{Attr_Col}    = src.{Attr_Col},
    tgt.{Date_Col}    = src.{Date_Col},
    tgt._source_system = src._source_system,
    tgt._loaded_at     = current_timestamp(),
    tgt._modified_by   = :job_name
WHEN NOT MATCHED THEN INSERT (
    {Entity}_Key, {Natural_Key}, {Attr_Col}, {Date_Col},
    _source_system, _loaded_at, _created_by, _modified_by
  )
  VALUES (
    src.{Entity}_Key, src.{Natural_Key}, src.{Attr_Col}, src.{Date_Col},
    src._source_system, current_timestamp(), :job_name, :job_name
  );
```

---

## SCD Type-2 Versioning MERGE Template  *(scd_strategy: type_2 — dimensional / hybrid-gold only)*

Type-2 needs **two statements** because a single MERGE cannot both close the prior version and
insert the new one against the same natural key. Run them in order in the transform: (1) close
rows whose tracked attributes changed, (2) insert the new current version. The surrogate hashes
natural key **+ `_effective_from`** so each version gets a distinct `{Entity}_Key`.

```sql
-- Databricks notebook source
-- Load notebook: dim_{entity} (SCD Type 2) — declares its own widgets, holds the MERGE. Run directly by the DAB job.
-- Natural Key: {Natural_Key} (STABLE) · tracked attrs: {Attr_Col}, {Date_Col}
-- CREATE WIDGET TEXT silver_catalog/silver_schema/src_*; USE CATALOG IDENTIFIER(:silver_catalog); USE SCHEMA IDENTIFIER(:silver_schema);

-- COMMAND ----------
-- (1) CLOSE the current version where a tracked attribute changed.
MERGE INTO dim_{entity} AS tgt
USING (
  WITH deduped AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY {Natural_Key} ORDER BY {recency_column} DESC) AS _rn
    FROM IDENTIFIER(:src_{logical} || '.{source_table}')
  )
  SELECT {Natural_Key}, NULLIF(TRIM({attr_col}), '') AS {Attr_Col}, TRY_CAST({date_col} AS DATE) AS {Date_Col}
  FROM deduped WHERE _rn = 1
) AS src
ON tgt.{Natural_Key} = src.{Natural_Key} AND tgt._is_current = TRUE
-- Change detection: OR across EVERY tracked attribute (<=> is null-safe). Add one clause per attr.
WHEN MATCHED AND (
       (tgt.{Attr_Col} <=> src.{Attr_Col}) = FALSE
    OR (tgt.{Date_Col} <=> src.{Date_Col}) = FALSE
    -- ... OR one line per additional tracked attribute
  )
  THEN UPDATE SET tgt._effective_to = current_timestamp(),
                  tgt._is_current   = FALSE,
                  tgt._modified_by  = :job_name;

-- COMMAND ----------
-- (2) INSERT the new current version for new NKs and changed NKs (now closed above).
MERGE INTO dim_{entity} AS tgt
USING (
  WITH deduped AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY {Natural_Key} ORDER BY {recency_column} DESC) AS _rn
    FROM IDENTIFIER(:src_{logical} || '.{source_table}')
  )
  SELECT
    CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',
      COALESCE(CAST({Natural_Key} AS STRING), '~'),
      CAST(current_timestamp() AS STRING)              -- version discriminator → new surrogate per version
    ), 256), 1, 15), 16, 10) AS BIGINT) AS {Entity}_Key,
    {Natural_Key}, NULLIF(TRIM({attr_col}), '') AS {Attr_Col}, TRY_CAST({date_col} AS DATE) AS {Date_Col},
    '{source_system}' AS _source_system
  FROM deduped WHERE _rn = 1
) AS src
-- match the OPEN current version; if none (new NK or just-closed), NOT MATCHED fires
ON tgt.{Natural_Key} = src.{Natural_Key} AND tgt._is_current = TRUE
WHEN NOT MATCHED THEN INSERT (
    {Entity}_Key, {Natural_Key}, {Attr_Col}, {Date_Col},
    _effective_from, _effective_to, _is_current,
    _source_system, _loaded_at, _created_by, _modified_by
  )
  VALUES (
    src.{Entity}_Key, src.{Natural_Key}, src.{Attr_Col}, src.{Date_Col},
    current_timestamp(), NULL, TRUE,
    src._source_system, current_timestamp(), :job_name, :job_name
  );
```

> Facts resolve a Type-2 FK by joining on natural key AND
> `fact.event_ts BETWEEN dim._effective_from AND COALESCE(dim._effective_to, TIMESTAMP'9999-12-31')`,
> then carrying the matched `{Entity}_Key`. A fact that must always point at the latest version
> instead joins on `dim._is_current = TRUE`. Validation adds a check that each natural key has
> **exactly one** `_is_current = TRUE` row.

---

## Silver Fact MERGE Template

```sql
-- Databricks notebook source
-- =============================================================================
-- Load notebook: fact_{name} — declares its own widgets, holds the MERGE. Run directly by the DAB job.
-- Target: <silver_catalog>.<silver_schema>.fact_{name}   (widgets)
-- Source: <src_{logical}>.{source_table}                 (widget prefix)
-- Grain: one row per {grain statement}
-- Strategy: Type 1 MERGE
-- =============================================================================
-- Header cells declare widgets, then set session context:
--   CREATE WIDGET TEXT silver_catalog/silver_schema/src_*; USE CATALOG IDENTIFIER(:silver_catalog); USE SCHEMA IDENTIFIER(:silver_schema);

MERGE INTO fact_{name} AS tgt          -- unqualified: session catalog.schema
USING (
  WITH deduped AS (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY {grain_columns}
      ORDER BY {recency_column} DESC
    ) AS _rn
    FROM IDENTIFIER(:src_{logical} || '.{source_table}')
    -- Optional watermark for incremental (target ref unqualified — session context):
    -- WHERE {updated_col} > (SELECT COALESCE(MAX(_source_updated_at), TIMESTAMP '1900-01-01') FROM fact_{name})
  ),
  -- Dedup FK lookup tables to prevent fan-out (silver dims — unqualified)
  dim_a_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY {A_Natural_Key}
      ORDER BY _loaded_at DESC
    ) AS _rn
    FROM dim_{A}
    WHERE {Entity}_Key != -1
  )
  SELECT
    -- Surrogate key: hash of grain natural keys
    CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',
      COALESCE(CAST(src.{grain_col_1} AS STRING), '~'),
      COALESCE(CAST(src.{grain_col_2} AS STRING), '~')
    ), 256), 1, 15), 16, 10) AS BIGINT) AS {Name}_Key,
    -- FK resolution: -1 maps misses to Unknown member
    COALESCE(dim_a.{A}_Key, -1) AS {A}_Key,
    COALESCE(dim_b.{B}_Key, -1) AS {B}_Key,
    -- Business columns
    src.{Natural_Key},
    src.{Degenerate_Col},
    TRY_CAST(src.{measure_col} AS DECIMAL(18,2)) AS {Measure_Amt},
    -- Metadata
    '{source_system}' AS _source_system
  FROM deduped src
  LEFT JOIN dim_a_deduped dim_a
    ON dim_a.{A_Natural_Key} = src.{fk_col_a} AND dim_a._rn = 1
  LEFT JOIN dim_{B} dim_b          -- unqualified: session catalog.schema
    ON dim_b.{B_Natural_Key} = src.{fk_col_b}
  WHERE src._rn = 1
) AS src
ON tgt.{Name}_Key = src.{Name}_Key
WHEN MATCHED THEN UPDATE SET
    tgt.{A}_Key        = src.{A}_Key,
    tgt.{B}_Key        = src.{B}_Key,
    tgt.{Natural_Key}  = src.{Natural_Key},
    tgt.{Measure_Amt}  = src.{Measure_Amt},
    tgt._source_system = src._source_system,
    tgt._loaded_at     = current_timestamp(),
    tgt._modified_by   = :job_name
WHEN NOT MATCHED THEN INSERT (
    {Name}_Key, {A}_Key, {B}_Key, {Natural_Key}, {Measure_Amt},
    _source_system, _loaded_at, _created_by, _modified_by
  )
  VALUES (
    src.{Name}_Key, src.{A}_Key, src.{B}_Key, src.{Natural_Key}, src.{Measure_Amt},
    src._source_system, current_timestamp(), :job_name, :job_name
  );
```

---

## Gold INSERT OVERWRITE Template

```sql
-- Databricks notebook source
-- =============================================================================
-- Load notebook: {business_name} — declares its own widgets, holds the INSERT OVERWRITE. Run directly by the DAB job.
-- Target: <gold_catalog>.<gold_schema>.{business_name}   (widgets)
-- Source: <silver_catalog>.<silver_schema> (multiple tables — widgets)
-- Strategy: INSERT OVERWRITE (full recompute)
-- =============================================================================
-- Gold WRITES gold but READS silver: header cells declare widgets, then set session to gold
-- (the write target); silver tables are read via a qualified IDENTIFIER prefix off the silver_* widgets.
--   CREATE WIDGET TEXT gold_catalog/gold_schema/silver_catalog/silver_schema/job_name;
--   USE CATALOG IDENTIFIER(:gold_catalog); USE SCHEMA IDENTIFIER(:gold_schema);

INSERT OVERWRITE {business_name}          -- unqualified: session = gold catalog.schema
SELECT
  f.{Business_Col_1},
  d.{Dimension_Attr},
  SUM(f.{Measure_Amt}) AS {Agg_Measure_Amt},
  COUNT(*) AS Record_Cnt,
  '{source_system}' AS _source_system,
  current_timestamp() AS _inserted_at,
  current_timestamp() AS _updated_at,
  :job_name AS _created_by,
  :job_name AS _modified_by
FROM IDENTIFIER(:silver_catalog || '.' || :silver_schema || '.fact_{name}') f
JOIN IDENTIFIER(:silver_catalog || '.' || :silver_schema || '.dim_{entity}') d
  ON f.{Entity}_Key = d.{Entity}_Key
WHERE d.{Entity}_Key != -1  -- Exclude Unknown member from aggregations
GROUP BY f.{Business_Col_1}, d.{Dimension_Attr};
```

---

## Defensive Coding Rules

### Critical Rules (MUST follow)

1. **Never use `UPDATE SET *` or `INSERT *`** — Target tables may have more columns than source provides. Always use explicit column lists.

2. **Always deduplicate source data** — Use `ROW_NUMBER() OVER (PARTITION BY {natural_key} ORDER BY {recency} DESC)` and filter `WHERE _rn = 1`.

3. **Deduplicate FK lookup joins** — If a parent table has multiple rows for the same join key, wrap it in a dedup CTE first.

4. **Use TRY_CAST for dirty data** — Bronze data often has malformed values. `TRY_CAST` returns NULL instead of failing. For date columns, read the source's physical format from `conventions.yml` `date_formats:` (SAP is `yyyyMMdd`, most others ISO `yyyy-MM-dd`) and parse with `TRY_TO_DATE(col, fmt)` — never the `TRY(TO_DATE(...))` wrapper (Rule 25 / SDP Rule B) — then verify a 5-row sample.

5. **Avoid OR in join conditions** — Can cause fan-out. Prefer single join key or COALESCE.

6. **Incremental loads for large tables** — Do NOT default large facts to full MERGE. Pick a strategy per entity via the **Load Strategy Decision** section above (FULL_MERGE / INCREMENTAL_MERGE / APPEND_ONLY / SDP). Watermark on the *source event timestamp* carried as `_source_updated_at`, not `_loaded_at`.

7. **Build surrogate keys with COALESCE on each key part** — Avoids hash collisions on NULLs. Use `'~'` as the null sentinel in CONCAT_WS.

8. **Standardize empty strings to NULL** — Apply `NULLIF(TRIM(...), '')` to all string columns that are not natural keys or bounded code columns.

9. **UTC conversion** — All TIMESTAMP columns stored in UTC. Convert source timezones during silver load using `CONVERT_TIMEZONE`.

10. **FK resolution always uses COALESCE to -1** *(dimensional / `hybrid`-gold only)* — Never leave FK columns as NULL; the Unknown member (-1) absorbs all misses. **This is a dimensional-mode convention and does NOT apply in `normalized` / `hybrid`-silver:** there is no `-1` Unknown member seeded there, so normalized FKs stay **NULL** when unresolved (the null rate is a DQ metric, not a `-1` sentinel) — COALESCE-ing a normalized STRING FK to `-1` produces an orphan pointing at a row that doesn't exist. See `ddl-and-modeling.md` Normalized-mode rules and `sdp-templates.md` Normalized-mode templates.

11. **Never inline-recompute FK surrogate keys from raw source values** *(dimensional / `hybrid`-gold)* — Always LEFT JOIN to the already-loaded silver dim to get FK values. Inline SHA2 recomputation silently fails whenever the fact source provides a different *representation* of the natural key than the dim was built from (e.g., a name field instead of a code field). The dim JOIN approach is the only safe method — it surfaces mismatches via COALESCE to -1 rather than producing quietly wrong FK values with 0% join rate and no error.

    > **Normalized / `hybrid`-silver differs.** There the FK is the parent's own natural-key-derived id (`SHA2(parent_nk)`), and the parent PK is computed the same deterministic way — so when the child source **carries the parent's natural key**, computing `SHA2(parent_nk)` directly is the *correct* resolution (no join, NULL sentinel, no -1); see the FK-resolution decision tree in `sdp-templates.md`. Use a join+dedup CTE only when the link is **indirect** (the child lacks the parent key). The "never inline-recompute" rule above is about dimensional **surrogates**, which are arbitrary and unshareable — it does not forbid the normalized direct-SHA2 pattern, whose safety comes from the shared deterministic key derivation.

    **Example — source semantic mismatch (Acuity Manufacturing V2, July 2026):** `dim_plant.Plant_Key = SHA2(tbl_plants.Code)` where `Code = "001"`. DFF fact source `tbl_efficiencyhxh_daily.Plant = "SEDC"` (plant *name*, not numeric code). Computing `SHA2("SEDC")` inline produced a completely different BIGINT — every Plant_Key and Work_Center_Key in `fact_oee_record` (156k rows) was an orphan with 0% join rate, with no error or warning raised at load time.

    **Correct pattern — join to the loaded dim:**
    ```sql
    -- Add a deduped lookup CTE per FK dim BEFORE the SELECT:
    dim_plant_lkp AS (
      SELECT Plant_Key, Plant_Name,
        ROW_NUMBER() OVER (PARTITION BY Plant_Name ORDER BY _loaded_at DESC) AS _rn
      FROM dim_plant          -- unqualified: session catalog.schema
      WHERE Plant_Key != -1
    )
    -- In SELECT (not an inline SHA2):
    COALESCE(dim_p.Plant_Key, -1) AS Plant_Key
    -- In FROM:
    LEFT JOIN dim_plant_lkp dim_p
      ON dim_p.{join_attribute} = TRIM(src.{source_fk_column}) AND dim_p._rn = 1
    ```
    The `{join_attribute}` on the dim may be *any* attribute that matches the fact source — it does not have to be the same column the dim's natural key was hashed on.

    **Semantic mismatch check (required during Phase 3/4):** For each FK in every fact, sample both tables and confirm the fact source column and the dim attribute you plan to join on contain the *exact same values*. Common mismatches to check: name vs. code, abbreviation vs. full name, internal numeric ID vs. external string code, padded vs. unpadded numbers. If they differ, join on the matching attribute — do not recompute the hash from the mismatched field.

12. **Reconcile MERGE columns against the TARGET schema before authoring** — Run
    `{silver_catalog}.information_schema.columns` (**catalog-qualified** — an unqualified
    `information_schema.columns` resolves against the session's current catalog and can return an
    empty manifest, silently passing this gate) or `DESCRIBE` on the target table, and use the result
    as the authoritative column list. **Every column** in the `ON` clause, `WHEN MATCHED THEN UPDATE SET`,
    and `WHEN NOT MATCHED THEN INSERT (…)` must appear in that list. **Never derive a target column
    name from business understanding of the source** — always read the actual schema. This is the
    build-side mirror of the source reconciliation gate (`discovery-and-gap-analysis.md` gate 2b);
    it prevents `DELTA_MERGE_UNRESOLVED_EXPRESSION`/`UNRESOLVED_COLUMN` from a mis-remembered name
    (`quote_number` vs the model's `number`, `customer_id` vs `account_id`, `total_amount` vs
    `quoted_value`), which recurs in `normalized` mode where the model's names diverge from common
    business terminology.

    **MERGE pre-flight (`EXPLAIN`) — catch column errors before the first real load.** After
    authoring a MERGE and before running it against real data, run `EXPLAIN` on the MERGE statement
    (or a dry MERGE against an empty/CTAS clone). If it fails with `UNRESOLVED_COLUMN` /
    `DELTA_MERGE_UNRESOLVED_EXPRESSION`, fix the SQL before attempting a real load. This turns a
    "run → fail → debug → fix → re-run" cycle into a "check → fix → run" one — cheap insurance on
    normalized entities with 30–45 columns.

---

## Common Failure Patterns

| Error | Root Cause | Fix |
| --- | --- | --- |
| `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE` | Duplicate PKs in source query | Add ROW_NUMBER() dedup |
| `DELTA_MERGE_UNRESOLVED_EXPRESSION` | UPDATE SET * with mismatched columns, or an authored target column that isn't in the table (e.g. `quote_number` vs model `number`) | Explicit column lists; **prevent** via target reconciliation (Rule 12) + pre-flight `EXPLAIN` |
| `CAST_INVALID_INPUT` | Dirty data in type conversion | Use TRY_CAST() |
| `UNRESOLVED_COLUMN` | Column name mismatch (source OR target) | **Prevent** via the bilateral reconciliation gate (Rule 12 / gate 2b) before authoring; reactively, check via `DESCRIBE` |
| FK orphan rate > 1% | Missing join, wrong key, or source gaps | Add/fix FK lookup join; check join key alignment |
| **FK orphan rate = 100% (silent — no error)** | Fact source uses different *representation* of NK than dim was hashed on (name vs. code, external vs. internal ID) | Replace inline SHA2 with LEFT JOIN to loaded dim on the matching attribute (Rule 11) |
| PK duplicates | Non-unique grain in source | Refine PARTITION BY in ROW_NUMBER() or revisit grain definition |

---

## Surrogate Key Formula (Reference)

> **Read the canonical expression from `conventions.yml` `surrogate_key_formula.bigint` verbatim**
> — do NOT reverse-engineer it from loaded data. Canonical BIGINT formula (single key):
> `CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST({natural_key} AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT)`.
> Composite keys add more `COALESCE(CAST(k AS STRING), '~')` terms inside `CONCAT_WS`.
> Null sentinel is `'~'`, never `∅`.
>
> **FK resolution is mode-dependent:** In `normalized` and `hybrid` (silver layer), use the same
> expression for FK resolution — a FK to a parent is that parent's hashed PK recomputed inline.
> In `dimensional` and `hybrid` (gold layer), resolve FKs to parent surrogates via JOIN to the
> dim table's PK column — never inline recompute (per Critical Rule 11).

```sql
-- Single natural key
CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',
  COALESCE(CAST({Natural_Key} AS STRING), '~')
), 256), 1, 15), 16, 10) AS BIGINT) AS {Entity}_Key

-- Composite natural key (multiple columns form the unique identifier)
CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',
  COALESCE(CAST({Key_Part_1} AS STRING), '~'),
  COALESCE(CAST({Key_Part_2} AS STRING), '~'),
  COALESCE(CAST({Key_Part_3} AS STRING), '~')
), 256), 1, 15), 16, 10) AS BIGINT) AS {Entity}_Key
```

**Rules:**
- Always COALESCE each key part to `'~'` before hashing (prevents collisions where NULL + value = value + NULL)
- CAST each key part to STRING before concatenation
- Use `CONCAT_WS('|', ...)` to delimit key parts
- Take first 15 hex characters of SHA2-256, convert to BIGINT via CONV
- Never use IDENTITY (breaks idempotency)
