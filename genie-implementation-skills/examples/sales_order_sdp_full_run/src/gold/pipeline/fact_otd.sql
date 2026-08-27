-- fact_otd (G2, Materialized View)
-- Schedule-line grain fact for delivery performance analysis
-- Source: silver otd_record + order_line + order + order_partner (Sold-To AG)
-- Grain: One row per delivery schedule line (22,212 rows)
-- PK: OTD_Key = otd_record_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.fact_otd (
  OTD_Key                     STRING    COMMENT 'PK (identity from silver otd_record_id)',
  Order_Number                STRING    COMMENT 'Degenerate dim: sales order number',
  Line_Number                 STRING    COMMENT 'Degenerate dim: order line position',
  Requested_Delivery_Date_Key DATE      COMMENT 'FK to dim_date (requested delivery date)',
  Customer_Key                STRING    COMMENT 'FK to dim_customer (via order Sold-To)',
  Material_Key                STRING    COMMENT 'FK to dim_material (via order_line)',
  Sales_Area_Key              STRING    COMMENT 'FK to dim_sales_area (via order)',
  OTD_Status                  STRING    COMMENT 'ON_TIME or LATE (proxy from schedule dates)',
  Days_Variance               INT       COMMENT 'Days between goods issue and requested date',
  Is_On_Time                  BOOLEAN   COMMENT 'OTD_Status = ON_TIME flag',
  Actual_Delivery_Date        DATE      COMMENT 'Actual delivery date (NULL — P0 gap, requires likp/lips)',
  _source_system              STRING    COMMENT 'Source system enum',
  _loaded_at                  TIMESTAMP COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_grain EXPECT (OTD_Key IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_date_resolved EXPECT (Requested_Delivery_Date_Key IS NOT NULL),
  CONSTRAINT fk_customer_resolved EXPECT (Customer_Key IS NOT NULL)
)
CLUSTER BY (Customer_Key)
COMMENT 'On-time delivery fact — schedule-line grain (OTD proxy, actual_delivery_date P0 gap)'
AS
SELECT
  otd.otd_record_id                          AS OTD_Key,
  otd.Order_Number,
  otd.Line_Number,
  otd.Requested_Delivery_Date                AS Requested_Delivery_Date_Key,
  SHA2(ag.Partner_Number, 256)               AS Customer_Key,
  SHA2(ol.Material_Number, 256)              AS Material_Key,
  o.sales_area_id                            AS Sales_Area_Key,
  otd.OTD_Status,
  otd.Days_Variance,
  otd.OTD_Status = 'ON_TIME'                 AS Is_On_Time,
  otd.Actual_Delivery_Date,
  'SAP_S4'                                   AS _source_system,
  current_timestamp()                        AS _loaded_at
FROM manufacturing_silver_vibe.sales_order_silver_sdp.otd_record otd
INNER JOIN manufacturing_silver_vibe.sales_order_silver_sdp.order_line ol
  ON ol.order_line_id = otd.order_line_id
INNER JOIN manufacturing_silver_vibe.sales_order_silver_sdp.`order` o
  ON o.order_id = ol.order_id
LEFT JOIN (
  SELECT order_id, Partner_Number,
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY Order_Number DESC) AS _rn
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_partner
  WHERE Partner_Function = 'AG'
) ag ON ag.order_id = ol.order_id AND ag._rn = 1;
