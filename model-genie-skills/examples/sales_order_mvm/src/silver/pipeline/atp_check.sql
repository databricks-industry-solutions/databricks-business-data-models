CREATE OR REFRESH MATERIALIZED VIEW atp_check (
  atp_check_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|posnr|check_number)',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  order_line_id BIGINT COMMENT 'FK to order_line via vbeln|posnr JOIN',
  check_status STRING COMMENT 'Overall result status of the ATP/CTP check indicating whether the requested quantity was fully confirmed, partially confirmed, not confirmed, placed on backorder, or encountered an error.. Valid value',
  requested_quantity DECIMAL(18,4) COMMENT 'The quantity of the material requested by the customer on the sales order line item, as submitted to the ATP/CTP check engine.',
  confirmed_quantity DECIMAL(18,4) COMMENT 'The quantity confirmed as available by the ATP/CTP check engine. May be less than requested quantity in partial confirmation scenarios.',
  earliest_confirmation_date DATE COMMENT 'The earliest date on which the confirmed quantity can be made available, as determined by the ATP/CTP check engine. Key output for order promising and delivery scheduling.',
  check_timestamp TIMESTAMP COMMENT 'ATP check timestamp (check_timestamp, yyyy-MM-dd format)',
  check_type STRING COMMENT 'Discriminator indicating the type of availability check performed: ATP (Available-to-Promise based on stock and planned receipts), CTP (Capable-to-Promise including production capacity), Rule-Based AT',
  source_system STRING COMMENT 'Originating system identifier (from source)',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|posnr|check_number); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (atp_check_id)
COMMENT 'Available-to-Promise (ATP) and Capable-to-Promise (CTP) check result record capturing the outcome of each availability check performed during order entry or order change. Captures check type (ATP, CTP. Grain: atp_check_id (SHA2 of vbeln|posnr|check_number). Source: sap_sd_mvm.atp_log.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.posnr AS STRING), '~'), COALESCE(CAST(s.check_number AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS atp_check_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  ol.order_line_id AS order_line_id,
  s.check_status AS check_status,
  TRY_CAST(s.requested_quantity AS DECIMAL(18,4)) AS requested_quantity,
  TRY_CAST(s.confirmed_quantity AS DECIMAL(18,4)) AS confirmed_quantity,
  TRY_TO_DATE(s.earliest_confirmation_date, 'yyyyMMdd') AS earliest_confirmation_date,
  CAST(TRY_TO_DATE(s.check_timestamp, 'yyyy-MM-dd') AS TIMESTAMP) AS check_timestamp,
  s.check_type AS check_type,
  s.source_system AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL OR s.check_number IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr, s.check_number) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, posnr, check_number ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.atp_log
) s
LEFT JOIN (
  SELECT order_line_id, source_system_line_key,
         ROW_NUMBER() OVER (PARTITION BY source_system_line_key ORDER BY order_line_id DESC) AS _fk_rn
  FROM order_line
) ol ON ol.source_system_line_key = CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr) END AND ol._fk_rn = 1
WHERE s._rn = 1