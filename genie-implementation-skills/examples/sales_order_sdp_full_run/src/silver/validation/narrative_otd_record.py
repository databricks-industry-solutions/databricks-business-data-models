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
# MAGIC # otd_record — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC On-time delivery tracking per schedule line. **PROXY** — uses goods_issue_date (wadat) vs requested_delivery_date (edatu) since actual_delivery_date requires likp/lips.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per order + line + schedule line (same source grain as order_schedule_line). Expected ~22,212 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vbeln + posnr + etenr` → SHA2 → `otd_record_id`
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.vbep` (22,212 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Child of:** order_line (FK: order_line_id, 100%), order_schedule_line (FK: hash-identity, 100%)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - **P0 GAP:** Actual_Delivery_Date = NULL (requires likp/lips ingestion)
# MAGIC - OTD_Status is a PROXY: ON_TIME = wadat <= edatu, LATE = wadat > edatu
# MAGIC - ~45.8% ON_TIME / 54.2% LATE (proxy metrics)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 6 (Partial grade)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'otd_record' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM otd_record;
# MAGIC
# MAGIC SELECT 'otd_record' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT otd_record_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT otd_record_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT otd_record_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM otd_record;

# COMMAND ----------

# DBTITLE 1,FK Integration — order_line + order_schedule_line
# MAGIC %sql
# MAGIC -- FK: order_line_id
# MAGIC SELECT 'otd_record' AS Entity, 'FK_order_line' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN p.order_line_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN p.order_line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct
# MAGIC FROM otd_record c LEFT JOIN order_line p ON c.order_line_id = p.order_line_id;
# MAGIC
# MAGIC -- FK: order_schedule_line_id (hash-identity)
# MAGIC SELECT 'otd_record' AS Entity, 'FK_order_schedule_line' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN s.order_schedule_line_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN s.order_schedule_line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct
# MAGIC FROM otd_record c LEFT JOIN order_schedule_line s ON c.order_schedule_line_id = s.order_schedule_line_id;

# COMMAND ----------

# DBTITLE 1,OTD Status Distribution
# MAGIC %sql
# MAGIC -- OTD proxy distribution
# MAGIC SELECT OTD_Status, COUNT(*) AS Cnt,
# MAGIC   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS Pct
# MAGIC FROM otd_record
# MAGIC GROUP BY OTD_Status;
# MAGIC
# MAGIC -- P0 gap: Actual_Delivery_Date should be 100% NULL
# MAGIC SELECT 'Actual_Delivery_Date_P0_Gap' AS Check_Name,
# MAGIC   SUM(CASE WHEN Actual_Delivery_Date IS NOT NULL THEN 1 ELSE 0 END) AS Non_Null_Count,
# MAGIC   CASE WHEN SUM(CASE WHEN Actual_Delivery_Date IS NOT NULL THEN 1 ELSE 0 END) = 0 THEN 'KNOWN_GAP' ELSE 'DATA_ARRIVED' END AS Status
# MAGIC FROM otd_record;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM otd_record),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'otd_record' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'otd_record' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'otd_record';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'otd_record', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT otd_record_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT otd_record_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM otd_record
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'otd_record', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Order_Number IS NULL OR Line_Number IS NULL OR Schedule_Line_Number IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Order_Number IS NULL OR Line_Number IS NULL OR Schedule_Line_Number IS NULL THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check', current_timestamp()
# MAGIC FROM otd_record
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'otd_record', 'FK_order_line', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.order_line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN p.order_line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: order_line_id', current_timestamp()
# MAGIC FROM otd_record c LEFT JOIN order_line p ON c.order_line_id = p.order_line_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'otd_record', 'FK_order_schedule_line', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN s.order_schedule_line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN s.order_schedule_line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: order_schedule_line_id (hash-identity)', current_timestamp()
# MAGIC FROM otd_record c LEFT JOIN order_schedule_line s ON c.order_schedule_line_id = s.order_schedule_line_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'otd_record', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN 100.0*COUNT(Requested_Delivery_Date)/COUNT(*) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(100.0*COUNT(Requested_Delivery_Date)/COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM otd_record
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'otd_record', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM otd_record) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'otd_record' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;