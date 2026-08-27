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
# MAGIC # dim_channel — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Distribution channel business rules dimension. Passthrough from silver `channel_config` with key rename.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per distribution channel. 4 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Channel_Key = channel_config_id` (identity passthrough from silver SHA2(Distribution_Channel))
# MAGIC
# MAGIC ## Source
# MAGIC `silver.channel_config` (4 rows — direct passthrough)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** fact_sales_order_line (Channel_Key)
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
# MAGIC -- Row count
# MAGIC SELECT 'dim_channel' AS Entity, COUNT(*) AS Row_Count FROM dim_channel;
# MAGIC
# MAGIC -- PK uniqueness
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Channel_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Channel_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Channel_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_channel;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- Business Key null check
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   SUM(CASE WHEN Channel_Key IS NULL THEN 1 ELSE 0 END) AS Null_Count,
# MAGIC   CASE WHEN SUM(CASE WHEN Channel_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_channel;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC -- Column population rates
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Distribution_Channel)/COUNT(*),2) AS Distribution_Channel_Pct,
# MAGIC   ROUND(100.0*COUNT(Channel_Name)/COUNT(*),2) AS Channel_Name_Pct,
# MAGIC   ROUND(100.0*COUNT(Credit_Check_Required)/COUNT(*),2) AS Credit_Check_Pct,
# MAGIC   ROUND(100.0*COUNT(EDI_Capable)/COUNT(*),2) AS EDI_Capable_Pct,
# MAGIC   ROUND(100.0*COUNT(Minimum_Order_Value)/COUNT(*),2) AS Min_Order_Val_Pct
# MAGIC FROM dim_channel;

# COMMAND ----------

# DBTITLE 1,Drift Check
# MAGIC %sql
# MAGIC -- Drift detection vs baseline
# MAGIC SELECT b.Table_Name, b.Metric_Type,
# MAGIC   CAST(b.Baseline_Value AS INT) AS Baseline_Rows,
# MAGIC   (SELECT COUNT(*) FROM dim_channel) AS Current_Rows,
# MAGIC   CASE WHEN (SELECT COUNT(*) FROM dim_channel) = CAST(b.Baseline_Value AS INT) THEN 'WITHIN_TOLERANCE' ELSE 'DRIFT_ALERT' END AS Drift_Status
# MAGIC FROM _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_channel' AND b.Is_Active = TRUE;

# COMMAND ----------

# DBTITLE 1,Sample (all rows)
# MAGIC %sql
# MAGIC -- All rows (compact dimension)
# MAGIC SELECT Channel_Key, Distribution_Channel, Channel_Name, Credit_Check_Required, EDI_Capable, Minimum_Order_Value
# MAGIC FROM dim_channel
# MAGIC ORDER BY Channel_Key;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC -- Write validation results (PENDING→claim)
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_channel';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'dim_channel', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Channel_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Channel_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT Channel_Key) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM dim_channel
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_channel', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Channel_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Channel_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: Channel_Key', current_timestamp()
# MAGIC FROM dim_channel
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_channel', 'Population_All_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Distribution_Channel)/COUNT(*), 100.0*COUNT(Channel_Name)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Distribution_Channel)/COUNT(*), 100.0*COUNT(Channel_Name)/COUNT(*)), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Lowest pop across key cols', current_timestamp()
# MAGIC FROM dim_channel
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_channel', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_channel), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_channel' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;