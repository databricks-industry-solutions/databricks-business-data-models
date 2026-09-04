# SDP Pipeline Deployment — the FILE model (etl_type: sdp_pipeline)

> Part of the `sdp_pipeline` template pack — the `pipeline` DAB resource (plain `.sql`, glob,
> `root_path`, source-linked dev). Overview: `sdp-pipeline-development.md`. Templates: `sdp-templates.md`.

## Pipeline DAB resource — the FILE model (plain `.sql`, glob, `root_path`)

> 🔴 **Use the FILE model, not the notebook model (VERIFIED best practice, 2026-08-08).** SDP
> pipeline sources are **plain `.sql` files with NO `-- Databricks notebook source` header**,
> included via a single **`glob:`** entry, with **`root_path:`** set to the source tree. Do NOT
> give SDP sources the notebook-source header, do NOT create notebook objects for them, and do NOT
> list them as per-entity `notebook:` libraries. A real build hit a three-way deadlock doing
> exactly that: `.sql` files carried the notebook header → became notebook-type objects →
> referenced as `notebook:` (which strips the `.sql` extension) → DLT looked for a bare `customer`
> object that either didn't exist or was created Python-language → `NO_TABLES_IN_PIPELINE`. The
> Databricks docs call plain `.py`/`.sql` + `libraries.glob` the module-style best practice for
> pipelines; `glob` cannot be combined with `notebook:`/`file:` in the same entry.

SDP mode emits **TWO** resources, usually in one `resources/{domain}_silver_pipeline.yml` file:
a `pipeline` (the declarative graph) **and** a thin scheduler `job` that triggers it on the daily
cadence. The pipeline is `continuous: false` (triggered) — a triggered pipeline has **no schedule of
its own**, so without the scheduler job it only ever runs when someone clicks Start. This is the SDP
analogue of the MERGE path's daily job; do not omit it.

```yaml
resources:
  pipelines:
    {domain}_silver_pipeline:
      name: {domain}_silver_pipeline
      channel: PREVIEW          # sane dev default (NOT for unit testing — see `sdp-pipeline-development.md` "Testing — NONE")
      continuous: false         # triggered (the scheduler job below drives the daily cadence)
      catalog: ${var.silver_catalog}       # the pipeline's DEFAULT write target
      schema: ${var.silver_schema}         # silver objects (unqualified names) land here
      # root_path = the PROJECT root (one level up from resources/), NOT ../src. This makes the
      # pipeline's root folder the whole project, so opening it in the editor (Genie Code) shows —
      # and can edit — everything: databricks.yml, resources/, docs/, all of src/. It is NOT the
      # workspace/repo root (that is the placement bug the 🔴 note below warns about) — it is the
      # bundle root that holds databricks.yml. What the pipeline RUNS is still scoped by `libraries`
      # below, so a wide root_path exposes the project for editing without pulling non-pipeline code
      # into the graph.
      root_path: ..
      # bronze paths hardcoded in each source; NO `parameters:` block.
      # In HYBRID, gold objects are SCHEMA-QUALIFIED with a HARDCODED catalog.gold_schema literal
      # (catalog.field_service_gold_sdp.dim_x) — same hardcode stance as bronze paths, no ${var}.
      libraries:
        # glob include paths resolve relative to THIS bundle YAML's directory (resources/),
        # NOT to root_path — keep the ../src prefix (same form the MERGE flows use). This is the
        # scoping knob: ONLY these globs become pipeline source, even though root_path is the whole
        # project — so the graph contains just the pipeline SQL, never docs/ or resources/.
        - glob:
            include: ../src/silver/pipeline/**    # normalized silver sources (unqualified -> default schema)
        # --- HYBRID ONLY: also include the downstream gold star sources ---
        - glob:
            include: ../src/gold/pipeline/**      # dim_/fact_ MVs, object names hardcoded to the gold schema
      notifications:
        - email_recipients: ["${var.alert_email}"]
          alerts: ["on-update-failure"]
      serverless: true          # required where the workspace enforces serverless compute

  # ─── Scheduler job — triggers the triggered pipeline on the daily cadence ───
  # A single-task job whose `pipeline_task` starts an update of the pipeline above.
  # This is what the MERGE path gets from its daily notebook job; the SDP pipeline
  # supplies the DQ/EXPECT logic, the job supplies the schedule.
  jobs:
    {domain}_silver_pipeline_job:
      name: {domain}_silver_pipeline_job
      schedule:
        quartz_cron_expression: "{job_schedule}"   # conventions.yml deployment.default_schedule_cron
        timezone_id: "{job_timezone}"              # conventions.yml deployment.default_timezone
        pause_status: PAUSED
      email_notifications:
        on_failure:
          - "${var.alert_email}"
      max_concurrent_runs: 1
      tasks:
        - task_key: run_{domain}_silver_pipeline
          pipeline_task:
            pipeline_id: ${resources.pipelines.{domain}_silver_pipeline.id}
            # full_refresh: false   # default incremental; UI Start ▸ Full refresh for a rebuild
```

> **Why two resources, not `parameters:` on the pipeline:** the scheduler is a plain job with a
> `pipeline_task`, referencing the pipeline by `${resources.pipelines.<key>.id}` so the DAB wires the
> real pipeline id per target. No compute/`environments` block is needed — a `pipeline_task` runs on
> the pipeline's own compute, not the job's.

**Layer → folder → schema** (in all layouts `root_path: ..` = the project root; the `libraries`
globs below are the scoping knob):
- `normalized` / `dimensional` (single layer): only `src/silver/pipeline/` exists; drop the gold
  glob and keep the single `include: ../src/silver/pipeline/**`.
- `hybrid` (two layers): `src/silver/pipeline/` (silver, unqualified → default silver schema) **and**
  `src/gold/pipeline/` (gold, object names hardcoded-qualified `catalog.gold_schema.dim_x`). Both are
  globbed into the ONE pipeline. The silver→gold graph resolves in one update (gold's fully-qualified
  references to the silver objects order silver first).

No `ddl/`, `transformations/`, `runners/`, or `tests/` subfolders in this mode — there is no
separate DDL step and no build-time test/validation artifact. Each layer's sources are plain `.sql`
files (no notebook-source header), one per entity.

> 🔴 **Author the pipeline and its sources INSIDE the project root, under `src/silver/pipeline/` —
> never at the repo/workspace root.** A real build wrote the pipeline sources to the root instead of
> the project tree, so the deployed pipeline was rooted at the workspace root rather than scoped to
> the project. The **project root** is the top level — the folder that holds `databricks.yml`,
> `resources/`, and `src/`. Everything the pipeline reads lives under that root's `src/` tree:
> - **Silver sources → `src/silver/pipeline/{entity}.sql`** (this is the SDP equivalent of the
>   merge-mode `src/silver/transformations/` folder — SDP uses `pipeline/`, `merge_notebook` uses
>   `transformations/`; do not mix them). Gold sources (hybrid) → `src/gold/pipeline/{entity}.sql`.
> - **`root_path: ..`** on the pipeline resource anchors the **project root** (relative to the
>   `resources/` YAML — one level up), so the running pipeline's root folder is the project (holding
>   `databricks.yml`/`resources/`/`src/`) and the editor exposes the whole project for Genie Code to
>   browse and edit. It must resolve to the project root, **never the workspace/repo root**. What the
>   pipeline actually RUNS stays scoped by the `libraries` globs (`../src/silver/pipeline/**`,
>   +`../src/gold/pipeline/**` for hybrid), regardless of how wide `root_path` is.
> - When authoring via Genie Code (`openAsset` pipeline editor, or programmatic file writes), write
>   each source to its **project-relative `src/silver/pipeline/{entity}.sql`** path. **After creating
>   the sources, verify they all live under the project's `src/silver/pipeline/` (and
>   `src/gold/pipeline/` for hybrid)** — a source file sitting at the root, or a pipeline whose
>   `root_path` resolves to the workspace root, is a placement bug: move it into the project tree and
>   re-point `root_path` before deploying.

**Deployment mode:**
- **Dev target:** `source_linked_deployment: true` — the pipeline references the source files
  in-place (its root folder = your repo tree), which is the git-friendly edit-in-place dev loop.
  Because the sources are plain `.sql` files (no header) included by `glob`, there is no
  extension-stripping collision.
- **Prod target:** `source_linked_deployment: false` (or immutable snapshots) — files are copied
  into the deploy path so the running pipeline is pinned and doesn't depend on a live repo.
- **Environment routing** (same as the MERGE path): serverless → author + `bundle validate` + hand
  off to the Deployments panel; web terminal / local / CI → `databricks bundle deploy` then trigger
  the pipeline update. A full refresh is required when an entity changes object type (e.g. MV→ST),
  and that (and `DROP TABLE`) may be blocked by tool safety policy on serverless — hand off to the
  UI's Start ▸ Full refresh rather than spiraling on CLI/SDK workarounds.

> **Tooling note — prefer programmatic file writes for SDP source edits.** On real builds the
> patch/edit-by-match tool (`editAsset`) failed repeatedly on these `.sql` sources: it could not match
> whitespace-sensitive `old_text`, choked on UTF-8 multi-byte characters these templates used to carry
> (a non-ASCII null sentinel, em-dashes, and middots inside code), and was intermittently blocked by
> safety policy for writing `CREATE ... ON VIOLATION` content (misread as a destructive op). Now that
> the null sentinel is ASCII `~` and the SQL code fences avoid multi-byte punctuation, `editAsset`
> should match reliably; if it still fails on a whitespace-heavy source, fall back to `createAsset`
> with the full file content (a full-file rewrite), which bypasses match-patching. For surgical
> multi-file fixes —
> especially applying the same type/CAST fix across many entity files at once — a full-file rewrite via
> plain file I/O (`open()/write()` in `executeCode`) is more reliable than exact-match patching. Also
> note `bundle run` intermittently returned "Command with guid not found"; starting the update via the
> SDK (`w.pipelines.start_update()`) was the reliable fallback. When editing a source from the
> **pipeline editor** page, `editAsset` needs the file registered first: read it with explicit
> `startLine`/`endLine` (e.g. `1`–`3`) then edit by numeric ID — a read without line params
> sometimes fails to register the file for editing.
