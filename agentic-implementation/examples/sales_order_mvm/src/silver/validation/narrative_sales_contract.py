# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';
# MAGIC
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative — sales_contract
# MAGIC %md
# MAGIC ## sales_contract — Validation Narrative
# MAGIC
# MAGIC **Entity:** `sales_contract` · **Tier:** 0 (root dimension) · **Type:** DIM · **Strategy:** MV (full recompute)
# MAGIC
# MAGIC **Business Purpose:** Sales contracts (blanket agreements) from SAP SD (`veda`) representing committed volume/value purchase agreements between customers and the company. These are root-level documents — other entities (contract lines, orders, quotations, delivery schedules) reference them.
# MAGIC
# MAGIC **Source:** `sap_sd_mvm.veda` · **Natural Key:** `vbeln` (contract number)
# MAGIC
# MAGIC **Surrogate Key:** `sales_contract_id` = `SHA2(vbeln)` as BIGINT
# MAGIC
# MAGIC **FK Resolution:** None — this is a root dimension with no intra-domain parent FKs.
# MAGIC
# MAGIC **Known Gaps / Annotations:**
# MAGIC - No cross-domain FK dependencies
# MAGIC - All 120 source rows expected; small reference table
# MAGIC
# MAGIC **Build Manifest Row Count:** 120

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC -- Row Count & PK Uniqueness
# MAGIC SELECT
# MAGIC   COUNT(*) AS row_count,
# MAGIC   COUNT(DISTINCT sales_contract_id) AS distinct_pk,
# MAGIC   COUNT(*) - COUNT(DISTINCT sales_contract_id) AS pk_duplicates,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_id) THEN 'PASS' ELSE 'FAIL' END AS pk_status
# MAGIC FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- BK Null Check: natural key columns must not be NULL or empty
# MAGIC -- NK derived from DDL comment: SHA2(vbeln) → NK = contract_number
# MAGIC SELECT
# MAGIC   'contract_number' AS column_name,
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN contract_number IS NULL OR TRIM(contract_number) = '' THEN 1 ELSE 0 END) AS null_or_empty,
# MAGIC   ROUND(SUM(CASE WHEN contract_number IS NULL OR TRIM(contract_number) = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) AS null_pct,
# MAGIC   CASE WHEN SUM(CASE WHEN contract_number IS NULL OR TRIM(contract_number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS bk_status
# MAGIC FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC -- POPULATION: non-null coverage of key business columns
# MAGIC SELECT
# MAGIC   'contract_number' AS col, ROUND(COUNT(contract_number)*100.0/COUNT(*),2) AS pop_pct
# MAGIC FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'customer_account_number', ROUND(COUNT(customer_account_number)*100.0/COUNT(*),2) FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'valid_from', ROUND(COUNT(valid_from)*100.0/COUNT(*),2) FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'valid_to', ROUND(COUNT(valid_to)*100.0/COUNT(*),2) FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'target_quantity', ROUND(COUNT(target_quantity)*100.0/COUNT(*),2) FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'target_value', ROUND(COUNT(target_value)*100.0/COUNT(*),2) FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'contract_status', ROUND(COUNT(contract_status)*100.0/COUNT(*),2) FROM sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'source_system_key', ROUND(COUNT(source_system_key)*100.0/COUNT(*),2) FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,Drift Check
# MAGIC %sql
# MAGIC -- DRIFT: compare current stats to baseline (first run = establish baseline)
# MAGIC SELECT
# MAGIC   'sales_contract' AS table_name,
# MAGIC   'ROW_COUNT' AS metric_type,
# MAGIC   CAST(cnt AS STRING) AS current_value,
# MAGIC   b.Baseline_Value,
# MAGIC   b.Tolerance_Pct,
# MAGIC   CASE
# MAGIC     WHEN b.Baseline_Value IS NULL THEN 'BASELINE'
# MAGIC     WHEN ABS(cnt - CAST(b.Baseline_Value AS BIGINT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS BIGINT), 0) <= b.Tolerance_Pct THEN 'PASS'
# MAGIC     ELSE 'FAIL'
# MAGIC   END AS drift_status
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_contract)
# MAGIC LEFT JOIN _data_drift_baseline b
# MAGIC   ON b.Table_Name = 'sales_contract' AND b.Column_Name = 'sales_contract_id' AND b.Metric_Type = 'ROW_COUNT';

# COMMAND ----------

# DBTITLE 1,Data Profile — Shape & Coverage
# MAGIC %sql
# MAGIC -- Data Profile: shape, coverage, distributions
# MAGIC SELECT
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   COUNT(DISTINCT contract_number) AS distinct_contracts,
# MAGIC   COUNT(DISTINCT customer_account_number) AS distinct_customers,
# MAGIC   COUNT(DISTINCT contract_status) AS distinct_statuses,
# MAGIC   MIN(valid_from) AS earliest_valid_from,
# MAGIC   MAX(valid_to) AS latest_valid_to,
# MAGIC   MIN(target_value) AS min_target_value,
# MAGIC   AVG(target_value) AS avg_target_value,
# MAGIC   MAX(target_value) AS max_target_value,
# MAGIC   MAX(last_modified_timestamp) AS last_load
# MAGIC FROM sales_contract;

# COMMAND ----------

# DBTITLE 1,Sample Rows — Representative Records
# MAGIC %sql
# MAGIC -- Sample Rows: typical records + edge cases
# MAGIC SELECT sales_contract_id, contract_number, customer_account_number,
# MAGIC        valid_from, valid_to, target_quantity, target_value,
# MAGIC        contract_status, source_system, source_system_key
# MAGIC FROM sales_contract
# MAGIC ORDER BY contract_number
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC -- Write validation results to metadata tables
# MAGIC DELETE FROM _validation_check_detail
# MAGIC WHERE Run_Id = 'PENDING' AND Table_Name = 'sales_contract';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC -- PK Uniqueness
# MAGIC SELECT 'PENDING', 'sales_contract', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT sales_contract_id) AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'PK_Uniqueness: ' || CASE WHEN COUNT(*) = COUNT(DISTINCT sales_contract_id) THEN 'PASS (0 dups)' ELSE 'FAIL (' || CAST(COUNT(*) - COUNT(DISTINCT sales_contract_id) AS STRING) || ' dups)' END,
# MAGIC   current_timestamp()
# MAGIC FROM sales_contract
# MAGIC UNION ALL
# MAGIC -- BK Null Check
# MAGIC SELECT 'PENDING', 'sales_contract', 'BK_Null_Check_contract_number', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN contract_number IS NULL OR TRIM(contract_number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN contract_number IS NULL OR TRIM(contract_number) = '' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'BK_Null_Check_contract_number: ' || CASE WHEN SUM(CASE WHEN contract_number IS NULL OR TRIM(contract_number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   current_timestamp()
# MAGIC FROM sales_contract
# MAGIC UNION ALL
# MAGIC -- POPULATION (key business columns - lowest)
# MAGIC SELECT 'PENDING', 'sales_contract', 'POP_Key_Columns', 'POP',
# MAGIC   CASE WHEN MIN(pop_pct) >= 95.0 THEN 'PASS'
# MAGIC        WHEN MIN(pop_pct) >= 90.0 THEN 'WARN'
# MAGIC        ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(MIN(pop_pct), 2) AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'POP_Key_Columns: min population ' || CAST(ROUND(MIN(pop_pct), 2) AS STRING) || '%',
# MAGIC   current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT COUNT(contract_number)*100.0/COUNT(*) AS pop_pct FROM sales_contract
# MAGIC   UNION ALL SELECT COUNT(customer_account_number)*100.0/COUNT(*) FROM sales_contract
# MAGIC   UNION ALL SELECT COUNT(valid_from)*100.0/COUNT(*) FROM sales_contract
# MAGIC   UNION ALL SELECT COUNT(valid_to)*100.0/COUNT(*) FROM sales_contract
# MAGIC   UNION ALL SELECT COUNT(contract_status)*100.0/COUNT(*) FROM sales_contract
# MAGIC   UNION ALL SELECT COUNT(source_system_key)*100.0/COUNT(*) FROM sales_contract
# MAGIC )
# MAGIC UNION ALL
# MAGIC -- DRIFT (row count - first run = BASELINE)
# MAGIC SELECT 'PENDING', 'sales_contract', 'DRIFT_Row_Count', 'DRIFT',
# MAGIC   CASE
# MAGIC     WHEN b.Baseline_Value IS NULL THEN 'PASS'
# MAGIC     WHEN ABS(cnt - CAST(b.Baseline_Value AS BIGINT)) * 100.0 / NULLIF(CAST(b.Baseline_Value AS BIGINT), 0) <= COALESCE(b.Tolerance_Pct, 20) THEN 'PASS'
# MAGIC     ELSE 'FAIL'
# MAGIC   END,
# MAGIC   COALESCE(b.Baseline_Value, 'NEW_BASELINE'),
# MAGIC   CAST(cnt AS STRING),
# MAGIC   NULL, FALSE, CAST(NULL AS STRING),
# MAGIC   'DRIFT_Row_Count: ' || CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE established at ' || CAST(cnt AS STRING) ELSE 'current=' || CAST(cnt AS STRING) || ' baseline=' || b.Baseline_Value END,
# MAGIC   current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM sales_contract)
# MAGIC LEFT JOIN _data_drift_baseline b
# MAGIC   ON b.Table_Name = 'sales_contract' AND b.Column_Name = 'sales_contract_id' AND b.Metric_Type = 'ROW_COUNT';