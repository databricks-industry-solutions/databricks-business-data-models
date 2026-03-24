-- Metric views for domain: authorization | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:06:50

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_appeal_decision`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Appeal Decision business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`appeal_decision`"
  dimensions:
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Address"
      expr: member_address
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Appeal Source"
      expr: appeal_source
    - name: "Appeal Submission Date"
      expr: appeal_submission_date
    - name: "Appeal Submission Method"
      expr: appeal_submission_method
    - name: "Appeal Deadline Date"
      expr: appeal_deadline_date
    - name: "Appeal Resolution Date"
      expr: appeal_resolution_date
    - name: "Appeal Outcome"
      expr: appeal_outcome
    - name: "Decision Effective Date"
      expr: decision_effective_date
    - name: "Decision Expiration Date"
      expr: decision_expiration_date
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Review Comments"
      expr: review_comments
    - name: "Clinical Guideline Result"
      expr: clinical_guideline_result
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Appeal Decision"
      expr: COUNT(DISTINCT appeal_decision_id)
    - name: "Total Decision Amount"
      expr: SUM(decision_amount)
    - name: "Average Decision Amount"
      expr: AVG(decision_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_approval_reason`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Approval Reason business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`approval_reason`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Subcategory"
      expr: subcategory
    - name: "Clinical Guideline Source"
      expr: clinical_guideline_source
    - name: "Guideline Version"
      expr: guideline_version
    - name: "Medical Necessity Indicator"
      expr: medical_necessity_indicator
    - name: "Requires Clinical Review"
      expr: requires_clinical_review
    - name: "Auto Approval Eligible"
      expr: auto_approval_eligible
    - name: "Regulatory Basis"
      expr: regulatory_basis
    - name: "Applicable Lob"
      expr: applicable_lob
    - name: "Applicable Plan Types"
      expr: applicable_plan_types
    - name: "Service Type Category"
      expr: service_type_category
    - name: "Cpt Code Applicability"
      expr: cpt_code_applicability
    - name: "Icd10 Code Applicability"
      expr: icd10_code_applicability
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Approval Reason"
      expr: COUNT(DISTINCT approval_reason_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Assignment business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_assignment`"
  dimensions:
    - name: "Assigned To User Name"
      expr: assigned_to_user_name
    - name: "Assigned To Workgroup Name"
      expr: assigned_to_workgroup_name
    - name: "Assignment Timestamp"
      expr: assignment_timestamp
    - name: "Assignment Date"
      expr: assignment_date
    - name: "Assignment Method"
      expr: assignment_method
    - name: "Assigned By User Name"
      expr: assigned_by_user_name
    - name: "Assignment Reason"
      expr: assignment_reason
    - name: "Assignment Notes"
      expr: assignment_notes
    - name: "Accepted Timestamp"
      expr: accepted_timestamp
    - name: "Started Timestamp"
      expr: started_timestamp
    - name: "Completed Timestamp"
      expr: completed_timestamp
    - name: "Due Date"
      expr: due_date
    - name: "Due Timestamp"
      expr: due_timestamp
    - name: "Is Sla Met"
      expr: is_sla_met
    - name: "Is Escalated"
      expr: is_escalated
    - name: "Escalation Reason"
      expr: escalation_reason
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Assignment"
      expr: COUNT(DISTINCT auth_assignment_id)
    - name: "Total Sla Hours"
      expr: SUM(sla_hours)
    - name: "Average Sla Hours"
      expr: AVG(sla_hours)
    - name: "Total Time To Accept Hours"
      expr: SUM(time_to_accept_hours)
    - name: "Average Time To Accept Hours"
      expr: AVG(time_to_accept_hours)
    - name: "Total Time To Start Hours"
      expr: SUM(time_to_start_hours)
    - name: "Average Time To Start Hours"
      expr: AVG(time_to_start_hours)
    - name: "Total Time To Complete Hours"
      expr: SUM(time_to_complete_hours)
    - name: "Average Time To Complete Hours"
      expr: AVG(time_to_complete_hours)
    - name: "Total Active Work Hours"
      expr: SUM(active_work_hours)
    - name: "Average Active Work Hours"
      expr: AVG(active_work_hours)
    - name: "Total Workload Score"
      expr: SUM(workload_score)
    - name: "Average Workload Score"
      expr: AVG(workload_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_notification`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Notification business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_notification`"
  dimensions:
    - name: "Notification Type"
      expr: notification_type
    - name: "Recipient Type"
      expr: recipient_type
    - name: "Recipient Name"
      expr: recipient_name
    - name: "Recipient Email"
      expr: recipient_email
    - name: "Recipient Fax"
      expr: recipient_fax
    - name: "Recipient Phone"
      expr: recipient_phone
    - name: "Recipient Address Line1"
      expr: recipient_address_line1
    - name: "Recipient Address Line2"
      expr: recipient_address_line2
    - name: "Recipient City"
      expr: recipient_city
    - name: "Recipient State"
      expr: recipient_state
    - name: "Recipient Zip Code"
      expr: recipient_zip_code
    - name: "Recipient Country Code"
      expr: recipient_country_code
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Notification Subject"
      expr: notification_subject
    - name: "Notification Body"
      expr: notification_body
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Notification"
      expr: COUNT(DISTINCT auth_notification_id)
    - name: "Total Approved Units"
      expr: SUM(approved_units)
    - name: "Average Approved Units"
      expr: AVG(approved_units)
    - name: "Total Turnaround Time Hours"
      expr: SUM(turnaround_time_hours)
    - name: "Average Turnaround Time Hours"
      expr: AVG(turnaround_time_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_override`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Override business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_override`"
  dimensions:
    - name: "Override Type"
      expr: override_type
    - name: "Override Reason Description"
      expr: override_reason_description
    - name: "Clinical Justification"
      expr: clinical_justification
    - name: "Original Decision"
      expr: original_decision
    - name: "Original Decision Date"
      expr: original_decision_date
    - name: "Override Decision"
      expr: override_decision
    - name: "Override Decision Date"
      expr: override_decision_date
    - name: "Override Decision Timestamp"
      expr: override_decision_timestamp
    - name: "Approver Name"
      expr: approver_name
    - name: "Approver Title"
      expr: approver_title
    - name: "Approver Credentials"
      expr: approver_credentials
    - name: "Approver Specialty"
      expr: approver_specialty
    - name: "Approver Npi"
      expr: approver_npi
    - name: "Requesting Provider Npi"
      expr: requesting_provider_npi
    - name: "Requesting Provider Name"
      expr: requesting_provider_name
    - name: "Member Name"
      expr: member_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Override"
      expr: COUNT(DISTINCT auth_override_id)
    - name: "Total Authorized Units"
      expr: SUM(authorized_units)
    - name: "Average Authorized Units"
      expr: AVG(authorized_units)
    - name: "Total Authorized Amount"
      expr: SUM(authorized_amount)
    - name: "Average Authorized Amount"
      expr: AVG(authorized_amount)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_queue`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Queue business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_queue`"
  dimensions:
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Queue Entry Timestamp"
      expr: queue_entry_timestamp
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Requested Service Date"
      expr: requested_service_date
    - name: "Admission Date"
      expr: admission_date
    - name: "Discharge Date"
      expr: discharge_date
    - name: "Length Of Stay"
      expr: length_of_stay
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Plan Type"
      expr: plan_type
    - name: "Reviewer Type"
      expr: reviewer_type
    - name: "Assignment Timestamp"
      expr: assignment_timestamp
    - name: "Review Start Timestamp"
      expr: review_start_timestamp
    - name: "Sla Due Timestamp"
      expr: sla_due_timestamp
    - name: "Turnaround Time Hours"
      expr: turnaround_time_hours
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Queue"
      expr: COUNT(DISTINCT auth_queue_id)
    - name: "Total Requested Units"
      expr: SUM(requested_units)
    - name: "Average Requested Units"
      expr: AVG(requested_units)
    - name: "Total Estimated Cost"
      expr: SUM(estimated_cost)
    - name: "Average Estimated Cost"
      expr: AVG(estimated_cost)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Rule business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_rule`"
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
    - name: "Cpt Code List"
      expr: cpt_code_list
    - name: "Hcpcs Code List"
      expr: hcpcs_code_list
    - name: "Icd10 Code List"
      expr: icd10_code_list
    - name: "Drg Code List"
      expr: drg_code_list
    - name: "Lob"
      expr: lob
    - name: "Plan Type"
      expr: plan_type
    - name: "Network Type"
      expr: network_type
    - name: "Medical Necessity Required"
      expr: medical_necessity_required
    - name: "Prior Authorization Required"
      expr: prior_authorization_required
    - name: "Concurrent Review Required"
      expr: concurrent_review_required
    - name: "Retrospective Review Required"
      expr: retrospective_review_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Rule"
      expr: COUNT(DISTINCT auth_rule_id)
    - name: "Total Quantity Threshold"
      expr: SUM(quantity_threshold)
    - name: "Average Quantity Threshold"
      expr: AVG(quantity_threshold)
    - name: "Total Cost Threshold Amount"
      expr: SUM(cost_threshold_amount)
    - name: "Average Cost Threshold Amount"
      expr: AVG(cost_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_status`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Status business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_status`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Is Active"
      expr: is_active
    - name: "Is Final"
      expr: is_final
    - name: "Is Appealable"
      expr: is_appealable
    - name: "Requires Notification"
      expr: requires_notification
    - name: "Notification Timeframe Hours"
      expr: notification_timeframe_hours
    - name: "Allows Partial Approval"
      expr: allows_partial_approval
    - name: "Requires Clinical Review"
      expr: requires_clinical_review
    - name: "Requires Peer To Peer"
      expr: requires_peer_to_peer
    - name: "Display Order"
      expr: display_order
    - name: "Color Code"
      expr: color_code
    - name: "Icon Name"
      expr: icon_name
    - name: "Sla Hours"
      expr: sla_hours
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Status"
      expr: COUNT(DISTINCT auth_status_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_auth_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auth Template business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`auth_template`"
  dimensions:
    - name: "Template Code"
      expr: template_code
    - name: "Template Name"
      expr: template_name
    - name: "Template Description"
      expr: template_description
    - name: "Cpt Code Range"
      expr: cpt_code_range
    - name: "Hcpcs Code Range"
      expr: hcpcs_code_range
    - name: "Icd10 Diagnosis Range"
      expr: icd10_diagnosis_range
    - name: "Drg Range"
      expr: drg_range
    - name: "Lob"
      expr: lob
    - name: "Plan Type"
      expr: plan_type
    - name: "Network Tier"
      expr: network_tier
    - name: "Standard Turnaround Hours"
      expr: standard_turnaround_hours
    - name: "Expedited Turnaround Hours"
      expr: expedited_turnaround_hours
    - name: "Requires Peer Review"
      expr: requires_peer_review
    - name: "Requires Medical Director Approval"
      expr: requires_medical_director_approval
    - name: "Auto Approval Eligible"
      expr: auto_approval_eligible
    - name: "Auto Approval Criteria"
      expr: auto_approval_criteria
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auth Template"
      expr: COUNT(DISTINCT auth_template_id)
    - name: "Total Approval Rate Percentage"
      expr: SUM(approval_rate_percentage)
    - name: "Average Approval Rate Percentage"
      expr: AVG(approval_rate_percentage)
    - name: "Total Average Processing Time Hours"
      expr: SUM(average_processing_time_hours)
    - name: "Average Average Processing Time Hours"
      expr: AVG(average_processing_time_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_authorization_denial_reason`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Authorization Denial Reason business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`authorization_denial_reason`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Subcategory"
      expr: subcategory
    - name: "Status"
      expr: status
    - name: "Cms Denial Code"
      expr: cms_denial_code
    - name: "Carc Code"
      expr: carc_code
    - name: "Rarc Code"
      expr: rarc_code
    - name: "Denial Type"
      expr: denial_type
    - name: "Appealable Flag"
      expr: appealable_flag
    - name: "Appeal Timeframe Days"
      expr: appeal_timeframe_days
    - name: "Reconsideration Allowed Flag"
      expr: reconsideration_allowed_flag
    - name: "Provider Notification Required Flag"
      expr: provider_notification_required_flag
    - name: "Member Notification Required Flag"
      expr: member_notification_required_flag
    - name: "Eob Display Text"
      expr: eob_display_text
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Authorization Denial Reason"
      expr: COUNT(DISTINCT authorization_denial_reason_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_care_setting`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Care Setting business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`care_setting`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Pos Code"
      expr: pos_code
    - name: "Revenue Code"
      expr: revenue_code
    - name: "Type Of Bill Code"
      expr: type_of_bill_code
    - name: "Requires Prior Authorization"
      expr: requires_prior_authorization
    - name: "Authorization Urgency Level"
      expr: authorization_urgency_level
    - name: "Standard Review Timeframe Hours"
      expr: standard_review_timeframe_hours
    - name: "Expedited Review Timeframe Hours"
      expr: expedited_review_timeframe_hours
    - name: "Requires Concurrent Review"
      expr: requires_concurrent_review
    - name: "Concurrent Review Frequency Days"
      expr: concurrent_review_frequency_days
    - name: "Allows Retrospective Review"
      expr: allows_retrospective_review
    - name: "Clinical Guideline Set"
      expr: clinical_guideline_set
    - name: "Is Facility Based"
      expr: is_facility_based
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Care Setting"
      expr: COUNT(DISTINCT care_setting_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_clinical_guideline`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Clinical Guideline business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`clinical_guideline`"
  dimensions:
    - name: "Guideline Name"
      expr: guideline_name
    - name: "Version Label"
      expr: version_label
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Guideline Type"
      expr: guideline_type
    - name: "Clinical Area"
      expr: clinical_area
    - name: "Specialty"
      expr: specialty
    - name: "Care Setting"
      expr: care_setting
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Diagnosis Description"
      expr: diagnosis_description
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Procedure Description"
      expr: procedure_description
    - name: "Evidence Level"
      expr: evidence_level
    - name: "Source"
      expr: source
    - name: "Source Version"
      expr: source_version
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Clinical Guideline"
      expr: COUNT(DISTINCT clinical_guideline_id)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Cost Estimate"
      expr: SUM(cost_estimate)
    - name: "Average Cost Estimate"
      expr: AVG(cost_estimate)
    - name: "Total Reimbursement Rate"
      expr: SUM(reimbursement_rate)
    - name: "Average Reimbursement Rate"
      expr: AVG(reimbursement_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_concurrent_review`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Concurrent Review business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`concurrent_review`"
  dimensions:
    - name: "Member Name"
      expr: member_name
    - name: "Member Date Of Birth"
      expr: member_date_of_birth
    - name: "Member Gender"
      expr: member_gender
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Service Code"
      expr: service_code
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Service Date"
      expr: service_date
    - name: "Service Start Timestamp"
      expr: service_start_timestamp
    - name: "Service End Timestamp"
      expr: service_end_timestamp
    - name: "Quantity"
      expr: quantity
    - name: "Unit Of Measure"
      expr: unit_of_measure
    - name: "Decision"
      expr: decision
    - name: "Decision Timestamp"
      expr: decision_timestamp
    - name: "Reviewer Role"
      expr: reviewer_role
    - name: "Reviewer Notes"
      expr: reviewer_notes
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Concurrent Review"
      expr: COUNT(DISTINCT concurrent_review_id)
    - name: "Total Charge Amount"
      expr: SUM(charge_amount)
    - name: "Average Charge Amount"
      expr: AVG(charge_amount)
    - name: "Total Approved Amount"
      expr: SUM(approved_amount)
    - name: "Average Approved Amount"
      expr: AVG(approved_amount)
    - name: "Total Patient Responsibility Amount"
      expr: SUM(patient_responsibility_amount)
    - name: "Average Patient Responsibility Amount"
      expr: AVG(patient_responsibility_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Clinical Score"
      expr: SUM(clinical_score)
    - name: "Average Clinical Score"
      expr: AVG(clinical_score)
    - name: "Total Claim Amount"
      expr: SUM(claim_amount)
    - name: "Average Claim Amount"
      expr: AVG(claim_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_decision`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Decision business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`decision`"
  dimensions:
    - name: "Date"
      expr: date
    - name: "Timestamp"
      expr: timestamp
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Approved Quantity Unit"
      expr: approved_quantity_unit
    - name: "Requested Quantity Unit"
      expr: requested_quantity_unit
    - name: "Type"
      expr: type
    - name: "Method"
      expr: method
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Reviewer Credential"
      expr: reviewer_credential
    - name: "Reviewer Specialty"
      expr: reviewer_specialty
    - name: "Medical Necessity Met"
      expr: medical_necessity_met
    - name: "Authorization Number"
      expr: authorization_number
    - name: "Certification Type Code"
      expr: certification_type_code
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Procedure Description"
      expr: procedure_description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Decision"
      expr: COUNT(DISTINCT decision_id)
    - name: "Total Approved Quantity"
      expr: SUM(approved_quantity)
    - name: "Average Approved Quantity"
      expr: AVG(approved_quantity)
    - name: "Total Requested Quantity"
      expr: SUM(requested_quantity)
    - name: "Average Requested Quantity"
      expr: AVG(requested_quantity)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_line_item`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Line Item business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`line_item`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Procedure Description"
      expr: procedure_description
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Diagnosis Description"
      expr: diagnosis_description
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
    - name: "Quantity Unit"
      expr: quantity_unit
    - name: "Determination Date"
      expr: determination_date
    - name: "Determination Timestamp"
      expr: determination_timestamp
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Service Start Date"
      expr: service_start_date
    - name: "Service End Date"
      expr: service_end_date
    - name: "Servicing Provider Npi"
      expr: servicing_provider_npi
    - name: "Servicing Provider Name"
      expr: servicing_provider_name
    - name: "Servicing Provider Tin"
      expr: servicing_provider_tin
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Line Item"
      expr: COUNT(DISTINCT line_item_id)
    - name: "Total Requested Quantity"
      expr: SUM(requested_quantity)
    - name: "Average Requested Quantity"
      expr: AVG(requested_quantity)
    - name: "Total Approved Quantity"
      expr: SUM(approved_quantity)
    - name: "Average Approved Quantity"
      expr: AVG(approved_quantity)
    - name: "Total Denied Quantity"
      expr: SUM(denied_quantity)
    - name: "Average Denied Quantity"
      expr: AVG(denied_quantity)
    - name: "Total Estimated Cost"
      expr: SUM(estimated_cost)
    - name: "Average Estimated Cost"
      expr: AVG(estimated_cost)
    - name: "Total Approved Cost"
      expr: SUM(approved_cost)
    - name: "Average Approved Cost"
      expr: AVG(approved_cost)
    - name: "Total Member Cost Share Estimate"
      expr: SUM(member_cost_share_estimate)
    - name: "Average Member Cost Share Estimate"
      expr: AVG(member_cost_share_estimate)
    - name: "Total Turnaround Time Hours"
      expr: SUM(turnaround_time_hours)
    - name: "Average Turnaround Time Hours"
      expr: AVG(turnaround_time_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_priority_level`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Priority Level business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`priority_level`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Severity Rank"
      expr: severity_rank
    - name: "Sla Business Days"
      expr: sla_business_days
    - name: "Requires Immediate Review"
      expr: requires_immediate_review
    - name: "Auto Escalation Enabled"
      expr: auto_escalation_enabled
    - name: "Clinical Review Required"
      expr: clinical_review_required
    - name: "Peer To Peer Eligible"
      expr: peer_to_peer_eligible
    - name: "Expedited Appeal Eligible"
      expr: expedited_appeal_eligible
    - name: "After Hours Processing"
      expr: after_hours_processing
    - name: "Weekend Processing"
      expr: weekend_processing
    - name: "Holiday Processing"
      expr: holiday_processing
    - name: "Applies To Inpatient"
      expr: applies_to_inpatient
    - name: "Applies To Outpatient"
      expr: applies_to_outpatient
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Priority Level"
      expr: COUNT(DISTINCT priority_level_id)
    - name: "Total Sla Response Hours"
      expr: SUM(sla_response_hours)
    - name: "Average Sla Response Hours"
      expr: AVG(sla_response_hours)
    - name: "Total Sla Decision Hours"
      expr: SUM(sla_decision_hours)
    - name: "Average Sla Decision Hours"
      expr: AVG(sla_decision_hours)
    - name: "Total Escalation Threshold Hours"
      expr: SUM(escalation_threshold_hours)
    - name: "Average Escalation Threshold Hours"
      expr: AVG(escalation_threshold_hours)
    - name: "Total Notification Frequency Hours"
      expr: SUM(notification_frequency_hours)
    - name: "Average Notification Frequency Hours"
      expr: AVG(notification_frequency_hours)
    - name: "Total Concurrent Review Interval Hours"
      expr: SUM(concurrent_review_interval_hours)
    - name: "Average Concurrent Review Interval Hours"
      expr: AVG(concurrent_review_interval_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_request`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Request business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`request`"
  dimensions:
    - name: "Requesting Provider Npi"
      expr: requesting_provider_npi
    - name: "Servicing Provider Npi"
      expr: servicing_provider_npi
    - name: "Facility Npi"
      expr: facility_npi
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Procedure Code Type"
      expr: procedure_code_type
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
    - name: "Drg Code"
      expr: drg_code
    - name: "Requested Service Date"
      expr: requested_service_date
    - name: "Requested Start Date"
      expr: requested_start_date
    - name: "Requested End Date"
      expr: requested_end_date
    - name: "Unit Type"
      expr: unit_type
    - name: "Admission Type"
      expr: admission_type
    - name: "Admission Source"
      expr: admission_source
    - name: "Clinical Justification"
      expr: clinical_justification
    - name: "Supporting Documentation Indicator"
      expr: supporting_documentation_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Request"
      expr: COUNT(DISTINCT request_id)
    - name: "Total Requested Units"
      expr: SUM(requested_units)
    - name: "Average Requested Units"
      expr: AVG(requested_units)
    - name: "Total Approved Units"
      expr: SUM(approved_units)
    - name: "Average Approved Units"
      expr: AVG(approved_units)
    - name: "Total Estimated Cost"
      expr: SUM(estimated_cost)
    - name: "Average Estimated Cost"
      expr: AVG(estimated_cost)
    - name: "Total Estimated Allowed Amount"
      expr: SUM(estimated_allowed_amount)
    - name: "Average Estimated Allowed Amount"
      expr: AVG(estimated_allowed_amount)
    - name: "Total Member Responsibility Amount"
      expr: SUM(member_responsibility_amount)
    - name: "Average Member Responsibility Amount"
      expr: AVG(member_responsibility_amount)
    - name: "Total Fraud Score"
      expr: SUM(fraud_score)
    - name: "Average Fraud Score"
      expr: AVG(fraud_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_request_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Request Type business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`request_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Priority Level"
      expr: priority_level
    - name: "Standard Turnaround Time Hours"
      expr: standard_turnaround_time_hours
    - name: "Expedited Turnaround Time Hours"
      expr: expedited_turnaround_time_hours
    - name: "Requires Clinical Review"
      expr: requires_clinical_review
    - name: "Requires Medical Director Review"
      expr: requires_medical_director_review
    - name: "Requires Peer To Peer"
      expr: requires_peer_to_peer
    - name: "Auto Approval Eligible"
      expr: auto_approval_eligible
    - name: "Requires Supporting Documentation"
      expr: requires_supporting_documentation
    - name: "Documentation Requirements"
      expr: documentation_requirements
    - name: "Clinical Guideline Source"
      expr: clinical_guideline_source
    - name: "Applicable Service Types"
      expr: applicable_service_types
    - name: "Applicable Lines Of Business"
      expr: applicable_lines_of_business
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Request Type"
      expr: COUNT(DISTINCT request_type_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_retrospective_review`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Retrospective Review business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`retrospective_review`"
  dimensions:
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Address"
      expr: member_address
    - name: "Member Phone"
      expr: member_phone
    - name: "Member Email"
      expr: member_email
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Specialty"
      expr: provider_specialty
    - name: "Claim Number"
      expr: claim_number
    - name: "Claim Service Date"
      expr: claim_service_date
    - name: "Claim Submission Date"
      expr: claim_submission_date
    - name: "Claim Type"
      expr: claim_type
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Drg Code"
      expr: drg_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Retrospective Review"
      expr: COUNT(DISTINCT retrospective_review_id)
    - name: "Total Service Charge Amount"
      expr: SUM(service_charge_amount)
    - name: "Average Service Charge Amount"
      expr: AVG(service_charge_amount)
    - name: "Total Payment Adjustment Amount"
      expr: SUM(payment_adjustment_amount)
    - name: "Average Payment Adjustment Amount"
      expr: AVG(payment_adjustment_amount)
    - name: "Total Corrected Claim Amount"
      expr: SUM(corrected_claim_amount)
    - name: "Average Corrected Claim Amount"
      expr: AVG(corrected_claim_amount)
    - name: "Total Original Claim Amount"
      expr: SUM(original_claim_amount)
    - name: "Average Original Claim Amount"
      expr: AVG(original_claim_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_service_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Service Type business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`service_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Code Type"
      expr: code_type
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Subcategory"
      expr: subcategory
    - name: "Specialty"
      expr: specialty
    - name: "Requires Prior Authorization"
      expr: requires_prior_authorization
    - name: "Authorization Type"
      expr: authorization_type
    - name: "Clinical Guideline Source"
      expr: clinical_guideline_source
    - name: "Medical Necessity Criteria"
      expr: medical_necessity_criteria
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Place Of Service"
      expr: place_of_service
    - name: "Service Setting"
      expr: service_setting
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Service Type"
      expr: COUNT(DISTINCT service_type_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_utilization_case`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Utilization Case business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`utilization_case`"
  dimensions:
    - name: "Case Number"
      expr: case_number
    - name: "Member First Name"
      expr: member_first_name
    - name: "Member Last Name"
      expr: member_last_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Gender"
      expr: member_gender
    - name: "Member Address"
      expr: member_address
    - name: "Member Phone"
      expr: member_phone
    - name: "Member Email"
      expr: member_email
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Specialty Code"
      expr: provider_specialty_code
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Diagnosis Description"
      expr: diagnosis_description
    - name: "Prior Auth Number"
      expr: prior_auth_number
    - name: "Prior Auth Status"
      expr: prior_auth_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Utilization Case"
      expr: COUNT(DISTINCT utilization_case_id)
    - name: "Total Estimated Cost"
      expr: SUM(estimated_cost)
    - name: "Average Estimated Cost"
      expr: AVG(estimated_cost)
    - name: "Total Approved Amount"
      expr: SUM(approved_amount)
    - name: "Average Approved Amount"
      expr: AVG(approved_amount)
    - name: "Total Patient Responsibility Amount"
      expr: SUM(patient_responsibility_amount)
    - name: "Average Patient Responsibility Amount"
      expr: AVG(patient_responsibility_amount)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percent"
      expr: SUM(coinsurance_percent)
    - name: "Average Coinsurance Percent"
      expr: AVG(coinsurance_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`authorization_utilization_review`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Utilization Review business metrics"
  source: "`cmoore_customer_demos`.`authorization`.`utilization_review`"
  dimensions:
    - name: "Member Age"
      expr: member_age
    - name: "Member Gender"
      expr: member_gender
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Specialty"
      expr: provider_specialty
    - name: "Request Source"
      expr: request_source
    - name: "Request Date"
      expr: request_date
    - name: "Review Type"
      expr: review_type
    - name: "Review Date"
      expr: review_date
    - name: "Reviewer Role"
      expr: reviewer_role
    - name: "Recommendation"
      expr: recommendation
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Hcpcs Code"
      expr: hcpcs_code
    - name: "Drg Code"
      expr: drg_code
    - name: "Ndc Code"
      expr: ndc_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Utilization Review"
      expr: COUNT(DISTINCT utilization_review_id)
    - name: "Total Approval Limit"
      expr: SUM(approval_limit)
    - name: "Average Approval Limit"
      expr: AVG(approval_limit)
    - name: "Total Approved Amount"
      expr: SUM(approved_amount)
    - name: "Average Approved Amount"
      expr: AVG(approved_amount)
    - name: "Total Patient Responsibility Amount"
      expr: SUM(patient_responsibility_amount)
    - name: "Average Patient Responsibility Amount"
      expr: AVG(patient_responsibility_amount)
    - name: "Total Insurer Responsibility Amount"
      expr: SUM(insurer_responsibility_amount)
    - name: "Average Insurer Responsibility Amount"
      expr: AVG(insurer_responsibility_amount)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
$$;