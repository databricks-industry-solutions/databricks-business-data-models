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
# MAGIC # return_order_line — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Line-item detail within RMA return orders. Captures returned products, quantities, inspection results, and credit values.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per RMA line item. Expected ~329 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `rma_line_id` → SHA2 → `return_order_line_id`
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.returns_portal.rma_line` (329 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Child of:** return_order (FK: return_order_id = SHA2(rma_number), hash-identity 100%), order_reason (FK: NULL — vocab gap P1)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - order_reason_id = NULL (same portal vocab gap as return_order)
# MAGIC - Is_Warranty is boolean cast from 'TRUE'/'FALSE' strings
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 7

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'return_order_line' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM return_order_line;
# MAGIC
# MAGIC SELECT 'return_order_line' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT return_order_line_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT return_order_line_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT return_order_line_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM return_order_line;

# COMMAND ----------

# DBTITLE 1,FK Integration — return_order
# MAGIC %sql
# MAGIC SELECT 'return_order_line' AS Entity, 'FK_return_order' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN p.return_order_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN p.return_order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct,
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.return_order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM return_order_line c LEFT JOIN return_order p ON c.return_order_id = p.return_order_id;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(SKU_Code) / COUNT(*), 2) AS SKU_Code_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Returned_Quantity) / COUNT(*), 2) AS Returned_Quantity_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Credit_Value) / COUNT(*), 2) AS Credit_Value_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Is_Warranty) / COUNT(*), 2) AS Is_Warranty_Pop_Pct
# MAGIC FROM return_order_line;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM return_order_line),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'return_order_line' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'return_order_line' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'return_order_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'return_order_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT return_order_line_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT return_order_line_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM return_order_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'return_order_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN RMA_Line_Id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN RMA_Line_Id IS NULL THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: RMA_Line_Id', current_timestamp()
# MAGIC FROM return_order_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'return_order_line', 'FK_return_order', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.return_order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN p.return_order_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: return_order_id (hash-identity)', current_timestamp()
# MAGIC FROM return_order_line c LEFT JOIN return_order p ON c.return_order_id = p.return_order_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'return_order_line', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(SKU_Code)/COUNT(*), 100.0*COUNT(Returned_Quantity)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(SKU_Code)/COUNT(*), 100.0*COUNT(Returned_Quantity)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM return_order_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'return_order_line', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM return_order_line) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'return_order_line' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;