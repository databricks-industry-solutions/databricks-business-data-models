# How to re-sync artifacts after a point change

**Goal:** after a *point fix* to a built model — closing a gap, fixing an FK, adding a column,
changing a caveat — bring every dependent artifact (MERGE, DDL, validation narrative, gap
registry, domain narrative, Model Guide, Genie space, dashboard) back into sync **without**
hand-re-running each skill.

**Why this recipe exists:** a single point change makes several artifacts stale at once, and
drift is silent. The first-pass output once shipped a narrative whose FK cell said "expected to
FAIL" next to a `PASS`-threshold query, and a Genie space carrying a wrong column name and
pre-fix caveats. `domain-sync` closes that gap.

## Use domain-sync, not a manual re-run

> "I {closed gap P2 / fixed the FK on `{entity}` / added column X to `{entity}`} — re-sync the
> `{domain}` model."

`domain-sync` will:

1. **Consult the change-impact matrix** — map your change type to exactly the artifacts it
   touches.
2. **Scope the regeneration** — delegate regeneration of only those artifacts to their owning
   station skill (build for MERGE/DDL, validation for narratives/dashboard, documentation for
   Model Guide/Genie/tutorials) — never "regenerate all 16."
3. **Re-stamp** — write a fresh `synced-against` stamp on each regenerated doc.
4. **Run the staleness linter** — a grep/regex sweep that flags contradictions, wrong column
   names, and bad gap statuses that survived.

## Do not

- Do **not** manually re-run `domain-documentation` for a point change — that's a full
  regeneration, far more expensive, and it won't run the staleness sweep. Full re-run is only
  for wholesale changes (many entities added, a domain restructure, a new skill in the suite).
- Do **not** hand-edit a generated doc to patch a contradiction — the next sync will overwrite
  it and the stamp will lie. Fix the source of truth and let sync regenerate.

## Done when

The staleness linter reports clean, every touched artifact carries a current `synced-against`
stamp, and `NEXT_STEPS.md` / `ARCHITECTURE.md` reflect the change.
