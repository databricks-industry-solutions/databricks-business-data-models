CREATE OR REFRESH MATERIALIZED VIEW sales_contract (
  sales_contract_id           BIGINT        COMMENT 'Surrogate primary key uniquely identifying a sales contract record in the lakehouse silver layer.',
  contract_number             STRING        COMMENT 'Natural business key for the sales contract as assigned by the source system (SAP SD contract document number).',
  customer_account_number     STRING        COMMENT 'SAP SD customer account number for the customer party to the contract. Sourced from veda.kunnr.',
  distribution_channel_code   STRING        COMMENT 'SAP SD distribution channel code indicating the route to market for the contract. Sourced from veda.vtweg.',
  contract_type_code          STRING        COMMENT 'Code classifying the commercial agreement structure. Sourced from veda.kbtyp.',
  valid_from                  DATE          COMMENT 'Calendar date on which the sales contract becomes effective and release orders may be placed against it. Sourced from veda.vbegdat (yyyyMMdd format).',
  valid_to                    DATE          COMMENT 'Calendar date on which the sales contract expires and no further release orders may be placed. Sourced from veda.venddat (yyyyMMdd format).',
  target_quantity             DECIMAL(18,4) COMMENT 'Total committed volume (in the contract unit of measure) that the customer agrees to purchase over the contract period.',
  target_value                DECIMAL(18,2) COMMENT 'Total committed monetary value the customer agrees to spend over the contract period.',
  contract_status             STRING        COMMENT 'Current lifecycle status of the sales contract. Drives order promising, ATP/CTP checks, and revenue recognition eligibility.',
  created_timestamp           TIMESTAMP     COMMENT 'Timestamp when the sales contract record was first created in the source system. Used for audit trail and pipeline age tracking.',
  last_modified_timestamp     TIMESTAMP     COMMENT 'Timestamp of the most recent change to the sales contract record in the source system.',
  source_system               STRING        COMMENT 'Identifies the originating operational system of record from which this sales contract was ingested.',
  source_system_key           STRING        COMMENT 'Natural key from source (vbeln); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (sales_contract_id)
COMMENT 'One row per sales contract. Grain: sales_contract_id (SHA2 of vbeln). Source: sap_sd_mvm.veda.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS sales_contract_id,
  vbeln AS contract_number,
  kunnr AS customer_account_number,
  vtweg AS distribution_channel_code,
  kbtyp AS contract_type_code,
  TRY_TO_DATE(vbegdat, 'yyyyMMdd') AS valid_from,
  TRY_TO_DATE(venddat, 'yyyyMMdd') AS valid_to,
  TRY_CAST(zmeng AS DECIMAL(18,4)) AS target_quantity,
  TRY_CAST(target_val AS DECIMAL(18,2)) AS target_value,
  vstat AS contract_status,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  'SAP_SD' AS source_system,
  vbeln AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.veda
) WHERE _rn = 1