-- =============================================================================
-- enrich_uc_metadata.sql — Sales Order Domain (Silver)
-- Phase 3: UC Tag Enrichment (SDP mode — tags only)
--
-- SDP EXCEPTION: all table COMMENTs and column COMMENTs are declared inline in
-- src/silver/pipeline/{entity}.sql and applied atomically by the pipeline run.
-- No live ALTER TABLE SET COMMENT needed. This script contains SET TAGS only.
--
-- Run idempotent: safe to re-run. Tags are replaced on each execution.
--
-- NOTE: Before running, confirm the tag vocabulary is registered in UC. If your
-- workspace restricts tag keys/values (governed tags), register the keys
-- 'domain', 'entity_type', 'tier', 'source_system' first, or substitute with
-- the governed equivalents. Treat a rejection as a documented skip.
--
-- Generated: 2026-09-03 | Synced-against: progress.md @ 2026-09-03 (rev: initial)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Tier 0: Root reference entities
-- ---------------------------------------------------------------------------

ALTER TABLE manufacturing_silver_vibe.sales_order.sales_contract
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'reference', 'tier' = '0', 'source_system' = 'sap_sd');

-- ---------------------------------------------------------------------------
-- Tier 1: First-level reference entities
-- ---------------------------------------------------------------------------

ALTER TABLE manufacturing_silver_vibe.sales_order.sales_contract_line
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'reference', 'tier' = '1', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.quotation
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'reference', 'tier' = '1', 'source_system' = 'salesforce_crm');

-- ---------------------------------------------------------------------------
-- Tier 2: Order header
-- ---------------------------------------------------------------------------

ALTER TABLE manufacturing_silver_vibe.sales_order.`order`
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '2', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.quotation_line
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'reference', 'tier' = '2', 'source_system' = 'salesforce_crm');

-- ---------------------------------------------------------------------------
-- Tier 3: Order detail and first-level events
-- ---------------------------------------------------------------------------

ALTER TABLE manufacturing_silver_vibe.sales_order.order_line
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '3', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.order_partner
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'reference', 'tier' = '3', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.return_order
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '3', 'source_system' = 'returns_portal');

ALTER TABLE manufacturing_silver_vibe.sales_order.delivery
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '3', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.credit_check
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '3', 'source_system' = 'sap_sd');

-- ---------------------------------------------------------------------------
-- Tier 4: Second-level detail and sub-line entities
-- ---------------------------------------------------------------------------

ALTER TABLE manufacturing_silver_vibe.sales_order.order_schedule_line
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '4', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.order_configuration
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '4', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.return_order_line
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '4', 'source_system' = 'returns_portal');

ALTER TABLE manufacturing_silver_vibe.sales_order.delivery_line
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '4', 'source_system' = 'sap_sd');

-- ---------------------------------------------------------------------------
-- Tier 5: Event logs and scheduling
-- ---------------------------------------------------------------------------

ALTER TABLE manufacturing_silver_vibe.sales_order.atp_check
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '5', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.order_status_event
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '5', 'source_system' = 'sap_sd');

ALTER TABLE manufacturing_silver_vibe.sales_order.delivery_schedule
  SET TAGS ('domain' = 'sales_order', 'entity_type' = 'transactional', 'tier' = '5', 'source_system' = 'sap_sd');

-- =============================================================================
-- Phase 3 Audit Notes
-- =============================================================================
-- All 17 SDP pipeline files carry inline COMMENTs on every table and business
-- column. The following minor issues were identified and repaired in the source
-- files during this run:
--
--   order.sql:
--     - document_date: was empty string '' — replaced with meaningful description
--     - net_value: truncated comment — completed
--     - incoterms_code: truncated comment — completed
--
--   order_line.sql:
--     - net_value: truncated comment — completed
--     - item_category_code: truncated comment — completed
--
-- FK registration: SKIPPED — Materialized Views do not support FK constraints.
-- FK relationships are documented in column COMMENTs and enforced by inline
-- EXPECT constraints.
-- =============================================================================
