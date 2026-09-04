# ETL State — sales_order (SDP Pipeline)
Updated: 2026-08-08 · Setup run: SDP-20260728 · Total entities: 30 (17 silver + 13 gold)

## Silver Layer (Wave 1)

| Entity | Tier | Type | Wave | Assigned_Session | Build_Status | Batch_Notes |
| --- | --- | --- | --- | --- | --- | --- |
| sales_area | 0 | REF | 1 | setup | BUILT | MV, 4 rows expected |
| order_reason | 0 | REF | 1 | setup | BUILT | MV, UNION dedup (SAP wins), ~9 rows |
| channel_config | 1 | REF | 1 | setup | BUILT | MV, 4 rows, sales_area_id=NULL (lacks vkorg/spart) |
| sales_contract | 1 | MASTER | 1 | setup | BUILT | MV, 120 rows |
| sales_contract_line | 2 | MASTER | 1 | setup | BUILT | MV, 373 rows |
| quotation | 2 | TXN | 1 | setup | BUILT | MV, 4000 rows |
| order | 3 | TXN | 1 | setup | BUILT | MV, 5000 rows, FK quotation ~19.9% |
| quotation_line | 3 | TXN | 1 | setup | BUILT | MV, 11982 rows, hash-identity FK |
| order_line | 4 | TXN | 1 | setup | BUILT | MV, 14762 rows |
| order_partner | 4 | TXN | 1 | setup | BUILT | MV, 15000 rows |
| order_schedule_line | 5 | TXN | 1 | setup | BUILT | MV, 22212 rows |
| delivery_schedule | 6 | MASTER | 1 | setup | BUILT | MV, 0 rows (no SA types in bronze) |
| edi_order_message | 6 | TXN | 1 | setup | BUILT | ST (append), 956 rows, excl DELFOR/DELJIT |
| order_credit_check | 6 | TXN | 1 | setup | BUILT | ST (append), 3104 rows, credit_util computed |
| return_order | 6 | TXN | 1 | setup | BUILT | MV, 227 rows, order_reason_id=NULL (vocab gap) |
| otd_record | 6 | TXN | 1 | setup | BUILT | MV, 22212 rows, actual_delivery_date=NULL (P0 gap) |
| return_order_line | 7 | TXN | 1 | setup | BUILT | MV, 329 rows, hash-identity FK |

## Gold Layer (Wave 3) — Dimensional Star downstream from Silver

| Entity | Tier | Type | Wave | Assigned_Session | Build_Status | Batch_Notes |
| --- | --- | --- | --- | --- | --- | --- |
| dim_date | G0 | DIM | 3 | gold_build | BUILT | MV (generated calendar), 730 rows |
| dim_sales_area | G0 | DIM | 3 | gold_build | BUILT | MV (passthrough), 4 rows |
| dim_channel | G0 | DIM | 3 | gold_build | BUILT | MV (passthrough), 4 rows |
| dim_order_reason | G0 | DIM | 3 | gold_build | BUILT | MV (passthrough), 9 rows |
| dim_customer | G1 | DIM | 3 | gold_build | BUILT | MV (AG partner dedup), 300 rows |
| dim_material | G1 | DIM | 3 | gold_build | BUILT | MV (order_line ∪ quotation_line), 800 rows |
| dim_sales_contract | G1 | DIM | 3 | gold_build | BUILT | MV (passthrough), 120 rows |
| bridge_order_partner | G1 | BRIDGE | 3 | gold_build | BUILT | MV (pivot AG/WE/RE), 5000 rows |
| fact_sales_order_line | G2 | FACT | 3 | gold_build | BUILT | MV (order_line+order+partner), 14762 rows |
| fact_otd | G2 | FACT | 3 | gold_build | BUILT | MV (otd+order_line+order), 22212 rows |
| fact_quotation_line | G2 | FACT | 3 | gold_build | BUILT | MV (quotation_line+quotation), 11982 rows |
| fact_return_line | G2 | FACT | 3 | gold_build | BUILT | MV (return_line+return_order), 329 rows |
| fact_credit_check | G2 | FACT | 3 | gold_build | BUILT | MV (credit_check+order), 3104 rows |

**Note:** In SDP mode, `BUILT` means the declarative SQL source is authored with inline EXPECT constraints. There is no `TESTED` gate at build time — validation is the downstream `domain-model-validation` skill after the first pipeline update.
