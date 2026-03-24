-- Metric views for domain: claim | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`claim_claim_summary`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "High‑level claim financial and performance summary"
  source: "`cmoore_customer_demos`.`claim`.`claim`"
  dimensions:
    - name: "claim_type"
      expr: claim_type
      comment: "Type of claim (professional, institutional, pharmacy, etc.)"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line (Commercial, Medicare Advantage, Medicaid, etc.)"
    - name: "product_type"
      expr: product_type
      comment: "Insurance product type (HMO, PPO, EPO, etc.)"
    - name: "claim_status"
      expr: status
      comment: "Current processing status of the claim"
    - name: "claim_submission_method"
      expr: submission_method
      comment: "Method used to submit the claim (EDI, paper, portal)"
    - name: "provider_id"
      expr: provider_id
      comment: "Identifier of the rendering provider"
    - name: "member_profile_id"
      expr: member_profile_id
      comment: "Identifier of the member who received the service"
    - name: "fiscal_year"
      expr: YEAR(received_date)
      comment: "Fiscal year of claim receipt"
  measures:
    - name: "total_claims"
      expr: COUNT(1)
      comment: "Number of claim records"
    - name: "total_billed_amount"
      expr: SUM(CAST(total_billed_amount AS DOUBLE))
      comment: "Sum of billed amounts for all claims"
    - name: "total_allowed_amount"
      expr: SUM(CAST(total_allowed_amount AS DOUBLE))
      comment: "Sum of allowed amounts for all claims"
    - name: "total_paid_amount"
      expr: SUM(CAST(total_paid_amount AS DOUBLE))
      comment: "Sum of paid amounts for all claims"
    - name: "total_adjustment_amount"
      expr: SUM(CAST(adjustment_amount AS DOUBLE))
      comment: "Sum of adjustment amounts applied to claims"
    - name: "avg_paid_per_claim"
      expr: AVG(CAST(total_paid_amount AS DOUBLE))
      comment: "Average paid amount per claim"
    - name: "avg_turnaround_days"
      expr: AVG(DATEDIFF(paid_date, received_date))
      comment: "Average number of days from claim receipt to payment"
    - name: "distinct_providers"
      expr: COUNT(DISTINCT provider_id)
      comment: "Count of unique providers across claims"
    - name: "distinct_members"
      expr: COUNT(DISTINCT member_profile_id)
      comment: "Count of unique members across claims"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`claim_adjustment_performance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial impact and efficiency of claim adjustments"
  source: "`cmoore_customer_demos`.`claim`.`adjustment`"
  dimensions:
    - name: "adjustment_type_code"
      expr: type_code
      comment: "Classification code of the adjustment (financial, administrative, etc.)"
    - name: "adjustment_reason_code"
      expr: reason_code
      comment: "Standard CARC reason code for the adjustment"
    - name: "adjustment_status"
      expr: status
      comment: "Current status of the adjustment"
    - name: "adjustment_priority"
      expr: priority
      comment: "Priority level assigned to the adjustment"
    - name: "effective_year"
      expr: YEAR(effective_date)
      comment: "Fiscal year when the adjustment became effective"
  measures:
    - name: "total_adjustments"
      expr: COUNT(1)
      comment: "Number of adjustment records"
    - name: "total_adjusted_paid_amount"
      expr: SUM(CAST(adjusted_paid_amount AS DOUBLE))
      comment: "Sum of adjusted paid amounts"
    - name: "total_adjusted_allowed_amount"
      expr: SUM(CAST(adjusted_allowed_amount AS DOUBLE))
      comment: "Sum of adjusted allowed amounts"
    - name: "total_patient_responsibility_amount"
      expr: SUM(CAST(patient_responsibility_amount AS DOUBLE))
      comment: "Sum of patient responsibility amounts from adjustments"
    - name: "avg_adjusted_paid_amount"
      expr: AVG(CAST(adjusted_paid_amount AS DOUBLE))
      comment: "Average adjusted paid amount per adjustment"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`claim_line_utilization`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Utilization and financial performance at the service‑line level"
  source: "`cmoore_customer_demos`.`claim`.`line`"
  dimensions:
    - name: "claim_id"
      expr: claim_id
      comment: "Parent claim identifier"
    - name: "procedure_code"
      expr: procedure_code
      comment: "Procedure code (CPT/HCPCS) for the line"
    - name: "procedure_code_type"
      expr: procedure_code_type
      comment: "Coding system of the procedure code"
    - name: "place_of_service_code"
      expr: place_of_service_code
      comment: "Two‑digit place of service code"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line for the claim"
    - name: "product_type"
      expr: product_type
      comment: "Product type (HMO, PPO, etc.)"
    - name: "service_month"
      expr: DATE_TRUNC('month', service_from_date)
      comment: "Month of service for the line"
    - name: "network_status"
      expr: network_status
      comment: "In‑network / out‑of‑network status"
  measures:
    - name: "total_lines"
      expr: COUNT(1)
      comment: "Number of claim line records"
    - name: "total_line_billed_amount"
      expr: SUM(CAST(billed_amount AS DOUBLE))
      comment: "Sum of billed amounts for all lines"
    - name: "total_line_allowed_amount"
      expr: SUM(CAST(allowed_amount AS DOUBLE))
      comment: "Sum of allowed amounts for all lines"
    - name: "total_line_paid_amount"
      expr: SUM(CAST(paid_amount AS DOUBLE))
      comment: "Sum of paid amounts for all lines"
    - name: "avg_units_per_line"
      expr: AVG(CAST(service_units AS DOUBLE))
      comment: "Average service units per line"
    - name: "avg_paid_per_line"
      expr: AVG(CAST(paid_amount AS DOUBLE))
      comment: "Average paid amount per line"
    - name: "distinct_procedures"
      expr: COUNT(DISTINCT procedure_code)
      comment: "Count of unique procedure codes used in lines"
    - name: "distinct_line_providers"
      expr: COUNT(DISTINCT rendering_provider_npi)
      comment: "Count of unique rendering providers across lines"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`claim_payment_allocation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial flow from payer to providers at the allocation level"
  source: "`cmoore_customer_demos`.`claim`.`payment_allocation`"
  dimensions:
    - name: "claim_id"
      expr: claim_id
      comment: "Parent claim identifier"
    - name: "provider_id"
      expr: provider_id
      comment: "Provider receiving the allocation"
    - name: "allocation_type"
      expr: allocation_type
      comment: "Type of allocation (standard, reversal, recoupment, etc.)"
    - name: "allocation_status"
      expr: allocation_status
      comment: "Current processing status of the allocation"
    - name: "allocation_year"
      expr: YEAR(allocation_date)
      comment: "Fiscal year of the allocation"
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line for the claim"
    - name: "product_type"
      expr: product_type
      comment: "Product type (HMO, PPO, etc.)"
  measures:
    - name: "total_allocations"
      expr: COUNT(1)
      comment: "Number of payment allocation records"
    - name: "total_allocated_amount"
      expr: SUM(CAST(allocated_amount AS DOUBLE))
      comment: "Sum of amounts allocated to claim lines"
    - name: "total_paid_amount"
      expr: SUM(CAST(paid_amount AS DOUBLE))
      comment: "Sum of amounts actually paid to providers"
    - name: "avg_allocation_amount"
      expr: AVG(CAST(allocated_amount AS DOUBLE))
      comment: "Average allocation amount per record"
    - name: "distinct_claims"
      expr: COUNT(DISTINCT claim_id)
      comment: "Count of unique claims represented in allocations"
$$;