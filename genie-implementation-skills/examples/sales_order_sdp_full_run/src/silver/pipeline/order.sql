-- order (T3, Materialized View)
-- Core confirmed B2B sales order headers
-- Source: manufacturing_bronze_vibe.sap_sd.vbak (5,000 rows)
-- Natural Key: vbeln
-- FK: sales_area_id (100%), order_reason_id (when augru populated), quotation_id (~19.9% via converted_order_number)
CREATE OR REFRESH MATERIALIZED VIEW `order` (
  order_id                  STRING    COMMENT 'Surrogate PK: SHA2(vbeln)',
  Order_Number              STRING    COMMENT 'SAP sales document number',
  Order_Type                STRING    COMMENT 'SAP document type (auart)',
  Distribution_Channel      STRING    COMMENT 'Distribution channel code',
  Sales_Organization        STRING    COMMENT 'Sales organization code',
  Division                  STRING    COMMENT 'Product division code',
  Customer_Number           STRING    COMMENT 'Sold-to customer number',
  Plant                     STRING    COMMENT 'Delivering plant',
  Order_Date                DATE      COMMENT 'Order creation date',
  Requested_Delivery_Date   DATE      COMMENT 'Customer-requested delivery date',
  Pricing_Date              DATE      COMMENT 'Date for pricing determination',
  Net_Value                 DECIMAL(15,2) COMMENT 'Order net value',
  Currency                  STRING    COMMENT 'Document currency (ISO)',
  Incoterms                 STRING    COMMENT 'Delivery terms',
  Payment_Terms             STRING    COMMENT 'Payment terms key',
  Overall_Status            STRING    COMMENT 'Overall processing status',
  Rejection_Reason          STRING    COMMENT 'Order-level rejection reason code',
  PO_Number                 STRING    COMMENT 'Customer purchase order reference',
  Shipping_Conditions       STRING    COMMENT 'Shipping conditions code',
  sales_area_id             STRING    COMMENT 'FK to sales_area',
  order_reason_id           STRING    COMMENT 'FK to order_reason (NULL when no rejection)',
  quotation_id              STRING    COMMENT 'FK to quotation (~19.9% resolved via converted_order_number)',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Number IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_sales_area_resolved EXPECT (sales_area_id IS NOT NULL),
  CONSTRAINT fk_quotation_resolved EXPECT (quotation_id IS NOT NULL)
)
CLUSTER BY (order_id)
COMMENT 'Core confirmed B2B sales order headers from SAP SD'
AS
SELECT
  SHA2(TRIM(o.vbeln), 256)                     AS order_id,
  TRIM(o.vbeln)                                AS Order_Number,
  TRIM(o.auart)                                AS Order_Type,
  TRIM(o.vtweg)                                AS Distribution_Channel,
  TRIM(o.vkorg)                                AS Sales_Organization,
  TRIM(o.spart)                                AS Division,
  TRIM(o.kunnr)                                AS Customer_Number,
  TRIM(o.werks)                                AS Plant,
  TRY_TO_DATE(o.erdat, 'yyyyMMdd')             AS Order_Date,
  TRY_TO_DATE(o.vdatu, 'yyyyMMdd')             AS Requested_Delivery_Date,
  TRY_TO_DATE(o.audat, 'yyyyMMdd')             AS Pricing_Date,
  TRY_CAST(o.netwr AS DECIMAL(15,2))           AS Net_Value,
  UPPER(TRIM(o.waerk))                         AS Currency,
  TRIM(o.inco1)                                AS Incoterms,
  TRIM(o.zterm)                                AS Payment_Terms,
  TRIM(o.gbstk)                                AS Overall_Status,
  TRIM(o.augru)                                AS Rejection_Reason,
  TRIM(o.bstnk)                                AS PO_Number,
  TRIM(o.vsbed)                                AS Shipping_Conditions,
  -- FK: sales_area_id
  SHA2(CONCAT(TRIM(o.vkorg), '|', TRIM(o.vtweg), '|', TRIM(o.spart)), 256) AS sales_area_id,
  -- FK: order_reason_id (only when augru populated)
  CASE WHEN NULLIF(TRIM(o.augru), '') IS NOT NULL
    THEN SHA2(CONCAT('SAP_S4', '|', TRIM(o.augru)), 256)
    ELSE NULL END                              AS order_reason_id,
  -- FK: quotation_id (~19.9% resolved via quote.converted_order_number matching vbeln)
  q.quotation_id                               AS quotation_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(o.erdat, 'yyyyMMdd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.sap_sd.vbak o
LEFT JOIN (
  SELECT
    SHA2(TRIM(quote_id), 256) AS quotation_id,
    TRIM(converted_order_number) AS converted_order_number
  FROM (
    SELECT *,
      ROW_NUMBER() OVER (PARTITION BY TRIM(converted_order_number) ORDER BY quote_date DESC) AS _rn
    FROM manufacturing_bronze_vibe.salesforce_crm.quote
    WHERE NULLIF(TRIM(converted_order_number), '') IS NOT NULL
  ) WHERE _rn = 1
) q ON q.converted_order_number = TRIM(o.vbeln);
