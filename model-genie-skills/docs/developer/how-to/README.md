# How-to guides

Task-oriented recipes. Each one assumes you already know the suite (if not, start with the
[tutorial](../tutorial.md)) and gets you to a specific goal. They use `{domain}`,
`{catalog}.{schema}`, and `{entity}` placeholders — substitute your own.

| Goal | Recipe |
| --- | --- |
| Fill out `conventions.yml` for a new customer/domain (choosing the knobs, the source map) | [fill-out-conventions.md](fill-out-conventions.md) |
| Prepare your own inputs for the assessment (requirement docs, discovery brief) | [prepare-assessment-inputs.md](prepare-assessment-inputs.md) |
| Choose what to do after the assessment and before the build (iterate upstream, ingest more, defer, deviate, keep/drop nulls) | [decide-before-the-build.md](decide-before-the-build.md) |
| Extend a built silver model to gold (the gold requirements brief, deriving the star) | [extend-to-gold.md](extend-to-gold.md) |
| Add a new table to an existing model | [add-a-table.md](add-a-table.md) |
| Operate the validation outputs — schedule the job, read the dashboard, route findings | [operate-validation-outputs.md](operate-validation-outputs.md) |
| Fix a table whose grade dropped | [fix-a-degraded-table.md](fix-a-degraded-table.md) |
| Promote a validated model to production | [promote-to-production.md](promote-to-production.md) |
| Investigate a data-drift alert | [investigate-drift.md](investigate-drift.md) |
| Query the built model in natural language (consumer-facing, reading answers honestly) | [query-the-model.md](query-the-model.md) |
| Re-sync artifacts after a point change | [re-sync-after-a-change.md](re-sync-after-a-change.md) |

For the "which skill do I use?" decision tree and the full skill catalog, see
[../reference.md](../reference.md).
