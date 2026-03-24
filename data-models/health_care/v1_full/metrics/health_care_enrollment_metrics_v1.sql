-- Metric views for domain: enrollment | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:06:23

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_action_type`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Action Type business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`action_type`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Requires Prior Coverage Flag"
      expr: requires_prior_coverage_flag
    - name: "Allows Mid Year Change Flag"
      expr: allows_mid_year_change_flag
    - name: "Requires Qle Flag"
      expr: requires_qle_flag
    - name: "Requires Documentation Flag"
      expr: requires_documentation_flag
    - name: "Processing Priority"
      expr: processing_priority
    - name: "Standard Processing Days"
      expr: standard_processing_days
    - name: "Retroactive Allowed Flag"
      expr: retroactive_allowed_flag
    - name: "Max Retroactive Days"
      expr: max_retroactive_days
    - name: "Triggers Premium Adjustment Flag"
      expr: triggers_premium_adjustment_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Action Type"
      expr: COUNT(DISTINCT action_type_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_application`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Application business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`application`"
  dimensions:
    - name: "Applicant Name"
      expr: applicant_name
    - name: "Applicant Dob"
      expr: applicant_dob
    - name: "Applicant Ssn"
      expr: applicant_ssn
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Mailing Address"
      expr: mailing_address
    - name: "Application Status"
      expr: application_status
    - name: "Application Type"
      expr: application_type
    - name: "Enrollment Channel"
      expr: enrollment_channel
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Plan Name"
      expr: plan_name
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Premium Frequency"
      expr: premium_frequency
    - name: "Payment Method"
      expr: payment_method
    - name: "Subsidy Type"
      expr: subsidy_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Application"
      expr: COUNT(DISTINCT application_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Tax Credit Amount"
      expr: SUM(tax_credit_amount)
    - name: "Average Tax Credit Amount"
      expr: AVG(tax_credit_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_change_detail`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Change Detail business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`change_detail`"
  dimensions:
    - name: "Change Type"
      expr: change_type
    - name: "Change Category"
      expr: change_category
    - name: "Change Reason Code"
      expr: change_reason_code
    - name: "Change Reason Description"
      expr: change_reason_description
    - name: "Qle Indicator"
      expr: qle_indicator
    - name: "Qle Date"
      expr: qle_date
    - name: "Field Name"
      expr: field_name
    - name: "Field Label"
      expr: field_label
    - name: "Previous Value"
      expr: previous_value
    - name: "New Value"
      expr: new_value
    - name: "Previous Plan Code"
      expr: previous_plan_code
    - name: "New Plan Code"
      expr: new_plan_code
    - name: "Previous Coverage Tier"
      expr: previous_coverage_tier
    - name: "New Coverage Tier"
      expr: new_coverage_tier
    - name: "Dependent Sequence Number"
      expr: dependent_sequence_number
    - name: "Dependent First Name"
      expr: dependent_first_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Change Detail"
      expr: COUNT(DISTINCT change_detail_id)
    - name: "Total Previous Premium Amount"
      expr: SUM(previous_premium_amount)
    - name: "Average Previous Premium Amount"
      expr: AVG(previous_premium_amount)
    - name: "Total New Premium Amount"
      expr: SUM(new_premium_amount)
    - name: "Average New Premium Amount"
      expr: AVG(new_premium_amount)
    - name: "Total Premium Difference Amount"
      expr: SUM(premium_difference_amount)
    - name: "Average Premium Difference Amount"
      expr: AVG(premium_difference_amount)
    - name: "Total Previous Deductible Amount"
      expr: SUM(previous_deductible_amount)
    - name: "Average Previous Deductible Amount"
      expr: AVG(previous_deductible_amount)
    - name: "Total New Deductible Amount"
      expr: SUM(new_deductible_amount)
    - name: "Average New Deductible Amount"
      expr: AVG(new_deductible_amount)
    - name: "Total Previous Oop Max Amount"
      expr: SUM(previous_oop_max_amount)
    - name: "Average Previous Oop Max Amount"
      expr: AVG(previous_oop_max_amount)
    - name: "Total New Oop Max Amount"
      expr: SUM(new_oop_max_amount)
    - name: "Average New Oop Max Amount"
      expr: AVG(new_oop_max_amount)
    - name: "Total Previous Copay Amount"
      expr: SUM(previous_copay_amount)
    - name: "Average Previous Copay Amount"
      expr: AVG(previous_copay_amount)
    - name: "Total New Copay Amount"
      expr: SUM(new_copay_amount)
    - name: "Average New Copay Amount"
      expr: AVG(new_copay_amount)
    - name: "Total Previous Coinsurance Percentage"
      expr: SUM(previous_coinsurance_percentage)
    - name: "Average Previous Coinsurance Percentage"
      expr: AVG(previous_coinsurance_percentage)
    - name: "Total New Coinsurance Percentage"
      expr: SUM(new_coinsurance_percentage)
    - name: "Average New Coinsurance Percentage"
      expr: AVG(new_coinsurance_percentage)
    - name: "Total Rider Premium Amount"
      expr: SUM(rider_premium_amount)
    - name: "Average Rider Premium Amount"
      expr: AVG(rider_premium_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_channel`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Channel business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`channel`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Description"
      expr: description
    - name: "Distribution Method"
      expr: distribution_method
    - name: "Status"
      expr: status
    - name: "Is Self Service"
      expr: is_self_service
    - name: "Requires Broker"
      expr: requires_broker
    - name: "Supports Individual Enrollment"
      expr: supports_individual_enrollment
    - name: "Supports Group Enrollment"
      expr: supports_group_enrollment
    - name: "Supports Medicare"
      expr: supports_medicare
    - name: "Supports Medicaid"
      expr: supports_medicaid
    - name: "Supports Commercial"
      expr: supports_commercial
    - name: "Supports Exchange Enrollment"
      expr: supports_exchange_enrollment
    - name: "Exchange Type"
      expr: exchange_type
    - name: "Supports Sep"
      expr: supports_sep
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Channel"
      expr: COUNT(DISTINCT channel_id)
    - name: "Total Average Enrollment Time Minutes"
      expr: SUM(average_enrollment_time_minutes)
    - name: "Average Average Enrollment Time Minutes"
      expr: AVG(average_enrollment_time_minutes)
    - name: "Total Cost Per Enrollment"
      expr: SUM(cost_per_enrollment)
    - name: "Average Cost Per Enrollment"
      expr: AVG(cost_per_enrollment)
    - name: "Total Commission Rate Percent"
      expr: SUM(commission_rate_percent)
    - name: "Average Commission Rate Percent"
      expr: AVG(commission_rate_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_cobra_continuation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cobra Continuation business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`cobra_continuation`"
  dimensions:
    - name: "Policy Number"
      expr: policy_number
    - name: "Qualifying Event Date"
      expr: qualifying_event_date
    - name: "Notification Date"
      expr: notification_date
    - name: "Election Date"
      expr: election_date
    - name: "Election Period Start Date"
      expr: election_period_start_date
    - name: "Election Period End Date"
      expr: election_period_end_date
    - name: "Coverage Start Date"
      expr: coverage_start_date
    - name: "Coverage End Date"
      expr: coverage_end_date
    - name: "Maximum Coverage Duration Months"
      expr: maximum_coverage_duration_months
    - name: "Extended Coverage Indicator"
      expr: extended_coverage_indicator
    - name: "Disability Extension Indicator"
      expr: disability_extension_indicator
    - name: "Disability Determination Date"
      expr: disability_determination_date
    - name: "Second Qualifying Event Indicator"
      expr: second_qualifying_event_indicator
    - name: "Second Qualifying Event Date"
      expr: second_qualifying_event_date
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Premium Payment Frequency"
      expr: premium_payment_frequency
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cobra Continuation"
      expr: COUNT(DISTINCT cobra_continuation_id)
    - name: "Total Monthly Premium Amount"
      expr: SUM(monthly_premium_amount)
    - name: "Average Monthly Premium Amount"
      expr: AVG(monthly_premium_amount)
    - name: "Total Administrative Fee Amount"
      expr: SUM(administrative_fee_amount)
    - name: "Average Administrative Fee Amount"
      expr: AVG(administrative_fee_amount)
    - name: "Total Total Monthly Cost"
      expr: SUM(total_monthly_cost)
    - name: "Average Total Monthly Cost"
      expr: AVG(total_monthly_cost)
    - name: "Total Subsidy Percentage"
      expr: SUM(subsidy_percentage)
    - name: "Average Subsidy Percentage"
      expr: AVG(subsidy_percentage)
    - name: "Total Last Payment Amount"
      expr: SUM(last_payment_amount)
    - name: "Average Last Payment Amount"
      expr: AVG(last_payment_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_dependent_enrollment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Dependent Enrollment business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`dependent_enrollment`"
  dimensions:
    - name: "Relationship Code"
      expr: relationship_code
    - name: "Relationship Description"
      expr: relationship_description
    - name: "Dependent First Name"
      expr: dependent_first_name
    - name: "Dependent Middle Name"
      expr: dependent_middle_name
    - name: "Dependent Last Name"
      expr: dependent_last_name
    - name: "Dependent Suffix"
      expr: dependent_suffix
    - name: "Dependent Ssn"
      expr: dependent_ssn
    - name: "Dependent Date Of Birth"
      expr: dependent_date_of_birth
    - name: "Dependent Gender"
      expr: dependent_gender
    - name: "Dependent Marital Status"
      expr: dependent_marital_status
    - name: "Dependent Student Status"
      expr: dependent_student_status
    - name: "Dependent Disabled Indicator"
      expr: dependent_disabled_indicator
    - name: "Dependent Tobacco User Indicator"
      expr: dependent_tobacco_user_indicator
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Coverage Termination Date"
      expr: coverage_termination_date
    - name: "Enrollment Type"
      expr: enrollment_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Dependent Enrollment"
      expr: COUNT(DISTINCT dependent_enrollment_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Aptc Amount"
      expr: SUM(aptc_amount)
    - name: "Average Aptc Amount"
      expr: AVG(aptc_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_effective_period`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Effective Period business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`effective_period`"
  dimensions:
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Original Start Date"
      expr: original_start_date
    - name: "Original End Date"
      expr: original_end_date
    - name: "Period Type"
      expr: period_type
    - name: "Change Reason Code"
      expr: change_reason_code
    - name: "Change Reason Description"
      expr: change_reason_description
    - name: "Qle Event Date"
      expr: qle_event_date
    - name: "Enrollment Channel"
      expr: enrollment_channel
    - name: "Enrollment Period Category"
      expr: enrollment_period_category
    - name: "Aep Year"
      expr: aep_year
    - name: "Sep Eligibility Verified"
      expr: sep_eligibility_verified
    - name: "Sep Verification Date"
      expr: sep_verification_date
    - name: "Cobra Qualifying Event"
      expr: cobra_qualifying_event
    - name: "Cobra Election Date"
      expr: cobra_election_date
    - name: "Cobra Maximum Period Months"
      expr: cobra_maximum_period_months
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Effective Period"
      expr: COUNT(DISTINCT effective_period_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_enrollment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`enrollment`"
  dimensions:
    - name: "Group Number"
      expr: group_number
    - name: "Product Type"
      expr: product_type
    - name: "Lob"
      expr: lob
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Relationship To Subscriber"
      expr: relationship_to_subscriber
    - name: "Type"
      expr: type
    - name: "Method"
      expr: method
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Original Effective Date"
      expr: original_effective_date
    - name: "Application Date"
      expr: application_date
    - name: "Approval Date"
      expr: approval_date
    - name: "Received Date"
      expr: received_date
    - name: "Processed Date"
      expr: processed_date
    - name: "Qle Event Date"
      expr: qle_event_date
    - name: "Sep Indicator"
      expr: sep_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment"
      expr: COUNT(DISTINCT enrollment_id)
    - name: "Total Aptc Amount"
      expr: SUM(aptc_amount)
    - name: "Average Aptc Amount"
      expr: AVG(aptc_amount)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Member Premium Amount"
      expr: SUM(member_premium_amount)
    - name: "Average Member Premium Amount"
      expr: AVG(member_premium_amount)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Oop Max Amount"
      expr: SUM(oop_max_amount)
    - name: "Average Oop Max Amount"
      expr: AVG(oop_max_amount)
    - name: "Total Copay Primary Care"
      expr: SUM(copay_primary_care)
    - name: "Average Copay Primary Care"
      expr: AVG(copay_primary_care)
    - name: "Total Copay Specialist"
      expr: SUM(copay_specialist)
    - name: "Average Copay Specialist"
      expr: AVG(copay_specialist)
    - name: "Total Copay Emergency Room"
      expr: SUM(copay_emergency_room)
    - name: "Average Copay Emergency Room"
      expr: AVG(copay_emergency_room)
    - name: "Total Hsa Contribution Amount"
      expr: SUM(hsa_contribution_amount)
    - name: "Average Hsa Contribution Amount"
      expr: AVG(hsa_contribution_amount)
    - name: "Total Hra Contribution Amount"
      expr: SUM(hra_contribution_amount)
    - name: "Average Hra Contribution Amount"
      expr: AVG(hra_contribution_amount)
    - name: "Total Fsa Election Amount"
      expr: SUM(fsa_election_amount)
    - name: "Average Fsa Election Amount"
      expr: AVG(fsa_election_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_enrollment_application`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment Application business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`enrollment_application`"
  dimensions:
    - name: "Member First Name"
      expr: member_first_name
    - name: "Member Last Name"
      expr: member_last_name
    - name: "Member Date Of Birth"
      expr: member_date_of_birth
    - name: "Member Social Security Number"
      expr: member_social_security_number
    - name: "Member Address"
      expr: member_address
    - name: "Member Phone Number"
      expr: member_phone_number
    - name: "Member Email"
      expr: member_email
    - name: "Enrollment Type"
      expr: enrollment_type
    - name: "Enrollment Status"
      expr: enrollment_status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Plan Name"
      expr: plan_name
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Premium Currency"
      expr: premium_currency
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Frequency"
      expr: payment_frequency
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment Application"
      expr: COUNT(DISTINCT enrollment_application_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Out Of Pocket Maximum"
      expr: SUM(out_of_pocket_maximum)
    - name: "Average Out Of Pocket Maximum"
      expr: AVG(out_of_pocket_maximum)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_enrollment_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment Event business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`enrollment_event`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Timestamp"
      expr: timestamp
    - name: "Date"
      expr: date
    - name: "Effective Date"
      expr: effective_date
    - name: "Received Date"
      expr: received_date
    - name: "Processed Date"
      expr: processed_date
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Qle Date"
      expr: qle_date
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Enrollment Period Start Date"
      expr: enrollment_period_start_date
    - name: "Enrollment Period End Date"
      expr: enrollment_period_end_date
    - name: "Submission Method"
      expr: submission_method
    - name: "Initiated By User Type"
      expr: initiated_by_user_type
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Is Correction"
      expr: is_correction
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment Event"
      expr: COUNT(DISTINCT enrollment_event_id)
    - name: "Total Aptc Amount"
      expr: SUM(aptc_amount)
    - name: "Average Aptc Amount"
      expr: AVG(aptc_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_enrollment_session`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment Session business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`enrollment_session`"
  dimensions:
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Ssn"
      expr: member_ssn
    - name: "Member Address"
      expr: member_address
    - name: "Member Phone"
      expr: member_phone
    - name: "Member Email"
      expr: member_email
    - name: "Session Start Timestamp"
      expr: session_start_timestamp
    - name: "Session End Timestamp"
      expr: session_end_timestamp
    - name: "Enrollment Type"
      expr: enrollment_type
    - name: "Enrollment Status"
      expr: enrollment_status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Employer Name"
      expr: employer_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment Session"
      expr: COUNT(DISTINCT enrollment_session_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_enrollment_status`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment Status business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`enrollment_status`"
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
    - name: "Is Billable"
      expr: is_billable
    - name: "Allows Claims"
      expr: allows_claims
    - name: "Requires Approval"
      expr: requires_approval
    - name: "Termination Reason Required"
      expr: termination_reason_required
    - name: "Edi Transaction Code"
      expr: edi_transaction_code
    - name: "Cms Transaction Type"
      expr: cms_transaction_type
    - name: "Display Order"
      expr: display_order
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Is System Generated"
      expr: is_system_generated
    - name: "Notification Required"
      expr: notification_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment Status"
      expr: COUNT(DISTINCT enrollment_status_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_enrollment_transaction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment Transaction business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`enrollment_transaction`"
  dimensions:
    - name: "Member First Name"
      expr: member_first_name
    - name: "Member Last Name"
      expr: member_last_name
    - name: "Member Date Of Birth"
      expr: member_date_of_birth
    - name: "Member Ssn"
      expr: member_ssn
    - name: "Member Address"
      expr: member_address
    - name: "Member Phone Number"
      expr: member_phone_number
    - name: "Transaction Type"
      expr: transaction_type
    - name: "Transaction Date"
      expr: transaction_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Enrollment Status"
      expr: enrollment_status
    - name: "Plan Name"
      expr: plan_name
    - name: "Coverage Type"
      expr: coverage_type
    - name: "Premium Currency"
      expr: premium_currency
    - name: "Employer Name"
      expr: employer_name
    - name: "Member Relationship"
      expr: member_relationship
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment Transaction"
      expr: COUNT(DISTINCT enrollment_transaction_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Out Of Pocket Max"
      expr: SUM(out_of_pocket_max)
    - name: "Average Out Of Pocket Max"
      expr: AVG(out_of_pocket_max)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_group_enrollment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Group Enrollment business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`group_enrollment`"
  dimensions:
    - name: "Group Number"
      expr: group_number
    - name: "Group Name"
      expr: group_name
    - name: "Employer Tin"
      expr: employer_tin
    - name: "Situs State"
      expr: situs_state
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Funding Arrangement"
      expr: funding_arrangement
    - name: "Plan Type"
      expr: plan_type
    - name: "Broker Name"
      expr: broker_name
    - name: "Broker Npi"
      expr: broker_npi
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Renewal Date"
      expr: renewal_date
    - name: "Enrollment Type"
      expr: enrollment_type
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Total Enrolled Members"
      expr: total_enrolled_members
    - name: "Total Enrolled Employees"
      expr: total_enrolled_employees
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Group Enrollment"
      expr: COUNT(DISTINCT group_enrollment_id)
    - name: "Total Employer Contribution Percentage"
      expr: SUM(employer_contribution_percentage)
    - name: "Average Employer Contribution Percentage"
      expr: AVG(employer_contribution_percentage)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Employee Contribution Percentage"
      expr: SUM(employee_contribution_percentage)
    - name: "Average Employee Contribution Percentage"
      expr: AVG(employee_contribution_percentage)
    - name: "Total Dependent Contribution Percentage"
      expr: SUM(dependent_contribution_percentage)
    - name: "Average Dependent Contribution Percentage"
      expr: AVG(dependent_contribution_percentage)
    - name: "Total Total Monthly Premium"
      expr: SUM(total_monthly_premium)
    - name: "Average Total Monthly Premium"
      expr: AVG(total_monthly_premium)
    - name: "Total Stop Loss Attachment Point"
      expr: SUM(stop_loss_attachment_point)
    - name: "Average Stop Loss Attachment Point"
      expr: AVG(stop_loss_attachment_point)
    - name: "Total Quality Rating Stars"
      expr: SUM(quality_rating_stars)
    - name: "Average Quality Rating Stars"
      expr: AVG(quality_rating_stars)
    - name: "Total Commission Percentage"
      expr: SUM(commission_percentage)
    - name: "Average Commission Percentage"
      expr: AVG(commission_percentage)
    - name: "Total Commission Override Percentage"
      expr: SUM(commission_override_percentage)
    - name: "Average Commission Override Percentage"
      expr: AVG(commission_override_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_household`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Household business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`household`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Primary Subscriber First Name"
      expr: primary_subscriber_first_name
    - name: "Primary Subscriber Last Name"
      expr: primary_subscriber_last_name
    - name: "Primary Subscriber Middle Name"
      expr: primary_subscriber_middle_name
    - name: "Primary Subscriber Ssn"
      expr: primary_subscriber_ssn
    - name: "Primary Subscriber Date Of Birth"
      expr: primary_subscriber_date_of_birth
    - name: "Primary Subscriber Gender"
      expr: primary_subscriber_gender
    - name: "Address Line 1"
      expr: address_line_1
    - name: "Address Line 2"
      expr: address_line_2
    - name: "City"
      expr: city
    - name: "State"
      expr: state
    - name: "Zip Code"
      expr: zip_code
    - name: "County"
      expr: county
    - name: "Country Code"
      expr: country_code
    - name: "Primary Phone Number"
      expr: primary_phone_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Household"
      expr: COUNT(DISTINCT household_id)
    - name: "Total Income Amount"
      expr: SUM(income_amount)
    - name: "Average Income Amount"
      expr: AVG(income_amount)
    - name: "Total Federal Poverty Level Percentage"
      expr: SUM(federal_poverty_level_percentage)
    - name: "Average Federal Poverty Level Percentage"
      expr: AVG(federal_poverty_level_percentage)
    - name: "Total Aptc Amount"
      expr: SUM(aptc_amount)
    - name: "Average Aptc Amount"
      expr: AVG(aptc_amount)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_notification_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Notification Template business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`notification_template`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Channel"
      expr: channel
    - name: "Template Type"
      expr: template_type
    - name: "Language Code"
      expr: language_code
    - name: "Status"
      expr: status
    - name: "Version Number"
      expr: version_number
    - name: "Is Default"
      expr: is_default
    - name: "Requires Opt In"
      expr: requires_opt_in
    - name: "Subject Line"
      expr: subject_line
    - name: "Body Content"
      expr: body_content
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Compliance Flag"
      expr: compliance_flag
    - name: "Audience"
      expr: audience
    - name: "Send Time"
      expr: send_time
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Notification Template"
      expr: COUNT(DISTINCT notification_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_open_enrollment_window`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Open Enrollment Window business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`open_enrollment_window`"
  dimensions:
    - name: "Window Name"
      expr: window_name
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Market Segment"
      expr: market_segment
    - name: "Plan Year"
      expr: plan_year
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Exchange Type"
      expr: exchange_type
    - name: "Eligibility Criteria"
      expr: eligibility_criteria
    - name: "Qualifying Life Event Required"
      expr: qualifying_life_event_required
    - name: "Geographic Scope"
      expr: geographic_scope
    - name: "State Code"
      expr: state_code
    - name: "Product Portfolio"
      expr: product_portfolio
    - name: "Plan Types Allowed"
      expr: plan_types_allowed
    - name: "Metal Tier"
      expr: metal_tier
    - name: "Minimum Enrollment Age"
      expr: minimum_enrollment_age
    - name: "Maximum Enrollment Age"
      expr: maximum_enrollment_age
    - name: "Dependent Coverage Allowed"
      expr: dependent_coverage_allowed
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Open Enrollment Window"
      expr: COUNT(DISTINCT open_enrollment_window_id)
    - name: "Total Commission Rate Percentage"
      expr: SUM(commission_rate_percentage)
    - name: "Average Commission Rate Percentage"
      expr: AVG(commission_rate_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_plan_option`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Plan Option business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`plan_option`"
  dimensions:
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Metal Tier"
      expr: metal_tier
    - name: "Hsa Eligible"
      expr: hsa_eligible
    - name: "Fsa Eligible"
      expr: fsa_eligible
    - name: "Hra Eligible"
      expr: hra_eligible
    - name: "Preventive Care Covered"
      expr: preventive_care_covered
    - name: "Dental Coverage Included"
      expr: dental_coverage_included
    - name: "Vision Coverage Included"
      expr: vision_coverage_included
    - name: "Mental Health Coverage Included"
      expr: mental_health_coverage_included
    - name: "Maternity Coverage Included"
      expr: maternity_coverage_included
    - name: "Prescription Drug Coverage Included"
      expr: prescription_drug_coverage_included
    - name: "Telehealth Coverage Included"
      expr: telehealth_coverage_included
    - name: "Pcp Referral Required"
      expr: pcp_referral_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Plan Option"
      expr: COUNT(DISTINCT plan_option_id)
    - name: "Total Actuarial Value"
      expr: SUM(actuarial_value)
    - name: "Average Actuarial Value"
      expr: AVG(actuarial_value)
    - name: "Total Individual Deductible In Network"
      expr: SUM(individual_deductible_in_network)
    - name: "Average Individual Deductible In Network"
      expr: AVG(individual_deductible_in_network)
    - name: "Total Individual Deductible Out Of Network"
      expr: SUM(individual_deductible_out_of_network)
    - name: "Average Individual Deductible Out Of Network"
      expr: AVG(individual_deductible_out_of_network)
    - name: "Total Family Deductible In Network"
      expr: SUM(family_deductible_in_network)
    - name: "Average Family Deductible In Network"
      expr: AVG(family_deductible_in_network)
    - name: "Total Family Deductible Out Of Network"
      expr: SUM(family_deductible_out_of_network)
    - name: "Average Family Deductible Out Of Network"
      expr: AVG(family_deductible_out_of_network)
    - name: "Total Individual Oop Max In Network"
      expr: SUM(individual_oop_max_in_network)
    - name: "Average Individual Oop Max In Network"
      expr: AVG(individual_oop_max_in_network)
    - name: "Total Individual Oop Max Out Of Network"
      expr: SUM(individual_oop_max_out_of_network)
    - name: "Average Individual Oop Max Out Of Network"
      expr: AVG(individual_oop_max_out_of_network)
    - name: "Total Family Oop Max In Network"
      expr: SUM(family_oop_max_in_network)
    - name: "Average Family Oop Max In Network"
      expr: AVG(family_oop_max_in_network)
    - name: "Total Family Oop Max Out Of Network"
      expr: SUM(family_oop_max_out_of_network)
    - name: "Average Family Oop Max Out Of Network"
      expr: AVG(family_oop_max_out_of_network)
    - name: "Total Coinsurance In Network"
      expr: SUM(coinsurance_in_network)
    - name: "Average Coinsurance In Network"
      expr: AVG(coinsurance_in_network)
    - name: "Total Coinsurance Out Of Network"
      expr: SUM(coinsurance_out_of_network)
    - name: "Average Coinsurance Out Of Network"
      expr: AVG(coinsurance_out_of_network)
    - name: "Total Pcp Copay"
      expr: SUM(pcp_copay)
    - name: "Average Pcp Copay"
      expr: AVG(pcp_copay)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_qualifying_life_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Qualifying Life Event business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`qualifying_life_event`"
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
    - name: "Sep Duration Days"
      expr: sep_duration_days
    - name: "Retroactive Coverage Allowed"
      expr: retroactive_coverage_allowed
    - name: "Retroactive Days Maximum"
      expr: retroactive_days_maximum
    - name: "Documentation Required"
      expr: documentation_required
    - name: "Documentation Types"
      expr: documentation_types
    - name: "Verification Timeframe Days"
      expr: verification_timeframe_days
    - name: "Applicable To Individual"
      expr: applicable_to_individual
    - name: "Applicable To Group"
      expr: applicable_to_group
    - name: "Applicable To Medicare"
      expr: applicable_to_medicare
    - name: "Applicable To Medicaid"
      expr: applicable_to_medicaid
    - name: "Applicable To Marketplace"
      expr: applicable_to_marketplace
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Qualifying Life Event"
      expr: COUNT(DISTINCT qualifying_life_event_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_renewal`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Renewal business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`renewal`"
  dimensions:
    - name: "Policy Number"
      expr: policy_number
    - name: "Type"
      expr: type
    - name: "Reason"
      expr: reason
    - name: "Date"
      expr: date
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Prior Plan Code"
      expr: prior_plan_code
    - name: "Renewed Plan Code"
      expr: renewed_plan_code
    - name: "Prior Plan Name"
      expr: prior_plan_name
    - name: "Renewed Plan Name"
      expr: renewed_plan_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Period Months"
      expr: period_months
    - name: "Auto Renewal Indicator"
      expr: auto_renewal_indicator
    - name: "Member Action Required Indicator"
      expr: member_action_required_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Renewal"
      expr: COUNT(DISTINCT renewal_id)
    - name: "Total Prior Premium Amount"
      expr: SUM(prior_premium_amount)
    - name: "Average Prior Premium Amount"
      expr: AVG(prior_premium_amount)
    - name: "Total Renewed Premium Amount"
      expr: SUM(renewed_premium_amount)
    - name: "Average Renewed Premium Amount"
      expr: AVG(renewed_premium_amount)
    - name: "Total Premium Change Amount"
      expr: SUM(premium_change_amount)
    - name: "Average Premium Change Amount"
      expr: AVG(premium_change_amount)
    - name: "Total Premium Change Percentage"
      expr: SUM(premium_change_percentage)
    - name: "Average Premium Change Percentage"
      expr: AVG(premium_change_percentage)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_sep_window`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sep Window business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`sep_window`"
  dimensions:
    - name: "Enrollment Channel"
      expr: enrollment_channel
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Window Duration Days"
      expr: window_duration_days
    - name: "Window Start Trigger"
      expr: window_start_trigger
    - name: "Window Start Offset Days"
      expr: window_start_offset_days
    - name: "Coverage Effective Date Rule"
      expr: coverage_effective_date_rule
    - name: "Retroactive Coverage Allowed"
      expr: retroactive_coverage_allowed
    - name: "Retroactive Coverage Max Days"
      expr: retroactive_coverage_max_days
    - name: "Documentation Required"
      expr: documentation_required
    - name: "Documentation Types"
      expr: documentation_types
    - name: "Documentation Submission Deadline Days"
      expr: documentation_submission_deadline_days
    - name: "Pre Enrollment Verification Required"
      expr: pre_enrollment_verification_required
    - name: "Plan Change Allowed"
      expr: plan_change_allowed
    - name: "Dependent Enrollment Allowed"
      expr: dependent_enrollment_allowed
    - name: "Dependent Enrollment Scope"
      expr: dependent_enrollment_scope
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sep Window"
      expr: COUNT(DISTINCT sep_window_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_source`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Source business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`source`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Exchange Type"
      expr: exchange_type
    - name: "Exchange State Code"
      expr: exchange_state_code
    - name: "Broker Channel Flag"
      expr: broker_channel_flag
    - name: "Employer Group Flag"
      expr: employer_group_flag
    - name: "Government Program Flag"
      expr: government_program_flag
    - name: "Digital Channel Flag"
      expr: digital_channel_flag
    - name: "Self Service Flag"
      expr: self_service_flag
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Lob Applicability"
      expr: lob_applicability
    - name: "Product Portfolio Scope"
      expr: product_portfolio_scope
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Source"
      expr: COUNT(DISTINCT source_id)
    - name: "Total Sla Processing Hours"
      expr: SUM(sla_processing_hours)
    - name: "Average Sla Processing Hours"
      expr: AVG(sla_processing_hours)
    - name: "Total Commission Rate Percent"
      expr: SUM(commission_rate_percent)
    - name: "Average Commission Rate Percent"
      expr: AVG(commission_rate_percent)
    - name: "Total Cost Per Enrollment"
      expr: SUM(cost_per_enrollment)
    - name: "Average Cost Per Enrollment"
      expr: AVG(cost_per_enrollment)
    - name: "Total Fraud Risk Score"
      expr: SUM(fraud_risk_score)
    - name: "Average Fraud Risk Score"
      expr: AVG(fraud_risk_score)
    - name: "Total Average Processing Time Hours"
      expr: SUM(average_processing_time_hours)
    - name: "Average Average Processing Time Hours"
      expr: AVG(average_processing_time_hours)
    - name: "Total Error Rate Percent"
      expr: SUM(error_rate_percent)
    - name: "Average Error Rate Percent"
      expr: AVG(error_rate_percent)
    - name: "Total Member Satisfaction Score"
      expr: SUM(member_satisfaction_score)
    - name: "Average Member Satisfaction Score"
      expr: AVG(member_satisfaction_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_termination_reason`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Termination Reason business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`termination_reason`"
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
    - name: "Is Member Initiated"
      expr: is_member_initiated
    - name: "Is Employer Initiated"
      expr: is_employer_initiated
    - name: "Is Carrier Initiated"
      expr: is_carrier_initiated
    - name: "Requires Notice"
      expr: requires_notice
    - name: "Notice Days Required"
      expr: notice_days_required
    - name: "Allows Cobra Continuation"
      expr: allows_cobra_continuation
    - name: "Allows Special Enrollment"
      expr: allows_special_enrollment
    - name: "Sep Duration Days"
      expr: sep_duration_days
    - name: "Requires Refund"
      expr: requires_refund
    - name: "Refund Calculation Method"
      expr: refund_calculation_method
    - name: "Impacts Mlr"
      expr: impacts_mlr
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Termination Reason"
      expr: COUNT(DISTINCT termination_reason_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`enrollment_waiver`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Waiver business metrics"
  source: "`cmoore_customer_demos`.`enrollment`.`waiver`"
  dimensions:
    - name: "Coverage Type"
      expr: coverage_type
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Alternate Coverage Carrier Name"
      expr: alternate_coverage_carrier_name
    - name: "Alternate Coverage Policy Number"
      expr: alternate_coverage_policy_number
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Status"
      expr: status
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Qle Event Date"
      expr: qle_event_date
    - name: "Submission Date"
      expr: submission_date
    - name: "Submission Timestamp"
      expr: submission_timestamp
    - name: "Submission Channel"
      expr: submission_channel
    - name: "Approval Date"
      expr: approval_date
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Rejection Date"
      expr: rejection_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Waiver"
      expr: COUNT(DISTINCT waiver_id)
    - name: "Total Opt Out Incentive Amount"
      expr: SUM(opt_out_incentive_amount)
    - name: "Average Opt Out Incentive Amount"
      expr: AVG(opt_out_incentive_amount)
    - name: "Total Employer Contribution Waived Amount"
      expr: SUM(employer_contribution_waived_amount)
    - name: "Average Employer Contribution Waived Amount"
      expr: AVG(employer_contribution_waived_amount)
    - name: "Total Employee Contribution Waived Amount"
      expr: SUM(employee_contribution_waived_amount)
    - name: "Average Employee Contribution Waived Amount"
      expr: AVG(employee_contribution_waived_amount)
    - name: "Total Surcharge Amount"
      expr: SUM(surcharge_amount)
    - name: "Average Surcharge Amount"
      expr: AVG(surcharge_amount)
$$;