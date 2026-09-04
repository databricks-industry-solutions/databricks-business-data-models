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
# MAGIC # order — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Core confirmed B2B sales order headers. Central fact entity for the sales order domain.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per sales document. Expected ~5,000 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vbeln` → SHA2 → `order_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.vbak` (5,000 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** order_line, order_partner, order_schedule_line, edi_order_message, order_credit_check, return_order, otd_record
# MAGIC - **Child of:** sales_area (100%), order_reason (when augru populated), quotation (~19.9%)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - quotation_id resolved ~19.9% (only converted quotes have matching vbeln)
# MAGIC - order_reason_id NULL when no rejection reason code
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 3 (central fact)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'order' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM `order`;
# MAGIC
# MAGIC SELECT 'order' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT order_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT order_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM `order`;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Order_Number IS NULL OR TRIM(Order_Number) = '' THEN 1 ELSE 0 END) AS Order_Number_Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN Order_Number IS NULL OR TRIM(Order_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM `order`;

# COMMAND ----------

# DBTITLE 1,FK Integration — sales_area + order_reason + quotation
# MAGIC %sql
# MAGIC -- FK: sales_area_id (expect 100%)
# MAGIC SELECT 'order' AS Entity, 'FK_sales_area' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN sa.sales_area_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN sa.sales_area_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct
# MAGIC FROM `order` o LEFT JOIN sales_area sa ON o.sales_area_id = sa.sales_area_id;
# MAGIC
# MAGIC -- FK: quotation_id (expect ~19.9%)
# MAGIC SELECT 'order' AS Entity, 'FK_quotation' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END) AS Non_Null_FK,
# MAGIC   SUM(CASE WHEN q.quotation_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN q.quotation_id IS NOT NULL THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END), 0), 2) AS Resolution_Of_NonNull_Pct
# MAGIC FROM `order` o LEFT JOIN quotation q ON o.quotation_id = q.quotation_id;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Order_Date) / COUNT(*), 2) AS Order_Date_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Net_Value) / COUNT(*), 2) AS Net_Value_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Currency) / COUNT(*), 2) AS Currency_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Overall_Status) / COUNT(*), 2) AS Overall_Status_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Customer_Number) / COUNT(*), 2) AS Customer_Number_Pop_Pct
# MAGIC FROM `order`;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM `order`),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'order' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'order' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'order';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'order', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT order_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM `order`
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'order', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Order_Number IS NULL OR TRIM(Order_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Order_Number IS NULL OR TRIM(Order_Number) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: Order_Number', current_timestamp()
# MAGIC FROM `order`
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'order', 'FK_sales_area', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN sa.sales_area_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN sa.sales_area_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: sales_area_id (100% expected)', current_timestamp()
# MAGIC FROM `order` o LEFT JOIN sales_area sa ON o.sales_area_id = sa.sales_area_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'order', 'FK_quotation', 'INTEGRATION',
# MAGIC   CASE WHEN SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '0 orphans', CAST(SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: quotation_id (~19.9% populated)', current_timestamp()
# MAGIC FROM `order` o LEFT JOIN quotation q ON o.quotation_id = q.quotation_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'order', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Order_Date)/COUNT(*), 100.0*COUNT(Net_Value)/COUNT(*), 100.0*COUNT(Currency)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Order_Date)/COUNT(*), 100.0*COUNT(Net_Value)/COUNT(*), 100.0*COUNT(Currency)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM `order`
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'order', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM `order`) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'order' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;