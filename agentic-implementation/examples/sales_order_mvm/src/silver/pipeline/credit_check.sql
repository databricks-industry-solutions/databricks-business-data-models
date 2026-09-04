CREATE OR REFRESH MATERIALIZED VIEW credit_check (
  credit_check_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|check_ts)',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  order_number STRING COMMENT 'Order number from source (vbeln)',
  customer_account_number STRING COMMENT 'Customer account number (kunnr)',
  account_id BIGINT COMMENT 'FK to customer.account (deferred).',
  check_timestamp TIMESTAMP COMMENT 'Credit check timestamp (check_ts, yyyyMMdd format)',
  check_type STRING COMMENT 'Credit check type',
  credit_limit DECIMAL(18,2) COMMENT 'Credit limit',
  exposure_before DECIMAL(18,2) COMMENT 'Exposure before check',
  order_value DECIMAL(18,2) COMMENT 'Order value at check time',
  exposure_after DECIMAL(18,2) COMMENT 'Exposure after check',
  check_result STRING COMMENT 'Credit check result',
  credit_control_area STRING COMMENT 'Credit control area',
  credit_control_point STRING COMMENT 'Credit control point',
  source_system STRING COMMENT 'Originating system identifier',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|check_ts); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (credit_check_id)
COMMENT 'Credit management check event capturing the outcome of each credit evaluation during sales order processing. Captures credit limit, exposure before/after, order value, check result, credit control area.. Grain: credit_check_id (SHA2 of vbeln|check_ts). Source: sap_sd_mvm.zcredit_log. Net-new entity from discovery.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.check_ts AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS credit_check_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  s.vbeln AS order_number,
  s.kunnr AS customer_account_number,
  CAST(NULL AS BIGINT) AS account_id,
  CAST(TRY_TO_DATE(s.check_ts, 'yyyyMMdd') AS TIMESTAMP) AS check_timestamp,
  s.check_type AS check_type,
  TRY_CAST(s.klimk AS DECIMAL(18,2)) AS credit_limit,
  TRY_CAST(s.exp_before AS DECIMAL(18,2)) AS exposure_before,
  TRY_CAST(s.order_val AS DECIMAL(18,2)) AS order_value,
  TRY_CAST(s.exp_after AS DECIMAL(18,2)) AS exposure_after,
  s.result AS check_result,
  s.kkber AS credit_control_area,
  s.ctlpc AS credit_control_point,
  'SAP_SD' AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  CASE WHEN s.vbeln IS NULL OR s.check_ts IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.check_ts) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, check_ts ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.zcredit_log
) s
WHERE s._rn = 1