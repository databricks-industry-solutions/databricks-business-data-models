# .pipeline Directory — Sales Order Domain

This directory holds the build pipeline's state, handoffs, and progress tracking.

## Structure

```
.pipeline/
├── README.md              (this file)
├── state/
│   ├── run/
│   │   └── progress.md    Run-global phase tracker
│   └── silver/
│       └── etl_state.md   Per-entity silver checkpoint (AUTHORED for all 17)
└── handoffs/
    └── silver/
        └── build_manifest.md   Build → Validation handoff (required input for domain-model-validation)
```

## Build Mode

- **etl_type**: sdp_pipeline (Lakeflow Declarative Pipeline)
- **output_model**: hybrid (normalized 3NF silver; gold star deferred — Mode B future)
- **All 17 entities**: Materialized Views (full recompute each refresh)
- **No build-time testing**: Confidence from inline EXPECT + event log + downstream validation
