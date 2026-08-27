# How to operate the validation outputs (job + dashboard)

**Goal:** you ran `domain-model-validation` once and it left behind a job, a dashboard, a scorecard, and
metadata tables. This guide is how to **run them as a steady-state monitoring surface** — schedule the
job, read the dashboard, query the metadata directly, and route what you find to the right fix.

**Roughly:** 15 minutes to schedule + wire alerts; then it's ongoing.

> This is the **hub** the reactive guides branch out of. [fix-a-degraded-table.md](fix-a-degraded-table.md)
> and [investigate-drift.md](investigate-drift.md) both *start* from "the dashboard shows a bad grade / a
> drift alert fired" — this guide is how you get to that starting point and what the surface means.

## What validation left you

One validation run produces a durable, re-runnable monitoring surface (read-only + `_validation_*` writes):

| Artifact | Where | What it's for |
| --- | --- | --- |
| **Validation job** | `resources/{domain}_validation.job.yml` (DAB) | Per-table `narrative_{entity}` tasks in load order, with `scorecard` as the terminal task. Re-runnable and schedulable. |
| **Scorecard** | `src/silver/validation/scorecard.sql` | Terminal task: grades every entity, writes the run, **enforces the fail gate**. |
| **Metadata tables** | `{silver_schema}._validation_*` | The graded results over time — the dashboard and any CI gate read these, never the model tables. |
| **Quality dashboard** | `{Domain} Validation Quality` (Lakeview) | 4 tabs; reads exclusively from `_validation_*`. The human-facing view. |

## Step 1 — Schedule the job and wire alerts

The validation job is a DAB resource — you operate it like any Lakeflow job. Two decisions:

- **Cadence:** run it **right after the ETL job** (validate what just loaded), plus on a daily schedule.
  The default cron/timezone come from `conventions.yml` → `deployment.default_schedule_cron` /
  `default_timezone`.
- **Alerting:** set `deployment.alert_email` in `conventions.yml` so a failed run (or a fail-gate trip)
  notifies you. Host and per-target values resolve from the DAB target, never baked into SQL.

The scorecard also honors a `Triggered_By` marker so you can distinguish run *contexts* in the metadata —
`SCHEDULED`, `PRE_DEPLOY` (the promotion gate, see [promote-to-production.md](promote-to-production.md)),
`MANUAL`. Deploy/run the job with the CLI and an explicit profile:

```
databricks bundle deploy -t {target} --profile {profile}
databricks bundle run {domain}_validation -t {target} --profile {profile}
```

## Step 2 — Read the dashboard (the 4 tabs)

Open `{Domain} Validation Quality`. Each tab answers one question — read them in order:

| Tab | Question it answers | What you're looking for |
| --- | --- | --- |
| **1 · Current State** | "Is the model healthy *right now*?" | The overall-health banner (grade + last-validated + drift-alert count) and the per-entity grade table. This is the at-a-glance check. |
| **2 · Historical Trend** | "Is it getting better or worse?" | Grade trajectory per entity — catches slow **degradation** a single run wouldn't flag. |
| **3 · Priority Backlog** | "What do I fix *next*?" | Failing entities ranked by severity — your work queue. |
| **4 · Integration Health** | "Do the pieces fit together?" | Star-schema / FK consistency across entities (orphans, unresolved keys). |

**Reading a grade.** Grades run **A · B+ · B · C+ · C** (the dashboard color-codes A green, B+ light-green,
B amber, C+/C red). The operational line is **B or better = production-ready**; C+ or below is a real
problem, and a D/F table is a **true human gate** — it does not promote until fixed or explicitly signed
off (see [promote-to-production.md](promote-to-production.md)).

## Step 3 — Query the metadata directly (ad-hoc + CI gates)

The dashboard is the human view; for automation or a quick drill-down, query the five `_validation_*`
tables (column names are authoritative in `skills/domain-model-validation/validation-schema.md`):

| Table | Holds | Typical use |
| --- | --- | --- |
| `_validation_run` | One row per run — overall grade, timestamp, entity/drift counts | "What's the latest overall grade?" · a CI gate that fails a build below B |
| `_validation_table_result` | Per-entity grade per run | Which entities regressed since last run |
| `_validation_check_detail` | Per-check pass/fail with values | Root-cause a specific failing entity (what fix-a-degraded-table opens) |
| `_data_drift_baseline` | The baselines drift is measured against | What a drift alert compared against (what investigate-drift opens) |
| `_gap_registry` | Known/accepted gaps + status | Distinguish a *real* failure from a *known, accepted* gap |

## Step 4 — Act on what you see (route, don't roam)

The dashboard/metadata tell you *what*; these guides tell you *how to fix*:

- **A grade dropped (C+ or below, or a regression on tab 2)** → [fix-a-degraded-table.md](fix-a-degraded-table.md).
- **A drift alert (tab 1 banner count > 0, or a `_data_drift_baseline` breach)** → [investigate-drift.md](investigate-drift.md).
- **A failing check is actually a known, accepted gap** → confirm it's in `_gap_registry` with an
  `ACCEPTED` status; if not, record it there rather than treating it as a fresh failure.
- **You changed the model (added a table, closed a gap)** → the metadata will look stale until you re-sync;
  route through [re-sync-after-a-change.md](re-sync-after-a-change.md), which also re-baselines.

## Done when

The validation job runs on a schedule (and after each ETL load), a failed run emails you, and you can read
the dashboard to answer "healthy now?", "trending which way?", and "what's next?" — then route any bad
grade or drift to the right fix without hand-querying tables to find your bearings.
