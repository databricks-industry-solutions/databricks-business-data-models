-- return_order_line (T7, Materialized View)
-- Line-item detail within return orders
-- Source: manufacturing_bronze_vibe.returns_portal.rma_line (329 rows)
-- Natural Key: rma_line_id
-- FK: return_order_id = SHA2(rma_number, 256) — hash-identity (100% resolved)
CREATE OR REFRESH MATERIALIZED VIEW return_order_line (
  return_order_line_id      STRING    COMMENT 'Surrogate PK: SHA2(rma_line_id)',
  RMA_Line_Id               STRING    COMMENT 'Unique return line identifier',
  RMA_Number                STRING    COMMENT 'Parent RMA number',
  Line_Number               STRING    COMMENT 'Line sequence within RMA',
  SKU_Code                  STRING    COMMENT 'Returned product SKU',
  Returned_Quantity         DECIMAL(15,3) COMMENT 'Quantity being returned',
  Unit_Of_Measure           STRING    COMMENT 'Unit of measure',
  Reason_Code               STRING    COMMENT 'Line-level return reason (portal vocab)',
  Inspection_Result         STRING    COMMENT 'Inspection outcome',
  Credit_Value              DECIMAL(15,2) COMMENT 'Credit value for this line',
  Restocking_Fee            DECIMAL(15,2) COMMENT 'Restocking fee charged',
  Is_Warranty               BOOLEAN   COMMENT 'Whether return is warranty-covered',
  return_order_id           STRING    COMMENT 'FK to return_order (hash-identity)',
  order_reason_id           STRING    COMMENT 'FK to order_reason (NULL — vocab gap, P1)',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (RMA_Line_Id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_return_order_resolved EXPECT (return_order_id IS NOT NULL)
)
CLUSTER BY (return_order_id)
COMMENT 'Line-item detail within RMA return orders'
AS
SELECT
  SHA2(TRIM(rma_line_id), 256)                 AS return_order_line_id,
  TRIM(rma_line_id)                            AS RMA_Line_Id,
  TRIM(rma_number)                             AS RMA_Number,
  TRIM(line_number)                            AS Line_Number,
  TRIM(sku_code)                               AS SKU_Code,
  TRY_CAST(returned_quantity AS DECIMAL(15,3)) AS Returned_Quantity,
  TRIM(uom)                                    AS Unit_Of_Measure,
  TRIM(reason_code)                            AS Reason_Code,
  TRIM(inspection_result)                      AS Inspection_Result,
  TRY_CAST(credit_value AS DECIMAL(15,2))      AS Credit_Value,
  TRY_CAST(restocking_fee AS DECIMAL(15,2))    AS Restocking_Fee,
  CASE UPPER(TRIM(is_warranty))
    WHEN 'TRUE' THEN TRUE WHEN 'YES' THEN TRUE
    WHEN 'FALSE' THEN FALSE WHEN 'NO' THEN FALSE
    ELSE NULL END                              AS Is_Warranty,
  -- FK: return_order_id (hash-identity — both use SHA2(rma_number))
  SHA2(TRIM(rma_number), 256)                  AS return_order_id,
  -- FK: order_reason_id = NULL (same portal vocab gap as return_order)
  CAST(NULL AS STRING)                         AS order_reason_id,
  'RETURNS_PORTAL'                             AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  current_timestamp()                          AS _source_updated_at
FROM manufacturing_bronze_vibe.returns_portal.rma_line;
