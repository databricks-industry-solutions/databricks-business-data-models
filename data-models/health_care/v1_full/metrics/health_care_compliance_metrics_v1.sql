-- Metric views for domain: compliance | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:07:47

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_asset_compliance_review`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Asset Compliance Review business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`asset_compliance_review`"
  dimensions:
    - name: "Compliance Review Date"
      expr: compliance_review_date
    - name: "Approval Status"
      expr: approval_status
    - name: "Exception Granted"
      expr: exception_granted
    - name: "Review Notes"
      expr: review_notes
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Review Created Timestamp"
      expr: review_created_timestamp
    - name: "Review Last Modified Timestamp"
      expr: review_last_modified_timestamp
    - name: "Compliance Review Date Month"
      expr: DATE_TRUNC('MONTH', compliance_review_date)
    - name: "Next Review Date Month"
      expr: DATE_TRUNC('MONTH', next_review_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Asset Compliance Review"
      expr: COUNT(DISTINCT asset_compliance_review_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_audit_finding`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit Finding business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`audit_finding`"
  dimensions:
    - name: "Finding Number"
      expr: finding_number
    - name: "Finding Title"
      expr: finding_title
    - name: "Finding Description"
      expr: finding_description
    - name: "Finding Type"
      expr: finding_type
    - name: "Severity Level"
      expr: severity_level
    - name: "Risk Rating"
      expr: risk_rating
    - name: "Likelihood"
      expr: likelihood
    - name: "Impact"
      expr: impact
    - name: "Root Cause"
      expr: root_cause
    - name: "Root Cause Category"
      expr: root_cause_category
    - name: "Affected Business Unit"
      expr: affected_business_unit
    - name: "Affected Process"
      expr: affected_process
    - name: "Affected System"
      expr: affected_system
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Recommendation"
      expr: recommendation
    - name: "Management Response"
      expr: management_response
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit Finding"
      expr: COUNT(DISTINCT audit_finding_id)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Remediation Cost Estimate"
      expr: SUM(remediation_cost_estimate)
    - name: "Average Remediation Cost Estimate"
      expr: AVG(remediation_cost_estimate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_benefit_compliance_requirement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Benefit Compliance Requirement business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`benefit_compliance_requirement`"
  dimensions:
    - name: "Effective Date"
      expr: effective_date
    - name: "Compliance Requirement Type"
      expr: compliance_requirement_type
    - name: "Attestation Status"
      expr: attestation_status
    - name: "Review Date"
      expr: review_date
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Compliance Status"
      expr: compliance_status
    - name: "Auditor Name"
      expr: auditor_name
    - name: "Notes"
      expr: notes
    - name: "Created Date"
      expr: created_date
    - name: "Last Updated Date"
      expr: last_updated_date
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "Review Date Month"
      expr: DATE_TRUNC('MONTH', review_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Benefit Compliance Requirement"
      expr: COUNT(DISTINCT benefit_compliance_requirement_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_breach_incident`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Breach Incident business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`breach_incident`"
  dimensions:
    - name: "Incident Number"
      expr: incident_number
    - name: "Breach Type"
      expr: breach_type
    - name: "Breach Category"
      expr: breach_category
    - name: "Breach Location Type"
      expr: breach_location_type
    - name: "Discovery Date"
      expr: discovery_date
    - name: "Discovery Timestamp"
      expr: discovery_timestamp
    - name: "Occurrence Date"
      expr: occurrence_date
    - name: "Occurrence Timestamp"
      expr: occurrence_timestamp
    - name: "Notification Date"
      expr: notification_date
    - name: "Hhs Notification Date"
      expr: hhs_notification_date
    - name: "Media Notification Date"
      expr: media_notification_date
    - name: "Containment Date"
      expr: containment_date
    - name: "Resolution Date"
      expr: resolution_date
    - name: "Affected Records Count"
      expr: affected_records_count
    - name: "Affected Members Count"
      expr: affected_members_count
    - name: "Affected States"
      expr: affected_states
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Breach Incident"
      expr: COUNT(DISTINCT breach_incident_id)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Estimated Financial Impact"
      expr: SUM(estimated_financial_impact)
    - name: "Average Estimated Financial Impact"
      expr: AVG(estimated_financial_impact)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_breach_notification`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Breach Notification business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`breach_notification`"
  dimensions:
    - name: "Notification Type"
      expr: notification_type
    - name: "Recipient Type"
      expr: recipient_type
    - name: "Recipient Name"
      expr: recipient_name
    - name: "Recipient Email"
      expr: recipient_email
    - name: "Recipient Mailing Address"
      expr: recipient_mailing_address
    - name: "Recipient Phone"
      expr: recipient_phone
    - name: "Delivery Method"
      expr: delivery_method
    - name: "Delivery Channel"
      expr: delivery_channel
    - name: "Notification Date"
      expr: notification_date
    - name: "Notification Timestamp"
      expr: notification_timestamp
    - name: "Required Notification Date"
      expr: required_notification_date
    - name: "Notification Status"
      expr: notification_status
    - name: "Delivery Confirmation Date"
      expr: delivery_confirmation_date
    - name: "Delivery Confirmation Number"
      expr: delivery_confirmation_number
    - name: "Notification Content"
      expr: notification_content
    - name: "Breach Description"
      expr: breach_description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Breach Notification"
      expr: COUNT(DISTINCT breach_notification_id)
    - name: "Total Notification Cost Amount"
      expr: SUM(notification_cost_amount)
    - name: "Average Notification Cost Amount"
      expr: AVG(notification_cost_amount)
    - name: "Total Postage Cost Amount"
      expr: SUM(postage_cost_amount)
    - name: "Average Postage Cost Amount"
      expr: AVG(postage_cost_amount)
    - name: "Total Printing Cost Amount"
      expr: SUM(printing_cost_amount)
    - name: "Average Printing Cost Amount"
      expr: AVG(printing_cost_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_calendar`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Calendar business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`calendar`"
  dimensions:
    - name: "Event Name"
      expr: event_name
    - name: "Event Description"
      expr: event_description
    - name: "Event Type"
      expr: event_type
    - name: "Event Category"
      expr: event_category
    - name: "Regulatory Body"
      expr: regulatory_body
    - name: "Applicable Line Of Business"
      expr: applicable_line_of_business
    - name: "Applicable State"
      expr: applicable_state
    - name: "Recurrence Pattern"
      expr: recurrence_pattern
    - name: "Scheduled Start Date"
      expr: scheduled_start_date
    - name: "Scheduled End Date"
      expr: scheduled_end_date
    - name: "Filing Deadline Date"
      expr: filing_deadline_date
    - name: "Advance Notice Days"
      expr: advance_notice_days
    - name: "Responsible Department"
      expr: responsible_department
    - name: "Responsible Owner Name"
      expr: responsible_owner_name
    - name: "Responsible Owner Email"
      expr: responsible_owner_email
    - name: "Backup Owner Name"
      expr: backup_owner_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Calendar"
      expr: COUNT(DISTINCT calendar_id)
    - name: "Total Estimated Penalty Amount"
      expr: SUM(estimated_penalty_amount)
    - name: "Average Estimated Penalty Amount"
      expr: AVG(estimated_penalty_amount)
    - name: "Total Training Completion Threshold Pct"
      expr: SUM(training_completion_threshold_pct)
    - name: "Average Training Completion Threshold Pct"
      expr: AVG(training_completion_threshold_pct)
    - name: "Total Estimated Effort Hours"
      expr: SUM(estimated_effort_hours)
    - name: "Average Estimated Effort Hours"
      expr: AVG(estimated_effort_hours)
    - name: "Total Estimated Cost Amount"
      expr: SUM(estimated_cost_amount)
    - name: "Average Estimated Cost Amount"
      expr: AVG(estimated_cost_amount)
    - name: "Total Actual Cost Amount"
      expr: SUM(actual_cost_amount)
    - name: "Average Actual Cost Amount"
      expr: AVG(actual_cost_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_compliance_exception`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Compliance Exception business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`compliance_exception`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Policy Name"
      expr: policy_name
    - name: "Policy Version"
      expr: policy_version
    - name: "Request Date"
      expr: request_date
    - name: "Requester Name"
      expr: requester_name
    - name: "Requester Email"
      expr: requester_email
    - name: "Requester Department"
      expr: requester_department
    - name: "Requester Title"
      expr: requester_title
    - name: "Business Justification"
      expr: business_justification
    - name: "Affected Systems"
      expr: affected_systems
    - name: "Affected Business Processes"
      expr: affected_business_processes
    - name: "Risk Level"
      expr: risk_level
    - name: "Risk Assessment"
      expr: risk_assessment
    - name: "Mitigation Controls"
      expr: mitigation_controls
    - name: "Status"
      expr: status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Compliance Exception"
      expr: COUNT(DISTINCT compliance_exception_id)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_compliance_reviewer`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Compliance Reviewer business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`compliance_reviewer`"
  dimensions:
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Reviewer Type"
      expr: reviewer_type
    - name: "Compliance Area"
      expr: compliance_area
    - name: "Certifications"
      expr: certifications
    - name: "Training Completion Date"
      expr: training_completion_date
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Status"
      expr: status
    - name: "Audit Experience Years"
      expr: audit_experience_years
    - name: "Jurisdiction"
      expr: jurisdiction
    - name: "Notes"
      expr: notes
    - name: "Last Review Date"
      expr: last_review_date
    - name: "Training Completion Date Month"
      expr: DATE_TRUNC('MONTH', training_completion_date)
    - name: "Effective Start Date Month"
      expr: DATE_TRUNC('MONTH', effective_start_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Compliance Reviewer"
      expr: COUNT(DISTINCT compliance_reviewer_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_consent_form`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Consent Form business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`consent_form`"
  dimensions:
    - name: "Form Type"
      expr: form_type
    - name: "Form Version"
      expr: form_version
    - name: "Form Title"
      expr: form_title
    - name: "Form Description"
      expr: form_description
    - name: "Consent Status"
      expr: consent_status
    - name: "Consent Decision"
      expr: consent_decision
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Signed Date"
      expr: signed_date
    - name: "Signed Timestamp"
      expr: signed_timestamp
    - name: "Revocation Date"
      expr: revocation_date
    - name: "Revocation Reason"
      expr: revocation_reason
    - name: "Signature Method"
      expr: signature_method
    - name: "Signature Location"
      expr: signature_location
    - name: "Witness Required Flag"
      expr: witness_required_flag
    - name: "Witness Name"
      expr: witness_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Consent Form"
      expr: COUNT(DISTINCT consent_form_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_control`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Control business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`control`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Frequency"
      expr: frequency
    - name: "Regulation Code"
      expr: regulation_code
    - name: "Regulation Name"
      expr: regulation_name
    - name: "Regulation Section"
      expr: regulation_section
    - name: "Governing Body"
      expr: governing_body
    - name: "Domain"
      expr: domain
    - name: "Risk Rating"
      expr: risk_rating
    - name: "Objective"
      expr: objective
    - name: "Owner"
      expr: owner
    - name: "Owner Department"
      expr: owner_department
    - name: "Implementation Status"
      expr: implementation_status
    - name: "Effectiveness Rating"
      expr: effectiveness_rating
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Control"
      expr: COUNT(DISTINCT control_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_control_test`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Control Test business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`control_test`"
  dimensions:
    - name: "Test Name"
      expr: test_name
    - name: "Test Type"
      expr: test_type
    - name: "Test Date"
      expr: test_date
    - name: "Test Period Start Date"
      expr: test_period_start_date
    - name: "Test Period End Date"
      expr: test_period_end_date
    - name: "Fiscal Year"
      expr: fiscal_year
    - name: "Fiscal Quarter"
      expr: fiscal_quarter
    - name: "Test Outcome"
      expr: test_outcome
    - name: "Deficiency Severity"
      expr: deficiency_severity
    - name: "Sample Size"
      expr: sample_size
    - name: "Exceptions Identified"
      expr: exceptions_identified
    - name: "Test Status"
      expr: test_status
    - name: "Tester Name"
      expr: tester_name
    - name: "Tester Role"
      expr: tester_role
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Review Date"
      expr: review_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Control Test"
      expr: COUNT(DISTINCT control_test_id)
    - name: "Total Exception Rate"
      expr: SUM(exception_rate)
    - name: "Average Exception Rate"
      expr: AVG(exception_rate)
    - name: "Total Confidence Level"
      expr: SUM(confidence_level)
    - name: "Average Confidence Level"
      expr: AVG(confidence_level)
    - name: "Total Tolerable Error Rate"
      expr: SUM(tolerable_error_rate)
    - name: "Average Tolerable Error Rate"
      expr: AVG(tolerable_error_rate)
    - name: "Total Expected Error Rate"
      expr: SUM(expected_error_rate)
    - name: "Average Expected Error Rate"
      expr: AVG(expected_error_rate)
    - name: "Total Test Hours"
      expr: SUM(test_hours)
    - name: "Average Test Hours"
      expr: AVG(test_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_corrective_action`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Corrective Action business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`corrective_action`"
  dimensions:
    - name: "Cap Number"
      expr: cap_number
    - name: "Title"
      expr: title
    - name: "Description"
      expr: description
    - name: "Finding Description"
      expr: finding_description
    - name: "Root Cause Analysis"
      expr: root_cause_analysis
    - name: "Status"
      expr: status
    - name: "Priority"
      expr: priority
    - name: "Severity"
      expr: severity
    - name: "Risk Level"
      expr: risk_level
    - name: "Compliance Domain"
      expr: compliance_domain
    - name: "Audit Type"
      expr: audit_type
    - name: "Owner Name"
      expr: owner_name
    - name: "Owner Email"
      expr: owner_email
    - name: "Owner Department"
      expr: owner_department
    - name: "Owner Title"
      expr: owner_title
    - name: "Assigned To Name"
      expr: assigned_to_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Corrective Action"
      expr: COUNT(DISTINCT corrective_action_id)
    - name: "Total Estimated Cost"
      expr: SUM(estimated_cost)
    - name: "Average Estimated Cost"
      expr: AVG(estimated_cost)
    - name: "Total Actual Cost"
      expr: SUM(actual_cost)
    - name: "Average Actual Cost"
      expr: AVG(actual_cost)
    - name: "Total Estimated Effort Hours"
      expr: SUM(estimated_effort_hours)
    - name: "Average Estimated Effort Hours"
      expr: AVG(estimated_effort_hours)
    - name: "Total Actual Effort Hours"
      expr: SUM(actual_effort_hours)
    - name: "Average Actual Effort Hours"
      expr: AVG(actual_effort_hours)
    - name: "Total Completion Percentage"
      expr: SUM(completion_percentage)
    - name: "Average Completion Percentage"
      expr: AVG(completion_percentage)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Potential Penalty Amount"
      expr: SUM(potential_penalty_amount)
    - name: "Average Potential Penalty Amount"
      expr: AVG(potential_penalty_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_employee`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Employee business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`employee`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Last Name"
      expr: last_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Date Of Birth"
      expr: date_of_birth
    - name: "Social Security Number"
      expr: social_security_number
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
    - name: "State"
      expr: state
    - name: "Postal Code"
      expr: postal_code
    - name: "Country"
      expr: country
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Employment Status"
      expr: employment_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Employee"
      expr: COUNT(DISTINCT employee_id)
    - name: "Total Annual Salary"
      expr: SUM(annual_salary)
    - name: "Average Annual Salary"
      expr: AVG(annual_salary)
    - name: "Total Hourly Rate"
      expr: SUM(hourly_rate)
    - name: "Average Hourly Rate"
      expr: AVG(hourly_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_filing_response`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Filing Response business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`filing_response`"
  dimensions:
    - name: "Response Reference Number"
      expr: response_reference_number
    - name: "Regulator Code"
      expr: regulator_code
    - name: "Regulator Name"
      expr: regulator_name
    - name: "State Jurisdiction"
      expr: state_jurisdiction
    - name: "Response Date"
      expr: response_date
    - name: "Received Date"
      expr: received_date
    - name: "Response Type"
      expr: response_type
    - name: "Outcome Status"
      expr: outcome_status
    - name: "Approval Effective Date"
      expr: approval_effective_date
    - name: "Response Summary"
      expr: response_summary
    - name: "Response Details"
      expr: response_details
    - name: "Deficiency Count"
      expr: deficiency_count
    - name: "Deficiency Description"
      expr: deficiency_description
    - name: "Conditions Imposed"
      expr: conditions_imposed
    - name: "Information Requested"
      expr: information_requested
    - name: "Response Due Date"
      expr: response_due_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Filing Response"
      expr: COUNT(DISTINCT filing_response_id)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_notification_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Notification Template business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`notification_template`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Channel"
      expr: channel
    - name: "Audience"
      expr: audience
    - name: "Template Type"
      expr: template_type
    - name: "Subject"
      expr: subject
    - name: "Body"
      expr: body
    - name: "Language Code"
      expr: language_code
    - name: "Compliance Category"
      expr: compliance_category
    - name: "Regulatory Requirement Code"
      expr: regulatory_requirement_code
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Version Number"
      expr: version_number
    - name: "Priority"
      expr: priority
    - name: "Is Mandatory"
      expr: is_mandatory
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Notification Template"
      expr: COUNT(DISTINCT notification_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_policy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Policy business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`policy`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Title"
      expr: title
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Governing Regulation"
      expr: governing_regulation
    - name: "Regulatory Citation"
      expr: regulatory_citation
    - name: "Scope"
      expr: scope
    - name: "Applicable Lines Of Business"
      expr: applicable_lines_of_business
    - name: "Applicable States"
      expr: applicable_states
    - name: "Status"
      expr: status
    - name: "Version Number"
      expr: version_number
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Last Review Date"
      expr: last_review_date
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Review Frequency Months"
      expr: review_frequency_months
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Policy"
      expr: COUNT(DISTINCT policy_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_policy_version`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Policy Version business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`policy_version`"
  dimensions:
    - name: "Version Number"
      expr: version_number
    - name: "Version Sequence"
      expr: version_sequence
    - name: "Version Status"
      expr: version_status
    - name: "Version Type"
      expr: version_type
    - name: "Change Description"
      expr: change_description
    - name: "Change Summary"
      expr: change_summary
    - name: "Change Reason"
      expr: change_reason
    - name: "Regulatory Trigger"
      expr: regulatory_trigger
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Approval Date"
      expr: approval_date
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Published Date"
      expr: published_date
    - name: "Review Date"
      expr: review_date
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Superseded Date"
      expr: superseded_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Policy Version"
      expr: COUNT(DISTINCT policy_version_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_privacy_notice`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Privacy Notice business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`privacy_notice`"
  dimensions:
    - name: "Notice Version"
      expr: notice_version
    - name: "Notice Title"
      expr: notice_title
    - name: "Notice Type"
      expr: notice_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Distribution Channel"
      expr: distribution_channel
    - name: "Distribution Method"
      expr: distribution_method
    - name: "Language Code"
      expr: language_code
    - name: "Lob"
      expr: lob
    - name: "Product Type"
      expr: product_type
    - name: "State Code"
      expr: state_code
    - name: "Market Segment"
      expr: market_segment
    - name: "Notice Content"
      expr: notice_content
    - name: "Document Url"
      expr: document_url
    - name: "Document Format"
      expr: document_format
    - name: "Document Size Bytes"
      expr: document_size_bytes
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Privacy Notice"
      expr: COUNT(DISTINCT privacy_notice_id)
    - name: "Total Readability Grade Level"
      expr: SUM(readability_grade_level)
    - name: "Average Readability Grade Level"
      expr: AVG(readability_grade_level)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_risk_assessment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Risk Assessment business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`risk_assessment`"
  dimensions:
    - name: "Assessment Name"
      expr: assessment_name
    - name: "Assessment Type"
      expr: assessment_type
    - name: "Scope Description"
      expr: scope_description
    - name: "Assessment Status"
      expr: assessment_status
    - name: "Risk Level"
      expr: risk_level
    - name: "Likelihood Rating"
      expr: likelihood_rating
    - name: "Impact Rating"
      expr: impact_rating
    - name: "Identified Threats"
      expr: identified_threats
    - name: "Identified Vulnerabilities"
      expr: identified_vulnerabilities
    - name: "Affected Systems"
      expr: affected_systems
    - name: "Affected Processes"
      expr: affected_processes
    - name: "Phi Categories At Risk"
      expr: phi_categories_at_risk
    - name: "Data Volume At Risk"
      expr: data_volume_at_risk
    - name: "Member Population Affected"
      expr: member_population_affected
    - name: "Compliance Domain"
      expr: compliance_domain
    - name: "Assessment Methodology"
      expr: assessment_methodology
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Risk Assessment"
      expr: COUNT(DISTINCT risk_assessment_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Inherent Risk Score"
      expr: SUM(inherent_risk_score)
    - name: "Average Inherent Risk Score"
      expr: AVG(inherent_risk_score)
    - name: "Total Residual Risk Score"
      expr: SUM(residual_risk_score)
    - name: "Average Residual Risk Score"
      expr: AVG(residual_risk_score)
    - name: "Total Estimated Financial Impact"
      expr: SUM(estimated_financial_impact)
    - name: "Average Estimated Financial Impact"
      expr: AVG(estimated_financial_impact)
    - name: "Total Potential Regulatory Penalties"
      expr: SUM(potential_regulatory_penalties)
    - name: "Average Potential Regulatory Penalties"
      expr: AVG(potential_regulatory_penalties)
    - name: "Total Assessment Cost"
      expr: SUM(assessment_cost)
    - name: "Average Assessment Cost"
      expr: AVG(assessment_cost)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_task`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Task business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`task`"
  dimensions:
    - name: "Title"
      expr: title
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Priority"
      expr: priority
    - name: "Status"
      expr: status
    - name: "Owner Name"
      expr: owner_name
    - name: "Owner Email"
      expr: owner_email
    - name: "Assigned Date"
      expr: assigned_date
    - name: "Due Date"
      expr: due_date
    - name: "Start Date"
      expr: start_date
    - name: "Completion Date"
      expr: completion_date
    - name: "Completion Status"
      expr: completion_status
    - name: "Regulatory Reference Number"
      expr: regulatory_reference_number
    - name: "Policy Name"
      expr: policy_name
    - name: "Risk Level"
      expr: risk_level
    - name: "Risk Description"
      expr: risk_description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Task"
      expr: COUNT(DISTINCT task_id)
    - name: "Total Estimated Effort Hours"
      expr: SUM(estimated_effort_hours)
    - name: "Average Estimated Effort Hours"
      expr: AVG(estimated_effort_hours)
    - name: "Total Actual Effort Hours"
      expr: SUM(actual_effort_hours)
    - name: "Average Actual Effort Hours"
      expr: AVG(actual_effort_hours)
    - name: "Total Cost Estimate Amount"
      expr: SUM(cost_estimate_amount)
    - name: "Average Cost Estimate Amount"
      expr: AVG(cost_estimate_amount)
    - name: "Total Actual Cost Amount"
      expr: SUM(actual_cost_amount)
    - name: "Average Actual Cost Amount"
      expr: AVG(actual_cost_amount)
    - name: "Total Penalty Risk Amount"
      expr: SUM(penalty_risk_amount)
    - name: "Average Penalty Risk Amount"
      expr: AVG(penalty_risk_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_test`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Test business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`test`"
  dimensions:
    - name: "Test Name"
      expr: test_name
    - name: "Test Description"
      expr: test_description
    - name: "Test Category"
      expr: test_category
    - name: "Regulatory Reference"
      expr: regulatory_reference
    - name: "Compliance Area"
      expr: compliance_area
    - name: "Risk Level"
      expr: risk_level
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
    - name: "Owner Name"
      expr: owner_name
    - name: "Owner Email"
      expr: owner_email
    - name: "Owner Phone"
      expr: owner_phone
    - name: "Documentation Url"
      expr: documentation_url
    - name: "Audit Frequency"
      expr: audit_frequency
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Test"
      expr: COUNT(DISTINCT test_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_third_party_risk`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Third Party Risk business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`third_party_risk`"
  dimensions:
    - name: "Vendor Name"
      expr: vendor_name
    - name: "Vendor Type"
      expr: vendor_type
    - name: "Tin"
      expr: tin
    - name: "Assessment Date"
      expr: assessment_date
    - name: "Assessment Type"
      expr: assessment_type
    - name: "Assessment Status"
      expr: assessment_status
    - name: "Overall Risk Rating"
      expr: overall_risk_rating
    - name: "Risk Tier"
      expr: risk_tier
    - name: "Data Access Level"
      expr: data_access_level
    - name: "Phi Access Flag"
      expr: phi_access_flag
    - name: "Ephi Access Flag"
      expr: ephi_access_flag
    - name: "Baa Required Flag"
      expr: baa_required_flag
    - name: "Baa Executed Flag"
      expr: baa_executed_flag
    - name: "Baa Execution Date"
      expr: baa_execution_date
    - name: "Baa Expiration Date"
      expr: baa_expiration_date
    - name: "Contract Start Date"
      expr: contract_start_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Third Party Risk"
      expr: COUNT(DISTINCT third_party_risk_id)
    - name: "Total Inherent Risk Score"
      expr: SUM(inherent_risk_score)
    - name: "Average Inherent Risk Score"
      expr: AVG(inherent_risk_score)
    - name: "Total Residual Risk Score"
      expr: SUM(residual_risk_score)
    - name: "Average Residual Risk Score"
      expr: AVG(residual_risk_score)
    - name: "Total Contract Value Amount"
      expr: SUM(contract_value_amount)
    - name: "Average Contract Value Amount"
      expr: AVG(contract_value_amount)
    - name: "Total Annual Spend Amount"
      expr: SUM(annual_spend_amount)
    - name: "Average Annual Spend Amount"
      expr: AVG(annual_spend_amount)
    - name: "Total Cyber Insurance Amount"
      expr: SUM(cyber_insurance_amount)
    - name: "Average Cyber Insurance Amount"
      expr: AVG(cyber_insurance_amount)
    - name: "Total Security Assessment Score"
      expr: SUM(security_assessment_score)
    - name: "Average Security Assessment Score"
      expr: AVG(security_assessment_score)
    - name: "Total Privacy Assessment Score"
      expr: SUM(privacy_assessment_score)
    - name: "Average Privacy Assessment Score"
      expr: AVG(privacy_assessment_score)
    - name: "Total Compliance Assessment Score"
      expr: SUM(compliance_assessment_score)
    - name: "Average Compliance Assessment Score"
      expr: AVG(compliance_assessment_score)
    - name: "Total Financial Stability Score"
      expr: SUM(financial_stability_score)
    - name: "Average Financial Stability Score"
      expr: AVG(financial_stability_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_training_course`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Training Course business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`training_course`"
  dimensions:
    - name: "Course Name"
      expr: course_name
    - name: "Course Code"
      expr: course_code
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Delivery Method"
      expr: delivery_method
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Compliance Area"
      expr: compliance_area
    - name: "Target Audience"
      expr: target_audience
    - name: "Mandatory Flag"
      expr: mandatory_flag
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Version Number"
      expr: version_number
    - name: "Language"
      expr: language
    - name: "Instructor Name"
      expr: instructor_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Training Course"
      expr: COUNT(DISTINCT training_course_id)
    - name: "Total Duration Hours"
      expr: SUM(duration_hours)
    - name: "Average Duration Hours"
      expr: AVG(duration_hours)
    - name: "Total Credit Hours"
      expr: SUM(credit_hours)
    - name: "Average Credit Hours"
      expr: AVG(credit_hours)
    - name: "Total Cost"
      expr: SUM(cost)
    - name: "Average Cost"
      expr: AVG(cost)
    - name: "Total Passing Score Percent"
      expr: SUM(passing_score_percent)
    - name: "Average Passing Score Percent"
      expr: AVG(passing_score_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_training_module`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Training Module business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`training_module`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Module Type"
      expr: module_type
    - name: "Version"
      expr: version
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Delivery Method"
      expr: delivery_method
    - name: "Duration Minutes"
      expr: duration_minutes
    - name: "Mandatory"
      expr: mandatory
    - name: "Target Audience"
      expr: target_audience
    - name: "Compliance Area"
      expr: compliance_area
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Trainer Name"
      expr: trainer_name
    - name: "Trainer Contact Email"
      expr: trainer_contact_email
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Training Module"
      expr: COUNT(DISTINCT training_module_id)
    - name: "Total Credit Hours"
      expr: SUM(credit_hours)
    - name: "Average Credit Hours"
      expr: AVG(credit_hours)
    - name: "Total Cost"
      expr: SUM(cost)
    - name: "Average Cost"
      expr: AVG(cost)
    - name: "Total Assessment Pass Score"
      expr: SUM(assessment_pass_score)
    - name: "Average Assessment Pass Score"
      expr: AVG(assessment_pass_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_training_record`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Training Record business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`training_record`"
  dimensions:
    - name: "Employee Name"
      expr: employee_name
    - name: "Employee Email"
      expr: employee_email
    - name: "Department"
      expr: department
    - name: "Job Title"
      expr: job_title
    - name: "Training Module Name"
      expr: training_module_name
    - name: "Training Category"
      expr: training_category
    - name: "Training Type"
      expr: training_type
    - name: "Training Delivery Method"
      expr: training_delivery_method
    - name: "Training Provider"
      expr: training_provider
    - name: "Assigned Date"
      expr: assigned_date
    - name: "Due Date"
      expr: due_date
    - name: "Start Timestamp"
      expr: start_timestamp
    - name: "Completion Timestamp"
      expr: completion_timestamp
    - name: "Completion Date"
      expr: completion_date
    - name: "Duration Minutes"
      expr: duration_minutes
    - name: "Status"
      expr: status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Training Record"
      expr: COUNT(DISTINCT training_record_id)
    - name: "Total Score"
      expr: SUM(score)
    - name: "Average Score"
      expr: AVG(score)
    - name: "Total Passing Score"
      expr: SUM(passing_score)
    - name: "Average Passing Score"
      expr: AVG(passing_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`compliance_vendor_compliance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Vendor Compliance business metrics"
  source: "`cmoore_customer_demos`.`compliance`.`vendor_compliance`"
  dimensions:
    - name: "Vendor Type"
      expr: vendor_type
    - name: "Tin"
      expr: tin
    - name: "Duns Number"
      expr: duns_number
    - name: "Compliance Status"
      expr: compliance_status
    - name: "Hipaa Compliant Flag"
      expr: hipaa_compliant_flag
    - name: "Hipaa Certification Date"
      expr: hipaa_certification_date
    - name: "Hipaa Expiration Date"
      expr: hipaa_expiration_date
    - name: "Baa Executed Flag"
      expr: baa_executed_flag
    - name: "Baa Execution Date"
      expr: baa_execution_date
    - name: "Baa Expiration Date"
      expr: baa_expiration_date
    - name: "Soc2 Type2 Certified Flag"
      expr: soc2_type2_certified_flag
    - name: "Soc2 Certification Date"
      expr: soc2_certification_date
    - name: "Soc2 Expiration Date"
      expr: soc2_expiration_date
    - name: "Iso27001 Certified Flag"
      expr: iso27001_certified_flag
    - name: "Iso27001 Certification Date"
      expr: iso27001_certification_date
    - name: "Iso27001 Expiration Date"
      expr: iso27001_expiration_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Vendor Compliance"
      expr: COUNT(DISTINCT vendor_compliance_id)
    - name: "Total Last Audit Score"
      expr: SUM(last_audit_score)
    - name: "Average Last Audit Score"
      expr: AVG(last_audit_score)
    - name: "Total Cyber Insurance Coverage Amount"
      expr: SUM(cyber_insurance_coverage_amount)
    - name: "Average Cyber Insurance Coverage Amount"
      expr: AVG(cyber_insurance_coverage_amount)
    - name: "Total General Liability Coverage Amount"
      expr: SUM(general_liability_coverage_amount)
    - name: "Average General Liability Coverage Amount"
      expr: AVG(general_liability_coverage_amount)
$$;