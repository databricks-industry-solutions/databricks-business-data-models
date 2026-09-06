CREATE OR REFRESH MATERIALIZED VIEW `order` (
  order_id BIGINT COMMENT 'Surrogate primary key uniquely identifying a sales order record in the lakehouse silver layer. System-generated BIGINT used as the canonical identifier across all downstream joins.',
  order_number STRING COMMENT 'Natural key',
  order_date DATE COMMENT 'The calendar date on which the sales order was created and confirmed in the source system. Serves as the commercial commitment date for revenue recognition and OTD baseline calculations.',
  requested_delivery_date DATE COMMENT 'The delivery date requested by the customer at the time of order placement. Used as the baseline for On-Time Delivery (OTD) performance measurement and ATP/CTP promising.',
  document_date DATE COMMENT 'Document date of the sales order in the source system (SAP audat). Typically the creation date; used for aging and period-reporting alongside order_date.',
  net_value DECIMAL(18,2) COMMENT 'Total net commercial value of the sales order after discounts and before taxes, expressed in the order currency. Represents the revenue commitment for this order. Used for revenue recognition, forecasting, and order-value reporting.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the order is denominated (e.g., USD, EUR, GBP). Used for multi-currency financial consolidation and FX reporting.. Valid values are `^[A-Z]{3}$`',
  order_type_code STRING COMMENT 'SAP SD order type code',
  distribution_channel_code STRING COMMENT 'SAP SD distribution channel',
  sales_organization_code STRING COMMENT 'SAP SD sales organization',
  division_code STRING COMMENT 'SAP SD division',
  customer_account_number STRING COMMENT 'Customer account number',
  plant_code STRING COMMENT 'Plant code',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms 2020) code defining the transfer of risk, cost, and responsibility between seller and buyer for the shipment. Governs logistics obligations and revenue recognition timing.',
  payment_terms_code STRING COMMENT 'Code identifying the agreed payment terms for the order (e.g., NET30, NET60, 2/10NET30). Drives accounts receivable due date calculation and cash flow forecasting.',
  overall_status STRING COMMENT 'Overall processing status',
  rejection_reason_code STRING COMMENT 'Rejection reason',
  customer_po_number STRING COMMENT 'Customer PO number',
  shipping_condition_code STRING COMMENT 'Shipping condition',
  quotation_id BIGINT COMMENT 'FK to quotation via converted_order_reference JOIN',
  sales_contract_id BIGINT COMMENT 'FK to sales_contract via contract_number JOIN',
  account_id BIGINT COMMENT 'FK to customer.account (deferred).',
  plant_id BIGINT COMMENT 'FK to manufacturing.plant (deferred).',
  contract_id BIGINT COMMENT 'FK to billing.contract (deferred).',
  price_list_id BIGINT COMMENT 'FK to pricing.price_list (deferred).',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_key STRING COMMENT 'Natural key from source (vbeln); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_id)
COMMENT 'Core sales order master record representing a confirmed commercial commitment from a B2B customer to purchase products or services. Captures order number, order type (standard, blanket, consignment, i. Grain: order_id (SHA2 of vbeln). Source: sap_sd_mvm.vbak. Reserved keyword: backtick-escaped.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  s.vbeln AS order_number,
  TRY_TO_DATE(s.erdat, 'yyyyMMdd') AS order_date,
  TRY_TO_DATE(s.vdatu, 'yyyyMMdd') AS requested_delivery_date,
  TRY_TO_DATE(s.audat, 'yyyyMMdd') AS document_date,
  TRY_CAST(s.netwr AS DECIMAL(18,2)) AS net_value,
  s.waerk AS currency_code,
  s.auart AS order_type_code,
  s.vtweg AS distribution_channel_code,
  s.vkorg AS sales_organization_code,
  s.spart AS division_code,
  s.kunnr AS customer_account_number,
  s.werks AS plant_code,
  s.inco1 AS incoterms_code,
  s.zterm AS payment_terms_code,
  s.gbstk AS overall_status,
  s.augru AS rejection_reason_code,
  s.bstnk AS customer_po_number,
  s.vsbed AS shipping_condition_code,
  q.quotation_id AS quotation_id,
  sc.sales_contract_id AS sales_contract_id,
  CAST(NULL AS BIGINT) AS account_id,
  CAST(NULL AS BIGINT) AS plant_id,
  CAST(NULL AS BIGINT) AS contract_id,
  CAST(NULL AS BIGINT) AS price_list_id,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SAP_SD' AS source_system,
  s.vbeln AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.vbak
) s
LEFT JOIN (
  SELECT quotation_id, converted_order_reference,
         ROW_NUMBER() OVER (PARTITION BY converted_order_reference ORDER BY quotation_id DESC) AS _fk_rn
  FROM quotation
) q ON q.converted_order_reference = s.vbeln AND q._fk_rn = 1
LEFT JOIN (
  SELECT sales_contract_id, contract_number,
         ROW_NUMBER() OVER (PARTITION BY contract_number ORDER BY sales_contract_id DESC) AS _fk_rn
  FROM sales_contract
) sc ON sc.contract_number = s.vbeln AND sc._fk_rn = 1
WHERE s._rn = 1