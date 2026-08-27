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
# MAGIC # dim_material — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Conformed material/product dimension. Union of SAP order_line materials and Salesforce quotation_line SKUs.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per unique material/SKU. ~800 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Material_Key = SHA2(Material_Number, 256)`
# MAGIC
# MAGIC ## Source
# MAGIC UNION of `silver.order_line` (Material_Number) and `silver.quotation_line` (SKU_Code), deduped by most frequent Item_Category and Product_Group.
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** fact_sales_order_line (Material_Key), fact_otd (Material_Key), fact_quotation_line (Material_Key), fact_return_line (Material_Key)
# MAGIC - **Child of:** Root dimension (no parent)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - Material master enrichment (description, weight, dimensions, product hierarchy) requires cross-domain join to product_catalog — DEFERRED
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** Verified (800 rows, 0 PK dups)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'dim_material' AS Entity, COUNT(*) AS Row_Count,
# MAGIC   MAX(_loaded_at) AS Last_Load
# MAGIC FROM dim_material;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Material_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Material_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Material_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_material;

# COMMAND ----------

# DBTITLE 1,BK Null & Population
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   SUM(CASE WHEN Material_Key IS NULL OR Material_Number IS NULL OR TRIM(Material_Number) = '' THEN 1 ELSE 0 END) AS Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN Material_Key IS NULL OR Material_Number IS NULL OR TRIM(Material_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_material;
# MAGIC
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Material_Number)/COUNT(*),2) AS Material_Number_Pct,
# MAGIC   ROUND(100.0*COUNT(Item_Category)/COUNT(*),2) AS Item_Category_Pct,
# MAGIC   ROUND(100.0*COUNT(Product_Group)/COUNT(*),2) AS Product_Group_Pct
# MAGIC FROM dim_material;

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Materials,
# MAGIC   COUNT(DISTINCT Item_Category) AS Distinct_Categories,
# MAGIC   COUNT(DISTINCT Product_Group) AS Distinct_Product_Groups,
# MAGIC   SUM(CASE WHEN Item_Category IS NULL THEN 1 ELSE 0 END) AS No_Item_Category,
# MAGIC   SUM(CASE WHEN Product_Group IS NULL THEN 1 ELSE 0 END) AS No_Product_Group
# MAGIC FROM dim_material;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT Material_Number, Item_Category, Product_Group
# MAGIC FROM dim_material
# MAGIC ORDER BY Material_Number
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_material';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'dim_material', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Material_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Material_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT Material_Key) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM dim_material
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_material', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Material_Key IS NULL OR Material_Number IS NULL OR TRIM(Material_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Material_Key IS NULL OR Material_Number IS NULL OR TRIM(Material_Number) = '' THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: Material_Key, Material_Number', current_timestamp()
# MAGIC FROM dim_material
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_material', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN 100.0*COUNT(Material_Number)/COUNT(*) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(100.0*COUNT(Material_Number)/COUNT(*), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Material_Number pop', current_timestamp()
# MAGIC FROM dim_material
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_material', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_material), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_material' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;