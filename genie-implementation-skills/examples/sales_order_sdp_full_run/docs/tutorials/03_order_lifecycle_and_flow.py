# Databricks notebook source
# DBTITLE 1,Tutorial 03: Order Lifecycle & Flow
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->
# MAGIC # Tutorial 03: Order Lifecycle & Flow
# MAGIC
# MAGIC This notebook answers: **How do orders flow from quotation through delivery, and what patterns emerge in the lifecycle?**
# MAGIC
# MAGIC Builds on the scale (01) and performance (02) context. Run each cell top-to-bottom.

# COMMAND ----------

# DBTITLE 1,Q1
# MAGIC %md
# MAGIC ### What's the quote-to-order conversion rate?

# COMMAND ----------

# DBTITLE 1,Quote Conversion
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_silver_sdp.quotation) AS Total_Quotes,
# MAGIC   (SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_silver_sdp.`order` WHERE quotation_id IS NOT NULL) AS Converted_Orders,
# MAGIC   ROUND((SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_silver_sdp.`order` WHERE quotation_id IS NOT NULL) * 100.0 /
# MAGIC         (SELECT COUNT(*) FROM manufacturing_silver_vibe.sales_order_silver_sdp.quotation), 1) AS Conversion_Rate_Pct

# COMMAND ----------

# DBTITLE 1,Obs 1
# MAGIC %md
# MAGIC **Observation:** Of 4,000 quotations in the CRM pipeline, approximately 19.9% converted to confirmed SAP orders. This is the cross-source resolution rate (quote → order via converted_order_number). The remaining 80% either lost, expired, or entered SAP directly without a formal quote.

# COMMAND ----------

# DBTITLE 1,Q2
# MAGIC %md
# MAGIC ### How many schedule lines does a typical order line generate?

# COMMAND ----------

# DBTITLE 1,Schedule Line Fan-Out
# MAGIC %sql
# MAGIC SELECT
# MAGIC   Schedule_Lines_Per_Order_Line,
# MAGIC   COUNT(*) AS Order_Lines_With_This_Count
# MAGIC FROM (
# MAGIC   SELECT ol.order_line_id, COUNT(osl.order_schedule_line_id) AS Schedule_Lines_Per_Order_Line
# MAGIC   FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_line ol
# MAGIC   LEFT JOIN manufacturing_silver_vibe.sales_order_silver_sdp.order_schedule_line osl
# MAGIC     ON ol.order_line_id = osl.order_line_id
# MAGIC   GROUP BY ol.order_line_id
# MAGIC )
# MAGIC GROUP BY Schedule_Lines_Per_Order_Line
# MAGIC ORDER BY Schedule_Lines_Per_Order_Line
# MAGIC LIMIT 10

# COMMAND ----------

# DBTITLE 1,Obs 2
# MAGIC %md
# MAGIC **Observation:** Most order lines have 1–2 schedule lines (single delivery), but some have many more — indicating partial deliveries or scheduling agreements with multiple call-offs. The total 22,212 schedule lines across 14,762 order lines averages 1.5 deliveries per line.

# COMMAND ----------

# DBTITLE 1,Q3
# MAGIC %md
# MAGIC ### What's the EDI message pattern — how much is automated vs. manual?

# COMMAND ----------

# DBTITLE 1,EDI Patterns
# MAGIC %sql
# MAGIC SELECT
# MAGIC   Message_Type,
# MAGIC   Message_Direction,
# MAGIC   COUNT(*) AS Messages
# MAGIC FROM manufacturing_silver_vibe.sales_order_silver_sdp.edi_order_message
# MAGIC GROUP BY Message_Type, Message_Direction
# MAGIC ORDER BY Messages DESC

# COMMAND ----------

# DBTITLE 1,Obs 3
# MAGIC %md
# MAGIC **Observation:** 956 EDI messages are tracked, showing the electronic order exchange pattern. The mix of inbound (customer-originated) vs. outbound (confirmations) and message types reveals the automation maturity of the order channel.

# COMMAND ----------

# DBTITLE 1,Q4
# MAGIC %md
# MAGIC ### How do contracts relate to actual orders? Are framework agreements being utilized?

# COMMAND ----------

# DBTITLE 1,Contract Utilization
# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT sc.sales_contract_id) AS Total_Contracts,
# MAGIC   COUNT(DISTINCT scl.sales_contract_line_id) AS Total_Contract_Lines,
# MAGIC   ROUND(COUNT(DISTINCT scl.sales_contract_line_id) * 1.0 / COUNT(DISTINCT sc.sales_contract_id), 1) AS Avg_Lines_Per_Contract
# MAGIC FROM manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract sc
# MAGIC LEFT JOIN manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract_line scl
# MAGIC   ON sc.sales_contract_id = scl.sales_contract_id

# COMMAND ----------

# DBTITLE 1,Obs 4
# MAGIC %md
# MAGIC **Observation:** 120 framework agreements contain 373 line items (avg ~3.1 lines per contract). These blanket agreements pre-negotiate pricing and quantities. The order-to-contract linkage would show call-off utilization but requires the contract_reference field on orders (not currently mapped).

# COMMAND ----------

# DBTITLE 1,Q5
# MAGIC %md
# MAGIC ### What's the monthly order volume trend?

# COMMAND ----------

# DBTITLE 1,Monthly Order Trend
# MAGIC %sql
# MAGIC SELECT
# MAGIC   DATE_TRUNC('month', Order_Date) AS Month,
# MAGIC   COUNT(*) AS Orders,
# MAGIC   SUM(Net_Value) AS Revenue
# MAGIC FROM manufacturing_silver_vibe.sales_order_silver_sdp.`order`
# MAGIC WHERE Order_Date IS NOT NULL
# MAGIC GROUP BY DATE_TRUNC('month', Order_Date)
# MAGIC ORDER BY Month

# COMMAND ----------

# DBTITLE 1,Obs 5
# MAGIC %md
# MAGIC **Observation:** The monthly trend reveals seasonality and growth patterns in the order book. Spikes may indicate bulk contract releases or quarter-end purchasing behavior.

# COMMAND ----------

# DBTITLE 1,What's Next
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## What's Next
# MAGIC
# MAGIC You've seen the **scale** (Tutorial 01), the **performance** (Tutorial 02), and the **flow** (Tutorial 03) of this sales order operation.
# MAGIC
# MAGIC * **Genie Space** — ask any ad-hoc question interactively
# MAGIC * **Model Guide** — full column dictionary and schema reference
# MAGIC * **Domain Narrative** — the full story of why this model exists and how it fits together