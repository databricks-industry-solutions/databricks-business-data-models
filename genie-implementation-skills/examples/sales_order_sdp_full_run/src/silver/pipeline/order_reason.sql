-- order_reason (T0, Materialized View)
-- Standardized reason/rejection code reference (UNION SAP + CRM sources)
-- Sources: sap_sd.tvaut (8 rows) + salesforce_crm.loss_reason_ref (4 rows) → deduped ~9
-- Natural Key: source_system + reason_code
-- Dedup: ROW_NUMBER tiebreaker ORDER BY source_system DESC (SAP_S4 wins over SALESFORCE)
CREATE OR REFRESH MATERIALIZED VIEW order_reason (
  order_reason_id        STRING    COMMENT 'Surrogate PK: SHA2(source_system|reason_code)',
  Reason_Code            STRING    COMMENT 'Reason/rejection code',
  Reason_Description     STRING    COMMENT 'Human-readable reason text',
  Reason_Category        STRING    COMMENT 'Reason grouping category',
  Source_System          STRING    COMMENT 'Originating system for this code',
  _source_system         STRING    COMMENT 'Source system enum',
  _loaded_at             TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by            STRING    COMMENT 'Pipeline identity',
  _modified_by           STRING    COMMENT 'Pipeline identity',
  _source_updated_at     TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Reason_Code IS NOT NULL AND Source_System IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (order_reason_id)
COMMENT 'Standardized reason/rejection code reference (multi-source UNION with SAP priority)'
AS
SELECT
  order_reason_id,
  Reason_Code,
  Reason_Description,
  Reason_Category,
  Source_System,
  Source_System         AS _source_system,
  current_timestamp()   AS _loaded_at,
  'meridian_sales_order_silver_sdp' AS _created_by,
  'meridian_sales_order_silver_sdp' AS _modified_by,
  current_timestamp()   AS _source_updated_at
FROM (
  SELECT
    SHA2(CONCAT(source_system, '|', reason_code), 256) AS order_reason_id,
    reason_code       AS Reason_Code,
    reason_desc       AS Reason_Description,
    category          AS Reason_Category,
    source_system     AS Source_System,
    ROW_NUMBER() OVER (PARTITION BY reason_code ORDER BY source_system DESC) AS _rn
  FROM (
    -- SAP tvaut
    SELECT
      TRIM(augru)   AS reason_code,
      TRIM(bezei)   AS reason_desc,
      TRIM(category) AS category,
      'SAP_S4'      AS source_system
    FROM manufacturing_bronze_vibe.sap_sd.tvaut
    UNION ALL
    -- Salesforce CRM loss_reason_ref
    SELECT
      TRIM(loss_reason_code) AS reason_code,
      TRIM(reason_name)      AS reason_desc,
      TRIM(category)         AS category,
      'SALESFORCE'           AS source_system
    FROM manufacturing_bronze_vibe.salesforce_crm.loss_reason_ref
  )
) WHERE _rn = 1;
