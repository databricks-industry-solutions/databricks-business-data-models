# Progress Tracker — Sales Order Domain (SDP Pipeline Build)

> Run-global checkpoint. Updated after every phase transition.

## Phase Status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 0: Requirements Gate | COMPLETE | business_requirements.md graded B+ (assessment handoff) |
| Phase 1: Discovery | COMPLETE | Bronze sources profiled. All 17 entities classified. All-STRING bronze confirmed. |
| Phase 2: Model & DDL | N/A (SDP) | DDL lives in the flow — inline schema in each MV source. |
| Phase 3: Gap Analysis | COMPLETE | 20 NULL_SOURCE cols dropped, 2 entities dropped, 3 net-new added, 12 cross-domain FKs deferred. |
| Phase 4: Scaffold | COMPLETE | 17 .sql source files authored in src/silver/pipeline/. |
| Phase 5: Load & DQ | N/A (SDP) | No build-time test gate. Inline EXPECT constraints + event log provide DQ. |
| Phase 6: Pipeline DAB | COMPLETE | databricks.yml + resources/sales_order_silver.pipeline.yml created. |
| Phase 7: Self-Audit | COMPLETE | All artifacts present. Ready for handoff to domain-model-validation. |

## Entity Status Summary

All 17 entities: AUTHORED (SDP mode — no TESTED state; validation deferred to downstream skill)

## Notes

- etl_type: sdp_pipeline — all entities are Materialized Views (full recompute each refresh)
- output_model: hybrid — normalized 3NF silver; gold star deferred (Mode B future)
- Bronze paths hardcoded (no parameterization — SDP beta limitation)
- 'order' entity backtick-escaped as reserved SQL keyword
- Per-column date formats verified (Rule C probe): mixed yyyyMMdd / yyyy-MM-dd within same table
