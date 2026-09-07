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
> templates in `sdp-templates.md` are written in the `dimensional`/`hybrid-gold` shape (`dim_/fact_` + SHA2 `_Key`)
> for illustration; in the default `normalized` (and the **silver layer of `hybrid`**) they instead follow the vibe model —
> product-named tables, natural PKs, no surrogates (per the "⚠️ Precedence & key strategy by mode"
> note in `naming-standards.md`). For **`hybrid`** — normalized 3NF silver first, THEN a
> dimensional gold star built downstream from that silver (**not** both at once) — see
> **`sdp-gold-star.md`**; it is the authoritative SDP recipe for the gold layer.


## Sub-files (the `sdp_pipeline` pack)

Bulky sections live in focused sub-files — load the one you need:

| File | Content |
| --- | --- |
| `sdp-templates.md` | SQL + Python + normalized-mode source templates; FK-resolution trees; multi-source UNION ALL; deferred entities |
| `sdp-gold-star.md` | `output_model: hybrid` — the downstream dimensional gold star built from normalized silver |
| `sdp-deployment.md` | The `pipeline` DAB resource — FILE/glob model, `root_path`, source-linked dev |

This file keeps the "how to think" core: when-to-use, key/FK-by-mode, load-strategy→object mapping,
parameterization rule, inline-schema discipline (Rules A–D), the incremental build loop, inline
`EXPECT` DQ, and event-log reads.

## Key & FK-sentinel by mode (read this first)

The PK type and FK-miss sentinel are set by `output_model` — NOT by `etl_type`. Read the
exact hash expression from `conventions.yml` `surrogate_key_formula`, selecting the variant
by the vibe model's DECLARED PK type.

| output_model  | PK type            | PK formula source          | FK-miss sentinel      | Unknown seed row? |
|---------------|--------------------|----------------------------|-----------------------|-------------------|
| normalized    | per vibe model     | surrogate_key_formula      | NULL (`CAST(NULL AS <type>)`) | No        |
| dimensional   | BIGINT `{Entity}_Key` | surrogate_key_formula.bigint | COALESCE(dim.Key, -1) | Yes (UNION ALL in each dim MV) |
| hybrid-silver | per vibe model     | surrogate_key_formula      | NULL (as normalized)  | No                |
| hybrid-gold   | BIGINT `{Entity}_Key` | surrogate_key_formula.bigint | COALESCE(dim.Key, -1) | Yes               |

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

> 🔴 **PRE-FLIGHT — run this checklist mentally before emitting ANY SQL.** The rules below are
> real but easy to lose in the wall of text; the `TRY(...)` anti-pattern (Rule B) recurred **3
> times in a single build** despite already being documented. Gate every source on this list first:
>
> ```
> □ Explicit inline schema present, with a vibe-model COMMENT on every column (Rule D)
> □ No TRY(TO_DATE(...)) / TRY(CAST(...)) — use TRY_TO_DATE / TRY_CAST (Rule B)
> □ No DAYOFWEEK_ISO() — use WEEKDAY() + 1 (Rule B)
> □ No CONSTRAINT PRIMARY KEY / FOREIGN KEY in an MV/ST inline schema — grain via EXPECT
> □ No LIVE.* references inside a CONSTRAINT EXPECT clause
> □ Every DECIMAL / arithmetic expression wrapped in an explicit CAST to its declared type (Rule A)
> □ Every date/timestamp source column probed for physical format (Rule C)
> □ Reserved-keyword table names (order, group, table, …) backtick-escaped (see build loop)
> □ Grain guarded by an inline EXPECT on the natural key, NOT a WHERE filter (normalized templates)
> ```

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
silently empties the whole table (see the Data-quality section's silent-0-row gate). `conventions.yml`
`date_formats:` pre-populates the **expected** format per source (SAP → `yyyyMMdd`, most others →
`yyyy-MM-dd`) — start from it, but still run the probe below as the verification gate. Before authoring
any entity, probe each date/timestamp source column:

```sql
SELECT col, TRY_CAST(col AS TIMESTAMP) AS as_ts, TRY_TO_DATE(col, 'yyyyMMdd') AS as_yyyymmdd
FROM {bronze_source} WHERE col IS NOT NULL LIMIT 5;
```

If `as_ts` is NULL but `as_yyyymmdd` resolves, the column is a `yyyyMMdd` string — parse it with
`CAST(TRY_TO_DATE(col,'yyyyMMdd') AS TIMESTAMP)`, not `TRY_CAST(... AS TIMESTAMP)`. This one check
prevents the most damaging SDP failure mode (a green pipeline that produced an empty table).

### Rule D — ALWAYS use the explicit inline schema with column COMMENTs from the vibe model

> 🔴 **Rule D — the SDP source file IS the DDL; author it with the full inline column list and the
> vibe model's column COMMENTs, never the inference-only form.** A `CREATE OR REFRESH MATERIALIZED
> VIEW x AS SELECT ...` with no `(col type COMMENT '...', ...)` column block **compiles and runs**,
> so nothing fails — but it ships a table with **zero column metadata**, discarding the rich,
> per-column descriptions the vibe model carries (e.g. `sales_area.area_status`: *"Current
> operational status of the sales area. active indicates the area is open for order processing;
> blocked prevents new orders…"*). A file without column comments is **incomplete even though it
> passes** — treat it as a build defect, the same as a broken one.
>
> **This overrides the system-level "schema inference first" guidance, which applies to TYPES only.**
> Use inferred types to avoid the declared-vs-inferred mismatch Rule A warns about (probe
> `df.schema` from the `AS SELECT` and declare exactly those types) — but the **explicit column list
> with COMMENTs is always required**. Inference-first governs *what type to declare*, never *whether
> to declare the column block at all*.
>
> **Pattern:** before authoring an entity, read its column comments from the vibe model
> (`readTable` / `information_schema.columns` on `{vibe_model_catalog}.{vibe_model_schema}.{entity}`
> — the same introspection `ddl-and-modeling.md` "Mandatory Model Introspection" mandates for the
> merge path), then author the inline schema with **types inferred from the SELECT + COMMENTs copied
> verbatim from the model** (do not abbreviate — keep examples, cross-system notes, and business
> justification). Every MV/ST template in `sdp-templates.md` shows this explicit form; it is the only accepted shape.

### Incremental build loop (entity-first, tier-gated update; do NOT write-all-then-test)

> 🔴 **The write-all-then-test anti-pattern is the costliest SDP build mistake.** Authoring all N
> sources and triggering a single pipeline update surfaced **14 errors at once** in the sales-order
> run (~45 min of tangled diagnosis) and hid the PRIMARY-KEY syntax error behind 16 other files.
> The tier ordering the assessment already gives you IS the validation progression — use it.

Authoring is SEQUENTIAL per entity; the pipeline UPDATE is triggered per TIER (SDP resolves
dependencies per-update). Do NOT author all sources then trigger one update (write-all-then-test —
it surfaced 14 errors at once on a real build).

**First, navigate to the SDP pipeline editor.** After the pipeline resource is created + deployed,
open the pipeline editor page (Genie Code `openAsset` with `assetType="pipeline-editor"`) and
author/fix sources from there — it has SDP-aware tooling (correct MV/constraint syntax, per-flow
dry-run, pipeline-scoped file editing, plan-time diagnostics) that the general file editor lacks.

**The loop (mandatory for any multi-entity SDP build):**

For each tier (T0 = root dims/masters first):
  For each entity in the tier — **author ONE entity** at a time, never the whole tier at once:
    1. **Author the entity's `AS SELECT` body** (inline schema + EXPECT + query / AUTO CDC).
       - **Backtick-escape reserved-keyword table names first.** If an entity name is a SQL reserved
         keyword (`order`, `table`, `index`, `group`, `select`, `from`, `where`, `column`, `check`,
         `key`, `primary`, `foreign`, `constraint`, `grant`, `user`, `role`, `function`,
         `procedure`, `view`, `schema`, `catalog`, `database`), it MUST be backtick-escaped in the
         `CREATE OR REFRESH … \`order\`` statement **and every downstream reference**
         (`FROM \`order\``). Missing this fails the dry run. Flag such names in the build manifest so
         downstream references stay escaped.
    2. **WRITE the `.sql` file** to `src/silver/pipeline/{entity}.sql` immediately — before the
       dry-run. Worst case on a session drop is "file exists, unvalidated", which is recoverable.
    3. **Dry-run the `AS SELECT` body** (recipe below); fix it in-place if it fails (the file already
       exists from step 2, so you edit — you do not re-author).
    4. Next entity.
  5. **Trigger the pipeline update for the tier** (from the pipeline editor — better SDP tooling).
  6. **POST-UPDATE ROW-COUNT GATE** (required exit gate — see the Data-quality section's gate
     definition below): every entity in the tier has rows > 0, or is a declared-DEFERRED/empty
     entity. Any unexpected 0-row object is a BUILD FAILURE — do not proceed.
  7. **Flip each entity's `etl_state.md` row to AUTHORED** (row-count verified) and update
     `progress.md` (per-entity commit contract, SKILL.md Critical Rule 28).
  8. Next tier.

**Dry-run recipe (build-loop step 3).** Validate a source WITHOUT a full pipeline update:

- Preferred — EXPLAIN the whole DDL (validates, does not execute):
  ```sql
  EXPLAIN CREATE OR REFRESH MATERIALIZED VIEW {entity} (...) AS SELECT ... ;
  ```
  A parse / `UNRESOLVED_COLUMN` / PK-constraint error surfaces here.
- Or — run just the `AS SELECT` body and diff its schema against the declared columns:
  ```python
  sql  = open('src/silver/pipeline/{entity}.sql').read()
  body = sql.split(' AS\n', 1)[1].rstrip(';')     # extract the SELECT body
  df   = spark.sql(body)
  for f in df.schema: print(f.name, f.dataType)   # compare to the CREATE column list
  ```
- On mismatch: fix the DECLARATION (type/name) or the SELECT in-place — the `.sql` file already
  exists (step 2), so you edit, you don't re-author.
- Do this in the SDP **pipeline editor** (Rule 26), not the file editor.

This is a real plan-time gate: `EXPLAIN` on an MV catches `UNRESOLVED_COLUMN` (a referenced column
doesn't exist), `PARSE_SYNTAX_ERROR` (an illegal MV `PRIMARY KEY`/`FOREIGN KEY` constraint), and
type mismatches (Rule A declared-vs-inferred) — unlike MERGE notebooks that only fail at runtime.
Do NOT trigger the tier update until every entity in the tier parses.


## Data quality — inline EXPECT

DQ moves from the standalone `validate_silver` notebook INTO each declarative object as
`CONSTRAINT <name> EXPECT (<expr>) [ON VIOLATION { DROP ROW | FAIL UPDATE }]`. Map the spec
§6 thresholds to expectations. There is no separate recurring DQ notebook in this mode.

- **PK / grain not null → `ON VIOLATION FAIL UPDATE`** (or `DROP ROW`), tested on the **natural
  key**, not the SHA2 surrogate (the surrogate is never NULL — see the `valid_grain` note on the
  append-only template in `sdp-templates.md`).
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
> - **POST-UPDATE ROW-COUNT GATE (build-loop step 6 — required exit gate).** This is the definition
>   of the incremental build loop's step 6, back-referenced from there. After every SDP update, read
>   each object's row count from the event log's `flow_progress` `num_output_rows` (or
>   `SELECT COUNT(*)`) and treat **any object at 0 rows that is not a declared-empty entity** as a
>   build failure — do not call the build done until every non-empty entity has rows. This is the SDP
>   equivalent of the MERGE path's `validate_silver` row-count check.
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
  `LEFT JOIN ... COALESCE(dim.Key, -1)` in the defining query (see `sdp-gold-star.md`), so
  the FK is a real BIGINT that is never NULL — track health as the soft `-1`-rate EXPECT above.
- 🔴 **Never put a cross-table subquery in a `CONSTRAINT EXPECT`.** `EXPECT (customer_id IN (SELECT
  customer_id FROM LIVE.customer))` — or any `SELECT … FROM LIVE.<table>` inside a column-spec
  constraint — **fails** with `[TABLE_OR_VIEW_NOT_FOUND] LIVE.customer`. `LIVE.*` does not resolve
  in the constraint block. A real build hit this by improvising exactly that pattern. FK
  completeness is checked downstream, never as an inline subquery, in **either** mode.


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


## Event-log DQ reads (inspect after a run — not a build gate)

After a pipeline update, EXPECT pass-rates are readable from the pipeline event log — this is how
you confirm inline DQ held, and it's the input the downstream `domain-model-validation` skill uses.
It is **not** a build-time gate (the SDP build has none — see Testing). Query the `event_log` for
the pipeline (via the `event_log()` TVF or the pipeline's event-log table) and extract
`flow_progress` events' `data_quality.expectations` (passed/failed record counts) per expectation,
comparing against spec §6 thresholds. (Exact TVF/table binding — confirm against the installed
runtime.)
