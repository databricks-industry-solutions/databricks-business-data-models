-- bridge_order_partner (G1, Materialized View)
-- Pivoted partner function lookup — enables Ship-To and Bill-To analysis on the order fact
-- Source: manufacturing_silver_vibe.sales_order_silver_sdp.order_partner (pivoted 3→1 per order)
-- PK: order_id (1:1 with fact at order-header grain)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.bridge_order_partner (
  order_id          STRING  COMMENT 'PK — links to fact via order.order_id',
  Sold_To_Number    STRING  COMMENT 'Sold-To partner number (AG)',
  Sold_To_Name      STRING  COMMENT 'Sold-To partner name',
  Ship_To_Number    STRING  COMMENT 'Ship-To partner number (WE)',
  Ship_To_Name      STRING  COMMENT 'Ship-To partner name',
  Ship_To_Country   STRING  COMMENT 'Ship-To country',
  Ship_To_City      STRING  COMMENT 'Ship-To city',
  Bill_To_Number    STRING  COMMENT 'Bill-To partner number (RE)',
  Bill_To_Name      STRING  COMMENT 'Bill-To partner name',
  CONSTRAINT valid_pk EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_id)
COMMENT 'Pivoted partner function bridge — Sold-To, Ship-To, Bill-To per order'
AS
SELECT
  order_id,
  MAX(CASE WHEN Partner_Function = 'AG' THEN Partner_Number END) AS Sold_To_Number,
  MAX(CASE WHEN Partner_Function = 'AG' THEN Partner_Name END)   AS Sold_To_Name,
  MAX(CASE WHEN Partner_Function = 'WE' THEN Partner_Number END) AS Ship_To_Number,
  MAX(CASE WHEN Partner_Function = 'WE' THEN Partner_Name END)   AS Ship_To_Name,
  MAX(CASE WHEN Partner_Function = 'WE' THEN Country END)        AS Ship_To_Country,
  MAX(CASE WHEN Partner_Function = 'WE' THEN City END)           AS Ship_To_City,
  MAX(CASE WHEN Partner_Function = 'RE' THEN Partner_Number END) AS Bill_To_Number,
  MAX(CASE WHEN Partner_Function = 'RE' THEN Partner_Name END)   AS Bill_To_Name
FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_partner
GROUP BY order_id;
