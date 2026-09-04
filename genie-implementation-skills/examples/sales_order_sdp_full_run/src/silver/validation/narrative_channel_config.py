# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT 'sales_order_silver_sdp';

# COMMAND ----------

# DBTITLE 1,Set Context
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative Header
# MAGIC %md
# MAGIC # channel_config — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Channel business rules and policies per distribution channel. Governs credit check requirements, EDI capability, minimum order values, and pricing procedures.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per distribution channel. Expected ~4 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vtweg` → SHA2 → `channel_config_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.zsd_channel_config` (4 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** None directly (channel used as distribution_channel in order)
# MAGIC - **Child of:** sales_area (FK: sales_area_id = NULL — source lacks vkorg/spart)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - sales_area_id = NULL for all rows (source zsd_channel_config lacks vkorg/spart columns)
# MAGIC - This is an ACCEPTED gap (HG-SDP)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 1

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC -- Row count and freshness
# MAGIC SELECT
# MAGIC   'channel_config' AS Entity,
# MAGIC   COUNT(*) AS Row_Count,
# MAGIC   MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM channel_config;
# MAGIC
# MAGIC -- PK uniqueness: expect 0 duplicates
# MAGIC SELECT
# MAGIC   'channel_config' AS Entity,
# MAGIC   'PK_Uniqueness' AS Check_Name,
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT channel_config_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT channel_config_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT channel_config_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM channel_config;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- Business Key null/dropped data check
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = '' THEN 1 ELSE 0 END) AS Distribution_Channel_Dropped,
# MAGIC   CASE
# MAGIC     WHEN SUM(CASE WHEN Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS'
# MAGIC     ELSE 'FAIL'
# MAGIC   END AS Status
# MAGIC FROM channel_config;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC -- Column population rates
# MAGIC SELECT
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Channel_Name) / COUNT(*), 2) AS Channel_Name_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Credit_Check_Required) / COUNT(*), 2) AS Credit_Check_Required_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Minimum_Order_Value) / COUNT(*), 2) AS Minimum_Order_Value_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Pricing_Procedure) / COUNT(*), 2) AS Pricing_Procedure_Pop_Pct
# MAGIC FROM channel_config;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC -- Drift detection
# MAGIC WITH current_stats AS (
# MAGIC   SELECT COUNT(*) AS current_row_count FROM channel_config
# MAGIC ),
# MAGIC baseline AS (
# MAGIC   SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct
# MAGIC   FROM _data_drift_baseline
# MAGIC   WHERE Table_Name = 'channel_config' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE
# MAGIC )
# MAGIC SELECT
# MAGIC   'channel_config' AS Entity,
# MAGIC   'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC -- Write validation results (PENDING→claim)
# MAGIC DELETE FROM _validation_check_detail
# MAGIC WHERE Run_Id = 'PENDING' AND Table_Name = 'channel_config';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'channel_config', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT channel_config_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT channel_config_id) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK uniqueness check', current_timestamp()
# MAGIC FROM channel_config
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'channel_config', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: Distribution_Channel', current_timestamp()
# MAGIC FROM channel_config
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'channel_config', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(
# MAGIC     100.0 * COUNT(Channel_Name) / COUNT(*),
# MAGIC     100.0 * COUNT(Pricing_Procedure) / COUNT(*)
# MAGIC   ) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(
# MAGIC     100.0 * COUNT(Channel_Name) / COUNT(*),
# MAGIC     100.0 * COUNT(Pricing_Procedure) / COUNT(*)
# MAGIC   ), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population check', current_timestamp()
# MAGIC FROM channel_config
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'channel_config', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM channel_config) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'channel_config' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;