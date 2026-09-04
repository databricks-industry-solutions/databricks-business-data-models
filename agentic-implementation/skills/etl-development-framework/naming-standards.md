# ETL Naming & Modeling Standards — *Acuity example profile*

## About This Document

This is the authoritative companion to the **ETL Development Framework Skill**. Genie Code **MUST** read this file before generating any DDL, MERGE, or DAB artifact for any silver or gold project. Every rule is **MANDATORY** unless explicitly labeled `PREFERRED` or `OPTIONAL`.

> **Portability — read first.** The concrete values in this document (catalog names like
> `cat_bi_bronze_prod`, the `_source_system` enum `ORACLE_EBS`/`ABL`/`DFF`, the Acuity CDM
> casing) are the **Acuity example profile**. A new customer does **not** rewrite this file —
> they edit **`templates/conventions.yml`** (the single config surface) to change catalogs,
> source-system enum, casing, surrogate-key method, audit-column prefix, and load-strategy
> thresholds. This document explains the *rationale* for each rule; `conventions.yml` holds the
> *values* the skills resolve at generation time. Where a value below is Acuity-specific, treat
> the corresponding `conventions.yml` key as the source of truth.
>
> **Runtime-parameter rule for generators (NOT authoring-time substitution):** catalog/schema
> are **runtime parameters carried by the load notebook's own widgets** (see `deployment-and-dab.md`
> "Runtime Parameters"):
> - **Load notebook** (`transformations/{entity}`) declares `CREATE WIDGET` for each param
>   (`silver_catalog`, `gold_*`, one `src_{logical}` per bronze source, `job_name`), receives the
>   DAB job's `base_parameters`, sets the session with `USE CATALOG/SCHEMA IDENTIFIER(:silver_catalog)`,
>   references target/silver tables **UNQUALIFIED**, and reads bronze via
>   `IDENTIFIER(:src_{logical} || '.{table}')`. This is what the daily job runs directly.
> - **DDL and validation** use widgets the same way (`CREATE WIDGET` + `IDENTIFIER(:...)`).
>
> The DAB job passes values per target via `base_parameters` wired to DAB `variables`;
> `conventions.yml` holds the defaults + the `bronze_sources` map. **NEVER bake catalog/schema/
> workspace-host/email/job-name literals into any generated notebook** — the first pass wrote
> literals into all files, which made re-targeting a many-file rewrite; the same notebooks must
> promote dev→prod unchanged. Full pattern: `deployment-and-dab.md` "Runtime Parameters".

This document supersedes legacy ADF/Azure Data Factory conventions. Do not replicate `DF_` column prefixes, external table patterns, or ADF pipeline naming in new work.

It also serves as the implementation-layer expression of the **customer's Customized CDM (Common Data Model)** — for the example profile, the Acuity CDM defined by the Data Modeling Lead. Where the CDM and this document differ, the open conflicts are documented in Section 4.5 for Platform Lead resolution. All other CDM rules are incorporated and aligned below.

---

## Part 1 — Catalog, Schema & Object Naming

### 1.1 Catalogs

Genie Code does **not** create catalogs. Reference only. **These are the live values in
`conventions.yml` (`catalogs:` + `bronze_sources:`), which supply the runtime-param DEFAULTS —
they are NOT substituted into generated SQL at authoring time.** The table below is the Acuity
example profile; replace per customer by editing `conventions.yml`, not this doc.

| Environment | `conventions.yml` key | Acuity example |
| --- | --- | --- |
| Bronze production | `catalogs.bronze` | `cat_bi_bronze_prod` |
| Vibe model (READ-ONLY target being graded) | `vibe_model.catalog` / `vibe_model.schema` | `cat_bi_model_v2.sales_order` |
| Silver production (LAND/WRITE target for built tables) | `catalogs.silver` | `cat_bi_silver_prod` |
| Gold production | `catalogs.gold` | `cat_bi_gold_prod` |
| Sandbox / dev | `catalogs.sandbox` | `cat_bi_sandbox_dev_eus` |
| HR bronze | `bronze_sources.src_hr` | `cat_hr_bronze_prod.odata_hr_curated` |

> **Read the model from `vibe_model.*`; land built silver into `catalogs.silver`.** These are
> distinct so a build never writes into the vibe model it grades against. They may point at
> different catalogs; if a customer keeps them in one catalog, still give the built silver its
> own schema (`silver_pattern`) separate from `vibe_model.schema`.

> ### ⚠️ Precedence & key strategy by mode (`conventions.yml` → `output_model`)
>
> Naming and keys are driven by **`output_model`**. (The old `naming.follow_vibe_model_ddl`
> boolean is **retired** — `normalized` mode IS "mirror the model"; `dimensional` mode IS "apply
> the Kimball standard below".)
>
> - **`normalized`** *(default)* (+ `hybrid`-silver) — **the vibe model's DDL is authoritative for every
>   table** (it defines them all). Its **table/product names, column names, casing, and PK
>   convention** (lowercase `order_id`, `snake_case` business columns, product name `customer` not
>   `dim_customer`) **OVERRIDE** the `Pascal_Snake_Case` + `{Entity}_Key` + `dim_/fact_` standard
>   below. Match the model exactly; do NOT "fix" the model's casing, add `dim_/fact_` prefixes, or
>   rename `order_id` → `Order_Key`. **Keys follow the model** — `surrogate_key_method: NONE`; add
>   a surrogate ONLY where the model PK is composite/mutable or cross-source integration needs one.
> - **`dimensional`** — the `Pascal_Snake_Case` / `{Entity}_Key` / `dim_/fact_/bridge_`
>   standard in this document applies throughout. The model's product names/keys **seed** the
>   design but are re-shaped into the star. `surrogate_key_method: SHA2`.
> - **`hybrid`** — **layered, not both-at-once:** the silver layer follows `normalized` (SSOT),
>   THEN a gold star built downstream from that silver follows `dimensional`. Silver first; gold
>   reads silver.
>
> **Key strategy — why it differs.** Surrogate keys are not a star-schema exclusive, but their
> *reason* differs: in dimensional they are near-mandatory (SCD2 versioning, uniform narrow
> fact→dim joins, `-1` unknown member); in normalized they are optional (stable identity for
> composite/mutable natural keys, cross-source integration). Because the vibe agent already emits a
> clean `{product}_id` PK/FK graph, `normalized` mode respects it rather than overlaying surrogates.
>
> **`scd_strategy: type_2`** (dimensional / hybrid-gold ONLY) forces `surrogate_key_method: SHA2`
> regardless of the per-mode default — you cannot version rows without a per-version surrogate.
> `normalized` + `type_2` is invalid (a 3NF current-state model does history via temporal /
> effective-dating) — error early and redirect the customer to `hybrid`.
>
> The metadata/audit column conventions (`_lower_snake_case`, `_loaded_at`, etc.) and the `-1`
> FK-default rule apply in ALL modes — the model rarely specifies those, and they don't conflict
> with the model's business-column names. (The `-1` seeding itself is dimensional-only; see the
> Normalized Product template in `ddl-and-modeling.md`.)

### 1.2 Schemas

| Layer | Pattern | Example |
| --- | --- | --- |
| Silver | `{domain}_silver[_{suffix}]` | `hr_silver`, `manufacturing_silver` |
| Gold | `{domain}_gold[_{suffix}]` | `hr_gold`, `item_gold` |
| Sandbox / dev | `{domain}_{layer}_{project}` | `hr_silver_2`, `manufacturing_silver_genie_workshop_live` |

### 1.3 Tables

| Layer | Pattern | Max length | Example |
| --- | --- | --- | --- |
| Bronze | Source name unchanged — **READ-ONLY, never create** | — | `employee_central` |
| Silver dimension | `dim_{entity}` — lowercase, descriptive | 35 chars | `dim_employee`, `dim_cost_center` |
| Silver fact | `fact_{name}` — lowercase, descriptive | 35 chars | `fact_headcount`, `fact_compensation` |
| Silver bridge | `bridge_{dim_a}_{dim_b}` — lowercase, resolves M:N relationship | 35 chars | `bridge_employee_cost_center`, `bridge_position_job_family` |
| Gold | `{subject_area}_{business_process}_{grain}` — business friendly, no `dim_`/`fact_` prefix | 35 chars | `hr_headcount_monthly`, `hr_attrition_weekly` |

> Gold tables do **NOT** use `dim_` or `fact_` prefixes. They are use-case tables, not dimensional model objects.

> **Singular names (CDM rule):** All table and entity names use **singular** form. Use `dim_employee` not `dim_employees`, `fact_order` not `fact_orders`, `Customer` not `Customers`. This applies to all layers.

### 1.4 Views

| Type | Pattern | Example |
| --- | --- | --- |
| Cover / passthrough view | `vw_{table_name}` | `vw_dim_employee` |
| Gold analytical view | Business friendly name, no prefix | `hr_headcount_summary` |
| Materialized view (DBSQL only) | `mvw_{table_name}` | `mvw_hr_headcount` |

> Materialized Views require DBSQL compute — they cannot run on serverless generic compute. For sandbox/workshop use, recreate as a regular VIEW with identical SQL.

> **CDM note:** The CDM examples show `Vw_items` with an uppercase `V`. This document standardizes to **lowercase** `vw_` for consistency with all other lowercase table/object prefixes. The Platform Lead should confirm this alignment.

---

## Part 2 — Asset Naming

### 2.1 ETL Notebooks (load notebook + DDL + validation)

Pattern: `{layer}_{domain}_{purpose}[_{detail}]`. Load notebooks and validation are
**extension-less notebook objects**; DDL is a `.sql` file.

| Notebook type | Path (extension-less unless noted) | Example |
| --- | --- | --- |
| Dimension load notebook | `transformations/dim_{entity}` | `transformations/dim_employee` |
| Fact load notebook | `transformations/fact_{name}` | `transformations/fact_headcount` |
| DDL setup (plain `.sql`) | `ddl/ddl_dim_{entity}.sql` | `ddl/ddl_dim_employee.sql` |
| Validation gate | `validate_{layer}` | `validate_silver` |

> **No version suffixes on any generated object.** Name notebooks plainly `dim_{entity}` — **never**
> `dim_{entity}_v2` / `_v1` / `_final`. A `_v2` on every file reads as "an unfinished v1 exists
> somewhere" and makes users ask why (it did — see the Meridian run). If a migration ever needs
> marking, put it in a comment, not the object name.

> **`src/` is layer-first, then role:** `src/{silver,gold}/{ddl/, transformations/}` plus
> `validate_{layer}` directly under the layer folder. The load notebook declares its own widgets,
> holds the MERGE, and is what the daily job references directly. See `deployment-and-dab.md`.

**Critical rule:** Every DDL notebook MUST begin with `-- Databricks notebook source` (DDL is
always SQL). Each load/validation notebook begins with the first line for its `etl_language`
shape — `-- Databricks notebook source` (SQL) or `# Databricks notebook source` (Python) — and
carries **no file extension**. See `deployment-and-dab.md` "Notebook-format contract". This header
(not an extension) is what lets a notebook run as a `notebook_task` on serverless Jobs compute.

### 2.2 Jobs

Pattern: `{subject_area}_{purpose}`

Examples: `hr_silver_gold_load`, `manufacturing_silver_daily`

### 2.3 DAB Bundles

Pattern: `{subject_area}_{layer}[_{suffix}]`

Examples: `hr_silver`, `hr_silver_gold`, `manufacturing_silver_enhancements`

### 2.4 Notebook Deployment

Notebooks are deployed exclusively via **Declarative Automation Bundles (DABs)**. There is no separate "notebook deployment" artifact — the DAB bundle IS the deployment unit.

- Each ETL notebook lives in `src/` as a SQL-source `.sql` file
- The bundle's `resources/{job_name}.job.yml` references each notebook as a `notebook_task`
- Deploy via `databricks bundle deploy -t dev` (or `prod`)
- Do NOT deploy notebooks individually via the workspace API or UI drag-and-drop

### 2.5 LakeFlow Spark Declarative Pipelines

Pattern: `pl-{layer}_{domain}_{purpose}[_{detail}]`

Examples: `pl-silver_hr_employee`, `pl-bronze_hr_ingestion`

> Use Lakeflow Spark Declarative Pipelines only when the ETL Framework Boundaries cell applies (SCD Type 2, streaming, DQ expectations). For standard Type 1 MERGE workloads, use the framework's SQL notebook + DAB pattern instead.

### 2.6 Other Assets

| Asset | Pattern | Example |
| --- | --- | --- |
| Cluster | `cl_{domain}_{group}_{purpose}` | `cl_hr_job_daily_load`, `cl_data_engineering_all_purpose` |
| SQL Warehouse | `sqlwh_{group}_{purpose}` | `sqlwh_hr_analytics` |
| AI/BI Dashboard | `{domain}_{subj_area}_{purpose}_{audience}` | `hr_headcount_overview_hrbp` |
| Genie Space | `{layer}_{domain}_{entity}_{asset_type}[_{optional}]` | `silver_hr_employee_genie` |
| Function | `{category}_{domain}_{purpose}[_{suffix}]` | `dq_hr_validate_employee_id` |
| Folder | `{domain}_{subject_area}_{project_name}` | `hr_headcount_poc` |
| Tag | `{project}-{domain}-{subjarea}-{layer}-{purpose}` | `hr-data-lake-data-engineering-silver-etl` |
| Repository | `bi-{technology}-{project}` | `bi-databricks-hr-silver` |
| Delta Share | `ds_{recipient_or_provider}_{domain}_{subject}` | `ds_external_hr_headcount` |

#### Function Category Prefixes

The `{category}` segment in function names is an enumerated list — use only these values:

| Category | Scope |
| --- | --- |
| `util` | General utilities: string manipulation, date helpers, type conversion |
| `dq` | Data quality: validation helpers, assertion wrappers, profiling |
| `sec` | Security: access control checks, entitlement helpers |
| `mask` | Data masking: PII obfuscation, anonymization, tokenization |
| `fmt` | Formatting: display formatting, unit conversion, label generation |

---

## Part 3 — Column Naming

### 3.0 General Column Naming Rules (CDM)

These rules apply to all column names across all layers. They come directly from the Acuity CDM standard and are non-negotiable.

| Rule | Requirement | Bad example | Good example |
| --- | --- | --- | --- |
| **Pascal_Snake_Case** | Each word starts with a capital letter, separated by underscores | `item_description`, `ITEMDESC` | `Item_Description` |
| **Singular form** | Column names reference singular concepts | `Sales_Orders_Count` | `Sales_Order_Cnt` |
| **No special characters** | No spaces, hyphens, slashes, or characters other than letters, digits, and underscores | `Sales-Amount`, `Sales Amount` | `Sales_Amt` |
| **Descriptive and meaningful** | Name reflects the business concept; domain context included when needed | `Item_Dsc`, `Amt` | `Item_Description`, `Sales_Amt` |
| **No calculated values in names** | Do not embed aggregation scope, time periods, or calculation logic into column names | `Sales_Amount_Total_By_Year`, `Total_Order_Amount_Quarter` | `Sales_Amt`, `Order_Amt` |
| **Datatype hints** | Use standard suffixes to convey type at a glance — see Sections 3.4 and 3.5 for the full list | `Is_Active` (ambiguous type) | `Is_Active_Flag` (clearly BOOLEAN) |

### 3.1 Case Rules

> **Applies to `dimensional` mode.** In `normalized`/`hybrid`-silver the vibe model's column names +
> casing + PK convention win (see the "⚠️ Precedence & key strategy by mode" note in Part 1, and
> `conventions.yml output_model`). The rows below govern the dimensional star (and net-new tables
> the model didn't define, e.g. a gold mart). The system/metadata rule and `-1` FK default always apply.

| Column class | Case rule | Example |
| --- | --- | --- |
| Business / domain columns | `Pascal_Snake_Case` | `Employee_Id`, `Hire_Date`, `Cost_Center_Code` |
| System / metadata columns | `_lower_snake_case` with leading underscore | `_source_system`, `_loaded_at`, `_batch_id` |
| Surrogate keys (PK) | `Pascal_Snake_Case` + `_Key` suffix | `Employee_Key`, `Cost_Center_Key` |
| Foreign key columns | Same name as the parent dim's PK | `Employee_Key` (FK in fact = `Employee_Key` PK in `dim_employee`) |
| Natural / business keys | Preserve source casing from bronze if from an external system; otherwise `Pascal_Snake_Case` | `Employee_Id` (SAP SF), `Inventory_Item_Id` (Oracle) |

> The leading underscore on system columns is a deliberate visual separator. It signals "infrastructure, not business data" and causes metadata columns to sort after business columns in most tooling.

### 3.2 Surrogate Key Convention

> **`dimensional` mode (+ `hybrid` gold).** In `normalized`/`hybrid`-silver, keys follow the vibe
> model's PKs (`{product}_id`), and this section does not apply unless a surrogate is added by
> exception (composite/mutable model PK, or cross-source integration). See Part 1 "key strategy by
> mode".

- **Name:** `{Entity}_Key` — e.g., `Employee_Key`, `Plant_Key`, `Cost_Center_Key`
- **Type:** `BIGINT NOT NULL`
- **Method:** Deterministic SHA2 hash — **never use `IDENTITY`** (IDENTITY breaks re-run idempotency and is unstable across reloads)
- **Formula:**
  ```sql
  CAST(CONV(SUBSTRING(SHA2(CONCAT_WS('|',
    COALESCE(CAST({k1} AS STRING), '~'),
    COALESCE(CAST({k2} AS STRING), '~')
  ), 256), 1, 15), 16, 10) AS BIGINT) AS {Entity}_Key
  ```
- **Composite natural keys:** When an entity requires multiple columns to form a unique identifier, include all key parts in the `CONCAT_WS` hash and document the composite key explicitly in the table `COMMENT`.
- **Facts get their own surrogate key:** Facts are assigned a surrogate key hashed from their grain columns. This enables the validation gate's PK uniqueness check to work identically across dims and facts.
- **Bridge tables:** The surrogate key is `{Association}_Key` where `{Association}` describes the relationship — e.g., `Employee_Cost_Center_Key` for `bridge_employee_cost_center`. A generic `Bridge_Key` violates this convention.
- **Unknown member:** Every surrogate key column must be seed-capable to -1 (see Section 6.1)

> **Note on framework template syntax:** The ETL Framework Template uses `{entity}_sk` in its code block examples. When generating actual DDL and MERGE notebooks, use `{Entity}_Key` (Pascal_Snake_Case) per this standard — not `_sk`.

### 3.3 Foreign Key Column Naming

FK columns in a fact or child table always carry the **same name as the PK in the parent dim**.

```sql
-- dim_employee has:   Employee_Key BIGINT NOT NULL
-- fact_headcount has: Employee_Key BIGINT NOT NULL  ← same name, FK semantics
```

FK values default to `-1` (Unknown member) via `COALESCE(..., -1)` when the join misses. FK columns are `NOT NULL` in silver facts — `-1` is the sentinel, not NULL.

### 3.3.1 Role-Based (Role-Playing) Dimension FK Naming

When a fact or child table references the **same dimension more than once** (each reference playing a different business role), the FK column **cannot** share the PK name — column names must be unique. Use the `{Role}_{Entity}_Key` pattern.

**Pattern:** `{Role}_{Entity}_Key`

```sql
-- dim_date has:          Date_Key BIGINT NOT NULL
-- fact_headcount has:    Snapshot_Date_Key   BIGINT NOT NULL  ← role = Snapshot
-- fact_headcount has:    Hire_Date_Key       BIGINT NOT NULL  ← role = Hire

-- dim_employee has:      Employee_Key BIGINT NOT NULL
-- fact_headcount has:    Employee_Key        BIGINT NOT NULL  ← single role (no prefix needed)
-- fact_headcount has:    Manager_Employee_Key BIGINT NOT NULL ← role = Manager
```

**Rules:**

1. **Single-role FK:** When a fact references a dimension only once, use the standard rule from Section 3.3.
2. **Multi-role FK:** When a fact references the same dimension two or more times, **every** reference uses the `{Role}_{Entity}_Key` pattern.
3. **Role prefix:** The `{Role}` segment is a short, business-meaningful descriptor in `Pascal_Snake_Case`.
4. **COALESCE to -1:** The Unknown member rule still applies to each role instance.
5. **NOT NULL:** All role-based FK columns are `NOT NULL` in silver facts.
6. **Column COMMENT:** Each role-based FK must include the role in its COMMENT.

**Constraint naming for role-based FKs:**

Pattern: `fk_{table}_{role}_{parent_dim}`

```sql
CONSTRAINT fk_fact_headcount_hire_date FOREIGN KEY (Hire_Date_Key)
  REFERENCES dim_date(Date_Key),                 -- unqualified: session catalog.schema
CONSTRAINT fk_fact_headcount_termination_date FOREIGN KEY (Termination_Date_Key)
  REFERENCES dim_date(Date_Key)
```

### 3.4 Flag Columns

Boolean columns use the suffix `_Flag`.

Examples: `Is_Active_Flag`, `Stock_Enabled_Flag`, `Contractor_Select_Flag`

### 3.5 Date & Time Columns

| Data type | Suffix convention | Type |
| --- | --- | --- |
| Date only | `_Date` | `DATE` preferred; `STRING` only if source format is non-standard and conversion is lossy |
| Date + time | `_Dttm` | `TIMESTAMP` — e.g., `Hire_Dttm`, `Last_Updated_Dttm` |
| Year-month (integer) | `_Yyyymm` | `INT` |

**UTC rule:** All `TIMESTAMP` columns across every layer are stored in UTC. Source data in a local timezone must be converted during the silver load using `CONVERT_TIMEZONE` or equivalent before writing to the silver table. Document the source timezone in the column `COMMENT` when a conversion was applied.

### 3.6 Abbreviation Glossary

Use these abbreviations in column names to keep names under ~40 characters.

| Full word | Abbreviation |
| --- | --- |
| Amount | `Amt` |
| Count | `Cnt` |
| Quantity | `Qty` |
| Number | `Nbr` |
| Identifier | `Id` |
| Description | `Desc` |
| Organization | `Org` |
| Department | `Dept` |
| Transaction | `Txn` |
| Code | `Cd` (only in long compound names) |
| Date | `Dt` (only in long compound names) |
| Maximum | `Max` |
| Minimum | `Min` |
| Average | `Avg` |
| Percentage | `Pct` |
| Sequence | `Seq` |
| Reference | `Ref` |
| Category | `Cat` |
| Indicator | `Ind` (for non-boolean indicator strings) |

### 3.7 Reserved Internal Names

The following names are reserved for framework use. Do not use them as business column names:

| Reserved name | Reserved for |
| --- | --- |
| `_rn` | `ROW_NUMBER()` alias in deduplication CTEs |
| `_src` | Source alias in MERGE statements |
| `_tgt` | Target alias in MERGE statements |
| `Key` (standalone) | Always part of `{Entity}_Key` — never a bare column named `Key` |
| `Id` (standalone) | Always part of `{Entity}_Id` — never a bare column named `Id` |

Additionally, avoid using bare SQL reserved words as column names without quoting: `SELECT`, `TABLE`, `DATE`, `SUM`, `AVG`, `COUNT`, `MAX`, `MIN`, `YEAR`, `MONTH`, `DAY`, `TIMESTAMP`, `SCHEMA`, `COLUMN`, `INDEX`, `KEY`, `VALUE`, `TYPE`, `STATUS`, `NAME`, `GROUP`, `ORDER`

If a source column uses one of these names, rename it on load — e.g., Oracle `STATUS` → `Item_Status`, Oracle `DATE` → `Effective_Date`.

---

## Part 4 — Standard Metadata Columns

Every table produced by this framework **must** include the metadata columns below.

### 4.1 Silver Tables

| Column | Type | NOT NULL | Position | Description |
| --- | --- | --- | --- | --- |
| `_source_system` | `STRING` | YES | Last | Source system identifier — see Section 4.3 for standard values |
| `_loaded_at` | `TIMESTAMP` | YES | Last | UTC timestamp of the last MERGE that touched this row — set via `current_timestamp()` |
| `_created_by` | `STRING` | NO | Last | OPTIONAL — name of the DAB job or bundle that first inserted this row |
| `_modified_by` | `STRING` | NO | Last | OPTIONAL — name of the DAB job or bundle that last updated this row |
| `_batch_id` | `STRING` | NO | Last | Job run ID for load traceability |

**MERGE SET example:**
```sql
WHEN MATCHED THEN UPDATE SET
  ...,
  tgt._source_system = src._source_system,
  tgt._loaded_at     = current_timestamp(),
  tgt._modified_by   = '{job_name}'
WHEN NOT MATCHED THEN INSERT (..., _source_system, _loaded_at, _created_by, _modified_by)
  VALUES (..., src._source_system, current_timestamp(), '{job_name}', '{job_name}')
```

### 4.2 Gold Tables

| Column | Type | NOT NULL | Position | Description |
| --- | --- | --- | --- | --- |
| `_source_system` | `STRING` | NO | Last | Inherited from silver source; may be NULL if aggregated across systems |
| `_inserted_at` | `TIMESTAMP` | YES | Last | UTC timestamp when this row was first written |
| `_updated_at` | `TIMESTAMP` | YES | Last | UTC timestamp of the last full refresh |
| `_created_by` | `STRING` | NO | Last | OPTIONAL — DAB job name that first created this row |
| `_modified_by` | `STRING` | NO | Last | OPTIONAL — DAB job name that last refreshed this row |

### 4.3 Source System Identifier Values

| Source | `_source_system` value |
| --- | --- |
| SAP SuccessFactors | `'SAP_SF'` |
| Oracle EBS (all modules: LIT, INV, BOM, APPS) | `'ORACLE_EBS'` |
| ABL / SQL Server | `'ABL'` |
| System-generated (seeds, calculations, aggregations) | `'SYSTEM'` |
| Multiple / mixed sources (gold aggregates) | `NULL` or `'MIXED'` |

### 4.4 Legacy ADF Columns — Do Not Replicate

| Legacy column | Replaced by |
| --- | --- |
| `DF_Gold_Created_By` | `_inserted_at` |
| `DF_Gold_Created_Date` | `_inserted_at` |
| `DF_Gold_Updated_By` | `_updated_at` |
| `DF_Gold_Updated_Date` | `_updated_at` |
| `DF_Scd_Start_Date` | Not applicable — Type 1 only |
| `DF_Scd_End_Date` | Not applicable — Type 1 only |
| `DF_Processing_Dttm` | `_loaded_at` / `_updated_at` |

### 4.5 CDM Audit Column Alignment — PLATFORM LEAD DECISION NEEDED

The Acuity CDM standard defines audit columns with `DF_` prefix. This framework uses `_` prefix (Option A). Until the Platform Lead decides, the framework uses Option A. See the full naming standards source document for the complete decision matrix.

---

## Part 5 — DDL Standards

### 5.1 Column Ordering

All tables must follow this column order:

1. **Surrogate key** — `{Entity}_Key BIGINT NOT NULL` (PK)
2. **Foreign key(s)** — one per parent dimension, `{Parent}_Key BIGINT NOT NULL`
3. **Natural / business key** — the source identifier(s)
4. **Business attribute columns** — alphabetical within logical groups
5. **Degenerate dimensions** — facts only
6. **Measure columns** — facts only (`DECIMAL(18,2)` preferred over `DOUBLE` for financial; `BIGINT` for integer counts)
7. **System metadata columns** — always last

### 5.2 Constraint Naming

| Constraint type | Pattern | Example |
| --- | --- | --- |
| PRIMARY KEY | `pk_{table_name}` | `pk_dim_employee`, `pk_fact_headcount` |
| FOREIGN KEY | `fk_{table}_{parent_dim}` | `fk_fact_headcount_employee` |
| FOREIGN KEY (role-based) | `fk_{table}_{role}_{parent_dim}` | `fk_fact_headcount_hire_date` |
| CHECK | `chk_{table}_{column}` | `chk_fact_headcount_headcount_cnt` |

```sql
-- PRIMARY KEY and FOREIGN KEY: inline in CREATE TABLE
CONSTRAINT pk_dim_employee PRIMARY KEY (Employee_Key),
CONSTRAINT fk_fact_headcount_employee FOREIGN KEY (Employee_Key)
  REFERENCES dim_employee(Employee_Key),         -- unqualified: session catalog.schema

-- CHECK: always via ALTER TABLE after CREATE TABLE
ALTER TABLE fact_headcount
  ADD CONSTRAINT chk_fact_headcount_headcount_cnt CHECK (Headcount_Cnt >= 0);
```

### 5.3 NOT NULL Policy

| Column class | Enforce NOT NULL? |
| --- | --- |
| Surrogate key (`{Entity}_Key`) | **YES — always** |
| Natural / business key | **YES — always** |
| FK columns in silver facts | **YES** — use `-1` Unknown, never `NULL` |
| `_source_system` | **YES** |
| `_loaded_at`, `_inserted_at`, `_updated_at` | **YES** |
| All other business columns | Optional — follow source nullability |

### 5.4 CLUSTER BY Convention

| Table type | Cluster by | Rationale |
| --- | --- | --- |
| Silver dimension | Natural key column | Lookups and joins hit the natural key most often |
| Silver fact | Primary dimension FK (highest-cardinality access pattern) | Reduces scan when filtering by the primary dimension |
| Gold table | Grain column(s) or primary BI filter column | Match the dashboard / Genie query access pattern |

Use `CLUSTER BY ({column})` in the `CREATE TABLE` statement. Do not use `PARTITIONED BY` unless the table is extremely large.

### 5.5 CHECK Constraint Policy

- Add CHECK only for invariants that **will never be violated by legitimate data**
- Safe checks: numeric measures `>= 0`, bounded enum/code columns
- Risky checks to avoid: date ranges, percentage values, optional fields
- Add each CHECK via `ALTER TABLE` immediately after the corresponding `CREATE TABLE`

### 5.6 Column & Table Comments — sourced from the vibe metamodel

Every table and every column in a DDL-generated table **must** carry a `COMMENT`, and the content is
**sourced, not invented**:

- **Table `COMMENT`** = the `vibe_metamodel_product.description` carried in the spec (Section 1 /
  Section 2 table-level `Metamodel description`), verbatim. Append a grain/source clause only if the
  model description omits it:
  ```sql
  COMMENT 'One row per dispatched field-service job on an installed asset. Grain: service_order_id. Source: fieldlink.service_order.';
  ```
- **Column `COMMENT` = metamodel base + lineage note.** Use the spec's `Metamodel description`
  (from `vibe_metamodel_attribute.description`) **verbatim as the base**, and append a short real-data note
  **only when it adds material info** — the source table, a NULL-when-unresolved caveat, or a grain
  correction the profiled data forced. Do NOT invent a description when the spec carries one; do NOT
  restate the glossary term in the comment (that goes to a tag — see below).
  ```sql
  {col} {type} COMMENT 'PK — natural key, FieldLink service_order_id. (Sourced from fieldlink.service_order; asset FK NULL until resolved.)'
  ```

**Glossary terms are UC column tags, not comment text.** For every column whose spec row carries a
`Glossary term`, apply it as a UC column tag with key **`glossary_term`** and the value taken verbatim from `vibe_metamodel_attribute.business_glossary_term`:
```sql
ALTER TABLE {table} ALTER COLUMN {col} SET TAGS ('glossary_term' = '{term}');
```
> **Tag-key for built tables is always `glossary_term`.** Every table built by this skill writes glossary
> terms under the key `glossary_term` — that key is what the assessment's Phase 1.6
> `information_schema.column_tags` read is key-agnostic about, but `glossary_term` is the key we emit.
> *Incoming model shells* may carry the term under `glossary_term` (as in the field_service example,
> `model_setup.sql` lines 215–217) **or** under a `dbx_`-prefixed governed key in some workspace setups —
> do not assume a single key on shells. Phase 1.6 reads `column_tags` without filtering on key name, so
> both forms are picked up. Do not apply a shell's `dbx_`-prefixed key to the tables you build; always use
> `glossary_term`.

> **`etl_type: sdp_pipeline` (Lakeflow streaming tables) — important constraint.** In SDP pipelines,
> column COMMENTs go **inline** in the streaming-table definition (inside the `CREATE OR REFRESH STREAMING
> TABLE` / `CREATE OR REFRESH MATERIALIZED VIEW` DDL). Glossary `SET TAGS` statements are **NOT** valid
> inside a pipeline source — they don't persist across refreshes and are rejected in some runtime versions.
> Apply `glossary_term` tags post-refresh via the documentation enrich step
> (`docs/.pipeline/handoffs/{layer}/enrich_uc_metadata.sql`), not as `ALTER` statements inside the
> pipeline source block.

---

## Part 6 — Silver Modeling Rules

### 6.1 Unknown Member (-1) Seeding

Every silver dimension **must** have a -1 Unknown row seeded immediately after the DDL `CREATE TABLE`.

```sql
MERGE INTO dim_{entity} AS t          -- unqualified: session catalog.schema
USING (SELECT CAST(-1 AS BIGINT) AS {Entity}_Key) s
ON t.{Entity}_Key = s.{Entity}_Key
WHEN NOT MATCHED THEN INSERT ({Entity}_Key, {Natural_Key}, _source_system, _loaded_at)
  VALUES (-1, 'UNKNOWN', 'SYSTEM', current_timestamp());
```

### 6.2 Conformed Dimensions

- Define each dimension **once**. Do not create per-fact copies.
- Conformed dimensions use surrogate keys that are stable across all facts.

### 6.3 SCD Strategy — Type 1 Default, Type 2 Opt-In

Default merge strategy is **Type 1 (current-state overwrite)** — `conventions.yml scd_strategy:
type_1`. Set `scd_strategy: type_2` (or a per-entity override in `etl_detailed_spec.md`) to keep
point-in-time history: this swaps in the **SCD Type-2 Dimension** template (`_effective_from` /
`_effective_to` / `_is_current`, a new surrogate per version) + the Type-2 versioning MERGE in
`merge-and-defensive-coding.md`. **Type 2 is dimensional-only** — valid in `output_model:
dimensional` or the gold layer of `hybrid`; it is invalid on `normalized`-mode silver (3NF does
history via temporal/effective-dating), so `normalized` + `type_2` errors early and redirects to
`hybrid`. Very large / high-churn Type-2 dims escalate to a Lakeflow Spark Declarative Pipeline.

### 6.4 Deduplication — Always Required

Every MERGE source query must deduplicate on the natural key using `ROW_NUMBER()`:

```sql
WITH deduped AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY {Natural_Key}
    ORDER BY {recency_column} DESC
  ) AS _rn
  FROM {source_table}
)
SELECT ... FROM deduped WHERE _rn = 1
```

### 6.5 NULL vs Empty String Policy

Empty strings (`''`) from source systems must be standardized to `NULL` during silver load:

```sql
NULLIF(TRIM(src.Cost_Center_Code), '') AS Cost_Center_Code
```

Apply `NULLIF(TRIM(...), '')` to all string columns that are not natural keys or bounded code columns.

### 6.6 Bridge Tables (Many-to-Many Resolution)

Use a bridge table when two dimensions share a **many-to-many** relationship.

**Table naming:** `bridge_{dim_a}_{dim_b}`
**Surrogate key:** `{Association}_Key` — named for the relationship, never generic `Bridge_Key`.

**Rules:**
1. Surrogate key naming: Use `{DimA}_{DimB}_Key`
2. Hash inputs: Include natural keys from **both** parent dimensions
3. FK columns: Follow standard FK naming. Each FK defaults to `-1` via `COALESCE`
4. Weighting column: If the bridge carries a weighting factor, include between FKs and metadata
5. Unknown member: Seed a `-1` row with both FK values set to `-1`
6. Constraint naming: Use `fk_bridge_{dim_a}_{dim_b}_{parent_dim}`

---

## Part 7 — Gold Modeling Rules

### 7.1 Build from Silver, Not Bronze

Gold tables read from the silver schema. They do **not** re-read bronze sources.

### 7.2 Full Recompute Pattern

Gold uses `INSERT OVERWRITE` full recompute by default. Incremental gold is only warranted if the silver fact is too large to aggregate within the job window.

### 7.3 Naming Reminder

Gold table names are **business-friendly** and **do not use `dim_` or `fact_` prefixes**.

| Bad | Good |
| --- | --- |
| `dim_employee_gold` | `hr_employee_master` |
| `fact_headcount_gold` | `hr_headcount_monthly` |

---

## Part 8 — Validation Gate Standards

The validation notebook (`validate_{layer}`) is the **final task** in every DAB daily job. Like
every load notebook, it declares its own **widgets directly** — it opens with the runtime-param
header (`CREATE WIDGET TEXT silver_catalog/silver_schema` → `USE CATALOG/SCHEMA IDENTIFIER(:...)`)
and references tables **unqualified**:

> **Checks are keyed to `output_model`.** In `dimensional` (+ `hybrid`-gold), the PK column is
> `{Entity}_Key` and FK orphans must be 0 (the `-1` Unknown member absorbs all misses). In
> `normalized` (+ `hybrid`-silver), the PK is the model's `{product}_id` and there is **no `-1`
> member** — FKs may be legitimately NULL when unresolved, so the orphan check counts rows whose
> FK is non-NULL but has no parent match (a real referential break), NOT NULL FKs. A `type_2` dim
> adds the "exactly one `_is_current = TRUE` per natural key" check.

```sql
-- 1. PK uniqueness (expect 0) — {Entity}_Key in dimensional; {product}_id in normalized
SELECT '{entity}' AS entity, COUNT(*) - COUNT(DISTINCT {pk_col}) AS dup_pks
FROM {table};

-- 2a. FK orphans, DIMENSIONAL (expect 0 — -1 member must absorb all misses)
SELECT '{fact}->{dim}' AS check_name, COUNT(*) AS orphans
FROM {fact} f
LEFT JOIN {dim} d ON f.{Entity}_Key = d.{Entity}_Key
WHERE d.{Entity}_Key IS NULL;

-- 2b. FK orphans, NORMALIZED (expect 0 — NULL FK is allowed/unresolved, only non-NULL-with-no-parent is a break)
SELECT '{child}->{parent}' AS check_name, COUNT(*) AS orphans
FROM {child} c
LEFT JOIN {parent} p ON c.{parent}_id = p.{parent}_id
WHERE c.{parent}_id IS NOT NULL AND p.{parent}_id IS NULL;

-- 3. Key column population (% non-null; expect >= 95%)
SELECT '{entity}.{Natural_Key}' AS col,
  ROUND(100.0 * COUNT({Natural_Key}) / COUNT(*), 2) AS pct_populated
FROM {table};

-- 4. (type_2 dims only) exactly one current version per natural key (expect 0)
SELECT '{entity}.current_dupes' AS check_name,
  COUNT(*) AS bad_nk FROM (
    SELECT {Natural_Key} FROM {table} WHERE _is_current = TRUE
    GROUP BY {Natural_Key} HAVING COUNT(*) <> 1
  );
```

If any check returns a non-zero result, the validation notebook should **raise an error** to fail the job.

---

## Part 9 — Grading Rubric

| Grade | PK uniqueness | FK orphan rate | Key column population | Action |
| --- | --- | --- | --- | --- |
| **A** | 100% | ≤ 1% (or accepted) | ≥ 95% | Promote — move to next entity |
| **B** | ≥ 99% | ≤ 3% | ≥ 90% | Fix before promoting |
| **C** | ≥ 97% | ≤ 5% | ≥ 80% | Fix before promoting |
| **D / F** | < 97% or PK violations | > 5% | < 80% | Fix or escalate as HUMAN NEEDED |

Accepted orphans (documented business exceptions) count toward Grade A.

---

## Part 10 — Data Governance & Unity Catalog Tagging

### 10.1 Table-Level UC Tags

Every managed table must have UC tags applied immediately after `CREATE TABLE` — in the same
DDL notebook, so the session catalog/schema (set in the header) resolve the unqualified name:

```sql
ALTER TABLE {table} SET TAGS (          -- unqualified: session catalog.schema
  'domain'       = '{hr|manufacturing|finance|supply_chain}',
  'layer'        = '{bronze|silver|gold}',
  'subject_area' = '{headcount|compensation|item|bom}',
  'pii_present'  = '{true|false}'
);
```

### 10.2 Column-Level PII Tags

Any column containing PII must be tagged at the column level:

```sql
ALTER TABLE {table}          -- unqualified: session catalog.schema
  ALTER COLUMN {column_name} SET TAGS ('pii_category' = '{category}', 'sensitivity' = '{level}');
```

| `pii_category` | Applies to |
| --- | --- |
| `name` | Full name, first name, last name |
| `email` | Email address |
| `phone` | Phone number |
| `national_id` | SSN, NIN, tax ID, passport number |
| `salary` | Base pay, bonus, total compensation |
| `date_of_birth` | Date of birth |
| `address` | Home address, postal code |
| `manager_id` | Indirect identifier — employee's manager |

| `sensitivity` | Meaning |
| --- | --- |
| `high` | Direct PII or financial — must not appear in gold without masking |
| `medium` | Indirect PII (manager ID, department, work location) |
| `low` | Non-identifying business attributes |

### 10.3 Job / Compute Tags

Pattern: `{project}-{domain}-{subjarea}-{layer}-{purpose}`

---

## Part 11 — What NOT to Carry Forward from ADF / Legacy

| Legacy practice | Framework replacement |
| --- | --- |
| External Delta tables on ADLS paths | Managed Delta tables in Unity Catalog |
| `DF_` column prefix | `_lower_snake_case` metadata columns |
| Azure Data Factory orchestration | Declarative Automation Bundles (DABs) + serverless Jobs |
| ADF-controlled SCD columns | Type 1 only by default; escalate to SDP |
| Plain `.sql` files as SQL File tasks | Source notebooks as `notebook_task` (serverless) |
| IDENTITY surrogate keys | Deterministic SHA2 hash surrogate keys |
| `UPDATE SET *` / `INSERT *` in MERGE | Explicit column lists always |
| Implicit nulls for missing FK joins | `COALESCE(..., -1)` to Unknown member always |
| Empty strings left as-is from source | `NULLIF(TRIM(...), '')` standardization on silver load |
| Local-timezone timestamps | UTC conversion on silver load |
