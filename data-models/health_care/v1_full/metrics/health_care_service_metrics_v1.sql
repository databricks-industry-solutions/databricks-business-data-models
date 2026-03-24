-- Metric views for domain: service | Business:  health Care | Version: 1 | Generated on: 2026-03-20 04:08:31

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_advocacy`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Advocacy business metrics"
  source: "`cmoore_customer_demos`.`service`.`advocacy`"
  dimensions:
    - name: "Request Number"
      expr: request_number
    - name: "Request Type"
      expr: request_type
    - name: "Request Subtype"
      expr: request_subtype
    - name: "Lob"
      expr: lob
    - name: "Product Code"
      expr: product_code
    - name: "Product Name"
      expr: product_name
    - name: "Request Date"
      expr: request_date
    - name: "Request Timestamp"
      expr: request_timestamp
    - name: "Assigned Date"
      expr: assigned_date
    - name: "Assigned Timestamp"
      expr: assigned_timestamp
    - name: "First Contact Date"
      expr: first_contact_date
    - name: "First Contact Timestamp"
      expr: first_contact_timestamp
    - name: "Target Resolution Date"
      expr: target_resolution_date
    - name: "Actual Resolution Date"
      expr: actual_resolution_date
    - name: "Actual Resolution Timestamp"
      expr: actual_resolution_timestamp
    - name: "Closed Date"
      expr: closed_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Advocacy"
      expr: COUNT(DISTINCT advocacy_id)
    - name: "Total Turnaround Time Hours"
      expr: SUM(turnaround_time_hours)
    - name: "Average Turnaround Time Hours"
      expr: AVG(turnaround_time_hours)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_agent`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Agent business metrics"
  source: "`cmoore_customer_demos`.`service`.`agent`"
  dimensions:
    - name: "First Name"
      expr: first_name
    - name: "Middle Name"
      expr: middle_name
    - name: "Last Name"
      expr: last_name
    - name: "Preferred Name"
      expr: preferred_name
    - name: "Email Address"
      expr: email_address
    - name: "Phone Number"
      expr: phone_number
    - name: "Role Code"
      expr: role_code
    - name: "Role Name"
      expr: role_name
    - name: "Job Title"
      expr: job_title
    - name: "Employment Status"
      expr: employment_status
    - name: "Employment Type"
      expr: employment_type
    - name: "Hire Date"
      expr: hire_date
    - name: "Termination Date"
      expr: termination_date
    - name: "Location Code"
      expr: location_code
    - name: "Location Name"
      expr: location_name
    - name: "Work Location Type"
      expr: work_location_type
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Agent"
      expr: COUNT(DISTINCT agent_id)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Nps Score"
      expr: SUM(nps_score)
    - name: "Average Nps Score"
      expr: AVG(nps_score)
    - name: "Total Csat Score"
      expr: SUM(csat_score)
    - name: "Average Csat Score"
      expr: AVG(csat_score)
    - name: "Total Fcr Rate"
      expr: SUM(fcr_rate)
    - name: "Average Fcr Rate"
      expr: AVG(fcr_rate)
    - name: "Total Adherence Percentage"
      expr: SUM(adherence_percentage)
    - name: "Average Adherence Percentage"
      expr: AVG(adherence_percentage)
    - name: "Total Utilization Percentage"
      expr: SUM(utilization_percentage)
    - name: "Average Utilization Percentage"
      expr: AVG(utilization_percentage)
    - name: "Total Approval Limit Amount"
      expr: SUM(approval_limit_amount)
    - name: "Average Approval Limit Amount"
      expr: AVG(approval_limit_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_article_program_applicability`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Article Program Applicability business metrics"
  source: "`cmoore_customer_demos`.`service`.`article_program_applicability`"
  dimensions:
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Version"
      expr: version
    - name: "Approval Status"
      expr: approval_status
    - name: "Approved By"
      expr: approved_by
    - name: "Approval Date"
      expr: approval_date
    - name: "Created Date"
      expr: created_date
    - name: "Last Updated Date"
      expr: last_updated_date
    - name: "Effective Date Month"
      expr: DATE_TRUNC('MONTH', effective_date)
    - name: "Expiration Date Month"
      expr: DATE_TRUNC('MONTH', expiration_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Article Program Applicability"
      expr: COUNT(DISTINCT article_program_applicability_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_case_escalation`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Case Escalation business metrics"
  source: "`cmoore_customer_demos`.`service`.`case_escalation`"
  dimensions:
    - name: "Case Number"
      expr: case_number
    - name: "Escalation Level"
      expr: escalation_level
    - name: "Escalation Tier"
      expr: escalation_tier
    - name: "Escalation Type"
      expr: escalation_type
    - name: "Escalation Reason Code"
      expr: escalation_reason_code
    - name: "Escalation Reason Description"
      expr: escalation_reason_description
    - name: "Escalated From User Name"
      expr: escalated_from_user_name
    - name: "Escalated From Team"
      expr: escalated_from_team
    - name: "Escalated To User Name"
      expr: escalated_to_user_name
    - name: "Escalated To Team"
      expr: escalated_to_team
    - name: "Escalated To Queue"
      expr: escalated_to_queue
    - name: "Member Name"
      expr: member_name
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Provider Name"
      expr: provider_name
    - name: "Claim Number"
      expr: claim_number
    - name: "Authorization Number"
      expr: authorization_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Case Escalation"
      expr: COUNT(DISTINCT case_escalation_id)
    - name: "Total Resolution Time Hours"
      expr: SUM(resolution_time_hours)
    - name: "Average Resolution Time Hours"
      expr: AVG(resolution_time_hours)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_category`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Category business metrics"
  source: "`cmoore_customer_demos`.`service`.`category`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Hierarchy Level"
      expr: hierarchy_level
    - name: "Hierarchy Path"
      expr: hierarchy_path
    - name: "Type"
      expr: type
    - name: "Status"
      expr: status
    - name: "Priority Level"
      expr: priority_level
    - name: "Severity Level"
      expr: severity_level
    - name: "Routing Queue"
      expr: routing_queue
    - name: "Escalation Queue"
      expr: escalation_queue
    - name: "Requires Authorization"
      expr: requires_authorization
    - name: "Requires Clinical Review"
      expr: requires_clinical_review
    - name: "Requires Supervisor Approval"
      expr: requires_supervisor_approval
    - name: "Is Grievance Eligible"
      expr: is_grievance_eligible
    - name: "Is Appeal Eligible"
      expr: is_appeal_eligible
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Category"
      expr: COUNT(DISTINCT category_id)
    - name: "Total Sla Response Hours"
      expr: SUM(sla_response_hours)
    - name: "Average Sla Response Hours"
      expr: AVG(sla_response_hours)
    - name: "Total Sla Resolution Hours"
      expr: SUM(sla_resolution_hours)
    - name: "Average Sla Resolution Hours"
      expr: AVG(sla_resolution_hours)
    - name: "Total Average Handle Time Minutes"
      expr: SUM(average_handle_time_minutes)
    - name: "Average Average Handle Time Minutes"
      expr: AVG(average_handle_time_minutes)
    - name: "Total First Call Resolution Target Pct"
      expr: SUM(first_call_resolution_target_pct)
    - name: "Average First Call Resolution Target Pct"
      expr: AVG(first_call_resolution_target_pct)
    - name: "Total Member Satisfaction Target Score"
      expr: SUM(member_satisfaction_target_score)
    - name: "Average Member Satisfaction Target Score"
      expr: AVG(member_satisfaction_target_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_certification`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Certification business metrics"
  source: "`cmoore_customer_demos`.`service`.`certification`"
  dimensions:
    - name: "Date"
      expr: date
    - name: "Training Completion Date"
      expr: training_completion_date
    - name: "Specialization Level"
      expr: specialization_level
    - name: "Active Status"
      expr: active_status
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Last Renewal Date"
      expr: last_renewal_date
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Updated Timestamp"
      expr: updated_timestamp
    - name: "Date Month"
      expr: DATE_TRUNC('MONTH', date)
    - name: "Training Completion Date Month"
      expr: DATE_TRUNC('MONTH', training_completion_date)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Certification"
      expr: COUNT(DISTINCT certification_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_communication`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Communication business metrics"
  source: "`cmoore_customer_demos`.`service`.`communication`"
  dimensions:
    - name: "Subject Line"
      expr: subject_line
    - name: "Message Body"
      expr: message_body
    - name: "Recipient Email"
      expr: recipient_email
    - name: "Recipient Phone"
      expr: recipient_phone
    - name: "Recipient Device Token"
      expr: recipient_device_token
    - name: "Recipient Mailing Address"
      expr: recipient_mailing_address
    - name: "Type"
      expr: type
    - name: "Priority Level"
      expr: priority_level
    - name: "Language Code"
      expr: language_code
    - name: "Sent Timestamp"
      expr: sent_timestamp
    - name: "Scheduled Timestamp"
      expr: scheduled_timestamp
    - name: "Delivery Status"
      expr: delivery_status
    - name: "Delivery Timestamp"
      expr: delivery_timestamp
    - name: "Opened Timestamp"
      expr: opened_timestamp
    - name: "Clicked Timestamp"
      expr: clicked_timestamp
    - name: "Bounce Reason"
      expr: bounce_reason
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Communication"
      expr: COUNT(DISTINCT communication_id)
    - name: "Total Cost Amount"
      expr: SUM(cost_amount)
    - name: "Average Cost Amount"
      expr: AVG(cost_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_communication_template`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Communication Template business metrics"
  source: "`cmoore_customer_demos`.`service`.`communication_template`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Channel"
      expr: channel
    - name: "Language"
      expr: language
    - name: "Template Type"
      expr: template_type
    - name: "Audience"
      expr: audience
    - name: "Priority"
      expr: priority
    - name: "Status"
      expr: status
    - name: "Version Number"
      expr: version_number
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
    - name: "Last Modified Timestamp"
      expr: last_modified_timestamp
    - name: "Approval Status"
      expr: approval_status
    - name: "Compliance Flag"
      expr: compliance_flag
    - name: "Max Send Attempts"
      expr: max_send_attempts
    - name: "Placeholder Count"
      expr: placeholder_count
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Communication Template"
      expr: COUNT(DISTINCT communication_template_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_communication_thread`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Communication Thread business metrics"
  source: "`cmoore_customer_demos`.`service`.`communication_thread`"
  dimensions:
    - name: "Channel"
      expr: channel
    - name: "Direction"
      expr: direction
    - name: "Status"
      expr: status
    - name: "Priority"
      expr: priority
    - name: "Category"
      expr: category
    - name: "Subcategory"
      expr: subcategory
    - name: "Subject"
      expr: subject
    - name: "Initial Message Timestamp"
      expr: initial_message_timestamp
    - name: "Last Message Timestamp"
      expr: last_message_timestamp
    - name: "First Response Timestamp"
      expr: first_response_timestamp
    - name: "Closed Timestamp"
      expr: closed_timestamp
    - name: "Interaction Count"
      expr: interaction_count
    - name: "Escalation Flag"
      expr: escalation_flag
    - name: "Satisfaction Score"
      expr: satisfaction_score
    - name: "Nps Score"
      expr: nps_score
    - name: "Language"
      expr: language
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Communication Thread"
      expr: COUNT(DISTINCT communication_thread_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_contact_center`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Contact Center business metrics"
  source: "`cmoore_customer_demos`.`service`.`contact_center`"
  dimensions:
    - name: "Member Name"
      expr: member_name
    - name: "Member Phone"
      expr: member_phone
    - name: "Member Email"
      expr: member_email
    - name: "Channel"
      expr: channel
    - name: "Direction"
      expr: direction
    - name: "Interaction Timestamp"
      expr: interaction_timestamp
    - name: "End Timestamp"
      expr: end_timestamp
    - name: "Duration Seconds"
      expr: duration_seconds
    - name: "Agent Name"
      expr: agent_name
    - name: "Issue Category"
      expr: issue_category
    - name: "Issue Subcategory"
      expr: issue_subcategory
    - name: "Resolution Status"
      expr: resolution_status
    - name: "First Contact Resolution Flag"
      expr: first_contact_resolution_flag
    - name: "Satisfaction Rating"
      expr: satisfaction_rating
    - name: "Nps Score"
      expr: nps_score
    - name: "Call Disposition"
      expr: call_disposition
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Contact Center"
      expr: COUNT(DISTINCT contact_center_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_department`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Department business metrics"
  source: "`cmoore_customer_demos`.`service`.`department`"
  dimensions:
    - name: "Department Name"
      expr: department_name
    - name: "Department Code"
      expr: department_code
    - name: "Department Type"
      expr: department_type
    - name: "Status"
      expr: status
    - name: "Manager Name"
      expr: manager_name
    - name: "Contact Email"
      expr: contact_email
    - name: "Contact Phone"
      expr: contact_phone
    - name: "Address Line1"
      expr: address_line1
    - name: "Address Line2"
      expr: address_line2
    - name: "City"
      expr: city
    - name: "State Province"
      expr: state_province
    - name: "Country Code"
      expr: country_code
    - name: "Zip Postal Code"
      expr: zip_postal_code
    - name: "Cost Center Code"
      expr: cost_center_code
    - name: "Effective Start Date"
      expr: effective_start_date
    - name: "Effective End Date"
      expr: effective_end_date
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Department"
      expr: COUNT(DISTINCT department_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_feedback`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Feedback business metrics"
  source: "`cmoore_customer_demos`.`service`.`feedback`"
  dimensions:
    - name: "Submission Timestamp"
      expr: submission_timestamp
    - name: "Submission Date"
      expr: submission_date
    - name: "Source System"
      expr: source_system
    - name: "Submitter Type"
      expr: submitter_type
    - name: "Policy Number"
      expr: policy_number
    - name: "Lob"
      expr: lob
    - name: "Text"
      expr: text
    - name: "Subcategory"
      expr: subcategory
    - name: "Sentiment"
      expr: sentiment
    - name: "Assigned To Team"
      expr: assigned_to_team
    - name: "Acknowledgment Timestamp"
      expr: acknowledgment_timestamp
    - name: "Resolution Timestamp"
      expr: resolution_timestamp
    - name: "Resolution Notes"
      expr: resolution_notes
    - name: "Action Taken"
      expr: action_taken
    - name: "Root Cause"
      expr: root_cause
    - name: "Nps Score"
      expr: nps_score
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Feedback"
      expr: COUNT(DISTINCT feedback_id)
    - name: "Total Sentiment Score"
      expr: SUM(sentiment_score)
    - name: "Average Sentiment Score"
      expr: AVG(sentiment_score)
    - name: "Total Response Time Hours"
      expr: SUM(response_time_hours)
    - name: "Average Response Time Hours"
      expr: AVG(response_time_hours)
    - name: "Total Resolution Time Hours"
      expr: SUM(resolution_time_hours)
    - name: "Average Resolution Time Hours"
      expr: AVG(resolution_time_hours)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_grievance`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Grievance business metrics"
  source: "`cmoore_customer_demos`.`service`.`grievance`"
  dimensions:
    - name: "Grievance Type"
      expr: grievance_type
    - name: "Category"
      expr: category
    - name: "Subcategory"
      expr: subcategory
    - name: "Priority"
      expr: priority
    - name: "Severity"
      expr: severity
    - name: "Source Channel"
      expr: source_channel
    - name: "Status"
      expr: status
    - name: "Submission Date"
      expr: submission_date
    - name: "Escalation Flag"
      expr: escalation_flag
    - name: "Escalation Date"
      expr: escalation_date
    - name: "Resolution Date"
      expr: resolution_date
    - name: "Resolution Outcome"
      expr: resolution_outcome
    - name: "Claim Number"
      expr: claim_number
    - name: "Policy Number"
      expr: policy_number
    - name: "Member Name"
      expr: member_name
    - name: "Member Dob"
      expr: member_dob
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Grievance"
      expr: COUNT(DISTINCT grievance_id)
    - name: "Total Resolution Time Hours"
      expr: SUM(resolution_time_hours)
    - name: "Average Resolution Time Hours"
      expr: AVG(resolution_time_hours)
    - name: "Total Financial Impact Amount"
      expr: SUM(financial_impact_amount)
    - name: "Average Financial Impact Amount"
      expr: AVG(financial_impact_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_interaction`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Interaction business metrics"
  source: "`cmoore_customer_demos`.`service`.`interaction`"
  dimensions:
    - name: "Contact Type"
      expr: contact_type
    - name: "Direction"
      expr: direction
    - name: "Start Timestamp"
      expr: start_timestamp
    - name: "End Timestamp"
      expr: end_timestamp
    - name: "Duration Seconds"
      expr: duration_seconds
    - name: "Wait Time Seconds"
      expr: wait_time_seconds
    - name: "Hold Time Seconds"
      expr: hold_time_seconds
    - name: "Agent Name"
      expr: agent_name
    - name: "Team Name"
      expr: team_name
    - name: "Queue Name"
      expr: queue_name
    - name: "Contact Reason Subcategory"
      expr: contact_reason_subcategory
    - name: "Contact Reason Code"
      expr: contact_reason_code
    - name: "Inquiry Type"
      expr: inquiry_type
    - name: "Disposition Code"
      expr: disposition_code
    - name: "Disposition Description"
      expr: disposition_description
    - name: "Resolution Status"
      expr: resolution_status
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Interaction"
      expr: COUNT(DISTINCT interaction_id)
    - name: "Total Sentiment Score"
      expr: SUM(sentiment_score)
    - name: "Average Sentiment Score"
      expr: AVG(sentiment_score)
    - name: "Total Quality Score"
      expr: SUM(quality_score)
    - name: "Average Quality Score"
      expr: AVG(quality_score)
    - name: "Total Cost Amount"
      expr: SUM(cost_amount)
    - name: "Average Cost Amount"
      expr: AVG(cost_amount)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_knowledge_article`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Knowledge Article business metrics"
  source: "`cmoore_customer_demos`.`service`.`knowledge_article`"
  dimensions:
    - name: "Title"
      expr: title
    - name: "Summary"
      expr: summary
    - name: "Content"
      expr: content
    - name: "Status"
      expr: status
    - name: "Language"
      expr: language
    - name: "Version"
      expr: version
    - name: "Created Timestamp"
      expr: created_timestamp
    - name: "Last Updated Timestamp"
      expr: last_updated_timestamp
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Author Name"
      expr: author_name
    - name: "Author Role"
      expr: author_role
    - name: "Audience"
      expr: audience
    - name: "Channel"
      expr: channel
    - name: "View Count"
      expr: view_count
    - name: "Compliance Classification"
      expr: compliance_classification
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Knowledge Article"
      expr: COUNT(DISTINCT knowledge_article_id)
    - name: "Total Rating"
      expr: SUM(rating)
    - name: "Average Rating"
      expr: AVG(rating)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_knowledge_base`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Knowledge Base business metrics"
  source: "`cmoore_customer_demos`.`service`.`knowledge_base`"
  dimensions:
    - name: "Article Number"
      expr: article_number
    - name: "Title"
      expr: title
    - name: "Content"
      expr: content
    - name: "Summary"
      expr: summary
    - name: "Category"
      expr: category
    - name: "Subcategory"
      expr: subcategory
    - name: "Article Type"
      expr: article_type
    - name: "Keywords"
      expr: keywords
    - name: "Version Number"
      expr: version_number
    - name: "Status"
      expr: status
    - name: "Effective Date"
      expr: effective_date
    - name: "Expiration Date"
      expr: expiration_date
    - name: "Published Date"
      expr: published_date
    - name: "Last Reviewed Date"
      expr: last_reviewed_date
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Author Name"
      expr: author_name
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Knowledge Base"
      expr: COUNT(DISTINCT knowledge_base_id)
    - name: "Total Average Rating"
      expr: SUM(average_rating)
    - name: "Average Average Rating"
      expr: AVG(average_rating)
    - name: "Total Search Rank Score"
      expr: SUM(search_rank_score)
    - name: "Average Search Rank Score"
      expr: AVG(search_rank_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_knowledge_usage`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Knowledge Usage business metrics"
  source: "`cmoore_customer_demos`.`service`.`knowledge_usage`"
  dimensions:
    - name: "Article Title"
      expr: article_title
    - name: "Article Category"
      expr: article_category
    - name: "Article Subcategory"
      expr: article_subcategory
    - name: "User Type"
      expr: user_type
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Device Type"
      expr: device_type
    - name: "Usage Type"
      expr: usage_type
    - name: "Search Query"
      expr: search_query
    - name: "Search Result Position"
      expr: search_result_position
    - name: "Search Result Count"
      expr: search_result_count
    - name: "Access Timestamp"
      expr: access_timestamp
    - name: "Access Date"
      expr: access_date
    - name: "Time Spent Seconds"
      expr: time_spent_seconds
    - name: "Article Version"
      expr: article_version
    - name: "Article Language"
      expr: article_language
    - name: "Helpful Flag"
      expr: helpful_flag
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Knowledge Usage"
      expr: COUNT(DISTINCT knowledge_usage_id)
    - name: "Total Article Average Rating"
      expr: SUM(article_average_rating)
    - name: "Average Article Average Rating"
      expr: AVG(article_average_rating)
    - name: "Total Recommendation Score"
      expr: SUM(recommendation_score)
    - name: "Average Recommendation Score"
      expr: AVG(recommendation_score)
    - name: "Total Article Readability Score"
      expr: SUM(article_readability_score)
    - name: "Average Article Readability Score"
      expr: AVG(article_readability_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_metric`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Metric business metrics"
  source: "`cmoore_customer_demos`.`service`.`metric`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Category"
      expr: category
    - name: "Description"
      expr: description
    - name: "Unit Of Measure"
      expr: unit_of_measure
    - name: "Measurement Date"
      expr: measurement_date
    - name: "Measurement Timestamp"
      expr: measurement_timestamp
    - name: "Reporting Period Start"
      expr: reporting_period_start
    - name: "Reporting Period End"
      expr: reporting_period_end
    - name: "Interaction Type"
      expr: interaction_type
    - name: "Created Date"
      expr: created_date
    - name: "Modified Date"
      expr: modified_date
    - name: "Source System"
      expr: source_system
    - name: "Data Quality Flag"
      expr: data_quality_flag
    - name: "Priority Level"
      expr: priority_level
    - name: "Is Compliance Required"
      expr: is_compliance_required
    - name: "Regulatory Reporting Code"
      expr: regulatory_reporting_code
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Metric"
      expr: COUNT(DISTINCT metric_id)
    - name: "Total Target Value"
      expr: SUM(target_value)
    - name: "Average Target Value"
      expr: AVG(target_value)
    - name: "Total Actual Value"
      expr: SUM(actual_value)
    - name: "Average Actual Value"
      expr: AVG(actual_value)
    - name: "Total Sla Target Time"
      expr: SUM(sla_target_time)
    - name: "Average Sla Target Time"
      expr: AVG(sla_target_time)
    - name: "Total Sla Actual Time"
      expr: SUM(sla_actual_time)
    - name: "Average Sla Actual Time"
      expr: AVG(sla_actual_time)
    - name: "Total Threshold Minimum"
      expr: SUM(threshold_minimum)
    - name: "Average Threshold Minimum"
      expr: AVG(threshold_minimum)
    - name: "Total Threshold Maximum"
      expr: SUM(threshold_maximum)
    - name: "Average Threshold Maximum"
      expr: AVG(threshold_maximum)
    - name: "Total Benchmark Value"
      expr: SUM(benchmark_value)
    - name: "Average Benchmark Value"
      expr: AVG(benchmark_value)
    - name: "Total Weighting Factor"
      expr: SUM(weighting_factor)
    - name: "Average Weighting Factor"
      expr: AVG(weighting_factor)
    - name: "Total Alert Threshold Critical"
      expr: SUM(alert_threshold_critical)
    - name: "Average Alert Threshold Critical"
      expr: AVG(alert_threshold_critical)
    - name: "Total Alert Threshold Warning"
      expr: SUM(alert_threshold_warning)
    - name: "Average Alert Threshold Warning"
      expr: AVG(alert_threshold_warning)
    - name: "Total Historical Baseline"
      expr: SUM(historical_baseline)
    - name: "Average Historical Baseline"
      expr: AVG(historical_baseline)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_metric_event`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Metric Event business metrics"
  source: "`cmoore_customer_demos`.`service`.`metric_event`"
  dimensions:
    - name: "Contact Channel"
      expr: contact_channel
    - name: "Interaction Type"
      expr: interaction_type
    - name: "Metric Type"
      expr: metric_type
    - name: "Metric Value Boolean"
      expr: metric_value_boolean
    - name: "Metric Timestamp"
      expr: metric_timestamp
    - name: "Metric Date"
      expr: metric_date
    - name: "Agent Name"
      expr: agent_name
    - name: "Duration Seconds"
      expr: duration_seconds
    - name: "First Contact Resolution Flag"
      expr: first_contact_resolution_flag
    - name: "Satisfaction Score"
      expr: satisfaction_score
    - name: "Net Promoter Score"
      expr: net_promoter_score
    - name: "Sla Target Seconds"
      expr: sla_target_seconds
    - name: "Sla Actual Seconds"
      expr: sla_actual_seconds
    - name: "Sla Met Flag"
      expr: sla_met_flag
    - name: "Escalation Flag"
      expr: escalation_flag
    - name: "Hold Time Seconds"
      expr: hold_time_seconds
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Metric Event"
      expr: COUNT(DISTINCT metric_event_id)
    - name: "Total Metric Value Numeric"
      expr: SUM(metric_value_numeric)
    - name: "Average Metric Value Numeric"
      expr: AVG(metric_value_numeric)
    - name: "Total Sentiment Score"
      expr: SUM(sentiment_score)
    - name: "Average Sentiment Score"
      expr: AVG(sentiment_score)
    - name: "Total Metric Value"
      expr: SUM(metric_value)
    - name: "Average Metric Value"
      expr: AVG(metric_value)
    - name: "Total Target Value"
      expr: SUM(target_value)
    - name: "Average Target Value"
      expr: AVG(target_value)
    - name: "Total Variance From Target"
      expr: SUM(variance_from_target)
    - name: "Average Variance From Target"
      expr: AVG(variance_from_target)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_nps_score`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Nps Score business metrics"
  source: "`cmoore_customer_demos`.`service`.`nps_score`"
  dimensions:
    - name: "Provider Npi"
      expr: provider_npi
    - name: "Respondent Type"
      expr: respondent_type
    - name: "Survey Type"
      expr: survey_type
    - name: "Survey Date"
      expr: survey_date
    - name: "Response Date"
      expr: response_date
    - name: "Response Timestamp"
      expr: response_timestamp
    - name: "Nps Score"
      expr: nps_score
    - name: "Nps Category"
      expr: nps_category
    - name: "Promoter Flag"
      expr: promoter_flag
    - name: "Detractor Flag"
      expr: detractor_flag
    - name: "Detractor Reason Code"
      expr: detractor_reason_code
    - name: "Detractor Reason Description"
      expr: detractor_reason_description
    - name: "Feedback Comment"
      expr: feedback_comment
    - name: "Sentiment Category"
      expr: sentiment_category
    - name: "Touchpoint Type"
      expr: touchpoint_type
    - name: "Case Number"
      expr: case_number
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Nps Score"
      expr: COUNT(DISTINCT nps_score_id)
    - name: "Total Sentiment Score"
      expr: SUM(sentiment_score)
    - name: "Average Sentiment Score"
      expr: AVG(sentiment_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_policy_acknowledgment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Policy Acknowledgment business metrics"
  source: "`cmoore_customer_demos`.`service`.`policy_acknowledgment`"
  dimensions:
    - name: "Acknowledgment Date"
      expr: acknowledgment_date
    - name: "Acknowledgment Status"
      expr: acknowledgment_status
    - name: "Version Acknowledged"
      expr: version_acknowledged
    - name: "Next Review Date"
      expr: next_review_date
    - name: "Acknowledgment Method"
      expr: acknowledgment_method
    - name: "Ip Address"
      expr: ip_address
    - name: "Acknowledgment Notes"
      expr: acknowledgment_notes
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
    - name: "Distinct Policy Acknowledgment"
      expr: COUNT(DISTINCT policy_acknowledgment_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_priority`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Priority business metrics"
  source: "`cmoore_customer_demos`.`service`.`priority`"
  dimensions:
    - name: "Code"
      expr: code
    - name: "Name"
      expr: name
    - name: "Description"
      expr: description
    - name: "Severity Level"
      expr: severity_level
    - name: "Response Time Minutes"
      expr: response_time_minutes
    - name: "Resolution Time Hours"
      expr: resolution_time_hours
    - name: "Escalation Time Hours"
      expr: escalation_time_hours
    - name: "Auto Escalation Enabled"
      expr: auto_escalation_enabled
    - name: "Business Impact"
      expr: business_impact
    - name: "Member Impact"
      expr: member_impact
    - name: "Regulatory Risk"
      expr: regulatory_risk
    - name: "Applies To Grievances"
      expr: applies_to_grievances
    - name: "Applies To Appeals"
      expr: applies_to_appeals
    - name: "Applies To Inquiries"
      expr: applies_to_inquiries
    - name: "Applies To Complaints"
      expr: applies_to_complaints
    - name: "Requires Management Notification"
      expr: requires_management_notification
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Priority"
      expr: COUNT(DISTINCT priority_id)
    - name: "Total Financial Impact Threshold"
      expr: SUM(financial_impact_threshold)
    - name: "Average Financial Impact Threshold"
      expr: AVG(financial_impact_threshold)
    - name: "Total Sla Compliance Target Pct"
      expr: SUM(sla_compliance_target_pct)
    - name: "Average Sla Compliance Target Pct"
      expr: AVG(sla_compliance_target_pct)
    - name: "Total Fcr Target Pct"
      expr: SUM(fcr_target_pct)
    - name: "Average Fcr Target Pct"
      expr: AVG(fcr_target_pct)
    - name: "Total Nps Impact Weight"
      expr: SUM(nps_impact_weight)
    - name: "Average Nps Impact Weight"
      expr: AVG(nps_impact_weight)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_queue`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Queue business metrics"
  source: "`cmoore_customer_demos`.`service`.`queue`"
  dimensions:
    - name: "Name"
      expr: name
    - name: "Code"
      expr: code
    - name: "Description"
      expr: description
    - name: "Type"
      expr: type
    - name: "Channel"
      expr: channel
    - name: "Lob"
      expr: lob
    - name: "Priority"
      expr: priority
    - name: "Status"
      expr: status
    - name: "Routing Strategy"
      expr: routing_strategy
    - name: "Skill Group Required"
      expr: skill_group_required
    - name: "Primary Skill Group"
      expr: primary_skill_group
    - name: "Secondary Skill Groups"
      expr: secondary_skill_groups
    - name: "Service Level Target Seconds"
      expr: service_level_target_seconds
    - name: "Average Handle Time Target Seconds"
      expr: average_handle_time_target_seconds
    - name: "Maximum Wait Time Seconds"
      expr: maximum_wait_time_seconds
    - name: "Abandon Threshold Seconds"
      expr: abandon_threshold_seconds
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Queue"
      expr: COUNT(DISTINCT queue_id)
    - name: "Total Service Level Target Percentage"
      expr: SUM(service_level_target_percentage)
    - name: "Average Service Level Target Percentage"
      expr: AVG(service_level_target_percentage)
    - name: "Total Fcr Target Percentage"
      expr: SUM(fcr_target_percentage)
    - name: "Average Fcr Target Percentage"
      expr: AVG(fcr_target_percentage)
    - name: "Total Survey Sample Rate"
      expr: SUM(survey_sample_rate)
    - name: "Average Survey Sample Rate"
      expr: AVG(survey_sample_rate)
    - name: "Total Agent Occupancy Target Percentage"
      expr: SUM(agent_occupancy_target_percentage)
    - name: "Average Agent Occupancy Target Percentage"
      expr: AVG(agent_occupancy_target_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_service_case_assignment`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Service Case Assignment business metrics"
  source: "`cmoore_customer_demos`.`service`.`service_case_assignment`"
  dimensions:
    - name: "Case Number"
      expr: case_number
    - name: "Assignment Timestamp"
      expr: assignment_timestamp
    - name: "Assignment Date"
      expr: assignment_date
    - name: "Assignment Type"
      expr: assignment_type
    - name: "Assignment Method"
      expr: assignment_method
    - name: "Assignment Reason Code"
      expr: assignment_reason_code
    - name: "Assignment Reason Description"
      expr: assignment_reason_description
    - name: "Assigner Name"
      expr: assigner_name
    - name: "Assigner Type"
      expr: assigner_type
    - name: "Assignee Name"
      expr: assignee_name
    - name: "Assignee Type"
      expr: assignee_type
    - name: "Assignee Email"
      expr: assignee_email
    - name: "Previous Assignee Name"
      expr: previous_assignee_name
    - name: "Team Name"
      expr: team_name
    - name: "Department Name"
      expr: department_name
    - name: "Acceptance Timestamp"
      expr: acceptance_timestamp
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Service Case Assignment"
      expr: COUNT(DISTINCT service_case_assignment_id)
    - name: "Total Skill Match Score"
      expr: SUM(skill_match_score)
    - name: "Average Skill Match Score"
      expr: AVG(skill_match_score)
    - name: "Total Workload Weight"
      expr: SUM(workload_weight)
    - name: "Average Workload Weight"
      expr: AVG(workload_weight)
    - name: "Total Assignment Confidence Score"
      expr: SUM(assignment_confidence_score)
    - name: "Average Assignment Confidence Score"
      expr: AVG(assignment_confidence_score)
    - name: "Total Workload Balance Score"
      expr: SUM(workload_balance_score)
    - name: "Average Workload Balance Score"
      expr: AVG(workload_balance_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_service_channel`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Service Channel business metrics"
  source: "`cmoore_customer_demos`.`service`.`service_channel`"
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
    - name: "Is Member Facing"
      expr: is_member_facing
    - name: "Is Provider Facing"
      expr: is_provider_facing
    - name: "Is Authenticated Required"
      expr: is_authenticated_required
    - name: "Authentication Method"
      expr: authentication_method
    - name: "Availability Hours"
      expr: availability_hours
    - name: "Availability Start Time"
      expr: availability_start_time
    - name: "Availability End Time"
      expr: availability_end_time
    - name: "Timezone"
      expr: timezone
    - name: "Is 24 7 Available"
      expr: is_24_7_available
    - name: "Routing Rule"
      expr: routing_rule
    - name: "Routing Priority"
      expr: routing_priority
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Service Channel"
      expr: COUNT(DISTINCT service_channel_id)
    - name: "Total Fcr Target Percentage"
      expr: SUM(fcr_target_percentage)
    - name: "Average Fcr Target Percentage"
      expr: AVG(fcr_target_percentage)
    - name: "Total Cost Per Interaction"
      expr: SUM(cost_per_interaction)
    - name: "Average Cost Per Interaction"
      expr: AVG(cost_per_interaction)
    - name: "Total Abandonment Rate Percentage"
      expr: SUM(abandonment_rate_percentage)
    - name: "Average Abandonment Rate Percentage"
      expr: AVG(abandonment_rate_percentage)
    - name: "Total Satisfaction Score"
      expr: SUM(satisfaction_score)
    - name: "Average Satisfaction Score"
      expr: AVG(satisfaction_score)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_service_schedule`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Service Schedule business metrics"
  source: "`cmoore_customer_demos`.`service`.`service_schedule`"
  dimensions:
    - name: "Agent Name"
      expr: agent_name
    - name: "Date"
      expr: date
    - name: "Shift Start Time"
      expr: shift_start_time
    - name: "Shift End Time"
      expr: shift_end_time
    - name: "Shift Duration Minutes"
      expr: shift_duration_minutes
    - name: "Shift Type"
      expr: shift_type
    - name: "Shift Code"
      expr: shift_code
    - name: "Break Start Time 1"
      expr: break_start_time_1
    - name: "Break End Time 1"
      expr: break_end_time_1
    - name: "Break Duration Minutes 1"
      expr: break_duration_minutes_1
    - name: "Break Type 1"
      expr: break_type_1
    - name: "Break Start Time 2"
      expr: break_start_time_2
    - name: "Break End Time 2"
      expr: break_end_time_2
    - name: "Break Duration Minutes 2"
      expr: break_duration_minutes_2
    - name: "Break Type 2"
      expr: break_type_2
    - name: "Break Start Time 3"
      expr: break_start_time_3
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Service Schedule"
      expr: COUNT(DISTINCT service_schedule_id)
    - name: "Total Productive Hours"
      expr: SUM(productive_hours)
    - name: "Average Productive Hours"
      expr: AVG(productive_hours)
    - name: "Total Pay Rate Multiplier"
      expr: SUM(pay_rate_multiplier)
    - name: "Average Pay Rate Multiplier"
      expr: AVG(pay_rate_multiplier)
    - name: "Total Target Fcr Percentage"
      expr: SUM(target_fcr_percentage)
    - name: "Average Target Fcr Percentage"
      expr: AVG(target_fcr_percentage)
    - name: "Total Adherence Target Percentage"
      expr: SUM(adherence_target_percentage)
    - name: "Average Adherence Target Percentage"
      expr: AVG(adherence_target_percentage)
    - name: "Total Adherence Percentage"
      expr: SUM(adherence_percentage)
    - name: "Average Adherence Percentage"
      expr: AVG(adherence_percentage)
    - name: "Total Target Occupancy Percentage"
      expr: SUM(target_occupancy_percentage)
    - name: "Average Target Occupancy Percentage"
      expr: AVG(target_occupancy_percentage)
    - name: "Total Target Utilization Percentage"
      expr: SUM(target_utilization_percentage)
    - name: "Average Target Utilization Percentage"
      expr: AVG(target_utilization_percentage)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_service_status_code`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Service Status Code business metrics"
  source: "`cmoore_customer_demos`.`service`.`service_status_code`"
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
    - name: "Is Terminal"
      expr: is_terminal
    - name: "Is Reopenable"
      expr: is_reopenable
    - name: "Requires Action"
      expr: requires_action
    - name: "Display Order"
      expr: display_order
    - name: "Color Code"
      expr: color_code
    - name: "Icon Name"
      expr: icon_name
    - name: "Sla Applicable"
      expr: sla_applicable
    - name: "Sla Pause"
      expr: sla_pause
    - name: "Auto Close Eligible"
      expr: auto_close_eligible
    - name: "Auto Close Days"
      expr: auto_close_days
    - name: "Notification Required"
      expr: notification_required
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Service Status Code"
      expr: COUNT(DISTINCT service_status_code_id)
$$;

CREATE OR REPLACE VIEW `cmoore_customer_demos`.`_metrics`.`service_session`
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Session business metrics"
  source: "`cmoore_customer_demos`.`service`.`session`"
  dimensions:
    - name: "Channel"
      expr: channel
    - name: "Start Timestamp"
      expr: start_timestamp
    - name: "End Timestamp"
      expr: end_timestamp
    - name: "Duration Seconds"
      expr: duration_seconds
    - name: "Interaction Type"
      expr: interaction_type
    - name: "Outcome Status"
      expr: outcome_status
    - name: "Satisfaction Score"
      expr: satisfaction_score
    - name: "First Contact Resolution Flag"
      expr: first_contact_resolution_flag
    - name: "Language Code"
      expr: language_code
    - name: "Device Type"
      expr: device_type
    - name: "Ip Address"
      expr: ip_address
    - name: "Country Code"
      expr: country_code
    - name: "Escalation Flag"
      expr: escalation_flag
    - name: "Follow Up Due Date"
      expr: follow_up_due_date
    - name: "Notes"
      expr: notes
    - name: "Start Timestamp Month"
      expr: DATE_TRUNC('MONTH', start_timestamp)
  measures:
    - name: "Row Count"
      expr: COUNT(1)
    - name: "Distinct Session"
      expr: COUNT(DISTINCT session_id)
$$;