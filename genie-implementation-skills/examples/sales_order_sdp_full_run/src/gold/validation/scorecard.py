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

# DBTITLE 1,Scorecard Header
# MAGIC %md
# MAGIC # Gold Validation Scorecard — Meridian Sales Order (SDP Hybrid)
# MAGIC
# MAGIC This notebook:
# MAGIC 1. Generates a Run_Id
# MAGIC 2. Claims all PENDING check rows
# MAGIC 3. Computes per-entity grades (A/B+/B/C/D/F)
# MAGIC 4. Writes `_validation_table_result` and `_validation_run`
# MAGIC 5. Fails the cell (assertion) if any entity is below threshold
# MAGIC
# MAGIC **Run this notebook after all narrative notebooks have been executed.**

# COMMAND ----------

# DBTITLE 1,Generate Run ID & Claim Pending
# MAGIC %sql
# MAGIC DECLARE OR REPLACE VARIABLE run_id STRING DEFAULT uuid();
# MAGIC DECLARE OR REPLACE VARIABLE run_ts TIMESTAMP DEFAULT current_timestamp();
# MAGIC
# MAGIC -- Claim all PENDING rows
# MAGIC UPDATE _validation_check_detail SET Run_Id = session.run_id WHERE Run_Id = 'PENDING';
# MAGIC
# MAGIC SELECT session.run_id AS Claimed_Run_Id, (SELECT COUNT(*) FROM _validation_check_detail WHERE Run_Id = session.run_id) AS Total_Checks_Claimed;

# COMMAND ----------

# DBTITLE 1,Coverage Gate
# MAGIC %sql
# MAGIC -- Verify minimum check coverage per entity
# MAGIC SELECT Table_Name,
# MAGIC   SUM(CASE WHEN Check_Type='PK' THEN 1 ELSE 0 END) AS pk,
# MAGIC   SUM(CASE WHEN Check_Type='BK' THEN 1 ELSE 0 END) AS bk,
# MAGIC   SUM(CASE WHEN Check_Type='FK' THEN 1 ELSE 0 END) AS fk,
# MAGIC   SUM(CASE WHEN Check_Type='POP' THEN 1 ELSE 0 END) AS pop,
# MAGIC   SUM(CASE WHEN Check_Type='DRIFT' THEN 1 ELSE 0 END) AS drift,
# MAGIC   SUM(CASE WHEN Check_Type='INTEGRATION' THEN 1 ELSE 0 END) AS integ,
# MAGIC   COUNT(*) AS total
# MAGIC FROM _validation_check_detail
# MAGIC WHERE Run_Id = session.run_id
# MAGIC GROUP BY Table_Name
# MAGIC ORDER BY Table_Name;

# COMMAND ----------

# DBTITLE 1,Compute & Write Entity Grades
# MAGIC %sql
# MAGIC DELETE FROM _validation_table_result WHERE Run_Id = session.run_id;
# MAGIC
# MAGIC INSERT INTO _validation_table_result
# MAGIC WITH entity_checks AS (
# MAGIC   SELECT Table_Name,
# MAGIC     COUNT(*) AS total_checks,
# MAGIC     SUM(CASE WHEN Status = 'FAIL' AND Is_Accepted_Exception = FALSE AND Check_Type = 'PK' THEN 1 ELSE 0 END) AS pk_fails,
# MAGIC     MAX(CASE WHEN Check_Type = 'FK' AND Is_Accepted_Exception = FALSE AND Status = 'FAIL'
# MAGIC              THEN CAST(Actual_Value AS DECIMAL(10,4)) ELSE 0 END) AS worst_fk_orphan_pct,
# MAGIC     MIN(CASE WHEN Check_Type = 'POP' THEN CAST(Actual_Value AS DECIMAL(10,4)) ELSE 100 END) AS key_pop_pct,
# MAGIC     SUM(CASE WHEN Check_Type = 'DRIFT' AND Status = 'FAIL' THEN 1 ELSE 0 END) AS drift_fails,
# MAGIC     CASE WHEN MAX(CASE WHEN Check_Type = 'INTEGRATION' AND Status = 'FAIL' THEN 1 ELSE 0 END) = 0
# MAGIC          AND MAX(CASE WHEN Check_Type = 'INTEGRATION' THEN 1 ELSE 0 END) > 0 THEN TRUE
# MAGIC          WHEN MAX(CASE WHEN Check_Type = 'INTEGRATION' THEN 1 ELSE 0 END) = 0 THEN NULL
# MAGIC          ELSE FALSE END AS integration_pass,
# MAGIC     SUM(CASE WHEN Is_Accepted_Exception = TRUE THEN 1 ELSE 0 END) AS accepted_exceptions
# MAGIC   FROM _validation_check_detail WHERE Run_Id = session.run_id GROUP BY Table_Name
# MAGIC ),
# MAGIC entity_meta AS (
# MAGIC   SELECT 'dim_date' AS t, 'DIMENSION' AS tt, 0 AS tier UNION ALL
# MAGIC   SELECT 'dim_sales_area', 'DIMENSION', 0 UNION ALL
# MAGIC   SELECT 'dim_channel', 'DIMENSION', 0 UNION ALL
# MAGIC   SELECT 'dim_order_reason', 'DIMENSION', 0 UNION ALL
# MAGIC   SELECT 'dim_customer', 'DIMENSION', 1 UNION ALL
# MAGIC   SELECT 'dim_material', 'DIMENSION', 1 UNION ALL
# MAGIC   SELECT 'dim_sales_contract', 'DIMENSION', 1 UNION ALL
# MAGIC   SELECT 'bridge_order_partner', 'BRIDGE', 1 UNION ALL
# MAGIC   SELECT 'fact_sales_order_line', 'FACT', 2 UNION ALL
# MAGIC   SELECT 'fact_otd', 'FACT', 2 UNION ALL
# MAGIC   SELECT 'fact_quotation_line', 'FACT', 2 UNION ALL
# MAGIC   SELECT 'fact_return_line', 'FACT', 2 UNION ALL
# MAGIC   SELECT 'fact_credit_check', 'FACT', 2
# MAGIC ),
# MAGIC row_counts AS (
# MAGIC   SELECT 'dim_date' AS t, (SELECT COUNT(*) FROM dim_date) AS rc UNION ALL
# MAGIC   SELECT 'dim_sales_area', (SELECT COUNT(*) FROM dim_sales_area) UNION ALL
# MAGIC   SELECT 'dim_channel', (SELECT COUNT(*) FROM dim_channel) UNION ALL
# MAGIC   SELECT 'dim_order_reason', (SELECT COUNT(*) FROM dim_order_reason) UNION ALL
# MAGIC   SELECT 'dim_customer', (SELECT COUNT(*) FROM dim_customer) UNION ALL
# MAGIC   SELECT 'dim_material', (SELECT COUNT(*) FROM dim_material) UNION ALL
# MAGIC   SELECT 'dim_sales_contract', (SELECT COUNT(*) FROM dim_sales_contract) UNION ALL
# MAGIC   SELECT 'bridge_order_partner', (SELECT COUNT(*) FROM bridge_order_partner) UNION ALL
# MAGIC   SELECT 'fact_sales_order_line', (SELECT COUNT(*) FROM fact_sales_order_line) UNION ALL
# MAGIC   SELECT 'fact_otd', (SELECT COUNT(*) FROM fact_otd) UNION ALL
# MAGIC   SELECT 'fact_quotation_line', (SELECT COUNT(*) FROM fact_quotation_line) UNION ALL
# MAGIC   SELECT 'fact_return_line', (SELECT COUNT(*) FROM fact_return_line) UNION ALL
# MAGIC   SELECT 'fact_credit_check', (SELECT COUNT(*) FROM fact_credit_check)
# MAGIC ),
# MAGIC gaps AS (
# MAGIC   SELECT Table_Name, COUNT(*) AS gap_cnt FROM _gap_registry WHERE Status != 'RESOLVED' GROUP BY Table_Name
# MAGIC )
# MAGIC SELECT session.run_id, ec.Table_Name, em.tt, em.tier, rc.rc, NULL,
# MAGIC   ec.pk_fails,
# MAGIC   CASE WHEN ec.worst_fk_orphan_pct > 0 THEN ec.worst_fk_orphan_pct ELSE NULL END,
# MAGIC   ec.key_pop_pct, NULL, ec.drift_fails, ec.integration_pass,
# MAGIC   CASE
# MAGIC     WHEN ec.pk_fails > 0 THEN 'F'
# MAGIC     WHEN ec.worst_fk_orphan_pct > 20 THEN 'F'
# MAGIC     WHEN ec.worst_fk_orphan_pct > 10 THEN 'D'
# MAGIC     WHEN ec.worst_fk_orphan_pct > 5 THEN 'C'
# MAGIC     WHEN ec.worst_fk_orphan_pct > 3 THEN 'B'
# MAGIC     WHEN ec.worst_fk_orphan_pct > 1 OR ec.drift_fails > 0 THEN 'B+'
# MAGIC     ELSE 'A'
# MAGIC   END,
# MAGIC   'NEW', COALESCE(g.gap_cnt, 0), ec.accepted_exceptions, NULL, current_timestamp()
# MAGIC FROM entity_checks ec
# MAGIC JOIN entity_meta em ON ec.Table_Name = em.t
# MAGIC JOIN row_counts rc ON ec.Table_Name = rc.t
# MAGIC LEFT JOIN gaps g ON ec.Table_Name = g.Table_Name;

# COMMAND ----------

# DBTITLE 1,Display Scorecard
# MAGIC %sql
# MAGIC SELECT Table_Name, Table_Type, Tier, Row_Count, Grade, Pk_Duplicate_Count,
# MAGIC   Fk_Orphan_Rate_Pct, Key_Column_Pop_Pct, Drift_Columns_Count, Integration_Pass,
# MAGIC   Known_Gaps_Count, Accepted_Exceptions
# MAGIC FROM _validation_table_result
# MAGIC WHERE Run_Id = session.run_id
# MAGIC ORDER BY Tier, Table_Name;

# COMMAND ----------

# DBTITLE 1,Write Run Summary
# MAGIC %sql
# MAGIC INSERT INTO _validation_run
# MAGIC SELECT session.run_id, session.run_ts,
# MAGIC   'meridian_sales_order_gold_sdp', 'sales_order_gold_sdp', 'SCHEDULED',
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = session.run_id),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade = 'A'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade = 'B+'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade = 'B'),
# MAGIC   (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade IN ('C','D','F')),
# MAGIC   CASE
# MAGIC     WHEN (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade IN ('D','F')) > 0 THEN 'FAIL'
# MAGIC     WHEN (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade IN ('C')) > 0 THEN 'C'
# MAGIC     WHEN (SELECT COUNT(*) FROM _validation_table_result WHERE Run_Id = run_id AND Grade IN ('B','B+')) > 0 THEN 'B+'
# MAGIC     ELSE 'A'
# MAGIC   END,
# MAGIC   0, NULL, current_timestamp();

# COMMAND ----------

# DBTITLE 1,Quality Gate (Fail on D/F)
# Quality gate: fail notebook if any entity grades D or F
df = spark.sql("""
  SELECT Table_Name, Grade
  FROM _validation_table_result
  WHERE Run_Id = (SELECT MAX(Run_Id) FROM _validation_run)
    AND Grade IN ('D', 'F')
""")
failures = df.collect()
if failures:
    msg = ", ".join([f"{r.Table_Name}={r.Grade}" for r in failures])
    raise AssertionError(f"QUALITY GATE FAILED: {msg}")
print("QUALITY GATE PASSED: all entities above threshold")