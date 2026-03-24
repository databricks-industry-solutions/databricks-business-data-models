-- Metric views for domain: eligibility | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`eligibility_benefit_package`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key KPIs for benefit package design and eligibility"
  source: "`cmoore_customer_demos`.`eligibility`.`benefit_package`"
  dimensions:
    - name: "plan_type"
      expr: plan_type
      comment: "Health plan classification (HMO, PPO, etc.)"
    - name: "metal_tier"
      expr: metal_tier
      comment: "ACA metal tier (Bronze, Silver, Gold, Platinum)"
    - name: "status"
      expr: status
      comment: "Current operational status of the benefit package"
    - name: "coverage_year"
      expr: DATE_TRUNC('year', coverage_effective_date)
      comment: "Year the benefit package became effective"
  measures:
    - name: "total_packages"
      expr: COUNT(1)
      comment: "Total number of benefit packages"
    - name: "avg_actuarial_value"
      expr: AVG(CAST(actuarial_value_percentage AS DOUBLE))
      comment: "Average actuarial value percentage across benefit packages"
    - name: "avg_individual_deductible"
      expr: AVG(CAST(deductible_individual_amount AS DOUBLE))
      comment: "Average individual deductible amount"
    - name: "avg_oop_max_individual"
      expr: AVG(CAST(out_of_pocket_max_individual_amount AS DOUBLE))
      comment: "Average out‑of‑pocket maximum for an individual"
    - name: "hsa_eligible_packages"
      expr: COUNT(CASE WHEN hsa_eligible_flag THEN 1 END)
      comment: "Number of benefit packages eligible for HSA"
    - name: "fsa_eligible_packages"
      expr: COUNT(CASE WHEN fsa_eligible_flag THEN 1 END)
      comment: "Number of benefit packages eligible for FSA"
    - name: "hra_eligible_packages"
      expr: COUNT(CASE WHEN hra_eligible_flag THEN 1 END)
      comment: "Number of benefit packages eligible for HRA"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`eligibility_cob_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Strategic view of COB rule configuration"
  source: "`cmoore_customer_demos`.`eligibility`.`cob_rule`"
  dimensions:
    - name: "payer_position"
      expr: payer_position
      comment: "Position in payment hierarchy (primary, secondary, etc.)"
    - name: "rule_type"
      expr: rule_type
      comment: "Category of COB rule"
    - name: "applies_to_coverage_type"
      expr: applies_to_coverage_type
      comment: "Coverage type the rule applies to (medical, dental, etc.)"
    - name: "state_specific_rule"
      expr: state_specific_rule
      comment: "State code if rule is state‑specific, otherwise 'ALL'"
  measures:
    - name: "total_rules"
      expr: COUNT(1)
      comment: "Total number of coordination of benefits rules"
    - name: "avg_priority_sequence"
      expr: AVG(CAST(priority_sequence AS DOUBLE))
      comment: "Average priority sequence (lower = higher priority)"
    - name: "duplicate_payment_allowed"
      expr: COUNT(CASE WHEN allows_duplicate_payment THEN 1 END)
      comment: "Number of rules that permit duplicate payments"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`eligibility_coverage`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Coverage‑level financial and cost‑sharing KPIs"
  source: "`cmoore_customer_demos`.`eligibility`.`coverage`"
  dimensions:
    - name: "plan_type"
      expr: plan_type
      comment: "Plan type (HMO, PPO, etc.)"
    - name: "lob"
      expr: lob
      comment: "Line of business (Commercial, Medicare, Medicaid, Marketplace)"
    - name: "effective_year"
      expr: DATE_TRUNC('year', effective_date)
      comment: "Year coverage became effective"
  measures:
    - name: "total_coverage"
      expr: COUNT(1)
      comment: "Total active coverage records"
    - name: "avg_individual_deductible"
      expr: AVG(CAST(deductible_individual AS DOUBLE))
      comment: "Average individual deductible amount"
    - name: "avg_family_deductible"
      expr: AVG(CAST(deductible_family AS DOUBLE))
      comment: "Average family deductible amount"
    - name: "avg_oop_max_individual"
      expr: AVG(CAST(oop_max_individual AS DOUBLE))
      comment: "Average out‑of‑pocket maximum for an individual"
    - name: "avg_premium_amount"
      expr: AVG(CAST(premium_amount AS DOUBLE))
      comment: "Average monthly premium amount"
    - name: "cobra_coverage"
      expr: COUNT(CASE WHEN cobra_indicator THEN 1 END)
      comment: "Number of coverages that are COBRA eligible"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`eligibility_verification`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Operational performance of eligibility verification engine"
  source: "`cmoore_customer_demos`.`eligibility`.`verification`"
  dimensions:
    - name: "plan_type"
      expr: plan_type
      comment: "Plan type associated with the verification"
    - name: "lob"
      expr: lob
      comment: "Line of business"
    - name: "service_type_code"
      expr: service_type_code
      comment: "Service type code being verified"
    - name: "queue_status"
      expr: queue_status
      comment: "Current processing status in the verification queue"
    - name: "request_year"
      expr: DATE_TRUNC('year', request_timestamp)
      comment: "Year the verification request was received"
  measures:
    - name: "total_verifications"
      expr: COUNT(1)
      comment: "Total eligibility verification requests processed"
    - name: "avg_response_time_ms"
      expr: AVG(CAST(response_time_milliseconds AS DOUBLE))
      comment: "Average response time in milliseconds"
    - name: "error_count"
      expr: COUNT(CASE WHEN error_flag THEN 1 END)
      comment: "Number of verification requests that returned an error"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`eligibility_verification_response`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial impact of eligibility decisions"
  source: "`cmoore_customer_demos`.`eligibility`.`verification_response`"
  dimensions:
    - name: "coverage_type"
      expr: coverage_type
      comment: "Category of coverage (medical, dental, vision, etc.)"
    - name: "service_year"
      expr: DATE_TRUNC('year', service_date)
      comment: "Year of the service date"
    - name: "network_indicator"
      expr: network_indicator
      comment: "Network status of the service (In‑Network, Out‑Network, Unknown)"
    - name: "authorization_required"
      expr: authorization_required
      comment: "Flag indicating if prior authorization is required"
  measures:
    - name: "total_responses"
      expr: COUNT(1)
      comment: "Total verification response records"
    - name: "avg_allowed_amount"
      expr: AVG(CAST(allowed_amount AS DOUBLE))
      comment: "Average allowed amount for services"
    - name: "avg_patient_responsibility"
      expr: AVG(CAST(patient_responsibility_amount AS DOUBLE))
      comment: "Average patient responsibility amount (copay, coinsurance, deductible)"
    - name: "auth_required_count"
      expr: COUNT(CASE WHEN authorization_required THEN 1 END)
      comment: "Number of responses indicating prior authorization is required"
$$;