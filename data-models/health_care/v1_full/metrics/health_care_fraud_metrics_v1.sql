-- Metric views for domain: fraud | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:05:24

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_analyst`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Analyst business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`analyst`"
  dimensions:
    - name: "Full Name"
      expr: full_name
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Role"
      expr: role
    - name: "Department"
      expr: department
    - name: "Employment Status"
      expr: employment_status
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Is Active"
      expr: is_active
    - name: "Seniority Level"
      expr: seniority_level
    - name: "Fraud Expertise Area"
      expr: fraud_expertise_area
    - name: "Case Load Count"
      expr: case_load_count
    - name: "Last Case Closed Date"
      expr: last_case_closed_date
    - name: "Certification Status"
      expr: certification_status
    - name: "Certifications"
      expr: certifications
    - name: "Security Clearance Level"
      expr: security_clearance_level
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Analyst"
      expr: COUNT(DISTINCT analyst_id)
    - name: "Total Avg Case Resolution Time Days"
      expr: SUM(avg_case_resolution_time_days)
    - name: "Average Avg Case Resolution Time Days"
      expr: AVG(avg_case_resolution_time_days)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_audit_hcc_finding`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit Hcc Finding business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`audit_hcc_finding`"
  dimensions:
    - name: "Audit Finding"
      expr: audit_finding
    - name: "Validation Status"
      expr: validation_status
    - name: "Audit Date"
      expr: audit_date
    - name: "Error Type"
      expr: error_type
    - name: "Error Description"
      expr: error_description
    - name: "Corrective Action Required"
      expr: corrective_action_required
    - name: "Corrective Action Description"
      expr: corrective_action_description
    - name: "Reviewed By Cms"
      expr: reviewed_by_cms
    - name: "Cms Review Result"
      expr: cms_review_result
    - name: "Created Date"
      expr: created_date
    - name: "Updated Date"
      expr: updated_date
    - name: "Audit Date Month"
      expr: DATE_TRUNC('MONTH', audit_date)
    - name: "Created Date Month"
      expr: DATE_TRUNC('MONTH', created_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit Hcc Finding"
      expr: COUNT(DISTINCT audit_hcc_finding_id)
    - name: "Total Documentation Quality Score"
      expr: SUM(documentation_quality_score)
    - name: "Average Documentation Quality Score"
      expr: AVG(documentation_quality_score)
    - name: "Total Financial Impact"
      expr: SUM(financial_impact)
    - name: "Average Financial Impact"
      expr: AVG(financial_impact)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_audit_interaction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit Interaction business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`audit_interaction`"
  dimensions:
    - name: "Interaction Date"
      expr: interaction_date
    - name: "Interaction Type"
      expr: interaction_type
    - name: "Audit Phase"
      expr: audit_phase
    - name: "Documentation Provided"
      expr: documentation_provided
    - name: "Follow Up Required"
      expr: follow_up_required
    - name: "Interaction Date Month"
      expr: DATE_TRUNC('MONTH', interaction_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit Interaction"
      expr: COUNT(DISTINCT audit_interaction_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_auditor`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Auditor business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`auditor`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Last Name"
      expr: last_name
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Role"
      expr: role
    - name: "Department"
      expr: department
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Audit Specialty"
      expr: audit_specialty
    - name: "Certification"
      expr: certification
    - name: "Certification Expiration"
      expr: certification_expiration
    - name: "Security Clearance Level"
      expr: security_clearance_level
    - name: "Is External"
      expr: is_external
    - name: "External Company Name"
      expr: external_company_name
    - name: "Audit Capacity"
      expr: audit_capacity
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Auditor"
      expr: COUNT(DISTINCT auditor_id)
    - name: "Total Average Case Resolution Time Days"
      expr: SUM(average_case_resolution_time_days)
    - name: "Average Average Case Resolution Time Days"
      expr: AVG(average_case_resolution_time_days)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_case_note`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Case Note business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`case_note`"
  dimensions:
    - name: "Note Sequence Number"
      expr: note_sequence_number
    - name: "Note Type"
      expr: note_type
    - name: "Note Category"
      expr: note_category
    - name: "Note Subject"
      expr: note_subject
    - name: "Note Text"
      expr: note_text
    - name: "Note Status"
      expr: note_status
    - name: "Priority Level"
      expr: priority_level
    - name: "Confidentiality Level"
      expr: confidentiality_level
    - name: "Author Name"
      expr: author_name
    - name: "Author Role"
      expr: author_role
    - name: "Author Department"
      expr: author_department
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Modified By Name"
      expr: modified_by_name
    - name: "Submitted Timestamp"
      expr: submitted_timestamp
    - name: "Reviewed Timestamp"
      expr: reviewed_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Case Note"
      expr: COUNT(DISTINCT case_note_id)
    - name: "Total Claim Amount"
      expr: SUM(claim_amount)
    - name: "Average Claim Amount"
      expr: AVG(claim_amount)
    - name: "Total Potential Overpayment Amount"
      expr: SUM(potential_overpayment_amount)
    - name: "Average Potential Overpayment Amount"
      expr: AVG(potential_overpayment_amount)
    - name: "Total Recovered Amount"
      expr: SUM(recovered_amount)
    - name: "Average Recovered Amount"
      expr: AVG(recovered_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_claim_review`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Claim Review business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`claim_review`"
  dimensions:
    - name: "Claim Number"
      expr: claim_number
    - name: "Review Type"
      expr: review_type
    - name: "Review Status"
      expr: review_status
    - name: "Review Outcome"
      expr: review_outcome
    - name: "Fraud Indicator"
      expr: fraud_indicator
    - name: "Waste Indicator"
      expr: waste_indicator
    - name: "Abuse Indicator"
      expr: abuse_indicator
    - name: "Detection Method"
      expr: detection_method
    - name: "Detection Date"
      expr: detection_date
    - name: "Review Start Date"
      expr: review_start_date
    - name: "Review End Date"
      expr: review_end_date
    - name: "Review Duration Days"
      expr: review_duration_days
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Reviewer Role"
      expr: reviewer_role
    - name: "Assigned Team"
      expr: assigned_team
    - name: "Provider Npi"
      expr: provider_npi
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Claim Review"
      expr: COUNT(DISTINCT claim_review_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Claim Amount Billed"
      expr: SUM(claim_amount_billed)
    - name: "Average Claim Amount Billed"
      expr: AVG(claim_amount_billed)
    - name: "Total Claim Amount Allowed"
      expr: SUM(claim_amount_allowed)
    - name: "Average Claim Amount Allowed"
      expr: AVG(claim_amount_allowed)
    - name: "Total Claim Amount Paid"
      expr: SUM(claim_amount_paid)
    - name: "Average Claim Amount Paid"
      expr: AVG(claim_amount_paid)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Recovery Amount"
      expr: SUM(recovery_amount)
    - name: "Average Recovery Amount"
      expr: AVG(recovery_amount)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Cost Avoidance Amount"
      expr: SUM(cost_avoidance_amount)
    - name: "Average Cost Avoidance Amount"
      expr: AVG(cost_avoidance_amount)
    - name: "Total Investigation Hours"
      expr: SUM(investigation_hours)
    - name: "Average Investigation Hours"
      expr: AVG(investigation_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_fraud_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Fraud Rule business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`fraud_rule`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Code"
      expr: code
    - name: "Description"
      expr: description
    - name: "Detection Method"
      expr: detection_method
    - name: "Threshold Unit"
      expr: threshold_unit
    - name: "Threshold Period Days"
      expr: threshold_period_days
    - name: "Applicable Claim Types"
      expr: applicable_claim_types
    - name: "Applicable Service Types"
      expr: applicable_service_types
    - name: "Applicable Lob"
      expr: applicable_lob
    - name: "Applicable Provider Types"
      expr: applicable_provider_types
    - name: "Cpt Code Filter"
      expr: cpt_code_filter
    - name: "Icd10 Code Filter"
      expr: icd10_code_filter
    - name: "Drg Code Filter"
      expr: drg_code_filter
    - name: "Ndc Code Filter"
      expr: ndc_code_filter
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Fraud Rule"
      expr: COUNT(DISTINCT fraud_rule_id)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Estimated Annual Savings"
      expr: SUM(estimated_annual_savings)
    - name: "Average Estimated Annual Savings"
      expr: AVG(estimated_annual_savings)
    - name: "Total False Positive Rate"
      expr: SUM(false_positive_rate)
    - name: "Average False Positive Rate"
      expr: AVG(false_positive_rate)
    - name: "Total True Positive Rate"
      expr: SUM(true_positive_rate)
    - name: "Average True Positive Rate"
      expr: AVG(true_positive_rate)
    - name: "Total Confidence Threshold"
      expr: SUM(confidence_threshold)
    - name: "Average Confidence Threshold"
      expr: AVG(confidence_threshold)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_investigation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Investigation business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`investigation`"
  dimensions:
    - name: "Case Number"
      expr: case_number
    - name: "Priority"
      expr: priority
    - name: "Status"
      expr: status
    - name: "Opened Date"
      expr: opened_date
    - name: "Opened Timestamp"
      expr: opened_timestamp
    - name: "Assigned Date"
      expr: assigned_date
    - name: "Closed Date"
      expr: closed_date
    - name: "Closed Timestamp"
      expr: closed_timestamp
    - name: "Target Date"
      expr: target_date
    - name: "Lead Investigator Name"
      expr: lead_investigator_name
    - name: "Assigned Team"
      expr: assigned_team
    - name: "Source Type"
      expr: source_type
    - name: "Source Reference Number"
      expr: source_reference_number
    - name: "Allegation Summary"
      expr: allegation_summary
    - name: "Allegation Details"
      expr: allegation_details
    - name: "Subject Type"
      expr: subject_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Investigation"
      expr: COUNT(DISTINCT investigation_id)
    - name: "Total Estimated Loss Amount"
      expr: SUM(estimated_loss_amount)
    - name: "Average Estimated Loss Amount"
      expr: AVG(estimated_loss_amount)
    - name: "Total Confirmed Loss Amount"
      expr: SUM(confirmed_loss_amount)
    - name: "Average Confirmed Loss Amount"
      expr: AVG(confirmed_loss_amount)
    - name: "Total Recovered Amount"
      expr: SUM(recovered_amount)
    - name: "Average Recovered Amount"
      expr: AVG(recovered_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Investigator Hours"
      expr: SUM(investigator_hours)
    - name: "Average Investigator Hours"
      expr: AVG(investigator_hours)
    - name: "Total Cost"
      expr: SUM(cost)
    - name: "Average Cost"
      expr: AVG(cost)
    - name: "Total Return On Investment"
      expr: SUM(return_on_investment)
    - name: "Average Return On Investment"
      expr: AVG(return_on_investment)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_investigation_audit`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Investigation Audit business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`investigation_audit`"
  dimensions:
    - name: "Scope"
      expr: scope
    - name: "Date"
      expr: date
    - name: "Findings"
      expr: findings
    - name: "Auditor Assigned"
      expr: auditor_assigned
    - name: "Review Status"
      expr: review_status
    - name: "Sample Selection Reason"
      expr: sample_selection_reason
    - name: "Compliance Rating"
      expr: compliance_rating
    - name: "Remediation Required"
      expr: remediation_required
    - name: "Remediation Due Date"
      expr: remediation_due_date
    - name: "Remediation Completed Date"
      expr: remediation_completed_date
    - name: "Date Month"
      expr: DATE_TRUNC('MONTH', date)
    - name: "Remediation Due Date Month"
      expr: DATE_TRUNC('MONTH', remediation_due_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Investigation Audit"
      expr: COUNT(DISTINCT investigation_audit_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_investigation_program_scope`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Investigation Program Scope business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`investigation_program_scope`"
  dimensions:
    - name: "Start Date"
      expr: start_date
    - name: "Scope"
      expr: scope
    - name: "Program Specific Violations"
      expr: program_specific_violations
    - name: "Status"
      expr: status
    - name: "Assigned Investigator"
      expr: assigned_investigator
    - name: "Findings Summary"
      expr: findings_summary
    - name: "Closed Date"
      expr: closed_date
    - name: "Start Date Month"
      expr: DATE_TRUNC('MONTH', start_date)
    - name: "Closed Date Month"
      expr: DATE_TRUNC('MONTH', closed_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Investigation Program Scope"
      expr: COUNT(DISTINCT investigation_program_scope_id)
    - name: "Total Estimated Program Loss Amount"
      expr: SUM(estimated_program_loss_amount)
    - name: "Average Estimated Program Loss Amount"
      expr: AVG(estimated_program_loss_amount)
    - name: "Total Confirmed Program Loss Amount"
      expr: SUM(confirmed_program_loss_amount)
    - name: "Average Confirmed Program Loss Amount"
      expr: AVG(confirmed_program_loss_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_investigator`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Investigator business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`investigator`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Last Name"
      expr: last_name
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Role"
      expr: role
    - name: "Department"
      expr: department
    - name: "Office Code"
      expr: office_code
    - name: "Clearance Level"
      expr: clearance_level
    - name: "Background Check Status"
      expr: background_check_status
    - name: "Background Check Date"
      expr: background_check_date
    - name: "Certification"
      expr: certification
    - name: "Years Of Experience"
      expr: years_of_experience
    - name: "Specialty Areas"
      expr: specialty_areas
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Investigator"
      expr: COUNT(DISTINCT investigator_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_law_enforcement_referral`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Law Enforcement Referral business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`law_enforcement_referral`"
  dimensions:
    - name: "Referral Number"
      expr: referral_number
    - name: "Referral Date"
      expr: referral_date
    - name: "Referral Timestamp"
      expr: referral_timestamp
    - name: "Agency Name"
      expr: agency_name
    - name: "Agency Type"
      expr: agency_type
    - name: "Agency Jurisdiction"
      expr: agency_jurisdiction
    - name: "Agency Contact Name"
      expr: agency_contact_name
    - name: "Agency Contact Title"
      expr: agency_contact_title
    - name: "Agency Contact Phone"
      expr: agency_contact_phone
    - name: "Agency Contact Email"
      expr: agency_contact_email
    - name: "Agency Case Number"
      expr: agency_case_number
    - name: "Referral Reason"
      expr: referral_reason
    - name: "Referral Description"
      expr: referral_description
    - name: "Affected Member Count"
      expr: affected_member_count
    - name: "Affected Claim Count"
      expr: affected_claim_count
    - name: "Suspected Provider Npi"
      expr: suspected_provider_npi
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Law Enforcement Referral"
      expr: COUNT(DISTINCT law_enforcement_referral_id)
    - name: "Total Estimated Loss Amount"
      expr: SUM(estimated_loss_amount)
    - name: "Average Estimated Loss Amount"
      expr: AVG(estimated_loss_amount)
    - name: "Total Confirmed Loss Amount"
      expr: SUM(confirmed_loss_amount)
    - name: "Average Confirmed Loss Amount"
      expr: AVG(confirmed_loss_amount)
    - name: "Total Recovery Amount"
      expr: SUM(recovery_amount)
    - name: "Average Recovery Amount"
      expr: AVG(recovery_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Restitution Amount"
      expr: SUM(restitution_amount)
    - name: "Average Restitution Amount"
      expr: AVG(restitution_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_member_sanction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Member Sanction business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`member_sanction`"
  dimensions:
    - name: "Sanction Type Code"
      expr: sanction_type_code
    - name: "Sanction Status"
      expr: sanction_status
    - name: "Investigation Finding Code"
      expr: investigation_finding_code
    - name: "Violation Description"
      expr: violation_description
    - name: "End Date"
      expr: end_date
    - name: "Duration Days"
      expr: duration_days
    - name: "Is Permanent"
      expr: is_permanent
    - name: "Imposed By Department"
      expr: imposed_by_department
    - name: "Imposed Timestamp"
      expr: imposed_timestamp
    - name: "Approved Timestamp"
      expr: approved_timestamp
    - name: "Notification Sent Date"
      expr: notification_sent_date
    - name: "Notification Method"
      expr: notification_method
    - name: "Appeal Filed Date"
      expr: appeal_filed_date
    - name: "Appeal Status"
      expr: appeal_status
    - name: "Appeal Decision Date"
      expr: appeal_decision_date
    - name: "Appeal Outcome"
      expr: appeal_outcome
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Member Sanction"
      expr: COUNT(DISTINCT member_sanction_id)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Recovery Amount"
      expr: SUM(recovery_amount)
    - name: "Average Recovery Amount"
      expr: AVG(recovery_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_overpayment_recovery`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Overpayment Recovery business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`overpayment_recovery`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Recovery Method"
      expr: recovery_method
    - name: "Recovery Status"
      expr: recovery_status
    - name: "Detection Method"
      expr: detection_method
    - name: "Detection Date"
      expr: detection_date
    - name: "Notification Date"
      expr: notification_date
    - name: "Demand Letter Date"
      expr: demand_letter_date
    - name: "First Recovery Date"
      expr: first_recovery_date
    - name: "Last Recovery Date"
      expr: last_recovery_date
    - name: "Closed Date"
      expr: closed_date
    - name: "Appeal Filed Date"
      expr: appeal_filed_date
    - name: "Appeal Decision Date"
      expr: appeal_decision_date
    - name: "Appeal Status"
      expr: appeal_status
    - name: "Appeal Outcome"
      expr: appeal_outcome
    - name: "Original Claim Paid Date"
      expr: original_claim_paid_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Overpayment Recovery"
      expr: COUNT(DISTINCT overpayment_recovery_id)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Recovered Amount"
      expr: SUM(recovered_amount)
    - name: "Average Recovered Amount"
      expr: AVG(recovered_amount)
    - name: "Total Outstanding Amount"
      expr: SUM(outstanding_amount)
    - name: "Average Outstanding Amount"
      expr: AVG(outstanding_amount)
    - name: "Total Interest Amount"
      expr: SUM(interest_amount)
    - name: "Average Interest Amount"
      expr: AVG(interest_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Original Paid Amount"
      expr: SUM(original_paid_amount)
    - name: "Average Original Paid Amount"
      expr: AVG(original_paid_amount)
    - name: "Total Correct Paid Amount"
      expr: SUM(correct_paid_amount)
    - name: "Average Correct Paid Amount"
      expr: AVG(correct_paid_amount)
    - name: "Total Installment Amount"
      expr: SUM(installment_amount)
    - name: "Average Installment Amount"
      expr: AVG(installment_amount)
    - name: "Total Settlement Amount"
      expr: SUM(settlement_amount)
    - name: "Average Settlement Amount"
      expr: AVG(settlement_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_payment_adjustment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Adjustment business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`payment_adjustment`"
  dimensions:
    - name: "Claim Number"
      expr: claim_number
    - name: "Adjustment Date"
      expr: adjustment_date
    - name: "Adjustment Timestamp"
      expr: adjustment_timestamp
    - name: "Adjustment Type"
      expr: adjustment_type
    - name: "Adjustment Reason Code"
      expr: adjustment_reason_code
    - name: "Adjustment Reason Description"
      expr: adjustment_reason_description
    - name: "Fraud Case Number"
      expr: fraud_case_number
    - name: "Currency Code"
      expr: currency_code
    - name: "Recovery Method"
      expr: recovery_method
    - name: "Recovery Status"
      expr: recovery_status
    - name: "Recovery Start Date"
      expr: recovery_start_date
    - name: "Recovery Completion Date"
      expr: recovery_completion_date
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Member Number"
      expr: member_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Adjustment"
      expr: COUNT(DISTINCT payment_adjustment_id)
    - name: "Total Original Payment Amount"
      expr: SUM(original_payment_amount)
    - name: "Average Original Payment Amount"
      expr: AVG(original_payment_amount)
    - name: "Total Adjusted Amount"
      expr: SUM(adjusted_amount)
    - name: "Average Adjusted Amount"
      expr: AVG(adjusted_amount)
    - name: "Total Net Payment Amount"
      expr: SUM(net_payment_amount)
    - name: "Average Net Payment Amount"
      expr: AVG(net_payment_amount)
    - name: "Total Amount Recovered"
      expr: SUM(amount_recovered)
    - name: "Average Amount Recovered"
      expr: AVG(amount_recovered)
    - name: "Total Amount Outstanding"
      expr: SUM(amount_outstanding)
    - name: "Average Amount Outstanding"
      expr: AVG(amount_outstanding)
    - name: "Total Interest Amount"
      expr: SUM(interest_amount)
    - name: "Average Interest Amount"
      expr: AVG(interest_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Total Recovery Amount"
      expr: SUM(total_recovery_amount)
    - name: "Average Total Recovery Amount"
      expr: AVG(total_recovery_amount)
    - name: "Total Payment Integrity Score"
      expr: SUM(payment_integrity_score)
    - name: "Average Payment Integrity Score"
      expr: AVG(payment_integrity_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_payment_hold`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Hold business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`payment_hold`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Hold Type"
      expr: hold_type
    - name: "Hold Reason Code"
      expr: hold_reason_code
    - name: "Hold Reason Description"
      expr: hold_reason_description
    - name: "Hold Status"
      expr: hold_status
    - name: "Hold Placed Date"
      expr: hold_placed_date
    - name: "Hold Placed Timestamp"
      expr: hold_placed_timestamp
    - name: "Hold Released Date"
      expr: hold_released_date
    - name: "Hold Released Timestamp"
      expr: hold_released_timestamp
    - name: "Expected Resolution Date"
      expr: expected_resolution_date
    - name: "Hold Duration Days"
      expr: hold_duration_days
    - name: "Siu Case Number"
      expr: siu_case_number
    - name: "Investigator Name"
      expr: investigator_name
    - name: "Fraud Indicator Flags"
      expr: fraud_indicator_flags
    - name: "Release Criteria"
      expr: release_criteria
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Hold"
      expr: COUNT(DISTINCT payment_hold_id)
    - name: "Total Hold Amount"
      expr: SUM(hold_amount)
    - name: "Average Hold Amount"
      expr: AVG(hold_amount)
    - name: "Total Original Payment Amount"
      expr: SUM(original_payment_amount)
    - name: "Average Original Payment Amount"
      expr: AVG(original_payment_amount)
    - name: "Total Released Amount"
      expr: SUM(released_amount)
    - name: "Average Released Amount"
      expr: AVG(released_amount)
    - name: "Total Remaining Hold Amount"
      expr: SUM(remaining_hold_amount)
    - name: "Average Remaining Hold Amount"
      expr: AVG(remaining_hold_amount)
    - name: "Total Fraud Risk Score"
      expr: SUM(fraud_risk_score)
    - name: "Average Fraud Risk Score"
      expr: AVG(fraud_risk_score)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_policy_violation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Policy Violation business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`policy_violation`"
  dimensions:
    - name: "Violation Date"
      expr: violation_date
    - name: "Violation Severity"
      expr: violation_severity
    - name: "Policy Section Violated"
      expr: policy_section_violated
    - name: "Finding"
      expr: finding
    - name: "Identified Timestamp"
      expr: identified_timestamp
    - name: "Remediation Required Flag"
      expr: remediation_required_flag
    - name: "Reported To Regulator Flag"
      expr: reported_to_regulator_flag
    - name: "Reported Date"
      expr: reported_date
    - name: "Violation Date Month"
      expr: DATE_TRUNC('MONTH', violation_date)
    - name: "Identified Timestamp Month"
      expr: DATE_TRUNC('MONTH', identified_timestamp)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Policy Violation"
      expr: COUNT(DISTINCT policy_violation_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_provider_audit`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Provider Audit business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`provider_audit`"
  dimensions:
    - name: "Audit Number"
      expr: audit_number
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Provider Type"
      expr: provider_type
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Audit Type"
      expr: audit_type
    - name: "Audit Scope"
      expr: audit_scope
    - name: "Audit Reason"
      expr: audit_reason
    - name: "Audit Status"
      expr: audit_status
    - name: "Initiated Date"
      expr: initiated_date
    - name: "Scheduled Start Date"
      expr: scheduled_start_date
    - name: "Actual Start Date"
      expr: actual_start_date
    - name: "Scheduled Completion Date"
      expr: scheduled_completion_date
    - name: "Actual Completion Date"
      expr: actual_completion_date
    - name: "Closed Date"
      expr: closed_date
    - name: "Audit Period Start Date"
      expr: audit_period_start_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Provider Audit"
      expr: COUNT(DISTINCT provider_audit_id)
    - name: "Total Error Rate Percentage"
      expr: SUM(error_rate_percentage)
    - name: "Average Error Rate Percentage"
      expr: AVG(error_rate_percentage)
    - name: "Total Total Billed Amount"
      expr: SUM(total_billed_amount)
    - name: "Average Total Billed Amount"
      expr: AVG(total_billed_amount)
    - name: "Total Total Paid Amount"
      expr: SUM(total_paid_amount)
    - name: "Average Total Paid Amount"
      expr: AVG(total_paid_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Underpayment Amount"
      expr: SUM(underpayment_amount)
    - name: "Average Underpayment Amount"
      expr: AVG(underpayment_amount)
    - name: "Total Projected Overpayment Amount"
      expr: SUM(projected_overpayment_amount)
    - name: "Average Projected Overpayment Amount"
      expr: AVG(projected_overpayment_amount)
    - name: "Total Recovered Amount"
      expr: SUM(recovered_amount)
    - name: "Average Recovered Amount"
      expr: AVG(recovered_amount)
    - name: "Total Outstanding Recovery Amount"
      expr: SUM(outstanding_recovery_amount)
    - name: "Average Outstanding Recovery Amount"
      expr: AVG(outstanding_recovery_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_provider_sanction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Provider Sanction business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`provider_sanction`"
  dimensions:
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Type"
      expr: provider_type
    - name: "Provider Specialty"
      expr: provider_specialty
    - name: "Sanction Type"
      expr: sanction_type
    - name: "Sanction Subtype"
      expr: sanction_subtype
    - name: "Sanction Status"
      expr: sanction_status
    - name: "Violation Description"
      expr: violation_description
    - name: "Sanction Effective Date"
      expr: sanction_effective_date
    - name: "Sanction End Date"
      expr: sanction_end_date
    - name: "Sanction Duration Days"
      expr: sanction_duration_days
    - name: "Reinstatement Eligible Flag"
      expr: reinstatement_eligible_flag
    - name: "Reinstatement Criteria"
      expr: reinstatement_criteria
    - name: "Reinstatement Date"
      expr: reinstatement_date
    - name: "Appeal Filed Flag"
      expr: appeal_filed_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Provider Sanction"
      expr: COUNT(DISTINCT provider_sanction_id)
    - name: "Total Monetary Penalty Amount"
      expr: SUM(monetary_penalty_amount)
    - name: "Average Monetary Penalty Amount"
      expr: AVG(monetary_penalty_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Recovered Amount"
      expr: SUM(recovered_amount)
    - name: "Average Recovered Amount"
      expr: AVG(recovered_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_recovery_action`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Recovery Action business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`recovery_action`"
  dimensions:
    - name: "Case Number"
      expr: case_number
    - name: "Claim Number"
      expr: claim_number
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Action Type"
      expr: action_type
    - name: "Action Status"
      expr: action_status
    - name: "Action Reason Code"
      expr: action_reason_code
    - name: "Action Reason Description"
      expr: action_reason_description
    - name: "Currency Code"
      expr: currency_code
    - name: "Initiated Date"
      expr: initiated_date
    - name: "Approved Date"
      expr: approved_date
    - name: "Notification Sent Date"
      expr: notification_sent_date
    - name: "Response Due Date"
      expr: response_due_date
    - name: "Payment Due Date"
      expr: payment_due_date
    - name: "First Collection Date"
      expr: first_collection_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Recovery Action"
      expr: COUNT(DISTINCT recovery_action_id)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Recovery Amount Requested"
      expr: SUM(recovery_amount_requested)
    - name: "Average Recovery Amount Requested"
      expr: AVG(recovery_amount_requested)
    - name: "Total Recovery Amount Collected"
      expr: SUM(recovery_amount_collected)
    - name: "Average Recovery Amount Collected"
      expr: AVG(recovery_amount_collected)
    - name: "Total Interest Amount"
      expr: SUM(interest_amount)
    - name: "Average Interest Amount"
      expr: AVG(interest_amount)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Administrative Fee"
      expr: SUM(administrative_fee)
    - name: "Average Administrative Fee"
      expr: AVG(administrative_fee)
    - name: "Total Installment Amount"
      expr: SUM(installment_amount)
    - name: "Average Installment Amount"
      expr: AVG(installment_amount)
    - name: "Total Settlement Amount"
      expr: SUM(settlement_amount)
    - name: "Average Settlement Amount"
      expr: AVG(settlement_amount)
    - name: "Total Judgment Amount"
      expr: SUM(judgment_amount)
    - name: "Average Judgment Amount"
      expr: AVG(judgment_amount)
    - name: "Total Write Off Amount"
      expr: SUM(write_off_amount)
    - name: "Average Write Off Amount"
      expr: AVG(write_off_amount)
    - name: "Total Recovery Likelihood Score"
      expr: SUM(recovery_likelihood_score)
    - name: "Average Recovery Likelihood Score"
      expr: AVG(recovery_likelihood_score)
    - name: "Total Error Rate Percentage"
      expr: SUM(error_rate_percentage)
    - name: "Average Error Rate Percentage"
      expr: AVG(error_rate_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_reviewer`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Reviewer business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`reviewer`"
  dimensions:
    - name: "Full Name"
      expr: full_name
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Role"
      expr: role
    - name: "Department"
      expr: department
    - name: "Status"
      expr: status
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Reviewer Type"
      expr: reviewer_type
    - name: "Level"
      expr: level
    - name: "Expertise Area"
      expr: expertise_area
    - name: "Certification Status"
      expr: certification_status
    - name: "Clearance Level"
      expr: clearance_level
    - name: "Work Location"
      expr: work_location
    - name: "Country Code"
      expr: country_code
    - name: "Created Timestamp"
      expr: created_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Reviewer"
      expr: COUNT(DISTINCT reviewer_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_rule_violation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Rule Violation business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`rule_violation`"
  dimensions:
    - name: "Transaction Type"
      expr: transaction_type
    - name: "Violation Timestamp"
      expr: violation_timestamp
    - name: "Violation Date"
      expr: violation_date
    - name: "Violation Status"
      expr: violation_status
    - name: "Violation Description"
      expr: violation_description
    - name: "Claim Number"
      expr: claim_number
    - name: "Claim Line Number"
      expr: claim_line_number
    - name: "Service Date"
      expr: service_date
    - name: "Service From Date"
      expr: service_from_date
    - name: "Service To Date"
      expr: service_to_date
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Type"
      expr: provider_type
    - name: "Provider Specialty"
      expr: provider_specialty
    - name: "Group Number"
      expr: group_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Rule Violation"
      expr: COUNT(DISTINCT rule_violation_id)
    - name: "Total Violation Amount"
      expr: SUM(violation_amount)
    - name: "Average Violation Amount"
      expr: AVG(violation_amount)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Actual Value"
      expr: SUM(actual_value)
    - name: "Average Actual Value"
      expr: AVG(actual_value)
    - name: "Total Variance Amount"
      expr: SUM(variance_amount)
    - name: "Average Variance Amount"
      expr: AVG(variance_amount)
    - name: "Total Variance Percentage"
      expr: SUM(variance_percentage)
    - name: "Average Variance Percentage"
      expr: AVG(variance_percentage)
    - name: "Total Billed Amount"
      expr: SUM(billed_amount)
    - name: "Average Billed Amount"
      expr: AVG(billed_amount)
    - name: "Total Allowed Amount"
      expr: SUM(allowed_amount)
    - name: "Average Allowed Amount"
      expr: AVG(allowed_amount)
    - name: "Total Paid Amount"
      expr: SUM(paid_amount)
    - name: "Average Paid Amount"
      expr: AVG(paid_amount)
    - name: "Total Expected Amount"
      expr: SUM(expected_amount)
    - name: "Average Expected Amount"
      expr: AVG(expected_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Confidence Score"
      expr: SUM(confidence_score)
    - name: "Average Confidence Score"
      expr: AVG(confidence_score)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_severity_level`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Severity Level business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`severity_level`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Priority Rank"
      expr: priority_rank
    - name: "Response Time Hours"
      expr: response_time_hours
    - name: "Resolution Time Hours"
      expr: resolution_time_hours
    - name: "Escalation Required Flag"
      expr: escalation_required_flag
    - name: "Law Enforcement Referral Flag"
      expr: law_enforcement_referral_flag
    - name: "Color Code"
      expr: color_code
    - name: "Notification Template"
      expr: notification_template
    - name: "Investigation Team Assignment"
      expr: investigation_team_assignment
    - name: "Approval Authority Level"
      expr: approval_authority_level
    - name: "Documentation Requirements"
      expr: documentation_requirements
    - name: "Regulatory Reporting Required Flag"
      expr: regulatory_reporting_required_flag
    - name: "Audit Trail Retention Years"
      expr: audit_trail_retention_years
    - name: "Status"
      expr: status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Severity Level"
      expr: COUNT(DISTINCT severity_level_id)
    - name: "Total Financial Threshold Minimum"
      expr: SUM(financial_threshold_minimum)
    - name: "Average Financial Threshold Minimum"
      expr: AVG(financial_threshold_minimum)
    - name: "Total Financial Threshold Maximum"
      expr: SUM(financial_threshold_maximum)
    - name: "Average Financial Threshold Maximum"
      expr: AVG(financial_threshold_maximum)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_siu_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Siu Assignment business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`siu_assignment`"
  dimensions:
    - name: "Case Number"
      expr: case_number
    - name: "Detection Method"
      expr: detection_method
    - name: "Source System"
      expr: source_system
    - name: "Provider Name"
      expr: provider_name
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Address"
      expr: member_address
    - name: "Member Ssn"
      expr: member_ssn
    - name: "Assignment Date"
      expr: assignment_date
    - name: "Assignment Timestamp"
      expr: assignment_timestamp
    - name: "Analyst Name"
      expr: analyst_name
    - name: "Analyst Role"
      expr: analyst_role
    - name: "Team Name"
      expr: team_name
    - name: "Due Date"
      expr: due_date
    - name: "Due Timestamp"
      expr: due_timestamp
    - name: "Outcome"
      expr: outcome
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Siu Assignment"
      expr: COUNT(DISTINCT siu_assignment_id)
    - name: "Total Recovery Amount"
      expr: SUM(recovery_amount)
    - name: "Average Recovery Amount"
      expr: AVG(recovery_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Pending Recovery Amount"
      expr: SUM(pending_recovery_amount)
    - name: "Average Pending Recovery Amount"
      expr: AVG(pending_recovery_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_transaction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Transaction business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`transaction`"
  dimensions:
    - name: "Transaction Date"
      expr: transaction_date
    - name: "Transaction Timestamp"
      expr: transaction_timestamp
    - name: "Transaction Type"
      expr: transaction_type
    - name: "Transaction Status"
      expr: transaction_status
    - name: "Currency Code"
      expr: currency_code
    - name: "Provider Name"
      expr: provider_name
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Address"
      expr: member_address
    - name: "Claim Number"
      expr: claim_number
    - name: "Service Code"
      expr: service_code
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Place Of Service"
      expr: place_of_service
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Channel"
      expr: payment_channel
    - name: "Is Suspected Fraud"
      expr: is_suspected_fraud
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Transaction"
      expr: COUNT(DISTINCT transaction_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Fraud Score"
      expr: SUM(fraud_score)
    - name: "Average Fraud Score"
      expr: AVG(fraud_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`fraud_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Type business metrics"
  source: "`cmoore_customer_demos`.`fraud`.`type`"
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
    - name: "Severity Level"
      expr: severity_level
    - name: "Fwa Classification"
      expr: fwa_classification
    - name: "Detection Method"
      expr: detection_method
    - name: "Typical Indicators"
      expr: typical_indicators
    - name: "Claim Type Applicability"
      expr: claim_type_applicability
    - name: "Lob Applicability"
      expr: lob_applicability
    - name: "Provider Specialty Risk"
      expr: provider_specialty_risk
    - name: "Investigation Priority"
      expr: investigation_priority
    - name: "Requires Law Enforcement Referral"
      expr: requires_law_enforcement_referral
    - name: "Statute Of Limitations Years"
      expr: statute_of_limitations_years
    - name: "Recovery Method"
      expr: recovery_method
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Type"
      expr: COUNT(DISTINCT type_id)
    - name: "Total Average Financial Impact"
      expr: SUM(average_financial_impact)
    - name: "Average Average Financial Impact"
      expr: AVG(average_financial_impact)
    - name: "Total Mandatory Reporting Threshold"
      expr: SUM(mandatory_reporting_threshold)
    - name: "Average Mandatory Reporting Threshold"
      expr: AVG(mandatory_reporting_threshold)
    - name: "Total Historical Prevalence Rate"
      expr: SUM(historical_prevalence_rate)
    - name: "Average Historical Prevalence Rate"
      expr: AVG(historical_prevalence_rate)
    - name: "Total Conviction Rate"
      expr: SUM(conviction_rate)
    - name: "Average Conviction Rate"
      expr: AVG(conviction_rate)
$$;