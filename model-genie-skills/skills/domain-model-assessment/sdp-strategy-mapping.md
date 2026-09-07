# SDP Strategy Mapping & Conventions Schema

Two references the assessment needs when `etl_type: sdp_pipeline`, learned from the Meridian
sales-order SDP hybrid run:

1. **SDP object-type mapping** — the Step 2.6 load-strategy labels don't map 1:1 to SDP objects;
   this fills the gap.
2. **`conventions.yml` schema** — the keys the skill reads throughout, defined once.

---

## Part 1 — Load strategy → SDP object type

The Mode-A load-strategy framework (`source-to-target-mapping.md`) emits `APPEND_ONLY` /
`FULL_MERGE` / `INCREMENTAL_MERGE` / `SDP`. Those name a *MERGE-notebook* mechanism. When the whole
build is a Lakeflow Declarative Pipeline, translate them to SDP object types:

| Load strategy (Step 2.6) | SDP object type | Notebook idiom |
| --- | --- | --- |
| `APPEND_ONLY` (immutable ledger + watermark) | **Streaming Table** | `CREATE STREAMING TABLE … AS SELECT … FROM STREAM(...)` |
| `FULL_MERGE` (mutable, small) | **Materialized View** | `CREATE MATERIALIZED VIEW …` (AUTO refresh — see MV note below) |
| `INCREMENTAL_MERGE` (mutable, keyed CDC — inserts/updates/deletes) | **Streaming Table with AUTO CDC** | `CREATE FLOW … AS AUTO CDC INTO … FROM STREAM(...) KEYS(...) SEQUENCE BY … [STORED AS SCD TYPE 1\|2]` |
| `INCREMENTAL_MERGE` (large fact, **windowed / late-arriving** batch refresh — no per-row CDC feed) | **Streaming Table with incremental `REPLACE WHERE` flow** | Declare the target streaming table, then a **separate flow** — `CREATE FLOW … AS INSERT INTO {table} BY NAME REPLACE WHERE {predicate} SELECT …` (two statements; the `REPLACE WHERE` sits between `BY NAME` and `SELECT` — see the worked example below) |
| `SDP` (mutable, no watermark, needs CDC / SCD2) | **Streaming Table with AUTO CDC** | as `INCREMENTAL_MERGE` CDC row above |

> **`APPLY CHANGES INTO` is now `AUTO CDC INTO`** — same primitive, current name (verified against
> internal Lakeflow guidance, Aug 2026). Use `AUTO CDC INTO` in new specs; treat `APPLY CHANGES` as
> the legacy alias. It handles inserts/updates/deletes, out-of-order events, partial updates
> (`IGNORE NULL UPDATES` / `COLUMNS TO UPDATE`), and SCD Type 1/2 declaratively. **`AUTO CDC` is a
> Lakeflow-Pipelines feature — not available in plain Apache Spark Declarative Pipelines.**

State the SDP object type in each entity's **Load strategy** line for SDP builds — do not leave the
MERGE-era label to be re-interpreted at build time.

### The large mutable fact — the case that broke the old "just use an MV" answer

**This is the exact question the Meridian test's tiny data hid.** A *large* fact that receives
**updates** (mutable, high volume) has no good MV answer — full recompute is too expensive — and a
plain append-only Streaming Table can't apply the updates. There are **two correct primitives**,
picked by *how the changes arrive*:

1. **A real per-row CDC feed exists** (source emits keyed insert/update/delete with a sequence) →
   **`AUTO CDC INTO` a Streaming Table.** This is the standard Lakeflow pattern for a large mutable
   fact/dim: applies changes incrementally, handles deletes + out-of-order + SCD1/2. Needs `KEYS`
   (business key) + `SEQUENCE BY` (sortable event order; add a tie-breaker when timestamps collide).
2. **No per-row CDC feed — changes are "reprocess a recent window"** (late-arriving data, upstream
   restatements, a dimension change that only touches recent facts, or building a long-retention
   table from a short-retention source) → **incremental `REPLACE WHERE` flow.** You declare a
   standing predicate (e.g. `order_date >= date_add(current_date(), -7)`); each run deletes +
   re-derives only that window and leaves history untouched. On serverless, Enzyme rewrites only the
   changed files (internal benchmark: ~3.4× faster / ~2.5× cheaper than a full rewrite). This is the
   right tool for a **large batch fact with corrections but no CDC stream** — precisely where a
   full-recompute MV is wasteful and AUTO CDC doesn't fit.

`REPLACE WHERE` requirements & sharp edges (verified against `docs.databricks.com/aws/en/ldp/flows-replace-where`):
- **UC + serverless** (Enzyme incremental is serverless-only; classic falls back to full window
  recompute) and the **PREVIEW** channel; the target table must be **created in the pipeline**.
- **One `REPLACE WHERE` flow per target**, and that target can't also be an AUTO CDC / append target.
- **Predicate must be deterministic + on base columns** (`current_date()` OK; `rand()` forbidden);
  for aggregations/joins put the predicate column in the `GROUP BY` / join key to keep the fast path.
- **`BY NAME` is required in SQL.** **Expectations are NOT supported** on a `REPLACE WHERE` target —
  put DQ on the upstream table.
- **FULL REFRESH is destructive** — it re-runs with only the standing predicate, so a year-old table
  with a 7-day predicate collapses to 7 days. Set `pipelines.reset.allowed = false` to guard it.

**Statement shape (two statements — target ST, then a separate flow):**

```sql
CREATE STREAMING TABLE orders_enriched;

CREATE FLOW orders_enriched AS
INSERT INTO orders_enriched BY NAME
REPLACE WHERE order_date >= date_add(current_date(), -7)   -- standing window predicate
SELECT
  o.order_id, o.order_date, o.region,
  p.product_name, o.qty, o.price
FROM orders_fct o
JOIN product_dim p ON o.product_id = p.product_id;
```

Note the clause order: `INSERT INTO {target} BY NAME` → `REPLACE WHERE {predicate}` → `SELECT …`.
`REPLACE WHERE` is **not** an inline clause on `CREATE STREAMING TABLE` — the target is declared
empty, and the flow carries the predicate + query.

### Materialized views are NOT "always full recompute" (correcting the earlier assumption)

An MV on **serverless** Lakeflow **incrementally refreshes** (Enzyme) when its query is
incrementalizable — it processes only upstream changes, not the whole result. It performs a full
recompute only when (a) compute is **classic**, or (b) the query isn't incrementalizable, or (c) the
cost model finds full cheaper. So an MV is a fine gold choice for aggregations/joins/dashboard
summaries *at scale*, provided you keep the query incrementalizable. Things that force a full
recompute (design around them): `COUNT(DISTINCT)`, `GROUP BY ... DISTINCT`, window functions without
`PARTITION BY` or below top level, non-deterministic UDFs / `RANDOM()`, non-top-level aggregation,
`SUM/AVG` over raw `FLOAT/DOUBLE` (cast to `DECIMAL`), source tables with **row filters / column
masks** (always full), and **expectations inside the MV** (documented as full-refresh every run).
When a full recompute is unacceptable, set **`REFRESH POLICY INCREMENTAL`** (falls back to full if
incrementalization drops out) or **`INCREMENTAL STRICT`** (fails instead of full-recomputing).
Enable `delta.enableRowTracking` + `delta.enableDeletionVectors` (+ `enableChangeDataFeed`) on source
Delta tables to keep incremental eligible. Confirm actual behavior via `EXPLAIN CREATE MATERIALIZED
VIEW` + the `planning_information` event (look for `FULL_RECOMPUTE` and cost-model rejection reasons
like `CHANGESET_SIZE_THRESHOLD_EXCEEDED`).

### Streaming Table vs Materialized View vs REPLACE WHERE — decision tree

```
1. Immutable append-only ledger (pct_mutated ≈ 0), streamable source, no cross-batch dedup/JOIN?
   YES → Streaming Table (STREAM())                       ← plain append
   NO  → continue.

2. Mutable, and a real per-row CDC feed exists (keyed change rows + a sequence)?
   YES → Streaming Table with AUTO CDC INTO (SCD 1 or 2)  ← the CDC path
   NO  → continue.

3. Mutable/large, changes are a reprocessable WINDOW (late data, restatements, recent-only
   dimension change, long-retention-from-short-source) — no per-row CDC feed?
   YES → Streaming Table with incremental REPLACE WHERE flow   ← the large-batch-fact answer
   NO  → continue.

4. Otherwise (small, or full-history-recompute measures, aggregations/joins for a mart):
   → Materialized View (serverless, incrementalizable; set REFRESH POLICY INCREMENTAL[ STRICT]
     if a surprise full recompute is unacceptable)
```

Two calls the sales-order run had to make by hand (still true):
- A multi-source JOIN entity (e.g. `service_order` joining 3 sources) that's append-only can be an
  **MV** — the JOIN isn't a pure append stream. (At high volume with windowed corrections, prefer a
  `REPLACE WHERE` flow over a full-recompute MV.)
- A name-slug derived key (e.g. `LOWER(REGEXP_REPLACE(TRIM(technician),…))`) must be **byte-identical**
  in the dim and any fact that references it, or the FK silently misses. Record the exact expression
  once in the spec and reuse it.

### Gold tier — simpler than silver, but facts still get a load-strategy decision

Do **not** blanket everything at gold to MV. Two rules:

**Dimensions & bridges — keyed on `scd_strategy`:**
- **`type_1` (default):** Materialized View, full recompute — dims are small, rebuild is cheap.
- **`type_2` dimension:** Streaming Table with `AUTO CDC … STORED AS SCD TYPE 2` — a full-recompute
  MV would destroy the version history the dim exists to keep.

**Facts — keyed on volume + mutability, the SAME decision as a silver fact (Part 1 above):**
- **Append-only, high-volume** (a gold ledger/line fact reading a large append-only silver ST) →
  **Streaming Table** (incremental append). Full-recompute MV over a large fact every run is the
  anti-pattern the silver framework forbids; it applies at gold too.
- **Small, OR measures need a full-history recompute / restatement** → Materialized View.

Gold *does* skip the bronze append-only *discovery* (source is typed silver, dependencies resolve
from SQL references), but the sizing question — MV vs Streaming Table per fact — is not skipped.
A small domain where every fact is < ~a few M rows lands on MV for all facts; that's the low-volume
answer, not a rule. State the row tier + object type per gold fact. (See `gold-derivation-protocol.md`
Step G6.)

### Pipeline configuration the assessment should record

| Setting | Guidance |
| --- | --- |
| `mode` | `TRIGGERED` for batch domains (default); `CONTINUOUS` only for genuine low-latency needs |
| `channel` | `PREVIEW` while iterating on new SDP features; `CURRENT` for stable production |
| `serverless` | `true` (default for these builds) |
| FK EXPECTs | **soft** (bare `CONSTRAINT … EXPECT`, no `ON VIOLATION`) in `normalized`/silver — no `-1` sentinels; `DROP ROW` only where a NULL FK truly invalidates the row |
| schedule | gold pipeline (if separate) runs *after* silver completes — state the offset |

---

## Part 2 — `conventions.yml` schema (the keys the skill reads)

The skill references these keys across all phases. Defined here so a new knob combination
(`etl_type: sdp_pipeline`, `output_model: hybrid`) doesn't force guessing. Authoritative source is
`templates/conventions.yml` + `templates/conventions-variants/` in the repo root.

| Key | Type | Default | Consumed by | Notes |
| --- | --- | --- | --- | --- |
| `output_model` | enum | `dimensional` | Phase 4, 6; Mode Gate | `normalized` \| `dimensional` \| `hybrid` |
| `etl_type` | enum | `merge_notebook` | Phase 4, 6 | `merge_notebook` \| `sdp_pipeline` |
| `etl_language` | enum | `sql` | Phase 6 handoff | `sql` \| `python`; DDL+docs always SQL |
| `scd_strategy` | enum | `type_1` | Phase 4 key derivation, 6 | `type_1` \| `type_2` (adds `_effective_from` to hash) |
| `vibe_model.catalog` | string | — | Phase 1 (READ) | where the metamodel + model live |
| `vibe_model.schema` | string | — | Phase 1 (READ) | model schema |
| `vibe_model.metamodel_schema` | string | unset → probe, else `schema` | Phase 1 Step 1.0 | when unset, Step 1.0 probes `information_schema`; co-located fallback is `vibe_model.schema` |
| `vibe_model.metamodel_prefix` | string | `vibe_metamodel_` | Phase 1 Step 1.0 | `''` when bare-named |
| `bronze_sources` | list | — | Phase 2 | schemas/systems to profile |
| `catalogs.silver` | string | — | Phase 4, 6 (WRITE target) | where silver lands |
| `catalogs.gold` / `schemas.gold_pattern` | string | — | gold Mode | where the gold star lands |
| `naming.*` | block | — | Phase 4 crosswalk, 6 | `dim_prefix`/`fact_prefix`/`bridge_prefix`/`gold_prefix`, `table_case`, `entity_form` |
| `thresholds.*` | block | — | Phase 4 grading, DQ | Full/Partial cutoffs, DQ pass rates |

> **READ vs WRITE split (keep it clear):** `vibe_model.*` is **READ** (the frozen model +
> metamodel). `catalogs.*` / `schemas.*` are **WRITE targets** (where the build lands). The
> assessment reads the former and *names* the latter — it writes to neither (data is read-only;
> only markdown + the one metamodel gate-edit).
