-- Databricks notebook source
CREATE WIDGET TEXT silver_catalog DEFAULT '';
CREATE WIDGET TEXT silver_schema  DEFAULT '';
USE CATALOG IDENTIFIER(:silver_catalog);
USE SCHEMA  IDENTIFIER(:silver_schema);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## atp_check — Validation Narrative
-- MAGIC 
-- MAGIC **Entity:** `atp_check` · **Tier:** 5 · **Type:** FACT · **Strategy:** MV (full recompute)
-- MAGIC 
-- MAGIC **Surrogate Key:** `atp_check_id`  
-- MAGIC **Natural Key:** `source_system_line_key`
-- MAGIC 
-- MAGIC **FK Relationships:**
-- MAGIC - `order_id` → ``order``.`order_id`
-- MAGIC - `order_line_id` → `order_line`.`order_line_id`
-- MAGIC 
-- MAGIC **Checks:** PK, FK×2, BK, POP, INTEGRATION, DRIFT

-- COMMAND ----------

DELETE FROM _validation_check_detail WHERE Run_Id='PENDING' AND Table_Name='atp_check';
INSERT INTO _validation_check_detail
-- PK
SELECT 'PENDING','atp_check','PK_Uniqueness','PK',
  CASE WHEN COUNT(*)=COUNT(DISTINCT atp_check_id) THEN 'PASS' ELSE 'FAIL' END,
  '0',CAST(COUNT(*)-COUNT(DISTINCT atp_check_id) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
  'PK: '||CASE WHEN COUNT(*)=COUNT(DISTINCT atp_check_id) THEN 'PASS' ELSE 'FAIL' END,current_timestamp()
FROM atp_check
UNION ALL
-- FK order_id
SELECT 'PENDING','atp_check','FK_order_id','FK',
  CASE WHEN COALESCE(SUM(CASE WHEN t.order_id IS NOT NULL AND p.order_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.order_id IS NOT NULL THEN 1 ELSE 0 END),0),0) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
  '1.0',CAST(ROUND(COALESCE(SUM(CASE WHEN t.order_id IS NOT NULL AND p.order_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.order_id IS NOT NULL THEN 1 ELSE 0 END),0),0),4) AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),
  'FK_order_id: orphan='||CAST(ROUND(COALESCE(SUM(CASE WHEN t.order_id IS NOT NULL AND p.order_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.order_id IS NOT NULL THEN 1 ELSE 0 END),0),0),2) AS STRING)||'%',current_timestamp()
FROM atp_check t LEFT JOIN `order` p ON t.order_id=p.order_id
UNION ALL
-- FK order_line_id
SELECT 'PENDING','atp_check','FK_order_line_id','FK',
  CASE WHEN COALESCE(SUM(CASE WHEN t.order_line_id IS NOT NULL AND p2.order_line_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.order_line_id IS NOT NULL THEN 1 ELSE 0 END),0),0) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
  '1.0',CAST(ROUND(COALESCE(SUM(CASE WHEN t.order_line_id IS NOT NULL AND p2.order_line_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.order_line_id IS NOT NULL THEN 1 ELSE 0 END),0),0),4) AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),
  'FK_order_line_id: orphan='||CAST(ROUND(COALESCE(SUM(CASE WHEN t.order_line_id IS NOT NULL AND p2.order_line_id IS NULL THEN 1 ELSE 0 END)*100.0/
    NULLIF(SUM(CASE WHEN t.order_line_id IS NOT NULL THEN 1 ELSE 0 END),0),0),2) AS STRING)||'%',current_timestamp()
FROM atp_check t LEFT JOIN order_line p2 ON t.order_line_id=p2.order_line_id
UNION ALL
-- BK
SELECT 'PENDING','atp_check','BK_Null_Check','BK',
  CASE WHEN SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,
  '0',CAST(SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key)='' THEN 1 ELSE 0 END) AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),'BK: '||CASE WHEN SUM(CASE WHEN source_system_line_key IS NULL OR TRIM(source_system_line_key)='' THEN 1 ELSE 0 END)=0 THEN 'PASS' ELSE 'FAIL' END,current_timestamp()
FROM atp_check
UNION ALL
-- POP
SELECT 'PENDING','atp_check','POP_Key_Columns','POP',
  CASE WHEN MIN(p)>=95.0 THEN 'PASS' WHEN MIN(p)>=90.0 THEN 'WARN' ELSE 'FAIL' END,
  '95.0',CAST(ROUND(MIN(p),2) AS STRING),NULL,FALSE,CAST(NULL AS STRING),
  'POP: min='||CAST(ROUND(MIN(p),2) AS STRING)||'%',current_timestamp()
FROM (SELECT COUNT(source_system_line_key)*100.0/COUNT(*) AS p FROM atp_check)
UNION ALL
-- INTEGRATION
SELECT 'PENDING','atp_check','INTEG_Join_Parent','INTEGRATION',
  CASE WHEN j=b THEN 'PASS' ELSE 'FAIL' END,
  CAST(b AS STRING),CAST(b AS STRING),
  NULL,FALSE,CAST(NULL AS STRING),
  'INTEG: base='||CAST(b AS STRING),current_timestamp()
FROM (SELECT (SELECT COUNT(*) FROM atp_check) AS b, (SELECT COUNT(*) FROM atp_check a LEFT JOIN `order` o ON a.order_id=o.order_id) AS j)
UNION ALL
-- DRIFT
SELECT 'PENDING','atp_check','DRIFT_Row_Count','DRIFT',
  CASE WHEN b.Baseline_Value IS NULL THEN 'PASS'
    WHEN ABS(cnt-CAST(b.Baseline_Value AS BIGINT))*100.0/NULLIF(CAST(b.Baseline_Value AS BIGINT),0)<=COALESCE(b.Tolerance_Pct,20) THEN 'PASS'
    ELSE 'FAIL' END,
  COALESCE(b.Baseline_Value,'NEW_BASELINE'),CAST(cnt AS STRING),NULL,FALSE,CAST(NULL AS STRING),
  'DRIFT: '||CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE='||CAST(cnt AS STRING) ELSE 'current='||CAST(cnt AS STRING) END,current_timestamp()
FROM (SELECT COUNT(*) AS cnt FROM atp_check)
LEFT JOIN _data_drift_baseline b ON b.Table_Name='atp_check' AND b.Column_Name='atp_check_id' AND b.Metric_Type='ROW_COUNT';
