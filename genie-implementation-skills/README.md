# vibe-model-skills

<!-- version -->**Version:** unreleased (pre-`v0.1.0`) — see [CHANGELOG.md](CHANGELOG.md)<!-- /version -->

A suite of **Genie Code skills** that take a generated **vibe data model** — a coherent,
documented business model — and **form it to a customer's real data on Databricks**, one domain at
a time, through a disciplined, phase-gated loop. Discovery, build, validation, and documentation
run as engineered stations with a human at the decision points, not a roaming agent.

The loop, in one line:

`domain-model-assessment` (assess) → `etl-development-framework` (build) →
`domain-model-validation` (validate) → `domain-documentation` (document) — with
`autonomous-validation` governing execution discipline throughout and `domain-sync` keeping the
model in sync after it's built. **Handoff between stations is through documents, not chat**
(`etl_detailed_spec.md` → `build_manifest.md` → `validation_summary.md`).

## Start here

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

## The skills

| # | Skill | Station | What it does |
|---|-------|---------|--------------|
| 1 | `domain-model-assessment` | **Assess** | Inspects the empty target model, profiles bronze, folds in existing silver/gold, produces source-to-target mapping + gap registry + fit grades, and generates the build skill's handoff docs. Read-only. |
| 2 | `etl-development-framework` | **Build** | Turns the assessment handoff into pipelines: DDL (PK/FK/CHECK/comments/CLUSTER BY), Type-1 MERGE notebooks (or a Lakeflow Declarative Pipeline), a DQ validation notebook, and a DAB job. |
| 3 | `domain-model-validation` | **Validate** | Proves the load landed as intended (0 FK orphans, 0 dropped rows, no silent nulls), writes per-table narrative + regression notebooks, metadata tables, a scorecard, and a quality dashboard. |
| 4 | `domain-documentation` | **Document** | Diátaxis docs, a Model Guide notebook, and an auto-generated Genie space so the domain is queryable in natural language the moment it's built. |
| — | `autonomous-validation` | *(cross-cutting)* | Execution-discipline guidance for running at scale: scratchpad-validate → confirm → persist, batching discipline, human-in-the-loop contract. |
| — | `domain-sync` | *(steady-state)* | Keeps a built model's artifacts in sync after point updates: change→artifact impact matrix, staleness linter, scoped regeneration. |

## Installing the skills

Genie Code discovers skills from a **`.assistant/skills/` directory**, at one of two scopes:

| Scope | Location | Who gets it |
| --- | --- | --- |
| **User** | `/Workspace/Users/<you>@databricks.com/.assistant/skills/` | just you |
| **Workspace** | `/Workspace/.assistant/skills/` | everyone in the workspace |

Install **all six skill folders together** into the location you want — each keeps its own folder,
and its `SKILL.md` + supporting files travel with it. They must stay **siblings in one directory**;
they cross-reference each other by sibling-relative path (see "Skills layout" below).

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

## Configuration — one file

Everything a customer/domain needs is set in a single `conventions.yml` (catalogs, naming,
source-system enum, load thresholds). Two orthogonal knobs shape the build:

- **`output_model`** — the model *shape*: `normalized` (3NF SSOT) · `dimensional` (Kimball star) ·
  `hybrid` (normalized silver → dimensional gold).
- **`etl_type`** — the build *mechanism*: `merge_notebook` (DDL + MERGE trio + job) ·
  `sdp_pipeline` (one whole-domain Lakeflow Declarative Pipeline).

See [`templates/conventions.yml`](templates/conventions.yml) for the fully-annotated base, and
[`templates/conventions-variants/`](templates/conventions-variants/README.md) for the six overlay
templates (the `etl_type` × `output_model` matrix).

## Try it — the Meridian demo

`examples/` is a portable, synthetic **Meridian Fluid Controls** dataset (a fictional
industrial-valve manufacturer) so you can run the loop without any customer data:

- `setup/` — stand up the shared synthetic bronze once: `setup/data_generator/` (seeded Python
  package that generates the CSVs) + `setup/ingest/` (the CTAS-from-`read_files` ingest SQL)
- `field_service/` — a minimal 5-entity fast-loop domain with all six matched `conventions.yml`
  variants (see its [README](examples/field_service/README.md)); it's the domain the
  [tutorial](docs/developer/tutorial.md) runs on, and
  [`EXAMPLE_OUTPUT.md`](examples/field_service/EXAMPLE_OUTPUT.md) illustrates the finished artifact
  tree a run produces
- `sales_order/` — the full 27-table counterpart to `field_service` (gold layer, cross-domain
  divergences, SQL-reserved-word edge cases): the same loop at the scale of a real customer model
  (see its [README](examples/sales_order/README.md))

## Repo layout

```
skills/                          The six skills (see "Skills layout" below)
templates/conventions.yml        Single config surface (catalogs, naming, thresholds)
templates/conventions-variants/  Six overlay templates — the etl_type × output_model matrix
examples/                        Synthetic bronze dataset + fast-loop domain (portable demo)
docs/developer/                  Diátaxis docs on using the suite
```

## Skills layout — IMPORTANT (read before moving skills)

In **this repo**, the skills live under `skills/` for tidiness:

```
skills/
├─ domain-model-assessment/     # station 1 — Assess
├─ etl-development-framework/    # station 2 — Build
├─ domain-model-validation/     # station 3 — Validate
├─ domain-documentation/        # station 4 — Document
├─ autonomous-validation/       # cross-cutting — execution discipline
└─ domain-sync/                 # steady-state — keep artifacts in sync after point fixes
```

**When installed for Genie Code, the six folders land flat as siblings in a `.assistant/skills/`
directory** (`/Workspace/.assistant/skills/` for the workspace, or
`/Workspace/Users/<you>@databricks.com/.assistant/skills/` for a user — see "Installing the skills"
above). That is functionally identical to how they sit under `skills/` here.

Every cross-reference *between* skills is **sibling-relative** (e.g.
`etl-development-framework/deployment-and-dab.md`), written relative to the skills' shared parent
directory, not the repo root. So it resolves in **both** layouts — as long as all six skills move
together and stay siblings. Do **not** rewrite these paths to add or strip a `skills/` prefix; a
hard-coded prefix would break in one layout or the other. The only **repo-root-relative** paths are
references to shared assets (`templates/conventions.yml`, `examples/…`), which are **not** installed
into `.assistant/skills/`.

## Versioning & releases

The suite is versioned as **one unit** — the six skills reference each other with sibling-relative
paths and hand off through documents, so they ship and version together. Releases follow
[Semantic Versioning](https://semver.org/), driven by [Conventional Commits](https://www.conventionalcommits.org/):

| Commit prefix | Bump | Meaning |
| --- | --- | --- |
| `feat!:` / `BREAKING CHANGE:` | **major** | Breaks a skill contract, the `conventions.yml` schema, or an inter-skill handoff doc — an in-flight model would need rework |
| `feat:` | **minor** | New skill, variant, or capability; backward-compatible |
| `fix:` / `docs:` / other | **patch** | Corrected or clarified guidance |

A release is a git tag `vX.Y.Z` on `main` plus a GitHub Release with the changelog notes and a
freshly built `skills.zip` attached. To cut one:

```bash
scripts/release.sh --dry-run     # preview the version + changelog, change nothing
scripts/release.sh               # auto-detect the bump from commits since the last tag
scripts/release.sh minor         # or force a bump …
scripts/release.sh 0.1.0         # … or pin an exact version
```

The script resolves the next version, regenerates [`CHANGELOG.md`](CHANGELOG.md), stamps
[`VERSION`](VERSION) and this README, rebuilds `skills.zip` (clean — no `.DS_Store`/`__MACOSX`),
commits `chore(release): vX.Y.Z`, tags, and — after a confirmation prompt — pushes and publishes
the GitHub Release. `skills.zip` is a build artifact (git-ignored); it lives only as a release
asset. The first tagged release will be **`v0.1.0`**.
