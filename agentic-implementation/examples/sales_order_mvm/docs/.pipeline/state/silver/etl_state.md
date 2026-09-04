# ETL State — Silver Checkpoint (SDP Pipeline Mode)

> Status enum for SDP mode: AUTHORED (no build-time test gate — validation deferred to downstream skill)

| Entity | Tier | Type | Object | Wave | Assigned_Session | Build_Status |
| --- | --- | --- | --- | --- | --- | --- |
| sales_contract | 0 | Master | MV | 1 | Setup | AUTHORED |
| sales_contract_line | 1 | Master | MV | 2 | Setup | AUTHORED |
| quotation | 1 | Transactional | MV | 2 | Setup | AUTHORED |
| order | 2 | Transactional | MV | 3 | Setup | AUTHORED |
| quotation_line | 2 | Transactional | MV | 3 | Setup | AUTHORED |
| order_line | 3 | Transactional | MV | 4 | Setup | AUTHORED |
| order_partner | 3 | Transactional | MV | 4 | Setup | AUTHORED |
| return_order | 3 | Transactional | MV | 4 | Setup | AUTHORED |
| delivery | 3 | Transactional | MV | 4 | Setup | AUTHORED |
| credit_check | 3 | Transactional | MV | 4 | Setup | AUTHORED |
| order_schedule_line | 4 | Transactional | MV | 5 | Setup | AUTHORED |
| order_configuration | 4 | Transactional | MV | 5 | Setup | AUTHORED |
| return_order_line | 4 | Transactional | MV | 5 | Setup | AUTHORED |
| delivery_line | 4 | Transactional | MV | 5 | Setup | AUTHORED |
| atp_check | 5 | Transactional | MV | 6 | Setup | AUTHORED |
| order_status_event | 5 | Transactional | MV | 6 | Setup | AUTHORED |
| delivery_schedule | 5 | Master | MV | 6 | Setup | AUTHORED |
