# Progress Tracking & Resume Protocol

## When to Use

Maintain a `progress.md` file in the project root throughout the entire ETL workflow.
Update it after EVERY phase transition and after EVERY notebook test iteration.
This file serves as both a status dashboard and a resume point if the session is interrupted.

---

## Phase Gate (Rule 13)

**Never author the DAB bundle until every entity's `progress.md` row shows Grade A (or HUMAN NEEDED).** The deploy only makes sense once all notebooks pass; bundling earlier produces a job that loads untested tables. This is the same gate stated in `deployment-and-dab.md` "When to Use."

---

## Update Triggers

Update `progress.md` after:
- Discovery completes (entity list proposed)
- Gap analysis completes (multi-session: this is also when the **Setup** session writes
  `docs/.pipeline/state/silver/etl_state.md` — the per-entity tier/type/wave checkpoint — before handing off to batch
  sessions; see the SKILL's Checkpoint & Session Roles)
- Each entity's load notebook is scaffolded
- Each entity's real load passes post-load DQ at Grade A + its idempotency recheck (the Phase 5 gate)
- Each notebook load/grade iteration (pass or fail)
- All notebooks reach Grade A (or HUMAN NEEDED)
- `build_manifest.md` emitted (Phase 6.5 — the typed build→validate handoff; records strategy/recency/FK-resolution/filters/exceptions/row-counts/thresholds + per-entity post-load DQ grade + idempotency-recheck result)
- Bundle creation
- Integration test

> Per the **per-entity commit contract** (SKILL.md Critical Rule 28), each entity's
> notebook + `etl_state.md` row + `progress.md` row are written together before the next
> entity starts — so a resume reads a consistent, per-entity checkpoint, never a
> half-committed one.

---

## progress.md Format

```markdown
# ETL Pipeline Progress

## Status: {DISCOVERING | GAP_ANALYSIS | SCAFFOLDING | TESTING | BUNDLING | INTEGRATION_TEST | COMPLETE | BLOCKED}

## Phase Summary
| Phase | Status | Notes |
| --- | --- | --- |
| 1. Discovery | ✓ Complete | 12 entities identified, 3 dims + 9 facts |
| 2. Model & DDL | ✓ Complete | DDL generated + approved, -1 seeds inserted |
| 3. Gap Analysis | ✓ Complete | 4 gaps found, 2 enrichment opportunities |
| 4. Scaffold | ✓ Complete | 12 load notebooks + 1 validation generated |
| 5. Load, DQ & Grade | ▶ In Progress | 8/12 Grade A + idempotency PASS, 2 in progress, 2 blocked |
| 6. Bundle & Deploy | ○ Pending | Waiting on Phase 5 |
| 6.5 Build Manifest | ○ Pending | Emit `docs/.pipeline/handoffs/silver/build_manifest.md` after build + tests |
| 7. Integration Test | ○ Pending | |

## Entity Status
| Entity | Tier | Load notebook | Loaded? | Idempotency recheck | Grade | Iterations | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dim_plant | 0 | ✓ | ✓ | PASS | A | 2 | ✓ Done | |
| dim_product | 0 | ✓ | ✓ | n/a | A | 1 | ✓ Done | |
| dim_customer | 0 | ✓ | ✓ | PASS | B+ | 3 | ▶ Fixing | FK to dim_region null 4% |
| fact_orders | 1 | ○ | ○ | - | - | 0 | ○ Pending | Depends on dim_customer |
| fact_shipments | 1 | ✓ | ✓ | PASS | D | 2 | ⚠ HUMAN NEEDED | Ambiguous date logic |

*Columns track the per-entity gate so no step is silently skipped:*
- ***Loaded?*** *— the real load ran successfully against the target table.*
- ***Idempotency recheck*** *— the RESULT of running the load a second time and asserting row-count
  + key-set stability. PASS is required before the batch advances (run on the first entity of each
  load strategy; `n/a` for sibling entities that inherit a proven shape). Distinct from the Grade
  (post-load DQ quality of the real load).*

## Human Review Needed
- **fact_shipments**: Ship date vs. delivery date — unclear which maps to `Event_Date`. Source has both `SHIP_DATE` and `ACTUAL_DELIVERY_DATE`. Need business decision.
- **dim_customer**: 4% FK orphans to dim_region — are these valid (international?) or bad data?

## Decisions Made
- dim_plant: Used `PLANT_CODE` as natural key (not `PLANT_ID` — codes are unique and human-readable)
- fact_orders: Watermark on `LAST_UPDATE_DATE` (>10M rows, incremental load)
- Unknown-member seeded: All dims have -1 row inserted via DDL seed step; facts default FK misses to -1 via COALESCE

## Next Action
Fixing dim_customer FK resolution — trying enrichment from `ref_region_mapping` table.
```

---

## Resume Protocol

If the user re-opens this project and prompts "continue", "resume", or "pick up where we left off":

1. **Read `docs/.pipeline/state/run/progress.md`** to determine current state
2. **Pick up from the last incomplete phase/entity**
3. **Do NOT re-run completed work** (notebooks already at Grade A stay done)
4. **Address any HUMAN NEEDED items** only if the user provides guidance
5. **Update `docs/.pipeline/state/run/progress.md`** with resumed status

### Per-Entity Commit Contract (Rule 28)

After an entity reaches its terminal status, **three artifacts must be persisted before the next entity starts:**

1. The load notebook (or `.sql` declarative source) written to `src/…`
2. The entity's row in `etl_state.md` flipped to its terminal status
3. The entity's row in `progress.md` updated

These three writes are the entity's atomic transaction — if any is missing on session loss, the entity's work is not recoverable. The entity-first loop (Phase 4) enforces this as a hard gate.

---

### conventions.yml Validation Gate (Rule 29)

**At session start (Setup role), before any SQL runs, validate `conventions.yml`:**
- `catalogs.silver` exists: `SHOW SCHEMAS IN {catalog}`
- Each `bronze_sources` entry resolves: `SHOW TABLES IN {catalog}.{schema}`
- `vibe_model.catalog`/`.schema` exists and holds the expected entity tables
- `schemas.silver_pattern` resolves

A misconfigured catalog or source is a HITL gate (b) — stop and report. Do not discover 10 entities into the build before surfacing a typo in `conventions.yml`.

---

### Multi-Session Resume (when `docs/.pipeline/state/silver/etl_state.md` exists)

A large-domain build may have been split into Setup / Batch / Finalize sessions (see
`etl-development-framework/SKILL.md` "Checkpoint & Session Roles"). If `docs/.pipeline/state/silver/etl_state.md` is
present, resume is **tier-, wave-, and session-aware**:

> **`etl_type: sdp_pipeline` — terminal status is `AUTHORED`, not `TESTED`.** SDP entities
> advance on `AUTHORED` (declarative source written + row-count verified) rather than `TESTED`
> (there is no post-load DQ gate in SDP mode). The wave barrier (`wave:1` dims → `wave:2` facts →
> `wave:3` gold) still applies, enforced on `AUTHORED` status. Finalize bundles once all rows
> reach `AUTHORED`. The three-artifact commit contract above applies: source `.sql` + `etl_state.md`
> row + `progress.md` row are persisted atomically per entity.

1. **Read `docs/.pipeline/state/silver/etl_state.md`** — get every entity's `Tier`, `Type`, `Wave`, `Assigned_Session`,
   and `Build_Status` (`NOT_STARTED → BUILT → TESTED`). This is the checkpoint of record for
   "what's built"; `progress.md` remains the human-readable phase/grade dashboard.
2. **Determine which entities to pick up:**
   - If a session was assigned specific rows (parallel launch), resume *only* that session's
     entities that are not yet `TESTED`.
   - If resuming serially, pick up the first non-`TESTED` entity **respecting the wave barrier** —
     do not start a `wave: N` entity until every `wave: <N` entity is `TESTED` (dims `wave:1` →
     facts `wave:2` → gold `wave:3`).
3. **Do NOT re-build or re-load entities already `TESTED`** — that is the wasted work this
   checkpoint exists to prevent. An entity that is `BUILT` but not `TESTED` still needs its
   post-load DQ gate (real load + DQ at Grade A + idempotency recheck).
4. **If all rows are `TESTED`**, this becomes the **Finalize** step: run the completeness gate,
   then Phases 6 → 6.5 → 7, updating `docs/.pipeline/state/silver/etl_state.md` and `docs/.pipeline/state/run/progress.md` as you go.
5. **Update both files** — flip `docs/.pipeline/state/silver/etl_state.md` rows as entities reach `BUILT`/`TESTED`; update
   `docs/.pipeline/state/run/progress.md` with resumed status. Writes are full-file replacement — `readFile` first, edit,
   write back (`autonomous-validation` Known Limitation #6).

The plain-`docs/.pipeline/state/run/progress.md` resume above still applies for single-session projects (no `docs/.pipeline/state/silver/etl_state.md`).

### Cold Recovery (tables exist, no progress.md / etl_state.md)

A partial build from a prior session may have left tables but no state files. This is
neither a fresh project nor a normal resume. Recover deterministically:

1. Enumerate tables in the target silver schema (`SHOW TABLES IN {catalog}.{schema}`).
2. Classify each by row count (`SELECT COUNT(*)`): loaded (>0) or empty.
3. **Loaded entities:** reconstruct DDL via `SHOW CREATE TABLE`, run the post-load DQ
   gate, and mark **BUILT** — NOT TESTED. TESTED requires the idempotency recheck, which
   needs a load notebook to re-run (see testing-and-grading.md).
4. **Empty entities:** mark `NOT_STARTED`.
5. Write `etl_state.md` + `progress.md` from this scan (per-entity rows, tier/type/wave).
6. **Flag loaded entities missing a load notebook** in `src/silver/transformations/` —
   they are NOT recoverable to TESTED until the notebook is authored. Authoring it, then
   running the full DQ + idempotency gate, is what advances them BUILT → TESTED.

### Resume Detection Keywords

Trigger resume protocol when the user says any of:
- "continue"
- "resume"
- "pick up where we left off"
- "what's the status"
- "where were we"
- "keep going"

---

## Status Values

| Status | Meaning |
| --- | --- |
| `DISCOVERING` | Phase 1 in progress — profiling sources, classifying entities |
| `GAP_ANALYSIS` | Phase 3 in progress — comparing sources to model |
| `SCAFFOLDING` | Phase 4 in progress — generating load notebooks |
| `TESTING` | Phase 5 in progress — loading, running post-load DQ, and grading notebooks |
| `BUNDLING` | Phase 6 in progress — creating DAB config |
| `INTEGRATION_TEST` | Phase 7 in progress — running full job |
| `COMPLETE` | All phases done, job deployed and passing |
| `BLOCKED` | Waiting on HUMAN NEEDED decision(s) |

---

## Entity Status Icons

| Icon | Meaning |
| --- | --- |
| ✓ | Done (Grade A or Accepted) |
| ▶ | In progress (currently being fixed/tested) |
| ○ | Pending (not yet started, waiting on dependencies) |
| ⚠ | HUMAN NEEDED (blocked, requires user decision) |

---

## Checkpoint & Session Roles (resumable + parallelizable build)

### The checkpoint file — `docs/.pipeline/state/silver/etl_state.md`

For a gold-layer build, substitute `silver/` → `gold/` in the state and handoff paths.

The **Setup** session writes it; every **Batch** session updates only its own rows; the
**Finalize** session reads it to confirm completeness before bundling. It is the single source of
truth for "what's built."

```markdown
# ETL State — {domain}
Updated: {YYYY-MM-DD HH:MM} · Setup run: {run stamp} · Total entities: {N}

| Entity | Tier | Type | Wave | Assigned_Session | Build_Status | Batch_Notes |
|---|---|---|---|---|---|---|
| dim_plant    | 0 | DIM  | 1 | setup      | TESTED      | Grade A, idempotency PASS |
| dim_customer | 0 | DIM  | 1 | session_A  | TESTED      | Grade A, idempotency PASS |
| fact_orders  | 1 | FACT | 2 | session_B  | BUILT       | needs post-load DQ gate |
| fact_returns | 1 | FACT | 2 | session_C  | NOT_STARTED | — |
```

- **`Build_Status` enum:** `NOT_STARTED → BUILT → TESTED`. Only the Phase 5 **post-load DQ gate**
  (real load + PK/FK/population/row-count at Grade A + twice-run idempotency PASS) may move a row to
  `TESTED` — an authored-but-not-loaded notebook is `BUILT`. A notebook can exist yet fail its load
  or DQ checks, so `BUILT` is not "done"; only `TESTED` is.
- **`Wave`** is the ETL-specific column: dims are `wave: 1`, facts `wave: 2`, gold (when in scope)
  `wave: 3`. **Rule: no wave-`N` entity starts until every wave-`<N` entity is `TESTED`** (facts
  need their parent dim *tables* loaded; gold reads from silver facts). In a single session this is
  just the normal dims-before-facts load order; across parallel sessions it is an explicit barrier
  the human enforces (launch wave-1 sessions, wait for all wave-1 `TESTED`, then launch wave-2).
- **`Assigned_Session`** is how two sessions avoid building the same entity — a batch session only
  touches rows assigned to it (or unassigned rows it claims by writing its id first).
- **Record build-time fixes in `Batch_Notes`** — when an entity's load failed on first attempt and
  needed a fix (a re-mapped target/source column, a corrected natural key, a filter fix), note it with
  a `fix:` prefix (e.g. `fix: 5 target column name mismatches — quote_number→number, …`). This flags
  fragile entities for Finalize, carries into `build_manifest.md`, and (per the manifest's mapping-fix
  note) the correction is also reflected back into `etl_detailed_spec.md` so the next iteration
  doesn't repeat it.
- Writes are atomic full-file replacements (`readFile` → edit → write back), never blind-append —
  see `autonomous-validation` Known Limitation #6.

### The three session roles (the 7 phases split by singleton-ness)

Phases 1–3 (discovery, DDL-as-setup, gap analysis — including the model-approval PAUSE) and
Phases 6–7 (bundle/deploy, integration test) are **singletons**. Per-entity authoring + loading
(Phases 4–5) is the fan-out. So a large domain builds as:

| Role | Runs | Does | Stops when |
|---|---|---|---|
| **Setup** (once) | Phase 1 + 2 + 3 | Discovery (**model-approval PAUSE stays**), create tables as the one-time DDL setup, gap analysis, **write `etl_state.md` with every entity `NOT_STARTED` + tier + type + wave + session assignments** | State file written; tables exist |
| **Batch** (1..M, may be parallel within a wave — human-managed multi-session only) | Phase 4 + 5 for its assigned entities only | Author DDL + load notebook → real load → post-load DQ + idempotency recheck → grade, ≤4 per session (one entity at a time), flip its rows `BUILT`→`TESTED` | All its assigned rows `TESTED` |
| **Finalize** (once) | Phase 6 + 6.5 + 7 | Confirm **every** row is `TESTED` (else stop and report which aren't, respecting waves), bundle + deploy, emit `build_manifest.md`, run integration test | Bundle authored + manifest emitted |

- **Setup and Finalize are short** (no per-entity authoring) — they never overflow. **Batch
  sessions are bounded** to ≤4–6 entities. This is the structural fix for the overflow,
  independent of whether you run sessions in parallel.
- **Single-session runs still use this.** One session plays all three roles in sequence but writes
  `etl_state.md` at each transition, so if it *does* overflow the next session resumes from the
  state file instead of re-inferring. The wave barrier is just the normal load order.
- **Finalize is the sole bundler** — never author the DAB or run the integration test from a batch
  session; bundling a partial model produces a job that loads tables that were never tested.
- **For a single agent session the default is SEQUENTIAL entity processing — one entity at a time.**
  Parallel processing within a wave is a human-managed multi-session scenario only (a human
  launches disjoint batch sessions and enforces the wave barrier); a single session must not
  treat a wave as a parallel-author batch.

> **Sibling skills hit the same wall.** `domain-model-validation` (`validation_state.md`) and
> `domain-documentation` (`documentation_state.md`) use the identical Setup/Batch/Finalize split.
> Keep the three patterns aligned; the wave column is the one ETL-specific addition.
