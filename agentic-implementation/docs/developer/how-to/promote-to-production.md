# How to promote a model to production

**Goal:** move a validated `{domain}` model from dev/sandbox to production.

**Roughly:** 15 minutes, assuming validation passes.

## Prerequisites

- All entities at **Grade B or better** in the latest validation run.
- Catalogs/schemas are **runtime parameters**, not baked into any notebook (they should be —
  the build skill authors them that way; see
  [../reference.md](../reference.md#conventionsyml--the-single-config-surface)). Promotion is a
  matter of pointing the DAB's prod target at the prod catalog, not editing SQL.

## Step 1 — Run the pre-deploy gate

Execute the validation job with the pre-deploy trigger:

> Run the validation job with `Triggered_By = 'PRE_DEPLOY'`.

Confirm every entity is Grade B or better. A Grade D/F table is a **true human gate** — either
fix it first (see [fix-a-degraded-table.md](fix-a-degraded-table.md)) or explicitly sign off
the exception.

## Step 2 — Point the prod target at prod catalogs

The prod `{catalog}.{schema}` come from the DAB's prod target variables and
`conventions.yml` defaults — not from editing notebooks. If the prod target isn't defined yet,
ask the build skill:

> "Promote `{domain}` to production. Wire the prod DAB target to the prod catalog."

## Step 3 — Deploy

Deploy the bundle to the prod target (DAB operations use the CLI with an explicit profile):

```
databricks bundle deploy -t prod --profile {profile}
```

## Step 4 — Re-validate in prod

Run the validation job against the prod schema and confirm grades hold.

## Step 5 — Point the Genie space at prod

> "Point the `{domain}` Genie space at the prod tables."

The documentation skill regenerates the space's table list + sample queries against prod.

## Done when

The bundle is deployed to prod, prod validation passes, and the Genie space answers a test
question against prod data.
