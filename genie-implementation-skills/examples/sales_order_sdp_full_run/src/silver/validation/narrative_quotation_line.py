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
# MAGIC # quotation_line — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Line-item detail within CRM quotations. Captures product, quantity, pricing, and discount information.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per quote line item. Expected ~11,982 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `quote_line_id` (CRM UUID) → SHA2 → `quotation_line_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.salesforce_crm.quote_line` (11,982 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** None
# MAGIC - **Child of:** quotation (FK: quotation_id = SHA2(quote_id) — hash-identity, 100% resolved)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - Hash-identity exception: quotation stores no raw quote_id column; SHA2(quote_id) computed inline
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 3

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'quotation_line' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM quotation_line;
# MAGIC
# MAGIC SELECT 'quotation_line' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT quotation_line_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT quotation_line_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT quotation_line_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM quotation_line;

# COMMAND ----------

# DBTITLE 1,FK Integration — quotation
# MAGIC %sql
# MAGIC SELECT 'quotation_line' AS Entity, 'FK_quotation' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN p.quotation_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN p.quotation_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct,
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.quotation_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM quotation_line c LEFT JOIN quotation p ON c.quotation_id = p.quotation_id;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(SKU_Code) / COUNT(*), 2) AS SKU_Code_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Quantity) / COUNT(*), 2) AS Quantity_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Net_Price) / COUNT(*), 2) AS Net_Price_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Net_Value) / COUNT(*), 2) AS Net_Value_Pop_Pct
# MAGIC FROM quotation_line;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM quotation_line),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'quotation_line' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'quotation_line' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'quotation_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'quotation_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT quotation_line_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT quotation_line_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN quotation_line_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN quotation_line_id IS NULL THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check', current_timestamp()
# MAGIC FROM quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation_line', 'FK_quotation', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.quotation_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN p.quotation_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: quotation_id (hash-identity)', current_timestamp()
# MAGIC FROM quotation_line c LEFT JOIN quotation p ON c.quotation_id = p.quotation_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation_line', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(SKU_Code)/COUNT(*), 100.0*COUNT(Quantity)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(SKU_Code)/COUNT(*), 100.0*COUNT(Quantity)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'quotation_line', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM quotation_line) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'quotation_line' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;