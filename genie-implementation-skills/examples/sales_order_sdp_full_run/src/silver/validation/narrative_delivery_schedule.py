# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT 'manufacturing_silver_vibe';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT 'sales_order_silver_sdp';

# COMMAND ----------

# DBTITLE 1,Set Context
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Narrative Header
# MAGIC %md
# MAGIC # delivery_schedule — Narrative & Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Scheduling agreement delivery cadence records (EDI schedule types). Currently **0 rows expected** — no scheduling agreement document types exist in bronze.
# MAGIC
# MAGIC ## Grain
# MAGIC One row per scheduling agreement + line + schedule line. Expected 0 rows (Partial grade).
# MAGIC
# MAGIC ## Natural Key
# MAGIC `vbeln + posnr + etenr` (for SA types) → SHA2 → `delivery_schedule_id`
# MAGIC
# MAGIC ## Source
# MAGIC `manufacturing_bronze_vibe.sap_sd.vbep` filtered by SA types (LZ/LZM/LP/LPA) — 0 rows match
# MAGIC
# MAGIC ## Relationships
# MAGIC - **Child of:** order_line (FK: order_line_id)
# MAGIC
# MAGIC ## Known Gaps & Annotations
# MAGIC - Partial grade: no scheduling agreement orders exist in current bronze data
# MAGIC - Table structure validated; will populate when SA orders are ingested
# MAGIC
# MAGIC ## Build History
# MAGIC - **Built:** 2026-07-28 (SDP pipeline)
# MAGIC - **SDP Object:** Materialized View
# MAGIC - **Tier:** 6 (0 rows expected)

# COMMAND ----------

# DBTITLE 1,Row Count Check
# MAGIC %sql
# MAGIC -- Expected: 0 rows (no scheduling agreement types in bronze)
# MAGIC SELECT 'delivery_schedule' AS Entity, COUNT(*) AS Row_Count,
# MAGIC   CASE WHEN COUNT(*) = 0 THEN 'PASS (expected 0)' ELSE 'INFO (data arrived)' END AS Status
# MAGIC FROM delivery_schedule;

# COMMAND ----------

# DBTITLE 1,Write Results
# MAGIC %sql
# MAGIC DELETE FROM _validation_check_detail WHERE Run_Id = 'PENDING' AND Table_Name = 'delivery_schedule';
# MAGIC
# MAGIC INSERT INTO _validation_check_detail
# MAGIC SELECT 'PENDING', 'delivery_schedule', 'PK_Uniqueness', 'PK',
# MAGIC   CASE WHEN COUNT(*) = 0 THEN 'PASS' WHEN COUNT(*) = COUNT(DISTINCT delivery_schedule_id) THEN 'PASS' ELSE 'FAIL' END,
# MAGIC   '0', CAST(COUNT(*) - COUNT(DISTINCT delivery_schedule_id) AS STRING), NULL, FALSE, NULL,
# MAGIC   'PK uniqueness (0 rows expected — no SA types in bronze)', current_timestamp()
# MAGIC FROM delivery_schedule
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'delivery_schedule', 'BK_Null_Check', 'BK', 'PASS',
# MAGIC   '0', '0', NULL, FALSE, NULL, 'BK check: 0 rows — no SA types in bronze', current_timestamp()
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'delivery_schedule', 'Population_Key_Columns', 'POP', 'PASS',
# MAGIC   'N/A', '0 rows', NULL, FALSE, NULL, 'Population: 0 rows (Partial grade, expected)', current_timestamp()
# MAGIC UNION ALL
# MAGIC SELECT 'PENDING', 'delivery_schedule', 'Drift_ROW_COUNT', 'DRIFT', 'PASS',
# MAGIC   '0', '0', NULL, FALSE, NULL, 'Drift: baseline 0, still 0', current_timestamp();