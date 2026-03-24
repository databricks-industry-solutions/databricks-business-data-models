-- Metric views for domain: contract | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:07:47

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_agreement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Agreement business metrics"
  source: "`cmoore_customer_demos`.`contract`.`agreement`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Subtype"
      expr: subtype
    - name: "Execution Date"
      expr: execution_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Renewal Date"
      expr: renewal_date
    - name: "Auto Renewal Indicator"
      expr: auto_renewal_indicator
    - name: "Notice Period Days"
      expr: notice_period_days
    - name: "Network Tier"
      expr: network_tier
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Geographic Coverage Area"
      expr: geographic_coverage_area
    - name: "Service Categories Covered"
      expr: service_categories_covered
    - name: "Reimbursement Methodology"
      expr: reimbursement_methodology
    - name: "Fee Schedule Name"
      expr: fee_schedule_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Agreement"
      expr: COUNT(DISTINCT agreement_id)
    - name: "Total Medicare Rate Percentage"
      expr: SUM(medicare_rate_percentage)
    - name: "Average Medicare Rate Percentage"
      expr: AVG(medicare_rate_percentage)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
    - name: "Total Stop Loss Threshold Amount"
      expr: SUM(stop_loss_threshold_amount)
    - name: "Average Stop Loss Threshold Amount"
      expr: AVG(stop_loss_threshold_amount)
    - name: "Total Contract Value Total Amount"
      expr: SUM(contract_value_total_amount)
    - name: "Average Contract Value Total Amount"
      expr: AVG(contract_value_total_amount)
    - name: "Total Annual Contract Value Amount"
      expr: SUM(annual_contract_value_amount)
    - name: "Average Annual Contract Value Amount"
      expr: AVG(annual_contract_value_amount)
    - name: "Total Performance Guarantee Amount"
      expr: SUM(performance_guarantee_amount)
    - name: "Average Performance Guarantee Amount"
      expr: AVG(performance_guarantee_amount)
    - name: "Total Minimum Liability Coverage Amount"
      expr: SUM(minimum_liability_coverage_amount)
    - name: "Average Minimum Liability Coverage Amount"
      expr: AVG(minimum_liability_coverage_amount)
    - name: "Total Rate Increase Cap Percentage"
      expr: SUM(rate_increase_cap_percentage)
    - name: "Average Rate Increase Cap Percentage"
      expr: AVG(rate_increase_cap_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_agreement_version`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Agreement Version business metrics"
  source: "`cmoore_customer_demos`.`contract`.`agreement_version`"
  dimensions:
    - name: "Agreement Number"
      expr: agreement_number
    - name: "Version Number"
      expr: version_number
    - name: "Version Effective Date"
      expr: version_effective_date
    - name: "Version End Date"
      expr: version_end_date
    - name: "Version Status"
      expr: version_status
    - name: "Contract Type"
      expr: contract_type
    - name: "Contract Name"
      expr: contract_name
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Type"
      expr: provider_type
    - name: "Provider Specialty"
      expr: provider_specialty
    - name: "Network Tier"
      expr: network_tier
    - name: "Lob"
      expr: lob
    - name: "Product Applicability"
      expr: product_applicability
    - name: "Geographic Scope"
      expr: geographic_scope
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Agreement Version"
      expr: COUNT(DISTINCT agreement_version_id)
    - name: "Total Base Reimbursement Rate"
      expr: SUM(base_reimbursement_rate)
    - name: "Average Base Reimbursement Rate"
      expr: AVG(base_reimbursement_rate)
    - name: "Total Medicare Percentage"
      expr: SUM(medicare_percentage)
    - name: "Average Medicare Percentage"
      expr: AVG(medicare_percentage)
    - name: "Total Charges Percentage"
      expr: SUM(charges_percentage)
    - name: "Average Charges Percentage"
      expr: AVG(charges_percentage)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Quality Incentive Percentage"
      expr: SUM(quality_incentive_percentage)
    - name: "Average Quality Incentive Percentage"
      expr: AVG(quality_incentive_percentage)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
    - name: "Total Interest Penalty Rate"
      expr: SUM(interest_penalty_rate)
    - name: "Average Interest Penalty Rate"
      expr: AVG(interest_penalty_rate)
    - name: "Total Value Based Modifier Percentage"
      expr: SUM(value_based_modifier_percentage)
    - name: "Average Value Based Modifier Percentage"
      expr: AVG(value_based_modifier_percentage)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Shared Risk Percentage"
      expr: SUM(shared_risk_percentage)
    - name: "Average Shared Risk Percentage"
      expr: AVG(shared_risk_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_amendment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Amendment business metrics"
  source: "`cmoore_customer_demos`.`contract`.`amendment`"
  dimensions:
    - name: "Version Number"
      expr: version_number
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Title"
      expr: title
    - name: "Description"
      expr: description
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Effective Date"
      expr: effective_date
    - name: "Execution Date"
      expr: execution_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Notice Date"
      expr: notice_date
    - name: "Requested Date"
      expr: requested_date
    - name: "Approved Date"
      expr: approved_date
    - name: "Clauses Modified"
      expr: clauses_modified
    - name: "Clauses Added"
      expr: clauses_added
    - name: "Clauses Deleted"
      expr: clauses_deleted
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Amendment"
      expr: COUNT(DISTINCT amendment_id)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Rate Change Percentage"
      expr: SUM(rate_change_percentage)
    - name: "Average Rate Change Percentage"
      expr: AVG(rate_change_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_approval_workflow`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Approval Workflow business metrics"
  source: "`cmoore_customer_demos`.`contract`.`approval_workflow`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Workflow Type"
      expr: workflow_type
    - name: "Contract Type"
      expr: contract_type
    - name: "Lob"
      expr: lob
    - name: "Network Tier"
      expr: network_tier
    - name: "Provider Type"
      expr: provider_type
    - name: "Specialty Type"
      expr: specialty_type
    - name: "Threshold Currency Code"
      expr: threshold_currency_code
    - name: "Risk Level"
      expr: risk_level
    - name: "Approval Sequence Count"
      expr: approval_sequence_count
    - name: "Parallel Approval Allowed"
      expr: parallel_approval_allowed
    - name: "Unanimous Approval Required"
      expr: unanimous_approval_required
    - name: "Auto Escalation Enabled"
      expr: auto_escalation_enabled
    - name: "Escalation Timeout Hours"
      expr: escalation_timeout_hours
    - name: "Sla Response Hours"
      expr: sla_response_hours
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Approval Workflow"
      expr: COUNT(DISTINCT approval_workflow_id)
    - name: "Total Contract Value Threshold Min"
      expr: SUM(contract_value_threshold_min)
    - name: "Average Contract Value Threshold Min"
      expr: AVG(contract_value_threshold_min)
    - name: "Total Contract Value Threshold Max"
      expr: SUM(contract_value_threshold_max)
    - name: "Average Contract Value Threshold Max"
      expr: AVG(contract_value_threshold_max)
    - name: "Total Approval Threshold Percentage"
      expr: SUM(approval_threshold_percentage)
    - name: "Average Approval Threshold Percentage"
      expr: AVG(approval_threshold_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_capitation_plan`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Capitation Plan business metrics"
  source: "`cmoore_customer_demos`.`contract`.`capitation_plan`"
  dimensions:
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Description"
      expr: plan_description
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Service Category"
      expr: service_category
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Rate Type"
      expr: rate_type
    - name: "Age Band Category"
      expr: age_band_category
    - name: "Gender Category"
      expr: gender_category
    - name: "Geographic Area Code"
      expr: geographic_area_code
    - name: "County Code"
      expr: county_code
    - name: "State Code"
      expr: state_code
    - name: "Network Tier"
      expr: network_tier
    - name: "Pcp Assignment Required"
      expr: pcp_assignment_required
    - name: "Member Panel Size Min"
      expr: member_panel_size_min
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Capitation Plan"
      expr: COUNT(DISTINCT capitation_plan_id)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Risk Score Floor"
      expr: SUM(risk_score_floor)
    - name: "Average Risk Score Floor"
      expr: AVG(risk_score_floor)
    - name: "Total Risk Score Ceiling"
      expr: SUM(risk_score_ceiling)
    - name: "Average Risk Score Ceiling"
      expr: AVG(risk_score_ceiling)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
    - name: "Total Quality Incentive Pool Percentage"
      expr: SUM(quality_incentive_pool_percentage)
    - name: "Average Quality Incentive Pool Percentage"
      expr: AVG(quality_incentive_pool_percentage)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Shared Risk Percentage"
      expr: SUM(shared_risk_percentage)
    - name: "Average Shared Risk Percentage"
      expr: AVG(shared_risk_percentage)
    - name: "Total Performance Corridor Lower"
      expr: SUM(performance_corridor_lower)
    - name: "Average Performance Corridor Lower"
      expr: AVG(performance_corridor_lower)
    - name: "Total Performance Corridor Upper"
      expr: SUM(performance_corridor_upper)
    - name: "Average Performance Corridor Upper"
      expr: AVG(performance_corridor_upper)
    - name: "Total Utilization Target Value"
      expr: SUM(utilization_target_value)
    - name: "Average Utilization Target Value"
      expr: AVG(utilization_target_value)
    - name: "Total Trend Factor"
      expr: SUM(trend_factor)
    - name: "Average Trend Factor"
      expr: AVG(trend_factor)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_change_request`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Change Request business metrics"
  source: "`cmoore_customer_demos`.`contract`.`change_request`"
  dimensions:
    - name: "Request Number"
      expr: request_number
    - name: "Request Type"
      expr: request_type
    - name: "Request Status"
      expr: request_status
    - name: "Priority"
      expr: priority
    - name: "Requester Name"
      expr: requester_name
    - name: "Requester Email"
      expr: requester_email
    - name: "Requester Department"
      expr: requester_department
    - name: "Requester Phone"
      expr: requester_phone
    - name: "Request Date"
      expr: request_date
    - name: "Request Timestamp"
      expr: request_timestamp
    - name: "Justification"
      expr: justification
    - name: "Business Impact Description"
      expr: business_impact_description
    - name: "Financial Impact Type"
      expr: financial_impact_type
    - name: "Requested Effective Date"
      expr: requested_effective_date
    - name: "Proposed Change Description"
      expr: proposed_change_description
    - name: "Current Contract Terms"
      expr: current_contract_terms
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Change Request"
      expr: COUNT(DISTINCT change_request_id)
    - name: "Total Estimated Financial Impact Amount"
      expr: SUM(estimated_financial_impact_amount)
    - name: "Average Estimated Financial Impact Amount"
      expr: AVG(estimated_financial_impact_amount)
    - name: "Total Mlr Impact Percentage"
      expr: SUM(mlr_impact_percentage)
    - name: "Average Mlr Impact Percentage"
      expr: AVG(mlr_impact_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_clause`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Clause business metrics"
  source: "`cmoore_customer_demos`.`contract`.`clause`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Text"
      expr: text
    - name: "Summary"
      expr: summary
    - name: "Version"
      expr: version
    - name: "Status"
      expr: status
    - name: "Is Mandatory"
      expr: is_mandatory
    - name: "Is Negotiable"
      expr: is_negotiable
    - name: "Is Standard"
      expr: is_standard
    - name: "Applicable Contract Types"
      expr: applicable_contract_types
    - name: "Applicable Lob"
      expr: applicable_lob
    - name: "Applicable Provider Types"
      expr: applicable_provider_types
    - name: "Regulatory Requirement"
      expr: regulatory_requirement
    - name: "Legal Jurisdiction"
      expr: legal_jurisdiction
    - name: "Effective Date"
      expr: effective_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Clause"
      expr: COUNT(DISTINCT clause_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_compliance_requirement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Compliance Requirement business metrics"
  source: "`cmoore_customer_demos`.`contract`.`compliance_requirement`"
  dimensions:
    - name: "Requirement Code"
      expr: requirement_code
    - name: "Requirement Name"
      expr: requirement_name
    - name: "Requirement Description"
      expr: requirement_description
    - name: "Requirement Type"
      expr: requirement_type
    - name: "Requirement Category"
      expr: requirement_category
    - name: "Regulatory Authority"
      expr: regulatory_authority
    - name: "Regulation Citation"
      expr: regulation_citation
    - name: "Applicable Line Of Business"
      expr: applicable_line_of_business
    - name: "Applicable Product Type"
      expr: applicable_product_type
    - name: "Applicable State"
      expr: applicable_state
    - name: "End Date"
      expr: end_date
    - name: "Compliance Status"
      expr: compliance_status
    - name: "Compliance Due Date"
      expr: compliance_due_date
    - name: "Last Assessment Date"
      expr: last_assessment_date
    - name: "Next Assessment Date"
      expr: next_assessment_date
    - name: "Assessment Frequency"
      expr: assessment_frequency
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Compliance Requirement"
      expr: COUNT(DISTINCT compliance_requirement_id)
    - name: "Total Monetary Penalty Amount"
      expr: SUM(monetary_penalty_amount)
    - name: "Average Monetary Penalty Amount"
      expr: AVG(monetary_penalty_amount)
    - name: "Total Implementation Cost Estimate"
      expr: SUM(implementation_cost_estimate)
    - name: "Average Implementation Cost Estimate"
      expr: AVG(implementation_cost_estimate)
    - name: "Total Ongoing Compliance Cost"
      expr: SUM(ongoing_compliance_cost)
    - name: "Average Ongoing Compliance Cost"
      expr: AVG(ongoing_compliance_cost)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_contract_discount`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Discount business metrics"
  source: "`cmoore_customer_demos`.`contract`.`contract_discount`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Basis"
      expr: basis
    - name: "Applies To Service Category"
      expr: applies_to_service_category
    - name: "Applies To Procedure Codes"
      expr: applies_to_procedure_codes
    - name: "Applies To Diagnosis Codes"
      expr: applies_to_diagnosis_codes
    - name: "Applies To Drg Codes"
      expr: applies_to_drg_codes
    - name: "Applies To Revenue Codes"
      expr: applies_to_revenue_codes
    - name: "Applies To Place Of Service"
      expr: applies_to_place_of_service
    - name: "Minimum Volume Threshold"
      expr: minimum_volume_threshold
    - name: "Maximum Volume Threshold"
      expr: maximum_volume_threshold
    - name: "Volume Measurement Unit"
      expr: volume_measurement_unit
    - name: "Volume Measurement Period"
      expr: volume_measurement_period
    - name: "Quality Metric Requirement"
      expr: quality_metric_requirement
    - name: "Network Tier"
      expr: network_tier
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Discount"
      expr: COUNT(DISTINCT contract_discount_id)
    - name: "Total Percentage"
      expr: SUM(percentage)
    - name: "Average Percentage"
      expr: AVG(percentage)
    - name: "Total Flat Amount"
      expr: SUM(flat_amount)
    - name: "Average Flat Amount"
      expr: AVG(flat_amount)
    - name: "Total Quality Threshold Value"
      expr: SUM(quality_threshold_value)
    - name: "Average Quality Threshold Value"
      expr: AVG(quality_threshold_value)
    - name: "Total Risk Sharing Percentage"
      expr: SUM(risk_sharing_percentage)
    - name: "Average Risk Sharing Percentage"
      expr: AVG(risk_sharing_percentage)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Cap Amount"
      expr: SUM(cap_amount)
    - name: "Average Cap Amount"
      expr: AVG(cap_amount)
    - name: "Total Floor Amount"
      expr: SUM(floor_amount)
    - name: "Average Floor Amount"
      expr: AVG(floor_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_contract_hierarchy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Hierarchy business metrics"
  source: "`cmoore_customer_demos`.`contract`.`contract_hierarchy`"
  dimensions:
    - name: "Parent Contract Number"
      expr: parent_contract_number
    - name: "Child Contract Number"
      expr: child_contract_number
    - name: "Relationship Type"
      expr: relationship_type
    - name: "Level"
      expr: level
    - name: "Path"
      expr: path
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Inheritance Flag"
      expr: inheritance_flag
    - name: "Override Flag"
      expr: override_flag
    - name: "Sequence Number"
      expr: sequence_number
    - name: "Version Number"
      expr: version_number
    - name: "Relationship Description"
      expr: relationship_description
    - name: "Business Reason"
      expr: business_reason
    - name: "Approval Status"
      expr: approval_status
    - name: "Approved By"
      expr: approved_by
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Hierarchy"
      expr: COUNT(DISTINCT contract_hierarchy_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_contract_payment_schedule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Payment Schedule business metrics"
  source: "`cmoore_customer_demos`.`contract`.`contract_payment_schedule`"
  dimensions:
    - name: "Schedule Sequence Number"
      expr: schedule_sequence_number
    - name: "Payment Type"
      expr: payment_type
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Frequency"
      expr: payment_frequency
    - name: "Scheduled Payment Date"
      expr: scheduled_payment_date
    - name: "Payment Due Date"
      expr: payment_due_date
    - name: "Adjustment Reason Code"
      expr: adjustment_reason_code
    - name: "Adjustment Reason Description"
      expr: adjustment_reason_description
    - name: "Currency Code"
      expr: currency_code
    - name: "Payment Status Date"
      expr: payment_status_date
    - name: "Actual Payment Date"
      expr: actual_payment_date
    - name: "Payment Period Start Date"
      expr: payment_period_start_date
    - name: "Payment Period End Date"
      expr: payment_period_end_date
    - name: "Performance Period Start Date"
      expr: performance_period_start_date
    - name: "Performance Period End Date"
      expr: performance_period_end_date
    - name: "Line Of Business"
      expr: line_of_business
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Payment Schedule"
      expr: COUNT(DISTINCT contract_payment_schedule_id)
    - name: "Total Actual Payment Amount"
      expr: SUM(actual_payment_amount)
    - name: "Average Actual Payment Amount"
      expr: AVG(actual_payment_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Quality Incentive Amount"
      expr: SUM(quality_incentive_amount)
    - name: "Average Quality Incentive Amount"
      expr: AVG(quality_incentive_amount)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Shared Savings Amount"
      expr: SUM(shared_savings_amount)
    - name: "Average Shared Savings Amount"
      expr: AVG(shared_savings_amount)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
    - name: "Total Withhold Amount"
      expr: SUM(withhold_amount)
    - name: "Average Withhold Amount"
      expr: AVG(withhold_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Interest Rate"
      expr: SUM(interest_rate)
    - name: "Average Interest Rate"
      expr: AVG(interest_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_contract_renewal`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Renewal business metrics"
  source: "`cmoore_customer_demos`.`contract`.`contract_renewal`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Previous Expiration Date"
      expr: previous_expiration_date
    - name: "Term Months"
      expr: term_months
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Initiated Date"
      expr: initiated_date
    - name: "Approved Date"
      expr: approved_date
    - name: "Executed Date"
      expr: executed_date
    - name: "Notification Date"
      expr: notification_date
    - name: "Auto Renewal Indicator"
      expr: auto_renewal_indicator
    - name: "Terms Modified Indicator"
      expr: terms_modified_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Renewal"
      expr: COUNT(DISTINCT contract_renewal_id)
    - name: "Total Rate Change Percentage"
      expr: SUM(rate_change_percentage)
    - name: "Average Rate Change Percentage"
      expr: AVG(rate_change_percentage)
    - name: "Total Stop Loss Threshold Amount"
      expr: SUM(stop_loss_threshold_amount)
    - name: "Average Stop Loss Threshold Amount"
      expr: AVG(stop_loss_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_contract_service_area`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Service Area business metrics"
  source: "`cmoore_customer_demos`.`contract`.`contract_service_area`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Geographic Scope"
      expr: geographic_scope
    - name: "State Code"
      expr: state_code
    - name: "County List"
      expr: county_list
    - name: "Zip Code List"
      expr: zip_code_list
    - name: "Msa Code"
      expr: msa_code
    - name: "Cbsa Code"
      expr: cbsa_code
    - name: "Product Type"
      expr: product_type
    - name: "Network Tier"
      expr: network_tier
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Renewal Date"
      expr: renewal_date
    - name: "Approval Date"
      expr: approval_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Service Area"
      expr: COUNT(DISTINCT contract_service_area_id)
    - name: "Total Maximum Travel Distance Miles"
      expr: SUM(maximum_travel_distance_miles)
    - name: "Average Maximum Travel Distance Miles"
      expr: AVG(maximum_travel_distance_miles)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Star Rating"
      expr: SUM(star_rating)
    - name: "Average Star Rating"
      expr: AVG(star_rating)
    - name: "Total Benchmark Rate"
      expr: SUM(benchmark_rate)
    - name: "Average Benchmark Rate"
      expr: AVG(benchmark_rate)
    - name: "Total County Ffs Rate"
      expr: SUM(county_ffs_rate)
    - name: "Average County Ffs Rate"
      expr: AVG(county_ffs_rate)
    - name: "Total Quality Bonus Percentage"
      expr: SUM(quality_bonus_percentage)
    - name: "Average Quality Bonus Percentage"
      expr: AVG(quality_bonus_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_contract_termination`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Termination business metrics"
  source: "`cmoore_customer_demos`.`contract`.`contract_termination`"
  dimensions:
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Type"
      expr: type
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Initiated By"
      expr: initiated_by
    - name: "Notice Date"
      expr: notice_date
    - name: "Notice Period Days"
      expr: notice_period_days
    - name: "Effective Date"
      expr: effective_date
    - name: "Run Out Period End Date"
      expr: run_out_period_end_date
    - name: "Member Transition Required"
      expr: member_transition_required
    - name: "Member Notification Date"
      expr: member_notification_date
    - name: "Affected Member Count"
      expr: affected_member_count
    - name: "Settlement Date"
      expr: settlement_date
    - name: "Outstanding Claims Count"
      expr: outstanding_claims_count
    - name: "Cause For Termination Flag"
      expr: cause_for_termination_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Termination"
      expr: COUNT(DISTINCT contract_termination_id)
    - name: "Total Settlement Amount"
      expr: SUM(settlement_amount)
    - name: "Average Settlement Amount"
      expr: AVG(settlement_amount)
    - name: "Total Outstanding Claims Amount"
      expr: SUM(outstanding_claims_amount)
    - name: "Average Outstanding Claims Amount"
      expr: AVG(outstanding_claims_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_dispute`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Dispute business metrics"
  source: "`cmoore_customer_demos`.`contract`.`dispute`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Priority Level"
      expr: priority_level
    - name: "Initiated By"
      expr: initiated_by
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Network Type"
      expr: network_type
    - name: "Contract Type"
      expr: contract_type
    - name: "Description"
      expr: description
    - name: "Disputed Amount Currency"
      expr: disputed_amount_currency
    - name: "Contract Provision Reference"
      expr: contract_provision_reference
    - name: "Filed Date"
      expr: filed_date
    - name: "Received Date"
      expr: received_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Dispute"
      expr: COUNT(DISTINCT dispute_id)
    - name: "Total Disputed Amount"
      expr: SUM(disputed_amount)
    - name: "Average Disputed Amount"
      expr: AVG(disputed_amount)
    - name: "Total Settlement Amount"
      expr: SUM(settlement_amount)
    - name: "Average Settlement Amount"
      expr: AVG(settlement_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_document`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Document business metrics"
  source: "`cmoore_customer_demos`.`contract`.`document`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "File Name"
      expr: file_name
    - name: "File Extension"
      expr: file_extension
    - name: "File Size Bytes"
      expr: file_size_bytes
    - name: "Mime Type"
      expr: mime_type
    - name: "Storage Location"
      expr: storage_location
    - name: "Storage Container"
      expr: storage_container
    - name: "Version"
      expr: version
    - name: "Version Sequence"
      expr: version_sequence
    - name: "Is Current Version"
      expr: is_current_version
    - name: "Status"
      expr: status
    - name: "Confidentiality Level"
      expr: confidentiality_level
    - name: "Contains Phi"
      expr: contains_phi
    - name: "Contains Pii"
      expr: contains_pii
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Document"
      expr: COUNT(DISTINCT document_id)
    - name: "Total Ocr Confidence Score"
      expr: SUM(ocr_confidence_score)
    - name: "Average Ocr Confidence Score"
      expr: AVG(ocr_confidence_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_document_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Document Template business metrics"
  source: "`cmoore_customer_demos`.`contract`.`document_template`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Template Type"
      expr: template_type
    - name: "Version Number"
      expr: version_number
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Document Format"
      expr: document_format
    - name: "Language"
      expr: language
    - name: "Jurisdiction"
      expr: jurisdiction
    - name: "Applicable Contract Type"
      expr: applicable_contract_type
    - name: "Reimbursement Method"
      expr: reimbursement_method
    - name: "Confidentiality Level"
      expr: confidentiality_level
    - name: "Is Default"
      expr: is_default
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Document Template"
      expr: COUNT(DISTINCT document_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_exclusion_criteria`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Exclusion Criteria business metrics"
  source: "`cmoore_customer_demos`.`contract`.`exclusion_criteria`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Exclusion Type"
      expr: exclusion_type
    - name: "Icd 10 Code"
      expr: icd_10_code
    - name: "Cpt Code"
      expr: cpt_code
    - name: "Hcpcs Code"
      expr: hcpcs_code
    - name: "Drg Code"
      expr: drg_code
    - name: "Ndc Code"
      expr: ndc_code
    - name: "Revenue Code"
      expr: revenue_code
    - name: "Place Of Service Code"
      expr: place_of_service_code
    - name: "Modifier Code"
      expr: modifier_code
    - name: "Provider Specialty Code"
      expr: provider_specialty_code
    - name: "Service Category"
      expr: service_category
    - name: "Exclusion Reason"
      expr: exclusion_reason
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Exclusion Criteria"
      expr: COUNT(DISTINCT exclusion_criteria_id)
    - name: "Total Dollar Limit Amount"
      expr: SUM(dollar_limit_amount)
    - name: "Average Dollar Limit Amount"
      expr: AVG(dollar_limit_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_incentive`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Incentive business metrics"
  source: "`cmoore_customer_demos`.`contract`.`incentive`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Measurement Period Start Date"
      expr: measurement_period_start_date
    - name: "Measurement Period End Date"
      expr: measurement_period_end_date
    - name: "Payment Frequency"
      expr: payment_frequency
    - name: "Threshold Type"
      expr: threshold_type
    - name: "Threshold Unit"
      expr: threshold_unit
    - name: "Calculation Methodology"
      expr: calculation_methodology
    - name: "Performance Metric Code"
      expr: performance_metric_code
    - name: "Performance Metric Name"
      expr: performance_metric_name
    - name: "Performance Metric Description"
      expr: performance_metric_description
    - name: "Data Source"
      expr: data_source
    - name: "Measurement Steward"
      expr: measurement_steward
    - name: "Nqf Number"
      expr: nqf_number
    - name: "Hedis Measure Code"
      expr: hedis_measure_code
    - name: "Baseline Period Start Date"
      expr: baseline_period_start_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Incentive"
      expr: COUNT(DISTINCT incentive_id)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Percentage"
      expr: SUM(percentage)
    - name: "Average Percentage"
      expr: AVG(percentage)
    - name: "Total Maximum Incentive Amount"
      expr: SUM(maximum_incentive_amount)
    - name: "Average Maximum Incentive Amount"
      expr: AVG(maximum_incentive_amount)
    - name: "Total Minimum Incentive Amount"
      expr: SUM(minimum_incentive_amount)
    - name: "Average Minimum Incentive Amount"
      expr: AVG(minimum_incentive_amount)
    - name: "Total Baseline Value"
      expr: SUM(baseline_value)
    - name: "Average Baseline Value"
      expr: AVG(baseline_value)
    - name: "Total Target Value"
      expr: SUM(target_value)
    - name: "Average Target Value"
      expr: AVG(target_value)
    - name: "Total Stretch Target Value"
      expr: SUM(stretch_target_value)
    - name: "Average Stretch Target Value"
      expr: AVG(stretch_target_value)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Shared Risk Percentage"
      expr: SUM(shared_risk_percentage)
    - name: "Average Shared Risk Percentage"
      expr: AVG(shared_risk_percentage)
    - name: "Total Quality Gate Threshold"
      expr: SUM(quality_gate_threshold)
    - name: "Average Quality Gate Threshold"
      expr: AVG(quality_gate_threshold)
    - name: "Total Composite Score Weight"
      expr: SUM(composite_score_weight)
    - name: "Average Composite Score Weight"
      expr: AVG(composite_score_weight)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_inclusion_criteria`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Inclusion Criteria business metrics"
  source: "`cmoore_customer_demos`.`contract`.`inclusion_criteria`"
  dimensions:
    - name: "Criteria Type"
      expr: criteria_type
    - name: "Criteria Code"
      expr: criteria_code
    - name: "Criteria Code System"
      expr: criteria_code_system
    - name: "Criteria Description"
      expr: criteria_description
    - name: "Inclusion Status"
      expr: inclusion_status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Eligibility Flag"
      expr: eligibility_flag
    - name: "Required Flag"
      expr: required_flag
    - name: "Minimum Quantity"
      expr: minimum_quantity
    - name: "Maximum Quantity"
      expr: maximum_quantity
    - name: "Frequency Limit"
      expr: frequency_limit
    - name: "Prior Authorization Required"
      expr: prior_authorization_required
    - name: "Prior Auth Code"
      expr: prior_auth_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Inclusion Criteria"
      expr: COUNT(DISTINCT inclusion_criteria_id)
    - name: "Total Reimbursement Rate"
      expr: SUM(reimbursement_rate)
    - name: "Average Reimbursement Rate"
      expr: AVG(reimbursement_rate)
    - name: "Total Cost Sharing Amount"
      expr: SUM(cost_sharing_amount)
    - name: "Average Cost Sharing Amount"
      expr: AVG(cost_sharing_amount)
    - name: "Total Cost Sharing Percent"
      expr: SUM(cost_sharing_percent)
    - name: "Average Cost Sharing Percent"
      expr: AVG(cost_sharing_percent)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_negotiation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Negotiation business metrics"
  source: "`cmoore_customer_demos`.`contract`.`negotiation`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Round"
      expr: round
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Initiated Date"
      expr: initiated_date
    - name: "Submitted Timestamp"
      expr: submitted_timestamp
    - name: "Response Due Date"
      expr: response_due_date
    - name: "Response Received Date"
      expr: response_received_date
    - name: "Approved Date"
      expr: approved_date
    - name: "Rejected Date"
      expr: rejected_date
    - name: "Completed Timestamp"
      expr: completed_timestamp
    - name: "Initiating Party"
      expr: initiating_party
    - name: "Responding Party"
      expr: responding_party
    - name: "Outcome"
      expr: outcome
    - name: "Contract Type"
      expr: contract_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Negotiation"
      expr: COUNT(DISTINCT negotiation_id)
    - name: "Total Proposed Rate Value"
      expr: SUM(proposed_rate_value)
    - name: "Average Proposed Rate Value"
      expr: AVG(proposed_rate_value)
    - name: "Total Current Rate Value"
      expr: SUM(current_rate_value)
    - name: "Average Current Rate Value"
      expr: AVG(current_rate_value)
    - name: "Total Rate Variance Percent"
      expr: SUM(rate_variance_percent)
    - name: "Average Rate Variance Percent"
      expr: AVG(rate_variance_percent)
    - name: "Total Risk Corridor Percent"
      expr: SUM(risk_corridor_percent)
    - name: "Average Risk Corridor Percent"
      expr: AVG(risk_corridor_percent)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
    - name: "Total Estimated Annual Claims"
      expr: SUM(estimated_annual_claims)
    - name: "Average Estimated Annual Claims"
      expr: AVG(estimated_annual_claims)
    - name: "Total Pmpm Target"
      expr: SUM(pmpm_target)
    - name: "Average Pmpm Target"
      expr: AVG(pmpm_target)
    - name: "Total Mlr Target Percent"
      expr: SUM(mlr_target_percent)
    - name: "Average Mlr Target Percent"
      expr: AVG(mlr_target_percent)
    - name: "Total Administrative Fee Percent"
      expr: SUM(administrative_fee_percent)
    - name: "Average Administrative Fee Percent"
      expr: AVG(administrative_fee_percent)
    - name: "Total Care Management Fee"
      expr: SUM(care_management_fee)
    - name: "Average Care Management Fee"
      expr: AVG(care_management_fee)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Roi Percent"
      expr: SUM(roi_percent)
    - name: "Average Roi Percent"
      expr: AVG(roi_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_network_inclusion`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Network Inclusion business metrics"
  source: "`cmoore_customer_demos`.`contract`.`network_inclusion`"
  dimensions:
    - name: "Network Tier"
      expr: network_tier
    - name: "Inclusion Type"
      expr: inclusion_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Value Based Contract Type"
      expr: value_based_contract_type
    - name: "Risk Sharing Model"
      expr: risk_sharing_model
    - name: "Reimbursement Method"
      expr: reimbursement_method
    - name: "Provider Type Allowed"
      expr: provider_type_allowed
    - name: "Specialty Codes Allowed"
      expr: specialty_codes_allowed
    - name: "Network Adequacy Metric"
      expr: network_adequacy_metric
    - name: "Provider Count"
      expr: provider_count
    - name: "Member Count Estimate"
      expr: member_count_estimate
    - name: "Contract Term Months"
      expr: contract_term_months
    - name: "Renewal Option"
      expr: renewal_option
    - name: "Termination Clause"
      expr: termination_clause
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Network Inclusion"
      expr: COUNT(DISTINCT network_inclusion_id)
    - name: "Total Capitation Rate"
      expr: SUM(capitation_rate)
    - name: "Average Capitation Rate"
      expr: AVG(capitation_rate)
    - name: "Total Max Distance Miles"
      expr: SUM(max_distance_miles)
    - name: "Average Max Distance Miles"
      expr: AVG(max_distance_miles)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_party`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Party business metrics"
  source: "`cmoore_customer_demos`.`contract`.`party`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Legal Entity Type"
      expr: legal_entity_type
    - name: "Npi"
      expr: npi
    - name: "Npi Type"
      expr: npi_type
    - name: "Tin"
      expr: tin
    - name: "Legal Business Name"
      expr: legal_business_name
    - name: "Dba Name"
      expr: dba_name
    - name: "Organization Name"
      expr: organization_name
    - name: "First Name"
      expr: first_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Last Name"
      expr: last_name
    - name: "Name Suffix"
      expr: name_suffix
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Specialty Description"
      expr: specialty_description
    - name: "Secondary Specialty Code"
      expr: secondary_specialty_code
    - name: "Provider Type"
      expr: provider_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Party"
      expr: COUNT(DISTINCT party_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
    - name: "Total Quality Tier Score"
      expr: SUM(quality_tier_score)
    - name: "Average Quality Tier Score"
      expr: AVG(quality_tier_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_payment_term`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Term business metrics"
  source: "`cmoore_customer_demos`.`contract`.`payment_term`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Payment Cycle Type"
      expr: payment_cycle_type
    - name: "Net Days"
      expr: net_days
    - name: "Discount Days"
      expr: discount_days
    - name: "Due Date Calculation Method"
      expr: due_date_calculation_method
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Late Fee Type"
      expr: late_fee_type
    - name: "Late Fee Frequency"
      expr: late_fee_frequency
    - name: "Interest Calculation Method"
      expr: interest_calculation_method
    - name: "Prepayment Allowed Flag"
      expr: prepayment_allowed_flag
    - name: "Partial Payment Allowed Flag"
      expr: partial_payment_allowed_flag
    - name: "Payment Method Restrictions"
      expr: payment_method_restrictions
    - name: "Auto Payment Eligible Flag"
      expr: auto_payment_eligible_flag
    - name: "Dispute Resolution Days"
      expr: dispute_resolution_days
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Term"
      expr: COUNT(DISTINCT payment_term_id)
    - name: "Total Discount Percentage"
      expr: SUM(discount_percentage)
    - name: "Average Discount Percentage"
      expr: AVG(discount_percentage)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Late Fee Percentage"
      expr: SUM(late_fee_percentage)
    - name: "Average Late Fee Percentage"
      expr: AVG(late_fee_percentage)
    - name: "Total Maximum Late Fee Amount"
      expr: SUM(maximum_late_fee_amount)
    - name: "Average Maximum Late Fee Amount"
      expr: AVG(maximum_late_fee_amount)
    - name: "Total Interest Rate Annual"
      expr: SUM(interest_rate_annual)
    - name: "Average Interest Rate Annual"
      expr: AVG(interest_rate_annual)
    - name: "Total Prepayment Discount Percentage"
      expr: SUM(prepayment_discount_percentage)
    - name: "Average Prepayment Discount Percentage"
      expr: AVG(prepayment_discount_percentage)
    - name: "Total Minimum Payment Amount"
      expr: SUM(minimum_payment_amount)
    - name: "Average Minimum Payment Amount"
      expr: AVG(minimum_payment_amount)
    - name: "Total Minimum Payment Percentage"
      expr: SUM(minimum_payment_percentage)
    - name: "Average Minimum Payment Percentage"
      expr: AVG(minimum_payment_percentage)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
    - name: "Total Stop Loss Threshold Amount"
      expr: SUM(stop_loss_threshold_amount)
    - name: "Average Stop Loss Threshold Amount"
      expr: AVG(stop_loss_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_performance_metric`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Performance Metric business metrics"
  source: "`cmoore_customer_demos`.`contract`.`performance_metric`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Metric Name"
      expr: metric_name
    - name: "Metric Code"
      expr: metric_code
    - name: "Metric Type"
      expr: metric_type
    - name: "Measure Set"
      expr: measure_set
    - name: "Reporting Year"
      expr: reporting_year
    - name: "Performance Tier"
      expr: performance_tier
    - name: "Achievement Status"
      expr: achievement_status
    - name: "Payment Eligibility Flag"
      expr: payment_eligibility_flag
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Member Population Count"
      expr: member_population_count
    - name: "Data Source"
      expr: data_source
    - name: "Data Collection Method"
      expr: data_collection_method
    - name: "Audit Status"
      expr: audit_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Performance Metric"
      expr: COUNT(DISTINCT performance_metric_id)
    - name: "Total Numerator"
      expr: SUM(numerator)
    - name: "Average Numerator"
      expr: AVG(numerator)
    - name: "Total Denominator"
      expr: SUM(denominator)
    - name: "Average Denominator"
      expr: AVG(denominator)
    - name: "Total Exclusions"
      expr: SUM(exclusions)
    - name: "Average Exclusions"
      expr: AVG(exclusions)
    - name: "Total Rate"
      expr: SUM(rate)
    - name: "Average Rate"
      expr: AVG(rate)
    - name: "Total Benchmark Rate"
      expr: SUM(benchmark_rate)
    - name: "Average Benchmark Rate"
      expr: AVG(benchmark_rate)
    - name: "Total Percentile Rank"
      expr: SUM(percentile_rank)
    - name: "Average Percentile Rank"
      expr: AVG(percentile_rank)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Weighted Score"
      expr: SUM(weighted_score)
    - name: "Average Weighted Score"
      expr: AVG(weighted_score)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
    - name: "Total Improvement Target"
      expr: SUM(improvement_target)
    - name: "Average Improvement Target"
      expr: AVG(improvement_target)
    - name: "Total Baseline Rate"
      expr: SUM(baseline_rate)
    - name: "Average Baseline Rate"
      expr: AVG(baseline_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_provider_participation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Provider Participation business metrics"
  source: "`cmoore_customer_demos`.`contract`.`provider_participation`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Provider Type"
      expr: provider_type
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Specialty Description"
      expr: specialty_description
    - name: "Participation Status"
      expr: participation_status
    - name: "Participation Effective Date"
      expr: participation_effective_date
    - name: "Participation Termination Date"
      expr: participation_termination_date
    - name: "Termination Reason Code"
      expr: termination_reason_code
    - name: "Termination Reason Description"
      expr: termination_reason_description
    - name: "Pcp Indicator"
      expr: pcp_indicator
    - name: "Accepting New Patients Flag"
      expr: accepting_new_patients_flag
    - name: "Panel Size Limit"
      expr: panel_size_limit
    - name: "Current Panel Size"
      expr: current_panel_size
    - name: "Reimbursement Method"
      expr: reimbursement_method
    - name: "Fee Schedule Name"
      expr: fee_schedule_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Provider Participation"
      expr: COUNT(DISTINCT provider_participation_id)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Star Rating"
      expr: SUM(star_rating)
    - name: "Average Star Rating"
      expr: AVG(star_rating)
    - name: "Total Patient Satisfaction Score"
      expr: SUM(patient_satisfaction_score)
    - name: "Average Patient Satisfaction Score"
      expr: AVG(patient_satisfaction_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_reimbursement_method`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Reimbursement Method business metrics"
  source: "`cmoore_customer_demos`.`contract`.`reimbursement_method`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Payment Basis"
      expr: payment_basis
    - name: "Risk Sharing Indicator"
      expr: risk_sharing_indicator
    - name: "Value Based Indicator"
      expr: value_based_indicator
    - name: "Apm Category"
      expr: apm_category
    - name: "Applicable Service Types"
      expr: applicable_service_types
    - name: "Applicable Provider Types"
      expr: applicable_provider_types
    - name: "Applicable Lob"
      expr: applicable_lob
    - name: "Calculation Methodology"
      expr: calculation_methodology
    - name: "Base Rate Type"
      expr: base_rate_type
    - name: "Adjustment Factors Applicable"
      expr: adjustment_factors_applicable
    - name: "Outlier Payment Indicator"
      expr: outlier_payment_indicator
    - name: "Stop Loss Indicator"
      expr: stop_loss_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Reimbursement Method"
      expr: COUNT(DISTINCT reimbursement_method_id)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_risk_sharing_agreement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Risk Sharing Agreement business metrics"
  source: "`cmoore_customer_demos`.`contract`.`risk_sharing_agreement`"
  dimensions:
    - name: "Risk Model Category"
      expr: risk_model_category
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Risk Corridor Type"
      expr: risk_corridor_type
    - name: "Performance Year"
      expr: performance_year
    - name: "Settlement Frequency"
      expr: settlement_frequency
    - name: "Settlement Lag Months"
      expr: settlement_lag_months
    - name: "Benchmark Methodology"
      expr: benchmark_methodology
    - name: "Risk Adjustment Model"
      expr: risk_adjustment_model
    - name: "Quality Performance Required"
      expr: quality_performance_required
    - name: "Quality Measure Set"
      expr: quality_measure_set
    - name: "Stop Loss Type"
      expr: stop_loss_type
    - name: "Reinsurance Arrangement"
      expr: reinsurance_arrangement
    - name: "Attributed Member Count"
      expr: attributed_member_count
    - name: "Attribution Methodology"
      expr: attribution_methodology
    - name: "Minimum Member Threshold"
      expr: minimum_member_threshold
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Risk Sharing Agreement"
      expr: COUNT(DISTINCT risk_sharing_agreement_id)
    - name: "Total Upside Sharing Percentage"
      expr: SUM(upside_sharing_percentage)
    - name: "Average Upside Sharing Percentage"
      expr: AVG(upside_sharing_percentage)
    - name: "Total Downside Sharing Percentage"
      expr: SUM(downside_sharing_percentage)
    - name: "Average Downside Sharing Percentage"
      expr: AVG(downside_sharing_percentage)
    - name: "Total Minimum Savings Rate"
      expr: SUM(minimum_savings_rate)
    - name: "Average Minimum Savings Rate"
      expr: AVG(minimum_savings_rate)
    - name: "Total Minimum Loss Rate"
      expr: SUM(minimum_loss_rate)
    - name: "Average Minimum Loss Rate"
      expr: AVG(minimum_loss_rate)
    - name: "Total Target Medical Cost Pmpm"
      expr: SUM(target_medical_cost_pmpm)
    - name: "Average Target Medical Cost Pmpm"
      expr: AVG(target_medical_cost_pmpm)
    - name: "Total Target Total Cost Of Care"
      expr: SUM(target_total_cost_of_care)
    - name: "Average Target Total Cost Of Care"
      expr: AVG(target_total_cost_of_care)
    - name: "Total Quality Withhold Percentage"
      expr: SUM(quality_withhold_percentage)
    - name: "Average Quality Withhold Percentage"
      expr: AVG(quality_withhold_percentage)
    - name: "Total Minimum Quality Score"
      expr: SUM(minimum_quality_score)
    - name: "Average Minimum Quality Score"
      expr: AVG(minimum_quality_score)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
    - name: "Total Performance Guarantee Amount"
      expr: SUM(performance_guarantee_amount)
    - name: "Average Performance Guarantee Amount"
      expr: AVG(performance_guarantee_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_specialty_coverage`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Specialty Coverage business metrics"
  source: "`cmoore_customer_demos`.`contract`.`specialty_coverage`"
  dimensions:
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Specialty Name"
      expr: specialty_name
    - name: "Specialty Category"
      expr: specialty_category
    - name: "Coverage Status"
      expr: coverage_status
    - name: "Coverage Type"
      expr: coverage_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Exclusion Reason"
      expr: exclusion_reason
    - name: "Prior Authorization Required"
      expr: prior_authorization_required
    - name: "Referral Required"
      expr: referral_required
    - name: "Reimbursement Method"
      expr: reimbursement_method
    - name: "Risk Sharing Arrangement"
      expr: risk_sharing_arrangement
    - name: "Quality Incentive Applicable"
      expr: quality_incentive_applicable
    - name: "Quality Measure Set"
      expr: quality_measure_set
    - name: "Network Tier"
      expr: network_tier
    - name: "Deductible Applicable"
      expr: deductible_applicable
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Specialty Coverage"
      expr: COUNT(DISTINCT specialty_coverage_id)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Case Rate Amount"
      expr: SUM(case_rate_amount)
    - name: "Average Case Rate Amount"
      expr: AVG(case_rate_amount)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percentage"
      expr: SUM(coinsurance_percentage)
    - name: "Average Coinsurance Percentage"
      expr: AVG(coinsurance_percentage)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_term`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Term business metrics"
  source: "`cmoore_customer_demos`.`contract`.`term`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Text"
      expr: text
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Amendment Date"
      expr: amendment_date
    - name: "Reimbursement Methodology"
      expr: reimbursement_methodology
    - name: "Payment Basis"
      expr: payment_basis
    - name: "Payment Rate Type"
      expr: payment_rate_type
    - name: "Currency Code"
      expr: currency_code
    - name: "Service Category"
      expr: service_category
    - name: "Service Type"
      expr: service_type
    - name: "Procedure Code Type"
      expr: procedure_code_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Term"
      expr: COUNT(DISTINCT term_id)
    - name: "Total Payment Rate"
      expr: SUM(payment_rate)
    - name: "Average Payment Rate"
      expr: AVG(payment_rate)
    - name: "Total Minimum Payment Amount"
      expr: SUM(minimum_payment_amount)
    - name: "Average Minimum Payment Amount"
      expr: AVG(minimum_payment_amount)
    - name: "Total Maximum Payment Amount"
      expr: SUM(maximum_payment_amount)
    - name: "Average Maximum Payment Amount"
      expr: AVG(maximum_payment_amount)
    - name: "Total Performance Target Value"
      expr: SUM(performance_target_value)
    - name: "Average Performance Target Value"
      expr: AVG(performance_target_value)
    - name: "Total Incentive Amount"
      expr: SUM(incentive_amount)
    - name: "Average Incentive Amount"
      expr: AVG(incentive_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Risk Sharing Percentage"
      expr: SUM(risk_sharing_percentage)
    - name: "Average Risk Sharing Percentage"
      expr: AVG(risk_sharing_percentage)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Stop Loss Threshold"
      expr: SUM(stop_loss_threshold)
    - name: "Average Stop Loss Threshold"
      expr: AVG(stop_loss_threshold)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
    - name: "Total Liability Limit Amount"
      expr: SUM(liability_limit_amount)
    - name: "Average Liability Limit Amount"
      expr: AVG(liability_limit_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`contract_value_based_agreement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Value Based Agreement business metrics"
  source: "`cmoore_customer_demos`.`contract`.`value_based_agreement`"
  dimensions:
    - name: "Apm Category"
      expr: apm_category
    - name: "Aco Type"
      expr: aco_type
    - name: "Risk Arrangement"
      expr: risk_arrangement
    - name: "Specialty"
      expr: specialty
    - name: "Lob"
      expr: lob
    - name: "Covered Lives Count"
      expr: covered_lives_count
    - name: "Attribution Methodology"
      expr: attribution_methodology
    - name: "Performance Period Start Date"
      expr: performance_period_start_date
    - name: "Performance Period End Date"
      expr: performance_period_end_date
    - name: "Measurement Year"
      expr: measurement_year
    - name: "Quality Measure Set"
      expr: quality_measure_set
    - name: "Quality Gate Required"
      expr: quality_gate_required
    - name: "Benchmark Methodology"
      expr: benchmark_methodology
    - name: "Risk Adjustment Model"
      expr: risk_adjustment_model
    - name: "Payment Frequency"
      expr: payment_frequency
    - name: "Settlement Lag Months"
      expr: settlement_lag_months
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Value Based Agreement"
      expr: COUNT(DISTINCT value_based_agreement_id)
    - name: "Total Quality Threshold Percentage"
      expr: SUM(quality_threshold_percentage)
    - name: "Average Quality Threshold Percentage"
      expr: AVG(quality_threshold_percentage)
    - name: "Total Cost Benchmark Amount"
      expr: SUM(cost_benchmark_amount)
    - name: "Average Cost Benchmark Amount"
      expr: AVG(cost_benchmark_amount)
    - name: "Total Shared Savings Percentage"
      expr: SUM(shared_savings_percentage)
    - name: "Average Shared Savings Percentage"
      expr: AVG(shared_savings_percentage)
    - name: "Total Shared Loss Percentage"
      expr: SUM(shared_loss_percentage)
    - name: "Average Shared Loss Percentage"
      expr: AVG(shared_loss_percentage)
    - name: "Total Minimum Savings Rate Percentage"
      expr: SUM(minimum_savings_rate_percentage)
    - name: "Average Minimum Savings Rate Percentage"
      expr: AVG(minimum_savings_rate_percentage)
    - name: "Total Minimum Loss Rate Percentage"
      expr: SUM(minimum_loss_rate_percentage)
    - name: "Average Minimum Loss Rate Percentage"
      expr: AVG(minimum_loss_rate_percentage)
    - name: "Total Savings Cap Amount"
      expr: SUM(savings_cap_amount)
    - name: "Average Savings Cap Amount"
      expr: AVG(savings_cap_amount)
    - name: "Total Loss Cap Amount"
      expr: SUM(loss_cap_amount)
    - name: "Average Loss Cap Amount"
      expr: AVG(loss_cap_amount)
    - name: "Total Stop Loss Threshold Amount"
      expr: SUM(stop_loss_threshold_amount)
    - name: "Average Stop Loss Threshold Amount"
      expr: AVG(stop_loss_threshold_amount)
    - name: "Total Corridor Lower Percentage"
      expr: SUM(corridor_lower_percentage)
    - name: "Average Corridor Lower Percentage"
      expr: AVG(corridor_lower_percentage)
    - name: "Total Corridor Upper Percentage"
      expr: SUM(corridor_upper_percentage)
    - name: "Average Corridor Upper Percentage"
      expr: AVG(corridor_upper_percentage)
    - name: "Total Withhold Percentage"
      expr: SUM(withhold_percentage)
    - name: "Average Withhold Percentage"
      expr: AVG(withhold_percentage)
$$;