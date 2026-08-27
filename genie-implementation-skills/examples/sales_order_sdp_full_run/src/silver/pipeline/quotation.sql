-- quotation (T2, Materialized View)
-- Formal sales quotation from CRM
-- Source: manufacturing_bronze_vibe.salesforce_crm.quote (4,000 rows)
-- Natural Key: quote_id (CRM UUID)
CREATE OR REFRESH MATERIALIZED VIEW quotation (
  quotation_id              STRING    COMMENT 'Surrogate PK: SHA2(quote_id)',
  Quote_Number              STRING    COMMENT 'Human-readable quote number',
  Opportunity_Id            STRING    COMMENT 'Source CRM opportunity reference',
  Account_Id                STRING    COMMENT 'CRM account identifier',
  Quote_Date                DATE      COMMENT 'Quotation creation date',
  Status                    STRING    COMMENT 'Quote lifecycle status',
  Valid_Until               DATE      COMMENT 'Quote validity expiration',
  Currency                  STRING    COMMENT 'Quote currency (ISO)',
  Conversion_Probability    DECIMAL(5,2) COMMENT 'Win probability percentage',
  Converted_Order_Number    STRING    COMMENT 'SAP order number if converted',
  Sales_Rep                 STRING    COMMENT 'Assigned sales representative',
  Total_Amount              DECIMAL(15,2) COMMENT 'Total quote value',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (quotation_id IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (quotation_id)
COMMENT 'Formal price/availability proposals to customers (Salesforce CRM)'
AS
SELECT
  SHA2(TRIM(quote_id), 256)                    AS quotation_id,
  TRIM(quote_number)                           AS Quote_Number,
  TRIM(opportunity_id)                         AS Opportunity_Id,
  TRIM(account_id)                             AS Account_Id,
  TRY_TO_DATE(quote_date, 'yyyy-MM-dd')        AS Quote_Date,
  TRIM(status)                                 AS Status,
  TRY_TO_DATE(valid_until, 'yyyy-MM-dd')       AS Valid_Until,
  UPPER(TRIM(currency))                        AS Currency,
  TRY_CAST(conversion_probability AS DECIMAL(5,2)) AS Conversion_Probability,
  NULLIF(TRIM(converted_order_number), '')     AS Converted_Order_Number,
  TRIM(sales_rep)                              AS Sales_Rep,
  TRY_CAST(total_amount AS DECIMAL(15,2))      AS Total_Amount,
  'SALESFORCE'                                 AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(quote_date, 'yyyy-MM-dd') AS TIMESTAMP) AS _source_updated_at
FROM manufacturing_bronze_vibe.salesforce_crm.quote;
