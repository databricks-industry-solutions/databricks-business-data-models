# How to fix a degraded table

**Goal:** restore a table (`{entity}`) whose validation grade dropped (e.g. to C or below).

**Roughly:** 15–45 minutes.

## Step 1 — Diagnose

The validation dashboard shows the degraded grade on `{entity}`. Get the specifics: run the
`narrative_{entity}` regression notebook, or inspect `_validation_check_detail` for the
failing checks.

## Step 2 — Get a remediation brief

Load `domain-model-validation`:

> "Generate a remediation brief for `{entity}`."

The skill produces `docs/.pipeline/handoffs/{layer}/remediation_brief.md` (silver default; a
gold run writes it under `gold/`): the failing checks, the root-cause category, and a suggested
fix type. This is the typed handoff to the build skill.

## Step 3 — Fix

Load `etl-development-framework`, handing it the brief:

> "Fix `{entity}`. Here's the remediation brief:
> `docs/.pipeline/handoffs/silver/remediation_brief.md`."

The skill diagnoses the load notebook, proposes a fix, re-runs the MERGE, and re-grades against
the real table via the post-load DQ gate.

## Step 4 — Confirm

Load `domain-model-validation` again for a targeted re-validation:

> "Run a POST_FIX validation for `{entity}`."

Confirms the grade is restored and updates the `_gap_registry` status to `RESOLVED`.

## Step 5 — Re-sync if the fix changed structure

If the fix changed columns, FKs, or grain (not just data), route the point change through
`domain-sync` so the docs stay honest — see [re-sync-after-a-change.md](re-sync-after-a-change.md).
A pure data/logic fix that leaves the schema unchanged usually needs no doc re-sync.

## Done when

`{entity}` is back at an acceptable grade, the POST_FIX run confirms it, and the gap registry
shows `RESOLVED`.
