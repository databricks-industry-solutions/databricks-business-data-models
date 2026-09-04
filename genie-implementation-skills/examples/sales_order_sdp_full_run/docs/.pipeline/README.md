# `.pipeline/` — machine plumbing for the modeling loop

**You can safely ignore this folder.** It holds the skill-to-skill handoffs and run
checkpoints that let the Assess → Build → Validate → Document loop run, resume, and fan out
across sessions. Nothing here is a human-facing deliverable — the docs you actually read live
one level up under `docs/` (`tutorials/`, `explanation/`, `contributor/`, `design/`). See
`ARCHITECTURE.md` "Where things live" for that map.

This file is a static structural manifest of the tier; it does not change per project.

## Two kinds of file

| Tier | Keyed by | Lifecycle | What it is |
| --- | --- | --- | --- |
| `handoffs/` | **(seam, layer)** | durable, typed | The contract passed *between* two stations. A consumer reads it by seam + its own layer — it never needs to know which skill produced it. |
| `state/` | **(station or run, layer)** | mutable checkpoint | Per-run bookkeeping that makes a station resumable and parallelizable across sessions. |

## Layer convention (applies throughout the tier)

- `.../silver/` and `.../gold/` — **layer-scoped**. Silver and gold runs write parallel copies
  so a `hybrid` model's two layers never collide.
- `state/run/` — **run-global** (layer-agnostic): checkpoints that describe the whole run, not
  one layer.

## Directory map (this run)

```
.pipeline/
  README.md                              # this file
  handoffs/
    genie_space_instructions.md          # Document  (Genie space config + sample queries; one per domain)
    silver/
      build_manifest.md                  # Build → Validate  (as-built mirror of the spec)
      validation_summary.md              # Validate → Document  (grades, gap deltas, caveats)
      enrich_uc_metadata.sql             # Document  (runnable ALTER mirror of applied UC comments/tags)
    gold/
      validation_summary.md              # Validate → Document  (gold-layer grades + caveats)
      enrich_uc_metadata.sql             # Document  (gold-layer UC comments/tags)
  state/
    run/
      progress.md                        # overall phase tracker (run-global)
      documentation_state.md             # docs per-table checkpoint (run-global; docs runs once over both layers)
    silver/
      etl_state.md                       # ETL per-entity checkpoint (tier/type/wave; NOT_STARTED→BUILT→TESTED)
      validation_state.md                # validation per-entity checkpoint (NOT_STARTED→AUTHORED→VERIFIED)
    gold/
      validation_state.md                # gold validation per-entity checkpoint
  commentary/                            # session build commentary (one file per station × layer)
```

> `remediation_brief.md` would appear under `handoffs/{layer}/` only when a grade degrades — the
> Validate → Build seam. A clean run like this one doesn't produce one. This run has no
> `handoffs/gold/build_manifest.md` or `state/gold/etl_state.md`: the gold star was authored
> directly in the single SDP pipeline (see `ARCHITECTURE.md`), not through a separate gold build.

## The seams, by producer → consumer

| File | Produced by | Consumed by | Seam |
| --- | --- | --- | --- |
| `handoffs/{layer}/build_manifest.md` | `etl-development-framework` | `domain-model-validation` | Build → Validate |
| `handoffs/{layer}/validation_summary.md` | `domain-model-validation` | `domain-documentation` | Validate → Document |
| `handoffs/{layer}/remediation_brief.md` | `domain-model-validation` | `etl-development-framework` | Validate → Build (conditional) |
| `handoffs/{layer}/enrich_uc_metadata.sql` | `domain-documentation` | (re-apply script) | Document |
| `handoffs/genie_space_instructions.md` | `domain-documentation` | (Genie space) | Document |

> Handoffs are keyed by **seam**, not producer, on purpose: the consumer finds its input by
> what the file *is* and which layer it's working, without coupling to the producer's name.
