# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT 'sales_order_gold_sdp';

# COMMAND ----------

# DBTITLE 1,Set Context
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative Header
# MAGIC %md
# MAGIC # bridge_order_partner — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Pivoted bridge table resolving the M:M relationship between orders and partner functions. One row per order with pivoted columns for each partner role (AG/RE/RG/WE).
# MAGIC
# MAGIC ## Grain
# MAGIC One row per order (order_id). 5000 rows = same as order count.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `order_id` (identity passthrough from silver order_partner pivot)
# MAGIC
# MAGIC ## Source
# MAGIC `silver.order_partner` pivoted by `partner_function` (AG=Sold-To, RE=Bill-To, RG=Payer, WE=Ship-To)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Resolves:** fact_sales_order_line.order_id ↔ partner functions
# MAGIC - **Child of:** Root bridge (no parent FK in star schema sense)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - None
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** Verified (5000 rows, 0 PK dups, 1:1 with fact grain via order_id)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'bridge_order_partner' AS Entity, COUNT(*) AS Row_Count FROM bridge_order_partner;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT order_id) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT order_id) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM bridge_order_partner;

# COMMAND ----------

# DBTITLE 1,BK Null & Population
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS Null_Count,
# MAGIC   CASE WHEN SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM bridge_order_partner;
# MAGIC
# MAGIC -- Partner function population (pivot columns)
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Sold_To_Number)/COUNT(*),2) AS Sold_To_Pct,
# MAGIC   ROUND(100.0*COUNT(Bill_To_Number)/COUNT(*),2) AS Bill_To_Pct,
# MAGIC   ROUND(100.0*COUNT(Ship_To_Number)/COUNT(*),2) AS Ship_To_Pct
# MAGIC FROM bridge_order_partner;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT order_id, Sold_To_Number, Sold_To_Name, Ship_To_Number, Ship_To_Name, Bill_To_Number
# MAGIC FROM bridge_order_partner
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'bridge_order_partner';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'bridge_order_partner', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT order_id) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT order_id) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM bridge_order_partner
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'bridge_order_partner', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: order_id', current_timestamp()
# MAGIC FROM bridge_order_partner
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'bridge_order_partner', 'Population_Pivot_Columns', 'POP',
# MAGIC   CASE WHEN 100.0*COUNT(Sold_To_Number)/COUNT(*) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(100.0*COUNT(Sold_To_Number)/COUNT(*), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Sold-To pop rate', current_timestamp()
# MAGIC FROM bridge_order_partner
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'bridge_order_partner', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM bridge_order_partner), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'bridge_order_partner' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;