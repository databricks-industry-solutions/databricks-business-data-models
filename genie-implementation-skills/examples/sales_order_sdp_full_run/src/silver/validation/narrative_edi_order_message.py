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
# MAGIC # edi_order_message — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Electronic order message log (append-only streaming table). Tracks inbound/outbound EDI transactions excluding scheduling types.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per message_id. Expected ~956 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `message_id` → SHA2 → `edi_order_message_id`
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.edi_gateway.edi_message_log` (956 rows, filtered: excludes DELFOR/DELJIT)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Child of:** order (FK: order_id = SHA2(order_number), 100% resolved)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - Streaming table (append-only); watermark on transmission_ts
# MAGIC - Excludes scheduling message types (DELFOR, DELJIT)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Streaming Table
# MAGIC - **Tier:** 6

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'edi_order_message' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM edi_order_message;
# MAGIC
# MAGIC SELECT 'edi_order_message' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT edi_order_message_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT edi_order_message_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT edi_order_message_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM edi_order_message;

# COMMAND ----------

# DBTITLE 1,FK Integration — order
# MAGIC %sql
# MAGIC SELECT 'edi_order_message' AS Entity, 'FK_order' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN p.order_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN p.order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct,
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM edi_order_message c LEFT JOIN `order` p ON c.order_id = p.order_id;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM edi_order_message),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'edi_order_message' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'edi_order_message' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'edi_order_message';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'edi_order_message', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT edi_order_message_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT edi_order_message_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM edi_order_message
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'edi_order_message', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Message_Id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Message_Id IS NULL THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: Message_Id', current_timestamp()
# MAGIC FROM edi_order_message
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'edi_order_message', 'FK_order', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN p.order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: order_id', current_timestamp()
# MAGIC FROM edi_order_message c LEFT JOIN `order` p ON c.order_id = p.order_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'edi_order_message', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Message_Type)/COUNT(*), 100.0*COUNT(Processing_Status)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Message_Type)/COUNT(*), 100.0*COUNT(Processing_Status)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM edi_order_message
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'edi_order_message', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM edi_order_message) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'edi_order_message' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;