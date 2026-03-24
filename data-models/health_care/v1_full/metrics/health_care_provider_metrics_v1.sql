-- Metric views for domain: provider | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`provider_aco_performance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key performance indicators for Accountable Care Organizations that drive revenue, quality incentives and risk‑adjusted payments."
  source: "`cmoore_customer_demos`.`provider`.`accountable_care_organization`"
  dimensions:
    - name: "aco_id"
      expr: accountable_care_organization_id
      comment: "Unique identifier for the ACO."
    - name: "aco_name"
      expr: name
      comment: "Legal name of the ACO."
    - name: "aco_type"
      expr: aco_type
      comment: "Classification of the ACO based on program participation."
    - name: "state"
      expr: state
      comment: "State where the ACO is headquartered."
    - name: "contract_status"
      expr: contract_status
      comment: "Current status of the ACO contract (e.g., active, terminated)."
  measures:
    - name: "total_shared_savings_amount"
      expr: SUM(CAST(shared_savings_amount AS DOUBLE))
      comment: "Total shared savings earned by the ACO in the most recent performance year, indicating financial benefit from value‑based contracts."
    - name: "average_quality_score"
      expr: AVG(CAST(quality_score AS DOUBLE))
      comment: "Average composite quality score across ACOs, reflecting overall care quality performance."
    - name: "average_risk_score"
      expr: AVG(CAST(risk_score AS DOUBLE))
      comment: "Average risk adjustment score of ACO populations, used for forecasting capitation payments."
    - name: "total_enrollment"
      expr: SUM(CAST(enrollment_count AS DOUBLE))
      comment: "Total number of members enrolled in all ACOs, a driver of revenue potential."
    - name: "total_providers"
      expr: SUM(CAST(provider_count AS DOUBLE))
      comment: "Total count of providers (physicians, hospitals) participating in ACOs, indicating network breadth."
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`provider_provider_credentialing`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing health metrics that support compliance monitoring and risk management."
  source: "`cmoore_customer_demos`.`provider`.`credential_summary`"
  dimensions:
    - name: "profile_id"
      expr: profile_id
      comment: "Provider profile surrogate key."
    - name: "provider_type"
      expr: provider_type
      comment: "Classification of the provider (individual, organization, hospital)."
    - name: "primary_specialty"
      expr: primary_specialty
      comment: "Main clinical specialty of the provider."
    - name: "state"
      expr: primary_license_state
      comment: "State where the primary professional license is issued."
  measures:
    - name: "credentialed_providers"
      expr: SUM(CASE WHEN credentialing_status = 'credentialed' THEN 1 ELSE 0 END)
      comment: "Count of providers whose credentialing is current and active."
    - name: "expired_credentialings"
      expr: SUM(CASE WHEN credentialing_status = 'expired' THEN 1 ELSE 0 END)
      comment: "Count of providers with expired credentialing, a risk indicator."
    - name: "average_days_since_last_verification"
      expr: AVG(DATEDIFF('day', last_verification_date, CURRENT_DATE()))
      comment: "Average number of days since the provider's credentials were last verified, measuring credentialing freshness."
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`provider_provider_network_participation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Network participation KPIs that guide capacity planning, PCP availability and telehealth rollout."
  source: "`cmoore_customer_demos`.`provider`.`network_affiliation`"
  dimensions:
    - name: "network_id"
      expr: network_id
      comment: "Identifier of the provider network."
    - name: "network_name"
      expr: name
      comment: "Human‑readable network name."
    - name: "network_type"
      expr: type
      comment: "Network classification (HMO, PPO, etc.)."
    - name: "state"
      expr: state
      comment: "State of the provider's primary practice location."
    - name: "specialty"
      expr: primary_specialty
      comment: "Provider's primary specialty, used for specialty‑specific capacity analysis."
  measures:
    - name: "active_participants"
      expr: SUM(CASE WHEN participation_status = 'active' THEN 1 ELSE 0 END)
      comment: "Number of providers actively participating in the network."
    - name: "pcp_participants"
      expr: SUM(CASE WHEN pcp_flag = true THEN 1 ELSE 0 END)
      comment: "Count of providers designated as Primary Care Physicians, critical for member assignment."
    - name: "specialist_participants"
      expr: SUM(CASE WHEN specialist_flag = true THEN 1 ELSE 0 END)
      comment: "Count of specialist providers, influencing specialty access metrics."
    - name: "telehealth_enabled"
      expr: SUM(CASE WHEN telehealth_enabled_flag = true THEN 1 ELSE 0 END)
      comment: "Number of providers enabled for telehealth, supporting virtual care strategy."
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`provider_metrics_provider_quality`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Aggregated quality metric KPIs that drive incentive payments and public reporting."
  source: "`cmoore_customer_demos`.`provider`.`quality_metric`"
  dimensions:
    - name: "profile_id"
      expr: profile_id
      comment: "Provider profile identifier."
    - name: "measure_category"
      expr: measure_category
      comment: "HEDIS domain category (e.g., effectiveness, access)."
    - name: "lob"
      expr: lob
      comment: "Line of business (commercial, Medicare, Medicaid)."
    - name: "reporting_year"
      expr: reporting_year
      comment: "Calendar year of the quality measurement period."
    - name: "state"
      expr: state
      comment: "State where the provider delivers care."
  measures:
    - name: "average_measure_rate"
      expr: AVG(CAST(rate AS DOUBLE))
      comment: "Average performance rate across quality measures, indicating overall care effectiveness."
    - name: "average_measure_score"
      expr: AVG(CAST(score AS DOUBLE))
      comment: "Average quality score, used for star rating calculations."
    - name: "average_star_rating"
      expr: AVG(CAST(star_rating AS DOUBLE))
      comment: "Mean star rating across measures, directly tied to public quality reporting."
    - name: "measure_count"
      expr: COUNT(1)
      comment: "Total number of quality metric records evaluated for the provider."
$$;