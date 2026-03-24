-- Metric views for domain: credentialing | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:07:17

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_board_certification`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Board Certification business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`board_certification`"
  dimensions:
    - name: "Certification Name"
      expr: certification_name
    - name: "Certification Code"
      expr: certification_code
    - name: "Specialty Type"
      expr: specialty_type
    - name: "Accrediting Body Name"
      expr: accrediting_body_name
    - name: "Accrediting Body Code"
      expr: accrediting_body_code
    - name: "Accrediting Body Type"
      expr: accrediting_body_type
    - name: "Abms Recognized Flag"
      expr: abms_recognized_flag
    - name: "Aoa Recognized Flag"
      expr: aoa_recognized_flag
    - name: "Ncqa Credentialing Accepted Flag"
      expr: ncqa_credentialing_accepted_flag
    - name: "Cms Recognized Flag"
      expr: cms_recognized_flag
    - name: "Specialty Category"
      expr: specialty_category
    - name: "Taxonomy Code"
      expr: taxonomy_code
    - name: "Recertification Required Flag"
      expr: recertification_required_flag
    - name: "Recertification Cycle Years"
      expr: recertification_cycle_years
    - name: "Moc Required Flag"
      expr: moc_required_flag
    - name: "Cme Hours Required"
      expr: cme_hours_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Board Certification"
      expr: COUNT(DISTINCT board_certification_id)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_caqh_integration`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Caqh Integration business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`caqh_integration`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Integration Type"
      expr: integration_type
    - name: "Integration Status"
      expr: integration_status
    - name: "Request Timestamp"
      expr: request_timestamp
    - name: "Response Timestamp"
      expr: response_timestamp
    - name: "Sync Date"
      expr: sync_date
    - name: "Last Successful Sync Date"
      expr: last_successful_sync_date
    - name: "Api Endpoint"
      expr: api_endpoint
    - name: "Api Version"
      expr: api_version
    - name: "Fields Requested"
      expr: fields_requested
    - name: "Fields Retrieved"
      expr: fields_retrieved
    - name: "Fields Missing"
      expr: fields_missing
    - name: "Record Count"
      expr: record_count
    - name: "Attestation Date"
      expr: attestation_date
    - name: "Attestation Status"
      expr: attestation_status
    - name: "Profile Status"
      expr: profile_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Caqh Integration"
      expr: COUNT(DISTINCT caqh_integration_id)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
    - name: "Total Completeness Percentage"
      expr: SUM(completeness_percentage)
    - name: "Average Completeness Percentage"
      expr: AVG(completeness_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_committee`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Committee business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`committee`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Description"
      expr: description
    - name: "Charter Document Reference"
      expr: charter_document_reference
    - name: "Formation Date"
      expr: formation_date
    - name: "Dissolution Date"
      expr: dissolution_date
    - name: "Meeting Frequency"
      expr: meeting_frequency
    - name: "Meeting Day Of Week"
      expr: meeting_day_of_week
    - name: "Meeting Time"
      expr: meeting_time
    - name: "Meeting Duration Minutes"
      expr: meeting_duration_minutes
    - name: "Meeting Location"
      expr: meeting_location
    - name: "Meeting Format"
      expr: meeting_format
    - name: "Quorum Requirement"
      expr: quorum_requirement
    - name: "Chair Npi"
      expr: chair_npi
    - name: "Chair Name"
      expr: chair_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Committee"
      expr: COUNT(DISTINCT committee_id)
    - name: "Total Quorum Percentage"
      expr: SUM(quorum_percentage)
    - name: "Average Quorum Percentage"
      expr: AVG(quorum_percentage)
    - name: "Total Voting Threshold Percentage"
      expr: SUM(voting_threshold_percentage)
    - name: "Average Voting Threshold Percentage"
      expr: AVG(voting_threshold_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_committee_policy_governance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Committee Policy Governance business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`committee_policy_governance`"
  dimensions:
    - name: "Policy Adoption Date"
      expr: policy_adoption_date
    - name: "Committee Vote Result"
      expr: committee_vote_result
    - name: "Effective Date"
      expr: effective_date
    - name: "Review Frequency"
      expr: review_frequency
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Governance Status"
      expr: governance_status
    - name: "Governance Scope Notes"
      expr: governance_scope_notes
    - name: "Last Review Date"
      expr: last_review_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Policy Adoption Date Month"
      expr: DATE_TRUNC('MONTH', policy_adoption_date)
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Committee Policy Governance"
      expr: COUNT(DISTINCT committee_policy_governance_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_committee_review`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Committee Review business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`committee_review`"
  dimensions:
    - name: "Meeting Date"
      expr: meeting_date
    - name: "Review Date"
      expr: review_date
    - name: "Decision"
      expr: decision
    - name: "Approval Effective Date"
      expr: approval_effective_date
    - name: "Approval Expiration Date"
      expr: approval_expiration_date
    - name: "Conditions Of Approval"
      expr: conditions_of_approval
    - name: "Denial Reason"
      expr: denial_reason
    - name: "Deferral Reason"
      expr: deferral_reason
    - name: "Review Status"
      expr: review_status
    - name: "Primary Source Verification Complete"
      expr: primary_source_verification_complete
    - name: "License Verification Status"
      expr: license_verification_status
    - name: "Board Certification Verification Status"
      expr: board_certification_verification_status
    - name: "Malpractice Insurance Verification Status"
      expr: malpractice_insurance_verification_status
    - name: "Dea Verification Status"
      expr: dea_verification_status
    - name: "Caqh Data Reviewed"
      expr: caqh_data_reviewed
    - name: "Oig Exclusion Screening Status"
      expr: oig_exclusion_screening_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Committee Review"
      expr: COUNT(DISTINCT committee_review_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credential`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credential business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credential`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Type"
      expr: type
    - name: "Application Date"
      expr: application_date
    - name: "Application Received Date"
      expr: application_received_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Next Recredential Date"
      expr: next_recredential_date
    - name: "Approval Date"
      expr: approval_date
    - name: "Denial Date"
      expr: denial_date
    - name: "Suspension Date"
      expr: suspension_date
    - name: "Caqh Attestation Date"
      expr: caqh_attestation_date
    - name: "Caqh Authorization Flag"
      expr: caqh_authorization_flag
    - name: "Primary Source Verification Status"
      expr: primary_source_verification_status
    - name: "Primary Source Verification Date"
      expr: primary_source_verification_date
    - name: "License Verification Status"
      expr: license_verification_status
    - name: "License Verification Date"
      expr: license_verification_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credential"
      expr: COUNT(DISTINCT credential_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
    - name: "Total Quality Review Score"
      expr: SUM(quality_review_score)
    - name: "Average Quality Review Score"
      expr: AVG(quality_review_score)
    - name: "Total Compliance Review Score"
      expr: SUM(compliance_review_score)
    - name: "Average Compliance Review Score"
      expr: AVG(compliance_review_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credential_policy_acknowledgment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credential Policy Acknowledgment business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credential_policy_acknowledgment`"
  dimensions:
    - name: "Acknowledgment Date"
      expr: acknowledgment_date
    - name: "Acknowledgment Status"
      expr: acknowledgment_status
    - name: "Policy Version Acknowledged"
      expr: policy_version_acknowledged
    - name: "Attestation Signature"
      expr: attestation_signature
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Acknowledgment Method"
      expr: acknowledgment_method
    - name: "Acknowledged By Name"
      expr: acknowledged_by_name
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Acknowledgment Date Month"
      expr: DATE_TRUNC('MONTH', acknowledgment_date)
    - name: "Next Review Date Month"
      expr: DATE_TRUNC('MONTH', next_review_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credential Policy Acknowledgment"
      expr: COUNT(DISTINCT credential_policy_acknowledgment_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_application`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Application business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_application`"
  dimensions:
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Created Timestamp Month"
      expr: DATE_TRUNC('MONTH', created_timestamp)
    - name: "Last Updated Timestamp Month"
      expr: DATE_TRUNC('MONTH', last_updated_timestamp)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Application"
      expr: COUNT(DISTINCT credentialing_application_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_decision`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Decision business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_decision`"
  dimensions:
    - name: "Status"
      expr: status
    - name: "Date"
      expr: date
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Committee Review Date"
      expr: committee_review_date
    - name: "Maker Name"
      expr: maker_name
    - name: "Maker Title"
      expr: maker_title
    - name: "Rationale"
      expr: rationale
    - name: "Denial Reason Code"
      expr: denial_reason_code
    - name: "Denial Reason Description"
      expr: denial_reason_description
    - name: "Approval Conditions"
      expr: approval_conditions
    - name: "Credentialing Cycle"
      expr: credentialing_cycle
    - name: "Recredentialing Due Date"
      expr: recredentialing_due_date
    - name: "Primary Source Verification Status"
      expr: primary_source_verification_status
    - name: "License Verification Status"
      expr: license_verification_status
    - name: "License Number"
      expr: license_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Decision"
      expr: COUNT(DISTINCT credentialing_decision_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
    - name: "Total Malpractice Aggregate Amount"
      expr: SUM(malpractice_aggregate_amount)
    - name: "Average Malpractice Aggregate Amount"
      expr: AVG(malpractice_aggregate_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Quality Review Score"
      expr: SUM(quality_review_score)
    - name: "Average Quality Review Score"
      expr: AVG(quality_review_score)
    - name: "Total Compliance Review Score"
      expr: SUM(compliance_review_score)
    - name: "Average Compliance Review Score"
      expr: AVG(compliance_review_score)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_network_participation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Network Participation business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_network_participation`"
  dimensions:
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Participation Tier"
      expr: participation_tier
    - name: "Network Status"
      expr: network_status
    - name: "Accepting New Patients Flag"
      expr: accepting_new_patients_flag
    - name: "Contract Reference Number"
      expr: contract_reference_number
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "Termination Date Month"
      expr: DATE_TRUNC('MONTH', termination_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Network Participation"
      expr: COUNT(DISTINCT credentialing_network_participation_id)
    - name: "Total Reimbursement Rate Modifier"
      expr: SUM(reimbursement_rate_modifier)
    - name: "Average Reimbursement Rate Modifier"
      expr: AVG(reimbursement_rate_modifier)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_policy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Policy business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_policy`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Version"
      expr: version
    - name: "Type"
      expr: type
    - name: "Provider Type"
      expr: provider_type
    - name: "Specialty Scope"
      expr: specialty_scope
    - name: "Lob Applicability"
      expr: lob_applicability
    - name: "Status"
      expr: status
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Review Cycle Months"
      expr: review_cycle_months
    - name: "Last Review Date"
      expr: last_review_date
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Approval Date"
      expr: approval_date
    - name: "Approved By"
      expr: approved_by
    - name: "Description"
      expr: description
    - name: "Objective"
      expr: objective
    - name: "Primary Source Verification Required"
      expr: primary_source_verification_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Policy"
      expr: COUNT(DISTINCT credentialing_policy_id)
    - name: "Total Minimum Malpractice Coverage Amount"
      expr: SUM(minimum_malpractice_coverage_amount)
    - name: "Average Minimum Malpractice Coverage Amount"
      expr: AVG(minimum_malpractice_coverage_amount)
    - name: "Total Minimum Aggregate Coverage Amount"
      expr: SUM(minimum_aggregate_coverage_amount)
    - name: "Average Minimum Aggregate Coverage Amount"
      expr: AVG(minimum_aggregate_coverage_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_provider_program_participation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Provider Program Participation business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_provider_program_participation`"
  dimensions:
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Status"
      expr: status
    - name: "Participation Level"
      expr: participation_level
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Termination Reason"
      expr: termination_reason
    - name: "Accepting New Patients Flag"
      expr: accepting_new_patients_flag
    - name: "Created Date"
      expr: created_date
    - name: "Updated Date"
      expr: updated_date
    - name: "Enrollment Date Month"
      expr: DATE_TRUNC('MONTH', enrollment_date)
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Provider Program Participation"
      expr: COUNT(DISTINCT participation_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_specialist`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Specialist business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_specialist`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Last Name"
      expr: last_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Email"
      expr: email
    - name: "Phone Number"
      expr: phone_number
    - name: "Employee Number"
      expr: employee_number
    - name: "Department"
      expr: department
    - name: "Role"
      expr: role
    - name: "Status"
      expr: status
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "License Number"
      expr: license_number
    - name: "License State"
      expr: license_state
    - name: "License Expiration Date"
      expr: license_expiration_date
    - name: "Board Certifications"
      expr: board_certifications
    - name: "Malpractice Insurance Provider"
      expr: malpractice_insurance_provider
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Specialist"
      expr: COUNT(DISTINCT credentialing_specialist_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_credentialing_status`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Credentialing Status business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`credentialing_status`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Lifecycle Stage"
      expr: lifecycle_stage
    - name: "Is Active"
      expr: is_active
    - name: "Allows Claims Submission"
      expr: allows_claims_submission
    - name: "Allows Patient Assignment"
      expr: allows_patient_assignment
    - name: "Requires Committee Review"
      expr: requires_committee_review
    - name: "Requires Notification"
      expr: requires_notification
    - name: "Notification Template Code"
      expr: notification_template_code
    - name: "Is Terminal"
      expr: is_terminal
    - name: "Is Appealable"
      expr: is_appealable
    - name: "Appeal Period Days"
      expr: appeal_period_days
    - name: "Default Duration Days"
      expr: default_duration_days
    - name: "Recredentialing Cycle Months"
      expr: recredentialing_cycle_months
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Credentialing Status"
      expr: COUNT(DISTINCT credentialing_status_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_delegated_entity`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Delegated Entity business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`delegated_entity`"
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
    - name: "Credentialing Scope"
      expr: credentialing_scope
    - name: "Authority Level"
      expr: authority_level
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
    - name: "State"
      expr: state
    - name: "Postal Code"
      expr: postal_code
    - name: "Country"
      expr: country
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Delegated Entity"
      expr: COUNT(DISTINCT delegated_entity_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_document_submission`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Document Submission business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`document_submission`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Document Name"
      expr: document_name
    - name: "Document Description"
      expr: document_description
    - name: "Submission Date"
      expr: submission_date
    - name: "Submission Timestamp"
      expr: submission_timestamp
    - name: "Submission Method"
      expr: submission_method
    - name: "Submission Source"
      expr: submission_source
    - name: "Document Status"
      expr: document_status
    - name: "Review Status"
      expr: review_status
    - name: "Verification Status"
      expr: verification_status
    - name: "Verification Method"
      expr: verification_method
    - name: "Primary Source Verified Flag"
      expr: primary_source_verified_flag
    - name: "Verification Date"
      expr: verification_date
    - name: "Verified By"
      expr: verified_by
    - name: "File Name"
      expr: file_name
    - name: "File Format"
      expr: file_format
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Document Submission"
      expr: COUNT(DISTINCT document_submission_id)
    - name: "Total Coverage Amount"
      expr: SUM(coverage_amount)
    - name: "Average Coverage Amount"
      expr: AVG(coverage_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_document_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Document Type business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`document_type`"
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
    - name: "Is Required"
      expr: is_required
    - name: "Is Primary Source Verified"
      expr: is_primary_source_verified
    - name: "Verification Method"
      expr: verification_method
    - name: "Issuing Authority Type"
      expr: issuing_authority_type
    - name: "Validity Period Months"
      expr: validity_period_months
    - name: "Recredentialing Required"
      expr: recredentialing_required
    - name: "Acceptable File Formats"
      expr: acceptable_file_formats
    - name: "Retention Period Years"
      expr: retention_period_years
    - name: "Sanctions Screening Required"
      expr: sanctions_screening_required
    - name: "Caqh Data Element"
      expr: caqh_data_element
    - name: "Credentialing Committee Review"
      expr: credentialing_committee_review
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Document Type"
      expr: COUNT(DISTINCT document_type_id)
    - name: "Total Max File Size Mb"
      expr: SUM(max_file_size_mb)
    - name: "Average Max File Size Mb"
      expr: AVG(max_file_size_mb)
    - name: "Total Minimum Coverage Amount"
      expr: SUM(minimum_coverage_amount)
    - name: "Average Minimum Coverage Amount"
      expr: AVG(minimum_coverage_amount)
    - name: "Total Cost Per Verification"
      expr: SUM(cost_per_verification)
    - name: "Average Cost Per Verification"
      expr: AVG(cost_per_verification)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_expiration_notification`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Expiration Notification business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`expiration_notification`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Issuing Organization"
      expr: issuing_organization
    - name: "Issuing State"
      expr: issuing_state
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Notification Sent Timestamp"
      expr: notification_sent_timestamp
    - name: "Notification Type"
      expr: notification_type
    - name: "Notification Method"
      expr: notification_method
    - name: "Recipient Email"
      expr: recipient_email
    - name: "Recipient Phone"
      expr: recipient_phone
    - name: "Recipient Address"
      expr: recipient_address
    - name: "Days Until Expiration"
      expr: days_until_expiration
    - name: "Notification Subject"
      expr: notification_subject
    - name: "Notification Body"
      expr: notification_body
    - name: "Delivery Status"
      expr: delivery_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Expiration Notification"
      expr: COUNT(DISTINCT expiration_notification_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
    - name: "Total Notification Cost"
      expr: SUM(notification_cost)
    - name: "Average Notification Cost"
      expr: AVG(notification_cost)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_fee`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Fee business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`fee`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Credentialing Type"
      expr: credentialing_type
    - name: "Category"
      expr: category
    - name: "Currency Code"
      expr: currency_code
    - name: "Status"
      expr: status
    - name: "Payment Reference Number"
      expr: payment_reference_number
    - name: "Waiver Indicator"
      expr: waiver_indicator
    - name: "Waiver Reason"
      expr: waiver_reason
    - name: "Waiver Approved By"
      expr: waiver_approved_by
    - name: "Waiver Approval Date"
      expr: waiver_approval_date
    - name: "Refund Indicator"
      expr: refund_indicator
    - name: "Refund Date"
      expr: refund_date
    - name: "Refund Reason"
      expr: refund_reason
    - name: "Dispute Indicator"
      expr: dispute_indicator
    - name: "Dispute Date"
      expr: dispute_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Fee"
      expr: COUNT(DISTINCT fee_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Amount Paid"
      expr: SUM(amount_paid)
    - name: "Average Amount Paid"
      expr: AVG(amount_paid)
    - name: "Total Amount Outstanding"
      expr: SUM(amount_outstanding)
    - name: "Average Amount Outstanding"
      expr: AVG(amount_outstanding)
    - name: "Total Refund Amount"
      expr: SUM(refund_amount)
    - name: "Average Refund Amount"
      expr: AVG(refund_amount)
    - name: "Total Late Payment Fee Amount"
      expr: SUM(late_payment_fee_amount)
    - name: "Average Late Payment Fee Amount"
      expr: AVG(late_payment_fee_amount)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_license_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "License Type business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`license_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Profession"
      expr: profession
    - name: "Issuing Authority Type"
      expr: issuing_authority_type
    - name: "Issuing Authority Name"
      expr: issuing_authority_name
    - name: "Jurisdiction Level"
      expr: jurisdiction_level
    - name: "Requires Primary Source Verification"
      expr: requires_primary_source_verification
    - name: "Verification Method"
      expr: verification_method
    - name: "Caqh Applicable"
      expr: caqh_applicable
    - name: "Npdb Reportable"
      expr: npdb_reportable
    - name: "Requires Dea"
      expr: requires_dea
    - name: "Prescriptive Authority"
      expr: prescriptive_authority
    - name: "Scope Of Practice"
      expr: scope_of_practice
    - name: "Education Requirement"
      expr: education_requirement
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct License Type"
      expr: COUNT(DISTINCT license_type_id)
    - name: "Total Minimum Coverage Amount"
      expr: SUM(minimum_coverage_amount)
    - name: "Average Minimum Coverage Amount"
      expr: AVG(minimum_coverage_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_malpractice_insurance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Malpractice Insurance business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`malpractice_insurance`"
  dimensions:
    - name: "Policy Number"
      expr: policy_number
    - name: "Carrier Name"
      expr: carrier_name
    - name: "Carrier Naic Code"
      expr: carrier_naic_code
    - name: "Carrier Am Best Rating"
      expr: carrier_am_best_rating
    - name: "Policy Type"
      expr: policy_type
    - name: "Coverage Type"
      expr: coverage_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Retroactive Date"
      expr: retroactive_date
    - name: "Tail Coverage Indicator"
      expr: tail_coverage_indicator
    - name: "Tail Coverage Expiration Date"
      expr: tail_coverage_expiration_date
    - name: "Self Insured Indicator"
      expr: self_insured_indicator
    - name: "Certificate Number"
      expr: certificate_number
    - name: "Certificate Issue Date"
      expr: certificate_issue_date
    - name: "Certificate Holder Name"
      expr: certificate_holder_name
    - name: "Additional Insured Indicator"
      expr: additional_insured_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Malpractice Insurance"
      expr: COUNT(DISTINCT malpractice_insurance_id)
    - name: "Total Per Occurrence Limit Amount"
      expr: SUM(per_occurrence_limit_amount)
    - name: "Average Per Occurrence Limit Amount"
      expr: AVG(per_occurrence_limit_amount)
    - name: "Total Aggregate Limit Amount"
      expr: SUM(aggregate_limit_amount)
    - name: "Average Aggregate Limit Amount"
      expr: AVG(aggregate_limit_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Self Insured Retention Amount"
      expr: SUM(self_insured_retention_amount)
    - name: "Average Self Insured Retention Amount"
      expr: AVG(self_insured_retention_amount)
    - name: "Total Total Settlements Amount"
      expr: SUM(total_settlements_amount)
    - name: "Average Total Settlements Amount"
      expr: AVG(total_settlements_amount)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Minimum Per Occurrence Requirement"
      expr: SUM(minimum_per_occurrence_requirement)
    - name: "Average Minimum Per Occurrence Requirement"
      expr: AVG(minimum_per_occurrence_requirement)
    - name: "Total Minimum Aggregate Requirement"
      expr: SUM(minimum_aggregate_requirement)
    - name: "Average Minimum Aggregate Requirement"
      expr: AVG(minimum_aggregate_requirement)
    - name: "Total Total Claims Paid Amount"
      expr: SUM(total_claims_paid_amount)
    - name: "Average Total Claims Paid Amount"
      expr: AVG(total_claims_paid_amount)
    - name: "Total Minimum Required Per Occurrence Amount"
      expr: SUM(minimum_required_per_occurrence_amount)
    - name: "Average Minimum Required Per Occurrence Amount"
      expr: AVG(minimum_required_per_occurrence_amount)
    - name: "Total Minimum Required Aggregate Amount"
      expr: SUM(minimum_required_aggregate_amount)
    - name: "Average Minimum Required Aggregate Amount"
      expr: AVG(minimum_required_aggregate_amount)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_network_eligibility`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Network Eligibility business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`network_eligibility`"
  dimensions:
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Eligibility Status"
      expr: eligibility_status
    - name: "Eligibility Determination Date"
      expr: eligibility_determination_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Credentialing Committee Decision"
      expr: credentialing_committee_decision
    - name: "Credentialing Committee Review Date"
      expr: credentialing_committee_review_date
    - name: "Primary Source Verification Status"
      expr: primary_source_verification_status
    - name: "Primary Source Verification Date"
      expr: primary_source_verification_date
    - name: "License Verification Status"
      expr: license_verification_status
    - name: "License Verification Date"
      expr: license_verification_date
    - name: "Board Certification Status"
      expr: board_certification_status
    - name: "Board Certification Verification Date"
      expr: board_certification_verification_date
    - name: "Malpractice Insurance Verification Status"
      expr: malpractice_insurance_verification_status
    - name: "Malpractice Insurance Verification Date"
      expr: malpractice_insurance_verification_date
    - name: "Caqh Profile Status"
      expr: caqh_profile_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Network Eligibility"
      expr: COUNT(DISTINCT network_eligibility_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_provider_board_cert`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Provider Board Cert business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`provider_board_cert`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Certification Type"
      expr: certification_type
    - name: "Certification Number"
      expr: certification_number
    - name: "Initial Certification Date"
      expr: initial_certification_date
    - name: "Current Certification Date"
      expr: current_certification_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Recertification Due Date"
      expr: recertification_due_date
    - name: "Certification Status"
      expr: certification_status
    - name: "Is Primary Specialty"
      expr: is_primary_specialty
    - name: "Is Lifetime Certification"
      expr: is_lifetime_certification
    - name: "Moc Participation Status"
      expr: moc_participation_status
    - name: "Verification Method"
      expr: verification_method
    - name: "Verification Date"
      expr: verification_date
    - name: "Verification Status"
      expr: verification_status
    - name: "Verified By"
      expr: verified_by
    - name: "Next Verification Due Date"
      expr: next_verification_due_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Provider Board Cert"
      expr: COUNT(DISTINCT provider_board_cert_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_provider_license`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Provider License business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`provider_license`"
  dimensions:
    - name: "License Number"
      expr: license_number
    - name: "Issuing State"
      expr: issuing_state
    - name: "Issuing Authority"
      expr: issuing_authority
    - name: "Issuing Authority Contact"
      expr: issuing_authority_contact
    - name: "Original Issue Date"
      expr: original_issue_date
    - name: "Current Issue Date"
      expr: current_issue_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Renewal Date"
      expr: renewal_date
    - name: "Renewal Cycle Months"
      expr: renewal_cycle_months
    - name: "Status"
      expr: status
    - name: "Verification Status"
      expr: verification_status
    - name: "Verification Method"
      expr: verification_method
    - name: "Verification Date"
      expr: verification_date
    - name: "Verification Due Date"
      expr: verification_due_date
    - name: "Verified By"
      expr: verified_by
    - name: "Caqh Attestation Date"
      expr: caqh_attestation_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Provider License"
      expr: COUNT(DISTINCT provider_license_id)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_provider_training_completion`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Provider Training Completion business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`provider_training_completion`"
  dimensions:
    - name: "Completion Date"
      expr: completion_date
    - name: "Status"
      expr: status
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Attestation Signed"
      expr: attestation_signed
    - name: "Attestation Date"
      expr: attestation_date
    - name: "Requirement Type"
      expr: requirement_type
    - name: "Verified By"
      expr: verified_by
    - name: "Verification Date"
      expr: verification_date
    - name: "Completion Date Month"
      expr: DATE_TRUNC('MONTH', completion_date)
    - name: "Expiration Date Month"
      expr: DATE_TRUNC('MONTH', expiration_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Provider Training Completion"
      expr: COUNT(DISTINCT provider_training_completion_id)
    - name: "Total Score"
      expr: SUM(score)
    - name: "Average Score"
      expr: AVG(score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_recredentialing_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Recredentialing Event business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`recredentialing_event`"
  dimensions:
    - name: "Recredentialing Cycle Number"
      expr: recredentialing_cycle_number
    - name: "Trigger Reason"
      expr: trigger_reason
    - name: "Trigger Date"
      expr: trigger_date
    - name: "Initiated Date"
      expr: initiated_date
    - name: "Due Date"
      expr: due_date
    - name: "Completed Date"
      expr: completed_date
    - name: "Status"
      expr: status
    - name: "Outcome"
      expr: outcome
    - name: "Outcome Reason"
      expr: outcome_reason
    - name: "Outcome Effective Date"
      expr: outcome_effective_date
    - name: "Next Recredentialing Due Date"
      expr: next_recredentialing_due_date
    - name: "Caqh Attestation Date"
      expr: caqh_attestation_date
    - name: "Caqh Data Retrieved Date"
      expr: caqh_data_retrieved_date
    - name: "Primary Source Verification Status"
      expr: primary_source_verification_status
    - name: "Primary Source Verification Completed Date"
      expr: primary_source_verification_completed_date
    - name: "License Verification Status"
      expr: license_verification_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Recredentialing Event"
      expr: COUNT(DISTINCT recredentialing_event_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_recredentialing_schedule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Recredentialing Schedule business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`recredentialing_schedule`"
  dimensions:
    - name: "Provider Type Code"
      expr: provider_type_code
    - name: "Provider Type Description"
      expr: provider_type_description
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Specialty Description"
      expr: specialty_description
    - name: "Recredentialing Interval Months"
      expr: recredentialing_interval_months
    - name: "Recredentialing Frequency Description"
      expr: recredentialing_frequency_description
    - name: "Trigger Type"
      expr: trigger_type
    - name: "Advance Notification Days"
      expr: advance_notification_days
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Primary Source Verification Required Flag"
      expr: primary_source_verification_required_flag
    - name: "License Verification Required Flag"
      expr: license_verification_required_flag
    - name: "Board Certification Verification Required Flag"
      expr: board_certification_verification_required_flag
    - name: "Dea Verification Required Flag"
      expr: dea_verification_required_flag
    - name: "Malpractice Insurance Verification Required Flag"
      expr: malpractice_insurance_verification_required_flag
    - name: "Work History Verification Required Flag"
      expr: work_history_verification_required_flag
    - name: "Work History Lookback Years"
      expr: work_history_lookback_years
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Recredentialing Schedule"
      expr: COUNT(DISTINCT recredentialing_schedule_id)
    - name: "Total Malpractice Insurance Minimum Coverage Amount"
      expr: SUM(malpractice_insurance_minimum_coverage_amount)
    - name: "Average Malpractice Insurance Minimum Coverage Amount"
      expr: AVG(malpractice_insurance_minimum_coverage_amount)
    - name: "Total Malpractice Insurance Aggregate Minimum Amount"
      expr: SUM(malpractice_insurance_aggregate_minimum_amount)
    - name: "Average Malpractice Insurance Aggregate Minimum Amount"
      expr: AVG(malpractice_insurance_aggregate_minimum_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_sanction_screening`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sanction Screening business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`sanction_screening`"
  dimensions:
    - name: "Provider First Name"
      expr: provider_first_name
    - name: "Provider Last Name"
      expr: provider_last_name
    - name: "Provider Middle Name"
      expr: provider_middle_name
    - name: "Provider Suffix"
      expr: provider_suffix
    - name: "Provider Organization Name"
      expr: provider_organization_name
    - name: "Screening Date"
      expr: screening_date
    - name: "Screening Timestamp"
      expr: screening_timestamp
    - name: "Screening Type"
      expr: screening_type
    - name: "Screening Source"
      expr: screening_source
    - name: "Oig Screening Performed"
      expr: oig_screening_performed
    - name: "Oig Screening Result"
      expr: oig_screening_result
    - name: "Sam Screening Performed"
      expr: sam_screening_performed
    - name: "Sam Screening Result"
      expr: sam_screening_result
    - name: "State Medicaid Screening Performed"
      expr: state_medicaid_screening_performed
    - name: "State Medicaid Screening Result"
      expr: state_medicaid_screening_result
    - name: "Ofac Screening Performed"
      expr: ofac_screening_performed
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sanction Screening"
      expr: COUNT(DISTINCT sanction_screening_id)
    - name: "Total Match Confidence Score"
      expr: SUM(match_confidence_score)
    - name: "Average Match Confidence Score"
      expr: AVG(match_confidence_score)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_sanction_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sanction Type business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`sanction_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Severity Level"
      expr: severity_level
    - name: "Issuing Authority"
      expr: issuing_authority
    - name: "Authority Type"
      expr: authority_type
    - name: "Jurisdiction"
      expr: jurisdiction
    - name: "Screening Source"
      expr: screening_source
    - name: "Screening Frequency"
      expr: screening_frequency
    - name: "Mandatory Screening Flag"
      expr: mandatory_screening_flag
    - name: "Auto Disqualification Flag"
      expr: auto_disqualification_flag
    - name: "Committee Review Required Flag"
      expr: committee_review_required_flag
    - name: "Network Participation Impact"
      expr: network_participation_impact
    - name: "Cms Reportable Flag"
      expr: cms_reportable_flag
    - name: "State Reportable Flag"
      expr: state_reportable_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sanction Type"
      expr: COUNT(DISTINCT sanction_type_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_verification_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Verification Event business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`verification_event`"
  dimensions:
    - name: "Verification Source"
      expr: verification_source
    - name: "Verification Source Type"
      expr: verification_source_type
    - name: "Verification Method"
      expr: verification_method
    - name: "Verification Status"
      expr: verification_status
    - name: "Verification Result"
      expr: verification_result
    - name: "Verification Date"
      expr: verification_date
    - name: "Verification Timestamp"
      expr: verification_timestamp
    - name: "Verification Expiration Date"
      expr: verification_expiration_date
    - name: "Credential Number"
      expr: credential_number
    - name: "Credential Issue Date"
      expr: credential_issue_date
    - name: "Credential Expiration Date"
      expr: credential_expiration_date
    - name: "Credential Status"
      expr: credential_status
    - name: "Issuing State"
      expr: issuing_state
    - name: "Issuing Country"
      expr: issuing_country
    - name: "Specialty Board Name"
      expr: specialty_board_name
    - name: "Specialty Name"
      expr: specialty_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Verification Event"
      expr: COUNT(DISTINCT verification_event_id)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_workflow_step`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Workflow Step business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`workflow_step`"
  dimensions:
    - name: "Step Code"
      expr: step_code
    - name: "Step Name"
      expr: step_name
    - name: "Step Description"
      expr: step_description
    - name: "Step Category"
      expr: step_category
    - name: "Step Type"
      expr: step_type
    - name: "Sequence Number"
      expr: sequence_number
    - name: "Is Mandatory"
      expr: is_mandatory
    - name: "Is Ncqa Required"
      expr: is_ncqa_required
    - name: "Is Cms Required"
      expr: is_cms_required
    - name: "Is State Required"
      expr: is_state_required
    - name: "Applicable Provider Types"
      expr: applicable_provider_types
    - name: "Applicable Specialties"
      expr: applicable_specialties
    - name: "Verification Source Type"
      expr: verification_source_type
    - name: "Verification Method"
      expr: verification_method
    - name: "External System Name"
      expr: external_system_name
    - name: "External System Integration Type"
      expr: external_system_integration_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Workflow Step"
      expr: COUNT(DISTINCT workflow_step_id)
    - name: "Total Quality Threshold Percentage"
      expr: SUM(quality_threshold_percentage)
    - name: "Average Quality Threshold Percentage"
      expr: AVG(quality_threshold_percentage)
    - name: "Total Cost Per Execution"
      expr: SUM(cost_per_execution)
    - name: "Average Cost Per Execution"
      expr: AVG(cost_per_execution)
    - name: "Total Automation Percentage"
      expr: SUM(automation_percentage)
    - name: "Average Automation Percentage"
      expr: AVG(automation_percentage)
    - name: "Total Average Completion Rate Percentage"
      expr: SUM(average_completion_rate_percentage)
    - name: "Average Average Completion Rate Percentage"
      expr: AVG(average_completion_rate_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`credentialing_workflow_step_sla`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Workflow Step Sla business metrics"
  source: "`cmoore_customer_demos`.`credentialing`.`workflow_step_sla`"
  dimensions:
    - name: "Business Priority"
      expr: business_priority
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Is Active"
      expr: is_active
    - name: "Applies To Provider Types"
      expr: applies_to_provider_types
    - name: "Escalation Contact Role"
      expr: escalation_contact_role
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Modified By"
      expr: modified_by
    - name: "Sla Duration Days"
      expr: sla_duration_days
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "End Date Month"
      expr: DATE_TRUNC('MONTH', end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Workflow Step Sla"
      expr: COUNT(DISTINCT workflow_step_sla_id)
    - name: "Total Sla Target Hours"
      expr: SUM(sla_target_hours)
    - name: "Average Sla Target Hours"
      expr: AVG(sla_target_hours)
    - name: "Total Escalation Threshold"
      expr: SUM(escalation_threshold)
    - name: "Average Escalation Threshold"
      expr: AVG(escalation_threshold)
$$;