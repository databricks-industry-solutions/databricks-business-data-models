# `conventions.yml` variant templates — the etl_type × output_model matrix

`templates/conventions.yml` is the **single, fully-annotated base** — every knob, every rule,
every rationale. These variant templates are **thin overlays** on that base: each one shows only
the blocks that change for one cell of the two-knob matrix, so you can see at a glance exactly
what to set for a given build shape + mechanism. **Fill in the base's identifiers (customer,
catalogs, bronze sources, deployment) and then apply the matching overlay below.**

The two orthogonal knobs (see the base file's headers):

- **`output_model`** — the model *shape* the build makes FROM the read-only vibe model:
  `normalized` (3NF SSOT) · `dimensional` (Kimball star) · `hybrid` (normalized silver → dimensional gold).
- **`etl_type`** — the build *mechanism*: `merge_notebook` (DDL + Type-1 MERGE trio + daily job) ·
  `sdp_pipeline` (one whole-domain Lakeflow Declarative Pipeline).

They compose independently — 2 × 3 = **six** cells:

| | `output_model: normalized` | `output_model: dimensional` | `output_model: hybrid` |
|---|---|---|---|
| **`etl_type: merge_notebook`** | [`merge.normalized.yml`](merge.normalized.yml) | [`merge.dimensional.yml`](merge.dimensional.yml) | [`merge.hybrid.yml`](merge.hybrid.yml) |
| **`etl_type: sdp_pipeline`** | [`sdp.normalized.yml`](sdp.normalized.yml) *(the default cell)* | [`sdp.dimensional.yml`](sdp.dimensional.yml) | [`sdp.hybrid.yml`](sdp.hybrid.yml) |

A **worked, runnable instance** of all six against one real model lives in
`examples/field_service/conventions.field_service.*.yml` (the fast-loop bench domain) — read those
to see the matrix filled in with concrete Meridian identifiers and land schemas. These templates
are the customer-agnostic abstraction of that set.

## How the two knobs interact (the parts that trip people up)

- **`hybrid` is LAYERED, not both-at-once.** Normalized 3NF silver FIRST (the SSOT, follows the
  vibe model — natural PKs, no `dim_`/`fact_`, no surrogates), THEN a dimensional Kimball star built
  *downstream from that silver* in gold (`dim_`/`fact_` + SHA2 `*_Key`). Gold reads silver, never
  bronze. `normalized`/`dimensional` are single-layer.
- **Naming resolves per layer in `hybrid`.** The `naming:` block is the dimensional/hybrid-gold
  default; the silver layer follows `normalized` regardless of those keys. See
  `naming-standards.md` "⚠️ Precedence & key strategy by mode".
- **`scd_strategy: type_2` is dimensional-only** (or the gold layer of `hybrid`). It is invalid on
  `normalized`-mode silver — the skill errors and redirects to `hybrid`.
- **SDP mode is a mechanism swap, not a shape swap** — it honors all three `output_model` values.
  In SDP mode: DDL lives inside the flow (no separate DDL step), bronze paths are hardcoded (no
  `parameters:` beta), there is **no build-time test/validation artifact** (validation is the
  downstream `domain-model-validation` skill), and sources are plain `.sql` FILE-model libraries
  (no notebook-source header). See `etl-development-framework/sdp-pipeline-development.md`.
- **Every cell keeps the invariants:** read/write separation (`vibe_model.*` ≠ `catalogs.silver`),
  `_lower_snake` metadata columns in all modes, and the no-silent-descope rule for unsourced entities.

## Using a variant

1. Copy `templates/conventions.yml` to your project root as `conventions.yml` and fill in the
   identifiers (customer, domain, catalogs, `vibe_model.*`, `bronze_sources`, deployment).
2. Open the matching variant here and set the overlay blocks it lists (`etl_type`, `output_model`,
   `schemas`, `naming`, `scd_strategy`) to the values shown.
3. Run the loop: `domain-model-assessment` → `etl-development-framework` →
   `domain-model-validation` → `domain-documentation`. Assess is identical across all cells (same
   model); the flows diverge at Build.
