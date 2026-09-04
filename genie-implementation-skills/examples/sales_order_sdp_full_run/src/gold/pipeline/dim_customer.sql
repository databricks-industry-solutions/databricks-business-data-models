-- dim_customer (G1, Materialized View)
-- Conformed customer dimension — Sold-To party with geo attributes
-- Source: manufacturing_silver_vibe.sales_order_silver_sdp.order_partner (AG only, ~300 distinct)
-- PK: Customer_Key = SHA2(Partner_Number, 256)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_customer (
  Customer_Key     STRING  COMMENT 'Surrogate PK: SHA2(Partner_Number, 256)',
  Customer_Number  STRING  COMMENT 'SAP Sold-To partner number',
  Customer_Name    STRING  COMMENT 'Customer display name',
  Country          STRING  COMMENT 'Country key',
  City             STRING  COMMENT 'City name',
  Postal_Code      STRING  COMMENT 'Postal code',
  _source_system   STRING  COMMENT 'Source system enum',
  _loaded_at       TIMESTAMP COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_pk EXPECT (Customer_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Customer_Key)
COMMENT 'Conformed customer dimension (Sold-To party from order_partner AG function)'
AS
SELECT
  SHA2(Partner_Number, 256)  AS Customer_Key,
  Partner_Number             AS Customer_Number,
  Partner_Name               AS Customer_Name,
  Country,
  City,
  Postal_Code,
  'SAP_S4'                   AS _source_system,
  current_timestamp()        AS _loaded_at
FROM (
  SELECT
    Partner_Number,
    Partner_Name,
    Country,
    City,
    Postal_Code,
    ROW_NUMBER() OVER (PARTITION BY Partner_Number ORDER BY Order_Number DESC) AS _rn
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_partner
  WHERE Partner_Function = 'AG'
) WHERE _rn = 1;
