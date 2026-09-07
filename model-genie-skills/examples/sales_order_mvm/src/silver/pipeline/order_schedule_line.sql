CREATE OR REFRESH MATERIALIZED VIEW order_schedule_line (
  order_schedule_line_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|posnr|etenr)',
  order_line_id BIGINT COMMENT 'FK to order_line via vbeln|posnr JOIN',
  scheduled_delivery_date DATE COMMENT 'Scheduled delivery date',
  goods_issue_date DATE COMMENT 'Planned or actual date on which goods are issued from the warehouse/shipping point for this schedule line. Triggers inventory reduction and initiates the billing process in SAP SD.',
  confirmed_quantity DECIMAL(18,4) COMMENT 'Quantity confirmed for delivery on this schedule line after Available-to-Promise (ATP) or Capable-to-Promise (CTP) check. Represents the committed delivery quantity for the specific delivery date.',
  ordered_quantity DECIMAL(18,4) COMMENT 'Original quantity requested by the customer on this schedule line before ATP/CTP confirmation. May differ from confirmed_quantity when partial availability exists.',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|posnr|etenr); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_schedule_line_id)
COMMENT 'Delivery schedule line within a sales order line item representing the confirmed delivery split across multiple dates and quantities. Captures schedule line number, confirmed quantity, confirmed deliv. Grain: order_schedule_line_id (SHA2 of vbeln|posnr|etenr). Source: sap_sd_mvm.vbep.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.posnr AS STRING), '~'), COALESCE(CAST(s.etenr AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS order_schedule_line_id,
  ol.order_line_id AS order_line_id,
  TRY_TO_DATE(s.edatu, 'yyyyMMdd') AS scheduled_delivery_date,
  TRY_TO_DATE(s.wadat, 'yyyyMMdd') AS goods_issue_date,
  TRY_CAST(s.bmeng AS DECIMAL(18,4)) AS confirmed_quantity,
  TRY_CAST(s.wmeng AS DECIMAL(18,4)) AS ordered_quantity,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SAP_SD' AS source_system,
  CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL OR s.etenr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr, s.etenr) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, posnr, etenr ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.vbep
) s
LEFT JOIN (
  SELECT order_line_id, source_system_line_key,
         ROW_NUMBER() OVER (PARTITION BY source_system_line_key ORDER BY order_line_id DESC) AS _fk_rn
  FROM order_line
) ol ON ol.source_system_line_key = CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr) END AND ol._fk_rn = 1
WHERE s._rn = 1