# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';
# MAGIC
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative — sales_contract_line
# MAGIC %md
# MAGIC ## sales_contract_line — Validation Narrative
# MAGIC
# MAGIC **Entity:** `sales_contract_line` · **Tier:** 1 · **Type:** DIM · **Strategy:** MV (full recompute)
# MAGIC
# MAGIC **Business Purpose:** Individual line items within sales contracts from SAP SD (`veda_item`). Each line commits a specific material at a negotiated price and quantity under the parent contract.
# MAGIC
# MAGIC **Source:** `sap_sd_mvm.veda_item` · **Natural Key:** `vbeln, posnr` (composite)
# MAGIC
# MAGIC **Surrogate Key:** `sales_contract_line_id` = `SHA2(vbeln|posnr)` as BIGINT
# MAGIC
# MAGIC **FK Resolution:**
# MAGIC - `sales_contract_id` → `sales_contract` (direct SHA2 — same hash formula as parent PK)
# MAGIC - `plant_id` → `manufacturing.plant` (deferred — cross-domain)
# MAGIC - `sku_id` → `product_catalog.sku` (deferred — cross-domain)
# MAGIC
# MAGIC **Known Gaps:** plant_id and sku_id are NULL (deferred cross-domain FKs).
# MAGIC
# MAGIC **Build Manifest Row Count:** 373

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(*) AS row_count,
# MAGIC   COUNT(DISTINCT sales_contract_line_id) AS distinct_pk,
# MAGIC   COUNT(*) - COUNT(DISTINCT sales_contract_line_id) AS pk_duplicates,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_line_id) THEN 'PASS' ELSE 'FAIL' END AS pk_status
# MAGIC FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,FK Check — sales_contract_id
# MAGIC %sql
# MAGIC -- FK: sales_contract_line.sales_contract_id -> sales_contract.sales_contract_id
# MAGIC SELECT
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN p.sales_contract_id IS NULL THEN 1 ELSE 0 END) AS orphan_count,
# MAGIC   ROUND(SUM(CASE WHEN p.sales_contract_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) AS orphan_pct,
# MAGIC   CASE WHEN SUM(CASE WHEN p.sales_contract_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) <= 1.0 THEN 'PASS' ELSE 'FAIL' END AS fk_status
# MAGIC FROM sales_contract_line c
# MAGIC LEFT JOIN sales_contract p ON c.sales_contract_id = p.sales_contract_id;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- BK Null Check: composite NK = source_system_line_key (vbeln|posnr)
# MAGIC SELECT
# MAGIC   'source_system_line_key' AS column_name,
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key) = '' THEN 1 ELSE 0 END) AS null_or_empty,
# MAGIC   CASE WHEN SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS bk_status
# MAGIC FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC SELECT 'material_number' AS col, ROUND(COUNT(material_number)*100.0/COUNT(*),2) AS pop_pct FROM sales_contract_line
# MAGIC UNION ALL SELECT 'target_quantity', ROUND(COUNT(target_quantity)*100.0/COUNT(*),2) FROM sales_contract_line
# MAGIC UNION ALL SELECT 'target_value', ROUND(COUNT(target_value)*100.0/COUNT(*),2) FROM sales_contract_line
# MAGIC UNION ALL SELECT 'net_price', ROUND(COUNT(net_price)*100.0/COUNT(*),2) FROM sales_contract_line
# MAGIC UNION ALL SELECT 'source_system_line_key', ROUND(COUNT(source_system_line_key)*100.0/COUNT(*),2) FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,Drift Check
# MAGIC %sql
# MAGIC SELECT
# MAGIC   'sales_contract_line' AS table_name, 'ROW_COUNT' AS metric_type,
# MAGIC   CAST(cnt AS STRING) AS current_value,
# MAGIC   b.Baseline_Value, b.Tolerance_Pct,
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE'
# MAGIC     WHEN ABS(cnt - CAST(b.Baseline_Value AS BIGINT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS BIGINT), 0) <= b.Tolerance_Pct THEN 'PASS'
# MAGIC     ELSE 'FAIL' END AS drift_status
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_contract_line)
# MAGIC LEFT JOIN _data_drift_baseline b
# MAGIC   ON b.Table_Name = 'sales_contract_line' AND b.Column_Name = 'sales_contract_line_id' AND b.Metric_Type = 'ROW_COUNT';

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_rows, COUNT(DISTINCT sales_contract_id) AS distinct_contracts,
# MAGIC   COUNT(DISTINCT material_number) AS distinct_materials,
# MAGIC   MIN(target_value) AS min_val, AVG(target_value) AS avg_val, MAX(target_value) AS max_val,
# MAGIC   MAX(last_modified_timestamp) AS last_load
# MAGIC FROM sales_contract_line;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT sales_contract_line_id, sales_contract_id, material_number,
# MAGIC   target_quantity, target_value, net_price, source_system, source_system_line_key
# MAGIC FROM sales_contract_line ORDER BY source_system_line_key LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail
# MAGIC WHERE Run_Id = 'PENDING' AND Table_Name = 'sales_contract_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_line_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT sales_contract_line_id) AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'PK_Uniqueness: ' || CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_line_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   current_timestamp()
# MAGIC FROM sales_contract_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'FK_sales_contract_id', 'FK',
# MAGIC   CASE WHEN SUM(CASE WHEN p.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(SUM(CASE WHEN p.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*),4) AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'FK_sales_contract_id: orphan rate=' || CAST(ROUND(SUM(CASE WHEN p.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS STRING) || '%',
# MAGIC   current_timestamp()
# MAGIC FROM sales_contract_line c LEFT JOIN sales_contract p ON c.sales_contract_id = p.sales_contract_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key)='' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'BK_Null_Check: ' || CASE WHEN SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   current_timestamp()
# MAGIC FROM sales_contract_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'POP_Key_Columns', 'POP',
# MAGIC   CASE WHEN MIN(p) >= 95.0 THEN 'PASS' WHEN MIN(p) >= 90.0 THEN 'WARN' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(MIN(p),2) AS STRING), NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'POP_Key_Columns: min=' || CAST(ROUND(MIN(p),2) AS STRING) || '%', current_timestamp()
# MAGIC FROM (SELECT COUNT(material_number)*100.0/COUNT(*) AS p FROM sales_contract_line
# MAGIC   UNION ALL SELECT COUNT(target_quantity)*100.0/COUNT(*) FROM sales_contract_line
# MAGIC   UNION ALL SELECT COUNT(target_value)*100.0/COUNT(*) FROM sales_contract_line
# MAGIC   UNION ALL SELECT COUNT(source_system_line_key)*100.0/COUNT(*) FROM sales_contract_line)
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'sales_contract_line', 'DRIFT_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'PASS'
# MAGIC     WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0) <= COALESCE(b.Tolerance_Pct,20) THEN 'PASS'
# MAGIC     ELSE 'FAIL' END,
# MAGIC   COALESCE(b.Baseline_Value,'NEW_BASELINE'), CAST(cnt AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'DRIFT_Row_Count: ' || CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE=' || CAST(cnt AS STRING) ELSE 'current=' || CAST(cnt AS STRING) END,
# MAGIC   current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_contract_line)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='sales_contract_line' AND b.Column_Name='sales_contract_line_id' AND b.Metric_Type='ROW_COUNT';