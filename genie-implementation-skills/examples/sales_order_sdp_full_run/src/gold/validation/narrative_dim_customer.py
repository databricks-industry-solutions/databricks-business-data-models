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
# MAGIC # dim_customer — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Conformed customer dimension — Sold-To party with geographic attributes. Deduped from order_partner (AG function) by Partner_Number, latest order wins.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per unique customer (Sold-To Partner_Number). 300 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Customer_Key = SHA2(Partner_Number, 256)`
# MAGIC
# MAGIC ## Source
# MAGIC `silver.order_partner` WHERE Partner_Function = 'AG', ROW_NUMBER dedup by Partner_Number (ORDER BY Order_Number DESC)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** fact_sales_order_line, fact_otd, fact_quotation_line (cross-source P2 gap), fact_return_line, fact_credit_check
# MAGIC - **Child of:** Root dimension (no parent)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - Customer master enrichment (industry, segment, credit group) requires cross-domain join — DEFERRED Phase 3
# MAGIC - fact_quotation_line uses SHA2(Account_Id) not SHA2(Partner_Number) — P2 100% orphan
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** Verified (300 rows, 0 PK dups)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'dim_customer' AS Entity, COUNT(*) AS Row_Count,
# MAGIC   MAX(_loaded_at) AS Last_Load, ROUND(TIMESTAMPDIFF(HOUR, MAX(_loaded_at), current_timestamp()), 2) AS Hours_Since_Load
# MAGIC FROM dim_customer;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Customer_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Customer_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Customer_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_customer;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name, COUNT(*) AS Total,
# MAGIC   SUM(CASE WHEN Customer_Key IS NULL OR Customer_Number IS NULL OR TRIM(Customer_Number) = '' THEN 1 ELSE 0 END) AS Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN Customer_Key IS NULL OR Customer_Number IS NULL OR TRIM(Customer_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_customer;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Customer_Number)/COUNT(*),2) AS Customer_Number_Pct,
# MAGIC   ROUND(100.0*COUNT(Customer_Name)/COUNT(*),2) AS Customer_Name_Pct,
# MAGIC   ROUND(100.0*COUNT(Country)/COUNT(*),2) AS Country_Pct,
# MAGIC   ROUND(100.0*COUNT(City)/COUNT(*),2) AS City_Pct,
# MAGIC   ROUND(100.0*COUNT(Postal_Code)/COUNT(*),2) AS Postal_Code_Pct
# MAGIC FROM dim_customer;

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Customers,
# MAGIC   COUNT(DISTINCT Country) AS Distinct_Countries,
# MAGIC   COUNT(DISTINCT City) AS Distinct_Cities,
# MAGIC   MAX(_loaded_at) AS Last_Load
# MAGIC FROM dim_customer;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT Customer_Number, Customer_Name, Country, City, Postal_Code
# MAGIC FROM dim_customer
# MAGIC ORDER BY Customer_Number
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_customer';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'dim_customer', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Customer_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Customer_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT Customer_Key) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM dim_customer
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_customer', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Customer_Key IS NULL OR Customer_Number IS NULL OR TRIM(Customer_Number) = '' THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Customer_Key IS NULL OR Customer_Number IS NULL OR TRIM(Customer_Number) = '' THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: Customer_Key, Customer_Number', current_timestamp()
# MAGIC FROM dim_customer
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_customer', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Customer_Number)/COUNT(*), 100.0*COUNT(Customer_Name)/COUNT(*), 100.0*COUNT(Country)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Customer_Number)/COUNT(*), 100.0*COUNT(Customer_Name)/COUNT(*), 100.0*COUNT(Country)/COUNT(*)), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Lowest pop: Customer_Number, Customer_Name, Country', current_timestamp()
# MAGIC FROM dim_customer
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_customer', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_customer), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_customer' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;