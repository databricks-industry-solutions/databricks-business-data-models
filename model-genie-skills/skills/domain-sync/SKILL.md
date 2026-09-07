---
name: domain-sync
description: Keep a built domain model's artifacts in sync after point updates — the steady-state skill, loaded once the model exists. Use when a gap is closed, an FK fixed, a column added or renamed, a source repointed, or an entity added, and the dependent notebooks/DDL/narratives/gap registry/Model Guide/Genie space/dashboard must be re-synced; also for staleness linting ("is anything stale?"), scoped regeneration, generating next steps, and producing ARCHITECTURE.md / NEXT_STEPS.md. Not for the initial build (use the four loop skills in order).
---

# Domain Sync Skill

> **⚙️ Load `autonomous-validation` alongside this skill — it is NOT pulled in automatically; nothing wires the two together, so load it explicitly at the session start.** (See its `When to Load` for the execution-discipline contract.)
> Scoped regeneration verifies each re-synced artifact in batches and routes gap-acceptance / entity-add sign-off through its HITL gate (c) — the inline pointers below assume it is loaded.

## Overview

This skill keeps a **built domain model's artifacts in sync** after point updates. Once all
four loop stations (assess → build → validate → document) have run, the codebase is a web of
interdependent artifacts: MERGE notebooks, DDL, validation narratives, the gap registry, the
domain narrative, the Model Guide, the Genie space, and the dashboard. A single point fix
(closing a P0 gap, fixing an FK, adding a column) makes several of them stale at once.

Without a sync discipline, drift is silent and immediate — the first-pass Acuity output already
shipped a narrative whose FK cell says "expected to FAIL" next to `PASS`-threshold SQL, and a
Genie space carrying a wrong column name and pre-fix caveats. This skill closes that.

**What this skill produces / maintains:**
- `ARCHITECTURE.md` (project root) — the steady-state map: how the codebase fits together, the
  source-of-truth hierarchy, and the sync rules a returning agent must follow.
- `NEXT_STEPS.md` (project root) — priority-ordered, actionable next steps generated from
  `_gap_registry` + open validation findings + the prod-promotion checklist.
- **Scoped regeneration** of exactly the artifacts a change touched (never "regenerate all 16").
- **`synced-against` stamps** on every generated doc so staleness is detectable.
- A **staleness report** from the grep-based linter (contradictions, wrong columns, bad statuses).

**Scope:** Orchestration + detection + doc regeneration. This skill does NOT rebuild data — it
delegates the actual regeneration to the owning station skill (ETL for MERGE/DDL, validation for
narratives/dashboard, documentation for Model Guide/Genie/tutorials) and verifies the result. It
writes `ARCHITECTURE.md`, `NEXT_STEPS.md`, and `synced-against` stamps directly.

---

## Directory Guide (required section of ARCHITECTURE.md)

ARCHITECTURE.md MUST open with a "Where things live" guide, because `docs/.pipeline/` is hidden
and would otherwise be forgotten:

- **Start here** → `docs/tutorials/`, the Model Guide notebook, the Genie space
- **Understand the model** → `docs/explanation/`, `docs/reference/`
- **Why it's built this way / how we got here** → `docs/design/` (and `docs/inputs/` if present)
- **Maintaining it** → `docs/contributor/`
- **Machine plumbing (safe to ignore)** → `docs/.pipeline/` — skill-to-skill handoffs, state
  checkpoints, and session commentary. Its own `docs/.pipeline/README.md` is the in-folder
  manifest (what each file is, its seam, who writes/reads it); the ETL skill drops it at setup.
  Do NOT regenerate or restate that manifest here — link to it. The tier splits into
  `handoffs/{silver,gold}/` (typed seams, keyed by seam + layer) and `state/` (run checkpoints:
  `state/run/` = run-global, `state/{silver,gold}/` = layer-scoped).

---

## Reference Files

| File | Content |
| --- | --- |
| `change-impact-matrix.md` | The change-type → affected-artifacts map + scoped regeneration protocol (which station regenerates what, in what order). |
| `staleness-linter.md` | The grep/regex rule set for detecting drift, plus the `synced-against` stamp format and how to run a staleness sweep. |
| `next-steps-generation.md` | How to generate `NEXT_STEPS.md` and `ARCHITECTURE.md` from the source-of-truth files. |

---

## When to Load This Skill

Load when:
- User says "I fixed X — keep everything in sync" / "propagate this change" / "update the docs"
- A gap was closed, an FK fixed, a column added/renamed, a source repointed, or an entity added
- User asks "is anything stale?" / "check the docs are current" / "lint the model"
- User asks "what should I do next?" / "generate next steps" / "what's the state of this project"
- After a remediation brief is applied (the validation skill hands off here)
- Periodically, as a steady-state health check on a mature model

Do NOT load for:
- Initial build of a model — use the four loop skills in order
- Fixing the data itself — that's `etl-development-framework` (this skill *invokes* it, scoped)
- One-off queries — just query directly

---

## Source-of-Truth Hierarchy (authoritative)

Sync always flows FROM the sources of truth TO the derived docs. Never edit a derived doc to
match reality — fix the source of truth, then regenerate the derived docs from it.

| Rank | Artifact | Owns the truth about |
| --- | --- | --- |
| 1 | `progress.md` | Entity list, load order, grades, fixes applied, configuration |
| 1 | `_gap_registry` (table) | Every known gap + status + unblock action |
| 2 | DDL notebooks | Live schema (columns, types, comments, FK, constraints) |
| 2 | MERGE notebooks | Source mappings, dedup/recency, FK-resolution joins, load strategy |
| 3 (derived) | narrative_*, domain_narrative.md | Explanation — regenerated from 1+2 |
| 3 (derived) | Model Guide, tutorials | Reference/onboarding — regenerated from 1+2 |
| 3 (derived) | Genie space (instructions + queries + caveats) | Analyst interface — regenerated from 1+2 |
| 3 (derived) | dashboard | Reads `_validation_*` — no regeneration, just reflects runs |

If a derived doc disagrees with a rank-1/2 source, the derived doc is WRONG. That is the
staleness the linter hunts for.

---

## Execution Model

### Phase 1: Establish what changed
- If the user named a change ("fixed the OEE FK"), classify it against `change-impact-matrix.md`.
- If not, run the **staleness sweep** (`staleness-linter.md`): compare every derived doc's
  `synced-against` stamp to the current `progress.md` rev, and run the regex rule set.
- **Output:** a change list (each with its type) and/or a staleness report.
- **Gate (auto-check):** change set identified with affected artifacts per the matrix.

### Phase 2: Update the source of truth
- Ensure the rank-1/2 sources reflect the change FIRST: update `progress.md` (fix log,
  grade, config), flip the `_gap_registry` row (status → `RESOLVED`/`DEFERRED` with date), and
  confirm the DDL/MERGE notebooks are the fixed versions.
- **Gate (HUMAN if the change is a model-shape or exception decision):** e.g. descoping an
  entity or accepting a gap needs sign-off (HITL gate (c) from `autonomous-validation`).

### Phase 3: Scoped regeneration (delegate to owning skill, one entity at a time)
- Follow `change-impact-matrix.md`: for each affected artifact, invoke the owning station skill
  **scoped to only the changed entity** — never regenerate all 16.
- Respect **Batching Discipline** — if a change touches several entities, regenerate in batches
  of ≤ 4, verifying each (see `autonomous-validation`).
- **Gate (auto-check):** each regenerated artifact runs clean and its stamp is refreshed.

### Phase 4: Re-stamp + re-lint
- Write a fresh `synced-against: {progress.md rev/date}` stamp on every regenerated doc, **at its
  canonical location** (do not create a second copy elsewhere): `narrative_*` in `src/silver/validation/`,
  `domain_narrative.md` in `docs/explanation/`, Model Guide at the project root, Genie instructions in
  `docs/.pipeline/handoffs/genie_space_instructions.md`, tutorials in `docs/tutorials/` — see the
  `ARCHITECTURE.md` Directory Guide.
- Re-run the linter to confirm zero remaining contradictions.
- Regenerate `NEXT_STEPS.md` and refresh `ARCHITECTURE.md` if structure changed.
- **Gate (auto-check):** linter clean; `NEXT_STEPS.md` current. Report the sync scorecard and
  finish (HITL gate (a) — report, don't ask).

---

## Critical Rules (Always Apply)

1. **Fix the source of truth, then regenerate derived docs** — never hand-patch a derived doc
   to hide a contradiction. That is how the first pass shipped "expected to FAIL" next to PASS.
2. **Scoped regeneration only** — touch the changed entity, not the whole model. All-16 regen
   is both wasteful and the exact scale trap the batching gate exists to avoid.
3. **Delegate to the owning station** — this skill does not write MERGE/DDL/narratives/Genie
   itself; it invokes ETL / validation / documentation scoped to the change and verifies.
4. **Every derived doc carries a `synced-against` stamp** — no stamp, or a stamp older than the
   current `progress.md` rev, means stale. See `staleness-linter.md`.
5. **Run the linter before declaring done** — zero contradictions is the exit gate.
6. **`NEXT_STEPS.md` regenerates from `_gap_registry`** — never hand-maintain the list; it is
   derived from the registry + open validation findings + the prod-promotion checklist.
7. **Genie space is re-pushed, not just re-written** — a stale Genie space ships wrong SQL to
   analysts. On any caveat/column change, regenerate AND push to the existing space id, then run
   every sample query through the documentation skill's Query Validation Gate before finishing.
8. **Report and proceed** — this skill runs autonomously through the sync; stop only at a true
   human gate (model-shape/exception decision) per the HITL contract.

---

## Relationship to Other Skills

- **Reads sources of truth from:** `etl-development-framework` (`progress.md`, DDL, MERGE) and
  `domain-model-assessment` (S2T, gap registry seed).
- **Invokes (scoped) for regeneration:** `etl-development-framework` (fix a MERGE/DDL),
  `domain-model-validation` (regen a narrative, re-run a validation batch, flip a gap row),
  `domain-documentation` (regen Model Guide / tutorials / Genie space).
- **Receives handoff from:** `domain-model-validation` remediation protocol — after a
  remediation brief is applied, this skill propagates the fix to all derived docs.
- **Owns at project root:** `ARCHITECTURE.md`, `NEXT_STEPS.md`, `synced-against` stamps.
  (`ARCHITECTURE.md` is generated by this skill — previously validation created it; `progress.md`
  stays owned by ETL.)
