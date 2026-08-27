-- channel_config (T1, Materialized View)
-- Channel business rules and policies per distribution channel
-- Source: manufacturing_bronze_vibe.sap_sd.zsd_channel_config (4 rows)
-- Natural Key: vtweg
-- FK: sales_area_id = NULL (zsd_channel_config lacks vkorg/spart)
CREATE OR REFRESH MATERIALIZED VIEW channel_config (
  channel_config_id         STRING    COMMENT 'Surrogate PK: SHA2(vtweg)',
  Distribution_Channel      STRING    COMMENT 'Distribution channel code',
  Channel_Name              STRING    COMMENT 'Channel display name',
  Credit_Check_Required     BOOLEAN   COMMENT 'Whether credit check is mandatory',
  EDI_Capable               BOOLEAN   COMMENT 'Whether channel supports EDI',
  Minimum_Order_Value       DECIMAL(15,2) COMMENT 'Minimum order value threshold',
  Pricing_Procedure         STRING    COMMENT 'Pricing procedure assignment',
  Payment_Terms             STRING    COMMENT 'Default payment terms',
  Incoterms                 STRING    COMMENT 'Default incoterms',
  sales_area_id             STRING    COMMENT 'FK to sales_area (NULL — source lacks vkorg/spart)',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Distribution_Channel IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_sales_area_resolved EXPECT (sales_area_id IS NOT NULL)
)
CLUSTER BY (channel_config_id)
COMMENT 'Channel business rules, pricing procedures, and credit requirements'
AS
SELECT
  SHA2(TRIM(vtweg), 256)                       AS channel_config_id,
  TRIM(vtweg)                                  AS Distribution_Channel,
  TRIM(chan_name)                               AS Channel_Name,
  CASE UPPER(TRIM(credit_check_req))
    WHEN 'TRUE' THEN TRUE WHEN 'YES' THEN TRUE
    WHEN 'FALSE' THEN FALSE WHEN 'NO' THEN FALSE
    ELSE NULL END                               AS Credit_Check_Required,
  CASE UPPER(TRIM(edi_capable))
    WHEN 'TRUE' THEN TRUE WHEN 'YES' THEN TRUE
    WHEN 'FALSE' THEN FALSE WHEN 'NO' THEN FALSE
    ELSE NULL END                               AS EDI_Capable,
  TRY_CAST(min_order_val AS DECIMAL(15,2))     AS Minimum_Order_Value,
  TRIM(pricing_proc)                           AS Pricing_Procedure,
  TRIM(pay_terms)                              AS Payment_Terms,
  TRIM(inco)                                   AS Incoterms,
  CAST(NULL AS STRING)                         AS sales_area_id,  -- source lacks vkorg/spart
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  current_timestamp()                          AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.zsd_channel_config;
