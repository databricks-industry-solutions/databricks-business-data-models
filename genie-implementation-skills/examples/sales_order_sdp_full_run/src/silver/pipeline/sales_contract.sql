-- sales_contract (T1, Materialized View)
-- Framework/blanket purchase agreements with customers
-- Source: manufacturing_bronze_vibe.sap_sd.veda (120 rows)
-- Natural Key: vbeln
CREATE OR REFRESH MATERIALIZED VIEW sales_contract (
  sales_contract_id         STRING    COMMENT 'Surrogate PK: SHA2(vbeln)',
  Contract_Number           STRING    COMMENT 'SAP contract document number',
  Customer_Number           STRING    COMMENT 'Sold-to customer number',
  Distribution_Channel      STRING    COMMENT 'Distribution channel code',
  Contract_Type             STRING    COMMENT 'Contract category (value/quantity)',
  Valid_From                DATE      COMMENT 'Contract validity start',
  Valid_To                  DATE      COMMENT 'Contract validity end',
  Target_Quantity           DECIMAL(15,3) COMMENT 'Target quantity commitment',
  Target_Value              DECIMAL(15,2) COMMENT 'Target value commitment',
  Contract_Status           STRING    COMMENT 'Contract lifecycle status',
  sales_area_id             STRING    COMMENT 'FK to sales_area',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Contract_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_sales_area_resolved EXPECT (sales_area_id IS NOT NULL)
)
CLUSTER BY (sales_contract_id)
COMMENT 'Framework/blanket purchase agreements with customers'
AS
SELECT
  SHA2(TRIM(vbeln), 256)                       AS sales_contract_id,
  TRIM(vbeln)                                  AS Contract_Number,
  TRIM(kunnr)                                  AS Customer_Number,
  TRIM(vtweg)                                  AS Distribution_Channel,
  TRIM(kbtyp)                                  AS Contract_Type,
  TRY_TO_DATE(vbegdat, 'yyyyMMdd')             AS Valid_From,
  TRY_TO_DATE(venddat, 'yyyyMMdd')             AS Valid_To,
  TRY_CAST(zmeng AS DECIMAL(15,3))             AS Target_Quantity,
  TRY_CAST(target_val AS DECIMAL(15,2))        AS Target_Value,
  TRIM(vstat)                                  AS Contract_Status,
  -- FK: sales_area_id — veda has vtweg but lacks vkorg/spart; resolve where possible
  CAST(NULL AS STRING)                         AS sales_area_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(vbegdat, 'yyyyMMdd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.veda;
