CREATE OR REFRESH MATERIALIZED VIEW quotation (
  quotation_id BIGINT COMMENT 'Surrogate primary key uniquely identifying a sales quotation record in the lakehouse silver layer.',
  number STRING COMMENT 'Business-facing natural key for the quotation as assigned by the source system (SAP SD or Salesforce CRM). Used for cross-system traceability and customer-facing references.. Valid values are `^[A-Z0-',
  quotation_date DATE COMMENT 'Calendar date on which the quotation was formally created and issued to the prospective customer. Used as the baseline date for validity period calculations and pipeline aging.',
  quotation_status STRING COMMENT 'Current lifecycle status of the sales quotation. Converted indicates the quotation has been accepted and a sales order has been created. Drives pipeline reporting and win/loss analytics.. Valid values',
  conversion_probability DECIMAL(18,2) COMMENT 'Estimated probability (0.00–100.00%) that this quotation will be accepted and converted to a sales order. Used in weighted pipeline forecasting and APS demand signal generation.',
  converted_order_reference STRING COMMENT 'Reference number of the sales order created upon acceptance of this quotation. Populated when quotation_status transitions to converted. Enables end-to-end quote-to-order traceability.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the quotation value is denominated (e.g., USD, EUR, GBP). Required for multi-currency reporting and FX conversion in financial consolidation.. Valid values',
  quoted_value DECIMAL(18,2) COMMENT 'Total net commercial value of the quotation in the transaction currency, representing the sum of all line items before tax. Core metric for pipeline valuation, revenue forecasting, and win/loss analys',
  opportunity_reference STRING COMMENT 'Reference identifier of the linked CRM opportunity from which this quotation was generated. Enables traceability from opportunity through quotation to sales order in the quote-to-order workflow.',
  account_id BIGINT COMMENT 'FK to customer.account (deferred -- cross-domain).',
  price_list_id BIGINT COMMENT 'FK to pricing.price_list (deferred -- cross-domain).',
  sales_contract_id BIGINT COMMENT 'FK to sales_contract (deferred -- not in source).',
  created_timestamp TIMESTAMP COMMENT 'Date and time when the quotation record was first created in the source system. Used for pipeline aging, SLA compliance, and audit trail.',
  last_modified_timestamp TIMESTAMP COMMENT 'Date and time of the most recent modification to the quotation record in the source system. Supports change detection, incremental data loading, and audit compliance.',
  source_system STRING COMMENT 'Identifies the originating operational system of record for this quotation record, supporting SSOT governance across multi-ERP and multi-CRM landscapes resulting from M&A activity. Per VREQ-004, a sin',
  source_system_key STRING COMMENT 'Natural key from source (quote_id); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (quotation_id)
COMMENT 'Sales quotation master record representing a formal price offer presented to a B2B customer prior to order placement. Captures quotation number, quotation date, valid-from date, valid-to date, quotati. Grain: quotation_id (SHA2 of quote_id). Source: salesforce_crm_mvm.quote.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.quote_id AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS quotation_id,
  s.quote_number AS number,
  TRY_TO_DATE(s.quote_date, 'yyyy-MM-dd') AS quotation_date,
  s.status AS quotation_status,
  TRY_CAST(s.conversion_probability AS DECIMAL(18,2)) AS conversion_probability,
  s.converted_order_number AS converted_order_reference,
  s.currency AS currency_code,
  TRY_CAST(s.total_amount AS DECIMAL(18,2)) AS quoted_value,
  s.opportunity_id AS opportunity_reference,
  CAST(NULL AS BIGINT) AS account_id,
  CAST(NULL AS BIGINT) AS price_list_id,
  CAST(NULL AS BIGINT) AS sales_contract_id,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SALESFORCE_CRM' AS source_system,
  s.quote_id AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY quote_id ORDER BY quote_id DESC) AS _rn
  FROM manufacturing_bronze_vibe.salesforce_crm_mvm.quote
) s
WHERE s._rn = 1