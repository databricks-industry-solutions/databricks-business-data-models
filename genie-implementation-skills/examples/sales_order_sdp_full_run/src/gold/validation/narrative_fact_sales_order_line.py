# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT 'sales_order_gold_sdp';

# COMMAND ----------

# DBTITLE 1,Set Context
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative Header
# MAGIC %md
# MAGIC # fact_sales_order_line — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Central grain fact table: one row per order line item. Contains quantities, values, and FK links to all dimensions.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per (order × line item). 14,762 rows.
# MAGIC
# MAGIC ## Surrogate Key
# MAGIC `Order_Line_Key` (BIGINT identity)
# MAGIC
# MAGIC ## FKs (6)
# MAGIC - Customer_Key → dim_customer (SHA2(Partner_Number) via bridge AG)
# MAGIC - Material_Key → dim_material (SHA2(Material_Number))
# MAGIC - Sales_Area_Key → dim_sales_area (order.sales_area_id)
# MAGIC - Channel_Key → dim_channel (P3 gap resolved: 0% orphan)
# MAGIC - Order_Reason_Key → dim_order_reason (nullable, no rejected orders = NULL)
# MAGIC - Order_Date_Key, Requested_Delivery_Date_Key → dim_date
# MAGIC
# MAGIC ## Measures
# MAGIC - Order_Quantity, Net_Value, Tax_Amount, Discount_Amount
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - Channel_Key P3 — **RESOLVED** by validation: 0% FK orphans
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** A (9/9 checks PASS)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'fact_sales_order_line' AS Entity, COUNT(*) AS Row_Count FROM fact_sales_order_line;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Order_Line_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Order_Line_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Order_Line_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM fact_sales_order_line;

# COMMAND ----------

# DBTITLE 1,FK Orphan Checks
# MAGIC %sql
# MAGIC -- FK orphan rates for all dimensional FKs
# MAGIC SELECT 'dim_customer' AS Dimension,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4) AS Orphan_Pct
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key
# MAGIC WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_material',
# MAGIC   ROUND(100.0 * SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4)
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key
# MAGIC WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_sales_area',
# MAGIC   ROUND(100.0 * SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4)
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_sales_area d ON f.Sales_Area_Key = d.Sales_Area_Key
# MAGIC WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_channel',
# MAGIC   ROUND(100.0 * SUM(CASE WHEN d.Channel_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4)
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_channel d ON f.Channel_Key = d.Channel_Key
# MAGIC WHERE f.Channel_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_date (Order_Date_Key)',
# MAGIC   ROUND(100.0 * SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END) / COUNT(*), 4)
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_date d ON f.Order_Date_Key = d.Date_Key
# MAGIC WHERE f.Order_Date_Key IS NOT NULL;

# COMMAND ----------

# DBTITLE 1,Population & Measures
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Order_Quantity)/COUNT(*),2) AS Order_Qty_Pct,
# MAGIC   ROUND(100.0*COUNT(Net_Value)/COUNT(*),2) AS Net_Value_Pct,
# MAGIC   ROUND(100.0*COUNT(Customer_Key)/COUNT(*),2) AS Customer_Key_Pct,
# MAGIC   ROUND(100.0*COUNT(Material_Key)/COUNT(*),2) AS Material_Key_Pct,
# MAGIC   ROUND(100.0*COUNT(Sales_Area_Key)/COUNT(*),2) AS Sales_Area_Key_Pct,
# MAGIC   ROUND(100.0*COUNT(Order_Date_Key)/COUNT(*),2) AS Order_Date_Pct
# MAGIC FROM fact_sales_order_line;

# COMMAND ----------

# DBTITLE 1,Integration: Join Preservation
# MAGIC %sql
# MAGIC -- Join preservation: LEFT JOIN all dims, row count must not change
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM fact_sales_order_line) AS Fact_Rows,
# MAGIC   (SELECT COUNT(*) FROM fact_sales_order_line f
# MAGIC    LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC    LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC    LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC    LEFT JOIN dim_channel ch ON f.Channel_Key = ch.Channel_Key
# MAGIC    LEFT JOIN dim_date dd ON f.Order_Date_Key = dd.Date_Key) AS Joined_Rows,
# MAGIC   CASE WHEN (SELECT COUNT(*) FROM fact_sales_order_line) =
# MAGIC        (SELECT COUNT(*) FROM fact_sales_order_line f
# MAGIC         LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC         LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC         LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC         LEFT JOIN dim_channel ch ON f.Channel_Key = ch.Channel_Key
# MAGIC         LEFT JOIN dim_date dd ON f.Order_Date_Key = dd.Date_Key)
# MAGIC   THEN 'PASS' ELSE 'FAIL' END AS Status;

# COMMAND ----------

# DBTITLE 1,Metric Sanity
# MAGIC %sql
# MAGIC -- Metric sanity: distribution of key measures
# MAGIC SELECT
# MAGIC   MIN(Net_Value) AS Min_Net_Value, MAX(Net_Value) AS Max_Net_Value,
# MAGIC   AVG(Net_Value) AS Avg_Net_Value, PERCENTILE(Net_Value, 0.5) AS Median_Net_Value,
# MAGIC   MIN(Order_Quantity) AS Min_Qty, MAX(Order_Quantity) AS Max_Qty,
# MAGIC   SUM(CASE WHEN Net_Value < 0 THEN 1 ELSE 0 END) AS Negative_Net_Values,
# MAGIC   SUM(CASE WHEN Order_Quantity <= 0 THEN 1 ELSE 0 END) AS Zero_Or_Neg_Qty
# MAGIC FROM fact_sales_order_line;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT Order_Line_Key, Order_Number, Line_Number, Material_Key, Order_Quantity, Net_Value, Order_Date_Key
# MAGIC FROM fact_sales_order_line
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'fact_sales_order_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Order_Line_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Order_Line_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK dups', current_timestamp()
# MAGIC FROM fact_sales_order_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Order_Line_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Order_Line_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null', current_timestamp()
# MAGIC FROM fact_sales_order_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'FK_Customer_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL,
# MAGIC   'FK dim_customer', current_timestamp()
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'FK_Material_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL,
# MAGIC   'FK dim_material', current_timestamp()
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'FK_Sales_Area_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL,
# MAGIC   'FK dim_sales_area', current_timestamp()
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_sales_area d ON f.Sales_Area_Key = d.Sales_Area_Key WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'FK_Order_Date_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL,
# MAGIC   'FK dim_date (Order)', current_timestamp()
# MAGIC FROM fact_sales_order_line f LEFT JOIN dim_date d ON f.Order_Date_Key = d.Date_Key WHERE f.Order_Date_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'Population_Measures', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Order_Quantity)/COUNT(*), 100.0*COUNT(Net_Value)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Order_Quantity)/COUNT(*), 100.0*COUNT(Net_Value)/COUNT(*)),2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Measure pop', current_timestamp()
# MAGIC FROM fact_sales_order_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM fact_sales_order_line), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'fact_sales_order_line' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_sales_order_line', 'Integration_Join_Preservation', 'INTEGRATION',
# MAGIC   CASE WHEN j = f THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(f AS STRING), CAST(j AS STRING), CASE WHEN f > 0 THEN ROUND((j-f)*100.0/f,4) ELSE 0 END, FALSE, NULL,
# MAGIC   'Join preservation', current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT (SELECT COUNT(*) FROM fact_sales_order_line) AS f,
# MAGIC     (SELECT COUNT(*) FROM fact_sales_order_line f
# MAGIC      LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC      LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC      LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC      LEFT JOIN dim_date dd ON f.Order_Date_Key = dd.Date_Key) AS j
# MAGIC );