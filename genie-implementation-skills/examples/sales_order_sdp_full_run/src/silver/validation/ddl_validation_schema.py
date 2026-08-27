# Databricks notebook source
# DBTITLE 1,Runtime Parameters
# MAGIC %sql
# MAGIC CREATE WIDGET TEXT silver_catalog DEFAULT '';
# MAGIC CREATE WIDGET TEXT silver_schema  DEFAULT '';

# COMMAND ----------

# DBTITLE 1,Set Context
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:silver_catalog);
# MAGIC USE SCHEMA  IDENTIFIER(:silver_schema);

# COMMAND ----------

# DBTITLE 1,Create _validation_run
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS _validation_run (
# MAGIC   Run_Id                   STRING       NOT NULL  COMMENT 'UUID for this validation run',
# MAGIC   Run_Timestamp            TIMESTAMP    NOT NULL  COMMENT 'UTC start time of the validation run',
# MAGIC   Project_Name             STRING       NOT NULL  COMMENT 'Project identifier',
# MAGIC   Schema_Name              STRING       NOT NULL  COMMENT 'Target schema being validated',
# MAGIC   Triggered_By             STRING       NOT NULL  COMMENT 'How this run was triggered: SCHEDULED | MANUAL | PRE_DEPLOY | POST_FIX',
# MAGIC   Total_Entities           INT          NOT NULL  COMMENT 'Number of entities validated in this run',
# MAGIC   Entities_Grade_A         INT          NOT NULL  COMMENT 'Count of entities achieving Grade A',
# MAGIC   Entities_Grade_B_Plus    INT          NOT NULL  COMMENT 'Count of entities at Grade B+',
# MAGIC   Entities_Grade_B         INT          NOT NULL  COMMENT 'Count of entities at Grade B',
# MAGIC   Entities_Grade_C_Or_Below INT         NOT NULL  COMMENT 'Count of entities at Grade C or worse',
# MAGIC   Overall_Grade            STRING       NOT NULL  COMMENT 'Worst grade across all entities',
# MAGIC   Drift_Alerts_Count       INT          NOT NULL  COMMENT 'Number of columns with drift exceeding tolerance',
# MAGIC   Run_Duration_Seconds     INT                    COMMENT 'Wall-clock duration of the full validation suite',
# MAGIC   _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
# MAGIC   CONSTRAINT pk_validation_run PRIMARY KEY (Run_Id)
# MAGIC )
# MAGIC USING DELTA
# MAGIC CLUSTER BY (Run_Timestamp)
# MAGIC COMMENT 'Validation metadata. One row per validation suite execution.';

# COMMAND ----------

# DBTITLE 1,Create _validation_table_result
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS _validation_table_result (
# MAGIC   Run_Id                   STRING       NOT NULL  COMMENT 'FK to _validation_run',
# MAGIC   Table_Name               STRING       NOT NULL  COMMENT 'Entity name',
# MAGIC   Table_Type               STRING       NOT NULL  COMMENT 'REF | MASTER | TXN',
# MAGIC   Tier                     INT          NOT NULL  COMMENT 'Load order tier (0 = root refs)',
# MAGIC   Row_Count                BIGINT       NOT NULL  COMMENT 'Current row count at validation time',
# MAGIC   Row_Count_Delta          BIGINT                 COMMENT 'Change from previous run (NULL on first run)',
# MAGIC   Pk_Duplicate_Count       BIGINT       NOT NULL  COMMENT 'Number of duplicate PK values (0 = clean)',
# MAGIC   Fk_Orphan_Rate_Pct       DECIMAL(7,4)           COMMENT 'Worst FK orphan rate across all FKs',
# MAGIC   Key_Column_Pop_Pct       DECIMAL(7,4) NOT NULL  COMMENT 'Lowest population pct across key columns',
# MAGIC   Freshness_Hours          DECIMAL(10,2)          COMMENT 'Hours since most recent _loaded_at',
# MAGIC   Drift_Columns_Count      INT          NOT NULL  COMMENT 'Number of columns with drift exceeding tolerance',
# MAGIC   Integration_Pass         BOOLEAN                COMMENT 'TRUE if all integration checks pass (TXN only)',
# MAGIC   Grade                    STRING       NOT NULL  COMMENT 'Computed grade: A | B+ | B | C | D | F',
# MAGIC   Grade_Delta              STRING                 COMMENT 'Change from previous run: IMPROVED | STABLE | DEGRADED | NEW',
# MAGIC   Known_Gaps_Count         INT          NOT NULL  COMMENT 'Number of documented known gaps for this entity',
# MAGIC   Accepted_Exceptions      INT          NOT NULL  COMMENT 'Number of checks excluded due to documented exceptions',
# MAGIC   Remediation_Status       STRING                 COMMENT 'NULL | DETECTED | TRIAGED | ESCALATED_TO_ETL | RESOLVED',
# MAGIC   _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
# MAGIC   CONSTRAINT pk_validation_table_result PRIMARY KEY (Run_Id, Table_Name)
# MAGIC )
# MAGIC USING DELTA
# MAGIC CLUSTER BY (Table_Name, Run_Id)
# MAGIC COMMENT 'Validation metadata. One row per entity per run.';

# COMMAND ----------

# DBTITLE 1,Create _validation_check_detail
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS _validation_check_detail (
# MAGIC   Run_Id                   STRING       NOT NULL  COMMENT 'FK to _validation_run',
# MAGIC   Table_Name               STRING       NOT NULL  COMMENT 'Entity being checked',
# MAGIC   Check_Name               STRING       NOT NULL  COMMENT 'Human-readable check name',
# MAGIC   Check_Type               STRING       NOT NULL  COMMENT 'Category: PK | FK | BK | POP | DRIFT | INTEGRATION | FRESHNESS',
# MAGIC   Status                   STRING       NOT NULL  COMMENT 'Result: PASS | FAIL | WARN | SKIP | KNOWN_GAP',
# MAGIC   Threshold_Value          STRING                 COMMENT 'Expected threshold',
# MAGIC   Actual_Value             STRING                 COMMENT 'Measured value',
# MAGIC   Deviation_Pct            DECIMAL(10,4)          COMMENT 'How far actual is from threshold',
# MAGIC   Is_Accepted_Exception    BOOLEAN      NOT NULL  COMMENT 'TRUE if excluded from grading',
# MAGIC   Exception_Reason         STRING                 COMMENT 'Why this check is accepted as exception',
# MAGIC   Message                  STRING                 COMMENT 'Human-readable result description',
# MAGIC   _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
# MAGIC   CONSTRAINT pk_validation_check_detail PRIMARY KEY (Run_Id, Table_Name, Check_Name)
# MAGIC )
# MAGIC USING DELTA
# MAGIC CLUSTER BY (Table_Name, Check_Type)
# MAGIC COMMENT 'Validation metadata. One row per check per entity per run.';

# COMMAND ----------

# DBTITLE 1,Create _data_drift_baseline
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS _data_drift_baseline (
# MAGIC   Table_Name               STRING       NOT NULL  COMMENT 'Entity this baseline applies to',
# MAGIC   Column_Name              STRING       NOT NULL  COMMENT 'Column being monitored',
# MAGIC   Metric_Type              STRING       NOT NULL  COMMENT 'What is measured: NULL_RATE | DISTINCT_COUNT | MIN_VALUE | MAX_VALUE | MEAN_VALUE | ROW_COUNT',
# MAGIC   Baseline_Value           STRING       NOT NULL  COMMENT 'Baseline measurement (stored as string)',
# MAGIC   Tolerance_Pct            DECIMAL(7,4) NOT NULL  COMMENT 'Allowed deviation from baseline before alerting',
# MAGIC   Tolerance_Direction      STRING       NOT NULL  COMMENT 'Which direction triggers alert: INCREASE | DECREASE | BOTH',
# MAGIC   Baseline_Set_Date        TIMESTAMP    NOT NULL  COMMENT 'When this baseline was established',
# MAGIC   Baseline_Run_Id          STRING       NOT NULL  COMMENT 'Run_Id that set this baseline',
# MAGIC   Last_Reset_Date          TIMESTAMP              COMMENT 'If manually reset, when',
# MAGIC   Reset_Reason             STRING                 COMMENT 'Why baseline was reset',
# MAGIC   Is_Active                BOOLEAN      NOT NULL  COMMENT 'FALSE to disable monitoring',
# MAGIC   _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
# MAGIC   CONSTRAINT pk_data_drift_baseline PRIMARY KEY (Table_Name, Column_Name, Metric_Type)
# MAGIC )
# MAGIC USING DELTA
# MAGIC CLUSTER BY (Table_Name)
# MAGIC COMMENT 'Validation metadata. Drift detection baselines.';

# COMMAND ----------

# DBTITLE 1,Create _gap_registry
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS _gap_registry (
# MAGIC   Gap_Id                   STRING       NOT NULL  COMMENT 'UUID for this gap entry',
# MAGIC   Table_Name               STRING       NOT NULL  COMMENT 'Entity affected by this gap',
# MAGIC   Column_Name              STRING                 COMMENT 'Specific column affected (NULL for table-level gaps)',
# MAGIC   Gap_Description          STRING       NOT NULL  COMMENT 'Human-readable description of the gap',
# MAGIC   Gap_Type                 STRING       NOT NULL  COMMENT 'Category: MISSING_SOURCE | FK_ORPHAN | PARTIAL_COVERAGE | CONSTRAINT_RELAXED | SYNTHETIC_KEY | DEFERRED_ENRICHMENT',
# MAGIC   Priority                 STRING       NOT NULL  COMMENT 'P0 | P1 | P2 | P3',
# MAGIC   Status                   STRING       NOT NULL  COMMENT 'OPEN | ACCEPTED | IN_PROGRESS | RESOLVED | DEFERRED',
# MAGIC   Remediation_Status       STRING                 COMMENT 'ETL handoff status',
# MAGIC   Unblock_Action           STRING                 COMMENT 'What needs to happen to close this gap',
# MAGIC   Source_Document          STRING                 COMMENT 'Where this gap was first documented',
# MAGIC   Created_Date             DATE         NOT NULL  COMMENT 'When this gap was first recorded',
# MAGIC   Resolved_Date            DATE                   COMMENT 'When this gap was closed',
# MAGIC   Impact_Description       STRING                 COMMENT 'Business impact of this gap remaining open',
# MAGIC   Assigned_To              STRING                 COMMENT 'Person or team responsible',
# MAGIC   _loaded_at               TIMESTAMP    NOT NULL  COMMENT 'UTC timestamp when this row was written',
# MAGIC   CONSTRAINT pk_gap_registry PRIMARY KEY (Gap_Id)
# MAGIC )
# MAGIC USING DELTA
# MAGIC CLUSTER BY (Priority, Status)
# MAGIC COMMENT 'Validation metadata. Registry of known gaps and data quality issues.';

# COMMAND ----------

# DBTITLE 1,Seed Gap Registry
# MAGIC %sql
# MAGIC -- Seed _gap_registry from build_manifest.md §6 Known Gaps
# MAGIC INSERT INTO _gap_registry VALUES
# MAGIC   (uuid(), 'otd_record', 'Actual_Delivery_Date', 'Actual_Delivery_Date is NULL for all rows — requires likp/lips (delivery document tables) ingestion', 'MISSING_SOURCE', 'P0', 'DEFERRED', NULL, 'Ingest SAP SD likp/lips tables into bronze', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'OTD analysis uses proxy status (comparing requested vs scheduled) but cannot measure real delivery performance', NULL, current_timestamp()),
# MAGIC   (uuid(), 'return_order', 'order_reason_id', 'Portal reason codes (DMG/WRONG/WARR) do not map to SAP/CRM vocabulary — FK always NULL', 'FK_ORPHAN', 'P1', 'ACCEPTED', NULL, 'Build returns reason code mapping table', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'Cannot categorize returns by standard reason codes', NULL, current_timestamp()),
# MAGIC   (uuid(), 'return_order_line', 'order_reason_id', 'Same portal vocab gap as return_order — inherited NULL FK', 'FK_ORPHAN', 'P1', 'ACCEPTED', NULL, 'Build returns reason code mapping table', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'Cannot categorize return lines by reason', NULL, current_timestamp()),
# MAGIC   (uuid(), 'channel_config', 'sales_area_id', 'Source (zsd_channel_config) lacks vkorg/spart columns — cannot resolve composite FK', 'PARTIAL_COVERAGE', 'P3', 'ACCEPTED', NULL, 'Enrich bronze source with org/division mapping', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'Channel config not linked to sales area hierarchy', NULL, current_timestamp()),
# MAGIC   (uuid(), 'sales_contract', 'sales_area_id', 'Source (veda) lacks vkorg/spart — cannot resolve composite FK to sales_area', 'PARTIAL_COVERAGE', 'P3', 'ACCEPTED', NULL, 'Enrich bronze veda with org/division', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'Sales contracts not linked to sales area hierarchy', NULL, current_timestamp()),
# MAGIC   (uuid(), 'delivery_schedule', NULL, '0 rows — no scheduling agreement (SA) document types exist in current bronze data', 'PARTIAL_COVERAGE', 'P3', 'ACCEPTED', NULL, 'Ingest SA-type sales documents into bronze', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'Delivery scheduling analytics unavailable until SA documents exist', NULL, current_timestamp()),
# MAGIC   (uuid(), 'order', 'quotation_id', 'Only ~19.9% of orders resolve to a quotation (via quote.converted_order_number match)', 'PARTIAL_COVERAGE', 'P3', 'ACCEPTED', NULL, 'Cross-source design limitation — only converted quotes link', 'build_manifest.md §6', DATE'2026-07-28', NULL, 'Quote-to-order conversion analysis limited to 19.9% of orders', NULL, current_timestamp());