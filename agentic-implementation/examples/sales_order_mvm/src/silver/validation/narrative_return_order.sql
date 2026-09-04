-- Databricks notebook source
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## return_order — Validation Narrative
-- MAGIC 
-- MAGIC **Entity:** `return_order` · **Tier:** 3 · **Type:** FACT · **Strategy:** MV (full recompute)
-- MAGIC 
-- MAGIC **Surrogate Key:** `return_order_id`  
-- MAGIC **Natural Key:** `source_system_key`
-- MAGIC 
-- MAGIC **FK Relationships:**
-- MAGIC - `original_order_id` → ``order``.`order_id`
-- MAGIC 
-- MAGIC **Checks:** PK, FK×1, BK, POP, INTEGRATION, DRIFT

-- COMMAND ----------

DELETE FROM _validation_check_detail WHERE Run_Id='PENDING' AND Table_Name='return_order';
INSERT INTO _validation_check_detail
-- PK
SELECT 'PENDING','return_order','PK_Uniqueness','PK',
  CASE WHEN COUNT(*)=COUNT(DISTINCT return_order_id) THEN 'PASS' ELSE 'FAIL' END,
  '0',CAST(COUNT(*)-COUNT(DISTINCT return_order_id) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
  'PK: '||CASE WHEN COUNT(*)=COUNT(DISTINCT return_order_id) THEN 'PASS' ELSE 'FAIL' END,current_timestamp()
FROM return_order
UNION ALL
-- FK original_order_id
SELECT 'PENDING','return_order','FK_original_order_id','FK',
  CASE WHEN COALESCE(SUM(CASE WHEN t.original_order_id IS NOT NULL AND p.order_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.original_order_id IS NOT NULL THEN 1 ELSE 0 END),0),0) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
  '1.0',CAST(ROUND(COALESCE(SUM(CASE WHEN t.original_order_id IS NOT NULL AND p.order_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.original_order_id IS NOT NULL THEN 1 ELSE 0 END),0),0),4) AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),
  'FK_original_order_id: orphan='||CAST(ROUND(COALESCE(SUM(CASE WHEN t.original_order_id IS NOT NULL AND p.order_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.original_order_id IS NOT NULL THEN 1 ELSE 0 END),0),0),2) AS STRING)||'%',current_timestamp()
FROM return_order t LEFT JOIN `order` p ON t.original_order_id=p.order_id
UNION ALL
-- BK
SELECT 'PENDING','return_order','BK_Null_Check','BK',
  CASE WHEN SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
  '0',CAST(SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END) AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),'BK: '||CASE WHEN SUM(CASE WHEN source_system_key IS NULL OR TRIM(source_system_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,current_timestamp()
FROM return_order
UNION ALL
-- POP
SELECT 'PENDING','return_order','POP_Key_Columns','POP',
  CASE WHEN MIN(p)>=95.0 THEN 'PASS' WHEN MIN(p)>=90.0 THEN 'WARN' ELSE 'FAIL' END,
  '95.0',CAST(ROUND(MIN(p),2) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
  'POP: min='||CAST(ROUND(MIN(p),2) AS STRING)||'%',current_timestamp()
FROM (SELECT COUNT(source_system_key)*100.0/COUNT(*) AS p FROM return_order)
UNION ALL
-- INTEGRATION
SELECT 'PENDING','return_order','INTEG_Join_Order','INTEGRATION',
  CASE WHEN j=b THEN 'PASS' ELSE 'FAIL' END,
  CAST(b AS STRING),CAST(b AS STRING)||' joined='||CAST(j AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),
  'INTEG: base='||CAST(b AS STRING)||' joined='||CAST(j AS STRING),current_timestamp()
FROM (SELECT (SELECT COUNT(*) FROM return_order) AS b, (SELECT COUNT(*) FROM return_order r LEFT JOIN `order` o ON r.original_order_id=o.order_id) AS j)
UNION ALL
-- DRIFT
SELECT 'PENDING','return_order','DRIFT_Row_Count','DRIFT',
  CASE WHEN b.Baseline_Value IS NULL THEN 'PASS'
    WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0)<=COALESCE(b.Tolerance_Pct,20) THEN 'PASS'
    ELSE 'FAIL' END,
  COALESCE(b.Baseline_Value,'NEW_BASELINE'),CAST(cnt AS STRING),NULL,FALSE,CAST(NULL AS STRING),
  'DRIFT: '||CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE='||CAST(cnt AS STRING) ELSE 'current='||CAST(cnt AS STRING) END,current_timestamp()
FROM (SELECT COUNT(*) AS cnt FROM return_order)
LEFT JOIN _data_drift_baseline b ON b.Table_Name='return_order' AND b.Column_Name='return_order_id' AND b.Metric_Type='ROW_COUNT';
