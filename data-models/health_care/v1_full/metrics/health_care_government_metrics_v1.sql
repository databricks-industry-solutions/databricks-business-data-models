-- Metric views for domain: government | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_benefit_design_financial`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial summary of government benefit designs to support pricing and product strategy decisions"
  source: "`cmoore_customer_demos`.`government`.`benefit_design`"
  dimensions:
    - name: "plan_year"
      expr: plan_year
      comment: "Plan year (calendar year) of the benefit design"
    - name: "plan_type"
      expr: plan_type
      comment: "Type of government plan (e.g., HMO, PPO, SNP)"
    - name: "lob"
      expr: lob
      comment: "Line of business category for the benefit design"
    - name: "snp_type"
      expr: snp_type
      comment: "Special Needs Plan classification"
    - name: "contract_number"
      expr: contract_number
      comment: "CMS contract number associated with the design"
    - name: "status"
      expr: status
      comment: "Operational status of the benefit design"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Calendar year when the benefit design became effective"
  measures:
    - name: "total_monthly_premium"
      expr: SUM(CAST(monthly_premium_amount AS DOUBLE))
      comment: "Total monthly premium amount across all benefit designs"
    - name: "avg_annual_deductible"
      expr: AVG(CAST(annual_deductible_amount AS DOUBLE))
      comment: "Average annual deductible amount for benefit designs"
    - name: "avg_moop"
      expr: AVG(CAST(moop_amount AS DOUBLE))
      comment: "Average maximum out‑of‑pocket (MOOP) amount"
    - name: "design_count"
      expr: COUNT(1)
      comment: "Number of benefit design records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_program_claim_financial`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key financial performance indicators for government program claims"
  source: "`cmoore_customer_demos`.`government`.`program_claim`"
  dimensions:
    - name: "claim_status"
      expr: claim_status
      comment: "Current processing status of the claim"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line (e.g., Medicare Advantage, Medicaid)"
  measures:
    - name: "total_billed"
      expr: SUM(CAST(billed_amount AS DOUBLE))
      comment: "Total amount billed on claims"
    - name: "total_allowed"
      expr: SUM(CAST(allowed_amount AS DOUBLE))
      comment: "Total allowed amount per contract and plan"
    - name: "total_paid"
      expr: SUM(CAST(paid_amount AS DOUBLE))
      comment: "Total paid amount to providers"
    - name: "total_member_responsibility"
      expr: SUM(CAST(member_responsibility_amount AS DOUBLE))
      comment: "Total member cost‑sharing (deductible, copay, coinsurance)"
    - name: "claim_count"
      expr: COUNT(1)
      comment: "Number of claim records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_program_claim_efficiency`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Operational efficiency and risk indicators for claim processing"
  source: "`cmoore_customer_demos`.`government`.`program_claim`"
  dimensions:
    - name: "claim_status"
      expr: claim_status
      comment: "Current processing status of the claim"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line of the claim"
  measures:
    - name: "delayed_claims"
      expr: COUNT(CASE WHEN processing_turnaround_days > 30 THEN 1 END)
      comment: "Count of claims where processing took more than 30 days"
    - name: "delayed_payment_claims"
      expr: COUNT(CASE WHEN payment_turnaround_days > 30 THEN 1 END)
      comment: "Count of claims where payment was issued more than 30 days after receipt"
    - name: "fraud_flagged_claims"
      expr: COUNT(CASE WHEN fraud_flag THEN 1 END)
      comment: "Count of claims flagged for potential fraud"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_program_payment_timeliness`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Timeliness and compliance metrics for government program payments"
  source: "`cmoore_customer_demos`.`government`.`program_payment`"
  dimensions:
    - name: "payment_status"
      expr: payment_status
      comment: "Current lifecycle status of the payment"
    - name: "program_type"
      expr: program_type
      comment: "Government program type (e.g., Medicare Advantage, Medicaid)"
    - name: "payment_year"
      expr: YEAR(payment_date)
      comment: "Calendar year of the payment"
    - name: "payment_month"
      expr: MONTH(payment_date)
      comment: "Month of the payment"
  measures:
    - name: "total_payment_amount"
      expr: SUM(CAST(payment_amount AS DOUBLE))
      comment: "Total dollar amount of payments issued"
    - name: "net_payment_sum"
      expr: SUM(CAST(net_payment_amount AS DOUBLE))
      comment: "Sum of net payments after adjustments and withholdings"
    - name: "prompt_payment_compliant_count"
      expr: COUNT(CASE WHEN is_prompt_payment_compliant THEN 1 END)
      comment: "Count of payments made within prompt‑payment regulations"
    - name: "non_prompt_payment_count"
      expr: COUNT(CASE WHEN NOT is_prompt_payment_compliant THEN 1 END)
      comment: "Count of payments that missed prompt‑payment windows"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_provider_participation_quality`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Network adequacy and quality metrics for provider participation in government programs"
  source: "`cmoore_customer_demos`.`government`.`provider_program_participation`"
  dimensions:
    - name: "program_type"
      expr: program_type
      comment: "Government program (e.g., Medicare Advantage, Medicaid)"
    - name: "participation_status"
      expr: participation_status
      comment: "Current participation status (active, inactive, suspended)"
    - name: "network_tier"
      expr: network_tier
      comment: "Provider network tier determining member cost‑share"
    - name: "service_area_state"
      expr: service_area_state
      comment: "State of the provider's service area"
  measures:
    - name: "active_provider_count"
      expr: COUNT(CASE WHEN participation_status = 'active' THEN 1 END)
      comment: "Number of providers actively participating in the program"
    - name: "avg_star_rating"
      expr: AVG(CAST(star_rating AS DOUBLE))
      comment: "Average CMS star rating of participating providers"
    - name: "pcp_provider_count"
      expr: COUNT(CASE WHEN pcp_flag THEN 1 END)
      comment: "Count of providers designated as Primary Care Physicians"
    - name: "specialist_provider_count"
      expr: COUNT(CASE WHEN specialist_flag THEN 1 END)
      comment: "Count of specialist providers"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_contract_sla_compliance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Compliance and financial impact of Service Level Agreements on provider contracts"
  source: "`cmoore_customer_demos`.`government`.`contract_sla`"
  dimensions:
    - name: "status"
      expr: status
      comment: "Lifecycle status of the SLA (active, suspended, waived, terminated)"
    - name: "measurement_period"
      expr: measurement_period
      comment: "Time period over which SLA performance is measured"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Calendar year when the SLA became effective"
  measures:
    - name: "sla_count"
      expr: COUNT(1)
      comment: "Number of SLA records linked to contracts"
    - name: "avg_actual_performance"
      expr: AVG(CAST(actual_performance_percent AS DOUBLE))
      comment: "Average actual performance percentage across SLAs"
    - name: "total_penalties_assessed"
      expr: SUM(CAST(penalties_assessed_ytd AS DOUBLE))
      comment: "Total penalties assessed year‑to‑date for SLA non‑compliance"
    - name: "non_compliant_sla_count"
      expr: COUNT(CASE WHEN compliance_status <> 'compliant' THEN 1 END)
      comment: "Count of SLAs that are not currently compliant"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`government_program_risk_adjustment_yield`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Revenue‑impacting risk‑adjustment metrics that drive Medicare Advantage payments"
  source: "`cmoore_customer_demos`.`government`.`program_risk_adjustment`"
  dimensions:
    - name: "plan_year"
      expr: plan_year
      comment: "Plan year for which risk adjustment applies"
    - name: "program_type"
      expr: program_type
      comment: "Government program type (e.g., MA, MA‑PD, PDP)"
  measures:
    - name: "total_raf_score"
      expr: SUM(CAST(raf_score AS DOUBLE))
      comment: "Sum of RAF scores for all risk‑adjustment records"
    - name: "avg_raf_score"
      expr: AVG(CAST(raf_score AS DOUBLE))
      comment: "Average RAF score per member"
    - name: "total_risk_payment"
      expr: SUM(CAST(payment_amount AS DOUBLE))
      comment: "Total CMS payment amount linked to risk adjustment"
    - name: "risk_record_count"
      expr: COUNT(1)
      comment: "Number of risk‑adjustment records submitted"
$$;