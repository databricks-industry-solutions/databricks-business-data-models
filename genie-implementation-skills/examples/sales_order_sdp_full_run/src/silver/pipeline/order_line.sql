-- order_line (T4, Materialized View)
-- Product-level line items within orders
-- Source: manufacturing_bronze_vibe.sap_sd.vbap (14,762 rows)
-- Natural Key: vbeln + posnr
CREATE OR REFRESH MATERIALIZED VIEW order_line (
  order_line_id             STRING    COMMENT 'Surrogate PK: SHA2(vbeln|posnr)',
  Order_Number              STRING    COMMENT 'Parent order document number',
  Line_Number               STRING    COMMENT 'Item position number',
  Material_Number           STRING    COMMENT 'Material/product code',
  Plant                     STRING    COMMENT 'Delivering plant',
  Order_Quantity            DECIMAL(15,3) COMMENT 'Ordered quantity',
  Unit_Of_Measure           STRING    COMMENT 'Sales unit of measure',
  Net_Price                 DECIMAL(15,2) COMMENT 'Net price per unit',
  Net_Value                 DECIMAL(15,2) COMMENT 'Line net value',
  Rejection_Reason          STRING    COMMENT 'Line-level rejection reason',
  Item_Category             STRING    COMMENT 'Item category (standard/return/free)',
  Higher_Level_Item         STRING    COMMENT 'Parent item (BOM structure)',
  Batch                     STRING    COMMENT 'Batch/lot number',
  Serial_Number_Profile     STRING    COMMENT 'Serial number profile',
  order_id                  STRING    COMMENT 'FK to order',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Number IS NOT NULL AND Line_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_resolved EXPECT (order_id IS NOT NULL)
)
CLUSTER BY (order_id)
COMMENT 'Product-level line items within sales orders'
AS
SELECT
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr)), 256) AS order_line_id,
  TRIM(vbeln)                                  AS Order_Number,
  TRIM(posnr)                                  AS Line_Number,
  TRIM(matnr)                                  AS Material_Number,
  TRIM(werks)                                  AS Plant,
  TRY_CAST(kwmeng AS DECIMAL(15,3))            AS Order_Quantity,
  TRIM(vrkme)                                  AS Unit_Of_Measure,
  TRY_CAST(netpr AS DECIMAL(15,2))             AS Net_Price,
  TRY_CAST(netwr AS DECIMAL(15,2))             AS Net_Value,
  TRIM(abgru)                                  AS Rejection_Reason,
  TRIM(pstyv)                                  AS Item_Category,
  TRIM(uepos)                                  AS Higher_Level_Item,
  TRIM(charg)                                  AS Batch,
  TRIM(serail)                                 AS Serial_Number_Profile,
  SHA2(TRIM(vbeln), 256)                       AS order_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  current_timestamp()                          AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.vbap;
