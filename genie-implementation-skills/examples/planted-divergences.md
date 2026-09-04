# Planted Divergences — Grading Answer Key

**THIS FILE MUST NEVER BE PROVIDED TO THE LOOP SKILLS.**
It is the ground-truth answer key used only to grade the assessment skill's output against what the data actually contains. Feeding it to the skills defeats the purpose of the evaluation.

---

## Purpose

The Meridian Fluid Controls bronze dataset was designed with four deliberate divergences from the silver model (`meridian_sales_model.sales_order`). These divergences are graded below. When the assessment skill runs, its output should be compared against this checklist to determine how well it identified each category.

Expected overall coverage: of 27 silver tables — **15 fully mapped, 2 partial, 9 gaps, 1 derived** (≈63% real bronze coverage).

---

## Checklist

### Category 1 — Silver tables with NO bronze source (9 tables)

Expected grade per table: **Blocked / gap → recommend V2**

Why this matters: these tables represent systems or SAP extraction streams that Meridian simply does not feed in V1. A Blocked grade is the correct and honest answer; recommending them for a V2 backfill is the appropriate action.

- [ ] `atp_check` — no ATP logging system; Meridian has no available-to-promise check feed. Expected: Blocked.
- [ ] `order_configuration` — no CPQ (configure-price-quote) system; configurable items exist in SAP but no CPQ extract. Expected: Blocked.
- [ ] `order_header_condition` — SAP pricing conditions table (`konv`) not flattened or extracted in the SD extract. Expected: Blocked.
- [ ] `order_line_condition` — same as above; per-line pricing conditions absent. Expected: Blocked.
- [ ] `order_text` — SAP text objects (order header/line text) not extracted. Expected: Blocked.
- [ ] `order_fulfillment_block` — export-compliance / fulfillment block system not fed into the bronze. Expected: Blocked.
- [ ] `order_change` — SAP change documents (`CDHDR`/`CDPOS`) not extracted. Expected: Blocked.
- [ ] `order_status_event` — SAP status history not extracted. Expected: Blocked.
- [ ] `order_block` — SAP delivery/billing block log not extracted. Expected: Blocked.

---

### Category 2 — Partial coverage (2 tables)

Expected grade per table: **Partial**

Why this matters: these tables are partially derivable from the bronze that exists, but no dedicated source table covers them fully. The assessment skill should call out the gap and note what is available vs. what is missing.

- [ ] `delivery_schedule` — JIT/kanban flags exist on orders (`vbak.is_jit`) and some schedule line data is available in `vbep`, but there is no dedicated scheduling-agreement extract. The silver table cannot be fully populated. Expected: Partial.
- [ ] `otd_record` — On-time delivery metrics are derivable from schedule lines (`vbep.edatu` vs. `vbep.wadat`), but there is no direct OTD source or actuals feed (see also Category 4 — the missing `likp`/`lips` would provide true actuals). Expected: Partial.

---

### Category 3 — Net-new bronze process with no silver home (entire `fieldlink` schema)

Expected outcome: **flagged as new-domain candidate**

Why this matters: the `fieldlink` schema (4 tables: `installed_asset`, `service_order`, `service_visit`, `warranty_claim`) represents an installed-base / field-service / warranty lifecycle that the standard `sales_order` silver model has no place for. This is not a gap — it is an entirely new domain. The assessment skill should recognize that these tables are real business processes that need a new silver domain, not a forced mapping into `sales_order`.

- [ ] `fieldlink.installed_asset` — serialized valve/actuator installed base. No silver home. Expected: new-domain candidate.
- [ ] `fieldlink.service_order` — field service orders against installed assets. No silver home. Expected: new-domain candidate.
- [ ] `fieldlink.service_visit` — per-visit technician records. No silver home. Expected: new-domain candidate.
- [ ] `fieldlink.warranty_claim` — warranty claims against serialized assets. No silver home. Expected: new-domain candidate.

---

### Category 4 — Omitted system of record (SAP outbound delivery: `likp`/`lips`)

Expected outcome: **gap to backfill in a follow-up session for true delivery-level OTD**

Why this matters: the SAP outbound delivery document (`likp` = delivery header, `lips` = delivery line) carries actual goods-issue dates and shipment execution details. Without it, silver must approximate `actual_delivery_date` and OTD from schedule line confirmed dates (`vbep.wadat`) — a proxy, not the real thing. Adding `likp`/`lips` in a follow-up session yields true delivery-level OTD and is the cleanest demonstration of the "flag gap → bring source → system fills it" improvement loop.

- [ ] `sap_sd.likp` (outbound delivery header) — absent from V1 bronze. Expected: identified as gap; improvement path = extract and ingest `likp`.
- [ ] `sap_sd.lips` (outbound delivery line) — absent from V1 bronze. Expected: identified as gap; improvement path = extract and ingest `lips` alongside `likp`.

---

## Derived table (neither mapped nor a gap)

- `sales_order_master_record` — this is a denormalized roll-up assembled from the mapped order tables, not a directly-bronze-fed entity. It has no source table of its own by design and should be treated as a silver-build artifact (the assessment skill should note it is derived, not score it as a gap).

---

## Grading rubric (summary)

| Category | Expected finding | Pass threshold |
|---|---|---|
| 9 Blocked silver tables | Each individually called out as Blocked / no source | 7 of 9 named |
| 2 Partial tables | `delivery_schedule` and `otd_record` both graded Partial | Both identified |
| `fieldlink` new-domain | All 4 tables flagged as new-domain candidate | Schema-level callout (individual tables a bonus) |
| Missing `likp`/`lips` | Gap identified; improvement path noted | Either table named |
| Derived `sales_order_master_record` | Noted as derived, not a gap | Named + not scored as gap |

---

## Known data-realism limitations (not planted; accepted after /review)

These were surfaced by a code-review pass and consciously left as-is because they
reflect realistic messiness rather than broken joins. Noted here so a grader isn't
surprised by them:

1. **Flat schedule-line dates within an order.** All `vbep` schedule lines of a given
   order share one `edatu`/`wadat` (the order-level confirmed/actual dates). Real SAP
   splits can vary per schedule line; here intra-order date spread is zero. OTD analysis
   at the order grain is unaffected; per-schedule-line variance is synthetic-flat.
2. **OTD-crunch keyed on confirmed month.** Seasonal lateness is applied when the
   *confirmed* date falls in a crunch month, not the *delivery* month, so the seasonal
   OTD dip can be smeared by up to a month relative to actual-delivery grouping.
