-- Metric views for domain: finance | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:07:18

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_account_balance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Account Balance business metrics"
  source: "`cmoore_customer_demos`.`finance`.`account_balance`"
  dimensions:
    - name: "Account Number"
      expr: account_number
    - name: "Ledger Name"
      expr: ledger_name
    - name: "Ledger Type"
      expr: ledger_type
    - name: "Legal Entity Code"
      expr: legal_entity_code
    - name: "Legal Entity Name"
      expr: legal_entity_name
    - name: "Business Unit Code"
      expr: business_unit_code
    - name: "Business Unit Name"
      expr: business_unit_name
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Line"
      expr: product_line
    - name: "Period Status"
      expr: period_status
    - name: "Snapshot Date"
      expr: snapshot_date
    - name: "Posting Date"
      expr: posting_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Balance Type"
      expr: balance_type
    - name: "Functional Currency Code"
      expr: functional_currency_code
    - name: "Reporting Currency Code"
      expr: reporting_currency_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Account Balance"
      expr: COUNT(DISTINCT account_balance_id)
    - name: "Total Debit Balance Amount"
      expr: SUM(debit_balance_amount)
    - name: "Average Debit Balance Amount"
      expr: AVG(debit_balance_amount)
    - name: "Total Credit Balance Amount"
      expr: SUM(credit_balance_amount)
    - name: "Average Credit Balance Amount"
      expr: AVG(credit_balance_amount)
    - name: "Total Net Balance Amount"
      expr: SUM(net_balance_amount)
    - name: "Average Net Balance Amount"
      expr: AVG(net_balance_amount)
    - name: "Total Beginning Balance Amount"
      expr: SUM(beginning_balance_amount)
    - name: "Average Beginning Balance Amount"
      expr: AVG(beginning_balance_amount)
    - name: "Total Ending Balance Amount"
      expr: SUM(ending_balance_amount)
    - name: "Average Ending Balance Amount"
      expr: AVG(ending_balance_amount)
    - name: "Total Period Activity Debit Amount"
      expr: SUM(period_activity_debit_amount)
    - name: "Average Period Activity Debit Amount"
      expr: AVG(period_activity_debit_amount)
    - name: "Total Period Activity Credit Amount"
      expr: SUM(period_activity_credit_amount)
    - name: "Average Period Activity Credit Amount"
      expr: AVG(period_activity_credit_amount)
    - name: "Total Period Net Activity Amount"
      expr: SUM(period_net_activity_amount)
    - name: "Average Period Net Activity Amount"
      expr: AVG(period_net_activity_amount)
    - name: "Total Reporting Currency Debit Amount"
      expr: SUM(reporting_currency_debit_amount)
    - name: "Average Reporting Currency Debit Amount"
      expr: AVG(reporting_currency_debit_amount)
    - name: "Total Reporting Currency Credit Amount"
      expr: SUM(reporting_currency_credit_amount)
    - name: "Average Reporting Currency Credit Amount"
      expr: AVG(reporting_currency_credit_amount)
    - name: "Total Reporting Currency Net Balance Amount"
      expr: SUM(reporting_currency_net_balance_amount)
    - name: "Average Reporting Currency Net Balance Amount"
      expr: AVG(reporting_currency_net_balance_amount)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_actuarial_assumption_set`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Actuarial Assumption Set business metrics"
  source: "`cmoore_customer_demos`.`finance`.`actuarial_assumption_set`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Assumption Type"
      expr: assumption_type
    - name: "Scenario"
      expr: scenario
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Unit Of Measure"
      expr: unit_of_measure
    - name: "Currency Code"
      expr: currency_code
    - name: "Risk Category"
      expr: risk_category
    - name: "Version Number"
      expr: version_number
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Approved By"
      expr: approved_by
    - name: "Approved Timestamp"
      expr: approved_timestamp
    - name: "Source System"
      expr: source_system
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Actuarial Assumption Set"
      expr: COUNT(DISTINCT actuarial_assumption_set_id)
    - name: "Total Assumption Value"
      expr: SUM(assumption_value)
    - name: "Average Assumption Value"
      expr: AVG(assumption_value)
    - name: "Total Discount Rate"
      expr: SUM(discount_rate)
    - name: "Average Discount Rate"
      expr: AVG(discount_rate)
    - name: "Total Inflation Rate"
      expr: SUM(inflation_rate)
    - name: "Average Inflation Rate"
      expr: AVG(inflation_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_actuarial_reserve`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Actuarial Reserve business metrics"
  source: "`cmoore_customer_demos`.`finance`.`actuarial_reserve`"
  dimensions:
    - name: "Reserve Type"
      expr: reserve_type
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Reserve Currency Code"
      expr: reserve_currency_code
    - name: "Valuation Date"
      expr: valuation_date
    - name: "Reserve Status"
      expr: reserve_status
    - name: "Calculation Method"
      expr: calculation_method
    - name: "Development Period Months"
      expr: development_period_months
    - name: "Expected Payout Date"
      expr: expected_payout_date
    - name: "Claim Count"
      expr: claim_count
    - name: "Member Months"
      expr: member_months
    - name: "Service Category"
      expr: service_category
    - name: "Diagnosis Category"
      expr: diagnosis_category
    - name: "Geographic Region"
      expr: geographic_region
    - name: "State Code"
      expr: state_code
    - name: "Plan Type"
      expr: plan_type
    - name: "Funding Arrangement"
      expr: funding_arrangement
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Actuarial Reserve"
      expr: COUNT(DISTINCT actuarial_reserve_id)
    - name: "Total Reserve Amount"
      expr: SUM(reserve_amount)
    - name: "Average Reserve Amount"
      expr: AVG(reserve_amount)
    - name: "Total Confidence Level Percent"
      expr: SUM(confidence_level_percent)
    - name: "Average Confidence Level Percent"
      expr: AVG(confidence_level_percent)
    - name: "Total Incurred Claims Amount"
      expr: SUM(incurred_claims_amount)
    - name: "Average Incurred Claims Amount"
      expr: AVG(incurred_claims_amount)
    - name: "Total Paid Claims Amount"
      expr: SUM(paid_claims_amount)
    - name: "Average Paid Claims Amount"
      expr: AVG(paid_claims_amount)
    - name: "Total Outstanding Claims Amount"
      expr: SUM(outstanding_claims_amount)
    - name: "Average Outstanding Claims Amount"
      expr: AVG(outstanding_claims_amount)
    - name: "Total Ibnr Amount"
      expr: SUM(ibnr_amount)
    - name: "Average Ibnr Amount"
      expr: AVG(ibnr_amount)
    - name: "Total Loss Adjustment Expense Amount"
      expr: SUM(loss_adjustment_expense_amount)
    - name: "Average Loss Adjustment Expense Amount"
      expr: AVG(loss_adjustment_expense_amount)
    - name: "Total Discount Rate Percent"
      expr: SUM(discount_rate_percent)
    - name: "Average Discount Rate Percent"
      expr: AVG(discount_rate_percent)
    - name: "Total Risk Margin Amount"
      expr: SUM(risk_margin_amount)
    - name: "Average Risk Margin Amount"
      expr: AVG(risk_margin_amount)
    - name: "Total Prior Period Reserve Amount"
      expr: SUM(prior_period_reserve_amount)
    - name: "Average Prior Period Reserve Amount"
      expr: AVG(prior_period_reserve_amount)
    - name: "Total Reserve Adjustment Amount"
      expr: SUM(reserve_adjustment_amount)
    - name: "Average Reserve Adjustment Amount"
      expr: AVG(reserve_adjustment_amount)
    - name: "Total Reserve Development Percent"
      expr: SUM(reserve_development_percent)
    - name: "Average Reserve Development Percent"
      expr: AVG(reserve_development_percent)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_allocation_detail`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Allocation Detail business metrics"
  source: "`cmoore_customer_demos`.`finance`.`allocation_detail`"
  dimensions:
    - name: "Allocation Rule Name"
      expr: allocation_rule_name
    - name: "Allocation Rule Version"
      expr: allocation_rule_version
    - name: "Allocation Basis"
      expr: allocation_basis
    - name: "Allocation Method"
      expr: allocation_method
    - name: "Allocation Date"
      expr: allocation_date
    - name: "Source Cost Center Code"
      expr: source_cost_center_code
    - name: "Target Cost Center Code"
      expr: target_cost_center_code
    - name: "Source Department Code"
      expr: source_department_code
    - name: "Source Department Name"
      expr: source_department_name
    - name: "Target Department Code"
      expr: target_department_code
    - name: "Target Department Name"
      expr: target_department_name
    - name: "Source Gl Account Code"
      expr: source_gl_account_code
    - name: "Target Gl Account Code"
      expr: target_gl_account_code
    - name: "Line Of Business Code"
      expr: line_of_business_code
    - name: "Line Of Business Name"
      expr: line_of_business_name
    - name: "Product Code"
      expr: product_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Allocation Detail"
      expr: COUNT(DISTINCT allocation_detail_id)
    - name: "Total Source Amount"
      expr: SUM(source_amount)
    - name: "Average Source Amount"
      expr: AVG(source_amount)
    - name: "Total Allocated Amount"
      expr: SUM(allocated_amount)
    - name: "Average Allocated Amount"
      expr: AVG(allocated_amount)
    - name: "Total Allocation Percentage"
      expr: SUM(allocation_percentage)
    - name: "Average Allocation Percentage"
      expr: AVG(allocation_percentage)
    - name: "Total Allocation Driver Value"
      expr: SUM(allocation_driver_value)
    - name: "Average Allocation Driver Value"
      expr: AVG(allocation_driver_value)
    - name: "Total Total Pool Amount"
      expr: SUM(total_pool_amount)
    - name: "Average Total Pool Amount"
      expr: AVG(total_pool_amount)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Variance Amount"
      expr: SUM(variance_amount)
    - name: "Average Variance Amount"
      expr: AVG(variance_amount)
    - name: "Total Variance Percentage"
      expr: SUM(variance_percentage)
    - name: "Average Variance Percentage"
      expr: AVG(variance_percentage)
    - name: "Total Budget Amount"
      expr: SUM(budget_amount)
    - name: "Average Budget Amount"
      expr: AVG(budget_amount)
    - name: "Total Prior Period Amount"
      expr: SUM(prior_period_amount)
    - name: "Average Prior Period Amount"
      expr: AVG(prior_period_amount)
    - name: "Total Year To Date Amount"
      expr: SUM(year_to_date_amount)
    - name: "Average Year To Date Amount"
      expr: AVG(year_to_date_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_allocation_rule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Allocation Rule business metrics"
  source: "`cmoore_customer_demos`.`finance`.`allocation_rule`"
  dimensions:
    - name: "Rule Code"
      expr: rule_code
    - name: "Rule Name"
      expr: rule_name
    - name: "Rule Description"
      expr: rule_description
    - name: "Rule Type"
      expr: rule_type
    - name: "Allocation Method"
      expr: allocation_method
    - name: "Allocation Basis"
      expr: allocation_basis
    - name: "Allocation Frequency"
      expr: allocation_frequency
    - name: "Source Cost Center"
      expr: source_cost_center
    - name: "Source Gl Account"
      expr: source_gl_account
    - name: "Target Dimension Type"
      expr: target_dimension_type
    - name: "Lob"
      expr: lob
    - name: "Plan Type"
      expr: plan_type
    - name: "Legal Entity"
      expr: legal_entity
    - name: "Business Unit"
      expr: business_unit
    - name: "Geography Code"
      expr: geography_code
    - name: "Mlr Category"
      expr: mlr_category
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Allocation Rule"
      expr: COUNT(DISTINCT allocation_rule_id)
    - name: "Total Allocation Percentage"
      expr: SUM(allocation_percentage)
    - name: "Average Allocation Percentage"
      expr: AVG(allocation_percentage)
    - name: "Total Allocation Weight"
      expr: SUM(allocation_weight)
    - name: "Average Allocation Weight"
      expr: AVG(allocation_weight)
    - name: "Total Minimum Allocation Amount"
      expr: SUM(minimum_allocation_amount)
    - name: "Average Minimum Allocation Amount"
      expr: AVG(minimum_allocation_amount)
    - name: "Total Maximum Allocation Amount"
      expr: SUM(maximum_allocation_amount)
    - name: "Average Maximum Allocation Amount"
      expr: AVG(maximum_allocation_amount)
    - name: "Total Approval Threshold Amount"
      expr: SUM(approval_threshold_amount)
    - name: "Average Approval Threshold Amount"
      expr: AVG(approval_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_allocation_run`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Allocation Run business metrics"
  source: "`cmoore_customer_demos`.`finance`.`allocation_run`"
  dimensions:
    - name: "Run Name"
      expr: run_name
    - name: "Run Type"
      expr: run_type
    - name: "Allocation Method"
      expr: allocation_method
    - name: "Allocation Basis"
      expr: allocation_basis
    - name: "Fiscal Year"
      expr: fiscal_year
    - name: "Fiscal Period"
      expr: fiscal_period
    - name: "Run Date"
      expr: run_date
    - name: "Start Timestamp"
      expr: start_timestamp
    - name: "End Timestamp"
      expr: end_timestamp
    - name: "Currency Code"
      expr: currency_code
    - name: "Number Of Transactions"
      expr: number_of_transactions
    - name: "Source System"
      expr: source_system
    - name: "Run Status"
      expr: run_status
    - name: "Is Approved"
      expr: is_approved
    - name: "Approval Timestamp"
      expr: approval_timestamp
    - name: "Run User"
      expr: run_user
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Allocation Run"
      expr: COUNT(DISTINCT allocation_run_id)
    - name: "Total Total Amount"
      expr: SUM(total_amount)
    - name: "Average Total Amount"
      expr: AVG(total_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_asset_depreciation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Asset Depreciation business metrics"
  source: "`cmoore_customer_demos`.`finance`.`asset_depreciation`"
  dimensions:
    - name: "Asset Number"
      expr: asset_number
    - name: "Asset Description"
      expr: asset_description
    - name: "Asset Category"
      expr: asset_category
    - name: "Depreciation Method"
      expr: depreciation_method
    - name: "Period Name"
      expr: period_name
    - name: "Fiscal Year"
      expr: fiscal_year
    - name: "Fiscal Period"
      expr: fiscal_period
    - name: "Depreciation Start Date"
      expr: depreciation_start_date
    - name: "Depreciation End Date"
      expr: depreciation_end_date
    - name: "Transaction Date"
      expr: transaction_date
    - name: "Posting Date"
      expr: posting_date
    - name: "Useful Life Months"
      expr: useful_life_months
    - name: "Remaining Life Months"
      expr: remaining_life_months
    - name: "Currency Code"
      expr: currency_code
    - name: "Functional Currency Code"
      expr: functional_currency_code
    - name: "Ledger Name"
      expr: ledger_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Asset Depreciation"
      expr: COUNT(DISTINCT asset_depreciation_id)
    - name: "Total Depreciation Amount"
      expr: SUM(depreciation_amount)
    - name: "Average Depreciation Amount"
      expr: AVG(depreciation_amount)
    - name: "Total Accumulated Depreciation"
      expr: SUM(accumulated_depreciation)
    - name: "Average Accumulated Depreciation"
      expr: AVG(accumulated_depreciation)
    - name: "Total Net Book Value"
      expr: SUM(net_book_value)
    - name: "Average Net Book Value"
      expr: AVG(net_book_value)
    - name: "Total Useful Life Years"
      expr: SUM(useful_life_years)
    - name: "Average Useful Life Years"
      expr: AVG(useful_life_years)
    - name: "Total Original Cost"
      expr: SUM(original_cost)
    - name: "Average Original Cost"
      expr: AVG(original_cost)
    - name: "Total Salvage Value"
      expr: SUM(salvage_value)
    - name: "Average Salvage Value"
      expr: AVG(salvage_value)
    - name: "Total Depreciable Basis"
      expr: SUM(depreciable_basis)
    - name: "Average Depreciable Basis"
      expr: AVG(depreciable_basis)
    - name: "Total Depreciation Rate Percent"
      expr: SUM(depreciation_rate_percent)
    - name: "Average Depreciation Rate Percent"
      expr: AVG(depreciation_rate_percent)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Functional Currency Amount"
      expr: SUM(functional_currency_amount)
    - name: "Average Functional Currency Amount"
      expr: AVG(functional_currency_amount)
    - name: "Total Impairment Amount"
      expr: SUM(impairment_amount)
    - name: "Average Impairment Amount"
      expr: AVG(impairment_amount)
    - name: "Total Bonus Depreciation Amount"
      expr: SUM(bonus_depreciation_amount)
    - name: "Average Bonus Depreciation Amount"
      expr: AVG(bonus_depreciation_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_audit_control`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit Control business metrics"
  source: "`cmoore_customer_demos`.`finance`.`audit_control`"
  dimensions:
    - name: "Control Number"
      expr: control_number
    - name: "Control Name"
      expr: control_name
    - name: "Control Description"
      expr: control_description
    - name: "Control Type"
      expr: control_type
    - name: "Control Category"
      expr: control_category
    - name: "Control Objective"
      expr: control_objective
    - name: "Risk Rating"
      expr: risk_rating
    - name: "Control Frequency"
      expr: control_frequency
    - name: "Automation Level"
      expr: automation_level
    - name: "Control Owner Name"
      expr: control_owner_name
    - name: "Control Owner Title"
      expr: control_owner_title
    - name: "Control Owner Department"
      expr: control_owner_department
    - name: "Control Owner Email"
      expr: control_owner_email
    - name: "Reviewer Name"
      expr: reviewer_name
    - name: "Reviewer Title"
      expr: reviewer_title
    - name: "Reviewer Email"
      expr: reviewer_email
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit Control"
      expr: COUNT(DISTINCT audit_control_id)
    - name: "Total Approval Threshold Amount"
      expr: SUM(approval_threshold_amount)
    - name: "Average Approval Threshold Amount"
      expr: AVG(approval_threshold_amount)
    - name: "Total Exception Tolerance Percentage"
      expr: SUM(exception_tolerance_percentage)
    - name: "Average Exception Tolerance Percentage"
      expr: AVG(exception_tolerance_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_audit_issue`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Audit Issue business metrics"
  source: "`cmoore_customer_demos`.`finance`.`audit_issue`"
  dimensions:
    - name: "Audit Number"
      expr: audit_number
    - name: "Audit Category"
      expr: audit_category
    - name: "Severity"
      expr: severity
    - name: "Control Name"
      expr: control_name
    - name: "Audit Source"
      expr: audit_source
    - name: "Discovery Date"
      expr: discovery_date
    - name: "Reported Date"
      expr: reported_date
    - name: "Remediation Action"
      expr: remediation_action
    - name: "Remediation Owner"
      expr: remediation_owner
    - name: "Remediation Status"
      expr: remediation_status
    - name: "Remediation Completed Date"
      expr: remediation_completed_date
    - name: "Status"
      expr: status
    - name: "Resolution Summary"
      expr: resolution_summary
    - name: "Resolution Date"
      expr: resolution_date
    - name: "Audit Owner"
      expr: audit_owner
    - name: "Audit Team"
      expr: audit_team
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Audit Issue"
      expr: COUNT(DISTINCT audit_issue_id)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
    - name: "Total Audit Score"
      expr: SUM(audit_score)
    - name: "Average Audit Score"
      expr: AVG(audit_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_balance_sheet`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Balance Sheet business metrics"
  source: "`cmoore_customer_demos`.`finance`.`balance_sheet`"
  dimensions:
    - name: "Reporting Entity Code"
      expr: reporting_entity_code
    - name: "Reporting Entity Name"
      expr: reporting_entity_name
    - name: "Ledger Name"
      expr: ledger_name
    - name: "Ledger Type"
      expr: ledger_type
    - name: "Currency Code"
      expr: currency_code
    - name: "Functional Currency Code"
      expr: functional_currency_code
    - name: "Reporting Currency Code"
      expr: reporting_currency_code
    - name: "Status"
      expr: status
    - name: "Consolidation Level"
      expr: consolidation_level
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Gaap Basis Indicator"
      expr: gaap_basis_indicator
    - name: "Ifrs Basis Indicator"
      expr: ifrs_basis_indicator
    - name: "Statutory Basis Indicator"
      expr: statutory_basis_indicator
    - name: "Audit Firm Name"
      expr: audit_firm_name
    - name: "Audit Opinion Type"
      expr: audit_opinion_type
    - name: "Sox Certification Indicator"
      expr: sox_certification_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Balance Sheet"
      expr: COUNT(DISTINCT balance_sheet_id)
    - name: "Total Total Assets"
      expr: SUM(total_assets)
    - name: "Average Total Assets"
      expr: AVG(total_assets)
    - name: "Total Current Assets"
      expr: SUM(current_assets)
    - name: "Average Current Assets"
      expr: AVG(current_assets)
    - name: "Total Cash And Cash Equivalents"
      expr: SUM(cash_and_cash_equivalents)
    - name: "Average Cash And Cash Equivalents"
      expr: AVG(cash_and_cash_equivalents)
    - name: "Total Short Term Investments"
      expr: SUM(short_term_investments)
    - name: "Average Short Term Investments"
      expr: AVG(short_term_investments)
    - name: "Total Accounts Receivable"
      expr: SUM(accounts_receivable)
    - name: "Average Accounts Receivable"
      expr: AVG(accounts_receivable)
    - name: "Total Premium Receivable"
      expr: SUM(premium_receivable)
    - name: "Average Premium Receivable"
      expr: AVG(premium_receivable)
    - name: "Total Reinsurance Recoverable"
      expr: SUM(reinsurance_recoverable)
    - name: "Average Reinsurance Recoverable"
      expr: AVG(reinsurance_recoverable)
    - name: "Total Allowance For Doubtful Accounts"
      expr: SUM(allowance_for_doubtful_accounts)
    - name: "Average Allowance For Doubtful Accounts"
      expr: AVG(allowance_for_doubtful_accounts)
    - name: "Total Prepaid Expenses"
      expr: SUM(prepaid_expenses)
    - name: "Average Prepaid Expenses"
      expr: AVG(prepaid_expenses)
    - name: "Total Deferred Acquisition Costs"
      expr: SUM(deferred_acquisition_costs)
    - name: "Average Deferred Acquisition Costs"
      expr: AVG(deferred_acquisition_costs)
    - name: "Total Other Current Assets"
      expr: SUM(other_current_assets)
    - name: "Average Other Current Assets"
      expr: AVG(other_current_assets)
    - name: "Total Non Current Assets"
      expr: SUM(non_current_assets)
    - name: "Average Non Current Assets"
      expr: AVG(non_current_assets)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_budget`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Budget business metrics"
  source: "`cmoore_customer_demos`.`finance`.`budget`"
  dimensions:
    - name: "Cost Center Code"
      expr: cost_center_code
    - name: "Account Code"
      expr: account_code
    - name: "Business Unit Code"
      expr: business_unit_code
    - name: "Business Unit Name"
      expr: business_unit_name
    - name: "Department Code"
      expr: department_code
    - name: "Department Name"
      expr: department_name
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Line"
      expr: product_line
    - name: "Currency Code"
      expr: currency_code
    - name: "Type"
      expr: type
    - name: "Subcategory"
      expr: subcategory
    - name: "Version Number"
      expr: version_number
    - name: "Version Name"
      expr: version_name
    - name: "Status"
      expr: status
    - name: "Approval Status"
      expr: approval_status
    - name: "Approved By"
      expr: approved_by
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Budget"
      expr: COUNT(DISTINCT budget_id)
    - name: "Total Amount"
      expr: SUM(amount)
    - name: "Average Amount"
      expr: AVG(amount)
    - name: "Total Variance Threshold Percent"
      expr: SUM(variance_threshold_percent)
    - name: "Average Variance Threshold Percent"
      expr: AVG(variance_threshold_percent)
    - name: "Total Pmpm Amount"
      expr: SUM(pmpm_amount)
    - name: "Average Pmpm Amount"
      expr: AVG(pmpm_amount)
    - name: "Total Pepm Amount"
      expr: SUM(pepm_amount)
    - name: "Average Pepm Amount"
      expr: AVG(pepm_amount)
    - name: "Total Inflation Rate Percent"
      expr: SUM(inflation_rate_percent)
    - name: "Average Inflation Rate Percent"
      expr: AVG(inflation_rate_percent)
    - name: "Total Trend Rate Percent"
      expr: SUM(trend_rate_percent)
    - name: "Average Trend Rate Percent"
      expr: AVG(trend_rate_percent)
    - name: "Total Baseline Amount"
      expr: SUM(baseline_amount)
    - name: "Average Baseline Amount"
      expr: AVG(baseline_amount)
    - name: "Total Prior Year Actual Amount"
      expr: SUM(prior_year_actual_amount)
    - name: "Average Prior Year Actual Amount"
      expr: AVG(prior_year_actual_amount)
    - name: "Total Forecast Amount"
      expr: SUM(forecast_amount)
    - name: "Average Forecast Amount"
      expr: AVG(forecast_amount)
    - name: "Total Committed Amount"
      expr: SUM(committed_amount)
    - name: "Average Committed Amount"
      expr: AVG(committed_amount)
    - name: "Total Reserved Amount"
      expr: SUM(reserved_amount)
    - name: "Average Reserved Amount"
      expr: AVG(reserved_amount)
    - name: "Total Available Amount"
      expr: SUM(available_amount)
    - name: "Average Available Amount"
      expr: AVG(available_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_budget_allocation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Budget Allocation business metrics"
  source: "`cmoore_customer_demos`.`finance`.`budget_allocation`"
  dimensions:
    - name: "Fiscal Year"
      expr: fiscal_year
    - name: "Allocation Date"
      expr: allocation_date
    - name: "Approval Status"
      expr: approval_status
    - name: "Allocation Type"
      expr: allocation_type
    - name: "Notes"
      expr: notes
    - name: "Created Date"
      expr: created_date
    - name: "Modified Date"
      expr: modified_date
    - name: "Allocation Date Month"
      expr: DATE_TRUNC('MONTH', allocation_date)
    - name: "Created Date Month"
      expr: DATE_TRUNC('MONTH', created_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Budget Allocation"
      expr: COUNT(DISTINCT budget_allocation_id)
    - name: "Total Allocated Amount"
      expr: SUM(allocated_amount)
    - name: "Average Allocated Amount"
      expr: AVG(allocated_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_budget_line`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Budget Line business metrics"
  source: "`cmoore_customer_demos`.`finance`.`budget_line`"
  dimensions:
    - name: "Line Number"
      expr: line_number
    - name: "Account Code"
      expr: account_code
    - name: "Cost Center Code"
      expr: cost_center_code
    - name: "Department Code"
      expr: department_code
    - name: "Department Name"
      expr: department_name
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Line"
      expr: product_line
    - name: "Currency Code"
      expr: currency_code
    - name: "Allocation Method"
      expr: allocation_method
    - name: "Allocation Driver"
      expr: allocation_driver
    - name: "Expense Type"
      expr: expense_type
    - name: "Mlr Category"
      expr: mlr_category
    - name: "Mlr Subcategory"
      expr: mlr_subcategory
    - name: "Statutory Reporting Category"
      expr: statutory_reporting_category
    - name: "Gaap Classification"
      expr: gaap_classification
    - name: "Sap Cost Element"
      expr: sap_cost_element
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Budget Line"
      expr: COUNT(DISTINCT budget_line_id)
    - name: "Total Original Budget Amount"
      expr: SUM(original_budget_amount)
    - name: "Average Original Budget Amount"
      expr: AVG(original_budget_amount)
    - name: "Total Revised Budget Amount"
      expr: SUM(revised_budget_amount)
    - name: "Average Revised Budget Amount"
      expr: AVG(revised_budget_amount)
    - name: "Total Committed Amount"
      expr: SUM(committed_amount)
    - name: "Average Committed Amount"
      expr: AVG(committed_amount)
    - name: "Total Actual Amount"
      expr: SUM(actual_amount)
    - name: "Average Actual Amount"
      expr: AVG(actual_amount)
    - name: "Total Variance Amount"
      expr: SUM(variance_amount)
    - name: "Average Variance Amount"
      expr: AVG(variance_amount)
    - name: "Total Variance Percentage"
      expr: SUM(variance_percentage)
    - name: "Average Variance Percentage"
      expr: AVG(variance_percentage)
    - name: "Total Allocation Percentage"
      expr: SUM(allocation_percentage)
    - name: "Average Allocation Percentage"
      expr: AVG(allocation_percentage)
    - name: "Total Allocation Driver Value"
      expr: SUM(allocation_driver_value)
    - name: "Average Allocation Driver Value"
      expr: AVG(allocation_driver_value)
    - name: "Total Contingency Percentage"
      expr: SUM(contingency_percentage)
    - name: "Average Contingency Percentage"
      expr: AVG(contingency_percentage)
    - name: "Total Contingency Amount"
      expr: SUM(contingency_amount)
    - name: "Average Contingency Amount"
      expr: AVG(contingency_amount)
    - name: "Total Baseline Amount"
      expr: SUM(baseline_amount)
    - name: "Average Baseline Amount"
      expr: AVG(baseline_amount)
    - name: "Total Growth Rate"
      expr: SUM(growth_rate)
    - name: "Average Growth Rate"
      expr: AVG(growth_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_cash_flow_statement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cash Flow Statement business metrics"
  source: "`cmoore_customer_demos`.`finance`.`cash_flow_statement`"
  dimensions:
    - name: "Reporting Entity Code"
      expr: reporting_entity_code
    - name: "Reporting Entity Name"
      expr: reporting_entity_name
    - name: "Statement Type"
      expr: statement_type
    - name: "Statement Status"
      expr: statement_status
    - name: "Currency Code"
      expr: currency_code
    - name: "Functional Currency Code"
      expr: functional_currency_code
    - name: "Presentation Method"
      expr: presentation_method
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Gaap Basis"
      expr: gaap_basis
    - name: "Consolidation Level"
      expr: consolidation_level
    - name: "Restatement Indicator"
      expr: restatement_indicator
    - name: "Restatement Reason"
      expr: restatement_reason
    - name: "Audit Status"
      expr: audit_status
    - name: "Auditor Name"
      expr: auditor_name
    - name: "Audit Opinion"
      expr: audit_opinion
    - name: "Filing Type"
      expr: filing_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cash Flow Statement"
      expr: COUNT(DISTINCT cash_flow_statement_id)
    - name: "Total Net Income"
      expr: SUM(net_income)
    - name: "Average Net Income"
      expr: AVG(net_income)
    - name: "Total Depreciation Amortization"
      expr: SUM(depreciation_amortization)
    - name: "Average Depreciation Amortization"
      expr: AVG(depreciation_amortization)
    - name: "Total Deferred Income Tax"
      expr: SUM(deferred_income_tax)
    - name: "Average Deferred Income Tax"
      expr: AVG(deferred_income_tax)
    - name: "Total Stock Based Compensation"
      expr: SUM(stock_based_compensation)
    - name: "Average Stock Based Compensation"
      expr: AVG(stock_based_compensation)
    - name: "Total Gain Loss On Asset Disposal"
      expr: SUM(gain_loss_on_asset_disposal)
    - name: "Average Gain Loss On Asset Disposal"
      expr: AVG(gain_loss_on_asset_disposal)
    - name: "Total Impairment Charges"
      expr: SUM(impairment_charges)
    - name: "Average Impairment Charges"
      expr: AVG(impairment_charges)
    - name: "Total Change In Accounts Receivable"
      expr: SUM(change_in_accounts_receivable)
    - name: "Average Change In Accounts Receivable"
      expr: AVG(change_in_accounts_receivable)
    - name: "Total Change In Premium Receivable"
      expr: SUM(change_in_premium_receivable)
    - name: "Average Change In Premium Receivable"
      expr: AVG(change_in_premium_receivable)
    - name: "Total Change In Claims Receivable"
      expr: SUM(change_in_claims_receivable)
    - name: "Average Change In Claims Receivable"
      expr: AVG(change_in_claims_receivable)
    - name: "Total Change In Prepaid Expenses"
      expr: SUM(change_in_prepaid_expenses)
    - name: "Average Change In Prepaid Expenses"
      expr: AVG(change_in_prepaid_expenses)
    - name: "Total Change In Accounts Payable"
      expr: SUM(change_in_accounts_payable)
    - name: "Average Change In Accounts Payable"
      expr: AVG(change_in_accounts_payable)
    - name: "Total Change In Claims Payable"
      expr: SUM(change_in_claims_payable)
    - name: "Average Change In Claims Payable"
      expr: AVG(change_in_claims_payable)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_cash_management`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cash Management business metrics"
  source: "`cmoore_customer_demos`.`finance`.`cash_management`"
  dimensions:
    - name: "Account Number"
      expr: account_number
    - name: "Account Name"
      expr: account_name
    - name: "Account Type"
      expr: account_type
    - name: "Bank Name"
      expr: bank_name
    - name: "Bank Routing Number"
      expr: bank_routing_number
    - name: "Swift Code"
      expr: swift_code
    - name: "Iban"
      expr: iban
    - name: "Currency Code"
      expr: currency_code
    - name: "Balance As Of Date"
      expr: balance_as_of_date
    - name: "Balance As Of Timestamp"
      expr: balance_as_of_timestamp
    - name: "Sweep Indicator"
      expr: sweep_indicator
    - name: "Sweep Type"
      expr: sweep_type
    - name: "Sweep Frequency"
      expr: sweep_frequency
    - name: "Last Sweep Date"
      expr: last_sweep_date
    - name: "Concentration Account Indicator"
      expr: concentration_account_indicator
    - name: "Zero Balance Account Indicator"
      expr: zero_balance_account_indicator
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cash Management"
      expr: COUNT(DISTINCT cash_management_id)
    - name: "Total Current Balance"
      expr: SUM(current_balance)
    - name: "Average Current Balance"
      expr: AVG(current_balance)
    - name: "Total Available Balance"
      expr: SUM(available_balance)
    - name: "Average Available Balance"
      expr: AVG(available_balance)
    - name: "Total Ledger Balance"
      expr: SUM(ledger_balance)
    - name: "Average Ledger Balance"
      expr: AVG(ledger_balance)
    - name: "Total Collected Balance"
      expr: SUM(collected_balance)
    - name: "Average Collected Balance"
      expr: AVG(collected_balance)
    - name: "Total Opening Balance"
      expr: SUM(opening_balance)
    - name: "Average Opening Balance"
      expr: AVG(opening_balance)
    - name: "Total Closing Balance"
      expr: SUM(closing_balance)
    - name: "Average Closing Balance"
      expr: AVG(closing_balance)
    - name: "Total Minimum Balance Required"
      expr: SUM(minimum_balance_required)
    - name: "Average Minimum Balance Required"
      expr: AVG(minimum_balance_required)
    - name: "Total Target Balance"
      expr: SUM(target_balance)
    - name: "Average Target Balance"
      expr: AVG(target_balance)
    - name: "Total Maximum Balance Limit"
      expr: SUM(maximum_balance_limit)
    - name: "Average Maximum Balance Limit"
      expr: AVG(maximum_balance_limit)
    - name: "Total Total Deposits Today"
      expr: SUM(total_deposits_today)
    - name: "Average Total Deposits Today"
      expr: AVG(total_deposits_today)
    - name: "Total Total Withdrawals Today"
      expr: SUM(total_withdrawals_today)
    - name: "Average Total Withdrawals Today"
      expr: AVG(total_withdrawals_today)
    - name: "Total Pending Deposits"
      expr: SUM(pending_deposits)
    - name: "Average Pending Deposits"
      expr: AVG(pending_deposits)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_chart_of_accounts`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Chart Of Accounts business metrics"
  source: "`cmoore_customer_demos`.`finance`.`chart_of_accounts`"
  dimensions:
    - name: "Account Number"
      expr: account_number
    - name: "Account Name"
      expr: account_name
    - name: "Account Description"
      expr: account_description
    - name: "Account Type"
      expr: account_type
    - name: "Account Subtype"
      expr: account_subtype
    - name: "Normal Balance"
      expr: normal_balance
    - name: "Parent Account Number"
      expr: parent_account_number
    - name: "Level"
      expr: level
    - name: "Is Summary Account"
      expr: is_summary_account
    - name: "Posting Allowed"
      expr: posting_allowed
    - name: "Status"
      expr: status
    - name: "Financial Statement Category"
      expr: financial_statement_category
    - name: "Financial Statement Line Item"
      expr: financial_statement_line_item
    - name: "Statutory Reporting Category"
      expr: statutory_reporting_category
    - name: "Mlr Category"
      expr: mlr_category
    - name: "Department Code"
      expr: department_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Chart Of Accounts"
      expr: COUNT(DISTINCT chart_of_accounts_id)
    - name: "Total Approval Threshold Amount"
      expr: SUM(approval_threshold_amount)
    - name: "Average Approval Threshold Amount"
      expr: AVG(approval_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_cost_center`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cost Center business metrics"
  source: "`cmoore_customer_demos`.`finance`.`cost_center`"
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
    - name: "Parent Cost Center Code"
      expr: parent_cost_center_code
    - name: "Level"
      expr: level
    - name: "Manager Name"
      expr: manager_name
    - name: "Manager Email"
      expr: manager_email
    - name: "Legal Entity Code"
      expr: legal_entity_code
    - name: "Legal Entity Name"
      expr: legal_entity_name
    - name: "Company Code"
      expr: company_code
    - name: "Business Unit"
      expr: business_unit
    - name: "Division"
      expr: division
    - name: "Department"
      expr: department
    - name: "Lob"
      expr: lob
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cost Center"
      expr: COUNT(DISTINCT cost_center_id)
    - name: "Total Budget Amount"
      expr: SUM(budget_amount)
    - name: "Average Budget Amount"
      expr: AVG(budget_amount)
    - name: "Total Actual Spend Amount"
      expr: SUM(actual_spend_amount)
    - name: "Average Actual Spend Amount"
      expr: AVG(actual_spend_amount)
    - name: "Total Committed Amount"
      expr: SUM(committed_amount)
    - name: "Average Committed Amount"
      expr: AVG(committed_amount)
    - name: "Total Variance Amount"
      expr: SUM(variance_amount)
    - name: "Average Variance Amount"
      expr: AVG(variance_amount)
    - name: "Total Approval Threshold Amount"
      expr: SUM(approval_threshold_amount)
    - name: "Average Approval Threshold Amount"
      expr: AVG(approval_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_cost_center_contract_allocation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cost Center Contract Allocation business metrics"
  source: "`cmoore_customer_demos`.`finance`.`cost_center_contract_allocation`"
  dimensions:
    - name: "Allocation Method"
      expr: allocation_method
    - name: "Effective Date"
      expr: effective_date
    - name: "End Date"
      expr: end_date
    - name: "Allocation Status"
      expr: allocation_status
    - name: "Allocation Notes"
      expr: allocation_notes
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Modified By"
      expr: last_modified_by
    - name: "Last Modified Timestamp"
      expr: last_modified_timestamp
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "End Date Month"
      expr: DATE_TRUNC('MONTH', end_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Cost Center Contract Allocation"
      expr: COUNT(DISTINCT allocation_id)
    - name: "Total Allocation Percentage"
      expr: SUM(allocation_percentage)
    - name: "Average Allocation Percentage"
      expr: AVG(allocation_percentage)
    - name: "Total Allocation Amount"
      expr: SUM(allocation_amount)
    - name: "Average Allocation Amount"
      expr: AVG(allocation_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_currency_rate`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Currency Rate business metrics"
  source: "`cmoore_customer_demos`.`finance`.`currency_rate`"
  dimensions:
    - name: "Currency Code"
      expr: currency_code
    - name: "Currency Name"
      expr: currency_name
    - name: "Base Currency Code"
      expr: base_currency_code
    - name: "Rate Date"
      expr: rate_date
    - name: "Rate Timestamp"
      expr: rate_timestamp
    - name: "Rate Type"
      expr: rate_type
    - name: "Source System"
      expr: source_system
    - name: "Market"
      expr: market
    - name: "Is Historical"
      expr: is_historical
    - name: "Effective Timestamp"
      expr: effective_timestamp
    - name: "Expiration Timestamp"
      expr: expiration_timestamp
    - name: "Status"
      expr: status
    - name: "Notes"
      expr: notes
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Precision"
      expr: precision
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Currency Rate"
      expr: COUNT(DISTINCT currency_rate_id)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Multiplier"
      expr: SUM(multiplier)
    - name: "Average Multiplier"
      expr: AVG(multiplier)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_finance_account`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Finance Account business metrics"
  source: "`cmoore_customer_demos`.`finance`.`finance_account`"
  dimensions:
    - name: "Number"
      expr: number
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Subcategory"
      expr: subcategory
    - name: "Normal Balance"
      expr: normal_balance
    - name: "Currency Code"
      expr: currency_code
    - name: "Status"
      expr: status
    - name: "Is Control Account"
      expr: is_control_account
    - name: "Is Posting Allowed"
      expr: is_posting_allowed
    - name: "Is Reconciliation Required"
      expr: is_reconciliation_required
    - name: "Reconciliation Frequency"
      expr: reconciliation_frequency
    - name: "Is Budget Enabled"
      expr: is_budget_enabled
    - name: "Is Statistical Account"
      expr: is_statistical_account
    - name: "Parent Account Number"
      expr: parent_account_number
    - name: "Level"
      expr: level
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Finance Account"
      expr: COUNT(DISTINCT finance_account_id)
    - name: "Total Approval Threshold Amount"
      expr: SUM(approval_threshold_amount)
    - name: "Average Approval Threshold Amount"
      expr: AVG(approval_threshold_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_financial_dimension`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial Dimension business metrics"
  source: "`cmoore_customer_demos`.`finance`.`financial_dimension`"
  dimensions:
    - name: "Dimension Name"
      expr: dimension_name
    - name: "Dimension Type"
      expr: dimension_type
    - name: "Description"
      expr: description
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Status"
      expr: status
    - name: "Hierarchy Level"
      expr: hierarchy_level
    - name: "Department Code"
      expr: department_code
    - name: "Project Code"
      expr: project_code
    - name: "Cost Center Code"
      expr: cost_center_code
    - name: "Profit Center Code"
      expr: profit_center_code
    - name: "Region Code"
      expr: region_code
    - name: "Business Unit"
      expr: business_unit
    - name: "Ledger Name"
      expr: ledger_name
    - name: "Currency Code"
      expr: currency_code
    - name: "Allocation Method"
      expr: allocation_method
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Financial Dimension"
      expr: COUNT(DISTINCT financial_dimension_id)
    - name: "Total Allocation Percentage"
      expr: SUM(allocation_percentage)
    - name: "Average Allocation Percentage"
      expr: AVG(allocation_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_financial_period`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial Period business metrics"
  source: "`cmoore_customer_demos`.`finance`.`financial_period`"
  dimensions:
    - name: "Period Name"
      expr: period_name
    - name: "Period Type"
      expr: period_type
    - name: "Fiscal Year"
      expr: fiscal_year
    - name: "Fiscal Quarter"
      expr: fiscal_quarter
    - name: "Fiscal Month"
      expr: fiscal_month
    - name: "Fiscal Week"
      expr: fiscal_week
    - name: "Calendar Year"
      expr: calendar_year
    - name: "Calendar Quarter"
      expr: calendar_quarter
    - name: "Calendar Month"
      expr: calendar_month
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Period Status"
      expr: period_status
    - name: "Adjustment Period Flag"
      expr: adjustment_period_flag
    - name: "Number Of Days"
      expr: number_of_days
    - name: "Number Of Business Days"
      expr: number_of_business_days
    - name: "Opening Date"
      expr: opening_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Financial Period"
      expr: COUNT(DISTINCT financial_period_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_financial_statement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial Statement business metrics"
  source: "`cmoore_customer_demos`.`finance`.`financial_statement`"
  dimensions:
    - name: "Statement Type"
      expr: statement_type
    - name: "Statement Name"
      expr: statement_name
    - name: "Statement Version"
      expr: statement_version
    - name: "Accounting Standard"
      expr: accounting_standard
    - name: "Reporting Entity Name"
      expr: reporting_entity_name
    - name: "Reporting Entity Type"
      expr: reporting_entity_type
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Legal Entity Identifier"
      expr: legal_entity_identifier
    - name: "Tax Identification Number"
      expr: tax_identification_number
    - name: "Naic Company Code"
      expr: naic_company_code
    - name: "State Of Domicile"
      expr: state_of_domicile
    - name: "Currency Code"
      expr: currency_code
    - name: "Presentation Currency"
      expr: presentation_currency
    - name: "Rounding Unit"
      expr: rounding_unit
    - name: "Statement Status"
      expr: statement_status
    - name: "Approval Status"
      expr: approval_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Financial Statement"
      expr: COUNT(DISTINCT financial_statement_id)
    - name: "Total Mlr Percentage"
      expr: SUM(mlr_percentage)
    - name: "Average Mlr Percentage"
      expr: AVG(mlr_percentage)
    - name: "Total Mlr Rebate Amount"
      expr: SUM(mlr_rebate_amount)
    - name: "Average Mlr Rebate Amount"
      expr: AVG(mlr_rebate_amount)
    - name: "Total Statutory Surplus"
      expr: SUM(statutory_surplus)
    - name: "Average Statutory Surplus"
      expr: AVG(statutory_surplus)
    - name: "Total Risk Based Capital Ratio"
      expr: SUM(risk_based_capital_ratio)
    - name: "Average Risk Based Capital Ratio"
      expr: AVG(risk_based_capital_ratio)
    - name: "Total Total Assets"
      expr: SUM(total_assets)
    - name: "Average Total Assets"
      expr: AVG(total_assets)
    - name: "Total Total Liabilities"
      expr: SUM(total_liabilities)
    - name: "Average Total Liabilities"
      expr: AVG(total_liabilities)
    - name: "Total Total Equity"
      expr: SUM(total_equity)
    - name: "Average Total Equity"
      expr: AVG(total_equity)
    - name: "Total Total Revenue"
      expr: SUM(total_revenue)
    - name: "Average Total Revenue"
      expr: AVG(total_revenue)
    - name: "Total Net Income"
      expr: SUM(net_income)
    - name: "Average Net Income"
      expr: AVG(net_income)
    - name: "Total Operating Cash Flow"
      expr: SUM(operating_cash_flow)
    - name: "Average Operating Cash Flow"
      expr: AVG(operating_cash_flow)
    - name: "Total Claims Reserves"
      expr: SUM(claims_reserves)
    - name: "Average Claims Reserves"
      expr: AVG(claims_reserves)
    - name: "Total Premium Revenue"
      expr: SUM(premium_revenue)
    - name: "Average Premium Revenue"
      expr: AVG(premium_revenue)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_fixed_asset`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Fixed Asset business metrics"
  source: "`cmoore_customer_demos`.`finance`.`fixed_asset`"
  dimensions:
    - name: "Asset Number"
      expr: asset_number
    - name: "Asset Name"
      expr: asset_name
    - name: "Asset Description"
      expr: asset_description
    - name: "Asset Category"
      expr: asset_category
    - name: "Asset Class"
      expr: asset_class
    - name: "Asset Type"
      expr: asset_type
    - name: "Asset Status"
      expr: asset_status
    - name: "Acquisition Date"
      expr: acquisition_date
    - name: "Placed In Service Date"
      expr: placed_in_service_date
    - name: "Depreciation Method"
      expr: depreciation_method
    - name: "Useful Life Months"
      expr: useful_life_months
    - name: "Remaining Life Months"
      expr: remaining_life_months
    - name: "Last Depreciation Date"
      expr: last_depreciation_date
    - name: "Next Depreciation Date"
      expr: next_depreciation_date
    - name: "Depreciation Frequency"
      expr: depreciation_frequency
    - name: "Currency Code"
      expr: currency_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Fixed Asset"
      expr: COUNT(DISTINCT fixed_asset_id)
    - name: "Total Acquisition Cost"
      expr: SUM(acquisition_cost)
    - name: "Average Acquisition Cost"
      expr: AVG(acquisition_cost)
    - name: "Total Capitalized Cost"
      expr: SUM(capitalized_cost)
    - name: "Average Capitalized Cost"
      expr: AVG(capitalized_cost)
    - name: "Total Salvage Value"
      expr: SUM(salvage_value)
    - name: "Average Salvage Value"
      expr: AVG(salvage_value)
    - name: "Total Book Value"
      expr: SUM(book_value)
    - name: "Average Book Value"
      expr: AVG(book_value)
    - name: "Total Accumulated Depreciation"
      expr: SUM(accumulated_depreciation)
    - name: "Average Accumulated Depreciation"
      expr: AVG(accumulated_depreciation)
    - name: "Total Useful Life Years"
      expr: SUM(useful_life_years)
    - name: "Average Useful Life Years"
      expr: AVG(useful_life_years)
    - name: "Total Depreciation Rate Percent"
      expr: SUM(depreciation_rate_percent)
    - name: "Average Depreciation Rate Percent"
      expr: AVG(depreciation_rate_percent)
    - name: "Total Insured Value"
      expr: SUM(insured_value)
    - name: "Average Insured Value"
      expr: AVG(insured_value)
    - name: "Total Disposal Proceeds"
      expr: SUM(disposal_proceeds)
    - name: "Average Disposal Proceeds"
      expr: AVG(disposal_proceeds)
    - name: "Total Gain Loss On Disposal"
      expr: SUM(gain_loss_on_disposal)
    - name: "Average Gain Loss On Disposal"
      expr: AVG(gain_loss_on_disposal)
    - name: "Total Tax Useful Life Years"
      expr: SUM(tax_useful_life_years)
    - name: "Average Tax Useful Life Years"
      expr: AVG(tax_useful_life_years)
    - name: "Total Tax Accumulated Depreciation"
      expr: SUM(tax_accumulated_depreciation)
    - name: "Average Tax Accumulated Depreciation"
      expr: AVG(tax_accumulated_depreciation)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_general_ledger`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "General Ledger business metrics"
  source: "`cmoore_customer_demos`.`finance`.`general_ledger`"
  dimensions:
    - name: "Ledger Name"
      expr: ledger_name
    - name: "Journal Entry Number"
      expr: journal_entry_number
    - name: "Journal Entry Line Number"
      expr: journal_entry_line_number
    - name: "Accounting Date"
      expr: accounting_date
    - name: "Effective Date"
      expr: effective_date
    - name: "Posting Date"
      expr: posting_date
    - name: "Reversal Date"
      expr: reversal_date
    - name: "Account Code"
      expr: account_code
    - name: "Cost Center"
      expr: cost_center
    - name: "Department"
      expr: department
    - name: "Business Unit"
      expr: business_unit
    - name: "Segment"
      expr: segment
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Code"
      expr: product_code
    - name: "Project Code"
      expr: project_code
    - name: "Profit Center Code"
      expr: profit_center_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct General Ledger"
      expr: COUNT(DISTINCT general_ledger_id)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Entered Debit Amount"
      expr: SUM(entered_debit_amount)
    - name: "Average Entered Debit Amount"
      expr: AVG(entered_debit_amount)
    - name: "Total Entered Credit Amount"
      expr: SUM(entered_credit_amount)
    - name: "Average Entered Credit Amount"
      expr: AVG(entered_credit_amount)
    - name: "Total Accounted Debit Amount"
      expr: SUM(accounted_debit_amount)
    - name: "Average Accounted Debit Amount"
      expr: AVG(accounted_debit_amount)
    - name: "Total Accounted Credit Amount"
      expr: SUM(accounted_credit_amount)
    - name: "Average Accounted Credit Amount"
      expr: AVG(accounted_credit_amount)
    - name: "Total Statistical Amount"
      expr: SUM(statistical_amount)
    - name: "Average Statistical Amount"
      expr: AVG(statistical_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Accrual Amount"
      expr: SUM(accrual_amount)
    - name: "Average Accrual Amount"
      expr: AVG(accrual_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_income_statement`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Income Statement business metrics"
  source: "`cmoore_customer_demos`.`finance`.`income_statement`"
  dimensions:
    - name: "Reporting Entity Name"
      expr: reporting_entity_name
    - name: "Reporting Entity Tax Number"
      expr: reporting_entity_tax_number
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Type"
      expr: product_type
    - name: "State Jurisdiction"
      expr: state_jurisdiction
    - name: "Accounting Standard"
      expr: accounting_standard
    - name: "Statement Type"
      expr: statement_type
    - name: "Currency Code"
      expr: currency_code
    - name: "Member Months"
      expr: member_months
    - name: "Statement Status"
      expr: statement_status
    - name: "Approval Date"
      expr: approval_date
    - name: "Approved By"
      expr: approved_by
    - name: "Filing Date"
      expr: filing_date
    - name: "Audit Status"
      expr: audit_status
    - name: "Auditor Name"
      expr: auditor_name
    - name: "Audit Opinion"
      expr: audit_opinion
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Income Statement"
      expr: COUNT(DISTINCT income_statement_id)
    - name: "Total Premium Revenue"
      expr: SUM(premium_revenue)
    - name: "Average Premium Revenue"
      expr: AVG(premium_revenue)
    - name: "Total Administrative Services Revenue"
      expr: SUM(administrative_services_revenue)
    - name: "Average Administrative Services Revenue"
      expr: AVG(administrative_services_revenue)
    - name: "Total Investment Income"
      expr: SUM(investment_income)
    - name: "Average Investment Income"
      expr: AVG(investment_income)
    - name: "Total Other Revenue"
      expr: SUM(other_revenue)
    - name: "Average Other Revenue"
      expr: AVG(other_revenue)
    - name: "Total Total Revenue"
      expr: SUM(total_revenue)
    - name: "Average Total Revenue"
      expr: AVG(total_revenue)
    - name: "Total Medical Claims Expense"
      expr: SUM(medical_claims_expense)
    - name: "Average Medical Claims Expense"
      expr: AVG(medical_claims_expense)
    - name: "Total Pharmacy Claims Expense"
      expr: SUM(pharmacy_claims_expense)
    - name: "Average Pharmacy Claims Expense"
      expr: AVG(pharmacy_claims_expense)
    - name: "Total Capitation Expense"
      expr: SUM(capitation_expense)
    - name: "Average Capitation Expense"
      expr: AVG(capitation_expense)
    - name: "Total Reinsurance Expense"
      expr: SUM(reinsurance_expense)
    - name: "Average Reinsurance Expense"
      expr: AVG(reinsurance_expense)
    - name: "Total Quality Incentive Expense"
      expr: SUM(quality_incentive_expense)
    - name: "Average Quality Incentive Expense"
      expr: AVG(quality_incentive_expense)
    - name: "Total Care Management Expense"
      expr: SUM(care_management_expense)
    - name: "Average Care Management Expense"
      expr: AVG(care_management_expense)
    - name: "Total Total Medical Expense"
      expr: SUM(total_medical_expense)
    - name: "Average Total Medical Expense"
      expr: AVG(total_medical_expense)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_intercompany_transaction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Intercompany Transaction business metrics"
  source: "`cmoore_customer_demos`.`finance`.`intercompany_transaction`"
  dimensions:
    - name: "Transaction Number"
      expr: transaction_number
    - name: "Transaction Date"
      expr: transaction_date
    - name: "Posting Date"
      expr: posting_date
    - name: "Source Legal Entity Code"
      expr: source_legal_entity_code
    - name: "Source Legal Entity Name"
      expr: source_legal_entity_name
    - name: "Destination Legal Entity Code"
      expr: destination_legal_entity_code
    - name: "Destination Legal Entity Name"
      expr: destination_legal_entity_name
    - name: "Transaction Type"
      expr: transaction_type
    - name: "Transaction Category"
      expr: transaction_category
    - name: "Transaction Currency Code"
      expr: transaction_currency_code
    - name: "Functional Currency Code"
      expr: functional_currency_code
    - name: "Reporting Currency Code"
      expr: reporting_currency_code
    - name: "Exchange Rate Date"
      expr: exchange_rate_date
    - name: "Exchange Rate Type"
      expr: exchange_rate_type
    - name: "Source Account Code"
      expr: source_account_code
    - name: "Destination Account Code"
      expr: destination_account_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Intercompany Transaction"
      expr: COUNT(DISTINCT intercompany_transaction_id)
    - name: "Total Transaction Amount"
      expr: SUM(transaction_amount)
    - name: "Average Transaction Amount"
      expr: AVG(transaction_amount)
    - name: "Total Functional Currency Amount"
      expr: SUM(functional_currency_amount)
    - name: "Average Functional Currency Amount"
      expr: AVG(functional_currency_amount)
    - name: "Total Reporting Currency Amount"
      expr: SUM(reporting_currency_amount)
    - name: "Average Reporting Currency Amount"
      expr: AVG(reporting_currency_amount)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Debit Amount"
      expr: SUM(debit_amount)
    - name: "Average Debit Amount"
      expr: AVG(debit_amount)
    - name: "Total Credit Amount"
      expr: SUM(credit_amount)
    - name: "Average Credit Amount"
      expr: AVG(credit_amount)
    - name: "Total Variance Amount"
      expr: SUM(variance_amount)
    - name: "Average Variance Amount"
      expr: AVG(variance_amount)
    - name: "Total Withholding Tax Amount"
      expr: SUM(withholding_tax_amount)
    - name: "Average Withholding Tax Amount"
      expr: AVG(withholding_tax_amount)
    - name: "Total Withholding Tax Rate"
      expr: SUM(withholding_tax_rate)
    - name: "Average Withholding Tax Rate"
      expr: AVG(withholding_tax_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_lease`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Lease business metrics"
  source: "`cmoore_customer_demos`.`finance`.`lease`"
  dimensions:
    - name: "Lease Number"
      expr: lease_number
    - name: "Lease Type"
      expr: lease_type
    - name: "Lease Status"
      expr: lease_status
    - name: "Start Date"
      expr: start_date
    - name: "End Date"
      expr: end_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Lease Term Months"
      expr: lease_term_months
    - name: "Lease Term Years"
      expr: lease_term_years
    - name: "Currency Code"
      expr: currency_code
    - name: "Payment Frequency"
      expr: payment_frequency
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Due Day"
      expr: payment_due_day
    - name: "Next Payment Date"
      expr: next_payment_date
    - name: "Lessor Name"
      expr: lessor_name
    - name: "Lessee Name"
      expr: lessee_name
    - name: "Asset Description"
      expr: asset_description
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Lease"
      expr: COUNT(DISTINCT lease_id)
    - name: "Total Lease Amount"
      expr: SUM(lease_amount)
    - name: "Average Lease Amount"
      expr: AVG(lease_amount)
    - name: "Total Lease Payment Amount"
      expr: SUM(lease_payment_amount)
    - name: "Average Lease Payment Amount"
      expr: AVG(lease_payment_amount)
    - name: "Total Right Of Use Asset Value"
      expr: SUM(right_of_use_asset_value)
    - name: "Average Right Of Use Asset Value"
      expr: AVG(right_of_use_asset_value)
    - name: "Total Lease Liability"
      expr: SUM(lease_liability)
    - name: "Average Lease Liability"
      expr: AVG(lease_liability)
    - name: "Total Interest Rate"
      expr: SUM(interest_rate)
    - name: "Average Interest Rate"
      expr: AVG(interest_rate)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_mlr_calculation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Mlr Calculation business metrics"
  source: "`cmoore_customer_demos`.`finance`.`mlr_calculation`"
  dimensions:
    - name: "Line Of Business"
      expr: line_of_business
    - name: "State Code"
      expr: state_code
    - name: "Market Type"
      expr: market_type
    - name: "Calculation Status"
      expr: calculation_status
    - name: "Submission Date"
      expr: submission_date
    - name: "Issuer Hios Code"
      expr: issuer_hios_code
    - name: "Experience Period Months"
      expr: experience_period_months
    - name: "Is Grandfathered Plan"
      expr: is_grandfathered_plan
    - name: "Is Student Health Plan"
      expr: is_student_health_plan
    - name: "Is Mini Med Plan"
      expr: is_mini_med_plan
    - name: "Is Expatriate Plan"
      expr: is_expatriate_plan
    - name: "Rebate Distribution Method"
      expr: rebate_distribution_method
    - name: "Rebate Payment Deadline Date"
      expr: rebate_payment_deadline_date
    - name: "Attestation Officer Name"
      expr: attestation_officer_name
    - name: "Attestation Officer Title"
      expr: attestation_officer_title
    - name: "Attestation Date"
      expr: attestation_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Mlr Calculation"
      expr: COUNT(DISTINCT mlr_calculation_id)
    - name: "Total Total Earned Premium Amount"
      expr: SUM(total_earned_premium_amount)
    - name: "Average Total Earned Premium Amount"
      expr: AVG(total_earned_premium_amount)
    - name: "Total Federal And State Taxes Amount"
      expr: SUM(federal_and_state_taxes_amount)
    - name: "Average Federal And State Taxes Amount"
      expr: AVG(federal_and_state_taxes_amount)
    - name: "Total Adjusted Earned Premium Amount"
      expr: SUM(adjusted_earned_premium_amount)
    - name: "Average Adjusted Earned Premium Amount"
      expr: AVG(adjusted_earned_premium_amount)
    - name: "Total Incurred Claims Amount"
      expr: SUM(incurred_claims_amount)
    - name: "Average Incurred Claims Amount"
      expr: AVG(incurred_claims_amount)
    - name: "Total Paid Claims Amount"
      expr: SUM(paid_claims_amount)
    - name: "Average Paid Claims Amount"
      expr: AVG(paid_claims_amount)
    - name: "Total Claim Reserves Beginning Balance"
      expr: SUM(claim_reserves_beginning_balance)
    - name: "Average Claim Reserves Beginning Balance"
      expr: AVG(claim_reserves_beginning_balance)
    - name: "Total Claim Reserves Ending Balance"
      expr: SUM(claim_reserves_ending_balance)
    - name: "Average Claim Reserves Ending Balance"
      expr: AVG(claim_reserves_ending_balance)
    - name: "Total Quality Improvement Expenses Amount"
      expr: SUM(quality_improvement_expenses_amount)
    - name: "Average Quality Improvement Expenses Amount"
      expr: AVG(quality_improvement_expenses_amount)
    - name: "Total Fraud Reduction Expenses Amount"
      expr: SUM(fraud_reduction_expenses_amount)
    - name: "Average Fraud Reduction Expenses Amount"
      expr: AVG(fraud_reduction_expenses_amount)
    - name: "Total Care Coordination Expenses Amount"
      expr: SUM(care_coordination_expenses_amount)
    - name: "Average Care Coordination Expenses Amount"
      expr: AVG(care_coordination_expenses_amount)
    - name: "Total Total Quality Improvement Amount"
      expr: SUM(total_quality_improvement_amount)
    - name: "Average Total Quality Improvement Amount"
      expr: AVG(total_quality_improvement_amount)
    - name: "Total Mlr Numerator Amount"
      expr: SUM(mlr_numerator_amount)
    - name: "Average Mlr Numerator Amount"
      expr: AVG(mlr_numerator_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_payable`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Payable business metrics"
  source: "`cmoore_customer_demos`.`finance`.`payable`"
  dimensions:
    - name: "Vendor Name"
      expr: vendor_name
    - name: "Vendor Address"
      expr: vendor_address
    - name: "Vendor Contact Name"
      expr: vendor_contact_name
    - name: "Vendor Contact Email"
      expr: vendor_contact_email
    - name: "Vendor Contact Phone"
      expr: vendor_contact_phone
    - name: "Currency Code"
      expr: currency_code
    - name: "Payment Currency Code"
      expr: payment_currency_code
    - name: "Tax Code"
      expr: tax_code
    - name: "Discount Due Date"
      expr: discount_due_date
    - name: "Due Date"
      expr: due_date
    - name: "Payment Terms"
      expr: payment_terms
    - name: "Payment Status"
      expr: payment_status
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Channel"
      expr: payment_channel
    - name: "Payment Date"
      expr: payment_date
    - name: "Payment Reference Number"
      expr: payment_reference_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Payable"
      expr: COUNT(DISTINCT payable_id)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Original Currency Amount"
      expr: SUM(original_currency_amount)
    - name: "Average Original Currency Amount"
      expr: AVG(original_currency_amount)
    - name: "Total Payment Amount"
      expr: SUM(payment_amount)
    - name: "Average Payment Amount"
      expr: AVG(payment_amount)
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
    - name: "Total Net Amount"
      expr: SUM(net_amount)
    - name: "Average Net Amount"
      expr: AVG(net_amount)
    - name: "Total Accrual Amount"
      expr: SUM(accrual_amount)
    - name: "Average Accrual Amount"
      expr: AVG(accrual_amount)
    - name: "Total Write Off Amount"
      expr: SUM(write_off_amount)
    - name: "Average Write Off Amount"
      expr: AVG(write_off_amount)
    - name: "Total Payment Processing Fee"
      expr: SUM(payment_processing_fee)
    - name: "Average Payment Processing Fee"
      expr: AVG(payment_processing_fee)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_receivable`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Receivable business metrics"
  source: "`cmoore_customer_demos`.`finance`.`receivable`"
  dimensions:
    - name: "Service Start Date"
      expr: service_start_date
    - name: "Service End Date"
      expr: service_end_date
    - name: "Billing Period Start"
      expr: billing_period_start
    - name: "Billing Period End"
      expr: billing_period_end
    - name: "Due Date"
      expr: due_date
    - name: "Payment Date"
      expr: payment_date
    - name: "Payment Method"
      expr: payment_method
    - name: "Collection Status"
      expr: collection_status
    - name: "Aging Bucket"
      expr: aging_bucket
    - name: "Days Outstanding"
      expr: days_outstanding
    - name: "Penalty Reason"
      expr: penalty_reason
    - name: "Insurance Plan Code"
      expr: insurance_plan_code
    - name: "Member First Name"
      expr: member_first_name
    - name: "Member Last Name"
      expr: member_last_name
    - name: "Member Dob"
      expr: member_dob
    - name: "Member Address"
      expr: member_address
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Receivable"
      expr: COUNT(DISTINCT receivable_id)
    - name: "Total Original Amount"
      expr: SUM(original_amount)
    - name: "Average Original Amount"
      expr: AVG(original_amount)
    - name: "Total Outstanding Balance"
      expr: SUM(outstanding_balance)
    - name: "Average Outstanding Balance"
      expr: AVG(outstanding_balance)
    - name: "Total Write Off Amount"
      expr: SUM(write_off_amount)
    - name: "Average Write Off Amount"
      expr: AVG(write_off_amount)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Payment Amount"
      expr: SUM(payment_amount)
    - name: "Average Payment Amount"
      expr: AVG(payment_amount)
    - name: "Total Interest Amount"
      expr: SUM(interest_amount)
    - name: "Average Interest Amount"
      expr: AVG(interest_amount)
    - name: "Total Interest Rate"
      expr: SUM(interest_rate)
    - name: "Average Interest Rate"
      expr: AVG(interest_rate)
    - name: "Total Penalty Amount"
      expr: SUM(penalty_amount)
    - name: "Average Penalty Amount"
      expr: AVG(penalty_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Tax Rate"
      expr: SUM(tax_rate)
    - name: "Average Tax Rate"
      expr: AVG(tax_rate)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Risk Score"
      expr: SUM(risk_score)
    - name: "Average Risk Score"
      expr: AVG(risk_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_tax_return`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Tax Return business metrics"
  source: "`cmoore_customer_demos`.`finance`.`tax_return`"
  dimensions:
    - name: "Filing Entity Name"
      expr: filing_entity_name
    - name: "Employer Identification Number"
      expr: employer_identification_number
    - name: "Return Type"
      expr: return_type
    - name: "Form Number"
      expr: form_number
    - name: "Filing Method"
      expr: filing_method
    - name: "Jurisdiction Code"
      expr: jurisdiction_code
    - name: "Jurisdiction Name"
      expr: jurisdiction_name
    - name: "Filing Due Date"
      expr: filing_due_date
    - name: "Extended Due Date"
      expr: extended_due_date
    - name: "Actual Filing Date"
      expr: actual_filing_date
    - name: "Payment Due Date"
      expr: payment_due_date
    - name: "Payment Date"
      expr: payment_date
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Reference Number"
      expr: payment_reference_number
    - name: "Consolidated Return Indicator"
      expr: consolidated_return_indicator
    - name: "Parent Company Ein"
      expr: parent_company_ein
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Tax Return"
      expr: COUNT(DISTINCT tax_return_id)
    - name: "Total Gross Receipts Amount"
      expr: SUM(gross_receipts_amount)
    - name: "Average Gross Receipts Amount"
      expr: AVG(gross_receipts_amount)
    - name: "Total Total Income Amount"
      expr: SUM(total_income_amount)
    - name: "Average Total Income Amount"
      expr: AVG(total_income_amount)
    - name: "Total Total Deductions Amount"
      expr: SUM(total_deductions_amount)
    - name: "Average Total Deductions Amount"
      expr: AVG(total_deductions_amount)
    - name: "Total Taxable Income Amount"
      expr: SUM(taxable_income_amount)
    - name: "Average Taxable Income Amount"
      expr: AVG(taxable_income_amount)
    - name: "Total Tax Rate Percentage"
      expr: SUM(tax_rate_percentage)
    - name: "Average Tax Rate Percentage"
      expr: AVG(tax_rate_percentage)
    - name: "Total Tax Liability Amount"
      expr: SUM(tax_liability_amount)
    - name: "Average Tax Liability Amount"
      expr: AVG(tax_liability_amount)
    - name: "Total Total Credits Amount"
      expr: SUM(total_credits_amount)
    - name: "Average Total Credits Amount"
      expr: AVG(total_credits_amount)
    - name: "Total Total Payments Amount"
      expr: SUM(total_payments_amount)
    - name: "Average Total Payments Amount"
      expr: AVG(total_payments_amount)
    - name: "Total Net Tax Due Amount"
      expr: SUM(net_tax_due_amount)
    - name: "Average Net Tax Due Amount"
      expr: AVG(net_tax_due_amount)
    - name: "Total Overpayment Amount"
      expr: SUM(overpayment_amount)
    - name: "Average Overpayment Amount"
      expr: AVG(overpayment_amount)
    - name: "Total Refund Amount"
      expr: SUM(refund_amount)
    - name: "Average Refund Amount"
      expr: AVG(refund_amount)
    - name: "Total Credit Forward Amount"
      expr: SUM(credit_forward_amount)
    - name: "Average Credit Forward Amount"
      expr: AVG(credit_forward_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_trial_balance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Trial Balance business metrics"
  source: "`cmoore_customer_demos`.`finance`.`trial_balance`"
  dimensions:
    - name: "Ledger Name"
      expr: ledger_name
    - name: "Ledger Type"
      expr: ledger_type
    - name: "Legal Entity"
      expr: legal_entity
    - name: "Legal Entity Code"
      expr: legal_entity_code
    - name: "Chart Of Accounts Version"
      expr: chart_of_accounts_version
    - name: "Account Number"
      expr: account_number
    - name: "Cost Center"
      expr: cost_center
    - name: "Department"
      expr: department
    - name: "Line Of Business"
      expr: line_of_business
    - name: "Product Line"
      expr: product_line
    - name: "Geography"
      expr: geography
    - name: "Balance Type"
      expr: balance_type
    - name: "Currency Code"
      expr: currency_code
    - name: "Functional Currency Code"
      expr: functional_currency_code
    - name: "Reporting Currency Code"
      expr: reporting_currency_code
    - name: "Exchange Rate Type"
      expr: exchange_rate_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Trial Balance"
      expr: COUNT(DISTINCT trial_balance_id)
    - name: "Total Beginning Balance Debit"
      expr: SUM(beginning_balance_debit)
    - name: "Average Beginning Balance Debit"
      expr: AVG(beginning_balance_debit)
    - name: "Total Beginning Balance Credit"
      expr: SUM(beginning_balance_credit)
    - name: "Average Beginning Balance Credit"
      expr: AVG(beginning_balance_credit)
    - name: "Total Period Debit Activity"
      expr: SUM(period_debit_activity)
    - name: "Average Period Debit Activity"
      expr: AVG(period_debit_activity)
    - name: "Total Period Credit Activity"
      expr: SUM(period_credit_activity)
    - name: "Average Period Credit Activity"
      expr: AVG(period_credit_activity)
    - name: "Total Ending Balance Debit"
      expr: SUM(ending_balance_debit)
    - name: "Average Ending Balance Debit"
      expr: AVG(ending_balance_debit)
    - name: "Total Ending Balance Credit"
      expr: SUM(ending_balance_credit)
    - name: "Average Ending Balance Credit"
      expr: AVG(ending_balance_credit)
    - name: "Total Net Balance"
      expr: SUM(net_balance)
    - name: "Average Net Balance"
      expr: AVG(net_balance)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Balance In Reporting Currency"
      expr: SUM(balance_in_reporting_currency)
    - name: "Average Balance In Reporting Currency"
      expr: AVG(balance_in_reporting_currency)
    - name: "Total Adjustment Amount"
      expr: SUM(adjustment_amount)
    - name: "Average Adjustment Amount"
      expr: AVG(adjustment_amount)
    - name: "Total Balance Variance"
      expr: SUM(balance_variance)
    - name: "Average Balance Variance"
      expr: AVG(balance_variance)
    - name: "Total Materiality Threshold"
      expr: SUM(materiality_threshold)
    - name: "Average Materiality Threshold"
      expr: AVG(materiality_threshold)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`finance_vendor_invoice`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Vendor Invoice business metrics"
  source: "`cmoore_customer_demos`.`finance`.`vendor_invoice`"
  dimensions:
    - name: "Vendor Name"
      expr: vendor_name
    - name: "Vendor Email"
      expr: vendor_email
    - name: "Vendor Phone"
      expr: vendor_phone
    - name: "Vendor Address"
      expr: vendor_address
    - name: "Invoice Number"
      expr: invoice_number
    - name: "Invoice Date"
      expr: invoice_date
    - name: "Due Date"
      expr: due_date
    - name: "Posting Date"
      expr: posting_date
    - name: "Payment Date"
      expr: payment_date
    - name: "Currency Code"
      expr: currency_code
    - name: "Invoice Type"
      expr: invoice_type
    - name: "Payment Terms"
      expr: payment_terms
    - name: "Payment Method"
      expr: payment_method
    - name: "Payment Reference"
      expr: payment_reference
    - name: "Approval Status"
      expr: approval_status
    - name: "Approved By"
      expr: approved_by
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Vendor Invoice"
      expr: COUNT(DISTINCT vendor_invoice_id)
    - name: "Total Exchange Rate"
      expr: SUM(exchange_rate)
    - name: "Average Exchange Rate"
      expr: AVG(exchange_rate)
    - name: "Total Invoice Amount"
      expr: SUM(invoice_amount)
    - name: "Average Invoice Amount"
      expr: AVG(invoice_amount)
    - name: "Total Tax Amount"
      expr: SUM(tax_amount)
    - name: "Average Tax Amount"
      expr: AVG(tax_amount)
    - name: "Total Total Amount"
      expr: SUM(total_amount)
    - name: "Average Total Amount"
      expr: AVG(total_amount)
    - name: "Total Discount Amount"
      expr: SUM(discount_amount)
    - name: "Average Discount Amount"
      expr: AVG(discount_amount)
    - name: "Total Discount Percent"
      expr: SUM(discount_percent)
    - name: "Average Discount Percent"
      expr: AVG(discount_percent)
    - name: "Total Late Fee Amount"
      expr: SUM(late_fee_amount)
    - name: "Average Late Fee Amount"
      expr: AVG(late_fee_amount)
    - name: "Total Tax Rate"
      expr: SUM(tax_rate)
    - name: "Average Tax Rate"
      expr: AVG(tax_rate)
    - name: "Total Line Item Quantity"
      expr: SUM(line_item_quantity)
    - name: "Average Line Item Quantity"
      expr: AVG(line_item_quantity)
    - name: "Total Line Item Unit Price"
      expr: SUM(line_item_unit_price)
    - name: "Average Line Item Unit Price"
      expr: AVG(line_item_unit_price)
    - name: "Total Line Item Total"
      expr: SUM(line_item_total)
    - name: "Average Line Item Total"
      expr: AVG(line_item_total)
    - name: "Total Line Item Tax Amount"
      expr: SUM(line_item_tax_amount)
    - name: "Average Line Item Tax Amount"
      expr: AVG(line_item_tax_amount)
$$;