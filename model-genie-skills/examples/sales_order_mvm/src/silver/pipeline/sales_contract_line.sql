CREATE OR REFRESH MATERIALIZED VIEW sales_contract_line (
  sales_contract_line_id BIGINT COMMENT 'Surrogate primary key uniquely identifying an individual line item within a sales contract in the lakehouse silver layer.',
  sales_contract_id BIGINT COMMENT 'FK to sales_contract. SHA2(vbeln).',
  plant_id BIGINT COMMENT 'FK to manufacturing.plant (deferred -- cross-domain).',
  sku_id BIGINT COMMENT 'FK to product_catalog.sku (deferred -- cross-domain).',
  material_number STRING COMMENT 'Source system material or product identifier (e.g., SAP material number) representing the specific product or component committed under this contract line.',
  target_quantity DECIMAL(18,4) COMMENT 'Total committed quantity of the product agreed upon in the contract line. Represents the full volume obligation the customer has committed to purchase over the contract period.',
  target_value DECIMAL(18,2) COMMENT 'Total contracted monetary value committed for this line item over the contract period. Represents the full revenue obligation in the contract currency.',
  net_price DECIMAL(18,4) COMMENT 'Negotiated net unit price for the product on this contract line after all applicable discounts and surcharges, expressed in the contract currency per unit of measure.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this contract line record was originally created in the source system, in ISO 8601 format with timezone offset.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this contract line record in the source system. Used for change tracking, delta processing, and audit trail purposes.',
  source_system STRING COMMENT 'Identifier of the originating operational system of record for this contract line per VREQ-004 SSOT rule. Supports multi-ERP environments from M&A activity without duplicating domains per source syste',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|posnr); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (sales_contract_line_id)
COMMENT 'Individual line item within a sales contract capturing the product-level commitment detail. Captures line number, material/SKU reference, target quantity, target value, released quantity, released val. Grain: sales_contract_line_id (SHA2 of vbeln|posnr). Source: sap_sd_mvm.veda_item.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.posnr AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS sales_contract_line_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS sales_contract_id,
  CAST(NULL AS BIGINT) AS plant_id,
  CAST(NULL AS BIGINT) AS sku_id,
  s.matnr AS material_number,
  TRY_CAST(s.zmeng AS DECIMAL(18,4)) AS target_quantity,
  TRY_CAST(s.target_val AS DECIMAL(18,2)) AS target_value,
  TRY_CAST(s.netpr AS DECIMAL(18,4)) AS net_price,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SAP_SD' AS source_system,
  CASE WHEN s.vbeln IS NULL OR s.posnr IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.posnr) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, posnr ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.veda_item
) s
WHERE s._rn = 1