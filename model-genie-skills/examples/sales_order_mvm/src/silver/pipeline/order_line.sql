CREATE OR REFRESH MATERIALIZED VIEW order_line (
  order_line_id BIGINT COMMENT 'Surrogate primary key uniquely identifying each individual line item within a sales order in the lakehouse Silver layer. System-generated BIGINT for internal joins and lineage tracking.',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  order_number STRING COMMENT 'Order number',
  line_number STRING COMMENT 'Sequential line item number within the parent sales order, as assigned by the source system (SAP SD item number, e.g., 10, 20, 30). Used to preserve the original order structure and support multi-line',
  sku_code STRING COMMENT 'Material/SKU code from source (matnr)',
  plant_code STRING COMMENT 'Plant code from source (werks)',
  order_quantity DECIMAL(18,4) COMMENT 'The quantity of the SKU/material requested by the customer on this order line, expressed in the sales unit of measure. This is the original customer-requested quantity before any ATP/CTP confirmation.',
  quantity_uom STRING COMMENT 'Unit of measure',
  unit_price DECIMAL(18,4) COMMENT 'Net unit price',
  net_value DECIMAL(18,2) COMMENT 'Total net value of this order line calculated as net_price multiplied by order_quantity, after all pricing conditions. Represents the revenue value of this line item. Used for order value reporting, revenue recognition, and margin analysis.',
  item_category_code STRING COMMENT 'SAP SD item category code controlling the processing behavior of this order line (e.g., TAN for standard item, TAK for consignment, TAD for service, TANN for free-of-charge). Determines billing relevance, delivery processing, and pricing.',
  serial_number_profile STRING COMMENT 'Serial number profile',
  sales_contract_line_id BIGINT COMMENT 'FK to sales_contract_line via vbeln|posnr JOIN',
  sku_id BIGINT COMMENT 'FK to product_catalog.sku (deferred).',
  plant_id BIGINT COMMENT 'FK to manufacturing.plant (deferred).',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|posnr); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_line_id)
COMMENT 'Individual line item within a sales order capturing the product-level detail for each SKU or configurable product ordered. Captures line number, material/SKU reference, order quantity, unit of measure. Grain: order_line_id (SHA2 of vbeln|posnr). Source: sap_sd_mvm.vbap.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.posnr AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS order_line_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  s.vbeln AS order_number,
  s.posnr AS line_number,
  s.matnr AS sku_code,
  s.werks AS plant_code,
  TRY_CAST(s.kwmeng AS DECIMAL(18,4)) AS order_quantity,
  s.vrkme AS quantity_uom,
  TRY_CAST(s.netpr AS DECIMAL(18,4)) AS unit_price,
  TRY_CAST(s.netwr AS DECIMAL(18,2)) AS net_value,
  s.pstyv AS item_category_code,
  s.serail AS serial_number_profile,
  scl.sales_contract_line_id AS sales_contract_line_id,
  CAST(NULL AS BIGINT) AS sku_id,
  CAST(NULL AS BIGINT) AS plant_id,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SAP_SD' AS source_system,
  CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, posnr ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.vbap
) s
LEFT JOIN (
  SELECT sales_contract_line_id, source_system_line_key,
         ROW_NUMBER() OVER (PARTITION BY source_system_line_key ORDER BY sales_contract_line_id DESC) AS _fk_rn
  FROM sales_contract_line
) scl ON scl.source_system_line_key = CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr) END AND scl._fk_rn = 1
WHERE s._rn = 1