CREATE OR REFRESH MATERIALIZED VIEW order_partner (
  order_partner_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|parvw)',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  partner_function_code STRING COMMENT 'SAP SD partner function code identifying the role of the business partner on the order. Standard codes include SP (Sold-To Party), SH (Ship-To Party), BP (Bill-To Party), PY (Payer), SR (Sales Represe',
  partner_customer_number STRING COMMENT 'Partner customer number',
  partner_name STRING COMMENT 'Full legal or trading name of the business partner at the time the order was created. Snapshot value captured to preserve the name as it appeared on the order, independent of subsequent master data ch',
  country_code STRING COMMENT 'Country code',
  city STRING COMMENT 'City',
  postal_code STRING COMMENT 'Postal code',
  address_number STRING COMMENT 'Address number',
  function_description STRING COMMENT 'Function description',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|parvw); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_partner_id)
COMMENT 'Partner function assignment record for a sales order capturing all business partners involved in the order transaction. Captures partner function code (sold-to, ship-to, bill-to, payer, sales rep, for. Grain: order_partner_id (SHA2 of vbeln|parvw). Source: sap_sd_mvm.vbpa.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.parvw AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS order_partner_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  s.parvw AS partner_function_code,
  s.kunnr AS partner_customer_number,
  s.name1 AS partner_name,
  s.land1 AS country_code,
  s.ort01 AS city,
  s.pstlz AS postal_code,
  s.adrnr AS address_number,
  s.func_desc AS function_description,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SAP_SD' AS source_system,
  CASE WHEN s.vbeln IS NULL OR s.parvw IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.parvw) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, parvw ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.vbpa
) s
WHERE s._rn = 1