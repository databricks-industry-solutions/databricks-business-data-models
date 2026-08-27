# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
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
# MAGIC # dim_order_reason — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Standardized reason/rejection code reference dimension. Covers order rejections (SAP) and loss reasons (Salesforce CRM).
# MAGIC
# MAGIC ## Grain
# MAGIC One row per source_system + reason_code combination. 9 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Order_Reason_Key = order_reason_id` (identity passthrough from silver)
# MAGIC
# MAGIC ## Source
# MAGIC `silver.order_reason` (9 rows — deduped union of SAP tvaut + Salesforce loss_reason_ref)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** fact_sales_order_line (Order_Reason_Key), fact_return_line (Order_Reason_Key — P1 gap: all NULL)
# MAGIC - **Child of:** Root dimension (no parent)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - fact_return_line.Order_Reason_Key = NULL for all rows (P1 portal vocab gap: DMG/WRONG/WARR codes don't map)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** Verified (9 rows, 0 PK dups)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'dim_order_reason' AS Entity, COUNT(*) AS Row_Count FROM dim_order_reason;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Order_Reason_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Order_Reason_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Order_Reason_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_order_reason;

# COMMAND ----------

# DBTITLE 1,BK Null & Population
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END) AS Null_Count,
# MAGIC   CASE WHEN SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_order_reason;
# MAGIC
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Reason_Code)/COUNT(*),2) AS Reason_Code_Pct,
# MAGIC   ROUND(100.0*COUNT(Reason_Description)/COUNT(*),2) AS Description_Pct,
# MAGIC   ROUND(100.0*COUNT(Reason_Category)/COUNT(*),2) AS Category_Pct,
# MAGIC   ROUND(100.0*COUNT(Source_System)/COUNT(*),2) AS Source_System_Pct
# MAGIC FROM dim_order_reason;

# COMMAND ----------

# DBTITLE 1,Sample (all rows)
# MAGIC %sql
# MAGIC SELECT * FROM dim_order_reason ORDER BY Source_System, Reason_Code;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_order_reason';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'dim_order_reason', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Order_Reason_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Order_Reason_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT Order_Reason_Key) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM dim_order_reason
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_order_reason', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Order_Reason_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: Order_Reason_Key', current_timestamp()
# MAGIC FROM dim_order_reason
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_order_reason', 'Population_All_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Reason_Code)/COUNT(*), 100.0*COUNT(Reason_Description)/COUNT(*), 100.0*COUNT(Reason_Category)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Reason_Code)/COUNT(*), 100.0*COUNT(Reason_Description)/COUNT(*), 100.0*COUNT(Reason_Category)/COUNT(*)), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Lowest pop across key cols', current_timestamp()
# MAGIC FROM dim_order_reason
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_order_reason', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_order_reason), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_order_reason' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;