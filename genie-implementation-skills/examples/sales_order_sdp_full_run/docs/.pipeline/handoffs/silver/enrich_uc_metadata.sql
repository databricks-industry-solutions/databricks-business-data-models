-- enrich_uc_metadata.sql — Sales Order SDP (Hybrid) — SILVER LAYER
-- Generated: 2026-08-09
--
-- This script is the idempotent catch-up enrichment for UC metadata.
-- The pipeline SQL files (src/silver/pipeline/*.sql) define inline COMMENTs on
-- every column and table — those are the source of truth. When the pipeline
-- runs, COMMENTs are applied atomically with schema creation.
--
-- AUDIT RESULT (silver): 0 gaps found.
--   Silver: 282/282 columns have COMMENTs (17 tables); all tables have table-level COMMENTs.
--
-- No ALTER statements required for comments. This file exists as the audit record
-- and will be updated if future columns are added without inline COMMENTs.
-- (The gold-layer enrichment lives in ../gold/enrich_uc_metadata.sql.)

-- Tag enrichment (entity_type + tier)
-- NOTE: The 'domain' tag was SKIPPED — governed tag vocabulary on this workspace
-- does not include 'sales_order' as an allowed value. Only entity_type and tier
-- are applied (always safe).

-- === SILVER LAYER: manufacturing_silver_vibe.sales_order_silver_sdp ===

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.sales_area
  SET TAGS ('entity_type' = 'REF', 'tier' = '0');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.order_reason
  SET TAGS ('entity_type' = 'REF', 'tier' = '0');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.channel_config
  SET TAGS ('entity_type' = 'REF', 'tier' = '1');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract
  SET TAGS ('entity_type' = 'MASTER', 'tier' = '1');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract_line
  SET TAGS ('entity_type' = 'MASTER', 'tier' = '2');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.quotation
  SET TAGS ('entity_type' = 'TXN', 'tier' = '2');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.`order`
  SET TAGS ('entity_type' = 'TXN', 'tier' = '3');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.quotation_line
  SET TAGS ('entity_type' = 'TXN', 'tier' = '3');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.order_line
  SET TAGS ('entity_type' = 'TXN', 'tier' = '4');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.order_partner
  SET TAGS ('entity_type' = 'TXN', 'tier' = '4');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.order_schedule_line
  SET TAGS ('entity_type' = 'TXN', 'tier' = '5');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.delivery_schedule
  SET TAGS ('entity_type' = 'MASTER', 'tier' = '6');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.edi_order_message
  SET TAGS ('entity_type' = 'TXN', 'tier' = '6');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.order_credit_check
  SET TAGS ('entity_type' = 'TXN', 'tier' = '6');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.return_order
  SET TAGS ('entity_type' = 'TXN', 'tier' = '6');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.otd_record
  SET TAGS ('entity_type' = 'TXN', 'tier' = '6');

ALTER TABLE manufacturing_silver_vibe.sales_order_silver_sdp.return_order_line
  SET TAGS ('entity_type' = 'TXN', 'tier' = '7');
