# Maintenance Guide Generation — `maintaining-this-domain.md`

## What this reference produces

Generation rules for **one auxiliary, per-domain artifact**:
`docs/contributor/maintaining-this-domain.md`. It is a **slim, domain-local** guide for the
*developers* who will later tend **this specific** model — how to add/fix/re-sync THIS
domain's tables using the skill suite.

It is **not** a Diátaxis quadrant (the four quadrants — narrative, Model Guide, Genie space,
tutorials — are for the domain's data *consumers*). And it is **not** the place for the
suite-level "how to use the skills" content.

## Single source of truth (do not duplicate)

The full skill-suite explanation — the decision tree, the cross-domain workflow recipes, the
skill-interaction protocol, human-gates-vs-auto-checks, troubleshooting — lives **once**, in
the repo-level developer docs at **`docs/developer/`**:

- `docs/developer/index.md` — the Diátaxis compass
- `docs/developer/tutorial.md` — run the loop end-to-end
- `docs/developer/how-to/` — the cross-domain task recipes (add a table, fix a degraded table,
  promote to prod, investigate drift, re-sync after a change)
- `docs/developer/reference.md` — skill catalog, handoff chain, `conventions.yml`, gates
- `docs/developer/explanation.md` — the motion + vibe-model fit

**This guide LINKS to those; it does not restate them.** If you find yourself authoring a
suite-wide decision tree or a generic full-lifecycle recipe here, stop — that belongs in
`docs/developer/`. Keep this artifact scoped to *this domain*.

> If the project is a standalone export without the repo `docs/developer/` tree alongside it,
> link to the repo (`vibe-model-skills`) instead, and keep the same slim scope.

## Generation rules

Fill from `docs/.pipeline/state/run/progress.md` + `docs/.pipeline/handoffs/silver/build_manifest.md` + `ARCHITECTURE.md`:

1. **Header + stamp.** First line is the `synced-against` stamp
   (`<!-- synced-against: progress.md @ {date} (rev: {sha|run_id}) -->`), then a one-paragraph
   statement of what this domain is and who maintains it.
2. **This domain at a glance.** A short table of THIS model's entities (from `docs/.pipeline/state/run/progress.md`):
   entity name, dim/fact, grain, source system(s), current grade (from `validation_summary.md`).
   Plus the concrete project paths (DDL dir, load-notebook dir, validation dir, Model Guide,
   Genie space name).
3. **Maintenance recipes (domain-local).** Three short recipes, each scoped to THIS project's
   names/paths, each of which **defers to the repo how-to guide** for the general procedure and
   only supplies the domain-specific specifics:
   - *Add a table to this model* → link `docs/developer/how-to/add-a-table.md`; list this
     domain's catalog/schema + which bronze sources are already mapped in `conventions.yml`.
   - *Fix a degraded table here* → link `docs/developer/how-to/fix-a-degraded-table.md`; name
     this domain's validation job + dashboard.
   - *Re-sync after a point change* → link `docs/developer/how-to/re-sync-after-a-change.md`;
     remind that point fixes route through `domain-sync`, never a manual full re-run.
4. **Where the full suite docs are.** A closing "See also" pointing to `docs/developer/` for
   everything cross-domain.

## Style

- **Slim.** Target roughly one screen. If it grows past ~1.5 pages, you're duplicating
  `docs/developer/` — cut and link instead.
- **Domain-specific, not generic.** Every recipe names this domain's entities, paths, catalog,
  and jobs. Generic procedure lives behind the links.
- **Invocation patterns, not code.** "Ask the ETL skill to add `dim_{x}`", not low-level edits.

## Acceptance gate (MUST pass before Phase 6 completes)

The first pass shipped a 194-line guide that **restated** the add-a-table / close-a-gap / staleness
procedures step-by-step and contained **zero** links to `docs/developer/` — the exact anti-pattern this
reference forbids. Before the maintenance guide is done, verify ALL of:

1. **It links out.** The guide contains outbound links to
   `docs/developer/how-to/add-a-table.md`, `.../fix-a-degraded-table.md`, and
   `.../re-sync-after-a-change.md` (or, for a standalone export, the equivalent repo links). A guide
   with no `docs/developer/` links fails the gate.
2. **It does not restate the general procedure.** No numbered multi-step "how to add a table" /
   "how to close a gap" recipe. Each recipe is 1–3 lines: the domain-specific specifics (this domain's
   entities, tiers, paths, jobs, catalog) + a link to the general how-to. If you've written a
   step-by-step or a low-level SQL edit sequence, delete it and link instead.
3. **Length.** Roughly one screen (~1.5 pages max). If longer, you are duplicating `docs/developer/` —
   cut.

Fail any of the three → revise before completing Phase 6.

## On re-run

Regenerated (idempotent) if this domain's entities/paths changed. Suite-level content is never
regenerated here — it isn't here. Re-stamped on each regeneration.
