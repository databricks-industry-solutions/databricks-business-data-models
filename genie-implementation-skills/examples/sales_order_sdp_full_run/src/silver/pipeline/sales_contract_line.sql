-- sales_contract_line (T2, Materialized View)
-- Material-level commitments within contracts
-- Source: manufacturing_bronze_vibe.sap_sd.veda_item (373 rows)
-- Natural Key: vbeln + posnr
CREATE OR REFRESH MATERIALIZED VIEW sales_contract_line (
  sales_contract_line_id    STRING    COMMENT 'Surrogate PK: SHA2(vbeln|posnr)',
  Contract_Number           STRING    COMMENT 'Parent contract document number',
  Line_Number               STRING    COMMENT 'Item position number',
  Material_Number           STRING    COMMENT 'Material/product code',
  Target_Quantity           DECIMAL(15,3) COMMENT 'Line-level target quantity',
  Target_Value              DECIMAL(15,2) COMMENT 'Line-level target value',
  Net_Price                 DECIMAL(15,2) COMMENT 'Agreed net price',
  sales_contract_id         STRING    COMMENT 'FK to sales_contract',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Contract_Number IS NOT NULL AND Line_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_sales_contract_resolved EXPECT (sales_contract_id IS NOT NULL)
)
CLUSTER BY (sales_contract_id)
COMMENT 'Material-level contract commitments within framework agreements'
AS
SELECT
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(posnr)), 256) AS sales_contract_line_id,
  TRIM(vbeln)                                  AS Contract_Number,
  TRIM(posnr)                                  AS Line_Number,
  TRIM(matnr)                                  AS Material_Number,
  TRY_CAST(zmeng AS DECIMAL(15,3))             AS Target_Quantity,
  TRY_CAST(target_val AS DECIMAL(15,2))        AS Target_Value,
  TRY_CAST(netpr AS DECIMAL(15,2))             AS Net_Price,
  SHA2(TRIM(vbeln), 256)                       AS sales_contract_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  current_timestamp()                          AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.veda_item;
