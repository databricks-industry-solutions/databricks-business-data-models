# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema DEFAULT 'sales_order_silver_sdp';
# MAGIC CREATE WIDGET TEXT gold_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT gold_schema DEFAULT 'sales_order_gold_sdp';
# MAGIC
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Welcome & Orientation
# MAGIC %md
# MAGIC <!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->
# MAGIC # Sales Order — Model Guide
# MAGIC
# MAGIC **What is this?** A governed hybrid data model (normalized 3NF silver + dimensional star gold) for B2B sales order management in manufacturing.
# MAGIC
# MAGIC **Silver Schema:** `manufacturing_silver_vibe.sales_order_silver_sdp`  
# MAGIC **Gold Schema:** `manufacturing_silver_vibe.sales_order_gold_sdp`  
# MAGIC **Entities:** 30 tables (17 silver + 13 gold: 7 dim + 1 bridge + 5 fact)  
# MAGIC **Total rows:** ~158,648 (100,294 silver + 58,354 gold)  
# MAGIC **Status:** DEVELOPMENT  
# MAGIC **Pipeline:** Lakeflow SDP (`1b57fa65-f8d3-434b-b5cd-9beeba43e872`)
# MAGIC
# MAGIC ## Quick Navigation
# MAGIC
# MAGIC | What you need | Where to go |
# MAGIC |---|---|
# MAGIC | Understand the model (why, architecture, decisions) | [Domain Narrative](docs/domain_narrative.md) |
# MAGIC | Business terms / vocabulary | Glossary (Cell 9 below) |
# MAGIC | What questions can this domain answer? | Capability Index (Cell 10 below) |
# MAGIC | Ask a business question interactively | Genie Space |
# MAGIC | Learn progressively (tutorials) | `docs/tutorials/` |
# MAGIC | Check data quality / grades | Validation Dashboard |
# MAGIC | Validate data (regression tests) | `src/silver/validation/` + `src/gold/validation/` |
# MAGIC | Contribute (add tables, fix issues) | [Contributor Guide](docs/contributor/maintaining-this-domain.md) |
# MAGIC
# MAGIC ## Architecture
# MAGIC
# MAGIC ```
# MAGIC Bronze (4 systems)  →  Silver (17 entities, 3NF)  →  Gold (13 entities, star schema)
# MAGIC   sap_sd                 sales_area, order,             dim_customer, dim_material,
# MAGIC   salesforce_crm         order_line, quotation,         fact_sales_order_line,
# MAGIC   edi_gateway            return_order, otd_record...    fact_otd, fact_credit_check...
# MAGIC   returns_portal
# MAGIC ```
# MAGIC
# MAGIC ## Document Hierarchy (Silver)
# MAGIC
# MAGIC ```
# MAGIC Sales Area (4) → Order (5,000) → Order Line (14,762) → Schedule Line (22,212)
# MAGIC                                 → Order Partner (15,000)
# MAGIC                                 → Credit Check (3,104)
# MAGIC                                 → Return Order (227) → Return Line (329)
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Current Health — Silver
# MAGIC %sql
# MAGIC -- Current silver model health (from most recent validation run)
# MAGIC SELECT
# MAGIC   r.Overall_Grade AS Model_Health,
# MAGIC   r.Run_Timestamp AS Last_Validated,
# MAGIC   r.Entities_Grade_A AS Grade_A_Count,
# MAGIC   r.Total_Entities,
# MAGIC   r.Drift_Alerts_Count AS Active_Drift_Alerts,
# MAGIC   ROUND(TIMESTAMPDIFF(HOUR, r.Run_Timestamp, current_timestamp()), 1) AS Hours_Since_Validation
# MAGIC FROM _validation_run r
# MAGIC ORDER BY r.Run_Timestamp DESC
# MAGIC LIMIT 1

# COMMAND ----------

# DBTITLE 1,Entity Overview — Silver
# MAGIC %sql
# MAGIC -- Silver entities with current grades and row counts
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

# DBTITLE 1,Entity Overview — Gold
# MAGIC %sql
# MAGIC -- Gold entities with current grades and row counts
# MAGIC SELECT
# MAGIC   t.Table_Name,
# MAGIC   t.Table_Type,
# MAGIC   t.Tier,
# MAGIC   t.Row_Count,
# MAGIC   t.Grade,
# MAGIC   t.Known_Gaps_Count,
# MAGIC   t.Fk_Orphan_Rate_Pct,
# MAGIC   t.Drift_Columns_Count
# MAGIC FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '._validation_table_result') t
# MAGIC WHERE t.Run_Id = (
# MAGIC   SELECT Run_Id FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '._validation_run')
# MAGIC   ORDER BY Run_Timestamp DESC LIMIT 1
# MAGIC )
# MAGIC ORDER BY t.Tier, t.Table_Name

# COMMAND ----------

# DBTITLE 1,Column Dictionary — Silver
# MAGIC %sql
# MAGIC -- Complete silver column dictionary (live from UC metadata)
# MAGIC SELECT
# MAGIC   c.table_name AS Table_Name,
# MAGIC   c.column_name AS Column_Name,
# MAGIC   c.data_type AS Data_Type,
# MAGIC   CASE WHEN c.is_nullable = 'NO' THEN '✗' ELSE '' END AS Required,
# MAGIC   c.comment AS Description
# MAGIC FROM IDENTIFIER(:silver_catalog || '.information_schema.columns') c
# MAGIC WHERE c.table_schema = :silver_schema
# MAGIC   AND c.table_name NOT LIKE '\\_%'
# MAGIC   AND c.table_name NOT LIKE 'event_log%'
# MAGIC ORDER BY c.table_name, c.ordinal_position

# COMMAND ----------

# DBTITLE 1,Column Dictionary — Gold
# MAGIC %sql
# MAGIC -- Complete gold column dictionary (live from UC metadata)
# MAGIC SELECT
# MAGIC   c.table_name AS Table_Name,
# MAGIC   c.column_name AS Column_Name,
# MAGIC   c.data_type AS Data_Type,
# MAGIC   CASE WHEN c.is_nullable = 'NO' THEN '✗' ELSE '' END AS Required,
# MAGIC   c.comment AS Description
# MAGIC FROM IDENTIFIER(:gold_catalog || '.information_schema.columns') c
# MAGIC WHERE c.table_schema = :gold_schema
# MAGIC   AND c.table_name NOT LIKE '\\_%'
# MAGIC ORDER BY
# MAGIC   CASE
# MAGIC     WHEN c.table_name LIKE 'dim_%' THEN 0
# MAGIC     WHEN c.table_name LIKE 'bridge_%' THEN 1
# MAGIC     WHEN c.table_name LIKE 'fact_%' THEN 2
# MAGIC     ELSE 3
# MAGIC   END,
# MAGIC   c.table_name,
# MAGIC   c.ordinal_position

# COMMAND ----------

# DBTITLE 1,Table Statistics
# MAGIC %sql
# MAGIC -- Table row counts across both schemas (from validation metadata)
# MAGIC SELECT 'silver' AS Layer, Table_Name, Row_Count, Grade
# MAGIC FROM _validation_table_result
# MAGIC WHERE Run_Id = (SELECT Run_Id FROM _validation_run ORDER BY Run_Timestamp DESC LIMIT 1)
# MAGIC UNION ALL
# MAGIC SELECT 'gold' AS Layer, Table_Name, Row_Count, Grade
# MAGIC FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '._validation_table_result')
# MAGIC WHERE Run_Id = (SELECT Run_Id FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '._validation_run') ORDER BY Run_Timestamp DESC LIMIT 1)
# MAGIC ORDER BY Layer, Table_Name

# COMMAND ----------

# DBTITLE 1,Freshness & Coverage
# MAGIC %md
# MAGIC ### Freshness & Coverage
# MAGIC
# MAGIC | Layer | Table | Refreshes | Coverage |
# MAGIC |---|---|---|---|
# MAGIC | Silver | order | Pipeline-triggered (MV) | 5,000 of 5,000 source rows (100%) |
# MAGIC | Silver | order_line | Pipeline-triggered (MV) | 14,762 of 14,762 source rows (100%) |
# MAGIC | Silver | order_schedule_line | Pipeline-triggered (MV) | 22,212 of 22,212 source rows (100%) |
# MAGIC | Silver | edi_order_message | Streaming (watermark) | 956 messages (incremental) |
# MAGIC | Silver | order_credit_check | Streaming (watermark) | 3,104 checks (incremental) |
# MAGIC | Gold | fact_sales_order_line | Pipeline-triggered (MV) | 14,762 from silver order_line (100%) |
# MAGIC | Gold | fact_otd | Pipeline-triggered (MV) | 22,212 from silver schedule lines (100%) |
# MAGIC | Gold | fact_credit_check | Pipeline-triggered (MV) | 3,104 from silver credit checks (100%) |
# MAGIC
# MAGIC All MVs fully recompute on pipeline trigger. Streaming tables append incrementally.

# COMMAND ----------

# DBTITLE 1,Quick-Start Queries
# MAGIC %md
# MAGIC ## Quick-Start Queries
# MAGIC
# MAGIC These are the 5 most common questions analysts ask of this model. Copy and modify for your use case. All queries target the **gold** star schema.

# COMMAND ----------

# DBTITLE 1,Example 1: Revenue by Sales Area
# MAGIC %sql
# MAGIC -- Revenue by sales area (gold star schema)
# MAGIC SELECT
# MAGIC   sa.Sales_Organization,
# MAGIC   sa.Distribution_Channel,
# MAGIC   sa.Division,
# MAGIC   COUNT(*) AS Line_Count,
# MAGIC   SUM(f.Net_Value) AS Total_Revenue,
# MAGIC   ROUND(AVG(f.Net_Value), 2) AS Avg_Line_Value
# MAGIC FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '.fact_sales_order_line') f
# MAGIC JOIN IDENTIFIER(:gold_catalog || '.' || :gold_schema || '.dim_sales_area') sa
# MAGIC   ON f.Sales_Area_Key = sa.Sales_Area_Key
# MAGIC WHERE f.Sales_Area_Key IS NOT NULL
# MAGIC GROUP BY sa.Sales_Organization, sa.Distribution_Channel, sa.Division
# MAGIC ORDER BY Total_Revenue DESC

# COMMAND ----------

# DBTITLE 1,Example 2: OTD Performance
# MAGIC %sql
# MAGIC -- On-time delivery rate (gold fact_otd)
# MAGIC SELECT
# MAGIC   OTD_Status,
# MAGIC   COUNT(*) AS Schedule_Lines,
# MAGIC   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS Pct
# MAGIC FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '.fact_otd')
# MAGIC GROUP BY OTD_Status
# MAGIC ORDER BY OTD_Status

# COMMAND ----------

# DBTITLE 1,Example 3: Top Customers by Order Volume
# MAGIC %sql
# MAGIC -- Top 10 customers by order line count (gold)
# MAGIC SELECT
# MAGIC   c.Customer_Number,
# MAGIC   c.Customer_Name,
# MAGIC   COUNT(*) AS Order_Lines,
# MAGIC   SUM(f.Net_Value) AS Total_Revenue
# MAGIC FROM IDENTIFIER(:gold_catalog || '.' || :gold_schema || '.fact_sales_order_line') f
# MAGIC JOIN IDENTIFIER(:gold_catalog || '.' || :gold_schema || '.dim_customer') c
# MAGIC   ON f.Customer_Key = c.Customer_Key
# MAGIC WHERE f.Customer_Key IS NOT NULL
# MAGIC GROUP BY c.Customer_Number, c.Customer_Name
# MAGIC ORDER BY Total_Revenue DESC
# MAGIC LIMIT 10

# COMMAND ----------

# DBTITLE 1,Known Limitations
# MAGIC %md
# MAGIC ## Known Limitations
# MAGIC
# MAGIC | Priority | Entity | Gap | Status |
# MAGIC |---|---|---|---|
# MAGIC | P0 | fact_otd | Actual_Delivery_Date = NULL (proxy OTD only) | DEFERRED |
# MAGIC | P1 | fact_return_line | Order_Reason_Key = NULL (portal vocab gap) | ACCEPTED |
# MAGIC | P2 | fact_quotation_line | Customer_Key (cross-source: Account_Id vs Partner_Number) | ACCEPTED |
# MAGIC | P3 | dim_channel / dim_sales_contract | sales_area_id = NULL (source gap) | ACCEPTED |
# MAGIC
# MAGIC For full gap registry, see the validation dashboard.  
# MAGIC For explanation of why each gap exists, see [Domain Narrative](docs/domain_narrative.md).

# COMMAND ----------

# DBTITLE 1,Glossary
# MAGIC %md
# MAGIC ## Glossary
# MAGIC
# MAGIC Business vocabulary an analyst uses that differs from column names.
# MAGIC
# MAGIC | Term | Means | In the model |
# MAGIC |---|---|---|
# MAGIC | Sales Area | Org + Channel + Division combination (market segment) | `dim_sales_area` / `sales_area` |
# MAGIC | AG / Sold-To | The customer placing the order (SAP partner function AG) | `dim_customer` (gold) / `order_partner` WHERE Partner_Function = 'AG' |
# MAGIC | WE / Ship-To | Delivery destination (SAP partner function WE) | `bridge_order_partner.Ship_To_Number` |
# MAGIC | OTD | On-Time Delivery — currently a schedule-adherence proxy | `fact_otd.OTD_Status` (ON_TIME / LATE) |
# MAGIC | RMA | Return Merchandise Authorization | `return_order` / `fact_return_line` |
# MAGIC | Framework agreement | Long-term blanket purchase contract | `sales_contract` / `dim_sales_contract` |
# MAGIC | Schedule line | A committed delivery tranche within an order line | `order_schedule_line` |
# MAGIC | Quotation | Formal price/availability proposal (from CRM) | `quotation` / `fact_quotation_line` |
# MAGIC | Net Value | Line-item revenue (price × qty less discounts) | `fact_sales_order_line.Net_Value` |
# MAGIC | Credit utilization | Credit_Exposure / Credit_Limit × 100 | `fact_credit_check.Credit_Utilization_Pct` |

# COMMAND ----------

# DBTITLE 1,Capability Index
# MAGIC %md
# MAGIC ## What Questions Can This Domain Answer?
# MAGIC
# MAGIC | Theme | Example questions | Where to answer it |
# MAGIC |---|---|---|
# MAGIC | Revenue & volume | "Revenue by customer, material, sales area?" | Tutorial 01 / Genie |
# MAGIC | Order composition | "Lines per order? Distribution channels?" | Tutorial 01 / Genie |
# MAGIC | Delivery performance | "OTD rate? Which lines are late?" | Tutorial 02 / Genie |
# MAGIC | Credit risk | "Credit utilization trends? High-risk orders?" | Tutorial 02 / Genie |
# MAGIC | Returns & quality | "Return rate? Top return reasons?" | Tutorial 02 / Genie |
# MAGIC | Quote-to-order conversion | "Quote pipeline value? Conversion rate?" | Tutorial 03 / Genie |
# MAGIC | Order lifecycle flow | "Quotation → Order → Delivery → Return" | Tutorial 03 |
# MAGIC | Partner analysis | "Sold-To vs Ship-To? Multi-partner orders?" | Genie |
# MAGIC
# MAGIC Not yet answerable (see Known Limitations): true OTD with actual delivery dates (P0); return reason classification (P1); quote-to-customer linkage (P2).

# COMMAND ----------

# DBTITLE 1,Documentation Map
# MAGIC %md
# MAGIC ## Full Documentation Map
# MAGIC
# MAGIC | Category | Artifact | Location | What It Answers |
# MAGIC |---|---|---|---|
# MAGIC | Explanation | Domain Narrative | `docs/domain_narrative.md` | Why was this built? How do tables relate? |
# MAGIC | Reference | This notebook (Cells 5–7) | _(you're here)_ | What columns, types, FKs exist? |
# MAGIC | Glossary | This notebook (Cell 9) | _(you're here)_ | What does this business term mean? |
# MAGIC | Capability index | This notebook (Cell 10) | _(you're here)_ | What questions can this domain answer? |
# MAGIC | How-to | Genie Space | Sales Order Analytics | How do I answer business question X? |
# MAGIC | Tutorials | Getting Started | `docs/tutorials/` | How do I learn this model from scratch? |
# MAGIC | Validation | Narrative notebooks | `src/silver/validation/` + `src/gold/validation/` | Is the data quality good? |
# MAGIC | Maintaining | Contributor Guide | `docs/contributor/maintaining-this-domain.md` | How do I add/fix/re-sync THIS model? |
# MAGIC
# MAGIC **No ERD is generated here.** Relationship views: the validation FK checks + Domain Narrative cross-reference matrix.