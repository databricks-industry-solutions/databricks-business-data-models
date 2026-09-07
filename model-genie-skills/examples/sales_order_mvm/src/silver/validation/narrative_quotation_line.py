# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative — quotation_line
# MAGIC %md
# MAGIC ## quotation_line — Validation Narrative
# MAGIC
# MAGIC **Entity:** `quotation_line` · **Tier:** 2 · **Type:** DIM · **Strategy:** MV
# MAGIC
# MAGIC **Source:** `salesforce_crm_mvm.quote_line` · **NK:** `quote_line_id`
# MAGIC
# MAGIC **SK:** `quotation_line_id` = `SHA2(quote_line_id)`
# MAGIC
# MAGIC **FK:** `quotation_id` → `quotation` (direct SHA2)
# MAGIC
# MAGIC **Row Count:** 11,982

# COMMAND ----------

# DBTITLE 1,Row Count & PK
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS row_count, COUNT(DISTINCT quotation_line_id) AS distinct_pk,
# MAGIC   COUNT(*)-COUNT(DISTINCT quotation_line_id) AS pk_dups,
# MAGIC   CASE WHEN COUNT(*)=COUNT(DISTINCT quotation_line_id) THEN 'PASS' ELSE 'FAIL' END AS pk_status
# MAGIC FROM quotation_line;

# COMMAND ----------

# DBTITLE 1,FK Check — quotation_id
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total,
# MAGIC   SUM(CASE WHEN p.quotation_id IS NULL THEN 1 ELSE 0 END) AS orphans,
# MAGIC   ROUND(SUM(CASE WHEN p.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*),4) AS orphan_pct
# MAGIC FROM quotation_line c LEFT JOIN quotation p ON c.quotation_id=p.quotation_id;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'source_system_key' AS col, COUNT(*) AS total,
# MAGIC   SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END) AS null_empty,
# MAGIC   CASE WHEN SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END AS bk_status
# MAGIC FROM quotation_line;

# COMMAND ----------

# DBTITLE 1,Population
# MAGIC %sql
# MAGIC SELECT 'sku_code' AS col, ROUND(COUNT(sku_code)*100.0/COUNT(*),2) AS pop FROM quotation_line
# MAGIC UNION ALL SELECT 'quantity', ROUND(COUNT(quantity)*100.0/COUNT(*),2) FROM quotation_line
# MAGIC UNION ALL SELECT 'net_price', ROUND(COUNT(net_price)*100.0/COUNT(*),2) FROM quotation_line
# MAGIC UNION ALL SELECT 'net_value', ROUND(COUNT(net_value)*100.0/COUNT(*),2) FROM quotation_line
# MAGIC UNION ALL SELECT 'source_system_key', ROUND(COUNT(source_system_key)*100.0/COUNT(*),2) FROM quotation_line;

# COMMAND ----------

# DBTITLE 1,Drift
# MAGIC %sql
# MAGIC SELECT 'quotation_line' AS t, CAST(cnt AS STRING) AS curr,
# MAGIC   b.Baseline_Value, CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE' ELSE 'CHECK' END AS drift_status
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM quotation_line)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='quotation_line' AND b.Column_Name='quotation_line_id' AND b.Metric_Type='ROW_COUNT';

# COMMAND ----------

# DBTITLE 1,Profile & Sample
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS rows, COUNT(DISTINCT quotation_id) AS quotes, COUNT(DISTINCT sku_code) AS skus,
# MAGIC   MIN(net_value) AS min_val, AVG(net_value) AS avg_val, MAX(net_value) AS max_val
# MAGIC FROM quotation_line;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id='PENDING' AND Table_Name='quotation_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING','quotation_line','PK_Uniqueness','PK',
# MAGIC   CASE WHEN COUNT(*)=COUNT(DISTINCT quotation_line_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0',CAST(COUNT(*)-COUNT(DISTINCT quotation_line_id) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'PK',current_timestamp()
# MAGIC FROM quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation_line','FK_quotation_id','FK',
# MAGIC   CASE WHEN SUM(CASE WHEN p.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*)<=1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0',CAST(ROUND(SUM(CASE WHEN p.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*),4) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),'FK_quotation_id',current_timestamp()
# MAGIC FROM quotation_line c LEFT JOIN quotation p ON c.quotation_id=p.quotation_id
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation_line','BK_Null_Check','BK',
# MAGIC   CASE WHEN SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0',CAST(SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),'BK',current_timestamp()
# MAGIC FROM quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation_line','POP_Key_Columns','POP',
# MAGIC   CASE WHEN MIN(p)>=95.0 THEN 'PASS' WHEN MIN(p)>=90.0 THEN 'WARN' ELSE 'FAIL' END,
# MAGIC   '95.0',CAST(ROUND(MIN(p),2) AS STRING),NULL,FALSE,CAST(NULL AS STRING),'POP',current_timestamp()
# MAGIC FROM (SELECT COUNT(sku_code)*100.0/COUNT(*) AS p FROM quotation_line
# MAGIC   UNION ALL SELECT COUNT(quantity)*100.0/COUNT(*) FROM quotation_line
# MAGIC   UNION ALL SELECT COUNT(net_value)*100.0/COUNT(*) FROM quotation_line
# MAGIC   UNION ALL SELECT COUNT(source_system_key)*100.0/COUNT(*) FROM quotation_line)
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation_line','DRIFT_Row_Count','DRIFT',
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'PASS'
# MAGIC     WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0)<=COALESCE(b.Tolerance_Pct,20) THEN 'PASS'
# MAGIC     ELSE 'FAIL' END,
# MAGIC   COALESCE(b.Baseline_Value,'NEW_BASELINE'),CAST(cnt AS STRING),NULL,FALSE,CAST(NULL AS STRING),'DRIFT',current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM quotation_line)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='quotation_line' AND b.Column_Name='quotation_line_id' AND b.Metric_Type='ROW_COUNT';