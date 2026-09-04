-- fact_quotation_line (G2, Materialized View)
-- Quote line grain fact for pipeline and conversion analysis
-- Source: silver quotation_line + quotation
-- Grain: One row per quotation line item (11,982 rows)
-- PK: Quotation_Line_Key = quotation_line_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.fact_quotation_line (
  Quotation_Line_Key      STRING        COMMENT 'PK (identity from silver quotation_line_id)',
  Quote_Number            STRING        COMMENT 'Degenerate dim: human-readable quote number',
  Line_Number             STRING        COMMENT 'Degenerate dim: line position within quote',
  Quote_Date_Key          DATE          COMMENT 'FK to dim_date (quotation creation date)',
  Customer_Key            STRING        COMMENT 'FK to dim_customer (SHA2 of Account_Id)',
  Material_Key            STRING        COMMENT 'FK to dim_material (SHA2 of SKU_Code)',
  Quote_Status            STRING        COMMENT 'Quote lifecycle status',
  Is_Converted            BOOLEAN       COMMENT 'Whether quote converted to an order',
  Conversion_Probability  DECIMAL(5,2)  COMMENT 'Win probability percentage',
  Quantity                DECIMAL(15,3) COMMENT 'Quoted quantity',
  List_Price              DECIMAL(15,2) COMMENT 'Catalog list price',
  Discount_Pct            DECIMAL(5,2)  COMMENT 'Applied discount percentage',
  Net_Price               DECIMAL(15,2) COMMENT 'Net price after discount',
  Net_Value               DECIMAL(15,2) COMMENT 'Extended net value (qty x net price)',
  Product_Group           STRING        COMMENT 'Product grouping category',
  Sales_Rep               STRING        COMMENT 'Assigned sales representative',
  _source_system          STRING        COMMENT 'Source system enum',
  _loaded_at              TIMESTAMP     COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_grain EXPECT (Quotation_Line_Key IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_date_resolved EXPECT (Quote_Date_Key IS NOT NULL)
)
CLUSTER BY (Customer_Key)
COMMENT 'Quotation line-item fact — pipeline value, conversion, and discount analysis'
AS
SELECT
  ql.quotation_line_id                       AS Quotation_Line_Key,
  q.Quote_Number,
  ql.Line_Number,
  q.Quote_Date                               AS Quote_Date_Key,
  SHA2(q.Account_Id, 256)                    AS Customer_Key,
  SHA2(ql.SKU_Code, 256)                     AS Material_Key,
  q.Status                                   AS Quote_Status,
  q.Converted_Order_Number IS NOT NULL       AS Is_Converted,
  q.Conversion_Probability,
  ql.Quantity,
  ql.List_Price,
  ql.Discount_Pct,
  ql.Net_Price,
  ql.Net_Value,
  ql.Product_Group,
  q.Sales_Rep,
  'SALESFORCE'                               AS _source_system,
  current_timestamp()                        AS _loaded_at
FROM manufacturing_silver_vibe.sales_order_silver_sdp.quotation_line ql
INNER JOIN manufacturing_silver_vibe.sales_order_silver_sdp.quotation q
  ON q.quotation_id = ql.quotation_id;
