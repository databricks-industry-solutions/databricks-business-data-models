# Gap Analysis — Meridian Sales Order Silver (SDP Pipeline)

**Domain:** sales_order 
**ETL Type:** sdp_pipeline (hybrid) 
**Assessment Date:** 2026-07-28 
**Bronze Sources:** 4 systems, 14 tables profiled 
**Model Scope:** 27 vibe model entities → 17 buildable, 9 blocked, 1 excluded

---

## 1. Summary

| Category | Count | Disposition |
| --- | --- | --- |
| Fully mapped entities | 15 | BUILT (MV) |
| Partially mapped entities | 2 | BUILT (delivery_schedule 0 rows, otd_record P0 gap) |
| Blocked entities (missing bronze) | 9 | DEFERRED (HG-SDP-2) |
| Degenerate entity | 1 | EXCLUDED (HG-SDP-3: sales_order_master_record) |
| Out-of-scope entity | 1 | DEFERRED (HG-SDP-1: opportunity → CRM pipeline) |

---

## 2. Unmapped Target Columns (Model → Bronze Gaps)

| Entity | Target Column | Gap Reason | Severity | Status |
| --- | --- | --- | --- | --- |
| otd_record | Actual_Delivery_Date | Requires likp/lips (delivery document tables) | P0 | DEFERRED |
| return_order | order_reason_id | Portal codes (DMG/WRONG/WARR) don't map to SAP/CRM vocabulary | P1 | ACCEPTED (HG-SDP-4) |
| return_order_line | order_reason_id | Same portal vocab gap as return_order | P1 | ACCEPTED (HG-SDP-4) |
| channel_config | sales_area_id | Source (zsd_channel_config) lacks vkorg/spart columns | WARN | ACCEPTED (NULL FK) |
| sales_contract | sales_area_id | Source (veda) lacks vkorg/spart; cannot resolve full composite key | WARN | ACCEPTED (NULL FK) |
| order | quotation_id | Only ~19.9% resolved (via quote.converted_order_number) | Expected | ACCEPTED (cross-source design) |
| delivery_schedule | (all columns) | 0 rows — no scheduling agreement types in current bronze | Expected | ACCEPTED (partial grade) |

---

## 3. Blocked Entities (Missing Bronze Ingestion)

| Entity | Required Bronze | SAP Object | Priority | Ingestion Ask |
| --- | --- | --- | --- | --- |
| order_header_condition | PRCD_ELEMENTS | Pricing conditions (header) | P0 | SAP SD pricing extraction |
| order_line_condition | PRCD_ELEMENTS | Pricing conditions (item) | P0 | SAP SD pricing extraction |
| order_status_event | cdhdr + cdpos | Change document headers + items | P0 | SAP change document extraction |
| order_change | cdhdr + cdpos | Same as above | P0 | SAP change document extraction |
| order_block | cdhdr + cdpos | Same as above | P0 | SAP change document extraction |
| order_text | stxh + stxl | SAPscript text storage | P2 | Low priority |
| order_configuration | CUOBJ / config | Variant configuration | P2 | Low priority |
| order_fulfillment_block | Export ctrl tables | Trade compliance | P2 | Low priority |
| atp_check | ATPLOG | ATP result logging | P2 | Low priority |

**Ingestion dependency clusters:**
- **Cluster A (P0):** PRCD_ELEMENTS → unblocks 2 entities (pricing conditions)
- **Cluster B (P0):** cdhdr + cdpos → unblocks 3 entities (status, changes, blocks)
- **Cluster C (P0):** likp + lips → unblocks OTD actual date (existing entity, partial)
- **Cluster D (P2):** stxh/stxl, CUOBJ, export ctrl, ATPLOG → low priority, 4 entities

---

## 4. Enrichment Opportunities (Bronze Columns Not Yet Mapped)

| Source Table | Column | Potential Use | Priority |
| --- | --- | --- | --- |
| sap_sd.vbak | bstnk | Customer PO reference → already mapped as PO_Number | N/A |
| sap_sd.vbak | vsbed | Shipping conditions → already mapped | N/A |
| salesforce_crm.quote | opportunity_id | Link to CRM opportunity (deferred entity) | P2 |
| edi_gateway.edi_message_log | interchange_control | EDI envelope tracking → mapped | N/A |
| returns_portal.rma_request | inspection_required | Inspection workflow flag → mapped | N/A |

**Note:** Bronze column coverage is high for buildable entities. Most unmapped columns relate to blocked entities (require new bronze tables, not new columns from existing tables).

---

## 5. Cross-Source FK Resolution Summary

| Relationship | Method | Resolution Rate | Notes |
| --- | --- | --- | --- |
| order → sales_area | Composite SHA2 (vkorg\|vtweg\|spart) | 100% | All orders have sales org data |
| order → order_reason | SHA2('SAP_S4'\|augru) when populated | ~28% (only rejected orders) | Expected: most orders not rejected |
| order → quotation | LEFT JOIN quote.converted_order_number | ~19.9% | Cross-source; only converted quotes link |
| order_line → order | SHA2(vbeln) hash-identity | 100% | Same document number |
| quotation_line → quotation | SHA2(quote_id) hash-identity | 100% | Same CRM UUID |
| return_order → order | SHA2(original_order_number) | 100% | Portal stores SAP order ref |
| return_order → order_reason | Vocab gap (portal codes ≠ SAP) | 0% | P1 — ACCEPTED as NULL |

---

## 6. Human Gate Decisions

| ID | Entity/Issue | Options Presented | Decision | Rationale |
| --- | --- | --- | --- | --- |
| HG-SDP-1 | opportunity entity | (a) DEFERRED (b) Build with partial data | DEFERRED | CRM pipeline scope; no SAP linkage |
| HG-SDP-2 | 9 blocked entities | (a) DEFERRED (b) Stub with NULL columns | DEFERRED | Missing bronze; stubbing adds no value |
| HG-SDP-3 | sales_order_master_record | (a) EXCLUDED (b) Build as thin view | EXCLUDED | Degenerate; all attributes covered by order+order_line |
| HG-SDP-4 | Returns portal vocab gap | (a) ACCEPTED with NULL (b) Build mapping table | ACCEPTED | P1; mapping table requires manual curation |

---

## 7. Recommendations (Post-Build)

1. **P0 — Ingest likp/lips** → enables real OTD actuals (Actual_Delivery_Date currently NULL)
2. **P0 — Ingest PRCD_ELEMENTS** → unblocks 2 pricing condition entities
3. **P0 — Ingest cdhdr/cdpos** → unblocks 3 order lifecycle entities
4. **P1 — Build returns reason code mapping** → resolves return_order.order_reason_id
5. **Phase 2 — Author gold star layer** → dimensional model downstream from this silver SSOT
