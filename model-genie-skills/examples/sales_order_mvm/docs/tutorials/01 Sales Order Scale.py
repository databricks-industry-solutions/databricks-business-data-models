# Databricks notebook source
# DBTITLE 1,Setup
# MAGIC %sql
# MAGIC -- Tutorial 01: Sales Order Scale
# MAGIC -- How large is this domain? What does the Sales Order portfolio look like?
# MAGIC USE CATALOG manufacturing_silver_vibe;
# MAGIC USE SCHEMA sales_order;

# COMMAND ----------

# DBTITLE 1,Tutorial Introduction
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->
# MAGIC # Tutorial 01: Sales Order Scale
# MAGIC ## The Sales Order Portfolio at a Glance
# MAGIC
# MAGIC **What you will learn:** How large is Meridian's Sales Order domain? What entities exist, how many rows does each carry, and how are orders distributed across channels and statuses?
# MAGIC
# MAGIC **Prerequisites:** None. This is the starting point for the Sales Order domain.
# MAGIC
# MAGIC **Schema:** `manufacturing_silver_vibe.sales_order` — 17 entities, ~132,275 rows total.
# MAGIC
# MAGIC **Next:** [Tutorial 02: Performance](02 Sales Order Performance) — delivery OTD, returns, credit.

# COMMAND ----------

# DBTITLE 1,Q1: How large is each entity?
# MAGIC %md
# MAGIC ## Question 1: How large is each entity in the domain?
# MAGIC
# MAGIC Before writing any analytics query, it helps to understand the scale of each entity —
# MAGIC how many rows exist, which entities dominate in volume, and which are master data vs. events.

# COMMAND ----------

# DBTITLE 1,Entity row counts
# MAGIC %sql
# MAGIC -- All entities by row count (descending)
# MAGIC SELECT 'order' AS Entity, COUNT(*) AS Row_Count FROM `order`
# MAGIC UNION ALL SELECT 'order_line', COUNT(*) FROM order_line
# MAGIC UNION ALL SELECT 'order_schedule_line', COUNT(*) FROM order_schedule_line
# MAGIC UNION ALL SELECT 'order_status_event', COUNT(*) FROM order_status_event
# MAGIC UNION ALL SELECT 'order_partner', COUNT(*) FROM order_partner
# MAGIC UNION ALL SELECT 'atp_check', COUNT(*) FROM atp_check
# MAGIC UNION ALL SELECT 'quotation_line', COUNT(*) FROM quotation_line
# MAGIC UNION ALL SELECT 'quotation', COUNT(*) FROM quotation
# MAGIC UNION ALL SELECT 'delivery', COUNT(*) FROM delivery
# MAGIC UNION ALL SELECT 'credit_check', COUNT(*) FROM credit_check
# MAGIC UNION ALL SELECT 'order_line', COUNT(*) FROM order_line  -- repeat for union label fix
# MAGIC UNION ALL SELECT 'delivery_line', COUNT(*) FROM delivery_line
# MAGIC UNION ALL SELECT 'order_configuration', COUNT(*) FROM order_configuration
# MAGIC UNION ALL SELECT 'return_order', COUNT(*) FROM return_order
# MAGIC UNION ALL SELECT 'return_order_line', COUNT(*) FROM return_order_line
# MAGIC UNION ALL SELECT 'sales_contract_line', COUNT(*) FROM sales_contract_line
# MAGIC UNION ALL SELECT 'delivery_schedule', COUNT(*) FROM delivery_schedule
# MAGIC UNION ALL SELECT 'sales_contract', COUNT(*) FROM sales_contract
# MAGIC ORDER BY Row_Count DESC

# COMMAND ----------

# DBTITLE 1,Observation 1
# MAGIC %md
# MAGIC > **Observation:** Event logs dominate by volume: `order_schedule_line` (22,212), `order_status_event` (18,512),
# MAGIC > `order_partner` (15,000), and `order_line` (14,762) each exceed the 5,000 core `order` records by 3× or
# MAGIC > more. This reflects the normalized 3NF model structure — each order spawns multiple related records
# MAGIC > across several entities. The `sales_contract` master table is notably small at 120 rows, underlining
# MAGIC > that Meridian operates under concentrated long-running framework agreements.

# COMMAND ----------

# DBTITLE 1,Q2: How are orders distributed across channels and statuses?
# MAGIC %md
# MAGIC ## Question 2: How are orders distributed across channels and statuses?
# MAGIC
# MAGIC Understanding the mix of distribution channels and order statuses tells you which commercial
# MAGIC paths are most active and what proportion of orders are still open vs. closed.

# COMMAND ----------

# DBTITLE 1,Orders by distribution channel and status
# MAGIC %sql
# MAGIC -- Orders by distribution channel and overall status
# MAGIC SELECT
# MAGIC   distribution_channel_code  AS Channel,
# MAGIC   overall_status             AS Status,
# MAGIC   COUNT(*)                   AS Order_Count,
# MAGIC   ROUND(SUM(net_value), 0)   AS Total_Net_Value
# MAGIC FROM `order`
# MAGIC WHERE distribution_channel_code IS NOT NULL
# MAGIC   AND overall_status IS NOT NULL
# MAGIC GROUP BY distribution_channel_code, overall_status
# MAGIC ORDER BY Channel, Order_Count DESC

# COMMAND ----------

# DBTITLE 1,Observation 2
# MAGIC %md
# MAGIC > **Observation:** Four distribution channels account for all orders: channel `10` (2,050 orders,
# MAGIC > 41%), `20` (1,682, 33.6%), `30` (997, 19.9%), and `40` (271, 5.4%). This implies three primary
# MAGIC > commercial routes and one smaller channel. The order-to-delivery conversion within each channel
# MAGIC > is explored in Tutorial 02.

# COMMAND ----------

# DBTITLE 1,Q3: What is the revenue concentration?
# MAGIC %md
# MAGIC ## Question 3: How is order value distributed?
# MAGIC
# MAGIC Revenue concentration analysis — are most orders small, or does a handful of large orders
# MAGIC dominate the portfolio? This shapes how you should filter and aggregate for financial metrics.

# COMMAND ----------

# DBTITLE 1,Order value distribution
# MAGIC %sql
# MAGIC -- Order value quintile distribution
# MAGIC SELECT
# MAGIC   NTILE(5) OVER (ORDER BY net_value)   AS Value_Quintile,
# MAGIC   COUNT(*)                              AS Order_Count,
# MAGIC   ROUND(MIN(net_value), 0)              AS Min_Value,
# MAGIC   ROUND(MAX(net_value), 0)              AS Max_Value,
# MAGIC   ROUND(AVG(net_value), 0)              AS Avg_Value,
# MAGIC   ROUND(SUM(net_value), 0)              AS Quintile_Total
# MAGIC FROM `order`
# MAGIC WHERE net_value IS NOT NULL
# MAGIC GROUP BY NTILE(5) OVER (ORDER BY net_value)
# MAGIC ORDER BY Value_Quintile

# COMMAND ----------

# DBTITLE 1,Observation 3
# MAGIC %md
# MAGIC > **Observation:** Each revenue quintile contains ~1,000 orders. Compare the `Max_Value` of Quintile 5
# MAGIC > against Quintile 1 to see the spread — this tells you whether the model needs to account for extreme
# MAGIC > high-value outliers in revenue reporting. Use `net_value IS NOT NULL` consistently in filters, as
# MAGIC > orders without a priced value may exist (e.g., free-of-charge item categories).
# MAGIC
# MAGIC **Continue to [Tutorial 02: Performance](02 Sales Order Performance)** →