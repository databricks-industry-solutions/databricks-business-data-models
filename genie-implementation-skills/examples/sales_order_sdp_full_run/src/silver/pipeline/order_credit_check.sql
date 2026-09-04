-- order_credit_check (T6, Streaming Table — append-only)
-- Credit limit check results (append-only event log)
-- Source: manufacturing_bronze_vibe.sap_sd.zcredit_log (3,104 rows)
-- Natural Key: vbeln + check_ts
-- Watermark: check_ts
CREATE OR REFRESH STREAMING TABLE order_credit_check (
  order_credit_check_id     STRING    COMMENT 'Surrogate PK: SHA2(vbeln|check_ts)',
  Order_Number              STRING    COMMENT 'Sales order document number',
  Customer_Number           STRING    COMMENT 'Customer being checked',
  Check_Timestamp           TIMESTAMP COMMENT 'Credit check execution timestamp',
  Check_Type                STRING    COMMENT 'Type of credit check performed',
  Credit_Limit              DECIMAL(15,2) COMMENT 'Assigned credit limit (klimk)',
  Exposure_Before           DECIMAL(15,2) COMMENT 'Credit exposure before this order',
  Order_Value               DECIMAL(15,2) COMMENT 'Value of the checked order',
  Exposure_After            DECIMAL(15,2) COMMENT 'Credit exposure after this order',
  Credit_Utilization_Pct    DECIMAL(7,2) COMMENT 'Utilization % (exp_after / klimk * 100)',
  Check_Result              STRING    COMMENT 'Pass/fail/warning outcome',
  Credit_Control_Area       STRING    COMMENT 'Credit control area code',
  Risk_Category             STRING    COMMENT 'Credit risk category',
  order_id                  STRING    COMMENT 'FK to order',
  _source_system            STRING    COMMENT 'Source system enum',
  _loaded_at                TIMESTAMP COMMENT 'Pipeline execution timestamp',
  _created_by               STRING    COMMENT 'Pipeline identity',
  _modified_by              STRING    COMMENT 'Pipeline identity',
  _source_updated_at        TIMESTAMP COMMENT 'Best-available source timestamp',
  CONSTRAINT valid_grain EXPECT (Order_Number IS NOT NULL AND Check_Timestamp IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_order_resolved EXPECT (order_id IS NOT NULL)
)
CLUSTER BY (order_id)
COMMENT 'Credit limit check results per order (append-only event stream)'
AS
SELECT
  SHA2(CONCAT(TRIM(vbeln), '|', TRIM(check_ts)), 256) AS order_credit_check_id,
  TRIM(vbeln)                                  AS Order_Number,
  TRIM(kunnr)                                  AS Customer_Number,
  CAST(TRY_TO_DATE(check_ts, 'yyyyMMdd') AS TIMESTAMP) AS Check_Timestamp,
  TRIM(check_type)                             AS Check_Type,
  TRY_CAST(klimk AS DECIMAL(15,2))             AS Credit_Limit,
  TRY_CAST(exp_before AS DECIMAL(15,2))        AS Exposure_Before,
  TRY_CAST(order_val AS DECIMAL(15,2))         AS Order_Value,
  TRY_CAST(exp_after AS DECIMAL(15,2))         AS Exposure_After,
  CAST(ROUND(
    TRY_CAST(exp_after AS DECIMAL(15,2)) /
    NULLIF(TRY_CAST(klimk AS DECIMAL(15,2)), 0) * 100,
    2
  ) AS DECIMAL(7,2))                           AS Credit_Utilization_Pct,
  TRIM(result)                                 AS Check_Result,
  TRIM(kkber)                                  AS Credit_Control_Area,
  TRIM(ctlpc)                                  AS Risk_Category,
  SHA2(TRIM(vbeln), 256)                       AS order_id,
  'SAP_S4'                                     AS _source_system,
  current_timestamp()                          AS _loaded_at,
  'meridian_sales_order_silver_sdp'            AS _created_by,
  'meridian_sales_order_silver_sdp'            AS _modified_by,
  CAST(TRY_TO_DATE(check_ts, 'yyyyMMdd') AS TIMESTAMP) AS _source_updated_at
FROM STREAM manufacturing_bronze_vibe.sap_sd.zcredit_log;
