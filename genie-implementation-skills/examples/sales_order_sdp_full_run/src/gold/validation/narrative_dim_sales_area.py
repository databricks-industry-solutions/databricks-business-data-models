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
# MAGIC # dim_sales_area — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Sales organization structure dimension (org + channel + division). Passthrough from silver `sales_area` with key rename.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per sales org + distribution channel + division combination. 4 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Sales_Area_Key = sales_area_id` (identity passthrough from silver)
# MAGIC
# MAGIC ## Source
# MAGIC `silver.sales_area` (4 rows — direct passthrough)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** fact_sales_order_line (Sales_Area_Key), fact_otd (Sales_Area_Key), fact_credit_check (Sales_Area_Key)
# MAGIC - **Child of:** Root dimension (no parent)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - None
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** Verified (4 rows, 0 PK dups)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'dim_sales_area' AS Entity, COUNT(*) AS Row_Count FROM dim_sales_area;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Sales_Area_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Sales_Area_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Sales_Area_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_sales_area;

# COMMAND ----------

# DBTITLE 1,BK Null & Population
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   SUM(CASE WHEN Sales_Area_Key IS NULL THEN 1 ELSE 0 END) AS Null_Count,
# MAGIC   CASE WHEN SUM(CASE WHEN Sales_Area_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_sales_area;
# MAGIC
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Sales_Organization)/COUNT(*),2) AS Sales_Org_Pct,
# MAGIC   ROUND(100.0*COUNT(Distribution_Channel)/COUNT(*),2) AS Channel_Pct,
# MAGIC   ROUND(100.0*COUNT(Division)/COUNT(*),2) AS Division_Pct,
# MAGIC   ROUND(100.0*COUNT(Currency_Code)/COUNT(*),2) AS Currency_Pct
# MAGIC FROM dim_sales_area;

# COMMAND ----------

# DBTITLE 1,Sample (all rows)
# MAGIC %sql
# MAGIC SELECT * FROM dim_sales_area ORDER BY Sales_Area_Key;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_sales_area';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'dim_sales_area', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Sales_Area_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Sales_Area_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT Sales_Area_Key) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM dim_sales_area
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_sales_area', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Sales_Area_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Sales_Area_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: Sales_Area_Key', current_timestamp()
# MAGIC FROM dim_sales_area
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_sales_area', 'Population_All_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Sales_Organization)/COUNT(*), 100.0*COUNT(Distribution_Channel)/COUNT(*), 100.0*COUNT(Division)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Sales_Organization)/COUNT(*), 100.0*COUNT(Distribution_Channel)/COUNT(*), 100.0*COUNT(Division)/COUNT(*)), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Lowest pop across key cols', current_timestamp()
# MAGIC FROM dim_sales_area
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_sales_area', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING), ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_sales_area), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_sales_area' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;