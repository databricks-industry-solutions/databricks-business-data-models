-- Metric views for domain: billing | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:07:56

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_account`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Account business metrics"
  source: "`cmoore_customer_demos`.`billing`.`account`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Name"
      expr: name
    - name: "Status Reason Code"
      expr: status_reason_code
    - name: "Status Reason Description"
      expr: status_reason_description
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Funding Arrangement"
      expr: funding_arrangement
    - name: "Billing Frequency"
      expr: billing_frequency
    - name: "Billing Method"
      expr: billing_method
    - name: "Payment Terms"
      expr: payment_terms
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Currency Code"
      expr: currency_code
    - name: "Tax Identification Number"
      expr: tax_identification_number
    - name: "Billing Address Line 1"
      expr: billing_address_line_1
    - name: "Billing Address Line 2"
      expr: billing_address_line_2
    - name: "Billing City"
      expr: billing_city
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Account"
      expr: COUNT(DISTINCT account_id)
    - name: "Total Current Balance"
      expr: SUM(current_balance)
    - name: "Average Current Balance"
      expr: AVG(current_balance)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
    - name: "Total Past Due Balance"
      expr: SUM(past_due_balance)
    - name: "Average Past Due Balance"
      expr: AVG(past_due_balance)
    - name: "Total Credit Balance"
      expr: SUM(credit_balance)
    - name: "Average Credit Balance"
      expr: AVG(credit_balance)
    - name: "Total Last Payment Amount"
      expr: SUM(last_payment_amount)
    - name: "Average Last Payment Amount"
      expr: AVG(last_payment_amount)
    - name: "Total Minimum Participation Percentage"
      expr: SUM(minimum_participation_percentage)
    - name: "Average Minimum Participation Percentage"
      expr: AVG(minimum_participation_percentage)
    - name: "Total Employer Contribution Percentage"
      expr: SUM(employer_contribution_percentage)
    - name: "Average Employer Contribution Percentage"
      expr: AVG(employer_contribution_percentage)
    - name: "Total Employee Contribution Percentage"
      expr: SUM(employee_contribution_percentage)
    - name: "Average Employee Contribution Percentage"
      expr: AVG(employee_contribution_percentage)
    - name: "Total Commission Rate Percentage"
      expr: SUM(commission_rate_percentage)
    - name: "Average Commission Rate Percentage"
      expr: AVG(commission_rate_percentage)
    - name: "Total Administrative Fee Amount"
      expr: SUM(administrative_fee_amount)
    - name: "Average Administrative Fee Amount"
      expr: AVG(administrative_fee_amount)
    - name: "Total Stop Loss Premium Amount"
      expr: SUM(stop_loss_premium_amount)
    - name: "Average Stop Loss Premium Amount"
      expr: AVG(stop_loss_premium_amount)
    - name: "Total Cobra Premium Percentage"
      expr: SUM(cobra_premium_percentage)
    - name: "Average Cobra Premium Percentage"
      expr: AVG(cobra_premium_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_accounts_receivable`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Accounts Receivable business metrics"
  source: "`cmoore_customer_demos`.`billing`.`accounts_receivable`"
  dimensions:
    - name: "Policy Number"
      expr: policy_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Receivable Type"
      expr: receivable_type
    - name: "Billing Type"
      expr: billing_type
    - name: "Currency Code"
      expr: currency_code
    - name: "Aging Bucket"
      expr: aging_bucket
    - name: "Days Outstanding"
      expr: days_outstanding
    - name: "Collection Status"
      expr: collection_status
    - name: "Payment Plan Indicator"
      expr: payment_plan_indicator
    - name: "Grace Period Indicator"
      expr: grace_period_indicator
    - name: "Grace Period End Date"
      expr: grace_period_end_date
    - name: "Due Date"
      expr: due_date
    - name: "Invoice Date"
      expr: invoice_date
    - name: "Service Start Date"
      expr: service_start_date
    - name: "Service End Date"
      expr: service_end_date
    - name: "Last Payment Date"
      expr: last_payment_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Accounts Receivable"
      expr: COUNT(DISTINCT accounts_receivable_id)
    - name: "Total Original Amount"
      expr: SUM(original_amount)
    - name: "Average Original Amount"
      expr: AVG(original_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
    - name: "Total Paid Amount"
      expr: SUM(paid_amount)
    - name: "Average Paid Amount"
      expr: AVG(paid_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Write Off Amount"
      expr: SUM(write_off_amount)
    - name: "Average Write Off Amount"
      expr: AVG(write_off_amount)
    - name: "Total Last Payment Amount"
      expr: SUM(last_payment_amount)
    - name: "Average Last Payment Amount"
      expr: AVG(last_payment_amount)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Amount"
      expr: SUM(coinsurance_amount)
    - name: "Average Coinsurance Amount"
      expr: AVG(coinsurance_amount)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Interest Amount"
      expr: SUM(interest_amount)
    - name: "Average Interest Amount"
      expr: AVG(interest_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_ar_line`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Ar Line business metrics"
  source: "`cmoore_customer_demos`.`billing`.`ar_line`"
  dimensions:
    - name: "Line Number"
      expr: line_number
    - name: "Line Type"
      expr: line_type
    - name: "Line Description"
      expr: line_description
    - name: "Currency Code"
      expr: currency_code
    - name: "Due Date"
      expr: due_date
    - name: "Grace Period End Date"
      expr: grace_period_end_date
    - name: "Status"
      expr: status
    - name: "Aging Bucket"
      expr: aging_bucket
    - name: "Days Past Due"
      expr: days_past_due
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Service Start Date"
      expr: service_start_date
    - name: "Service End Date"
      expr: service_end_date
    - name: "Group Number"
      expr: group_number
    - name: "Policy Number"
      expr: policy_number
    - name: "Line Of Business"
      expr: line_of_business
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Ar Line"
      expr: COUNT(DISTINCT ar_line_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Outstanding Amount"
      expr: SUM(outstanding_amount)
    - name: "Average Outstanding Amount"
      expr: AVG(outstanding_amount)
    - name: "Total Paid Amount"
      expr: SUM(paid_amount)
    - name: "Average Paid Amount"
      expr: AVG(paid_amount)
    - name: "Total Adjusted Amount"
      expr: SUM(adjusted_amount)
    - name: "Average Adjusted Amount"
      expr: AVG(adjusted_amount)
    - name: "Total Rate Per Member"
      expr: SUM(rate_per_member)
    - name: "Average Rate Per Member"
      expr: AVG(rate_per_member)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Tax Rate"
      expr: SUM(tax_rate)
    - name: "Average Tax Rate"
      expr: AVG(tax_rate)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Write Off Amount"
      expr: SUM(write_off_amount)
    - name: "Average Write Off Amount"
      expr: AVG(write_off_amount)
    - name: "Total Last Payment Amount"
      expr: SUM(last_payment_amount)
    - name: "Average Last Payment Amount"
      expr: AVG(last_payment_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_billing_adjustment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Billing Adjustment business metrics"
  source: "`cmoore_customer_demos`.`billing`.`billing_adjustment`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Currency Code"
      expr: currency_code
    - name: "Date"
      expr: date
    - name: "Effective Date"
      expr: effective_date
    - name: "Applied Date"
      expr: applied_date
    - name: "Reversal Date"
      expr: reversal_date
    - name: "Status"
      expr: status
    - name: "Approval Status"
      expr: approval_status
    - name: "Approval Date"
      expr: approval_date
    - name: "Approved By"
      expr: approved_by
    - name: "Initiated By"
      expr: initiated_by
    - name: "Source System"
      expr: source_system
    - name: "Group Number"
      expr: group_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Billing Adjustment"
      expr: COUNT(DISTINCT billing_adjustment_id)
    - name: "Total Rate Amount"
      expr: SUM(rate_amount)
    - name: "Average Rate Amount"
      expr: AVG(rate_amount)
    - name: "Total Original Amount"
      expr: SUM(original_amount)
    - name: "Average Original Amount"
      expr: AVG(original_amount)
    - name: "Total Adjusted Amount"
      expr: SUM(adjusted_amount)
    - name: "Average Adjusted Amount"
      expr: AVG(adjusted_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Capitation Amount"
      expr: SUM(capitation_amount)
    - name: "Average Capitation Amount"
      expr: AVG(capitation_amount)
    - name: "Total Approval Threshold Amount"
      expr: SUM(approval_threshold_amount)
    - name: "Average Approval Threshold Amount"
      expr: AVG(approval_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_billing_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Billing Event business metrics"
  source: "`cmoore_customer_demos`.`billing`.`billing_event`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Timestamp"
      expr: timestamp
    - name: "Date"
      expr: date
    - name: "Billing Statement Number"
      expr: billing_statement_number
    - name: "Policy Number"
      expr: policy_number
    - name: "Lob"
      expr: lob
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Type"
      expr: plan_type
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Coverage Termination Date"
      expr: coverage_termination_date
    - name: "Currency Code"
      expr: currency_code
    - name: "Billing Frequency"
      expr: billing_frequency
    - name: "Payment Channel"
      expr: payment_channel
    - name: "Payment Due Date"
      expr: payment_due_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Billing Event"
      expr: COUNT(DISTINCT billing_event_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Member Premium Amount"
      expr: SUM(member_premium_amount)
    - name: "Average Member Premium Amount"
      expr: AVG(member_premium_amount)
    - name: "Total Employer Premium Amount"
      expr: SUM(employer_premium_amount)
    - name: "Average Employer Premium Amount"
      expr: AVG(employer_premium_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
    - name: "Total Total Amount Due"
      expr: SUM(total_amount_due)
    - name: "Average Total Amount Due"
      expr: AVG(total_amount_due)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Pepm Rate"
      expr: SUM(pepm_rate)
    - name: "Average Pepm Rate"
      expr: AVG(pepm_rate)
    - name: "Total Capitation Amount"
      expr: SUM(capitation_amount)
    - name: "Average Capitation Amount"
      expr: AVG(capitation_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_billing_exception`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Billing Exception business metrics"
  source: "`cmoore_customer_demos`.`billing`.`billing_exception`"
  dimensions:
    - name: "Type Code"
      expr: type_code
    - name: "Status"
      expr: status
    - name: "Severity Level"
      expr: severity_level
    - name: "Priority Rank"
      expr: priority_rank
    - name: "Detected Date"
      expr: detected_date
    - name: "Detected Timestamp"
      expr: detected_timestamp
    - name: "Detection Method"
      expr: detection_method
    - name: "Detection Source System"
      expr: detection_source_system
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Billing Cycle Code"
      expr: billing_cycle_code
    - name: "Group Number"
      expr: group_number
    - name: "Policy Number"
      expr: policy_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Code"
      expr: product_code
    - name: "Plan Code"
      expr: plan_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Billing Exception"
      expr: COUNT(DISTINCT billing_exception_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Expected Amount"
      expr: SUM(expected_amount)
    - name: "Average Expected Amount"
      expr: AVG(expected_amount)
    - name: "Total Actual Amount"
      expr: SUM(actual_amount)
    - name: "Average Actual Amount"
      expr: AVG(actual_amount)
    - name: "Total Variance Amount"
      expr: SUM(variance_amount)
    - name: "Average Variance Amount"
      expr: AVG(variance_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Employee Contribution Amount"
      expr: SUM(employee_contribution_amount)
    - name: "Average Employee Contribution Amount"
      expr: AVG(employee_contribution_amount)
    - name: "Total Age Rating Factor"
      expr: SUM(age_rating_factor)
    - name: "Average Age Rating Factor"
      expr: AVG(age_rating_factor)
    - name: "Total Tobacco Rating Factor"
      expr: SUM(tobacco_rating_factor)
    - name: "Average Tobacco Rating Factor"
      expr: AVG(tobacco_rating_factor)
    - name: "Total Capitation Rate Pmpm"
      expr: SUM(capitation_rate_pmpm)
    - name: "Average Capitation Rate Pmpm"
      expr: AVG(capitation_rate_pmpm)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Aso Fee Amount"
      expr: SUM(aso_fee_amount)
    - name: "Average Aso Fee Amount"
      expr: AVG(aso_fee_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_billing_note`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Billing Note business metrics"
  source: "`cmoore_customer_demos`.`billing`.`billing_note`"
  dimensions:
    - name: "Group Number"
      expr: group_number
    - name: "Type"
      expr: type
    - name: "Text"
      expr: text
    - name: "Subject"
      expr: subject
    - name: "Visibility"
      expr: visibility
    - name: "Priority"
      expr: priority
    - name: "Status"
      expr: status
    - name: "Created Date"
      expr: created_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Created By User Name"
      expr: created_by_user_name
    - name: "Modified Date"
      expr: modified_date
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Modified By User Name"
      expr: modified_by_user_name
    - name: "Resolved Date"
      expr: resolved_date
    - name: "Resolved Timestamp"
      expr: resolved_timestamp
    - name: "Resolved By User Name"
      expr: resolved_by_user_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Billing Note"
      expr: COUNT(DISTINCT billing_note_id)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Capitation Amount"
      expr: SUM(capitation_amount)
    - name: "Average Capitation Amount"
      expr: AVG(capitation_amount)
    - name: "Total Pmpm Amount"
      expr: SUM(pmpm_amount)
    - name: "Average Pmpm Amount"
      expr: AVG(pmpm_amount)
    - name: "Total Pepm Amount"
      expr: SUM(pepm_amount)
    - name: "Average Pepm Amount"
      expr: AVG(pepm_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_billing_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Billing Rule business metrics"
  source: "`cmoore_customer_demos`.`billing`.`billing_rule`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Calculation Method"
      expr: calculation_method
    - name: "Calculation Formula"
      expr: calculation_formula
    - name: "Threshold Operator"
      expr: threshold_operator
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Applies To Lob"
      expr: applies_to_lob
    - name: "Applies To Plan Type"
      expr: applies_to_plan_type
    - name: "Applies To Group Size"
      expr: applies_to_group_size
    - name: "Applies To Funding Type"
      expr: applies_to_funding_type
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Priority Order"
      expr: priority_order
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Billing Rule"
      expr: COUNT(DISTINCT billing_rule_id)
    - name: "Total Base Amount"
      expr: SUM(base_amount)
    - name: "Average Base Amount"
      expr: AVG(base_amount)
    - name: "Total Percentage Rate"
      expr: SUM(percentage_rate)
    - name: "Average Percentage Rate"
      expr: AVG(percentage_rate)
    - name: "Total Minimum Amount"
      expr: SUM(minimum_amount)
    - name: "Average Minimum Amount"
      expr: AVG(minimum_amount)
    - name: "Total Maximum Amount"
      expr: SUM(maximum_amount)
    - name: "Average Maximum Amount"
      expr: AVG(maximum_amount)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Late Fee Percentage"
      expr: SUM(late_fee_percentage)
    - name: "Average Late Fee Percentage"
      expr: AVG(late_fee_percentage)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Discount Percentage"
      expr: SUM(discount_percentage)
    - name: "Average Discount Percentage"
      expr: AVG(discount_percentage)
    - name: "Total Estimated Annual Impact Amount"
      expr: SUM(estimated_annual_impact_amount)
    - name: "Average Estimated Annual Impact Amount"
      expr: AVG(estimated_annual_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_capitation_payment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Capitation Payment business metrics"
  source: "`cmoore_customer_demos`.`billing`.`capitation_payment`"
  dimensions:
    - name: "Provider Tin"
      expr: provider_tin
    - name: "Payment Period Start Date"
      expr: payment_period_start_date
    - name: "Payment Period End Date"
      expr: payment_period_end_date
    - name: "Payment Date"
      expr: payment_date
    - name: "Payment Due Date"
      expr: payment_due_date
    - name: "Lob"
      expr: lob
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Member Count"
      expr: member_count
    - name: "Currency Code"
      expr: currency_code
    - name: "Service Category"
      expr: service_category
    - name: "Network Tier"
      expr: network_tier
    - name: "Geographic Region"
      expr: geographic_region
    - name: "State Code"
      expr: state_code
    - name: "County Code"
      expr: county_code
    - name: "Payment Frequency"
      expr: payment_frequency
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Capitation Payment"
      expr: COUNT(DISTINCT capitation_payment_id)
    - name: "Total Member Months"
      expr: SUM(member_months)
    - name: "Average Member Months"
      expr: AVG(member_months)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Base Capitation Amount"
      expr: SUM(base_capitation_amount)
    - name: "Average Base Capitation Amount"
      expr: AVG(base_capitation_amount)
    - name: "Total Risk Adjustment Amount"
      expr: SUM(risk_adjustment_amount)
    - name: "Average Risk Adjustment Amount"
      expr: AVG(risk_adjustment_amount)
    - name: "Total Withhold Amount"
      expr: SUM(withhold_amount)
    - name: "Average Withhold Amount"
      expr: AVG(withhold_amount)
    - name: "Total Retroactive Adjustment Amount"
      expr: SUM(retroactive_adjustment_amount)
    - name: "Average Retroactive Adjustment Amount"
      expr: AVG(retroactive_adjustment_amount)
    - name: "Total Total Payment Amount"
      expr: SUM(total_payment_amount)
    - name: "Average Total Payment Amount"
      expr: AVG(total_payment_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_collection_agency`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Collection Agency business metrics"
  source: "`cmoore_customer_demos`.`billing`.`collection_agency`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Code"
      expr: code
    - name: "Agency Type"
      expr: agency_type
    - name: "Status"
      expr: status
    - name: "Contact Name"
      expr: contact_name
    - name: "Contact Title"
      expr: contact_title
    - name: "Email"
      expr: email
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
    - name: "Country Code"
      expr: country_code
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Terms"
      expr: payment_terms
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Collection Agency"
      expr: COUNT(DISTINCT collection_agency_id)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_commission_plan`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Commission Plan business metrics"
  source: "`cmoore_customer_demos`.`billing`.`commission_plan`"
  dimensions:
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Lob"
      expr: lob
    - name: "Product Line"
      expr: product_line
    - name: "Market Segment"
      expr: market_segment
    - name: "Commission Basis"
      expr: commission_basis
    - name: "Commission Rate Unit"
      expr: commission_rate_unit
    - name: "Tier Structure Indicator"
      expr: tier_structure_indicator
    - name: "Tier Count"
      expr: tier_count
    - name: "Performance Metric"
      expr: performance_metric
    - name: "Eligibility Criteria"
      expr: eligibility_criteria
    - name: "Bonus Eligibility Indicator"
      expr: bonus_eligibility_indicator
    - name: "Bonus Structure Description"
      expr: bonus_structure_description
    - name: "Chargeback Policy"
      expr: chargeback_policy
    - name: "Chargeback Period Months"
      expr: chargeback_period_months
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Commission Plan"
      expr: COUNT(DISTINCT commission_plan_id)
    - name: "Total Base Commission Rate"
      expr: SUM(base_commission_rate)
    - name: "Average Base Commission Rate"
      expr: AVG(base_commission_rate)
    - name: "Total Minimum Commission Amount"
      expr: SUM(minimum_commission_amount)
    - name: "Average Minimum Commission Amount"
      expr: AVG(minimum_commission_amount)
    - name: "Total Maximum Commission Amount"
      expr: SUM(maximum_commission_amount)
    - name: "Average Maximum Commission Amount"
      expr: AVG(maximum_commission_amount)
    - name: "Total First Year Commission Rate"
      expr: SUM(first_year_commission_rate)
    - name: "Average First Year Commission Rate"
      expr: AVG(first_year_commission_rate)
    - name: "Total Renewal Commission Rate"
      expr: SUM(renewal_commission_rate)
    - name: "Average Renewal Commission Rate"
      expr: AVG(renewal_commission_rate)
    - name: "Total Override Commission Rate"
      expr: SUM(override_commission_rate)
    - name: "Average Override Commission Rate"
      expr: AVG(override_commission_rate)
    - name: "Total Advance Payment Percentage"
      expr: SUM(advance_payment_percentage)
    - name: "Average Advance Payment Percentage"
      expr: AVG(advance_payment_percentage)
    - name: "Total Minimum Production Threshold"
      expr: SUM(minimum_production_threshold)
    - name: "Average Minimum Production Threshold"
      expr: AVG(minimum_production_threshold)
    - name: "Total Cross Sell Bonus Rate"
      expr: SUM(cross_sell_bonus_rate)
    - name: "Average Cross Sell Bonus Rate"
      expr: AVG(cross_sell_bonus_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_cycle`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cycle business metrics"
  source: "`cmoore_customer_demos`.`billing`.`cycle`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Frequency"
      expr: frequency
    - name: "Frequency Interval"
      expr: frequency_interval
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Billing Date"
      expr: billing_date
    - name: "Due Date"
      expr: due_date
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Grace Period End Date"
      expr: grace_period_end_date
    - name: "Status"
      expr: status
    - name: "Lob"
      expr: lob
    - name: "Billing Type"
      expr: billing_type
    - name: "Calculation Method"
      expr: calculation_method
    - name: "Currency Code"
      expr: currency_code
    - name: "Member Count"
      expr: member_count
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cycle"
      expr: COUNT(DISTINCT cycle_id)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Pepm Rate"
      expr: SUM(pepm_rate)
    - name: "Average Pepm Rate"
      expr: AVG(pepm_rate)
    - name: "Total Total Premium Amount"
      expr: SUM(total_premium_amount)
    - name: "Average Total Premium Amount"
      expr: AVG(total_premium_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Net Premium Amount"
      expr: SUM(net_premium_amount)
    - name: "Average Net Premium Amount"
      expr: AVG(net_premium_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
    - name: "Total Total Billed Amount"
      expr: SUM(total_billed_amount)
    - name: "Average Total Billed Amount"
      expr: AVG(total_billed_amount)
    - name: "Total Payment Amount"
      expr: SUM(payment_amount)
    - name: "Average Payment Amount"
      expr: AVG(payment_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_discount`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Discount business metrics"
  source: "`cmoore_customer_demos`.`billing`.`discount`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Currency Code"
      expr: currency_code
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Applicable Member Group"
      expr: applicable_member_group
    - name: "Is Stackable"
      expr: is_stackable
    - name: "Stackable With"
      expr: stackable_with
    - name: "Priority"
      expr: priority
    - name: "Application Method"
      expr: application_method
    - name: "Source"
      expr: source
    - name: "Reason Code"
      expr: reason_code
    - name: "Regulatory Approval Required"
      expr: regulatory_approval_required
    - name: "Regulatory Approval Status"
      expr: regulatory_approval_status
    - name: "Approval Date"
      expr: approval_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Discount"
      expr: COUNT(DISTINCT discount_id)
    - name: "Total Value"
      expr: SUM(value)
    - name: "Average Value"
      expr: AVG(value)
    - name: "Total Min Premium Amount"
      expr: SUM(min_premium_amount)
    - name: "Average Min Premium Amount"
      expr: AVG(min_premium_amount)
    - name: "Total Max Premium Amount"
      expr: SUM(max_premium_amount)
    - name: "Average Max Premium Amount"
      expr: AVG(max_premium_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_discount_application`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Discount Application business metrics"
  source: "`cmoore_customer_demos`.`billing`.`discount_application`"
  dimensions:
    - name: "Discount Type Code"
      expr: discount_type_code
    - name: "Discount Reason Code"
      expr: discount_reason_code
    - name: "Discount Reason Description"
      expr: discount_reason_description
    - name: "Currency Code"
      expr: currency_code
    - name: "Application Method"
      expr: application_method
    - name: "Approval Status"
      expr: approval_status
    - name: "Approval Required Flag"
      expr: approval_required_flag
    - name: "Approved By User Name"
      expr: approved_by_user_name
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Application Date"
      expr: application_date
    - name: "Application Timestamp"
      expr: application_timestamp
    - name: "Promo Code"
      expr: promo_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Discount Application"
      expr: COUNT(DISTINCT discount_application_id)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Discount Percentage"
      expr: SUM(discount_percentage)
    - name: "Average Discount Percentage"
      expr: AVG(discount_percentage)
    - name: "Total Original Premium Amount"
      expr: SUM(original_premium_amount)
    - name: "Average Original Premium Amount"
      expr: AVG(original_premium_amount)
    - name: "Total Discounted Premium Amount"
      expr: SUM(discounted_premium_amount)
    - name: "Average Discounted Premium Amount"
      expr: AVG(discounted_premium_amount)
    - name: "Total Max Discount Amount"
      expr: SUM(max_discount_amount)
    - name: "Average Max Discount Amount"
      expr: AVG(max_discount_amount)
    - name: "Total Min Discount Amount"
      expr: SUM(min_discount_amount)
    - name: "Average Min Discount Amount"
      expr: AVG(min_discount_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_grace_period`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Grace Period business metrics"
  source: "`cmoore_customer_demos`.`billing`.`grace_period`"
  dimensions:
    - name: "Plan Type"
      expr: plan_type
    - name: "Lob"
      expr: lob
    - name: "Funding Arrangement"
      expr: funding_arrangement
    - name: "Duration Days"
      expr: duration_days
    - name: "Marketplace Duration Days"
      expr: marketplace_duration_days
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Applies To New Enrollments"
      expr: applies_to_new_enrollments
    - name: "Applies To Renewals"
      expr: applies_to_renewals
    - name: "Coverage Continues During Grace"
      expr: coverage_continues_during_grace
    - name: "Claims Pended During Grace"
      expr: claims_pended_during_grace
    - name: "Retroactive Termination Allowed"
      expr: retroactive_termination_allowed
    - name: "Retroactive Termination Date"
      expr: retroactive_termination_date
    - name: "Notification Required"
      expr: notification_required
    - name: "Notification Timing Days"
      expr: notification_timing_days
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Grace Period"
      expr: COUNT(DISTINCT grace_period_id)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Late Fee Percentage"
      expr: SUM(late_fee_percentage)
    - name: "Average Late Fee Percentage"
      expr: AVG(late_fee_percentage)
    - name: "Total Minimum Payment Required"
      expr: SUM(minimum_payment_required)
    - name: "Average Minimum Payment Required"
      expr: AVG(minimum_payment_required)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_hold`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Hold business metrics"
  source: "`cmoore_customer_demos`.`billing`.`hold`"
  dimensions:
    - name: "Group Number"
      expr: group_number
    - name: "Type Code"
      expr: type_code
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Status"
      expr: status
    - name: "Placed Date"
      expr: placed_date
    - name: "Placed Timestamp"
      expr: placed_timestamp
    - name: "Released Date"
      expr: released_date
    - name: "Released Timestamp"
      expr: released_timestamp
    - name: "Expected Resolution Date"
      expr: expected_resolution_date
    - name: "Duration Days"
      expr: duration_days
    - name: "Currency Code"
      expr: currency_code
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Code"
      expr: product_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Hold"
      expr: COUNT(DISTINCT hold_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_invoice`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Invoice business metrics"
  source: "`cmoore_customer_demos`.`billing`.`invoice`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Type"
      expr: type
    - name: "Billing Level"
      expr: billing_level
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Date"
      expr: date
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Due Date"
      expr: due_date
    - name: "Grace Period End Date"
      expr: grace_period_end_date
    - name: "Payment Received Date"
      expr: payment_received_date
    - name: "Group Number"
      expr: group_number
    - name: "Group Name"
      expr: group_name
    - name: "Subscriber Name"
      expr: subscriber_name
    - name: "Billing Address Line1"
      expr: billing_address_line1
    - name: "Billing Address Line2"
      expr: billing_address_line2
    - name: "Billing City"
      expr: billing_city
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Invoice"
      expr: COUNT(DISTINCT invoice_id)
    - name: "Total Total Amount Due"
      expr: SUM(total_amount_due)
    - name: "Average Total Amount Due"
      expr: AVG(total_amount_due)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Administrative Fee Amount"
      expr: SUM(administrative_fee_amount)
    - name: "Average Administrative Fee Amount"
      expr: AVG(administrative_fee_amount)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Credit Amount"
      expr: SUM(credit_amount)
    - name: "Average Credit Amount"
      expr: AVG(credit_amount)
    - name: "Total Previous Balance Amount"
      expr: SUM(previous_balance_amount)
    - name: "Average Previous Balance Amount"
      expr: AVG(previous_balance_amount)
    - name: "Total Payment Amount"
      expr: SUM(payment_amount)
    - name: "Average Payment Amount"
      expr: AVG(payment_amount)
    - name: "Total Outstanding Balance Amount"
      expr: SUM(outstanding_balance_amount)
    - name: "Average Outstanding Balance Amount"
      expr: AVG(outstanding_balance_amount)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Pepm Rate"
      expr: SUM(pepm_rate)
    - name: "Average Pepm Rate"
      expr: AVG(pepm_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_late_fee`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Late Fee business metrics"
  source: "`cmoore_customer_demos`.`billing`.`late_fee`"
  dimensions:
    - name: "Policy Number"
      expr: policy_number
    - name: "Fee Type"
      expr: fee_type
    - name: "Fee Reason Code"
      expr: fee_reason_code
    - name: "Fee Description"
      expr: fee_description
    - name: "Fee Currency"
      expr: fee_currency
    - name: "Tax Currency"
      expr: tax_currency
    - name: "Total Currency"
      expr: total_currency
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Days Past Due"
      expr: days_past_due
    - name: "Fee Applied Date"
      expr: fee_applied_date
    - name: "Fee Posted Timestamp"
      expr: fee_posted_timestamp
    - name: "Fee Status"
      expr: fee_status
    - name: "Waiver Applied Flag"
      expr: waiver_applied_flag
    - name: "Waiver Reason"
      expr: waiver_reason
    - name: "Payment Due Date"
      expr: payment_due_date
    - name: "Payment Status"
      expr: payment_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Late Fee"
      expr: COUNT(DISTINCT late_fee_id)
    - name: "Total Fee Amount"
      expr: SUM(fee_amount)
    - name: "Average Fee Amount"
      expr: AVG(fee_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Total Amount Due"
      expr: SUM(total_amount_due)
    - name: "Average Total Amount Due"
      expr: AVG(total_amount_due)
    - name: "Total Overdue Amount"
      expr: SUM(overdue_amount)
    - name: "Average Overdue Amount"
      expr: AVG(overdue_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_payment_method`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Method business metrics"
  source: "`cmoore_customer_demos`.`billing`.`payment_method`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Description"
      expr: description
    - name: "Status"
      expr: status
    - name: "Is Electronic"
      expr: is_electronic
    - name: "Requires Bank Account"
      expr: requires_bank_account
    - name: "Requires Card Details"
      expr: requires_card_details
    - name: "Supports Recurring"
      expr: supports_recurring
    - name: "Supports One Time"
      expr: supports_one_time
    - name: "Supports Refunds"
      expr: supports_refunds
    - name: "Processing Time Days"
      expr: processing_time_days
    - name: "Settlement Time Days"
      expr: settlement_time_days
    - name: "Currency Code"
      expr: currency_code
    - name: "Payment Processor"
      expr: payment_processor
    - name: "Processor Code"
      expr: processor_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Method"
      expr: COUNT(DISTINCT payment_method_id)
    - name: "Total Transaction Fee Amount"
      expr: SUM(transaction_fee_amount)
    - name: "Average Transaction Fee Amount"
      expr: AVG(transaction_fee_amount)
    - name: "Total Transaction Fee Percentage"
      expr: SUM(transaction_fee_percentage)
    - name: "Average Transaction Fee Percentage"
      expr: AVG(transaction_fee_percentage)
    - name: "Total Minimum Amount"
      expr: SUM(minimum_amount)
    - name: "Average Minimum Amount"
      expr: AVG(minimum_amount)
    - name: "Total Maximum Amount"
      expr: SUM(maximum_amount)
    - name: "Average Maximum Amount"
      expr: AVG(maximum_amount)
    - name: "Total Success Rate Percentage"
      expr: SUM(success_rate_percentage)
    - name: "Average Success Rate Percentage"
      expr: AVG(success_rate_percentage)
    - name: "Total Average Transaction Amount"
      expr: SUM(average_transaction_amount)
    - name: "Average Average Transaction Amount"
      expr: AVG(average_transaction_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_payment_processor`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Processor business metrics"
  source: "`cmoore_customer_demos`.`billing`.`payment_processor`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Supported Currencies"
      expr: supported_currencies
    - name: "Settlement Period Days"
      expr: settlement_period_days
    - name: "Processing Method"
      expr: processing_method
    - name: "Channel"
      expr: channel
    - name: "Integration Type"
      expr: integration_type
    - name: "Contact Name"
      expr: contact_name
    - name: "Contact Email"
      expr: contact_email
    - name: "Contact Phone"
      expr: contact_phone
    - name: "Address"
      expr: address
    - name: "Country Code"
      expr: country_code
    - name: "Supports Recurring"
      expr: supports_recurring
    - name: "Supports Refunds"
      expr: supports_refunds
    - name: "Effective Date"
      expr: effective_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Processor"
      expr: COUNT(DISTINCT payment_processor_id)
    - name: "Total Transaction Fee Percent"
      expr: SUM(transaction_fee_percent)
    - name: "Average Transaction Fee Percent"
      expr: AVG(transaction_fee_percent)
    - name: "Total Transaction Fee Fixed Amount"
      expr: SUM(transaction_fee_fixed_amount)
    - name: "Average Transaction Fee Fixed Amount"
      expr: AVG(transaction_fee_fixed_amount)
    - name: "Total Max Transaction Amount"
      expr: SUM(max_transaction_amount)
    - name: "Average Max Transaction Amount"
      expr: AVG(max_transaction_amount)
    - name: "Total Min Transaction Amount"
      expr: SUM(min_transaction_amount)
    - name: "Average Min Transaction Amount"
      expr: AVG(min_transaction_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_payment_reconciliation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Reconciliation business metrics"
  source: "`cmoore_customer_demos`.`billing`.`payment_reconciliation`"
  dimensions:
    - name: "Reconciliation Date"
      expr: reconciliation_date
    - name: "Reconciliation Timestamp"
      expr: reconciliation_timestamp
    - name: "Payment Date"
      expr: payment_date
    - name: "Payment Channel"
      expr: payment_channel
    - name: "Payment Reference Number"
      expr: payment_reference_number
    - name: "Adjustment Reason Code"
      expr: adjustment_reason_code
    - name: "Adjustment Reason Description"
      expr: adjustment_reason_description
    - name: "Reconciliation Status"
      expr: reconciliation_status
    - name: "Reconciliation Type"
      expr: reconciliation_type
    - name: "Match Criteria"
      expr: match_criteria
    - name: "Payer Name"
      expr: payer_name
    - name: "Payer Type"
      expr: payer_type
    - name: "Policy Number"
      expr: policy_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Reconciliation"
      expr: COUNT(DISTINCT payment_reconciliation_id)
    - name: "Total Payment Amount"
      expr: SUM(payment_amount)
    - name: "Average Payment Amount"
      expr: AVG(payment_amount)
    - name: "Total Invoice Amount"
      expr: SUM(invoice_amount)
    - name: "Average Invoice Amount"
      expr: AVG(invoice_amount)
    - name: "Total Applied Amount"
      expr: SUM(applied_amount)
    - name: "Average Applied Amount"
      expr: AVG(applied_amount)
    - name: "Total Unapplied Amount"
      expr: SUM(unapplied_amount)
    - name: "Average Unapplied Amount"
      expr: AVG(unapplied_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Underpayment Amount"
      expr: SUM(underpayment_amount)
    - name: "Average Underpayment Amount"
      expr: AVG(underpayment_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Match Confidence Score"
      expr: SUM(match_confidence_score)
    - name: "Average Match Confidence Score"
      expr: AVG(match_confidence_score)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Refund Amount"
      expr: SUM(refund_amount)
    - name: "Average Refund Amount"
      expr: AVG(refund_amount)
    - name: "Total Credit Balance Amount"
      expr: SUM(credit_balance_amount)
    - name: "Average Credit Balance Amount"
      expr: AVG(credit_balance_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_payment_run`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payment Run business metrics"
  source: "`cmoore_customer_demos`.`billing`.`payment_run`"
  dimensions:
    - name: "Run Number"
      expr: run_number
    - name: "Run Date"
      expr: run_date
    - name: "Run Type"
      expr: run_type
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Currency Code"
      expr: currency_code
    - name: "Processing Timestamp"
      expr: processing_timestamp
    - name: "Posted Timestamp"
      expr: posted_timestamp
    - name: "Grace Period End Date"
      expr: grace_period_end_date
    - name: "Retroactive Flag"
      expr: retroactive_flag
    - name: "Capitation Flag"
      expr: capitation_flag
    - name: "Number Of Members"
      expr: number_of_members
    - name: "Number Of Accounts"
      expr: number_of_accounts
    - name: "Description"
      expr: description
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payment Run"
      expr: COUNT(DISTINCT payment_run_id)
    - name: "Total Total Premium Amount"
      expr: SUM(total_premium_amount)
    - name: "Average Total Premium Amount"
      expr: AVG(total_premium_amount)
    - name: "Total Total Tax Amount"
      expr: SUM(total_tax_amount)
    - name: "Average Total Tax Amount"
      expr: AVG(total_tax_amount)
    - name: "Total Total Adjustments Amount"
      expr: SUM(total_adjustments_amount)
    - name: "Average Total Adjustments Amount"
      expr: AVG(total_adjustments_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Premium Per Member Per Month"
      expr: SUM(premium_per_member_per_month)
    - name: "Average Premium Per Member Per Month"
      expr: AVG(premium_per_member_per_month)
    - name: "Total Premium Per Employee Per Month"
      expr: SUM(premium_per_employee_per_month)
    - name: "Average Premium Per Employee Per Month"
      expr: AVG(premium_per_employee_per_month)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_premium`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Premium business metrics"
  source: "`cmoore_customer_demos`.`billing`.`premium`"
  dimensions:
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Coverage Termination Date"
      expr: coverage_termination_date
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Name"
      expr: plan_name
    - name: "Metal Tier"
      expr: metal_tier
    - name: "Funding Arrangement"
      expr: funding_arrangement
    - name: "Rating Method"
      expr: rating_method
    - name: "Rate Basis"
      expr: rate_basis
    - name: "Family Tier"
      expr: family_tier
    - name: "Retroactive Adjustment Reason"
      expr: retroactive_adjustment_reason
    - name: "Retroactive Period Start Date"
      expr: retroactive_period_start_date
    - name: "Retroactive Period End Date"
      expr: retroactive_period_end_date
    - name: "Payment Status"
      expr: payment_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Premium"
      expr: COUNT(DISTINCT premium_id)
    - name: "Total Base Premium Amount"
      expr: SUM(base_premium_amount)
    - name: "Average Base Premium Amount"
      expr: AVG(base_premium_amount)
    - name: "Total Age Rating Factor"
      expr: SUM(age_rating_factor)
    - name: "Average Age Rating Factor"
      expr: AVG(age_rating_factor)
    - name: "Total Tobacco Surcharge Amount"
      expr: SUM(tobacco_surcharge_amount)
    - name: "Average Tobacco Surcharge Amount"
      expr: AVG(tobacco_surcharge_amount)
    - name: "Total Geographic Rating Factor"
      expr: SUM(geographic_rating_factor)
    - name: "Average Geographic Rating Factor"
      expr: AVG(geographic_rating_factor)
    - name: "Total Family Tier Factor"
      expr: SUM(family_tier_factor)
    - name: "Average Family Tier Factor"
      expr: AVG(family_tier_factor)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
    - name: "Total Wellness Discount Amount"
      expr: SUM(wellness_discount_amount)
    - name: "Average Wellness Discount Amount"
      expr: AVG(wellness_discount_amount)
    - name: "Total Group Discount Amount"
      expr: SUM(group_discount_amount)
    - name: "Average Group Discount Amount"
      expr: AVG(group_discount_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Employee Contribution Amount"
      expr: SUM(employee_contribution_amount)
    - name: "Average Employee Contribution Amount"
      expr: AVG(employee_contribution_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_premium_calculation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Premium Calculation business metrics"
  source: "`cmoore_customer_demos`.`billing`.`premium_calculation`"
  dimensions:
    - name: "Policy Number"
      expr: policy_number
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Premium Frequency"
      expr: premium_frequency
    - name: "Premium Type"
      expr: premium_type
    - name: "Calculation Method"
      expr: calculation_method
    - name: "Grace Period Days"
      expr: grace_period_days
    - name: "Retroactive Adjustment Flag"
      expr: retroactive_adjustment_flag
    - name: "Billing Cycle Start"
      expr: billing_cycle_start
    - name: "Billing Cycle End"
      expr: billing_cycle_end
    - name: "Payment Due Date"
      expr: payment_due_date
    - name: "Payment Status"
      expr: payment_status
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Channel"
      expr: payment_channel
    - name: "Capitation Payment Flag"
      expr: capitation_payment_flag
    - name: "Discount Type"
      expr: discount_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Premium Calculation"
      expr: COUNT(DISTINCT premium_calculation_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Rate Per Member"
      expr: SUM(rate_per_member)
    - name: "Average Rate Per Member"
      expr: AVG(rate_per_member)
    - name: "Total Rate Per Employee"
      expr: SUM(rate_per_employee)
    - name: "Average Rate Per Employee"
      expr: AVG(rate_per_employee)
    - name: "Total Retroactive Adjustment Amount"
      expr: SUM(retroactive_adjustment_amount)
    - name: "Average Retroactive Adjustment Amount"
      expr: AVG(retroactive_adjustment_amount)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Tax Rate"
      expr: SUM(tax_rate)
    - name: "Average Tax Rate"
      expr: AVG(tax_rate)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Rebate Amount"
      expr: SUM(rebate_amount)
    - name: "Average Rebate Amount"
      expr: AVG(rebate_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_premium_rate`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Premium Rate business metrics"
  source: "`cmoore_customer_demos`.`billing`.`premium_rate`"
  dimensions:
    - name: "Rate Schedule Code"
      expr: rate_schedule_code
    - name: "Lob"
      expr: lob
    - name: "Plan Type"
      expr: plan_type
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Rating Area Code"
      expr: rating_area_code
    - name: "Age Band"
      expr: age_band
    - name: "Tobacco Use Indicator"
      expr: tobacco_use_indicator
    - name: "Rate Basis"
      expr: rate_basis
    - name: "Rate Type"
      expr: rate_type
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Rate Filing Number"
      expr: rate_filing_number
    - name: "Rate Filing Date"
      expr: rate_filing_date
    - name: "Rate Approval Date"
      expr: rate_approval_date
    - name: "Rate Approval Status"
      expr: rate_approval_status
    - name: "State Code"
      expr: state_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Premium Rate"
      expr: COUNT(DISTINCT premium_rate_id)
    - name: "Total Rate Amount"
      expr: SUM(rate_amount)
    - name: "Average Rate Amount"
      expr: AVG(rate_amount)
    - name: "Total Actuarial Value"
      expr: SUM(actuarial_value)
    - name: "Average Actuarial Value"
      expr: AVG(actuarial_value)
    - name: "Total Participation Requirement Percentage"
      expr: SUM(participation_requirement_percentage)
    - name: "Average Participation Requirement Percentage"
      expr: AVG(participation_requirement_percentage)
    - name: "Total Contribution Requirement Percentage"
      expr: SUM(contribution_requirement_percentage)
    - name: "Average Contribution Requirement Percentage"
      expr: AVG(contribution_requirement_percentage)
    - name: "Total Risk Adjustment Factor"
      expr: SUM(risk_adjustment_factor)
    - name: "Average Risk Adjustment Factor"
      expr: AVG(risk_adjustment_factor)
    - name: "Total Hcc Score"
      expr: SUM(hcc_score)
    - name: "Average Hcc Score"
      expr: AVG(hcc_score)
    - name: "Total Gender Rating Factor"
      expr: SUM(gender_rating_factor)
    - name: "Average Gender Rating Factor"
      expr: AVG(gender_rating_factor)
    - name: "Total Family Size Factor"
      expr: SUM(family_size_factor)
    - name: "Average Family Size Factor"
      expr: AVG(family_size_factor)
    - name: "Total Geographic Adjustment Factor"
      expr: SUM(geographic_adjustment_factor)
    - name: "Average Geographic Adjustment Factor"
      expr: AVG(geographic_adjustment_factor)
    - name: "Total Wellness Program Discount Percentage"
      expr: SUM(wellness_program_discount_percentage)
    - name: "Average Wellness Program Discount Percentage"
      expr: AVG(wellness_program_discount_percentage)
    - name: "Total Rate Increase Percentage"
      expr: SUM(rate_increase_percentage)
    - name: "Average Rate Increase Percentage"
      expr: AVG(rate_increase_percentage)
    - name: "Total Medical Trend Factor"
      expr: SUM(medical_trend_factor)
    - name: "Average Medical Trend Factor"
      expr: AVG(medical_trend_factor)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_retroactive_adjustment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Retroactive Adjustment business metrics"
  source: "`cmoore_customer_demos`.`billing`.`retroactive_adjustment`"
  dimensions:
    - name: "Original Billing Period Start Date"
      expr: original_billing_period_start_date
    - name: "Original Billing Period End Date"
      expr: original_billing_period_end_date
    - name: "Adjustment Processed Date"
      expr: adjustment_processed_date
    - name: "Adjustment Approved Date"
      expr: adjustment_approved_date
    - name: "Adjustment Requested Date"
      expr: adjustment_requested_date
    - name: "Policy Number"
      expr: policy_number
    - name: "Group Number"
      expr: group_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Coverage Tier"
      expr: coverage_tier
    - name: "Adjustment Direction"
      expr: adjustment_direction
    - name: "Currency Code"
      expr: currency_code
    - name: "Member Count Original"
      expr: member_count_original
    - name: "Member Count Adjusted"
      expr: member_count_adjusted
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Retroactive Adjustment"
      expr: COUNT(DISTINCT retroactive_adjustment_id)
    - name: "Total Original Premium Amount"
      expr: SUM(original_premium_amount)
    - name: "Average Original Premium Amount"
      expr: AVG(original_premium_amount)
    - name: "Total Adjusted Premium Amount"
      expr: SUM(adjusted_premium_amount)
    - name: "Average Adjusted Premium Amount"
      expr: AVG(adjusted_premium_amount)
    - name: "Total Original Rate"
      expr: SUM(original_rate)
    - name: "Average Original Rate"
      expr: AVG(original_rate)
    - name: "Total Adjusted Rate"
      expr: SUM(adjusted_rate)
    - name: "Average Adjusted Rate"
      expr: AVG(adjusted_rate)
    - name: "Total Rate Change Percentage"
      expr: SUM(rate_change_percentage)
    - name: "Average Rate Change Percentage"
      expr: AVG(rate_change_percentage)
    - name: "Total Pmpm Original"
      expr: SUM(pmpm_original)
    - name: "Average Pmpm Original"
      expr: AVG(pmpm_original)
    - name: "Total Pmpm Adjusted"
      expr: SUM(pmpm_adjusted)
    - name: "Average Pmpm Adjusted"
      expr: AVG(pmpm_adjusted)
    - name: "Total Pepm Original"
      expr: SUM(pepm_original)
    - name: "Average Pepm Original"
      expr: AVG(pepm_original)
    - name: "Total Pepm Adjusted"
      expr: SUM(pepm_adjusted)
    - name: "Average Pepm Adjusted"
      expr: AVG(pepm_adjusted)
    - name: "Total Accounts Receivable Impact"
      expr: SUM(accounts_receivable_impact)
    - name: "Average Accounts Receivable Impact"
      expr: AVG(accounts_receivable_impact)
    - name: "Total Revenue Impact"
      expr: SUM(revenue_impact)
    - name: "Average Revenue Impact"
      expr: AVG(revenue_impact)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_status`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Status business metrics"
  source: "`cmoore_customer_demos`.`billing`.`status`"
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
    - name: "Is Collectible"
      expr: is_collectible
    - name: "Is Reversible"
      expr: is_reversible
    - name: "Is Final"
      expr: is_final
    - name: "Requires Payment"
      expr: requires_payment
    - name: "Allows Grace Period"
      expr: allows_grace_period
    - name: "Triggers Termination"
      expr: triggers_termination
    - name: "Triggers Notification"
      expr: triggers_notification
    - name: "Impacts Eligibility"
      expr: impacts_eligibility
    - name: "Impacts Claims"
      expr: impacts_claims
    - name: "Aging Category"
      expr: aging_category
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Status"
      expr: COUNT(DISTINCT status_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Collection Probability Percent"
      expr: SUM(collection_probability_percent)
    - name: "Average Collection Probability Percent"
      expr: AVG(collection_probability_percent)
    - name: "Total Reserve Percentage"
      expr: SUM(reserve_percentage)
    - name: "Average Reserve Percentage"
      expr: AVG(reserve_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_surcharge`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Surcharge business metrics"
  source: "`cmoore_customer_demos`.`billing`.`surcharge`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Calculation Basis"
      expr: calculation_basis
    - name: "Lob"
      expr: lob
    - name: "Product Type"
      expr: product_type
    - name: "Eligibility Criteria"
      expr: eligibility_criteria
    - name: "Tobacco Use Indicator"
      expr: tobacco_use_indicator
    - name: "Age Based Indicator"
      expr: age_based_indicator
    - name: "Geographic Based Indicator"
      expr: geographic_based_indicator
    - name: "Risk Adjustment Indicator"
      expr: risk_adjustment_indicator
    - name: "Regulatory Mandated Indicator"
      expr: regulatory_mandated_indicator
    - name: "Taxable Indicator"
      expr: taxable_indicator
    - name: "Mlr Included Indicator"
      expr: mlr_included_indicator
    - name: "Waivable Indicator"
      expr: waivable_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Surcharge"
      expr: COUNT(DISTINCT surcharge_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Percentage"
      expr: SUM(percentage)
    - name: "Average Percentage"
      expr: AVG(percentage)
    - name: "Total Minimum Surcharge Amount"
      expr: SUM(minimum_surcharge_amount)
    - name: "Average Minimum Surcharge Amount"
      expr: AVG(minimum_surcharge_amount)
    - name: "Total Maximum Surcharge Amount"
      expr: SUM(maximum_surcharge_amount)
    - name: "Average Maximum Surcharge Amount"
      expr: AVG(maximum_surcharge_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`billing_write_off`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Write Off business metrics"
  source: "`cmoore_customer_demos`.`billing`.`write_off`"
  dimensions:
    - name: "Group Number"
      expr: group_number
    - name: "Policy Number"
      expr: policy_number
    - name: "Lob"
      expr: lob
    - name: "Date"
      expr: date
    - name: "Reason Code"
      expr: reason_code
    - name: "Reason Description"
      expr: reason_description
    - name: "Category"
      expr: category
    - name: "Approval Status"
      expr: approval_status
    - name: "Approved By"
      expr: approved_by
    - name: "Approval Date"
      expr: approval_date
    - name: "Requested By"
      expr: requested_by
    - name: "Request Date"
      expr: request_date
    - name: "Billing Period Start Date"
      expr: billing_period_start_date
    - name: "Billing Period End Date"
      expr: billing_period_end_date
    - name: "Due Date"
      expr: due_date
    - name: "Grace Period End Date"
      expr: grace_period_end_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Write Off"
      expr: COUNT(DISTINCT write_off_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Original Billed Amount"
      expr: SUM(original_billed_amount)
    - name: "Average Original Billed Amount"
      expr: AVG(original_billed_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
    - name: "Total Recovery Amount"
      expr: SUM(recovery_amount)
    - name: "Average Recovery Amount"
      expr: AVG(recovery_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
$$;