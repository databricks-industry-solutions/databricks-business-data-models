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
# MAGIC # sales_contract — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Framework/blanket purchase agreements with customers. Captures contract validity periods, target quantities/values, and lifecycle status.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per contract document. Expected ~120 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vbeln` → SHA2 → `sales_contract_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.veda` (120 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** sales_contract_line (via sales_contract_id)
# MAGIC - **Child of:** sales_area (FK: sales_area_id = NULL — veda lacks vkorg/spart)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - sales_area_id = NULL (source veda has vtweg but lacks vkorg/spart)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 1

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'sales_contract' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM sales_contract;
# MAGIC
# MAGIC SELECT 'sales_contract' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT sales_contract_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT sales_contract_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' THEN 1 ELSE 0 END) AS Contract_Number_Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Contract_Type) / COUNT(*), 2) AS Contract_Type_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Valid_From) / COUNT(*), 2) AS Valid_From_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Valid_To) / COUNT(*), 2) AS Valid_To_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Contract_Status) / COUNT(*), 2) AS Contract_Status_Pop_Pct
# MAGIC FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM sales_contract),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'sales_contract' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'sales_contract' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'sales_contract';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'sales_contract', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT sales_contract_id) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK uniqueness check', current_timestamp()
# MAGIC FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: Contract_Number', current_timestamp()
# MAGIC FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Contract_Type)/COUNT(*), 100.0*COUNT(Valid_From)/COUNT(*), 100.0*COUNT(Contract_Status)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Contract_Type)/COUNT(*), 100.0*COUNT(Valid_From)/COUNT(*), 100.0*COUNT(Contract_Status)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population check', current_timestamp()
# MAGIC FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_contract) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'sales_contract' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;