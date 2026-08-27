-- dim_date (G0, Materialized View — Generated Calendar)
-- Standard date dimension covering the full order date range (2024-07-01 to 2026-06-30)
-- Source: Generated via SEQUENCE (no silver source table)
-- PK: Date_Key (DATE type, self-keyed)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.dim_date (
  Date_Key        DATE    COMMENT 'PK — the calendar date',
  Year            INT     COMMENT 'Calendar year',
  Quarter         INT     COMMENT 'Quarter number (1-4)',
  Month           INT     COMMENT 'Month number (1-12)',
  Month_Name      STRING  COMMENT 'Full month name',
  Week_Of_Year    INT     COMMENT 'ISO week number',
  Day_Of_Week     INT     COMMENT 'Day of week (1=Mon, 7=Sun)',
  Day_Name        STRING  COMMENT 'Full day name',
  Is_Weekday      BOOLEAN COMMENT 'Mon-Fri flag',
  Fiscal_Year     INT     COMMENT 'Fiscal year (Jul-Jun)',
  Fiscal_Quarter  INT     COMMENT 'Fiscal quarter',
  Fiscal_Period   STRING  COMMENT 'FY{YY}-Q{Q} label',
  CONSTRAINT valid_pk EXPECT (Date_Key IS NOT NULL) ON VIOLATION DROP ROW
)
CLUSTER BY (Date_Key)
COMMENT 'Generated calendar dimension covering 2024-07-01 to 2026-06-30 (fiscal Jul-Jun)'
AS
SELECT
  date_value                                           AS Date_Key,
  YEAR(date_value)                                     AS Year,
  QUARTER(date_value)                                  AS Quarter,
  MONTH(date_value)                                    AS Month,
  DATE_FORMAT(date_value, 'MMMM')                      AS Month_Name,
  WEEKOFYEAR(date_value)                               AS Week_Of_Year,
  WEEKDAY(date_value) + 1                              AS Day_Of_Week,
  DATE_FORMAT(date_value, 'EEEE')                      AS Day_Name,
  WEEKDAY(date_value) + 1 <= 5                         AS Is_Weekday,
  -- Fiscal year: Jul-Jun (if month >= 7 then current year + 1)
  CASE WHEN MONTH(date_value) >= 7 THEN YEAR(date_value) + 1 ELSE YEAR(date_value) END AS Fiscal_Year,
  -- Fiscal quarter: Jul-Sep=Q1, Oct-Dec=Q2, Jan-Mar=Q3, Apr-Jun=Q4
  CASE
    WHEN MONTH(date_value) IN (7,8,9)   THEN 1
    WHEN MONTH(date_value) IN (10,11,12) THEN 2
    WHEN MONTH(date_value) IN (1,2,3)   THEN 3
    ELSE 4
  END AS Fiscal_Quarter,
  CONCAT(
    'FY',
    SUBSTR(CAST(CASE WHEN MONTH(date_value) >= 7 THEN YEAR(date_value) + 1 ELSE YEAR(date_value) END AS STRING), 3, 2),
    '-Q',
    CAST(CASE
      WHEN MONTH(date_value) IN (7,8,9)   THEN 1
      WHEN MONTH(date_value) IN (10,11,12) THEN 2
      WHEN MONTH(date_value) IN (1,2,3)   THEN 3
      ELSE 4
    END AS STRING)
  ) AS Fiscal_Period
FROM (
  SELECT EXPLODE(SEQUENCE(DATE'2024-07-01', DATE'2026-06-30', INTERVAL 1 DAY)) AS date_value
);
