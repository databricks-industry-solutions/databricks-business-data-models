-- Databricks notebook source
-- =============================================================================
-- sales_order (MVM) — vibe MODEL setup (READ-ONLY, NORMALIZED 3NF spec)
-- =============================================================================
-- Stands up the "perfect demo" sales_order vibe model: 16 EMPTY target shells
-- with PKs, INTRA-DOMAIN FK constraints, and full column/table comments, plus
-- 6 metric views. This is the PRISTINE model — the two pricing-condition tables
-- and some columns are removed later via model_deviation during the run, and
-- delivery is ADDED then; do not pre-apply those here.
--
-- SHAPE: normalized 3NF SSOT. Cross-domain FKs (customer/pricing/manufacturing/
-- billing/product_catalog/product_lifecycle/supply_chain) are DEFERRED — kept as
-- plain nullable columns (business keys retained), no constraint. Only the
-- within-sales_order FK edges are declared.
--
-- READ-ONLY model location (conventions -> vibe_model.*). Builds LAND elsewhere
-- (catalogs.silver / .gold). Never point a build here.
--
-- Run once. Idempotent: CREATE OR REPLACE. Catalog/schema are runtime widgets.
-- =============================================================================

-- COMMAND ----------
CREATE WIDGET TEXT vibe_model_catalog DEFAULT 'meridian_model';
CREATE WIDGET TEXT vibe_model_schema  DEFAULT 'sales_order_model';

-- COMMAND ----------
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:vibe_model_catalog || '.' || :vibe_model_schema);
USE CATALOG IDENTIFIER(:vibe_model_catalog);
USE SCHEMA  IDENTIFIER(:vibe_model_schema);

-- COMMAND ----------
-- ============================== TARGET SHELLS ================================


-- COMMAND ----------
-- sales_contract
CREATE OR REPLACE TABLE `sales_contract` (
  sales_contract_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a sales contract record in the lakehouse silver layer.',
  account_assignment_group STRING COMMENT 'SAP SD account assignment group for the customer, controlling the revenue account determination and GL (General Ledger) posting logic for invoices raised under this contract. Critical for financial reporting accuracy.',
  approved_timestamp TIMESTAMP COMMENT 'Timestamp when the sales contract received final commercial or legal approval, enabling it to transition to active status. Supports approval workflow audit trails required under SOX internal controls.',
  billing_plan_type STRING COMMENT 'Defines the invoicing cadence and trigger for the contract. Milestone billing ties invoices to project deliverables; periodic billing generates invoices on a calendar schedule; on-delivery billing triggers at goods issue; subscription and usage-based billing align with Zuora billing engine patterns.. Valid values are `milestone|periodic|on_delivery|subscription|usage_based`',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the commercial channel through which the contract was established. Direct/OE contracts are placed by end-customers or original equipment manufacturers directly; distributor and dealer contracts flow through intermediary channel partners. Required per VREQ-009 to avoid separate domain copies per channel.. Valid values are `direct_oe|distributor|dealer|oem|ecommerce|intercompany`',
  contract_category STRING COMMENT 'Business classification of the contract by strategic importance and commercial relationship type. Strategic and preferred-supplier contracts may carry special SLA commitments and executive visibility; spot contracts are one-time or short-term.. Valid values are `standard|strategic|preferred_supplier|spot|consignment|intercompany`',
  contract_name STRING COMMENT 'Descriptive business name or title of the sales contract as agreed with the customer, used for identification in commercial documents and reporting dashboards.',
  contract_number STRING COMMENT 'Natural business key for the sales contract as assigned by the source system (SAP SD contract document number). Enables cross-system traceability and is the primary reference used in commercial communications.',
  contract_owner STRING COMMENT 'Name or employee identifier of the internal sales representative or account manager responsible for managing this contract. Used for accountability tracking, renewal workflows, and CRM alignment with Salesforce.',
  contract_status STRING COMMENT 'Current lifecycle status of the sales contract. Drives order promising, ATP/CTP checks, and revenue recognition eligibility. Active contracts allow release orders; expired or cancelled contracts block new releases. [ENUM-REF-CANDIDATE: draft|active|suspended|expired|cancelled|closed|pending_approval — 7 candidates stripped; promote to reference product]',
  contract_type STRING COMMENT 'Classifies the commercial agreement structure. Quantity contracts commit to a target volume; value contracts commit to a target spend; scheduling agreements define a delivery cadence; blanket orders cover recurring purchases; framework agreements establish general terms without specific commitments.. Valid values are `quantity_contract|value_contract|scheduling_agreement|blanket_order|framework_agreement`',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when the sales contract record was first created in the source system. Used for audit trail, SLA measurement, and data lineage tracking.',
  credit_limit_override BOOLEAN COMMENT 'Indicates whether release orders under this contract are exempt from standard credit limit checks. Typically set for strategic customers with pre-approved credit arrangements or intercompany transactions.',
  crm_opportunity_number STRING COMMENT 'Reference to the originating Salesforce CRM opportunity that led to this contract. Enables quote-to-order traceability and pipeline-to-revenue analytics across Salesforce and SAP SD.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the contract target value, released value, and pricing are denominated (e.g., USD, EUR, GBP). Required for multi-currency financial consolidation under IFRS/GAAP.. Valid values are `^[A-Z]{3}$`',
  delivery_priority STRING COMMENT 'Priority level assigned to fulfillment of release orders under this contract. Influences APS scheduling, warehouse pick sequencing, and OTD (On-Time Delivery) SLA commitments.. Valid values are `critical|high|standard|low`',
  end_date DATE COMMENT 'Calendar date on which the sales contract expires and no further release orders may be placed. Used for OTD (On-Time Delivery) planning and contract renewal workflows.',
  external_reference_number STRING COMMENT 'Customer-assigned contract or purchase order reference number used in the customers own procurement system. Required for invoice matching and dispute resolution in B2B transactions.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms 2020) code defining the transfer of risk, cost, and responsibility between seller and buyer for goods shipped under this contract. Impacts logistics cost allocation and revenue recognition timing. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  incoterms_location STRING COMMENT 'Named place or port associated with the Incoterms code (e.g., Port of Rotterdam for FOB). Required to fully specify delivery obligations and risk transfer point per Incoterms 2020 rules.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent change to the sales contract record in the source system. Supports change detection in ETL pipelines and audit compliance.',
  minimum_order_value DECIMAL(18,2) COMMENT 'Minimum monetary value required per release order placed against this contract. Enforces commercial terms and prevents uneconomical small orders that erode margin.',
  payment_terms_code STRING COMMENT 'Code identifying the agreed payment terms for invoices raised under this contract (e.g., NET30, 2/10NET30). Drives accounts receivable (AR) due date calculation and early payment discount eligibility.',
  plant_code STRING COMMENT 'Manufacturing or distribution plant code responsible for fulfilling the contract. Supports multi-site rule (VREQ-008) by embedding plant as an attribute rather than creating separate domain copies per site.',
  pricing_procedure_code STRING COMMENT 'SAP SD pricing procedure assigned to the contract, determining the sequence of condition types (base price, discounts, surcharges, taxes) applied when creating release orders. Distinct from the price terms owned by pricing.contract_price.',
  quantity_uom STRING COMMENT 'Unit of measure in which the target quantity and released quantity are expressed (e.g., EA, KG, M, PCE). Aligns with the material master unit of measure in SAP MM.',
  released_quantity DECIMAL(18,2) COMMENT 'Cumulative quantity already released against the contract through release orders or delivery schedules. Compared against target_quantity to determine remaining open commitment and trigger renewal alerts.',
  released_value DECIMAL(18,2) COMMENT 'Cumulative monetary value already released against the contract through release orders. Compared against target_value to determine remaining open commitment and support revenue recognition schedules.',
  renewal_notice_days STRING COMMENT 'Number of calendar days before contract end_date that a renewal notification must be issued to the customer or account team. Supports automated contract lifecycle alerts and prevents unintended lapses.',
  renewal_type STRING COMMENT 'Specifies whether the contract automatically renews at expiry, requires manual renewal action, or terminates without renewal. Drives contract lifecycle management workflows and renewal notification triggers.. Valid values are `auto_renew|manual_renew|no_renewal`',
  shipping_condition STRING COMMENT 'SAP SD shipping condition code specifying the mode and urgency of transportation for deliveries under this contract (e.g., standard ground, express air, customer pickup). Drives route determination and carrier selection.',
  signed_date DATE COMMENT 'Date on which the sales contract was formally executed and signed by both parties. Establishes the legal commencement point for revenue recognition and obligation tracking under IFRS 15.',
  source_system STRING COMMENT 'Identifies the originating operational system of record from which this sales contract was ingested. Supports SSOT rule (VREQ-004) by exposing the source system as an attribute rather than creating separate domain copies per system. SAP SD is the primary source; Salesforce CRM may originate contracts from opportunity-to-contract workflows; Oracle ERP covers M&A-acquired entities.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  start_date DATE COMMENT 'Calendar date on which the sales contract becomes effective and release orders may be placed against it. Used for contract validity checks during order entry.',
  target_quantity DECIMAL(18,2) COMMENT 'Total committed volume (in the contract unit of measure) that the customer agrees to purchase over the contract period. Applicable primarily to quantity contracts and scheduling agreements. Used for MRP/APS demand planning and volume discount validation.',
  target_value DECIMAL(18,2) COMMENT 'Total committed monetary value the customer agrees to spend over the contract period. Applicable primarily to value contracts. Used for revenue forecasting, credit limit checks, and IFRS 15 transaction price allocation.',
  CONSTRAINT `pk_sales_contract` PRIMARY KEY (`sales_contract_id`)
)
COMMENT 'Sales contract master record representing a long-term commercial agreement with a B2B customer establishing framework pricing, volume commitments, and delivery terms over a defined period. Captures contract number, contract type (quantity contract, value contract, scheduling agreement), contract start date, contract end date, target quantity, target value, released quantity, released value, contract status (active, expired, cancelled, suspended), channel_type discriminator, sales organization, distribution channel, incoterms, payment terms, and source_system (SAP SD). Distinct from pricing.contract_price which owns the price terms — this entity owns the commercial commitment framework.';

-- COMMAND ----------
-- sales_contract_line
CREATE OR REPLACE TABLE `sales_contract_line` (
  sales_contract_line_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying an individual line item within a sales contract in the lakehouse silver layer.',
  plant_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to manufacturing.plant',
  sales_contract_id BIGINT COMMENT 'Foreign key linking to sales_order.sales_contract. Business justification: sales_contract_line is a child of sales_contract (line-to-header rule). Has contract_number (STRING) as a denormalized reference but no FK. Adding sales_contract_id FK establishes the proper parent-child relationship for contract fulfillment tracking, release order validation, and contract utilization analytics.',
  sku_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to product_catalog.sku',
  billing_block_code STRING COMMENT 'Code indicating whether billing is blocked for this contract line and the reason for the block (e.g., credit hold, pricing dispute, approval pending). Null if no billing block is active.',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the commercial channel for this contract line per VREQ-009. Differentiates direct/OE (Original Equipment) orders from distributor and dealer orders without creating separate tables per channel.. Valid values are `direct_oe|distributor|dealer|intercompany|ecommerce|service`',
  contract_currency STRING COMMENT 'ISO 4217 three-letter currency code in which the target value, released value, and open value for this contract line are denominated (e.g., USD, EUR, GBP).. Valid values are `^[A-Z]{3}$`',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this contract line record was originally created in the source system, in ISO 8601 format with timezone offset.',
  delivery_block_code STRING COMMENT 'Code indicating whether delivery is blocked for this contract line and the reason (e.g., export control hold, credit block, quality hold). Null if no delivery block is active.',
  delivery_schedule_type STRING COMMENT 'Type of delivery scheduling arrangement for this contract line, indicating whether releases are governed by JIT (Just-in-Time) call-offs, forecast-based schedules, firm orders, blanket releases, or Kanban signals.. Valid values are `jit|forecast|firm|blanket|kanban`',
  distribution_channel_code STRING COMMENT 'SAP SD distribution channel code indicating the route to market for this contract line (e.g., direct sales, dealer, distributor). Complements the channel_type discriminator.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms 2020) code defining the delivery obligations, risk transfer point, and cost responsibilities between seller and buyer for this contract line. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  item_category_code STRING COMMENT 'SAP SD item category code controlling the behavior of this contract line (e.g., WKN for value contract item, MKN for material contract item). Determines pricing, delivery, and billing rules.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this contract line record in the source system. Used for change tracking, delta processing, and audit trail purposes.',
  line_number STRING COMMENT 'Sequential line item number within the parent sales contract, used to order and reference individual product commitments. Corresponds to SAP SD contract item number.',
  line_status STRING COMMENT 'Current fulfillment status of the contract line item, tracking progression from open commitment through partial or full release to closure or cancellation.. Valid values are `open|partially_released|fully_released|closed|cancelled|blocked`',
  material_number STRING COMMENT 'Source system material or product identifier (e.g., SAP material number) representing the specific product or component committed under this contract line.',
  minimum_order_quantity DECIMAL(18,2) COMMENT 'Minimum quantity that must be included in each release order placed against this contract line. Enforces supplier or production MOQ constraints agreed in the contract.',
  net_price DECIMAL(18,2) COMMENT 'Negotiated net unit price for the product on this contract line after all applicable discounts and surcharges, expressed in the contract currency per unit of measure.',
  open_quantity DECIMAL(18,2) COMMENT 'Remaining quantity yet to be released or fulfilled on this contract line (target quantity minus released quantity). Drives backlog and demand planning visibility.',
  open_value DECIMAL(18,2) COMMENT 'Remaining monetary value yet to be released on this contract line (target value minus released value). Key metric for backlog and revenue pipeline reporting.',
  over_delivery_tolerance_pct DECIMAL(18,2) COMMENT 'Maximum percentage by which the delivered quantity may exceed the released quantity for this contract line without triggering a rejection or exception. Expressed as a percentage of the release quantity.',
  price_unit DECIMAL(18,2) COMMENT 'Quantity basis for the net price (e.g., price per 1 unit, per 100 units, per 1000 units). Enables correct price calculation when pricing is expressed per multiple units.',
  pricing_date DATE COMMENT 'Date used to determine applicable pricing conditions and exchange rates for this contract line. May differ from contract creation date for forward-dated pricing agreements.',
  product_hierarchy_code STRING COMMENT 'Product hierarchy classification code assigned to this contract line item, enabling aggregated reporting across product families, segments, and business lines.',
  rejection_reason_code STRING COMMENT 'Code indicating the reason this contract line was rejected or cancelled, if applicable. Used for contract performance analysis and customer relationship management.',
  released_quantity DECIMAL(18,2) COMMENT 'Cumulative quantity already released against this contract line via release orders or delivery schedules. Used to track fulfillment progress against the target commitment.',
  released_value DECIMAL(18,2) COMMENT 'Cumulative monetary value of all release orders issued against this contract line. Used for revenue recognition tracking and contract utilization reporting.',
  sales_org_code STRING COMMENT 'SAP SD sales organization code responsible for this contract line, representing the legal entity and sales structure under which the contract is managed.',
  source_system STRING COMMENT 'Identifier of the originating operational system of record for this contract line per VREQ-004 SSOT rule. Supports multi-ERP environments from M&A activity without duplicating domains per source system.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP_CLOUD`',
  source_system_line_key STRING COMMENT 'Natural key of this contract line in the originating source system (e.g., SAP SD contract number + item number concatenation). Enables traceability and reconciliation back to the system of record.',
  target_quantity DECIMAL(18,2) COMMENT 'Total committed quantity of the product agreed upon in the contract line. Represents the full volume obligation the customer has committed to purchase over the contract period.',
  target_value DECIMAL(18,2) COMMENT 'Total contracted monetary value committed for this line item over the contract period. Represents the full revenue obligation in the contract currency.',
  under_delivery_tolerance_pct DECIMAL(18,2) COMMENT 'Maximum percentage by which the delivered quantity may fall short of the released quantity for this contract line without triggering a shortage exception. Expressed as a percentage of the release quantity.',
  unit_of_measure STRING COMMENT 'Unit of measure for all quantity fields on this contract line (e.g., EA, KG, M, L, PC). Follows ISO 80000 standard unit codes as configured in the source ERP.',
  valid_from_date DATE COMMENT 'Start date from which this contract line is effective and release orders can be placed against it. Defines the beginning of the contractual commitment window.',
  valid_to_date DATE COMMENT 'Expiry date after which no further release orders can be placed against this contract line. Defines the end of the contractual commitment window.',
  CONSTRAINT `pk_sales_contract_line` PRIMARY KEY (`sales_contract_line_id`),
  CONSTRAINT `fk_sales_order_sales_contract_line_sales_contract_id` FOREIGN KEY (`sales_contract_id`) REFERENCES `sales_contract` (`sales_contract_id`)
)
COMMENT 'Individual line item within a sales contract capturing the product-level commitment detail. Captures line number, material/SKU reference, target quantity, target value, released quantity, released value, open quantity, open value, unit of measure, plant, and source_system. Enables contract fulfillment tracking and release order management against long-term customer commitments.';

-- COMMAND ----------
-- quotation
CREATE OR REPLACE TABLE `quotation` (
  quotation_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a sales quotation record in the lakehouse silver layer.',
  account_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to customer.account. Business justification: Quotations are prepared for specific customer accounts. This FK establishes the authoritative link from the quotation to the customer SSOT, enabling customer-level quote-to-order conversion analytics.',
  price_list_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to pricing.price_list.price_list_id',
  sales_contract_id BIGINT COMMENT 'Foreign key linking to sales_order.sales_contract. Business justification: Quotation can reference a master sales contract (blanket agreement) that it is pricing against. Business reality: quotations often price against existing contract terms to ensure consistency. This ena',
  approved_timestamp TIMESTAMP COMMENT 'Date and time when the quotation was formally approved by the authorized approver (e.g., sales manager or pricing authority). Required for discount approval audit trails and SOX compliance.',
  approver_name STRING COMMENT 'Name or employee ID of the individual who approved the quotation, particularly relevant when discount thresholds require management authorization. Supports SOX audit and delegation-of-authority compliance.',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the commercial channel through which the quotation is issued. Differentiates direct/OE (Original Equipment) orders from distributor and dealer orders within a single domain per VREQ-009. Enables channel-specific pricing, margin, and OTD analytics.. Valid values are `direct_oe|distributor|dealer|ecommerce|intercompany`',
  competitor_reference STRING COMMENT 'Name or identifier of the primary competitor against whom this quotation is competing. Supports win/loss analysis, competitive intelligence, and pricing strategy refinement.',
  confirmed_delivery_date DATE COMMENT 'Delivery date confirmed by manufacturing and supply chain after ATP/CTP check. May differ from requested delivery date. Baseline for OTD performance measurement.',
  conversion_probability DECIMAL(18,2) COMMENT 'Estimated probability (0.00–100.00%) that this quotation will be accepted and converted to a sales order. Used in weighted pipeline forecasting and APS demand signal generation.',
  converted_order_reference STRING COMMENT 'Reference number of the sales order created upon acceptance of this quotation. Populated when quotation_status transitions to converted. Enables end-to-end quote-to-order traceability.',
  created_timestamp TIMESTAMP COMMENT 'Date and time when the quotation record was first created in the source system. Used for pipeline aging, SLA compliance, and audit trail.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the quotation value is denominated (e.g., USD, EUR, GBP). Required for multi-currency reporting and FX conversion in financial consolidation.. Valid values are `^[A-Z]{3}$`',
  customer_reference_number STRING COMMENT 'Customers own reference or RFQ (Request for Quotation) number provided by the buyer for cross-referencing with their procurement system. Required for B2B order matching and dispute resolution.',
  discount_percent DECIMAL(18,2) COMMENT 'Overall header-level discount percentage applied to the quotation. Supports margin analysis, discount approval workflows, and channel discount compliance monitoring.',
  exchange_rate DECIMAL(18,2) COMMENT 'Foreign exchange rate applied to convert the transaction currency to USD on the quotation date. Stored for auditability and financial reconciliation.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms 2020) code defining the delivery obligations, risk transfer point, and cost responsibilities between seller and buyer for this quotation. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  incoterms_location STRING COMMENT 'Named place or port associated with the Incoterms code (e.g., Port of Hamburg for FOB). Required to fully specify delivery terms per Incoterms 2020 rules.',
  last_modified_timestamp TIMESTAMP COMMENT 'Date and time of the most recent modification to the quotation record in the source system. Supports change detection, incremental data loading, and audit compliance.',
  number STRING COMMENT 'Business-facing natural key for the quotation as assigned by the source system (SAP SD or Salesforce CRM). Used for cross-system traceability and customer-facing references.. Valid values are `^[A-Z0-9-]{5,30}$`',
  opportunity_reference STRING COMMENT 'Reference identifier of the linked CRM opportunity from which this quotation was generated. Enables traceability from opportunity through quotation to sales order in the quote-to-order workflow.',
  payment_terms_code STRING COMMENT 'Code identifying the agreed payment terms for this quotation (e.g., NET30, 2/10NET30). Drives accounts receivable planning and cash flow forecasting upon order conversion.',
  plant_code STRING COMMENT 'Manufacturing plant or fulfillment site code from which the quoted products are planned to be sourced or shipped. Modeled as an attribute per VREQ-008 multi-site rule — no separate domain per plant.',
  priority STRING COMMENT 'Business priority assigned to the quotation indicating its strategic importance. Used to prioritize sales engineering effort, capacity reservation, and management review.. Valid values are `low|medium|high|strategic`',
  quotation_date DATE COMMENT 'Calendar date on which the quotation was formally created and issued to the prospective customer. Used as the baseline date for validity period calculations and pipeline aging.',
  quotation_status STRING COMMENT 'Current lifecycle status of the sales quotation. Converted indicates the quotation has been accepted and a sales order has been created. Drives pipeline reporting and win/loss analytics.. Valid values are `open|accepted|rejected|expired|converted|cancelled`',
  quotation_type STRING COMMENT 'Classification of the quotation by commercial nature. Distinguishes standard product quotations from project-based, framework agreement, service, spare parts, or subscription quotations. Drives pricing logic and contract template selection.. Valid values are `standard|framework|project|service|spare_parts|subscription`',
  quoted_value DECIMAL(18,2) COMMENT 'Total net commercial value of the quotation in the transaction currency, representing the sum of all line items before tax. Core metric for pipeline valuation, revenue forecasting, and win/loss analysis.',
  quoted_value_usd DECIMAL(18,2) COMMENT 'Total quoted value converted to USD at the exchange rate applicable on the quotation date. Enables consistent global pipeline reporting and cross-currency revenue analytics without requiring runtime FX conversion.',
  region_code STRING COMMENT 'Geographic sales region code associated with the quotation (e.g., AMER, EMEA, APAC). Modeled as an attribute per VREQ-008 — no separate domain per region. Supports regional revenue and pipeline analytics.',
  requested_delivery_date DATE COMMENT 'Customer-requested delivery date for the quoted products. Used in ATP/CTP (Available-to-Promise / Capable-to-Promise) checks and OTD (On-Time Delivery) commitment tracking.',
  revision_number STRING COMMENT 'Sequential revision counter incremented each time the quotation is amended and reissued to the customer. Supports version control and audit trail for commercial negotiations.',
  sales_office STRING COMMENT 'SAP SD sales office code representing the physical or organizational sales office responsible for this quotation. Supports territory management and regional sales reporting.',
  sales_representative STRING COMMENT 'Name or employee ID of the sales representative responsible for creating and managing this quotation. Used for sales performance reporting, commission calculation, and accountability tracking.',
  source_system STRING COMMENT 'Identifies the originating operational system of record for this quotation record, supporting SSOT governance across multi-ERP and multi-CRM landscapes resulting from M&A activity. Per VREQ-004, a single domain serves all source systems.. Valid values are `SAP_SD|SALESFORCE_CRM`',
  tax_amount DECIMAL(18,2) COMMENT 'Total tax amount calculated on the quotation in the transaction currency. Required for VAT/GST compliance reporting and revenue recognition under IFRS 15.',
  valid_from_date DATE COMMENT 'Start date of the quotation validity window. The quoted price and commercial terms are binding from this date. Required for contract compliance and price protection tracking.',
  valid_to_date DATE COMMENT 'Expiry date of the quotation validity window. After this date the quotation status transitions to expired unless accepted or extended. Critical for pipeline hygiene and revenue forecasting.',
  CONSTRAINT `pk_quotation` PRIMARY KEY (`quotation_id`),
  CONSTRAINT `fk_sales_order_quotation_sales_contract_id` FOREIGN KEY (`sales_contract_id`) REFERENCES `sales_contract` (`sales_contract_id`)
)
COMMENT 'Sales quotation master record representing a formal price offer presented to a B2B customer prior to order placement. Captures quotation number, quotation date, valid-from date, valid-to date, quotation status (open, accepted, rejected, expired, converted), channel_type (direct/OE vs distributor/dealer), total quoted value, currency, probability of conversion, linked opportunity reference, sales organization, distribution channel, incoterms, payment terms, and source_system (Salesforce CRM or SAP SD). SSOT for the pre-order commercial offer.';

-- COMMAND ----------
-- order
CREATE OR REPLACE TABLE `order` (
  order_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a sales order record in the lakehouse silver layer. System-generated BIGINT used as the canonical identifier across all downstream joins.',
  account_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to customer.account. Business justification: Sales orders belong to customer accounts. This FK establishes the authoritative link from the sales order to the customer SSOT, enabling customer-level order analytics and credit management.',
  contract_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to billing.billing_contract. Business justification: Sales orders can be linked to billing contracts (especially for project-based or subscription billing). This FK enables order-to-billing contract traceability for revenue recognition and billing plan ',
  plant_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to manufacturing.plant.plant_id',
  price_list_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to pricing.price_list. Business justification: Sales orders use specific price lists for pricing determination. This FK links the sales order to the pricing SSOT, enabling price list effectiveness analysis and order-to-price waterfall traceability',
  quotation_id BIGINT COMMENT 'Foreign key linking to sales_order.quotation. Business justification: order has quote_number (STRING) referencing the originating quotation that was converted to this order. Adding quotation_id FK normalizes this relationship, enabling quote-to-order conversion tracking',
  sales_contract_id BIGINT COMMENT 'Foreign key linking to sales_order.sales_contract. Business justification: order has contract_number (STRING) referencing the sales contract it was released against. Adding sales_contract_id FK normalizes this relationship, enabling proper contract release tracking, quantity',
  actual_delivery_date DATE COMMENT 'The date on which the goods were actually delivered to the customer. Compared against confirmed_delivery_date to compute On-Time Delivery (OTD) performance. Populated upon goods issue confirmation.',
  billing_block STRING COMMENT 'Indicates whether the order has a billing block preventing invoice creation. A non-none value signals that the order cannot be invoiced until the block is resolved. Used for revenue recognition compliance and AR management.. Valid values are `none|credit_hold|pricing_incomplete|contract_pending|manual_hold`',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the commercial channel through which the order was placed. direct_oe indicates Original Equipment (OE) or direct B2B orders; distributor and dealer indicate indirect channel orders. Required per VREQ-009 — no separate tables or domains per channel.. Valid values are `direct_oe|distributor|dealer|ecommerce|intercompany`',
  confirmed_delivery_date DATE COMMENT 'The delivery date confirmed by the system after Available-to-Promise (ATP) or Capable-to-Promise (CTP) check. May differ from the requested delivery date when supply constraints exist. Primary date used for OTD tracking.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when the sales order record was first created in the source system. Used for order aging analysis, SLA compliance tracking, and audit trail.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the order is denominated (e.g., USD, EUR, GBP). Used for multi-currency financial consolidation and FX reporting.. Valid values are `^[A-Z]{3}$`',
  customer_po_date DATE COMMENT 'The date on which the customer issued their purchase order. Used for contractual lead time calculations and dispute resolution when delivery timing is contested.',
  customer_po_number STRING COMMENT 'The customers own purchase order number referencing this sales order. Required for invoice matching, customer remittance reconciliation, and dispute resolution. Key cross-reference for B2B order management.',
  delivery_block STRING COMMENT 'Indicates whether the order has a delivery block preventing shipment processing. Supports credit management, export control compliance, and quality hold workflows.. Valid values are `none|credit_hold|export_control|quality_hold|customer_request`',
  exchange_rate DECIMAL(18,2) COMMENT 'Foreign exchange rate applied to convert the order currency to the company code local currency at the time of order creation. Used for financial consolidation and FX gain/loss reporting.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms 2020) code defining the transfer of risk, cost, and responsibility between seller and buyer for the shipment. Governs logistics obligations and revenue recognition timing. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  is_export_controlled BOOLEAN COMMENT 'Indicates whether the order is subject to export control regulations (e.g., EAR, ITAR, EU Dual-Use). True triggers export license verification before shipment. Critical for trade compliance in industrial automation and electrification products.',
  is_otd_compliant BOOLEAN COMMENT 'Indicates whether the order was delivered on or before the confirmed delivery date. True when actual_delivery_date <= confirmed_delivery_date. Key KPI flag for OTD reporting and customer scorecard analytics.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to the sales order record in the source system. Used for change detection in ETL pipelines and audit compliance.',
  net_value DECIMAL(18,2) COMMENT 'Total net commercial value of the sales order after discounts and before taxes, expressed in the order currency. Represents the revenue commitment for this order. Used for revenue recognition, forecasting, and financial reporting.',
  number STRING COMMENT 'Natural business key for the sales order as assigned by the originating source system (SAP SD order number or Salesforce CRM order number). Used for cross-system reconciliation and customer-facing references.',
  opportunity_number STRING COMMENT 'Reference to the Salesforce CRM opportunity that originated this sales order. Enables quote-to-order traceability, win/loss analysis, and sales pipeline-to-revenue conversion reporting.',
  order_date DATE COMMENT 'The calendar date on which the sales order was created and confirmed in the source system. Serves as the commercial commitment date for revenue recognition and OTD baseline calculations.',
  order_status STRING COMMENT 'Current lifecycle status of the sales order. Drives downstream processing in MES, logistics, and billing. Blocked indicates a credit or compliance hold preventing further processing. [ENUM-REF-CANDIDATE: open|in_process|shipped|invoiced|closed|cancelled|blocked — 7 candidates stripped; promote to reference product]',
  order_type STRING COMMENT 'Classifies the commercial nature of the sales order. Standard orders represent one-time purchases; blanket orders cover recurring releases against a master agreement; consignment orders transfer goods to customer premises without immediate revenue recognition; intercompany orders represent intra-entity transactions.. Valid values are `standard|blanket|consignment|intercompany|returns|sample`',
  payment_terms_code STRING COMMENT 'Code identifying the agreed payment terms for the order (e.g., NET30, NET60, 2/10NET30). Drives accounts receivable due date calculation and cash flow forecasting.',
  priority STRING COMMENT 'Business priority level assigned to the order, influencing production scheduling, warehouse picking sequence, and logistics allocation. Critical orders may trigger expedite workflows in MES and APS.. Valid values are `critical|high|medium|low`',
  requested_delivery_date DATE COMMENT 'The delivery date requested by the customer at the time of order placement. Used as the baseline for On-Time Delivery (OTD) performance measurement and ATP/CTP promising.',
  sales_group STRING COMMENT 'Code identifying the sales group or team within the sales office responsible for the order. Used for sales performance reporting and commission calculations.',
  sales_office STRING COMMENT 'Code identifying the sales office or regional sales unit responsible for managing the customer relationship and order. Supports multi-site reporting per VREQ-008 without duplicating domains per region.',
  ship_to_country_code STRING COMMENT 'ISO 3166-1 alpha-3 country code of the customers ship-to address. Used for trade compliance, export control screening, tax jurisdiction determination, and logistics routing.. Valid values are `^[A-Z]{3}$`',
  ship_to_region STRING COMMENT 'State, province, or region code of the customers ship-to address. Used for tax jurisdiction determination and regional sales analytics. Modeled as attribute per VREQ-008 — no separate domain per region.',
  shipping_terms_code STRING COMMENT 'Code defining the agreed shipping conditions including carrier responsibility, freight cost allocation, and delivery mode. Complements Incoterms with operational shipping instructions.',
  source_system STRING COMMENT 'Identifies the originating operational system of record for this sales order record. Supports SSOT rule (VREQ-004) by exposing provenance rather than duplicating domains per system. SAP_SD indicates SAP S/4HANA SD module; SALESFORCE_CRM indicates Salesforce CRM.. Valid values are `SAP_SD|SALESFORCE_CRM`',
  source_system_order_reference STRING COMMENT 'The native primary key or document number of the sales order in the originating source system (e.g., SAP internal document number or Salesforce record ID). Enables traceability back to the system of record.',
  tax_amount DECIMAL(18,2) COMMENT 'Total tax amount applicable to the sales order, expressed in the order currency. Includes VAT, GST, or applicable sales tax based on the ship-to jurisdiction. Required for financial reporting and tax compliance.',
  CONSTRAINT `pk_order` PRIMARY KEY (`order_id`),
  CONSTRAINT `fk_sales_order_order_sales_contract_id` FOREIGN KEY (`sales_contract_id`) REFERENCES `sales_contract` (`sales_contract_id`),
  CONSTRAINT `fk_sales_order_order_quotation_id` FOREIGN KEY (`quotation_id`) REFERENCES `quotation` (`quotation_id`)
)
COMMENT 'Core sales order master record representing a confirmed commercial commitment from a B2B customer to purchase products or services. Captures order number, order type (standard, blanket, consignment, intercompany), channel_type discriminator (direct/OE vs distributor/dealer), order date, requested delivery date, confirmed delivery date, order status (open, in-process, shipped, invoiced, closed, cancelled), total order value, currency, incoterms, payment terms, shipping terms, plant, sales organization, distribution channel, division, sales office, sales group, source_system (SAP SD or Salesforce CRM), and OTD tracking flags. SSOT for the sales order transaction — sourced from SAP S/4HANA SD module and Salesforce CRM.';

-- COMMAND ----------
-- order_line
CREATE OR REPLACE TABLE `order_line` (
  order_line_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying each individual line item within a sales order in the lakehouse Silver layer. System-generated BIGINT for internal joins and lineage tracking.',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: order_line is a child of order (line-to-header rule). order_line has no FK to its parent order — only a denormalized sales_order_number string. Adding order_id FK establishes the proper parent-child r',
  part_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.part. Business justification: Industrial manufacturers sell custom/configured automation systems and electrification solutions requiring engineer-to-order (ETO) and configure-to-order (CTO) flows. Order lines must reference engine',
  plant_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to manufacturing.plant.plant_id',
  product_specification_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.product_specification. Business justification: Custom industrial equipment orders (voltage class, IP rating, functional safety level, operating temp ranges) require product specification references for compliance validation, manufacturing feasibil',
  sales_contract_line_id BIGINT COMMENT 'Foreign key linking to sales_order.sales_contract_line. Business justification: Order line can release against a sales contract line (contract release order). Business reality: blanket contracts have target quantities, order lines release against them incrementally. This is stand',
  sku_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_catalog.sku. Business justification: Order lines reference specific SKUs. sku_code is visible on order_line and becomes redundant once sku_id FK is established to the product catalog SSOT for product-level order analytics.',
  actual_goods_issue_date DATE COMMENT 'The date on which goods were physically issued from the warehouse and shipped to the customer for this order line. Used as the actual delivery date for OTD (On-Time Delivery) performance measurement against confirmed_delivery_date.',
  channel_type STRING COMMENT 'Discriminator attribute identifying the sales channel through which this order line was placed. Distinguishes direct/OE (Original Equipment) orders from distributor, dealer, intercompany, e-commerce, and aftermarket channels. Mandatory per VREQ-009 — no separate tables or domains per channel.. Valid values are `DIRECT_OE|DISTRIBUTOR|DEALER|INTERCOMPANY|ECOMMERCE|AFTERMARKET`',
  configuration_key STRING COMMENT 'Identifier for the specific product configuration selected for configurable products (variant configuration). Links to the configuration model in PLM/ERP. Null for standard non-configurable products.',
  confirmed_delivery_date DATE COMMENT 'The delivery date confirmed by the system following ATP/CTP availability check and production/supply planning. Used for OTD (On-Time Delivery) measurement by comparing against actual goods issue date.',
  confirmed_quantity DECIMAL(18,2) COMMENT 'The quantity confirmed as available for delivery following ATP (Available-to-Promise) or CTP (Capable-to-Promise) check. May be less than order_quantity in cases of partial availability or capacity constraints.',
  cost_center_code STRING COMMENT 'Cost center associated with this order line for internal cost allocation and management accounting purposes. Used in conjunction with profit_center_code for full P&L attribution in SAP CO.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this order line record was first created in the source system. Used for audit trail, data lineage, and order intake timing analysis. Formatted as yyyy-MM-ddTHH:mm:ss.SSSXXX per model conventions.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which all monetary amounts on this order line (list_price, net_price, net_value, discount_amount, surcharge_amount) are expressed. Supports multi-currency order management.. Valid values are `^[A-Z]{3}$`',
  delivered_quantity DECIMAL(18,2) COMMENT 'Cumulative quantity of this order line that has been physically shipped and goods-issued to the customer across all associated delivery documents. Supports partial delivery tracking and OTD (On-Time Delivery) analysis.',
  discount_amount DECIMAL(18,2) COMMENT 'Total monetary discount applied to this order line, representing the reduction from list price to net price. Includes all discount condition types (customer discount, volume discount, promotional discount). Used for margin and pricing analytics.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms 2020) code defining the delivery obligations, risk transfer point, and cost responsibilities between seller and buyer for this order line. Critical for logistics, customs, and revenue recognition. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  invoiced_quantity DECIMAL(18,2) COMMENT 'Cumulative quantity of this order line that has been billed to the customer in issued invoices. Used for revenue recognition, billing completeness checks, and order-to-cash reconciliation.',
  is_free_of_charge BOOLEAN COMMENT 'Indicates whether this order line is a free-of-charge delivery (e.g., sample, warranty replacement, goodwill gesture). When true, net_value is zero and the line is excluded from revenue reporting but included in cost-of-goods-sold tracking.',
  is_partial_delivery_allowed BOOLEAN COMMENT 'Indicates whether partial delivery is permitted for this order line. When false, the full confirmed_quantity must be shipped in a single delivery. Drives delivery scheduling and warehouse fulfillment logic.',
  item_category_code STRING COMMENT 'SAP SD item category code controlling the processing behavior of this order line (e.g., TAN for standard item, TAK for consignment, TAD for service, TANN for free-of-charge). Determines billing relevance, delivery relevance, and pricing behavior.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this order line record in the source system. Used for change detection, incremental data loading, and audit compliance. Formatted as yyyy-MM-ddTHH:mm:ss.SSSXXX per model conventions.',
  line_number STRING COMMENT 'Sequential line item number within the parent sales order, as assigned by the source system (SAP SD item number, e.g., 10, 20, 30). Used to preserve the original order structure and support multi-line order management.',
  line_status STRING COMMENT 'Current processing status of the sales order line reflecting its position in the order-to-cash lifecycle. Drives workflow routing, reporting, and customer communication. Aligned with SAP SD overall delivery and billing status. [ENUM-REF-CANDIDATE: OPEN|IN_PROCESS|PARTIALLY_DELIVERED|FULLY_DELIVERED|INVOICED|COMPLETED|REJECTED|CANCELLED|BLOCKED — 9 candidates stripped; promote to reference product]',
  list_price DECIMAL(18,2) COMMENT 'The standard catalog or list price per unit of measure for this material before any discounts, surcharges, or customer-specific pricing conditions are applied. Used as the baseline for discount analysis and margin reporting.',
  lot_number STRING COMMENT 'Production lot number (batch number) assigned to the material on this order line. Natural key for regulated and batch-managed products per VREQ-007. Enables traceability from customer order back to production lot, quality records, and supplier batches.',
  net_price DECIMAL(18,2) COMMENT 'The net price per unit of measure after all applicable pricing conditions (discounts, surcharges, customer agreements) have been applied. This is the effective unit price used to calculate the net line value.',
  net_value DECIMAL(18,2) COMMENT 'Total net value of this order line calculated as net_price multiplied by order_quantity, after all pricing conditions. Represents the revenue value of this line item. Used for order value reporting, revenue recognition, and financial analytics.',
  order_quantity DECIMAL(18,2) COMMENT 'The quantity of the SKU/material requested by the customer on this order line, expressed in the sales unit of measure. This is the original customer-requested quantity before any ATP/CTP confirmation.',
  over_delivery_tolerance_pct DECIMAL(18,2) COMMENT 'Maximum percentage by which the delivered quantity may exceed the confirmed order quantity without triggering a tolerance exception. Common in process industries and bulk material orders. Expressed as a percentage (e.g., 5.00 = 5%).',
  product_hierarchy_code STRING COMMENT 'Hierarchical product classification code assigned to the material on this order line, used for sales reporting, revenue analysis, and demand planning aggregation. Supports multi-level product hierarchy reporting (e.g., product family, product group, product line).',
  profit_center_code STRING COMMENT 'Controlling profit center assigned to this order line for internal profitability reporting and P&L attribution. Enables revenue and margin analysis by business unit, product line, or region within the finance domain.',
  requested_delivery_date DATE COMMENT 'The delivery date requested by the customer for this specific order line. May differ from the header-level requested delivery date for multi-line orders with staggered delivery requirements. Key input for ATP/CTP and delivery scheduling.',
  serial_number STRING COMMENT 'Unique serial number assigned to the specific unit shipped on this order line for serialized finished goods. Natural key per VREQ-007. Enables unit-level traceability, warranty registration, installed base management, and field service linkage.',
  source_system STRING COMMENT 'Identifies the originating operational system of record for this order line record, supporting SSOT governance across multi-ERP/CRM landscapes resulting from M&A activity. Enables lineage tracing back to SAP SD, Salesforce CRM, or Oracle ERP Cloud.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP_CLOUD`',
  source_system_line_key STRING COMMENT 'Natural key of the order line as it exists in the originating source system (e.g., SAP SD VBELN+POSNR concatenated key, Salesforce Order Product ID). Enables reconciliation and traceability back to the system of record.',
  storage_location_code STRING COMMENT 'Code identifying the specific storage location within the assigned plant from which this order line will be or has been fulfilled. Used for warehouse picking, inventory reservation, and WMS integration with Blue Yonder.',
  sub_line_number STRING COMMENT 'Sub-item or schedule line number within a sales order line, used for partial delivery schedules or configurable product sub-components (SAP SD schedule line ETENR). Null for lines without sub-items.',
  surcharge_amount DECIMAL(18,2) COMMENT 'Total monetary surcharge applied to this order line (e.g., freight surcharge, hazardous material surcharge, small order surcharge). Adds to the net price. Used for cost recovery and pricing transparency reporting.',
  under_delivery_tolerance_pct DECIMAL(18,2) COMMENT 'Maximum percentage by which the delivered quantity may fall short of the confirmed order quantity and still be considered complete. Expressed as a percentage (e.g., 3.00 = 3%). Prevents unnecessary open order residuals.',
  unit_of_measure STRING COMMENT 'The sales unit of measure in which order, confirmed, delivered, and invoiced quantities are expressed (e.g., EA for each, PC for piece, KG for kilogram, M for meter). Follows ISO 80000 unit codes as used in SAP.',
  CONSTRAINT `pk_order_line` PRIMARY KEY (`order_line_id`),
  CONSTRAINT `fk_sales_order_order_line_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`),
  CONSTRAINT `fk_sales_order_order_line_sales_contract_line_id` FOREIGN KEY (`sales_contract_line_id`) REFERENCES `sales_contract_line` (`sales_contract_line_id`)
)
COMMENT 'Individual line item within a sales order capturing the product-level detail for each SKU or configurable product ordered. Captures line number, material/SKU reference, order quantity, unit of measure, confirmed quantity, delivered quantity, invoiced quantity, requested delivery date per line, confirmed delivery date per line, line status, net price, list price, discount amount, surcharge amount, net value, plant assignment, storage location, batch/lot number, serial number (for serialized products), configuration key (for configurable products), rejection reason code, and source_system. Supports partial deliveries and multi-line order management in SAP SD.';

-- COMMAND ----------
-- quotation_line
CREATE OR REPLACE TABLE `quotation_line` (
  quotation_line_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying each individual line item within a sales quotation in the lakehouse silver layer.',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: quotation_line has sales_order_line_ref (STRING) tracking which order line resulted when the quote was accepted. This is a critical quote-to-order conversion tracking relationship. Adding converted_or',
  list_price_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to pricing.list_price.list_price_id',
  part_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.part. Business justification: Quotations for custom/engineered industrial products require engineering part references for technical feasibility assessment, cost estimation (material + labor), lead time calculation, and make-vs-bu',
  product_specification_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.product_specification. Business justification: Quotations must validate against product specifications to confirm technical feasibility (voltage class, power rating, environmental ratings, regulatory compliance scope). Critical for ensuring quoted',
  quotation_id BIGINT COMMENT 'Reference to the parent sales quotation header to which this line item belongs. Enables aggregation of all line items under a single quotation.',
  sku_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_catalog.sku. Business justification: Quotation lines reference specific SKUs for pricing. sku_code is visible on quotation_line and becomes redundant once sku_id FK is established to the product catalog SSOT.',
  bom_explosion_flag BOOLEAN COMMENT 'Indicates whether the Bill of Materials (BOM) has been exploded for this quotation line item to support cost estimation, component availability checks, or MRP planning during the quoting process.',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the sales channel for this quotation line. Differentiates direct/OE (Original Equipment) orders from distributor, dealer, OEM, or e-commerce channel orders. Mandatory per VREQ-009 — no separate tables per channel.. Valid values are `direct_oe|distributor|dealer|ecommerce|intercompany|oem`',
  configuration_key STRING COMMENT 'Unique identifier or hash representing the product configuration selected for this quotation line (e.g., variant configuration in SAP VC or CPQ configuration ID). Captures configurable product options such as voltage, enclosure rating, or communication protocol.',
  confirmed_delivery_date DATE COMMENT 'System-confirmed delivery date for this quotation line based on ATP/CTP availability check results. May differ from the requested delivery date when stock or capacity is constrained.',
  cost_price DECIMAL(18,2) COMMENT 'Standard or moving average cost per unit for the quoted material at the time of quotation. Used for margin calculation and profitability analysis at the quotation line level.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this quotation line record was first created in the source system. Supports audit trail, SLA measurement, and quote cycle time analytics.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the quotation line prices and values are expressed (e.g., USD, EUR, GBP). Supports multi-currency commercial operations.. Valid values are `^[A-Z]{3}$`',
  discount_percentage DECIMAL(18,2) COMMENT 'Percentage discount applied to the list price to arrive at the quoted net price on this line item. Supports margin analysis, discount approval workflows, and win/loss analytics.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms) code specifying the delivery and risk transfer conditions for this quotation line (e.g., DAP, DDP, FOB). Governs logistics cost allocation and risk transfer point. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this quotation line record in the source system. Used for incremental data loading, change detection, and audit compliance.',
  lead_time_days STRING COMMENT 'Estimated order-to-delivery lead time in calendar days for this quotation line item. Informs the customer of expected delivery duration and supports ATP/CTP promising in SAP IBP/APS.',
  line_number STRING COMMENT 'Sequential position number of this line item within the parent quotation (e.g., 10, 20, 30 in SAP SD convention). Used for ordering and referencing individual line items.',
  line_status STRING COMMENT 'Current processing status of the quotation line item. Drives win/loss analysis, pipeline reporting, and quote-to-order conversion tracking at the line level. [ENUM-REF-CANDIDATE: open|won|lost|cancelled|expired|converted|rejected — 7 candidates stripped; promote to reference product]',
  list_price DECIMAL(18,2) COMMENT 'Standard published list price per unit for the quoted SKU before any discounts or surcharges are applied. Sourced from the pricing condition master in SAP SD or Salesforce CPQ.',
  margin_percentage DECIMAL(18,2) COMMENT 'Gross margin percentage for this quotation line, derived from the difference between quoted net price and cost price relative to net price. Supports profitability analysis and discount approval thresholds.',
  material_description STRING COMMENT 'Short descriptive text of the material or product being quoted, as sourced from the product catalog or PLM system. Provides human-readable product identification on the quotation line.',
  minimum_order_quantity DECIMAL(18,2) COMMENT 'Minimum Order Quantity (MOQ) constraint for the quoted SKU on this line. Defines the smallest quantity the manufacturer will accept for this product, impacting order feasibility and pricing tier.',
  net_value DECIMAL(18,2) COMMENT 'Total net commercial value of this quotation line, calculated as quoted net price multiplied by quoted quantity plus applicable surcharges. Represents the line-level revenue commitment in the quotation.',
  opportunity_line_ref STRING COMMENT 'Reference to the CRM opportunity line item from which this quotation line was generated. Supports end-to-end opportunity-to-quote-to-order traceability in Salesforce CRM.',
  plant_code STRING COMMENT 'Code identifying the manufacturing plant or distribution center from which this quotation line item will be fulfilled. Supports multi-site operations per VREQ-008 — plant is an attribute, not a separate domain.. Valid values are `^[A-Z0-9]{1,10}$`',
  pricing_date DATE COMMENT 'Reference date used to determine applicable pricing conditions, discount agreements, and price lists for this quotation line. Pricing conditions valid on this date are applied.',
  product_group STRING COMMENT 'Product family or category grouping to which the quoted SKU belongs (e.g., Automation Systems, Electrification Solutions, Smart Infrastructure). Supports revenue analysis by product line.',
  quoted_net_price DECIMAL(18,2) COMMENT 'Net price per unit offered to the customer on this quotation line after applying all applicable discounts and surcharges. Represents the actual per-unit commercial offer.',
  quoted_quantity DECIMAL(18,2) COMMENT 'The quantity of the SKU or product being quoted on this line item, expressed in the sales unit of measure. Used for pricing, ATP/CTP checks, and order promising.',
  rejection_reason STRING COMMENT 'Coded reason explaining why this quotation line was rejected or lost. Populated when line_status is lost, rejected, or cancelled. Drives win/loss analysis and commercial strategy improvement. [ENUM-REF-CANDIDATE: price_too_high|competitor_selected|no_budget|specification_mismatch|delivery_too_late|customer_cancelled|other — 7 candidates stripped; promote to reference product]',
  requested_delivery_date DATE COMMENT 'Customer-requested delivery date for the quantity on this quotation line. Used for ATP/CTP (Available-to-Promise / Capable-to-Promise) checks and order promising in SAP IBP/APS.',
  source_system STRING COMMENT 'Identifies the originating operational system of record from which this quotation line was ingested (e.g., SAP_SD, SALESFORCE_CRM, ORACLE_ERP). Supports SSOT governance and multi-ERP lineage tracing per VREQ-004.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  source_system_line_key STRING COMMENT 'Natural key of this quotation line item as assigned by the originating source system (e.g., SAP SD document number + item number concatenation, or Salesforce QuoteLineItem ID). Enables reverse traceability to the system of record.',
  storage_location STRING COMMENT 'Warehouse storage location within the fulfillment plant from which the quoted material will be sourced or shipped. Used for inventory reservation and WMS integration.. Valid values are `^[A-Z0-9]{1,10}$`',
  surcharge_amount DECIMAL(18,2) COMMENT 'Additional surcharge amount applied to this quotation line (e.g., freight surcharge, hazardous material surcharge, expedite fee). Added on top of the list price before or after discount.',
  tax_code STRING COMMENT 'Tax classification code applied to this quotation line determining the applicable VAT, GST, or sales tax rate. Drives tax calculation in the order-to-cash process.. Valid values are `^[A-Z0-9]{1,10}$`',
  unit_of_measure STRING COMMENT 'Sales unit of measure in which the quoted quantity is expressed (e.g., EA for each, KG for kilogram, M for meter). Aligns with ISO 80000 standard units. [ENUM-REF-CANDIDATE: EA|PC|KG|M|M2|M3|L|SET|BOX|PAL|HR|DAY — 12 candidates stripped; promote to reference product]',
  validity_end_date DATE COMMENT 'Date after which the quoted price and terms on this line item expire. After this date, the quotation line is no longer commercially binding and must be re-quoted.',
  validity_start_date DATE COMMENT 'Date from which the quoted price and terms on this line item are valid. Defines the start of the commercial offer window for this specific line.',
  CONSTRAINT `pk_quotation_line` PRIMARY KEY (`quotation_line_id`),
  CONSTRAINT `fk_sales_order_quotation_line_quotation_id` FOREIGN KEY (`quotation_id`) REFERENCES `quotation` (`quotation_id`),
  CONSTRAINT `fk_sales_order_quotation_line_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`)
)
COMMENT 'Individual line item within a sales quotation capturing the product-level pricing detail for each SKU or configurable product quoted. Captures line number, material/SKU reference, quoted quantity, unit of measure, list price, quoted net price, discount percentage, surcharge amount, net value, requested delivery date, plant, configuration key, and source_system. Enables quote-to-order conversion tracking and win/loss analysis at the product level.';

-- COMMAND ----------
-- order_partner
CREATE OR REPLACE TABLE `order_partner` (
  order_partner_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a partner function assignment record on a sales order. Generated by the lakehouse ingestion layer.',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: order_partner records partner function assignments (sold-to, ship-to, bill-to, payer) for a sales order. Has sales_order_number (STRING) as a denormalized reference but no FK. Adding order_id FK norma',
  address_city STRING COMMENT 'City component of the partner address snapshot captured at order creation. Used for logistics routing, tax jurisdiction determination, and OTD (On-Time Delivery) regional analysis.',
  address_country_code STRING COMMENT 'ISO 3166-1 alpha-3 three-letter country code of the partner address snapshot. Drives export control classification, incoterms applicability, VAT/tax treatment, and customs documentation.. Valid values are `^[A-Z]{3}$`',
  address_postal_code STRING COMMENT 'Postal or ZIP code of the partner address snapshot. Used for freight zone determination, tax jurisdiction mapping, and geographic analytics.',
  address_region_code STRING COMMENT 'State, province, or region code of the partner address snapshot (ISO 3166-2 subdivision code). Used for tax jurisdiction, export control classification, and regional sales analytics.',
  address_street STRING COMMENT 'Street address line of the business partner as snapshotted at order creation time. Captured as an address snapshot to preserve the delivery or billing address independent of master data changes.',
  channel_type STRING COMMENT 'Discriminator attribute identifying the sales channel through which the order was placed. Distinguishes direct/OE (Original Equipment) orders from distributor, dealer, e-commerce, and intercompany orders. Required per VREQ-009 to avoid splitting domains per channel.. Valid values are `direct_oe|distributor|dealer|ecommerce|intercompany`',
  contact_email STRING COMMENT 'Email address of the contact person or business partner for this partner function. Used for order confirmation, shipping notification, and invoice delivery communications.. Valid values are `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$`',
  contact_person_name STRING COMMENT 'Full name of the individual contact person associated with this partner function on the order. Relevant when partner_function_code is CP (Contact Person) or when a named contact is designated for the sold-to or ship-to party.',
  contact_phone STRING COMMENT 'Primary telephone number for the contact person or business partner associated with this partner function. Used for logistics coordination and order exception handling.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this partner function assignment record was created in the source system. Used for audit trail, data lineage, and order processing timeline analysis.',
  credit_control_area STRING COMMENT 'SAP credit control area code associated with the sold-to or payer partner, defining the credit management organizational unit responsible for credit limit monitoring and order release decisions.',
  customer_classification STRING COMMENT 'ABC classification of the customer partner indicating strategic importance and revenue tier (A=key account, B=major account, C=standard account, D=small/occasional). Used for prioritization in order promising (ATP/CTP) and service level differentiation.. Valid values are `A|B|C|D`',
  delivery_priority STRING COMMENT 'Numeric delivery priority assigned to this ship-to partner on the order, used by APS (Advanced Planning and Scheduling) and MRP (Material Requirements Planning) to sequence deliveries when capacity or stock is constrained.',
  export_control_classification STRING COMMENT 'Export control classification status of the partner (e.g., denied party, restricted country, license required, cleared). Populated from export compliance screening results for the ship-to and sold-to partner functions.',
  goods_receiving_hours STRING COMMENT 'Operating hours during which the ship-to partner accepts goods deliveries (e.g., Mon-Fri 07:00-16:00). Used in transportation planning and delivery scheduling to ensure OTD (On-Time Delivery) compliance.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms) code applicable to this ship-to partner assignment, defining the point of risk transfer and freight responsibility. Relevant primarily for the SH (Ship-To) and FA (Forwarding Agent) partner functions. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  industry_sector_code STRING COMMENT 'Industry sector classification of the business partner (e.g., automotive, aerospace, energy, building automation). Used for segment-level sales analytics, PPAP requirements determination, and regulatory compliance tracking.',
  is_primary BOOLEAN COMMENT 'Indicates whether this partner assignment is the primary (default) partner for the given function code on the order. When multiple partners share the same function, only one is flagged as primary for default processing.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this partner function assignment record in the source system. Used for change detection in incremental data loads and audit compliance.',
  partner_function_code STRING COMMENT 'SAP SD partner function code identifying the role of the business partner on the order. Standard codes include SP (Sold-To Party), SH (Ship-To Party), BP (Bill-To Party), PY (Payer), SR (Sales Representative), FA (Forwarding Agent), CP (Contact Person), AG (Ordering Party), RE (Goods Recipient). [ENUM-REF-CANDIDATE: SP|SH|BP|PY|SR|FA|CP|AG|RE|ZZ — 10 candidates stripped; promote to reference product]',
  partner_function_description STRING COMMENT 'Human-readable description of the partner function role (e.g., Sold-To Party, Ship-To Party, Bill-To Party, Payer, Forwarding Agent, Contact Person). Derived from the partner function code for reporting clarity.',
  partner_language_code STRING COMMENT 'ISO 639-1 two-letter language code of the business partner, used to determine the language for order confirmations, invoices, shipping documents, and customer-facing communications.. Valid values are `^[A-Z]{2}$`',
  partner_name STRING COMMENT 'Full legal or trading name of the business partner at the time the order was created. Snapshot value captured to preserve the name as it appeared on the order, independent of subsequent master data changes.',
  partner_name_2 STRING COMMENT 'Second name line for the business partner, used for extended legal names, DBA (doing business as) names, or department/division qualifiers as captured on the order document.',
  partner_number STRING COMMENT 'Business partner number or customer account number as maintained in the source system (SAP Business Partner / Customer Master or Salesforce Account ID). Natural key identifying the partner entity in the originating system.',
  partner_sequence_number STRING COMMENT 'Sequential counter distinguishing multiple partners assigned to the same function code on a single order (e.g., multiple ship-to parties or multiple contact persons). Starts at 1 for the primary partner of each function.',
  partner_status STRING COMMENT 'Current status of this partner function assignment on the order. Blocked status may indicate a credit hold, export control restriction, or compliance review preventing order processing for this partner.. Valid values are `active|inactive|blocked|pending_validation`',
  partner_type STRING COMMENT 'Classification of the business partner entity as an organization (company), individual person, or group. Drives address formatting, salutation, and GDPR data handling rules.. Valid values are `organization|person|group`',
  payment_terms_code STRING COMMENT 'Payment terms code applicable to the payer (PY) partner function, defining due dates, early payment discounts, and installment schedules. Sourced from the SAP SD customer master payment terms.',
  sales_district_code STRING COMMENT 'Sales district code associated with the partners geographic location as maintained in the SAP SD customer master. Used for territory management, sales rep assignment, and regional performance reporting.',
  source_system STRING COMMENT 'Identifier of the originating operational system of record from which this partner function assignment was sourced. Supports SSOT (Single Source of Truth) traceability across multi-ERP and multi-CRM landscapes arising from M&A activity. Required per VREQ-004.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  source_system_partner_key STRING COMMENT 'Natural key or composite key of this partner function assignment record in the originating source system (e.g., SAP SD VBPA table key combining VBELN+PARVW+COUNTER, or Salesforce OrderContactRole ID). Enables bidirectional traceability and delta load reconciliation.',
  tax_classification_code STRING COMMENT 'Tax classification indicator for the partner as captured on the order, determining VAT/GST/sales tax treatment applicable to this partner function. Sourced from the customer master tax classification in SAP SD.',
  unloading_point STRING COMMENT 'Specific unloading point or dock designation at the ship-to partners facility. Used by logistics and the forwarding agent to direct deliveries to the correct receiving dock, relevant for JIT and Kanban delivery schedules.',
  valid_from_date DATE COMMENT 'Date from which this partner function assignment is effective on the order. Used for time-bound partner assignments such as temporary forwarding agents or seasonal distributor arrangements.',
  valid_to_date DATE COMMENT 'Date until which this partner function assignment is effective on the order. A null value indicates the assignment is open-ended and remains valid for the full order lifecycle.',
  vat_registration_number STRING COMMENT 'Value Added Tax (VAT) or GST registration number of the business partner as captured on the order. Required for EU intra-community supply documentation, reverse charge VAT, and tax compliance reporting.',
  CONSTRAINT `pk_order_partner` PRIMARY KEY (`order_partner_id`),
  CONSTRAINT `fk_sales_order_order_partner_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`)
)
COMMENT 'Partner function assignment record for a sales order capturing all business partners involved in the order transaction. Captures partner function code (sold-to, ship-to, bill-to, payer, sales rep, forwarding agent, contact person), partner number, partner name, partner address snapshot, and source_system. Enables multi-party order management for distributor/dealer channel orders where sold-to, ship-to, and bill-to parties differ.';

-- COMMAND ----------
-- order_schedule_line
CREATE OR REPLACE TABLE `order_schedule_line` (
  order_schedule_line_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a delivery schedule line within the sales order management system. Generated by the lakehouse silver layer ingestion process.',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: order_schedule_line is a child of order_line (delivery schedule splits belong to a specific line item). Has sales_order_number and sales_order_line_number as denormalized string references. Adding ord',
  actual_goods_issue_date DATE COMMENT 'Actual date on which goods were physically issued from the warehouse for this schedule line. Used for OTD calculation and variance analysis against planned goods_issue_date.',
  atp_confirmation_status STRING COMMENT 'Result of the Available-to-Promise (ATP) check for this schedule line, indicating whether the requested quantity can be fulfilled from existing stock and planned receipts on the requested date.. Valid values are `fully_confirmed|partially_confirmed|not_confirmed|atp_not_checked|backorder`',
  channel_type STRING COMMENT 'Discriminator attribute identifying the sales channel through which this schedule line order was placed. Distinguishes direct/OE (Original Equipment) orders from distributor, dealer, intercompany, e-commerce, and OEM channels. Required per VREQ-009 to avoid separate domain splits per channel.. Valid values are `direct_oe|distributor|dealer|intercompany|ecommerce|oem`',
  confirmed_delivery_date DATE COMMENT 'Date confirmed by ATP/CTP check on which the goods are committed to be delivered to the customer. Primary date used for OTD (On-Time Delivery) performance measurement.',
  confirmed_quantity DECIMAL(18,2) COMMENT 'Quantity confirmed for delivery on this schedule line after Available-to-Promise (ATP) or Capable-to-Promise (CTP) check. Represents the committed delivery quantity for the specific delivery date.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this schedule line record was originally created in the source system. Used for audit trail and data lineage tracking.',
  ctp_confirmation_status STRING COMMENT 'Result of the Capable-to-Promise (CTP) check for this schedule line, indicating whether production capacity and material availability can support fulfillment. Used for make-to-order and engineer-to-order scenarios.. Valid values are `fully_confirmed|partially_confirmed|not_confirmed|ctp_not_checked|capacity_constrained`',
  delivered_quantity DECIMAL(18,2) COMMENT 'Actual quantity that has been goods-issued and delivered against this schedule line. Used for OTD (On-Time Delivery) tracking and open quantity calculation.',
  delivery_block STRING COMMENT 'Block reason preventing the creation of a delivery document for this schedule line. Common blocks include credit holds, export control restrictions, quality holds, and customer-requested holds.. Valid values are `credit_block|export_block|quality_block|customer_request|payment_block|no_block`',
  delivery_document_number STRING COMMENT 'SAP SD outbound delivery document number (VBELN of delivery) created from this schedule line. Links the schedule line to the physical shipment and goods issue posting.',
  goods_issue_date DATE COMMENT 'Planned or actual date on which goods are issued from the warehouse/shipping point for this schedule line. Triggers inventory reduction and initiates the billing process in SAP SD.',
  incoterms STRING COMMENT 'International Commercial Terms (Incoterms 2020) applicable to this schedule line delivery, defining the transfer of risk, cost responsibility, and delivery obligations between seller and buyer. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  is_mrp_relevant BOOLEAN COMMENT 'Flag indicating whether this schedule line generates a demand requirement in MRP (Material Requirements Planning) for production or procurement planning purposes.',
  is_relevant_for_delivery BOOLEAN COMMENT 'Flag indicating whether this schedule line is relevant for outbound delivery creation. Non-relevant lines (e.g., statistical lines, text lines) are excluded from delivery processing.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this schedule line record in the source system. Used for change detection, incremental loading, and audit compliance.',
  loading_date DATE COMMENT 'Planned date on which goods are to be loaded onto the transport vehicle at the shipping point for this schedule line.',
  lot_number STRING COMMENT 'Production lot number associated with the goods to be delivered on this schedule line. Natural key for regulated product traceability per VREQ-007. Enables batch/lot traceability from production through delivery.',
  material_availability_date DATE COMMENT 'Date by which all materials must be available in the warehouse to support picking and packing for this schedule line delivery. Calculated backward from goods_issue_date using the shipping calendar.',
  movement_type STRING COMMENT 'SAP MM/WM movement type code controlling the inventory transaction triggered upon goods issue for this schedule line (e.g., 601 for standard delivery goods issue, 602 for reversal). Determines the accounting and inventory impact.',
  ordered_quantity DECIMAL(18,2) COMMENT 'Original quantity requested by the customer on this schedule line before ATP/CTP confirmation. May differ from confirmed_quantity when partial availability exists.',
  otd_status STRING COMMENT 'On-Time Delivery (OTD) performance status for this schedule line, comparing actual goods issue date against confirmed delivery date. Critical KPI for supply chain performance reporting.. Valid values are `on_time|late|early|not_yet_due|cancelled`',
  otd_variance_days STRING COMMENT 'Number of calendar days by which the actual delivery deviated from the confirmed delivery date. Negative values indicate early delivery; positive values indicate late delivery. Used for OTD trend analysis.',
  plant STRING COMMENT 'Manufacturing plant or distribution center code from which this schedule line will be fulfilled. Supports multi-site operations per VREQ-008 — plant is modeled as an attribute, not a separate domain.',
  rejection_reason STRING COMMENT 'Reason code for cancellation or rejection of this schedule line, if applicable. Used for demand analysis and order loss reporting.. Valid values are `customer_cancellation|duplicate_order|credit_rejection|out_of_stock|superseded|no_reason`',
  requested_delivery_date DATE COMMENT 'Customer-requested delivery date for this schedule line as originally specified in the sales order. Compared against confirmed_delivery_date to measure promise gap.',
  route STRING COMMENT 'Transportation route code assigned to this schedule line defining the path from shipping point to customer destination, including transit time, carrier mode, and intermediate stops.',
  schedule_line_category STRING COMMENT 'SAP SD schedule line category code (e.g., CP for standard confirmed, CN for not relevant) that controls the movement type, goods issue relevance, and MRP behavior for this delivery split.. Valid values are `confirmed|not_relevant|returns|consignment|third_party`',
  schedule_line_number STRING COMMENT 'Sequential line number identifying the delivery schedule split within a sales order line item, as assigned by SAP SD (e.g., schedule line 1, 2, 3 for a multi-delivery order line). Natural key component within the context of a sales order line.',
  schedule_line_status STRING COMMENT 'Current processing status of the delivery schedule line, reflecting the fulfillment lifecycle from open through delivery completion or cancellation.. Valid values are `open|partially_delivered|fully_delivered|cancelled|blocked|closed`',
  serial_number STRING COMMENT 'Unique serial number of the finished good unit assigned to this schedule line delivery. Natural key for serialized product traceability per VREQ-007. Applicable for high-value or regulated serialized products.',
  shipping_point STRING COMMENT 'SAP organizational unit (shipping point code) from which the goods for this schedule line will be dispatched. Determines the warehouse, loading dock, and shipping calendar used for delivery scheduling.',
  source_system STRING COMMENT 'Originating operational system of record from which this schedule line record was sourced. Supports SSOT (Single Source of Truth) multi-ERP traceability per VREQ-004 without creating separate domain copies per system.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  source_system_key STRING COMMENT 'Natural key or composite key from the originating source system uniquely identifying this schedule line record in the upstream system (e.g., SAP SD VBELN+POSNR+ETENR composite). Enables reconciliation and lineage tracing.',
  storage_location STRING COMMENT 'Warehouse storage location code within the plant from which inventory will be picked for this schedule line delivery.',
  transportation_planning_date DATE COMMENT 'Date by which transportation must be planned and booked for this schedule line to meet the confirmed delivery date. Used by logistics and freight planning teams.',
  unit_of_measure STRING COMMENT 'Unit of measure in which the confirmed, ordered, and delivered quantities are expressed (e.g., EA for each, KG for kilogram, PC for piece). Aligns with ISO 80000 standard units. [ENUM-REF-CANDIDATE: EA|KG|LB|M|M2|M3|L|PC|SET|BOX|PAL|ROL — 12 candidates stripped; promote to reference product]',
  CONSTRAINT `pk_order_schedule_line` PRIMARY KEY (`order_schedule_line_id`),
  CONSTRAINT `fk_sales_order_order_schedule_line_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`)
)
COMMENT 'Delivery schedule line within a sales order line item representing the confirmed delivery split across multiple dates and quantities. Captures schedule line number, confirmed quantity, confirmed delivery date, goods issue date, route, shipping point, delivery block, ATP (Available-to-Promise) confirmation status, CTP (Capable-to-Promise) confirmation status, movement type, and source_system. Critical for multi-delivery order management and OTD (On-Time Delivery) tracking in SAP SD.';

-- COMMAND ----------
-- return_order
CREATE OR REPLACE TABLE `return_order` (
  return_order_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a return order (Return Material Authorization) record in the silver layer lakehouse. System-generated BIGINT for internal joins and lineage.',
  account_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to customer.account.account_id',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: return_order (RMA) references the original sales order via original_order_number (STRING). Adding original_order_id FK normalizes this relationship, enabling proper return-to-original-order traceabili',
  ecn_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.ecn. Business justification: Field failures resulting in returns may trigger Engineering Change Notices (ECNs) for design corrections. Links return/warranty claims to engineering change management for closed-loop quality feedback',
  approved_by STRING COMMENT 'User ID or name of the sales or quality representative who approved the return order. Supports audit trail and authorization compliance.',
  approved_date DATE COMMENT 'Date on which the return order was formally approved by the authorized sales or quality representative. Marks the transition from requested to approved status.',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the sales channel through which the original order was placed and the return is being processed. Differentiates direct/OE returns from distributor and dealer returns per VREQ-009.. Valid values are `direct_oe|distributor|dealer|ecommerce|intercompany`',
  country_code STRING COMMENT 'ISO 3166-1 alpha-3 country code of the customer location from which the return originates. Used for export control, trade compliance, and regional reporting.. Valid values are `[A-Z]{3}`',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when the return order record was created in the source system. Used for audit trail, SLA measurement, and data lineage tracking.',
  credit_memo_number STRING COMMENT 'Reference number of the financial credit memo issued to the customer following successful return processing. Links the return order to the billing and accounts receivable reversal document.',
  credit_memo_required BOOLEAN COMMENT 'Indicates whether a financial credit memo must be issued to the customer upon completion of the return process. Drives accounts receivable credit posting in SAP FI.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code for the return order value (e.g., USD, EUR, GBP). Aligns with the currency of the original sales order.. Valid values are `[A-Z]{3}`',
  disposition_code STRING COMMENT 'Quality disposition decision for the returned goods following inspection. Determines whether items are restocked, scrapped, reworked, or returned to the vendor. Drives inventory and cost accounting.. Valid values are `restock|scrap|rework|return_to_vendor|quarantine|pending`',
  distribution_channel_code STRING COMMENT 'SAP SD distribution channel code associated with the return order, reflecting the channel through which the original sale was made.',
  exchange_rate DECIMAL(18,2) COMMENT 'Foreign exchange rate applied to convert the return order value from transaction currency to USD at the time of return order creation.',
  goods_receipt_date DATE COMMENT 'Date on which the returned goods were physically received and goods receipt was posted at the return plant. Used for cycle time analysis and SLA compliance.',
  goods_receipt_number STRING COMMENT 'Material document number generated in SAP MM when the returned goods are physically received at the return plant. Confirms physical receipt and triggers inventory posting.',
  inspection_required BOOLEAN COMMENT 'Indicates whether the returned goods must undergo quality inspection upon receipt before disposition (restock, scrap, or rework). Triggers quality management workflow when TRUE.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent update to the return order record in the source system. Supports incremental data loading, change detection, and audit compliance.',
  lot_number STRING COMMENT 'Production lot number of the returned product. Natural key for regulated and batch-traceable products per VREQ-007. Enables traceability to the manufacturing batch for quality investigations and potential field recalls.',
  material_description STRING COMMENT 'Short description of the returned material or product as maintained in the product catalog. Provides human-readable product identification for operations and customer communication.',
  ncr_number STRING COMMENT 'Reference to the Non-Conformance Report raised in the quality management system when the return reason is a quality defect. Links the return order to the quality investigation and CAPA process.',
  number STRING COMMENT 'Business-facing natural key for the return order as assigned by the source system (SAP SD returns document number or Salesforce RMA record number). Used for cross-system traceability and customer communication.',
  original_order_line_number STRING COMMENT 'Line item number on the original sales order that is being returned. Supports partial-line returns and precise financial reversal at the line level.',
  region_code STRING COMMENT 'Geographic region code associated with the return order (e.g., EMEA, APAC, AMER). Modeled as an attribute per VREQ-008 to support multi-site and multi-region analytics without domain duplication.',
  requested_return_date DATE COMMENT 'Date by which the customer has requested the return to be processed and credit issued. Used for SLA tracking and customer satisfaction management.',
  return_order_date DATE COMMENT 'Calendar date on which the return order was created or initiated by the customer or sales representative. Used for aging analysis and SLA compliance tracking.',
  return_order_status STRING COMMENT 'Current lifecycle status of the return order. Tracks progression from customer request through physical receipt, quality inspection, and financial credit issuance. [ENUM-REF-CANDIDATE: requested|approved|in_transit|received|inspected|credited|rejected|closed — 8 candidates stripped; promote to reference product]',
  return_plant_code STRING COMMENT 'Plant or facility code to which the returned goods are to be shipped and received. Determines the receiving location for physical inspection and restocking. Supports multi-site operations per VREQ-008.',
  return_plant_name STRING COMMENT 'Human-readable name of the plant or facility designated to receive the returned goods. Complements return_plant_code for operational clarity.',
  return_quantity DECIMAL(18,2) COMMENT 'Quantity of product units authorized for return under this return order. May be less than or equal to the original ordered quantity to support partial returns.',
  return_value DECIMAL(18,2) COMMENT 'Total net value of the return order in the transaction currency. Represents the financial exposure for credit memo issuance and revenue reversal under ASC 606 / IFRS 15.',
  return_value_usd DECIMAL(18,2) COMMENT 'Return order value converted to US Dollars using the exchange rate at the time of return order creation. Enables consistent global financial reporting and cross-currency analytics.',
  sales_organization STRING COMMENT 'SAP SD sales organization responsible for processing the return order. Determines pricing procedures, credit memo authority, and revenue reversal posting.',
  serial_number STRING COMMENT 'Unique serial number of the returned finished goods unit. Natural key for serialized products per VREQ-007. Enables unit-level traceability, warranty validation, and installed base updates.',
  sku_code STRING COMMENT 'Material or SKU number of the product being returned. Identifies the specific product variant and links to the product catalog for valuation and restocking decisions.',
  source_system STRING COMMENT 'Identifies the originating operational system of record for this return order record per VREQ-004 SSOT rule. Supports multi-ERP environments (SAP S/4HANA SD and Oracle ERP Cloud from M&A) without domain duplication.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  source_system_return_key STRING COMMENT 'Primary key or document number of the return order as stored in the originating source system. Enables reverse lookup and reconciliation between the lakehouse silver layer and the operational system of record.',
  storage_location_code STRING COMMENT 'Storage location within the return plant where received returned goods are staged pending inspection and disposition decision.',
  unit_of_measure STRING COMMENT 'Unit of measure applicable to the return quantity (e.g., EA, KG, M, PC). Aligned with the unit of measure on the original sales order line.',
  CONSTRAINT `pk_return_order` PRIMARY KEY (`return_order_id`),
  CONSTRAINT `fk_sales_order_return_order_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`)
)
COMMENT 'Sales return order (RMA — Return Material Authorization) master record capturing a customer-initiated product return request. Captures return order number, original order reference, return reason code (quality defect, wrong item, over-delivery, warranty return, commercial return), return quantity, return value, return status (requested, approved, in-transit, received, credited), RMA number, return plant, inspection required flag, credit memo required flag, channel_type, and source_system. SSOT for the returns management process in the order-to-cash cycle.';

-- COMMAND ----------
-- order_configuration
CREATE OR REPLACE TABLE `order_configuration` (
  order_configuration_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a variant configuration record for a configurable product ordered by a customer. Used as the system-generated identifier within the Databricks Silver Layer.',
  bom_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.bom. Business justification: Complex configured assemblies (automation systems, switchgear, control panels) require specific BOM variant references for material planning, production version selection, and cost calculation. Suppor',
  part_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.part. Business justification: Configure-to-order (CTO) sales process requires linking configured sales items to base engineering parts for BOM explosion, manufacturing routing determination, and cost rollup. Core to variant manage',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: Configuration should link to order header for reporting and aggregation. Business reality: configurations are order-level entities (not just line-level) and need header linkage for order-level configu',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: order_configuration is a variant configuration record for a configurable product on a specific order line (e.g., automation system, drive, switchgear). Has sales_order_number and sales_order_item_numb',
  product_specification_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.product_specification. Business justification: Configured orders must reference governing product specifications to validate technical feasibility (voltage class, power rating, protection rating, regulatory compliance scope). Essential for enginee',
  quotation_line_id BIGINT COMMENT 'Foreign key linking to sales_order.quotation_line. Business justification: Configurations can be created at quotation stage (pre-order). Business reality: configure-to-order workflow starts at quotation, configuration is copied to order when quotation converts. Nullable (con',
  approved_timestamp TIMESTAMP COMMENT 'Timestamp when the configuration received final engineering or commercial approval and was released for production planning. Null if not yet approved or approval not required.',
  bom_explosion_status STRING COMMENT 'Status of the Bill of Materials (BOM) explosion for this configuration. Indicates whether the variant configuration has been successfully resolved into a specific BOM for production planning and MRP.. Valid values are `not_exploded|exploded|partial|error`',
  certification_marks STRING COMMENT 'Comma-separated list of product safety and regulatory certification marks required for this configuration (e.g., CE, UL, CSA, ATEX, IECEx, CCC). Drives compliance documentation and labeling requirements during manufacturing.',
  channel_type STRING COMMENT 'Sales channel discriminator indicating whether this configuration is associated with a direct/OE (Original Equipment) order or a distributor/dealer order. Required per VREQ-009 to distinguish channel without creating separate tables. direct_oe = direct original equipment customer; distributor = sold through distribution partner; dealer = sold through authorized dealer; oem = OEM customer integration; epc = engineering procurement construction contractor; digital = e-commerce or digital channel.. Valid values are `direct_oe|distributor|dealer|oem|epc|digital`',
  characteristic_profile_code STRING COMMENT 'Code identifying the classification profile or configuration class used to define the set of allowable characteristics and values for this product model. Corresponds to the SAP Classification System class or PLM product family template.',
  communication_protocol STRING COMMENT 'Industrial communication protocol characteristic selected for the configured product (e.g., PROFINET, EtherNet/IP, Modbus TCP, PROFIBUS, CANopen, EtherCAT). Determines fieldbus integration capability with customer PLC/DCS/SCADA systems.',
  configurable_material_number STRING COMMENT 'SAP material number or PLM part number of the configurable (KMAT) product being configured. Represents the base configurable material in the product catalog from which the variant is derived.',
  configuration_date DATE COMMENT 'Calendar date on which the product configuration was created or finalized by the sales or engineering team. Used for traceability and order promising timelines.',
  configuration_key STRING COMMENT 'Natural business key identifying the configuration record as assigned by the source system (CPQ tool, SAP SD variant configuration, or EDI). Serves as the human-readable unique identifier for the configuration across systems.',
  configuration_revision STRING COMMENT 'Integer revision counter tracking the number of times this configuration has been modified. Increments with each change to characteristic assignments, enabling version history and audit traceability.',
  configuration_source STRING COMMENT 'Origin method by which the configuration was created. cpq indicates a Configure-Price-Quote tool (e.g., Salesforce CPQ); manual indicates direct entry by a sales or application engineer; edi indicates received via Electronic Data Interchange from a customer or distributor; plm_import indicates imported from a PLM system (Teamcenter or Windchill); api indicates submitted via programmatic interface.. Valid values are `cpq|manual|edi|plm_import|api`',
  configuration_status STRING COMMENT 'Current lifecycle status of the configuration record. valid indicates a complete and validated configuration ready for production; incomplete indicates missing required characteristics; error indicates a conflict or invalid combination; superseded indicates replaced by a newer revision; cancelled indicates the configuration was voided.. Valid values are `valid|incomplete|error|superseded|cancelled`',
  cooling_type STRING COMMENT 'Thermal management / cooling method characteristic selected for the configured product. Determines installation requirements and thermal derating factors.. Valid values are `air_cooled|liquid_cooled|forced_air|natural_convection|heat_exchanger`',
  created_timestamp TIMESTAMP COMMENT 'Timestamp recording when the configuration record was first created in the source system. Used for audit trail, SLA tracking, and order-to-delivery cycle time analysis.',
  ecn_reference STRING COMMENT 'Reference number of the Engineering Change Notice (ECN) that triggered or is associated with this configuration, if applicable. Links the sales configuration to the formal engineering change management process in PLM.',
  engineering_review_status STRING COMMENT 'Current status of the engineering review process for this configuration. Tracks the approval workflow from submission through engineering sign-off before the configuration is released to production planning.. Valid values are `not_required|pending|in_review|approved|rejected`',
  export_control_classification STRING COMMENT 'Export Control Classification Number (ECCN) or equivalent export license classification assigned to this configuration. Required for dual-use industrial automation and electrification products subject to export regulations.',
  frame_size STRING COMMENT 'Physical frame or enclosure size characteristic of the configured product (e.g., Frame D, Size 3, 400mm). Determines mechanical dimensions and mounting requirements for drives, switchgear, and automation components.',
  hazardous_area_classification STRING COMMENT 'Hazardous area zone classification for which the product is configured (ATEX/IECEx zones or NEC divisions). Required for products deployed in explosive atmospheres such as oil and gas, chemical, or mining environments. [ENUM-REF-CANDIDATE: zone_0|zone_1|zone_2|zone_20|zone_21|zone_22|non_hazardous|div_1|div_2 — 9 candidates stripped; promote to reference product]',
  is_engineering_review_required BOOLEAN COMMENT 'Indicates whether this configuration requires review and approval by an application or design engineer before release to manufacturing. Typically set to True for ETO (Engineer-to-Order) configurations or non-standard option combinations.',
  is_validated BOOLEAN COMMENT 'Indicates whether the configuration has passed all validation rules in the CPQ or variant configurator engine (e.g., no conflicting characteristics, all mandatory options selected, BOM explodable). True = validated; False = not yet validated or validation failed.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to the configuration record. Tracks changes to characteristic assignments, status updates, or engineering review outcomes.',
  manufacturing_model STRING COMMENT 'Manufacturing fulfillment model applicable to this configuration. eto (Engineer-to-Order) indicates custom engineering is required; cto (Configure-to-Order) indicates assembly from standard options; mto (Make-to-Order) indicates production triggered by order; mts (Make-to-Stock) indicates fulfilled from existing inventory.. Valid values are `eto|cto|mto|mts`',
  output_current_rating STRING COMMENT 'Rated output current characteristic of the configured product in amperes (e.g., 32A, 100A, 630A). Used for electrical sizing, protection coordination, and compliance verification.',
  plant_code STRING COMMENT 'Code identifying the manufacturing plant or production facility assigned to fulfill this configuration. Supports multi-site manufacturing per VREQ-008 — plant is an attribute, not a separate domain.',
  power_rating STRING COMMENT 'Rated power output characteristic of the configured product (e.g., 7.5kW, 22kW, 110kW, 1.5MW). Essential for drives, motors, and power distribution equipment configurations.',
  product_description STRING COMMENT 'Human-readable description of the configured product, typically derived from the base product model and the selected characteristic values (e.g., Low Voltage Drive 22kW IP55 PROFINET). Used in order documents and customer-facing outputs.',
  product_model_number STRING COMMENT 'Base product model or platform identifier (e.g., drive series, switchgear family, automation controller model) to which this configuration applies. Links the configuration to the product catalog master.',
  protection_rating STRING COMMENT 'Ingress Protection (IP) rating characteristic selected for the configured product enclosure (e.g., IP20, IP54, IP65, IP66). Defines the degree of protection against solid particles and liquids per IEC 60529.',
  quantity DECIMAL(18,2) COMMENT 'Ordered quantity of units with this specific configuration. Supports scenarios where multiple identical configured units are ordered on a single line item.',
  region_code STRING COMMENT 'Geographic region code associated with the configuration (e.g., EMEA, APAC, AMER, DACH). Supports multi-region reporting and regional compliance requirements per VREQ-008.',
  rohs_compliant BOOLEAN COMMENT 'Indicates whether this product configuration is compliant with the EU Restriction of Hazardous Substances (RoHS) Directive, restricting the use of specific hazardous materials in electrical and electronic equipment.',
  software_version STRING COMMENT 'Firmware or software version characteristic assigned to the configured product at time of order (e.g., v3.2.1, FW-2024-Q1). Ensures the correct software baseline is loaded during manufacturing and supports traceability for field service.',
  source_system STRING COMMENT 'Identifier of the originating operational system of record from which this configuration record was sourced. Supports SSOT (Single Source of Truth) traceability per VREQ-004 across multi-ERP and multi-PLM environments resulting from M&A activity. [ENUM-REF-CANDIDATE: sap_sd|salesforce_cpq|oracle_erp|ptc_windchill|teamcenter|edi|manual — 7 candidates stripped; promote to reference product]',
  target_market_country STRING COMMENT 'Three-letter ISO country code of the country where the configured product will be installed or used. Drives country-specific certification requirements, voltage standards, and export control classification.. Valid values are `[A-Z]{3}`',
  unit_of_measure STRING COMMENT 'Unit of measure for the configured quantity (e.g., EA for each, SET for set, PCE for piece). Follows SAP UoM codes and ISO 80000 measurement standards.',
  voltage_class STRING COMMENT 'Electrical voltage class characteristic selected for the configured product (e.g., LV 400V, MV 6.6kV, HV 33kV). Critical for electrification and automation product configurations to ensure compatibility with customer installation.',
  CONSTRAINT `pk_order_configuration` PRIMARY KEY (`order_configuration_id`),
  CONSTRAINT `fk_sales_order_order_configuration_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`),
  CONSTRAINT `fk_sales_order_order_configuration_quotation_line_id` FOREIGN KEY (`quotation_line_id`) REFERENCES `quotation_line` (`quotation_line_id`),
  CONSTRAINT `fk_sales_order_order_configuration_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`)
)
COMMENT 'Variant configuration record for a configurable product (e.g., automation system, drive, switchgear) ordered by a customer. Captures configuration key, configuration date, product model, characteristic assignments (voltage class, frame size, protection rating, communication protocol, software version), configuration status (valid, incomplete, error), configuration source (CPQ tool, manual, EDI), and source_system. Supports engineer-to-order (ETO) and configure-to-order (CTO) manufacturing models common in industrial automation.';

-- COMMAND ----------
-- return_order_line
CREATE OR REPLACE TABLE `return_order_line` (
  return_order_line_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying each return order line item within the sales_order domain lakehouse silver layer.',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: return_order_line has original_order_number and original_order_line_number referencing the original order line being returned. Adding original_order_line_id FK normalizes this relationship, enabling r',
  order_schedule_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_schedule_line. Business justification: return_order_line has original_order_line_id but returns are often against specific deliveries tracked at schedule line level. Adding original_order_schedule_line_id FK to sales_order.order_schedule_l',
  return_order_id BIGINT COMMENT 'Foreign key linking to sales_order.return_order. Business justification: return_order_line is a child of return_order (line-to-header rule). Has return_order_number (STRING) as a denormalized reference but no FK. Adding return_order_id FK establishes the proper parent-chil',
  part_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to product_lifecycle.part. Business justification: Return processing requires part-level traceability for root cause analysis, failure mode identification, DFMEA updates, and disposition decisions (scrap/rework/refurbish). Critical for quality feedbac',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the sales channel of the originating order — direct/OE versus distributor/dealer versus intercompany, per VREQ-009. Enables channel-segmented returns analysis without splitting into separate tables.. Valid values are `DIRECT_OE|DISTRIBUTOR|DEALER|INTERCOMPANY|ECOMMERCE`',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this return order line record was created in the source system, used for audit trail and data lineage tracking.',
  credit_memo_number STRING COMMENT 'Reference number of the credit memo or credit note issued to the customer for this return line, linking the commercial return to the billing and accounts receivable document.',
  credit_value DECIMAL(18,2) COMMENT 'Total credit amount to be issued to the customer for this return line (returned_quantity × net_price minus restocking fee), expressed in the transaction currency. Feeds accounts receivable and revenue reversal.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code in which the credit value, net price, and restocking fee are expressed for this return line.. Valid values are `^[A-Z]{3}$`',
  disposition_code STRING COMMENT 'Inventory disposition decision for the returned goods following inspection — determines whether the item is restocked, scrapped, reworked, returned to vendor, or quarantined. Drives warehouse and inventory actions.. Valid values are `RESTOCK|SCRAP|REWORK|RETURN_TO_VENDOR|QUARANTINE|DONATE`',
  goods_receipt_date DATE COMMENT 'Date on which the returned goods were physically received at the plant or warehouse, triggering the inspection process and inventory movement.',
  inspection_completion_date DATE COMMENT 'Date on which the quality inspection of the returned goods was completed and the usage decision (inspection result) was recorded.',
  inspection_result STRING COMMENT 'Outcome of the goods receipt quality inspection for the returned item — accepted for restocking, rejected (return to customer or supplier), or scrapped. Feeds quality management and inventory disposition.. Valid values are `ACCEPTED|REJECTED|SCRAP|PENDING|REWORK_REQUIRED`',
  is_quality_hold BOOLEAN COMMENT 'Indicates whether the returned goods have been placed on quality hold pending further investigation (e.g., potential safety issue, CAPA trigger, or regulatory hold).',
  is_warranty_return BOOLEAN COMMENT 'Indicates whether this return line is driven by a warranty claim (True) or a commercial/non-warranty return (False). Determines credit processing path and cost allocation.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent update to this return order line record in the source system, supporting change tracking and incremental data loading.',
  line_number STRING COMMENT 'Sequential line item number within the return order document, used to uniquely identify each returned SKU position within the same return order.',
  line_status STRING COMMENT 'Current processing status of the return order line, tracking progression from open receipt through inspection disposition to credit issuance or scrap. Drives workflow and reporting. [ENUM-REF-CANDIDATE: OPEN|IN_INSPECTION|ACCEPTED|REJECTED|SCRAPPED|CREDITED|CANCELLED|CLOSED — 8 candidates stripped; promote to reference product]',
  list_price DECIMAL(18,2) COMMENT 'Standard list price per unit of the returned SKU at the time of the original order, used as the basis for credit value calculation.',
  lot_number STRING COMMENT 'Production lot number (natural key for regulated/traceable products per VREQ-007) identifying the manufacturing batch of the returned item. Critical for quality feedback loop, NCR initiation, and traceability to manufacturing execution.',
  material_description STRING COMMENT 'Short description of the returned material or product as maintained in the product master, providing human-readable identification alongside the SKU code.',
  ncr_reference STRING COMMENT 'Reference number of the Non-Conformance Report (NCR) raised in the quality management system as a result of this return line, enabling traceability from commercial returns to quality corrective actions.',
  net_price DECIMAL(18,2) COMMENT 'Net selling price per unit after discounts and surcharges as invoiced on the original order, used as the basis for credit memo calculation.',
  plant_code STRING COMMENT 'Manufacturing or distribution plant code to which the returned goods are being received and processed. Per VREQ-008, plant is modeled as an attribute — not a separate domain — enabling multi-site returns analysis.',
  restocking_fee DECIMAL(18,2) COMMENT 'Fee charged to the customer for processing the return and restocking the item, deducted from the gross credit value. Expressed in the transaction currency.',
  returned_quantity DECIMAL(18,2) COMMENT 'Quantity of the SKU being returned on this line item, expressed in the unit of measure. Used for inventory revaluation, credit calculation, and returns rate analytics.',
  rma_number STRING COMMENT 'Return Material Authorization number issued to the customer authorizing the physical return of goods. Serves as the customer-facing reference for the return transaction.',
  serial_number STRING COMMENT 'Unique unit-level serial number (natural key for finished goods per VREQ-007) of the specific returned item. Enables unit-level traceability, installed base reconciliation, and warranty claim linkage.',
  sku_code STRING COMMENT 'Material or SKU identifier for the product being returned, as defined in the product catalog. Aligns with the SAP material number or Salesforce product code.',
  source_system STRING COMMENT 'Originating operational system of record for this return order line, per SSOT multi-ERP rule (VREQ-004). Distinguishes SAP S/4HANA SD, Salesforce CRM, Oracle ERP Cloud (M&A), or manual entry.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  source_system_line_key STRING COMMENT 'Natural key or composite key of this return order line as it exists in the originating source system, enabling traceability and reconciliation back to the system of record.',
  storage_location_code STRING COMMENT 'Warehouse storage location within the receiving plant where returned goods are physically placed pending inspection and disposition.',
  sub_line_number STRING COMMENT 'Sub-item or schedule line number within a return order line, used when a single line is split across multiple lots, serial numbers, or partial return confirmations.',
  tax_amount DECIMAL(18,2) COMMENT 'Tax amount applicable to the credit value for this return line, calculated based on the tax code and jurisdiction. Required for VAT/GST credit note compliance.',
  tax_code STRING COMMENT 'Tax determination code applied to this return line, driving the tax rate and tax category for credit note generation. Aligns with SAP FI tax codes.',
  unit_of_measure STRING COMMENT 'Unit of measure in which the returned quantity is expressed (e.g., EA for each, KG for kilogram, M for meter). Aligns with ISO 80000 and SAP base unit of measure. [ENUM-REF-CANDIDATE: EA|PC|KG|M|M2|M3|L|SET|BOX|ROLL|PAIR — 11 candidates stripped; promote to reference product]',
  warranty_claim_reference STRING COMMENT 'Reference to an associated warranty claim if the return is driven by a warranty defect, enabling linkage between the commercial return and the warranty_claim domain.',
  CONSTRAINT `pk_return_order_line` PRIMARY KEY (`return_order_line_id`),
  CONSTRAINT `fk_sales_order_return_order_line_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`),
  CONSTRAINT `fk_sales_order_return_order_line_order_schedule_line_id` FOREIGN KEY (`order_schedule_line_id`) REFERENCES `order_schedule_line` (`order_schedule_line_id`),
  CONSTRAINT `fk_sales_order_return_order_line_return_order_id` FOREIGN KEY (`return_order_id`) REFERENCES `return_order` (`return_order_id`)
)
COMMENT 'Individual line item within a sales return order capturing the product-level detail for each returned SKU. Captures line number, material/SKU reference, returned quantity, unit of measure, original order line reference, return reason code, lot number, serial number, inspection result (accepted, rejected, scrap), credit value, restocking fee, and source_system. Enables granular returns analysis and quality feedback loop to manufacturing.';

-- COMMAND ----------
-- atp_check
CREATE OR REPLACE TABLE `atp_check` (
  atp_check_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying each ATP/CTP check result record in the silver layer.',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: ATP checks should link to order header for reporting and order-level ATP aggregation. Business reality: ATP is performed at order level (aggregated across lines) for order acceptance decisions. Nullab',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: atp_check records ATP/CTP check results for a specific order line item. Has sales_order_number and sales_order_item_number as string references. Adding order_line_id FK normalizes this relationship, e',
  order_schedule_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_schedule_line. Business justification: atp_check has schedule_line_date and atp_confirmation_status fields that directly correspond to a specific schedule line confirmation. Adding order_schedule_line_id FK enables precise ATP-to-schedule-',
  plant_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to manufacturing.plant.plant_id',
  sku_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to product_catalog.sku.sku_id',
  atp_quantity_available DECIMAL(18,2) COMMENT 'The total ATP-relevant stock quantity available at the time of the check, representing the cumulative available quantity before this orders demand is applied.',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the sales channel of the originating order: direct/OE orders versus distributor/dealer orders. Aligns with VREQ-009 — no separate tables per channel.. Valid values are `DIRECT_OE|DISTRIBUTOR|DEALER|INTERCOMPANY|ECOMMERCE|SERVICE`',
  check_duration_ms STRING COMMENT 'Elapsed time in milliseconds for the ATP/CTP check to complete, used for order promising system performance monitoring and SLA compliance tracking.',
  check_number STRING COMMENT 'Business-facing natural key or reference number assigned to the ATP/CTP check transaction, as generated by the source system (SAP SD availability check document number).',
  check_scope STRING COMMENT 'Defines the geographic or organizational scope of the ATP check — whether it checked a single plant, multiple plants, global inventory, or a specific storage location.. Valid values are `SINGLE_PLANT|MULTI_PLANT|GLOBAL|STORAGE_LOCATION`',
  check_status STRING COMMENT 'Overall result status of the ATP/CTP check indicating whether the requested quantity was fully confirmed, partially confirmed, not confirmed, placed on backorder, or encountered an error.. Valid values are `CONFIRMED|PARTIALLY_CONFIRMED|NOT_CONFIRMED|BACKORDER|PENDING|ERROR`',
  check_timestamp TIMESTAMP COMMENT 'Date and time when the ATP/CTP check was executed, recorded in ISO 8601 format with timezone offset. Used for order promising accuracy tracking and latency analysis.',
  check_type STRING COMMENT 'Discriminator indicating the type of availability check performed: ATP (Available-to-Promise based on stock and planned receipts), CTP (Capable-to-Promise including production capacity), Rule-Based ATP, Multilevel ATP, or Allocation-Based check.. Valid values are `ATP|CTP|RULE_BASED_ATP|MULTILEVEL_ATP|ALLOCATION_BASED`',
  checking_group STRING COMMENT 'Checking group assigned to the material master that controls the ATP check behavior, determining whether individual or total requirements are used.',
  checking_rule STRING COMMENT 'SAP SD checking rule code that defines which stock categories and inward/outward movements are included in the ATP calculation (e.g., A for sales order, B for delivery).',
  confirmation_gap_days STRING COMMENT 'Number of calendar days between the customer-requested delivery date and the earliest ATP-confirmed date. Positive values indicate late confirmation; zero or negative indicates on-time or early confirmation. Key metric for OTD (On-Time Delivery) analysis.',
  confirmed_quantity DECIMAL(18,2) COMMENT 'The quantity confirmed as available by the ATP/CTP check engine. May be less than requested quantity in partial confirmation scenarios.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when the ATP check result record was created in the data lakehouse silver layer, supporting audit trail and data lineage requirements.',
  earliest_confirmation_date DATE COMMENT 'The earliest date on which the confirmed quantity can be made available, as determined by the ATP/CTP check engine. Key output for order promising and delivery scheduling.',
  is_backorder BOOLEAN COMMENT 'Indicates whether the ATP check resulted in a backorder situation where the requested quantity could not be confirmed for the requested delivery date and is queued for future fulfillment.',
  is_ctp_capacity_checked BOOLEAN COMMENT 'Indicates whether the check included a Capable-to-Promise (CTP) capacity evaluation against work center capacity in addition to material availability, relevant for make-to-order scenarios.',
  is_partial_delivery_allowed BOOLEAN COMMENT 'Indicates whether the customer or order configuration permits partial delivery, allowing the ATP engine to confirm a subset of the requested quantity rather than requiring full confirmation.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to the ATP check result record in the silver layer, used for incremental load tracking and change data capture.',
  material_number STRING COMMENT 'Material or product identifier (SKU/part number) for which the ATP/CTP availability check was executed. Corresponds to the SAP material master number.',
  mrp_element_type STRING COMMENT 'Type of MRP (Material Requirements Planning) element that provided the confirmed supply for this ATP check, indicating whether confirmation came from existing stock, a planned order, purchase order, or production order.. Valid values are `STOCK|PLANNED_ORDER|PURCHASE_ORDER|PRODUCTION_ORDER|TRANSFER_ORDER|SALES_ORDER_RESERVATION`',
  quantity_unit STRING COMMENT 'Unit of measure applicable to both requested and confirmed quantities (e.g., EA, KG, M, PC). Follows SAP base unit of measure from material master.',
  region_code STRING COMMENT 'Region or geographic area code associated with the plant or fulfillment location used in the ATP check. Supports multi-site analytics without domain duplication per VREQ-008.',
  replenishment_lead_time_days STRING COMMENT 'The replenishment lead time in calendar days used by the CTP check to calculate the earliest possible production or procurement completion date for the requested material.',
  requested_delivery_date DATE COMMENT 'The delivery date requested by the customer on the sales order, used as the target date input to the ATP/CTP check.',
  requested_quantity DECIMAL(18,2) COMMENT 'The quantity of the material requested by the customer on the sales order line item, as submitted to the ATP/CTP check engine.',
  sales_organization STRING COMMENT 'SAP sales organization code under which the originating sales order was created, providing organizational context for the ATP check and enabling cross-org availability analysis.',
  schedule_line_date DATE COMMENT 'The confirmed schedule line date assigned to the sales order item as a result of the ATP check, representing the committed delivery date communicated to the customer.',
  source_system STRING COMMENT 'Identifies the originating operational system of record that performed and recorded the ATP/CTP check. Supports SSOT rule — single domain serves all source systems without duplication.. Valid values are `SAP_S4HANA|SAP_IBP|ORACLE_ERP_CLOUD|SFDC_CRM`',
  source_system_check_reference STRING COMMENT 'Native primary key or document number of the ATP check record in the originating source system, enabling traceability and reconciliation back to SAP SD or SAP IBP.',
  storage_location_code STRING COMMENT 'Storage location within the plant used as the scope for the ATP availability check, enabling warehouse-level stock visibility.',
  supply_source_reference STRING COMMENT 'Reference number of the specific MRP element (e.g., planned order number, purchase order number, production order number) that was allocated to fulfill this ATP check confirmation.',
  trigger_context STRING COMMENT 'Business context that triggered the ATP/CTP check — whether it was initiated during order entry, an order change, delivery creation, backorder processing, manual re-check, or a scheduled batch run.. Valid values are `ORDER_ENTRY|ORDER_CHANGE|DELIVERY_CREATION|BACKORDER_PROCESSING|MANUAL|BATCH_RUN`',
  work_center_code STRING COMMENT 'Code of the manufacturing work center whose capacity was evaluated during a CTP check. Populated only when check_type is CTP or RULE_BASED_ATP with capacity inclusion.',
  CONSTRAINT `pk_atp_check` PRIMARY KEY (`atp_check_id`),
  CONSTRAINT `fk_sales_order_atp_check_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`),
  CONSTRAINT `fk_sales_order_atp_check_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`),
  CONSTRAINT `fk_sales_order_atp_check_order_schedule_line_id` FOREIGN KEY (`order_schedule_line_id`) REFERENCES `order_schedule_line` (`order_schedule_line_id`)
)
COMMENT 'Available-to-Promise (ATP) and Capable-to-Promise (CTP) check result record capturing the outcome of each availability check performed during order entry or order change. Captures check type (ATP, CTP, rule-based ATP), check timestamp, requested quantity, confirmed quantity, earliest confirmation date, plant, storage location, checking rule, checking group, backorder flag, partial delivery allowed flag, and source_system. Enables order promising accuracy tracking and ATP rule performance analysis.';

-- COMMAND ----------
-- delivery_schedule
CREATE OR REPLACE TABLE `delivery_schedule` (
  delivery_schedule_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a delivery schedule master record within the lakehouse silver layer.',
  demand_plan_id BIGINT COMMENT 'DEFERRED cross-domain FK — Foreign key linking to supply_chain.demand_plan. Business justification: Delivery schedules from customers feed into supply chain demand plans. This FK links the sales order delivery schedule to the supply chain demand plan, enabling demand-driven supply planning.',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: Delivery schedule should link to order header for aggregation and reporting. Business reality: schedules are order-level agreements (scheduling agreements reference the order). Nullable (schedules can',
  order_line_id BIGINT COMMENT 'FK to sales_order.order_line.order_line_id',
  order_schedule_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_schedule_line. Business justification: delivery_schedule already has order_id and order_line_id, but for granular delivery tracking against scheduling agreements, it should also link to the specific order_schedule_line. This enables precis',
  plant_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to manufacturing.plant',
  sales_contract_id BIGINT COMMENT 'Foreign key linking to sales_order.sales_contract. Business justification: delivery_schedule (scheduling agreement) is typically associated with a sales contract or blanket order in industrial manufacturing. Has scheduling_agreement_number (STRING) as a business key. Adding ',
  sales_contract_line_id BIGINT COMMENT 'Foreign key linking to sales_order.sales_contract_line. Business justification: delivery_schedule has sales_contract_id (header level) but delivery schedules are often defined at the contract line level (specific SKU/part). Adding sales_contract_line_id FK to sales_order.sales_co',
  sku_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to product_catalog.sku.sku_id',
  channel_type STRING COMMENT 'Discriminator attribute distinguishing the sales channel through which the delivery schedule was established — direct/OE (Original Equipment) orders versus distributor, dealer, intercompany, or e-commerce channels. Required per VREQ-009.. Valid values are `direct_oe|distributor|dealer|intercompany|ecommerce`',
  country_code STRING COMMENT 'ISO 3166-1 alpha-3 country code of the ship-to destination, used for export control screening, customs documentation, and regulatory compliance checks.. Valid values are `^[A-Z]{3}$`',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when the delivery schedule record was first created in the source system, establishing the start of the records audit trail.',
  cumulative_delivered_quantity DECIMAL(18,2) COMMENT 'Running cumulative quantity actually delivered and goods-issued to the customer under this scheduling agreement from inception to date. Compared against cumulative_ordered_quantity to identify delivery shortfalls or overages.',
  cumulative_ordered_quantity DECIMAL(18,2) COMMENT 'Running cumulative quantity ordered by the customer under this scheduling agreement from inception to the current schedule date. Used for reconciliation in automotive JIT/JIS environments where cumulative quantities govern call-off accuracy.',
  currency_code STRING COMMENT 'ISO 4217 three-letter currency code applicable to any price or value fields associated with this delivery schedule (e.g., USD, EUR, JPY).. Valid values are `^[A-Z]{3}$`',
  customer_material_number STRING COMMENT 'Customer-specific part number or SKU identifier for the material being scheduled, used for cross-referencing in customer-facing documents and EDI messages.',
  customer_reference_number STRING COMMENT 'Customer-assigned reference number for this delivery schedule, such as the customers own purchase order or release number used for cross-referencing in EDI transactions.',
  delivery_frequency STRING COMMENT 'Planned cadence at which deliveries are expected under this schedule — daily, weekly, biweekly, monthly, on-demand, shift-based, or a custom pattern defined in the schedule lines. [ENUM-REF-CANDIDATE: daily|weekly|biweekly|monthly|on_demand|shift_based|custom — 7 candidates stripped; promote to reference product]',
  edi_transaction_set STRING COMMENT 'Electronic Data Interchange (EDI) transaction set or message type used to transmit this delivery schedule between the customer and the manufacturer (e.g., ANSI X12 830 Planning Schedule, 862 Shipping Schedule, EDIFACT DELFOR, DELJIT).. Valid values are `830|862|DELFOR|DELJIT|SYNCRO`',
  horizon_end_date DATE COMMENT 'End date of the planning horizon covered by this delivery schedule, defining the latest date for which delivery requirements are currently planned.',
  horizon_start_date DATE COMMENT 'Start date of the planning horizon covered by this delivery schedule, defining the earliest date for which delivery requirements are communicated to the plant.',
  incoterms_code STRING COMMENT 'International Commercial Terms (Incoterms) code defining the delivery obligations, risk transfer point, and cost responsibility between the manufacturer and the customer for shipments under this schedule. [ENUM-REF-CANDIDATE: EXW|FCA|CPT|CIP|DAP|DPU|DDP|FAS|FOB|CFR|CIF — 11 candidates stripped; promote to reference product]',
  incoterms_location STRING COMMENT 'Named place or port associated with the Incoterms code, specifying the exact point of risk and cost transfer (e.g., DAP Detroit or FOB Shanghai Port).',
  is_jis BOOLEAN COMMENT 'Indicates whether this delivery schedule requires Just-in-Sequence (JIS) delivery, where parts must arrive at the customers assembly line in the exact production sequence, typically for automotive OEM customers.',
  is_jit BOOLEAN COMMENT 'Indicates whether this delivery schedule operates under Just-in-Time (JIT) delivery requirements, where deliveries must arrive within a narrow time window to avoid customer line-side inventory buildup.',
  is_kanban_triggered BOOLEAN COMMENT 'Indicates whether delivery call-offs under this schedule are triggered by Kanban signals (pull-based replenishment) rather than forecast-based push scheduling.',
  last_edi_received_timestamp TIMESTAMP COMMENT 'Timestamp of the most recently received EDI transmission updating this delivery schedule, used to detect stale schedules and trigger alerts when customer releases are overdue.',
  last_modified_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to the delivery schedule record in the source system, used for change detection and incremental data loading.',
  lead_time_days STRING COMMENT 'Agreed delivery lead time in calendar days from order release or call-off to expected goods receipt at the customers location. Used for delivery promising and ATP/CTP calculations.',
  material_number STRING COMMENT 'Internal material or part number identifying the product/SKU to be delivered under this schedule. Corresponds to the SAP material master number or PLM part number.',
  open_quantity DECIMAL(18,2) COMMENT 'Remaining quantity yet to be delivered under the current schedule horizon, calculated as the difference between scheduled quantity and delivered quantity for the active planning period.',
  otd_target_percent DECIMAL(18,2) COMMENT 'Contractually agreed On-Time Delivery (OTD) performance target expressed as a percentage, defining the minimum acceptable delivery punctuality for this schedule. Used for SLA monitoring and customer scorecard reporting.',
  quantity_unit STRING COMMENT 'Unit of measure applicable to all quantity fields on this delivery schedule (cumulative ordered, cumulative delivered, open quantity). Follows ISO 80000 unit codes. [ENUM-REF-CANDIDATE: EA|PC|KG|LB|M|FT|L|GAL|SET|BOX|PAL — 11 candidates stripped; promote to reference product]',
  region_code STRING COMMENT 'Geographic region code associated with the fulfilling plant or customer ship-to location, supporting multi-region analytics per VREQ-008 without duplicating domains per region.',
  revision_number STRING COMMENT 'Sequential revision counter incremented each time the delivery schedule is updated by a new customer release or internal amendment, supporting version tracking and audit trail.',
  schedule_number STRING COMMENT 'Business-facing natural key for the delivery schedule, typically matching the scheduling agreement release number or blanket order schedule identifier in the source ERP system (SAP SD LPA/LPE document number).',
  schedule_status STRING COMMENT 'Current lifecycle status of the delivery schedule record, controlling whether new schedule lines can be created and deliveries executed against it.. Valid values are `active|suspended|closed|cancelled|draft|under_review`',
  schedule_type STRING COMMENT 'Classification of the delivery schedule indicating the replenishment or delivery call-off mechanism: forecast-based, Just-in-Time (JIT), Just-in-Sequence (JIS), Kanban-triggered, blanket order, or consignment.. Valid values are `forecast|jit|jis|kanban|blanket|consignment`',
  scheduling_agreement_number STRING COMMENT 'Reference to the parent scheduling agreement or blanket order contract under which this delivery schedule is issued. Links the schedule to its governing commercial agreement.',
  ship_to_location_code STRING COMMENT 'Code identifying the customers receiving location or dock to which deliveries under this schedule must be directed. May represent a specific plant gate, dock door, or line-side location for JIT/JIS deliveries.',
  source_system STRING COMMENT 'Identifier of the originating operational system of record from which this delivery schedule was sourced (e.g., SAP SD, Salesforce CRM, Oracle ERP Cloud). Supports SSOT rule per VREQ-004 by exposing the source system as an attribute rather than duplicating domains per system.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP|MANUAL`',
  source_system_schedule_key STRING COMMENT 'Primary key or unique identifier of this delivery schedule record in the originating source system, enabling traceability and reconciliation back to the system of record.',
  takt_time_seconds DECIMAL(18,2) COMMENT 'Customers takt time in seconds — the rate at which the customers assembly line consumes the scheduled material. Used to validate delivery frequency alignment with customer production rhythm.',
  tolerance_over_percent DECIMAL(18,2) COMMENT 'Maximum percentage by which actual delivered quantity may exceed the scheduled quantity without triggering a delivery discrepancy or customer complaint.',
  tolerance_under_percent DECIMAL(18,2) COMMENT 'Maximum percentage by which actual delivered quantity may fall short of the scheduled quantity without triggering a delivery discrepancy or short-shipment claim.',
  unloading_point STRING COMMENT 'Specific unloading point or dock identifier at the customers ship-to location, used for routing deliveries to the correct receiving area, particularly in automotive JIT environments.',
  CONSTRAINT `pk_delivery_schedule` PRIMARY KEY (`delivery_schedule_id`),
  CONSTRAINT `fk_sales_order_delivery_schedule_sales_contract_id` FOREIGN KEY (`sales_contract_id`) REFERENCES `sales_contract` (`sales_contract_id`),
  CONSTRAINT `fk_sales_order_delivery_schedule_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`),
  CONSTRAINT `fk_sales_order_delivery_schedule_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`),
  CONSTRAINT `fk_sales_order_delivery_schedule_sales_contract_line_id` FOREIGN KEY (`sales_contract_line_id`) REFERENCES `sales_contract_line` (`sales_contract_line_id`),
  CONSTRAINT `fk_sales_order_delivery_schedule_order_schedule_line_id` FOREIGN KEY (`order_schedule_line_id`) REFERENCES `order_schedule_line` (`order_schedule_line_id`)
)
COMMENT 'Delivery schedule master record associated with a scheduling agreement or blanket order, defining the planned delivery cadence for a customer-material combination over a planning horizon. Captures schedule number, customer reference, material/SKU, plant, delivery frequency (daily, weekly, monthly), forecast horizon start and end dates, cumulative ordered quantity, cumulative delivered quantity, just-in-time (JIT) delivery flag, kanban-triggered flag, and source_system. Supports automotive and industrial OEM customers with JIT and JIS (Just-in-Sequence) delivery requirements.';

-- COMMAND ----------
-- order_status_event
CREATE OR REPLACE TABLE `order_status_event` (
  order_status_event_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying each order status lifecycle event record in the sales order domain.',
  employee_id BIGINT COMMENT 'DEFERRED cross-domain FK — System user ID or service account identifier of the actor who initiated the status transition. Populated when triggered_by_type is user; contains system/service account name for automated triggers. Supports audit trail and accountability tracking.',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: order_status_event tracks lifecycle status transitions for a sales order. Has sales_order_number (STRING) as a denormalized reference but no FK. Adding order_id FK normalizes this relationship, enabli',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: order_status_event has sales_order_item_number indicating it can capture item-level status transitions (e.g., partial delivery, line-level rejection). Adding order_line_id FK enables item-level event ',
  order_schedule_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_schedule_line. Business justification: Status events can occur at schedule line level (delivery confirmations, goods issue, ATP confirmation). Business reality: schedule line is the atomic delivery unit and has its own lifecycle. Replaces ',
  plant_id BIGINT COMMENT 'DEFERRED cross-domain FK — FK to manufacturing.plant',
  reversed_event_order_status_event_id BIGINT COMMENT 'Reference to the order_status_event_id of the original event that this record reverses. Populated only when is_reversal is TRUE. Enables self-referential linkage within the event log for reversal chain analysis without requiring a separate reversal table.',
  actual_goods_issue_date DATE COMMENT 'Date on which goods were physically issued from the warehouse and shipment was initiated. Populated when event_type is goods_issued. Primary date used in OTD (On-Time Delivery) calculation against confirmed_delivery_date.',
  billing_document_number STRING COMMENT 'SAP SD billing document or invoice number associated with this event when event_type is invoiced. Enables order-to-cash cycle time measurement from order creation to invoice issuance.',
  channel_type STRING COMMENT 'Discriminator attribute identifying the commercial channel through which the sales order was placed. Distinguishes direct/OE (Original Equipment) orders from distributor and dealer orders per VREQ-009. Enables channel-specific OTD and cycle time benchmarking. [ENUM-REF-CANDIDATE: direct_oe|distributor|dealer|ecommerce|intercompany|service_parts|project — 7 candidates stripped; promote to reference product]',
  confirmed_delivery_date DATE COMMENT 'ATP/CTP-confirmed delivery date committed to the customer at the time of this status event. Compared against requested_delivery_date to measure promise gap and against actual_goods_issue_date for OTD performance.',
  country_code STRING COMMENT 'ISO 3166-1 alpha-3 country code of the ship-to or sold-to country associated with this order status event. Supports country-level OTD analysis, export compliance reporting, and regulatory jurisdiction determination.. Valid values are `[A-Z]{3}`',
  credit_check_status STRING COMMENT 'Result of the SAP SD automatic credit check performed at the time of this status event. Indicates whether the order passed, failed, or bypassed the credit limit check. Critical for understanding credit-hold-related OTD delays.. Valid values are `passed|failed|bypassed|not_checked|pending`',
  days_late STRING COMMENT 'Number of calendar days by which the actual goods issue date exceeded the confirmed delivery date. Negative values indicate early delivery. Populated only on goods_issued events. Raw business measurement supporting OTD root cause analysis and customer penalty calculations.',
  delivery_number STRING COMMENT 'SAP SD outbound delivery document number associated with this event when event_type is delivery_created or goods_issued. Links the order status event to the physical shipment for OTD traceability.',
  distribution_channel_code STRING COMMENT 'SAP SD distribution channel code (e.g., 10 for direct, 20 for distributor) that further qualifies the sales channel within the sales organization. Works in conjunction with channel_type for granular channel analytics.',
  division_code STRING COMMENT 'SAP SD division code representing the product division or business segment associated with the order. Enables OTD and cycle time analysis by product line or business unit.',
  duration_from_previous_event_min STRING COMMENT 'Elapsed time in minutes between this status event and the immediately preceding status event for the same sales order. Stored as a raw business measurement (not a derived KPI) to support order cycle time analysis and bottleneck identification without requiring self-joins in analytics queries.',
  event_comment STRING COMMENT 'Free-text comment or note entered by the user or system at the time of the status transition. Captures context not expressible through structured codes, such as customer communication notes, exception explanations, or escalation details.',
  event_sequence_number STRING COMMENT 'Sequential integer indicating the chronological order of status events for a given sales order. Enables ordered reconstruction of the full order lifecycle and detection of out-of-sequence events.',
  event_timestamp TIMESTAMP COMMENT 'Precise date and time (ISO 8601 with timezone offset) at which the status transition occurred. Used as the primary chronological anchor for OTD root cause analysis and order cycle time measurement.',
  event_type STRING COMMENT 'Classifies the nature of the status transition event. Covers the full SAP SD order lifecycle including creation, confirmation, delivery, goods issue, invoicing, cancellation, blocking, and unblocking events. Enables granular OTD root cause analysis. [ENUM-REF-CANDIDATE: order_created|order_confirmed|delivery_created|goods_issued|invoiced|cancelled|blocked|unblocked|credit_hold|credit_released|schedule_line_confirmed|partial_delivery|backorder_created — 13 candidates stripped; promote to reference product]',
  export_control_status STRING COMMENT 'Status of export control compliance screening at the time of this event. Relevant for industrial automation and electrification products subject to dual-use export regulations (EAR, ITAR). Blocked status contributes to OTD delays.. Valid values are `cleared|blocked|pending_review|not_applicable|escalated`',
  is_reversal BOOLEAN COMMENT 'Boolean flag indicating whether this status event represents a reversal or correction of a previously recorded event (e.g., reversal of a goods issue, cancellation of a delivery). Enables accurate cycle time calculation by excluding reversal events from forward-path analysis.',
  new_status STRING COMMENT 'The order status immediately after this transition event. Represents the current state of the sales order following the event. Used in conjunction with previous_status for state machine analysis. [ENUM-REF-CANDIDATE: open|in_process|partially_delivered|fully_delivered|partially_invoiced|fully_invoiced|blocked|cancelled|closed|pending_confirmation|credit_hold — 11 candidates stripped; promote to reference product]',
  otd_flag BOOLEAN COMMENT 'Boolean indicator set to TRUE when goods_issued event occurs on or before the confirmed_delivery_date, and FALSE when delivery is late. Populated only on goods_issued events. Enables direct OTD rate calculation without complex date comparisons in reporting layers.',
  previous_status STRING COMMENT 'The order status immediately before this transition event. Together with new_status, defines the state transition pair for lifecycle analysis and process mining. [ENUM-REF-CANDIDATE: open|in_process|partially_delivered|fully_delivered|partially_invoiced|fully_invoiced|blocked|cancelled|closed|pending_confirmation|credit_hold — 11 candidates stripped; promote to reference product]',
  region_code STRING COMMENT 'Geographic region code (e.g., EMEA, APAC, AMER) associated with the sales order event. Modeled as an attribute per VREQ-008 multi-site rule — regions are not separate domain copies. Enables regional OTD benchmarking and performance reporting.',
  requested_delivery_date DATE COMMENT 'Customer-requested delivery date captured at the time of this status event. Carried on the event record to enable point-in-time OTD analysis — the requested date may change across events, so each event snapshot preserves the date as it stood at that moment.',
  sales_org_code STRING COMMENT 'SAP SD sales organization code representing the legal entity or business unit responsible for the sale. Enables revenue attribution and OTD reporting by sales organization across M&A subsidiaries.',
  source_system STRING COMMENT 'Identifies the originating operational system of record that generated this status event. Supports SSOT (Single Source of Truth) traceability across multi-ERP environments from M&A activity per VREQ-004. Values include SAP SD, Salesforce CRM, Oracle ERP Cloud (M&A), or manual entry.. Valid values are `SAP_SD|Salesforce_CRM|Oracle_ERP_Cloud|manual`',
  source_system_event_reference STRING COMMENT 'Native identifier of this status event in the originating source system (e.g., SAP change document number, Salesforce history record ID). Enables bidirectional traceability between the lakehouse silver layer and the operational system of record.',
  triggered_by_type STRING COMMENT 'Indicates whether the status transition was initiated by a human user, an automated system process, a workflow engine, an integration event, a batch job, or an approval rule. Critical for distinguishing manual interventions from automated processing in root cause analysis.. Valid values are `user|system|workflow|integration|batch_job|approval_rule`',
  workflow_instance_reference STRING COMMENT 'Identifier of the workflow or approval process instance that triggered this status event when triggered_by_type is workflow or approval_rule. Enables end-to-end workflow audit trail and process performance analysis.',
  CONSTRAINT `pk_order_status_event` PRIMARY KEY (`order_status_event_id`),
  CONSTRAINT `fk_sales_order_order_status_event_order_schedule_line_id` FOREIGN KEY (`order_schedule_line_id`) REFERENCES `order_schedule_line` (`order_schedule_line_id`),
  CONSTRAINT `fk_sales_order_order_status_event_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`),
  CONSTRAINT `fk_sales_order_order_status_event_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`)
)
COMMENT 'Lifecycle status event log for a sales order capturing each status transition as a discrete record. Captures order reference, previous status, new status, event timestamp, event type (order created, order confirmed, delivery created, goods issued, invoiced, cancelled, blocked, unblocked), triggered by (user, system, workflow), plant, sales organization, and source_system. Enables OTD (On-Time Delivery) root cause analysis and order cycle time measurement.';

-- COMMAND ----------
-- order_header_condition
CREATE OR REPLACE TABLE `order_header_condition` (
  order_header_condition_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a pricing condition record applied at the sales order header level in the Databricks Silver Layer.',
  order_id BIGINT COMMENT 'Foreign key linking to sales_order.order. Business justification: order_header_condition is a pricing condition record applied at the sales order header level. It must reference its parent order to support pricing procedure execution, condition record lookup, and re',
  access_sequence STRING COMMENT 'The access sequence used by the pricing engine to search for and determine the applicable condition record for this condition type. Defines the hierarchy of search keys (e.g., customer/material, customer group/material group) used during pricing determination.',
  approval_status STRING COMMENT 'Approval workflow status for manually entered or overridden pricing conditions that exceed authorized discount thresholds. Supports pricing governance, sales manager approval workflows, and SOX compliance controls on revenue recognition.. Valid values are `not_required|pending|approved|rejected`',
  approved_by STRING COMMENT 'User ID or name of the sales manager or pricing authority who approved a manually entered or overridden condition value. Populated only when approval_status is approved. Supports audit trail and SOX compliance.',
  approved_timestamp TIMESTAMP COMMENT 'Date and time when the pricing condition override was approved by the authorized approver. Provides a complete audit trail for pricing governance and SOX compliance reporting.',
  channel_type STRING COMMENT 'Discriminator attribute identifying the sales channel through which the parent sales order was placed. Distinguishes direct/OE (Original Equipment) orders from distributor, dealer, intercompany, or e-commerce orders. Enables channel-specific pricing analysis and margin reporting without splitting into separate tables per channel. Required per VREQ-009.. Valid values are `direct_oe|distributor|dealer|intercompany|ecommerce|other`',
  condition_base_value DECIMAL(18,2) COMMENT 'The base amount upon which the condition rate is applied to derive the condition value. For percentage discounts, this is the subtotal from the preceding pricing step. Enables full price waterfall reconstruction and audit.',
  condition_calculation_type STRING COMMENT 'Specifies how the condition value is calculated from the condition rate and base value. Determines whether the condition is a percentage of the base, a fixed monetary amount, or quantity/weight/volume-dependent.. Valid values are `percentage|fixed_amount|quantity_dependent|weight_dependent|volume_dependent|formula`',
  condition_category STRING COMMENT 'Business classification of the pricing condition at the header level, grouping condition types into functional categories such as price, discount, surcharge, freight, tax, rebate, intercompany, or minimum order. Enables price waterfall grouping and analytics. [ENUM-REF-CANDIDATE: price|discount|surcharge|freight|tax|rebate|intercompany|minimum_order|other — 9 candidates stripped; promote to reference product]',
  condition_currency STRING COMMENT 'ISO 4217 currency code in which the condition rate is defined in the condition record master. May differ from the document currency when the condition record is maintained in a different currency and requires conversion.. Valid values are `^[A-Z]{3}$`',
  condition_origin STRING COMMENT 'Indicates the origin or source of the condition determination — whether it was derived from a condition record, manually entered, pulled from a sales contract, linked to a rebate agreement, or applied as an intercompany pricing rule. [ENUM-REF-CANDIDATE: condition_record|manual|contract|rebate_agreement|pricing_rule|intercompany|default — 7 candidates stripped; promote to reference product]',
  condition_quantity DECIMAL(18,2) COMMENT 'Reference quantity used in the condition rate calculation for quantity-dependent pricing conditions. Represents the denominator quantity for per-unit rate conditions (e.g., rate per 100 units).',
  condition_rate DECIMAL(18,2) COMMENT 'Rate or percentage used to calculate the condition value. For percentage-based conditions (e.g., 5% header discount), this holds the percentage. For fixed-amount conditions, this holds the per-unit or flat rate. Interpretation depends on condition_calculation_type.',
  condition_record_number STRING COMMENT 'Reference number of the master condition record (pricing master data) from which this header condition was automatically determined. Enables traceability back to the pricing master data for audit and governance.',
  condition_status STRING COMMENT 'Processing status of the pricing condition record on the sales order header. Statistical conditions are included in the price waterfall for reporting but do not affect the net order value. Manually_changed indicates a user override of the system-determined value.. Valid values are `active|inactive|manually_changed|deleted|statistical|error`',
  condition_type STRING COMMENT 'SAP SD condition type code identifying the nature of the pricing element (e.g., PR00 for base price, HA00 for header discount, HB00 for header surcharge, HD00 for freight, AMIW for minimum order value surcharge, PI01 for intercompany markup). Drives the pricing procedure logic.',
  condition_type_description STRING COMMENT 'Human-readable description of the condition type (e.g., Header Discount, Freight Surcharge, Minimum Order Surcharge, Intercompany Markup) to support reporting and price waterfall visualization.',
  condition_unit STRING COMMENT 'Unit of measure associated with the condition rate for quantity- or weight-dependent conditions (e.g., EA for each, KG for kilogram, LB for pound). Blank for percentage-based conditions.',
  condition_value DECIMAL(18,2) COMMENT 'Monetary value of the pricing condition applied at the sales order header level in the document currency. Represents the absolute amount of the discount, surcharge, freight charge, or markup. Positive values increase the order value; negative values reduce it.',
  counter STRING COMMENT 'Counter within a pricing procedure step, allowing multiple condition records at the same step number. Together with step_number, uniquely positions this condition within the pricing procedure.',
  created_timestamp TIMESTAMP COMMENT 'Timestamp when this pricing condition record was first created on the sales order header, either by the pricing engine during order creation or by manual entry. Used for audit trail and data lineage.',
  currency STRING COMMENT 'ISO 4217 three-letter currency code in which the condition value is expressed (e.g., USD, EUR, GBP). Matches the sales order document currency.. Valid values are `^[A-Z]{3}$`',
  exclusion_indicator STRING COMMENT 'Indicates whether this condition or its pricing step has been excluded from the price calculation due to a condition exclusion group rule. When conditions are mutually exclusive (e.g., best-price logic), only the most favorable condition is applied and others are excluded.. Valid values are `not_excluded|condition_excluded|step_excluded`',
  is_mandatory BOOLEAN COMMENT 'Indicates whether this condition type is mandatory in the pricing procedure (True) and must be present for the order to be processed, or optional (False). Mandatory conditions trigger an error if not found during pricing.',
  is_manually_entered BOOLEAN COMMENT 'Indicates whether the condition value or rate was manually entered or overridden by a sales representative (True), as opposed to being automatically determined by the pricing engine from condition records (False). Supports audit and pricing compliance controls.',
  is_statistical BOOLEAN COMMENT 'Indicates whether this condition is statistical only (True) and does not affect the net order value, or whether it actively contributes to the price calculation (False). Statistical conditions are used for reporting, cost analysis, and price waterfall transparency.',
  last_changed_timestamp TIMESTAMP COMMENT 'Timestamp of the most recent modification to this pricing condition record, including value changes, manual overrides, or status updates. Supports change tracking and pricing audit requirements.',
  plant STRING COMMENT 'Plant or manufacturing site code associated with the sales order header, used to contextualize freight surcharges, intercompany markups, and plant-specific pricing conditions. Modeled as an attribute per VREQ-008 multi-site rule — not duplicated as a separate domain.',
  pricing_date DATE COMMENT 'The date used to determine applicable condition records and validity periods for this pricing condition. Typically the order creation date or a contractually agreed pricing date. Drives which condition record version is selected.',
  pricing_procedure STRING COMMENT 'Identifier of the pricing procedure (calculation schema) under which this condition record is evaluated. Determines the sequence of condition types applied to the sales order header (e.g., RVAA01 for standard sales, ICAA01 for intercompany).',
  region STRING COMMENT 'Geographic sales region associated with the sales order, used for regional pricing analysis and condition applicability. Modeled as an attribute per VREQ-008 — not duplicated as a separate domain per region.',
  sales_org STRING COMMENT 'SAP SD sales organization code under which the parent sales order and this pricing condition are processed. Represents the organizational unit responsible for the sale of products and services, enabling multi-org pricing analysis.',
  scale_basis STRING COMMENT 'Defines the basis on which pricing scales are applied for this condition type at the header level (e.g., total order quantity, total order value, total weight). Enables tiered pricing and volume discount analysis.. Valid values are `quantity|value|weight|volume|none`',
  scale_value DECIMAL(18,2) COMMENT 'The scale threshold value (quantity, value, or weight) at which this condition rate applies. Used to identify which tier of a tiered pricing scale was triggered for this sales order header.',
  source_system STRING COMMENT 'Identifies the originating operational system of record from which this pricing condition record was sourced. Supports SSOT (Single Source of Truth) governance in multi-ERP environments resulting from M&A activity (e.g., SAP S/4HANA SD vs Oracle ERP Cloud). Required per VREQ-004.. Valid values are `SAP_S4HANA_SD|Salesforce_CRM|Oracle_ERP_Cloud|manual`',
  step_number STRING COMMENT 'Sequential step number within the pricing procedure at which this condition type is evaluated. Defines the order of condition application in the price waterfall calculation.',
  valid_from DATE COMMENT 'Start date of the validity period for the underlying condition record from which this header condition was determined. Supports temporal pricing analysis and contract compliance verification.',
  valid_to DATE COMMENT 'End date of the validity period for the underlying condition record. After this date, the condition record is no longer valid for automatic pricing determination. Used for contract expiry monitoring and pricing governance.',
  CONSTRAINT `pk_order_header_condition` PRIMARY KEY (`order_header_condition_id`),
  CONSTRAINT `fk_sales_order_order_header_condition_order_id` FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`)
)
COMMENT 'Pricing condition record applied at the sales order header level capturing header-level pricing elements such as header discounts, freight surcharges, minimum order surcharges, and intercompany markups. Captures condition type, condition value, currency, calculation base, condition category, pricing procedure step, counter, and source_system. Complements order_line_condition for complete price waterfall reconstruction at the order level.';

-- COMMAND ----------
-- order_line_condition
CREATE OR REPLACE TABLE `order_line_condition` (
  order_line_condition_id BIGINT NOT NULL COMMENT 'Surrogate primary key uniquely identifying a pricing condition record applied at the sales order line item level within the Databricks Silver Layer.',
  order_line_id BIGINT COMMENT 'Foreign key linking to sales_order.order_line. Business justification: order_line_condition is a pricing condition record applied at the sales order line level. It must reference its parent order_line to support granular price building, discount/surcharge application, an',
  access_sequence_code STRING COMMENT 'Code identifying the access sequence used to find the applicable condition record during automatic pricing determination. Defines the hierarchy of search keys (e.g., customer/material, price list/material, material) applied by the pricing engine.',
  approval_status STRING COMMENT 'Approval workflow status for manually entered or overridden pricing conditions. Manual price deviations in industrial manufacturing sales typically require management approval per internal controls and SOX compliance requirements.. Valid values are `not_required|pending|approved|rejected`',
  approval_timestamp TIMESTAMP COMMENT 'Date and time when the manual pricing condition was approved by the authorized approver. Part of the audit trail for SOX-compliant pricing override controls.',
  approved_by STRING COMMENT 'User ID or name of the sales manager or authorized approver who approved a manually entered or overridden pricing condition. Required for SOX audit trail on manual price deviations.',
  calculation_base_value DECIMAL(18,2) COMMENT 'The monetary base amount upon which the condition rate is applied to derive the condition value. For percentage-based conditions, this is the subtotal from prior pricing steps that serves as the calculation foundation.',
  calculation_type STRING COMMENT 'Method used to calculate the condition value from the condition rate and base. Determines whether the condition is applied as a percentage of the base, a fixed monetary amount, or a quantity/weight/volume-dependent charge.. Valid values are `percentage|fixed_amount|quantity_based|weight_based|volume_based|formula`',
  channel_type STRING COMMENT 'Sales channel discriminator indicating whether the order line condition applies to a direct/OE (Original Equipment) order, distributor order, dealer order, e-commerce order, intercompany transaction, or OEM arrangement. Enables channel-specific pricing analysis and margin reporting per VREQ-009.. Valid values are `direct_oe|distributor|dealer|ecommerce|intercompany|oem`',
  condition_category STRING COMMENT 'Business classification of the pricing condition into functional categories used for price waterfall analysis and revenue reporting. Distinguishes between base price, discounts, surcharges, freight charges, taxes, rebates, and cash discounts. [ENUM-REF-CANDIDATE: price|discount|surcharge|freight|tax|rebate|royalty|cash_discount — 8 candidates stripped; promote to reference product]',
  condition_currency STRING COMMENT 'ISO 4217 three-letter currency code in which the condition value and rate are expressed. Supports multi-currency pricing for global industrial manufacturing sales operations.. Valid values are `^[A-Z]{3}$`',
  condition_origin STRING COMMENT 'Indicates the origin of the pricing condition — whether it was automatically determined from a condition record, manually entered, transferred from a contract or scheduling agreement, derived from an intercompany transaction, or applied from a promotional pricing campaign.. Valid values are `automatic|manual|transfer|intercompany|contract|promotion`',
  condition_quantity DECIMAL(18,2) COMMENT 'Quantity to which the condition rate applies, expressed in the condition unit of measure. Used for quantity-scaled pricing conditions such as freight charges per pallet or surcharges per unit.',
  condition_rate DECIMAL(18,2) COMMENT 'Rate or percentage value of the pricing condition before application to the calculation base. For percentage-based conditions (e.g., 5% discount), this holds the percentage. For fixed-amount conditions, this holds the per-unit rate.',
  condition_record_number STRING COMMENT 'Reference number of the master condition record (pricing master data) from which this order line condition was derived. Enables traceability back to the pricing master data for audit and price waterfall reconstruction.',
  condition_status STRING COMMENT 'Current lifecycle status of the pricing condition record on the order line. Active conditions contribute to the net price; inactive or deleted conditions are retained for audit; superseded conditions have been replaced by a repricing action.. Valid values are `active|inactive|deleted|superseded`',
  condition_type_code STRING COMMENT 'SAP SD condition type code identifying the nature of the pricing element (e.g., PR00 for base price, K007 for customer discount, KF00 for freight, MWST for tax). Drives the pricing procedure logic and price waterfall classification.',
  condition_unit STRING COMMENT 'Unit of measure associated with the condition rate for quantity-based or weight-based pricing conditions (e.g., EA for per-each, KG for per-kilogram, M for per-meter). Blank for percentage-based conditions.',
  condition_value DECIMAL(18,2) COMMENT 'Monetary value of the pricing condition applied to the order line in the document currency. Represents the absolute amount contributed by this condition element to the price waterfall (positive for prices/surcharges, negative for discounts).',
  condition_value_local DECIMAL(18,2) COMMENT 'Condition value converted to the company code local currency for financial reporting and general ledger posting. Supports multi-currency consolidation across global manufacturing plants and subsidiaries.',
  counter STRING COMMENT 'Counter within a pricing procedure step allowing multiple condition records at the same step number. Used to differentiate between alternative or supplementary conditions at the same pricing step.',
  created_timestamp TIMESTAMP COMMENT 'Date and time when the pricing condition record was first created on the sales order line. Establishes the audit trail start point for the condition lifecycle.',
  is_inactive BOOLEAN COMMENT 'Indicates whether this pricing condition has been deactivated on the order line. Inactive conditions are retained for audit and price waterfall reconstruction but do not contribute to the final net price.',
  is_manual BOOLEAN COMMENT 'Indicates whether the pricing condition was manually entered or overridden by a sales representative rather than automatically determined by the pricing engine. Manual conditions require audit trail and approval workflow compliance.',
  is_statistical BOOLEAN COMMENT 'Indicates whether the condition is statistical only (informational) and does not affect the net price or document value. Statistical conditions are used for reporting and analysis purposes such as list price reference or target price tracking.',
  last_modified_timestamp TIMESTAMP COMMENT 'Date and time of the most recent modification to the pricing condition record. Tracks repricing events, manual overrides, and condition updates throughout the order lifecycle.',
  local_currency STRING COMMENT 'ISO 4217 three-letter currency code of the company code local currency used for condition value conversion and financial reporting. Determined by the plant or company code associated with the sales order.. Valid values are `^[A-Z]{3}$`',
  pricing_date DATE COMMENT 'The date used to determine the applicable condition record from the pricing master data. Condition records are validity-date-controlled; the pricing date determines which rate is selected from overlapping validity periods.',
  pricing_procedure_code STRING COMMENT 'Identifier of the pricing procedure (calculation schema) under which this condition was determined. Defines the sequence of condition types applied to build the full price waterfall for the order line.',
  pricing_procedure_step_description STRING COMMENT 'Human-readable description of the pricing procedure step for this condition, such as Gross Price, Customer Discount, Freight Surcharge, or Output Tax. Supports price waterfall reporting and business user interpretation without requiring lookup to pricing configuration.',
  repricing_reason_code STRING COMMENT 'Code indicating the business reason for a repricing action that modified or replaced this condition (e.g., contract amendment, price list update, customer negotiation, ECN-driven cost change). Supports revenue variance analysis and audit compliance.',
  scale_basis STRING COMMENT 'Defines the basis on which pricing scales are applied for this condition type — whether the rate varies by order quantity, order value, weight, or volume. Supports tiered pricing structures common in industrial manufacturing volume agreements.. Valid values are `quantity|value|weight|volume|none`',
  scale_quantity DECIMAL(18,2) COMMENT 'The quantity threshold from the pricing scale that was matched during condition determination. Indicates which tier of a quantity-based scale pricing structure was applied to this order line.',
  source_system STRING COMMENT 'Identifier of the originating operational system of record from which this pricing condition record was extracted. Supports SSOT (Single Source of Truth) multi-ERP traceability per VREQ-004, distinguishing between SAP S/4HANA SD, Salesforce CRM, and Oracle ERP Cloud (M&A secondary ERP) as source systems.. Valid values are `SAP_SD|SALESFORCE_CRM|ORACLE_ERP_CLOUD`',
  source_system_condition_key STRING COMMENT 'Natural key of the pricing condition record in the originating source system (e.g., SAP KONV document number + item + step + counter composite key, or Salesforce price adjustment ID). Enables reverse traceability from the lakehouse back to the system of record for audit and reconciliation.',
  step_number STRING COMMENT 'Sequential step number within the pricing procedure at which this condition type is evaluated. Determines the order of price element application in the price waterfall calculation.',
  tax_code STRING COMMENT 'Tax code associated with tax-category pricing conditions (e.g., VAT, GST, sales tax). Links the condition to the applicable tax jurisdiction and rate for statutory tax reporting and compliance.',
  tax_jurisdiction_code STRING COMMENT 'Geographic tax jurisdiction code identifying the applicable tax authority for tax-category conditions. Used for multi-jurisdiction tax compliance in cross-border industrial manufacturing sales.',
  CONSTRAINT `pk_order_line_condition` PRIMARY KEY (`order_line_condition_id`),
  CONSTRAINT `fk_sales_order_order_line_condition_order_line_id` FOREIGN KEY (`order_line_id`) REFERENCES `order_line` (`order_line_id`)
)
COMMENT 'Pricing condition record applied at the sales order line item level capturing the granular price build-up for each order line. Captures condition type (price, discount, surcharge, freight, tax), condition value, currency, calculation base, condition category, pricing procedure step, counter, manual vs automatic flag, and source_system. Enables full price waterfall reconstruction per line item for revenue analysis and audit compliance.';


-- COMMAND ----------
-- ============================== METRIC VIEWS ================================

-- COMMAND ----------
-- metric view: sales_order_order
CREATE VIEW sales_order_order (
  order_date COMMENT 'Date the order was created',
  order_type COMMENT 'Business type of the order',
  sales_group COMMENT 'Sales group responsible for the order',
  sales_office COMMENT 'Sales office handling the order',
  plant_id COMMENT 'Manufacturing plant associated with the order',
  source_system COMMENT 'Originating ERP system',
  order_count COMMENT 'Number of orders',
  total_net_value COMMENT 'Sum of net value across all orders',
  average_order_value COMMENT 'Average net value per order')
COMMENT 'Core order level KPIs'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: '`meridian_model`.`sales_order_model`.`order`'

comment: Core order level KPIs

dimensions:
  - name: order_date
    expr: order_date
    comment: Date the order was created

  - name: order_type
    expr: order_type
    comment: Business type of the order

  - name: sales_group
    expr: sales_group
    comment: Sales group responsible for the order

  - name: sales_office
    expr: sales_office
    comment: Sales office handling the order

  - name: plant_id
    expr: plant_id
    comment: Manufacturing plant associated with the order

  - name: source_system
    expr: source_system
    comment: Originating ERP system

measures:
  - name: order_count
    expr: COUNT(1)
    comment: Number of orders

  - name: total_net_value
    expr: SUM(CAST(net_value AS DOUBLE))
    comment: Sum of net value across all orders

  - name: average_order_value
    expr: AVG(CAST(net_value AS DOUBLE))
    comment: Average net value per order
$$

-- COMMAND ----------
-- metric view: sales_order_order_line
CREATE VIEW sales_order_order_line (
  line_status COMMENT 'Current status of the order line',
  product_hierarchy_code COMMENT 'Product hierarchy classification',
  lot_number COMMENT 'Lot identifier for traceability',
  serial_number COMMENT 'Serial identifier for traceability',
  plant_id COMMENT 'Plant where the line is fulfilled',
  source_system COMMENT 'Originating ERP system',
  order_line_count COMMENT 'Number of order line records',
  total_line_net_value COMMENT 'Sum of net value for all order lines',
  total_line_quantity COMMENT 'Total quantity ordered across all lines',
  average_line_price COMMENT 'Average net price per line')
COMMENT 'Line‑level financial and quantity KPIs'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: '`meridian_model`.`sales_order_model`.`order_line`'

comment: Line‑level financial and quantity KPIs

dimensions:
  - name: line_status
    expr: line_status
    comment: Current status of the order line

  - name: product_hierarchy_code
    expr: product_hierarchy_code
    comment: Product hierarchy classification

  - name: lot_number
    expr: lot_number
    comment: Lot identifier for traceability

  - name: serial_number
    expr: serial_number
    comment: Serial identifier for traceability

  - name: plant_id
    expr: plant_id
    comment: Plant where the line is fulfilled

  - name: source_system
    expr: source_system
    comment: Originating ERP system

measures:
  - name: order_line_count
    expr: COUNT(1)
    comment: Number of order line records

  - name: total_line_net_value
    expr: SUM(CAST(net_value AS DOUBLE))
    comment: Sum of net value for all order lines

  - name: total_line_quantity
    expr: SUM(CAST(order_quantity AS DOUBLE))
    comment: Total quantity ordered across all lines

  - name: average_line_price
    expr: AVG(CAST(net_price AS DOUBLE))
    comment: Average net price per line
$$

-- COMMAND ----------
-- metric view: sales_order_atp_check
CREATE VIEW sales_order_atp_check (
  check_status COMMENT 'Result status of the ATP check',
  check_type COMMENT 'Type of ATP check',
  plant_id COMMENT 'Plant for which the check was run',
  sku_id COMMENT 'SKU identifier',
  source_system COMMENT 'Originating ERP system',
  atp_check_count COMMENT 'Number of ATP checks performed',
  total_atp_quantity_available COMMENT 'Sum of ATP quantity available')
COMMENT 'Availability check KPIs'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: '`meridian_model`.`sales_order_model`.`atp_check`'

comment: Availability check KPIs

dimensions:
  - name: check_status
    expr: check_status
    comment: Result status of the ATP check

  - name: check_type
    expr: check_type
    comment: Type of ATP check

  - name: plant_id
    expr: plant_id
    comment: Plant for which the check was run

  - name: sku_id
    expr: sku_id
    comment: SKU identifier

  - name: source_system
    expr: source_system
    comment: Originating ERP system

measures:
  - name: atp_check_count
    expr: COUNT(1)
    comment: Number of ATP checks performed

  - name: total_atp_quantity_available
    expr: SUM(CAST(atp_quantity_available AS DOUBLE))
    comment: Sum of ATP quantity available
$$

-- COMMAND ----------
-- metric view: sales_order_delivery_schedule
CREATE VIEW sales_order_delivery_schedule (
  schedule_status COMMENT 'Current status of the schedule',
  schedule_type COMMENT 'Type of delivery schedule',
  plant_id COMMENT 'Plant linked to the schedule',
  region_code COMMENT 'Geographic region code',
  source_system COMMENT 'Originating ERP system',
  schedule_count COMMENT 'Number of delivery schedules',
  total_open_quantity COMMENT 'Sum of open quantity across schedules',
  total_delivered_quantity COMMENT 'Sum of cumulative delivered quantity')
COMMENT 'Delivery planning KPIs'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: '`meridian_model`.`sales_order_model`.`delivery_schedule`'

comment: Delivery planning KPIs

dimensions:
  - name: schedule_status
    expr: schedule_status
    comment: Current status of the schedule

  - name: schedule_type
    expr: schedule_type
    comment: Type of delivery schedule

  - name: plant_id
    expr: plant_id
    comment: Plant linked to the schedule

  - name: region_code
    expr: region_code
    comment: Geographic region code

  - name: source_system
    expr: source_system
    comment: Originating ERP system

measures:
  - name: schedule_count
    expr: COUNT(1)
    comment: Number of delivery schedules

  - name: total_open_quantity
    expr: SUM(CAST(open_quantity AS DOUBLE))
    comment: Sum of open quantity across schedules

  - name: total_delivered_quantity
    expr: SUM(CAST(cumulative_delivered_quantity AS DOUBLE))
    comment: Sum of cumulative delivered quantity
$$

-- COMMAND ----------
-- metric view: sales_order_order_status_event
CREATE VIEW sales_order_order_status_event (
  event_type COMMENT 'Type of status event',
  event_date COMMENT 'Date of the event',
  plant_id COMMENT 'Plant where the event occurred',
  source_system COMMENT 'Originating ERP system',
  event_count COMMENT 'Total number of status events',
  otd_issue_count COMMENT 'Count of on‑time‑delivery flag issues')
COMMENT 'Operational event tracking KPIs'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: '`meridian_model`.`sales_order_model`.`order_status_event`'

comment: Operational event tracking KPIs

dimensions:
  - name: event_type
    expr: event_type
    comment: Type of status event

  - name: event_date
    expr: "DATE_TRUNC('day', event_timestamp)"
    comment: Date of the event

  - name: plant_id
    expr: plant_id
    comment: Plant where the event occurred

  - name: source_system
    expr: source_system
    comment: Originating ERP system

measures:
  - name: event_count
    expr: COUNT(1)
    comment: Total number of status events

  - name: otd_issue_count
    expr: SUM(CASE WHEN otd_flag THEN 1 ELSE 0 END)
    comment: Count of on‑time‑delivery flag issues
$$

-- COMMAND ----------
-- metric view: sales_order_sales_contract
CREATE VIEW sales_order_sales_contract (
  contract_type COMMENT 'Type of sales contract',
  contract_status COMMENT 'Current status of the contract',
  plant_code COMMENT 'Plant code associated with the contract',
  source_system COMMENT 'Originating ERP system',
  contract_count COMMENT 'Number of sales contracts',
  total_contract_value COMMENT 'Sum of target contract value',
  average_contract_value COMMENT 'Average target value per contract')
COMMENT 'Contract financial KPIs'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: '`meridian_model`.`sales_order_model`.`sales_contract`'

comment: Contract financial KPIs

dimensions:
  - name: contract_type
    expr: contract_type
    comment: Type of sales contract

  - name: contract_status
    expr: contract_status
    comment: Current status of the contract

  - name: plant_code
    expr: plant_code
    comment: Plant code associated with the contract

  - name: source_system
    expr: source_system
    comment: Originating ERP system

measures:
  - name: contract_count
    expr: COUNT(1)
    comment: Number of sales contracts

  - name: total_contract_value
    expr: SUM(CAST(target_value AS DOUBLE))
    comment: Sum of target contract value

  - name: average_contract_value
    expr: AVG(CAST(target_value AS DOUBLE))
    comment: Average target value per contract
$$
