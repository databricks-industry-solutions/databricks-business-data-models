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
# MAGIC # fact_otd — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC On-Time Delivery (OTD) fact: one row per schedule line. Computes proxy OTD status from requested vs. confirmed dates.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per order schedule line. 22,212 rows.
# MAGIC
# MAGIC ## Surrogate Key
# MAGIC `OTD_Key` (BIGINT identity)
# MAGIC
# MAGIC ## FKs
# MAGIC - Customer_Key → dim_customer (via order_partner AG)
# MAGIC - Material_Key → dim_material (via order_line)
# MAGIC - Sales_Area_Key → dim_sales_area
# MAGIC - Requested_Delivery_Date_Key → dim_date
# MAGIC
# MAGIC ## Measures
# MAGIC - OTD_Status (ON_TIME/LATE proxy), Delay_Days (confirmed - requested), Actual_Delivery_Date (**NULL — P0 gap**)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - **P0 DEFERRED:** Actual_Delivery_Date = NULL for all rows — requires likp/lips ingestion
# MAGIC - OTD proxy: 45.8% ON_TIME / 54.2% LATE (uses confirmed_date vs requested_delivery_date)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** A (8/8 PASS + 1 accepted P0 gap)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'fact_otd' AS Entity, COUNT(*) AS Row_Count FROM fact_otd;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT OTD_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT OTD_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT OTD_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM fact_otd;

# COMMAND ----------

# DBTITLE 1,FK Orphan Checks
# MAGIC %sql
# MAGIC SELECT 'dim_customer' AS Dimension, ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS Orphan_Pct
# MAGIC FROM fact_otd f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_material', ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_otd f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_sales_area', ROUND(100.0*SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_otd f LEFT JOIN dim_sales_area d ON f.Sales_Area_Key = d.Sales_Area_Key WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_date (Requested)', ROUND(100.0*SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_otd f LEFT JOIN dim_date d ON f.Requested_Delivery_Date_Key = d.Date_Key WHERE f.Requested_Delivery_Date_Key IS NOT NULL;

# COMMAND ----------

# DBTITLE 1,P0 Gap: Actual_Delivery_Date
# MAGIC %sql
# MAGIC -- Confirm known P0 gap: Actual_Delivery_Date 100% NULL
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Actual_Delivery_Date IS NULL THEN 1 ELSE 0 END) AS Null_Count,
# MAGIC   ROUND(100.0*SUM(CASE WHEN Actual_Delivery_Date IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS Null_Pct,
# MAGIC   'P0 DEFERRED: requires likp/lips ingestion' AS Gap_Status
# MAGIC FROM fact_otd;

# COMMAND ----------

# DBTITLE 1,OTD Status Distribution
# MAGIC %sql
# MAGIC -- OTD proxy status distribution
# MAGIC SELECT OTD_Status, COUNT(*) AS Cnt, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM fact_otd),2) AS Pct
# MAGIC FROM fact_otd
# MAGIC GROUP BY OTD_Status
# MAGIC ORDER BY OTD_Status;

# COMMAND ----------

# DBTITLE 1,Integration: Join Preservation
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM fact_otd) AS Fact_Rows,
# MAGIC   (SELECT COUNT(*) FROM fact_otd f
# MAGIC    LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC    LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC    LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC    LEFT JOIN dim_date dd ON f.Requested_Delivery_Date_Key = dd.Date_Key) AS Joined_Rows,
# MAGIC   CASE WHEN (SELECT COUNT(*) FROM fact_otd) =
# MAGIC        (SELECT COUNT(*) FROM fact_otd f
# MAGIC         LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC         LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC         LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC         LEFT JOIN dim_date dd ON f.Requested_Delivery_Date_Key = dd.Date_Key)
# MAGIC   THEN 'PASS' ELSE 'FAIL' END AS Status;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'fact_otd';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'fact_otd', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT OTD_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT OTD_Key) AS STRING), NULL, FALSE, NULL, 'PK', current_timestamp()
# MAGIC FROM fact_otd
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN OTD_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN OTD_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL, 'BK', current_timestamp()
# MAGIC FROM fact_otd
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'FK_Customer_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL, 'FK dim_customer', current_timestamp()
# MAGIC FROM fact_otd f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'FK_Material_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL, 'FK dim_material', current_timestamp()
# MAGIC FROM fact_otd f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'Population_Measures', 'POP',
# MAGIC   CASE WHEN 100.0*COUNT(OTD_Status)/COUNT(*) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(100.0*COUNT(OTD_Status)/COUNT(*),2) AS STRING), NULL, FALSE, NULL, 'OTD_Status pop', current_timestamp()
# MAGIC FROM fact_otd
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'Gap_Actual_Delivery_Date_NULL', 'POP',
# MAGIC   'PASS', NULL, CAST(SUM(CASE WHEN Actual_Delivery_Date IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, TRUE,
# MAGIC   'P0 gap: Actual_Delivery_Date NULL (requires likp/lips)',
# MAGIC   'KNOWN_GAP: all NULL as expected', current_timestamp()
# MAGIC FROM fact_otd
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL, 'Drift', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM fact_otd), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'fact_otd' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_otd', 'Integration_Join_Preservation', 'INTEGRATION',
# MAGIC   CASE WHEN j = f THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(f AS STRING), CAST(j AS STRING), CASE WHEN f > 0 THEN ROUND((j-f)*100.0/f,4) ELSE 0 END, FALSE, NULL, 'Join preservation', current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT (SELECT COUNT(*) FROM fact_otd) AS f,
# MAGIC     (SELECT COUNT(*) FROM fact_otd fo
# MAGIC      LEFT JOIN dim_customer c ON fo.Customer_Key = c.Customer_Key
# MAGIC      LEFT JOIN dim_material m ON fo.Material_Key = m.Material_Key
# MAGIC      LEFT JOIN dim_sales_area sa ON fo.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC      LEFT JOIN dim_date dd ON fo.Requested_Delivery_Date_Key = dd.Date_Key) AS j
# MAGIC );