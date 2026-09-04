-- enrich_uc_metadata.sql — Sales Order SDP (Hybrid) — GOLD LAYER
-- Generated: 2026-08-09
--
-- This script is the idempotent catch-up enrichment for UC metadata.
-- The pipeline SQL files (src/gold/pipeline/*.sql) define inline COMMENTs on
-- every column and table — those are the source of truth. When the pipeline
-- runs, COMMENTs are applied atomically with schema creation.
--
-- AUDIT RESULT (gold): 0 gaps found.
--   Gold: 149/149 columns have COMMENTs (13 tables); all tables have table-level COMMENTs.
--
-- No ALTER statements required for comments. This file exists as the audit record
-- and will be updated if future columns are added without inline COMMENTs.
-- (The silver-layer enrichment lives in ../silver/enrich_uc_metadata.sql.)

-- Tag enrichment (entity_type + tier)
-- NOTE: The 'domain' tag was SKIPPED — governed tag vocabulary on this workspace
-- does not include 'sales_order' as an allowed value. Only entity_type and tier
-- are applied (always safe).

-- === GOLD LAYER: manufacturing_silver_vibe.sales_order_gold_sdp ===

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_date
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G0');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_sales_area
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G0');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_channel
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G0');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_order_reason
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G0');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_customer
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G1');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_material
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G1');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.dim_sales_contract
  SET TAGS ('entity_type' = 'DIM', 'tier' = 'G1');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.bridge_order_partner
  SET TAGS ('entity_type' = 'BRIDGE', 'tier' = 'G1');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line
  SET TAGS ('entity_type' = 'FACT', 'tier' = 'G2');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.fact_otd
  SET TAGS ('entity_type' = 'FACT', 'tier' = 'G2');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.fact_quotation_line
  SET TAGS ('entity_type' = 'FACT', 'tier' = 'G2');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.fact_return_line
  SET TAGS ('entity_type' = 'FACT', 'tier' = 'G2');

ALTER TABLE manufacturing_silver_vibe.sales_order_gold_sdp.fact_credit_check
  SET TAGS ('entity_type' = 'FACT', 'tier' = 'G2');
