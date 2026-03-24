-- Metric views for domain: shared | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:08:31

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_alert`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Alert business metrics"
  source: "`cmoore_customer_demos`.`shared`.`alert`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Source System"
      expr: source_system
    - name: "Timestamp"
      expr: timestamp
    - name: "Severity"
      expr: severity
    - name: "Status"
      expr: status
    - name: "Rule Name"
      expr: rule_name
    - name: "Metric Name"
      expr: metric_name
    - name: "Detection Method"
      expr: detection_method
    - name: "Action Required"
      expr: action_required
    - name: "Due Date"
      expr: due_date
    - name: "Resolution Timestamp"
      expr: resolution_timestamp
    - name: "Resolution Notes"
      expr: resolution_notes
    - name: "Is Escalated"
      expr: is_escalated
    - name: "Escalation Level"
      expr: escalation_level
    - name: "Notification Sent Timestamp"
      expr: notification_sent_timestamp
    - name: "Notification Method"
      expr: notification_method
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Alert"
      expr: COUNT(DISTINCT alert_id)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Actual Value"
      expr: SUM(actual_value)
    - name: "Average Actual Value"
      expr: AVG(actual_value)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Claim Amount"
      expr: SUM(claim_amount)
    - name: "Average Claim Amount"
      expr: AVG(claim_amount)
    - name: "Total Quality Target Value"
      expr: SUM(quality_target_value)
    - name: "Average Quality Target Value"
      expr: AVG(quality_target_value)
    - name: "Total Quality Actual Value"
      expr: SUM(quality_actual_value)
    - name: "Average Quality Actual Value"
      expr: AVG(quality_actual_value)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_appeal`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Appeal business metrics"
  source: "`cmoore_customer_demos`.`shared`.`appeal`"
  dimensions:
    - name: "Member Number"
      expr: member_number
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Ssn"
      expr: member_ssn
    - name: "Member Address"
      expr: member_address
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Type"
      expr: type
    - name: "Subcategory"
      expr: subcategory
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Plan Name"
      expr: plan_name
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Submitted Timestamp"
      expr: submitted_timestamp
    - name: "Received Timestamp"
      expr: received_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Appeal"
      expr: COUNT(DISTINCT appeal_id)
    - name: "Total Requested Amount"
      expr: SUM(requested_amount)
    - name: "Average Requested Amount"
      expr: AVG(requested_amount)
    - name: "Total Original Claim Amount"
      expr: SUM(original_claim_amount)
    - name: "Average Original Claim Amount"
      expr: AVG(original_claim_amount)
    - name: "Total Adjusted Amount"
      expr: SUM(adjusted_amount)
    - name: "Average Adjusted Amount"
      expr: AVG(adjusted_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_audit`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit business metrics"
  source: "`cmoore_customer_demos`.`shared`.`audit`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Name"
      expr: name
    - name: "Scope"
      expr: scope
    - name: "Objective"
      expr: objective
    - name: "Status"
      expr: status
    - name: "Auditor Name"
      expr: auditor_name
    - name: "Auditor Organization"
      expr: auditor_organization
    - name: "Auditor Type"
      expr: auditor_type
    - name: "Regulatory Body"
      expr: regulatory_body
    - name: "Program"
      expr: program
    - name: "Year"
      expr: year
    - name: "Period Start Date"
      expr: period_start_date
    - name: "Period End Date"
      expr: period_end_date
    - name: "Scheduled Start Date"
      expr: scheduled_start_date
    - name: "Actual Start Date"
      expr: actual_start_date
    - name: "Scheduled End Date"
      expr: scheduled_end_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit"
      expr: COUNT(DISTINCT audit_id)
    - name: "Total Confidence Level"
      expr: SUM(confidence_level)
    - name: "Average Confidence Level"
      expr: AVG(confidence_level)
    - name: "Total Error Rate"
      expr: SUM(error_rate)
    - name: "Average Error Rate"
      expr: AVG(error_rate)
    - name: "Total Projected Error Rate"
      expr: SUM(projected_error_rate)
    - name: "Average Projected Error Rate"
      expr: AVG(projected_error_rate)
    - name: "Total Compliance Score"
      expr: SUM(compliance_score)
    - name: "Average Compliance Score"
      expr: AVG(compliance_score)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Underpayment Amount"
      expr: SUM(underpayment_amount)
    - name: "Average Underpayment Amount"
      expr: AVG(underpayment_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_audit_log`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit Log business metrics"
  source: "`cmoore_customer_demos`.`shared`.`audit_log`"
  dimensions:
    - name: "Entity Type"
      expr: entity_type
    - name: "Operation Type"
      expr: operation_type
    - name: "Operation Timestamp"
      expr: operation_timestamp
    - name: "Performed By User Name"
      expr: performed_by_user_name
    - name: "Performed By Role"
      expr: performed_by_role
    - name: "Source System"
      expr: source_system
    - name: "Source Module"
      expr: source_module
    - name: "Ip Address"
      expr: ip_address
    - name: "Change Description"
      expr: change_description
    - name: "Changed Field Names"
      expr: changed_field_names
    - name: "Old Values"
      expr: old_values
    - name: "New Values"
      expr: new_values
    - name: "Audit Status"
      expr: audit_status
    - name: "Audit Result"
      expr: audit_result
    - name: "Reason Code"
      expr: reason_code
    - name: "Comments"
      expr: comments
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit Log"
      expr: COUNT(DISTINCT audit_log_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_business_associate`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Business Associate business metrics"
  source: "`cmoore_customer_demos`.`shared`.`business_associate`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Relationship Start Date"
      expr: relationship_start_date
    - name: "Relationship End Date"
      expr: relationship_end_date
    - name: "Termination Reason"
      expr: termination_reason
    - name: "Primary Contact Name"
      expr: primary_contact_name
    - name: "Primary Contact Email"
      expr: primary_contact_email
    - name: "Primary Contact Phone"
      expr: primary_contact_phone
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State Province"
      expr: state_province
    - name: "Postal Code"
      expr: postal_code
    - name: "Country Code"
      expr: country_code
    - name: "Tax Id Number"
      expr: tax_id_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Business Associate"
      expr: COUNT(DISTINCT business_associate_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_case`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Case business metrics"
  source: "`cmoore_customer_demos`.`shared`.`case`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Priority"
      expr: priority
    - name: "Severity"
      expr: severity
    - name: "Group Number"
      expr: group_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Plan Code"
      expr: plan_code
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Claim Number"
      expr: claim_number
    - name: "Authorization Number"
      expr: authorization_number
    - name: "Referral Source"
      expr: referral_source
    - name: "Referral Date"
      expr: referral_date
    - name: "Opened Date"
      expr: opened_date
    - name: "Opened Timestamp"
      expr: opened_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Case"
      expr: COUNT(DISTINCT case_id)
    - name: "Total Estimated Savings Amount"
      expr: SUM(estimated_savings_amount)
    - name: "Average Estimated Savings Amount"
      expr: AVG(estimated_savings_amount)
    - name: "Total Recovered Amount"
      expr: SUM(recovered_amount)
    - name: "Average Recovered Amount"
      expr: AVG(recovered_amount)
    - name: "Total Total Case Cost"
      expr: SUM(total_case_cost)
    - name: "Average Total Case Cost"
      expr: AVG(total_case_cost)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
    - name: "Total Raf Score"
      expr: SUM(raf_score)
    - name: "Average Raf Score"
      expr: AVG(raf_score)
    - name: "Total Medication Adherence Rate"
      expr: SUM(medication_adherence_rate)
    - name: "Average Medication Adherence Rate"
      expr: AVG(medication_adherence_rate)
    - name: "Total Member Satisfaction Score"
      expr: SUM(member_satisfaction_score)
    - name: "Average Member Satisfaction Score"
      expr: AVG(member_satisfaction_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_clearinghouse`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Clearinghouse business metrics"
  source: "`cmoore_customer_demos`.`shared`.`clearinghouse`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Clearinghouse Code"
      expr: clearinghouse_code
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Contact Name"
      expr: contact_name
    - name: "Contact Email"
      expr: contact_email
    - name: "Contact Phone"
      expr: contact_phone
    - name: "Address Line1"
      expr: address_line1
    - name: "City"
      expr: city
    - name: "State"
      expr: state
    - name: "Postal Code"
      expr: postal_code
    - name: "Country"
      expr: country
    - name: "Supported Transaction Codes"
      expr: supported_transaction_codes
    - name: "Integration Method"
      expr: integration_method
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Clearinghouse"
      expr: COUNT(DISTINCT clearinghouse_id)
    - name: "Total Fee Schedule"
      expr: SUM(fee_schedule)
    - name: "Average Fee Schedule"
      expr: AVG(fee_schedule)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_collection_agency`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Collection Agency business metrics"
  source: "`cmoore_customer_demos`.`shared`.`collection_agency`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Legal Entity Name"
      expr: legal_entity_name
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State"
      expr: state
    - name: "Postal Code"
      expr: postal_code
    - name: "Country Code"
      expr: country_code
    - name: "Phone Number"
      expr: phone_number
    - name: "Email Address"
      expr: email_address
    - name: "Primary Contact Name"
      expr: primary_contact_name
    - name: "Contract Start Date"
      expr: contract_start_date
    - name: "Contract End Date"
      expr: contract_end_date
    - name: "Status"
      expr: status
    - name: "Agency Type"
      expr: agency_type
    - name: "Payment Method Supported"
      expr: payment_method_supported
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Collection Agency"
      expr: COUNT(DISTINCT collection_agency_id)
    - name: "Total Fee Percentage"
      expr: SUM(fee_percentage)
    - name: "Average Fee Percentage"
      expr: AVG(fee_percentage)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
    - name: "Total Max Collection Amount"
      expr: SUM(max_collection_amount)
    - name: "Average Max Collection Amount"
      expr: AVG(max_collection_amount)
    - name: "Total Min Collection Amount"
      expr: SUM(min_collection_amount)
    - name: "Average Min Collection Amount"
      expr: AVG(min_collection_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_communication_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Communication Template business metrics"
  source: "`cmoore_customer_demos`.`shared`.`communication_template`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Channel"
      expr: channel
    - name: "Language Code"
      expr: language_code
    - name: "Template Type"
      expr: template_type
    - name: "Subject"
      expr: subject
    - name: "Body"
      expr: body
    - name: "Placeholders"
      expr: placeholders
    - name: "Version Number"
      expr: version_number
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Requires Approval"
      expr: requires_approval
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Audience"
      expr: audience
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Communication Template"
      expr: COUNT(DISTINCT communication_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_complaint`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Complaint business metrics"
  source: "`cmoore_customer_demos`.`shared`.`complaint`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Subcategory"
      expr: subcategory
    - name: "Priority"
      expr: priority
    - name: "Severity"
      expr: severity
    - name: "Status"
      expr: status
    - name: "Source"
      expr: source
    - name: "Filing Date"
      expr: filing_date
    - name: "Received Date"
      expr: received_date
    - name: "Acknowledged Date"
      expr: acknowledged_date
    - name: "Due Date"
      expr: due_date
    - name: "Resolved Date"
      expr: resolved_date
    - name: "Closed Date"
      expr: closed_date
    - name: "Incident Date"
      expr: incident_date
    - name: "Subject"
      expr: subject
    - name: "Description"
      expr: description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Complaint"
      expr: COUNT(DISTINCT complaint_id)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Reimbursement Amount"
      expr: SUM(reimbursement_amount)
    - name: "Average Reimbursement Amount"
      expr: AVG(reimbursement_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_contract`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract business metrics"
  source: "`cmoore_customer_demos`.`shared`.`contract`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Name"
      expr: name
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Termination Reason"
      expr: termination_reason
    - name: "Renewal Date"
      expr: renewal_date
    - name: "Auto Renewal Indicator"
      expr: auto_renewal_indicator
    - name: "Notice Period Days"
      expr: notice_period_days
    - name: "Contracting Party Name"
      expr: contracting_party_name
    - name: "Contracting Party Type"
      expr: contracting_party_type
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Owner"
      expr: owner
    - name: "Line Of Business"
      expr: line_of_business
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract"
      expr: COUNT(DISTINCT contract_id)
    - name: "Total Discount Percentage"
      expr: SUM(discount_percentage)
    - name: "Average Discount Percentage"
      expr: AVG(discount_percentage)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Commission Rate Percentage"
      expr: SUM(commission_rate_percentage)
    - name: "Average Commission Rate Percentage"
      expr: AVG(commission_rate_percentage)
    - name: "Total Value Amount"
      expr: SUM(value_amount)
    - name: "Average Value Amount"
      expr: AVG(value_amount)
    - name: "Total Liability Limit Amount"
      expr: SUM(liability_limit_amount)
    - name: "Average Liability Limit Amount"
      expr: AVG(liability_limit_amount)
    - name: "Total Minimum Insurance Amount"
      expr: SUM(minimum_insurance_amount)
    - name: "Average Minimum Insurance Amount"
      expr: AVG(minimum_insurance_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_contract_audit`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Audit business metrics"
  source: "`cmoore_customer_demos`.`shared`.`contract_audit`"
  dimensions:
    - name: "Audit Scope"
      expr: audit_scope
    - name: "Contract Clause Reviewed"
      expr: contract_clause_reviewed
    - name: "Compliance Status"
      expr: compliance_status
    - name: "Audit Period Start"
      expr: audit_period_start
    - name: "Audit Period End"
      expr: audit_period_end
    - name: "Claims Reviewed Count"
      expr: claims_reviewed_count
    - name: "Findings Summary"
      expr: findings_summary
    - name: "Review Completed Date"
      expr: review_completed_date
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Audit Period Start Month"
      expr: DATE_TRUNC('MONTH', audit_period_start)
    - name: "Audit Period End Month"
      expr: DATE_TRUNC('MONTH', audit_period_end)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Audit"
      expr: COUNT(DISTINCT contract_audit_id)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_contract_journal_allocation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Journal Allocation business metrics"
  source: "`cmoore_customer_demos`.`shared`.`contract_journal_allocation`"
  dimensions:
    - name: "Contract Line Reference"
      expr: contract_line_reference
    - name: "Entry Type"
      expr: entry_type
    - name: "Period"
      expr: period
    - name: "Allocation Date"
      expr: allocation_date
    - name: "Allocation Status"
      expr: allocation_status
    - name: "Allocated By"
      expr: allocated_by
    - name: "Allocation Method"
      expr: allocation_method
    - name: "Notes"
      expr: notes
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Allocation Date Month"
      expr: DATE_TRUNC('MONTH', allocation_date)
    - name: "Created Timestamp Month"
      expr: DATE_TRUNC('MONTH', created_timestamp)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Journal Allocation"
      expr: COUNT(DISTINCT contract_journal_allocation_id)
    - name: "Total Allocation Percentage"
      expr: SUM(allocation_percentage)
    - name: "Average Allocation Percentage"
      expr: AVG(allocation_percentage)
    - name: "Total Allocated Amount"
      expr: SUM(allocated_amount)
    - name: "Average Allocated Amount"
      expr: AVG(allocated_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_contract_quality_metric`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Quality Metric business metrics"
  source: "`cmoore_customer_demos`.`shared`.`contract_quality_metric`"
  dimensions:
    - name: "Measurement Period"
      expr: measurement_period
    - name: "Payment Tier"
      expr: payment_tier
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Status"
      expr: status
    - name: "Reporting Frequency"
      expr: reporting_frequency
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "End Date Month"
      expr: DATE_TRUNC('MONTH', end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Quality Metric"
      expr: COUNT(DISTINCT contract_quality_metric_id)
    - name: "Total Performance Threshold"
      expr: SUM(performance_threshold)
    - name: "Average Performance Threshold"
      expr: AVG(performance_threshold)
    - name: "Total Incentive Amount"
      expr: SUM(incentive_amount)
    - name: "Average Incentive Amount"
      expr: AVG(incentive_amount)
    - name: "Total Metric Weight"
      expr: SUM(metric_weight)
    - name: "Average Metric Weight"
      expr: AVG(metric_weight)
    - name: "Total Baseline Value"
      expr: SUM(baseline_value)
    - name: "Average Baseline Value"
      expr: AVG(baseline_value)
    - name: "Total Target Value"
      expr: SUM(target_value)
    - name: "Average Target Value"
      expr: AVG(target_value)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_eligibility_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Eligibility Rule business metrics"
  source: "`cmoore_customer_demos`.`shared`.`eligibility_rule`"
  dimensions:
    - name: "Rule Name"
      expr: rule_name
    - name: "Rule Description"
      expr: rule_description
    - name: "Rule Type"
      expr: rule_type
    - name: "Rule Category"
      expr: rule_category
    - name: "Rule Version"
      expr: rule_version
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Priority"
      expr: priority
    - name: "Eligibility Engine"
      expr: eligibility_engine
    - name: "Evaluation Order"
      expr: evaluation_order
    - name: "Age Min"
      expr: age_min
    - name: "Age Max"
      expr: age_max
    - name: "Residency State"
      expr: residency_state
    - name: "Residency Country"
      expr: residency_country
    - name: "Plan Type"
      expr: plan_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Eligibility Rule"
      expr: COUNT(DISTINCT eligibility_rule_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_exchange`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Exchange business metrics"
  source: "`cmoore_customer_demos`.`shared`.`exchange`"
  dimensions:
    - name: "Exchange Code"
      expr: exchange_code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Description"
      expr: description
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Currency Code"
      expr: currency_code
    - name: "Settlement Date"
      expr: settlement_date
    - name: "Market Segment"
      expr: market_segment
    - name: "Regulatory Status"
      expr: regulatory_status
    - name: "Compliance Effective Date"
      expr: compliance_effective_date
    - name: "Compliance Expiration Date"
      expr: compliance_expiration_date
    - name: "Contact Email"
      expr: contact_email
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Exchange"
      expr: COUNT(DISTINCT exchange_id)
    - name: "Total Settlement Amount"
      expr: SUM(settlement_amount)
    - name: "Average Settlement Amount"
      expr: AVG(settlement_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_fee_schedule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Fee Schedule business metrics"
  source: "`cmoore_customer_demos`.`shared`.`fee_schedule`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Code"
      expr: code
    - name: "Type"
      expr: type
    - name: "Version"
      expr: version
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Description"
      expr: description
    - name: "Pricing Methodology"
      expr: pricing_methodology
    - name: "Geographic Scope"
      expr: geographic_scope
    - name: "Lob"
      expr: lob
    - name: "Network Tier"
      expr: network_tier
    - name: "Specialty"
      expr: specialty
    - name: "Base Fee Schedule Code"
      expr: base_fee_schedule_code
    - name: "Currency Code"
      expr: currency_code
    - name: "Rvu Based Flag"
      expr: rvu_based_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Fee Schedule"
      expr: COUNT(DISTINCT fee_schedule_id)
    - name: "Total Adjustment Factor"
      expr: SUM(adjustment_factor)
    - name: "Average Adjustment Factor"
      expr: AVG(adjustment_factor)
    - name: "Total Conversion Factor"
      expr: SUM(conversion_factor)
    - name: "Average Conversion Factor"
      expr: AVG(conversion_factor)
    - name: "Total Outlier Threshold Amount"
      expr: SUM(outlier_threshold_amount)
    - name: "Average Outlier Threshold Amount"
      expr: AVG(outlier_threshold_amount)
    - name: "Total Stop Loss Amount"
      expr: SUM(stop_loss_amount)
    - name: "Average Stop Loss Amount"
      expr: AVG(stop_loss_amount)
    - name: "Total Minimum Payment Amount"
      expr: SUM(minimum_payment_amount)
    - name: "Average Minimum Payment Amount"
      expr: AVG(minimum_payment_amount)
    - name: "Total Maximum Payment Amount"
      expr: SUM(maximum_payment_amount)
    - name: "Average Maximum Payment Amount"
      expr: AVG(maximum_payment_amount)
    - name: "Total Percentage Of Medicare"
      expr: SUM(percentage_of_medicare)
    - name: "Average Percentage Of Medicare"
      expr: AVG(percentage_of_medicare)
    - name: "Total Percentage Of Charges"
      expr: SUM(percentage_of_charges)
    - name: "Average Percentage Of Charges"
      expr: AVG(percentage_of_charges)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_formulary`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Formulary business metrics"
  source: "`cmoore_customer_demos`.`shared`.`formulary`"
  dimensions:
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Generic Name"
      expr: generic_name
    - name: "Brand Name"
      expr: brand_name
    - name: "Therapeutic Class"
      expr: therapeutic_class
    - name: "Drug Class Code"
      expr: drug_class_code
    - name: "Tier Level"
      expr: tier_level
    - name: "Tier Description"
      expr: tier_description
    - name: "Coverage Status"
      expr: coverage_status
    - name: "Prior Authorization Required"
      expr: prior_authorization_required
    - name: "Step Therapy Required"
      expr: step_therapy_required
    - name: "Quantity Limit Period"
      expr: quantity_limit_period
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Strength"
      expr: strength
    - name: "Route Of Administration"
      expr: route_of_administration
    - name: "Daw Code"
      expr: daw_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Formulary"
      expr: COUNT(DISTINCT formulary_id)
    - name: "Total Quantity Limit"
      expr: SUM(quantity_limit)
    - name: "Average Quantity Limit"
      expr: AVG(quantity_limit)
    - name: "Total Awp"
      expr: SUM(awp)
    - name: "Average Awp"
      expr: AVG(awp)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percentage"
      expr: SUM(coinsurance_percentage)
    - name: "Average Coinsurance Percentage"
      expr: AVG(coinsurance_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_formulary_tier`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Formulary Tier business metrics"
  source: "`cmoore_customer_demos`.`shared`.`formulary_tier`"
  dimensions:
    - name: "Tier Code"
      expr: tier_code
    - name: "Tier Name"
      expr: tier_name
    - name: "Tier Level"
      expr: tier_level
    - name: "Tier Category"
      expr: tier_category
    - name: "Tier Description"
      expr: tier_description
    - name: "Cost Share Type"
      expr: cost_share_type
    - name: "Deductible Applies Flag"
      expr: deductible_applies_flag
    - name: "Prior Authorization Required Flag"
      expr: prior_authorization_required_flag
    - name: "Step Therapy Required Flag"
      expr: step_therapy_required_flag
    - name: "Quantity Limit Applies Flag"
      expr: quantity_limit_applies_flag
    - name: "Specialty Tier Flag"
      expr: specialty_tier_flag
    - name: "Generic Tier Flag"
      expr: generic_tier_flag
    - name: "Brand Tier Flag"
      expr: brand_tier_flag
    - name: "Preventive Tier Flag"
      expr: preventive_tier_flag
    - name: "Lob"
      expr: lob
    - name: "Plan Type"
      expr: plan_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Formulary Tier"
      expr: COUNT(DISTINCT formulary_tier_id)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percentage"
      expr: SUM(coinsurance_percentage)
    - name: "Average Coinsurance Percentage"
      expr: AVG(coinsurance_percentage)
    - name: "Total Initial Coverage Copay"
      expr: SUM(initial_coverage_copay)
    - name: "Average Initial Coverage Copay"
      expr: AVG(initial_coverage_copay)
    - name: "Total Initial Coverage Coinsurance"
      expr: SUM(initial_coverage_coinsurance)
    - name: "Average Initial Coverage Coinsurance"
      expr: AVG(initial_coverage_coinsurance)
    - name: "Total Gap Coverage Copay"
      expr: SUM(gap_coverage_copay)
    - name: "Average Gap Coverage Copay"
      expr: AVG(gap_coverage_copay)
    - name: "Total Gap Coverage Coinsurance"
      expr: SUM(gap_coverage_coinsurance)
    - name: "Average Gap Coverage Coinsurance"
      expr: AVG(gap_coverage_coinsurance)
    - name: "Total Catastrophic Copay"
      expr: SUM(catastrophic_copay)
    - name: "Average Catastrophic Copay"
      expr: AVG(catastrophic_copay)
    - name: "Total Catastrophic Coinsurance"
      expr: SUM(catastrophic_coinsurance)
    - name: "Average Catastrophic Coinsurance"
      expr: AVG(catastrophic_coinsurance)
    - name: "Total Mail Order Copay"
      expr: SUM(mail_order_copay)
    - name: "Average Mail Order Copay"
      expr: AVG(mail_order_copay)
    - name: "Total Mail Order Coinsurance"
      expr: SUM(mail_order_coinsurance)
    - name: "Average Mail Order Coinsurance"
      expr: AVG(mail_order_coinsurance)
    - name: "Total Retail 30 Day Copay"
      expr: SUM(retail_30_day_copay)
    - name: "Average Retail 30 Day Copay"
      expr: AVG(retail_30_day_copay)
    - name: "Total Retail 90 Day Copay"
      expr: SUM(retail_90_day_copay)
    - name: "Average Retail 90 Day Copay"
      expr: AVG(retail_90_day_copay)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_lead`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Lead business metrics"
  source: "`cmoore_customer_demos`.`shared`.`lead`"
  dimensions:
    - name: "Source System"
      expr: source_system
    - name: "Type"
      expr: type
    - name: "Lob"
      expr: lob
    - name: "First Name"
      expr: first_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Last Name"
      expr: last_name
    - name: "Suffix"
      expr: suffix
    - name: "Salutation"
      expr: salutation
    - name: "Organization Name"
      expr: organization_name
    - name: "Title"
      expr: title
    - name: "Email Address"
      expr: email_address
    - name: "Secondary Email Address"
      expr: secondary_email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Phone Type"
      expr: phone_type
    - name: "Secondary Phone Number"
      expr: secondary_phone_number
    - name: "Secondary Phone Type"
      expr: secondary_phone_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Lead"
      expr: COUNT(DISTINCT lead_id)
    - name: "Total Annual Household Income"
      expr: SUM(annual_household_income)
    - name: "Average Annual Household Income"
      expr: AVG(annual_household_income)
    - name: "Total Estimated Subsidy Amount"
      expr: SUM(estimated_subsidy_amount)
    - name: "Average Estimated Subsidy Amount"
      expr: AVG(estimated_subsidy_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_letter_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Letter Template business metrics"
  source: "`cmoore_customer_demos`.`shared`.`letter_template`"
  dimensions:
    - name: "Template Name"
      expr: template_name
    - name: "Template Type"
      expr: template_type
    - name: "Version Number"
      expr: version_number
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Language Code"
      expr: language_code
    - name: "Channel"
      expr: channel
    - name: "Subject"
      expr: subject
    - name: "Body"
      expr: body
    - name: "Placeholders"
      expr: placeholders
    - name: "Audience Segment"
      expr: audience_segment
    - name: "Priority"
      expr: priority
    - name: "Is Default"
      expr: is_default
    - name: "Document Format"
      expr: document_format
    - name: "Signature Line"
      expr: signature_line
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Letter Template"
      expr: COUNT(DISTINCT letter_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_notification_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Notification Template business metrics"
  source: "`cmoore_customer_demos`.`shared`.`notification_template`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Channel"
      expr: channel
    - name: "Template Type"
      expr: template_type
    - name: "Language"
      expr: language
    - name: "Subject"
      expr: subject
    - name: "Body"
      expr: body
    - name: "Is Active"
      expr: is_active
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiry Date"
      expr: expiry_date
    - name: "Version Number"
      expr: version_number
    - name: "Priority"
      expr: priority
    - name: "Compliance Requirements"
      expr: compliance_requirements
    - name: "Audience"
      expr: audience
    - name: "Send Limit Per Day"
      expr: send_limit_per_day
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Notification Template"
      expr: COUNT(DISTINCT notification_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_payee`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payee business metrics"
  source: "`cmoore_customer_demos`.`shared`.`payee`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Payee Type"
      expr: payee_type
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State"
      expr: state
    - name: "Postal Code"
      expr: postal_code
    - name: "Country Code"
      expr: country_code
    - name: "Email"
      expr: email
    - name: "Phone Number"
      expr: phone_number
    - name: "Bank Account Number"
      expr: bank_account_number
    - name: "Bank Routing Number"
      expr: bank_routing_number
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Currency"
      expr: payment_currency
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payee"
      expr: COUNT(DISTINCT payee_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_payer`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payer business metrics"
  source: "`cmoore_customer_demos`.`shared`.`payer`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Short Name"
      expr: short_name
    - name: "Payer Type"
      expr: payer_type
    - name: "Status"
      expr: status
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State"
      expr: state
    - name: "Postal Code"
      expr: postal_code
    - name: "Country Code"
      expr: country_code
    - name: "Phone Number"
      expr: phone_number
    - name: "Email Address"
      expr: email_address
    - name: "Website Url"
      expr: website_url
    - name: "Contract Start Date"
      expr: contract_start_date
    - name: "Contract End Date"
      expr: contract_end_date
    - name: "Termination Date"
      expr: termination_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payer"
      expr: COUNT(DISTINCT payer_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_premium_schedule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Premium Schedule business metrics"
  source: "`cmoore_customer_demos`.`shared`.`premium_schedule`"
  dimensions:
    - name: "Schedule Type"
      expr: schedule_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Currency Code"
      expr: currency_code
    - name: "Payment Frequency"
      expr: payment_frequency
    - name: "Payment Method"
      expr: payment_method
    - name: "Billing Type"
      expr: billing_type
    - name: "First Payment Due Date"
      expr: first_payment_due_date
    - name: "Last Payment Due Date"
      expr: last_payment_due_date
    - name: "Next Payment Due Date"
      expr: next_payment_due_date
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Installment Count"
      expr: installment_count
    - name: "Installment Number"
      expr: installment_number
    - name: "Lob"
      expr: lob
    - name: "Product Type"
      expr: product_type
    - name: "Coverage Tier"
      expr: coverage_tier
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Premium Schedule"
      expr: COUNT(DISTINCT premium_schedule_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Base Premium Amount"
      expr: SUM(base_premium_amount)
    - name: "Average Base Premium Amount"
      expr: AVG(base_premium_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Member Responsibility Amount"
      expr: SUM(member_responsibility_amount)
    - name: "Average Member Responsibility Amount"
      expr: AVG(member_responsibility_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Surcharge Amount"
      expr: SUM(surcharge_amount)
    - name: "Average Surcharge Amount"
      expr: AVG(surcharge_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
    - name: "Total Aptc Amount"
      expr: SUM(aptc_amount)
    - name: "Average Aptc Amount"
      expr: AVG(aptc_amount)
    - name: "Total Csr Amount"
      expr: SUM(csr_amount)
    - name: "Average Csr Amount"
      expr: AVG(csr_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_pricing_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Pricing Rule business metrics"
  source: "`cmoore_customer_demos`.`shared`.`pricing_rule`"
  dimensions:
    - name: "Rule Code"
      expr: rule_code
    - name: "Rule Name"
      expr: rule_name
    - name: "Rule Description"
      expr: rule_description
    - name: "Rule Type"
      expr: rule_type
    - name: "Rule Category"
      expr: rule_category
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Market Segment"
      expr: market_segment
    - name: "Rating Area"
      expr: rating_area
    - name: "State Code"
      expr: state_code
    - name: "Coverage Tier"
      expr: coverage_tier
    - name: "Age Band Min"
      expr: age_band_min
    - name: "Age Band Max"
      expr: age_band_max
    - name: "Tobacco Use Indicator"
      expr: tobacco_use_indicator
    - name: "Network Tier"
      expr: network_tier
    - name: "Service Category"
      expr: service_category
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Pricing Rule"
      expr: COUNT(DISTINCT pricing_rule_id)
    - name: "Total Tobacco Surcharge Rate"
      expr: SUM(tobacco_surcharge_rate)
    - name: "Average Tobacco Surcharge Rate"
      expr: AVG(tobacco_surcharge_rate)
    - name: "Total Base Rate Amount"
      expr: SUM(base_rate_amount)
    - name: "Average Base Rate Amount"
      expr: AVG(base_rate_amount)
    - name: "Total Rate Per Member Per Month"
      expr: SUM(rate_per_member_per_month)
    - name: "Average Rate Per Member Per Month"
      expr: AVG(rate_per_member_per_month)
    - name: "Total Rate Per Employee Per Month"
      expr: SUM(rate_per_employee_per_month)
    - name: "Average Rate Per Employee Per Month"
      expr: AVG(rate_per_employee_per_month)
    - name: "Total Adjustment Factor"
      expr: SUM(adjustment_factor)
    - name: "Average Adjustment Factor"
      expr: AVG(adjustment_factor)
    - name: "Total Discount Percentage"
      expr: SUM(discount_percentage)
    - name: "Average Discount Percentage"
      expr: AVG(discount_percentage)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Subsidy Percentage"
      expr: SUM(subsidy_percentage)
    - name: "Average Subsidy Percentage"
      expr: AVG(subsidy_percentage)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Employer Contribution Percentage"
      expr: SUM(employer_contribution_percentage)
    - name: "Average Employer Contribution Percentage"
      expr: AVG(employer_contribution_percentage)
    - name: "Total Member Premium Amount"
      expr: SUM(member_premium_amount)
    - name: "Average Member Premium Amount"
      expr: AVG(member_premium_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_program`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Program business metrics"
  source: "`cmoore_customer_demos`.`shared`.`program`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Lob"
      expr: lob
    - name: "Status"
      expr: status
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Enrollment Start Date"
      expr: enrollment_start_date
    - name: "Enrollment End Date"
      expr: enrollment_end_date
    - name: "Target Population"
      expr: target_population
    - name: "Eligibility Criteria"
      expr: eligibility_criteria
    - name: "Enrollment Method"
      expr: enrollment_method
    - name: "Is Mandatory"
      expr: is_mandatory
    - name: "Budget Period"
      expr: budget_period
    - name: "Cost Center Code"
      expr: cost_center_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Program"
      expr: COUNT(DISTINCT program_id)
    - name: "Total Budget Amount"
      expr: SUM(budget_amount)
    - name: "Average Budget Amount"
      expr: AVG(budget_amount)
    - name: "Total Roi Target Percentage"
      expr: SUM(roi_target_percentage)
    - name: "Average Roi Target Percentage"
      expr: AVG(roi_target_percentage)
    - name: "Total Pmpm Cost Target"
      expr: SUM(pmpm_cost_target)
    - name: "Average Pmpm Cost Target"
      expr: AVG(pmpm_cost_target)
    - name: "Total Member Incentive Amount"
      expr: SUM(member_incentive_amount)
    - name: "Average Member Incentive Amount"
      expr: AVG(member_incentive_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_program_compliance_policy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Program Compliance Policy business metrics"
  source: "`cmoore_customer_demos`.`shared`.`program_compliance_policy`"
  dimensions:
    - name: "Effective Date"
      expr: effective_date
    - name: "Compliance Scope"
      expr: compliance_scope
    - name: "Attestation Required"
      expr: attestation_required
    - name: "Review Frequency"
      expr: review_frequency
    - name: "Status"
      expr: status
    - name: "Implementation Notes"
      expr: implementation_notes
    - name: "Created Date"
      expr: created_date
    - name: "Last Modified Date"
      expr: last_modified_date
    - name: "Last Modified By"
      expr: last_modified_by
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "Created Date Month"
      expr: DATE_TRUNC('MONTH', created_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Program Compliance Policy"
      expr: COUNT(DISTINCT program_compliance_policy_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_program_credentialing_policy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Program Credentialing Policy business metrics"
  source: "`cmoore_customer_demos`.`shared`.`program_credentialing_policy`"
  dimensions:
    - name: "Policy Effective Date"
      expr: policy_effective_date
    - name: "Policy End Date"
      expr: policy_end_date
    - name: "Program Specific Requirements"
      expr: program_specific_requirements
    - name: "Override Flag"
      expr: override_flag
    - name: "Approval Date"
      expr: approval_date
    - name: "Approved By"
      expr: approved_by
    - name: "Status"
      expr: status
    - name: "Compliance Notes"
      expr: compliance_notes
    - name: "Policy Effective Date Month"
      expr: DATE_TRUNC('MONTH', policy_effective_date)
    - name: "Policy End Date Month"
      expr: DATE_TRUNC('MONTH', policy_end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Program Credentialing Policy"
      expr: COUNT(DISTINCT program_credentialing_policy_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_program_diagnosis_mapping`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Program Diagnosis Mapping business metrics"
  source: "`cmoore_customer_demos`.`shared`.`program_diagnosis_mapping`"
  dimensions:
    - name: "Reporting Requirement"
      expr: reporting_requirement
    - name: "Quality Measure Indicator"
      expr: quality_measure_indicator
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Is Active"
      expr: is_active
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "End Date Month"
      expr: DATE_TRUNC('MONTH', end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Program Diagnosis Mapping"
      expr: COUNT(DISTINCT program_diagnosis_mapping_id)
    - name: "Total Program Weight"
      expr: SUM(program_weight)
    - name: "Average Program Weight"
      expr: AVG(program_weight)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_rate_schedule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Rate Schedule business metrics"
  source: "`cmoore_customer_demos`.`shared`.`rate_schedule`"
  dimensions:
    - name: "Schedule Name"
      expr: schedule_name
    - name: "Schedule Type"
      expr: schedule_type
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Plan Type"
      expr: plan_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Currency Code"
      expr: currency_code
    - name: "Rate Unit"
      expr: rate_unit
    - name: "Service Category"
      expr: service_category
    - name: "Procedure Code Type"
      expr: procedure_code_type
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Place Of Service"
      expr: place_of_service
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Rate Schedule"
      expr: COUNT(DISTINCT rate_schedule_id)
    - name: "Total Rate Amount"
      expr: SUM(rate_amount)
    - name: "Average Rate Amount"
      expr: AVG(rate_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percent"
      expr: SUM(coinsurance_percent)
    - name: "Average Coinsurance Percent"
      expr: AVG(coinsurance_percent)
    - name: "Total Out Of Pocket Max"
      expr: SUM(out_of_pocket_max)
    - name: "Average Out Of Pocket Max"
      expr: AVG(out_of_pocket_max)
    - name: "Total Discount Percent"
      expr: SUM(discount_percent)
    - name: "Average Discount Percent"
      expr: AVG(discount_percent)
    - name: "Total Surcharge Percent"
      expr: SUM(surcharge_percent)
    - name: "Average Surcharge Percent"
      expr: AVG(surcharge_percent)
    - name: "Total Usage Limit Quantity"
      expr: SUM(usage_limit_quantity)
    - name: "Average Usage Limit Quantity"
      expr: AVG(usage_limit_quantity)
    - name: "Total Tax Rate Percent"
      expr: SUM(tax_rate_percent)
    - name: "Average Tax Rate Percent"
      expr: AVG(tax_rate_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_regulatory_filing`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Regulatory Filing business metrics"
  source: "`cmoore_customer_demos`.`shared`.`regulatory_filing`"
  dimensions:
    - name: "Filing Number"
      expr: filing_number
    - name: "Filing Type"
      expr: filing_type
    - name: "Filing Subtype"
      expr: filing_subtype
    - name: "Regulatory Agency"
      expr: regulatory_agency
    - name: "Agency Code"
      expr: agency_code
    - name: "Jurisdiction"
      expr: jurisdiction
    - name: "Jurisdiction Code"
      expr: jurisdiction_code
    - name: "Filing Status"
      expr: filing_status
    - name: "Submission Date"
      expr: submission_date
    - name: "Submission Timestamp"
      expr: submission_timestamp
    - name: "Submission Method"
      expr: submission_method
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Approval Date"
      expr: approval_date
    - name: "Rejection Date"
      expr: rejection_date
    - name: "Withdrawal Date"
      expr: withdrawal_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Regulatory Filing"
      expr: COUNT(DISTINCT regulatory_filing_id)
    - name: "Total Rate Change Percentage"
      expr: SUM(rate_change_percentage)
    - name: "Average Rate Change Percentage"
      expr: AVG(rate_change_percentage)
    - name: "Total Mlr Percentage"
      expr: SUM(mlr_percentage)
    - name: "Average Mlr Percentage"
      expr: AVG(mlr_percentage)
    - name: "Total Rebate Amount"
      expr: SUM(rebate_amount)
    - name: "Average Rebate Amount"
      expr: AVG(rebate_amount)
    - name: "Total Premium Revenue"
      expr: SUM(premium_revenue)
    - name: "Average Premium Revenue"
      expr: AVG(premium_revenue)
    - name: "Total Claims Incurred"
      expr: SUM(claims_incurred)
    - name: "Average Claims Incurred"
      expr: AVG(claims_incurred)
    - name: "Total Administrative Expenses"
      expr: SUM(administrative_expenses)
    - name: "Average Administrative Expenses"
      expr: AVG(administrative_expenses)
    - name: "Total Pmpm Amount"
      expr: SUM(pmpm_amount)
    - name: "Average Pmpm Amount"
      expr: AVG(pmpm_amount)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Quality Rating Score"
      expr: SUM(quality_rating_score)
    - name: "Average Quality Rating Score"
      expr: AVG(quality_rating_score)
    - name: "Total Filing Fee Amount"
      expr: SUM(filing_fee_amount)
    - name: "Average Filing Fee Amount"
      expr: AVG(filing_fee_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_reporting_entity`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Reporting Entity business metrics"
  source: "`cmoore_customer_demos`.`shared`.`reporting_entity`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Entity Type"
      expr: entity_type
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Owner Department"
      expr: owner_department
    - name: "Contact Email"
      expr: contact_email
    - name: "Contact Phone"
      expr: contact_phone
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State Province"
      expr: state_province
    - name: "Country Code"
      expr: country_code
    - name: "Tax Identifier"
      expr: tax_identifier
    - name: "Reporting Frequency"
      expr: reporting_frequency
    - name: "Data Format"
      expr: data_format
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Reporting Entity"
      expr: COUNT(DISTINCT reporting_entity_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_risk_score`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Risk Score business metrics"
  source: "`cmoore_customer_demos`.`shared`.`risk_score`"
  dimensions:
    - name: "Calculation Date"
      expr: calculation_date
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Payment Year"
      expr: payment_year
    - name: "Data Year"
      expr: data_year
    - name: "Model Type"
      expr: model_type
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Age Group"
      expr: age_group
    - name: "Gender"
      expr: gender
    - name: "Medicaid Status"
      expr: medicaid_status
    - name: "Disability Status"
      expr: disability_status
    - name: "Esrd Status"
      expr: esrd_status
    - name: "Institutional Status"
      expr: institutional_status
    - name: "New Enrollee Status"
      expr: new_enrollee_status
    - name: "Months Enrolled"
      expr: months_enrolled
    - name: "Hcc Count"
      expr: hcc_count
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Risk Score"
      expr: COUNT(DISTINCT risk_score_id)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
    - name: "Total Raf Score"
      expr: SUM(raf_score)
    - name: "Average Raf Score"
      expr: AVG(raf_score)
    - name: "Total Demographic Score"
      expr: SUM(demographic_score)
    - name: "Average Demographic Score"
      expr: AVG(demographic_score)
    - name: "Total Disease Score"
      expr: SUM(disease_score)
    - name: "Average Disease Score"
      expr: AVG(disease_score)
    - name: "Total Interaction Score"
      expr: SUM(interaction_score)
    - name: "Average Interaction Score"
      expr: AVG(interaction_score)
    - name: "Total Normalization Factor"
      expr: SUM(normalization_factor)
    - name: "Average Normalization Factor"
      expr: AVG(normalization_factor)
    - name: "Total Coding Intensity Adjustment"
      expr: SUM(coding_intensity_adjustment)
    - name: "Average Coding Intensity Adjustment"
      expr: AVG(coding_intensity_adjustment)
    - name: "Total Payment Amount"
      expr: SUM(payment_amount)
    - name: "Average Payment Amount"
      expr: AVG(payment_amount)
    - name: "Total Base Rate"
      expr: SUM(base_rate)
    - name: "Average Base Rate"
      expr: AVG(base_rate)
    - name: "Total Benchmark Rate"
      expr: SUM(benchmark_rate)
    - name: "Average Benchmark Rate"
      expr: AVG(benchmark_rate)
    - name: "Total Rebate Percentage"
      expr: SUM(rebate_percentage)
    - name: "Average Rebate Percentage"
      expr: AVG(rebate_percentage)
    - name: "Total Quality Bonus Percentage"
      expr: SUM(quality_bonus_percentage)
    - name: "Average Quality Bonus Percentage"
      expr: AVG(quality_bonus_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_shared_payment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Shared Payment business metrics"
  source: "`cmoore_customer_demos`.`shared`.`shared_payment`"
  dimensions:
    - name: "Date"
      expr: date
    - name: "Currency"
      expr: currency
    - name: "Method"
      expr: method
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Status Reason"
      expr: status_reason
    - name: "Posting Date"
      expr: posting_date
    - name: "Service Date"
      expr: service_date
    - name: "Transaction Reference Number"
      expr: transaction_reference_number
    - name: "Check Number"
      expr: check_number
    - name: "Electronic Reference"
      expr: electronic_reference
    - name: "Bank Account Number"
      expr: bank_account_number
    - name: "Bank Routing Number"
      expr: bank_routing_number
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Revenue Code"
      expr: revenue_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Shared Payment"
      expr: COUNT(DISTINCT shared_payment_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Charge Amount"
      expr: SUM(charge_amount)
    - name: "Average Charge Amount"
      expr: AVG(charge_amount)
    - name: "Total Allowed Amount"
      expr: SUM(allowed_amount)
    - name: "Average Allowed Amount"
      expr: AVG(allowed_amount)
    - name: "Total Patient Responsibility Amount"
      expr: SUM(patient_responsibility_amount)
    - name: "Average Patient Responsibility Amount"
      expr: AVG(patient_responsibility_amount)
    - name: "Total Co Payment Amount"
      expr: SUM(co_payment_amount)
    - name: "Average Co Payment Amount"
      expr: AVG(co_payment_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Coinsurance Amount"
      expr: SUM(coinsurance_amount)
    - name: "Average Coinsurance Amount"
      expr: AVG(coinsurance_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Write Off Amount"
      expr: SUM(write_off_amount)
    - name: "Average Write Off Amount"
      expr: AVG(write_off_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Currency Exchange Rate"
      expr: SUM(currency_exchange_rate)
    - name: "Average Currency Exchange Rate"
      expr: AVG(currency_exchange_rate)
    - name: "Total Original Currency Amount"
      expr: SUM(original_currency_amount)
    - name: "Average Original Currency Amount"
      expr: AVG(original_currency_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_shared_program_enrollment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Shared Program Enrollment business metrics"
  source: "`cmoore_customer_demos`.`shared`.`shared_program_enrollment`"
  dimensions:
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Program Status"
      expr: program_status
    - name: "Completion Date"
      expr: completion_date
    - name: "Participation Level"
      expr: participation_level
    - name: "Referral Source"
      expr: referral_source
    - name: "Opt Out Date"
      expr: opt_out_date
    - name: "Opt Out Reason"
      expr: opt_out_reason
    - name: "Enrollment Date Month"
      expr: DATE_TRUNC('MONTH', enrollment_date)
    - name: "Completion Date Month"
      expr: DATE_TRUNC('MONTH', completion_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Shared Program Enrollment"
      expr: COUNT(DISTINCT shared_program_enrollment_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_sla`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sla business metrics"
  source: "`cmoore_customer_demos`.`shared`.`sla`"
  dimensions:
    - name: "Service Name"
      expr: service_name
    - name: "Channel"
      expr: channel
    - name: "Category"
      expr: category
    - name: "Target Response Time Minutes"
      expr: target_response_time_minutes
    - name: "Target Resolution Time Minutes"
      expr: target_resolution_time_minutes
    - name: "Measurement Criteria"
      expr: measurement_criteria
    - name: "Penalty Type"
      expr: penalty_type
    - name: "Penalty Currency"
      expr: penalty_currency
    - name: "Escalation Contact Name"
      expr: escalation_contact_name
    - name: "Escalation Contact Phone"
      expr: escalation_contact_phone
    - name: "Escalation Contact Email"
      expr: escalation_contact_email
    - name: "Monitoring Tool"
      expr: monitoring_tool
    - name: "Monitoring Frequency Minutes"
      expr: monitoring_frequency_minutes
    - name: "Reporting Frequency"
      expr: reporting_frequency
    - name: "Status"
      expr: status
    - name: "Effective Start Date"
      expr: effective_start_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sla"
      expr: COUNT(DISTINCT sla_id)
    - name: "Total Target Uptime Percent"
      expr: SUM(target_uptime_percent)
    - name: "Average Target Uptime Percent"
      expr: AVG(target_uptime_percent)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Availability Actual Percent"
      expr: SUM(availability_actual_percent)
    - name: "Average Availability Actual Percent"
      expr: AVG(availability_actual_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_status_history`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Status History business metrics"
  source: "`cmoore_customer_demos`.`shared`.`status_history`"
  dimensions:
    - name: "Entity Type"
      expr: entity_type
    - name: "Previous Status"
      expr: previous_status
    - name: "New Status"
      expr: new_status
    - name: "Status Effective Date"
      expr: status_effective_date
    - name: "Status Effective Timestamp"
      expr: status_effective_timestamp
    - name: "Status End Date"
      expr: status_end_date
    - name: "Status End Timestamp"
      expr: status_end_timestamp
    - name: "Change Reason Code"
      expr: change_reason_code
    - name: "Change Reason Description"
      expr: change_reason_description
    - name: "Change Category"
      expr: change_category
    - name: "Initiated By User Name"
      expr: initiated_by_user_name
    - name: "Initiated By Role"
      expr: initiated_by_role
    - name: "Approved By User Name"
      expr: approved_by_user_name
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Source System"
      expr: source_system
    - name: "Is Current Status"
      expr: is_current_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Status History"
      expr: COUNT(DISTINCT status_history_id)
    - name: "Total Sla Actual Hours"
      expr: SUM(sla_actual_hours)
    - name: "Average Sla Actual Hours"
      expr: AVG(sla_actual_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_survey`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Survey business metrics"
  source: "`cmoore_customer_demos`.`shared`.`survey`"
  dimensions:
    - name: "Title"
      expr: title
    - name: "Type"
      expr: type
    - name: "Lob"
      expr: lob
    - name: "Description"
      expr: description
    - name: "Version"
      expr: version
    - name: "Status"
      expr: status
    - name: "Language"
      expr: language
    - name: "Delivery Method"
      expr: delivery_method
    - name: "Vendor Name"
      expr: vendor_name
    - name: "Question Count"
      expr: question_count
    - name: "Estimated Completion Minutes"
      expr: estimated_completion_minutes
    - name: "Target Population"
      expr: target_population
    - name: "Sampling Method"
      expr: sampling_method
    - name: "Sample Size Target"
      expr: sample_size_target
    - name: "Frequency"
      expr: frequency
    - name: "Trigger Event"
      expr: trigger_event
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Survey"
      expr: COUNT(DISTINCT survey_id)
    - name: "Total Response Rate Target Pct"
      expr: SUM(response_rate_target_pct)
    - name: "Average Response Rate Target Pct"
      expr: AVG(response_rate_target_pct)
    - name: "Total Incentive Amount"
      expr: SUM(incentive_amount)
    - name: "Average Incentive Amount"
      expr: AVG(incentive_amount)
    - name: "Total Cost Per Survey"
      expr: SUM(cost_per_survey)
    - name: "Average Cost Per Survey"
      expr: AVG(cost_per_survey)
    - name: "Total Budget Amount"
      expr: SUM(budget_amount)
    - name: "Average Budget Amount"
      expr: AVG(budget_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_survey_question`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Survey Question business metrics"
  source: "`cmoore_customer_demos`.`shared`.`survey_question`"
  dimensions:
    - name: "Question Text"
      expr: question_text
    - name: "Question Type"
      expr: question_type
    - name: "Response Format"
      expr: response_format
    - name: "Is Required"
      expr: is_required
    - name: "Display Order"
      expr: display_order
    - name: "Category"
      expr: category
    - name: "Status"
      expr: status
    - name: "Created Date"
      expr: created_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Language"
      expr: language
    - name: "Version Number"
      expr: version_number
    - name: "Source System"
      expr: source_system
    - name: "Confidentiality Level"
      expr: confidentiality_level
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Survey Question"
      expr: COUNT(DISTINCT survey_question_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_survey_response`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Survey Response business metrics"
  source: "`cmoore_customer_demos`.`shared`.`survey_response`"
  dimensions:
    - name: "Survey Name"
      expr: survey_name
    - name: "Question Text"
      expr: question_text
    - name: "Question Category"
      expr: question_category
    - name: "Response Value"
      expr: response_value
    - name: "Response Type"
      expr: response_type
    - name: "Response Timestamp"
      expr: response_timestamp
    - name: "Response Date"
      expr: response_date
    - name: "Survey Administration Date"
      expr: survey_administration_date
    - name: "Survey Completion Date"
      expr: survey_completion_date
    - name: "Response Channel"
      expr: response_channel
    - name: "Response Status"
      expr: response_status
    - name: "Is Required Question"
      expr: is_required_question
    - name: "Is Validated"
      expr: is_validated
    - name: "Validation Status"
      expr: validation_status
    - name: "Validation Error Code"
      expr: validation_error_code
    - name: "Validation Error Description"
      expr: validation_error_description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Survey Response"
      expr: COUNT(DISTINCT survey_response_id)
    - name: "Total Response Score"
      expr: SUM(response_score)
    - name: "Average Response Score"
      expr: AVG(response_score)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
    - name: "Total Prior Year Total Paid Amount"
      expr: SUM(prior_year_total_paid_amount)
    - name: "Average Prior Year Total Paid Amount"
      expr: AVG(prior_year_total_paid_amount)
    - name: "Total Incentive Amount"
      expr: SUM(incentive_amount)
    - name: "Average Incentive Amount"
      expr: AVG(incentive_amount)
    - name: "Total Weight Factor"
      expr: SUM(weight_factor)
    - name: "Average Weight Factor"
      expr: AVG(weight_factor)
    - name: "Total Sentiment Score"
      expr: SUM(sentiment_score)
    - name: "Average Sentiment Score"
      expr: AVG(sentiment_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_tax_detail`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Tax Detail business metrics"
  source: "`cmoore_customer_demos`.`shared`.`tax_detail`"
  dimensions:
    - name: "Tax Code"
      expr: tax_code
    - name: "Tax Name"
      expr: tax_name
    - name: "Tax Type"
      expr: tax_type
    - name: "Tax Category"
      expr: tax_category
    - name: "Jurisdiction Code"
      expr: jurisdiction_code
    - name: "Jurisdiction Name"
      expr: jurisdiction_name
    - name: "Jurisdiction Type"
      expr: jurisdiction_type
    - name: "Tax Rate Type"
      expr: tax_rate_type
    - name: "Taxable Base"
      expr: taxable_base
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Product Type Applicability"
      expr: product_type_applicability
    - name: "Line Of Business Applicability"
      expr: line_of_business_applicability
    - name: "Member Location Type"
      expr: member_location_type
    - name: "Employer Location Type"
      expr: employer_location_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Tax Detail"
      expr: COUNT(DISTINCT tax_detail_id)
    - name: "Total Tax Rate"
      expr: SUM(tax_rate)
    - name: "Average Tax Rate"
      expr: AVG(tax_rate)
    - name: "Total Minimum Tax Amount"
      expr: SUM(minimum_tax_amount)
    - name: "Average Minimum Tax Amount"
      expr: AVG(minimum_tax_amount)
    - name: "Total Maximum Tax Amount"
      expr: SUM(maximum_tax_amount)
    - name: "Average Maximum Tax Amount"
      expr: AVG(maximum_tax_amount)
    - name: "Total Surcharge Rate"
      expr: SUM(surcharge_rate)
    - name: "Average Surcharge Rate"
      expr: AVG(surcharge_rate)
    - name: "Total Penalty Rate"
      expr: SUM(penalty_rate)
    - name: "Average Penalty Rate"
      expr: AVG(penalty_rate)
    - name: "Total Interest Rate"
      expr: SUM(interest_rate)
    - name: "Average Interest Rate"
      expr: AVG(interest_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_third_party_administrator`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Third Party Administrator business metrics"
  source: "`cmoore_customer_demos`.`shared`.`third_party_administrator`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Legal Entity Name"
      expr: legal_entity_name
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State Province"
      expr: state_province
    - name: "Postal Code"
      expr: postal_code
    - name: "Country Code"
      expr: country_code
    - name: "Phone Number"
      expr: phone_number
    - name: "Email Address"
      expr: email_address
    - name: "Website Url"
      expr: website_url
    - name: "Contact Name"
      expr: contact_name
    - name: "Contact Role"
      expr: contact_role
    - name: "Contract Start Date"
      expr: contract_start_date
    - name: "Contract End Date"
      expr: contract_end_date
    - name: "Status"
      expr: status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Third Party Administrator"
      expr: COUNT(DISTINCT third_party_administrator_id)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_user`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "User business metrics"
  source: "`cmoore_customer_demos`.`shared`.`user`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Last Name"
      expr: last_name
    - name: "Date Of Birth"
      expr: date_of_birth
    - name: "Gender"
      expr: gender
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State Province"
      expr: state_province
    - name: "Postal Code"
      expr: postal_code
    - name: "Country Code"
      expr: country_code
    - name: "Policy Number"
      expr: policy_number
    - name: "Group Number"
      expr: group_number
    - name: "Plan Name"
      expr: plan_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct User"
      expr: COUNT(DISTINCT user_id)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Out Of Pocket Max"
      expr: SUM(out_of_pocket_max)
    - name: "Average Out Of Pocket Max"
      expr: AVG(out_of_pocket_max)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_workflow`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Workflow business metrics"
  source: "`cmoore_customer_demos`.`shared`.`workflow`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Workflow Type"
      expr: workflow_type
    - name: "Status"
      expr: status
    - name: "Owner Name"
      expr: owner_name
    - name: "Department"
      expr: department
    - name: "Priority"
      expr: priority
    - name: "Trigger Event"
      expr: trigger_event
    - name: "Start Date"
      expr: start_date
    - name: "Scheduled Start Timestamp"
      expr: scheduled_start_timestamp
    - name: "End Date"
      expr: end_date
    - name: "Completion Timestamp"
      expr: completion_timestamp
    - name: "Is Automated"
      expr: is_automated
    - name: "Version Number"
      expr: version_number
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Workflow"
      expr: COUNT(DISTINCT workflow_id)
    - name: "Total Sla Target Hours"
      expr: SUM(sla_target_hours)
    - name: "Average Sla Target Hours"
      expr: AVG(sla_target_hours)
    - name: "Total Sla Actual Hours"
      expr: SUM(sla_actual_hours)
    - name: "Average Sla Actual Hours"
      expr: AVG(sla_actual_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`shared_workgroup`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Workgroup business metrics"
  source: "`cmoore_customer_demos`.`shared`.`workgroup`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Cost Center Code"
      expr: cost_center_code
    - name: "Business Unit"
      expr: business_unit
    - name: "Region"
      expr: region
    - name: "Is Default"
      expr: is_default
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Workflow Category"
      expr: workflow_category
    - name: "Confidentiality Level"
      expr: confidentiality_level
    - name: "Effective Start Date Month"
      expr: DATE_TRUNC('MONTH', effective_start_date)
    - name: "Effective End Date Month"
      expr: DATE_TRUNC('MONTH', effective_end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Workgroup"
      expr: COUNT(DISTINCT workgroup_id)
$$;