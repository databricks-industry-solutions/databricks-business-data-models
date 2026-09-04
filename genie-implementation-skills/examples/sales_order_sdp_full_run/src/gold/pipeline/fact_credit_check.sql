-- fact_credit_check (G2, Materialized View)
-- Credit check event grain fact for credit exposure and risk monitoring
-- Source: silver order_credit_check + order
-- Grain: One row per credit check event (3,104 rows)
-- PK: Credit_Check_Key = order_credit_check_id (identity from silver)
CREATE OR REFRESH MATERIALIZED VIEW manufacturing_silver_vibe.sales_order_gold_sdp.fact_credit_check (
  Credit_Check_Key        STRING        COMMENT 'PK (identity from silver order_credit_check_id)',
  Order_Number            STRING        COMMENT 'Degenerate dim: sales order document number',
  Check_Date_Key          DATE          COMMENT 'FK to dim_date (credit check date)',
  Customer_Key            STRING        COMMENT 'FK to dim_customer (SHA2 of Customer_Number)',
  Sales_Area_Key          STRING        COMMENT 'FK to dim_sales_area (via order)',
  Check_Type              STRING        COMMENT 'Type of credit check performed',
  Check_Result            STRING        COMMENT 'Pass/fail/warning outcome',
  Risk_Category           STRING        COMMENT 'Credit risk category',
  Credit_Control_Area     STRING        COMMENT 'Credit control area code',
  Credit_Limit            DECIMAL(15,2) COMMENT 'Assigned credit limit at check time',
  Exposure_Before         DECIMAL(15,2) COMMENT 'Credit exposure before this order',
  Order_Value             DECIMAL(15,2) COMMENT 'Value of the checked order',
  Exposure_After          DECIMAL(15,2) COMMENT 'Credit exposure after this order',
  Credit_Utilization_Pct  DECIMAL(7,2)  COMMENT 'Utilization % (exp_after / limit * 100)',
  Is_Approved             BOOLEAN       COMMENT 'Check_Result = APPROVED flag',
  _source_system          STRING        COMMENT 'Source system enum',
  _loaded_at              TIMESTAMP     COMMENT 'Pipeline execution timestamp',
  CONSTRAINT valid_grain EXPECT (Credit_Check_Key IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT fk_date_resolved EXPECT (Check_Date_Key IS NOT NULL),
  CONSTRAINT fk_customer_resolved EXPECT (Customer_Key IS NOT NULL)
)
CLUSTER BY (Customer_Key)
COMMENT 'Credit check event fact — exposure, risk, and approval analysis'
AS
SELECT
  cc.order_credit_check_id                   AS Credit_Check_Key,
  cc.Order_Number,
  CAST(cc.Check_Timestamp AS DATE)           AS Check_Date_Key,
  SHA2(cc.Customer_Number, 256)              AS Customer_Key,
  o.sales_area_id                            AS Sales_Area_Key,
  cc.Check_Type,
  cc.Check_Result,
  cc.Risk_Category,
  cc.Credit_Control_Area,
  cc.Credit_Limit,
  cc.Exposure_Before,
  cc.Order_Value,
  cc.Exposure_After,
  cc.Credit_Utilization_Pct,
  cc.Check_Result = 'APPROVED'               AS Is_Approved,
  'SAP_S4'                                   AS _source_system,
  current_timestamp()                        AS _loaded_at
FROM manufacturing_silver_vibe.sales_order_silver_sdp.order_credit_check cc
LEFT JOIN manufacturing_silver_vibe.sales_order_silver_sdp.`order` o
  ON o.order_id = cc.order_id;
