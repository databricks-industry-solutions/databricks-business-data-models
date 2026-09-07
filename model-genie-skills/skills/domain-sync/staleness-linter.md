# Staleness Linter & synced-against Stamps

Two mechanisms detect drift: **stamps** (is this doc older than the source of truth?) and the
**regex rule set** (does this doc contradict the source of truth or itself?). Run both in a
staleness sweep (SKILL.md Phase 1) or after any regeneration (Phase 4).

---

## The `synced-against` Stamp

Every derived doc carries a stamp near the top — at its canonical location (see the target skill /
`ARCHITECTURE.md` Directory Guide): `narrative_*` (`src/silver/validation/`), `domain_narrative.md`
(`docs/explanation/`), the Model Guide (project root), the Genie instructions markdown
(`docs/.pipeline/handoffs/genie_space_instructions.md`), and tutorials (`docs/tutorials/`):

```
<!-- synced-against: progress.md @ 2026-07-16 (rev: <short git sha or run id>) -->
```

- For notebooks, put it in the first markdown cell.
- For the Genie space, record the stamp in `docs/.pipeline/handoffs/genie_space_instructions.md` AND
  in the space's instruction text footer.
- **Staleness rule:** a doc is stale if it has **no stamp**, or its stamp date/rev is **older
  than the current `progress.md`** last-modified rev. The sweep lists every stale doc.

`progress.md` itself is the clock. When a fix updates `progress.md`, every derived doc's stamp
is now behind until it's regenerated and re-stamped.

---

## Regex Rule Set (contradiction detection)

Run these against the project tree. Each is a heuristic — a hit is a *candidate* contradiction
to inspect, not an automatic failure. Tune per project.

| Rule | Pattern (intent) | Why it's drift |
| --- | --- | --- |
| **Stale-gap-vs-pass** | A cell/comment containing `expected to FAIL` / `P0 GAP` / `100% orphan` sitting in the same notebook as a passing threshold (`PASS`, `<= 1.0`, `Is_Accepted_Exception = FALSE`) | The gap was fixed but the narrative still says it's broken (the exact OEE FK bug) |
| **Wrong-column** | Any column name referenced in a doc/query that is NOT in the live schema for that table (diff doc column refs vs `INFORMATION_SCHEMA.columns`) | Renamed column left dangling (the `Record_Date`→`Shift_Date` bug) |
| **Bad-gap-status** | A gap status word not in the standardized enum (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `ACCEPTED`, `DEFERRED`) — e.g. `Descoped`, `Backlog`, `Open` | Status vocab mismatch → dashboard/Genie filters silently drop the row |
| **Orphan-caveat** | A Genie/narrative caveat naming a gap whose `_gap_registry` status is now `RESOLVED` | Caveat outlived its gap |
| **Stamp-missing** | A derived doc with no `synced-against` stamp | Can't tell if it's current |
| **Grade-mismatch** | A grade asserted in a narrative/Model Guide that differs from the latest `_validation_table_result` for that entity | Doc grade is frozen at an old run |

### How to run the sweep

1. Build the entity → live-schema map (one `INFORMATION_SCHEMA.columns` query for the schema).
2. For each derived doc: extract its `synced-against` stamp and its column references.
3. Apply the rules above (grep for the literal-pattern rules; set-diff for the schema rules).
4. For gap-status and grade rules, join against `_gap_registry` / `_validation_table_result`.
5. Emit a **staleness report**: one row per hit — file, rule, the offending line, suggested
   change-type from `change-impact-matrix.md`.

---

## Staleness Report Format

```
## Staleness Report — {project} — {date}

| File | Rule | Line / detail | Change-type to run |
| --- | --- | --- | --- |
| narrative_fact_oee_record | stale-gap-vs-pass | "P0 GAP … expected to FAIL" vs PASS <=1.0 | FK fixed |
| genie_space_instructions.md | wrong-column | `o.Record_Date` (schema has `Shift_Date`) | column renamed |
| gap_analysis.md | bad-gap-status | `Descoped` not in enum | gap status changed |

Stale by stamp (behind progress.md @ {rev}): {list}
Clean: {count} docs current.
```

Feed each row's "change-type" into the change-impact matrix and regenerate scoped.

---

## Exit Gate

Sync is not done until a re-run of the sweep reports **zero contradiction hits** and **no docs
behind the current `progress.md` rev**. Report the clean sweep as the sync scorecard.
