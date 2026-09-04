# Databricks notebook source
# DBTITLE 1,Tutorial 02: Delivery & Risk Performance
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->
# MAGIC # Tutorial 02: Delivery & Risk Performance
# MAGIC
# MAGIC This notebook answers: **How is delivery performance, what does credit risk look like, and what's the return profile?**
# MAGIC
# MAGIC Builds on the scale context from Tutorial 01. Run each cell top-to-bottom.

# COMMAND ----------

# DBTITLE 1,Q1
# MAGIC %md
# MAGIC ### What's the overall on-time delivery rate?

# COMMAND ----------

# DBTITLE 1,OTD Rate
# MAGIC %sql
# MAGIC SELECT
# MAGIC   OTD_Status,
# MAGIC   COUNT(*) AS Schedule_Lines,
# MAGIC   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS Pct
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_otd
# MAGIC GROUP BY OTD_Status
# MAGIC ORDER BY OTD_Status

# COMMAND ----------

# DBTITLE 1,Obs 1
# MAGIC %md
# MAGIC **Observation:** Only 45.8% of schedule lines are ON_TIME (10,168 of 22,212); 54.2% are LATE (12,044). Note: this is a *proxy* metric based on scheduled vs. current date — actual delivery confirmation (likp/lips) is a P0 gap. Even as a proxy, this signals delivery pressure across the order book.

# COMMAND ----------

# DBTITLE 1,Q2
# MAGIC %md
# MAGIC ### What does the credit risk distribution look like?

# COMMAND ----------

# DBTITLE 1,Credit Risk Distribution
# MAGIC %sql
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN Credit_Utilization_Pct < 50 THEN '1. Low (<50%)'
# MAGIC     WHEN Credit_Utilization_Pct < 80 THEN '2. Medium (50-80%)'
# MAGIC     WHEN Credit_Utilization_Pct < 100 THEN '3. High (80-100%)'
# MAGIC     ELSE '4. Over-limit (>100%)'
# MAGIC   END AS Risk_Band,
# MAGIC   COUNT(*) AS Checks,
# MAGIC   ROUND(AVG(Credit_Utilization_Pct), 1) AS Avg_Utilization
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_credit_check
# MAGIC GROUP BY 1
# MAGIC ORDER BY 1

# COMMAND ----------

# DBTITLE 1,Obs 2
# MAGIC %md
# MAGIC **Observation:** The credit check events distribute across risk bands, showing the enterprise's credit exposure profile. Orders in the "over-limit" band required manual approval or holds, directly impacting order fulfillment cycle time.

# COMMAND ----------

# DBTITLE 1,Q3
# MAGIC %md
# MAGIC ### How many returns are there, and what's the return rate relative to orders?

# COMMAND ----------

# DBTITLE 1,Return Profile
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_return_line) AS Return_Lines,
# MAGIC   (SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line) AS Order_Lines,
# MAGIC   ROUND((SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_return_line) * 100.0 /
# MAGIC         (SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line), 2) AS Return_Rate_Pct

# COMMAND ----------

# DBTITLE 1,Obs 3
# MAGIC %md
# MAGIC **Observation:** 329 return lines against 14,762 order lines = a 2.2% return rate. This is relatively low for B2B manufacturing. The return reason classification is unavailable (P1 gap — portal vocab doesn't map to SAP codes), so root-cause analysis by reason is currently blocked.

# COMMAND ----------

# DBTITLE 1,Q4
# MAGIC %md
# MAGIC ### Which customers have the highest credit utilization?

# COMMAND ----------

# DBTITLE 1,High-Risk Customers
# MAGIC %sql
# MAGIC SELECT
# MAGIC   c.Customer_Number,
# MAGIC   c.Customer_Name,
# MAGIC   COUNT(*) AS Credit_Checks,
# MAGIC   ROUND(AVG(cc.Credit_Utilization_Pct), 1) AS Avg_Utilization_Pct,
# MAGIC   ROUND(MAX(cc.Credit_Utilization_Pct), 1) AS Max_Utilization_Pct
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_credit_check cc
# MAGIC JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_customer c
# MAGIC   ON cc.Customer_Key = c.Customer_Key
# MAGIC WHERE cc.Customer_Key IS NOT NULL
# MAGIC GROUP BY c.Customer_Number, c.Customer_Name
# MAGIC ORDER BY Avg_Utilization_Pct DESC
# MAGIC LIMIT 10

# COMMAND ----------

# DBTITLE 1,Obs 4
# MAGIC %md
# MAGIC **Observation:** The top 10 customers by credit utilization consistently push toward or beyond their credit limits. These are candidates for proactive credit line reviews or payment term renegotiation.

# COMMAND ----------

# DBTITLE 1,Q5
# MAGIC %md
# MAGIC ### What's the warranty return profile?

# COMMAND ----------

# DBTITLE 1,Warranty Returns
# MAGIC %sql
# MAGIC SELECT
# MAGIC   CASE WHEN Is_Warranty THEN 'Warranty' ELSE 'Non-Warranty' END AS Return_Type,
# MAGIC   COUNT(*) AS Return_Lines,
# MAGIC   SUM(Return_Quantity) AS Total_Qty,
# MAGIC   ROUND(SUM(Return_Value), 2) AS Total_Value
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_return_line
# MAGIC GROUP BY Is_Warranty
# MAGIC ORDER BY Return_Lines DESC

# COMMAND ----------

# DBTITLE 1,Obs 5
# MAGIC %md
# MAGIC **Observation:** The warranty vs. non-warranty split shows what proportion of returns are covered claims vs. customer-initiated RMAs. Warranty returns have different financial treatment (credit notes vs. repair costs).

# COMMAND ----------

# DBTITLE 1,What's Next
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## What's Next
# MAGIC
# MAGIC * **Tutorial 03: Order Lifecycle & Flow** — quote-to-order conversion, order-to-delivery lifecycle, EDI patterns
# MAGIC * **Genie Space** — ask ad-hoc questions interactively
# MAGIC * **Model Guide** — full column dictionary and schema reference