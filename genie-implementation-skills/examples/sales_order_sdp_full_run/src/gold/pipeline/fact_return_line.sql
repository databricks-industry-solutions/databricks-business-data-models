-- fact_return_line (G2, Materialized View)
-- Return line grain fact for reverse logistics and quality analysis
-- Source: silver return_order_line + return_order
-- Grain: One row per return order line item (329 rows)
-- PK: Return_Line_Key = return_order_line_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.fact_return_line (
  Return_Line_Key         STRING        COMMENT 'PK (identity from silver return_order_line_id)',
  RMA_Number              STRING        COMMENT 'Degenerate dim: return merchandise authorization number',
  Line_Number             STRING        COMMENT 'Degenerate dim: line sequence within RMA',
  RMA_Date_Key            DATE          COMMENT 'FK to dim_date (return request date)',
  Customer_Key            STRING        COMMENT 'FK to dim_customer (SHA2 of Customer_Number)',
  Material_Key            STRING        COMMENT 'FK to dim_material (SHA2 of SKU_Code)',
  Order_Reason_Key        STRING        COMMENT 'FK to dim_order_reason (NULL — P1 vocab gap)',
  Original_Order_Number   STRING        COMMENT 'Degenerate dim: original order being returned against',
  Reason_Code             STRING        COMMENT 'Portal return reason code (unmapped)',
  Inspection_Result       STRING        COMMENT 'Inspection outcome',
  Is_Warranty             BOOLEAN       COMMENT 'Whether return is warranty-covered',
  Returned_Quantity       DECIMAL(15,3) COMMENT 'Quantity being returned',
  Credit_Value            DECIMAL(15,2) COMMENT 'Credit value for this line',
  Restocking_Fee          DECIMAL(15,2) COMMENT 'Restocking fee charged',
  Net_Return_Value        DECIMAL(15,2) COMMENT 'Credit_Value - Restocking_Fee',
  _source_system          STRING        COMMENT 'Source system enum',
  _loaded_at              TIMESTAMP     COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_grain EXPECT (Return_Line_Key IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_date_resolved EXPECT (RMA_Date_Key IS NOT NULL),
  CONSTRAINT fk_customer_resolved EXPECT (Customer_Key IS NOT NULL)
)
CLUSTER BY (Customer_Key)
COMMENT 'Return order line-item fact — reverse logistics and quality analysis'
AS
SELECT
  rl.return_order_line_id                    AS Return_Line_Key,
  ro.RMA_Number,
  rl.Line_Number,
  ro.RMA_Date                                AS RMA_Date_Key,
  SHA2(ro.Customer_Number, 256)              AS Customer_Key,
  SHA2(rl.SKU_Code, 256)                     AS Material_Key,
  ro.order_reason_id                         AS Order_Reason_Key,
  ro.Original_Order_Number,
  rl.Reason_Code,
  rl.Inspection_Result,
  rl.Is_Warranty,
  rl.Returned_Quantity,
  rl.Credit_Value,
  rl.Restocking_Fee,
  CAST(COALESCE(rl.Credit_Value, 0) - COALESCE(rl.Restocking_Fee, 0) AS DECIMAL(15,2)) AS Net_Return_Value,
  'RETURNS_PORTAL'                           AS _source_system,
  current_timestamp()                        AS _loaded_at
FROM manufacturing_silver_vibe.sales_order_silver_sdp.return_order_line rl
INNER JOIN manufacturing_silver_vibe.sales_order_silver_sdp.return_order ro
  ON ro.return_order_id = rl.return_order_id;
