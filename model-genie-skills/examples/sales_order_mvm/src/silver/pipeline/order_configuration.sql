CREATE OR REFRESH MATERIALIZED VIEW order_configuration (
  order_configuration_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|posnr|configuration_key)',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  order_line_id BIGINT COMMENT 'FK to order_line via vbeln|posnr JOIN',
  configuration_status STRING COMMENT 'Current lifecycle status of the configuration record. valid indicates a complete and validated configuration ready for production; incomplete indicates missing required characteristics; error indicate',
  bom_explosion_status STRING COMMENT 'Status of the Bill of Materials (BOM) explosion for this configuration. Indicates whether the variant configuration has been successfully resolved into a specific BOM for production planning and MRP..',
  configuration_source STRING COMMENT 'Origin method by which the configuration was created. cpq indicates a Configure-Price-Quote tool (e.g., Salesforce CPQ); manual indicates direct entry by a sales or application engineer; edi indicates',
  configuration_date DATE COMMENT 'Calendar date on which the product configuration was created or finalized by the sales or engineering team. Used for traceability and order promising timelines.',
  source_system STRING COMMENT 'Originating system identifier (from source)',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|posnr|configuration_key); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_configuration_id)
COMMENT 'Variant configuration record for a configurable product (e.g., automation system, drive, switchgear) ordered by a customer. Captures configuration key, configuration date, product model, characteristi. Grain: order_configuration_id (SHA2 of vbeln|posnr|configuration_key). Source: sap_sd_mvm.cpq_config.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.posnr AS STRING), '~'), COALESCE(CAST(s.configuration_key AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS order_configuration_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  ol.order_line_id AS order_line_id,
  s.configuration_status AS configuration_status,
  s.bom_explosion_status AS bom_explosion_status,
  s.configuration_source AS configuration_source,
  TRY_TO_DATE(s.configuration_date, 'yyyyMMdd') AS configuration_date,
  s.source_system AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL OR s.configuration_key IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr, s.configuration_key) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, posnr, configuration_key ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.cpq_config
) s
LEFT JOIN (
  SELECT order_line_id, source_system_line_key,
         ROW_NUMBER() OVER (PARTITION BY source_system_line_key ORDER BY order_line_id DESC) AS _fk_rn
  FROM order_line
) ol ON ol.source_system_line_key = CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr) END AND ol._fk_rn = 1
WHERE s._rn = 1