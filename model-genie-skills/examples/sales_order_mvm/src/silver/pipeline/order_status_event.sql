CREATE OR REFRESH MATERIALIZED VIEW order_status_event (
  order_status_event_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln|event_seq)',
  order_id BIGINT COMMENT 'FK to order via SHA2(vbeln)',
  event_type STRING COMMENT 'Classifies the nature of the status transition event. Covers the full SAP SD order lifecycle including creation, confirmation, delivery, goods issue, invoicing, cancellation, blocking, and unblocking ',
  event_timestamp TIMESTAMP COMMENT 'Event timestamp (event_timestamp, yyyy-MM-dd format)',
  previous_status STRING COMMENT 'The order status immediately before this transition event. Together with new_status, defines the state transition pair for lifecycle analysis and process mining. [ENUM-REF-CANDIDATE: open|in_process|p',
  new_status STRING COMMENT 'The order status immediately after this transition event. Represents the current state of the sales order following the event. Used in conjunction with previous_status for state machine analysis. [ENU',
  otd_flag STRING COMMENT 'Boolean indicator set to TRUE when goods_issued event occurs on or before the confirmed_delivery_date, and FALSE when delivery is late. Populated only on goods_issued events. Enables direct OTD rate c',
  confirmed_delivery_date DATE COMMENT 'ATP/CTP-confirmed delivery date committed to the customer at the time of this status event. Compared against requested_delivery_date to measure promise gap and against actual_goods_issue_date for OTD ',
  actual_goods_issue_date DATE COMMENT 'Date on which goods were physically issued from the warehouse and shipment was initiated. Populated when event_type is goods_issued. Primary date used in OTD (On-Time Delivery) calculation against con',
  triggered_by_type STRING COMMENT 'Indicates whether the status transition was initiated by a human user, an automated system process, a workflow engine, an integration event, a batch job, or an approval rule. Critical for distinguishi',
  source_system STRING COMMENT 'Originating system identifier (from source)',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_line_key STRING COMMENT 'Natural key from source (vbeln|event_seq); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_line_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_status_event_id)
COMMENT 'Lifecycle status event log for a sales order capturing each status transition as a discrete record. Captures order reference, previous status, new status, event timestamp, event type (order created, o. Grain: order_status_event_id (SHA2 of vbeln|event_seq). Source: sap_sd_mvm.status_log.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|', COALESCE(CAST(s.vbeln AS STRING), '~'), COALESCE(CAST(s.event_seq AS STRING), '~')), 256), 1, 15), 16, 10) AS BIGINT) AS order_status_event_id,
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS order_id,
  s.event_type AS event_type,
  CAST(TRY_TO_DATE(s.event_timestamp, 'yyyy-MM-dd') AS TIMESTAMP) AS event_timestamp,
  s.previous_status AS previous_status,
  s.new_status AS new_status,
  s.otd_flag AS otd_flag,
  TRY_TO_DATE(s.confirmed_delivery_date, 'yyyyMMdd') AS confirmed_delivery_date,
  TRY_TO_DATE(s.actual_goods_issue_date, 'yyyyMMdd') AS actual_goods_issue_date,
  s.triggered_by_type AS triggered_by_type,
  s.source_system AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  CASE WHEN s.vbeln IS NULL OR s.event_seq IS NULL THEN NULL ELSE CONCAT_WS('|', s.vbeln, s.event_seq) END AS source_system_line_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln, event_seq ORDER BY vbeln DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.status_log
) s
WHERE s._rn = 1