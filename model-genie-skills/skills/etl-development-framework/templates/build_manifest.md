# [Project Name] — Build Manifest (as-built)

*The typed **build → validate** handoff. This is the **as-built MIRROR** of
`etl_detailed_spec.md`: the spec is the plan, this manifest is what actually shipped plus the
runtime facts the load produced. Write it as **confirmation-plus-deltas** — confirm the
as-built matches the spec, and call out every deviation — NOT a restatement of the spec.*

*`domain-model-validation` reads this as authoritative for per-entity strategy, recency column,
FK-resolution attribute, filters, accepted exceptions, final row counts, threshold seeds, and
post-load DQ grade + idempotency-recheck result. It does NOT reverse-engineer intent from MERGE
SQL. Emit it after the pipeline is built + graded (Phase 6.5), before/at handoff. Source it from
`progress.md`, the spec, the DDL, and the Phase-5 load + DQ run.*

> **When a build-time fix corrected a column mapping** (a source column the spec named wrong, a
> filter column that didn't exist, a natural key that was a target name), **reflect the correction
> back into `etl_detailed_spec.md` §2/§3** as well as recording it here. The manifest is the
> as-built truth for validation; the spec must stay authoritative for the *next* iteration so the
> same rewrite isn't repeated. §3.5's as-built column inventory is the source of the corrected names.

- **Domain:** {domain}   **Layer:** {silver | silver+gold}   **etl_language:** {sql | python}
- **output_model:** {normalized | dimensional | hybrid}   **scd_strategy:** {type_1 | type_2 (+ per-entity overrides)}
- **Built:** {date}   **Run/rev:** {job run_id or git sha}   **Entities:** {N}

---

## Section 1 — Load Strategy Applied (per entity) — mirrors spec §5

*What was actually built. Flag any deviation from the strategy the spec §5 stamped.*

| Entity | Strategy applied (FULL_MERGE / INCREMENTAL_MERGE / APPEND_ONLY / SDP) | SCD (type_1 / type_2) | Matches spec §5? | Deviation + why |
| --- | --- | --- | --- | --- |
| | | type_1 | yes / no | (only if no) |

*Validation uses this to set idempotency/drift expectations per strategy (APPEND_ONLY never
UPDATEs; INCREMENTAL only touches watermarked rows; FULL_MERGE re-scans). For `type_2` dims,
validation additionally checks exactly one `_is_current = TRUE` row per natural key and that
closed versions have `_effective_to` set.*

*When `etl_type: sdp_pipeline`: record the following per entity in addition to the strategy code
(`MV` / `ST-APPEND` / `ST-CDC1` / `ST-CDC2`) — mirroring how the MERGE manifest records
strategy/watermark/FK-resolution:*

| Entity | SDP object (`MV`/`ST-APPEND`/`ST-CDC1`/`ST-CDC2`) | Flow keys (CDC entities) | `SEQUENCE BY` column (CDC entities) | CDF required on bronze? |
| --- | --- | --- | --- | --- |
| | | | | yes / no / n/a |

*Flow keys are the natural-key columns used in the AUTO CDC `KEYS` clause. `SEQUENCE BY` is the
ordering column that resolves out-of-order events (prefer a source event timestamp). CDF
(`delta.enableChangeDataFeed = true`) is required on the bronze source only for `ST-CDC1` /
`ST-CDC2` entities — flag as a cross-team dependency if not already enabled. See
`sdp-pipeline-development.md` "Load-strategy → SDP object mapping".*

*When `etl_type: sdp_pipeline`, add an **SDP Operational Notes** block so operators know the refresh
semantics of what shipped:*
- *MV refreshes are managed by the pipeline (TRIGGERED mode) — do NOT run `REFRESH MATERIALIZED
  VIEW` outside the pipeline.*
- *`pipelines.reset.allowed: true` means a FULL REFRESH is safe for MVs (recomputable, no data
  loss). For Streaming Tables / `REPLACE WHERE` it must be `false` (a reset would drop appended
  history).*
- *An object-type change (MV→ST) requires a full refresh on next deploy.*
- *Per-entity graduation triggers (e.g. "re-assess object type when `vbep` exceeds ~5M rows") — see
  `sdp-pipeline-development.md` volume-graduation table.*

## Section 2 — Recency Column Used (per entity) — mirrors spec §3

| Entity | Recency column used in `ORDER BY ... DESC` | Matches spec §3? | Note |
| --- | --- | --- | --- |
| | source event ts (e.g. `LAST_UPDATE_DATE`) | yes / no | |

*Validation uses this to pick the dedup tiebreaker when checking for PK duplicates.*

## Section 3 — FK Resolution Attribute (per fact FK) — mirrors spec §3 FK-resolution

*The single highest-value handoff field, carried forward NOT re-derived — the OEE-bug fix.
Each FK was resolved by LEFT JOIN to the loaded dim on the join attribute below (never inline
SHA2 — see `merge-and-defensive-coding.md` Rule 11).*

| Fact entity | FK column | Fact source column | Dim joined | Dim join attribute | Join rate at load |
| --- | --- | --- | --- | --- | --- |
| | {Dim}_Key | e.g. `Plant` = "SEDC" (name) | dim_plant | `Plant_Name` (NOT `Plant_Code`) | e.g. 99.4% |

*Validation joins its FK orphan checks the SAME way (same source col ↔ dim attribute) so it
measures orphans against the real load path, not a re-derived hash.*

## Section 3.5 — As-Built Column Inventory (per entity) — the check contract

*The **exact physical column names in the DEPLOYED table**, so `domain-model-validation` codes its
check SQL against real columns instead of inferring them from the spec, the source tables, or
naming convention. Missing this is the #1 cause of validation authoring bugs (checks referencing
`Material_Number` when the gold table shipped `Material_Key`, or silver natural keys where a
dimensional rename applied). At minimum list the **PK, every FK, and the key measures**; listing
all columns is better. **Use the names as they appear in the built table** — for `dimensional` /
`hybrid`-gold entities that is the dimensional name (`Sold_To_Number`, `Material_Key`), NOT the
silver natural key the column was sourced from.*

| Entity | PK column(s) | FK columns | Key measure columns | Other columns (optional) |
| --- | --- | --- | --- | --- |
| | {Entity}_Key | {Dim}_Key, … | Net_Value, Ordered_Quantity, … | … |

*Validation prefers this as its column contract: for any column listed here it codes directly
against the given name. It is a **seed, not a closed set** — the PK/FK/measure minimum does not
cover attribute columns a POP or drift check might reference, so validation **always confirms
against a `DESCRIBE` of the deployed table** and treats `DESCRIBE` as authoritative when the two
disagree or a needed column is absent here. A referenced column missing from §3.5 is therefore NOT
an authoring error — it just falls back to `DESCRIBE`. Listing all columns (not just the minimum)
removes that extra round; a complete inventory is the ideal.*

## Section 4 — Filters Applied (per entity)

*Any `WHERE` predicate the load applied that changes the population vs. the raw source
(business filter, watermark, quarantine). Validation reads these to set expected row
counts / population thresholds rather than comparing to the full source.*

| Entity | Filter applied | Purpose (business filter / watermark / quality) |
| --- | --- | --- |
| | e.g. `WHERE TRANS_TYPE = 'PROD'` | |

## Section 5 — Accepted Exceptions / Constraint Relaxations

*Anything relaxed at build with a reason: an accepted FK orphan population, a CHECK not added,
a NOT NULL softened, a known-null column. Validation annotates these and EXCLUDES them from
grading (they are decisions, not defects).*

| Entity | Exception / relaxation | Why accepted | Expected magnitude |
| --- | --- | --- | --- |
| | e.g. 2% orphans to dim_region | international sites not in ref | ≈ 2% |

## Section 6 — Final Row Counts (per entity) — drift baseline seed

*The row count the FIRST clean load produced. Validation seeds its drift baseline from these —
a later run compares against this number for the `Row_Count_Delta` drift check.*

| Entity | Final row count | Source row count | Delta vs source (dedup/filter) |
| --- | --- | --- | --- |
| | | | e.g. −3% (dedup) |

## Section 7 — Threshold Seeds Applied — mirrors spec §6 (as actually set)

*The DQ thresholds the build actually wired into `validate_silver` / grading, taken from spec
§6. Validation READS these thresholds — it does not guess a number from S2T prose.*

| Check | Entity scope | Threshold set | Action (warn / fail) |
| --- | --- | --- | --- |
| PK uniqueness | all | 0 duplicates | fail |
| FK orphan rate | all (or per-FK override) | 0 orphans (or accepted per §5) | fail |
| Column population | {key cols} | ≥ 95% non-null | warn |
| Row count delta | all | ≤ 10% drop vs §6 baseline | warn |

## Section 8 — Post-Load DQ Grade + Idempotency Recheck (per entity) — from `testing-and-grading.md` (Phase 5 gate)

*Proof each entity's REAL load passed post-load DQ (PK/FK/population/row-count) at Grade A and
that re-running the load converges (row count + key set stable) — the build's per-entity gate.
Validation references this as confidence the load landed as intended; it runs its own
comprehensive data-state checks against the live tables.*

> **This section is a Phase 6 PREREQUISITE, not an afterthought.** The bundle (Phase 6) MUST NOT
> be generated while any entity shows a blank / FAIL here, or is missing from the table. Every
> entity in Section 1 must appear here at Grade A (or a documented HUMAN NEEDED) with its
> idempotency recheck PASS. If this section is incomplete, the owed work is loading/grading the
> missing entities — do that first, then emit the manifest and bundle. (The first Meridian pass
> emitted the pipeline with entities ungraded; this gate exists to prevent that.)

| Entity | Grade (post-load DQ) | Idempotency recheck (re-run: row count + key set stable) | Load strategy proven | Column comment coverage | Notes |
| --- | --- | --- | --- | --- | --- |
| | A | PASS / n/a | FULL_MERGE / INCREMENTAL_MERGE / APPEND_ONLY / SCD2 | e.g. 43/43 (100%) | e.g. inherited from sibling of same strategy |

*Every entity must show Grade A (or HUMAN NEEDED) — a batch did not advance otherwise (SKILL.md
Rule 17). Idempotency recheck is run on the first entity of each load strategy; sibling entities
show `n/a` (inherit the proven shape). A row here with a blank Grade means the pipeline is NOT
ready to bundle.*

*__Column comment coverage__ = count of built columns carrying a non-null `COMMENT` over total
columns. Column comments are sourced from the vibe model and are a REQUIRED part of the artifact
(merge DDL: `ddl-and-modeling.md` "Mandatory Model Introspection"; SDP source: `sdp-pipeline-development.md`
Rule D) — anything below 100% (excluding audit columns, which carry standard comments) means model
metadata was dropped. Flag any entity < 100% as an open item, not a pass.*
