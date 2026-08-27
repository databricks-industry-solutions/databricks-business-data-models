# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Tutorial 01: Sales Order at a Glance
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->
# MAGIC # Tutorial 01: Sales Order at a Glance
# MAGIC
# MAGIC This notebook answers: **How big is this sales operation, where does revenue concentrate, and what's the order composition?**
# MAGIC
# MAGIC Run each cell top-to-bottom. Every SQL cell returns real data from the gold star schema.

# COMMAND ----------

# DBTITLE 1,Q1
# MAGIC %md
# MAGIC ### How much revenue flows through this sales operation, and across how many orders?

# COMMAND ----------

# DBTITLE 1,Revenue Scale
# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT Order_Number) AS Total_Orders,
# MAGIC   COUNT(*) AS Total_Lines,
# MAGIC   ROUND(SUM(Net_Value), 2) AS Total_Revenue,
# MAGIC   ROUND(AVG(Net_Value), 2) AS Avg_Line_Value
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line

# COMMAND ----------

# DBTITLE 1,Obs 1
# MAGIC %md
# MAGIC **Observation:** The operation tracks 5,000 orders comprising 14,762 line items, generating ~$332M in total revenue. The average line value is ~$22.5K — consistent with B2B manufacturing transactions (high-value, low-volume).

# COMMAND ----------

# DBTITLE 1,Q2
# MAGIC %md
# MAGIC ### How is revenue distributed across sales areas (market segments)?

# COMMAND ----------

# DBTITLE 1,Revenue by Sales Area
# MAGIC %sql
# MAGIC SELECT
# MAGIC   sa.Sales_Organization,
# MAGIC   sa.Distribution_Channel,
# MAGIC   COUNT(*) AS Lines,
# MAGIC   ROUND(SUM(f.Net_Value), 2) AS Revenue,
# MAGIC   ROUND(SUM(f.Net_Value) * 100.0 / SUM(SUM(f.Net_Value)) OVER (), 1) AS Revenue_Pct
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line f
# MAGIC JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_sales_area sa
# MAGIC   ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC GROUP BY sa.Sales_Organization, sa.Distribution_Channel
# MAGIC ORDER BY Revenue DESC

# COMMAND ----------

# DBTITLE 1,Obs 2
# MAGIC %md
# MAGIC **Observation:** Channel 10 dominates with 41% of revenue ($136M, 6,044 lines), followed by Channel 20 at 34%. Channel 40 is the smallest at just 5% — likely a specialized or newer route to market.

# COMMAND ----------

# DBTITLE 1,Q3
# MAGIC %md
# MAGIC ### Who are the top customers driving the most order volume?

# COMMAND ----------

# DBTITLE 1,Top Customers
# MAGIC %sql
# MAGIC SELECT
# MAGIC   c.Customer_Number,
# MAGIC   c.Customer_Name,
# MAGIC   COUNT(*) AS Order_Lines,
# MAGIC   ROUND(SUM(f.Net_Value), 2) AS Revenue
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line f
# MAGIC JOIN manufacturing_silver_vibe.sales_order_gold_sdp.dim_customer c
# MAGIC   ON f.Customer_Key = c.Customer_Key
# MAGIC WHERE f.Customer_Key IS NOT NULL
# MAGIC GROUP BY c.Customer_Number, c.Customer_Name
# MAGIC ORDER BY Revenue DESC
# MAGIC LIMIT 10

# COMMAND ----------

# DBTITLE 1,Obs 3
# MAGIC %md
# MAGIC **Observation:** The top 10 customers account for a meaningful share of total order volume. Revenue is spread across 300 distinct Sold-To customers, indicating a diversified B2B customer base rather than dependence on a handful of accounts.

# COMMAND ----------

# DBTITLE 1,Q4
# MAGIC %md
# MAGIC ### What types of orders exist, and what's the rejection rate?

# COMMAND ----------

# DBTITLE 1,Order Types and Rejections
# MAGIC %sql
# MAGIC SELECT
# MAGIC   Order_Type,
# MAGIC   COUNT(*) AS Lines,
# MAGIC   SUM(CASE WHEN Is_Rejected THEN 1 ELSE 0 END) AS Rejected_Lines,
# MAGIC   ROUND(SUM(CASE WHEN Is_Rejected THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS Rejection_Rate_Pct
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line
# MAGIC GROUP BY Order_Type
# MAGIC ORDER BY Lines DESC

# COMMAND ----------

# DBTITLE 1,Obs 4
# MAGIC %md
# MAGIC **Observation:** The rejection rate across order types shows how often lines are cancelled or refused. This metric is a leading indicator of order quality and customer satisfaction.

# COMMAND ----------

# DBTITLE 1,Q5
# MAGIC %md
# MAGIC ### How many materials (products) are sold, and how concentrated is the portfolio?

# COMMAND ----------

# DBTITLE 1,Material Portfolio
# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT Material_Key) AS Total_Materials,
# MAGIC   COUNT(*) AS Total_Lines,
# MAGIC   ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT Material_Key), 1) AS Avg_Lines_Per_Material
# MAGIC FROM manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line
# MAGIC WHERE Material_Key IS NOT NULL

# COMMAND ----------

# DBTITLE 1,Obs 5
# MAGIC %md
# MAGIC **Observation:** 800 distinct materials are sold across 14,762 order lines — averaging ~18 lines per material. This indicates a broad product catalog with moderate concentration.

# COMMAND ----------

# DBTITLE 1,What's Next
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## What's Next
# MAGIC
# MAGIC * **Tutorial 02: Delivery & Risk Performance** — OTD rates, credit risk, and returns analysis
# MAGIC * **Genie Space** — ask ad-hoc questions interactively
# MAGIC * **Model Guide** — full column dictionary and schema reference