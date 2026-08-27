-- dim_order_reason (G0, Materialized View — passthrough from silver)
-- Reason/rejection code reference dimension
-- Source: manufacturing_silver_vibe.sales_order_silver_sdp.order_reason (9 rows)
-- PK: Order_Reason_Key = order_reason_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_order_reason (
  Order_Reason_Key    STRING  COMMENT 'Surrogate PK (identity from silver order_reason_id)',
  Reason_Code         STRING  COMMENT 'Reason/rejection code',
  Reason_Description  STRING  COMMENT 'Human-readable reason text',
  Reason_Category     STRING  COMMENT 'Reason grouping category',
  Source_System       STRING  COMMENT 'Originating system for this code',
  CONSTRAINT valid_pk EXPECT (Order_Reason_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Order_Reason_Key)
COMMENT 'Standardized reason/rejection code reference dimension'
AS
SELECT
  order_reason_id    AS Order_Reason_Key,
  Reason_Code,
  Reason_Description,
  Reason_Category,
  Source_System
FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_reason;
