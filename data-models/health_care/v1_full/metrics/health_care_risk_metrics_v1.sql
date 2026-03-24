-- Metric views for domain: risk | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`risk_adjustment_submission`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key performance indicators for risk adjustment data submissions (RAPS/EDPS) that affect revenue forecasts and data‑quality initiatives"
  source: "`cmoore_customer_demos`.`risk`.`adjustment_submission`"
  dimensions:
    - name: "measurement_year"
      expr: measurement_year
      comment: "Calendar year of the risk data measurement period"
    - name: "payment_year"
      expr: payment_year
      comment: "Year in which CMS will apply the risk scores for capitation"
    - name: "plan_benefit_package_id"
      expr: plan_benefit_package_id
      comment: "Identifier of the specific benefit package the submission applies to"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business segment (e.g., Medicare Advantage, Part D)"
  measures:
    - name: "total_submissions"
      expr: COUNT(1)
      comment: "Number of adjustment submissions recorded in the period"
    - name: "average_acceptance_rate_percent"
      expr: AVG(CAST(acceptance_rate_percent AS DOUBLE))
      comment: "Average acceptance rate across submissions, indicating data quality and CMS acceptance"
    - name: "total_estimated_raf_impact"
      expr: SUM(CAST(estimated_raf_impact AS DOUBLE))
      comment: "Aggregate estimated RAF score impact from all submissions, driving projected risk‑adjusted revenue"
    - name: "total_estimated_revenue_impact_amount"
      expr: SUM(CAST(estimated_revenue_impact_amount AS DOUBLE))
      comment: "Projected dollar impact of the submissions on Medicare Advantage payments"
    - name: "submissions_requiring_resubmission"
      expr: SUM(CASE WHEN resubmission_required_flag THEN 1 ELSE 0 END)
      comment: "Count of submissions flagged for correction and resubmission"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`risk_member_risk_profile`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Strategic KPIs that drive revenue forecasting, care‑management prioritization and risk‑adjustment monitoring"
  source: "`cmoore_customer_demos`.`risk`.`member_risk_profile`"
  dimensions:
    - name: "payment_year"
      expr: payment_year
      comment: "Year for which the risk‑adjusted payment is calculated"
    - name: "risk_model_version"
      expr: risk_model_version
      comment: "CMS risk‑adjustment model version applied"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Product line (e.g., Medicare Advantage, Part D)"
  measures:
    - name: "member_count"
      expr: COUNT(1)
      comment: "Total number of member risk profiles in the view"
    - name: "average_raf_score"
      expr: AVG(CAST(raf_score AS DOUBLE))
      comment: "Mean RAF score across members, reflecting overall risk level"
    - name: "average_normalized_raf_score"
      expr: AVG(CAST(normalized_raf_score AS DOUBLE))
      comment: "Mean normalized RAF score after CMS budget‑neutrality adjustment"
    - name: "total_estimated_annual_revenue"
      expr: SUM(CAST(estimated_annual_revenue AS DOUBLE))
      comment: "Projected annual revenue from risk‑adjusted payments for the member cohort"
    - name: "high_risk_tier_members"
      expr: SUM(CASE WHEN risk_tier = 'High' THEN 1 ELSE 0 END)
      comment: "Count of members classified in the high risk tier, a focus for care‑management resources"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`risk_payment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial KPIs that directly impact profitability and compliance monitoring for Medicare Advantage contracts"
  source: "`cmoore_customer_demos`.`risk`.`payment`"
  dimensions:
    - name: "year"
      expr: year
      comment: "Calendar year of the payment"
    - name: "month"
      expr: month
      comment: "Month within the payment year"
    - name: "plan_benefit_package_id"
      expr: plan_benefit_package_id
      comment: "Benefit package identifier for the contract"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Product line (e.g., MA, MA‑PD)"
  measures:
    - name: "total_net_payment_amount"
      expr: SUM(CAST(net_payment_amount AS DOUBLE))
      comment: "Total net amount received after all adjustments, rebates and deductions"
    - name: "total_risk_adjusted_amount"
      expr: SUM(CAST(risk_adjusted_amount AS DOUBLE))
      comment: "Aggregate amount attributable to risk adjustment (RAF) across all payments"
    - name: "average_raf_score"
      expr: AVG(CAST(raf_score AS DOUBLE))
      comment: "Mean RAF score of members associated with the payments, indicating risk intensity"
    - name: "total_quality_bonus_amount"
      expr: SUM(CAST(quality_bonus_amount AS DOUBLE))
      comment: "Cumulative quality‑bonus payments earned via CMS Star Ratings"
    - name: "payments_flagged_for_audit"
      expr: SUM(CASE WHEN audit_flag THEN 1 ELSE 0 END)
      comment: "Count of payment records that have been flagged for CMS RADV or internal audit"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`risk_member_hcc_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Clinical risk complexity metrics that inform care‑management intensity and model validation"
  source: "`cmoore_customer_demos`.`risk`.`member_hcc_assignment`"
  dimensions:
    - name: "measurement_year"
      expr: measurement_year
      comment: "Year of the measurement period for which HCCs are captured"
    - name: "payment_year"
      expr: payment_year
      comment: "Year in which the HCC‑derived risk scores affect payments"
    - name: "plan_benefit_package_id"
      expr: plan_benefit_package_id
      comment: "Benefit package context for the assignment"
    - name: "risk_model_type"
      expr: risk_model_type
      comment: "Specific CMS risk model (e.g., CMS‑HCC, RxHCC)"
  measures:
    - name: "total_hcc_assignments"
      expr: COUNT(1)
      comment: "Total HCC assignment records processed"
    - name: "distinct_members"
      expr: COUNT(DISTINCT member_profile_id)
      comment: "Number of unique members with at least one HCC assignment"
    - name: "distinct_hcc_codes"
      expr: COUNT(DISTINCT hcc_code)
      comment: "Count of unique HCC codes assigned, reflecting clinical complexity breadth"
$$;