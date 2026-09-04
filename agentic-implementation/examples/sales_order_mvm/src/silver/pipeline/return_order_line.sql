CREATE OR REFRESH MATERIALIZED VIEW return_order_line (
  return_order_line_id BIGINT COMMENT 'Surrogate PK: SHA2(rma_line_id)',
  return_order_id BIGINT COMMENT 'FK to return_order via rma_number JOIN',
  line_number STRING COMMENT 'Sequential line item number within the return order document, used to uniquely identify each returned SKU position within the same return order.',
  sku_code STRING COMMENT 'Material/SKU code',
  returned_quantity DECIMAL(18,4) COMMENT 'Quantity of the SKU being returned on this line item, expressed in the unit of measure. Used for inventory revaluation, credit calculation, and returns rate analytics.',
  unit_of_measure STRING COMMENT 'Unit of measure in which the returned quantity is expressed (e.g., EA for each, KG for kilogram, M for meter). Aligns with ISO 80000 and SAP base unit of measure. [ENUM-REF-CANDIDATE: EA|PC|KG|M|M2|M3',
  reason_code STRING COMMENT 'Return reason code',
  inspection_result STRING COMMENT 'Outcome of the goods receipt quality inspection for the returned item — accepted for restocking, rejected (return to customer or supplier), or scrapped. Feeds quality management and inventory disposit',
  credit_value DECIMAL(18,2) COMMENT 'Total credit amount to be issued to the customer for this return line (returned_quantity × net_price minus restocking fee), expressed in the transaction currency. Feeds accounts receivable and revenue',
  restocking_fee DECIMAL(18,2) COMMENT 'Fee charged to the customer for processing the return and restocking the item, deducted from the gross credit value. Expressed in the transaction currency.',
  is_warranty STRING COMMENT 'Warranty flag',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_key STRING COMMENT 'Natural key from source (rma_line_id); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (return_order_line_id)
COMMENT 'Individual line item within a sales return order capturing the product-level detail for each returned SKU. Captures line number, material/SKU reference, returned quantity, unit of measure, original or. Grain: return_order_line_id (SHA2 of rma_line_id). Source: returns_portal_mvm.rma_line.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.rma_line_id AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS return_order_line_id,
  ro.return_order_id AS return_order_id,
  s.line_number AS line_number,
  s.sku_code AS sku_code,
  TRY_CAST(s.returned_quantity AS DECIMAL(18,4)) AS returned_quantity,
  s.uom AS unit_of_measure,
  s.reason_code AS reason_code,
  s.inspection_result AS inspection_result,
  TRY_CAST(s.credit_value AS DECIMAL(18,2)) AS credit_value,
  TRY_CAST(s.restocking_fee AS DECIMAL(18,2)) AS restocking_fee,
  s.is_warranty AS is_warranty,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'RETURNS_PORTAL' AS source_system,
  s.rma_line_id AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY rma_line_id ORDER BY rma_line_id DESC) AS _rn
  FROM manufacturing_bronze_vibe.returns_portal_mvm.rma_line
) s
LEFT JOIN (
  SELECT return_order_id, source_system_key,
         ROW_NUMBER() OVER (PARTITION BY source_system_key ORDER BY return_order_id DESC) AS _fk_rn
  FROM return_order
) ro ON ro.source_system_key = s.rma_number AND ro._fk_rn = 1
WHERE s._rn = 1