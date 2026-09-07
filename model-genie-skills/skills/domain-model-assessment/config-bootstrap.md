# Config Bootstrap — Phase −1

Interactive `conventions.yml` authoring guide. Run this before Phase 0 when the config file is
absent.

---

## 1. When this runs

**Phase −1.** If `conventions.yml` is absent at the output root, STOP and run this interactive
bootstrap before any assessment. If present, skip to Phase 0.

---

## 2. Principle

**Q&A-first.** Explain each knob in plain English as you ask. Offer read-only workspace probing,
but never require it. Do not begin Phase 0 until a `conventions.yml` is written and confirmed back
to the user.

---

## 3. The question script

Ask these questions in order. Read the explainer text to the user before each question.

### 3.1 Customer and domain

Ask for:
- `customer` — a short slug (e.g. `acme`, `bridgestone`).
- `domain` — the domain being assessed (e.g. `field_service`, `order_management`).

### 3.2 `output_model`

Read this explainer verbatim before asking:

> **normalized** = 3NF single-source-of-truth: one place for each fact, minimal duplication, you
> join for reporting. **dimensional** = Kimball star: `dim_`/`fact_` tables, denormalized for BI
> speed. **hybrid** = normalized 3NF silver first, then a dimensional gold star built downstream
> from it (layered, not both at once). Default: normalized.

Then ask: "Which output model do you want? (`normalized` / `dimensional` / `hybrid`)"

### 3.3 `etl_type`

Read this explainer verbatim before asking:

> **merge_notebook** = generated DDL + a Type-1 MERGE notebook trio + a daily job; explicit and
> easy to debug. **sdp_pipeline** = one declarative Lakeflow pipeline for the whole domain; less
> code, managed refresh. Default: sdp_pipeline.

Then ask: "Which ETL type? (`merge_notebook` / `sdp_pipeline`)"

### 3.4 Probe offer (opt-in)

Before collecting catalog and schema answers (3.5–3.6 below), offer this exactly:

> "Want me to probe the workspace (read-only) to locate your `vibe_metamodel_*` tables and list
> candidate bronze schemas, so you don't hand-type them? I won't change anything."

**On yes** → Run the Step 1.0 metamodel-locate queries from `discovery-protocol.md` plus an
`information_schema.schemata` / `.tables` scan of the bronze catalog. Proceed to 3.5–3.6 with
the discovered values pre-filled; present each and ask the user to CONFIRM or correct before
moving on.

**On no or unreachable** → Proceed to 3.5–3.6 as plain questions; do not retry the probe.

### 3.5 Vibe model location

If the user accepted the probe, present the discovered `vibe_metamodel_*` location for
confirmation. If they declined or the workspace was unreachable, ask for:

- `vibe_model.catalog` — the Unity Catalog catalog that holds the vibe model and its metamodel
  (READ-ONLY source; the skill never writes here).
- `vibe_model.schema` — the schema within that catalog where `vibe_metamodel_*` tables live.

### 3.6 Target catalogs

If the user accepted the probe, present the discovered candidate bronze schemas and any
identifiable silver/gold catalogs for confirmation. If they declined or the workspace was
unreachable, ask for:

- `catalogs.bronze` — the bronze source catalog (READ-ONLY for this skill).
- `catalogs.silver` — the silver WRITE target catalog.
- `catalogs.gold` — the gold catalog (may be the same as silver; leave blank if not yet
  determined).

### 3.7 Secondary / confirm-or-default

Present these as a single confirm-or-change block. State the default for each and ask the user
to change only what differs.

| Key | Default | Notes |
| --- | --- | --- |
| `etl_language` | `sql` | `sql` or `python` |
| `scd_strategy` | `type_1` | SCD strategy for MERGE notebooks (`type_1` \| `type_2`) |
| `load_strategy.full_merge_max_rows` | `5_000_000` | Row count at or below which full-merge is used |
| `load_strategy.incremental_max_rows` | `100_000_000` | Row count at or below which incremental merge is used; above this → escalate to SDP |
| `null_columns.disposition` | `keep` | `keep` \| `drop` |
| `model_deviation` block | all OFF (`preset: none`) | Deviation makes descoping explicit and recoverable. Defaults OFF; can also be enabled at the Completion Self-Audit gate at the end of the assessment (see SKILL.md Completion Self-Audit end-of-session surfacing). Keys: `preset`, `drop_null_columns`, `drop_unbuilt_domain_fks`, `drop_no_process_tables`, `allow_new_entities`. |

---

## 4. Writing the file

Once all questions are answered:

1. **Seed** from this skill's `templates/conventions.yml` — the basic, generic seed shipped
   *inside* the skill (skill-relative path: `domain-model-assessment/templates/conventions.yml`),
   so it resolves even when the skill is installed flat. Preserve its comments; do not strip them.
   Fill the `<PLACEHOLDER>` values from Section 3. (For a fully-worked reference, the repo-root
   `templates/conventions.yml` carries the Meridian example profile — repo-root assets are **not**
   shipped with the skill, so use the skill-local seed at bootstrap time.)
2. **Apply** the mode-specific overlay for keys specific to the chosen mode (e.g. SDP pipeline
   topology, dimensional naming) **when available**. These overlays live at the repo root under
   `templates/conventions-variants/{etl_type}.{output_model}.yml` and are reference material — they
   are **not** shipped inside the skill. If the repo root is reachable, apply the matching overlay;
   otherwise fill the mode-specific keys directly from the Section 3 answers (the basic seed already
   carries every core key with per-mode guidance in its comments).
3. **Fill** the values collected in Section 3 above.
4. **Write** the resolved file to the output root as `conventions.yml`.
5. **Echo** the full resolved config back to the user in a fenced YAML block and ask:
   "Does this look right? Confirm or edit before I start the assessment."
6. Only once the user confirms → proceed to Phase 0.
