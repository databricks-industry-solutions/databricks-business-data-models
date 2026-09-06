# How to add a table to an existing model

**Goal:** add a new entity (`{entity}`) to a model that's already built, validated, and
documented — without re-running the whole loop.

**Roughly:** 30–60 minutes.

## Decide your starting point

- **You know the source** (which bronze table(s) feed `{entity}`) → skip to Step 2, use the
  build skill directly for the single entity.
- **You don't know the source** → start at Step 1 with a scoped assessment.

## Step 1 — Assess the new entity (only if the source is unknown)

Load `domain-model-assessment`, scoped to the one entity:

> "Assess adding `{entity}` to the `{domain}` model. I think the source is
> `{catalog}.{schema_or_bronze}`."

The skill profiles the candidate source, maps columns, and identifies FKs to existing
dimensions. It produces a scoped S2T mapping for just this entity.

## Step 2 — Build the entity

Load `etl-development-framework`:

> "Add `{entity}` to the `{domain}` project. Here's the S2T mapping."
> (or, if source was known: "…I think the source is `{catalog}.{schema}.{table}`.")

The skill generates the DDL + load notebook, runs the MERGE and gates the entity on a
post-load DQ check against the real table (PK/FK/population/row-count + idempotency), and
updates the DAB job to include the new task in load order.

## Step 3 — Validate the entity

Load `domain-model-validation`:

> "Add `{entity}` to the validation suite."

Generates a new `narrative_{entity}` regression notebook, updates the scorecard, and
establishes a baseline.

## Step 4 — Re-sync the docs

Do **not** manually re-run the documentation skill. A single new entity is a *point change*
— route it through sync:

> "I added `{entity}` — re-sync the `{domain}` docs."

`domain-sync` uses its change-impact matrix to regenerate only what the new table touched
(Model Guide FK map, Genie sample queries, narrative cross-reference, tutorials if structure
changed) and re-stamps them. See [re-sync-after-a-change.md](re-sync-after-a-change.md).

## Done when

`{entity}` loads, clears its post-load DQ gate and regression checks at an acceptable grade,
appears in the DAB job in load order, and the docs reflect it (no staleness-linter warnings).
