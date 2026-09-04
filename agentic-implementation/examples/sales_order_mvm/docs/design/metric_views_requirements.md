# Metric-View Requirements — sales_order (MVM)

> ⚠️ **DESIGNED, NOT BUILT.** These metric views sit on the gold star, which the committed
> silver-only run did not build. This is the requirement spec for a future gold pass, not as-built
> output.

Five Unity Catalog **metric views** (`CREATE VIEW … WITH METRICS LANGUAGE YAML`) built on the
gold star (`sales_order_mvm_gold_sdp`), extending the 6 model-level metric views (defined on the
silver shells in `model_setup.sql`) to the gold grain. Built by `domain-documentation`.

Each is a YAML sketch (dimensions + measures + comments). `source:` points at the gold fact;
dimensions reference conformed-dim keys / degenerate attributes on the fact.

---

## 1. `sales_orders` — booking & order value
```yaml
version: 1.1
source: sales_order_mvm_gold_sdp.fact_sales_order_line
dimensions:
  - {name: order_date,   expr: order_date}
  - {name: channel,      expr: channel_type}
  - {name: sales_org,    expr: sales_org}
  - {name: customer,     expr: partner_number}
  - {name: material,     expr: material_number}
measures:
  - {name: order_line_count,   expr: COUNT(1)}
  - {name: total_net_value,    expr: SUM(net_value)}
  - {name: avg_order_value,    expr: AVG(net_value)}
  - {name: total_quantity,     expr: SUM(order_quantity)}
```

## 2. `otd_performance` — on-time delivery (headline; powered by the net-new delivery)
```yaml
version: 1.1
source: sales_order_mvm_gold_sdp.fact_delivery
dimensions:
  - {name: goods_issue_date, expr: actual_goods_issue_date}
  - {name: plant,            expr: plant}
  - {name: channel,          expr: channel_type}
  - {name: customer,         expr: partner_number}
measures:
  - {name: delivered_line_count,    expr: COUNT(1)}
  - {name: on_time_delivery_rate,   expr: AVG(CAST(on_time_flag AS DOUBLE))}   # target ~0.85
  - {name: late_line_count,         expr: SUM(CASE WHEN on_time_flag THEN 0 ELSE 1 END)}
  - {name: avg_days_late,           expr: AVG(CASE WHEN days_late > 0 THEN days_late END)}
```

## 3. `quote_conversion` — quote-to-order
```yaml
version: 1.1
source: sales_order_mvm_gold_sdp.fact_quotation_line
dimensions:
  - {name: quotation_date, expr: quotation_date}
  - {name: sales_org,      expr: sales_org}
  - {name: customer,       expr: partner_number}
measures:
  - {name: quote_line_count,  expr: COUNT(1)}
  - {name: converted_count,   expr: SUM(CASE WHEN is_converted THEN 1 ELSE 0 END)}
  - {name: conversion_rate,   expr: AVG(CAST(is_converted AS DOUBLE))}
  - {name: quoted_value,      expr: SUM(quoted_value)}
```

## 4. `returns` — return rate & value
```yaml
version: 1.1
source: sales_order_mvm_gold_sdp.fact_return_line
dimensions:
  - {name: return_date, expr: return_date}
  - {name: reason,      expr: return_reason}
  - {name: material,    expr: material_number}
  - {name: customer,    expr: partner_number}
measures:
  - {name: return_line_count, expr: COUNT(1)}
  - {name: return_value,      expr: SUM(return_value)}
  - {name: return_quantity,   expr: SUM(return_quantity)}
```
> Return **rate** (returns ÷ shipped) spans two facts — expose it in the tutorial/dashboard as a
> cross-metric ratio, not a single-source measure.

## 5. `order_cycle_time` — lifecycle velocity
```yaml
version: 1.1
source: sales_order_mvm_gold_sdp.fact_order_status_event
dimensions:
  - {name: event_date, expr: event_date}
  - {name: channel,    expr: channel_type}
  - {name: plant,      expr: plant}
  - {name: event_type, expr: event_type}
measures:
  - {name: event_count,             expr: COUNT(1)}
  - {name: avg_minutes_since_prev,  expr: AVG(duration_from_previous_event_min)}
```
> `avg_order_to_ship_days` (order_created → goods_issued) is a per-order derivation across
> events — compute it in the tutorial notebook / a downstream view, not as a raw measure here.

---

## Notes
- Comments on every dimension/measure (omitted above for brevity) are **required** in the built
  YAML — mirror the style of the 6 model-level metric views in `model_setup.sql`.
- `otd_performance` is the demo's headline: it is buildable **only** because
  `delivery(_line)` was added via the `allow_new_entities` deviation.
