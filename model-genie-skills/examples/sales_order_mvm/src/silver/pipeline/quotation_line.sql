CREATE OR REFRESH MATERIALIZED VIEW quotation_line (
  quotation_line_id BIGINT COMMENT 'Surrogate PK: SHA2(quote_line_id)',
  quotation_id BIGINT COMMENT 'FK to quotation via SHA2(quote_id)',
  line_number STRING COMMENT 'Sequential position number of this line item within the parent quotation (e.g., 10, 20, 30 in SAP SD convention). Used for ordering and referencing individual line items.',
  sku_code STRING COMMENT 'Material/SKU code from source',
  material_description STRING COMMENT 'Short descriptive text of the material or product being quoted, as sourced from the product catalog or PLM system. Provides human-readable product identification on the quotation line.',
  quantity DECIMAL(18,4) COMMENT 'Quoted quantity',
  unit_of_measure STRING COMMENT 'Sales unit of measure in which the quoted quantity is expressed (e.g., EA for each, KG for kilogram, M for meter). Aligns with ISO 80000 standard units. [ENUM-REF-CANDIDATE: EA|PC|KG|M|M2|M3|L|SET|BOX',
  list_price DECIMAL(18,4) COMMENT 'Standard published list price per unit for the quoted SKU before any discounts or surcharges are applied. Sourced from the pricing condition master in SAP SD or Salesforce CPQ.',
  discount_percent DECIMAL(18,2) COMMENT 'Discount percentage',
  net_price DECIMAL(18,4) COMMENT 'Net unit price',
  net_value DECIMAL(18,2) COMMENT 'Total net commercial value of this quotation line, calculated as quoted net price multiplied by quoted quantity plus applicable surcharges. Represents the line-level revenue commitment in the quotatio',
  product_group STRING COMMENT 'Product family or category grouping to which the quoted SKU belongs (e.g., Automation Systems, Electrification Solutions, Smart Infrastructure). Supports revenue analysis by product line.',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system STRING COMMENT 'Originating system identifier',
  source_system_key STRING COMMENT 'Natural key from source (quote_line_id); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (quotation_line_id)
COMMENT 'Individual line item within a sales quotation capturing the product-level pricing detail for each SKU or configurable product quoted. Captures line number, material/SKU reference, quoted quantity, uni. Grain: quotation_line_id (SHA2 of quote_line_id). Source: salesforce_crm_mvm.quote_line.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.quote_line_id AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS quotation_line_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.quote_id AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS quotation_id,
  s.line_number AS line_number,
  s.sku_code AS sku_code,
  s.material_description AS material_description,
  TRY_CAST(s.quantity AS DECIMAL(18,4)) AS quantity,
  s.uom AS unit_of_measure,
  TRY_CAST(s.list_price AS DECIMAL(18,4)) AS list_price,
  TRY_CAST(s.discount_pct AS DECIMAL(18,2)) AS discount_percent,
  TRY_CAST(s.net_price AS DECIMAL(18,4)) AS net_price,
  TRY_CAST(s.net_value AS DECIMAL(18,2)) AS net_value,
  s.product_group AS product_group,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SALESFORCE_CRM' AS source_system,
  s.quote_line_id AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY quote_line_id ORDER BY quote_line_id DESC) AS _rn
  FROM manufacturing_bronze_vibe.salesforce_crm_mvm.quote_line
) s
WHERE s._rn = 1