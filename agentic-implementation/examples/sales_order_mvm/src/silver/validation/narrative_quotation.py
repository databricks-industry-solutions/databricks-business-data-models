# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';
# MAGIC
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative — quotation
# MAGIC %md
# MAGIC ## quotation — Validation Narrative
# MAGIC
# MAGIC **Entity:** `quotation` · **Tier:** 1 · **Type:** DIM · **Strategy:** MV (full recompute)
# MAGIC
# MAGIC **Business Purpose:** Sales quotations from Salesforce CRM (`quote`). Represents formal commercial proposals issued to prospective customers with pricing, validity periods, and conversion probability.
# MAGIC
# MAGIC **Source:** `salesforce_crm_mvm.quote` · **Natural Key:** `quote_id`
# MAGIC
# MAGIC **Surrogate Key:** `quotation_id` = `SHA2(quote_id)` as BIGINT
# MAGIC
# MAGIC **FK Resolution:**
# MAGIC - `account_id` → `customer.account` (deferred — cross-domain)
# MAGIC - `price_list_id` → `pricing.price_list` (deferred — cross-domain)
# MAGIC - `sales_contract_id` → `sales_contract` (deferred — not in source)
# MAGIC
# MAGIC **Known Gaps:** All 3 FKs are deferred (cross-domain or not in source). No intra-domain FK to validate.
# MAGIC
# MAGIC **Build Manifest Row Count:** 4,000

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS row_count,
# MAGIC   COUNT(DISTINCT quotation_id) AS distinct_pk,
# MAGIC   COUNT(*) - COUNT(DISTINCT quotation_id) AS pk_duplicates,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT quotation_id) THEN 'PASS' ELSE 'FAIL' END AS pk_status
# MAGIC FROM quotation;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- BK: NK = number (quote_id mapped to 'number' column)
# MAGIC SELECT 'number' AS column_name, COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN number IS NULL OR TRIM(number) = '' THEN 1 ELSE 0 END) AS null_or_empty,
# MAGIC   CASE WHEN SUM(CASE WHEN number IS NULL OR TRIM(number)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END AS bk_status
# MAGIC FROM quotation;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC SELECT 'number' AS col, ROUND(COUNT(number)*100.0/COUNT(*),2) AS pop_pct FROM quotation
# MAGIC UNION ALL SELECT 'quotation_date', ROUND(COUNT(quotation_date)*100.0/COUNT(*),2) FROM quotation
# MAGIC UNION ALL SELECT 'quotation_status', ROUND(COUNT(quotation_status)*100.0/COUNT(*),2) FROM quotation
# MAGIC UNION ALL SELECT 'conversion_probability', ROUND(COUNT(conversion_probability)*100.0/COUNT(*),2) FROM quotation
# MAGIC UNION ALL SELECT 'quoted_value', ROUND(COUNT(quoted_value)*100.0/COUNT(*),2) FROM quotation
# MAGIC UNION ALL SELECT 'currency_code', ROUND(COUNT(currency_code)*100.0/COUNT(*),2) FROM quotation
# MAGIC UNION ALL SELECT 'source_system_key', ROUND(COUNT(source_system_key)*100.0/COUNT(*),2) FROM quotation;

# COMMAND ----------

# DBTITLE 1,Drift Check
# MAGIC %sql
# MAGIC SELECT 'quotation' AS table_name, 'ROW_COUNT' AS metric_type,
# MAGIC   CAST(cnt AS STRING) AS current_value, b.Baseline_Value, b.Tolerance_Pct,
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE'
# MAGIC     WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0) <= b.Tolerance_Pct THEN 'PASS'
# MAGIC     ELSE 'FAIL' END AS drift_status
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM quotation)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='quotation' AND b.Column_Name='quotation_id' AND b.Metric_Type='ROW_COUNT';

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_rows, COUNT(DISTINCT number) AS distinct_quotes,
# MAGIC   COUNT(DISTINCT quotation_status) AS distinct_statuses,
# MAGIC   MIN(quotation_date) AS earliest, MAX(quotation_date) AS latest,
# MAGIC   MIN(quoted_value) AS min_value, AVG(quoted_value) AS avg_value, MAX(quoted_value) AS max_value,
# MAGIC   MAX(last_modified_timestamp) AS last_load
# MAGIC FROM quotation;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT quotation_id, number, quotation_date, quotation_status,
# MAGIC   conversion_probability, quoted_value, currency_code, source_system, source_system_key
# MAGIC FROM quotation ORDER BY number LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id='PENDING' AND Table_Name='quotation';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING','quotation','PK_Uniqueness','PK',
# MAGIC   CASE WHEN COUNT(*)=COUNT(DISTINCT quotation_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0',CAST(COUNT(*)-COUNT(DISTINCT quotation_id) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'PK_Uniqueness: '||CASE WHEN COUNT(*)=COUNT(DISTINCT quotation_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   current_timestamp()
# MAGIC FROM quotation
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation','BK_Null_Check_number','BK',
# MAGIC   CASE WHEN SUM(CASE WHEN number IS NULL OR TRIM(number)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0',CAST(SUM(CASE WHEN number IS NULL OR TRIM(number)='' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'BK_Null_Check_number: '||CASE WHEN SUM(CASE WHEN number IS NULL OR TRIM(number)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   current_timestamp()
# MAGIC FROM quotation
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation','POP_Key_Columns','POP',
# MAGIC   CASE WHEN MIN(p)>=95.0 THEN 'PASS' WHEN MIN(p)>=90.0 THEN 'WARN' ELSE 'FAIL' END,
# MAGIC   '95.0',CAST(ROUND(MIN(p),2) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'POP_Key_Columns: min='||CAST(ROUND(MIN(p),2) AS STRING)||'%',current_timestamp()
# MAGIC FROM (SELECT COUNT(number)*100.0/COUNT(*) AS p FROM quotation
# MAGIC   UNION ALL SELECT COUNT(quotation_date)*100.0/COUNT(*) FROM quotation
# MAGIC   UNION ALL SELECT COUNT(quotation_status)*100.0/COUNT(*) FROM quotation
# MAGIC   UNION ALL SELECT COUNT(quoted_value)*100.0/COUNT(*) FROM quotation
# MAGIC   UNION ALL SELECT COUNT(source_system_key)*100.0/COUNT(*) FROM quotation)
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING','quotation','DRIFT_Row_Count','DRIFT',
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'PASS'
# MAGIC     WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0)<=COALESCE(b.Tolerance_Pct,20) THEN 'PASS'
# MAGIC     ELSE 'FAIL' END,
# MAGIC   COALESCE(b.Baseline_Value,'NEW_BASELINE'),CAST(cnt AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'DRIFT_Row_Count: '||CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE='||CAST(cnt AS STRING) ELSE 'current='||CAST(cnt AS STRING) END,
# MAGIC   current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM quotation)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='quotation' AND b.Column_Name='quotation_id' AND b.Metric_Type='ROW_COUNT';