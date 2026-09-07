CREATE OR REFRESH MATERIALIZED VIEW delivery (
  delivery_id BIGINT COMMENT 'Surrogate PK: SHA2(vbeln_delivery)',
  order_id BIGINT COMMENT 'FK to order via vbeln_order JOIN',
  delivery_number STRING COMMENT 'Natural key (vbeln_delivery)',
  order_number STRING COMMENT 'Order number from source (vbeln_order)',
  planned_delivery_date DATE COMMENT 'Planned delivery date',
  actual_goods_issue_date DATE COMMENT 'Actual goods issue date',
  shipping_point_code STRING COMMENT 'Shipping point code',
  transportation_type_code STRING COMMENT 'Transportation type code',
  route_code STRING COMMENT 'Route code',
  source_system STRING COMMENT 'Originating system identifier (from source)',
  created_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  last_modified_timestamp TIMESTAMP COMMENT 'ETL audit timestamp',
  source_system_key STRING COMMENT 'Natural key from source (vbeln_delivery); NULL when key is missing -- grain guard column.',
  CONSTRAINT valid_pk EXPECT (source_system_key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (delivery_id)
COMMENT 'Outbound delivery document tracking physical shipment of goods against a sales order. Captures delivery number, shipping point, planned and actual goods issue dates, transportation type, and route.. Grain: delivery_id (SHA2 of vbeln_delivery). Source: sap_sd_mvm.likp. Net-new entity from discovery.'
AS
SELECT
  CAST(CONV(SUBSTRING(SHA2(COALESCE(CAST(s.vbeln_delivery AS STRING), '~'), 256), 1, 15), 16, 10) AS BIGINT) AS delivery_id,
  o.order_id AS order_id,
  s.vbeln_delivery AS delivery_number,
  s.vbeln_order AS order_number,
  TRY_TO_DATE(s.lfdat, 'yyyyMMdd') AS planned_delivery_date,
  TRY_TO_DATE(s.wadat_ist, 'yyyyMMdd') AS actual_goods_issue_date,
  s.vstel AS shipping_point_code,
  s.traty AS transportation_type_code,
  s.route AS route_code,
  s.source_system AS source_system,
  CURRENT_TIMESTAMP() AS created_timestamp,
  CURRENT_TIMESTAMP() AS last_modified_timestamp,
  s.vbeln_delivery AS source_system_key
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY vbeln_delivery ORDER BY vbeln_delivery DESC) AS _rn
  FROM manufacturing_bronze_vibe.sap_sd_mvm.likp
) s
LEFT JOIN (
  SELECT order_id, order_number,
         ROW_NUMBER() OVER (PARTITION BY order_number ORDER BY order_id DESC) AS _fk_rn
  FROM `order`
) o ON o.order_number = s.vbeln_order AND o._fk_rn = 1
WHERE s._rn = 1