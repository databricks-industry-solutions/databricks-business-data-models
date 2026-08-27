-- dim_sales_contract (G1, Materialized View — passthrough from silver)
-- Contract reference dimension for contract-linked order analysis
-- Source: manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract (120 rows)
-- PK: Sales_Contract_Key = sales_contract_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_sales_contract (
  Sales_Contract_Key  STRING        COMMENT 'Surrogate PK (identity from silver sales_contract_id)',
  Contract_Number     STRING        COMMENT 'SAP contract document number',
  Customer_Number     STRING        COMMENT 'Sold-to customer number',
  Contract_Type       STRING        COMMENT 'Contract category (value/quantity)',
  Valid_From          DATE          COMMENT 'Contract validity start',
  Valid_To            DATE          COMMENT 'Contract validity end',
  Target_Quantity     DECIMAL(15,3) COMMENT 'Target quantity commitment',
  Target_Value        DECIMAL(15,2) COMMENT 'Target value commitment',
  Contract_Status     STRING        COMMENT 'Contract lifecycle status',
  CONSTRAINT valid_pk EXPECT (Sales_Contract_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Sales_Contract_Key)
COMMENT 'Framework/blanket purchase agreement reference dimension'
AS
SELECT
  sales_contract_id  AS Sales_Contract_Key,
  Contract_Number,
  Customer_Number,
  Contract_Type,
  Valid_From,
  Valid_To,
  Target_Quantity,
  Target_Value,
  Contract_Status
FROM manufacturing_silver_vibe.sales_order_silver_sdp.sales_contract;
