-- Metric views for domain: product | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`product_product_plan`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key financial and cost‑sharing KPIs for product plans"
  source: "`cmoore_customer_demos`.`product`.`product_plan`"
  dimensions:
    - name: "plan_type"
      expr: plan_type
      comment: "Plan type classification (e.g., HMO, PPO)"
    - name: "market"
      expr: market
      comment: "Target market segment for the plan"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Line of business (Commercial, Medicare, Medicaid, Exchange)"
    - name: "metal_level"
      expr: metal_level
      comment: "ACA metal tier (Bronze, Silver, Gold, Platinum)"
    - name: "status"
      expr: status
      comment: "Current lifecycle status of the plan"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Calendar year when the plan became effective"
  measures:
    - name: "total_plans"
      expr: COUNT(1)
      comment: "Total number of product plans"
    - name: "average_premium_amount"
      expr: AVG(CAST(premium_amount AS DOUBLE))
      comment: "Average monthly premium amount across plans"
    - name: "average_deductible_individual"
      expr: AVG(CAST(deductible_individual AS DOUBLE))
      comment: "Average individual deductible amount"
    - name: "average_out_of_pocket_max_individual"
      expr: AVG(CAST(out_of_pocket_max_individual AS DOUBLE))
      comment: "Average individual out-of-pocket maximum"
    - name: "average_copay_primary_care"
      expr: AVG(CAST(copay_primary_care AS DOUBLE))
      comment: "Average copayment for primary care visits"
    - name: "average_coinsurance_percentage"
      expr: AVG(CAST(coinsurance_percentage AS DOUBLE))
      comment: "Average coinsurance percentage across plans"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`product_attribute`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Governance and member‑experience metrics for product attributes"
  source: "`cmoore_customer_demos`.`product`.`attribute`"
  dimensions:
    - name: "line_of_business"
      expr: line_of_business
      comment: "Line of business the attribute applies to"
    - name: "category"
      expr: category
      comment: "Logical grouping of the attribute"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Year the attribute became effective"
    - name: "is_aca_compliant"
      expr: is_aca_compliant
      comment: "Flag indicating ACA compliance"
    - name: "is_regulatory_required"
      expr: is_regulatory_required
      comment: "Flag indicating regulatory requirement"
    - name: "is_member_visible"
      expr: is_member_visible
      comment: "Flag indicating member visibility"
  measures:
    - name: "total_attributes"
      expr: COUNT(1)
      comment: "Total number of product attributes"
    - name: "pct_aca_compliant"
      expr: AVG(CASE WHEN is_aca_compliant THEN 1 ELSE 0 END) * 100
      comment: "Percentage of attributes that are ACA compliant"
    - name: "pct_member_visible"
      expr: AVG(CASE WHEN is_member_visible THEN 1 ELSE 0 END) * 100
      comment: "Percentage of attributes visible to members"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`product_enrollment_window`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Capacity and utilization KPIs for enrollment windows"
  source: "`cmoore_customer_demos`.`product`.`enrollment_window`"
  dimensions:
    - name: "market_segment"
      expr: market_segment
      comment: "Market segment the enrollment window targets"
    - name: "window_type"
      expr: window_type
      comment: "Classification of the enrollment window (e.g., AOE, SEP)"
    - name: "start_year"
      expr: YEAR(start_date)
      comment: "Calendar year the enrollment window starts"
    - name: "status"
      expr: status
      comment: "Operational status of the enrollment window"
    - name: "is_active"
      expr: is_active
      comment: "Flag indicating if the window is currently active"
  measures:
    - name: "total_windows"
      expr: COUNT(1)
      comment: "Total number of enrollment windows defined"
    - name: "average_enrollment_capacity"
      expr: AVG(CAST(enrollment_cap AS DOUBLE))
      comment: "Average enrollment capacity across windows"
    - name: "enrollment_utilization_pct"
      expr: AVG(CAST(current_enrollment_count AS DOUBLE) / NULLIF(enrollment_cap, 0)) * 100
      comment: "Average percentage of enrollment capacity utilized"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`product_plan_version`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Versioning and pricing trend metrics for health plans"
  source: "`cmoore_customer_demos`.`product`.`plan_version`"
  dimensions:
    - name: "plan_type_id"
      expr: plan_type_id
      comment: "Foreign key to plan type for the version"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Year the plan version became effective"
    - name: "plan_status_id"
      expr: plan_status_id
      comment: "Foreign key to plan status for the version"
  measures:
    - name: "total_versions"
      expr: COUNT(1)
      comment: "Total number of plan versions recorded"
    - name: "average_premium_amount"
      expr: AVG(CAST(premium_amount AS DOUBLE))
      comment: "Average monthly premium across plan versions"
    - name: "average_deductible_individual_amount"
      expr: AVG(CAST(deductible_individual_amount AS DOUBLE))
      comment: "Average individual deductible amount across versions"
$$;