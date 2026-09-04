# Developer docs — using the skill suite

These docs teach **developers** how to use this skill suite to build data solutions, and
how the suite fits with the **vibe model**. They follow the
[Diátaxis](https://diataxis.fr/) framework — four modes of documentation, each serving a
different need. Pick the one that matches what you're trying to do right now:

| I want to… | Go to | Mode |
| --- | --- | --- |
| **Learn the whole loop by doing it** — run assess → build → validate → document end-to-end on the Meridian `field_service` domain | [tutorial.md](tutorial.md) | Tutorial (learning) |
| **Accomplish a specific task** — fill out `conventions.yml`, prepare assessment inputs, extend to gold, operate the validation dashboard/job, add a table, fix a degraded table, promote to prod, investigate drift, query the model, re-sync after a change | [how-to/](how-to/) | How-to (task) |
| **Look something up** — which skill does what, the handoff-artifact chain, the `conventions.yml` surface, human gates, troubleshooting | [reference.md](reference.md) | Reference (information) |
| **Understand why the suite works this way** — the agentic-loop motion, the vibe-model fit, why it's phase-gated | [explanation.md](explanation.md) | Explanation (understanding) |

> **Want to see the finished result first?** Two complementary examples:
> - [`examples/field_service/EXAMPLE_OUTPUT.md`](../../examples/field_service/EXAMPLE_OUTPUT.md) —
>   an *illustrative* picture of the artifact tree the tutorial produces (`merge_notebook` /
>   `normalized`): the three-tier layout plus sample handoff and narrative excerpts.
> - [`examples/sales_order_sdp_full_run/`](../../examples/sales_order_sdp_full_run/) — a *real,
>   captured* full run of the other flow (`sdp_pipeline` / `hybrid`, 30 tables), kept as a frozen
>   reference snapshot you can browse. Start at its
>   [`ARCHITECTURE.md`](../../examples/sales_order_sdp_full_run/ARCHITECTURE.md). Reference-only —
>   not runnable.

## The compass, in one picture

```
                     PRACTICAL  ─────────────────────  THEORETICAL
                        steps                             grounding
   STUDYING   ┌────────────────────────┐ ┌────────────────────────┐
   (learning) │  Tutorial               │ │  Explanation            │
              │  "Run the loop on your  │ │  "The motion, the vibe- │
              │   domain"               │ │   model fit, the why"   │
              │  → tutorial.md          │ │  → explanation.md       │
              └────────────────────────┘ └────────────────────────┘
   WORKING    ┌────────────────────────┐ ┌────────────────────────┐
   (task)     │  How-to guides          │ │  Reference              │
              │  "Add a table",         │ │  Skill catalog, handoff │
              │  "Fix a degraded table" │ │  chain, conventions,    │
              │  → how-to/              │ │  gates → reference.md   │
              └────────────────────────┘ └────────────────────────┘
```

## What these docs are *not*

- They are **not** the repo overview. What the suite is and how the skills fit together lives
  in [`../../README.md`](../../README.md) and [`../../CLAUDE.md`](../../CLAUDE.md). These
  developer docs are about *using the suite to build solutions* — a task-oriented companion to
  that overview.
- They are **not** per-domain documentation. When you run the loop, the
  `domain-documentation` skill produces documentation *for the domain you built* — a
  Model Guide, a Genie space, tutorials, and a narrative aimed at that domain's data
  **consumers** (analysts, stakeholders). Those are generated artifacts that live in the
  domain project, not here. See [explanation.md](explanation.md#two-layers-of-docs) for
  the distinction.

## The loop, in one line

`domain-model-assessment` (assess) → `etl-development-framework` (build) →
`domain-model-validation` (validate) → `domain-documentation` (document) — with
`autonomous-validation` governing execution discipline throughout and `domain-sync`
maintaining the model in steady state after it's built. **Handoff between stations is
through documents, not chat.**
