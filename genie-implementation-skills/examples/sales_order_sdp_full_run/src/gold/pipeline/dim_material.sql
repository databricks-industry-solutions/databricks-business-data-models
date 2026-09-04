-- dim_material (G1, Materialized View)
-- Conformed material/product dimension
-- Source: order_line (Material_Number) UNION quotation_line (SKU_Code) — ~400 distinct
-- PK: Material_Key = SHA2(Material_Number, 256)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_material (
  Material_Key     STRING  COMMENT 'Surrogate PK: SHA2(Material_Number, 256)',
  Material_Number  STRING  COMMENT 'Material/product code',
  Item_Category    STRING  COMMENT 'Most frequent item category per material',
  Product_Group    STRING  COMMENT 'Product group (from quotation_line where available)',
  _source_system   STRING  COMMENT 'Source system enum',
  _loaded_at       TIMESTAMP COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_pk EXPECT (Material_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Material_Key)
COMMENT 'Conformed material/product dimension (order_line + quotation_line sources)'
AS
WITH order_materials AS (
  SELECT
    Material_Number,
    Item_Category,
    ROW_NUMBER() OVER (PARTITION BY Material_Number ORDER BY COUNT(*) DESC) AS _rn
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_line
  WHERE Material_Number IS NOT NULL
  GROUP BY Material_Number, Item_Category
),
quote_materials AS (
  SELECT
    SKU_Code AS Material_Number,
    Product_Group,
    ROW_NUMBER() OVER (PARTITION BY SKU_Code ORDER BY COUNT(*) DESC) AS _rn
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.quotation_line
  WHERE SKU_Code IS NOT NULL
  GROUP BY SKU_Code, Product_Group
),
all_materials AS (
  SELECT DISTINCT Material_Number
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_line
  WHERE Material_Number IS NOT NULL
  UNION
  SELECT DISTINCT SKU_Code AS Material_Number
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.quotation_line
  WHERE SKU_Code IS NOT NULL
)
SELECT
  SHA2(m.Material_Number, 256)  AS Material_Key,
  m.Material_Number,
  om.Item_Category,
  qm.Product_Group,
  'SAP_S4'                      AS _source_system,
  current_timestamp()           AS _loaded_at
FROM all_materials m
LEFT JOIN order_materials om ON om.Material_Number = m.Material_Number AND om._rn = 1
LEFT JOIN quote_materials qm ON qm.Material_Number = m.Material_Number AND qm._rn = 1;
