# Change → Artifact Impact Matrix

For each change type, this maps the artifacts that go stale and the owning skill that
regenerates each — **scoped to the changed entity only**. Work top-to-bottom; each row is
independent unless a dependency is noted.

---

## The Matrix

### Change: FK fixed / FK-resolution join corrected (e.g. OEE Plant_Key name-vs-code fix)

| Affected artifact | Owner | Action |
| --- | --- | --- |
| MERGE notebook for the fact | ETL | Already fixed (this is the source change) — confirm it's the deployed version |
| `progress.md` fix log | ETL | Add the fix + new orphan rate |
| `_gap_registry` row | validation | Flip status → `RESOLVED` (date); if it was a P0/P2 gap |
| `narrative_{fact}` FK cell + comments | validation | Regenerate — comments must match the new PASS threshold, not the old "expected to FAIL" |
| `domain_narrative.md` fact story | validation | Regenerate that entity's paragraph + known-limitations line |
| Genie caveats + sample queries | documentation | Regenerate caveats (drop the stale gap), re-push to space id, re-validate queries |
| Model Guide health cell | documentation | Refresh (reads latest `_validation_table_result`) |
| `NEXT_STEPS.md` | domain-sync | Regenerate (the gap is now closed) |

### Change: Column added / renamed / retyped on an entity

| Affected artifact | Owner | Action |
| --- | --- | --- |
| DDL notebook | ETL | Source change — confirm ALTER/CREATE reflects it |
| MERGE notebook | ETL | Add/rename the column mapping |
| `narrative_{entity}` | validation | Regenerate — schema, sample rows, data profile, any new BK/POPULATION check |
| Genie sample queries referencing the column | documentation | Regenerate + re-validate (a renamed column is the classic `Record_Date`→`Shift_Date` bug) |
| Tutorials referencing the column | documentation | Regenerate only if a tutorial uses it |
| Model Guide column dictionary | documentation | Auto-current (live INFORMATION_SCHEMA) — no action if cells are live |

### Change: New entity added to the model

| Affected artifact | Owner | Action |
| --- | --- | --- |
| S2T mapping + spec | assessment | Add the entity's mapping, keys, FK-resolution, load strategy |
| DDL + MERGE notebook | ETL | Build the new entity (its own batch) |
| DAB job task | ETL | Add task in the correct load-order tier with depends_on |
| `narrative_{entity}` + scorecard | validation | Add narrative (its own batch), extend scorecard |
| Genie space table list + queries | documentation | Add table to space, add sample queries |
| `domain_narrative.md`, Model Guide, tutorials | documentation | Add the entity's story / reference / example |
| `ARCHITECTURE.md`, `NEXT_STEPS.md` | domain-sync | Update structure map + steps |

### Change: Load strategy changed (e.g. full MERGE → APPEND_ONLY / incremental)

| Affected artifact | Owner | Action |
| --- | --- | --- |
| MERGE notebook | ETL | Source change (new strategy) |
| `progress.md` config + spec Section 5 | ETL | Record the new strategy + rationale |
| `narrative_{entity}` "why is it this way" annotation | validation | Regenerate to explain the strategy |
| Row-count / freshness expectations in narrative | validation | Regenerate (incremental changes the load-delta expectations) |

### Change: Gap status changed (closed, deferred, newly opened)

| Affected artifact | Owner | Action |
| --- | --- | --- |
| `_gap_registry` row | validation | Update status per the standardized enum |
| Genie caveats | documentation | Regenerate (caveats are derived from open gaps) |
| dashboard Tab 3 | validation | Auto-reflects (reads `_gap_registry`) — no action |
| `NEXT_STEPS.md` | domain-sync | Regenerate |

### Change: Grade degraded (a scheduled run dropped a table below B)

Handled by the validation skill's **remediation-protocol** first (generate brief → ETL fix).
Once the fix lands, treat it as an "FK fixed" / "column" / "load strategy" change above and
propagate.

---

## Scoped Regeneration Protocol

1. **Identify the change type** and read its row(s) above → the affected-artifact set.
2. **Confirm the source of truth is fixed first** (rank-1/2 in the hierarchy). If not, stop —
   there is nothing valid to regenerate from.
3. **Regenerate derived artifacts one entity at a time**, invoking the owning skill scoped to
   that entity. If several entities are affected, batch in ≤ 4 (Batching Discipline).
4. **Never** invoke a station skill's full run — always scope: "regenerate the narrative for
   `fact_oee_record` only," not "re-run the validation skill."
5. **Re-stamp** each regenerated doc (`staleness-linter.md`) and **re-lint** to confirm clean.
6. **Regenerate `NEXT_STEPS.md`** and refresh `ARCHITECTURE.md` if structure changed.

## Anti-Patterns

- ❌ Regenerating all 16 narratives because one FK changed — scope it.
- ❌ Editing the narrative comment to say "PASS" without re-running the notebook — regenerate
  from the fixed MERGE + a fresh run, don't hand-patch.
- ❌ Updating the Genie markdown but not pushing to the live space — analysts still get old SQL.
- ❌ Leaving `NEXT_STEPS.md` hand-edited — it is derived; regenerate it.
