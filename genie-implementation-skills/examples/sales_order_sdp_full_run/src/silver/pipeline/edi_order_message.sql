-- edi_order_message (T6, Streaming Table — append-only)
-- Electronic order message log
-- Source: manufacturing_bronze_vibe.edi_gateway.edi_message_log (956 rows)
-- Natural Key: message_id
-- Watermark: transmission_ts
-- Filter: excludes scheduling message types (DELFOR, DELJIT)
CREATE OR REFRESH STREAMING TABLE edi_order_message (
  edi_order_message_id      STRING    COMMENT 'Surrogate PK: SHA2(message_id)',
  Message_Id                STRING    COMMENT 'Unique EDI message identifier',
  Order_Number              STRING    COMMENT 'Referenced sales order number',
  Partner_Id                STRING    COMMENT 'Trading partner identifier',
  Direction                 STRING    COMMENT 'Message direction (INBOUND/OUTBOUND)',
  Message_Type              STRING    COMMENT 'EDI message type (ORDERS, ORDRSP, etc.)',
  Standard                  STRING    COMMENT 'EDI standard (EDIFACT/X12)',
  Transmission_Timestamp    TIMESTAMP COMMENT 'Message transmission timestamp',
  Processing_Status         STRING    COMMENT 'Processing outcome status',
  Error_Code                STRING    COMMENT 'Error code if failed',
  Ack_Status                STRING    COMMENT 'Acknowledgement status',
  Interchange_Control       STRING    COMMENT 'EDI interchange control number',
  order_id                  STRING    COMMENT 'FK to order',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Message_Id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_resolved EXPECT (order_id IS NOT NULL)
)
CLUSTER BY (order_id)
COMMENT 'Inbound/outbound electronic order transactions (append-only stream)'
AS
SELECT
  SHA2(TRIM(message_id), 256)                  AS edi_order_message_id,
  TRIM(message_id)                             AS Message_Id,
  TRIM(order_number)                           AS Order_Number,
  TRIM(partner_id)                             AS Partner_Id,
  UPPER(TRIM(direction))                       AS Direction,
  UPPER(TRIM(message_type))                    AS Message_Type,
  UPPER(TRIM(standard))                        AS Standard,
  TRY_CAST(transmission_ts AS TIMESTAMP)       AS Transmission_Timestamp,
  TRIM(processing_status)                      AS Processing_Status,
  TRIM(error_code)                             AS Error_Code,
  TRIM(ack_status)                             AS Ack_Status,
  TRIM(interchange_control)                    AS Interchange_Control,
  SHA2(TRIM(order_number), 256)                AS order_id,
  'EDI'                                        AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  TRY_CAST(transmission_ts AS TIMESTAMP)       AS _source_updated_at
FROM STREAM manufacturing_bronze_vibe.edi_gateway.edi_message_log
WHERE UPPER(TRIM(message_type)) NOT IN ('DELFOR', 'DELJIT');  -- Exclude scheduling message types
