# Databricks notebook source
# DBTITLE 1,Setup
# MAGIC %sql
# MAGIC -- Tutorial 03: Sales Order Flow
# MAGIC USE CATALOG manufacturing_silver_vibe;
# MAGIC USE SCHEMA sales_order;

# COMMAND ----------

# DBTITLE 1,Tutorial Introduction
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->
# MAGIC # Tutorial 03: Sales Order Flow
# MAGIC ## How Do Sales Orders Move Through the System?
# MAGIC
# MAGIC **What you will learn:** The lifecycle of a sales order — from creation through confirmation,
# MAGIC delivery, and invoicing — and how the ATP availability check shapes delivery commitments.
# MAGIC
# MAGIC **Prerequisites:** [Tutorial 01: Scale](01 Sales Order Scale) + [Tutorial 02: Performance](02 Sales Order Performance).
# MAGIC
# MAGIC This tutorial uses the `order_status_event` lifecycle log and `atp_check` event table
# MAGIC alongside the core `order` and `delivery` entities.

# COMMAND ----------

# DBTITLE 1,Q1: What lifecycle stages does a sales order pass through?
# MAGIC %md
# MAGIC ## Question 1: What are the lifecycle event types and their reach?
# MAGIC
# MAGIC `order_status_event` is an append-only log of every status change on a sales order.
# MAGIC Each row captures `event_type`, `previous_status`, `new_status`, and a timestamp.
# MAGIC Counting events by type reveals the lifecycle funnel.

# COMMAND ----------

# DBTITLE 1,Order lifecycle event funnel
# MAGIC %sql
# MAGIC -- Order lifecycle funnel: events by type
# MAGIC SELECT
# MAGIC   event_type,
# MAGIC   COUNT(*)                  AS Event_Count,
# MAGIC   COUNT(DISTINCT order_id)  AS Distinct_Orders,
# MAGIC   ROUND(100.0 * COUNT(DISTINCT order_id) / (
# MAGIC     SELECT COUNT(DISTINCT order_id) FROM `order`
# MAGIC   ), 1)                     AS Pct_Of_All_Orders
# MAGIC FROM order_status_event
# MAGIC WHERE event_type IS NOT NULL
# MAGIC GROUP BY event_type
# MAGIC ORDER BY Event_Count DESC

# COMMAND ----------

# DBTITLE 1,Observation 1
# MAGIC %md
# MAGIC > **Observation:** The lifecycle funnel is visible in the event types:
# MAGIC > - **order_created**: 5,000 events — 100% of orders have a creation event
# MAGIC > - **order_confirmed**: 4,502 (90.0%) — 9.8% of orders were not confirmed (rejected or on hold)
# MAGIC > - **delivery_created + goods_issued**: 3,244 each (64.9%) — all created deliveries had goods issued
# MAGIC > - **invoiced**: 2,522 (50.4%) — approximately half of orders are fully invoiced
# MAGIC >
# MAGIC > This funnel highlights that 35.1% of confirmed orders have no delivery record yet —
# MAGIC > either still open, pending shipment, or blocked. Compare with the ~64.9% delivery
# MAGIC > coverage from Tutorial 02 to corroborate.

# COMMAND ----------

# DBTITLE 1,Q2: How does ATP availability shaping affect delivery?
# MAGIC %md
# MAGIC ## Question 2: How do ATP checks affect quantity confirmation?
# MAGIC
# MAGIC ATP (Available-to-Promise) checks are fired when an order line is created or changed.
# MAGIC The check determines whether the requested quantity can be confirmed for the requested date.
# MAGIC The `check_status` column captures the outcome.

# COMMAND ----------

# DBTITLE 1,ATP check confirmation rates
# MAGIC %sql
# MAGIC -- ATP check status and quantity confirmation rates
# MAGIC SELECT
# MAGIC   check_status,
# MAGIC   COUNT(*)                                                      AS Checks,
# MAGIC   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS Pct_Of_Checks,
# MAGIC   ROUND(SUM(requested_quantity), 0)                             AS Total_Requested,
# MAGIC   ROUND(SUM(confirmed_quantity), 0)                             AS Total_Confirmed,
# MAGIC   ROUND(
# MAGIC     100.0 * SUM(confirmed_quantity) / NULLIF(SUM(requested_quantity), 0)
# MAGIC   , 1)                                                          AS Qty_Confirmation_Rate_Pct
# MAGIC FROM atp_check
# MAGIC WHERE check_status IS NOT NULL
# MAGIC GROUP BY check_status
# MAGIC ORDER BY Checks DESC

# COMMAND ----------

# DBTITLE 1,Observation 2
# MAGIC %md
# MAGIC > **Observation:** **69.4% of ATP checks (8,329) are fully CONFIRMED** — the requested quantity
# MAGIC > was available and the delivery date was met. The remaining 30.6% faced availability
# MAGIC > constraints: PARTIALLY_CONFIRMED (1,816 — only 49.8% of requested qty confirmed),
# MAGIC > NOT_CONFIRMED (1,230 — 50.4% partial confirmation despite the "not confirmed" status),
# MAGIC > and BACKORDER (625 — 51.5%). The consistent ~50% confirmation rate across non-CONFIRMED
# MAGIC > statuses suggests a split-delivery pattern where about half the quantity can be
# MAGIC > sourced immediately and the rest is deferred.

# COMMAND ----------

# DBTITLE 1,Q3: What is the delivery pipeline volume?
# MAGIC %md
# MAGIC ## Question 3: What does the delivery schedule commitment calendar look like?
# MAGIC
# MAGIC `order_schedule_line` records the planned split-delivery dates and confirmed quantities
# MAGIC for each order line. This is the most granular forward-commitment view in the domain.

# COMMAND ----------

# DBTITLE 1,Schedule line delivery commitments by month
# MAGIC %sql
# MAGIC -- Delivery schedule commitment by month (historic + forward)
# MAGIC SELECT
# MAGIC   DATE_FORMAT(scheduled_delivery_date, 'yyyy-MM') AS Delivery_Month,
# MAGIC   COUNT(*)                                        AS Schedule_Lines,
# MAGIC   ROUND(SUM(confirmed_quantity), 0)               AS Total_Confirmed_Qty,
# MAGIC   ROUND(SUM(ordered_quantity), 0)                 AS Total_Ordered_Qty,
# MAGIC   ROUND(
# MAGIC     100.0 * SUM(confirmed_quantity) / NULLIF(SUM(ordered_quantity), 0)
# MAGIC   , 1)                                            AS Confirmation_Rate_Pct
# MAGIC FROM order_schedule_line
# MAGIC WHERE scheduled_delivery_date IS NOT NULL
# MAGIC GROUP BY DATE_FORMAT(scheduled_delivery_date, 'yyyy-MM')
# MAGIC ORDER BY Delivery_Month

# COMMAND ----------

# DBTITLE 1,Observation 3
# MAGIC %md
# MAGIC > **Observation:** `order_schedule_line` is the most detailed delivery commitment view:
# MAGIC > 22,212 schedule lines across order lines (avg 1.5 per order line) reflect split-delivery
# MAGIC > patterns. The confirmation rate per month shows how ATP-constrained months compare
# MAGIC > to open-stock months. Group by month and look for months with low confirmation rates
# MAGIC > — those are the periods where availability pressure is highest.
# MAGIC >
# MAGIC > **What comes next:** When the Customer (`account_id`), Plant (`plant_id`), and Product Catalog
# MAGIC > (`sku_id`) domains are built, these same queries can be enriched with customer names,
# MAGIC > plant locations, and SKU descriptions. See the [Known Limitations](../explanation/domain_narrative.md)
# MAGIC > section of the Domain Narrative for the full roadmap.
# MAGIC
# MAGIC **You have completed all three Sales Order tutorials.** Return to the
# MAGIC [Sales Order Model Guide](/editor/notebooks/2237626864845444) or open the
# MAGIC [Sales Order Analytics Genie Space](/genie/rooms/01f1a7a4c7a513e8ba12be272cde5a82)
# MAGIC to ask free-form business questions.