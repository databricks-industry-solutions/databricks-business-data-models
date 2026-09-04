-- fact_sales_order_line (G2, Materialized View)
-- Line-item grain fact for revenue, volume, and order analysis
-- Source: silver order_line + order + order_partner (Sold-To AG)
-- Grain: One row per order line item (14,762 rows)
-- PK: Order_Line_Key = order_line_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.fact_sales_order_line (
  Order_Line_Key              STRING        COMMENT 'PK (identity from silver order_line_id)',
  Order_Number                STRING        COMMENT 'Degenerate dim: SAP order document number',
  Line_Number                 STRING        COMMENT 'Degenerate dim: item position number',
  Order_Date_Key              DATE          COMMENT 'FK to dim_date (order creation date)',
  Requested_Delivery_Date_Key DATE          COMMENT 'FK to dim_date (customer-requested delivery)',
  Customer_Key                STRING        COMMENT 'FK to dim_customer (Sold-To AG partner)',
  Material_Key                STRING        COMMENT 'FK to dim_material',
  Sales_Area_Key              STRING        COMMENT 'FK to dim_sales_area',
  Channel_Key                 STRING        COMMENT 'FK to dim_channel',
  Order_Reason_Key            STRING        COMMENT 'FK to dim_order_reason (NULL when no rejection)',
  Order_Type                  STRING        COMMENT 'SAP document type',
  Plant                       STRING        COMMENT 'Delivering plant',
  Overall_Status              STRING        COMMENT 'Overall processing status',
  Item_Category               STRING        COMMENT 'Item category (standard/return/free)',
  PO_Number                   STRING        COMMENT 'Customer purchase order reference',
  Order_Quantity              DECIMAL(15,3) COMMENT 'Ordered quantity',
  Net_Price                   DECIMAL(15,2) COMMENT 'Net price per unit',
  Net_Value                   DECIMAL(15,2) COMMENT 'Line net value',
  Currency                    STRING        COMMENT 'Document currency (ISO)',
  Is_Rejected                 BOOLEAN       COMMENT 'Whether line has a rejection reason',
  _source_system              STRING        COMMENT 'Source system enum',
  _loaded_at                  TIMESTAMP     COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Line_Key IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_date_resolved EXPECT (Order_Date_Key IS NOT NULL),
  CONSTRAINT fk_customer_resolved EXPECT (Customer_Key IS NOT NULL),
  CONSTRAINT fk_material_resolved EXPECT (Material_Key IS NOT NULL)
)
CLUSTER BY (Customer_Key)
COMMENT 'Sales order line-item fact — revenue, volume, and order analysis'
AS
SELECT
  ol.order_line_id                           AS Order_Line_Key,
  o.Order_Number,
  ol.Line_Number,
  o.Order_Date                               AS Order_Date_Key,
  o.Requested_Delivery_Date                  AS Requested_Delivery_Date_Key,
  SHA2(ag.Partner_Number, 256)               AS Customer_Key,
  SHA2(ol.Material_Number, 256)              AS Material_Key,
  o.sales_area_id                            AS Sales_Area_Key,
  SHA2(o.Distribution_Channel, 256)          AS Channel_Key,
  o.order_reason_id                          AS Order_Reason_Key,
  o.Order_Type,
  ol.Plant,
  o.Overall_Status,
  ol.Item_Category,
  o.PO_Number,
  ol.Order_Quantity,
  ol.Net_Price,
  ol.Net_Value,
  o.Currency,
  ol.Rejection_Reason IS NOT NULL            AS Is_Rejected,
  'SAP_S4'                                   AS _source_system,
  current_timestamp()                        AS _loaded_at
FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_line ol
INNER JOIN manufacturing_silver_vibe.sales_order_silver_sdp.`order` o
  ON o.order_id = ol.order_id
LEFT JOIN (
  SELECT order_id, Partner_Number,
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY Order_Number DESC) AS _rn
  FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_partner
  WHERE Partner_Function = 'AG'
) ag ON ag.order_id = ol.order_id AND ag._rn = 1;
