# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT 'sales_order_silver_sdp';

# COMMAND ----------

# DBTITLE 1,Set Context and Claim PENDING
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);
# MAGIC
# MAGIC -- Generate run context and claim all PENDING rows
# MAGIC DECLARE OR REPLACE VARIABLE run_id STRING DEFAULT uuid();
# MAGIC DECLARE OR REPLACE VARIABLE run_ts TIMESTAMP DEFAULT current_timestamp();
# MAGIC
# MAGIC UPDATE _validation_check_detail
# MAGIC SET Run_Id = run_id
# MAGIC WHERE Run_Id = 'PENDING';

# COMMAND ----------

# DBTITLE 1,Compute Per-Entity Grades
# MAGIC %sql
# MAGIC -- Write _validation_table_result
# MAGIC DELETE FROM _validation_table_result WHERE Run_Id = run_id;
# MAGIC
# MAGIC INSERT INTO _validation_table_result
# MAGIC WITH entity_stats AS (
# MAGIC   SELECT Table_Name,
# MAGIC     SUM(CASE WHEN Status='FAIL' AND Check_Type='PK' THEN 1 ELSE 0 END) AS pk_fails,
# MAGIC     MAX(CASE WHEN Check_Type='FK' AND Status NOT IN ('KNOWN_GAP','PASS') THEN CAST(Actual_Value AS DECIMAL(7,4)) ELSE 0 END) AS worst_fk,
# MAGIC     MIN(CASE WHEN Check_Type='POP' AND Status!='PASS' THEN CAST(Actual_Value AS DECIMAL(7,4)) ELSE 100.0 END) AS worst_pop,
# MAGIC     SUM(CASE WHEN Check_Type='DRIFT' AND Status='FAIL' THEN 1 ELSE 0 END) AS drift_fails,
# MAGIC     SUM(CASE WHEN Check_Type='INTEGRATION' AND Status='FAIL' THEN 1 ELSE 0 END) AS integ_fails,
# MAGIC     SUM(CASE WHEN Is_Accepted_Exception=TRUE THEN 1 ELSE 0 END) AS exceptions
# MAGIC   FROM _validation_check_detail WHERE Run_Id=run_id GROUP BY Table_Name
# MAGIC ),
# MAGIC meta AS (SELECT * FROM (VALUES
# MAGIC   ('sales_area','REF',0),('order_reason','REF',0),('channel_config','REF',1),('sales_contract','MASTER',1),
# MAGIC   ('sales_contract_line','MASTER',2),('quotation','TXN',2),('order','TXN',3),('quotation_line','TXN',3),
# MAGIC   ('order_line','TXN',4),('order_partner','TXN',4),('order_schedule_line','TXN',5),
# MAGIC   ('delivery_schedule','MASTER',6),('edi_order_message','TXN',6),('order_credit_check','TXN',6),
# MAGIC   ('return_order','TXN',6),('otd_record','TXN',6),('return_order_line','TXN',7)
# MAGIC ) AS t(Table_Name,Table_Type,Tier)),
# MAGIC counts AS (
# MAGIC   SELECT 'sales_area' AS tbl, COUNT(*) AS cnt FROM sales_area
# MAGIC   UNION ALL SELECT 'order_reason',COUNT(*) FROM order_reason
# MAGIC   UNION ALL SELECT 'channel_config',COUNT(*) FROM channel_config
# MAGIC   UNION ALL SELECT 'sales_contract',COUNT(*) FROM sales_contract
# MAGIC   UNION ALL SELECT 'sales_contract_line',COUNT(*) FROM sales_contract_line
# MAGIC   UNION ALL SELECT 'quotation',COUNT(*) FROM quotation
# MAGIC   UNION ALL SELECT 'order',COUNT(*) FROM `order`
# MAGIC   UNION ALL SELECT 'quotation_line',COUNT(*) FROM quotation_line
# MAGIC   UNION ALL SELECT 'order_line',COUNT(*) FROM order_line
# MAGIC   UNION ALL SELECT 'order_partner',COUNT(*) FROM order_partner
# MAGIC   UNION ALL SELECT 'order_schedule_line',COUNT(*) FROM order_schedule_line
# MAGIC   UNION ALL SELECT 'delivery_schedule',COUNT(*) FROM delivery_schedule
# MAGIC   UNION ALL SELECT 'edi_order_message',COUNT(*) FROM edi_order_message
# MAGIC   UNION ALL SELECT 'order_credit_check',COUNT(*) FROM order_credit_check
# MAGIC   UNION ALL SELECT 'return_order',COUNT(*) FROM return_order
# MAGIC   UNION ALL SELECT 'otd_record',COUNT(*) FROM otd_record
# MAGIC   UNION ALL SELECT 'return_order_line',COUNT(*) FROM return_order_line
# MAGIC ),
# MAGIC gaps AS (SELECT Table_Name, COUNT(*) AS gap_cnt FROM _gap_registry WHERE Status!='RESOLVED' GROUP BY Table_Name)
# MAGIC SELECT run_id, m.Table_Name, m.Table_Type, m.Tier, c.cnt,
# MAGIC   (SELECT c.cnt - r.Row_Count FROM _validation_table_result r JOIN _validation_run v ON r.Run_Id=v.Run_Id WHERE r.Table_Name=m.Table_Name ORDER BY v.Run_Timestamp DESC LIMIT 1),
# MAGIC   CAST(s.pk_fails AS BIGINT), CAST(s.worst_fk AS DECIMAL(7,4)),
# MAGIC   CAST(COALESCE(s.worst_pop,100.0) AS DECIMAL(7,4)), NULL, CAST(s.drift_fails AS INT),
# MAGIC   CASE WHEN s.integ_fails=0 AND m.Table_Type='TXN' THEN TRUE WHEN m.Table_Type!='TXN' THEN NULL ELSE FALSE END,
# MAGIC   CASE WHEN s.pk_fails>0 THEN 'F' WHEN c.cnt=0 AND m.Table_Name!='delivery_schedule' THEN 'F'
# MAGIC     WHEN s.worst_fk>20 THEN 'F' WHEN s.worst_fk>10 THEN 'D' WHEN s.worst_fk>5 OR s.worst_pop<80 THEN 'C'
# MAGIC     WHEN s.worst_fk>3 OR s.worst_pop<90 THEN 'B' WHEN s.worst_fk>1 OR s.worst_pop<95 OR s.drift_fails>0 THEN 'B+' ELSE 'A' END,
# MAGIC   COALESCE((SELECT CASE WHEN Grade=CASE WHEN s.pk_fails>0 THEN 'F' WHEN c.cnt=0 AND m.Table_Name!='delivery_schedule' THEN 'F' WHEN s.worst_fk>20 THEN 'F' WHEN s.worst_fk>10 THEN 'D' WHEN s.worst_fk>5 OR s.worst_pop<80 THEN 'C' WHEN s.worst_fk>3 OR s.worst_pop<90 THEN 'B' WHEN s.worst_fk>1 OR s.worst_pop<95 OR s.drift_fails>0 THEN 'B+' ELSE 'A' END THEN 'STABLE' ELSE 'DEGRADED' END FROM _validation_table_result r JOIN _validation_run v ON r.Run_Id=v.Run_Id WHERE r.Table_Name=m.Table_Name ORDER BY v.Run_Timestamp DESC LIMIT 1), 'NEW'),
# MAGIC   COALESCE(g.gap_cnt,0), CAST(s.exceptions AS INT), NULL, current_timestamp()
# MAGIC FROM meta m JOIN entity_stats s ON m.Table_Name=s.Table_Name JOIN counts c ON m.Table_Name=c.tbl LEFT JOIN gaps g ON m.Table_Name=g.Table_Name;

# COMMAND ----------

# DBTITLE 1,Display Scorecard
# MAGIC %sql
# MAGIC -- Validation Scorecard
# MAGIC SELECT Table_Name, Table_Type, Tier, Row_Count, Grade, Grade_Delta,
# MAGIC        Pk_Duplicate_Count, Fk_Orphan_Rate_Pct, Key_Column_Pop_Pct,
# MAGIC        Drift_Columns_Count, Integration_Pass, Known_Gaps_Count
# MAGIC FROM _validation_table_result
# MAGIC WHERE Run_Id = run_id
# MAGIC ORDER BY Tier, Table_Name;

# COMMAND ----------

# DBTITLE 1,Write Run Summary
# MAGIC %sql
# MAGIC -- Write _validation_run (LAST — so previous-run deltas work correctly)
# MAGIC INSERT INTO _validation_run
# MAGIC SELECT run_id, run_ts, 'meridian_sales_order_silver_sdp', :silver_schema, 'SCHEDULED',
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=run_id),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=run_id AND Grade='A'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=run_id AND Grade='B+'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=run_id AND Grade='B'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=run_id AND Grade IN ('C','D','F')),
# MAGIC   (SELECT CASE WHEN COUNT(CASE WHEN Grade='F' THEN 1 END)>0 THEN 'F' WHEN COUNT(CASE WHEN Grade='D' THEN 1 END)>0 THEN 'D' WHEN COUNT(CASE WHEN Grade='C' THEN 1 END)>0 THEN 'C' WHEN COUNT(CASE WHEN Grade='B' THEN 1 END)>0 THEN 'B' WHEN COUNT(CASE WHEN Grade='B+' THEN 1 END)>0 THEN 'B+' ELSE 'A' END FROM _validation_table_result WHERE Run_Id=run_id),
# MAGIC   (SELECT SUM(Drift_Columns_Count) FROM _validation_table_result WHERE Run_Id=run_id),
# MAGIC   NULL, current_timestamp();

# COMMAND ----------

# DBTITLE 1,Fail Gate
# MAGIC %sql
# MAGIC -- Fail gate: raise error if any critical failures
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN COUNT(*) > 0 THEN
# MAGIC       RAISE_ERROR('VALIDATION FAILED: ' || CAST(COUNT(*) AS STRING) || ' entities at Grade D or F.')
# MAGIC     ELSE 'ALL ENTITIES PASSING — Quality Gate PASS'
# MAGIC   END AS Gate_Result
# MAGIC FROM _validation_table_result
# MAGIC WHERE Run_Id = run_id AND Grade IN ('D', 'F');