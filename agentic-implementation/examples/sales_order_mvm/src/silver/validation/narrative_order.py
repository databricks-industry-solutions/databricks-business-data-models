# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative — order
# MAGIC %md
# MAGIC ## order — Validation Narrative
# MAGIC
# MAGIC **Entity:** `order` · **Tier:** 2 · **Type:** FACT · **Strategy:** MV (full recompute)
# MAGIC
# MAGIC **Business Purpose:** Sales orders from SAP SD (`vbak`). Central transactional entity — most downstream entities reference it. `order` is a SQL reserved keyword; backtick-escaped in all DDL/SQL.
# MAGIC
# MAGIC **Source:** `sap_sd_mvm.vbak` · **Natural Key:** `vbeln` (order number)
# MAGIC
# MAGIC **Surrogate Key:** `order_id` = `SHA2(vbeln)` as BIGINT
# MAGIC
# MAGIC **FK Resolution (intra-domain):**
# MAGIC - `quotation_id` → `quotation` (JOIN via converted_order_reference)
# MAGIC - `sales_contract_id` → `sales_contract` (JOIN via contract_number)
# MAGIC
# MAGIC **Deferred FKs (cross-domain):** account_id, plant_id, contract_id, price_list_id
# MAGIC
# MAGIC **Build Manifest Row Count:** 5,000

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS row_count,
# MAGIC   COUNT(DISTINCT order_id) AS distinct_pk,
# MAGIC   COUNT(*) - COUNT(DISTINCT order_id) AS pk_duplicates,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END AS pk_status
# MAGIC FROM `order`;

# COMMAND ----------

# DBTITLE 1,FK Check — quotation_id
# MAGIC %sql
# MAGIC -- FK: order.quotation_id -> quotation.quotation_id (JOIN resolution)
# MAGIC -- Many orders won't have a quotation (NULL is acceptable)
# MAGIC SELECT COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END) AS orphan_count,
# MAGIC   SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END) AS non_null_fk,
# MAGIC   ROUND(SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END),0),4) AS orphan_pct_of_populated
# MAGIC FROM `order` o
# MAGIC LEFT JOIN quotation q ON o.quotation_id = q.quotation_id;

# COMMAND ----------

# DBTITLE 1,FK Check — sales_contract_id
# MAGIC %sql
# MAGIC -- FK: order.sales_contract_id -> sales_contract.sales_contract_id (JOIN resolution)
# MAGIC SELECT COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN o.sales_contract_id IS NOT NULL AND sc.sales_contract_id IS NULL THEN 1 ELSE 0 END) AS orphan_count,
# MAGIC   SUM(CASE WHEN o.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) AS non_null_fk,
# MAGIC   ROUND(SUM(CASE WHEN o.sales_contract_id IS NOT NULL AND sc.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END),0),4) AS orphan_pct
# MAGIC FROM `order` o
# MAGIC LEFT JOIN sales_contract sc ON o.sales_contract_id = sc.sales_contract_id;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'order_number' AS col, COUNT(*) AS total,
# MAGIC   SUM(CASE WHEN order_number IS NULL OR TRIM(order_number)='' THEN 1 ELSE 0 END) AS null_empty,
# MAGIC   CASE WHEN SUM(CASE WHEN order_number IS NULL OR TRIM(order_number)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END AS bk_status
# MAGIC FROM `order`;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC SELECT 'order_number' AS col, ROUND(COUNT(order_number)*100.0/COUNT(*),2) AS pop_pct FROM `order`
# MAGIC UNION ALL SELECT 'order_date', ROUND(COUNT(order_date)*100.0/COUNT(*),2) FROM `order`
# MAGIC UNION ALL SELECT 'net_value', ROUND(COUNT(net_value)*100.0/COUNT(*),2) FROM `order`
# MAGIC UNION ALL SELECT 'currency_code', ROUND(COUNT(currency_code)*100.0/COUNT(*),2) FROM `order`
# MAGIC UNION ALL SELECT 'overall_status', ROUND(COUNT(overall_status)*100.0/COUNT(*),2) FROM `order`
# MAGIC UNION ALL SELECT 'source_system_key', ROUND(COUNT(source_system_key)*100.0/COUNT(*),2) FROM `order`;

# COMMAND ----------

# DBTITLE 1,INTEGRATION — Star Schema Join Preservation
# MAGIC %sql
# MAGIC -- INTEGRATION: Join preservation + fan-out check
# MAGIC -- order (FACT) joined to its dim parents should preserve row count
# MAGIC WITH base AS (SELECT COUNT(*) AS base_count FROM `order`),
# MAGIC join_quotation AS (
# MAGIC   SELECT COUNT(*) AS joined_count
# MAGIC   FROM `order` o LEFT JOIN quotation q ON o.quotation_id = q.quotation_id
# MAGIC ),
# MAGIC join_contract AS (
# MAGIC   SELECT COUNT(*) AS joined_count
# MAGIC   FROM `order` o LEFT JOIN sales_contract sc ON o.sales_contract_id = sc.sales_contract_id
# MAGIC )
# MAGIC SELECT
# MAGIC   b.base_count,
# MAGIC   jq.joined_count AS after_quotation_join,
# MAGIC   jc.joined_count AS after_contract_join,
# MAGIC   CASE WHEN jq.joined_count = b.base_count AND jc.joined_count = b.base_count THEN 'PASS' ELSE 'FAIL' END AS integration_status
# MAGIC FROM base b, join_quotation jq, join_contract jc;

# COMMAND ----------

# DBTITLE 1,Drift Check
# MAGIC %sql
# MAGIC SELECT 'order' AS table_name, 'ROW_COUNT' AS metric_type,
# MAGIC   CAST(cnt AS STRING) AS current_value, b.Baseline_Value, b.Tolerance_Pct,
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE'
# MAGIC     WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0)<=b.Tolerance_Pct THEN 'PASS'
# MAGIC     ELSE 'FAIL' END AS drift_status
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM `order`)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='order' AND b.Column_Name='order_id' AND b.Metric_Type='ROW_COUNT';

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_rows, COUNT(DISTINCT order_number) AS distinct_orders,
# MAGIC   COUNT(DISTINCT overall_status) AS statuses,
# MAGIC   MIN(order_date) AS earliest, MAX(order_date) AS latest,
# MAGIC   MIN(net_value) AS min_val, AVG(net_value) AS avg_val, MAX(net_value) AS max_val,
# MAGIC   SUM(CASE WHEN quotation_id IS NOT NULL THEN 1 ELSE 0 END) AS has_quotation,
# MAGIC   SUM(CASE WHEN sales_contract_id IS NOT NULL THEN 1 ELSE 0 END) AS has_contract,
# MAGIC   MAX(last_modified_timestamp) AS last_load
# MAGIC FROM `order`;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT order_id, order_number, order_date, net_value, currency_code,
# MAGIC   overall_status, quotation_id, sales_contract_id, source_system
# MAGIC FROM `order` ORDER BY order_number LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id='PENDING' AND Table_Name='order';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC -- PK
# MAGIC SELECT 'PENDING','order','PK_Uniqueness','PK',
# MAGIC   CASE WHEN COUNT(*)=COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0',CAST(COUNT(*)-COUNT(DISTINCT order_id) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'PK: '||CASE WHEN COUNT(*)=COUNT(DISTINCT order_id) THEN 'PASS' ELSE 'FAIL' END,current_timestamp()
# MAGIC FROM `order`
# MAGIC UNION ALL
# MAGIC -- FK quotation_id (orphan among populated only)
# MAGIC SELECT 'PENDING','order','FK_quotation_id','FK',
# MAGIC   CASE WHEN COALESCE(SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END),0),0) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0',CAST(ROUND(COALESCE(SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END),0),0),4) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'FK_quotation_id: orphan='||CAST(ROUND(COALESCE(SUM(CASE WHEN o.quotation_id IS NOT NULL AND q.quotation_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.quotation_id IS NOT NULL THEN 1 ELSE 0 END),0),0),2) AS STRING)||'%',current_timestamp()
# MAGIC FROM `order` o LEFT JOIN quotation q ON o.quotation_id=q.quotation_id
# MAGIC UNION ALL
# MAGIC -- FK sales_contract_id
# MAGIC SELECT 'PENDING','order','FK_sales_contract_id','FK',
# MAGIC   CASE WHEN COALESCE(SUM(CASE WHEN o.sales_contract_id IS NOT NULL AND sc.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END),0),0) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0',CAST(ROUND(COALESCE(SUM(CASE WHEN o.sales_contract_id IS NOT NULL AND sc.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END),0),0),4) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'FK_sales_contract_id: orphan='||CAST(ROUND(COALESCE(SUM(CASE WHEN o.sales_contract_id IS NOT NULL AND sc.sales_contract_id IS NULL THEN 1 ELSE 0 END)*100.0/
# MAGIC     NULLIF(SUM(CASE WHEN o.sales_contract_id IS NOT NULL THEN 1 ELSE 0 END),0),0),2) AS STRING)||'%',current_timestamp()
# MAGIC FROM `order` o LEFT JOIN sales_contract sc ON o.sales_contract_id=sc.sales_contract_id
# MAGIC UNION ALL
# MAGIC -- BK
# MAGIC SELECT 'PENDING','order','BK_Null_Check_order_number','BK',
# MAGIC   CASE WHEN SUM(CASE WHEN order_number IS NULL OR TRIM(order_number)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0',CAST(SUM(CASE WHEN order_number IS NULL OR TRIM(order_number)='' THEN 1 ELSE 0 END) AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),'BK: '||CASE WHEN SUM(CASE WHEN order_number IS NULL OR TRIM(order_number)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,current_timestamp()
# MAGIC FROM `order`
# MAGIC UNION ALL
# MAGIC -- POP
# MAGIC SELECT 'PENDING','order','POP_Key_Columns','POP',
# MAGIC   CASE WHEN MIN(p)>=95.0 THEN 'PASS' WHEN MIN(p)>=90.0 THEN 'WARN' ELSE 'FAIL' END,
# MAGIC   '95.0',CAST(ROUND(MIN(p),2) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'POP: min='||CAST(ROUND(MIN(p),2) AS STRING)||'%',current_timestamp()
# MAGIC FROM (SELECT COUNT(order_number)*100.0/COUNT(*) AS p FROM `order`
# MAGIC   UNION ALL SELECT COUNT(order_date)*100.0/COUNT(*) FROM `order`
# MAGIC   UNION ALL SELECT COUNT(net_value)*100.0/COUNT(*) FROM `order`
# MAGIC   UNION ALL SELECT COUNT(overall_status)*100.0/COUNT(*) FROM `order`
# MAGIC   UNION ALL SELECT COUNT(source_system_key)*100.0/COUNT(*) FROM `order`)
# MAGIC UNION ALL
# MAGIC -- INTEGRATION (join preservation)
# MAGIC SELECT 'PENDING','order','INTEG_Join_Preservation','INTEGRATION',
# MAGIC   CASE WHEN jq=b AND jc=b THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(b AS STRING),CAST(b AS STRING)||' q='||CAST(jq AS STRING)||' c='||CAST(jc AS STRING),
# MAGIC   NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'INTEG: base='||CAST(b AS STRING)||' after_quotation='||CAST(jq AS STRING)||' after_contract='||CAST(jc AS STRING),current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT (SELECT COUNT(*) FROM `order`) AS b,
# MAGIC     (SELECT COUNT(*) FROM `order` o LEFT JOIN quotation q ON o.quotation_id=q.quotation_id) AS jq,
# MAGIC     (SELECT COUNT(*) FROM `order` o LEFT JOIN sales_contract sc ON o.sales_contract_id=sc.sales_contract_id) AS jc
# MAGIC )
# MAGIC UNION ALL
# MAGIC -- DRIFT
# MAGIC SELECT 'PENDING','order','DRIFT_Row_Count','DRIFT',
# MAGIC   CASE WHEN b.Baseline_Value IS NULL THEN 'PASS'
# MAGIC     WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0)<=COALESCE(b.Tolerance_Pct,20) THEN 'PASS'
# MAGIC     ELSE 'FAIL' END,
# MAGIC   COALESCE(b.Baseline_Value,'NEW_BASELINE'),CAST(cnt AS STRING),NULL,FALSE,CAST(NULL AS STRING),
# MAGIC   'DRIFT: '||CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE='||CAST(cnt AS STRING) ELSE 'current='||CAST(cnt AS STRING) END,current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM `order`)
# MAGIC LEFT JOIN _data_drift_baseline b ON b.Table_Name='order' AND b.Column_Name='order_id' AND b.Metric_Type='ROW_COUNT';