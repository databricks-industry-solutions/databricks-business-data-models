# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Claim PENDING Rows
# MAGIC %sql
# MAGIC -- Generate run context and claim all PENDING rows
# MAGIC DECLARE OR REPLACE VARIABLE v_run_id STRING DEFAULT uuid();
# MAGIC DECLARE OR REPLACE VARIABLE v_run_ts TIMESTAMP DEFAULT current_timestamp();
# MAGIC
# MAGIC UPDATE _validation_check_detail
# MAGIC SET Run_Id = session.v_run_id
# MAGIC WHERE Run_Id = 'PENDING';
# MAGIC
# MAGIC -- Verify claim
# MAGIC SELECT session.v_run_id AS run_id, COUNT(*) AS claimed_rows
# MAGIC FROM _validation_check_detail WHERE Run_Id = session.v_run_id;

# COMMAND ----------

# DBTITLE 1,Compute Per-Entity Grades
# MAGIC %sql
# MAGIC DELETE FROM _validation_table_result WHERE Run_Id = session.v_run_id;
# MAGIC
# MAGIC INSERT INTO _validation_table_result
# MAGIC SELECT
# MAGIC   session.v_run_id,
# MAGIC   cd.Table_Name,
# MAGIC   CASE WHEN cd.Table_Name IN ('sales_contract','sales_contract_line','quotation','quotation_line','order_partner') THEN 'DIMENSION' ELSE 'FACT' END,
# MAGIC   CASE cd.Table_Name
# MAGIC     WHEN 'sales_contract' THEN 0 WHEN 'sales_contract_line' THEN 1 WHEN 'quotation' THEN 1
# MAGIC     WHEN 'order' THEN 2 WHEN 'quotation_line' THEN 2
# MAGIC     WHEN 'order_line' THEN 3 WHEN 'order_partner' THEN 3 WHEN 'return_order' THEN 3 WHEN 'delivery' THEN 3 WHEN 'credit_check' THEN 3
# MAGIC     WHEN 'order_schedule_line' THEN 4 WHEN 'order_configuration' THEN 4 WHEN 'return_order_line' THEN 4 WHEN 'delivery_line' THEN 4
# MAGIC     ELSE 5 END,
# MAGIC   COALESCE(rc.row_count, 0),
# MAGIC   CAST(NULL AS BIGINT),
# MAGIC   COALESCE(SUM(CASE WHEN cd.Check_Type='PK' AND cd.Status='FAIL' AND NOT cd.Is_Accepted_Exception THEN 1 ELSE 0 END),0),
# MAGIC   MAX(CASE WHEN cd.Check_Type='FK' AND NOT cd.Is_Accepted_Exception THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),
# MAGIC   MIN(CASE WHEN cd.Check_Type='POP' THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),
# MAGIC   CAST(NULL AS DECIMAL(10,2)),
# MAGIC   COALESCE(SUM(CASE WHEN cd.Check_Type='DRIFT' AND cd.Status='FAIL' AND NOT cd.Is_Accepted_Exception THEN 1 ELSE 0 END),0),
# MAGIC   CASE WHEN cd.Table_Name IN ('sales_contract','sales_contract_line','quotation','quotation_line','order_partner') THEN NULL
# MAGIC     WHEN SUM(CASE WHEN cd.Check_Type='INTEGRATION' AND cd.Status='FAIL' THEN 1 ELSE 0 END)=0 THEN TRUE ELSE FALSE END,
# MAGIC   CASE
# MAGIC     WHEN SUM(CASE WHEN cd.Check_Type='PK' AND cd.Status='FAIL' AND NOT cd.Is_Accepted_Exception THEN 1 ELSE 0 END) > 0 THEN 'F'
# MAGIC     WHEN COALESCE(rc.row_count,0) = 0 THEN 'F'
# MAGIC     WHEN COALESCE(MAX(CASE WHEN cd.Check_Type='FK' AND NOT cd.Is_Accepted_Exception THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),0) > 20 THEN 'F'
# MAGIC     WHEN COALESCE(MAX(CASE WHEN cd.Check_Type='FK' AND NOT cd.Is_Accepted_Exception THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),0) > 10 THEN 'D'
# MAGIC     WHEN COALESCE(MAX(CASE WHEN cd.Check_Type='FK' AND NOT cd.Is_Accepted_Exception THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),0) > 5
# MAGIC       OR COALESCE(MIN(CASE WHEN cd.Check_Type='POP' THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),100) < 80 THEN 'C'
# MAGIC     WHEN COALESCE(MAX(CASE WHEN cd.Check_Type='FK' AND NOT cd.Is_Accepted_Exception THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),0) > 3
# MAGIC       OR COALESCE(MIN(CASE WHEN cd.Check_Type='POP' THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),100) < 90 THEN 'B'
# MAGIC     WHEN COALESCE(MAX(CASE WHEN cd.Check_Type='FK' AND NOT cd.Is_Accepted_Exception THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),0) > 1
# MAGIC       OR COALESCE(MIN(CASE WHEN cd.Check_Type='POP' THEN CAST(cd.Actual_Value AS DECIMAL(7,4)) END),100) < 95
# MAGIC       OR SUM(CASE WHEN cd.Check_Type='DRIFT' AND cd.Status='FAIL' AND NOT cd.Is_Accepted_Exception THEN 1 ELSE 0 END) > 0 THEN 'B+'
# MAGIC     ELSE 'A'
# MAGIC   END,
# MAGIC   'NEW',
# MAGIC   COALESCE(gc.gap_count, 0),
# MAGIC   COALESCE(SUM(CASE WHEN cd.Is_Accepted_Exception THEN 1 ELSE 0 END),0),
# MAGIC   CAST(NULL AS STRING),
# MAGIC   current_timestamp()
# MAGIC FROM _validation_check_detail cd
# MAGIC LEFT JOIN (
# MAGIC   SELECT 'sales_contract' AS t, COUNT(*) AS row_count FROM sales_contract
# MAGIC   UNION ALL SELECT 'sales_contract_line', COUNT(*) FROM sales_contract_line
# MAGIC   UNION ALL SELECT 'quotation', COUNT(*) FROM quotation
# MAGIC   UNION ALL SELECT 'order', COUNT(*) FROM `order`
# MAGIC   UNION ALL SELECT 'quotation_line', COUNT(*) FROM quotation_line
# MAGIC   UNION ALL SELECT 'order_line', COUNT(*) FROM order_line
# MAGIC   UNION ALL SELECT 'order_partner', COUNT(*) FROM order_partner
# MAGIC   UNION ALL SELECT 'return_order', COUNT(*) FROM return_order
# MAGIC   UNION ALL SELECT 'delivery', COUNT(*) FROM delivery
# MAGIC   UNION ALL SELECT 'credit_check', COUNT(*) FROM credit_check
# MAGIC   UNION ALL SELECT 'order_schedule_line', COUNT(*) FROM order_schedule_line
# MAGIC   UNION ALL SELECT 'order_configuration', COUNT(*) FROM order_configuration
# MAGIC   UNION ALL SELECT 'return_order_line', COUNT(*) FROM return_order_line
# MAGIC   UNION ALL SELECT 'delivery_line', COUNT(*) FROM delivery_line
# MAGIC   UNION ALL SELECT 'atp_check', COUNT(*) FROM atp_check
# MAGIC   UNION ALL SELECT 'order_status_event', COUNT(*) FROM order_status_event
# MAGIC   UNION ALL SELECT 'delivery_schedule', COUNT(*) FROM delivery_schedule
# MAGIC ) rc ON cd.Table_Name = rc.t
# MAGIC LEFT JOIN (
# MAGIC   SELECT Table_Name, COUNT(*) AS gap_count
# MAGIC   FROM _gap_registry
# MAGIC   WHERE Status != 'RESOLVED'
# MAGIC   GROUP BY Table_Name
# MAGIC ) gc ON cd.Table_Name = gc.Table_Name
# MAGIC WHERE cd.Run_Id = session.v_run_id
# MAGIC GROUP BY cd.Table_Name, rc.row_count, gc.gap_count;

# COMMAND ----------

# DBTITLE 1,Write Run Summary
# MAGIC %sql
# MAGIC INSERT INTO _validation_run
# MAGIC SELECT session.v_run_id, session.v_run_ts, 'meridian_sales_order', :silver_schema, 'MANUAL',
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=session.v_run_id),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=session.v_run_id AND Grade='A'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=session.v_run_id AND Grade='B+'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=session.v_run_id AND Grade='B'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id=session.v_run_id AND Grade IN ('C','D','F')),
# MAGIC   (SELECT CASE
# MAGIC     WHEN COUNT(CASE WHEN Grade='F' THEN 1 END)>0 THEN 'F'
# MAGIC     WHEN COUNT(CASE WHEN Grade='D' THEN 1 END)>0 THEN 'D'
# MAGIC     WHEN COUNT(CASE WHEN Grade='C' THEN 1 END)>0 THEN 'C'
# MAGIC     WHEN COUNT(CASE WHEN Grade='B' THEN 1 END)>0 THEN 'B'
# MAGIC     WHEN COUNT(CASE WHEN Grade='B+' THEN 1 END)>0 THEN 'B+'
# MAGIC     ELSE 'A' END FROM _validation_table_result WHERE Run_Id=session.v_run_id),
# MAGIC   (SELECT COALESCE(SUM(Drift_Columns_Count),0) FROM _validation_table_result WHERE Run_Id=session.v_run_id),
# MAGIC   NULL, current_timestamp();

# COMMAND ----------

# DBTITLE 1,Final Scorecard
# MAGIC %sql
# MAGIC SELECT Table_Name, Table_Type, Tier, Row_Count, Grade, Grade_Delta,
# MAGIC   Pk_Duplicate_Count, Fk_Orphan_Rate_Pct, Key_Column_Pop_Pct,
# MAGIC   Drift_Columns_Count, Integration_Pass, Known_Gaps_Count
# MAGIC FROM _validation_table_result WHERE Run_Id = session.v_run_id
# MAGIC ORDER BY Tier, Table_Name;

# COMMAND ----------

# DBTITLE 1,Run Summary
# MAGIC %sql
# MAGIC SELECT * FROM _validation_run WHERE Run_Id = session.v_run_id;