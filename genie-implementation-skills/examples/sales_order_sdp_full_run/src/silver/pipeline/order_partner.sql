-- order_partner (T4, Materialized View)
-- Partner function assignments per order (sold-to, ship-to, bill-to, payer)
-- Source: manufacturing_bronze_vibe.sap_sd.vbpa (15,000 rows)
-- Natural Key: vbeln + parvw
CREATE OR REFRESH MATERIALIZED VIEW order_partner (
  order_partner_id          STRING    COMMENT 'Surrogate PK: SHA2(vbeln|parvw)',
  Order_Number              STRING    COMMENT 'Parent order document number',
  Partner_Function          STRING    COMMENT 'Partner function code (AG/WE/RE/RG)',
  Partner_Function_Description STRING COMMENT 'Partner function display name',
  Partner_Number            STRING    COMMENT 'Business partner number',
  Partner_Name              STRING    COMMENT 'Partner name',
  Country                   STRING    COMMENT 'Country key',
  City                      STRING    COMMENT 'City name',
  Postal_Code               STRING    COMMENT 'Postal code',
  Address_Number            STRING    COMMENT 'Address reference number',
  order_id                  STRING    COMMENT 'FK to order',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Number IS NOT NULL AND Partner_Function IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_resolved EXPECT (order_id IS NOT NULL)
)
CLUSTER BY (order_id)
COMMENT 'Partner function assignments per sales order'
AS
SELECT
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(parvw)), 256) AS order_partner_id,
  TRIM(vbeln)                                  AS Order_Number,
  TRIM(parvw)                                  AS Partner_Function,
  TRIM(func_desc)                              AS Partner_Function_Description,
  TRIM(kunnr)                                  AS Partner_Number,
  TRIM(name1)                                  AS Partner_Name,
  TRIM(land1)                                  AS Country,
  TRIM(ort01)                                  AS City,
  TRIM(pstlz)                                  AS Postal_Code,
  TRIM(adrnr)                                  AS Address_Number,
  SHA2(TRIM(vbeln), 256)                       AS order_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  current_timestamp()                          AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.vbpa;
