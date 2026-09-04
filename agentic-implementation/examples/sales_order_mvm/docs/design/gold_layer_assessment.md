# Gold Layer Requirements — sales_order (MVM) hybrid star

> ⚠️ **DESIGNED, NOT BUILT.** This is the gold-layer *requirement* — the assessment's gold
> derivation (Mode B). The committed run in this folder built and validated **silver only**; the
> dimensional star described here is a future pass. Treat this as the spec a gold build would
> consume, not as as-built output.

**Flow:** `output_model: hybrid` — the normalized 3NF silver (`sales_order_mvm_silver_sdp`)
is the SSOT; this gold layer (`sales_order_mvm_gold_sdp`) is a **dimensional star built
downstream from silver** (reads silver, never bronze). Built by `etl-development-framework`;
this doc is its input requirement.

> **Cross-domain note.** Because cross-domain FKs are deferred (business keys retained,
> per `conventions … drop_unbuilt_domain_fks`), the conformed dimensions below are built
> from the **business-key columns present on the silver rows** (e.g. `material_number`,
> `plant`, `partner_number`), not from a joined-in cross-domain master. Each such dim is a
> lightweight, deduplicated key-and-label table.

## Facts

| Fact | Grain | Source silver table(s) | Key measures | Conformed dims |
|---|---|---|---|---|
| `fact_sales_order_line` | one order line | `order` + `order_line` | order_quantity, net_value, list_price, net_price, discount_amount | date, customer, material, plant, sales_org, channel, order (degenerate) |
| `fact_delivery` | one delivery_line | **`delivery` + `delivery_line`** | delivered_quantity, **on_time_flag**, **days_late** | date, customer, material, plant, channel |
| `fact_order_status_event` | one status event | `order_status_event` | event_count, duration_from_previous_event_min | date, channel, plant, order (degenerate), event_type (degenerate) |
| `fact_return_line` | one return order line | `return_order` + `return_order_line` | return_quantity, return_value | date, customer, material, reason (degenerate) |
| `fact_quotation_line` | one quotation line | `quotation` + `quotation_line` | quoted_quantity, quoted_value, **is_converted** | date, customer, material, sales_org |
| `fact_atp_check` | one ATP check | `atp_check` | requested_quantity, confirmed_quantity, **confirmation_gap** | date, material, plant |

`fact_delivery` is the headline addition — it exists only because the net-new
`delivery(_line)` was added via `allow_new_entities` (bronze `likp`/`lips`), and it carries the
**true OTD actuals** (`wadat_ist` goods-issue vs `lfdat` confirmed) that power `otd_performance`.

## Dimensions

| Dimension | Type | Built from | Natural key |
|---|---|---|---|
| `dim_date` | generated | date spine over the data window | date |
| `dim_customer` | conformed (business-key) | `order_partner` sold-to (`partner_number`, `partner_name`, address) | partner_number |
| `dim_material` | conformed (business-key) | `order_line.material_number` (+ product_hierarchy_code) | material_number |
| `dim_plant` | conformed (business-key) | `plant` / `sales_office` codes on order + lines | plant |
| `dim_sales_org` | conformed | `sales_org` / `sales_office` / `sales_group` on order | sales_org+office+group |
| `dim_channel` | conformed | `channel_type` discriminator | channel_type |
| `dim_sales_contract` | conformed | silver `sales_contract` (+ line) | sales_contract number |
| `dim_order` | degenerate | order-header attributes carried on facts | order number |

## FK / conformance rules

- Every fact FK to a conformed dim resolves on the dim's natural key (a single silver hop);
  0 orphans is the validation gate (`domain-model-validation`).
- Degenerate dims (`dim_order`, event_type, reason) live as attributes on the fact — no
  separate table.
- Surrogate keys per `conventions.naming.surrogate_key_formula` (SHA2 → BIGINT).

## Out of scope (deferred)

- Deep BU metrics/gold beyond this star (finance rollups, cohort/retention) — human-defined.
- Cross-domain conformed masters (true `dim_customer` from `customer.account`, `dim_material`
  from `product_catalog.sku`) — deferred with the cross-domain FKs; the business-key dims
  above are the buildable stand-ins and the recovery path is recorded in `next_vibes`.
