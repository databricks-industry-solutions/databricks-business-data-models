-- Metric views for domain: sales | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:05:52

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_activity`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Activity business metrics"
  source: "`cmoore_customer_demos`.`sales`.`activity`"
  dimensions:
    - name: "Type"
      expr: type
    - name: "Date"
      expr: date
    - name: "Timestamp"
      expr: timestamp
    - name: "Duration Minutes"
      expr: duration_minutes
    - name: "Subject"
      expr: subject
    - name: "Description"
      expr: description
    - name: "Outcome"
      expr: outcome
    - name: "Status"
      expr: status
    - name: "Priority"
      expr: priority
    - name: "Direction"
      expr: direction
    - name: "Sales Team Name"
      expr: sales_team_name
    - name: "Broker Name"
      expr: broker_name
    - name: "Account Name"
      expr: account_name
    - name: "Contact Name"
      expr: contact_name
    - name: "Contact Email"
      expr: contact_email
    - name: "Contact Phone"
      expr: contact_phone
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Activity"
      expr: COUNT(DISTINCT activity_id)
    - name: "Total Estimated Premium Amount"
      expr: SUM(estimated_premium_amount)
    - name: "Average Estimated Premium Amount"
      expr: AVG(estimated_premium_amount)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Sentiment Score"
      expr: SUM(sentiment_score)
    - name: "Average Sentiment Score"
      expr: AVG(sentiment_score)
    - name: "Total Probability Percent"
      expr: SUM(probability_percent)
    - name: "Average Probability Percent"
      expr: AVG(probability_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_broker`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Broker business metrics"
  source: "`cmoore_customer_demos`.`sales`.`broker`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Tin"
      expr: tin
    - name: "Legal Name"
      expr: legal_name
    - name: "Doing Business As Name"
      expr: doing_business_as_name
    - name: "Type"
      expr: type
    - name: "Primary Contact First Name"
      expr: primary_contact_first_name
    - name: "Primary Contact Last Name"
      expr: primary_contact_last_name
    - name: "Primary Contact Title"
      expr: primary_contact_title
    - name: "Primary Email"
      expr: primary_email
    - name: "Secondary Email"
      expr: secondary_email
    - name: "Primary Phone"
      expr: primary_phone
    - name: "Secondary Phone"
      expr: secondary_phone
    - name: "Fax Number"
      expr: fax_number
    - name: "Website Url"
      expr: website_url
    - name: "Business Address Line 1"
      expr: business_address_line_1
    - name: "Business Address Line 2"
      expr: business_address_line_2
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Broker"
      expr: COUNT(DISTINCT broker_id)
    - name: "Total Errors And Omissions Coverage Amount"
      expr: SUM(errors_and_omissions_coverage_amount)
    - name: "Average Errors And Omissions Coverage Amount"
      expr: AVG(errors_and_omissions_coverage_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_broker_campaign_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Broker Campaign Assignment business metrics"
  source: "`cmoore_customer_demos`.`sales`.`broker_campaign_assignment`"
  dimensions:
    - name: "Assigned Date"
      expr: assigned_date
    - name: "Territory Coverage"
      expr: territory_coverage
    - name: "Performance Tier"
      expr: performance_tier
    - name: "Target Enrollment Count"
      expr: target_enrollment_count
    - name: "Actual Enrollment Count"
      expr: actual_enrollment_count
    - name: "Assignment Status"
      expr: assignment_status
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Assigned Date Month"
      expr: DATE_TRUNC('MONTH', assigned_date)
    - name: "Start Date Month"
      expr: DATE_TRUNC('MONTH', start_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Broker Campaign Assignment"
      expr: COUNT(DISTINCT assignment_id)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_broker_program_appointment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Broker Program Appointment business metrics"
  source: "`cmoore_customer_demos`.`sales`.`broker_program_appointment`"
  dimensions:
    - name: "Appointment Date"
      expr: appointment_date
    - name: "Certification Status"
      expr: certification_status
    - name: "Certification Expiration Date"
      expr: certification_expiration_date
    - name: "Territory Assignment"
      expr: territory_assignment
    - name: "Commission Tier"
      expr: commission_tier
    - name: "Appointment Type"
      expr: appointment_type
    - name: "Appointment Status"
      expr: appointment_status
    - name: "Appointment End Date"
      expr: appointment_end_date
    - name: "Termination Reason"
      expr: termination_reason
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Appointment Date Month"
      expr: DATE_TRUNC('MONTH', appointment_date)
    - name: "Certification Expiration Date Month"
      expr: DATE_TRUNC('MONTH', certification_expiration_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Broker Program Appointment"
      expr: COUNT(DISTINCT broker_program_appointment_id)
    - name: "Total Commission Rate Percentage"
      expr: SUM(commission_rate_percentage)
    - name: "Average Commission Rate Percentage"
      expr: AVG(commission_rate_percentage)
    - name: "Total Annual Enrollment Quota"
      expr: SUM(annual_enrollment_quota)
    - name: "Average Annual Enrollment Quota"
      expr: AVG(annual_enrollment_quota)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_broker_program_participation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Broker Program Participation business metrics"
  source: "`cmoore_customer_demos`.`sales`.`broker_program_participation`"
  dimensions:
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Certification Status"
      expr: certification_status
    - name: "Performance Tier"
      expr: performance_tier
    - name: "Program Effective Date"
      expr: program_effective_date
    - name: "Program End Date"
      expr: program_end_date
    - name: "Enrollment Date Month"
      expr: DATE_TRUNC('MONTH', enrollment_date)
    - name: "Program Effective Date Month"
      expr: DATE_TRUNC('MONTH', program_effective_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Broker Program Participation"
      expr: COUNT(DISTINCT broker_program_participation_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_channel_campaign_execution`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Channel Campaign Execution business metrics"
  source: "`cmoore_customer_demos`.`sales`.`channel_campaign_execution`"
  dimensions:
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Priority Level"
      expr: priority_level
    - name: "Expected Lead Volume"
      expr: expected_lead_volume
    - name: "Actual Lead Volume"
      expr: actual_lead_volume
    - name: "Execution Status"
      expr: execution_status
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Start Date Month"
      expr: DATE_TRUNC('MONTH', start_date)
    - name: "End Date Month"
      expr: DATE_TRUNC('MONTH', end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Channel Campaign Execution"
      expr: COUNT(DISTINCT channel_campaign_execution_id)
    - name: "Total Channel Budget Allocation"
      expr: SUM(channel_budget_allocation)
    - name: "Average Channel Budget Allocation"
      expr: AVG(channel_budget_allocation)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_commission`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Commission business metrics"
  source: "`cmoore_customer_demos`.`sales`.`commission`"
  dimensions:
    - name: "Agent Name"
      expr: agent_name
    - name: "Agent Type"
      expr: agent_type
    - name: "Agent License Number"
      expr: agent_license_number
    - name: "Broker Type"
      expr: broker_type
    - name: "Broker License Number"
      expr: broker_license_number
    - name: "Broker License State"
      expr: broker_license_state
    - name: "Broker Npi"
      expr: broker_npi
    - name: "Policy Number"
      expr: policy_number
    - name: "Group Number"
      expr: group_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Year"
      expr: plan_year
    - name: "Sale Date"
      expr: sale_date
    - name: "Effective Date"
      expr: effective_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Commission"
      expr: COUNT(DISTINCT commission_id)
    - name: "Total Rate"
      expr: SUM(rate)
    - name: "Average Rate"
      expr: AVG(rate)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Gross Commission Amount"
      expr: SUM(gross_commission_amount)
    - name: "Average Gross Commission Amount"
      expr: AVG(gross_commission_amount)
    - name: "Total Net Commission Amount"
      expr: SUM(net_commission_amount)
    - name: "Average Net Commission Amount"
      expr: AVG(net_commission_amount)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Basis Amount"
      expr: SUM(basis_amount)
    - name: "Average Basis Amount"
      expr: AVG(basis_amount)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Split Percentage"
      expr: SUM(split_percentage)
    - name: "Average Split Percentage"
      expr: AVG(split_percentage)
    - name: "Total Override Amount"
      expr: SUM(override_amount)
    - name: "Average Override Amount"
      expr: AVG(override_amount)
    - name: "Total Bonus Amount"
      expr: SUM(bonus_amount)
    - name: "Average Bonus Amount"
      expr: AVG(bonus_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_commission_statement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Commission Statement business metrics"
  source: "`cmoore_customer_demos`.`sales`.`commission_statement`"
  dimensions:
    - name: "Statement Number"
      expr: statement_number
    - name: "Sales Channel"
      expr: sales_channel
    - name: "Product Type"
      expr: product_type
    - name: "Policy Number"
      expr: policy_number
    - name: "Enrollment Date"
      expr: enrollment_date
    - name: "Payment Date"
      expr: payment_date
    - name: "Payment Method"
      expr: payment_method
    - name: "Currency Code"
      expr: currency_code
    - name: "Status"
      expr: status
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Approved Timestamp"
      expr: approved_timestamp
    - name: "Processed Timestamp"
      expr: processed_timestamp
    - name: "Notes"
      expr: notes
    - name: "Enrollment Date Month"
      expr: DATE_TRUNC('MONTH', enrollment_date)
    - name: "Payment Date Month"
      expr: DATE_TRUNC('MONTH', payment_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Commission Statement"
      expr: COUNT(DISTINCT commission_statement_id)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Tax Withheld"
      expr: SUM(tax_withheld)
    - name: "Average Tax Withheld"
      expr: AVG(tax_withheld)
    - name: "Total Net Commission"
      expr: SUM(net_commission)
    - name: "Average Net Commission"
      expr: AVG(net_commission)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_compensation_plan`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Compensation Plan business metrics"
  source: "`cmoore_customer_demos`.`sales`.`compensation_plan`"
  dimensions:
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Description"
      expr: plan_description
    - name: "Plan Type"
      expr: plan_type
    - name: "Plan Status"
      expr: plan_status
    - name: "Lob"
      expr: lob
    - name: "Product Category"
      expr: product_category
    - name: "Agent Type"
      expr: agent_type
    - name: "Commission Basis"
      expr: commission_basis
    - name: "Commission Frequency"
      expr: commission_frequency
    - name: "Bonus Eligible Flag"
      expr: bonus_eligible_flag
    - name: "Bonus Type"
      expr: bonus_type
    - name: "Performance Threshold Unit"
      expr: performance_threshold_unit
    - name: "Cap Period"
      expr: cap_period
    - name: "Chargeback Policy"
      expr: chargeback_policy
    - name: "Chargeback Period Months"
      expr: chargeback_period_months
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Compensation Plan"
      expr: COUNT(DISTINCT compensation_plan_id)
    - name: "Total Commission Rate Percent"
      expr: SUM(commission_rate_percent)
    - name: "Average Commission Rate Percent"
      expr: AVG(commission_rate_percent)
    - name: "Total First Year Commission Rate Percent"
      expr: SUM(first_year_commission_rate_percent)
    - name: "Average First Year Commission Rate Percent"
      expr: AVG(first_year_commission_rate_percent)
    - name: "Total Renewal Commission Rate Percent"
      expr: SUM(renewal_commission_rate_percent)
    - name: "Average Renewal Commission Rate Percent"
      expr: AVG(renewal_commission_rate_percent)
    - name: "Total Bonus Amount"
      expr: SUM(bonus_amount)
    - name: "Average Bonus Amount"
      expr: AVG(bonus_amount)
    - name: "Total Bonus Rate Percent"
      expr: SUM(bonus_rate_percent)
    - name: "Average Bonus Rate Percent"
      expr: AVG(bonus_rate_percent)
    - name: "Total Performance Threshold Value"
      expr: SUM(performance_threshold_value)
    - name: "Average Performance Threshold Value"
      expr: AVG(performance_threshold_value)
    - name: "Total Minimum Production Requirement"
      expr: SUM(minimum_production_requirement)
    - name: "Average Minimum Production Requirement"
      expr: AVG(minimum_production_requirement)
    - name: "Total Cap Amount"
      expr: SUM(cap_amount)
    - name: "Average Cap Amount"
      expr: AVG(cap_amount)
    - name: "Total Override Rate Percent"
      expr: SUM(override_rate_percent)
    - name: "Average Override Rate Percent"
      expr: AVG(override_rate_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_enrollment_request`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Enrollment Request business metrics"
  source: "`cmoore_customer_demos`.`sales`.`enrollment_request`"
  dimensions:
    - name: "Request Number"
      expr: request_number
    - name: "Request Date"
      expr: request_date
    - name: "Request Timestamp"
      expr: request_timestamp
    - name: "Request Status"
      expr: request_status
    - name: "Request Type"
      expr: request_type
    - name: "Request Source"
      expr: request_source
    - name: "Lob"
      expr: lob
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Plan Year"
      expr: plan_year
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Coverage Termination Date"
      expr: coverage_termination_date
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Sep Reason Code"
      expr: sep_reason_code
    - name: "Sep Reason Description"
      expr: sep_reason_description
    - name: "Subscriber First Name"
      expr: subscriber_first_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Enrollment Request"
      expr: COUNT(DISTINCT enrollment_request_id)
    - name: "Total Agent Commission Rate"
      expr: SUM(agent_commission_rate)
    - name: "Average Agent Commission Rate"
      expr: AVG(agent_commission_rate)
    - name: "Total Monthly Premium Amount"
      expr: SUM(monthly_premium_amount)
    - name: "Average Monthly Premium Amount"
      expr: AVG(monthly_premium_amount)
    - name: "Total Subscriber Premium Amount"
      expr: SUM(subscriber_premium_amount)
    - name: "Average Subscriber Premium Amount"
      expr: AVG(subscriber_premium_amount)
    - name: "Total Dependent Premium Amount"
      expr: SUM(dependent_premium_amount)
    - name: "Average Dependent Premium Amount"
      expr: AVG(dependent_premium_amount)
    - name: "Total Aptc Amount"
      expr: SUM(aptc_amount)
    - name: "Average Aptc Amount"
      expr: AVG(aptc_amount)
    - name: "Total Household Income Amount"
      expr: SUM(household_income_amount)
    - name: "Average Household Income Amount"
      expr: AVG(household_income_amount)
    - name: "Total Federal Poverty Level Percentage"
      expr: SUM(federal_poverty_level_percentage)
    - name: "Average Federal Poverty Level Percentage"
      expr: AVG(federal_poverty_level_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_incentive_program`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Incentive Program business metrics"
  source: "`cmoore_customer_demos`.`sales`.`incentive_program`"
  dimensions:
    - name: "Program Code"
      expr: program_code
    - name: "Program Name"
      expr: program_name
    - name: "Program Description"
      expr: program_description
    - name: "Program Type"
      expr: program_type
    - name: "Lob"
      expr: lob
    - name: "Product Category"
      expr: product_category
    - name: "Participant Role"
      expr: participant_role
    - name: "Eligibility Criteria"
      expr: eligibility_criteria
    - name: "Performance Metric"
      expr: performance_metric
    - name: "Measurement Period Type"
      expr: measurement_period_type
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Enrollment Start Date"
      expr: enrollment_start_date
    - name: "Enrollment End Date"
      expr: enrollment_end_date
    - name: "Performance Period Start Date"
      expr: performance_period_start_date
    - name: "Performance Period End Date"
      expr: performance_period_end_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Incentive Program"
      expr: COUNT(DISTINCT incentive_program_id)
    - name: "Total Base Commission Rate"
      expr: SUM(base_commission_rate)
    - name: "Average Base Commission Rate"
      expr: AVG(base_commission_rate)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Cap Amount"
      expr: SUM(cap_amount)
    - name: "Average Cap Amount"
      expr: AVG(cap_amount)
    - name: "Total Accelerator Threshold"
      expr: SUM(accelerator_threshold)
    - name: "Average Accelerator Threshold"
      expr: AVG(accelerator_threshold)
    - name: "Total Accelerator Multiplier"
      expr: SUM(accelerator_multiplier)
    - name: "Average Accelerator Multiplier"
      expr: AVG(accelerator_multiplier)
    - name: "Total Residual Payment Rate"
      expr: SUM(residual_payment_rate)
    - name: "Average Residual Payment Rate"
      expr: AVG(residual_payment_rate)
    - name: "Total Override Commission Rate"
      expr: SUM(override_commission_rate)
    - name: "Average Override Commission Rate"
      expr: AVG(override_commission_rate)
    - name: "Total Budget Amount"
      expr: SUM(budget_amount)
    - name: "Average Budget Amount"
      expr: AVG(budget_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_lead_source`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Lead Source business metrics"
  source: "`cmoore_customer_demos`.`sales`.`lead_source`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Category"
      expr: category
    - name: "Channel"
      expr: channel
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "Market Segment"
      expr: market_segment
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Cost Currency Code"
      expr: cost_currency_code
    - name: "Priority Rank"
      expr: priority_rank
    - name: "Attribution Method"
      expr: attribution_method
    - name: "Tracking Code"
      expr: tracking_code
    - name: "Vendor Name"
      expr: vendor_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Lead Source"
      expr: COUNT(DISTINCT lead_source_id)
    - name: "Total Cost Per Lead"
      expr: SUM(cost_per_lead)
    - name: "Average Cost Per Lead"
      expr: AVG(cost_per_lead)
    - name: "Total Conversion Rate Percent"
      expr: SUM(conversion_rate_percent)
    - name: "Average Conversion Rate Percent"
      expr: AVG(conversion_rate_percent)
    - name: "Total Lead Quality Score"
      expr: SUM(lead_quality_score)
    - name: "Average Lead Quality Score"
      expr: AVG(lead_quality_score)
    - name: "Total Budget Allocated"
      expr: SUM(budget_allocated)
    - name: "Average Budget Allocated"
      expr: AVG(budget_allocated)
    - name: "Total Data Quality Threshold Percent"
      expr: SUM(data_quality_threshold_percent)
    - name: "Average Data Quality Threshold Percent"
      expr: AVG(data_quality_threshold_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_medical_director`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Medical Director business metrics"
  source: "`cmoore_customer_demos`.`sales`.`medical_director`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Last Name"
      expr: last_name
    - name: "Full Name"
      expr: full_name
    - name: "Title"
      expr: title
    - name: "Department"
      expr: department
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
    - name: "Country"
      expr: country
    - name: "License Number"
      expr: license_number
    - name: "License State"
      expr: license_state
    - name: "Specialty"
      expr: specialty
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Medical Director"
      expr: COUNT(DISTINCT medical_director_id)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_opportunity`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Opportunity business metrics"
  source: "`cmoore_customer_demos`.`sales`.`opportunity`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Lob"
      expr: lob
    - name: "Product Type"
      expr: product_type
    - name: "Campaign Code"
      expr: campaign_code
    - name: "Expected Close Date"
      expr: expected_close_date
    - name: "Actual Close Date"
      expr: actual_close_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Enrollment Period"
      expr: enrollment_period
    - name: "Fiscal Year"
      expr: fiscal_year
    - name: "Fiscal Quarter"
      expr: fiscal_quarter
    - name: "Group Size"
      expr: group_size
    - name: "Estimated Member Count"
      expr: estimated_member_count
    - name: "Quote Number"
      expr: quote_number
    - name: "Quote Date"
      expr: quote_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Opportunity"
      expr: COUNT(DISTINCT opportunity_id)
    - name: "Total Probability Percent"
      expr: SUM(probability_percent)
    - name: "Average Probability Percent"
      expr: AVG(probability_percent)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Expected Revenue"
      expr: SUM(expected_revenue)
    - name: "Average Expected Revenue"
      expr: AVG(expected_revenue)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Pepm Rate"
      expr: SUM(pepm_rate)
    - name: "Average Pepm Rate"
      expr: AVG(pepm_rate)
    - name: "Total Commission Rate Percent"
      expr: SUM(commission_rate_percent)
    - name: "Average Commission Rate Percent"
      expr: AVG(commission_rate_percent)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
    - name: "Total Minimum Participation Percent"
      expr: SUM(minimum_participation_percent)
    - name: "Average Minimum Participation Percent"
      expr: AVG(minimum_participation_percent)
    - name: "Total Employer Contribution Percent"
      expr: SUM(employer_contribution_percent)
    - name: "Average Employer Contribution Percent"
      expr: AVG(employer_contribution_percent)
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
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_opportunity_stage`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Opportunity Stage business metrics"
  source: "`cmoore_customer_demos`.`sales`.`opportunity_stage`"
  dimensions:
    - name: "Stage Code"
      expr: stage_code
    - name: "Stage Name"
      expr: stage_name
    - name: "Stage Category"
      expr: stage_category
    - name: "Stage Type"
      expr: stage_type
    - name: "Display Order"
      expr: display_order
    - name: "Is Active"
      expr: is_active
    - name: "Is Closed"
      expr: is_closed
    - name: "Is Won"
      expr: is_won
    - name: "Forecast Category"
      expr: forecast_category
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Sales Channel"
      expr: sales_channel
    - name: "Product Type"
      expr: product_type
    - name: "Market Segment"
      expr: market_segment
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Requires Underwriting"
      expr: requires_underwriting
    - name: "Requires Quote"
      expr: requires_quote
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Opportunity Stage"
      expr: COUNT(DISTINCT opportunity_stage_id)
    - name: "Total Probability Percentage"
      expr: SUM(probability_percentage)
    - name: "Average Probability Percentage"
      expr: AVG(probability_percentage)
    - name: "Total Commission Percentage"
      expr: SUM(commission_percentage)
    - name: "Average Commission Percentage"
      expr: AVG(commission_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_order`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Order business metrics"
  source: "`cmoore_customer_demos`.`sales`.`order`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Date"
      expr: date
    - name: "Timestamp"
      expr: timestamp
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Type"
      expr: type
    - name: "Lob"
      expr: lob
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Plan Year"
      expr: plan_year
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Subscriber First Name"
      expr: subscriber_first_name
    - name: "Subscriber Last Name"
      expr: subscriber_last_name
    - name: "Subscriber Date Of Birth"
      expr: subscriber_date_of_birth
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Order"
      expr: COUNT(DISTINCT order_id)
    - name: "Total Broker Commission Rate"
      expr: SUM(broker_commission_rate)
    - name: "Average Broker Commission Rate"
      expr: AVG(broker_commission_rate)
    - name: "Total Broker Commission Amount"
      expr: SUM(broker_commission_amount)
    - name: "Average Broker Commission Amount"
      expr: AVG(broker_commission_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Member Responsibility Amount"
      expr: SUM(member_responsibility_amount)
    - name: "Average Member Responsibility Amount"
      expr: AVG(member_responsibility_amount)
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
    - name: "Total Tobacco Surcharge Amount"
      expr: SUM(tobacco_surcharge_amount)
    - name: "Average Tobacco Surcharge Amount"
      expr: AVG(tobacco_surcharge_amount)
    - name: "Total Actuarial Value"
      expr: SUM(actuarial_value)
    - name: "Average Actuarial Value"
      expr: AVG(actuarial_value)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_order_line`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Order Line business metrics"
  source: "`cmoore_customer_demos`.`sales`.`order_line`"
  dimensions:
    - name: "Line Number"
      expr: line_number
    - name: "Benefit Type"
      expr: benefit_type
    - name: "Coverage Code"
      expr: coverage_code
    - name: "Quantity"
      expr: quantity
    - name: "Unit Of Measure"
      expr: unit_of_measure
    - name: "Tax Code"
      expr: tax_code
    - name: "Currency Code"
      expr: currency_code
    - name: "Line Status"
      expr: line_status
    - name: "Fulfillment Method"
      expr: fulfillment_method
    - name: "Shipping Address"
      expr: shipping_address
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Approved Timestamp"
      expr: approved_timestamp
    - name: "Fulfilled Timestamp"
      expr: fulfilled_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Order Line"
      expr: COUNT(DISTINCT order_line_id)
    - name: "Total Unit Price"
      expr: SUM(unit_price)
    - name: "Average Unit Price"
      expr: AVG(unit_price)
    - name: "Total Discount Percent"
      expr: SUM(discount_percent)
    - name: "Average Discount Percent"
      expr: AVG(discount_percent)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Net Price"
      expr: SUM(net_price)
    - name: "Average Net Price"
      expr: AVG(net_price)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_proposal`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Proposal business metrics"
  source: "`cmoore_customer_demos`.`sales`.`proposal`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Lob"
      expr: lob
    - name: "Market Segment"
      expr: market_segment
    - name: "Funding Arrangement"
      expr: funding_arrangement
    - name: "Plan Design Type"
      expr: plan_design_type
    - name: "Number Of Plan Options"
      expr: number_of_plan_options
    - name: "Employer Group Name"
      expr: employer_group_name
    - name: "Employer Tin"
      expr: employer_tin
    - name: "Employer Sic Code"
      expr: employer_sic_code
    - name: "Employer Naics Code"
      expr: employer_naics_code
    - name: "Employer Address Line 1"
      expr: employer_address_line_1
    - name: "Employer Address Line 2"
      expr: employer_address_line_2
    - name: "Employer City"
      expr: employer_city
    - name: "Employer State"
      expr: employer_state
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Proposal"
      expr: COUNT(DISTINCT proposal_id)
    - name: "Total Commission Rate Percent"
      expr: SUM(commission_rate_percent)
    - name: "Average Commission Rate Percent"
      expr: AVG(commission_rate_percent)
    - name: "Total Estimated Annual Premium"
      expr: SUM(estimated_annual_premium)
    - name: "Average Estimated Annual Premium"
      expr: AVG(estimated_annual_premium)
    - name: "Total Estimated Monthly Premium"
      expr: SUM(estimated_monthly_premium)
    - name: "Average Estimated Monthly Premium"
      expr: AVG(estimated_monthly_premium)
    - name: "Total Actuarial Value Percent"
      expr: SUM(actuarial_value_percent)
    - name: "Average Actuarial Value Percent"
      expr: AVG(actuarial_value_percent)
    - name: "Total Individual Deductible In Network"
      expr: SUM(individual_deductible_in_network)
    - name: "Average Individual Deductible In Network"
      expr: AVG(individual_deductible_in_network)
    - name: "Total Family Deductible In Network"
      expr: SUM(family_deductible_in_network)
    - name: "Average Family Deductible In Network"
      expr: AVG(family_deductible_in_network)
    - name: "Total Individual Oop Max In Network"
      expr: SUM(individual_oop_max_in_network)
    - name: "Average Individual Oop Max In Network"
      expr: AVG(individual_oop_max_in_network)
    - name: "Total Family Oop Max In Network"
      expr: SUM(family_oop_max_in_network)
    - name: "Average Family Oop Max In Network"
      expr: AVG(family_oop_max_in_network)
    - name: "Total Primary Care Copay"
      expr: SUM(primary_care_copay)
    - name: "Average Primary Care Copay"
      expr: AVG(primary_care_copay)
    - name: "Total Specialist Copay"
      expr: SUM(specialist_copay)
    - name: "Average Specialist Copay"
      expr: AVG(specialist_copay)
    - name: "Total Emergency Room Copay"
      expr: SUM(emergency_room_copay)
    - name: "Average Emergency Room Copay"
      expr: AVG(emergency_room_copay)
    - name: "Total Urgent Care Copay"
      expr: SUM(urgent_care_copay)
    - name: "Average Urgent Care Copay"
      expr: AVG(urgent_care_copay)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_quote`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Quote business metrics"
  source: "`cmoore_customer_demos`.`sales`.`quote`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Version"
      expr: version
    - name: "Status"
      expr: status
    - name: "Type"
      expr: type
    - name: "Lob"
      expr: lob
    - name: "Product Type"
      expr: product_type
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Code"
      expr: plan_code
    - name: "Metal Tier"
      expr: metal_tier
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Coverage Termination Date"
      expr: coverage_termination_date
    - name: "Generated Date"
      expr: generated_date
    - name: "Generated Timestamp"
      expr: generated_timestamp
    - name: "Sent Date"
      expr: sent_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Accepted Date"
      expr: accepted_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Quote"
      expr: COUNT(DISTINCT quote_id)
    - name: "Total Total Premium Amount"
      expr: SUM(total_premium_amount)
    - name: "Average Total Premium Amount"
      expr: AVG(total_premium_amount)
    - name: "Total Employee Premium Amount"
      expr: SUM(employee_premium_amount)
    - name: "Average Employee Premium Amount"
      expr: AVG(employee_premium_amount)
    - name: "Total Employee Spouse Premium Amount"
      expr: SUM(employee_spouse_premium_amount)
    - name: "Average Employee Spouse Premium Amount"
      expr: AVG(employee_spouse_premium_amount)
    - name: "Total Employee Children Premium Amount"
      expr: SUM(employee_children_premium_amount)
    - name: "Average Employee Children Premium Amount"
      expr: AVG(employee_children_premium_amount)
    - name: "Total Family Premium Amount"
      expr: SUM(family_premium_amount)
    - name: "Average Family Premium Amount"
      expr: AVG(family_premium_amount)
    - name: "Total Individual Premium Amount"
      expr: SUM(individual_premium_amount)
    - name: "Average Individual Premium Amount"
      expr: AVG(individual_premium_amount)
    - name: "Total Pmpm Rate"
      expr: SUM(pmpm_rate)
    - name: "Average Pmpm Rate"
      expr: AVG(pmpm_rate)
    - name: "Total Pepm Rate"
      expr: SUM(pepm_rate)
    - name: "Average Pepm Rate"
      expr: AVG(pepm_rate)
    - name: "Total Deductible Individual"
      expr: SUM(deductible_individual)
    - name: "Average Deductible Individual"
      expr: AVG(deductible_individual)
    - name: "Total Deductible Family"
      expr: SUM(deductible_family)
    - name: "Average Deductible Family"
      expr: AVG(deductible_family)
    - name: "Total Oop Max Individual"
      expr: SUM(oop_max_individual)
    - name: "Average Oop Max Individual"
      expr: AVG(oop_max_individual)
    - name: "Total Oop Max Family"
      expr: SUM(oop_max_family)
    - name: "Average Oop Max Family"
      expr: AVG(oop_max_family)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_region`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Region business metrics"
  source: "`cmoore_customer_demos`.`sales`.`region`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Type"
      expr: type
    - name: "Hierarchy Level"
      expr: hierarchy_level
    - name: "Parent Region Code"
      expr: parent_region_code
    - name: "Geographic Scope"
      expr: geographic_scope
    - name: "State Codes"
      expr: state_codes
    - name: "Country Code"
      expr: country_code
    - name: "Time Zone"
      expr: time_zone
    - name: "Lob Coverage"
      expr: lob_coverage
    - name: "Channel Coverage"
      expr: channel_coverage
    - name: "Market Segment"
      expr: market_segment
    - name: "Quota Currency Code"
      expr: quota_currency_code
    - name: "Quota Measurement Type"
      expr: quota_measurement_type
    - name: "Regional Manager Name"
      expr: regional_manager_name
    - name: "Regional Manager Email"
      expr: regional_manager_email
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Region"
      expr: COUNT(DISTINCT region_id)
    - name: "Total Annual Quota Amount"
      expr: SUM(annual_quota_amount)
    - name: "Average Annual Quota Amount"
      expr: AVG(annual_quota_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_sales_channel`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sales Channel business metrics"
  source: "`cmoore_customer_demos`.`sales`.`sales_channel`"
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
    - name: "Product Category"
      expr: product_category
    - name: "Enrollment Period Type"
      expr: enrollment_period_type
    - name: "Target Market Segment"
      expr: target_market_segment
    - name: "Distribution Method"
      expr: distribution_method
    - name: "Status"
      expr: status
    - name: "Is Broker Enabled"
      expr: is_broker_enabled
    - name: "Is Agent Enabled"
      expr: is_agent_enabled
    - name: "Is Direct Enrollment"
      expr: is_direct_enrollment
    - name: "Commission Structure Type"
      expr: commission_structure_type
    - name: "Sales Territory"
      expr: sales_territory
    - name: "Regulatory Approval Required"
      expr: regulatory_approval_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sales Channel"
      expr: COUNT(DISTINCT sales_channel_id)
    - name: "Total Default Commission Rate"
      expr: SUM(default_commission_rate)
    - name: "Average Default Commission Rate"
      expr: AVG(default_commission_rate)
    - name: "Total Revenue Target Amount"
      expr: SUM(revenue_target_amount)
    - name: "Average Revenue Target Amount"
      expr: AVG(revenue_target_amount)
    - name: "Total Cost Per Acquisition Target"
      expr: SUM(cost_per_acquisition_target)
    - name: "Average Cost Per Acquisition Target"
      expr: AVG(cost_per_acquisition_target)
    - name: "Total Marketing Budget Amount"
      expr: SUM(marketing_budget_amount)
    - name: "Average Marketing Budget Amount"
      expr: AVG(marketing_budget_amount)
    - name: "Total Average Deal Size"
      expr: SUM(average_deal_size)
    - name: "Average Average Deal Size"
      expr: AVG(average_deal_size)
    - name: "Total Conversion Rate Target"
      expr: SUM(conversion_rate_target)
    - name: "Average Conversion Rate Target"
      expr: AVG(conversion_rate_target)
    - name: "Total Retention Rate Target"
      expr: SUM(retention_rate_target)
    - name: "Average Retention Rate Target"
      expr: AVG(retention_rate_target)
    - name: "Total Quality Assurance Sampling Rate"
      expr: SUM(quality_assurance_sampling_rate)
    - name: "Average Quality Assurance Sampling Rate"
      expr: AVG(quality_assurance_sampling_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_sales_policy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sales Policy business metrics"
  source: "`cmoore_customer_demos`.`sales`.`sales_policy`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Group Policy Number"
      expr: group_policy_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Metal Tier"
      expr: metal_tier
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Subscriber First Name"
      expr: subscriber_first_name
    - name: "Subscriber Last Name"
      expr: subscriber_last_name
    - name: "Subscriber Date Of Birth"
      expr: subscriber_date_of_birth
    - name: "Subscriber Ssn"
      expr: subscriber_ssn
    - name: "Subscriber Email"
      expr: subscriber_email
    - name: "Subscriber Phone"
      expr: subscriber_phone
    - name: "Subscriber Address Line 1"
      expr: subscriber_address_line_1
    - name: "Subscriber Address Line 2"
      expr: subscriber_address_line_2
    - name: "Subscriber City"
      expr: subscriber_city
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sales Policy"
      expr: COUNT(DISTINCT sales_policy_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Subscriber Premium Amount"
      expr: SUM(subscriber_premium_amount)
    - name: "Average Subscriber Premium Amount"
      expr: AVG(subscriber_premium_amount)
    - name: "Total Employer Contribution Amount"
      expr: SUM(employer_contribution_amount)
    - name: "Average Employer Contribution Amount"
      expr: AVG(employer_contribution_amount)
    - name: "Total Subsidy Amount"
      expr: SUM(subsidy_amount)
    - name: "Average Subsidy Amount"
      expr: AVG(subsidy_amount)
    - name: "Total Deductible Individual"
      expr: SUM(deductible_individual)
    - name: "Average Deductible Individual"
      expr: AVG(deductible_individual)
    - name: "Total Deductible Family"
      expr: SUM(deductible_family)
    - name: "Average Deductible Family"
      expr: AVG(deductible_family)
    - name: "Total Out Of Pocket Max Individual"
      expr: SUM(out_of_pocket_max_individual)
    - name: "Average Out Of Pocket Max Individual"
      expr: AVG(out_of_pocket_max_individual)
    - name: "Total Out Of Pocket Max Family"
      expr: SUM(out_of_pocket_max_family)
    - name: "Average Out Of Pocket Max Family"
      expr: AVG(out_of_pocket_max_family)
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
    - name: "Total Coinsurance Rate"
      expr: SUM(coinsurance_rate)
    - name: "Average Coinsurance Rate"
      expr: AVG(coinsurance_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_sales_representative`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sales Representative business metrics"
  source: "`cmoore_customer_demos`.`sales`.`sales_representative`"
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
    - name: "Sales Channel"
      expr: sales_channel
    - name: "Region Code"
      expr: region_code
    - name: "Territory"
      expr: territory
    - name: "Commission Structure"
      expr: commission_structure
    - name: "Performance Rating"
      expr: performance_rating
    - name: "License Number"
      expr: license_number
    - name: "License Expiration Date"
      expr: license_expiration_date
    - name: "Language Preference"
      expr: language_preference
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sales Representative"
      expr: COUNT(DISTINCT sales_representative_id)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Annual Quota Amount"
      expr: SUM(annual_quota_amount)
    - name: "Average Annual Quota Amount"
      expr: AVG(annual_quota_amount)
    - name: "Total Actual Annual Sales"
      expr: SUM(actual_annual_sales)
    - name: "Average Actual Annual Sales"
      expr: AVG(actual_annual_sales)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_sales_transaction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Sales Transaction business metrics"
  source: "`cmoore_customer_demos`.`sales`.`sales_transaction`"
  dimensions:
    - name: "Transaction Type"
      expr: transaction_type
    - name: "Transaction Status"
      expr: transaction_status
    - name: "Transaction Date"
      expr: transaction_date
    - name: "Channel"
      expr: channel
    - name: "Product Code"
      expr: product_code
    - name: "Policy Number"
      expr: policy_number
    - name: "Currency Code"
      expr: currency_code
    - name: "Coverage Start Date"
      expr: coverage_start_date
    - name: "Coverage End Date"
      expr: coverage_end_date
    - name: "Enrollment Period"
      expr: enrollment_period
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Status"
      expr: payment_status
    - name: "Payment Date"
      expr: payment_date
    - name: "Is New Business"
      expr: is_new_business
    - name: "Is Renewal"
      expr: is_renewal
    - name: "Is Cancelled"
      expr: is_cancelled
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Sales Transaction"
      expr: COUNT(DISTINCT sales_transaction_id)
    - name: "Total Premium Amount"
      expr: SUM(premium_amount)
    - name: "Average Premium Amount"
      expr: AVG(premium_amount)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Total Amount"
      expr: SUM(total_amount)
    - name: "Average Total Amount"
      expr: AVG(total_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_target`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Target business metrics"
  source: "`cmoore_customer_demos`.`sales`.`target`"
  dimensions:
    - name: "Broker Name"
      expr: broker_name
    - name: "Broker Email"
      expr: broker_email
    - name: "Broker Phone"
      expr: broker_phone
    - name: "Market"
      expr: market
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Type"
      expr: type
    - name: "Measurement Unit"
      expr: measurement_unit
    - name: "Currency Code"
      expr: currency_code
    - name: "Period Start Date"
      expr: period_start_date
    - name: "Period End Date"
      expr: period_end_date
    - name: "Status"
      expr: status
    - name: "Approval Status"
      expr: approval_status
    - name: "Approved By Name"
      expr: approved_by_name
    - name: "Approved By Email"
      expr: approved_by_email
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Target"
      expr: COUNT(DISTINCT target_id)
    - name: "Total Value"
      expr: SUM(value)
    - name: "Average Value"
      expr: AVG(value)
    - name: "Total Commission Rate"
      expr: SUM(commission_rate)
    - name: "Average Commission Rate"
      expr: AVG(commission_rate)
    - name: "Total Commission Amount"
      expr: SUM(commission_amount)
    - name: "Average Commission Amount"
      expr: AVG(commission_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_underwriter`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Underwriter business metrics"
  source: "`cmoore_customer_demos`.`sales`.`underwriter`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Last Name"
      expr: last_name
    - name: "Full Name"
      expr: full_name
    - name: "Email"
      expr: email
    - name: "Phone Number"
      expr: phone_number
    - name: "Employee Number"
      expr: employee_number
    - name: "License Number"
      expr: license_number
    - name: "License State"
      expr: license_state
    - name: "License Expiration Date"
      expr: license_expiration_date
    - name: "Underwriter Type"
      expr: underwriter_type
    - name: "Department Code"
      expr: department_code
    - name: "Manager Name"
      expr: manager_name
    - name: "Status"
      expr: status
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Currency Code"
      expr: currency_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Underwriter"
      expr: COUNT(DISTINCT underwriter_id)
    - name: "Total Max Approval Limit"
      expr: SUM(max_approval_limit)
    - name: "Average Max Approval Limit"
      expr: AVG(max_approval_limit)
    - name: "Total Commission Rate Percent"
      expr: SUM(commission_rate_percent)
    - name: "Average Commission Rate Percent"
      expr: AVG(commission_rate_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`sales_underwriting_decision`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Underwriting Decision business metrics"
  source: "`cmoore_customer_demos`.`sales`.`underwriting_decision`"
  dimensions:
    - name: "Decision Status"
      expr: decision_status
    - name: "Decision Outcome"
      expr: decision_outcome
    - name: "Decision Date"
      expr: decision_date
    - name: "Decision Timestamp"
      expr: decision_timestamp
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Lob"
      expr: lob
    - name: "Product Type"
      expr: product_type
    - name: "Plan Code"
      expr: plan_code
    - name: "Plan Name"
      expr: plan_name
    - name: "Underwriter Name"
      expr: underwriter_name
    - name: "Underwriting Method"
      expr: underwriting_method
    - name: "Hcc Count"
      expr: hcc_count
    - name: "Medical Underwriting Required"
      expr: medical_underwriting_required
    - name: "Health Questionnaire Completed"
      expr: health_questionnaire_completed
    - name: "Pre Existing Conditions Identified"
      expr: pre_existing_conditions_identified
    - name: "Tobacco User"
      expr: tobacco_user
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Underwriting Decision"
      expr: COUNT(DISTINCT underwriting_decision_id)
    - name: "Total Raf Score"
      expr: SUM(raf_score)
    - name: "Average Raf Score"
      expr: AVG(raf_score)
    - name: "Total Age Rated Premium Amount"
      expr: SUM(age_rated_premium_amount)
    - name: "Average Age Rated Premium Amount"
      expr: AVG(age_rated_premium_amount)
    - name: "Total Tobacco Rated Premium Amount"
      expr: SUM(tobacco_rated_premium_amount)
    - name: "Average Tobacco Rated Premium Amount"
      expr: AVG(tobacco_rated_premium_amount)
    - name: "Total Total Premium Amount"
      expr: SUM(total_premium_amount)
    - name: "Average Total Premium Amount"
      expr: AVG(total_premium_amount)
    - name: "Total Participation Rate"
      expr: SUM(participation_rate)
    - name: "Average Participation Rate"
      expr: AVG(participation_rate)
    - name: "Total Employer Contribution Percentage"
      expr: SUM(employer_contribution_percentage)
    - name: "Average Employer Contribution Percentage"
      expr: AVG(employer_contribution_percentage)
    - name: "Total Medical Loss Ratio Projection"
      expr: SUM(medical_loss_ratio_projection)
    - name: "Average Medical Loss Ratio Projection"
      expr: AVG(medical_loss_ratio_projection)
    - name: "Total Broker Commission Percentage"
      expr: SUM(broker_commission_percentage)
    - name: "Average Broker Commission Percentage"
      expr: AVG(broker_commission_percentage)
    - name: "Total Actuarial Value"
      expr: SUM(actuarial_value)
    - name: "Average Actuarial Value"
      expr: AVG(actuarial_value)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Out Of Pocket Maximum"
      expr: SUM(out_of_pocket_maximum)
    - name: "Average Out Of Pocket Maximum"
      expr: AVG(out_of_pocket_maximum)
    - name: "Total Coinsurance Percentage"
      expr: SUM(coinsurance_percentage)
    - name: "Average Coinsurance Percentage"
      expr: AVG(coinsurance_percentage)
$$;