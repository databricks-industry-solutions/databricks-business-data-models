<!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->

# Genie Space Instructions — Sales Order Analytics

**Space ID:** `01f193a8e28b18eb91b85edac9274d28`  
**Tables:** 30 (17 silver 3NF + 13 gold dimensional star)

## Instructions Text (paste into Genie Space UI)

```
This is the Sales Order hybrid data model (normalized silver + dimensional gold star).

Gold schema (preferred for analytics): manufacturing_silver_vibe.sales_order_gold_sdp
Silver schema (3NF SSOT): manufacturing_silver_vibe.sales_order_silver_sdp

Use GOLD tables for analytical queries (facts + dimensions). Use SILVER for operational detail or when gold doesn't cover the entity.

Star schema joins (gold):
- Revenue/volume: fact_sales_order_line JOIN dim_customer ON Customer_Key, JOIN dim_material ON Material_Key, JOIN dim_sales_area ON Sales_Area_Key
- OTD performance: fact_otd (OTD_Status = ON_TIME or LATE)
- Credit risk: fact_credit_check JOIN dim_customer ON Customer_Key, JOIN dim_sales_area ON Sales_Area_Key
- Quotation pipeline: fact_quotation_line JOIN dim_material ON Material_Key
- Returns: fact_return_line JOIN dim_customer ON Customer_Key
- Partner functions: bridge_order_partner (Sold_To_Number, Ship_To_Number, Bill_To_Number per order)
- Date dimension: JOIN dim_date ON Order_Date_Key (or any date key)

Silver hierarchy:
- sales_area (root) → order → order_line → order_schedule_line
- order → order_partner (multiple per order: AG, WE, RE)
- order → order_credit_check, edi_order_message, return_order

Business terms:
- "OTD" = On-Time Delivery = fact_otd.OTD_Status (proxy — actual delivery date is NULL)
- "AG" / "Sold-To" = customer placing order (Partner_Function = 'AG')
- "RMA" = Return Merchandise Authorization = return_order / fact_return_line
- "Net Value" = line revenue = fact_sales_order_line.Net_Value
- "Credit utilization" = exposure/limit*100 = fact_credit_check.Credit_Utilization_Pct
- "Schedule line" = committed delivery tranche within an order line
- "Framework agreement" = blanket purchase contract = sales_contract / dim_sales_contract

Important caveats:
- NULL FK values mean "unresolved" (no -1 sentinel). Filter WHERE {Key} IS NOT NULL for aggregations.
- fact_otd.Actual_Delivery_Date is always NULL (P0 gap — requires likp/lips ingestion). OTD is schedule-date proxy only.
- fact_return_line.Order_Reason_Key is always NULL (P1 gap — portal vocab doesn't map to SAP codes).
- fact_quotation_line.Customer_Key has low resolution (P2 gap — cross-source Account_Id vs Partner_Number).
- delivery_schedule has 0 rows (expected — no scheduling agreement documents in source).
- order.quotation_id is ~19.9% populated (only converted quotes resolve).

Table grains:
- fact_sales_order_line: one row per order line item (14,762 rows)
- fact_otd: one row per order schedule line (22,212 rows)
- fact_quotation_line: one row per quotation line item (11,982 rows)
- fact_return_line: one row per return line item (329 rows)
- fact_credit_check: one row per credit check event (3,104 rows)

<!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->
```

---

## Sample Queries (add to Genie Space)

### 1. Total revenue by sales area
```sql
SELECT sa.Sales_Organization, sa.Distribution_Channel, SUM(f.Net_Value) AS Total_Revenue, COUNT(*) AS Lines
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line f
JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
WHERE f.Sales_Area_Key IS NOT NULL
GROUP BY sa.Sales_Organization, sa.Distribution_Channel
ORDER BY Total_Revenue DESC
```

### 2. Top 10 customers by revenue
```sql
SELECT c.Customer_Number, c.Customer_Name, SUM(f.Net_Value) AS Revenue, COUNT(*) AS Lines
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line f
JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_customer c ON f.Customer_Key = c.Customer_Key
WHERE f.Customer_Key IS NOT NULL
GROUP BY c.Customer_Number, c.Customer_Name
ORDER BY Revenue DESC LIMIT 10
```

### 3. OTD rate overall
```sql
SELECT OTD_Status, COUNT(*) AS Lines, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) AS Pct
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_otd
GROUP BY OTD_Status
```

### 4. Monthly revenue trend
```sql
SELECT DATE_TRUNC('month', d.Full_Date) AS Month, SUM(f.Net_Value) AS Revenue, COUNT(*) AS Lines
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line f
JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_date d ON f.Order_Date_Key = d.Date_Key
WHERE f.Order_Date_Key IS NOT NULL
GROUP BY DATE_TRUNC('month', d.Full_Date)
ORDER BY Month
```

### 5. Revenue by material (top 10)
```sql
SELECT m.Material_Number, m.Material_Description, SUM(f.Net_Value) AS Revenue
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line f
JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_material m ON f.Material_Key = m.Material_Key
WHERE f.Material_Key IS NOT NULL
GROUP BY m.Material_Number, m.Material_Description
ORDER BY Revenue DESC LIMIT 10
```

### 6. Credit utilization distribution
```sql
SELECT
  CASE WHEN Credit_Utilization_Pct < 50 THEN 'Low (<50%)'
       WHEN Credit_Utilization_Pct < 80 THEN 'Medium (50-80%)'
       ELSE 'High (>80%)' END AS Risk_Band,
  COUNT(*) AS Checks
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_credit_check
GROUP BY 1 ORDER BY 1
```

### 7. Return rate by customer
```sql
SELECT c.Customer_Number, c.Customer_Name, COUNT(*) AS Return_Lines, SUM(r.Return_Quantity) AS Total_Qty
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_return_line r
JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_customer c ON r.Customer_Key = c.Customer_Key
WHERE r.Customer_Key IS NOT NULL
GROUP BY c.Customer_Number, c.Customer_Name
ORDER BY Return_Lines DESC LIMIT 10
```

### 8. Order volume by type
```sql
SELECT Order_Type, COUNT(*) AS Orders, SUM(Net_Value) AS Total_Value
FROM manufacturing_silver_vibe.sales_order_silver_sdp.`order`
GROUP BY Order_Type ORDER BY Orders DESC
```

### 9. Average lines per order
```sql
SELECT ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT order_id), 1) AS Avg_Lines_Per_Order
FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_line
```

### 10. Quotation pipeline value
```sql
SELECT COUNT(*) AS Quote_Lines, SUM(Line_Value) AS Pipeline_Value, ROUND(AVG(Discount_Percent), 1) AS Avg_Discount_Pct
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_quotation_line
```

### 11. Late deliveries by month
```sql
SELECT DATE_TRUNC('month', Scheduled_Delivery_Date) AS Month, COUNT(*) AS Late_Lines
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_otd
WHERE OTD_Status = 'LATE'
GROUP BY 1 ORDER BY 1
```

### 12. Orders with credit blocks
```sql
SELECT Check_Result, COUNT(*) AS Checks, ROUND(AVG(Credit_Utilization_Pct), 1) AS Avg_Utilization
FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_credit_check
GROUP BY Check_Result ORDER BY Checks DESC
```

### 13. Partner function distribution per order
```sql
SELECT Partner_Function, COUNT(*) AS Records
FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_partner
GROUP BY Partner_Function ORDER BY Records DESC
```

### 14. Contract utilization (lines per contract)
```sql
SELECT c.Contract_Number, COUNT(cl.sales_contract_line_id) AS Line_Count
FROM manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract c
JOIN manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract_line cl ON c.sales_contract_id = cl.sales_contract_id
GROUP BY c.Contract_Number ORDER BY Line_Count DESC LIMIT 10
```

### 15. EDI message volume by type
```sql
SELECT Message_Type, Message_Direction, COUNT(*) AS Messages
FROM manufacturing_silver_vibe.sales_order_silver_sdp.edi_order_message
GROUP BY Message_Type, Message_Direction ORDER BY Messages DESC
```

---

## Manual Steps

1. Open the Genie space: [Sales Order Analytics](https://fevm-serverless-ss-dev.cloud.databricks.com/genie/rooms/01f193a8e28b18eb91b85edac9274d28)
2. Paste the instruction text (between the ``` markers above) into the space settings
3. Add each sample query above as a saved query in the space
4. Test with: "What is the total revenue by sales area?"
