-- dim_sales_area (G0, Materialized View — passthrough from silver)
-- Sales organization structure dimension
-- Source: manufacturing_silver_vibe.sales_order_silver_sdp.sales_area (4 rows)
-- PK: Sales_Area_Key = sales_area_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_sales_area (
  Sales_Area_Key        STRING  COMMENT 'Surrogate PK (identity from silver sales_area_id)',
  Sales_Organization    STRING  COMMENT 'Sales organization code',
  Distribution_Channel  STRING  COMMENT 'Distribution channel code',
  Division              STRING  COMMENT 'Product division code',
  Currency_Code         STRING  COMMENT 'Local currency (ISO)',
  Pricing_Procedure     STRING  COMMENT 'Pricing procedure assignment',
  Sales_Area_Description STRING COMMENT 'Display description',
  CONSTRAINT valid_pk EXPECT (Sales_Area_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Sales_Area_Key)
COMMENT 'Sales organization structure dimension (org + channel + division)'
AS
SELECT
  sales_area_id          AS Sales_Area_Key,
  Sales_Organization,
  Distribution_Channel,
  Division,
  Currency_Code,
  Pricing_Procedure,
  Sales_Area_Description
FROM manufacturing_silver_vibe.sales_order_silver_sdp.sales_area;
