-- Metric views for domain: member | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_member_profile_overview`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "High‑level snapshot of the member population, useful for executive health‑plan performance monitoring"
  source: "`cmoore_customer_demos`.`member`.`member_profile`"
  dimensions:
    - name: "lob"
      expr: lob
      comment: "Line of business (e.g., Commercial, Medicare)"
  measures:
    - name: "total_members"
      expr: COUNT(1)
      comment: "Total number of member records"
    - name: "avg_risk_score"
      expr: AVG(CAST(risk_score AS DOUBLE))
      comment: "Average risk adjustment score across members"
    - name: "avg_premium_amount"
      expr: AVG(CAST(premium_amount AS DOUBLE))
      comment: "Average monthly premium amount for members"
    - name: "avg_deductible_amount"
      expr: AVG(CAST(deductible_amount AS DOUBLE))
      comment: "Average deductible amount across members"
    - name: "avg_out_of_pocket_maximum"
      expr: AVG(CAST(out_of_pocket_maximum AS DOUBLE))
      comment: "Average out‑of‑pocket maximum across members"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_active_member_profile`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Core active member count – a primary KPI for revenue forecasting and capacity planning"
  source: "`cmoore_customer_demos`.`member`.`member_profile`"
  filter: member_status = 'Active' AND current_record_indicator = true
  dimensions:
    - name: "lob"
      expr: lob
      comment: "Line of business"
    - name: "plan_type"
      expr: plan_type
      comment: "Plan design (HMO, PPO, etc.)"
    - name: "network_id"
      expr: network_id
      comment: "Provider network identifier"
    - name: "primary_language"
      expr: primary_language
      comment: "Member preferred language (ISO 639‑1)"
  measures:
    - name: "active_member_count"
      expr: COUNT(1)
      comment: "Count of members with active status"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_address_quality`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Address data quality metrics that drive mail‑based communications and cost‑avoidance"
  source: "`cmoore_customer_demos`.`member`.`address`"
  dimensions:
    - name: "type"
      expr: type
      comment: "Address purpose (home, mailing, billing, etc.)"
    - name: "state_code"
      expr: state_code
      comment: "Two‑letter state code"
    - name: "country_code"
      expr: country_code
      comment: "ISO country code"
  measures:
    - name: "total_addresses"
      expr: COUNT(1)
      comment: "Total address records"
    - name: "standardized_address_count"
      expr: SUM(CASE WHEN standardized_flag THEN 1 ELSE 0 END)
      comment: "Number of addresses that have been standardized against postal authority standards"
    - name: "avg_deliverability_score"
      expr: AVG(CAST(deliverability_score AS DOUBLE))
      comment: "Average deliverability score (0‑100) indicating mailing success likelihood"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_consent_rates`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Consent capture metrics that inform compliance and marketing strategy"
  source: "`cmoore_customer_demos`.`member`.`consent`"
  dimensions:
    - name: "type"
      expr: type
      comment: "Consent category (e.g., data sharing, marketing)"
    - name: "status"
      expr: status
      comment: "Current consent status"
    - name: "source_system"
      expr: source_system
      comment: "System that originated the consent"
  measures:
    - name: "total_consents"
      expr: COUNT(1)
      comment: "Total consent records captured"
    - name: "marketing_consents"
      expr: SUM(CASE WHEN marketing_consent_flag THEN 1 ELSE 0 END)
      comment: "Count of members who have opted‑in to marketing communications"
    - name: "research_consents"
      expr: SUM(CASE WHEN research_consent_flag THEN 1 ELSE 0 END)
      comment: "Count of members who have opted‑in to research use of their data"
    - name: "revoked_consents"
      expr: SUM(CASE WHEN status = 'Revoked' THEN 1 ELSE 0 END)
      comment: "Count of consents that have been revoked"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_program_enrollment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Program participation KPIs that support quality reporting and ROI analysis"
  source: "`cmoore_customer_demos`.`member`.`program_enrollment`"
  dimensions:
    - name: "program_id"
      expr: program_id
      comment: "Identifier of the care or wellness program"
    - name: "participation_status"
      expr: participation_status
      comment: "Current status of the member's participation"
    - name: "enrollment_method"
      expr: enrollment_method
      comment: "How the member was enrolled (Automatic, Opt‑In, Referral, Outreach)"
  measures:
    - name: "enrollment_count"
      expr: COUNT(1)
      comment: "Total program enrollment records"
    - name: "completed_enrollments"
      expr: SUM(CASE WHEN participation_status = 'Completed' THEN 1 ELSE 0 END)
      comment: "Number of enrollments that have reached completion"
    - name: "avg_outcome_score"
      expr: AVG(CAST(outcome_score AS DOUBLE))
      comment: "Average outcome score for program participants"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_primary_pcp_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Primary care assignment coverage – a leading indicator of network adequacy and member satisfaction"
  source: "`cmoore_customer_demos`.`member`.`provider_assignment`"
  filter: assignment_type = 'Primary Care Physician' AND status = 'Active'
  dimensions:
    - name: "network_id"
      expr: network_id
      comment: "Provider network identifier"
    - name: "is_telehealth_enabled"
      expr: is_telehealth_enabled
      comment: "Whether the PCP offers telehealth services"
    - name: "is_accepting_new_patients"
      expr: is_accepting_new_patients
      comment: "Current new‑patient acceptance status"
  measures:
    - name: "pcp_assigned_members"
      expr: COUNT(DISTINCT member_profile_id)
      comment: "Number of members with an active primary care physician assignment"
    - name: "avg_distance_from_member_miles"
      expr: AVG(CAST(distance_from_member_miles AS DOUBLE))
      comment: "Average geographic distance (miles) between member home address and assigned PCP practice"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_member_event_latency`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Event processing latency KPI – helps operations monitor timeliness of event handling"
  source: "`cmoore_customer_demos`.`member`.`member_event`"
  dimensions:
    - name: "type_code"
      expr: type_code
      comment: "Event type code (e.g., enrollment, plan change)"
    - name: "source"
      expr: source
      comment: "System or channel that originated the event"
    - name: "status"
      expr: status
      comment: "Current processing status of the event"
  measures:
    - name: "event_count"
      expr: COUNT(1)
      comment: "Total member events recorded"
    - name: "avg_processing_days"
      expr: AVG(DATEDIFF(processed_date, DATE(timestamp)))
      comment: "Average number of days between event occurrence and processing"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_tax_subsidy_eligibility`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Tax‑subsidy eligibility metrics that drive Marketplace premium credit calculations"
  source: "`cmoore_customer_demos`.`member`.`tax_info`"
  dimensions:
    - name: "tax_year"
      expr: tax_year
      comment: "Calendar year of the tax record"
    - name: "filing_status"
      expr: filing_status
      comment: "Federal filing status (e.g., Single, Married)"
  measures:
    - name: "total_tax_records"
      expr: COUNT(1)
      comment: "Total tax information records"
    - name: "aptc_eligible_members"
      expr: SUM(CASE WHEN aptc_eligible_flag THEN 1 ELSE 0 END)
      comment: "Count of members eligible for Advanced Premium Tax Credits"
    - name: "csr_eligible_members"
      expr: SUM(CASE WHEN csr_eligible_flag THEN 1 ELSE 0 END)
      comment: "Count of members eligible for Cost‑Sharing Reductions"
    - name: "avg_household_income"
      expr: AVG(CAST(household_income_amount AS DOUBLE))
      comment: "Average reported household income for tax‑eligible members"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`member_relationship_active_dependents`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Active dependent relationship counts – essential for eligibility and premium calculations"
  source: "`cmoore_customer_demos`.`member`.`relationship`"
  filter: status = 'Active' AND (termination_date IS NULL OR termination_date > CURRENT_DATE())
  dimensions:
    - name: "type_code"
      expr: type_code
      comment: "Relationship type code (e.g., 01=Spouse, 19=Child)"
  measures:
    - name: "active_relationships"
      expr: COUNT(1)
      comment: "Number of active dependent relationships"
    - name: "primary_dependent_count"
      expr: SUM(CASE WHEN is_primary_dependent THEN 1 ELSE 0 END)
      comment: "Count of dependents flagged as primary for the subscriber"
$$;