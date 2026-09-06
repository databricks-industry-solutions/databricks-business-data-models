# Validation State — Sales Order Domain
Updated: 2026-09-03 · Setup run: initial · Total entities: 17

| Entity | Tier | Type | Assigned_Session | Notebook_Status | Batch_Notes |
|---|---|---|---|---|---|
| sales_contract | 0 | DIM | setup | VERIFIED | 4/4 PASS, Grade A |
| sales_contract_line | 1 | DIM | setup | VERIFIED | 5/5 PASS, Grade A |
| quotation | 1 | DIM | setup | VERIFIED | 4/4 PASS, Grade A |
| order | 2 | FACT | setup | VERIFIED | 7/7 PASS, Grade A (INTEG) |
| quotation_line | 2 | DIM | setup | VERIFIED | 5/5 PASS, Grade A |
| order_line | 3 | FACT | setup | VERIFIED | 7/7 PASS, Grade A (INTEG) |
| order_partner | 3 | DIM | setup | VERIFIED | 5/5 PASS, Grade A |
| return_order | 3 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| delivery | 3 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| credit_check | 3 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| order_schedule_line | 4 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| order_configuration | 4 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| return_order_line | 4 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| delivery_line | 4 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| atp_check | 5 | FACT | setup | VERIFIED | 7/7 PASS, Grade A (INTEG) |
| order_status_event | 5 | FACT | setup | VERIFIED | 6/6 PASS, Grade A (INTEG) |
| delivery_schedule | 5 | FACT | setup | VERIFIED | 7/7 PASS, Grade A (INTEG) |

## Batch 1 — 2026-09-03
Entities: sales_contract, sales_contract_line, quotation
Checks: 13 PASS / 0 FAIL
Cumulative: 13/13

## Batch 2 — 2026-09-03
Entities: order, quotation_line
Checks: 12 PASS / 0 FAIL
Cumulative: 25/25

## Batch 3 — 2026-09-03
Entities: order_line, order_partner, return_order, delivery
Checks: 24 PASS / 0 FAIL
Cumulative: 49/49

## Batch 4-6 — 2026-09-03
Entities: credit_check, order_schedule_line, order_configuration, return_order_line, delivery_line, atp_check, order_status_event, delivery_schedule
Checks: 50 PASS / 0 FAIL
Cumulative: 99/99
