-- Metric views for domain: marketing | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:03:45

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`marketing_asset`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Key performance indicators for marketing assets"
  source: "`cmoore_customer_demos`.`marketing`.`asset`"
  dimensions:
    - name: "asset_type"
      expr: type
      comment: "Media format of the asset (e.g., image, video)"
  measures:
    - name: "asset_record_count"
      expr: COUNT(1)
      comment: "Number of asset records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`marketing_asset_cost`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Cost efficiency of assets"
  source: "`cmoore_customer_demos`.`marketing`.`asset`"
  dimensions:
    - name: "is_active"
      expr: is_active
      comment: "Indicates whether the asset is currently active"
  measures:
    - name: "asset_record_count"
      expr: COUNT(1)
      comment: "Number of asset records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`marketing_campaign`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Overall campaign financial and response performance"
  source: "`cmoore_customer_demos`.`marketing`.`campaign`"
  dimensions:
    - name: "line_of_business"
      expr: line_of_business
      comment: "Business line the campaign belongs to (e.g., Medicare, Commercial)"
  measures:
    - name: "campaign_record_count"
      expr: COUNT(1)
      comment: "Number of campaigns"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`marketing_campaign_budget`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Budget allocation and spend tracking at the campaign level"
  source: "`cmoore_customer_demos`.`marketing`.`campaign_budget`"
  dimensions:
    - name: "budget_year"
      expr: budget_year
      comment: "Fiscal year of the budget"
  measures:
    - name: "campaign_budget_record_count"
      expr: COUNT(1)
      comment: "Number of campaign budget records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`marketing_campaign_line_item`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Efficiency and financial performance of individual campaign line items"
  source: "`cmoore_customer_demos`.`marketing`.`campaign_line_item`"
  dimensions:
    - name: "line_item_type"
      expr: line_item_type
      comment: "Category of marketing activity (e.g., email, digital ad)"
  measures:
    - name: "line_item_record_count"
      expr: COUNT(1)
      comment: "Number of campaign line‑item records"
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`marketing_offer`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Financial and uptake metrics for promotional offers"
  source: "`cmoore_customer_demos`.`marketing`.`offer`"
  dimensions:
    - name: "product_line"
      expr: product_line
      comment: "Line of business the offer applies to (e.g., Medicare)"
  measures:
    - name: "offer_record_count"
      expr: COUNT(1)
      comment: "Number of offers"
$$;