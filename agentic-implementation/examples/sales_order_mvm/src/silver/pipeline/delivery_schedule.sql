CREATE OR REFRESH MATERIALIZED VIEW delivery_schedule (
  delivery_schedule_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|schedule_number)',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  sales_contract_id BIGINT COMMENT 'FK to sales_contract via contract_number JOIN',
  contract_number STRING COMMENT 'Contract number from source',
  schedule_type STRING COMMENT 'Classification of the delivery schedule indicating the replenishment or delivery call-off mechanism: forecast-based, Just-in-Time (JIT), Just-in-Sequence (JIS), Kanban-triggered, blanket order, or con',
  schedule_status STRING COMMENT 'Current lifecycle status of the delivery schedule record, controlling whether new schedule lines can be created and deliveries executed against it.. Valid values are `active|suspended|closed|cancelled',
  horizon_start_date DATE COMMENT 'Start date of the planning horizon covered by this delivery schedule, defining the earliest date for which delivery requirements are communicated to the plant.',
  horizon_end_date DATE COMMENT 'End date of the planning horizon covered by this delivery schedule, defining the latest date for which delivery requirements are currently planned.',
  open_quantity DECIMAL(18,4) COMMENT 'Remaining quantity yet to be delivered under the current schedule horizon, calculated as the difference between scheduled quantity and delivered quantity for the active planning period.',
  quantity_unit STRING COMMENT 'Unit of measure applicable to all quantity fields on this delivery schedule (cumulative ordered, cumulative delivered, open quantity). Follows ISO 80000 unit codes. [ENUM-REF-CANDIDATE: EA|PC|KG|LB|M|',
  source_system STRING COMMENT 'Originating system identifier (from source)',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|schedule_number); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (delivery_schedule_id)
COMMENT 'Delivery schedule master record associated with a scheduling agreement or blanket order, defining the planned delivery cadence for a customer-material combination over a planning horizon. Captures sch. Grain: delivery_schedule_id (SHA2 of vbeln|schedule_number). Source: sap_sd_mvm.sched_agreement.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.schedule_number AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS delivery_schedule_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  sc.sales_contract_id AS sales_contract_id,
  s.contract_number AS contract_number,
  s.schedule_type AS schedule_type,
  s.schedule_status AS schedule_status,
  TRY_TO_DATE(s.horizon_start_date, 'yyyyMMdd') AS horizon_start_date,
  TRY_TO_DATE(s.horizon_end_date, 'yyyyMMdd') AS horizon_end_date,
  TRY_CAST(s.open_quantity AS DECIMAL(18,4)) AS open_quantity,
  s.quantity_unit AS quantity_unit,
  s.source_system AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  CASE WHEN s.vbeln IS NULL OR s.schedule_number IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.schedule_number) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, schedule_number ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.sched_agreement
) s
LEFT JOIN (
  SELECT sales_contract_id, contract_number,
         ROW_NUMBER() OVER (PARTITION BY contract_number ORDER BY sales_contract_id DESC) AS _fk_rn
  FROM sales_contract
) sc ON sc.contract_number = s.contract_number AND sc._fk_rn = 1
WHERE s._rn = 1