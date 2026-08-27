-- otd_record (T6, Materialized View)
-- On-time delivery tracking per schedule line (proxy — actual_delivery_date requires likp/lips)
-- Source: manufacturing_bronze_vibe.sap_sd.vbep (22,212 rows)
-- Natural Key: vbeln + posnr + etenr
-- FK: order_line_id, order_schedule_line_id (hash-identity)
-- P0 Gap: actual_delivery_date = NULL (requires likp/lips ingestion)
CREATE OR REFRESH MATERIALIZED VIEW otd_record (
  otd_record_id             STRING    COMMENT 'Surrogate PK: SHA2(vbeln|posnr|etenr)',
  Order_Number              STRING    COMMENT 'Sales order document number',
  Line_Number               STRING    COMMENT 'Order line position',
  Schedule_Line_Number      STRING    COMMENT 'Schedule line sequence',
  Requested_Delivery_Date   DATE      COMMENT 'Customer-requested date (edatu)',
  Goods_Issue_Date          DATE      COMMENT 'Planned goods issue date (wadat) — OTD proxy',
  Actual_Delivery_Date      DATE      COMMENT 'Actual delivery date (NULL — P0 gap, requires likp/lips)',
  OTD_Status                STRING    COMMENT 'ON_TIME or LATE (proxy: wadat <= edatu)',
  Days_Variance             INT       COMMENT 'Days between goods issue and requested date',
  order_line_id             STRING    COMMENT 'FK to order_line',
  order_schedule_line_id    STRING    COMMENT 'FK to order_schedule_line (hash-identity)',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Number IS NOT NULL AND Line_Number IS NOT NULL AND Schedule_Line_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_line_resolved EXPECT (order_line_id IS NOT NULL),
  CONSTRAINT fk_schedule_line_resolved EXPECT (order_schedule_line_id IS NOT NULL)
)
CLUSTER BY (order_line_id)
COMMENT 'On-time delivery tracking per schedule line (proxy — actual_delivery_date P0 gap)'
AS
SELECT
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr), '|', TRIM(etenr)), 256) AS otd_record_id,
  TRIM(vbeln)                                  AS Order_Number,
  TRIM(posnr)                                  AS Line_Number,
  TRIM(etenr)                                  AS Schedule_Line_Number,
  TRY_TO_DATE(edatu, 'yyyyMMdd')               AS Requested_Delivery_Date,
  TRY_TO_DATE(wadat, 'yyyyMMdd')               AS Goods_Issue_Date,
  CAST(NULL AS DATE)                           AS Actual_Delivery_Date,  -- P0 gap: requires likp/lips
  -- OTD proxy: compare wadat (goods issue) to edatu (requested)
  CASE
    WHEN TRY_TO_DATE(wadat, 'yyyyMMdd') IS NULL THEN NULL
    WHEN TRY_TO_DATE(wadat, 'yyyyMMdd') <= TRY_TO_DATE(edatu, 'yyyyMMdd') THEN 'ON_TIME'
    ELSE 'LATE'
  END                                          AS OTD_Status,
  DATEDIFF(TRY_TO_DATE(wadat, 'yyyyMMdd'), TRY_TO_DATE(edatu, 'yyyyMMdd')) AS Days_Variance,
  -- FK: order_line_id
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr)), 256) AS order_line_id,
  -- FK: order_schedule_line_id (hash-identity — same source, same key components)
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr), '|', TRIM(etenr)), 256) AS order_schedule_line_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(edatu, 'yyyyMMdd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.vbep;
