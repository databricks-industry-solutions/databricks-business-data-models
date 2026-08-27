# Validation State - sales_order Gold (SDP Pipeline)
Updated: 2026-08-09 | Scorecard run: PASS | Total entities: 13 | Overall Grade: A

## Status Summary
- Validation SQL: All 13 entities executed — 70 checks (67 PASS + 3 accepted exceptions)
- Narrative Notebooks: 13/13 fully populated and verified (7-10 cells each)
- Scorecard: PASS — 13/13 Grade A; quality gate PASS; run_id f5e40509-59ed-4b1f-9962-426e7a5eedd5
- Job YAML: resources/meridian_sales_order_gold_validation.job.yml (15 tasks, all SUCCEEDED)
- Job ID: 74728959503728 (deployed to dev)
- Run: 856735942771277 (2026-08-09 03:28–03:32 UTC, SUCCESS)
- Bugs fixed: bridge column names (AG_Partner→Sold_To), fact_sales_order_line (Material_Number→Material_Key), scorecard PENDING claim (run_id→session.run_id)

## Entity Validation Matrix

| Entity | Tier | Type | Checks | Notebook | SQL_Status | Batch_Notes |
| --- | --- | --- | --- | --- | --- | --- |
| dim_date | G0 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| dim_sales_area | G0 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| dim_channel | G0 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| dim_order_reason | G0 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| dim_customer | G1 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| dim_material | G1 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| dim_sales_contract | G1 | DIM | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| bridge_order_partner | G1 | BRIDGE | PK,BK,POP,DRIFT | POPULATED | VERIFIED | 4/4 PASS |
| fact_sales_order_line | G2 | FACT | PK,BK,FKx4,POP,DRIFT,INTEG | POPULATED | VERIFIED | 9/9 PASS |
| fact_otd | G2 | FACT | PK,BK,FKx2,POPx2,DRIFT,INTEG | POPULATED | VERIFIED | 8/8 PASS (1 P0 exc) |
| fact_quotation_line | G2 | FACT | PK,BK,FKx2,POP,DRIFT,INTEG | POPULATED | VERIFIED | 7/7 PASS (1 P2 exc) |
| fact_return_line | G2 | FACT | PK,BK,FK+GAP,POP,DRIFT,INTEG | POPULATED | VERIFIED | 7/7 PASS (1 P1 exc) |
| fact_credit_check | G2 | FACT | PK,BK,FKx2,POP,DRIFT,INTEG | POPULATED | VERIFIED | 7/7 PASS |

## Known Gaps (4 seeded in _gap_registry)

| Entity | Column | Priority | Status | Description |
| --- | --- | --- | --- | --- |
| fact_otd | Actual_Delivery_Date | P0 | DEFERRED | Requires likp/lips ingestion |
| fact_return_line | Order_Reason_Key | P1 | ACCEPTED | Portal vocab gap (DMG/WRONG/WARR) |
| fact_quotation_line | Customer_Key | P2 | ACCEPTED | Cross-source FK (Account_Id vs Partner_Number) |
| fact_sales_order_line | Channel_Key | P3 | ACCEPTED | SHA2 vs identity key (0% orphan) |

## Artifacts

| Asset | Path | Status |
| --- | --- | --- |
| DDL notebook | src/gold/validation/ddl_validation_schema | COMPLETE |
| 13 narrative notebooks | src/gold/validation/narrative_* | ALL VERIFIED |
| Scorecard notebook | src/gold/validation/scorecard | VERIFIED (session.run_id fix applied) |
| Job YAML | resources/meridian_sales_order_gold_validation.job.yml | DEPLOYED (job 74728959503728) |
| Validation summary | docs/gold_validation_summary.md | COMPLETE |
| Build manifest | docs/build_manifest.md | UPDATED (§Gold validation line) |
