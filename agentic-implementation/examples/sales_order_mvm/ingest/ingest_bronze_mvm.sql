-- Meridian sales_order (MVM) — bronze ingest for the 6 MVM-profile SAP SD sources.
-- Run AFTER examples/setup/ingest/ingest_bronze.sql (this only adds the new tables).
-- CTAS from read_files (inferSchema=false keeps raw string quirks); catalog meridian_bronze.
-- Prereq: landing volume holds the CSVs from `generate_bronze --profile mvm`:
--   /Volumes/meridian_bronze/default/_landing/sap_sd/<table>.csv

CREATE SCHEMA IF NOT EXISTS meridian_bronze.sap_sd;

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.status_log AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/status_log.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.atp_log AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/atp_log.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.sched_agreement AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/sched_agreement.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.cpq_config AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/cpq_config.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.likp AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/likp.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.lips AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/lips.csv',
  format => 'csv', header => true, inferSchema => false);
