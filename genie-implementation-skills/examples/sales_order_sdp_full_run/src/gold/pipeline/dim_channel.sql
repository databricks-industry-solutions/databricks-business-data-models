-- dim_channel (G0, Materialized View — passthrough from silver)
-- Distribution channel business rules dimension
-- Source: manufacturing_silver_vibe.sales_order_silver_sdp.channel_config (4 rows)
-- PK: Channel_Key = channel_config_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_channel (
  Channel_Key             STRING        COMMENT 'Surrogate PK (identity from silver channel_config_id)',
  Distribution_Channel    STRING        COMMENT 'Distribution channel code',
  Channel_Name            STRING        COMMENT 'Channel display name',
  Credit_Check_Required   BOOLEAN       COMMENT 'Whether credit check is mandatory',
  EDI_Capable             BOOLEAN       COMMENT 'Whether channel supports EDI',
  Minimum_Order_Value     DECIMAL(15,2) COMMENT 'Minimum order value threshold',
  CONSTRAINT valid_pk EXPECT (Channel_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Channel_Key)
COMMENT 'Distribution channel business rules and policies'
AS
SELECT
  channel_config_id      AS Channel_Key,
  Distribution_Channel,
  Channel_Name,
  Credit_Check_Required,
  EDI_Capable,
  Minimum_Order_Value
FROM manufacturing_silver_vibe.sales_order_silver_sdp.channel_config;
