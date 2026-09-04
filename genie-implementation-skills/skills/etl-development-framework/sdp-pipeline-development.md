# SDP Pipeline Development (etl_type: sdp_pipeline)

## When to Use

Load this whenever `conventions.yml` `etl_type: sdp_pipeline`. It REPLACES the MERGE
load notebook and the daily `job` resource with a whole-domain Lakeflow
Declarative Pipeline. Everything else in the skill (discovery, gap analysis — **Phase 3 still writes
`docs/gap_analysis.md`, same format as merge_notebook mode** — requirements gate, `build_manifest.md`,
checkpoint state) is reused unchanged. In `etl_type: merge_notebook` (the default) this file does not
apply.

> **No beta dependencies, and NO build-time testing in this mode.** SDP deliberately avoids two
> SDP betas: **native `parameters:`** (bronze paths are hardcoded literals) and the **LDP unit-test
> framework** (`pyspark.pipelines.testing`, Editor-only). There is **no test/validation gate in the
> SDP build at all** — no unit tests, no post-load validation notebook, no TDD pre-advance gate.
> Confidence comes from inline `EXPECT` constraints + the pipeline event log while running, and from
> the downstream `domain-model-validation` skill afterward. Revisit build-time testing once the LDP
> testing framework leaves beta and gains a headless (bundle/CLI) run path.

> **DDL lives inside the flow.** There is NO separate DDL-as-setup step in this mode —
> `CREATE STREAMING TABLE` / `MATERIALIZED VIEW` carry the full inline schema (columns,
> types, COMMENT, `CONSTRAINT ... EXPECT`, CLUSTER BY) AND the defining query in one
> object. The MERGE rule "DDL is SETUP, kept out of the daily job" does not apply here.

> 🔴 **NEVER emit `CONSTRAINT ... PRIMARY KEY` or `FOREIGN KEY` inside a Materialized View (or a
> plain Streaming Table's) column spec.** SDP serverless does **not** accept DDL constraints in an
> MV/ST inline schema — it is a `PARSE_SYNTAX_ERROR` (the parser chokes at the next `EXPECT`), and
> in the sales-order SDP run it broke all 17 files on the first update. The **only** constraint form
> valid inline is `CONSTRAINT <name> EXPECT (<expr>) [ON VIOLATION ...]`. Enforce **PK uniqueness via
> a grain expectation** — `CONSTRAINT valid_grain EXPECT ({natural_key} IS NOT NULL) ON VIOLATION
> DROP ROW` — not a `PRIMARY KEY` clause. If PK/FK metadata is wanted for documentation, put it in a
> column `COMMENT` (`COMMENT 'PK: SHA2(...)'`), never a constraint.
>
> Two narrow exceptions: (a) the `merge_notebook` path's separate DDL tables DO take
> `ALTER TABLE ADD CONSTRAINT ... PRIMARY KEY` (informational UC constraints) — that is unchanged,
> see `ddl-and-modeling.md`; (b) Streaming Tables fed by `AUTO CDC` / `APPLY CHANGES` may declare a
> `PRIMARY KEY` for the CDC keying — so distinguish MV (never) from an AUTO CDC ST (allowed for the
> CDC key). When in doubt on an MV, the answer is always: no DDL constraint, use `EXPECT`.

> **`output_model` still applies in SDP mode** — `normalized`, `dimensional`, or `hybrid`. The
> templates below are written in the `dimensional`/`hybrid-gold` shape (`dim_/fact_` + SHA2 `_Key`)
> for illustration; in the default `normalized` (and the **silver layer of `hybrid`**) they instead follow the vibe model —
> product-named tables, natural PKs, no surrogates (per the "⚠️ Precedence & key strategy by mode"
> note in `naming-standards.md`). For **`hybrid`** — normalized 3NF silver first, THEN a
> dimensional gold star built downstream from that silver (**not** both at once) — see the
> **"Hybrid mode: the downstream gold star layer"** section below; it is the authoritative SDP
> recipe for the gold layer.

## Load-strategy → SDP object mapping

The Load Strategy Decision (`merge-and-defensive-coding.md`) still classifies each entity by
mutability then volume. In this mode the classification selects an SDP object + flow, not a
MERGE variant:

| Entity classification (spec §5) | SDP object |
|---|---|
| Small conformed dimension (fully recomputable) | `CREATE MATERIALIZED VIEW dim_x … AS SELECT` (code: **MV**) |
| Append-only ledger fact (immutable) | `CREATE STREAMING TABLE fact_x …` + append flow (`AS`/`FLOW INSERT BY NAME`) (code: **ST-APPEND**) |
| Mutable SCD1 upserts / mutable-no-watermark | `STREAMING TABLE` + `FLOW … AUTO CDC … STORED AS SCD TYPE 1` (code: **ST-CDC1**) |
| SCD2 dimension (`scd_strategy: type_2`) | `STREAMING TABLE` + `FLOW … AUTO CDC … STORED AS SCD TYPE 2` (code: **ST-CDC2**) |
| >100M mutable fact | `STREAMING TABLE` + incremental / `AUTO CDC` flow (code: **ST-CDC1** or **ST-CDC2** per scd_strategy) |

`AUTO CDC` (deletes / SCD2 / mutable-no-watermark) **needs CDF on bronze**
(`delta.enableChangeDataFeed = true`, enabled going forward) — flag it as the same cross-team
dependency the MERGE path already calls out. Append-only and simple recompute need no CDF.

**When to graduate an entity from MV to a Streaming Table (volume thresholds).** A Materialized View
full-recomputes on every refresh — free at small volume, costly as the source grows. Default small
entities to `MV`, and record a graduation note in the spec/manifest so scaling is a known decision,
not a surprise:

| Source rows | Guidance |
|---|---|
| **< 1M** | `MV` is always fine — full recompute is trivial. |
| **1M–5M** | `MV` is fine while refresh stays fast (< ~5 min); watch the refresh time. |
| **> 5M** | Re-evaluate: **append-only → `ST-APPEND`** (incremental, no re-scan); **mutable → `AUTO CDC` (`ST-CDC1/2`)** or an incremental `REPLACE WHERE` flow. Full MV recompute stops being free. |

Note the trigger inline per entity — e.g. "MV now (23K rows); re-assess object type when `vbep`
exceeds ~5M rows." Object-type changes (MV→ST) require a **full refresh** on next deploy.

## Templates — SQL dialect (`etl_language: sql`)

**Materialized view (recomputable dimension):**

```sql
-- Databricks notebook source
-- Declarative source: dim_plant (materialized view). Inline schema + EXPECT + query.
CREATE OR REFRESH MATERIALIZED VIEW dim_plant (
  Plant_Key      BIGINT      COMMENT 'Surrogate key (SHA2 of natural key)',
  Plant_Bk       STRING      COMMENT 'Natural/business key',
  Plant_Name     STRING      COMMENT 'Plant display name',
  _source_system STRING      COMMENT 'Originating system',
  CONSTRAINT valid_bk EXPECT (Plant_Bk IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Plant_Key)
COMMENT 'Conformed plant dimension'
AS
SELECT
  CAST(CONV(SUBSTR(SHA2(CONCAT_WS('|', COALESCE(CAST(Code AS STRING),'∅')),256),1,15),16,10) AS BIGINT) AS Plant_Key,
  Code AS Plant_Bk,
  NULLIF(TRIM(Name),'') AS Plant_Name,
  'SAP_S4' AS _source_system
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY Code ORDER BY LAST_UPDATE_DATE DESC) AS _rn
  FROM manufacturing_bronze.sap_sd.tbl_plants   -- hardcoded fully-qualified bronze path (see below)
) WHERE _rn = 1;
```

**Streaming table + AUTO CDC (SCD1 mutable dim / fact upsert):**

```sql
-- Databricks notebook source
-- Declarative source: dim_customer (streaming table + AUTO CDC, SCD type 1).
CREATE OR REFRESH STREAMING TABLE dim_customer (
  Customer_Key   BIGINT  COMMENT 'Surrogate key',
  Customer_Bk    STRING  COMMENT 'Natural key',
  Customer_Name  STRING  COMMENT 'Name',
  _source_system STRING,
  CONSTRAINT valid_bk EXPECT (Customer_Bk IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Customer_Key)
COMMENT 'Customer dimension (SCD1)';

CREATE FLOW customer_cdc AS AUTO CDC INTO dim_customer
FROM (
  SELECT
    CAST(CONV(SUBSTR(SHA2(CONCAT_WS('|',COALESCE(CAST(cust_id AS STRING),'∅')),256),1,15),16,10) AS BIGINT) AS Customer_Key,
    cust_id AS Customer_Bk,
    NULLIF(TRIM(cust_name),'') AS Customer_Name,
    'SALESFORCE' AS _source_system,
    last_modified AS _source_updated_at
  FROM STREAM manufacturing_bronze.salesforce_crm.accounts   -- hardcoded fully-qualified bronze path
)
KEYS (Customer_Bk)
SEQUENCE BY _source_updated_at
STORED AS SCD TYPE 1;
```

**SCD Type 2** — identical to the SCD1 flow but `STORED AS SCD TYPE 2` (SDP manages
`__START_AT`/`__END_AT` version columns; declare them in the table spec per the current docs).
This REPLACES the two-statement versioning MERGE in `merge-and-defensive-coding.md`.

**Append-only ledger fact (streaming table, no CDC):**

```sql
CREATE OR REFRESH STREAMING TABLE fact_material_txn (
  Material_Txn_Key BIGINT,
  Txn_Bk           STRING,   -- degenerate natural key, retained so the grain EXPECT has a real column to test
  Plant_Key        BIGINT,
  Txn_Amt          DECIMAL(18,2),
  _source_system   STRING,
  -- Guard the GRAIN on the natural key, NOT the surrogate. The SHA2 surrogate is never NULL
  -- (COALESCE(..,'∅') always hashes to a value), so a constraint on Material_Txn_Key can never
  -- fire — a row with a NULL txn_id would slip through under a fabricated key. Test the source NK.
  CONSTRAINT valid_grain EXPECT (Txn_Bk IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Plant_Key)
AS SELECT
  CAST(CONV(SUBSTR(SHA2(CONCAT_WS('|',COALESCE(CAST(txn_id AS STRING),'∅')),256),1,15),16,10) AS BIGINT) AS Material_Txn_Key,
  CAST(txn_id AS STRING) AS Txn_Bk,
  COALESCE(p.Plant_Key,-1) AS Plant_Key,
  TRY_CAST(s.amount AS DECIMAL(18,2)) AS Txn_Amt,
  'SAP_S4' AS _source_system
FROM STREAM manufacturing_bronze.sap_sd.material_txn s   -- hardcoded fully-qualified bronze path
LEFT JOIN dim_plant p ON p.Plant_Bk = TRIM(s.plant_code);
```

> 🔴 **Bronze source paths are HARDCODED as fully-qualified `catalog.schema.table` — SDP does not
> parameterize them.** The native LDP `parameters:` block is a **beta**, and it only half-works:
> `IDENTIFIER(:param)` resolves in a **materialized view** `AS SELECT`, but `STREAM
> IDENTIFIER(:param …)` in a `CREATE STREAMING TABLE`/`CREATE FLOW` fails at runtime with
> `[UNRESOLVABLE_TABLE_VALUED_FUNCTION]` (hit on a real build). Rather than carry a half-working
> beta and split MV-vs-ST parameterization rules, **SDP hardcodes every bronze path** — in both MV
> and ST sources, both SQL and Python. The bronze catalog/schema for a domain is a build-time
> constant from `conventions.yml` `bronze_sources:`; write it directly into each source. Do NOT
> emit a pipeline `parameters:` block, `:param` markers, `IDENTIFIER(:param)`, or `spark.conf.get`
> for bronze paths. (Revisit if/when native parameters leaves beta and supports streaming sources.)

> **FK resolution** still LEFT JOINs the already-defined dim (Rule 11 from
> `merge-and-defensive-coding.md`) and COALESCEs misses to -1 — never inline-recompute the FK
> surrogate from the fact source.
>
> 🔴 **Every FK-resolution LEFT JOIN must be 1:1 on the lookup side — or it fans out the fact.** If
> the parent table has more than one row per join key, the LEFT JOIN multiplies fact rows and breaks
> the grain. A real build hit this: the silver `order` entity LEFT JOINed `quote` on
> `converted_order_number`, but multiple quotes shared the same value → **136 duplicate order rows**.
> This is Rule 3 / Rule 11 from `merge-and-defensive-coding.md`, and it applies identically to SDP
> MVs and streaming tables. **Wherever the lookup side is not guaranteed unique on the join key**
> (especially cross-source joins, where the foreign system's schema gives you no uniqueness
> guarantee), dedup it in a subquery/CTE first:
> `... FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY join_key ORDER BY <recency> DESC) AS _rn FROM parent) WHERE _rn = 1`.
> Verify grain with a PK-count check after the first run (declared count == distinct-NK count).
>
> ⚠️ **Stream-static join permanence (append-only only).** In a `ST-APPEND` fact this LEFT JOIN
> is a **stream-static** join: each fact row's FK is resolved to whatever the dim held **at append
> time**. Because the fact is append-only (no CDC, no reprocessing), a row that arrives before its
> `dim_plant` row materializes — or whose plant key later changes — is written with `Plant_Key = -1`
> and **stays -1 forever**, even after the dimension catches up. Two mitigations: (a) enforce the
> **wave order** so all wave-1 dims materialize before wave-2 facts in the same pipeline update
> (declare the dim reference so SDP orders it first), and (b) if late-arriving dimension members are
> expected and FK completeness matters, make the fact a **materialized view** (recomputable) instead
> of `ST-APPEND`, trading incremental cost for correct re-resolution. Flag this trade-off in the spec.

## Templates — Python dialect (`etl_language: python`)

Same objects via the `@dlt` decorators. Bronze paths are **hardcoded** fully-qualified strings
(no `spark.conf.get`, no parameters — see the Parameterization note). **Confirm at implementation:**
the Python source module generation (`import dlt` — classic, vs `from pyspark.pipelines import dlt`
— newer) must match the installed runtime; verify against the target DBR/LDP runtime before
authoring.

```python
# Databricks notebook source
import dlt
from pyspark.sql import functions as F

# STEP 1 — a streaming view does the derivation (surrogate, renames, audit ts). The AUTO CDC
# flow's keys/sequence_by/expectations reference the DERIVED column names, so its source MUST be
# this transformed view — NOT the raw `accounts` table (raw has cust_id/cust_name/last_modified,
# not Customer_Bk/_source_updated_at). Pointing the flow straight at raw errors column-not-found.
@dlt.view(name="v_customer_src")
def v_customer_src():
    return (
        spark.readStream.table("manufacturing_bronze.salesforce_crm.accounts")  # hardcoded bronze path
        .select(
            F.expr(
                "CAST(CONV(SUBSTR(SHA2(CONCAT_WS('|',COALESCE(CAST(cust_id AS STRING),'∅')),256),1,15),16,10) AS BIGINT)"
            ).alias("Customer_Key"),
            F.col("cust_id").alias("Customer_Bk"),
            F.nullif(F.trim(F.col("cust_name")), F.lit("")).alias("Customer_Name"),
            F.lit("SALESFORCE").alias("_source_system"),
            F.col("last_modified").alias("_source_updated_at"),
        )
    )

# STEP 2 — the streaming target + AUTO CDC flow reference the view's derived columns.
dlt.create_streaming_table(
    name="dim_customer",
    comment="Customer dimension (SCD1)",
    cluster_by=["Customer_Key"],
    expect_all_or_drop={"valid_bk": "Customer_Bk IS NOT NULL"},
)
dlt.create_auto_cdc_flow(
    target="dim_customer",
    source="v_customer_src",          # the DERIVED view, not the raw table
    keys=["Customer_Bk"],
    sequence_by=F.col("_source_updated_at"),
    stored_as_scd_type=1,
)
```

> Confirm `create_auto_cdc_flow(... stored_as_scd_type=2)` against the installed SDK when
> authoring SCD2. Bronze paths are hardcoded literals (see Parameterization) — never interpolate
> analyst/free-text into `spark.sql`/f-strings; the only interpolated values are build-time
> config constants.

## Parameterization — NONE (bronze paths are hardcoded)

> 🔴 **SDP does not parameterize bronze source paths in the current beta.** The native LDP
> `parameters:` block is a beta and only half-works (`IDENTIFIER(:param)` in MVs yes; `STREAM
> IDENTIFIER(:param)` in streaming tables/FLOWs no — see the ST-APPEND note). To keep SDP free of
> half-working beta dependencies, **write bronze paths as fully-qualified `catalog.schema.table`
> literals directly in each source** — MV and ST, SQL and Python alike.

- **Source of truth:** `conventions.yml` `bronze_sources:` gives the `catalog.schema` for each
  logical source; the table name comes from the entity's S2T mapping. Concatenate them at authoring
  time into a literal (e.g. `meridian_bronze.fieldlink.service_order`) — this is a
  build-time constant, not a runtime input.
- **Do NOT emit:** a pipeline `parameters:` block, `:param` markers, `IDENTIFIER(:param)`, or
  `spark.conf.get(...)` for bronze paths. The widget→session-var bridge is a MERGE-path mechanism
  and also must not appear.
- **What still varies per target:** only the **silver write target** (`catalog:`/`schema:` on the
  pipeline resource, via DAB `${var...}`) and deployment mode. The bronze read paths are fixed for
  the domain. If a future need arises to retarget bronze per environment, revisit once native
  parameters leaves beta and supports streaming sources.

## Inline schema: declared-vs-inferred type discipline (READ BEFORE AUTHORING)

> 🔴 **The #1 cause of SDP pipeline failures is a declared column type that does not match the type
> Spark *infers* from the defining query.** Because an SDP object carries BOTH an explicit column
> spec AND the `AS SELECT` that populates it, any mismatch between the two aborts the update with a
> schema error. This is a confirmed **recurring** failure — it fired on both the silver and the gold
> arm of the same build. Apply the rules below while authoring, not after failing.

### Rule A — CAST every computed expression to its declared type

Spark widens arithmetic results beyond the operands' precision. If you declare a narrower type than
the inferred one, the update fails. **Wrap every computed column in an explicit `CAST(... AS <declared type>)`.**

- **DECIMAL widening — the big one.** For `DECIMAL(p,s)` operands, Spark infers:
  - Addition / subtraction → `DECIMAL(max(p1,p2) + 1, ...)` — so `COALESCE(a,0) - COALESCE(b,0)` on
    two `DECIMAL(15,2)` infers `DECIMAL(16,2)`, not `DECIMAL(15,2)`.
  - Multiplication → `DECIMAL(p1 + p2 + 1, s1 + s2)` — e.g. `DECIMAL(15,2) * DECIMAL(15,2)` infers
    `DECIMAL(31,4)`.
  - Division → a **much** wider type via a complex rule (scale grows to `s1 + p2 + 1`, precision to
    the 38 cap) — the exact inferred type is impractical to predict by hand, which is exactly why you
    must CAST rather than guess. `ROUND(x/y*100, 2)` still infers far wider than the `DECIMAL(7,2)` a
    percentage column wants.
  - **Fix:** `CAST(ROUND(x/y*100, 2) AS DECIMAL(7,2)) AS Pct_Col` — the CAST forces the declared
    precision. Never let a bare arithmetic expression populate a DECIMAL column.
- **Timestamp vs date.** `_source_updated_at` is declared `TIMESTAMP`, but `TRY_TO_DATE(col,'yyyyMMdd')`
  infers `DATE` → mismatch. Always `CAST(TRY_TO_DATE(col, fmt) AS TIMESTAMP)` when the source is a
  date-only column feeding a TIMESTAMP column. Never bare `TRY_TO_DATE` into a TIMESTAMP.
- **String literals infer NOT NULL.** `'SAP_S4' AS _source_system` infers `STRING NOT NULL`, while
  the column spec says `nullable=true`. This is **harmless** (the wider/looser nullability wins) —
  call it out so builders don't panic and "fix" a non-problem.

### Rule B — serverless SQL function compatibility

Some functions resolve on older DBR runtimes but **fail on serverless SQL** with `[UNRESOLVED_ROUTINE]`.
SDP pipelines run serverless — use the serverless-safe form:

| Do NOT use | Use instead | Note |
|---|---|---|
| `DAYOFWEEK_ISO(d)` | `WEEKDAY(d) + 1` | `WEEKDAY` returns 0=Mon..6=Sun; +1 gives ISO 1=Mon..7=Sun |
| — | `WEEKOFYEAR(d)` | fine on serverless |
| `DAYOFWEEK(d)` (if you need ISO) | `WEEKDAY(d) + 1` | `DAYOFWEEK` returns 1=Sun..7=Sat (non-ISO) |

This bites `dim_date` calendar dimensions hardest (they lean on day-of-week math). When authoring a
`dim_date`, use `WEEKDAY()+1` for the ISO weekday and verify any other date-part function against
serverless before relying on it.

🔴 **NEVER wrap a cast/parse in the `TRY(...)` higher-order form — use the `TRY_*` builtins.**
`TRY(TO_DATE(col,'yyyyMMdd'))` and `TRY(CAST(col AS ...))` are **not supported on serverless Spark**
and fail at parse/plan time. This has now recurred across three projects (merge_notebook
sales-order, normalized field_service, SDP sales-order). Always write the dedicated builtin
directly:

| Do NOT use | Use instead |
|---|---|
| `TRY(TO_DATE(col, 'yyyyMMdd'))` | `TRY_TO_DATE(col, 'yyyyMMdd')` |
| `TRY(CAST(col AS DECIMAL(15,2)))` | `TRY_CAST(col AS DECIMAL(15,2))` |
| `TRY(TO_TIMESTAMP(col))` | `TRY_CAST(col AS TIMESTAMP)` (or `CAST(TRY_TO_DATE(...) AS TIMESTAMP)` for a date-only source — Rule A) |

Check this before emitting ANY type-casting SQL — it is a hard rule, not a preference.

### Rule C — verify source date/timestamp FORMATS before authoring (30-second probe)

The S2T spec names a watermark/timestamp column but rarely states its **physical format**. SAP columns
named `*_ts`, `*_dat`, or `*date` are frequently `yyyyMMdd` **strings**, not ISO timestamps — so
`TRY_CAST(col AS TIMESTAMP)` returns NULL for every row. Combined with `ON VIOLATION DROP ROW`, that
silently empties the whole table (see the Data-quality section's silent-0-row gate). Before authoring
any entity, probe each date/timestamp source column:

```sql
SELECT col, TRY_CAST(col AS TIMESTAMP) AS as_ts, TRY_TO_DATE(col, 'yyyyMMdd') AS as_yyyymmdd
FROM {bronze_source} WHERE col IS NOT NULL LIMIT 5;
```

If `as_ts` is NULL but `as_yyyymmdd` resolves, the column is a `yyyyMMdd` string — parse it with
`CAST(TRY_TO_DATE(col,'yyyyMMdd') AS TIMESTAMP)`, not `TRY_CAST(... AS TIMESTAMP)`. This one check
prevents the most damaging SDP failure mode (a green pipeline that produced an empty table).

### Incremental build loop — author by tier, dry-run before deploy (do NOT write-all-then-test)

> 🔴 **The write-all-then-test anti-pattern is the costliest SDP build mistake.** Authoring all N
> sources and triggering a single pipeline update surfaced **14 errors at once** in the sales-order
> run (~45 min of tangled diagnosis) and hid the PRIMARY-KEY syntax error behind 16 other files.
> The tier ordering the assessment already gives you IS the validation progression — use it.

**The loop (mandatory for any multi-entity SDP build):**

1. **Navigate to the SDP pipeline editor first.** After the pipeline resource is created + deployed,
   open the pipeline editor page (Genie Code `openAsset` with `assetType="pipeline-editor"`) and
   author/fix sources from there — it has SDP-aware tooling (correct MV/constraint syntax, per-flow
   dry-run, pipeline-scoped file editing, plan-time diagnostics) that the general file editor lacks.
2. **Author one tier at a time, T0 first.** Write the T0 (root dim/master) sources, then stop.
3. **Dry-run each new source before moving on** — run its `AS SELECT` body (without the
   `CREATE ... ()` wrapper) and compare `df.schema` to the declared column list, and/or
   `spark.sql(f"EXPLAIN {ddl}")` on the full statement. This catches **at plan time**:
   - `UNRESOLVED_COLUMN` (a referenced column doesn't exist — the reconciliation gate's backstop),
   - `PARSE_SYNTAX_ERROR` (an illegal MV `PRIMARY KEY`/`FOREIGN KEY` constraint),
   - type mismatches (Rule A declared-vs-inferred).
   MVs validate at plan time, so `EXPLAIN` is a real gate here (unlike MERGE notebooks that only
   fail at runtime). Do NOT proceed to the next tier until the current tier's sources all parse.
4. **Trigger the pipeline update once a tier parses**, verify it materialized (row-count check —
   see the silent-0-row gate), then author the next tier. Writing `sales_area.sql` alone first would
   have caught the PRIMARY KEY error before the other 16 files were ever written.

The batch discipline is the same ≤4-per-batch, verify-before-next cap the MERGE path uses
(`autonomous-validation` Batching Discipline) — SDP just validates via dry-run/plan instead of a
post-load DQ notebook (there is none in this mode).

## Data quality — inline EXPECT

DQ moves from the standalone `validate_silver` notebook INTO each declarative object as
`CONSTRAINT <name> EXPECT (<expr>) [ON VIOLATION { DROP ROW | FAIL UPDATE }]`. Map the spec
§6 thresholds to expectations. There is no separate recurring DQ notebook in this mode.

- **PK / grain not null → `ON VIOLATION FAIL UPDATE`** (or `DROP ROW`), tested on the **natural
  key**, not the SHA2 surrogate (the surrogate is never NULL — see the `valid_grain` note on the
  append-only template above).
- **Soft thresholds (`pct nulls < x`, range checks) → warn** (bare `EXPECT`, tracked in the event log).
- **FK orphans are NOT a FAIL-UPDATE constraint here — this is deliberate.** The fact templates
  resolve every unmatched FK to the **-1 Unknown member** via `COALESCE(dim.Key, -1)` (the same
  Rule 11 philosophy the MERGE path uses), so by the time any EXPECT runs there are no NULL/orphan
  FKs left to catch — an `EXPECT (FK IS NOT NULL)` would trivially pass and a `FAIL UPDATE` on it
  is unrealizable. Monitor FK health instead as a **soft** expectation on the -1 rate, e.g.
  `CONSTRAINT fk_resolved EXPECT (Plant_Key != -1)` (bare EXPECT → tracks the orphan-to-Unknown
  rate in the event log without failing the update). Escalate to `FAIL UPDATE` only if the domain
  truly forbids Unknown members — but that also means dropping the `-1` COALESCE, which changes the
  fact's semantics; flag it in the spec rather than defaulting to it.

> 🔴 **Silent-0-row trap — `ON VIOLATION DROP ROW` can empty a table and still exit GREEN.**
> `DROP ROW` is intentionally non-failing: it discards violating rows and lets the update succeed. But
> if a bug makes *every* row violate a grain/parse constraint (the classic being a `yyyyMMdd` string
> that `TRY_CAST(... AS TIMESTAMP)` turns to NULL — see Rule C), the object silently goes to **0 rows**
> while the pipeline reports success. A real build lost all 3,104 rows of `order_credit_check` this
> way and only caught it via post-run row-count inspection. Because SDP has **no post-load validation
> notebook**, this is a genuine hole. Two defenses, use at least one:
> - **Mandatory post-run row-count check (required exit gate).** After every SDP update, read each
>   object's row count from the event log's `flow_progress` `num_output_rows` (or `SELECT COUNT(*)`)
>   and treat **any object at 0 rows that is not a declared-empty entity** as a build failure — do not
>   call the build done until every non-empty entity has rows. This is the SDP equivalent of the MERGE
>   path's `validate_silver` row-count check.
> - **`ON VIOLATION FAIL UPDATE` on grain constraints for objects with known-nonempty sources.** If
>   the source definitely has data, a schema/format bug should fail the update **loudly** rather than
>   silently draining the table. This trades availability for correctness — appropriate for a
>   grain/PK constraint where 0 rows is always a bug, never intended.

### FK validation by `output_model` — and the `LIVE.*` trap

The `-1` Unknown-member pattern above is a **dimensional-mode** device (surrogate keys, conformed
dims) — it also applies to the **gold layer of `hybrid`**. **Normalized mode** (natural PKs, no
surrogates, no `-1` seed row), and the **silver layer of `hybrid`**, validate FKs differently:

- **Normalized (and `hybrid`-silver):** the inline constraint can only be a **soft
  `EXPECT (fk IS NOT NULL)`** — it tracks the null-FK rate in the event log, nothing more. **Real
  FK-orphan detection is deferred to the downstream `domain-model-validation` skill** (`LEFT ANTI
  JOIN child → parent`). Do NOT try to enforce referential integrity inline, and do NOT author a
  build-time validation step for it.
- **Dimensional (and `hybrid`-gold):** the fact resolves each FK to the parent dim's surrogate via
  `LEFT JOIN ... COALESCE(dim.Key, -1)` in the defining query (see the gold-star section below), so
  the FK is a real BIGINT that is never NULL — track health as the soft `-1`-rate EXPECT above.
- 🔴 **Never put a cross-table subquery in a `CONSTRAINT EXPECT`.** `EXPECT (customer_id IN (SELECT
  customer_id FROM LIVE.customer))` — or any `SELECT … FROM LIVE.<table>` inside a column-spec
  constraint — **fails** with `[TABLE_OR_VIEW_NOT_FOUND] LIVE.customer`. `LIVE.*` does not resolve
  in the constraint block. A real build hit this by improvising exactly that pattern. FK
  completeness is checked downstream, never as an inline subquery, in **either** mode.

## Hybrid mode: the downstream gold star layer (`output_model: hybrid`)

**This is the authoritative SDP recipe for `hybrid`.** In `hybrid`, the build produces TWO layers
**in sequence, in ONE pipeline** — normalized 3NF silver FIRST, THEN a dimensional Kimball gold
star built **downstream from that silver** (not from bronze, not both-at-once):

- **Silver layer** — build exactly as `normalized`: product-named MVs / ST-APPEND, natural PKs, no
  surrogates, hardcoded bronze paths. Lands in the **silver** schema. Nothing new here.
- **Gold layer** — one declarative object per star table, reading **the silver tables** (`LIVE`
  references to the silver objects in the same pipeline), adding the SHA2 `{Entity}_Key` surrogate,
  `dim_/fact_` naming, and Pascal_Snake business columns. Lands in the **gold** schema.

> **Gold discovery step — read the silver sources before authoring gold.** The gold requirements
> handoff is a **design** spec (grain, FK targets, source tables, column lists), not a **build** spec
> — it does not give you the exact silver column names, the SHA2 surrogate composition, or the join
> keys between silver tables. Before writing any gold source, **read every silver pipeline file the
> requirements reference** (the `.sql` under `src/silver/pipeline/`) to capture: exact physical column
> names + types, which column is each dim's natural key (to hash on), and the FK columns that join a
> fact to its dims. Budget a handful of reads up front; it is far cheaper than guessing a column name
> and failing the update. The silver sources are the implementation contract; the requirements doc is
> the intent. *(An upstream `domain-model-assessment` gold pass may supply a machine-readable gold S2T
> that pre-answers most of this — if present, use it and skip the manual reads.)*

**Same pipeline, two schemas.** A single LDP pipeline has ONE default `schema:`. Put the silver
sources under `src/silver/pipeline/` (unqualified names → default schema = silver) and the gold
sources under `src/gold/pipeline/` with **fully schema-qualified object names**
(`catalog.gold_schema.dim_customer`) so they land in the gold schema regardless of the pipeline
default. **Hardcode the gold `catalog.schema` literal** in each gold source, exactly as bronze paths
are hardcoded — do NOT use `${var}`/`:param` substitution (SDP avoids parameterization, and DAB does
not reliably substitute into plain `.sql` pipeline sources). Reference silver objects from gold by
their **fully-qualified `catalog.schema.object`** name, NOT bare `LIVE.<name>` (which resolves only
against the pipeline default schema — see the fact template note). Both folders are globbed into the
one `pipeline` resource (see the DAB block below), so the silver→gold dependency graph resolves in
one update: a gold MV that selects from the silver `customer` object orders automatically after it.

**Gold dimension (MV over the silver product):**

```sql
-- src/gold/pipeline/dim_customer.sql   (plain .sql, NO notebook-source header)
-- gold catalog.schema is a HARDCODED literal (no ${var}/:param) — from conventions gold_pattern
CREATE OR REFRESH MATERIALIZED VIEW meridian_silver.field_service_gold_sdp.dim_customer (
  Customer_Key   BIGINT  COMMENT 'Surrogate key (SHA2 of natural key)',
  Customer_Bk    STRING  COMMENT 'Natural/business key (silver customer_id)',
  Customer_Name  STRING,
  _source_system STRING,
  CONSTRAINT valid_bk EXPECT (Customer_Bk IS NOT NULL) ON VIOLATION DROP ROW  -- grain on NK, not surrogate
)
CLUSTER BY (Customer_Key)
COMMENT 'Conformed customer dimension (gold star, built from silver SSOT)'
AS
SELECT
  CAST(CONV(SUBSTR(SHA2(CONCAT_WS('|',COALESCE(CAST(customer_id AS STRING),'∅')),256),1,15),16,10) AS BIGINT) AS Customer_Key,
  customer_id    AS Customer_Bk,
  customer_name  AS Customer_Name,
  _source_system
FROM meridian_silver.field_service_silver_sdp.customer   -- SILVER object, fully-qualified (see refs note)
UNION ALL
-- -1 Unknown member: an MV is fully recomputed (no INSERT), so the seed MUST be a UNION ALL row
-- in the defining query — this is what the fact's COALESCE(...,-1) points at.
SELECT CAST(-1 AS BIGINT), '__UNKNOWN__', 'Unknown', '__UNKNOWN__';
```

**Gold fact (MV over the silver fact, FK-resolved against the gold dims):**

```sql
-- src/gold/pipeline/fact_service_order.sql   (gold catalog.schema hardcoded, no ${var}/:param)
CREATE OR REFRESH MATERIALIZED VIEW meridian_silver.field_service_gold_sdp.fact_service_order (
  Service_Order_Key BIGINT,
  Service_Order_Bk  STRING,   -- degenerate NK, retained so the grain EXPECT has a real column
  Customer_Key      BIGINT,
  Asset_Key         BIGINT,
  _source_system    STRING,
  CONSTRAINT valid_grain EXPECT (Service_Order_Bk IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_customer_resolved EXPECT (Customer_Key != -1),   -- soft: track orphan-to-Unknown rate
  CONSTRAINT fk_asset_resolved    EXPECT (Asset_Key != -1)
)
CLUSTER BY (Customer_Key)
AS SELECT
  CAST(CONV(SUBSTR(SHA2(CONCAT_WS('|',COALESCE(CAST(s.service_order_id AS STRING),'∅')),256),1,15),16,10) AS BIGINT) AS Service_Order_Key,
  s.service_order_id AS Service_Order_Bk,
  COALESCE(c.Customer_Key,-1) AS Customer_Key,   -- Rule 11: LEFT JOIN the gold dim, COALESCE miss to -1
  COALESCE(a.Asset_Key,-1)    AS Asset_Key,
  s._source_system
FROM meridian_silver.field_service_silver_sdp.service_order s   -- SILVER fact (fully-qualified)
LEFT JOIN meridian_silver.field_service_gold_sdp.dim_customer        c ON c.Customer_Bk = s.customer_id
LEFT JOIN meridian_silver.field_service_gold_sdp.dim_installed_asset a ON a.Asset_Bk   = s.asset_id;
```

> 🔴 **Cross-schema references must be fully qualified — do NOT use bare `LIVE.<name>`.** In a
> multi-schema pipeline the `LIVE.*` virtual schema resolves against the pipeline's **default**
> (silver) schema, so `LIVE.dim_customer` would fail to find a dim that actually lives in the gold
> schema (and `LIVE.*` is being deprecated in favor of direct references). Reference every silver and
> gold object by its full `catalog.schema.object` name.
>
> ⚠️ **EXIT GATE — verify DAG ordering on the first hybrid run (do not assume it).** The two-layer
> flow depends on SDP registering an **intra-pipeline dependency** from a gold MV's fully-qualified
> `FROM catalog.silver_schema.<object>` reference, so silver materializes before its gold consumer.
> This is expected on current LDP but is **NOT runtime-verified here.** On the first hybrid run you
> MUST confirm, from the pipeline graph / event log, that each gold object shows an upstream edge to
> its silver source (not an external-table read). **If ordering does NOT register** (gold fails
> "silver not found" on first update, or reads empty/stale silver), the fix is a documented fallback,
> not a silent failure: wrap the silver reference so SDP recognizes it as a pipeline dependency
> (`FROM STREAM catalog.silver_schema.<object>` for a streaming read, or the runtime's dependency-
> declaring form) while keeping it schema-qualified — then re-run and re-check the graph. Treat
> "DAG edges confirmed silver→gold" as a required checkpoint before the hybrid build is called done.

**Rules for the gold layer:**
- 🔴 **Gold reads SILVER, never bronze.** A gold object that re-reads `catalog.bronze_schema.*`
  instead of the fully-qualified `catalog.silver_schema.<object>` defeats the SSOT — flag it.
- **FK resolution is Rule 11:** `LEFT JOIN` the already-defined gold dim on the natural key and
  `COALESCE(dim.Key, -1)`. Never inline-recompute a parent's surrogate from the fact source.
- **Guard the grain on the natural/degenerate key**, never the SHA2 surrogate (it can't be NULL).
- **`scd_strategy: type_2`** is a gold-only concept — the SCD2 `AUTO CDC` template applies to the
  gold dim, and needs CDF on the **silver** source. (Out of scope for the `type_1` field_service
  fixture.)
- **Seed the `-1` Unknown member** in each gold dim exactly as the dimensional MERGE path does, so
  the fact's `COALESCE(...,-1)` points at a real row.
- **FK-resolution joins must be 1:1 on the dim side** (see the fan-out rule in the FK-resolution note
  above). Bridge tables are the sharp edge: a `bridge_*` at **header** grain LEFT JOINed to a fact at
  **line** grain fans out — join on the header key (e.g. `order_id`), never the line key, or the fact
  row count multiplies. Confirm grain with a PK-count check on the first run.
- **`dim_date` / calendar dims:** use the serverless-safe date functions from Rule B (`WEEKDAY()+1`
  for ISO weekday, not `DAYOFWEEK_ISO`). CAST computed date-part columns to their declared types
  (Rule A). These are the two things that most often fail a gold `dim_date` on the first run.
- **Pipeline resource naming.** When gold is added to a silver pipeline in `hybrid`, the one pipeline
  now contains both layers. Naming it `{domain}_silver_pipeline` is then misleading — prefer
  `{domain}_sdp_pipeline` (drop the `silver_` qualifier). Keeping the original name is functionally
  harmless, but rename it when you add gold so the resource reflects its contents.

## Testing — NONE in the SDP build (deferred until the LDP framework leaves beta)

> 🔴 **The SDP build has no test/validation gate — this is intentional.** Do NOT author the LDP
> unit-test framework (`pyspark.pipelines.testing` / `TestPipeline` / `test_spark`), a post-load
> validation notebook, or any build-time TDD gate. The LDP testing framework is **beta and
> Editor-only** — verified against the Databricks docs (2026-08-08): *"Tests must be run from the
> web-based Lakeflow Pipelines Editor,"* and `TestPipeline.active()` only resolves inside the
> Editor, so there is **no bundle/CLI path** to run it as an autonomous gate. A real build proved
> this — 15 `TestPipeline` tests were authored, deployed, and **never ran**.

**What provides confidence instead, without any build-time test artifact:**
- **Inline `EXPECT` constraints** enforce/track DQ *while the pipeline runs* (grain/PK, regex/enum,
  soft FK NOT-NULL) — see the Data-quality section above.
- **The pipeline event log** records per-expectation pass/fail counts on every update (see the
  Event-log section below) — inspect it after a run to confirm DQ held.
- **The downstream `domain-model-validation` skill** does the real data-state proof (0 FK orphans,
  0 dropped rows, scorecard) *after* the build — that is where validation lives for SDP, not in the
  build.

Do not set `channel: PREVIEW` *because of* testing (PREVIEW/triggered remains a fine dev default,
just not for that reason). Revisit build-time testing only when the LDP testing framework leaves
beta and gains a headless run path.

## Pipeline DAB resource — the FILE model (plain `.sql`, glob, `root_path`)

> 🔴 **Use the FILE model, not the notebook model (VERIFIED best practice, 2026-08-08).** SDP
> pipeline sources are **plain `.sql` files with NO `-- Databricks notebook source` header**,
> included via a single **`glob:`** entry, with **`root_path:`** set to the source tree. Do NOT
> give SDP sources the notebook-source header, do NOT create notebook objects for them, and do NOT
> list them as per-entity `notebook:` libraries. A real build hit a three-way deadlock doing
> exactly that: `.sql` files carried the notebook header → became notebook-type objects →
> referenced as `notebook:` (which strips the `.sql` extension) → DLT looked for a bare `customer`
> object that either didn't exist or was created Python-language → `NO_TABLES_IN_PIPELINE`. The
> Databricks docs call plain `.py`/`.sql` + `libraries.glob` the module-style best practice for
> pipelines; `glob` cannot be combined with `notebook:`/`file:` in the same entry.

Emit ONE `pipeline` resource (not a `job`):

```yaml
resources:
  pipelines:
    {domain}_silver_pipeline:
      name: {domain}_silver_pipeline
      channel: PREVIEW          # sane dev default (NOT for unit testing — see above)
      continuous: false         # triggered
      catalog: ${var.silver_catalog}       # the pipeline's DEFAULT write target
      schema: ${var.silver_schema}         # silver objects (unqualified names) land here
      root_path: ../src                    # anchors BOTH src/silver/pipeline and src/gold/pipeline
      # bronze paths hardcoded in each source; NO `parameters:` block.
      # In HYBRID, gold objects are SCHEMA-QUALIFIED with a HARDCODED catalog.gold_schema literal
      # (catalog.field_service_gold_sdp.dim_x) — same hardcode stance as bronze paths, no ${var}.
      libraries:
        # glob include paths resolve relative to THIS bundle YAML's directory (resources/),
        # NOT to root_path — keep the ../src prefix (same form the MERGE flows use).
        - glob:
            include: ../src/silver/pipeline/**    # normalized silver sources (unqualified -> default schema)
        # --- HYBRID ONLY: also include the downstream gold star sources ---
        - glob:
            include: ../src/gold/pipeline/**      # dim_/fact_ MVs, object names hardcoded to the gold schema
      notifications:
        - email_recipients: ["${var.alert_email}"]
          alerts: ["on-update-failure"]
      serverless: true          # required where the workspace enforces serverless compute
```

**Layer → folder → schema:**
- `normalized` / `dimensional` (single layer): only `src/silver/pipeline/` exists; drop the gold
  glob and keep `root_path: ../src/silver/pipeline`.
- `hybrid` (two layers): `src/silver/pipeline/` (silver, unqualified → default silver schema) **and**
  `src/gold/pipeline/` (gold, object names hardcoded-qualified `catalog.gold_schema.dim_x`). Both are
  globbed into the ONE pipeline; `root_path: ../src` so it spans both. The silver→gold graph
  resolves in one update (gold's fully-qualified references to the silver objects order silver first).

No `ddl/`, `transformations/`, `runners/`, or `tests/` subfolders in this mode — there is no
separate DDL step and no build-time test/validation artifact. Each layer's sources are plain `.sql`
files (no notebook-source header), one per entity.

**Deployment mode:**
- **Dev target:** `source_linked_deployment: true` — the pipeline references the source files
  in-place (its root folder = your repo tree), which is the git-friendly edit-in-place dev loop.
  Because the sources are plain `.sql` files (no header) included by `glob`, there is no
  extension-stripping collision.
- **Prod target:** `source_linked_deployment: false` (or immutable snapshots) — files are copied
  into the deploy path so the running pipeline is pinned and doesn't depend on a live repo.
- **Environment routing** (same as the MERGE path): serverless → author + `bundle validate` + hand
  off to the Deployments panel; web terminal / local / CI → `databricks bundle deploy` then trigger
  the pipeline update. A full refresh is required when an entity changes object type (e.g. MV→ST),
  and that (and `DROP TABLE`) may be blocked by tool safety policy on serverless — hand off to the
  UI's Start ▸ Full refresh rather than spiraling on CLI/SDK workarounds.

> **Tooling note — prefer programmatic file writes for SDP source edits.** On real builds the
> patch/edit-by-match tool (`editAsset`) failed repeatedly on these `.sql` sources: it could not match
> whitespace-sensitive `old_text`, choked on the UTF-8 multi-byte characters these templates use (the
> `∅` null sentinel, `—` em-dashes, `·`), and was intermittently blocked by safety policy for writing
> `CREATE ... ON VIOLATION` content (misread as a destructive op). For surgical multi-file fixes —
> especially applying the same type/CAST fix across many entity files at once — a full-file rewrite via
> plain file I/O (`open()/write()` in `executeCode`) is more reliable than exact-match patching. Also
> note `bundle run` intermittently returned "Command with guid not found"; starting the update via the
> SDK (`w.pipelines.start_update()`) was the reliable fallback. When editing a source from the
> **pipeline editor** page, `editAsset` needs the file registered first: read it with explicit
> `startLine`/`endLine` (e.g. `1`–`3`) then edit by numeric ID — a read without line params
> sometimes fails to register the file for editing.

## Event-log DQ reads (inspect after a run — not a build gate)

After a pipeline update, EXPECT pass-rates are readable from the pipeline event log — this is how
you confirm inline DQ held, and it's the input the downstream `domain-model-validation` skill uses.
It is **not** a build-time gate (the SDP build has none — see Testing). Query the `event_log` for
the pipeline (via the `event_log()` TVF or the pipeline's event-log table) and extract
`flow_progress` events' `data_quality.expectations` (passed/failed record counts) per expectation,
comparing against spec §6 thresholds. (Exact TVF/table binding — confirm against the installed
runtime.)
