---
name: autonomous-validation
description: Execution-discipline guidance for Genie Code running autonomously at scale — a cross-cutting skill loaded alongside the loop stations, not a station itself. Load for any task spanning 3+ notebooks or 5+ tool calls where correctness matters — multi-notebook/table validation, iterative SQL development, or self-verification before finishing. Codifies scratchpad-validate then confirm then persist, batching discipline, and the run-until-a-gate human-in-the-loop contract. Not for single obvious edits or pure read/exploration.
---

# Skill: autonomous-validation

## Purpose

Codifies execution patterns, limitations, and best practices for Genie Code operating autonomously at scale — particularly multi-notebook validation, iterative SQL development, and self-verification workflows.

## When to Load

- User asks to validate, test, or verify multiple notebooks/tables in one turn
- User asks to build or run a multi-step ETL pipeline and confirm results
- User asks to "check your own work" or "make sure it's right before finishing"
- Agent is about to write SQL/Python to a notebook without having tested it first
- Any task spanning 3+ notebooks or 5+ tool calls where correctness matters

## Do NOT Load For

- Single-cell edits with obvious correctness (renaming a column, fixing a typo)
- Pure read/exploration tasks (browsing schemas, reading notebooks)
- Tasks where the user explicitly says "just write it, I'll test later"

---

## Core Execution Model

### Tool Hierarchy (fastest → slowest feedback loop)

| Tool | Feedback | Scope | Use For |
|------|----------|-------|---------|
| `executeCode` (scratchpad) | Immediate, same turn | Ephemeral — no persistence | Validation, iteration, exploration |
| `editAsset` (write cells) | No execution feedback | Persistent | Final, tested code only |
| `runNotebookCells` | Immediate, same turn | Current notebook only | Running cells after writing them |
| `openAsset` + `continueMessage` | **Ends the turn** | Target notebook | Only when execution on another page is required |

### The Golden Rule

> **Validate in scratchpad → Confirm results → Persist to notebook**

Never write untested SQL or Python directly to a notebook cell when correctness can be verified first. The scratchpad (`executeCode`) is free, fast, and iterative. Use it.

### Persist-Before-Advance

After a unit of work (a notebook, a DDL file, an artifact) passes its scratchpad validation, persist it to its durable asset *before* starting the next unit. Never let validated work live only in ephemeral execution results — an interruption would lose it. Verify the write succeeded before marking the unit complete.

### Verification Pass Before Declaring Done

Before declaring any batch or phase complete, run a concrete verification pass — (a) every artifact is persisted at its expected path, (b) every generated statement executes without error (a `SELECT … LIMIT 0` parse is enough), (c) produced counts match expectations. Prefer executing the artifact over pattern-matching its text: a dry-run parse catches 100% of syntax/semantic errors regardless of formatting. Present the results; do not declare done until it passes.

### Commentary on Completion

Each loop station's final closeout emits a `docs/commentary/{skill}-improvement-recommendations.md` file — see `commentary-protocol.md` (hosted in this skill) for the contract and template.

---

## Human-in-the-Loop Contract (READ FIRST)

**Default posture: run autonomously through a batch or phase. Do NOT ask the user "should I
continue?" between entities, notebooks, or batches.** Prodding the user to continue at every
step is the failure mode this contract exists to prevent. Keep going until you hit a **HITL
gate** — one of exactly three situations:

| Gate | Trigger | What to do |
| --- | --- | --- |
| **(a) Deliverable ready + self-graded** | A batch/phase completed and you have graded it | **Report the mini-scorecard and PROCEED.** State results; do not ask permission to move to the next batch. Only stop here if the phase is the *last* one or the user set an explicit checkpoint. **At the *last* phase, render the Completion Self-Audit list unprompted** — reconcile the skill's closing obligations and report what is still open; do not let the user discover leftovers by asking "are we done?". Name it **"Remaining before handoff"** when a next skill consumes the output, or **"Remaining before done"** at the loop's terminal station (documentation). An empty list is what unlocks the handoff / "done". Each loop skill defines its own worked instance: `domain-model-assessment` (Phase 5 → 6), `etl-development-framework` (Phase 7), `domain-model-validation` (Phase 5), `domain-documentation` (Phase 6). |
| **(b) Genuinely blocked** | 5 failed fix attempts on the same error; ambiguous schema you can't resolve by profiling; a destructive/irreversible action (DROP, OVERWRITE prod, deploy to prod) | **Stop and ask**, with the specific decision you need and the options. |
| **(c) Judgment call the human owns** | A Grade D/F table, accepting a known exception, descoping an entity, or any model-shape change | **Stop and ask**, present evidence + recommendation. |

**Self-grading IS the gate artifact.** After each batch, emit a compact scorecard — entities
done, PASS/FAIL per check, any KNOWN_GAP — then continue automatically unless (b) or (c) fires.
"I finished X, here's the grade, moving to Y" is the desired cadence; "I finished X, shall I do
Y?" is not.

**When you must stop, make it one decisive ask** — bundle the open questions, don't drip them.
A resuming agent should be able to read your scorecard + open questions and pick up without
re-deriving state.

---

## Patterns

### Pattern 1: Validate-Before-Persist (Single Notebook)

```
1. executeCode → run the query/logic, inspect results
2. If error → fix in executeCode, re-run (iterate up to 5x)
3. If success → editAsset to write the validated code to the target cell
4. (Optional) runNotebookCells if on the current notebook to confirm end-to-end
```

**Why:** Writing directly to a notebook and discovering errors requires 3 tool calls per fix cycle (read error → edit cell → re-run). Scratchpad iteration is 1 call per fix.

### Pattern 2: Multi-Notebook Validation (Same Turn)

When validating N notebooks without navigating:

```
1. readAssetById on all relevant notebooks (parallel — up to 5 at once)
2. Extract the SQL/Python logic from each notebook's cells
3. executeCode to run each query sequentially (or key assertions)
4. Summarize pass/fail per notebook
5. Only navigate (openAsset) if a fix requires running the full notebook graph
```

**Why:** Navigation is a handoff. Reading + scratchpad execution keeps everything in one turn.

### Pattern 3: Multi-Table Assertion Suite

When checking data quality across many tables:

```sql
-- Run as a single executeCode call with UNION ALL
SELECT 'dim_plant' as entity, COUNT(*) as row_ct,
       COUNT(DISTINCT Plant_Key) as pk_distinct,
       SUM(CASE WHEN Plant_Key IS NULL THEN 1 ELSE 0 END) as pk_nulls
FROM catalog.schema.dim_plant
UNION ALL
SELECT 'dim_shift', COUNT(*), COUNT(DISTINCT Shift_Key), ...
FROM catalog.schema.dim_shift
UNION ALL
...
```

**Why:** One executeCode call validates N tables. Avoids N separate tool calls.

### Pattern 4: Iterative SQL Development

```
1. Start with SELECT * FROM table LIMIT 5 — understand shape
2. Build the query incrementally, running each version
3. Add JOINs one at a time, verifying row counts don't explode
4. Add WHERE/GROUP BY, verify aggregates make sense
5. Final version → write to notebook
```

**Why:** Complex queries built blindly often have silent fan-out or filter errors. Incremental build catches them early.

### Pattern 5: Pre-Flight Check Before Completing a Task

Before marking a multi-step task complete, run a "pre-flight" validation:

```
1. Re-read the target notebooks (readAssetById) to confirm edits landed
2. Run key assertions in scratchpad:
   - Row counts are non-zero
   - Primary keys are unique
   - Foreign keys resolve (JOIN produces expected row count)
   - No unexpected NULLs in NOT NULL columns
3. Summarize results to user with pass/fail per check
```

---

## Known Limitations & Workarounds

### 1. Cannot Execute Cells in Multiple Notebooks Per Turn

- **Constraint:** `runNotebookCells` only works on the currently open notebook.
- **Workaround:** Read other notebooks, extract logic, validate in scratchpad. Only navigate if you truly need the full notebook execution context (e.g., widget parameters, sequential cell dependencies).

### 2. Navigation Ends the Turn

- **Constraint:** `openAsset` with `navigate: true` hands off to the destination page agent.
- **Workaround:** Batch all work for the current page before navigating. Use `continueMessage` to pass a complete task description — don't navigate with vague instructions.

### 3. Scratchpad Variables Don't Persist Across Turns

- **Constraint:** Each new conversation turn gets a fresh execution context.
- **Workaround:** If intermediate results are needed later, write them to a temp table or summarize them in your response. Re-run setup code at the start of a new turn if needed.

### 4. Context Window Erosion

- **Constraint:** Very long turns (20+ tool calls) risk losing early context.
- **Workaround:**
  - Use TODO lists to externalize state
  - Summarize intermediate results after each phase
  - Keep scratchpad queries tight — use LIMIT, select specific columns
  - Avoid dumping large result sets; prefer aggregates for validation

### 5. Large Result Sets Burn Tokens

- **Constraint:** Every tool result consumes context window.
- **Workaround:**
  - Always LIMIT (default 100, prefer 10-20 for validation)
  - Use COUNT/SUM/MIN/MAX for assertions, not SELECT *
  - For schema exploration, use `readTable` (structured) over `SELECT * LIMIT 5`

### 6. File Writes Are Atomic (Full Replacement)

- **Constraint:** `workspaceUpdateFile` replaces the entire file.
- **Workaround:** Always `readFile` first, make targeted edits, write back the full content. Never write from memory alone.

### 7. 10-Minute Default Timeout

- **Constraint:** `executeCode` times out at 10 minutes by default.
- **Workaround:**
  - Prefer scoped queries (single day, single table, LIMIT)
  - Only raise timeout if: prior run measured > 8 min, or user explicitly requested full scope
  - If timeout occurs: narrow first (shorter date range, fewer columns), don't just bump the timeout

---

## Autonomy Budget

To prevent infinite loops while still being thorough. "Then" actions that say *ask* are
**HITL gate (b)** — a genuine block, not a routine check-in. Everything else: report and
proceed.

| Scenario | Max Iterations | Then |
|----------|---------------|------|
| Fixing a failing query in scratchpad | 5 | **Gate (b)** — stop, ask with the specific error + options |
| Retrying after timeout | 1 (narrower scope or higher timeout) | Report and proceed; if still failing, gate (b) |
| Validating across tables | 1 pass + 1 re-check of failures | Report findings and proceed to next batch |
| Writing + testing a single notebook | 3 edit-run cycles | If still failing, gate (b); otherwise proceed |
| **Authoring notebooks in bulk** | **1 at a time (≤4 per session)** | **Persist + verify each before the next (see Batching Discipline)** |

---

## Batching Discipline (for multi-notebook generation)

**The failure mode:** authoring many notebooks in one turn — e.g. generating all 16
validation narratives or all 16 MERGE notebooks before running any — overflows the context
window and produces silent errors (wrong column names, missing PENDING writes, drifted paths)
that aren't discovered until a scheduled job fails. This is the single most common way
large-model runs break.

**The rule: author ONE artifact, verify it, persist it, then move on.** The `≤4`
cap is a **session budget, not a batch target**: how many entities one session
attempts before checkpointing out — not how many to author before running.
Authoring more than one un-verified artifact at a time is the *exception* — two
reference tables with zero dependencies, say — never the default. A batch of
un-verified artifacts is the durability hole this discipline exists to close: if
the session drops, un-persisted work is lost and a landed load may have no artifact
to reproduce it.

```
For each entity (in load-order tier sequence, ≤4 per session to bound context):
  1. Author the artifact (validate its SQL in scratchpad FIRST — Golden Rule)
  2. PERSIST it to the workspace immediately (before running the real load)
  3. Run it (or its key assertions via executeCode)
  4. Confirm results landed (target rows non-zero / no errors)
  5. Checkpoint the entity (state + progress) before starting the next
  6. Emit a mini-scorecard only at the batch/session boundary (HITL gate (a)) and PROCEED
```

- **Batch by tier**, so FK targets exist when dependents are validated: dims Tier 0–1 first,
  then Tier 2 dims, then facts. Never validate a fact before its dimensions are loaded.
- **Author → run → verify is one interleaved loop, not two phases.** Do not "generate all,
  then run all." Generate a batch, prove it, move on. The unit of the loop is **one entity**,
  not a batch; persist each entity before the next.
- This directly caps context growth: at most ~4 notebooks' worth of state is live before it's
  externalized into results and a scorecard.

---

## Multi-Session Execution (Setup / Batch / Finalize)

**The failure mode this solves:** even with the ≤4 sub-batch discipline above, running an entire
domain (16–17 entities) end-to-end in **one** Genie session accumulates too much state and
overflows the context window near the end — the session hangs (the Meridian failure mode). The fix
is to split one long run into three session types and checkpoint progress to a file a fresh session
can resume from.

**The model.** The ≤4 Batching Discipline loop above still applies — it now runs *inside* a single
**Batch** session that owns only its assigned slice of the domain.

| Session type | Runs | Count | Why it can't overflow |
| --- | --- | --- | --- |
| **Setup** | The singleton front phases (context, schema/DDL, seeding) + **writes the checkpoint file** with every entity `NOT_STARTED` | exactly 1 | No notebook authoring — short |
| **Batch** | Authors/runs/verifies **only its assigned slice** (the ≤4 loop runs inside), flipping its rows toward "done" | 1..N | Bounded by slice size (~≤6 entities) |
| **Finalize** | Completeness gate (every row done?) → the singleton end phases (scorecard/bundle/Genie space, handoff docs) | exactly 1 | No notebook authoring — short |

**Each loop skill defines its own checkpoint file and role split** — this section is the shared
mechanism they point back to. The per-skill files:

| Skill | Checkpoint file | Status enum | Skill-specific note |
| --- | --- | --- | --- |
| `domain-model-validation` | `docs/.pipeline/state/silver/validation_state.md` | `NOT_STARTED→AUTHORED→VERIFIED` | Finalize is the sole scorecard runner |
| `etl-development-framework` | `docs/.pipeline/state/silver/etl_state.md` | `NOT_STARTED→BUILT→TESTED` | Adds a **wave barrier** (dims→facts→gold) |
| `domain-documentation` | `docs/.pipeline/state/run/documentation_state.md` | `NOT_STARTED→ENRICHED→VALIDATED` | One Genie space per layer (hybrid: silver + gold), created in Finalize; parallel value low |

> **Path convention:** layer-scoped checkpoints live under `state/silver/` (or `state/gold/`);
> run-global ones (`progress.md`, `documentation_state.md` — documentation runs once over the
> whole domain) live under `state/run/`. See `docs/.pipeline/README.md`.

### Shared rules for the checkpoint file

- **Setup writes it once with every entity `NOT_STARTED`; Batch sessions update only their own
  rows; Finalize reads it to confirm completeness.** It is the single source of truth for "what's
  done" and makes the run resumable after an overflow.
- **Writes are atomic full-file replacement** (Known Limitation #6): `readFile` → make targeted
  edits → write the whole file back. A batch session edits **only its assigned rows** and, if
  sessions run in parallel, coordinates on `Assigned_Session` so two sessions never author the same
  entity. Never blind-append.
- **Finalize runs a completeness gate first** — confirm every entity reached its terminal status;
  if any hasn't, report exactly which slices still need a batch session and **STOP**. Never run the
  singleton finalizer (scorecard / bundle / Genie space) on partial data — a half-finished run must
  not produce a falsely-complete deliverable. This is HITL gate (b) — a genuine prerequisite block.
- **Single-session runs still use this** — one session plays all three roles in order but writes
  the checkpoint at each transition, so resumability is free. Small domains may skip it.

---

## Anti-Patterns (What NOT to Do)

1. **Don't write SQL to a notebook then navigate there to run it** — validate in scratchpad first, write the proven version.

2. **Don't read a 500-line notebook just to check one value** — use `startCell`/`endCell` or `executeCode` with a targeted query.

3. **Don't navigate to validate** — only navigate when execution *on that page* is required (e.g., widget-dependent cells, streaming context).

4. **Don't dump full tables into context** — use COUNT, DISTINCT, aggregates for validation assertions.

5. **Don't skip validation because "the SQL looks right"** — silent errors (wrong JOIN cardinality, NULL key mismatches, filter typos) are the most common class of bugs in generated SQL.

6. **Don't raise timeout preemptively** — start with default, narrow scope on failure, only raise with evidence.

7. **Don't cram a whole domain into one session** — for 16–17 entities, split into Setup / Batch / Finalize sessions with a checkpoint file (Multi-Session Execution). One session that authors and runs every entity is the overflow-and-hang failure mode this skill exists to prevent.

8. **Don't run the singleton finalizer on partial data** — the scorecard (validation), bundle/deploy (ETL), and Genie-space creation (docs) each run exactly once, in Finalize, only after the completeness gate confirms every entity reached its terminal status. Running one early grades/ships an incomplete set.

9. **Don't author a batch, then run the batch.** The per-entity commit loop (author → persist → run → checkpoint → next) is the default. A batch of un-verified, un-persisted artifacts is exactly the write-all-then-run pattern that loses work on session drop.

---

## Checklist: Before Completing Any Multi-Step Task

- [ ] All SQL/Python was validated in scratchpad before being written to notebooks
- [ ] Row counts are non-zero for all target tables
- [ ] Primary keys are unique (COUNT = COUNT DISTINCT)
- [ ] Foreign key joins resolve (no unexpected zero-row results)
- [ ] No silent data loss (compare source row count to target)
- [ ] TODO list items are all marked complete
- [ ] User has been given a summary of what was built and any known gaps

---

*Version: 1.1 — July 2026 (added Multi-Session Execution: setup/batch/finalize + per-skill checkpoint files)*
