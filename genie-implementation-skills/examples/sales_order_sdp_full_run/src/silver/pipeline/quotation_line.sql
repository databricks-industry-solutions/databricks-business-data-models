-- quotation_line (T3, Materialized View)
-- Line-item detail within quotations
-- Source: manufacturing_bronze_vibe.salesforce_crm.quote_line (11,982 rows)
-- Natural Key: quote_line_id (CRM UUID)
-- FK: quotation_id = SHA2(quote_id, 256) — hash-identity (both CRM UUID)
CREATE OR REFRESH MATERIALIZED VIEW quotation_line (
  quotation_line_id         STRING    COMMENT 'Surrogate PK: SHA2(quote_line_id)',
  Line_Number               STRING    COMMENT 'Line position within quote',
  SKU_Code                  STRING    COMMENT 'Product/material SKU',
  Material_Description      STRING    COMMENT 'Product description',
  Quantity                  DECIMAL(15,3) COMMENT 'Quoted quantity',
  Unit_Of_Measure           STRING    COMMENT 'Unit of measure',
  List_Price                DECIMAL(15,2) COMMENT 'Catalog list price',
  Discount_Pct              DECIMAL(5,2) COMMENT 'Applied discount percentage',
  Net_Price                 DECIMAL(15,2) COMMENT 'Net price after discount',
  Net_Value                 DECIMAL(15,2) COMMENT 'Extended net value (qty x net price)',
  Product_Group             STRING    COMMENT 'Product grouping category',
  quotation_id              STRING    COMMENT 'FK to quotation (hash-identity)',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (quotation_line_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_quotation_resolved EXPECT (quotation_id IS NOT NULL)
)
CLUSTER BY (quotation_id)
COMMENT 'Line-item detail within CRM quotations'
AS
SELECT
  SHA2(TRIM(quote_line_id), 256)               AS quotation_line_id,
  TRIM(line_number)                            AS Line_Number,
  TRIM(sku_code)                               AS SKU_Code,
  TRIM(material_description)                   AS Material_Description,
  TRY_CAST(quantity AS DECIMAL(15,3))          AS Quantity,
  TRIM(uom)                                    AS Unit_Of_Measure,
  TRY_CAST(list_price AS DECIMAL(15,2))        AS List_Price,
  TRY_CAST(discount_pct AS DECIMAL(5,2))       AS Discount_Pct,
  TRY_CAST(net_price AS DECIMAL(15,2))         AS Net_Price,
  TRY_CAST(net_value AS DECIMAL(15,2))         AS Net_Value,
  TRIM(product_group)                          AS Product_Group,
  -- FK: hash-identity safe (both quote_id and quotation PK are SHA2 of same CRM UUID)
  SHA2(TRIM(quote_id), 256)                    AS quotation_id,
  'SALESFORCE'                                 AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  current_timestamp()                          AS _source_updated_at
FROM manufacturing_bronze_vibe.salesforce_crm.quote_line;
