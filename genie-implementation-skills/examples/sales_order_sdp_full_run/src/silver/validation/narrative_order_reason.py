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
# MAGIC # order_reason — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Standardized reason/rejection code reference. Multi-source UNION (SAP + Salesforce CRM) with SAP priority dedup.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per unique reason code (deduped across sources). Expected ~9 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `source_system + reason_code` → SHA2 → `order_reason_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC - `manufacturing_bronze_vibe.sap_sd.tvaut` (8 rows)
# MAGIC - `manufacturing_bronze_vibe.salesforce_crm.loss_reason_ref` (4 rows)
# MAGIC - Dedup: ROW_NUMBER tiebreaker ORDER BY source_system DESC (SAP_S4 wins)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** order (via order_reason_id), return_order (NULL — vocab gap P1), return_order_line (NULL — vocab gap P1)
# MAGIC - **Child of:** Root reference (no parent)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - return_order/return_order_line cannot resolve order_reason_id (portal vocab gap: DMG/WRONG/WARR ≠ SAP codes)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 0 (root reference)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC -- Row count and freshness
# MAGIC SELECT
# MAGIC   'order_reason' AS Entity,
# MAGIC   COUNT(*) AS Row_Count,
# MAGIC   MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM order_reason;
# MAGIC
# MAGIC -- PK uniqueness: expect 0 duplicates
# MAGIC SELECT
# MAGIC   'order_reason' AS Entity,
# MAGIC   'PK_Uniqueness' AS Check_Name,
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT order_reason_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT order_reason_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_reason_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM order_reason;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- Business Key null/dropped data check
# MAGIC -- NK columns: Reason_Code, Source_System
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Reason_Code IS NULL OR TRIM(Reason_Code) = '' THEN 1 ELSE 0 END) AS Reason_Code_Dropped,
# MAGIC   SUM(CASE WHEN Source_System IS NULL OR TRIM(Source_System) = '' THEN 1 ELSE 0 END) AS Source_System_Dropped,
# MAGIC   CASE
# MAGIC     WHEN SUM(CASE WHEN Reason_Code IS NULL OR TRIM(Reason_Code) = ''
# MAGIC               OR Source_System IS NULL OR TRIM(Source_System) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS'
# MAGIC     ELSE 'FAIL'
# MAGIC   END AS Status
# MAGIC FROM order_reason;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC -- Column population rates for key business columns
# MAGIC SELECT
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Reason_Description) / COUNT(*), 2) AS Reason_Description_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Reason_Category) / COUNT(*), 2) AS Reason_Category_Pop_Pct
# MAGIC FROM order_reason;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC -- Drift detection: compare current row count to baseline
# MAGIC WITH current_stats AS (
# MAGIC   SELECT COUNT(*) AS current_row_count FROM order_reason
# MAGIC ),
# MAGIC baseline AS (
# MAGIC   SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct
# MAGIC   FROM _data_drift_baseline
# MAGIC   WHERE Table_Name = 'order_reason' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE
# MAGIC )
# MAGIC SELECT
# MAGIC   'order_reason' AS Entity,
# MAGIC   'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count,
# MAGIC   c.current_row_count,
# MAGIC   b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE
# MAGIC     WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL'
# MAGIC     ELSE 'PASS'
# MAGIC   END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC -- Write validation results to metadata tables (PENDING→claim)
# MAGIC DELETE FROM _validation_check_detail
# MAGIC WHERE Run_Id = 'PENDING' AND Table_Name = 'order_reason';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC -- PK check
# MAGIC SELECT 'PENDING', 'order_reason', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_reason_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT order_reason_id) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK uniqueness: ' || CAST(COUNT(*) - COUNT(DISTINCT order_reason_id) AS STRING) || ' duplicates',
# MAGIC   current_timestamp()
# MAGIC FROM order_reason
# MAGIC UNION ALL
# MAGIC -- BK check
# MAGIC SELECT 'PENDING', 'order_reason', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Reason_Code IS NULL OR TRIM(Reason_Code) = ''
# MAGIC             OR Source_System IS NULL OR TRIM(Source_System) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Reason_Code IS NULL OR TRIM(Reason_Code) = ''
# MAGIC             OR Source_System IS NULL OR TRIM(Source_System) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: Reason_Code, Source_System',
# MAGIC   current_timestamp()
# MAGIC FROM order_reason
# MAGIC UNION ALL
# MAGIC -- POP check
# MAGIC SELECT 'PENDING', 'order_reason', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(
# MAGIC     100.0 * COUNT(Reason_Description) / COUNT(*),
# MAGIC     100.0 * COUNT(Reason_Category) / COUNT(*)
# MAGIC   ) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(
# MAGIC     100.0 * COUNT(Reason_Description) / COUNT(*),
# MAGIC     100.0 * COUNT(Reason_Category) / COUNT(*)
# MAGIC   ), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population check',
# MAGIC   current_timestamp()
# MAGIC FROM order_reason
# MAGIC UNION ALL
# MAGIC -- DRIFT check
# MAGIC SELECT 'PENDING', 'order_reason', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check',
# MAGIC   current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM order_reason) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'order_reason' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;