# Documentation State — sales_order (SDP Hybrid)
Updated: 2026-08-09 · Setup run: DOC-SDP-20260809 · Total tables: 30

## Silver Layer (17 tables)

| Table | Assigned_Session | Doc_Status | Notes |
| --- | --- | --- | --- |
| sales_area | setup | VALIDATED | UC comment present; sample queries verified |
| order_reason | setup | VALIDATED | UC comment present; sample queries verified |
| channel_config | setup | VALIDATED | UC comment present; sample queries verified |
| sales_contract | setup | VALIDATED | UC comment present; sample queries verified |
| sales_contract_line | setup | VALIDATED | UC comment present; sample queries verified |
| quotation | setup | VALIDATED | UC comment present; sample queries verified |
| order | setup | VALIDATED | UC comment present; sample queries verified |
| quotation_line | setup | VALIDATED | UC comment present; sample queries verified |
| order_line | setup | VALIDATED | UC comment present; sample queries verified |
| order_partner | setup | VALIDATED | UC comment present; sample queries verified |
| order_schedule_line | setup | VALIDATED | UC comment present; sample queries verified |
| delivery_schedule | setup | VALIDATED | UC comment present; 0 rows expected |
| edi_order_message | setup | VALIDATED | UC comment present; sample queries verified |
| order_credit_check | setup | VALIDATED | UC comment present; sample queries verified |
| return_order | setup | VALIDATED | UC comment present; sample queries verified |
| otd_record | setup | VALIDATED | UC comment present; sample queries verified |
| return_order_line | setup | VALIDATED | UC comment present; sample queries verified |

## Gold Layer (13 tables)

| Table | Assigned_Session | Doc_Status | Notes |
| --- | --- | --- | --- |
| dim_date | setup | VALIDATED | UC comment present; sample queries verified |
| dim_sales_area | setup | VALIDATED | UC comment present; sample queries verified |
| dim_channel | setup | VALIDATED | UC comment present; sample queries verified |
| dim_order_reason | setup | VALIDATED | UC comment present; sample queries verified |
| dim_customer | setup | VALIDATED | UC comment present; sample queries verified |
| dim_material | setup | VALIDATED | UC comment present; sample queries verified |
| dim_sales_contract | setup | VALIDATED | UC comment present; sample queries verified |
| bridge_order_partner | setup | VALIDATED | UC comment present; sample queries verified |
| fact_sales_order_line | setup | VALIDATED | UC comment present; sample queries verified |
| fact_otd | setup | VALIDATED | UC comment present; sample queries verified |
| fact_quotation_line | setup | VALIDATED | UC comment present; sample queries verified |
| fact_return_line | setup | VALIDATED | UC comment present; sample queries verified |
| fact_credit_check | setup | VALIDATED | UC comment present; sample queries verified |
