# Deployment & DAB Conventions

## When to Use

After ALL notebooks have been individually loaded and graded to Grade A (Phase 5 complete).
**DO NOT create the DAB config until all notebooks pass** (or are flagged HUMAN NEEDED).

---

## DABs Are the Core Deploy Pattern (non-negotiable)

**Everything is deployed as a Databricks Asset Bundle.** The bundle is the single source of truth
for jobs + notebooks; DABs work well with Genie Code — use them as the default and only pattern.
But **how the bundle actually gets deployed depends on WHERE you are running** — and that is a gate
you must resolve before touching a deploy command. See "Deploy is environment-routed" immediately
below; the CLI is NOT always available.

**What a bundle deploy does for you (so you DON'T hand-roll it):**
- **Uploads your `src/**` source files as executable notebook objects** (extension-less
  load notebooks + `.sql` DDL) when they're referenced by a `notebook_task`. You do NOT need to
  call `w.workspace.import_()`, `createAsset`, or any SDK upload — the bundle deploy handles
  source→notebook conversion.
- **Creates and updates the job** from `resources/*.job.yml`. You do NOT need `w.jobs.create`,
  `w.jobs.reset`, or a hardcoded `job_id` — the bundle owns the job's identity and reconciles it
  on every deploy.
- **Runs it** via `databricks bundle run {job_name}` (terminal environments only — see routing).

---

## Deploy is environment-routed (resolve this FIRST — it is a hard gate)

**The single biggest deploy failure is choosing the wrong deploy path because you never checked
where you are running.** On Genie Code's default **serverless notebook compute the Databricks CLI
is blocked by design** ("CLI only supported from web terminal"). Shelling out to
`databricks bundle deploy` there fails — and the failure tends to spiral into path-rewrites, YAML
re-writes, and SDK fallbacks, none of which are correct. Stop that before it starts:

### Step 0 — Detect the execution environment (before any deploy action)

Establish up front which of three environments you are in. This is the gate; do not skip it.

| Environment | How you got here | Deploy path |
| --- | --- | --- |
| **Serverless notebook compute** | Genie Code's default; MCP/notebook execution, no shell | **CLI is BLOCKED.** Deploy is NOT your job — author + validate, then **HAND OFF** to the workspace **Deployments panel (🚀 icon) → Deploy** |
| **Web terminal on an x86 all-purpose cluster** | user opened a web terminal with the CLI installed | `databricks bundle deploy -t <target>` is legitimate — use it |
| **Local / CI machine** | running from a laptop or pipeline with the CLI | CLI is the normal path — `databricks bundle deploy -t <target>` |

### Separate AUTHOR from DEPLOY as distinct phases

You are reliably good at **authoring** — adding/editing jobs in `resources/*.yml`, fixing YAML,
re-validating. Own that fully. Treat **deploy as a gated handoff, not a continuation** — it mirrors
how the product actually works (Genie Code edits the YAML; the Deployments panel deploys). The
loop iterates on **author + validate + diagnose**, never on deploy retries.

### Route the deploy — ONE path only

- **Serverless / no CLI → deploy is NOT the agent's job.** Author/edit `resources/*.yml`, run
  `bundle validate` if available, then emit an **explicit instruction to the user**: "Open the
  Deployments panel (🚀) and click Deploy for target `<dev|prod>`." Do not attempt the deploy.
- **Web terminal (x86) / local / CI →** `databricks bundle deploy -t <target>`, then
  `databricks bundle run {job_name}`.

### Hard prohibitions — encode as NEVER (this is what stops the spiral)

- **NEVER** shell out to `databricks bundle deploy` from serverless compute (blocked by design).
- **NEVER** retry the same CLI command via subprocess after it fails once.
- **NEVER** fall back to reconstructing bundle resources via the Python SDK / REST API
  (`w.workspace.import_()`, `w.jobs.create/reset`, `createAsset`) — bundle-managed resources must
  stay bundle-managed, or you get **state drift and orphaned jobs**.
- **NEVER** promise "just deploy this one job" — a deploy always applies the **whole bundle**
  (shared code). If the bundle holds many jobs, warn the user that all of them get touched.
- If the supported path is blocked, **STOP and tell the user the manual step** — do not invent an
  alternative.

> **Why the prohibitions are also a context-preservation measure:** Genie Code sessions die when
> context maxes out from retry loops. **One clean attempt + handoff beats twenty failed retries.**

**ANTI-PATTERN — do NOT do this:** writing an imperative Python orchestrator (e.g. a
`run_pipeline.py` that calls `w.workspace.import_()` in a loop, then `w.jobs.reset(job_id=...)`
against a hardcoded id and host) is a **bypass of the deploy pattern** and must not be produced.
If you feel the urge to write one, the deploy path is misrouted or the bundle is misconfigured —
re-check Step 0 and fix the YAML. The only sanctioned imperative snippet is the interactive-creation
fallback far below, and it is for *local/interactive* notebook creation, never for deploying the job.

> Per `manage_workspace` / MCP conventions, DAB `bundle` commands are the ONE place the CLI is
> called directly (with an explicit `--profile`) — **and only in a terminal environment (Step 0).**
> Everything else stays in the bundle.

---

## File Structure

Every table gets **one load notebook** plus DDL. **DDL is always a `.sql` file** (deployed by a
setup job). Load notebooks and validation are **extension-less notebook objects** whose format
follows `conventions.yml` `etl_language` (SQL: `-- Databricks notebook source`; Python:
`# Databricks notebook source`) — the extension is what marks a plain FILE that a `notebook_task`
cannot execute, so these carry none. See "Notebook-format contract" below for the shapes.

Notebooks are organized in **subfolders per layer** under `src/`:

```
{workspace_path}/
├── docs/
│   ├── Kickoff                         # Parameter notebook
│   ├── business_requirements.md        # User-filled requirements
│   ├── etl_detailed_spec.md            # Optional spec override
│   └── progress.md                     # Auto-maintained status
├── src/
│   ├── silver/
│   │   ├── ddl/                          # DDL — plain .sql files (setup job)
│   │   │   ├── ddl_dim_{entity_a}.sql   # CREATE TABLE + tags + -1 seed (one per dim)
│   │   │   ├── ddl_fact_{name_a}.sql    # CREATE TABLE + tags + CHECK (one per fact)
│   │   │   └── ddl_bridge_{a}_{b}.sql   # CREATE TABLE + tags + -1 seed (one per bridge)
│   │   ├── transformations/             # Load NOTEBOOKS — declare own widgets, hold the MERGE
│   │   │   ├── dim_{entity_a}           # ← extension-less notebook; what the DAB DAILY job runs
│   │   │   ├── fact_{name_a}
│   │   │   └── bridge_{a}_{b}
│   │   └── validate_silver              # Recurring DQ gate for ALL silver entities (notebook)
│   ├── gold/
│   │   ├── ddl/
│   │   │   └── ddl_{business_name_a}.sql  # CREATE TABLE + tags (one per gold table)
│   │   ├── transformations/
│   │   │   └── {business_name_a}        # INSERT OVERWRITE load notebook (declares own widgets)
│   │   └── validate_gold                # Recurring DQ gate for ALL gold entities
│   └── README.md                        # Optional: notes on load order, dependencies
├── resources/
│   └── {job_name}.job.yml               # DAB DAILY job (load notebooks + validation)
├── databricks.yml                      # DAB bundle config
├── gap_analysis.md
└── data_quality_assessment.md
```

### Key Structural Rules

1. **One load notebook per table** — every `dim_*`, `fact_*`, `bridge_*`, and gold table gets a single load notebook (`transformations/{entity}`) that declares its own widgets and holds the MERGE. Never combine multiple entities into a single notebook.
2. **Layer subfolders** — `src/{silver,gold}/{ddl/, transformations/}`. `src/silver/` and `src/gold/` separate layers; `ddl/` and `transformations/` separate DDL from loads. If only building one layer, only that layer's subfolder tree exists.
3. **DDL in a nested `ddl/` subfolder** — plain `.sql` files. DDL runs once (or is idempotent via `CREATE TABLE IF NOT EXISTS`) as a setup job; loads run on schedule.
4. **The load notebook declares its own widgets and holds the MERGE.** The daily job runs it directly via `notebook_task` + `base_parameters`. See "Notebook-format contract" below.
5. **One validation notebook per layer** — `validate_silver` checks ALL silver entities; `validate_gold` checks ALL gold entities. These are the final tasks in the daily job.
6. **DDL always starts with `-- Databricks notebook source`** (always SQL). Load notebooks and validation start with the first line for their `etl_language` shape — `-- Databricks notebook source` (SQL) or `# Databricks notebook source` (Python). Without the correct header the file is a plain file and cannot run as a notebook. See "Notebook-format contract".
7. **Header** — every load notebook and validation notebook declares `CREATE WIDGET` for each param, then `USE CATALOG/SCHEMA IDENTIFIER(:...)` in its own cells. **DDL** uses the same pattern. Catalog/schema are NEVER hard-coded; the daily job's `base_parameters` feed the widgets.

---

## Runtime Parameters (the promotion contract)

**Catalog/schema are runtime parameters passed by the job, NOT literals baked into notebooks.**
This is what lets the SAME notebook objects promote dev→prod unchanged. The chain runs directly
through the load notebook's own widgets:

```
conventions.yml (defaults) → DAB variables (per-target) → daily-job base_parameters
   → LOAD NOTEBOOK widgets → USE CATALOG/SCHEMA IDENTIFIER(:silver_catalog) + IDENTIFIER(:src_* || '.tbl')
```

- **`variables`** in `databricks.yml` declare every catalog/schema and per-source bronze prefix,
  with a **per-target override** so `dev` and `prod` write to different places.
- **`base_parameters`** on each task pass the variables into the **load notebook's** widgets.
- The **load notebook** sets its session `USE CATALOG/SCHEMA IDENTIFIER(:silver_catalog)` from the
  widgets and reads bronze via `IDENTIFIER(:src_{logical} || '.{table}')` (see
  `merge-and-defensive-coding.md` "Notebook Format").

Promotion is then `databricks bundle deploy -t prod` — no notebook edits, no find-replace.

> **`vibe_model.*` is NOT part of this runtime chain.** The vibe model location
> (`conventions.yml` → `vibe_model.catalog`/`vibe_model.schema`) is read at **authoring time**
> only — during assessment and DDL/spec generation, to learn the model's structure. It is NOT a
> DAB `variable`, NOT a `base_parameters` entry, and NOT a load-notebook widget. Generated
> notebooks never reference it at run time; they write to `silver_catalog`/`silver_schema`. Do
> not add `vibe_model_catalog`/`vibe_model_schema` to `databricks.yml` variables or task
> `base_parameters`. (The Kickoff notebook may capture them as authoring defaults, but they stop
> there.) See `SKILL.md` "Layering Contract" and `discovery-and-gap-analysis.md` Step 0.

### Kickoff notebook — parameter widgets (defaults that seed conventions.yml + DAB variables)

```python
# NOTE: catalog/schema are RUNTIME PARAMETERS. The Kickoff notebook captures the
# DEFAULTS (which seed conventions.yml + DAB variables); the generated ETL/DDL/
# validation notebooks each declare their OWN widgets and read values passed by the
# job's base_parameters at run time — nothing is baked in. See deployment-and-dab.md.
#
# Source (bronze) configuration — a domain reads MANY bronze schemas, sometimes across
# different catalogs. These map to conventions.yml `bronze_sources` (logical name →
# catalog.schema). Do NOT collapse to one source_catalog/source_schema pair.
dbutils.widgets.text("bronze_sources", "", "Bronze sources (logical=catalog.schema, comma-sep)")
# Vibe model (READ-ONLY target structure being graded — conventions.yml vibe_model.*).
# Captured as a default so discovery/gap analysis reads the model from here; the build
# LANDS built tables into the SEPARATE silver target below, never into these.
dbutils.widgets.text("vibe_model_catalog", "", "Vibe Model Catalog (read-only)")
dbutils.widgets.text("vibe_model_schema", "", "Vibe Model Schema (read-only)")
# Silver (dimensional model) LAND/WRITE target — distinct from the vibe model above
dbutils.widgets.text("silver_catalog", "", "Silver Catalog (land target)")
dbutils.widgets.text("silver_schema", "", "Silver Schema (land target)")
# Gold (use-case BI) target
dbutils.widgets.text("gold_catalog", "", "Gold Catalog")
dbutils.widgets.text("gold_schema", "", "Gold Schema")
# Sandbox (dev target catalog — dev DAB variable points silver/gold here)
dbutils.widgets.text("sandbox_catalog", "", "Sandbox (Dev) Catalog")
dbutils.widgets.dropdown("layer_type", "silver", ["silver", "gold", "both"], "Layer Type")
# Output model shape (THE shape knob — seeds conventions.yml output_model)
dbutils.widgets.dropdown("output_model", "dimensional", ["normalized", "dimensional", "hybrid"], "Output Model")
dbutils.widgets.dropdown("scd_strategy", "type_1", ["type_1", "type_2"], "SCD Strategy (dims)")
# Deployment configuration
dbutils.widgets.text("bundle_name", "", "DAB Bundle Name")
dbutils.widgets.text("job_name", "", "Job Name")
dbutils.widgets.text("job_schedule", "0 0 10 * * ? *", "Job Schedule (Quartz Cron)")
dbutils.widgets.text("job_timezone", "America/New_York", "Job Timezone")
dbutils.widgets.text("alert_email", "", "Failure Alert Email")
dbutils.widgets.text("workspace_path", "", "Output Workspace Path")
# Strategy defaults
dbutils.widgets.dropdown("merge_strategy", "auto", ["auto", "MERGE", "INSERT_OVERWRITE", "APPEND"], "Merge Strategy")
dbutils.widgets.dropdown("surrogate_key_method", "auto", ["auto", "SHA2", "NONE"], "Surrogate Key Method")
# auto -> resolve from output_model: dimensional/hybrid-gold=SHA2, normalized/hybrid-silver=NONE
```

---

## Widgets carry the runtime parameters (no `%run`, no session-variable bridge)

The load notebook declares its own widgets and the daily job feeds them via `base_parameters`.
There is no runner and no `%run`, so a widget-based notebook is exactly what runs — the parameter
markers (`:silver_catalog`, `:src_* `) bind directly from the job's `base_parameters`.

- `CREATE WIDGET TEXT silver_catalog DEFAULT ''` (SQL) / `dbutils.widgets.text("silver_catalog", "")`
  (Python) declares each param; the DAB task's `base_parameters` supply the values.
- Reference them with the `:name` marker inside `IDENTIFIER(:silver_catalog)` /
  `IDENTIFIER(:src_{logical} || '.tbl')`.
- An empty widget DEFAULT means a mis-wired task fails fast (`IDENTIFIER('')` errors) rather than
  silently writing to the wrong place.

> **Runtime requirement: DBR 13.3 LTS+.** The `IDENTIFIER()` clause with parameter markers
> (`IDENTIFIER(:silver_catalog)`, `IDENTIFIER(:src || '.tbl')`) requires Databricks Runtime
> 13.3 LTS or later. The default serverless compute this skill targets satisfies it — only a
> concern if someone pins an older classic cluster (don't). On first use, smoke-test the chain
> once on the target workspace: a one-cell notebook with `USE CATALOG IDENTIFIER(:c)` run from a
> job that passes `c` via `base_parameters`, to confirm widget→`:name` binding on that runtime.

---

## Notebook-format contract

Every load / validation notebook is one of two shapes, selected by `conventions.yml`
`etl_language`. **DDL is always the SQL shape** regardless of this setting; so are the Model Guide
and Genie/dashboard config. Within a shape, the **load notebook declares its own widgets** and
holds the MERGE. This section is the single source of truth; other reference files point here
rather than restating it.

### Shape A — `etl_language: sql` (default)

- First line: `-- Databricks notebook source`; cell separator `-- COMMAND ----------`; markdown `-- %md`.
- **Load notebook** — declares its own widgets, sets the session, holds the MERGE:

```sql
-- Databricks notebook source
-- Load notebook: dim_plant — declares its own widgets, holds the MERGE. Run directly by the DAB job.
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';
CREATE WIDGET TEXT src_orcy_wip   DEFAULT '';   -- one per bronze source this notebook reads
CREATE WIDGET TEXT job_name       DEFAULT '';
-- COMMAND ----------
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);
-- COMMAND ----------
MERGE INTO dim_plant AS tgt
USING (SELECT ... FROM IDENTIFIER(:src_orcy_wip || '.tbl')) AS src
ON tgt.Plant_Bk = src.Plant_Bk
WHEN MATCHED THEN UPDATE SET ...      -- explicit column list (never SET *)
WHEN NOT MATCHED THEN INSERT ...;
```

### Shape B — `etl_language: python`

- First line: `# Databricks notebook source`; cell separator `# COMMAND ----------`; markdown `# MAGIC %md`.
- **Load notebook** — reads its widgets and runs the MERGE via `spark.sql(f"...")`, interpolating the
  catalog/schema/source names directly (no `IDENTIFIER()`):

```python
# Databricks notebook source
# Load notebook: dim_plant — declares its own widgets, holds the MERGE. Run directly by the DAB job.
for v in ["silver_catalog", "silver_schema", "src_orcy_wip", "job_name"]:
    dbutils.widgets.text(v, "")
cat = dbutils.widgets.get("silver_catalog"); sch = dbutils.widgets.get("silver_schema")
src_orcy_wip = dbutils.widgets.get("src_orcy_wip"); job_name = dbutils.widgets.get("job_name")
# COMMAND ----------
spark.sql(f"USE CATALOG {cat}")
spark.sql(f"USE SCHEMA  {sch}")
# COMMAND ----------
spark.sql(f"""
  MERGE INTO dim_plant AS tgt
  USING (SELECT ... FROM {src_orcy_wip}.tbl) AS src
  ON tgt.Plant_Bk = src.Plant_Bk
  WHEN MATCHED THEN UPDATE SET ...
  WHEN NOT MATCHED THEN INSERT ...
""")
```

> **Why interpolation, not `IDENTIFIER(:param)`.** `:param` markers auto-bind in a SQL notebook cell
> (Shape A) but NOT inside `spark.sql("...")` in Python — that raises `UNBOUND_SQL_PARAMETER`. The
> Python shape uses the normal Databricks idiom: read the widget, interpolate the name.
>
> **Safety — Python shape.** Interpolate ONLY config-sourced values (conventions.yml → DAB variables
> → job `base_parameters` → widgets). NEVER interpolate analyst/free-text input into `spark.sql(f"...")`.
> An empty widget DEFAULT fails fast (`USE CATALOG ` with a blank name errors) rather than writing
> to the wrong place.
>
> **Brace escaping (only after substitution):** the authoring-time `{placeholder}` metavariables
> (`{entity}`, `{bk}`, …) are substituted with real names FIRST. Only a genuine literal `{`/`}`
> that must survive to runtime in the resulting SQL (e.g. a Spark complex-type / map / struct
> literal) is doubled to `{{`/`}}` inside the f-string.

### Choosing the shape

Read `etl_language` from `conventions.yml`. `sql` (or unset) → Shape A. `python` → Shape B.
Load and validation notebooks use the SAME shape. DDL, Model Guide, Genie/dashboard: SQL always.

---

## databricks.yml Template

```yaml
bundle:
  name: {bundle_name}

include:
  - resources/*.yml

# Runtime params — declared once, overridden per target. Values are the DEFAULTS
# from conventions.yml (catalogs/schemas + bronze_sources). Declare a variable for
# every catalog/schema and every bronze source ANY notebook in the bundle reads.
variables:
  silver_catalog: { default: "{silver_catalog}" }
  silver_schema:  { default: "{silver_schema}" }
  gold_catalog:   { default: "{gold_catalog}" }
  gold_schema:    { default: "{gold_schema}" }
  # One per bronze source (name = conventions.yml bronze_sources key, value = catalog.schema):
  src_dff:        { default: "cat_bi_bronze_prod.dff_curated" }
  src_orcy_wip:   { default: "cat_bi_bronze_prod.orcy_wip_curated" }
  # ...add the rest this bundle actually reads

targets:
  dev:
    workspace:
      host: https://{workspace_host}
    # dev writes to the sandbox catalog; sources usually stay on prod bronze
    variables:
      silver_catalog: "{sandbox_catalog}"
      gold_catalog:   "{sandbox_catalog}"
  prod:
    workspace:
      host: https://{workspace_host}
    variables:
      silver_catalog: "{silver_catalog}"   # e.g. cat_bi_silver_prod
      gold_catalog:   "{gold_catalog}"     # e.g. cat_bi_gold_prod
```

**Notes:**
- `bundle_name` follows the pattern `{subject_area}_{layer}[_{suffix}]` (e.g., `hr_silver_gold`, `manufacturing_silver_enhancements`)
- Both `dev` and `prod` targets point to the same workspace host unless the user specifies otherwise
- For Azure Databricks: `https://adb-{workspace_id}.{region}.azuredatabricks.net`
- **Per-target `variables:` blocks are the promotion knob** — dev points silver/gold at the
  sandbox catalog, prod at the prod catalogs. Add source overrides here too if dev reads from
  a different bronze (rare — bronze is usually shared prod).

---

## Job YAML Template

**resources/{job_name}.job.yml:**

```yaml
resources:
  jobs:
    {job_name}:
      name: {job_name}
      schedule:
        quartz_cron_expression: "{job_schedule}"
        timezone_id: "{job_timezone}"
        pause_status: PAUSED
      email_notifications:
        on_failure:
          - "{alert_email}"
      max_concurrent_runs: 1
      # Serverless jobs MUST declare the 'default' environment their tasks reference,
      # or `jobs/create` 400s ("Job environment 'default' ... not defined in field
      # 'environments'"). See "Serverless jobs REQUIRE a job-level environments block".
      # Omit this block ONLY if the job is pinned to classic job_clusters.
      environments:
        - environment_key: default
          spec:
            client: "1"
      tasks:
        # ─── NOTE: DDL is NOT in this daily job. Tables/constraints are created
        #     as one-time setup (run directly by Genie Code, or via a separate
        #     {domain}_ddl_setup bundle job). The daily job starts at the dims.
        #     See "DDL is SETUP, not a recurring load task" below. ────────────

        # ─── Tier 0: Dimensions (no dependencies — tables already exist) ─────
        # notebook_path points at the LOAD NOTEBOOK directly (it declares its own
        # widgets and takes base_parameters). Pass the TARGET params every task needs
        # plus the src_* prefixes THIS notebook reads (from discovery). job_name →
        # the run's own job name.
        - task_key: dim_{entity_a}
          notebook_task:
            notebook_path: ../src/silver/transformations/dim_{entity_a}
            base_parameters:
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}
              src_{logical_a}: ${var.src_{logical_a}}   # only the source(s) this notebook reads
              job_name: "{{job.name}}"

        - task_key: dim_{entity_b}
          notebook_task:
            notebook_path: ../src/silver/transformations/dim_{entity_b}
            base_parameters:
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}
              src_{logical_b}: ${var.src_{logical_b}}
              job_name: "{{job.name}}"

        # ─── Tier 1: Facts (depend on dimensions) ────────────────────────
        # A fact that joins several bronze schemas passes MULTIPLE src_* prefixes —
        # this is the multi-source case: one prefix per logical source, each carrying
        # its own catalog, so cross-catalog joins need no special handling.
        - task_key: fact_{name_a}
          depends_on:
            - task_key: dim_{entity_a}
            - task_key: dim_{entity_b}
          notebook_task:
            notebook_path: ../src/silver/transformations/fact_{name_a}
            base_parameters:
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}
              src_{logical_a}: ${var.src_{logical_a}}
              src_{logical_c}: ${var.src_{logical_c}}   # e.g. joins DFF + WIP → two prefixes
              job_name: "{{job.name}}"

        - task_key: fact_{name_b}
          depends_on:
            - task_key: dim_{entity_a}
          notebook_task:
            notebook_path: ../src/silver/transformations/fact_{name_b}
            base_parameters:
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}
              src_{logical_a}: ${var.src_{logical_a}}
              job_name: "{{job.name}}"

        # ─── Silver Validation (depends on ALL silver loads) ─────────────
        - task_key: validate_silver
          depends_on:
            - task_key: fact_{name_a}
            - task_key: fact_{name_b}
          notebook_task:
            notebook_path: ../src/silver/validate_silver
            base_parameters:
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}

        # ─── Gold DDL is also SETUP — not in the daily job (see silver note) ─

        # ─── Tier 2: Gold tables (depend on silver validation passing) ───
        # Gold WRITES gold, READS silver → pass both target sets (see gold template).
        - task_key: gold_{business_name_a}
          depends_on:
            - task_key: validate_silver
          notebook_task:
            notebook_path: ../src/gold/transformations/{business_name_a}
            base_parameters:
              gold_catalog:   ${var.gold_catalog}
              gold_schema:    ${var.gold_schema}
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}
              job_name: "{{job.name}}"

        - task_key: gold_{business_name_b}
          depends_on:
            - task_key: validate_silver
          notebook_task:
            notebook_path: ../src/gold/transformations/{business_name_b}
            base_parameters:
              gold_catalog:   ${var.gold_catalog}
              gold_schema:    ${var.gold_schema}
              silver_catalog: ${var.silver_catalog}
              silver_schema:  ${var.silver_schema}
              job_name: "{{job.name}}"

        # ─── Gold Validation (depends on ALL gold loads) ─────────────────
        - task_key: validate_gold
          depends_on:
            - task_key: gold_{business_name_a}
            - task_key: gold_{business_name_b}
          notebook_task:
            notebook_path: ../src/gold/validate_gold
            base_parameters:
              gold_catalog: ${var.gold_catalog}
              gold_schema:  ${var.gold_schema}
```

> **Every task passes `base_parameters`.** A task with no params would fall back to the load
> notebook's widget DEFAULTs (blank), and `USE CATALOG IDENTIFIER('')` fails fast — which is the
> desired behavior (a mis-wired task errors loudly rather than silently writing to the wrong
> place). Keep the per-task `src_*` list to exactly what that notebook reads; discovery (Phase 1)
> records this per entity.
>
> **Validation notebooks (`validate_silver`/`validate_gold`) work the same way** — `notebook_path`
> points straight at `../src/silver/validate_silver`; the task's `base_parameters` feed its own widgets.

---

### Pipeline resource (etl_type: sdp_pipeline)

When `conventions.yml` `etl_type: sdp_pipeline`, the bundle emits a `pipeline` resource **plus a thin
scheduler `job`** (a single `pipeline_task` that triggers the triggered pipeline on the daily cadence
— a `continuous: false` pipeline has no schedule of its own) instead of the MERGE path's per-notebook
daily job. The full template + wiring lives in `sdp-deployment.md`. Key deploy-doc points:

- **`channel: PREVIEW` + `continuous: false`** (triggered) — a sane dev default (NOT for unit
  testing; the LDP test framework is beta + Editor-only and is not used — see `sdp-pipeline-development.md`).
- **NO parameterization — bronze paths are hardcoded literals.** Do NOT emit a `parameters:` block,
  `:param` markers, or `base_parameters` widgets for bronze paths (the native `parameters:` block is
  a half-working beta — see `sdp-pipeline-development.md` "Parameterization — NONE"). Only the silver
  write target (`catalog:`/`schema:`) varies per target, via DAB `${var}`.
- **DDL is NOT a task** here either — but for a different reason than the MERGE path: there is no
  separate DDL step at all; schema is inline in each declarative object.
- **Declarative sources live under `src/silver/pipeline/`** (plain `.sql`, one per entity), pulled in
  via a `libraries: [glob: {include: ../src/silver/pipeline/**}]` entry — the SDP equivalent of the
  merge-mode `transformations/` folder.
- 🔴 **Scope the pipeline to the PROJECT root, not the workspace/repo root.** Author sources into the
  project's `src/silver/pipeline/` (and `src/gold/pipeline/` for hybrid), and set `root_path: ..` (the
  project root — the folder holding `databricks.yml`) so the pipeline's root folder is the whole
  project and the editor exposes it for Genie Code to edit, while `libraries` globs keep the *running*
  graph scoped to `src/*/pipeline/**`. `root_path` must resolve to the project root — never the
  workspace root. Verify placement after creating the sources; a file at the root is a placement bug
  (see `sdp-deployment.md`).
- **Deploy is environment-routed identically:** serverless → author + `bundle validate` + hand off to
  the Deployments panel (🚀); terminal/CI → `databricks bundle deploy` then trigger the pipeline update.

---

## Key DAB Rules

### Path References
- `notebook_path` is **RELATIVE to the YAML file location** (the `resources/` folder), so paths start with `../src/silver/` or `../src/gold/`
- **The daily job references the load notebooks directly** (each declares its own widgets and takes `base_parameters`). Notebook objects are extension-less. Examples:
  - daily-load task: `../src/silver/transformations/dim_employee`
  - gold daily-load task: `../src/gold/transformations/hr_headcount_monthly`
  - validation task: `../src/silver/validate_silver`
  - setup-job DDL path (plain `.sql`, extension omitted): `../src/silver/ddl/ddl_dim_employee`

### Compute
- Omitting `job_clusters` and `existing_cluster_id` defaults to **serverless**
- Serverless is the default and preferred compute for ETL notebooks
- Only specify a cluster if the user explicitly requires one

#### Serverless jobs REQUIRE a job-level `environments:` block (deploy fails without it)

**Every serverless job must declare a job-level `environments:` block, or the deploy fails at
`jobs/create` with a 400.** On serverless, each task implicitly runs under the environment
`environment_key: default`; if that key is not defined in the job's `environments` field, the
create call is rejected:

```
API error_code: INVALID_PARAMETER_VALUE
API message: Job environment 'default' used by task dim_customer is not defined in field 'environments'.
```

Add this block to **every serverless job** in this bundle (daily-load job and any setup job) — it
is a sibling of `tasks:`, at the job level. This is verified from a real deploy
failure on the field_service run:

```yaml
resources:
  jobs:
    {job_name}:
      name: {job_name}
      # ... schedule / notifications / max_concurrent_runs ...
      environments:
        - environment_key: default
          spec:
            client: "1"        # serverless environment version (a string, quoted)
      tasks:
        # ... tasks reference environment_key: default implicitly on serverless ...
```

- `client: "1"` selects the serverless environment version — keep it a **quoted string**, not an int.
- Only serverless jobs need this. A job pinned to `job_clusters` / `existing_cluster_id` (classic
  compute) must NOT carry an `environments:` block — it has no environment to reference.
- If you add per-task library dependencies later, they go under `spec.dependencies:` in this same
  block; `client` alone is the minimal valid spec.

### Schedule
- `pause_status: PAUSED` means the schedule will NOT fire automatically
- Change to `UNPAUSED` when ready for production
- Default schedule: `0 0 10 * * ? *` (daily at 10:00 AM)
- Default timezone: `America/New_York`

### Task Dependencies
- Use `depends_on` to enforce load order
- **DDL is NOT a task in the daily job** — tables exist already (created as setup). The DAG
  starts at Tier 0 dims.
- Tier 0 dims have no dependencies (tables already exist), run in parallel with each other
- Tier 1 facts depend on the dims they reference
- Silver validation depends on ALL silver loads
- Tier 2 gold depends on silver validation passing
- Gold validation depends on ALL gold loads

### Task Key Naming
- Use the entity name as the task key: `dim_employee`, `fact_headcount`
- DDL is not in the daily job; if you make a separate setup job, name it `{domain}_ddl_setup`
- For validation: `validate_silver`, `validate_gold`
- For gold: `gold_{business_name}` or just `{business_name}`

---

## Phase Gating Sequence

1. **Scaffold** one load notebook per entity into `src/{layer}/transformations/` (Phase 4)
2. **Create tables** — run the DDL notebooks once as setup (directly via Genie Code, or a
   separate `{domain}_ddl_setup` bundle job). This is not the daily job.
3. **Load + grade** each entity: run the real load in dependency order, run post-load DQ on the
   real table + the twice-run idempotency recheck → iterate to Grade A (Phase 5)
4. **Only after all pass — AUTHOR the bundle:** Generate `databricks.yml` +
   `resources/{job_name}.job.yml` (daily job: load notebooks + validation, no DDL) (Phase 6).
   *In `sdp_pipeline` mode instead emit `resources/{domain}_silver_pipeline.yml` holding **both** the
   `pipeline` and its scheduler `job` (the `pipeline_task` that drives the daily cadence) — see
   `sdp-deployment.md`.* The `databricks.yml` `include: [resources/*.yml]` glob picks up whichever
   resource files you write, so the pipeline + scheduler job in one file are both bundled.
   **After writing any DAB YAML, read it back and confirm it is non-empty and parses** before
   treating the phase as done — a silent empty-file write is a recurring hazard that only surfaces
   (by luck) at deploy time.
5. **Detect the environment (Step 0), then route the deploy** — see "Deploy is environment-routed"
   above. Serverless → author/validate + hand off to the Deployments panel (🚀). Terminal → run the
   deploy commands below.
6. **Verify** — after deploy (or after the user deploys), confirm the job actually exists and
   inspect it (`manage_jobs` / list). **Never report success off the deploy command alone.**
7. **Run** the full daily job as an end-to-end integration test (Phase 7)
8. **If integration test reveals cross-notebook issues** (FK timing, race conditions): fix and re-run

### The validate → fix → re-validate loop (safe to iterate; deploy is NOT)

Iterate here freely — this loop is productive and safe:

```
bundle validate → read the actual error text → fix the YAML → re-validate
```

On a **deploy** error, **diagnose the real error and fix config — do not blindly retry.** Common
real errors to handle explicitly rather than route around:
- missing job permissions (`does not have ... permissions on job`)
- invalid `user_api_scopes`
- unrestricted-cluster-creation needs

### Deploy Commands (terminal environments ONLY — see Step 0)

**Run these only in a web terminal (x86) or local/CI — never subprocessed from serverless compute.**
On serverless, deploy is a handoff to the Deployments panel (🚀), not a command you run.

```bash
# Validate bundle configuration (safe to run/iterate wherever the CLI is available)
databricks bundle validate

# Deploy to dev target
databricks bundle deploy -t dev

# Run the job
databricks bundle run {job_name}

# Deploy to production (when ready)
databricks bundle deploy -t prod
```

---

## Notebook Deployment Rules

- Notebooks are deployed **exclusively** via DABs — not via the workspace API or UI drag-and-drop
- **One load notebook per table** — never combine multiple entities into one file
- Load notebooks and validation are **extension-less notebook objects** (first line `-- Databricks notebook source` or `# Databricks notebook source`); DDL is a `.sql` file
- This format enables execution as a `notebook_task` on **serverless Jobs compute** without a SQL warehouse
- Do NOT use `sql_task.file` — that requires a SQL warehouse
- Organize into `src/{silver,gold}/{ddl,transformations}/` — never mix layers or roles

### Two authoring workflows → two `notebook_path` shapes

**The `notebook_path` you write depends on how the notebooks got authored.** Genie Code commonly
authors notebooks **directly as workspace objects via MCP** as it builds — in that case there are no
local `src/**` source files for a deploy to upload, and the relative `../src/...` upload model does
not apply. Know which workflow you are in before writing the job YAML:

| Workflow | How notebooks exist | `notebook_path` in the job YAML |
| --- | --- | --- |
| **(A) Local-file authoring** | `src/**` source files on disk; the deploy uploads them | **Relative** — `../src/silver/transformations/{entity}` (resolved relative to the `resources/` YAML). The deploy converts extension-less sources → notebook objects. |
| **(B) Workspace-object authoring** (Genie Code's common mode) | notebooks already live in the workspace (authored via MCP); nothing local to upload | Reference the **existing workspace objects** — either sync the source root so `../src/...` resolves, or point at the absolute workspace path where the objects live. |

Pick one and be consistent across the whole bundle. Do NOT silently mix relative and absolute paths
task-by-task — that is the symptom of improvising around a failed deploy rather than choosing a
workflow. If you are in workflow (B) on serverless, the deploy itself is a Deployments-panel handoff
(Step 0), not a CLI upload.

### Source files → notebook objects: DAB deploy handles this (workflow A)

**A workspace FILE is NOT a notebook.** Databricks Jobs `notebook_task` can ONLY act on
notebook objects — NOT plain workspace files. **In workflow (A) the DAB deploy resolves this for
you:** when `databricks bundle deploy` uploads a `src/**` source referenced by a `notebook_task`,
it lands it as an executable **notebook object**. You do not create the notebooks yourself. (In
workflow (B) the objects already exist — reference them per the table above.)

**Requirements that make the DAB deploy produce notebooks (not files):**
- Every load-notebook file's first line is the notebook-source header
  (`-- Databricks notebook source` for SQL, `# Databricks notebook source` for Python) and the
  file has **no extension** — the header, not an extension, marks it as notebook source.
- The `notebook_path` in the job YAML references the load notebook (extension-less), e.g.
  `../src/silver/transformations/dim_plant`.
- Cells are separated with `-- COMMAND ----------` / `# COMMAND ----------`.

If a `notebook_task` fails with "is not a notebook," the fix is one of the requirements
above (usually a stray `.sql`/`.py` extension on a load notebook) — **not** hand-importing
via the SDK, and **not** switching to an imperative orchestrator.

> **"Silent twin" anti-pattern (Rule 10).** A stray `.sql` file placed alongside the
> extension-less load notebook in `transformations/` (e.g. `dim_plant` and `dim_plant.sql`
> both present) causes the `notebook_task` to fail — the file is not a notebook. This was
> the root cause of the first Meridian build failure. Remove any extension files from
> `transformations/`; `ddl/` is the only folder that should hold `.sql` files.

#### Interactive-only fallback (NOT for job deploy)

*Only* when you need a notebook created **for interactive/local use outside the bundle** (e.g.
poking at one notebook manually), the workspace import API can create one directly. This is a
fallback for interactive work — the job's notebooks always come from `databricks bundle deploy`:

> **Language-aware:** the snippet below is the SQL path (`etl_language: sql`). For
> `etl_language: python`, import with `language=Language.PYTHON`, use
> `notebook_source = "# Databricks notebook source\n"`, `# COMMAND ----------` separators, and
> emit each statement as a `spark.sql(f"...")` cell per Shape B. DDL always uses the SQL path.

```python
# INTERACTIVE FALLBACK ONLY — the DAB deploy is the deploy path for jobs.
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat, Language
import base64

w = WorkspaceClient()
with open(file_path) as f:
    content = f.read()
w.workspace.import_(                       # path WITHOUT extension (load notebook)
    path="/Workspace/.../src/silver/transformations/dim_entity",
    content=base64.b64encode(content.encode()).decode(),
    format=ImportFormat.SOURCE, language=Language.SQL, overwrite=True,
)
```

Do NOT wrap this in a loop over all entities plus a `w.jobs.reset(job_id=...)` to stand up the
job — that is the orchestrator anti-pattern. Deploy the job with `databricks bundle deploy`.

### Multi-Statement SQL Notebooks (DDL)

SQL notebooks support ONE statement per cell. For DDL files with multiple statements
(CREATE TABLE + ALTER TABLE tags + ALTER TABLE constraints), separate them with:

```sql
-- Databricks notebook source
CREATE TABLE IF NOT EXISTS ...

-- COMMAND ----------

ALTER TABLE ... SET TAGS (...)

-- COMMAND ----------

ALTER TABLE ... ADD CONSTRAINT ...
```

When programmatically converting multi-statement `.sql` files to notebooks:

> **Language-aware:** the snippet below is the SQL path (`etl_language: sql`). For
> `etl_language: python`, import with `language=Language.PYTHON`, use
> `notebook_source = "# Databricks notebook source\n"`, `# COMMAND ----------` separators, and
> emit each statement as a `spark.sql(f"...")` cell per Shape B. DDL always uses the SQL path.

```python
# Split on semicolons, rejoin with cell separators
statements = [s.strip() for s in content.split(";") if s.strip() and not_only_comments(s)]
notebook_source = "-- Databricks notebook source\n"
for i, stmt in enumerate(statements):
    notebook_source += stmt
    if i < len(statements) - 1:
        notebook_source += "\n\n-- COMMAND ----------\n\n"
```

### DDL is SETUP, not a recurring load task — keep it OUT of the daily job

DDL creates tables + constraints + tags; it is **one-time setup**, not something the daily load
job should re-run. `ADD CONSTRAINT` also fails with `DELTA_CONSTRAINT_ALREADY_EXISTS` on re-run,
so bundling it into the recurring job just creates idempotency headaches. **Do not put DDL tasks
in the daily load job.** Choose one of:

1. **Run DDL directly with Genie Code at build time (preferred for setup).** During Phase 2,
   after DDL is approved, Genie Code executes the DDL notebooks once (via `executeCode` /
   `runNotebookCells`) to create the tables. This is a setup action, not a scheduled load — it's
   fine to run it directly. Re-run only when the schema changes.
2. **A separate one-time `{domain}_ddl_setup` DAB job.** Still deployed via
   `databricks bundle deploy` (DABs remain the deploy pattern), but as its OWN job, run manually
   on setup / schema change — never on the daily schedule. Keep it in `resources/` alongside the
   load job.

Either way, the **daily load job's task DAG starts at the dimensions, not DDL** (the Job YAML
template's NOTE comment marks where DDL used to sit — it is not a task in the daily job). This
keeps the recurring job to loads + validation, which is what should run on a schedule.

> This is still fully within the deploy pattern: DDL runs either as a direct Genie-Code setup
> action or as a separate bundle-deployed setup job. What you must NOT do is hand-roll an
> imperative orchestrator that imports notebooks and resets a job id (the anti-pattern above).

### MERGE Idempotency for Re-Runs

MERGE fails with `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE` if the
source CTE produces duplicate keys matching the same target row. This is silent on
first load (INSERT) but fails on subsequent runs (UPDATE attempt on same row from
multiple source rows).

**Fix:** Ensure the ROW_NUMBER() dedup PARTITION BY uses the EXACT same columns that
generate the surrogate key. If the PK = SHA2(col_a, col_b, col_c), then dedup must be:
`ROW_NUMBER() OVER (PARTITION BY col_a, col_b, col_c ORDER BY recency DESC)`.

This is exactly what the **Phase 5 idempotency recheck** catches — running the real load a second
time and asserting the row count + key set are stable (see `testing-and-grading.md` "Idempotency
recheck"). A second-run failure or row-count change means the dedup is wrong; fix the notebook.

---

## Job Naming Convention

Pattern: `{subject_area}_{purpose}`

| Example | Description |
| --- | --- |
| `hr_silver_gold_load` | HR domain, loads both silver and gold |
| `manufacturing_silver_daily` | Manufacturing domain, silver only, daily |
| `finance_gold_refresh` | Finance domain, gold layer refresh |
