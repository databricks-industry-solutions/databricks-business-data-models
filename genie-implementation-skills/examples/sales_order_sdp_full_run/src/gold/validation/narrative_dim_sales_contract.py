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
# MAGIC # dim_sales_contract — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Contract reference dimension for contract-linked order analysis. Framework/blanket purchase agreements.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per contract. 120 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Sales_Contract_Key = sales_contract_id` (identity passthrough from silver)
# MAGIC
# MAGIC ## Source
# MAGIC `silver.sales_contract` (120 rows — direct passthrough)
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** (potential future FK from fact_sales_order_line)
# MAGIC - **Child of:** Root dimension (no parent)
# MAGIC
# MAGIC ## Known Gaps
# MAGIC - None at gold level
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08 | **Grade:** Verified (120 rows, 0 PK dups)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC SELECT 'dim_sales_contract' AS Entity, COUNT(*) AS Row_Count FROM dim_sales_contract;
# MAGIC
# MAGIC SELECT 'PK_Uniqueness' AS Check_Name, COUNT(*) AS Total, COUNT(DISTINCT Sales_Contract_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Sales_Contract_Key) AS Dups,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Sales_Contract_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_sales_contract;

# COMMAND ----------

# DBTITLE 1,BK Null & Population
# MAGIC %sql
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   SUM(CASE WHEN Sales_Contract_Key IS NULL OR Contract_Number IS NULL THEN 1 ELSE 0 END) AS Dropped,
# MAGIC   CASE WHEN SUM(CASE WHEN Sales_Contract_Key IS NULL OR Contract_Number IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_sales_contract;
# MAGIC
# MAGIC SELECT COUNT(*) AS Total,
# MAGIC   ROUND(100.0*COUNT(Contract_Number)/COUNT(*),2) AS Contract_Number_Pct,
# MAGIC   ROUND(100.0*COUNT(Contract_Type)/COUNT(*),2) AS Contract_Type_Pct,
# MAGIC   ROUND(100.0*COUNT(Contract_Status)/COUNT(*),2) AS Contract_Status_Pct,
# MAGIC   ROUND(100.0*COUNT(Valid_From)/COUNT(*),2) AS Valid_From_Pct,
# MAGIC   ROUND(100.0*COUNT(Valid_To)/COUNT(*),2) AS Valid_To_Pct
# MAGIC FROM dim_sales_contract;

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS Total_Contracts,
# MAGIC   COUNT(DISTINCT Contract_Type) AS Distinct_Types,
# MAGIC   COUNT(DISTINCT Contract_Status) AS Distinct_Statuses,
# MAGIC   COUNT(DISTINCT Customer_Number) AS Distinct_Customers,
# MAGIC   MIN(Valid_From) AS Earliest_Start,
# MAGIC   MAX(Valid_To) AS Latest_End
# MAGIC FROM dim_sales_contract;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC SELECT Contract_Number, Customer_Number, Contract_Type, Valid_From, Valid_To, Target_Value, Contract_Status
# MAGIC FROM dim_sales_contract
# MAGIC ORDER BY Valid_From DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_sales_contract';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'dim_sales_contract', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Sales_Contract_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Sales_Contract_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK: ' || CAST(COUNT(*) - COUNT(DISTINCT Sales_Contract_Key) AS STRING) || ' dups', current_timestamp()
# MAGIC FROM dim_sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_sales_contract', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Sales_Contract_Key IS NULL OR Contract_Number IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Sales_Contract_Key IS NULL OR Contract_Number IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null: Sales_Contract_Key, Contract_Number', current_timestamp()
# MAGIC FROM dim_sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_sales_contract', 'Population_Key_Columns', 'POP',
# MAGIC   CASE WHEN LEAST(100.0*COUNT(Contract_Number)/COUNT(*), 100.0*COUNT(Contract_Type)/COUNT(*), 100.0*COUNT(Contract_Status)/COUNT(*)) >= 95.0 THEN 'PASS' ELSE 'WARN' END,
# MAGIC   '95.0', CAST(ROUND(LEAST(100.0*COUNT(Contract_Number)/COUNT(*), 100.0*COUNT(Contract_Type)/COUNT(*), 100.0*COUNT(Contract_Status)/COUNT(*)), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Pop: Contract_Number, Type, Status', current_timestamp()
# MAGIC FROM dim_sales_contract
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'dim_sales_contract', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   b.Baseline_Value, CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4), FALSE, NULL,
# MAGIC   'Drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_sales_contract), _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_sales_contract' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;