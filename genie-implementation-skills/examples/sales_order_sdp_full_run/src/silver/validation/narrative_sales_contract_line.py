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
# MAGIC # sales_contract_line — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Material-level commitments within framework agreements. Captures line quantities, values, and pricing.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per contract + line number combination. Expected ~373 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vbeln + posnr` → SHA2 → `sales_contract_line_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.veda_item` (373 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** None
# MAGIC - **Child of:** sales_contract (FK: sales_contract_id = SHA2(vbeln))
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - None
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 2

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'sales_contract_line' AS Entity, COUNT(*) AS Row_Count, MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM sales_contract_line;
# MAGIC
# MAGIC SELECT 'sales_contract_line' AS Entity, 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT sales_contract_line_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT sales_contract_line_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_line_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' THEN 1 ELSE 0 END) AS Contract_Number_Dropped,
# MAGIC   SUM(CASE WHEN Line_Number IS NULL OR TRIM(Line_Number) = '' THEN 1 ELSE 0 END) AS Line_Number_Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' OR Line_Number IS NULL OR TRIM(Line_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,FK Integration — sales_contract
# MAGIC %sql
# MAGIC -- FK resolution: sales_contract_id → sales_contract
# MAGIC SELECT
# MAGIC   'sales_contract_line' AS Entity,
# MAGIC   'FK_sales_contract' AS Check_Name,
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN p.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) AS Resolved,
# MAGIC   ROUND(100.0 * SUM(CASE WHEN p.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS Resolution_Pct,
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM sales_contract_line c
# MAGIC LEFT JOIN sales_contract p ON c.sales_contract_id = p.sales_contract_id;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Material_Number) / COUNT(*), 2) AS Material_Number_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Target_Quantity) / COUNT(*), 2) AS Target_Quantity_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Net_Price) / COUNT(*), 2) AS Net_Price_Pop_Pct
# MAGIC FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC WITH current_stats AS (SELECT COUNT(*) AS current_row_count FROM sales_contract_line),
# MAGIC baseline AS (SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'sales_contract_line' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE)
# MAGIC SELECT 'sales_contract_line' AS Entity, 'Drift_ROW_COUNT' AS Check_Name,
# MAGIC   b.baseline_row_count, c.current_row_count, b.Tolerance_Pct,
# MAGIC   ROUND(ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0), 2) AS Drift_Pct,
# MAGIC   CASE WHEN ABS(c.current_row_count - b.baseline_row_count) * 100.0 / NULLIF(b.baseline_row_count, 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END AS Status
# MAGIC FROM current_stats c, baseline b;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'sales_contract_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_line_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT sales_contract_line_id) AS STRING), NULL, FALSE, NULL, 'PK uniqueness check', current_timestamp()
# MAGIC FROM sales_contract_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' OR Line_Number IS NULL OR TRIM(Line_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Contract_Number IS NULL OR TRIM(Contract_Number) = '' OR Line_Number IS NULL OR TRIM(Line_Number) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check', current_timestamp()
# MAGIC FROM sales_contract_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'FK_sales_contract', 'INTEGRATION',
# MAGIC   CASE WHEN 100.0 * SUM(CASE WHEN p.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) >= 95.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(100.0 * SUM(CASE WHEN p.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'FK resolution: sales_contract_id', current_timestamp()
# MAGIC FROM sales_contract_line c LEFT JOIN sales_contract p ON c.sales_contract_id = p.sales_contract_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Material_Number)/COUNT(*), 100.0*COUNT(Net_Price)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Material_Number)/COUNT(*), 100.0*COUNT(Net_Price)/COUNT(*)), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population', current_timestamp()
# MAGIC FROM sales_contract_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_contract_line) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'sales_contract_line' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;