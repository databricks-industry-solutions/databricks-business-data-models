CREATE OR REFRESH MATERIALIZED VIEW return_order (
  return_order_id BIGINT COMMENT 'Surrogate PK: SHA2(rma_number)',
  original_order_id BIGINT COMMENT 'FK to order via original_order_number JOIN',
  customer_account_number STRING COMMENT 'Customer account number from source (customer_kunnr)',
  rma_date DATE COMMENT 'RMA date',
  reason_code STRING COMMENT 'Return reason code',
  status STRING COMMENT 'RMA status',
  return_plant_code STRING COMMENT 'Return plant code',
  credit_memo_required STRING COMMENT 'Credit memo required flag',
  inspection_required STRING COMMENT 'Inspection required flag',
  total_return_value DECIMAL(18,2) COMMENT 'Total return value',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_key STRING COMMENT 'Natural key from source (rma_number); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (return_order_id)
COMMENT 'Sales return order (RMA — Return Material Authorization) master record capturing a customer-initiated product return request. Captures return order number, original order reference, return reason code. Grain: return_order_id (SHA2 of rma_number). Source: returns_portal_mvm.rma_request.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.rma_number AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS return_order_id,
  o.order_id AS original_order_id,
  s.customer_kunnr AS customer_account_number,
  TRY_TO_DATE(s.rma_date, 'yyyy-MM-dd') AS rma_date,
  s.reason_code AS reason_code,
  s.status AS status,
  s.return_plant AS return_plant_code,
  s.credit_memo_required AS credit_memo_required,
  s.inspection_required AS inspection_required,
  TRY_CAST(s.total_return_value AS DECIMAL(18,2)) AS total_return_value,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'RETURNS_PORTAL' AS source_system,
  s.rma_number AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY rma_number ORDER BY rma_number DESC) AS _rn
  FROM manufacturing_bronze_vibe.returns_portal_mvm.rma_request
) s
LEFT JOIN (
  SELECT order_id, order_number,
         ROW_NUMBER() OVER (PARTITION BY order_number ORDER BY order_id DESC) AS _fk_rn
  FROM `order`
) o ON o.order_number = s.original_order_number AND o._fk_rn = 1
WHERE s._rn = 1