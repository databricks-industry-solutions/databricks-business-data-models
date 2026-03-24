-- Metric views for domain: care | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:04:23

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_assessment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Assessment business metrics"
  source: "`cmoore_customer_demos`.`care`.`assessment`"
  dimensions:
    - name: "Date"
      expr: date
    - name: "Start Timestamp"
      expr: start_timestamp
    - name: "End Timestamp"
      expr: end_timestamp
    - name: "Status"
      expr: status
    - name: "Method"
      expr: method
    - name: "Setting"
      expr: setting
    - name: "Assessor Name"
      expr: assessor_name
    - name: "Assessor Type"
      expr: assessor_type
    - name: "Assessor Npi"
      expr: assessor_npi
    - name: "Score Interpretation"
      expr: score_interpretation
    - name: "Risk Level"
      expr: risk_level
    - name: "Risk Category"
      expr: risk_category
    - name: "Hcc Codes"
      expr: hcc_codes
    - name: "Primary Diagnosis Code"
      expr: primary_diagnosis_code
    - name: "Primary Diagnosis Description"
      expr: primary_diagnosis_description
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Assessment"
      expr: COUNT(DISTINCT assessment_id)
    - name: "Total Total Score"
      expr: SUM(total_score)
    - name: "Average Total Score"
      expr: AVG(total_score)
    - name: "Total Raf Score"
      expr: SUM(raf_score)
    - name: "Average Raf Score"
      expr: AVG(raf_score)
    - name: "Total Completion Percentage"
      expr: SUM(completion_percentage)
    - name: "Average Completion Percentage"
      expr: AVG(completion_percentage)
    - name: "Total Adl Score"
      expr: SUM(adl_score)
    - name: "Average Adl Score"
      expr: AVG(adl_score)
    - name: "Total Iadl Score"
      expr: SUM(iadl_score)
    - name: "Average Iadl Score"
      expr: AVG(iadl_score)
    - name: "Total Depression Screening Score"
      expr: SUM(depression_screening_score)
    - name: "Average Depression Screening Score"
      expr: AVG(depression_screening_score)
    - name: "Total Fall Risk Score"
      expr: SUM(fall_risk_score)
    - name: "Average Fall Risk Score"
      expr: AVG(fall_risk_score)
    - name: "Total Medication Adherence Score"
      expr: SUM(medication_adherence_score)
    - name: "Average Medication Adherence Score"
      expr: AVG(medication_adherence_score)
    - name: "Total Hospitalization Risk Score"
      expr: SUM(hospitalization_risk_score)
    - name: "Average Hospitalization Risk Score"
      expr: AVG(hospitalization_risk_score)
    - name: "Total Emergency Department Risk Score"
      expr: SUM(emergency_department_risk_score)
    - name: "Average Emergency Department Risk Score"
      expr: AVG(emergency_department_risk_score)
    - name: "Total Readmission Risk Score"
      expr: SUM(readmission_risk_score)
    - name: "Average Readmission Risk Score"
      expr: AVG(readmission_risk_score)
    - name: "Total Data Quality Score"
      expr: SUM(data_quality_score)
    - name: "Average Data Quality Score"
      expr: AVG(data_quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_assessment_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Assessment Type business metrics"
  source: "`cmoore_customer_demos`.`care`.`assessment_type`"
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
    - name: "Clinical Domain"
      expr: clinical_domain
    - name: "Scoring Methodology"
      expr: scoring_methodology
    - name: "Interpretation Guidance"
      expr: interpretation_guidance
    - name: "Risk Stratification Enabled"
      expr: risk_stratification_enabled
    - name: "Standard Code System"
      expr: standard_code_system
    - name: "Standard Code"
      expr: standard_code
    - name: "Standard Code Description"
      expr: standard_code_description
    - name: "Administration Method"
      expr: administration_method
    - name: "Target Population"
      expr: target_population
    - name: "Age Range Min"
      expr: age_range_min
    - name: "Age Range Max"
      expr: age_range_max
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Assessment Type"
      expr: COUNT(DISTINCT assessment_type_id)
    - name: "Total Scoring Range Min"
      expr: SUM(scoring_range_min)
    - name: "Average Scoring Range Min"
      expr: AVG(scoring_range_min)
    - name: "Total Scoring Range Max"
      expr: SUM(scoring_range_max)
    - name: "Average Scoring Range Max"
      expr: AVG(scoring_range_max)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_care_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Care Event business metrics"
  source: "`cmoore_customer_demos`.`care`.`care_event`"
  dimensions:
    - name: "Member Name"
      expr: member_name
    - name: "Member Date Of Birth"
      expr: member_date_of_birth
    - name: "Member Gender"
      expr: member_gender
    - name: "Provider Name"
      expr: provider_name
    - name: "Provider Type"
      expr: provider_type
    - name: "Date"
      expr: date
    - name: "Start Timestamp"
      expr: start_timestamp
    - name: "End Timestamp"
      expr: end_timestamp
    - name: "Duration Minutes"
      expr: duration_minutes
    - name: "Location Type"
      expr: location_type
    - name: "Location Address"
      expr: location_address
    - name: "Telehealth Platform"
      expr: telehealth_platform
    - name: "Diagnosis Code"
      expr: diagnosis_code
    - name: "Procedure Code"
      expr: procedure_code
    - name: "Hcc Code"
      expr: hcc_code
    - name: "Medication Prescribed"
      expr: medication_prescribed
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Care Event"
      expr: COUNT(DISTINCT care_event_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Billed Amount"
      expr: SUM(billed_amount)
    - name: "Average Billed Amount"
      expr: AVG(billed_amount)
    - name: "Total Paid Amount"
      expr: SUM(paid_amount)
    - name: "Average Paid Amount"
      expr: AVG(paid_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_case_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Case Assignment business metrics"
  source: "`cmoore_customer_demos`.`care`.`case_assignment`"
  dimensions:
    - name: "Role"
      expr: role
    - name: "Responsibility"
      expr: responsibility
    - name: "Assignment Start Date"
      expr: assignment_start_date
    - name: "Assignment End Date"
      expr: assignment_end_date
    - name: "Assignment Status"
      expr: assignment_status
    - name: "Assignment Type"
      expr: assignment_type
    - name: "Assignment Reason"
      expr: assignment_reason
    - name: "Notes"
      expr: notes
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Approved By"
      expr: approved_by
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Priority"
      expr: priority
    - name: "Communication Method"
      expr: communication_method
    - name: "Contact Preference"
      expr: contact_preference
    - name: "Compliance Flag"
      expr: compliance_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Case Assignment"
      expr: COUNT(DISTINCT case_assignment_id)
    - name: "Total Scheduled Hours Per Week"
      expr: SUM(scheduled_hours_per_week)
    - name: "Average Scheduled Hours Per Week"
      expr: AVG(scheduled_hours_per_week)
    - name: "Total Actual Hours Worked"
      expr: SUM(actual_hours_worked)
    - name: "Average Actual Hours Worked"
      expr: AVG(actual_hours_worked)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_clinical_pathway`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Clinical Pathway business metrics"
  source: "`cmoore_customer_demos`.`care`.`clinical_pathway`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Disease Category"
      expr: disease_category
    - name: "Condition Code"
      expr: condition_code
    - name: "Specialty"
      expr: specialty
    - name: "Care Setting"
      expr: care_setting
    - name: "Target Population"
      expr: target_population
    - name: "Pathway Type"
      expr: pathway_type
    - name: "Version Number"
      expr: version_number
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Clinical Guideline Reference"
      expr: clinical_guideline_reference
    - name: "Hedis Measure Code"
      expr: hedis_measure_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Clinical Pathway"
      expr: COUNT(DISTINCT clinical_pathway_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_cohort`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cohort business metrics"
  source: "`cmoore_customer_demos`.`care`.`cohort`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Segment"
      expr: segment
    - name: "Inclusion Criteria"
      expr: inclusion_criteria
    - name: "Exclusion Criteria"
      expr: exclusion_criteria
    - name: "Risk Score Method"
      expr: risk_score_method
    - name: "Population Size"
      expr: population_size
    - name: "Member Count"
      expr: member_count
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Status"
      expr: status
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Source System"
      expr: source_system
    - name: "Version Number"
      expr: version_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cohort"
      expr: COUNT(DISTINCT cohort_id)
    - name: "Total Risk Score Threshold"
      expr: SUM(risk_score_threshold)
    - name: "Average Risk Score Threshold"
      expr: AVG(risk_score_threshold)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_cohort_member`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cohort Member business metrics"
  source: "`cmoore_customer_demos`.`care`.`cohort_member`"
  dimensions:
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Enrollment Timestamp"
      expr: enrollment_timestamp
    - name: "Disenrollment Date"
      expr: disenrollment_date
    - name: "Disenrollment Timestamp"
      expr: disenrollment_timestamp
    - name: "Status"
      expr: status
    - name: "Enrollment Reason Code"
      expr: enrollment_reason_code
    - name: "Enrollment Reason Description"
      expr: enrollment_reason_description
    - name: "Disenrollment Reason Code"
      expr: disenrollment_reason_code
    - name: "Disenrollment Reason Description"
      expr: disenrollment_reason_description
    - name: "Enrollment Source"
      expr: enrollment_source
    - name: "Enrollment Channel"
      expr: enrollment_channel
    - name: "Priority Level"
      expr: priority_level
    - name: "Primary Diagnosis Code"
      expr: primary_diagnosis_code
    - name: "Primary Diagnosis Description"
      expr: primary_diagnosis_description
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
    - name: "Program Type"
      expr: program_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cohort Member"
      expr: COUNT(DISTINCT cohort_member_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Engagement Score"
      expr: SUM(engagement_score)
    - name: "Average Engagement Score"
      expr: AVG(engagement_score)
    - name: "Total Total Cost Of Care"
      expr: SUM(total_cost_of_care)
    - name: "Average Total Cost Of Care"
      expr: AVG(total_cost_of_care)
    - name: "Total Pmpm Cost"
      expr: SUM(pmpm_cost)
    - name: "Average Pmpm Cost"
      expr: AVG(pmpm_cost)
    - name: "Total Baseline Pmpm Cost"
      expr: SUM(baseline_pmpm_cost)
    - name: "Average Baseline Pmpm Cost"
      expr: AVG(baseline_pmpm_cost)
    - name: "Total Cost Savings Amount"
      expr: SUM(cost_savings_amount)
    - name: "Average Cost Savings Amount"
      expr: AVG(cost_savings_amount)
    - name: "Total Assignment Confidence Score"
      expr: SUM(assignment_confidence_score)
    - name: "Average Assignment Confidence Score"
      expr: AVG(assignment_confidence_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_cohort_membership`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cohort Membership business metrics"
  source: "`cmoore_customer_demos`.`care`.`cohort_membership`"
  dimensions:
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Exit Date"
      expr: exit_date
    - name: "Enrollment Reason"
      expr: enrollment_reason
    - name: "Status"
      expr: status
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Enrollment Date Month"
      expr: DATE_TRUNC('MONTH', enrollment_date)
    - name: "Exit Date Month"
      expr: DATE_TRUNC('MONTH', exit_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cohort Membership"
      expr: COUNT(DISTINCT cohort_membership_id)
    - name: "Total Risk Score At Entry"
      expr: SUM(risk_score_at_entry)
    - name: "Average Risk Score At Entry"
      expr: AVG(risk_score_at_entry)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_encounter`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Encounter business metrics"
  source: "`cmoore_customer_demos`.`care`.`encounter`"
  dimensions:
    - name: "Encounter Type"
      expr: encounter_type
    - name: "Service Date"
      expr: service_date
    - name: "Admission Date"
      expr: admission_date
    - name: "Discharge Date"
      expr: discharge_date
    - name: "Length Of Stay"
      expr: length_of_stay
    - name: "Primary Diagnosis Code"
      expr: primary_diagnosis_code
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
    - name: "Procedure Codes"
      expr: procedure_codes
    - name: "Revenue Code"
      expr: revenue_code
    - name: "Encounter Status"
      expr: encounter_status
    - name: "Place Of Service Code"
      expr: place_of_service_code
    - name: "Care Setting"
      expr: care_setting
    - name: "Referral Source"
      expr: referral_source
    - name: "Hedis Measure Flag"
      expr: hedis_measure_flag
    - name: "Value Based Care Flag"
      expr: value_based_care_flag
    - name: "Created Timestamp"
      expr: created_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Encounter"
      expr: COUNT(DISTINCT encounter_id)
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
    - name: "Total Payer Responsibility Amount"
      expr: SUM(payer_responsibility_amount)
    - name: "Average Payer Responsibility Amount"
      expr: AVG(payer_responsibility_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_event_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Event Type business metrics"
  source: "`cmoore_customer_demos`.`care`.`event_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Modality"
      expr: modality
    - name: "Setting"
      expr: setting
    - name: "Service Type"
      expr: service_type
    - name: "Clinical Focus"
      expr: clinical_focus
    - name: "Lob Applicability"
      expr: lob_applicability
    - name: "Program Type"
      expr: program_type
    - name: "Is Billable"
      expr: is_billable
    - name: "Cpt Code"
      expr: cpt_code
    - name: "Hcpcs Code"
      expr: hcpcs_code
    - name: "Revenue Code"
      expr: revenue_code
    - name: "Requires Authorization"
      expr: requires_authorization
    - name: "Requires Referral"
      expr: requires_referral
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Event Type"
      expr: COUNT(DISTINCT event_type_id)
    - name: "Total Cost Per Event"
      expr: SUM(cost_per_event)
    - name: "Average Cost Per Event"
      expr: AVG(cost_per_event)
    - name: "Total Reimbursement Amount"
      expr: SUM(reimbursement_amount)
    - name: "Average Reimbursement Amount"
      expr: AVG(reimbursement_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_intervention`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Intervention business metrics"
  source: "`cmoore_customer_demos`.`care`.`intervention`"
  dimensions:
    - name: "Status"
      expr: status
    - name: "Outcome"
      expr: outcome
    - name: "Scheduled Date"
      expr: scheduled_date
    - name: "Scheduled Start Time"
      expr: scheduled_start_time
    - name: "Scheduled End Time"
      expr: scheduled_end_time
    - name: "Actual Start Timestamp"
      expr: actual_start_timestamp
    - name: "Actual End Timestamp"
      expr: actual_end_timestamp
    - name: "Duration Minutes"
      expr: duration_minutes
    - name: "Delivery Method"
      expr: delivery_method
    - name: "Delivery Channel"
      expr: delivery_channel
    - name: "Delivery Location"
      expr: delivery_location
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Care Manager Name"
      expr: care_manager_name
    - name: "Care Manager Role"
      expr: care_manager_role
    - name: "Care Manager Credential"
      expr: care_manager_credential
    - name: "Primary Diagnosis Code"
      expr: primary_diagnosis_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Intervention"
      expr: COUNT(DISTINCT intervention_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Cost To Member"
      expr: SUM(cost_to_member)
    - name: "Average Cost To Member"
      expr: AVG(cost_to_member)
    - name: "Total Cost To Plan"
      expr: SUM(cost_to_plan)
    - name: "Average Cost To Plan"
      expr: AVG(cost_to_plan)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_intervention_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Intervention Type business metrics"
  source: "`cmoore_customer_demos`.`care`.`intervention_type`"
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
    - name: "Modality"
      expr: modality
    - name: "Clinical Focus"
      expr: clinical_focus
    - name: "Target Population"
      expr: target_population
    - name: "Complexity Level"
      expr: complexity_level
    - name: "Duration Minutes"
      expr: duration_minutes
    - name: "Frequency Recommendation"
      expr: frequency_recommendation
    - name: "Clinical Guideline Reference"
      expr: clinical_guideline_reference
    - name: "Hedis Measure Alignment"
      expr: hedis_measure_alignment
    - name: "Stars Rating Impact"
      expr: stars_rating_impact
    - name: "Vbc Program Alignment"
      expr: vbc_program_alignment
    - name: "Hcc Relevance"
      expr: hcc_relevance
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Intervention Type"
      expr: COUNT(DISTINCT intervention_type_id)
    - name: "Total Reimbursement Rate"
      expr: SUM(reimbursement_rate)
    - name: "Average Reimbursement Rate"
      expr: AVG(reimbursement_rate)
    - name: "Total Quality Threshold"
      expr: SUM(quality_threshold)
    - name: "Average Quality Threshold"
      expr: AVG(quality_threshold)
    - name: "Total Member Satisfaction Target"
      expr: SUM(member_satisfaction_target)
    - name: "Average Member Satisfaction Target"
      expr: AVG(member_satisfaction_target)
    - name: "Total Sla Compliance Target"
      expr: SUM(sla_compliance_target)
    - name: "Average Sla Compliance Target"
      expr: AVG(sla_compliance_target)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_note`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Note business metrics"
  source: "`cmoore_customer_demos`.`care`.`note`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Title"
      expr: title
    - name: "Content"
      expr: content
    - name: "Status"
      expr: status
    - name: "Priority"
      expr: priority
    - name: "Confidentiality Level"
      expr: confidentiality_level
    - name: "Author Name"
      expr: author_name
    - name: "Author Npi"
      expr: author_npi
    - name: "Author Role"
      expr: author_role
    - name: "Author Department"
      expr: author_department
    - name: "Created Date"
      expr: created_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Date"
      expr: modified_date
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Signed Date"
      expr: signed_date
    - name: "Signed Timestamp"
      expr: signed_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Note"
      expr: COUNT(DISTINCT note_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_outreach_channel`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Outreach Channel business metrics"
  source: "`cmoore_customer_demos`.`care`.`outreach_channel`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Is Interactive"
      expr: is_interactive
    - name: "Is Automated"
      expr: is_automated
    - name: "Is Secure"
      expr: is_secure
    - name: "Is Hipaa Compliant"
      expr: is_hipaa_compliant
    - name: "Requires Member Consent"
      expr: requires_member_consent
    - name: "Supports Phi"
      expr: supports_phi
    - name: "Delivery Speed"
      expr: delivery_speed
    - name: "Priority Rank"
      expr: priority_rank
    - name: "Member Preference Rank"
      expr: member_preference_rank
    - name: "Accessibility Level"
      expr: accessibility_level
    - name: "Supports Multilingual"
      expr: supports_multilingual
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Outreach Channel"
      expr: COUNT(DISTINCT outreach_channel_id)
    - name: "Total Average Response Time Hours"
      expr: SUM(average_response_time_hours)
    - name: "Average Average Response Time Hours"
      expr: AVG(average_response_time_hours)
    - name: "Total Cost Per Contact"
      expr: SUM(cost_per_contact)
    - name: "Average Cost Per Contact"
      expr: AVG(cost_per_contact)
    - name: "Total Effectiveness Score"
      expr: SUM(effectiveness_score)
    - name: "Average Effectiveness Score"
      expr: AVG(effectiveness_score)
    - name: "Total Member Satisfaction Score"
      expr: SUM(member_satisfaction_score)
    - name: "Average Member Satisfaction Score"
      expr: AVG(member_satisfaction_score)
    - name: "Total Sla Response Time Hours"
      expr: SUM(sla_response_time_hours)
    - name: "Average Sla Response Time Hours"
      expr: AVG(sla_response_time_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_outreach_contact`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Outreach Contact business metrics"
  source: "`cmoore_customer_demos`.`care`.`outreach_contact`"
  dimensions:
    - name: "Member Number"
      expr: member_number
    - name: "Member First Name"
      expr: member_first_name
    - name: "Member Last Name"
      expr: member_last_name
    - name: "Member Date Of Birth"
      expr: member_date_of_birth
    - name: "Member Gender"
      expr: member_gender
    - name: "Member Phone Number"
      expr: member_phone_number
    - name: "Member Email Address"
      expr: member_email_address
    - name: "Member Address"
      expr: member_address
    - name: "Member Plan Type"
      expr: member_plan_type
    - name: "Member Status"
      expr: member_status
    - name: "Outreach Purpose"
      expr: outreach_purpose
    - name: "Outreach Outcome"
      expr: outreach_outcome
    - name: "Contact Timestamp"
      expr: contact_timestamp
    - name: "Scheduled Timestamp"
      expr: scheduled_timestamp
    - name: "Contact Duration Seconds"
      expr: contact_duration_seconds
    - name: "Contact Attempt Number"
      expr: contact_attempt_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Outreach Contact"
      expr: COUNT(DISTINCT outreach_contact_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_plan`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Plan business metrics"
  source: "`cmoore_customer_demos`.`care`.`plan`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Code"
      expr: code
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Description"
      expr: description
    - name: "Clinical Focus"
      expr: clinical_focus
    - name: "Icd 10 Codes"
      expr: icd_10_codes
    - name: "Duration Days"
      expr: duration_days
    - name: "Duration Type"
      expr: duration_type
    - name: "Intervention Frequency"
      expr: intervention_frequency
    - name: "Primary Objective"
      expr: primary_objective
    - name: "Secondary Objectives"
      expr: secondary_objectives
    - name: "Eligibility Criteria"
      expr: eligibility_criteria
    - name: "Exclusion Criteria"
      expr: exclusion_criteria
    - name: "Target Population"
      expr: target_population
    - name: "Lob Applicability"
      expr: lob_applicability
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Plan"
      expr: COUNT(DISTINCT plan_id)
    - name: "Total Estimated Cost Pmpm"
      expr: SUM(estimated_cost_pmpm)
    - name: "Average Estimated Cost Pmpm"
      expr: AVG(estimated_cost_pmpm)
    - name: "Total Expected Roi Percentage"
      expr: SUM(expected_roi_percentage)
    - name: "Average Expected Roi Percentage"
      expr: AVG(expected_roi_percentage)
    - name: "Total Member Satisfaction Target"
      expr: SUM(member_satisfaction_target)
    - name: "Average Member Satisfaction Target"
      expr: AVG(member_satisfaction_target)
    - name: "Total Engagement Rate Target"
      expr: SUM(engagement_rate_target)
    - name: "Average Engagement Rate Target"
      expr: AVG(engagement_rate_target)
    - name: "Total Completion Rate Target"
      expr: SUM(completion_rate_target)
    - name: "Average Completion Rate Target"
      expr: AVG(completion_rate_target)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_plan_enrollment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Plan Enrollment business metrics"
  source: "`cmoore_customer_demos`.`care`.`plan_enrollment`"
  dimensions:
    - name: "Care Plan Type"
      expr: care_plan_type
    - name: "Care Plan Name"
      expr: care_plan_name
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Enrollment Timestamp"
      expr: enrollment_timestamp
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Status"
      expr: status
    - name: "Status Reason"
      expr: status_reason
    - name: "Enrollment Source"
      expr: enrollment_source
    - name: "Enrollment Method"
      expr: enrollment_method
    - name: "Enrollment Channel"
      expr: enrollment_channel
    - name: "Priority Level"
      expr: priority_level
    - name: "Risk Stratification Level"
      expr: risk_stratification_level
    - name: "Primary Diagnosis Code"
      expr: primary_diagnosis_code
    - name: "Primary Diagnosis Description"
      expr: primary_diagnosis_description
    - name: "Secondary Diagnosis Codes"
      expr: secondary_diagnosis_codes
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Plan Enrollment"
      expr: COUNT(DISTINCT plan_enrollment_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Estimated Cost Savings"
      expr: SUM(estimated_cost_savings)
    - name: "Average Estimated Cost Savings"
      expr: AVG(estimated_cost_savings)
    - name: "Total Program Cost"
      expr: SUM(program_cost)
    - name: "Average Program Cost"
      expr: AVG(program_cost)
    - name: "Total Roi Projection"
      expr: SUM(roi_projection)
    - name: "Average Roi Projection"
      expr: AVG(roi_projection)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_program_goal`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Program Goal business metrics"
  source: "`cmoore_customer_demos`.`care`.`program_goal`"
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
    - name: "Clinical Domain"
      expr: clinical_domain
    - name: "Target Metric Name"
      expr: target_metric_name
    - name: "Target Metric Type"
      expr: target_metric_type
    - name: "Target Operator"
      expr: target_operator
    - name: "Unit Of Measure"
      expr: unit_of_measure
    - name: "Measurement Frequency"
      expr: measurement_frequency
    - name: "Hedis Measure Code"
      expr: hedis_measure_code
    - name: "Hedis Measure Name"
      expr: hedis_measure_name
    - name: "Star Rating Domain"
      expr: star_rating_domain
    - name: "Hcc Category"
      expr: hcc_category
    - name: "Applicable Lob"
      expr: applicable_lob
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Program Goal"
      expr: COUNT(DISTINCT program_goal_id)
    - name: "Total Target Value"
      expr: SUM(target_value)
    - name: "Average Target Value"
      expr: AVG(target_value)
    - name: "Total Target Value Upper Bound"
      expr: SUM(target_value_upper_bound)
    - name: "Average Target Value Upper Bound"
      expr: AVG(target_value_upper_bound)
    - name: "Total Incentive Amount"
      expr: SUM(incentive_amount)
    - name: "Average Incentive Amount"
      expr: AVG(incentive_amount)
    - name: "Total Alert Threshold Value"
      expr: SUM(alert_threshold_value)
    - name: "Average Alert Threshold Value"
      expr: AVG(alert_threshold_value)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_risk_score_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Risk Score Type business metrics"
  source: "`cmoore_customer_demos`.`care`.`risk_score_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Model Version"
      expr: model_version
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Status"
      expr: status
    - name: "Program Type"
      expr: program_type
    - name: "Population Segment"
      expr: population_segment
    - name: "Calculation Frequency"
      expr: calculation_frequency
    - name: "Data Source"
      expr: data_source
    - name: "Coding System"
      expr: coding_system
    - name: "Hcc Model Indicator"
      expr: hcc_model_indicator
    - name: "Prospective Indicator"
      expr: prospective_indicator
    - name: "Payment Year"
      expr: payment_year
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Risk Score Type"
      expr: COUNT(DISTINCT risk_score_type_id)
    - name: "Total Normalization Factor"
      expr: SUM(normalization_factor)
    - name: "Average Normalization Factor"
      expr: AVG(normalization_factor)
    - name: "Total Minimum Score"
      expr: SUM(minimum_score)
    - name: "Average Minimum Score"
      expr: AVG(minimum_score)
    - name: "Total Maximum Score"
      expr: SUM(maximum_score)
    - name: "Average Maximum Score"
      expr: AVG(maximum_score)
    - name: "Total Average Score"
      expr: SUM(average_score)
    - name: "Average Average Score"
      expr: AVG(average_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_team`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Team business metrics"
  source: "`cmoore_customer_demos`.`care`.`team`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Purpose"
      expr: purpose
    - name: "Type"
      expr: type
    - name: "Service Area"
      expr: service_area
    - name: "Care Model"
      expr: care_model
    - name: "Composition Rules"
      expr: composition_rules
    - name: "Member Population"
      expr: member_population
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Contact Phone"
      expr: contact_phone
    - name: "Contact Email"
      expr: contact_email
    - name: "Contact Fax"
      expr: contact_fax
    - name: "Address Line1"
      expr: address_line1
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Team"
      expr: COUNT(DISTINCT team_id)
    - name: "Total Hcc Risk Adjustment Factor"
      expr: SUM(hcc_risk_adjustment_factor)
    - name: "Average Hcc Risk Adjustment Factor"
      expr: AVG(hcc_risk_adjustment_factor)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Last Quality Review Score"
      expr: SUM(last_quality_review_score)
    - name: "Average Last Quality Review Score"
      expr: AVG(last_quality_review_score)
    - name: "Total Average Member Age"
      expr: SUM(average_member_age)
    - name: "Average Average Member Age"
      expr: AVG(average_member_age)
    - name: "Total Care Team Budget"
      expr: SUM(care_team_budget)
    - name: "Average Care Team Budget"
      expr: AVG(care_team_budget)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`care_team_member`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Team Member business metrics"
  source: "`cmoore_customer_demos`.`care`.`team_member`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "First Name"
      expr: first_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Last Name"
      expr: last_name
    - name: "Suffix"
      expr: suffix
    - name: "Role Code"
      expr: role_code
    - name: "Role Description"
      expr: role_description
    - name: "Specialty Code"
      expr: specialty_code
    - name: "Specialty Description"
      expr: specialty_description
    - name: "Credential Type"
      expr: credential_type
    - name: "License State"
      expr: license_state
    - name: "License Expiration Date"
      expr: license_expiration_date
    - name: "Board Certification Status"
      expr: board_certification_status
    - name: "Board Certification Date"
      expr: board_certification_date
    - name: "Dea Number"
      expr: dea_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Team Member"
      expr: COUNT(DISTINCT team_member_id)
    - name: "Total Fte Percentage"
      expr: SUM(fte_percentage)
    - name: "Average Fte Percentage"
      expr: AVG(fte_percentage)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Member Satisfaction Score"
      expr: SUM(member_satisfaction_score)
    - name: "Average Member Satisfaction Score"
      expr: AVG(member_satisfaction_score)
    - name: "Total Malpractice Coverage Amount"
      expr: SUM(malpractice_coverage_amount)
    - name: "Average Malpractice Coverage Amount"
      expr: AVG(malpractice_coverage_amount)
$$;