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
# MAGIC # quotation — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Formal price/availability proposals from Salesforce CRM. Tracks quote lifecycle, conversion probability, and linkage to converted orders.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per CRM quote. Expected ~4,000 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `quote_id` (CRM UUID) → SHA2 → `quotation_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.salesforce_crm.quote` (4,000 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** quotation_line (via quotation_id), order (via quotation_id ~19.9%)
# MAGIC - **Child of:** Root reference (no FK parents)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - ~19.9% of orders resolve quotation_id via converted_order_number matching
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 2

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'quotation' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM quotation;
# MAGIC
# MAGIC SELECT 'quotation' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT quotation_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT quotation_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT quotation_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM quotation;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN quotation_id IS NULL THEN 1 ELSE 0 END) AS Quotation_Id_Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN quotation_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM quotation;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Quote_Number) / COUNT(*), 2) AS Quote_Number_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Status) / COUNT(*), 2) AS Status_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Quote_Date) / COUNT(*), 2) AS Quote_Date_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Total_Amount) / COUNT(*), 2) AS Total_Amount_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Converted_Order_Number) / COUNT(*), 2) AS Converted_Order_Number_Pop_Pct
# MAGIC FROM quotation;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM quotation),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'quotation' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'quotation' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'quotation';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'quotation', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT quotation_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT quotation_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM quotation
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN quotation_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN quotation_id IS NULL THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: quotation_id', current_timestamp()
# MAGIC FROM quotation
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Quote_Number)/COUNT(*), 100.0*COUNT(Status)/COUNT(*), 100.0*COUNT(Quote_Date)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Quote_Number)/COUNT(*), 100.0*COUNT(Status)/COUNT(*), 100.0*COUNT(Quote_Date)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM quotation
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM quotation) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'quotation' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;