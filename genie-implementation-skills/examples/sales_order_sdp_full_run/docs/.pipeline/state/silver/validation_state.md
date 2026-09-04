# Validation State — sales_order (SDP Pipeline)
Updated: 2026-07-28 · Setup run: VAL-SDP-20260728 · Total entities: 17

| Entity | Tier | Type | Assigned_Session | Notebook_Status | Batch_Notes |
| --- | --- | --- | --- | --- | --- |
| sales_area | 0 | REF | setup | VERIFIED | 4/4 PASS, Grade A |
| order_reason | 0 | REF | setup | VERIFIED | 4/4 PASS, Grade A |
| channel_config | 1 | REF | setup | VERIFIED | 5/5 PASS, Grade A (1 KNOWN_GAP) |
| sales_contract | 1 | MASTER | setup | VERIFIED | 5/5 PASS, Grade A (1 KNOWN_GAP) |
| sales_contract_line | 2 | MASTER | setup | VERIFIED | 6/6 PASS, Grade A |
| quotation | 2 | TXN | setup | VERIFIED | 4/4 PASS, Grade A |
| order | 3 | TXN | setup | VERIFIED | 7/7 PASS, Grade A (1 accepted) |
| quotation_line | 3 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| order_line | 4 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| order_partner | 4 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| order_schedule_line | 5 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| delivery_schedule | 6 | MASTER | setup | VERIFIED | 4/4 PASS, Grade A (0 rows expected) |
| edi_order_message | 6 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| order_credit_check | 6 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| return_order | 6 | TXN | setup | VERIFIED | 7/7 PASS, Grade A (1 KNOWN_GAP) |
| otd_record | 6 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
| return_order_line | 7 | TXN | setup | VERIFIED | 6/6 PASS, Grade A |
