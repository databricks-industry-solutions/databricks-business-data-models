-- sales_area (T0, Materialized View)
-- Sales organization structure: org + channel + division combinations
-- Source: manufacturing_bronze_vibe.sap_sd.tvta (4 rows)
-- Natural Key: vkorg + vtweg + spart
CREATE OR REFRESH MATERIALIZED VIEW sales_area (
  sales_area_id             STRING    COMMENT 'Surrogate PK: SHA2(vkorg|vtweg|spart)',
  Sales_Organization        STRING    COMMENT 'Sales organization code',
  Distribution_Channel      STRING    COMMENT 'Distribution channel code',
  Division                  STRING    COMMENT 'Product division code',
  Currency_Code             STRING    COMMENT 'Local currency (ISO)',
  Pricing_Procedure         STRING    COMMENT 'Pricing procedure assignment',
  Sales_Area_Description    STRING    COMMENT 'Display description',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Sales_Organization IS NOT NULL AND Distribution_Channel IS NOT NULL AND Division IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (sales_area_id)
COMMENT 'Sales organization structure defining org + channel + division combinations'
AS
SELECT
  SHA2(CONCAT(TRIM(vkorg), '|', TRIM(vtweg), '|', TRIM(spart)), 256) AS sales_area_id,
  TRIM(vkorg)           AS Sales_Organization,
  TRIM(vtweg)           AS Distribution_Channel,
  TRIM(spart)           AS Division,
  UPPER(TRIM(waers))    AS Currency_Code,
  TRIM(kalks)           AS Pricing_Procedure,
  TRIM(bezei)           AS Sales_Area_Description,
  'SAP_S4'              AS _source_system,
  current_timestamp()   AS _loaded_at,
  'meridian_sales_order_silver_sdp' AS _created_by,
  'meridian_sales_order_silver_sdp' AS _modified_by,
  current_timestamp()   AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.tvta;
