# Model Genie Skills

*Take a generated vibe data model and form it to a customer's real data on Databricks — assess → build → validate → document, one domain at a time.*

## Summary

- **What it is** — a suite of **Genie Code skills** that take a generated **vibe data model** (a
  coherent, documented business model) and **form it to a customer's real data on Databricks**, one
  domain at a time, through a disciplined, phase-gated loop. Engineered stations with a human at the
  decision points, not a roaming agent.
- **The loop** — `domain-model-assessment` (assess) → `etl-development-framework` (build) →
  `domain-model-validation` (validate) → `domain-documentation` (document), with
  `autonomous-validation` governing execution discipline throughout and `domain-sync` keeping the
  model in sync after it's built.
- **Handoff is through documents, not chat** — `etl_detailed_spec.md` → `build_manifest.md` →
  `validation_summary.md`. Discovery runs once; everything downstream inherits it.
- **What you get** — a coherent, documented, validated **silver** layer, fast; the same skills
  accelerate the **gold/metrics** layer when there are existing KPIs to grade generated metrics
  against.

---

## Start here

**Prefer a picture?** The [workflow map](docs/developer/workflow.md) shows it in two diagrams:
**when to start** (from deploying the vibe-modeling app and settling a model in the app, through
deploying it to a catalog, into this suite's assess → build → validate → document loop) and the
**decision tree after the assessment** — how you close the gap between the model and your real
data before the build.

**New to the suite? Start at the [developer docs index](docs/developer/index.md)** — the landing
page for [`docs/developer/`](docs/developer/), a Diátaxis-style set on how a developer drives these
skills to build a data solution, and how the suite fits with the vibe model. It routes to the four
quadrants below:

| I want to… | Go to |
| --- | --- |
| **Learn the loop by running it** end-to-end on the Meridian `field_service` domain | [tutorial.md](docs/developer/tutorial.md) |
| **Do a specific task** — add a table, fix a grade, promote, investigate drift, re-sync | [how-to/](docs/developer/how-to/) |
| **Look something up** — skill catalog, handoff chain, `conventions.yml`, human gates | [reference.md](docs/developer/reference.md) |
| **Understand why it works this way** — the motion, the vibe-model fit, phase gates | [explanation.md](docs/developer/explanation.md) |

---

## The skills

| # | Skill | Station | What it does |
|---|-------|---------|--------------|
| 1 | `domain-model-assessment` | **Assess** | Inspects the empty target model, profiles bronze, folds in existing silver/gold, produces source-to-target mapping + gap registry + fit grades, and generates the build skill's handoff docs. Read-only. |
| 2 | `etl-development-framework` | **Build** | Turns the assessment handoff into pipelines: DDL (PK/FK/CHECK/comments/CLUSTER BY), Type-1 MERGE notebooks (or a Lakeflow Declarative Pipeline), a DQ validation notebook, and a DAB job. |
| 3 | `domain-model-validation` | **Validate** | Proves the load landed as intended (0 FK orphans, 0 dropped rows, no silent nulls), writes per-table narrative + regression notebooks, metadata tables, a scorecard, and a quality dashboard. |
| 4 | `domain-documentation` | **Document** | Diátaxis docs, a Model Guide notebook, and an auto-generated Genie space so the domain is queryable in natural language the moment it's built. |
| — | `autonomous-validation` | *(cross-cutting)* | Execution-discipline guidance for running at scale: scratchpad-validate → confirm → persist, batching discipline, human-in-the-loop contract. |
| — | `domain-sync` | *(steady-state)* | Keeps a built model's artifacts in sync after point updates: change→artifact impact matrix, staleness linter, scoped regeneration. |

Every loop station emits `docs/commentary/{skill}-improvement-recommendations.md` on completion
(protocol: `autonomous-validation/commentary-protocol.md`) — a per-run, self-improving feedback
artifact.

---

## Installing the skills

Genie Code discovers skills from a **`.assistant/skills/` directory**, at one of two scopes:

| Scope | Location | Who gets it |
| --- | --- | --- |
| **User** | `/Workspace/Users/<you>@databricks.com/.assistant/skills/` | just you |
| **Workspace** | `/Workspace/.assistant/skills/` | everyone in the workspace |

Install **all six skill folders together** into the location you want — each keeps its own folder,
and its `SKILL.md` + supporting files travel with it. They must stay **siblings in one directory**;
they cross-reference each other by sibling-relative path (see [Repo layout](#repo-layout) below).

```
/Workspace/.assistant/skills/          # or /Workspace/Users/<you>@databricks.com/.assistant/skills/
├── domain-model-assessment/
│   ├── SKILL.md
│   └── …supporting .md files + templates/
├── etl-development-framework/
├── domain-model-validation/
├── domain-documentation/
├── autonomous-validation/
└── domain-sync/
```

**Getting the files there** — clone this repo into a Databricks **Git folder** (*Create ▸ Git folder*
→ `https://github.com/stuart-swartz_data/vibe-model-skills.git`), then copy its `skills/*` into the
`.assistant/skills/` location above (import/upload works too — just keep each skill's folder intact).

**Registration is automatic.** Each `SKILL.md` carries the frontmatter Genie Code matches against
your request:

```yaml
---
name: domain-model-assessment
description: Assess a vibe/domain data model against a customer's real Databricks data …
---
```

Genie Code picks the skills up the next time you use it — no toggle to flip (after *editing* a skill,
start a new chat to apply the change). Invoke one by **`@`-mentioning it** (`@domain-model-assessment`)
or just describe the task and let Genie Code match it by relevance.

> **The shared assets are not skills** and do **not** go under `.assistant/skills/`:
> `templates/conventions.yml` (+ `conventions-variants/`) is the one file you fill in per domain —
> copy it into the working project where you run the loop; `examples/` is the reference/demo dataset,
> used from this repo.

---

## Configuration

Everything a customer/domain needs is set in a single `conventions.yml` (catalogs, naming,
source-system enum, load thresholds). Two orthogonal knobs shape the build:

- **`output_model`** — the model *shape*: `normalized` (3NF SSOT) · `dimensional` (Kimball star) ·
  `hybrid` (normalized silver → dimensional gold).
- **`etl_type`** — the build *mechanism*: `merge_notebook` (DDL + MERGE trio + job) ·
  `sdp_pipeline` (one whole-domain Lakeflow Declarative Pipeline).

See [`templates/conventions.yml`](templates/conventions.yml) for the fully-annotated base, and
[`templates/conventions-variants/`](templates/conventions-variants/README.md) for the six overlay
templates (the `etl_type` × `output_model` matrix).

---

## Try it: the Meridian demo

`examples/` is a portable, synthetic **Meridian Fluid Controls** dataset (a fictional
industrial-valve manufacturer) so you can run the loop without any customer data:

- **`setup/`** — stand up the shared synthetic bronze once: `data_generator/` (seeded Python package
  that generates the CSVs) + `ingest/` (the CTAS-from-`read_files` SQL).
- **`field_service/`** — a minimal 5-entity fast-loop domain with all six matched `conventions.yml`
  variants ([README](examples/field_service/README.md)). It's the domain the
  [tutorial](docs/developer/tutorial.md) runs on; [`EXAMPLE_OUTPUT.md`](examples/field_service/EXAMPLE_OUTPUT.md)
  shows the finished artifact tree a run produces.
- **`sales_order_mvm/`** — the realistic-scale counterpart: a 16-table `sales_order` model with a
  **committed real run** (assess→build→validate→document, silver — 17 tables, all Grade A) exercising
  all three `model_deviation` levers, cross-domain FK deferral, and SQL-reserved-word edge cases; the
  gold star is designed but not built ([README](examples/sales_order_mvm/README.md),
  [`EXAMPLE_OUTPUT.md`](examples/sales_order_mvm/EXAMPLE_OUTPUT.md)).

---

## Repo layout

```
skills/                          The six skills, each a folder (SKILL.md + supporting files)
templates/conventions.yml        Single config surface (catalogs, naming, thresholds)
templates/conventions-variants/  Six overlay templates — the etl_type × output_model matrix
examples/                        Synthetic bronze dataset + fast-loop domain (portable demo)
docs/developer/                  Diátaxis docs on using the suite
```

The six skills live under `skills/` here for tidiness, but they install **flat as siblings** in a
`.assistant/skills/` directory (see [Installing the skills](#installing-the-skills)) — functionally
identical. Every cross-reference *between* skills is **sibling-relative** (e.g.
`etl-development-framework/deployment-and-dab.md`), so it resolves in both layouts as long as the six
move together and stay siblings. Don't add or strip a `skills/` prefix on those paths; only
shared-asset references (`templates/…`, `examples/…`) are repo-root-relative.

---

## Versioning

The suite versions as **one unit** — the six skills reference each other with sibling-relative
paths and hand off through documents, so they ship together. Release history lives in
[`CHANGELOG.md`](CHANGELOG.md); releases follow [Semantic Versioning](https://semver.org/) driven
by [Conventional Commits](https://www.conventionalcommits.org/), cut with
[`scripts/release.sh`](scripts/release.sh).
