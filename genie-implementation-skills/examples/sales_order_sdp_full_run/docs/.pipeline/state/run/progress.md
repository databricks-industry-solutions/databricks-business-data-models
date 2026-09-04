# Progress — Meridian Sales Order SDP Pipeline (Hybrid)

**Started:** 2026-07-28
**Status:** COMPLETE (deployed, pipeline running, 17 silver + 13 gold entities verified)

## Silver Layer Phase Tracker

| Phase | Description | Status | Notes |
| --- | --- | --- | --- |
| 1 | Discovery | COMPLETE | S2T mapping report complete (from domain-model-assessment) |
| 2 | Model & DDL | COMPLETE | DDL is inline in SDP (no separate step) |
| 3 | Gap Analysis | COMPLETE | 9 blocked entities (P0–P2); 17 buildable; gap_analysis.md + etl_state.md written |
| 4 | Scaffold | COMPLETE | 17 plain .sql pipeline sources authored (15 MV + 2 ST) |
| 5 | Load & DQ | N/A | SDP mode: no build-time test gate; inline EXPECT + event log |
| 6 | Deploy | COMPLETE | Bundle deployed (source-linked dev); pipeline ID 1b57fa65-f8d3-434b-b5cd-9beeba43e872 |
| 6.5 | Build Manifest | COMPLETE | docs/build_manifest.md emitted |
| 7 | Integration Test | COMPLETE | 4 runs: 2 schema fixes + 1 logic fix + 1 green. 100,294 rows, 0 PK dups |

## Gold Layer Build (2026-08-08)

| Phase | Description | Status | Notes |
| --- | --- | --- | --- |
| Gold Req | gold_layer_assessment.md | COMPLETE | 13 objects specified (7 dim + 1 bridge + 5 fact) |
| Gold Build | 13 MVs in src/gold/pipeline/ | COMPLETE | All plain .sql, fully-qualified to gold schema |
| Gold Deploy | Pipeline resource updated | COMPLETE | Gold glob added to existing pipeline; root_path changed to ../src |
| Gold Run | Full refresh | COMPLETE | Update 93aea6b7 COMPLETED; 2 fixes applied |
| Gold Verify | Row counts validated | COMPLETE | All 13 tables match assessment expectations |

### Gold Build Issues Resolved

| Run | Issue | Root Cause | Fix |
| --- | --- | --- | --- |
| 1 | dim_date UNRESOLVED_ROUTINE | DAYOFWEEK_ISO not available on serverless | WEEKDAY() + 1 |
| 1 | fact_return_line schema mismatch | DECIMAL subtraction widens (15,2)→(16,2) | CAST(...AS DECIMAL(15,2)) |
| 2 | Clean run | Both fixes applied | All 13 gold entities materialized |

### Gold Row Counts (Update 93aea6b7, COMPLETED)

| Entity | Rows | PK Status |
| --- | --- | --- |
| dim_date | 730 | ✓ |
| dim_sales_area | 4 | ✓ |
| dim_channel | 4 | ✓ |
| dim_order_reason | 9 | ✓ |
| dim_customer | 300 | ✓ |
| dim_material | 800 | ✓ |
| dim_sales_contract | 120 | ✓ |
| bridge_order_partner | 5,000 | ✓ |
| fact_sales_order_line | 14,762 | ✓ |
| fact_otd | 22,212 | ✓ |
| fact_quotation_line | 11,982 | ✓ |
| fact_return_line | 329 | ✓ |
| fact_credit_check | 3,104 | ✓ |
| **TOTAL** | **58,354** | **0 dups** |

## Human Gate Decisions

| ID | Decision | Disposition |
| --- | --- | --- |
| HG-SDP-1 | Opportunity entity | DEFERRED (CRM pipeline, out of scope) |
| HG-SDP-2 | 9 Blocked entities | DEFERRED until bronze ingestion |
| HG-SDP-3 | sales_order_master_record (degenerate) | EXCLUDED |
| HG-SDP-4 | Returns vocab gap (order_reason_id = NULL) | ACCEPTED (P1) |
| HG-GOLD-5 | Unknown dimension handling | NULL FK (no -1 sentinel) — consistent with silver 3NF |

## Silver Build Issues Resolved

| Run | Issue | Root Cause | Fix |
| --- | --- | --- | --- |
| 1 | order_credit_check schema mismatch | ROUND(DECIMAL/DECIMAL*100) widens to (22,2) vs declared (7,2) | Added CAST(...AS DECIMAL(7,2)) |
| 2 | delivery_schedule + 6 others type mismatch | TRY_TO_DATE returns DATE, schema declares TIMESTAMP | CAST(... AS TIMESTAMP) in 7 files |
| 3 | order_credit_check 0 rows | check_ts is yyyyMMdd; TRY_CAST AS TIMESTAMP→NULL; EXPECT drops all | TRY_TO_DATE(check_ts, 'yyyyMMdd') |
| 3 | order 136 PK duplicates | Multiple quotes share converted_order_number→LEFT JOIN fan-out | ROW_NUMBER dedup on quote subquery |
| 4 | Clean run | All fixes applied | 100,294 rows, 0 PK dups across 17 entities |

## Final Silver Row Counts (Update b89046d8, COMPLETED)

| Entity | Rows | PK Status |
| --- | --- | --- |
| sales_area | 4 | ✓ |
| order_reason | 9 | ✓ |
| channel_config | 4 | ✓ |
| sales_contract | 120 | ✓ |
| sales_contract_line | 373 | ✓ |
| quotation | 4,000 | ✓ |
| order | 5,000 | ✓ |
| quotation_line | 11,982 | ✓ |
| order_line | 14,762 | ✓ |
| order_partner | 15,000 | ✓ |
| order_schedule_line | 22,212 | ✓ |
| delivery_schedule | 0 | ✓ (expected) |
| edi_order_message | 956 | ✓ |
| order_credit_check | 3,104 | ✓ |
| return_order | 227 | ✓ |
| otd_record | 22,212 | ✓ |
| return_order_line | 329 | ✓ |
| **TOTAL** | **100,294** | **0 dups** |

## Next Steps

1. Inspect pipeline event-log EXPECT pass-rates for gold entities
2. Run downstream `domain-model-validation` skill for full data-state proof (silver + gold)
3. (Future) Ingest likp/lips to resolve OTD actual_delivery_date P0 gap
4. (Future) Build returns reason code mapping to resolve order_reason_id P1 gap
