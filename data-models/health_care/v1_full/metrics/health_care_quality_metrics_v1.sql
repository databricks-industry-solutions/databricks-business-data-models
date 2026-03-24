-- Metric views for domain: quality | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_accreditation_status`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "High‑level view of accreditation activity and overall scores for strategic oversight"
  source: "`cmoore_customer_demos`.`quality`.`accreditation`"
  dimensions:
    - name: "entity_type"
      expr: entity_type
      comment: "Type of entity being accredited (e.g., health plan, provider organization)"
    - name: "accrediting_body"
      expr: accrediting_body
      comment: "Accrediting organization (NCQA, URAC, Joint Commission)"
    - name: "status"
      expr: status
      comment: "Current accreditation status (active, expired, suspended, revoked)"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Calendar year the accreditation became effective"
  measures:
    - name: "total_accreditations"
      expr: COUNT(1)
      comment: "Total number of accreditation records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_accreditation_score`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key performance indicators for accreditation quality and activity"
  source: "`cmoore_customer_demos`.`quality`.`accreditation`"
  dimensions:
    - name: "accrediting_body"
      expr: accrediting_body
      comment: "Accrediting organization"
    - name: "entity_type"
      expr: entity_type
      comment: "Entity type being accredited"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Year accreditation became effective"
  measures:
    - name: "average_overall_score"
      expr: AVG(CAST(overall_score AS DOUBLE))
      comment: "Average overall accreditation score across all records"
    - name: "active_accreditations"
      expr: COUNT(CASE WHEN record_active_flag THEN 1 END)
      comment: "Count of currently active accreditation records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_clinical_metric_performance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Strategic view of clinical quality metric outcomes used for quality improvement and star rating impact"
  source: "`cmoore_customer_demos`.`quality`.`clinical_metric_result`"
  dimensions:
    - name: "metric_category"
      expr: metric_category
      comment: "High‑level category of the clinical metric"
    - name: "metric_type"
      expr: metric_type
      comment: "Type of metric (process, outcome, patient experience, etc.)"
    - name: "entity_type"
      expr: entity_type
      comment: "Entity the metric result applies to (provider, facility, cohort)"
    - name: "geographic_region"
      expr: geographic_region
      comment: "Geographic region of the entity"
    - name: "state_code"
      expr: state_code
      comment: "Two‑letter state code"
    - name: "measurement_year"
      expr: YEAR(measurement_period_start_date)
      comment: "Calendar year of the measurement period"
  measures:
    - name: "average_rate"
      expr: AVG(CAST(rate AS DOUBLE))
      comment: "Average clinical metric rate (percentage) across the selected period"
    - name: "average_risk_adjusted_rate"
      expr: AVG(CAST(risk_adjusted_rate AS DOUBLE))
      comment: "Average risk‑adjusted rate for the metric"
    - name: "total_metric_results"
      expr: COUNT(1)
      comment: "Total number of clinical metric result records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_measure_outcomes`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Core KPI view for HEDIS/quality measure performance, supporting executive monitoring and remediation"
  source: "`cmoore_customer_demos`.`quality`.`measure_result`"
  dimensions:
    - name: "measure_id"
      expr: measure_id
      comment: "Identifier of the quality measure"
    - name: "measure_domain"
      expr: measure_domain
      comment: "Domain/category of the measure (e.g., Effectiveness, Access)"
    - name: "reporting_year"
      expr: reporting_year
      comment: "Calendar year the result was reported"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line (Commercial, Medicare, Medicaid, etc.)"
    - name: "geographic_region"
      expr: geographic_region
      comment: "Geographic region of the result"
    - name: "state_code"
      expr: state_code
      comment: "State code"
  measures:
    - name: "average_rate_value"
      expr: AVG(CAST(rate_value AS DOUBLE))
      comment: "Average raw rate value for the measure"
    - name: "average_rate_percentage"
      expr: AVG(CAST(rate_percentage AS DOUBLE))
      comment: "Average rate expressed as a percentage"
    - name: "compliant_measure_results"
      expr: COUNT(CASE WHEN compliance_status = 'compliant' THEN 1 END)
      comment: "Count of measure results that met compliance"
    - name: "total_measure_results"
      expr: COUNT(1)
      comment: "Total number of measure result records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_star_rating_summary`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Executive‑level KPI for monitoring overall star rating performance and trends"
  source: "`cmoore_customer_demos`.`quality`.`star_rating`"
  dimensions:
    - name: "rating_year"
      expr: rating_year
      comment: "Calendar year of the star rating"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line of the plan"
    - name: "state_code"
      expr: state_code
      comment: "State where the plan operates"
    - name: "service_area_type"
      expr: service_area_type
      comment: "Geographic service area classification"
  measures:
    - name: "average_overall_star_rating"
      expr: AVG(CAST(overall_star_rating AS DOUBLE))
      comment: "Average overall CMS star rating across plans"
    - name: "average_part_c_rating"
      expr: AVG(CAST(part_c_summary_rating AS DOUBLE))
      comment: "Average Part C (health plan) star rating"
    - name: "average_part_d_rating"
      expr: AVG(CAST(part_d_summary_rating AS DOUBLE))
      comment: "Average Part D (prescription drug) star rating"
    - name: "plan_count"
      expr: COUNT(1)
      comment: "Number of plans with a star rating for the period"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_provider_quality_score`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Strategic KPI for provider performance, used for network management and value‑based contracts"
  source: "`cmoore_customer_demos`.`quality`.`provider_score`"
  dimensions:
    - name: "specialty"
      expr: specialty
      comment: "Provider specialty (e.g., Cardiology, Primary Care)"
    - name: "network_tier"
      expr: network_tier
      comment: "Network tier classification"
    - name: "geographic_region"
      expr: geographic_region
      comment: "Region of provider practice"
    - name: "state_code"
      expr: state_code
      comment: "State code"
    - name: "measurement_year"
      expr: YEAR(measurement_period_start_date)
      comment: "Year of the measurement period"
  measures:
    - name: "average_composite_score"
      expr: AVG(CAST(composite_score AS DOUBLE))
      comment: "Average composite quality score for providers"
    - name: "average_stars_rating"
      expr: AVG(CAST(stars_rating AS DOUBLE))
      comment: "Average CMS stars rating for providers"
    - name: "provider_count"
      expr: COUNT(1)
      comment: "Total number of provider quality score records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_satisfaction_score`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key member experience KPI that drives CAHPS‑based star rating and quality incentive eligibility"
  source: "`cmoore_customer_demos`.`quality`.`satisfaction_score`"
  dimensions:
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line (Commercial, Medicare, Medicaid, etc.)"
    - name: "plan_type"
      expr: plan_type
      comment: "Plan product type (HMO, PPO, SNP, etc.)"
    - name: "geographic_region"
      expr: geographic_region
      comment: "Region of the member population"
    - name: "state_code"
      expr: state_code
      comment: "State code"
    - name: "reporting_year"
      expr: reporting_year
      comment: "Calendar year of the satisfaction measurement"
  measures:
    - name: "average_composite_score"
      expr: AVG(CAST(composite_score AS DOUBLE))
      comment: "Average overall member satisfaction score"
    - name: "average_nps_score"
      expr: AVG(CAST(nps_score AS DOUBLE))
      comment: "Average Net Promoter Score"
    - name: "survey_response_rate"
      expr: AVG(CAST(response_rate_percentage AS DOUBLE))
      comment: "Average survey response rate percentage"
    - name: "survey_count"
      expr: COUNT(1)
      comment: "Number of satisfaction score records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`quality_hedis_score_summary`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Executive KPI linking HEDIS performance to star rating and bonus eligibility"
  source: "`cmoore_customer_demos`.`quality`.`hedis_score`"
  dimensions:
    - name: "plan_type"
      expr: plan_type
      comment: "Type of health plan"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line"
    - name: "reporting_year"
      expr: reporting_year
      comment: "Calendar year of the HEDIS reporting"
    - name: "state_code"
      expr: state_code
      comment: "State where the plan operates"
  measures:
    - name: "average_score_value"
      expr: AVG(CAST(score_value AS DOUBLE))
      comment: "Average HEDIS score value (percentage) across plans"
    - name: "average_star_rating"
      expr: AVG(CAST(rating AS DOUBLE))
      comment: "Average CMS star rating derived from HEDIS scores"
    - name: "plan_count"
      expr: COUNT(1)
      comment: "Number of plan‑level HEDIS score records"
$$;