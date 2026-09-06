-- Meridian Fluid Controls bronze ingest — CTAS from read_files (inferSchema=false keeps raw string quirks)
-- Generated from examples/setup/data_generator/output/ tree; catalog meridian_bronze.
-- Prereq: the landing volume must exist and hold the CSVs:
--   /Volumes/meridian_bronze/default/_landing/<schema>/<table>.csv

CREATE SCHEMA IF NOT EXISTS meridian_bronze.edi_gateway;
CREATE SCHEMA IF NOT EXISTS meridian_bronze.fieldlink;
CREATE SCHEMA IF NOT EXISTS meridian_bronze.returns_portal;
CREATE SCHEMA IF NOT EXISTS meridian_bronze.salesforce_crm;
CREATE SCHEMA IF NOT EXISTS meridian_bronze.sap_sd;

CREATE OR REPLACE TABLE meridian_bronze.edi_gateway.edi_message_log AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/edi_gateway/edi_message_log.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.edi_gateway.trading_partner AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/edi_gateway/trading_partner.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.fieldlink.installed_asset AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/fieldlink/installed_asset.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.fieldlink.service_order AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/fieldlink/service_order.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.fieldlink.service_visit AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/fieldlink/service_visit.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.fieldlink.warranty_claim AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/fieldlink/warranty_claim.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.returns_portal.rma_line AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/returns_portal/rma_line.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.returns_portal.rma_reason_code AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/returns_portal/rma_reason_code.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.returns_portal.rma_request AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/returns_portal/rma_request.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.salesforce_crm.account AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/salesforce_crm/account.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.salesforce_crm.loss_reason_ref AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/salesforce_crm/loss_reason_ref.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.salesforce_crm.opportunity AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/salesforce_crm/opportunity.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.salesforce_crm.quote AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/salesforce_crm/quote.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.salesforce_crm.quote_line AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/salesforce_crm/quote_line.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.kna1 AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/kna1.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.knvv AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/knvv.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.makt AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/makt.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.mara AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/mara.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.t001w AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/t001w.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.t052u AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/t052u.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.tinct AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/tinct.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.tvakt AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/tvakt.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.tvaut AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/tvaut.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.tvta AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/tvta.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.vbak AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/vbak.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.vbap AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/vbap.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.vbep AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/vbep.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.vbpa AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/vbpa.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.veda AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/veda.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.veda_item AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/veda_item.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.zcredit_log AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/zcredit_log.csv',
  format => 'csv', header => true, inferSchema => false);

CREATE OR REPLACE TABLE meridian_bronze.sap_sd.zsd_channel_config AS
SELECT * FROM read_files(
  '/Volumes/meridian_bronze/default/_landing/sap_sd/zsd_channel_config.csv',
  format => 'csv', header => true, inferSchema => false);
