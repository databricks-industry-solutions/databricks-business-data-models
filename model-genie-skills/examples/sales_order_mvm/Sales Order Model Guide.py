# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT 'sales_order';
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Welcome & Orientation
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-09-03 (rev: initial) -->
# MAGIC # Sales Order — Model Guide
# MAGIC
# MAGIC **What is this?** The governed Silver 3NF model for Meridian Manufacturing's end-to-end sales
# MAGIC order lifecycle: contracts, quotations, orders, deliveries, and returns. Use this notebook as
# MAGIC your front door to the domain — run it for live reference data; browse it for orientation.
# MAGIC
# MAGIC > **Scope note:** `conventions.yml` declares `output_model: hybrid`. The dimensional gold star
# MAGIC > layer is **deferred (Mode B, not yet built)**. This guide covers the silver 3NF schema only.
# MAGIC
# MAGIC **Schema:** `manufacturing_silver_vibe.sales_order`  
# MAGIC **Entities:** 17 tables (5 reference, 12 transactional)  
# MAGIC **Total rows:** ~132,275  
# MAGIC **Status:** DEVELOPMENT  
# MAGIC **Sources:** SAP SD (dominant), Salesforce CRM (quotations), Returns Portal (RMAs)
# MAGIC
# MAGIC ## Quick Navigation
# MAGIC
# MAGIC | What you need | Where to go |
# MAGIC |---|---|
# MAGIC | Understand the model (why, architecture, decisions) | [Domain Narrative](docs/explanation/domain_narrative.md).... [in browser link](https://fevm-serverless-ss-dev.cloud.databricks.com/editor/files/2237626864845442?o=7474660174009075) |
# MAGIC | Business terms / vocabulary | Glossary (Cell 9 below) |
# MAGIC | What questions can this domain answer? | Capability Index (Cell 10 below) |
# MAGIC | Ask a business question interactively | [Sales Order Analytics](/genie/rooms/01f1a7a4c7a513e8ba12be272cde5a82) (Genie space UUID: `01f1a7a4c7a513e8ba12be272cde5a82`) |
# MAGIC | Learn progressively (tutorials) | `docs/tutorials/` |
# MAGIC | Check data quality / grades | Sales Order Validation Quality dashboard |
# MAGIC | Validate data (regression tests) | `src/silver/validation/` |
# MAGIC | Contribute (add tables, fix issues) | [Contributor Guide](docs/contributor/maintaining-this-domain.md) ... [in browser link](https://fevm-serverless-ss-dev.cloud.databricks.com/editor/files/2237626864845452?o=7474660174009075)|
# MAGIC
# MAGIC ## Architecture (summary)
# MAGIC
# MAGIC ```
# MAGIC SAP SD (sap_sd_mvm)         ─────►  manufacturing_silver_vibe.sales_order
# MAGIC Salesforce CRM              ─────►  17 Materialized Views (full recompute, Type 1)
# MAGIC Returns Portal              ─────►  [gold star schema — deferred, not yet built]
# MAGIC ```
# MAGIC
# MAGIC ## Document Hierarchy
# MAGIC
# MAGIC ```
# MAGIC Sales Contract (120)                    Quotation (4,000)
# MAGIC   └─ Sales Contract Line (373)            └─ Quotation Line (11,982)
# MAGIC
# MAGIC Order (5,000) ────────────────────────────────────────────
# MAGIC   ├─ Order Partner (15,000)   Credit Check (3,104)     ATP Check (12,000)
# MAGIC   ├─ Order Line (14,762)      Order Status Event (18,512)
# MAGIC   │    ├─ Order Schedule Line (22,212)
# MAGIC   │    └─ Order Configuration (2,025)
# MAGIC   ├─ Delivery (3,244)
# MAGIC   │    ├─ Delivery Line (9,605)
# MAGIC   │    └─ Delivery Schedule (800)
# MAGIC   └─ Return Order (227)
# MAGIC        └─ Return Order Line (329)
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Current Model Health
# MAGIC %sql
# MAGIC -- Current model health (from most recent validation run)
# MAGIC SELECT
# MAGIC   r.Overall_Grade        AS Model_Health,
# MAGIC   r.Run_Timestamp        AS Last_Validated,
# MAGIC   r.Entities_Grade_A     AS Grade_A_Count,
# MAGIC   r.Total_Entities,
# MAGIC   r.Drift_Alerts_Count   AS Active_Drift_Alerts,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, r.Run_Timestamp, current_timestamp()), 1) AS Hours_Since_Validation
# MAGIC FROM _validation_run r
# MAGIC ORDER BY r.Run_Timestamp DESC
# MAGIC LIMIT 1

# COMMAND ----------

# DBTITLE 1,Entity Overview (Grades & Row Counts)
# MAGIC %sql
# MAGIC -- All entities with current grades and row counts
# MAGIC SELECT
# MAGIC   t.Table_Name,
# MAGIC   t.Table_Type,
# MAGIC   t.Tier,
# MAGIC   t.Row_Count,
# MAGIC   t.Grade,
# MAGIC   t.Known_Gaps_Count,
# MAGIC   t.Fk_Orphan_Rate_Pct,
# MAGIC   t.Drift_Columns_Count
# MAGIC FROM _validation_table_result t
# MAGIC WHERE t.Run_Id = (
# MAGIC   SELECT Run_Id FROM _validation_run
# MAGIC   ORDER BY Run_Timestamp DESC LIMIT 1
# MAGIC )
# MAGIC ORDER BY t.Tier, t.Table_Name

# COMMAND ----------

# DBTITLE 1,Column Dictionary (Live UC Reference)
# MAGIC %sql
# MAGIC -- Complete column dictionary (live from UC metadata)
# MAGIC SELECT
# MAGIC   c.table_name       AS Table_Name,
# MAGIC   c.column_name      AS Column_Name,
# MAGIC   c.data_type        AS Data_Type,
# MAGIC   CASE WHEN c.is_nullable = 'NO' THEN '✗' ELSE '' END AS Required,
# MAGIC   c.comment          AS Description
# MAGIC FROM IDENTIFIER(:silver_catalog || '.information_schema.columns') c
# MAGIC WHERE c.table_schema = :silver_schema
# MAGIC   AND c.table_name NOT LIKE '!_%' ESCAPE '!'
# MAGIC   AND c.table_name NOT LIKE 'event_log_%'
# MAGIC ORDER BY
# MAGIC   c.table_name,
# MAGIC   c.ordinal_position

# COMMAND ----------

# DBTITLE 1,FK Relationship Map (Live UC Reference)
# MAGIC %sql
# MAGIC -- FK relationship map (live from UC metadata)
# MAGIC -- NOTE: This model is built as Materialized Views (SDP pipeline). UC does not
# MAGIC -- support FK constraints on MVs, so this query will return 0 rows. FK relationships
# MAGIC -- are documented in column COMMENTs (see Column Dictionary above) and in the
# MAGIC -- Entity Relationship Matrix in docs/explanation/domain_narrative.md.
# MAGIC SELECT
# MAGIC   tc.table_name       AS Child_Table,
# MAGIC   kcu.column_name     AS FK_Column,
# MAGIC   ccu.table_name      AS Parent_Table,
# MAGIC   ccu.column_name     AS Parent_Column
# MAGIC FROM IDENTIFIER(:silver_catalog || '.information_schema.table_constraints') tc
# MAGIC JOIN IDENTIFIER(:silver_catalog || '.information_schema.key_column_usage') kcu
# MAGIC   ON tc.constraint_name = kcu.constraint_name
# MAGIC   AND tc.table_schema = kcu.table_schema
# MAGIC JOIN IDENTIFIER(:silver_catalog || '.information_schema.constraint_column_usage') ccu
# MAGIC   ON tc.constraint_name = ccu.constraint_name
# MAGIC   AND tc.table_schema = ccu.table_schema
# MAGIC WHERE tc.table_schema = :silver_schema
# MAGIC   AND tc.constraint_type = 'FOREIGN KEY'
# MAGIC ORDER BY Child_Table, FK_Column

# COMMAND ----------

# DBTITLE 1,Table Statistics
# MAGIC %sql
# MAGIC -- Table listing (live from UC metadata)
# MAGIC SELECT
# MAGIC   table_name       AS Table_Name,
# MAGIC   table_type       AS UC_Type,
# MAGIC   comment          AS Table_Description
# MAGIC FROM IDENTIFIER(:silver_catalog || '.information_schema.tables')
# MAGIC WHERE table_schema = :silver_schema
# MAGIC   AND table_name NOT LIKE '!_%' ESCAPE '!'
# MAGIC   AND table_name NOT LIKE 'event_log_%'
# MAGIC ORDER BY table_name

# COMMAND ----------

# DBTITLE 1,Freshness & Coverage
# MAGIC %md
# MAGIC ### Freshness & Coverage
# MAGIC
# MAGIC All 17 entities are Materialized Views (full recompute on every pipeline refresh).
# MAGIC Row counts below are as-built from the build manifest (2026-09-03).
# MAGIC
# MAGIC | Table | Source Rows | Silver Rows | Coverage | Notes |
# MAGIC |---|---|---|---|---|
# MAGIC | sales_contract | 120 | 120 | 100% | Root entity |
# MAGIC | sales_contract_line | 373 | 373 | 100% | |
# MAGIC | quotation | 4,000 | 4,000 | 100% | Salesforce CRM |
# MAGIC | quotation_line | 11,982 | 11,982 | 100% | Salesforce CRM |
# MAGIC | order | 5,000 | 5,000 | 100% | Core entity |
# MAGIC | order_line | 14,762 | 14,762 | 100% | |
# MAGIC | order_partner | 15,000 | 15,000 | 100% | |
# MAGIC | order_schedule_line | 22,212 | 22,212 | 100% | |
# MAGIC | order_configuration | 2,025 | 2,025 | 100% | CPQ-configured lines only |
# MAGIC | delivery | 3,244 | 3,244 | 100% | ~65% of orders have a delivery |
# MAGIC | delivery_line | 9,605 | 9,605 | 100% | |
# MAGIC | delivery_schedule | 800 | 800 | 100% | |
# MAGIC | return_order | 227 | 227 | 100% | Returns Portal |
# MAGIC | return_order_line | 329 | 329 | 100% | Returns Portal |
# MAGIC | credit_check | 3,104 | 3,104 | 100% | ~62% of orders had credit checks |
# MAGIC | atp_check | 12,000 | 12,000 | 100% | |
# MAGIC | order_status_event | 18,512 | 18,512 | 100% | ~3.7 events per order |
# MAGIC
# MAGIC **Total: ~132,275 rows across all entities.**
# MAGIC
# MAGIC **Refresh schedule:** Full recompute on each pipeline trigger (no incremental merge).
# MAGIC Run the `sales_order_silver_pipeline` to refresh all 17 Materialized Views.

# COMMAND ----------

# DBTITLE 1,Quick-Start Queries
# MAGIC %md
# MAGIC ## Quick-Start Queries
# MAGIC
# MAGIC The 5 most common questions analysts ask of this model.
# MAGIC Copy and modify for your use case. All queries use the schema set by the widget header above.

# COMMAND ----------

# DBTITLE 1,QS1: Orders by Status
# MAGIC %sql
# MAGIC -- Quick-Start 1: Order portfolio by current status
# MAGIC SELECT
# MAGIC   overall_status                                         AS Status,
# MAGIC   COUNT(*)                                               AS Order_Count,
# MAGIC   ROUND(SUM(net_value), 0)                               AS Total_Net_Value,
# MAGIC   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)     AS Pct_Of_Orders
# MAGIC FROM `order`
# MAGIC WHERE overall_status IS NOT NULL
# MAGIC GROUP BY overall_status
# MAGIC ORDER BY Order_Count DESC

# COMMAND ----------

# DBTITLE 1,QS2: Monthly Order Volume Trend
# MAGIC %sql
# MAGIC -- Quick-Start 2: Monthly order volume and revenue trend
# MAGIC SELECT
# MAGIC   DATE_FORMAT(order_date, 'yyyy-MM')   AS Order_Month,
# MAGIC   COUNT(*)                             AS Orders,
# MAGIC   ROUND(SUM(net_value), 0)             AS Total_Net_Value,
# MAGIC   ROUND(AVG(net_value), 0)             AS Avg_Order_Value
# MAGIC FROM `order`
# MAGIC WHERE order_date IS NOT NULL
# MAGIC GROUP BY DATE_FORMAT(order_date, 'yyyy-MM')
# MAGIC ORDER BY Order_Month

# COMMAND ----------

# DBTITLE 1,QS3: Delivery On-Time Performance
# MAGIC %sql
# MAGIC -- Quick-Start 3: Delivery on-time performance
# MAGIC -- Positive = late; negative = early; zero = on-time
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) < 0  THEN 'Early'
# MAGIC     WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) = 0  THEN 'On Time'
# MAGIC     WHEN DATEDIFF(actual_goods_issue_date, planned_delivery_date) <= 3 THEN 'Slightly Late (1-3 days)'
# MAGIC     ELSE 'Late (4+ days)'
# MAGIC   END                                                           AS Delivery_Status,
# MAGIC   COUNT(*)                                                      AS Delivery_Count,
# MAGIC   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS Pct
# MAGIC FROM delivery
# MAGIC WHERE actual_goods_issue_date IS NOT NULL
# MAGIC   AND planned_delivery_date IS NOT NULL
# MAGIC GROUP BY 1
# MAGIC ORDER BY Delivery_Count DESC

# COMMAND ----------

# DBTITLE 1,QS4: Order Fulfillment Coverage
# MAGIC %sql
# MAGIC -- Quick-Start 4: What share of orders have at least one delivery created?
# MAGIC SELECT
# MAGIC   CASE WHEN d.order_id IS NOT NULL THEN 'Has Delivery' ELSE 'No Delivery Yet' END AS Fulfillment_Status,
# MAGIC   COUNT(DISTINCT o.order_id)                                                        AS Order_Count,
# MAGIC   ROUND(100.0 * COUNT(DISTINCT o.order_id) / SUM(COUNT(DISTINCT o.order_id)) OVER (), 1) AS Pct
# MAGIC FROM `order` o
# MAGIC LEFT JOIN (SELECT DISTINCT order_id FROM delivery) d ON o.order_id = d.order_id
# MAGIC GROUP BY 1
# MAGIC ORDER BY Order_Count DESC

# COMMAND ----------

# DBTITLE 1,QS5: Order Return Rate
# MAGIC %sql
# MAGIC -- Quick-Start 5: Order-level return rate
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT o.order_id)                                                         AS Total_Orders,
# MAGIC   COUNT(DISTINCT r.original_order_id)                                                AS Orders_With_Returns,
# MAGIC   ROUND(
# MAGIC     100.0 * COUNT(DISTINCT r.original_order_id) / NULLIF(COUNT(DISTINCT o.order_id), 0)
# MAGIC   , 1)                                                                               AS Return_Rate_Pct
# MAGIC FROM `order` o
# MAGIC LEFT JOIN return_order r ON o.order_id = r.original_order_id  -- return_order.original_order_id is the FK to order

# COMMAND ----------

# DBTITLE 1,Known Limitations
# MAGIC %md
# MAGIC ## Known Limitations
# MAGIC
# MAGIC For full gap registry and resolution status, see the
# MAGIC [Sales Order Validation Quality dashboard](#dashboard-01f1a757c2cd1aad8f0fdd33227b71f8)
# MAGIC and [Domain Narrative](docs/explanation/domain_narrative.md).
# MAGIC
# MAGIC | Priority | Entity | Gap | Status |
# MAGIC |---|---|---|---|
# MAGIC | P2 | order, order_partner, quotation, credit_check | `account_id` = NULL — Customer domain not yet built | DEFERRED |
# MAGIC | P2 | order, order_line | `plant_id` = NULL — Plant/Facility domain not yet built | DEFERRED |
# MAGIC | P2 | order_line, quotation_line, delivery_line | `sku_id` = NULL — Product Catalog domain not yet built | DEFERRED |
# MAGIC | P2 | quotation | `price_list_id` = NULL — Pricing domain not yet built | DEFERRED |
# MAGIC | P3 | quotation | `sales_contract_id` = NULL — join to governing contract deferred | DEFERRED |
# MAGIC | P3 | N/A | `order_header_condition`, `order_line_condition` not modelled (pricing conditions) | DROPPED |
# MAGIC | P3 | order_line | `abgru`, `uepos`, `charg` dropped (NULL in bronze) | ACCEPTED |
# MAGIC | P3 | order_schedule_line | `lifsp` dropped (NULL in bronze) | ACCEPTED |

# COMMAND ----------

# DBTITLE 1,Glossary
# MAGIC %md
# MAGIC ## Glossary
# MAGIC
# MAGIC Business vocabulary an analyst uses that may differ from column names.
# MAGIC These same definitions seed the Genie space instructions.
# MAGIC
# MAGIC | Term | Means | In the model |
# MAGIC |---|---|---|
# MAGIC | Sales contract | Master commercial framework agreement; customers place release orders against it | `sales_contract`, `sales_contract_line` |
# MAGIC | Release order | A sales order placed against an existing sales contract commitment | `order` with `sales_contract_id` set |
# MAGIC | RMA | Return Merchandise Authorization — a formally approved product return | `return_order`, `return_order_line` |
# MAGIC | ATP | Available-to-Promise check — confirms whether material can be delivered on the requested date | `atp_check` |
# MAGIC | OTD | On-Time Delivery — actual goods issue date vs. planned delivery date | `delivery.actual_goods_issue_date` vs `planned_delivery_date` |
# MAGIC | Sold-to party | The customer entity that places the order | `order_partner WHERE partner_function_code = 'AG'` |
# MAGIC | Ship-to party | The address where goods are physically delivered | `order_partner WHERE partner_function_code = 'WE'` |
# MAGIC | Incoterms | International Commercial Terms defining risk/cost transfer in shipments | `order.incoterms_code` |
# MAGIC | Item category | SAP SD code controlling order line processing (TAN=standard, TAK=consignment, TANN=free) | `order_line.item_category_code` |
# MAGIC | vbeln | SAP sales document number — the natural key for orders, deliveries, contracts | `order_number`, `delivery_number`, `contract_number` |
# MAGIC | Distribution channel | Route to market (direct, distributor, retail, etc.) | `order.distribution_channel_code` |
# MAGIC | Credit control area | SAP organizational unit managing credit limits per customer group | `credit_check.credit_control_area` |

# COMMAND ----------

# DBTITLE 1,Capability Index
# MAGIC %md
# MAGIC ## What Questions Can This Domain Answer?
# MAGIC
# MAGIC | Theme | Example questions | Where to start |
# MAGIC |---|---|---|
# MAGIC | Order portfolio | How many orders? Volume by status, type, channel? | Quick-Start 1 / Genie |
# MAGIC | Order value & revenue | Revenue by month? Average order value? Payment terms mix? | Quick-Start 2 / Genie |
# MAGIC | Contract coverage | What % of orders are against contracts? Contract utilization rate? | Genie |
# MAGIC | Quotation conversion | How many quotations converted to orders? Conversion rate? | Genie |
# MAGIC | Delivery performance | OTD rate? Average delay days? Delivery coverage? | Quick-Start 3 / Tutorial 02 |
# MAGIC | Fulfillment gaps | What share of orders have a delivery created? | Quick-Start 4 / Tutorial 02 |
# MAGIC | Return rate & reasons | Return rate by order? Which product codes return most? | Quick-Start 5 / Genie |
# MAGIC | Credit management | Credit check pass rate? Blocked orders? Exposure before/after check? | Genie |
# MAGIC | ATP availability | Date slip by month? Lines with ATP pushout? | Tutorial 03 / Genie |
# MAGIC | Order lifecycle | Average order cycle time? Status transition patterns? | Tutorial 03 / Genie |
# MAGIC
# MAGIC **Not yet answerable** (see Known Limitations, Cell 8):
# MAGIC - Customer-level analysis (`account_id` = NULL — Customer domain not yet built)
# MAGIC - Plant/facility-level breakdown (`plant_id` = NULL)
# MAGIC - Product-level analysis (`sku_id` = NULL — Product Catalog not yet built)
# MAGIC - Pricing condition analysis (`order_header_condition` / `order_line_condition` not modelled)

# COMMAND ----------

# DBTITLE 1,Documentation Map
# MAGIC %md
# MAGIC ## Full Documentation Map
# MAGIC
# MAGIC | Category | Artifact | Location | What It Answers |
# MAGIC |---|---|---|---|
# MAGIC | Explanation | Domain Narrative | `docs/explanation/domain_narrative.md` | Why was this built? How do entities relate? |
# MAGIC | Reference | This notebook (Cells 4–6) | _(you’re here)_ | What columns, types, FKs exist? |
# MAGIC | Glossary | This notebook (Cell 9) | _(you’re here)_ | What does this business term mean? |
# MAGIC | Capability index | This notebook (Cell 10) | _(you’re here)_ | What questions can this domain answer? |
# MAGIC | How-to | Genie Space | [Sales Order Analytics](/genie/rooms/01f1a7a4c7a513e8ba12be272cde5a82) | How do I answer business question X? |
# MAGIC | Tutorials | Tutorial notebooks | `docs/tutorials/` | How do I learn this model from scratch? |
# MAGIC | Validation | Narrative notebooks | `src/silver/validation/narrative_{entity}` | Is the data quality good? |
# MAGIC | Quality | Dashboard | Sales Order Validation Quality (`01f1a757c2cd1aad8f0fdd33227b71f8`) | Health at a glance |
# MAGIC | UC Tag Enrichment | Tags script | `docs/.pipeline/handoffs/silver/enrich_uc_metadata.sql` | How to apply domain/tier/source tags |
# MAGIC | Maintaining | Contributor Guide | `docs/contributor/maintaining-this-domain.md` | How to add/fix/re-sync THIS domain via the skills |
# MAGIC
# MAGIC **No ERD is generated here.** The live FK map (Cell 5) and the Entity Relationship Matrix
# MAGIC in the Domain Narrative are the interim relationship views. Comprehensive ERDs come from
# MAGIC the Databricks App.