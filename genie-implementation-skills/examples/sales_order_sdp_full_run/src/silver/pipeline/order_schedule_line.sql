-- order_schedule_line (T5, Materialized View)
-- Confirmed delivery schedule per order line item
-- Source: manufacturing_bronze_vibe.sap_sd.vbep (22,212 rows)
-- Natural Key: vbeln + posnr + etenr
CREATE OR REFRESH MATERIALIZED VIEW order_schedule_line (
  order_schedule_line_id    STRING    COMMENT 'Surrogate PK: SHA2(vbeln|posnr|etenr)',
  Order_Number              STRING    COMMENT 'Parent order document number',
  Line_Number               STRING    COMMENT 'Order line position',
  Schedule_Line_Number      STRING    COMMENT 'Schedule line sequence number',
  Requested_Delivery_Date   DATE      COMMENT 'Requested delivery date (edatu)',
  Goods_Issue_Date          DATE      COMMENT 'Planned goods issue date (wadat)',
  Confirmed_Quantity        DECIMAL(15,3) COMMENT 'Confirmed delivery quantity',
  Ordered_Quantity          DECIMAL(15,3) COMMENT 'Original ordered quantity',
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
CLUSTER BY (order_line_id)
COMMENT 'Confirmed delivery dates and quantities per order line item'
AS
SELECT
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr), '|', TRIM(etenr)), 256) AS order_schedule_line_id,
  TRIM(vbeln)                                  AS Order_Number,
  TRIM(posnr)                                  AS Line_Number,
  TRIM(etenr)                                  AS Schedule_Line_Number,
  TRY_TO_DATE(edatu, 'yyyyMMdd')               AS Requested_Delivery_Date,
  TRY_TO_DATE(wadat, 'yyyyMMdd')               AS Goods_Issue_Date,
  TRY_CAST(bmeng AS DECIMAL(15,3))             AS Confirmed_Quantity,
  TRY_CAST(wmeng AS DECIMAL(15,3))             AS Ordered_Quantity,
  TRIM(lifsp)                                  AS Delivery_Block,
  -- FK: order_line_id via hash of vbeln|posnr (same components as order_line PK)
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr)), 256) AS order_line_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(edatu, 'yyyyMMdd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.vbep;
