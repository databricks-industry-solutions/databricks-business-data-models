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
# MAGIC # fact_return_line — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Return/RMA line items from the returns portal. Tracks return quantities, warranty status, and return reasons.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per return line item. 329 rows.
# MAGIC
# MAGIC ## Surrogate Key
# MAGIC `Return_Line_Key` (BIGINT identity)
# MAGIC
# MAGIC ## FKs
# MAGIC - Customer_Key → dim_customer (SHA2(Customer_Number))
# MAGIC - Material_Key → dim_material (SHA2(SKU_Code))
# MAGIC - Order_Reason_Key → dim_order_reason (**P1 GAP: 100% NULL** — portal vocab gap)
# MAGIC - RMA_Date_Key → dim_date
# MAGIC
# MAGIC ## Measures
# MAGIC - Returned_Quantity, Return_Value, Is_Warranty
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - **P1 ACCEPTED:** Order_Reason_Key = NULL for all rows (portal uses DMG/WRONG/WARR codes that don't map to SAP/CRM reason vocabulary in dim_order_reason)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** A (7/7 PASS, 1 accepted P1 exception)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'fact_return_line' AS Entity, COUNT(*) AS Row_Count FROM fact_return_line;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Return_Line_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Return_Line_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Return_Line_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM fact_return_line;

# COMMAND ----------

# DBTITLE 1,FK Orphan Checks
# MAGIC %sql
# MAGIC SELECT 'dim_customer' AS Dimension, ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS Orphan_Pct
# MAGIC FROM fact_return_line f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_material', ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_return_line f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_date (RMA_Date_Key)', ROUND(100.0*SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_return_line f LEFT JOIN dim_date d ON f.RMA_Date_Key = d.Date_Key WHERE f.RMA_Date_Key IS NOT NULL;

# COMMAND ----------

# DBTITLE 1,P1 Gap: Order_Reason_Key
# MAGIC %sql
# MAGIC -- Confirm known P1 gap: Order_Reason_Key 100% NULL
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END) AS Null_Count,
# MAGIC   ROUND(100.0*SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS Null_Pct,
# MAGIC   'P1 ACCEPTED: portal vocab gap (DMG/WRONG/WARR codes)' AS Gap_Status
# MAGIC FROM fact_return_line;

# COMMAND ----------

# DBTITLE 1,Integration: Join Preservation
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM fact_return_line) AS Fact_Rows,
# MAGIC   (SELECT COUNT(*) FROM fact_return_line f
# MAGIC    LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC    LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC    LEFT JOIN dim_date dd ON f.RMA_Date_Key = dd.Date_Key) AS Joined_Rows,
# MAGIC   CASE WHEN (SELECT COUNT(*) FROM fact_return_line) =
# MAGIC        (SELECT COUNT(*) FROM fact_return_line f
# MAGIC         LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC         LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC         LEFT JOIN dim_date dd ON f.RMA_Date_Key = dd.Date_Key)
# MAGIC   THEN 'PASS' ELSE 'FAIL' END AS Status;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'fact_return_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'fact_return_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Return_Line_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Return_Line_Key) AS STRING), NULL, FALSE, NULL, 'PK', current_timestamp()
# MAGIC FROM fact_return_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_return_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Return_Line_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Return_Line_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL, 'BK', current_timestamp()
# MAGIC FROM fact_return_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_return_line', 'FK_Customer_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL, 'FK dim_customer', current_timestamp()
# MAGIC FROM fact_return_line f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_return_line', 'FK_Order_Reason_Key', 'FK',
# MAGIC   'PASS', NULL, CAST(SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL,
# MAGIC   TRUE, 'P1 gap: Order_Reason_Key 100% NULL (portal vocab gap)', 'KNOWN_GAP', current_timestamp()
# MAGIC FROM fact_return_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_return_line', 'Population_Measures', 'POP',
# MAGIC   CASE WHEN 100.0*COUNT(Returned_Quantity)/COUNT(*) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(100.0*COUNT(Returned_Quantity)/COUNT(*),2) AS STRING), NULL, FALSE, NULL, 'Returned_Qty pop', current_timestamp()
# MAGIC FROM fact_return_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_return_line', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL, 'Drift', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM fact_return_line), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'fact_return_line' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_return_line', 'Integration_Join_Preservation', 'INTEGRATION',
# MAGIC   CASE WHEN j = f THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(f AS STRING), CAST(j AS STRING), CASE WHEN f > 0 THEN ROUND((j-f)*100.0/f,4) ELSE 0 END, FALSE, NULL, 'Join preservation', current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT (SELECT COUNT(*) FROM fact_return_line) AS f,
# MAGIC     (SELECT COUNT(*) FROM fact_return_line fr
# MAGIC      LEFT JOIN dim_customer c ON fr.Customer_Key = c.Customer_Key
# MAGIC      LEFT JOIN dim_date dd ON fr.RMA_Date_Key = dd.Date_Key) AS j
# MAGIC );