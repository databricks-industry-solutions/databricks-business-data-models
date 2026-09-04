-- delivery_schedule (T6, Materialized View)
-- Scheduling agreement delivery cadence records (EDI schedule types)
-- Source: manufacturing_bronze_vibe.sap_sd.vbep filtered by scheduling agreement orders (0 rows expected)
-- Natural Key: vbeln + posnr + etenr (for scheduling agreement types)
-- Note: Partial grade — no scheduling agreement orders exist in current bronze
CREATE OR REFRESH MATERIALIZED VIEW delivery_schedule (
  delivery_schedule_id      STRING    COMMENT 'Surrogate PK: SHA2(vbeln|posnr|etenr)',
  Order_Number              STRING    COMMENT 'Scheduling agreement document number',
  Line_Number               STRING    COMMENT 'Schedule line item',
  Schedule_Line_Number      STRING    COMMENT 'Schedule line sequence',
  Delivery_Date             DATE      COMMENT 'Scheduled delivery date',
  Delivery_Quantity         DECIMAL(15,3) COMMENT 'Scheduled delivery quantity',
  Cumulative_Quantity       DECIMAL(15,3) COMMENT 'Cumulative delivered quantity',
  Delivery_Block            STRING    COMMENT 'Delivery block indicator',
  order_line_id             STRING    COMMENT 'FK to order_line',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Number IS NOT NULL AND Line_Number IS NOT NULL AND Schedule_Line_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_line_resolved EXPECT (order_line_id IS NOT NULL)
)
CLUSTER BY (delivery_schedule_id)
COMMENT 'Scheduling agreement delivery cadence records (0 rows expected — no SA types in bronze)'
AS
SELECT
  SHA2(CONCAT(TRIM(ep.vbeln), '|', TRIM(ep.posnr), '|', TRIM(ep.etenr)), 256) AS delivery_schedule_id,
  TRIM(ep.vbeln)                               AS Order_Number,
  TRIM(ep.posnr)                               AS Line_Number,
  TRIM(ep.etenr)                               AS Schedule_Line_Number,
  TRY_TO_DATE(ep.edatu, 'yyyyMMdd')            AS Delivery_Date,
  TRY_CAST(ep.bmeng AS DECIMAL(15,3))          AS Delivery_Quantity,
  TRY_CAST(ep.wmeng AS DECIMAL(15,3))          AS Cumulative_Quantity,
  TRIM(ep.lifsp)                               AS Delivery_Block,
  SHA2(CONCAT(TRIM(ep.vbeln), '|', TRIM(ep.posnr)), 256) AS order_line_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(ep.edatu, 'yyyyMMdd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.vbep ep
INNER JOIN manufacturing_bronze_vibe.sap_sd.vbak hdr
  ON TRIM(ep.vbeln) = TRIM(hdr.vbeln)
WHERE TRIM(hdr.auart) IN ('LZ', 'LZM', 'LP', 'LPA');  -- Scheduling agreement document types (none in current bronze)
