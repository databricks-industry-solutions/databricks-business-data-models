# Validation Summary — Meridian Sales Order Silver (SDP Pipeline)

**Run Timestamp:** 2026-07-28  
**Overall Grade:** A (17/17 entities)  
**Quality Gate:** PASS  
**Total Rows Validated:** 100,294  
**Pipeline:** meridian_sales_order_silver_sdp  
**Schema:** `manufacturing_silver_vibe.sales_order_silver_sdp`

---

## Per-Entity Grades

| Entity | Type | Tier | Rows | Grade | Build Grade | PK Dups | FK Orphan % | Integration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sales_area | REF | 0 | 4 | A | A | 0 | N/A | N/A |
| order_reason | REF | 0 | 9 | A | A | 0 | N/A | N/A |
| channel_config | REF | 1 | 4 | A | A | 0 | KNOWN_GAP | N/A |
| sales_contract | MASTER | 1 | 120 | A | A | 0 | KNOWN_GAP | N/A |
| sales_contract_line | MASTER | 2 | 373 | A | A | 0 | 0% | PASS |
| quotation | TXN | 2 | 4,000 | A | A | 0 | N/A | PASS |
| order | TXN | 3 | 5,000 | A | A | 0 | 0% | PASS |
| quotation_line | TXN | 3 | 11,982 | A | A | 0 | 0% | PASS |
| order_line | TXN | 4 | 14,762 | A | A | 0 | 0% | PASS |
| order_partner | TXN | 4 | 15,000 | A | A | 0 | 0% | PASS |
| order_schedule_line | TXN | 5 | 22,212 | A | A | 0 | 0% | PASS |
| delivery_schedule | MASTER | 6 | 0 | A | A (Partial) | 0 | N/A | N/A |
| edi_order_message | TXN | 6 | 956 | A | A | 0 | 0% | PASS |
| order_credit_check | TXN | 6 | 3,104 | A | A | 0 | 0% | PASS |
| return_order | TXN | 6 | 227 | A | A | 0 | 0% | PASS |
| otd_record | TXN | 6 | 22,212 | A | A | 0 | 0% | PASS |
| return_order_line | TXN | 7 | 329 | A | A | 0 | 0% | PASS |

---

## Gap Deltas (vs. build)

| Gap | Entity | Priority | Status | Changed? |
| --- | --- | --- | --- | --- |
| Actual_Delivery_Date NULL | otd_record | P0 | DEFERRED | No change |
| order_reason_id NULL (vocab gap) | return_order | P1 | ACCEPTED | No change |
| order_reason_id NULL (inherited) | return_order_line | P1 | ACCEPTED | No change |
| sales_area_id NULL | channel_config | P3 | ACCEPTED | No change |
| sales_area_id NULL | sales_contract | P3 | ACCEPTED | No change |
| 0 rows (no SA types) | delivery_schedule | P3 | ACCEPTED | No change |
| quotation_id ~19.9% | order | P3 | ACCEPTED | No change |

**No gaps resolved or degraded since build.**

---

## Changed Genie Caveats

No changes to consumer-facing caveats this run.

---

## Metadata Tables

Validation results stored in:
- `manufacturing_silver_vibe.sales_order_silver_sdp._validation_run`
- `manufacturing_silver_vibe.sales_order_silver_sdp._validation_table_result`
- `manufacturing_silver_vibe.sales_order_silver_sdp._validation_check_detail`
- `manufacturing_silver_vibe.sales_order_silver_sdp._data_drift_baseline`
- `manufacturing_silver_vibe.sales_order_silver_sdp._gap_registry`

---

## Next Steps

1. Deploy validation job (authored in `resources/meridian_sales_order_validation.job.yml`)
2. Run `domain-documentation` skill using this summary as input
3. Resolve P0 gap: ingest likp/lips for OTD actual delivery dates
4. (Future) Build gold star layer in `src/gold/pipeline/`
