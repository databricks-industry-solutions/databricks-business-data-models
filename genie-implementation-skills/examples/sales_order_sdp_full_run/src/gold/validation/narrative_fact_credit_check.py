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

# DBTITLE 1,Narrative Header
# MAGIC %md
# MAGIC # fact_credit_check — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Credit check events from order_credit_check silver. Tracks credit limit, utilization, and check outcomes per customer per order.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per credit check event. 3,104 rows.
# MAGIC
# MAGIC ## Surrogate Key
# MAGIC `Credit_Check_Key` (BIGINT identity)
# MAGIC
# MAGIC ## FKs
# MAGIC - Customer_Key → dim_customer (SHA2(Customer_Number))
# MAGIC - Sales_Area_Key → dim_sales_area (via LEFT JOIN to order)
# MAGIC - Check_Date_Key → dim_date (CAST(Check_Timestamp AS DATE))
# MAGIC
# MAGIC ## Measures
# MAGIC - Credit_Limit, Credit_Exposure, Credit_Utilization_Pct, Check_Result (PASS/FAIL)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - None at gold level
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** A (7/7 PASS)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'fact_credit_check' AS Entity, COUNT(*) AS Row_Count FROM fact_credit_check;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Credit_Check_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Credit_Check_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Credit_Check_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM fact_credit_check;

# COMMAND ----------

# DBTITLE 1,FK Orphan Checks
# MAGIC %sql
# MAGIC SELECT 'dim_customer' AS Dimension, ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS Orphan_Pct
# MAGIC FROM fact_credit_check f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_sales_area', ROUND(100.0*SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_credit_check f LEFT JOIN dim_sales_area d ON f.Sales_Area_Key = d.Sales_Area_Key WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_date (Check_Date_Key)', ROUND(100.0*SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4)
# MAGIC FROM fact_credit_check f LEFT JOIN dim_date d ON f.Check_Date_Key = d.Date_Key WHERE f.Check_Date_Key IS NOT NULL;

# COMMAND ----------

# DBTITLE 1,Population & Measures
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Credit_Limit)/COUNT(*),2) AS Credit_Limit_Pct,
# MAGIC   ROUND(100.0*COUNT(Credit_Utilization_Pct)/COUNT(*),2) AS Utilization_Pct_Pct,
# MAGIC   ROUND(100.0*COUNT(Check_Result)/COUNT(*),2) AS Check_Result_Pct,
# MAGIC   ROUND(100.0*COUNT(Customer_Key)/COUNT(*),2) AS Customer_Key_Pct
# MAGIC FROM fact_credit_check;

# COMMAND ----------

# DBTITLE 1,Integration: Join Preservation
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM fact_credit_check) AS Fact_Rows,
# MAGIC   (SELECT COUNT(*) FROM fact_credit_check f
# MAGIC    LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC    LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC    LEFT JOIN dim_date dd ON f.Check_Date_Key = dd.Date_Key) AS Joined_Rows,
# MAGIC   CASE WHEN (SELECT COUNT(*) FROM fact_credit_check) =
# MAGIC        (SELECT COUNT(*) FROM fact_credit_check f
# MAGIC         LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC         LEFT JOIN dim_sales_area sa ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC         LEFT JOIN dim_date dd ON f.Check_Date_Key = dd.Date_Key)
# MAGIC   THEN 'PASS' ELSE 'FAIL' END AS Status;

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC -- Credit check outcome distribution
# MAGIC SELECT Check_Result, COUNT(*) AS Cnt, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM fact_credit_check),2) AS Pct
# MAGIC FROM fact_credit_check
# MAGIC GROUP BY Check_Result
# MAGIC ORDER BY Cnt DESC;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'fact_credit_check';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Credit_Check_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Credit_Check_Key) AS STRING), NULL, FALSE, NULL, 'PK', current_timestamp()
# MAGIC FROM fact_credit_check
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Credit_Check_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Credit_Check_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL, 'BK', current_timestamp()
# MAGIC FROM fact_credit_check
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'FK_Customer_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL, 'FK dim_customer', current_timestamp()
# MAGIC FROM fact_credit_check f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'FK_Sales_Area_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Sales_Area_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL, 'FK dim_sales_area', current_timestamp()
# MAGIC FROM fact_credit_check f LEFT JOIN dim_sales_area d ON f.Sales_Area_Key = d.Sales_Area_Key WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'Population_Measures', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Credit_Limit)/COUNT(*), 100.0*COUNT(Credit_Utilization_Pct)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Credit_Limit)/COUNT(*), 100.0*COUNT(Credit_Utilization_Pct)/COUNT(*)),2) AS STRING), NULL, FALSE, NULL, 'Measure pop', current_timestamp()
# MAGIC FROM fact_credit_check
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL, 'Drift', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM fact_credit_check), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'fact_credit_check' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_credit_check', 'Integration_Join_Preservation', 'INTEGRATION',
# MAGIC   CASE WHEN j = f THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(f AS STRING), CAST(j AS STRING), CASE WHEN f > 0 THEN ROUND((j-f)*100.0/f,4) ELSE 0 END, FALSE, NULL, 'Join preservation', current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT (SELECT COUNT(*) FROM fact_credit_check) AS f,
# MAGIC     (SELECT COUNT(*) FROM fact_credit_check fc
# MAGIC      LEFT JOIN dim_customer c ON fc.Customer_Key = c.Customer_Key
# MAGIC      LEFT JOIN dim_sales_area sa ON fc.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC      LEFT JOIN dim_date dd ON fc.Check_Date_Key = dd.Date_Key) AS j
# MAGIC );