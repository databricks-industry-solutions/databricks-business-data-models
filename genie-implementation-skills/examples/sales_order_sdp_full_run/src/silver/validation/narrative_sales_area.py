# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
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
# MAGIC # sales_area — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Sales organization structure defining org + channel + division combinations. Root reference entity for the sales order domain.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per unique Sales Organization + Distribution Channel + Division combination. Expected ~4 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vkorg | vtweg | spart` → SHA2 → `sales_area_id` (STRING surrogate)
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.tvta` (4 rows)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** order (via sales_area_id)
# MAGIC - **Child of:** Root reference (no parent)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - channel_config and sales_contract cannot resolve sales_area_id FK (source lacks vkorg/spart)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 0 (root)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC -- Row count and freshness
# MAGIC SELECT
# MAGIC   'sales_area' AS Entity,
# MAGIC   COUNT(*) AS Row_Count,
# MAGIC   MAX(_loaded_at) AS Last_Load_Timestamp,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM sales_area;
# MAGIC
# MAGIC -- PK uniqueness: expect 0 duplicates
# MAGIC SELECT
# MAGIC   'sales_area' AS Entity,
# MAGIC   'PK_Uniqueness' AS Check_Name,
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT sales_area_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT sales_area_id) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_area_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM sales_area;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- Business Key null/dropped data check
# MAGIC -- NK columns: Sales_Organization, Distribution_Channel, Division (compose SHA2 surrogate)
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Sales_Organization IS NULL OR TRIM(Sales_Organization) = '' THEN 1 ELSE 0 END) AS Sales_Organization_Dropped,
# MAGIC   SUM(CASE WHEN Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = '' THEN 1 ELSE 0 END) AS Distribution_Channel_Dropped,
# MAGIC   SUM(CASE WHEN Division IS NULL OR TRIM(Division) = '' THEN 1 ELSE 0 END) AS Division_Dropped,
# MAGIC   CASE
# MAGIC     WHEN SUM(CASE WHEN Sales_Organization IS NULL OR TRIM(Sales_Organization) = ''
# MAGIC               OR Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = ''
# MAGIC               OR Division IS NULL OR TRIM(Division) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS'
# MAGIC     ELSE 'FAIL'
# MAGIC   END AS Status
# MAGIC FROM sales_area;

# COMMAND ----------

# DBTITLE 1,Column Population
# MAGIC %sql
# MAGIC -- Column population rates for key business columns
# MAGIC SELECT
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Currency_Code) / COUNT(*), 2) AS Currency_Code_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Pricing_Procedure) / COUNT(*), 2) AS Pricing_Procedure_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Sales_Area_Description) / COUNT(*), 2) AS Sales_Area_Description_Pop_Pct
# MAGIC FROM sales_area;

# COMMAND ----------

# DBTITLE 1,Drift Detection
# MAGIC %sql
# MAGIC -- Drift detection: compare current row count to baseline
# MAGIC WITH current_stats AS (
# MAGIC   SELECT COUNT(*) AS current_row_count FROM sales_area
# MAGIC ),
# MAGIC baseline AS (
# MAGIC   SELECT CAST(Baseline_Value AS INT) AS baseline_row_count, Tolerance_Pct
# MAGIC   FROM _data_drift_baseline
# MAGIC   WHERE Table_Name = 'sales_area' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE
# MAGIC )
# MAGIC SELECT
# MAGIC   'sales_area' AS Entity,
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

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC -- Data profile: all rows for this compact reference table (4 rows)
# MAGIC SELECT
# MAGIC   sales_area_id,
# MAGIC   Sales_Organization,
# MAGIC   Distribution_Channel,
# MAGIC   Division,
# MAGIC   Currency_Code,
# MAGIC   Pricing_Procedure,
# MAGIC   Sales_Area_Description,
# MAGIC   _source_system
# MAGIC FROM sales_area
# MAGIC ORDER BY Sales_Organization, Distribution_Channel, Division;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC -- Write validation results to metadata tables (PENDING→claim)
# MAGIC DELETE FROM _validation_check_detail
# MAGIC WHERE Run_Id = 'PENDING' AND Table_Name = 'sales_area';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC -- PK check
# MAGIC SELECT 'PENDING', 'sales_area', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_area_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT sales_area_id) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK uniqueness: ' || CAST(COUNT(*) - COUNT(DISTINCT sales_area_id) AS STRING) || ' duplicates',
# MAGIC   current_timestamp()
# MAGIC FROM sales_area
# MAGIC UNION ALL
# MAGIC -- BK check
# MAGIC SELECT 'PENDING', 'sales_area', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Sales_Organization IS NULL OR TRIM(Sales_Organization) = ''
# MAGIC             OR Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = ''
# MAGIC             OR Division IS NULL OR TRIM(Division) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Sales_Organization IS NULL OR TRIM(Sales_Organization) = ''
# MAGIC             OR Distribution_Channel IS NULL OR TRIM(Distribution_Channel) = ''
# MAGIC             OR Division IS NULL OR TRIM(Division) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'BK null check: Sales_Organization, Distribution_Channel, Division',
# MAGIC   current_timestamp()
# MAGIC FROM sales_area
# MAGIC UNION ALL
# MAGIC -- POP check (minimum population across key columns)
# MAGIC SELECT 'PENDING', 'sales_area', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(
# MAGIC     100.0 * COUNT(Currency_Code) / COUNT(*),
# MAGIC     100.0 * COUNT(Sales_Area_Description) / COUNT(*)
# MAGIC   ) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(
# MAGIC     100.0 * COUNT(Currency_Code) / COUNT(*),
# MAGIC     100.0 * COUNT(Sales_Area_Description) / COUNT(*)
# MAGIC   ), 2) AS STRING),
# MAGIC   NULL, FALSE, NULL, 'Key column population check',
# MAGIC   current_timestamp()
# MAGIC FROM sales_area
# MAGIC UNION ALL
# MAGIC -- DRIFT check
# MAGIC SELECT 'PENDING', 'sales_area', 'Drift_ROW_COUNT', 'DRIFT',
# MAGIC   CASE WHEN ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0) > b.Tolerance_Pct THEN 'FAIL' ELSE 'PASS' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(c.cnt AS STRING),
# MAGIC   ROUND(ABS(c.cnt - CAST(b.Baseline_Value AS INT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS INT), 0), 4),
# MAGIC   FALSE, NULL, 'Row count drift check',
# MAGIC   current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_area) c,
# MAGIC      (SELECT Baseline_Value, Tolerance_Pct FROM _data_drift_baseline WHERE Table_Name = 'sales_area' AND Metric_Type = 'ROW_COUNT' AND Is_Active = TRUE) b;