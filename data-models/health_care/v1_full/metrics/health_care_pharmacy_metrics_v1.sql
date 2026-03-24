-- Metric views for domain: pharmacy | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:06:50

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_benefit_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Benefit Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`benefit_pharmacy`"
  dimensions:
    - name: "Formulary Name"
      expr: formulary_name
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Coverage Type"
      expr: coverage_type
    - name: "Network Type"
      expr: network_type
    - name: "Deductible Applies To Tiers"
      expr: deductible_applies_to_tiers
    - name: "Coverage Gap Applies"
      expr: coverage_gap_applies
    - name: "Mail Order Enabled"
      expr: mail_order_enabled
    - name: "Mail Order Day Supply"
      expr: mail_order_day_supply
    - name: "Retail Day Supply"
      expr: retail_day_supply
    - name: "Specialty Pharmacy Required"
      expr: specialty_pharmacy_required
    - name: "Prior Authorization Required Tiers"
      expr: prior_authorization_required_tiers
    - name: "Step Therapy Applies"
      expr: step_therapy_applies
    - name: "Quantity Limit Applies"
      expr: quantity_limit_applies
    - name: "Generic Substitution Required"
      expr: generic_substitution_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Benefit Pharmacy"
      expr: COUNT(DISTINCT benefit_pharmacy_id)
    - name: "Total Tier 1 Copay Amount"
      expr: SUM(tier_1_copay_amount)
    - name: "Average Tier 1 Copay Amount"
      expr: AVG(tier_1_copay_amount)
    - name: "Total Tier 1 Coinsurance Percent"
      expr: SUM(tier_1_coinsurance_percent)
    - name: "Average Tier 1 Coinsurance Percent"
      expr: AVG(tier_1_coinsurance_percent)
    - name: "Total Tier 2 Copay Amount"
      expr: SUM(tier_2_copay_amount)
    - name: "Average Tier 2 Copay Amount"
      expr: AVG(tier_2_copay_amount)
    - name: "Total Tier 2 Coinsurance Percent"
      expr: SUM(tier_2_coinsurance_percent)
    - name: "Average Tier 2 Coinsurance Percent"
      expr: AVG(tier_2_coinsurance_percent)
    - name: "Total Tier 3 Copay Amount"
      expr: SUM(tier_3_copay_amount)
    - name: "Average Tier 3 Copay Amount"
      expr: AVG(tier_3_copay_amount)
    - name: "Total Tier 3 Coinsurance Percent"
      expr: SUM(tier_3_coinsurance_percent)
    - name: "Average Tier 3 Coinsurance Percent"
      expr: AVG(tier_3_coinsurance_percent)
    - name: "Total Tier 4 Copay Amount"
      expr: SUM(tier_4_copay_amount)
    - name: "Average Tier 4 Copay Amount"
      expr: AVG(tier_4_copay_amount)
    - name: "Total Tier 4 Coinsurance Percent"
      expr: SUM(tier_4_coinsurance_percent)
    - name: "Average Tier 4 Coinsurance Percent"
      expr: AVG(tier_4_coinsurance_percent)
    - name: "Total Tier 5 Copay Amount"
      expr: SUM(tier_5_copay_amount)
    - name: "Average Tier 5 Copay Amount"
      expr: AVG(tier_5_copay_amount)
    - name: "Total Tier 5 Coinsurance Percent"
      expr: SUM(tier_5_coinsurance_percent)
    - name: "Average Tier 5 Coinsurance Percent"
      expr: AVG(tier_5_coinsurance_percent)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Out Of Pocket Maximum"
      expr: SUM(out_of_pocket_maximum)
    - name: "Average Out Of Pocket Maximum"
      expr: AVG(out_of_pocket_maximum)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_claim_adj`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Claim Adj business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`claim_adj`"
  dimensions:
    - name: "Adjustment Reason Code"
      expr: adjustment_reason_code
    - name: "Adjustment Reason Description"
      expr: adjustment_reason_description
    - name: "Adjustment Timestamp"
      expr: adjustment_timestamp
    - name: "Effective Date"
      expr: effective_date
    - name: "Original Days Supply"
      expr: original_days_supply
    - name: "Adjusted Days Supply"
      expr: adjusted_days_supply
    - name: "Ndc"
      expr: ndc
    - name: "Pharmacy Npi"
      expr: pharmacy_npi
    - name: "Prescriber Npi"
      expr: prescriber_npi
    - name: "Group Number"
      expr: group_number
    - name: "Pbm Processor"
      expr: pbm_processor
    - name: "Adjustment Status"
      expr: adjustment_status
    - name: "Reversal Indicator"
      expr: reversal_indicator
    - name: "Cob Indicator"
      expr: cob_indicator
    - name: "Original Service Date"
      expr: original_service_date
    - name: "Original Submission Date"
      expr: original_submission_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Claim Adj"
      expr: COUNT(DISTINCT claim_adj_id)
    - name: "Total Original Paid Amount"
      expr: SUM(original_paid_amount)
    - name: "Average Original Paid Amount"
      expr: AVG(original_paid_amount)
    - name: "Total Adjusted Paid Amount"
      expr: SUM(adjusted_paid_amount)
    - name: "Average Adjusted Paid Amount"
      expr: AVG(adjusted_paid_amount)
    - name: "Total Original Ingredient Cost"
      expr: SUM(original_ingredient_cost)
    - name: "Average Original Ingredient Cost"
      expr: AVG(original_ingredient_cost)
    - name: "Total Adjusted Ingredient Cost"
      expr: SUM(adjusted_ingredient_cost)
    - name: "Average Adjusted Ingredient Cost"
      expr: AVG(adjusted_ingredient_cost)
    - name: "Total Original Dispensing Fee"
      expr: SUM(original_dispensing_fee)
    - name: "Average Original Dispensing Fee"
      expr: AVG(original_dispensing_fee)
    - name: "Total Adjusted Dispensing Fee"
      expr: SUM(adjusted_dispensing_fee)
    - name: "Average Adjusted Dispensing Fee"
      expr: AVG(adjusted_dispensing_fee)
    - name: "Total Original Patient Pay Amount"
      expr: SUM(original_patient_pay_amount)
    - name: "Average Original Patient Pay Amount"
      expr: AVG(original_patient_pay_amount)
    - name: "Total Adjusted Patient Pay Amount"
      expr: SUM(adjusted_patient_pay_amount)
    - name: "Average Adjusted Patient Pay Amount"
      expr: AVG(adjusted_patient_pay_amount)
    - name: "Total Original Copay Amount"
      expr: SUM(original_copay_amount)
    - name: "Average Original Copay Amount"
      expr: AVG(original_copay_amount)
    - name: "Total Adjusted Copay Amount"
      expr: SUM(adjusted_copay_amount)
    - name: "Average Adjusted Copay Amount"
      expr: AVG(adjusted_copay_amount)
    - name: "Total Original Coinsurance Amount"
      expr: SUM(original_coinsurance_amount)
    - name: "Average Original Coinsurance Amount"
      expr: AVG(original_coinsurance_amount)
    - name: "Total Adjusted Coinsurance Amount"
      expr: SUM(adjusted_coinsurance_amount)
    - name: "Average Adjusted Coinsurance Amount"
      expr: AVG(adjusted_coinsurance_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_claim_denial`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Claim Denial business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`claim_denial`"
  dimensions:
    - name: "Denial Reason"
      expr: denial_reason
    - name: "Denial Date"
      expr: denial_date
    - name: "Denial Timestamp"
      expr: denial_timestamp
    - name: "Appeal Eligible Flag"
      expr: appeal_eligible_flag
    - name: "Appeal Deadline Date"
      expr: appeal_deadline_date
    - name: "Appeal Filed Date"
      expr: appeal_filed_date
    - name: "Appeal Resolution Date"
      expr: appeal_resolution_date
    - name: "Appeal Outcome"
      expr: appeal_outcome
    - name: "Member Name"
      expr: member_name
    - name: "Member Date Of Birth"
      expr: member_date_of_birth
    - name: "Group Number"
      expr: group_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Pharmacy Npi"
      expr: pharmacy_npi
    - name: "Pharmacy Name"
      expr: pharmacy_name
    - name: "Prescriber Npi"
      expr: prescriber_npi
    - name: "Prescriber Name"
      expr: prescriber_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Claim Denial"
      expr: COUNT(DISTINCT claim_denial_id)
    - name: "Total Denied Amount"
      expr: SUM(denied_amount)
    - name: "Average Denied Amount"
      expr: AVG(denied_amount)
    - name: "Total Submitted Amount"
      expr: SUM(submitted_amount)
    - name: "Average Submitted Amount"
      expr: AVG(submitted_amount)
    - name: "Total Quantity Denied"
      expr: SUM(quantity_denied)
    - name: "Average Quantity Denied"
      expr: AVG(quantity_denied)
    - name: "Total Maximum Allowed Quantity"
      expr: SUM(maximum_allowed_quantity)
    - name: "Average Maximum Allowed Quantity"
      expr: AVG(maximum_allowed_quantity)
    - name: "Total Member Responsibility Amount"
      expr: SUM(member_responsibility_amount)
    - name: "Average Member Responsibility Amount"
      expr: AVG(member_responsibility_amount)
    - name: "Total Awp Unit Price"
      expr: SUM(awp_unit_price)
    - name: "Average Awp Unit Price"
      expr: AVG(awp_unit_price)
    - name: "Total Mac Unit Price"
      expr: SUM(mac_unit_price)
    - name: "Average Mac Unit Price"
      expr: AVG(mac_unit_price)
    - name: "Total Dispensing Fee"
      expr: SUM(dispensing_fee)
    - name: "Average Dispensing Fee"
      expr: AVG(dispensing_fee)
    - name: "Total Denial Financial Impact"
      expr: SUM(denial_financial_impact)
    - name: "Average Denial Financial Impact"
      expr: AVG(denial_financial_impact)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_claim_line`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Claim Line business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`claim_line`"
  dimensions:
    - name: "Pharmacy Npi"
      expr: pharmacy_npi
    - name: "Prescriber Npi"
      expr: prescriber_npi
    - name: "Ndc Code"
      expr: ndc_code
    - name: "Drug Name"
      expr: drug_name
    - name: "Drug Strength"
      expr: drug_strength
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Days Supply"
      expr: days_supply
    - name: "Refill Number"
      expr: refill_number
    - name: "Prescription Number"
      expr: prescription_number
    - name: "Date Written"
      expr: date_written
    - name: "Date Filled"
      expr: date_filled
    - name: "Date Submitted"
      expr: date_submitted
    - name: "Date Processed"
      expr: date_processed
    - name: "Date Paid"
      expr: date_paid
    - name: "Denial Reason Code"
      expr: denial_reason_code
    - name: "Denial Reason Description"
      expr: denial_reason_description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Claim Line"
      expr: COUNT(DISTINCT claim_line_id)
    - name: "Total Quantity Dispensed"
      expr: SUM(quantity_dispensed)
    - name: "Average Quantity Dispensed"
      expr: AVG(quantity_dispensed)
    - name: "Total Ingredient Cost Submitted"
      expr: SUM(ingredient_cost_submitted)
    - name: "Average Ingredient Cost Submitted"
      expr: AVG(ingredient_cost_submitted)
    - name: "Total Dispensing Fee Submitted"
      expr: SUM(dispensing_fee_submitted)
    - name: "Average Dispensing Fee Submitted"
      expr: AVG(dispensing_fee_submitted)
    - name: "Total Sales Tax Submitted"
      expr: SUM(sales_tax_submitted)
    - name: "Average Sales Tax Submitted"
      expr: AVG(sales_tax_submitted)
    - name: "Total Total Amount Submitted"
      expr: SUM(total_amount_submitted)
    - name: "Average Total Amount Submitted"
      expr: AVG(total_amount_submitted)
    - name: "Total Ingredient Cost Paid"
      expr: SUM(ingredient_cost_paid)
    - name: "Average Ingredient Cost Paid"
      expr: AVG(ingredient_cost_paid)
    - name: "Total Dispensing Fee Paid"
      expr: SUM(dispensing_fee_paid)
    - name: "Average Dispensing Fee Paid"
      expr: AVG(dispensing_fee_paid)
    - name: "Total Sales Tax Paid"
      expr: SUM(sales_tax_paid)
    - name: "Average Sales Tax Paid"
      expr: AVG(sales_tax_paid)
    - name: "Total Total Amount Paid"
      expr: SUM(total_amount_paid)
    - name: "Average Total Amount Paid"
      expr: AVG(total_amount_paid)
    - name: "Total Member Copay Amount"
      expr: SUM(member_copay_amount)
    - name: "Average Member Copay Amount"
      expr: AVG(member_copay_amount)
    - name: "Total Member Coinsurance Amount"
      expr: SUM(member_coinsurance_amount)
    - name: "Average Member Coinsurance Amount"
      expr: AVG(member_coinsurance_amount)
    - name: "Total Member Deductible Amount"
      expr: SUM(member_deductible_amount)
    - name: "Average Member Deductible Amount"
      expr: AVG(member_deductible_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_claim_txn`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Claim Txn business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`claim_txn`"
  dimensions:
    - name: "Rx Number"
      expr: rx_number
    - name: "Fill Number"
      expr: fill_number
    - name: "Group Number"
      expr: group_number
    - name: "Person Code"
      expr: person_code
    - name: "Patient First Name"
      expr: patient_first_name
    - name: "Patient Last Name"
      expr: patient_last_name
    - name: "Patient Date Of Birth"
      expr: patient_date_of_birth
    - name: "Patient Gender"
      expr: patient_gender
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Drug Strength"
      expr: drug_strength
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Days Supply"
      expr: days_supply
    - name: "Date Of Service"
      expr: date_of_service
    - name: "Date Prescription Written"
      expr: date_prescription_written
    - name: "Prescriber First Name"
      expr: prescriber_first_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Claim Txn"
      expr: COUNT(DISTINCT claim_txn_id)
    - name: "Total Quantity Dispensed"
      expr: SUM(quantity_dispensed)
    - name: "Average Quantity Dispensed"
      expr: AVG(quantity_dispensed)
    - name: "Total Ingredient Cost Submitted"
      expr: SUM(ingredient_cost_submitted)
    - name: "Average Ingredient Cost Submitted"
      expr: AVG(ingredient_cost_submitted)
    - name: "Total Dispensing Fee Submitted"
      expr: SUM(dispensing_fee_submitted)
    - name: "Average Dispensing Fee Submitted"
      expr: AVG(dispensing_fee_submitted)
    - name: "Total Total Amount Submitted"
      expr: SUM(total_amount_submitted)
    - name: "Average Total Amount Submitted"
      expr: AVG(total_amount_submitted)
    - name: "Total Ingredient Cost Paid"
      expr: SUM(ingredient_cost_paid)
    - name: "Average Ingredient Cost Paid"
      expr: AVG(ingredient_cost_paid)
    - name: "Total Dispensing Fee Paid"
      expr: SUM(dispensing_fee_paid)
    - name: "Average Dispensing Fee Paid"
      expr: AVG(dispensing_fee_paid)
    - name: "Total Sales Tax Paid"
      expr: SUM(sales_tax_paid)
    - name: "Average Sales Tax Paid"
      expr: AVG(sales_tax_paid)
    - name: "Total Incentive Amount Paid"
      expr: SUM(incentive_amount_paid)
    - name: "Average Incentive Amount Paid"
      expr: AVG(incentive_amount_paid)
    - name: "Total Total Amount Paid"
      expr: SUM(total_amount_paid)
    - name: "Average Total Amount Paid"
      expr: AVG(total_amount_paid)
    - name: "Total Patient Pay Amount"
      expr: SUM(patient_pay_amount)
    - name: "Average Patient Pay Amount"
      expr: AVG(patient_pay_amount)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Amount"
      expr: SUM(coinsurance_amount)
    - name: "Average Coinsurance Amount"
      expr: AVG(coinsurance_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_contract_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contract Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`contract_pharmacy`"
  dimensions:
    - name: "Contract Type"
      expr: contract_type
    - name: "Contract Status"
      expr: contract_status
    - name: "Pharmacy Name"
      expr: pharmacy_name
    - name: "Pharmacy Dba Name"
      expr: pharmacy_dba_name
    - name: "Pharmacy Chain Code"
      expr: pharmacy_chain_code
    - name: "Pharmacy Address Line 1"
      expr: pharmacy_address_line_1
    - name: "Pharmacy Address Line 2"
      expr: pharmacy_address_line_2
    - name: "Pharmacy City"
      expr: pharmacy_city
    - name: "Pharmacy State"
      expr: pharmacy_state
    - name: "Pharmacy Zip Code"
      expr: pharmacy_zip_code
    - name: "Pharmacy Country Code"
      expr: pharmacy_country_code
    - name: "Pharmacy Phone Number"
      expr: pharmacy_phone_number
    - name: "Pharmacy Fax Number"
      expr: pharmacy_fax_number
    - name: "Pharmacy Email Address"
      expr: pharmacy_email_address
    - name: "Network Tier"
      expr: network_tier
    - name: "Network Participation Status"
      expr: network_participation_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contract Pharmacy"
      expr: COUNT(DISTINCT contract_pharmacy_id)
    - name: "Total Awp Discount Percentage"
      expr: SUM(awp_discount_percentage)
    - name: "Average Awp Discount Percentage"
      expr: AVG(awp_discount_percentage)
    - name: "Total Dispensing Fee Amount"
      expr: SUM(dispensing_fee_amount)
    - name: "Average Dispensing Fee Amount"
      expr: AVG(dispensing_fee_amount)
    - name: "Total Generic Dispensing Fee Amount"
      expr: SUM(generic_dispensing_fee_amount)
    - name: "Average Generic Dispensing Fee Amount"
      expr: AVG(generic_dispensing_fee_amount)
    - name: "Total Brand Dispensing Fee Amount"
      expr: SUM(brand_dispensing_fee_amount)
    - name: "Average Brand Dispensing Fee Amount"
      expr: AVG(brand_dispensing_fee_amount)
    - name: "Total Specialty Dispensing Fee Amount"
      expr: SUM(specialty_dispensing_fee_amount)
    - name: "Average Specialty Dispensing Fee Amount"
      expr: AVG(specialty_dispensing_fee_amount)
    - name: "Total Compound Dispensing Fee Amount"
      expr: SUM(compound_dispensing_fee_amount)
    - name: "Average Compound Dispensing Fee Amount"
      expr: AVG(compound_dispensing_fee_amount)
    - name: "Total Vaccine Administration Fee Amount"
      expr: SUM(vaccine_administration_fee_amount)
    - name: "Average Vaccine Administration Fee Amount"
      expr: AVG(vaccine_administration_fee_amount)
    - name: "Total Generic Fill Rate Target Percentage"
      expr: SUM(generic_fill_rate_target_percentage)
    - name: "Average Generic Fill Rate Target Percentage"
      expr: AVG(generic_fill_rate_target_percentage)
    - name: "Total Generic Fill Rate Actual Percentage"
      expr: SUM(generic_fill_rate_actual_percentage)
    - name: "Average Generic Fill Rate Actual Percentage"
      expr: AVG(generic_fill_rate_actual_percentage)
    - name: "Total Prompt Pay Discount Percentage"
      expr: SUM(prompt_pay_discount_percentage)
    - name: "Average Prompt Pay Discount Percentage"
      expr: AVG(prompt_pay_discount_percentage)
    - name: "Total Contract Value Amount"
      expr: SUM(contract_value_amount)
    - name: "Average Contract Value Amount"
      expr: AVG(contract_value_amount)
    - name: "Total Liability Limit Amount"
      expr: SUM(liability_limit_amount)
    - name: "Average Liability Limit Amount"
      expr: AVG(liability_limit_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_cost_share_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cost Share Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`cost_share_pharmacy`"
  dimensions:
    - name: "Benefit Period Start Date"
      expr: benefit_period_start_date
    - name: "Benefit Period End Date"
      expr: benefit_period_end_date
    - name: "Formulary Tier"
      expr: formulary_tier
    - name: "Pharmacy Type"
      expr: pharmacy_type
    - name: "Supply Days"
      expr: supply_days
    - name: "Deductible Applies Flag"
      expr: deductible_applies_flag
    - name: "Catastrophic Coverage Flag"
      expr: catastrophic_coverage_flag
    - name: "Coverage Gap Applies Flag"
      expr: coverage_gap_applies_flag
    - name: "Low Income Subsidy Level"
      expr: low_income_subsidy_level
    - name: "Prior Authorization Required Flag"
      expr: prior_authorization_required_flag
    - name: "Step Therapy Required Flag"
      expr: step_therapy_required_flag
    - name: "Quantity Limit"
      expr: quantity_limit
    - name: "Quantity Limit Period Days"
      expr: quantity_limit_period_days
    - name: "Generic Substitution Allowed Flag"
      expr: generic_substitution_allowed_flag
    - name: "Preventive Drug Flag"
      expr: preventive_drug_flag
    - name: "Specialty Drug Flag"
      expr: specialty_drug_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cost Share Pharmacy"
      expr: COUNT(DISTINCT cost_share_pharmacy_id)
    - name: "Total Coinsurance Percentage"
      expr: SUM(coinsurance_percentage)
    - name: "Average Coinsurance Percentage"
      expr: AVG(coinsurance_percentage)
    - name: "Total Out Of Pocket Maximum"
      expr: SUM(out_of_pocket_maximum)
    - name: "Average Out Of Pocket Maximum"
      expr: AVG(out_of_pocket_maximum)
    - name: "Total Initial Coverage Limit"
      expr: SUM(initial_coverage_limit)
    - name: "Average Initial Coverage Limit"
      expr: AVG(initial_coverage_limit)
    - name: "Total Coverage Gap Copay Amount"
      expr: SUM(coverage_gap_copay_amount)
    - name: "Average Coverage Gap Copay Amount"
      expr: AVG(coverage_gap_copay_amount)
    - name: "Total Coverage Gap Coinsurance Percentage"
      expr: SUM(coverage_gap_coinsurance_percentage)
    - name: "Average Coverage Gap Coinsurance Percentage"
      expr: AVG(coverage_gap_coinsurance_percentage)
    - name: "Total Lis Copay Amount"
      expr: SUM(lis_copay_amount)
    - name: "Average Lis Copay Amount"
      expr: AVG(lis_copay_amount)
    - name: "Total Brand Penalty Amount"
      expr: SUM(brand_penalty_amount)
    - name: "Average Brand Penalty Amount"
      expr: AVG(brand_penalty_amount)
    - name: "Total Minimum Cost Share Amount"
      expr: SUM(minimum_cost_share_amount)
    - name: "Average Minimum Cost Share Amount"
      expr: AVG(minimum_cost_share_amount)
    - name: "Total Maximum Cost Share Amount"
      expr: SUM(maximum_cost_share_amount)
    - name: "Average Maximum Cost Share Amount"
      expr: AVG(maximum_cost_share_amount)
    - name: "Total Mail Order Copay Amount"
      expr: SUM(mail_order_copay_amount)
    - name: "Average Mail Order Copay Amount"
      expr: AVG(mail_order_copay_amount)
    - name: "Total Retail Copay Amount"
      expr: SUM(retail_copay_amount)
    - name: "Average Retail Copay Amount"
      expr: AVG(retail_copay_amount)
    - name: "Total Preferred Pharmacy Copay Amount"
      expr: SUM(preferred_pharmacy_copay_amount)
    - name: "Average Preferred Pharmacy Copay Amount"
      expr: AVG(preferred_pharmacy_copay_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_dispense`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Dispense business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`dispense`"
  dimensions:
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Drug Strength"
      expr: drug_strength
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Days Supply"
      expr: days_supply
    - name: "Date"
      expr: date
    - name: "Written Date"
      expr: written_date
    - name: "Prescription Number"
      expr: prescription_number
    - name: "Refill Number"
      expr: refill_number
    - name: "Refills Authorized"
      expr: refills_authorized
    - name: "Daw Code"
      expr: daw_code
    - name: "Generic Indicator"
      expr: generic_indicator
    - name: "Compound Indicator"
      expr: compound_indicator
    - name: "Therapeutic Class"
      expr: therapeutic_class
    - name: "Drug Category"
      expr: drug_category
    - name: "Formulary Status"
      expr: formulary_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Dispense"
      expr: COUNT(DISTINCT dispense_id)
    - name: "Total Quantity Dispensed"
      expr: SUM(quantity_dispensed)
    - name: "Average Quantity Dispensed"
      expr: AVG(quantity_dispensed)
    - name: "Total Ingredient Cost"
      expr: SUM(ingredient_cost)
    - name: "Average Ingredient Cost"
      expr: AVG(ingredient_cost)
    - name: "Total Dispensing Fee"
      expr: SUM(dispensing_fee)
    - name: "Average Dispensing Fee"
      expr: AVG(dispensing_fee)
    - name: "Total Sales Tax"
      expr: SUM(sales_tax)
    - name: "Average Sales Tax"
      expr: AVG(sales_tax)
    - name: "Total Total Amount Paid"
      expr: SUM(total_amount_paid)
    - name: "Average Total Amount Paid"
      expr: AVG(total_amount_paid)
    - name: "Total Plan Paid Amount"
      expr: SUM(plan_paid_amount)
    - name: "Average Plan Paid Amount"
      expr: AVG(plan_paid_amount)
    - name: "Total Member Copay"
      expr: SUM(member_copay)
    - name: "Average Member Copay"
      expr: AVG(member_copay)
    - name: "Total Member Coinsurance"
      expr: SUM(member_coinsurance)
    - name: "Average Member Coinsurance"
      expr: AVG(member_coinsurance)
    - name: "Total Member Deductible"
      expr: SUM(member_deductible)
    - name: "Average Member Deductible"
      expr: AVG(member_deductible)
    - name: "Total Member Out Of Pocket"
      expr: SUM(member_out_of_pocket)
    - name: "Average Member Out Of Pocket"
      expr: AVG(member_out_of_pocket)
    - name: "Total Awp Unit Price"
      expr: SUM(awp_unit_price)
    - name: "Average Awp Unit Price"
      expr: AVG(awp_unit_price)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_drug`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Drug business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`drug`"
  dimensions:
    - name: "Ndc"
      expr: ndc
    - name: "Ndc Format"
      expr: ndc_format
    - name: "Labeler Code"
      expr: labeler_code
    - name: "Product Code"
      expr: product_code
    - name: "Package Code"
      expr: package_code
    - name: "Proprietary Name"
      expr: proprietary_name
    - name: "Non Proprietary Name"
      expr: non_proprietary_name
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Route Of Administration"
      expr: route_of_administration
    - name: "Strength"
      expr: strength
    - name: "Active Ingredient"
      expr: active_ingredient
    - name: "Inactive Ingredients"
      expr: inactive_ingredients
    - name: "Labeler Name"
      expr: labeler_name
    - name: "Class"
      expr: class
    - name: "Therapeutic Category"
      expr: therapeutic_category
    - name: "Dea Schedule"
      expr: dea_schedule
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Drug"
      expr: COUNT(DISTINCT drug_id)
    - name: "Total Awp"
      expr: SUM(awp)
    - name: "Average Awp"
      expr: AVG(awp)
    - name: "Total Wac"
      expr: SUM(wac)
    - name: "Average Wac"
      expr: AVG(wac)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
    - name: "Total Unit Price"
      expr: SUM(unit_price)
    - name: "Average Unit Price"
      expr: AVG(unit_price)
    - name: "Total Package Quantity"
      expr: SUM(package_quantity)
    - name: "Average Package Quantity"
      expr: AVG(package_quantity)
    - name: "Total Quantity Limit"
      expr: SUM(quantity_limit)
    - name: "Average Quantity Limit"
      expr: AVG(quantity_limit)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_drug_price`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Drug Price business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`drug_price`"
  dimensions:
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Generic Name"
      expr: generic_name
    - name: "Labeler Name"
      expr: labeler_name
    - name: "Package Size"
      expr: package_size
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Strength"
      expr: strength
    - name: "Route Of Administration"
      expr: route_of_administration
    - name: "Price Type"
      expr: price_type
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Price Source"
      expr: price_source
    - name: "Price Source File Date"
      expr: price_source_file_date
    - name: "Price Change Indicator"
      expr: price_change_indicator
    - name: "Drug Class"
      expr: drug_class
    - name: "Gpi"
      expr: gpi
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Drug Price"
      expr: COUNT(DISTINCT drug_price_id)
    - name: "Total Awp"
      expr: SUM(awp)
    - name: "Average Awp"
      expr: AVG(awp)
    - name: "Total Mac"
      expr: SUM(mac)
    - name: "Average Mac"
      expr: AVG(mac)
    - name: "Total Wac"
      expr: SUM(wac)
    - name: "Average Wac"
      expr: AVG(wac)
    - name: "Total Nadac"
      expr: SUM(nadac)
    - name: "Average Nadac"
      expr: AVG(nadac)
    - name: "Total Unit Price"
      expr: SUM(unit_price)
    - name: "Average Unit Price"
      expr: AVG(unit_price)
    - name: "Total Price Change Percentage"
      expr: SUM(price_change_percentage)
    - name: "Average Price Change Percentage"
      expr: AVG(price_change_percentage)
    - name: "Total Previous Price"
      expr: SUM(previous_price)
    - name: "Average Previous Price"
      expr: AVG(previous_price)
    - name: "Total Rebate Amount"
      expr: SUM(rebate_amount)
    - name: "Average Rebate Amount"
      expr: AVG(rebate_amount)
    - name: "Total Rebate Percentage"
      expr: SUM(rebate_percentage)
    - name: "Average Rebate Percentage"
      expr: AVG(rebate_percentage)
    - name: "Total Dispensing Fee"
      expr: SUM(dispensing_fee)
    - name: "Average Dispensing Fee"
      expr: AVG(dispensing_fee)
    - name: "Total Ingredient Cost"
      expr: SUM(ingredient_cost)
    - name: "Average Ingredient Cost"
      expr: AVG(ingredient_cost)
    - name: "Total Reimbursement Percentage"
      expr: SUM(reimbursement_percentage)
    - name: "Average Reimbursement Percentage"
      expr: AVG(reimbursement_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_dur_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Dur Rule business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`dur_rule`"
  dimensions:
    - name: "Rule Code"
      expr: rule_code
    - name: "Rule Name"
      expr: rule_name
    - name: "Rule Description"
      expr: rule_description
    - name: "Rule Type"
      expr: rule_type
    - name: "Severity Level"
      expr: severity_level
    - name: "Action Required"
      expr: action_required
    - name: "Override Allowed Flag"
      expr: override_allowed_flag
    - name: "Override Reason Required Flag"
      expr: override_reason_required_flag
    - name: "Clinical Rationale"
      expr: clinical_rationale
    - name: "Rule Category"
      expr: rule_category
    - name: "Evaluation Scope"
      expr: evaluation_scope
    - name: "Lookback Period Days"
      expr: lookback_period_days
    - name: "Threshold Unit"
      expr: threshold_unit
    - name: "Comparison Operator"
      expr: comparison_operator
    - name: "Minimum Age Years"
      expr: minimum_age_years
    - name: "Maximum Age Years"
      expr: maximum_age_years
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Dur Rule"
      expr: COUNT(DISTINCT dur_rule_id)
    - name: "Total Threshold Value"
      expr: SUM(threshold_value)
    - name: "Average Threshold Value"
      expr: AVG(threshold_value)
    - name: "Total Minimum Quantity"
      expr: SUM(minimum_quantity)
    - name: "Average Minimum Quantity"
      expr: AVG(minimum_quantity)
    - name: "Total Maximum Quantity"
      expr: SUM(maximum_quantity)
    - name: "Average Maximum Quantity"
      expr: AVG(maximum_quantity)
    - name: "Total Cumulative Dose Limit"
      expr: SUM(cumulative_dose_limit)
    - name: "Average Cumulative Dose Limit"
      expr: AVG(cumulative_dose_limit)
    - name: "Total Daily Dose Limit"
      expr: SUM(daily_dose_limit)
    - name: "Average Daily Dose Limit"
      expr: AVG(daily_dose_limit)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_eligibility_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Eligibility Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`eligibility_pharmacy`"
  dimensions:
    - name: "Group Number"
      expr: group_number
    - name: "Plan Name"
      expr: plan_name
    - name: "Plan Type"
      expr: plan_type
    - name: "Coverage Level"
      expr: coverage_level
    - name: "Pbm Name"
      expr: pbm_name
    - name: "Bin Number"
      expr: bin_number
    - name: "Pcn"
      expr: pcn
    - name: "Rx Group"
      expr: rx_group
    - name: "Person Code"
      expr: person_code
    - name: "Coverage Effective Date"
      expr: coverage_effective_date
    - name: "Coverage Termination Date"
      expr: coverage_termination_date
    - name: "Snapshot Date"
      expr: snapshot_date
    - name: "Formulary Name"
      expr: formulary_name
    - name: "Formulary Tier Structure"
      expr: formulary_tier_structure
    - name: "Retail Network Type"
      expr: retail_network_type
    - name: "Mail Order Available"
      expr: mail_order_available
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Eligibility Pharmacy"
      expr: COUNT(DISTINCT eligibility_pharmacy_id)
    - name: "Total Deductible Amount"
      expr: SUM(deductible_amount)
    - name: "Average Deductible Amount"
      expr: AVG(deductible_amount)
    - name: "Total Deductible Met Amount"
      expr: SUM(deductible_met_amount)
    - name: "Average Deductible Met Amount"
      expr: AVG(deductible_met_amount)
    - name: "Total Out Of Pocket Max"
      expr: SUM(out_of_pocket_max)
    - name: "Average Out Of Pocket Max"
      expr: AVG(out_of_pocket_max)
    - name: "Total Out Of Pocket Met Amount"
      expr: SUM(out_of_pocket_met_amount)
    - name: "Average Out Of Pocket Met Amount"
      expr: AVG(out_of_pocket_met_amount)
    - name: "Total Catastrophic Coverage Threshold"
      expr: SUM(catastrophic_coverage_threshold)
    - name: "Average Catastrophic Coverage Threshold"
      expr: AVG(catastrophic_coverage_threshold)
    - name: "Total Copay Tier 1"
      expr: SUM(copay_tier_1)
    - name: "Average Copay Tier 1"
      expr: AVG(copay_tier_1)
    - name: "Total Copay Tier 2"
      expr: SUM(copay_tier_2)
    - name: "Average Copay Tier 2"
      expr: AVG(copay_tier_2)
    - name: "Total Copay Tier 3"
      expr: SUM(copay_tier_3)
    - name: "Average Copay Tier 3"
      expr: AVG(copay_tier_3)
    - name: "Total Copay Tier 4"
      expr: SUM(copay_tier_4)
    - name: "Average Copay Tier 4"
      expr: AVG(copay_tier_4)
    - name: "Total Coinsurance Tier 1 Percent"
      expr: SUM(coinsurance_tier_1_percent)
    - name: "Average Coinsurance Tier 1 Percent"
      expr: AVG(coinsurance_tier_1_percent)
    - name: "Total Coinsurance Tier 2 Percent"
      expr: SUM(coinsurance_tier_2_percent)
    - name: "Average Coinsurance Tier 2 Percent"
      expr: AVG(coinsurance_tier_2_percent)
    - name: "Total Coinsurance Tier 3 Percent"
      expr: SUM(coinsurance_tier_3_percent)
    - name: "Average Coinsurance Tier 3 Percent"
      expr: AVG(coinsurance_tier_3_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_location_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Location Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`location_pharmacy`"
  dimensions:
    - name: "Npi"
      expr: npi
    - name: "Name"
      expr: name
    - name: "Dba Name"
      expr: dba_name
    - name: "Chain Code"
      expr: chain_code
    - name: "Chain Name"
      expr: chain_name
    - name: "Pharmacy Type"
      expr: pharmacy_type
    - name: "Service Type"
      expr: service_type
    - name: "Status"
      expr: status
    - name: "Network Tier"
      expr: network_tier
    - name: "Is Specialty"
      expr: is_specialty
    - name: "Is Mail Order"
      expr: is_mail_order
    - name: "Is 340b"
      expr: is_340b
    - name: "Is 24 Hour"
      expr: is_24_hour
    - name: "Is Drive Through"
      expr: is_drive_through
    - name: "Is Compounding"
      expr: is_compounding
    - name: "Is Immunization Provider"
      expr: is_immunization_provider
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Location Pharmacy"
      expr: COUNT(DISTINCT location_pharmacy_id)
    - name: "Total Latitude"
      expr: SUM(latitude)
    - name: "Average Latitude"
      expr: AVG(latitude)
    - name: "Total Longitude"
      expr: SUM(longitude)
    - name: "Average Longitude"
      expr: AVG(longitude)
    - name: "Total Quality Rating"
      expr: SUM(quality_rating)
    - name: "Average Quality Rating"
      expr: AVG(quality_rating)
    - name: "Total Member Satisfaction Score"
      expr: SUM(member_satisfaction_score)
    - name: "Average Member Satisfaction Score"
      expr: AVG(member_satisfaction_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_mail_order`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Mail Order business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`mail_order`"
  dimensions:
    - name: "Program Name"
      expr: program_name
    - name: "Program Code"
      expr: program_code
    - name: "Program Type"
      expr: program_type
    - name: "Lob"
      expr: lob
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Enrollment Eligibility Rule"
      expr: enrollment_eligibility_rule
    - name: "Minimum Days Supply"
      expr: minimum_days_supply
    - name: "Maximum Days Supply"
      expr: maximum_days_supply
    - name: "Standard Days Supply"
      expr: standard_days_supply
    - name: "Refill Limit"
      expr: refill_limit
    - name: "Deductible Applies Flag"
      expr: deductible_applies_flag
    - name: "Oop Max Applies Flag"
      expr: oop_max_applies_flag
    - name: "Shipping Method"
      expr: shipping_method
    - name: "Standard Shipping Days"
      expr: standard_shipping_days
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Mail Order"
      expr: COUNT(DISTINCT mail_order_id)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percentage"
      expr: SUM(coinsurance_percentage)
    - name: "Average Coinsurance Percentage"
      expr: AVG(coinsurance_percentage)
    - name: "Total Shipping Cost Member"
      expr: SUM(shipping_cost_member)
    - name: "Average Shipping Cost Member"
      expr: AVG(shipping_cost_member)
    - name: "Total Free Shipping Threshold Amount"
      expr: SUM(free_shipping_threshold_amount)
    - name: "Average Free Shipping Threshold Amount"
      expr: AVG(free_shipping_threshold_amount)
    - name: "Total Member Cost Savings Percentage"
      expr: SUM(member_cost_savings_percentage)
    - name: "Average Member Cost Savings Percentage"
      expr: AVG(member_cost_savings_percentage)
    - name: "Total Plan Cost Savings Percentage"
      expr: SUM(plan_cost_savings_percentage)
    - name: "Average Plan Cost Savings Percentage"
      expr: AVG(plan_cost_savings_percentage)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Member Satisfaction Score"
      expr: SUM(member_satisfaction_score)
    - name: "Average Member Satisfaction Score"
      expr: AVG(member_satisfaction_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_manufacturer`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Manufacturer business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`manufacturer`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Manufacturer Code"
      expr: manufacturer_code
    - name: "Duns Number"
      expr: duns_number
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
    - name: "Manufacturer Type"
      expr: manufacturer_type
    - name: "Specialty Area"
      expr: specialty_area
    - name: "Status"
      expr: status
    - name: "Contract Start Date"
      expr: contract_start_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Manufacturer"
      expr: COUNT(DISTINCT manufacturer_id)
    - name: "Total Rating Score"
      expr: SUM(rating_score)
    - name: "Average Rating Score"
      expr: AVG(rating_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_pbm`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Pbm business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`pbm`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Status"
      expr: status
    - name: "Prior Auth Required"
      expr: prior_auth_required
    - name: "Specialty Drug Coverage"
      expr: specialty_drug_coverage
    - name: "Mail Order Allowed"
      expr: mail_order_allowed
    - name: "Tier"
      expr: tier
    - name: "Drug Category"
      expr: drug_category
    - name: "Ndc List"
      expr: ndc_list
    - name: "Pricing Method"
      expr: pricing_method
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Modified Timestamp"
      expr: modified_timestamp
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "Termination Date Month"
      expr: DATE_TRUNC('MONTH', termination_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Pbm"
      expr: COUNT(DISTINCT pbm_id)
    - name: "Total Maximum Annual Benefit"
      expr: SUM(maximum_annual_benefit)
    - name: "Average Maximum Annual Benefit"
      expr: AVG(maximum_annual_benefit)
    - name: "Total Maximum Per Prescription"
      expr: SUM(maximum_per_prescription)
    - name: "Average Maximum Per Prescription"
      expr: AVG(maximum_per_prescription)
    - name: "Total Copay Amount"
      expr: SUM(copay_amount)
    - name: "Average Copay Amount"
      expr: AVG(copay_amount)
    - name: "Total Coinsurance Percent"
      expr: SUM(coinsurance_percent)
    - name: "Average Coinsurance Percent"
      expr: AVG(coinsurance_percent)
    - name: "Total Awp Price"
      expr: SUM(awp_price)
    - name: "Average Awp Price"
      expr: AVG(awp_price)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
    - name: "Total Reimbursement Rate"
      expr: SUM(reimbursement_rate)
    - name: "Average Reimbursement Rate"
      expr: AVG(reimbursement_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`pharmacy`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Npi"
      expr: npi
    - name: "License Number"
      expr: license_number
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State"
      expr: state
    - name: "Zip Code"
      expr: zip_code
    - name: "Country"
      expr: country
    - name: "Phone Number"
      expr: phone_number
    - name: "Fax Number"
      expr: fax_number
    - name: "Email Address"
      expr: email_address
    - name: "Pharmacy Type"
      expr: pharmacy_type
    - name: "Status"
      expr: status
    - name: "Contract Start Date"
      expr: contract_start_date
    - name: "Contract End Date"
      expr: contract_end_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Pharmacy"
      expr: COUNT(DISTINCT pharmacy_id)
    - name: "Total Discount Rate"
      expr: SUM(discount_rate)
    - name: "Average Discount Rate"
      expr: AVG(discount_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_prescription`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Prescription business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`prescription`"
  dimensions:
    - name: "Member Name"
      expr: member_name
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
    - name: "Prescriber Npi"
      expr: prescriber_npi
    - name: "Prescriber Name"
      expr: prescriber_name
    - name: "Pharmacy Npi"
      expr: pharmacy_npi
    - name: "Pharmacy Name"
      expr: pharmacy_name
    - name: "Pharmacy Address"
      expr: pharmacy_address
    - name: "Pharmacy Phone"
      expr: pharmacy_phone
    - name: "Fill Number"
      expr: fill_number
    - name: "Written Date"
      expr: written_date
    - name: "Fill Date"
      expr: fill_date
    - name: "Prior Auth Required"
      expr: prior_auth_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Prescription"
      expr: COUNT(DISTINCT prescription_id)
    - name: "Total Drug Cost"
      expr: SUM(drug_cost)
    - name: "Average Drug Cost"
      expr: AVG(drug_cost)
    - name: "Total Patient Responsibility Amount"
      expr: SUM(patient_responsibility_amount)
    - name: "Average Patient Responsibility Amount"
      expr: AVG(patient_responsibility_amount)
    - name: "Total Pharmacy Payment Amount"
      expr: SUM(pharmacy_payment_amount)
    - name: "Average Pharmacy Payment Amount"
      expr: AVG(pharmacy_payment_amount)
    - name: "Total Claim Amount"
      expr: SUM(claim_amount)
    - name: "Average Claim Amount"
      expr: AVG(claim_amount)
    - name: "Total Claim Adjustment Amount"
      expr: SUM(claim_adjustment_amount)
    - name: "Average Claim Adjustment Amount"
      expr: AVG(claim_adjustment_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_prior_auth_dec`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Prior Auth Dec business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`prior_auth_dec`"
  dimensions:
    - name: "Decision Timestamp"
      expr: decision_timestamp
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Approval Duration Days"
      expr: approval_duration_days
    - name: "Decision Reason Code"
      expr: decision_reason_code
    - name: "Decision Reason Description"
      expr: decision_reason_description
    - name: "Denial Reason Category"
      expr: denial_reason_category
    - name: "Approved Ndc"
      expr: approved_ndc
    - name: "Approved Drug Name"
      expr: approved_drug_name
    - name: "Approved Quantity Unit"
      expr: approved_quantity_unit
    - name: "Approved Days Supply"
      expr: approved_days_supply
    - name: "Approved Refills"
      expr: approved_refills
    - name: "Max Daily Dose Unit"
      expr: max_daily_dose_unit
    - name: "Step Therapy Required Flag"
      expr: step_therapy_required_flag
    - name: "Step Therapy Drugs Required"
      expr: step_therapy_drugs_required
    - name: "Clinical Criteria Met Flag"
      expr: clinical_criteria_met_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Prior Auth Dec"
      expr: COUNT(DISTINCT prior_auth_dec_id)
    - name: "Total Approved Quantity"
      expr: SUM(approved_quantity)
    - name: "Average Approved Quantity"
      expr: AVG(approved_quantity)
    - name: "Total Max Daily Dose"
      expr: SUM(max_daily_dose)
    - name: "Average Max Daily Dose"
      expr: AVG(max_daily_dose)
    - name: "Total Turnaround Time Hours"
      expr: SUM(turnaround_time_hours)
    - name: "Average Turnaround Time Hours"
      expr: AVG(turnaround_time_hours)
    - name: "Total Estimated Cost Per Fill"
      expr: SUM(estimated_cost_per_fill)
    - name: "Average Estimated Cost Per Fill"
      expr: AVG(estimated_cost_per_fill)
    - name: "Total Estimated Member Copay"
      expr: SUM(estimated_member_copay)
    - name: "Average Estimated Member Copay"
      expr: AVG(estimated_member_copay)
    - name: "Total Awp Price"
      expr: SUM(awp_price)
    - name: "Average Awp Price"
      expr: AVG(awp_price)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_prior_auth_req`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Prior Auth Req business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`prior_auth_req`"
  dimensions:
    - name: "Request Number"
      expr: request_number
    - name: "Request Date"
      expr: request_date
    - name: "Request Timestamp"
      expr: request_timestamp
    - name: "Request Type"
      expr: request_type
    - name: "Request Urgency"
      expr: request_urgency
    - name: "Ndc Code"
      expr: ndc_code
    - name: "Drug Name"
      expr: drug_name
    - name: "Drug Strength"
      expr: drug_strength
    - name: "Drug Form"
      expr: drug_form
    - name: "Quantity Unit"
      expr: quantity_unit
    - name: "Days Supply"
      expr: days_supply
    - name: "Refills Requested"
      expr: refills_requested
    - name: "Prescriber Npi"
      expr: prescriber_npi
    - name: "Prescriber Name"
      expr: prescriber_name
    - name: "Prescriber Specialty"
      expr: prescriber_specialty
    - name: "Prescriber Phone"
      expr: prescriber_phone
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Prior Auth Req"
      expr: COUNT(DISTINCT prior_auth_req_id)
    - name: "Total Quantity Requested"
      expr: SUM(quantity_requested)
    - name: "Average Quantity Requested"
      expr: AVG(quantity_requested)
    - name: "Total Quantity Limit Value"
      expr: SUM(quantity_limit_value)
    - name: "Average Quantity Limit Value"
      expr: AVG(quantity_limit_value)
    - name: "Total Estimated Cost"
      expr: SUM(estimated_cost)
    - name: "Average Estimated Cost"
      expr: AVG(estimated_cost)
    - name: "Total Awp Price"
      expr: SUM(awp_price)
    - name: "Average Awp Price"
      expr: AVG(awp_price)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
    - name: "Total Approved Quantity"
      expr: SUM(approved_quantity)
    - name: "Average Approved Quantity"
      expr: AVG(approved_quantity)
    - name: "Total Member Copay Amount"
      expr: SUM(member_copay_amount)
    - name: "Average Member Copay Amount"
      expr: AVG(member_copay_amount)
    - name: "Total Member Coinsurance Percent"
      expr: SUM(member_coinsurance_percent)
    - name: "Average Member Coinsurance Percent"
      expr: AVG(member_coinsurance_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_rebate`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Rebate business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`rebate`"
  dimensions:
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Contract Type"
      expr: contract_type
    - name: "Type"
      expr: type
    - name: "Calculation Basis"
      expr: calculation_basis
    - name: "Minimum Volume"
      expr: minimum_volume
    - name: "Maximum Volume"
      expr: maximum_volume
    - name: "Volume Unit"
      expr: volume_unit
    - name: "Formulary Tier"
      expr: formulary_tier
    - name: "Prior Authorization Required"
      expr: prior_authorization_required
    - name: "Step Therapy Required"
      expr: step_therapy_required
    - name: "Effective Date"
      expr: effective_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Payment Frequency"
      expr: payment_frequency
    - name: "Payment Lag Days"
      expr: payment_lag_days
    - name: "Line Of Business"
      expr: line_of_business
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Rebate"
      expr: COUNT(DISTINCT rebate_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Percentage"
      expr: SUM(percentage)
    - name: "Average Percentage"
      expr: AVG(percentage)
    - name: "Total Market Share Target"
      expr: SUM(market_share_target)
    - name: "Average Market Share Target"
      expr: AVG(market_share_target)
    - name: "Total Pass Through Percentage"
      expr: SUM(pass_through_percentage)
    - name: "Average Pass Through Percentage"
      expr: AVG(pass_through_percentage)
    - name: "Total Retained Percentage"
      expr: SUM(retained_percentage)
    - name: "Average Retained Percentage"
      expr: AVG(retained_percentage)
    - name: "Total Performance Target"
      expr: SUM(performance_target)
    - name: "Average Performance Target"
      expr: AVG(performance_target)
    - name: "Total Guarantee Amount"
      expr: SUM(guarantee_amount)
    - name: "Average Guarantee Amount"
      expr: AVG(guarantee_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_rebate_txn`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Rebate Txn business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`rebate_txn`"
  dimensions:
    - name: "Pbm Partner Name"
      expr: pbm_partner_name
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Drug Strength"
      expr: drug_strength
    - name: "Drug Form"
      expr: drug_form
    - name: "Therapeutic Class"
      expr: therapeutic_class
    - name: "Formulary Tier"
      expr: formulary_tier
    - name: "Rebate Type"
      expr: rebate_type
    - name: "Rebate Program Code"
      expr: rebate_program_code
    - name: "Rebate Program Name"
      expr: rebate_program_name
    - name: "Transaction Date"
      expr: transaction_date
    - name: "Transaction Timestamp"
      expr: transaction_timestamp
    - name: "Service Period Start Date"
      expr: service_period_start_date
    - name: "Service Period End Date"
      expr: service_period_end_date
    - name: "Claim Count"
      expr: claim_count
    - name: "Prescription Count"
      expr: prescription_count
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Rebate Txn"
      expr: COUNT(DISTINCT rebate_txn_id)
    - name: "Total Quantity Dispensed"
      expr: SUM(quantity_dispensed)
    - name: "Average Quantity Dispensed"
      expr: AVG(quantity_dispensed)
    - name: "Total Total Ingredient Cost"
      expr: SUM(total_ingredient_cost)
    - name: "Average Total Ingredient Cost"
      expr: AVG(total_ingredient_cost)
    - name: "Total Awp Amount"
      expr: SUM(awp_amount)
    - name: "Average Awp Amount"
      expr: AVG(awp_amount)
    - name: "Total Mac Amount"
      expr: SUM(mac_amount)
    - name: "Average Mac Amount"
      expr: AVG(mac_amount)
    - name: "Total Rebate Amount"
      expr: SUM(rebate_amount)
    - name: "Average Rebate Amount"
      expr: AVG(rebate_amount)
    - name: "Total Rebate Per Unit"
      expr: SUM(rebate_per_unit)
    - name: "Average Rebate Per Unit"
      expr: AVG(rebate_per_unit)
    - name: "Total Rebate Percentage"
      expr: SUM(rebate_percentage)
    - name: "Average Rebate Percentage"
      expr: AVG(rebate_percentage)
    - name: "Total Base Rebate Amount"
      expr: SUM(base_rebate_amount)
    - name: "Average Base Rebate Amount"
      expr: AVG(base_rebate_amount)
    - name: "Total Performance Bonus Amount"
      expr: SUM(performance_bonus_amount)
    - name: "Average Performance Bonus Amount"
      expr: AVG(performance_bonus_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Net Rebate Amount"
      expr: SUM(net_rebate_amount)
    - name: "Average Net Rebate Amount"
      expr: AVG(net_rebate_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_refill_request`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Refill Request business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`refill_request`"
  dimensions:
    - name: "Request Date"
      expr: request_date
    - name: "Request Timestamp"
      expr: request_timestamp
    - name: "Request Method"
      expr: request_method
    - name: "Status Reason Code"
      expr: status_reason_code
    - name: "Status Reason Description"
      expr: status_reason_description
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Drug Strength"
      expr: drug_strength
    - name: "Drug Form"
      expr: drug_form
    - name: "Days Supply Requested"
      expr: days_supply_requested
    - name: "Refills Remaining"
      expr: refills_remaining
    - name: "Original Fill Date"
      expr: original_fill_date
    - name: "Last Fill Date"
      expr: last_fill_date
    - name: "Prescription Expiration Date"
      expr: prescription_expiration_date
    - name: "Prescriber Npi"
      expr: prescriber_npi
    - name: "Prescriber Name"
      expr: prescriber_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Refill Request"
      expr: COUNT(DISTINCT refill_request_id)
    - name: "Total Quantity Requested"
      expr: SUM(quantity_requested)
    - name: "Average Quantity Requested"
      expr: AVG(quantity_requested)
    - name: "Total Estimated Copay Amount"
      expr: SUM(estimated_copay_amount)
    - name: "Average Estimated Copay Amount"
      expr: AVG(estimated_copay_amount)
    - name: "Total Estimated Total Cost"
      expr: SUM(estimated_total_cost)
    - name: "Average Estimated Total Cost"
      expr: AVG(estimated_total_cost)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`pharmacy_specialty_pharmacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Specialty Pharmacy business metrics"
  source: "`cmoore_customer_demos`.`pharmacy`.`specialty_pharmacy`"
  dimensions:
    - name: "Ndc"
      expr: ndc
    - name: "Drug Name"
      expr: drug_name
    - name: "Generic Name"
      expr: generic_name
    - name: "Drug Classification"
      expr: drug_classification
    - name: "Therapeutic Class"
      expr: therapeutic_class
    - name: "Disease State"
      expr: disease_state
    - name: "Manufacturer Name"
      expr: manufacturer_name
    - name: "Dosage Form"
      expr: dosage_form
    - name: "Strength"
      expr: strength
    - name: "Route Of Administration"
      expr: route_of_administration
    - name: "Storage Requirements"
      expr: storage_requirements
    - name: "Requires Refrigeration"
      expr: requires_refrigeration
    - name: "Requires Freezing"
      expr: requires_freezing
    - name: "Light Sensitive"
      expr: light_sensitive
    - name: "Handling Requirements"
      expr: handling_requirements
    - name: "Requires Prior Authorization"
      expr: requires_prior_authorization
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Specialty Pharmacy"
      expr: COUNT(DISTINCT specialty_pharmacy_id)
    - name: "Total Temperature Range Min Celsius"
      expr: SUM(temperature_range_min_celsius)
    - name: "Average Temperature Range Min Celsius"
      expr: AVG(temperature_range_min_celsius)
    - name: "Total Temperature Range Max Celsius"
      expr: SUM(temperature_range_max_celsius)
    - name: "Average Temperature Range Max Celsius"
      expr: AVG(temperature_range_max_celsius)
    - name: "Total Awp Unit Price"
      expr: SUM(awp_unit_price)
    - name: "Average Awp Unit Price"
      expr: AVG(awp_unit_price)
    - name: "Total Wac Unit Price"
      expr: SUM(wac_unit_price)
    - name: "Average Wac Unit Price"
      expr: AVG(wac_unit_price)
    - name: "Total Mac Price"
      expr: SUM(mac_price)
    - name: "Average Mac Price"
      expr: AVG(mac_price)
$$;