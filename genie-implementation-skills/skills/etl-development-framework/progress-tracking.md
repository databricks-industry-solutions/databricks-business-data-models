# Progress Tracking & Resume Protocol

## When to Use

Maintain a `progress.md` file in the project root throughout the entire ETL workflow.
Update it after EVERY phase transition and after EVERY notebook test iteration.
This file serves as both a status dashboard and a resume point if the session is interrupted.

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

### Multi-Session Resume (when `docs/.pipeline/state/silver/etl_state.md` exists)

A large-domain build may have been split into Setup / Batch / Finalize sessions (see
`etl-development-framework/SKILL.md` "Checkpoint & Session Roles"). If `docs/.pipeline/state/silver/etl_state.md` is
present, resume is **tier-, wave-, and session-aware**:

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
