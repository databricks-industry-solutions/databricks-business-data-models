# Databricks notebook source
# DBTITLE 1,Setup
# MAGIC %sql
# MAGIC -- Tutorial 02: Sales Order Performance
# MAGIC USE CATALOG manufacturing_silver_vibe;
# MAGIC USE SCHEMA sales_order;

# COMMAND ----------

# DBTITLE 1,Tutorial Introduction
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->
# MAGIC # Tutorial 02: Sales Order Performance
# MAGIC ## Delivery, Returns, and Credit — How Is the Domain Performing?
# MAGIC
# MAGIC **What you will learn:** Three core performance metrics for the Sales Order domain:
# MAGIC on-time delivery (OTD) rate, order return rate, and credit check approval rate.
# MAGIC
# MAGIC **Prerequisites:** [Tutorial 01: Scale](01 Sales Order Scale) — understanding entity row counts.
# MAGIC
# MAGIC **Next:** [Tutorial 03: Flow](03 Sales Order Flow) — order lifecycle and the delivery pipeline.

# COMMAND ----------

# DBTITLE 1,Q1: What is the on-time delivery performance?
# MAGIC %md
# MAGIC ## Question 1: How does Meridian perform on delivery timeliness?
# MAGIC
# MAGIC On-Time Delivery (OTD) = whether `actual_goods_issue_date` was on or before `planned_delivery_date`.
# MAGIC Negative DATEDIFF = early; zero = on time; positive = late.

# COMMAND ----------

# DBTITLE 1,Delivery OTD breakdown
# MAGIC %sql
# MAGIC -- Delivery on-time performance breakdown
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) < 0  THEN 'Early'
# MAGIC     WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) = 0  THEN 'On Time'
# MAGIC     WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) <= 3 THEN 'Slightly Late (1-3 days)'
# MAGIC     ELSE 'Late (4+ days)'
# MAGIC   END                                                            AS Delivery_Status,
# MAGIC   COUNT(*)                                                       AS Deliveries,
# MAGIC   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS Pct_Of_Deliveries,
# MAGIC   ROUND(AVG(ABS(DATEDIFF(actual_goods_issue_date, planned_delivery_date))), 1) AS Avg_Days_Deviation
# MAGIC FROM delivery
# MAGIC WHERE actual_goods_issue_date IS NOT NULL
# MAGIC   AND planned_delivery_date IS NOT NULL
# MAGIC GROUP BY 1
# MAGIC ORDER BY Deliveries DESC

# COMMAND ----------

# DBTITLE 1,Observation 1
# MAGIC %md
# MAGIC > **Observation:** Of 3,244 deliveries with known dates, **65.4% (2,083) were early** and
# MAGIC > **20.9% (667) were exactly on time** — making the combined on-or-early rate **86.3%**.
# MAGIC > **10.6% (337) were late by 4+ days** and **4.9% (157) were slightly late (1–3 days)**.
# MAGIC > The high early-delivery rate suggests Meridian's logistics teams ship ahead of schedule
# MAGIC > — which is generally positive but may indicate conservative planned delivery dates.

# COMMAND ----------

# DBTITLE 1,Q2: What is the order return rate?
# MAGIC %md
# MAGIC ## Question 2: What percentage of orders result in a return?
# MAGIC
# MAGIC Return orders from the Returns Portal link back to `order` via `return_order.original_order_id`.
# MAGIC The return rate is the share of orders with at least one associated RMA.

# COMMAND ----------

# DBTITLE 1,Order return rate
# MAGIC %sql
# MAGIC -- Order return rate (return_order.original_order_id is the FK to order)
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT o.order_id)                                AS Total_Orders,
# MAGIC   COUNT(DISTINCT r.original_order_id)                       AS Orders_With_Returns,
# MAGIC   ROUND(
# MAGIC     100.0 * COUNT(DISTINCT r.original_order_id)
# MAGIC             / NULLIF(COUNT(DISTINCT o.order_id), 0), 1
# MAGIC   )                                                         AS Return_Rate_Pct,
# MAGIC   COUNT(*) FILTER (WHERE r.original_order_id IS NOT NULL)   AS Total_RMAs
# MAGIC FROM `order` o
# MAGIC LEFT JOIN return_order r ON o.order_id = r.original_order_id

# COMMAND ----------

# DBTITLE 1,Observation 2
# MAGIC %md
# MAGIC > **Observation:** **4.5% of orders (227 of 5,000) resulted in at least one return**, with
# MAGIC > 227 total RMA records. The low rate suggests Meridian's order fulfilment quality is high,
# MAGIC > or that not all return paths flow through the Returns Portal system. Cross-referencing
# MAGIC > `return_order.reason_code` (sample query 17 in the Genie space) reveals which product
# MAGIC > categories or customer types drive the most returns.

# COMMAND ----------

# DBTITLE 1,Q3: What is the credit check approval rate?
# MAGIC %md
# MAGIC ## Question 3: How often do orders pass credit checks without being blocked?
# MAGIC
# MAGIC Credit checks are SAP events. Not all orders have a credit check record (62% coverage).
# MAGIC This query shows the breakdown for orders that were credit-checked.

# COMMAND ----------

# DBTITLE 1,Credit check pass/fail rate
# MAGIC %sql
# MAGIC -- Credit check pass/fail/warning breakdown
# MAGIC SELECT
# MAGIC   check_result                                                AS Result,
# MAGIC   COUNT(*)                                                    AS Checks,
# MAGIC   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)         AS Pct,
# MAGIC   ROUND(AVG(credit_limit), 0)                                 AS Avg_Credit_Limit,
# MAGIC   ROUND(AVG(exposure_before), 0)                              AS Avg_Exposure_Before
# MAGIC FROM credit_check
# MAGIC WHERE check_result IS NOT NULL
# MAGIC GROUP BY check_result
# MAGIC ORDER BY Checks DESC

# COMMAND ----------

# DBTITLE 1,Observation 3
# MAGIC %md
# MAGIC > **Observation:** Of 3,104 credit check events, **47.8% (1,485) were approved** on the first
# MAGIC > evaluation, **45.7% (1,418) were blocked**, and **6.5% (201) triggered a warning**.
# MAGIC > The near-equal split between approved and blocked suggests a significant portion of
# MAGIC > Meridian's orders face credit challenges — possibly reflecting customers approaching their
# MAGIC > credit limits. The `exposure_before` vs. `credit_limit` difference (visible in the Avg columns)
# MAGIC > explains whether blocks are driven by tight limits or high outstanding exposure.
# MAGIC
# MAGIC **Continue to [Tutorial 03: Flow](03 Sales Order Flow)** →