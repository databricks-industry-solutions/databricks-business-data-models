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
# MAGIC # dim_date — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Standard generated calendar dimension covering 2024-07-01 to 2026-06-30 (730 days). Supports all date-role FK relationships across facts (Order_Date, Requested_Delivery_Date, Quote_Date, RMA_Date, Check_Date).
# MAGIC
# MAGIC ## Grain
# MAGIC One row per calendar date. Expected 730 rows.
# MAGIC
# MAGIC ## Natural Key
# MAGIC `Date_Key` (DATE type, self-keyed — no hash surrogate needed)
# MAGIC
# MAGIC ## Source
# MAGIC Generated via `SEQUENCE(DATE'2024-07-01', DATE'2026-06-30', INTERVAL 1 DAY)` — no silver source table.
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Parent of:** fact_sales_order_line (Order_Date_Key, Requested_Delivery_Date_Key), fact_otd (Requested_Delivery_Date_Key), fact_quotation_line (Quote_Date_Key), fact_return_line (RMA_Date_Key), fact_credit_check (Check_Date_Key)
# MAGIC - **Child of:** Root dimension (no parent)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - None (generated dimension — fully deterministic)
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-08-08
# MAGIC - **Grade at build:** Verified (730 rows, 0 PK dups)
# MAGIC - **Fixes applied:** DAYOFWEEK_ISO → WEEKDAY()+1 (serverless compatibility)

# COMMAND ----------

# DBTITLE 1,Row Count & PK Uniqueness
# MAGIC %sql
# MAGIC -- Row count check
# MAGIC SELECT
# MAGIC   'dim_date' AS Entity,
# MAGIC   COUNT(*) AS Row_Count,
# MAGIC   MIN(Date_Key) AS Earliest_Date,
# MAGIC   MAX(Date_Key) AS Latest_Date,
# MAGIC   DATEDIFF(MAX(Date_Key), MIN(Date_Key)) + 1 AS Expected_Days
# MAGIC FROM dim_date;
# MAGIC
# MAGIC -- PK uniqueness: expect 0 duplicates
# MAGIC SELECT
# MAGIC   'dim_date' AS Entity,
# MAGIC   'PK_Uniqueness' AS Check_Name,
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   COUNT(DISTINCT Date_Key) AS Distinct_Keys,
# MAGIC   COUNT(*) - COUNT(DISTINCT Date_Key) AS Duplicate_Count,
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Date_Key) THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_date;

# COMMAND ----------

# DBTITLE 1,BK Null Check
# MAGIC %sql
# MAGIC -- Business Key null check (Date_Key is the NK and PK)
# MAGIC SELECT 'BK_Null_Check' AS Check_Name,
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   SUM(CASE WHEN Date_Key IS NULL THEN 1 ELSE 0 END) AS Date_Key_Null,
# MAGIC   CASE WHEN SUM(CASE WHEN Date_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS Status
# MAGIC FROM dim_date;

# COMMAND ----------

# DBTITLE 1,Population Check
# MAGIC %sql
# MAGIC -- Column population rates for all business columns
# MAGIC SELECT
# MAGIC   COUNT(*) AS Total_Rows,
# MAGIC   ROUND(100.0 * COUNT(Year) / COUNT(*), 2) AS Year_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Quarter) / COUNT(*), 2) AS Quarter_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Month) / COUNT(*), 2) AS Month_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Month_Name) / COUNT(*), 2) AS Month_Name_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Week_Of_Year) / COUNT(*), 2) AS Week_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Day_Of_Week) / COUNT(*), 2) AS Day_Of_Week_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Day_Name) / COUNT(*), 2) AS Day_Name_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Is_Weekday) / COUNT(*), 2) AS Is_Weekday_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Fiscal_Year) / COUNT(*), 2) AS Fiscal_Year_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Fiscal_Quarter) / COUNT(*), 2) AS Fiscal_Qtr_Pop_Pct,
# MAGIC   ROUND(100.0 * COUNT(Fiscal_Period) / COUNT(*), 2) AS Fiscal_Period_Pop_Pct
# MAGIC FROM dim_date;

# COMMAND ----------

# DBTITLE 1,Drift Check
# MAGIC %sql
# MAGIC -- Drift detection: compare current row count to baseline
# MAGIC SELECT
# MAGIC   b.Table_Name,
# MAGIC   b.Metric_Type,
# MAGIC   CAST(b.Baseline_Value AS INT) AS Baseline_Rows,
# MAGIC   (SELECT COUNT(*) FROM dim_date) AS Current_Rows,
# MAGIC   ROUND(ABS((SELECT COUNT(*) FROM dim_date) - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 2) AS Drift_Pct,
# MAGIC   CASE
# MAGIC     WHEN ABS((SELECT COUNT(*) FROM dim_date) - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 > b.Tolerance_Pct THEN 'DRIFT_ALERT'
# MAGIC     ELSE 'WITHIN_TOLERANCE'
# MAGIC   END AS Drift_Status
# MAGIC FROM _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_date' AND b.Is_Active = TRUE;

# COMMAND ----------

# DBTITLE 1,Data Profile
# MAGIC %sql
# MAGIC -- Data profile: calendar coverage and fiscal structure
# MAGIC SELECT
# MAGIC   COUNT(*) AS Total_Days,
# MAGIC   COUNT(DISTINCT Year) AS Distinct_Years,
# MAGIC   COUNT(DISTINCT Fiscal_Year) AS Distinct_Fiscal_Years,
# MAGIC   SUM(CASE WHEN Is_Weekday THEN 1 ELSE 0 END) AS Weekdays,
# MAGIC   SUM(CASE WHEN NOT Is_Weekday THEN 1 ELSE 0 END) AS Weekends,
# MAGIC   MIN(Date_Key) AS First_Date,
# MAGIC   MAX(Date_Key) AS Last_Date,
# MAGIC   COUNT(DISTINCT Fiscal_Period) AS Distinct_Fiscal_Periods
# MAGIC FROM dim_date;

# COMMAND ----------

# DBTITLE 1,Sample Rows
# MAGIC %sql
# MAGIC -- Sample: first day of each fiscal quarter
# MAGIC SELECT Date_Key, Year, Quarter, Month_Name, Day_Name, Is_Weekday, Fiscal_Year, Fiscal_Quarter, Fiscal_Period
# MAGIC FROM dim_date
# MAGIC WHERE Day_Of_Week = 1 AND Month IN (1, 4, 7, 10)
# MAGIC ORDER BY Date_Key
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC -- Write validation results (PENDING→claim)
# MAGIC DELETE FROM _validation_check_detail
# MAGIC WHERE Run_Id = 'PENDING' AND Table_Name = 'dim_date';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC -- PK uniqueness
# MAGIC SELECT 'PENDING', 'dim_date', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = COUNT(DISTINCT Date_Key) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT Date_Key) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK uniqueness: ' || CAST(COUNT(*) - COUNT(DISTINCT Date_Key) AS STRING) || ' dups',
# MAGIC   current_timestamp()
# MAGIC FROM dim_date
# MAGIC UNION ALL
# MAGIC -- BK null check
# MAGIC SELECT 'PENDING', 'dim_date', 'BK_Null_Check', 'BK',
# MAGIC   CASE WHEN SUM(CASE WHEN Date_Key IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(SUM(CASE WHEN Date_Key IS NULL THEN 1 ELSE 0 END) AS STRING), NULL, FALSE, NULL,
# MAGIC   'BK null check: Date_Key', current_timestamp()
# MAGIC FROM dim_date
# MAGIC UNION ALL
# MAGIC -- Population (lowest across all columns)
# MAGIC SELECT 'PENDING', 'dim_date', 'Population_All_Columns', 'POP',
# MAGIC   CASE WHEN MIN(pop) >= 95.0 THEN 'PASS' WHEN MIN(pop) >= 80.0 THEN 'WARN' ELSE 'FAIL' END,
# MAGIC   '95.0', CAST(ROUND(MIN(pop), 2) AS STRING), NULL, FALSE, NULL,
# MAGIC   'Lowest population: ' || CAST(ROUND(MIN(pop), 2) AS STRING) || '%', current_timestamp()
# MAGIC FROM (
# MAGIC   SELECT LEAST(
# MAGIC     100.0 * COUNT(Year)/COUNT(*), 100.0 * COUNT(Quarter)/COUNT(*),
# MAGIC     100.0 * COUNT(Month)/COUNT(*), 100.0 * COUNT(Month_Name)/COUNT(*),
# MAGIC     100.0 * COUNT(Week_Of_Year)/COUNT(*), 100.0 * COUNT(Day_Of_Week)/COUNT(*),
# MAGIC     100.0 * COUNT(Day_Name)/COUNT(*), 100.0 * COUNT(Is_Weekday)/COUNT(*),
# MAGIC     100.0 * COUNT(Fiscal_Year)/COUNT(*), 100.0 * COUNT(Fiscal_Quarter)/COUNT(*),
# MAGIC     100.0 * COUNT(Fiscal_Period)/COUNT(*)
# MAGIC   ) AS pop FROM dim_date
# MAGIC )
# MAGIC UNION ALL
# MAGIC -- Drift (row count vs baseline)
# MAGIC SELECT 'PENDING', 'dim_date', 'Drift_Row_Count', 'DRIFT',
# MAGIC   CASE WHEN ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100 <= b.Tolerance_Pct THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   CAST(b.Baseline_Value AS STRING), CAST(cnt AS STRING),
# MAGIC   ROUND(ABS(cnt - CAST(b.Baseline_Value AS INT)) / CAST(b.Baseline_Value AS DECIMAL(20,4)) * 100, 4),
# MAGIC   FALSE, NULL,
# MAGIC   'Row count drift: baseline=' || b.Baseline_Value || ' current=' || CAST(cnt AS STRING), current_timestamp()
# MAGIC FROM (SELECT COUNT(*) AS cnt FROM dim_date),
# MAGIC      _data_drift_baseline b
# MAGIC WHERE b.Table_Name = 'dim_date' AND b.Metric_Type = 'ROW_COUNT' AND b.Is_Active = TRUE;