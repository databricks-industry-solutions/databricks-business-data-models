CREATE OR REFRESH MATERIALIZED VIEW delivery_line (
  delivery_line_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln_delivery|posnr)',
  delivery_id BIGINT COMMENT 'FK to delivery via SHA2(vbeln_delivery)',
  delivery_number STRING COMMENT 'Delivery number (vbeln_delivery)',
  line_number STRING COMMENT 'Delivery line number (posnr)',
  order_number STRING COMMENT 'Order number (vbeln_order)',
  order_line_number STRING COMMENT 'Order line number (posnr_order)',
  order_line_id BIGINT COMMENT 'FK to order_line via vbeln_order|posnr_order JOIN',
  delivered_quantity DECIMAL(18,4) COMMENT 'Delivered quantity (lfimg)',
  sku_code STRING COMMENT 'Material/SKU code (matnr)',
  sku_id BIGINT COMMENT 'FK to product_catalog.sku (deferred).',
  batch_number STRING COMMENT 'Batch/lot number (charg)',
  serial_number STRING COMMENT 'Serial number (serial)',
  source_system STRING COMMENT 'Originating system identifier (from source)',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln_delivery|posnr); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (delivery_line_id)
COMMENT 'Individual line item within an outbound delivery capturing product-level shipment detail. Captures delivered quantity, material/SKU reference, batch/lot, serial number, and links to originating order line.. Grain: delivery_line_id (SHA2 of vbeln_delivery|posnr). Source: sap_sd_mvm.lips. Net-new entity from discovery.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln_delivery AS STRING), '~'), COALESCE(CAST(s.posnr AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS delivery_line_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln_delivery AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS delivery_id,
  s.vbeln_delivery AS delivery_number,
  s.posnr AS line_number,
  s.vbeln_order AS order_number,
  s.posnr_order AS order_line_number,
  ol.order_line_id AS order_line_id,
  TRY_CAST(s.lfimg AS DECIMAL(18,4)) AS delivered_quantity,
  s.matnr AS sku_code,
  CAST(NULL AS BIGINT) AS sku_id,
  s.charg AS batch_number,
  s.serial AS serial_number,
  s.source_system AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  CASE WHEN s.vbeln_delivery IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln_delivery, s.posnr) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln_delivery, posnr ORDER BY vbeln_delivery DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.lips
) s
LEFT JOIN (
  SELECT order_line_id, source_system_line_key,
         ROW_NUMBER() OVER (PARTITION BY source_system_line_key ORDER BY order_line_id DESC) AS _fk_rn
  FROM order_line
) ol ON ol.source_system_line_key = CASE WHEN s.vbeln_order IS NULL OR s.posnr_order IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln_order, s.posnr_order) END AND ol._fk_rn = 1
WHERE s._rn = 1