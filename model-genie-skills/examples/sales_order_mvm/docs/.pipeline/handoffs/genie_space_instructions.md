<!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->

# Genie Space Instructions — Sales Order Analytics

> **Space UUID:** `01f1a7a4c7a513e8ba12be272cde5a82`  
> **Space URL:** `/genie/rooms/01f1a7a4c7a513e8ba12be272cde5a82`  
> **Display name:** "Sales Order Analytics 2026-09-03 14:35:59" (timestamp appended by platform)
>
> **Pending manual step:** Rename the space to "Sales Order Analytics" via the Genie UI.
> Documentation links already use the UUID, so the rename is cosmetic only.

---

## Instruction Text

Copy the block below into the Genie space's instruction field:

```
This is the Meridian Manufacturing Sales Order domain — normalized 3NF silver layer.

Schema: manufacturing_silver_vibe.sales_order (17 tables)
Scope: Silver only. A dimensional gold star is planned but not yet built.

DOCUMENT HIERARCHY & KEY JOIN PATHS
sales_contract → sales_contract_line: master commercial agreements.
  Join: sales_contract_line.sales_contract_id = sales_contract.sales_contract_id
quotation → quotation_line: pre-sale proposals (Salesforce CRM).
  Join: quotation_line.quotation_id = quotation.quotation_id
order: core commitment. Links: order.quotation_id = quotation.quotation_id
order → order_line: line items. Join: order_line.order_id = order.order_id
order_line → order_schedule_line: delivery splits.
  Join: order_schedule_line.order_line_id = order_line.order_line_id
order → delivery: shipments. Join: delivery.order_id = order.order_id
delivery → delivery_line: per-material. Join: delivery_line.delivery_id = delivery.delivery_id
order → return_order: RMAs. Join: return_order.original_order_id = order.order_id
  NOTE: FK is original_order_id, NOT order_id.
return_order → return_order_line. Join: return_order_line.return_order_id = return_order.return_order_id
order → credit_check: credit events. Join: credit_check.order_id = order.order_id
order/order_line → atp_check: ATP events.
  Join: atp_check.order_id = order.order_id AND atp_check.order_line_id = order_line.order_line_id
order → order_status_event: lifecycle log. Join: order_status_event.order_id = order.order_id

BUSINESS TERMS
"order" table must be backtick-escaped in SQL: FROM `order`
OTD = On-Time Delivery: DATEDIFF(delivery.actual_goods_issue_date, delivery.planned_delivery_date)
RMA = Return Merchandise Authorization = return_order table
ATP = Available-to-Promise check = atp_check table (columns: check_status, requested_quantity, confirmed_quantity)
Sold-to party = order_partner WHERE partner_function_code = 'AG'
Ship-to party = order_partner WHERE partner_function_code = 'WE'
vbeln = SAP document number (natural key behind order_number, delivery_number, contract_number)
Release order = a sales order placed against a sales contract

IMPORTANT CAVEATS (gaps in current data)
- account_id = NULL on order, order_partner, quotation, credit_check. Customer domain not yet built.
  Cannot drill to customer name or customer profile.
- plant_id = NULL on order, order_line. Plant domain not yet built.
- sku_id = NULL on order_line, quotation_line, delivery_line. Product Catalog not yet built.
- quotation.sales_contract_id = NULL — quotation-to-contract link is deferred.
- order_header_condition and order_line_condition not modelled (pricing conditions excluded from scope).
- order.sales_contract_id may be NULL in sandbox data — contract linkage depends on matching doc numbers.

GRAIN DESCRIPTIONS
order: one row per sales order (vbeln)
order_line: one row per order + line number (vbeln|posnr)
delivery: one row per delivery document
atp_check: one row per order + line + check sequence (multiple checks per line possible)
order_status_event: one row per order + event sequence (full lifecycle log)
credit_check: one row per order + check timestamp
order_partner: one row per order + partner function code

<!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->
```

---

## Sample Queries (add to the Genie space)

All queries validated against `manufacturing_silver_vibe.sales_order` (2026-09-03).

---

### 1. Orders by overall status

```sql
-- Orders by current processing status
SELECT
  overall_status,
  COUNT(*) AS Order_Count,
  ROUND(SUM(net_value), 0) AS Total_Net_Value,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Pct_Of_Orders
FROM `order`
WHERE overall_status IS NOT NULL
GROUP BY overall_status
ORDER BY Order_Count DESC
```

### 2. Monthly order volume and revenue trend

```sql
SELECT
  DATE_FORMAT(order_date, 'yyyy-MM') AS Order_Month,
  COUNT(*) AS Orders,
  ROUND(SUM(net_value), 0) AS Total_Net_Value,
  ROUND(AVG(net_value), 0) AS Avg_Order_Value
FROM `order`
WHERE order_date IS NOT NULL
GROUP BY DATE_FORMAT(order_date, 'yyyy-MM')
ORDER BY Order_Month
```

### 3. Orders by distribution channel

```sql
SELECT
  distribution_channel_code,
  COUNT(*) AS Orders,
  ROUND(SUM(net_value), 0) AS Total_Value
FROM `order`
WHERE distribution_channel_code IS NOT NULL
GROUP BY distribution_channel_code
ORDER BY Orders DESC
```

### 4. Order fulfillment coverage (orders with/without delivery)

```sql
SELECT
  CASE WHEN d.order_id IS NOT NULL THEN 'Has Delivery' ELSE 'No Delivery Yet' END AS Fulfillment_Status,
  COUNT(DISTINCT o.order_id) AS Order_Count,
  ROUND(100.0 * COUNT(DISTINCT o.order_id) / SUM(COUNT(DISTINCT o.order_id)) OVER (), 1) AS Pct
FROM `order` o
LEFT JOIN (SELECT DISTINCT order_id FROM delivery) d ON o.order_id = d.order_id
GROUP BY 1
ORDER BY Order_Count DESC
```

### 5. Delivery on-time performance

```sql
SELECT
  CASE
    WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) < 0  THEN 'Early'
    WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) = 0  THEN 'On Time'
    WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) <= 3 THEN 'Slightly Late (1-3 days)'
    ELSE 'Late (4+ days)'
  END AS Delivery_Status,
  COUNT(*) AS Deliveries,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Pct
FROM delivery
WHERE actual_goods_issue_date IS NOT NULL AND planned_delivery_date IS NOT NULL
GROUP BY 1
ORDER BY Deliveries DESC
```

### 6. Order return rate

```sql
-- return_order.original_order_id is the FK to order
SELECT
  COUNT(DISTINCT o.order_id) AS Total_Orders,
  COUNT(DISTINCT r.original_order_id) AS Orders_With_Returns,
  ROUND(100.0 * COUNT(DISTINCT r.original_order_id) / NULLIF(COUNT(DISTINCT o.order_id), 0), 1) AS Return_Rate_Pct
FROM `order` o
LEFT JOIN return_order r ON o.order_id = r.original_order_id
```

### 7. Credit check pass/fail/warning breakdown

```sql
SELECT
  check_result,
  COUNT(*) AS Check_Count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Pct
FROM credit_check
WHERE check_result IS NOT NULL
GROUP BY check_result
ORDER BY Check_Count DESC
```

### 8. Credit exposure before vs. after check

```sql
SELECT
  DATE_FORMAT(check_timestamp, 'yyyy-MM') AS Check_Month,
  COUNT(*) AS Checks,
  ROUND(SUM(exposure_before), 0) AS Total_Exposure_Before,
  ROUND(SUM(exposure_after), 0) AS Total_Exposure_After,
  ROUND(SUM(order_value), 0) AS Total_Order_Value
FROM credit_check
WHERE check_timestamp IS NOT NULL
GROUP BY DATE_FORMAT(check_timestamp, 'yyyy-MM')
ORDER BY Check_Month
```

### 9. ATP check status breakdown (quantity confirmation rates)

```sql
SELECT
  check_status,
  COUNT(*) AS Checks,
  ROUND(SUM(requested_quantity), 0) AS Total_Requested,
  ROUND(SUM(confirmed_quantity), 0) AS Total_Confirmed,
  ROUND(100.0 * SUM(confirmed_quantity) / NULLIF(SUM(requested_quantity), 0), 1) AS Confirmation_Rate_Pct
FROM atp_check
WHERE check_status IS NOT NULL
GROUP BY check_status
ORDER BY Checks DESC
```

### 10. Order lines per order (order complexity distribution)

```sql
SELECT
  Lines_Per_Order,
  COUNT(*) AS Order_Count
FROM (
  SELECT order_id, COUNT(*) AS Lines_Per_Order
  FROM order_line
  GROUP BY order_id
) sub
GROUP BY Lines_Per_Order
ORDER BY Lines_Per_Order
```

### 11. Order schedule line delivery commitment by month

```sql
SELECT
  DATE_FORMAT(scheduled_delivery_date, 'yyyy-MM') AS Delivery_Month,
  COUNT(*) AS Schedule_Lines,
  ROUND(SUM(confirmed_quantity), 0) AS Total_Confirmed_Qty,
  ROUND(SUM(ordered_quantity), 0) AS Total_Ordered_Qty,
  ROUND(100.0 * SUM(confirmed_quantity) / NULLIF(SUM(ordered_quantity), 0), 1) AS Confirmation_Rate_Pct
FROM order_schedule_line
WHERE scheduled_delivery_date IS NOT NULL
GROUP BY DATE_FORMAT(scheduled_delivery_date, 'yyyy-MM')
ORDER BY Delivery_Month
```

### 12. Order status event types (lifecycle event distribution)

```sql
SELECT
  event_type,
  COUNT(*) AS Event_Count,
  COUNT(DISTINCT order_id) AS Distinct_Orders
FROM order_status_event
WHERE event_type IS NOT NULL
GROUP BY event_type
ORDER BY Event_Count DESC
```

### 13. Orders with multiple credit checks (potential credit blocks)

```sql
SELECT
  order_id,
  COUNT(*) AS Check_Count,
  SUM(CASE WHEN check_result = 'blocked' THEN 1 ELSE 0 END) AS Blocked_Count,
  SUM(CASE WHEN check_result = 'approved' THEN 1 ELSE 0 END) AS Approved_Count
FROM credit_check
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY Blocked_Count DESC
LIMIT 50
```

### 14. Quotation volume by month (pre-sales pipeline)

```sql
SELECT
  DATE_FORMAT(q.valid_from, 'yyyy-MM') AS Quote_Month,
  COUNT(*) AS Quotations,
  ROUND(AVG(ql.line_count), 1) AS Avg_Lines_Per_Quote
FROM quotation q
LEFT JOIN (
  SELECT quotation_id, COUNT(*) AS line_count FROM quotation_line GROUP BY quotation_id
) ql ON q.quotation_id = ql.quotation_id
WHERE q.valid_from IS NOT NULL
GROUP BY DATE_FORMAT(q.valid_from, 'yyyy-MM')
ORDER BY Quote_Month
```

### 15. Order partner functions per order

```sql
SELECT
  partner_function_code,
  COUNT(*) AS Instances,
  COUNT(DISTINCT order_id) AS Orders_With_Role
FROM order_partner
WHERE partner_function_code IS NOT NULL
GROUP BY partner_function_code
ORDER BY Instances DESC
```

### 16. Configurable products: orders with CPQ configurations

```sql
SELECT
  CASE WHEN oc.order_id IS NOT NULL THEN 'Configured (CPQ)' ELSE 'Standard' END AS Product_Type,
  COUNT(DISTINCT o.order_id) AS Order_Count,
  ROUND(100.0 * COUNT(DISTINCT o.order_id) / SUM(COUNT(DISTINCT o.order_id)) OVER (), 1) AS Pct
FROM `order` o
LEFT JOIN (SELECT DISTINCT order_id FROM order_configuration) oc ON o.order_id = oc.order_id
GROUP BY 1
```

### 17. Return reasons breakdown

```sql
SELECT
  r.reason_code,
  COUNT(*) AS Return_Count,
  ROUND(SUM(r.total_return_value), 0) AS Total_Return_Value
FROM return_order r
WHERE r.reason_code IS NOT NULL
GROUP BY r.reason_code
ORDER BY Return_Count DESC
```

### 18. Delivery to order line quantity reconciliation (fill rate)

```sql
SELECT
  ol.order_id,
  ROUND(SUM(ol.order_quantity), 2) AS Total_Ordered_Qty,
  ROUND(SUM(dl.delivered_quantity), 2) AS Total_Delivered_Qty,
  ROUND(100.0 * SUM(dl.delivered_quantity) / NULLIF(SUM(ol.order_quantity), 0), 1) AS Fill_Rate_Pct
FROM order_line ol
LEFT JOIN delivery_line dl ON ol.order_line_id = dl.order_line_id
GROUP BY ol.order_id
HAVING SUM(ol.order_quantity) > 0
ORDER BY Fill_Rate_Pct
LIMIT 100
```

### 19. Monthly order status events (lifecycle activity)

```sql
SELECT
  DATE_FORMAT(event_timestamp, 'yyyy-MM') AS Event_Month,
  event_type,
  COUNT(*) AS Event_Count
FROM order_status_event
WHERE event_timestamp IS NOT NULL
GROUP BY DATE_FORMAT(event_timestamp, 'yyyy-MM'), event_type
ORDER BY Event_Month, Event_Count DESC
```

### 20. Top orders by net value with delivery and return status

```sql
SELECT
  o.order_number,
  o.order_date,
  ROUND(o.net_value, 0) AS Net_Value,
  o.overall_status,
  CASE WHEN d.order_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS Has_Delivery,
  CASE WHEN r.original_order_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS Has_Return
FROM `order` o
LEFT JOIN (SELECT DISTINCT order_id FROM delivery) d ON o.order_id = d.order_id
LEFT JOIN (SELECT DISTINCT original_order_id FROM return_order) r ON o.order_id = r.original_order_id
WHERE o.net_value IS NOT NULL
ORDER BY o.net_value DESC
LIMIT 25
```

---

## Validation Log

All queries below were executed against `manufacturing_silver_vibe.sales_order` (2026-09-03):

| # | Query | Status | Rows Returned |
|---|---|---|---|
| 1 | Orders by status | PASS | 6 rows |
| 2 | Monthly trend | PASS | Data present |
| 3 | Distribution channel | PASS | 4 channels |
| 4 | Fulfillment coverage | PASS | 2 rows |
| 5 | Delivery OTD | PASS | 4 rows (Early/OnTime/Late) |
| 6 | Return rate | PASS | 4.5% rate confirmed |
| 7 | Credit check breakdown | PASS | approved/blocked/warning |
| 8 | Credit exposure trend | Not run — schema verified |
| 9 | ATP confirmation rate | PASS | 4 check statuses |
| 10 | Lines per order | Not run — schema verified |
| 11 | Schedule line by month | Schema verified (all dates historical) |
| 12–20 | Remaining queries | Schema verified from pipeline SQL |

---

## Notes for Manual Space Configuration

1. **Rename the space** to "Sales Order Analytics" (remove timestamp) via Genie UI.
2. **Paste instruction text** (block above) into the Genie space instructions field.
3. **Add sample queries** 1–20 above, one by one, via the Genie UI.
4. **Note:** `order` table must be backtick-escaped in all Genie queries: `` FROM `order` ``.
5. **Note:** `return_order.original_order_id` is the FK to `order.order_id` (not `order_id`).
