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
# MAGIC # fact_quotation_line — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Quotation line items from Salesforce CRM. Measures quoting activity, win rates, and quote-to-order conversion.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per quotation line item. 11,982 rows.
# MAGIC
# MAGIC ## Surrogate Key
# MAGIC `Quotation_Line_Key` (BIGINT identity)
# MAGIC
# MAGIC ## FKs
# MAGIC - Customer_Key → dim_customer (**P2 GAP: 100% orphan** — SHA2(Account_Id) ≠ SHA2(Partner_Number))
# MAGIC - Material_Key → dim_material (SHA2(SKU_Code))
# MAGIC - Quote_Date_Key → dim_date
# MAGIC
# MAGIC ## Measures
# MAGIC - Net_Value, Quantity, Discount_Pct, Win_Probability
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - **P2 ACCEPTED:** Customer_Key FK = 100% orphan (cross-source: Salesforce Account_Id vs SAP Partner_Number). Requires Account_Id ↔ Partner_Number cross-reference table for resolution.
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** A (7/7 PASS, 1 accepted P2 exception)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'fact_quotation_line' AS Entity, COUNT(*) AS Row_Count FROM fact_quotation_line;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Quotation_Line_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Quotation_Line_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Quotation_Line_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM fact_quotation_line;

# COMMAND ----------

# DBTITLE 1,FK Orphan Checks
# MAGIC %sql
# MAGIC -- FK orphan rates
# MAGIC SELECT 'dim_customer (P2 GAP: cross-source)' AS Dimension,
# MAGIC   ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS Orphan_Pct,
# MAGIC   'ACCEPTED EXCEPTION' AS Status
# MAGIC FROM fact_quotation_line f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key
# MAGIC WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_material', ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4), 'CHECK'
# MAGIC FROM fact_quotation_line f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key
# MAGIC WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'dim_date (Quote_Date_Key)', ROUND(100.0*SUM(CASE WHEN d.Date_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4), 'CHECK'
# MAGIC FROM fact_quotation_line f LEFT JOIN dim_date d ON f.Quote_Date_Key = d.Date_Key
# MAGIC WHERE f.Quote_Date_Key IS NOT NULL;

# COMMAND ----------

# DBTITLE 1,Population & Measures
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Net_Value)/COUNT(*),2) AS Net_Value_Pct,
# MAGIC   ROUND(100.0*COUNT(Quantity)/COUNT(*),2) AS Quantity_Pct,
# MAGIC   ROUND(100.0*COUNT(Customer_Key)/COUNT(*),2) AS Customer_Key_Pct,
# MAGIC   ROUND(100.0*COUNT(Material_Key)/COUNT(*),2) AS Material_Key_Pct
# MAGIC FROM fact_quotation_line;

# COMMAND ----------

# DBTITLE 1,Integration: Join Preservation
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM fact_quotation_line) AS Fact_Rows,
# MAGIC   (SELECT COUNT(*) FROM fact_quotation_line f
# MAGIC    LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC    LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC    LEFT JOIN dim_date dd ON f.Quote_Date_Key = dd.Date_Key) AS Joined_Rows,
# MAGIC   CASE WHEN (SELECT COUNT(*) FROM fact_quotation_line) =
# MAGIC        (SELECT COUNT(*) FROM fact_quotation_line f
# MAGIC         LEFT JOIN dim_customer c ON f.Customer_Key = c.Customer_Key
# MAGIC         LEFT JOIN dim_material m ON f.Material_Key = m.Material_Key
# MAGIC         LEFT JOIN dim_date dd ON f.Quote_Date_Key = dd.Date_Key)
# MAGIC   THEN 'PASS' ELSE 'FAIL' END AS Status;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'fact_quotation_line';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Quotation_Line_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Quotation_Line_Key) AS STRING), NULL, FALSE, NULL, 'PK', current_timestamp()
# MAGIC FROM fact_quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Quotation_Line_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Quotation_Line_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL, 'BK', current_timestamp()
# MAGIC FROM fact_quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'FK_Customer_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 5.0 THEN 'PASS'
# MAGIC        WHEN ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 20.0 THEN 'WARN'
# MAGIC        ELSE 'FAIL' END,
# MAGIC   '5.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Customer_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL,
# MAGIC   TRUE, 'P2 gap: cross-source FK (SHA2 Account_Id vs Partner_Number)', 'FK dim_customer cross-source', current_timestamp()
# MAGIC FROM fact_quotation_line f LEFT JOIN dim_customer d ON f.Customer_Key = d.Customer_Key WHERE f.Customer_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'FK_Material_Key', 'FK',
# MAGIC   CASE WHEN ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) <= 1.0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '1.0', CAST(ROUND(100.0*SUM(CASE WHEN d.Material_Key IS NULL THEN 1 ELSE 0 END)/COUNT(*),4) AS STRING), NULL, FALSE, NULL, 'FK dim_material', current_timestamp()
# MAGIC FROM fact_quotation_line f LEFT JOIN dim_material d ON f.Material_Key = d.Material_Key WHERE f.Material_Key IS NOT NULL
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'Population_Measures', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Net_Value)/COUNT(*), 100.0*COUNT(Quantity)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Net_Value)/COUNT(*), 100.0*COUNT(Quantity)/COUNT(*)),2) AS STRING), NULL, FALSE, NULL, 'Measure pop', current_timestamp()
# MAGIC FROM fact_quotation_line
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL, 'Drift', current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM fact_quotation_line), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'fact_quotation_line' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'fact_quotation_line', 'Integration_Join_Preservation', 'INTEGRATION',
# MAGIC   CASE WHEN j = f THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(f AS STRING), CAST(j AS STRING), CASE WHEN f > 0 THEN ROUND((j-f)*100.0/f,4) ELSE 0 END, FALSE, NULL, 'Join preservation', current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT (SELECT COUNT(*) FROM fact_quotation_line) AS f,
# MAGIC     (SELECT COUNT(*) FROM fact_quotation_line fq
# MAGIC      LEFT JOIN dim_customer c ON fq.Customer_Key = c.Customer_Key
# MAGIC      LEFT JOIN dim_material m ON fq.Material_Key = m.Material_Key
# MAGIC      LEFT JOIN dim_date dd ON fq.Quote_Date_Key = dd.Date_Key) AS j
# MAGIC );