-- return_order (T6, Materialized View)
-- RMA return order headers from returns portal
-- Source: manufacturing_bronze_vibe.returns_portal.rma_request (227 rows)
-- Natural Key: rma_number
-- FK: order_id = 100% resolved; order_reason_id = NULL (vocab gap — HG-SDP-4 ACCEPTED)
CREATE OR REFRESH MATERIALIZED VIEW return_order (
  return_order_id           STRING    COMMENT 'Surrogate PK: SHA2(rma_number)',
  RMA_Number                STRING    COMMENT 'Return merchandise authorization number',
  Original_Order_Number     STRING    COMMENT 'Original sales order being returned against',
  Customer_Number           STRING    COMMENT 'Returning customer number',
  RMA_Date                  DATE      COMMENT 'Return request date',
  Reason_Code               STRING    COMMENT 'Portal reason code (unmapped to SAP vocab)',
  Status                    STRING    COMMENT 'Return processing status',
  Return_Plant              STRING    COMMENT 'Receiving plant for returned goods',
  Credit_Memo_Required      BOOLEAN   COMMENT 'Whether credit memo is needed',
  Inspection_Required       BOOLEAN   COMMENT 'Whether inspection is needed',
  Total_Return_Value        DECIMAL(15,2) COMMENT 'Total value of the return',
  order_id                  STRING    COMMENT 'FK to order (100% resolved)',
  order_reason_id           STRING    COMMENT 'FK to order_reason (NULL — vocab gap, P1)',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (RMA_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_resolved EXPECT (order_id IS NOT NULL)
)
CLUSTER BY (order_id)
COMMENT 'RMA return order headers (order_reason_id=NULL due to portal vocab gap — P1)'
AS
SELECT
  SHA2(TRIM(rma_number), 256)                  AS return_order_id,
  TRIM(rma_number)                             AS RMA_Number,
  TRIM(original_order_number)                  AS Original_Order_Number,
  TRIM(customer_kunnr)                         AS Customer_Number,
  TRY_TO_DATE(rma_date, 'yyyy-MM-dd')          AS RMA_Date,
  TRIM(reason_code)                            AS Reason_Code,
  TRIM(status)                                 AS Status,
  TRIM(return_plant)                           AS Return_Plant,
  CASE UPPER(TRIM(credit_memo_required))
    WHEN 'TRUE' THEN TRUE WHEN 'YES' THEN TRUE
    WHEN 'FALSE' THEN FALSE WHEN 'NO' THEN FALSE
    ELSE NULL END                              AS Credit_Memo_Required,
  CASE UPPER(TRIM(inspection_required))
    WHEN 'TRUE' THEN TRUE WHEN 'YES' THEN TRUE
    WHEN 'FALSE' THEN FALSE WHEN 'NO' THEN FALSE
    ELSE NULL END                              AS Inspection_Required,
  TRY_CAST(total_return_value AS DECIMAL(15,2)) AS Total_Return_Value,
  -- FK: order_id via original_order_number
  SHA2(TRIM(original_order_number), 256)       AS order_id,
  -- FK: order_reason_id = NULL (portal codes DMG/WRONG/WARR don't map to SAP codes)
  CAST(NULL AS STRING)                         AS order_reason_id,
  'RETURNS_PORTAL'                             AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(rma_date, 'yyyy-MM-dd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.returns_portal.rma_request;
