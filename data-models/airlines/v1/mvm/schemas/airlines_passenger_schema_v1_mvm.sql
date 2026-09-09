-- Schema for Domain: passenger | Business: Airlines | Version: v1_mvm
-- Generated on: 2026-05-07 15:14:30

-- ========= DATABASE =========
CREATE DATABASE IF NOT EXISTS `airlines_ecm`.`passenger` COMMENT 'Single source of truth for all passenger identity and profile data — the WHO the airline serves. Owns PNR-linked passenger profiles, identity documents, contact details, travel preferences, accessibility and SSR (Special Service Request) preferences, loyalty tier linkage, and segmentation attributes. Serves as the authoritative customer identity hub referenced by reservation, loyalty, and ancillary domains. Aligns with Amadeus Altéa PSS.';

-- ========= TABLES =========
CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`profile` (
    `profile_id` BIGINT COMMENT 'Primary key for profile',
    `ffp_member_id` BIGINT COMMENT 'Reference to the loyalty program membership record for this passenger. Links passenger profile to their FFP account for tier status and mileage accrual.',
    `city_pair_id` BIGINT COMMENT 'Foreign key linking to route.city_pair. Business justification: Route development and network planning teams analyze passenger home/preferred city pairs to identify underserved markets and optimize route networks. Marketing uses this for targeted route launch camp',
    `accessibility_requirements` STRING COMMENT 'Special assistance or accessibility needs for passengers with disabilities or reduced mobility. Free-text field capturing wheelchair requirements, visual/hearing impairments, service animal needs, medical equipment, etc. Detailed SSR codes stored in separate SSR product.',
    `completeness_score` DECIMAL(18,2) COMMENT 'Calculated percentage score (0.00 to 100.00) indicating the completeness of the passenger profile based on presence of key fields (contact details, travel documents, preferences, loyalty linkage). Used for data quality monitoring and personalization readiness.',
    `country_of_residence` STRING COMMENT 'Country where the passenger permanently resides, represented as ISO 3166-1 alpha-3 country code. Used for customs declarations and passenger segmentation analytics.. Valid values are `^[A-Z]{3}$`',
    `created_timestamp` TIMESTAMP COMMENT 'Date and time when the passenger profile was first created in the system. Immutable audit field for profile lifecycle tracking.',
    `creation_source` STRING COMMENT 'System or channel through which the passenger profile was originally created. Tracks profile origin for data quality and channel analytics. GDS=Global Distribution System (Amadeus, Sabre, Travelport).. Valid values are `altea_pss|web|mobile|gds|call_center|airport_kiosk`',
    `customer_segment` STRING COMMENT 'Marketing segmentation classification for the passenger based on travel behavior, spend patterns, and loyalty tier. Examples: premium_frequent_flyer, leisure_traveler, business_traveler, occasional_flyer, vip_corporate. [ENUM-REF-CANDIDATE: premium_frequent_flyer|leisure_traveler|business_traveler|occasional_flyer|vip_corporate|group_traveler|family_traveler — promote to reference product]',
    `data_sharing_consent` BOOLEAN COMMENT 'Indicates whether the passenger has consented to sharing their personal data with airline partners, codeshare airlines, and third-party service providers. True=consented, False=not consented.',
    `date_of_birth` DATE COMMENT 'Date of birth of the passenger. Required for age verification, infant/child classification, unaccompanied minor processing, and compliance with TSA Secure Flight and API (Advanced Passenger Information) requirements.',
    `emergency_contact_name` STRING COMMENT 'Full name of the passengers designated emergency contact person to be notified in case of travel disruptions, medical emergencies, or incidents.',
    `emergency_contact_phone` STRING COMMENT 'Phone number of the passengers designated emergency contact person. E.164 international format recommended.. Valid values are `^+?[1-9]d{1,14}$`',
    `emergency_contact_relationship` STRING COMMENT 'Relationship of the emergency contact person to the passenger (e.g., spouse, parent, child, sibling, friend).. Valid values are `spouse|parent|child|sibling|friend|other`',
    `first_name` STRING COMMENT 'Legal first name (given name) of the passenger as it appears on government-issued identification documents. Must match travel documents for international travel.',
    `gender` STRING COMMENT 'Gender of the passenger as recorded in travel documents. M=Male, F=Female, X=Unspecified/Non-binary, U=Undisclosed. Required for API and TSA Secure Flight compliance.. Valid values are `M|F|X|U`',
    `known_traveler_number` STRING COMMENT 'TSA PreCheck Known Traveler Number or equivalent trusted traveler program identifier (e.g., Global Entry, NEXUS, SENTRI). Enables expedited security screening at participating airports.',
    `last_name` STRING COMMENT 'Legal last name (surname/family name) of the passenger as it appears on government-issued identification documents. Must match travel documents for international travel.',
    `marketing_opt_in` BOOLEAN COMMENT 'Indicates whether the passenger has consented to receive marketing communications, promotional offers, and newsletters from the airline. True=opted in, False=opted out.',
    `meal_preference` STRING COMMENT 'Passengers preferred meal type for in-flight catering. Standard IATA SSR meal codes (e.g., VGML=Vegetarian, KSML=Kosher, DBML=Diabetic, MOML=Muslim, HNML=Hindu). [ENUM-REF-CANDIDATE: VGML|KSML|DBML|MOML|HNML|AVML|BBML|BLML|CHML|FPML|GFML|LCML|LFML|LSML|NLML|ORML|PRML|SFML|SPML|VJML|VOML — promote to reference product]',
    `middle_name` STRING COMMENT 'Middle name or initial of the passenger. Optional field that may be required for certain international destinations or to match travel documents.',
    `nationality` STRING COMMENT 'Nationality of the passenger represented as ISO 3166-1 alpha-3 country code. Required for visa validation, customs processing, and API submission to destination countries.. Valid values are `^[A-Z]{3}$`',
    `passenger_type` STRING COMMENT 'Classification of passenger by age and travel status. ADT=Adult (12+ years), CHD=Child (2-11 years), INF=Infant (under 2 years), UMN=Unaccompanied Minor. Determines fare rules, seating requirements, and service protocols.. Valid values are `ADT|CHD|INF|UMN`',
    `preferred_language` STRING COMMENT 'Preferred language for passenger communications, notifications, and in-flight services. ISO 639-1 two-letter language code (e.g., en, es, fr, de, zh).. Valid values are `^[a-z]{2}$`',
    `primary_email` STRING COMMENT 'Primary email address for passenger communications, booking confirmations, flight notifications, and digital receipts. Display-only summary field; authoritative multi-valued contact store is the contact_detail product.. Valid values are `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$`',
    `primary_phone` STRING COMMENT 'Primary contact phone number for passenger communications, flight alerts, and operational notifications. E.164 international format recommended. Display-only summary field; authoritative multi-valued contact store is the contact_detail product.. Valid values are `^+?[1-9]d{1,14}$`',
    `profile_status` STRING COMMENT 'Current lifecycle status of the passenger profile. Active=profile in use, Inactive=dormant profile, Suspended=temporarily blocked, Merged=consolidated into another profile, Deceased=passenger deceased per notification.. Valid values are `active|inactive|suspended|merged|deceased`',
    `redress_number` STRING COMMENT 'DHS Traveler Redress Inquiry Program (TRIP) control number issued to passengers who have been misidentified or delayed during security screening. Prevents future watchlist false positives.',
    `seat_preference` STRING COMMENT 'Passengers preferred seat location on the aircraft. Used for automated seat assignment and upgrade processing.. Valid values are `window|aisle|middle|no_preference`',
    `suffix` STRING COMMENT 'Name suffix such as Jr, Sr, III, etc. Used to distinguish passengers with identical names.',
    `title` STRING COMMENT 'Courtesy title or honorific for the passenger used in communications and boarding documents.. Valid values are `Mr|Mrs|Ms|Miss|Dr|Prof`',
    `unaccompanied_minor_guardian_name` STRING COMMENT 'Full name of the parent or legal guardian responsible for an unaccompanied minor passenger. Required for UMN bookings to coordinate drop-off and pick-up procedures.',
    `unaccompanied_minor_guardian_phone` STRING COMMENT 'Contact phone number for the parent or legal guardian of an unaccompanied minor passenger. Used for coordination during travel and emergency contact.. Valid values are `^+?[1-9]d{1,14}$`',
    `updated_timestamp` TIMESTAMP COMMENT 'Date and time when the passenger profile was last modified. Updated on any change to profile attributes, contact details, or preferences.',
    `vip_indicator` BOOLEAN COMMENT 'Flag indicating whether the passenger is designated as a VIP requiring special handling, premium services, or executive attention. True=VIP status, False=standard passenger.',
    CONSTRAINT pk_profile PRIMARY KEY(`profile_id`)
) COMMENT 'Core master record for every individual passenger served by the airline — the authoritative identity hub (SSOT) for the passenger domain. Stores full legal name, date of birth, gender, nationality, preferred language, passenger type (adult, child, infant, unaccompanied minor), profile creation source (Altéa PSS, web, mobile, GDS), profile status, and data consent flags. Holds a summary primary contact reference (single email, single phone) for display purposes only — the authoritative multi-valued contact store is the contact_detail product. Referenced by reservation, loyalty, and ancillary domains via passenger_id. Aligns with Amadeus Altéa passenger profile entity.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`travel_identity_document` (
    `travel_identity_document_id` BIGINT COMMENT 'Unique identifier for the travel identity document record. Primary key.',
    `profile_id` BIGINT COMMENT 'Reference to the passenger who holds this travel document. Links to the passenger master record.',
    `apis_response_code` STRING COMMENT 'Response code received from border control authority after APIS transmission. OK=cleared to board; INHIBITED=passenger denied boarding; CONDITIONAL=manual review required. Codes vary by country.',
    `apis_transmission_timestamp` TIMESTAMP COMMENT 'Date and time when the document data was transmitted to border control authorities. Used to prove compliance with advance notification requirements (typically 72 hours before departure for USA).',
    `apis_transmitted_flag` BOOLEAN COMMENT 'Indicates whether this documents data has been successfully transmitted to destination country border control authorities via APIS. Required for flights to USA, Canada, UK, EU, and many other jurisdictions.',
    `created_timestamp` TIMESTAMP COMMENT 'Date and time when this document record was first created in the system. Part of audit trail for regulatory compliance and data lineage.',
    `date_of_birth` DATE COMMENT 'Date of birth of the document holder as printed on the travel document. Required for APIS reporting, secure flight screening (TSA), and age-based service eligibility (unaccompanied minor, senior fares).',
    `document_image_url` STRING COMMENT 'Secure storage location (URI) of the scanned or photographed document image. Used for manual verification, fraud investigation, and regulatory compliance. Access restricted to authorized personnel only.',
    `document_number` STRING COMMENT 'Unique alphanumeric identifier printed on the travel document. This is the primary identifier used for APIS (Advance Passenger Information System) reporting and border control verification.',
    `document_source` STRING COMMENT 'Method by which the document data was captured. Manual_entry=agent typed data; OCR_scan=automated optical character recognition from image; Mobile_app=passenger self-service via mobile; GDS=received from Global Distribution System; API_integration=received from partner system.. Valid values are `manual_entry|ocr_scan|mobile_app|gds|api_integration`',
    `document_type` STRING COMMENT 'Type of travel identity document. Passport is the most common for international travel; national ID cards are accepted within certain regions (e.g., EU, Schengen); visas grant entry permission; residence permits prove legal residency; refugee travel documents and stateless person documents are issued under international conventions.. Valid values are `passport|national_id|visa|residence_permit|refugee_travel_document|stateless_person_document`',
    `expiry_date` DATE COMMENT 'Date the travel document expires. Most countries require passport validity of 6 months beyond the intended stay. System must alert if document expires before return travel date.',
    `gender` STRING COMMENT 'Gender marker as printed on the travel document. M=Male, F=Female, X=Unspecified/Non-binary (per ICAO 2018 guidelines). Required for APIS and secure flight reporting.. Valid values are `M|F|X`',
    `given_names` STRING COMMENT 'First and middle names as printed on the travel document. Must match PNR for secure flight and APIS compliance.',
    `is_primary_document` BOOLEAN COMMENT 'Flag indicating whether this is the passengers primary travel document for the current booking. A passenger may hold multiple documents (e.g., passport + national ID), but only one is designated primary for APIS reporting.',
    `issue_date` DATE COMMENT 'Date the travel document was issued by the authority. Used to calculate document age and assess fraud risk (newly issued documents before travel may trigger additional screening).',
    `issuing_authority` STRING COMMENT 'Name of the government agency or authority that issued the document (e.g., U.S. Department of State, UK Home Office). Used for document verification and fraud detection.',
    `issuing_country_code` STRING COMMENT 'Three-letter ISO 3166-1 alpha-3 code of the country or authority that issued the document. Critical for APIS reporting and visa waiver program eligibility determination.. Valid values are `^[A-Z]{3}$`',
    `known_traveller_number` STRING COMMENT 'Trusted traveller program membership number (e.g., TSA PreCheck, Global Entry, NEXUS, SENTRI, APEC Business Travel Card). Enables expedited security screening and border clearance. Stored for automatic inclusion in secure flight data.',
    `known_traveller_program` STRING COMMENT 'Name of the trusted traveller program associated with the known traveller number. Determines which expedited lanes and services the passenger is eligible for.. Valid values are `TSA_PRECHECK|GLOBAL_ENTRY|NEXUS|SENTRI|APEC_BUSINESS_TRAVEL_CARD|CLEAR`',
    `last_used_flight_date` DATE COMMENT 'Date of the most recent flight on which this document was used for travel. Helps identify stale or outdated document records and supports passenger profile analytics.',
    `mrz_line1` STRING COMMENT 'First line of the machine-readable zone at the bottom of the document. Contains document type, issuing country, and surname/given names in standardized format. Used for automated document scanning and APIS transmission.',
    `mrz_line2` STRING COMMENT 'Second line of the machine-readable zone. Contains document number, nationality, date of birth, gender, expiry date, and check digits. Enables rapid data capture via optical character recognition (OCR) at check-in kiosks and border control.',
    `mrz_line3` STRING COMMENT 'Third line of the machine-readable zone (present on some document types such as ID cards). Contains additional personal data and check digits.',
    `nationality_code` STRING COMMENT 'Three-letter ISO 3166-1 alpha-3 code representing the nationality of the document holder. May differ from issuing country for dual nationals or residents. Required for APIS and visa requirement checks.. Valid values are `^[A-Z]{3}$`',
    `notes` STRING COMMENT 'Free-text field for agent or system notes regarding the document. May include verification issues, special handling instructions, or discrepancies requiring follow-up.',
    `place_of_birth` STRING COMMENT 'City and country of birth as printed on the travel document. Required for certain APIS destinations (e.g., USA, Canada) and visa applications.',
    `redress_number` STRING COMMENT 'DHS Traveler Redress Inquiry Program (TRIP) control number issued to passengers who have been misidentified as a security threat. Prevents false positive watchlist matches during secure flight screening.',
    `secure_flight_status` STRING COMMENT 'TSA Secure Flight screening result for USA-bound flights. Not_submitted=data not yet sent; Cleared=passenger approved for boarding; Inhibited=passenger denied boarding (no-fly list match); Conditional=requires additional screening or documentation.. Valid values are `not_submitted|cleared|inhibited|conditional`',
    `surname` STRING COMMENT 'Family name or surname as printed on the travel document. Must match exactly with booking PNR (Passenger Name Record) for boarding pass issuance and border clearance.',
    `updated_timestamp` TIMESTAMP COMMENT 'Date and time when this document record was last modified. Tracks changes to document data, verification status, or APIS transmission results.',
    `verification_status` STRING COMMENT 'Current verification state of the document. Not_verified=newly entered, pending check; Verified=passed authenticity and expiry checks; Failed=document rejected (invalid format, fraudulent); Expired=document past expiry date; Flagged=requires manual review by security or compliance team.. Valid values are `not_verified|verified|failed|expired|flagged`',
    `verification_timestamp` TIMESTAMP COMMENT 'Date and time when the document verification status was last updated. Used for audit trail and compliance reporting.',
    `verified_by` STRING COMMENT 'User ID or system identifier of the agent or automated process that performed the verification. Supports audit trail and accountability for document acceptance decisions.',
    `visa_required_flag` BOOLEAN COMMENT 'Indicates whether a visa is required for the passengers itinerary based on nationality, destination, and transit countries. Calculated using IATA Timatic rules. If true, a separate visa document record must exist.',
    CONSTRAINT pk_travel_identity_document PRIMARY KEY(`travel_identity_document_id`)
) COMMENT 'Stores all identity and travel documents associated with a passenger — passports, national ID cards, visas, residence permits, and known traveller numbers (e.g., TSA PreCheck, Global Entry, NEXUS). Captures document number, issuing country (ICAO alpha-2), document type, issue date, expiry date, machine-readable zone (MRZ) data, and document verification status. Supports APIS (Advance Passenger Information System) regulatory reporting and border control compliance. A passenger may hold multiple documents across multiple nationalities.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`contact_detail` (
    `contact_detail_id` BIGINT COMMENT 'Unique identifier for the contact detail record. Primary key.',
    `profile_id` BIGINT COMMENT 'Reference to the passenger who owns this contact detail. Links to the passenger profile in the passenger domain.',
    `address_line_1` STRING COMMENT 'The primary street address line (street number, street name, building). Part of the postal address for the passenger.',
    `address_line_2` STRING COMMENT 'Secondary address line for apartment, suite, unit, or building details. Optional component of postal address.',
    `city` STRING COMMENT 'The city or municipality name for the postal address.',
    `contact_channel` STRING COMMENT 'The communication channel or medium through which this contact method operates (voice, SMS, email, postal, WhatsApp, app notification). Distinct from contact_type which defines the category.. Valid values are `voice|sms|email|postal|whatsapp|app_notification`',
    `contact_status` STRING COMMENT 'The current lifecycle status of this contact detail: active (in use), inactive (not in use), bounced (delivery failed), invalid (format error), pending_verification (awaiting confirmation).. Valid values are `active|inactive|bounced|invalid|pending_verification`',
    `contact_type` STRING COMMENT 'The category of contact channel: email, mobile phone, home phone, work phone, postal address, or emergency contact.. Valid values are `email|mobile|home_phone|work_phone|postal_address|emergency`',
    `country_code` STRING COMMENT 'The 3-letter ISO country code for the contact address or phone number (e.g., USA, GBR, CAN). Aligns with IATA and ICAO standards.. Valid values are `^[A-Z]{3}$`',
    `created_timestamp` TIMESTAMP COMMENT 'The timestamp when this contact detail record was first created in the system. Supports audit trail and data lineage.',
    `effective_from_date` DATE COMMENT 'The date from which this contact detail becomes active and valid for use. Supports temporal contact management.',
    `effective_to_date` DATE COMMENT 'The date until which this contact detail remains active and valid. Null indicates no expiration. Supports temporal contact management and historical tracking.',
    `email_address` STRING COMMENT 'The email address for this contact record. Used for e-ticket delivery, booking confirmations, IROP notifications, and marketing communications per DOT consumer communication requirements.. Valid values are `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$`',
    `emergency_contact_name` STRING COMMENT 'The full name of the emergency contact person. Populated only when contact_type is emergency. Used for incident response and passenger welfare.',
    `emergency_contact_relationship` STRING COMMENT 'The relationship of the emergency contact to the passenger (spouse, parent, child, sibling, friend, other). Populated only when contact_type is emergency.. Valid values are `spouse|parent|child|sibling|friend|other`',
    `is_preferred` BOOLEAN COMMENT 'Flag indicating whether this is the passengers preferred contact method for operational and marketing communications. Only one contact per type should be marked preferred.',
    `is_verified` BOOLEAN COMMENT 'Flag indicating whether this contact detail has been verified (e.g., email confirmed via link, phone verified via OTP). Supports data quality and fraud prevention.',
    `last_used_date` DATE COMMENT 'The date when this contact detail was last used for communication (email sent, SMS delivered, call made). Supports contact data quality and hygiene.',
    `opt_in_date` DATE COMMENT 'The date when the passenger provided consent for communications via this contact channel. Required for audit and compliance purposes.',
    `opt_in_marketing` BOOLEAN COMMENT 'Flag indicating whether the passenger has consented to receive marketing communications via this contact channel. Required for GDPR and CAN-SPAM compliance.',
    `opt_in_operational` BOOLEAN COMMENT 'Flag indicating whether the passenger has consented to receive operational communications (flight status, IROP notifications, gate changes) via this contact channel. Typically defaults to true for service delivery.',
    `opt_out_date` DATE COMMENT 'The date when the passenger withdrew consent for communications via this contact channel. Supports unsubscribe tracking and compliance.',
    `phone_country_code` STRING COMMENT 'The international dialing code for the phone number (e.g., +1 for USA, +44 for UK). Supports global passenger contact management.. Valid values are `^+?[1-9]d{0,3}$`',
    `phone_number` STRING COMMENT 'The telephone number in E.164 international format. Includes mobile, home, and work phone numbers. Used for operational notifications, IROP proactive communication, and SSR coordination.. Valid values are `^+?[1-9]d{1,14}$`',
    `postal_code` STRING COMMENT 'The postal or ZIP code for the address. Format varies by country (e.g., 5-digit ZIP in USA, alphanumeric in Canada/UK).',
    `source_system` STRING COMMENT 'The system or channel through which this contact detail was originally captured (Altéa PSS, mobile app, web booking, call center, airport kiosk, GDS, partner API). Supports data lineage and quality assessment. [ENUM-REF-CANDIDATE: altea_pss|mobile_app|web_booking|call_center|airport_kiosk|gds|partner_api — 7 candidates stripped; promote to reference product]',
    `state_province` STRING COMMENT 'The state, province, or region for the postal address. Supports jurisdiction-specific compliance and tax reporting.',
    `updated_timestamp` TIMESTAMP COMMENT 'The timestamp when this contact detail record was last modified. Supports audit trail and change tracking.',
    `verification_date` DATE COMMENT 'The date when this contact detail was last verified by the passenger. Supports contact data quality management.',
    CONSTRAINT pk_contact_detail PRIMARY KEY(`contact_detail_id`)
) COMMENT 'All contact channels for a passenger — email addresses, phone numbers (mobile, home, work), postal addresses, and emergency contacts. Captures contact type, channel, preferred contact flag, opt-in/opt-out status for marketing and operational communications, verification status, and effective date range. Supports IROP proactive notification and DOT consumer communication requirements. A passenger may have multiple active contact records across channels. Distinct from pax_profile (which holds a summary contact reference) — this is the detailed, multi-valued contact store.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`ssr_record` (
    `ssr_record_id` BIGINT COMMENT 'Unique identifier for the SSR record instance. Primary key.',
    `accessibility_profile_id` BIGINT COMMENT 'Foreign key linking to passenger.accessibility_profile. Business justification: SSR records for mobility assistance (WCHR, WCHC, WCHS), oxygen requirements, medical equipment, and other PRM-related service codes are directly derived from or linked to a passengers accessibility_p',
    `ancillary_emd_id` BIGINT COMMENT 'Foreign key linking to ancillary.ancillary_emd. Business justification: Chargeable SSR revenue reconciliation: when is_chargeable=true, an SSR generates an ancillary EMD for billing and settlement. Revenue accounting and airport operations teams must reconcile each charge',
    `cabin_class_id` BIGINT COMMENT 'Foreign key linking to inventory.cabin_class. Business justification: SSR fulfillment (meal codes, wheelchair boarding, medical clearance) is cabin-class-specific. Catering orders, ground handling briefs, and crew service plans are prepared per cabin. Aviation ops teams',
    `cost_centre_id` BIGINT COMMENT 'Foreign key linking to finance.cost_centre. Business justification: SSR services (wheelchair, special meals, medical equipment, unaccompanied minor handling) generate operational costs attributed to specific cost centres (ground services, catering, medical). Airlines ',
    `ffp_member_id` BIGINT COMMENT 'Foreign key linking to loyalty.ffp_member. Business justification: Links special service requests to loyalty status for benefit fulfillment validation. Airlines must verify tier-based entitlements (complimentary lounge access, priority boarding, extra baggage) when p',
    `flight_inventory_id` BIGINT COMMENT 'Foreign key linking to inventory.flight_inventory. Business justification: SSRs (wheelchairs, meals, oxygen) are fulfilled on specific flight inventory instances. Operations must track which inventory leg delivers each service for catering, ground handling, and compliance. C',
    `flight_leg_id` BIGINT COMMENT 'Reference to the specific flight leg for which this SSR applies. Nullable if SSR applies to entire journey.',
    `member_id` BIGINT COMMENT 'Foreign key linking to crew.crew_member. Business justification: Airlines track which cabin crew member fulfilled special service requests (wheelchair assistance, medical needs, special meals) for quality assurance, training feedback, and incident investigation. Op',
    `mel_item_id` BIGINT COMMENT 'Foreign key linking to maintenance.mel_item. Business justification: Medical/special SSR pre-flight MEL compliance: MEDA, OXYG, STCR, and WCHR SSRs require verification that the governing MEL item (onboard oxygen system, stretcher fittings, wheelchair stowage) is servi',
    `member_benefit_id` BIGINT COMMENT 'Foreign key linking to loyalty.member_benefit. Business justification: SSR fulfillment tracking: when a tier benefit (priority meal, wheelchair assistance) authorizes an SSR, the SSR record must reference the specific member_benefit entitlement consumed. Enables benefit ',
    `carrier_id` BIGINT COMMENT 'Foreign key linking to route.carrier. Business justification: Interline SSR passthrough requires identifying the operating carrier to route handling instructions and special service requests to the correct airline. The is_interline flag and existing operating_ca',
    `profile_id` BIGINT COMMENT 'Reference to the passenger profile to whom this SSR is linked.',
    `pnr_id` BIGINT COMMENT 'Reference to the PNR booking under which this SSR was requested.',
    `product_catalog_id` BIGINT COMMENT 'Foreign key linking to ancillary.product_catalog. Business justification: SSR pricing and EMD issuance process: chargeable SSRs (WCHR, SPML, SPEQ) map to specific ancillary catalog products for pricing, revenue accounting, and IATA EMD generation. Airlines must link each SS',
    `route_id` BIGINT COMMENT 'Foreign key linking to route.route. Business justification: SSR fulfillment planning requires route-level context (wheelchair assistance varies by airport infrastructure, meal catering by route length/type). Operations teams pre-position resources by route. Co',
    `advance_notice_hours` STRING COMMENT 'Minimum number of hours before departure that this SSR must be requested. Nullable if no advance notice required.',
    `booking_channel` STRING COMMENT 'Channel through which this SSR was requested: web, mobile_app, call_center, airport_counter, travel_agent, GDS, API. [ENUM-REF-CANDIDATE: web|mobile_app|call_center|airport_counter|travel_agent|gds|api — 7 candidates stripped; promote to reference product]',
    `cancellation_timestamp` TIMESTAMP COMMENT 'Date and time when the SSR was cancelled. Nullable if not cancelled.',
    `charge_amount` DECIMAL(18,2) COMMENT 'Monetary amount charged for this SSR service. Nullable if not chargeable or charge not yet determined.',
    `charge_currency_code` STRING COMMENT 'Three-letter ISO 4217 currency code for the SSR charge amount (e.g., USD, EUR, GBP).. Valid values are `^[A-Z]{3}$`',
    `confirmation_timestamp` TIMESTAMP COMMENT 'Date and time when the SSR was confirmed by the airline or service provider. Nullable if not yet confirmed.',
    `created_timestamp` TIMESTAMP COMMENT 'System timestamp when this SSR record was first created in the database.',
    `equipment_required` STRING COMMENT 'Description of special equipment needed to fulfill this SSR (e.g., onboard wheelchair, oxygen concentrator, stretcher, incubator).',
    `fulfillment_notes` STRING COMMENT 'Free-text notes recorded by ground staff or cabin crew documenting how the SSR was fulfilled, any issues encountered, or passenger feedback.',
    `handling_instructions` STRING COMMENT 'Operational instructions for ground staff, cabin crew, or service providers on how to fulfill this SSR, including equipment needs, timing, and coordination requirements.',
    `is_chargeable` BOOLEAN COMMENT 'Boolean flag indicating whether this SSR incurs a charge to the passenger (true) or is provided as a complimentary service (false).',
    `is_interline` BOOLEAN COMMENT 'Boolean flag indicating whether this SSR applies to an interline segment operated by a partner carrier (true) or an own-metal flight (false).',
    `is_standing_preference` BOOLEAN COMMENT 'Boolean flag indicating whether this SSR was auto-populated from the passengers standing travel preferences (true) or requested ad-hoc for this booking (false).',
    `meal_code` STRING COMMENT 'Four-letter IATA meal code for dietary SSRs (e.g., VGML for vegetarian, KSML for kosher, DBML for diabetic). Applicable only when ssr_code is SPML.. Valid values are `^[A-Z]{4}$`',
    `medical_clearance_status` STRING COMMENT 'Status of medical clearance for SSRs requiring medical approval. Values: not_required, pending, approved, denied.. Valid values are `not_required|pending|approved|denied`',
    `request_timestamp` TIMESTAMP COMMENT 'Date and time when the SSR was initially requested by the passenger or booking agent.',
    `requires_advance_notice` BOOLEAN COMMENT 'Boolean flag indicating whether this SSR type requires advance notice to the airline (true) or can be requested at check-in or boarding (false).',
    `requires_medical_clearance` BOOLEAN COMMENT 'Boolean flag indicating whether this SSR requires medical clearance or MEDA form approval before confirmation (true for MEDA, OXYG, STCR SSRs).',
    `service_delivery_timestamp` TIMESTAMP COMMENT 'Date and time when the SSR service was actually delivered or completed. Nullable if not yet delivered.',
    `ssr_category` STRING COMMENT 'High-level categorization of the SSR type for reporting and operational grouping (accessibility, medical, dietary, unaccompanied minor, pet transport, special baggage, other). [ENUM-REF-CANDIDATE: accessibility|medical|dietary|unaccompanied_minor|pet_transport|special_baggage|other — 7 candidates stripped; promote to reference product]',
    `ssr_code` STRING COMMENT 'Four-letter IATA SSR code identifying the type of service requested (e.g., WCHR, WCHC, BLND, DEAF, MEDA, OXYG, SPML, UMNR, PETC, DPNA).. Valid values are `^[A-Z]{4}$`',
    `ssr_description` STRING COMMENT 'Free-text description providing additional details about the SSR, including handling instructions, meal preferences, medical conditions, or special equipment requirements.',
    `ssr_status` STRING COMMENT 'Current lifecycle status of the SSR indicating whether the service has been requested, confirmed by the airline, waitlisted, cancelled, denied, or completed.. Valid values are `requested|confirmed|waitlisted|cancelled|denied|completed`',
    `updated_timestamp` TIMESTAMP COMMENT 'System timestamp when this SSR record was last modified.',
    `wheelchair_type` STRING COMMENT 'Specific wheelchair assistance level for accessibility SSRs: WCHR (can walk stairs), WCHS (cannot walk stairs), WCHC (immobile, requires onboard wheelchair). Applicable only for wheelchair SSR codes.. Valid values are `WCHR|WCHS|WCHC`',
    CONSTRAINT pk_ssr_record PRIMARY KEY(`ssr_record_id`)
) COMMENT 'Special Service Request (SSR) records linked to a passenger profile — capturing per-flight or per-booking service instances for accessibility needs (WCHR, WCHC, BLND, DEAF), medical requirements (MEDA, OXYG), dietary meal requests (SPML codes instantiated from travel_preference standing preferences or ad-hoc), unaccompanied minor (UMNR) service, and other service codes defined by IATA SSR taxonomy. Each SSR record carries the IATA SSR code, free-text description, service status (requested, confirmed, cancelled), applicable flight scope, and handling instructions for ground and cabin crew. Distinct from travel_preference (standing preferences) and accessibility_profile (persistent PRM master) — this is the per-flight service instance.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` (
    `loyalty_linkage_id` BIGINT COMMENT 'Unique identifier for the loyalty program linkage record. Primary key.',
    `ffp_member_id` BIGINT COMMENT 'Foreign key linking to loyalty.ffp_member. Business justification: Enables real-time loyalty benefit validation during check-in, boarding, and service delivery. Airlines must resolve member number to full loyalty profile for tier recognition, lounge access, baggage a',
    `profile_id` BIGINT COMMENT 'Reference to the passenger profile to whom this loyalty program membership is linked.',
    `tier_status_id` BIGINT COMMENT 'Foreign key linking to loyalty.tier_status. Business justification: Tier recognition during account linkage: when an external FFP is linked, the airline records which tier_status was recognized/matched. loyalty_linkage already stores tier_effective_date and tier_expir',
    `alliance_code` STRING COMMENT 'The global airline alliance to which the FFP program belongs (Star Alliance, oneworld, SkyTeam). None indicates the program is not part of a major alliance or is the airlines own non-alliance program.. Valid values are `star_alliance|oneworld|skyteam|none`',
    `auto_recognition_enabled_flag` BOOLEAN COMMENT 'Boolean flag indicating whether automatic tier recognition and benefit application is enabled for this linkage at check-in, boarding, and service touchpoints. True enables automatic recognition; False requires manual override.',
    `created_timestamp` TIMESTAMP COMMENT 'The timestamp when this loyalty linkage record was first created in the system. Immutable audit field.',
    `data_quality_score` DECIMAL(18,2) COMMENT 'Numeric score (0.00 to 100.00) representing the completeness and accuracy of the loyalty linkage data. Higher scores indicate higher confidence in the linkage validity. Used for data stewardship and cleansing prioritization.',
    `external_reference_code` STRING COMMENT 'The unique identifier or key used by the external loyalty system or partner FFP to reference this linkage. Used for API calls, reconciliation, and cross-system traceability.',
    `ffp_program_code` STRING COMMENT 'IATA two-letter or three-character airline code identifying the loyalty program (e.g., UA for United MileagePlus, BA for British Airways Executive Club, LH for Lufthansa Miles & More). Includes own airline and partner programs within alliances (Star Alliance, oneworld, SkyTeam).. Valid values are `^[A-Z0-9]{2,3}$`',
    `last_modified_timestamp` TIMESTAMP COMMENT 'The timestamp when this loyalty linkage record was last modified. Updated on every change to the record.',
    `last_sync_timestamp` TIMESTAMP COMMENT 'The timestamp when this loyalty linkage record was last synchronized with the source loyalty system (e.g., Oracle Loyalty Cloud, partner FFP API). Used for data freshness monitoring and incremental load orchestration.',
    `last_verified_timestamp` TIMESTAMP COMMENT 'The timestamp when the linkage and tier status were last verified or synchronized with the authoritative loyalty system. Used to determine data freshness and trigger re-verification workflows.',
    `linkage_source_system` STRING COMMENT 'The operational system or channel from which this loyalty linkage was created or last updated (e.g., Amadeus Altéa PSS, Oracle Loyalty Cloud, Mobile App, Web Portal, Customer Service, GDS).',
    `linkage_status` STRING COMMENT 'Current status of the loyalty program linkage. Active indicates the linkage is operational and tier benefits apply. Suspended indicates temporary hold (e.g., fraud investigation). Unlinked indicates the passenger has removed the association. Pending verification indicates awaiting confirmation from the FFP. Expired indicates the membership has lapsed. Merged indicates the membership was consolidated into another record.. Valid values are `active|suspended|unlinked|pending_verification|expired|merged`',
    `linkage_type` STRING COMMENT 'Classification of the loyalty linkage. Primary indicates the passengers main FFP membership with the airline. Secondary indicates an additional membership. Partner indicates a linked membership with a codeshare or alliance partner. Reciprocal indicates a mutual recognition agreement membership.. Valid values are `primary|secondary|partner|reciprocal`',
    `notes` STRING COMMENT 'Free-text field for customer service agents or data stewards to record additional context, exceptions, or special handling instructions related to this loyalty linkage (e.g., VIP handling, disputed tier status, manual override reasons).',
    `reciprocal_benefit_eligible_flag` BOOLEAN COMMENT 'Boolean flag indicating whether this linkage qualifies for reciprocal benefits under alliance or partnership agreements (e.g., lounge access, priority boarding on partner airlines). True indicates eligibility; False indicates ineligible or restricted.',
    `recognition_priority` STRING COMMENT 'Numeric priority order for tier recognition when a passenger has multiple linked FFP memberships. Lower numbers indicate higher priority (1 = highest). Used at check-in and boarding to determine which tier benefits to apply.',
    `sync_status` STRING COMMENT 'Status of the most recent synchronization attempt with the source loyalty system. Success indicates data is current. Failed indicates synchronization error. Pending indicates sync in progress. Skipped indicates sync was bypassed. Partial indicates incomplete data received.. Valid values are `success|failed|pending|skipped|partial`',
    `tier_effective_date` DATE COMMENT 'The date on which the current tier status became effective for this membership.',
    `tier_expiry_date` DATE COMMENT 'The date on which the current tier status expires. Null if the tier does not expire or is lifetime status.',
    `unlinked_date` DATE COMMENT 'The date on which this loyalty program membership was unlinked from the passenger profile. Null if the linkage is still active or has never been unlinked.',
    `unlinked_reason_code` STRING COMMENT 'The reason code explaining why the loyalty linkage was unlinked. Null if the linkage has never been unlinked.. Valid values are `passenger_request|fraud_detected|membership_expired|duplicate_linkage|data_quality_issue|system_migration`',
    CONSTRAINT pk_loyalty_linkage PRIMARY KEY(`loyalty_linkage_id`)
) COMMENT 'Association entity linking a passenger profile to one or more Frequent Flyer Program (FFP) memberships — both the airlines own programme and partner airline programmes (Star Alliance, oneworld, SkyTeam). Stores FFP number, programme code (IATA carrier code), tier status at linkage time, tier expiry, linkage status (active, suspended, unlinked), and source system. This is a reference pointer only — loyalty master data (accrual, redemption, tier calculation) lives in the loyalty domain. Enables tier recognition at check-in and boarding without SSOT duplication.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`traveller_segment` (
    `traveller_segment_id` BIGINT COMMENT 'Primary key for traveller_segment',
    `cabin_class_id` BIGINT COMMENT 'Foreign key linking to inventory.cabin_class. Business justification: Traveller segments drive cabin-targeted upsell campaigns, upgrade eligibility pools, and RM-driven offer personalization. cabin_preference is a denormalized string representation of inventory.cabin_cl',
    `ffp_member_id` BIGINT COMMENT 'Foreign key linking to loyalty.ffp_member. Business justification: Enables loyalty-driven segmentation strategy and targeted promotions. Airlines use passenger behavioral segments to design tier qualification campaigns, bonus mile offers, and retention programs—requi',
    `profile_id` BIGINT COMMENT 'Reference to the passenger being segmented. Links to the passenger master record in the passenger domain.',
    `city_pair_id` BIGINT COMMENT 'Foreign key linking to route.city_pair. Business justification: Segmentation models analyze route preferences by customer type (business travelers prefer hub-to-hub, leisure prefer resort destinations). Marketing campaigns target segments with city-pair-specific o',
    `ancillary_propensity_score` DECIMAL(18,2) COMMENT 'Propensity score (0.0000 to 1.0000) indicating likelihood of purchasing ancillary services (seat selection, baggage, meals, lounge access). Used for upsell targeting.',
    `assignment_date` DATE COMMENT 'Date when the passenger was assigned to this segment. Used for segment tenure analysis and lifecycle tracking.',
    `booking_channel_preference` STRING COMMENT 'Preferred or most frequently used booking channel: direct web, mobile app, GDS (Global Distribution System), travel agent, call center, or mixed.. Valid values are `direct_web|mobile_app|gds|travel_agent|call_center|mixed`',
    `churn_risk_score` DECIMAL(18,2) COMMENT 'Predictive score (0.0000 to 1.0000) indicating the likelihood of passenger churn (switching to competitor or ceasing travel). Higher score indicates higher risk.',
    `confidence_score` DECIMAL(18,2) COMMENT 'Statistical confidence or probability score (0.0000 to 1.0000) indicating the models certainty in this segment assignment. Applicable for ML-derived segments; null for rule-based assignments.',
    `corporate_affiliation_flag` BOOLEAN COMMENT 'Indicates whether the passenger is affiliated with a corporate travel program or business account (true) or is a leisure/individual traveller (false).',
    `created_timestamp` TIMESTAMP COMMENT 'Timestamp when this segment assignment record was first created in the system. Used for audit trail and data lineage.',
    `effective_from_date` DATE COMMENT 'Date from which this segment assignment becomes active and should be used for targeting, pricing, and personalization decisions.',
    `effective_to_date` DATE COMMENT 'Date until which this segment assignment remains valid. Nullable for open-ended assignments. Used for segment expiry and refresh scheduling.',
    `last_modified_timestamp` TIMESTAMP COMMENT 'Timestamp when this segment assignment record was last updated. Used for change tracking and audit purposes.',
    `last_review_date` DATE COMMENT 'Date when this segment assignment was last reviewed or refreshed by the segmentation process. Used for data quality monitoring and refresh scheduling.',
    `lifetime_value_tier` STRING COMMENT 'Lifetime value tier classification derived from historical and predicted revenue: platinum (highest value), gold, silver, bronze, or standard. Distinct from loyalty program tier.. Valid values are `platinum|gold|silver|bronze|standard`',
    `loyalty_engagement_level` STRING COMMENT 'Level of engagement with the airlines FFP (Frequent Flyer Program): highly engaged (active accrual and redemption), engaged, moderately engaged, low engagement, or not enrolled.. Valid values are `highly_engaged|engaged|moderately_engaged|low_engagement|not_enrolled`',
    `next_review_date` DATE COMMENT 'Scheduled date for the next review or refresh of this segment assignment. Ensures segments remain current and accurate.',
    `price_sensitivity_indicator` STRING COMMENT 'Assessed price sensitivity level of the passenger segment: very high (highly price-sensitive, seeks lowest fares), high, medium, low, or very low (price-insensitive, values convenience/service).. Valid values are `very_high|high|medium|low|very_low`',
    `revenue_contribution_score` DECIMAL(18,2) COMMENT 'Estimated or actual revenue contribution value associated with this passenger segment, used for value-based segmentation and prioritization. Currency in airlines base currency.',
    `route_preference_type` STRING COMMENT 'Predominant route type preference: domestic, short-haul international, long-haul international, or mixed. Used for network planning and targeted offers.. Valid values are `domestic|short_haul_intl|long_haul_intl|mixed`',
    `segment_category` STRING COMMENT 'High-level classification of the segment type: value-based, behavior-based, lifecycle stage, propensity model, demographic, or geographic segmentation.. Valid values are `value|behavior|lifecycle|propensity|demographic|geographic`',
    `segment_code` STRING COMMENT 'Unique code identifying the segment type (e.g., HVT for high-value traveller, CFF for corporate frequent flyer, LSR for leisure traveller, PSN for price-sensitive, PRM for premium loyalist, LPS for lapsed traveller).. Valid values are `^[A-Z0-9_]{2,20}$`',
    `segment_description` STRING COMMENT 'Detailed textual description of the segment characteristics, targeting criteria, and business rationale. Used for segment documentation and stakeholder communication.',
    `segment_model_version` STRING COMMENT 'Version identifier of the segmentation model or rule set used to assign this segment. Enables tracking of model evolution and reprocessing.',
    `segment_name` STRING COMMENT 'Human-readable name of the passenger segment (e.g., High-Value Traveller, Corporate Frequent Flyer, Leisure Traveller, Price-Sensitive, Premium Loyalist, Lapsed Traveller).',
    `segment_notes` STRING COMMENT 'Free-text field for additional notes, comments, or context about this segment assignment. Used for manual overrides, special cases, or analyst annotations.',
    `segment_priority` STRING COMMENT 'Numeric priority ranking (1=highest) used when a passenger belongs to multiple segments simultaneously. Determines which segment takes precedence for targeting and personalization.',
    `segment_source` STRING COMMENT 'Origin of the segment assignment: rules engine (business rule-based), ML model (machine learning algorithm), manual (analyst-assigned), third-party (external data provider), or hybrid (combination of methods).. Valid values are `rules_engine|ml_model|manual|third_party|hybrid`',
    `segment_source_system` STRING COMMENT 'Name or identifier of the system or model that generated the segment assignment (e.g., Sabre AirVision Revenue Management, internal propensity model, CRM segmentation engine).',
    `segment_status` STRING COMMENT 'Current lifecycle status of the segment assignment: active (in use), inactive (not currently applied), expired (past effective date), suspended (temporarily disabled), or pending (awaiting activation).. Valid values are `active|inactive|expired|suspended|pending`',
    `targeting_eligible_flag` BOOLEAN COMMENT 'Indicates whether this segment assignment makes the passenger eligible for targeted marketing campaigns and personalized offers (true) or should be excluded (false) due to opt-out or regulatory restrictions.',
    `travel_frequency_band` STRING COMMENT 'Classification of passenger travel frequency based on flight count over a defined period: very high (frequent business traveller), high, medium, low, very low, or inactive (lapsed).. Valid values are `very_high|high|medium|low|very_low|inactive`',
    CONSTRAINT pk_traveller_segment PRIMARY KEY(`traveller_segment_id`)
) COMMENT 'Passenger segmentation and marketing classification records — assigns passengers to analytically derived or rule-based segments such as high-value traveller, corporate frequent flyer, leisure traveller, price-sensitive, premium loyalist, or lapsed traveller. Captures segment code, segment name, segment source (rules engine, ML model, manual), assignment date, expiry date, and confidence score where applicable. Used by revenue management for personalised pricing, by loyalty for targeted offers, and by ancillary for upsell propensity. Distinct from loyalty tier — this is a commercial segmentation layer.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`consent` (
    `consent_id` BIGINT COMMENT 'Primary key for consent',
    `company_code_id` BIGINT COMMENT 'Foreign key linking to finance.company_code. Business justification: GDPR and aviation data protection regulations require consent records to identify the data controller legal entity (company code). Airlines operating multiple subsidiaries must scope each passenger co',
    `minor_guardian_id` BIGINT COMMENT 'Foreign key linking to passenger.minor_guardian. Business justification: The consent table has explicit minor_consent_flag and parental_consent_verified_flag attributes, indicating that consent records for unaccompanied minors are a distinct business scenario requiring gua',
    `profile_id` BIGINT COMMENT 'Reference to the passenger profile to whom this consent record belongs. Links to the authoritative passenger identity in the passenger domain.',
    `promotion_id` BIGINT COMMENT 'Foreign key linking to loyalty.loyalty_promotion. Business justification: GDPR/regulatory consent traceability: when a passenger opts into a loyalty promotion, the consent record must reference the specific promotion as the processing_purpose. Regulators require consent to ',
    `audit_trail` STRING COMMENT 'A structured log or reference to detailed audit records capturing all consent lifecycle events (granted, modified, withdrawn, expired). Supports regulatory audit and dispute resolution.',
    `channel` STRING COMMENT 'The channel or touchpoint through which the passenger provided or updated their consent. Critical for audit trail and consent validity verification.. Valid values are `web|mobile_app|call_centre|airport_kiosk|email|in_flight`',
    `consent_status` STRING COMMENT 'Current lifecycle status of the consent. Indicates whether the passenger has granted, withdrawn, or is pending decision on the consent request. Expired indicates consent has passed its validity period.. Valid values are `granted|withdrawn|pending|expired|declined`',
    `consent_type` STRING COMMENT 'The category of consent granted or withheld by the passenger. Defines the specific data processing activity for which consent is required under GDPR, CCPA, PDPA, or other applicable data protection regulations.. Valid values are `marketing_email|marketing_sms|marketing_push|data_sharing_partner|profiling|personalisation`',
    `created_timestamp` TIMESTAMP COMMENT 'The date and time when this consent record was first created in the system. Recorded in ISO 8601 format (yyyy-MM-ddTHH:mm:ss.SSSXXX). Distinct from consent_granted_timestamp, which reflects the passengers action.',
    `device_type` STRING COMMENT 'The type of device used by the passenger to provide consent. Supports user experience analysis and consent validity verification.. Valid values are `desktop|mobile|tablet|kiosk|other`',
    `dpo_review_flag` BOOLEAN COMMENT 'Boolean indicator of whether this consent record has been reviewed or flagged for review by the airlines Data Protection Officer (DPO). Used for high-risk or disputed consent cases.',
    `expiry_date` DATE COMMENT 'The date on which the consent expires and must be re-requested from the passenger. Null for consents with no expiration. Recorded in ISO 8601 date format (yyyy-MM-dd). Required for jurisdictions with time-bound consent validity.',
    `granted_timestamp` TIMESTAMP COMMENT 'The date and time when the passenger granted consent. Recorded in ISO 8601 format (yyyy-MM-ddTHH:mm:ss.SSSXXX). Required for GDPR and CCPA audit trails.',
    `ip_address` STRING COMMENT 'The IP address from which the passenger submitted their consent. Used for fraud detection, audit trail, and jurisdiction determination. May be considered PII in some jurisdictions.',
    `jurisdiction_code` STRING COMMENT 'The three-letter ISO 3166-1 alpha-3 country code representing the legal jurisdiction under which this consent was collected. Determines applicable data protection regulation (GDPR for EU, CCPA for California, PDPA for Singapore, etc.).. Valid values are `^[A-Z]{3}$`',
    `language_code` STRING COMMENT 'The two-letter ISO 639-1 language code in which the consent request was presented to the passenger. Required for demonstrating informed consent in the passengers preferred language.. Valid values are `^[a-z]{2}$`',
    `last_modified_timestamp` TIMESTAMP COMMENT 'The date and time when this consent record was last modified. Recorded in ISO 8601 format (yyyy-MM-ddTHH:mm:ss.SSSXXX). Required for audit trail and data lineage.',
    `legal_basis` STRING COMMENT 'The lawful basis under GDPR Article 6 for processing the passengers personal data. While this product focuses on consent, other legal bases may apply for specific processing activities.. Valid values are `consent|contract|legal_obligation|vital_interest|public_task|legitimate_interest`',
    `minor_consent_flag` BOOLEAN COMMENT 'Boolean indicator of whether this consent record pertains to a minor (passenger under the age of consent in the applicable jurisdiction). Triggers additional parental consent and verification requirements under GDPR Article 8 and COPPA.',
    `modified_by_user` STRING COMMENT 'The identifier of the system user or automated process that last modified this consent record. Supports audit trail and accountability.',
    `notes` STRING COMMENT 'Free-text field for capturing additional context, exceptions, or special handling instructions related to this consent record. Used by customer service and compliance teams.',
    `opt_in_flag` BOOLEAN COMMENT 'Boolean indicator of whether the consent was obtained via opt-in (true) or opt-out (false) mechanism. GDPR requires opt-in for most marketing and profiling activities.',
    `parental_consent_verified_flag` BOOLEAN COMMENT 'Boolean indicator of whether parental or guardian consent has been verified for a minor passenger. Null if minor_consent_flag is false. Required for GDPR Article 8 and COPPA compliance.',
    `processing_purpose` STRING COMMENT 'The specific purpose for which the passengers data will be processed under this consent. Examples include marketing communications, service personalization, loyalty program analytics, or partner offers. Required for GDPR Article 13 transparency.',
    `renewal_due_date` DATE COMMENT 'The date by which the airline should proactively request consent renewal from the passenger. Used for consent lifecycle management and regulatory compliance in jurisdictions requiring periodic re-consent.',
    `source_system` STRING COMMENT 'The name or identifier of the source system or application that captured the consent record. Examples include Amadeus Altéa PSS, airline mobile app, loyalty portal, or third-party booking platform.',
    `text_snapshot` STRING COMMENT 'A snapshot or reference to the exact consent text presented to the passenger at the time of consent. Supports audit and dispute resolution by preserving the wording the passenger agreed to.',
    `third_party_sharing_scope` STRING COMMENT 'Description of the third-party entities or categories of entities with whom passenger data may be shared under this consent. Required for transparency under GDPR Article 13 and CCPA Section 1798.100(b).',
    `user_agent` STRING COMMENT 'The user agent string of the browser or application used by the passenger to provide consent. Supports technical audit and fraud detection.',
    `version` STRING COMMENT 'The version identifier of the privacy policy or consent terms that were in effect at the time the passenger granted consent. Enables tracking of consent under different policy versions and supports re-consent workflows when policies change.',
    `withdrawn_timestamp` TIMESTAMP COMMENT 'The date and time when the passenger withdrew their consent. Null if consent has not been withdrawn. Recorded in ISO 8601 format (yyyy-MM-ddTHH:mm:ss.SSSXXX). Required for right-to-erasure compliance.',
    CONSTRAINT pk_consent PRIMARY KEY(`consent_id`)
) COMMENT 'Manages passenger data privacy and consent records in compliance with GDPR, CCPA, PDPA, and other applicable data protection regulations. Captures consent type (marketing email, SMS, data sharing with partners, profiling, personalisation), consent status (granted, withdrawn, pending), consent channel (web, mobile app, call centre, airport kiosk), consent timestamp, consent version (policy version at time of grant), and jurisdiction. Provides the legal basis for data processing activities and supports right-to-erasure and data portability requests. Mandatory for DOT and EASA consumer protection compliance.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`minor_guardian` (
    `minor_guardian_id` BIGINT COMMENT 'Unique identifier for the minor-guardian relationship record. Primary key.',
    `member_id` BIGINT COMMENT 'Foreign key linking to crew.crew_member. Business justification: Unaccompanied minor programs require airlines to document which cabin crew member accepted custody of the child at departure and handover. Legal liability and duty-of-care mandate. Crew member signs h',
    `flight_leg_assignment_id` BIGINT COMMENT 'Foreign key linking to crew.flight_leg_assignment. Business justification: Unaccompanied minor (UM) regulatory compliance and post-flight audit trails require tracing the exact crew flight leg assignment under which a crew member accepted a minor. Links the UM handoff event ',
    `profile_id` BIGINT COMMENT 'Reference to the unaccompanied minor (UMNR) passenger. Links to the passenger master record.',
    `pnr_id` BIGINT COMMENT 'Foreign key linking to reservation.pnr. Business justification: Unaccompanied minor handling workflow: guardian authorization is specific to a travel booking. Linking to the PNR enables check-in validation, crew handoff processes, and regulatory compliance for una',
    `ticket_id` BIGINT COMMENT 'Foreign key linking to revenue.ticket. Business justification: Unaccompanied minor (UM) service fulfillment requires ground staff to match the guardian authorization record to the specific ticketed UM journey. Airlines UM handling procedures and liability docume',
    `authorization_document_expiry_date` DATE COMMENT 'Expiration date of the authorization document, if applicable. Ensures authorization is valid for the travel date.',
    `authorization_document_reference` STRING COMMENT 'Reference number or identifier of the authorization document. Used for audit trail and compliance verification.',
    `authorization_document_type` STRING COMMENT 'Type of legal authorization document provided to permit the minor to travel unaccompanied. Required for regulatory compliance and liability protection.. Valid values are `parental_consent|court_order|legal_guardianship|notarized_letter|airline_form|other`',
    `created_timestamp` TIMESTAMP COMMENT 'Timestamp when this guardian record was first created in the system. Part of the audit trail.',
    `dropoff_authorization_flag` BOOLEAN COMMENT 'Indicates whether this guardian is authorized to drop off the minor at the origin airport. True if authorized, False otherwise. Used for origin handover verification.',
    `effective_from_date` DATE COMMENT 'Start date from which this guardian authorization is valid. Supports time-bound guardianship arrangements.',
    `effective_to_date` DATE COMMENT 'End date until which this guardian authorization is valid. Null indicates open-ended authorization. Supports time-bound guardianship arrangements.',
    `guardian_address_line_1` STRING COMMENT 'Primary street address line for the guardian. Required for emergency contact and legal documentation.',
    `guardian_address_line_2` STRING COMMENT 'Secondary address line for the guardian (apartment, suite, unit number). Optional address component.',
    `guardian_alternate_phone_number` STRING COMMENT 'Secondary contact phone number for the guardian. Used as backup contact channel during UMNR service delivery.',
    `guardian_city` STRING COMMENT 'City or municipality of the guardian residence. Part of the complete contact address.',
    `guardian_country_code` STRING COMMENT 'Three-letter ISO country code of the guardian residence country (e.g., USA, CAN, GBR). Required for international UMNR services.. Valid values are `^[A-Z]{3}$`',
    `guardian_email_address` STRING COMMENT 'Email address of the guardian. Used for pre-flight notifications, service confirmations, and post-flight communication.. Valid values are `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$`',
    `guardian_first_name` STRING COMMENT 'First name or given name of the guardian. Used for identity verification during minor handover.',
    `guardian_full_name` STRING COMMENT 'Full legal name of the authorized guardian or escort responsible for the unaccompanied minor. Required for handover procedures at origin and destination.',
    `guardian_government_id_number` STRING COMMENT 'Identification number from the guardian government-issued document. Recorded for liability and handover audit trail.',
    `guardian_government_id_type` STRING COMMENT 'Type of government-issued identification document presented by the guardian for identity verification during minor handover.. Valid values are `passport|national_id|drivers_license|state_id|other`',
    `guardian_id_issuing_country` STRING COMMENT 'Three-letter ISO country code of the country that issued the guardian identification document (e.g., USA, GBR, CAN).. Valid values are `^[A-Z]{3}$`',
    `guardian_last_name` STRING COMMENT 'Last name or family name of the guardian. Used for identity verification during minor handover.',
    `guardian_phone_country_code` STRING COMMENT 'International dialing code for the guardian phone number (e.g., +1, +44, +971). Ensures correct routing for international UMNR services.. Valid values are `^+[0-9]{1,3}$`',
    `guardian_phone_number` STRING COMMENT 'Primary contact phone number for the guardian. Used for operational communication during UMNR service delivery and irregular operations (IROP).',
    `guardian_postal_code` STRING COMMENT 'Postal or ZIP code of the guardian residence. Used for address validation and emergency contact.',
    `guardian_role` STRING COMMENT 'Operational role of the guardian in the UMNR service workflow. Determines which airport handover procedures apply.. Valid values are `origin_dropoff|destination_pickup|both|emergency_contact`',
    `guardian_state_province` STRING COMMENT 'State, province, or administrative region of the guardian residence. Required for certain jurisdictions.',
    `guardianship_status` STRING COMMENT 'Current lifecycle status of the guardian authorization record. Determines whether the guardian can be used for active UMNR bookings.. Valid values are `active|inactive|expired|revoked|pending_verification`',
    `pickup_authorization_flag` BOOLEAN COMMENT 'Indicates whether this guardian is authorized to pick up the minor at the destination airport. True if authorized, False otherwise. Critical for ground handling handover procedures.',
    `relationship_to_minor` STRING COMMENT 'Nature of the relationship between the guardian and the unaccompanied minor. Determines authorization level and liability scope.. Valid values are `parent|legal_guardian|authorized_adult|grandparent|sibling|other_relative`',
    `source_system` STRING COMMENT 'Name of the operational system that created or last updated this guardian record (e.g., Amadeus Altéa, SITA Airport Management). Used for data lineage and troubleshooting.',
    `special_instructions` STRING COMMENT 'Free-text field for special handling instructions related to the guardian handover (e.g., custody arrangements, security concerns, language preferences). Used by ground handling staff.',
    `updated_timestamp` TIMESTAMP COMMENT 'Timestamp when this guardian record was last modified. Supports change tracking and audit compliance.',
    `verification_date` DATE COMMENT 'Date when the guardian identity and authorization documents were verified by airline staff. Part of the compliance audit trail.',
    `verification_status` STRING COMMENT 'Status of identity and authorization document verification for the guardian. Critical for compliance and liability management.. Valid values are `verified|pending|failed|not_required`',
    CONSTRAINT pk_minor_guardian PRIMARY KEY(`minor_guardian_id`)
) COMMENT 'Manages the relationship between unaccompanied minor (UMNR) passengers and their authorised guardians or escorts. Captures guardian full name, relationship to minor (parent, legal guardian, authorised adult), contact phone numbers, government-issued ID reference, authorisation document reference, pickup authorisation at destination, and the effective date range of the guardianship record. Required for UMNR service fulfilment, ground handling handover procedures, and liability compliance. Distinct from contact_detail — this entity carries legal authorisation and handover workflow data specific to minors.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`watchlist_check` (
    `watchlist_check_id` BIGINT COMMENT 'Primary key for watchlist_check',
    `checkin_session_id` BIGINT COMMENT 'Foreign key linking to airport.checkin_session. Business justification: Security and regulatory audit trails require linking each watchlist screening result to the specific check-in session that triggered it. Aviation security compliance (TSA, DHS) mandates traceability f',
    `station_id` BIGINT COMMENT 'Foreign key linking to airport.station. Business justification: APIS/watchlist regulatory screening is filed per departure station for border authority compliance reporting. Aviation security regulators require screening results traceable to the specific departure',
    `flight_inventory_id` BIGINT COMMENT 'Foreign key linking to inventory.flight_inventory. Business justification: TSA/border authority compliance mandates associating watchlist screening results with specific flight inventory records for denied boarding decisions, regulatory audit submissions, and post-departure ',
    `flight_leg_id` BIGINT COMMENT 'Foreign key linking to flight.flight_leg. Business justification: DHS Secure Flight and CBP APIS regulatory requirements mandate watchlist screening against a specific flight leg. Ground security and border authorities reference the exact operating flight for compli',
    `flight_number_id` BIGINT COMMENT 'Foreign key linking to route.flight_number. Business justification: Regulatory security screening (TSA, border authorities) requires watchlist checks to be tied to a specific flight number for APIS compliance reporting and audit trails. Aviation security operations ex',
    `profile_id` BIGINT COMMENT 'Reference to the passenger profile being screened.',
    `pnr_id` BIGINT COMMENT 'Foreign key linking to reservation.pnr. Business justification: Security compliance and TSA/border authority audit: watchlist checks are performed in the context of a specific booking. Linking to the PNR enables security compliance reporting, boarding denial workf',
    `ticket_id` BIGINT COMMENT 'Foreign key linking to revenue.ticket. Business justification: DHS/TSA security compliance requires linking watchlist screening outcomes to specific ticketed travel. Security operations and regulatory audit reports must demonstrate that every ticketed passenger w',
    `travel_identity_document_id` BIGINT COMMENT 'Foreign key linking to passenger.travel_identity_document. Business justification: Security watchlist screening is performed against a specific travel document — the document presented or on file for a given flight. Linking watchlist_check.travel_identity_document_id → travel_identi',
    `apis_submission_id` BIGINT COMMENT 'Foreign key linking to passenger.apis_submission. Business justification: Watchlist screening in airline operations is frequently triggered by or performed in conjunction with APIS data submission to border authorities. Linking watchlist_check.triggering_apis_submission_id ',
    `api_pnr_indicator` STRING COMMENT 'Indicates whether the screening was performed using API data, PNR data, or both.. Valid values are `API|PNR|BOTH`',
    `boarding_pass_issued` BOOLEAN COMMENT 'Indicates whether a boarding pass was issued following the watchlist check clearance.',
    `check_status` STRING COMMENT 'Current status of the watchlist check record in its lifecycle.. Valid values are `COMPLETED|IN_PROGRESS|FAILED|EXPIRED|CANCELLED`',
    `check_timestamp` TIMESTAMP COMMENT 'Date and time when the watchlist screening check was performed.',
    `created_timestamp` TIMESTAMP COMMENT 'Date and time when this watchlist check record was first created in the system.',
    `data_retention_date` DATE COMMENT 'Date when this watchlist check record must be purged per regulatory data retention requirements.',
    `expiry_timestamp` TIMESTAMP COMMENT 'Date and time when the watchlist check result expires and a new check must be performed.',
    `match_reason` STRING COMMENT 'Description of the reason for the match, including which passenger attributes triggered the screening alert.',
    `match_score` DECIMAL(18,2) COMMENT 'Numerical confidence score (0.00 to 100.00) indicating the likelihood of a true match when a potential match is detected.',
    `match_status` STRING COMMENT 'Result of the watchlist screening check indicating whether the passenger matched any watchlist entries.. Valid values are `CLEAR|POTENTIAL_MATCH|CONFIRMED_MATCH|RESOLVED|INHIBITED`',
    `regulatory_submission_reference` STRING COMMENT 'Reference number or identifier for the regulatory submission of screening results to TSA, EU authorities, or other governing bodies.',
    `resolution_action` STRING COMMENT 'Action taken to resolve a potential or confirmed match, including clearance, escalation, or denial.. Valid values are `CLEARED_BY_AGENT|REDRESS_NUMBER_APPLIED|DOCUMENT_VERIFICATION|ESCALATED_TO_SECURITY|BOARDING_DENIED|PENDING_REVIEW`',
    `resolution_notes` STRING COMMENT 'Free-text notes documenting the resolution process, verification steps, and outcome.',
    `resolution_timestamp` TIMESTAMP COMMENT 'Date and time when the watchlist match was resolved or cleared.',
    `screening_jurisdiction` STRING COMMENT 'Two or three-letter country or region code indicating the regulatory jurisdiction under which screening was performed.. Valid values are `^[A-Z]{2,3}$`',
    `screening_program` STRING COMMENT 'The regulatory or security program under which the watchlist check was performed.. Valid values are `TSA_SECURE_FLIGHT|OFAC_SANCTIONS|INTERPOL_NOTICE|EU_PNR_DIRECTIVE|NATIONAL_NO_FLY|CUSTOMS_WATCHLIST`',
    `screening_system` STRING COMMENT 'Name or identifier of the automated screening system that performed the watchlist check.',
    `screening_version` STRING COMMENT 'Version number of the screening algorithm or watchlist data used for the check.',
    `selectee_indicator` BOOLEAN COMMENT 'Indicates whether the passenger was designated for enhanced secondary screening (SSSS - Secondary Security Screening Selection).',
    `submission_timestamp` TIMESTAMP COMMENT 'Date and time when screening results were submitted to the regulatory authority.',
    `updated_timestamp` TIMESTAMP COMMENT 'Date and time when this watchlist check record was last modified.',
    `watchlist_name` STRING COMMENT 'Name or identifier of the specific watchlist that triggered a match (e.g., No Fly List, Selectee List, OFAC SDN List).',
    CONSTRAINT pk_watchlist_check PRIMARY KEY(`watchlist_check_id`)
) COMMENT 'Records the results of security watchlist screening checks performed against a passenger profile — covering TSA Secure Flight, OFAC sanctions screening, Interpol notices, and national no-fly list checks. Captures check timestamp, screening programme (Secure Flight, OFAC, EU PNR Directive, etc.), match status (clear, potential match, confirmed match, resolved), resolution action, resolving officer ID, and regulatory submission reference. Mandatory for TSA Secure Flight compliance on US-bound flights and EU PNR Directive compliance on EU-bound flights. Distinct from redress_record — this captures the screening event, not the resolution credential.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`apis_submission` (
    `apis_submission_id` BIGINT COMMENT 'Unique identifier for the APIS submission record. Primary key.',
    `aircraft_id` BIGINT COMMENT 'Foreign key linking to fleet.aircraft. Business justification: APIS regulatory submissions to border authorities (CBP, EU, UK Home Office) require aircraft tail number and registration details. A direct FK to fleet.aircraft enables the APIS system to retrieve tai',
    `booking_passenger_id` BIGINT COMMENT 'Foreign key linking to reservation.reservation_booking_passenger. Business justification: APIS data completeness tracking: APIS submissions are per-passenger per-booking; linking to reservation_booking_passenger enables direct update of apis_data_complete_flag, supports check-in eligibilit',
    `station_id` BIGINT COMMENT 'Foreign key linking to airport.station. Business justification: APIS submissions are filed per departure station to the relevant border authority. Regulatory compliance reporting and audit trails require linking each APIS submission to the originating station. dep',
    `flight_inventory_id` BIGINT COMMENT 'Foreign key linking to inventory.flight_inventory. Business justification: APIS submissions are regulatory filings tied to specific flight inventory instances for border control. Customs authorities require passenger manifests linked to exact operating flights. Mandatory com',
    `flight_leg_id` BIGINT COMMENT 'Reference to the specific flight leg for which APIS data was submitted to border control authorities.',
    `flight_number_id` BIGINT COMMENT 'Foreign key linking to route.flight_number. Business justification: APIS regulatory submissions to border authorities are filed per flight number per carrier. Compliance reporting, resubmission tracking, and authority response reconciliation all require linking the su',
    `original_submission_apis_submission_id` BIGINT COMMENT 'Reference to the original APIS submission record if this is a resubmission or correction. Null for original submissions.',
    `profile_id` BIGINT COMMENT 'Reference to the passenger whose travel document data was submitted to border control authorities.',
    `pnr_id` BIGINT COMMENT 'Foreign key linking to reservation.pnr. Business justification: APIS regulatory compliance: APIS submissions are made per booking/PNR for border authority reporting. Linking to the PNR enables compliance tracking, resubmission workflows, and authority response rec',
    `ticket_id` BIGINT COMMENT 'Foreign key linking to revenue.ticket. Business justification: APIS regulatory filings must be reconcilable to specific ticketed passengers. Border authorities require airlines to demonstrate APIS data matches ticketed travel. Compliance auditors and APIS reconci',
    `travel_identity_document_id` BIGINT COMMENT 'Foreign key linking to passenger.travel_identity_document. Business justification: APIS submissions transmit passenger identity and travel document data to border control authorities. The apis_submission table currently duplicates document_number, document_type, document_expiry_date',
    `arrival_airport_code` STRING COMMENT 'Three-letter IATA airport code of the arrival airport for the flight leg associated with this APIS submission.. Valid values are `^[A-Z]{3}$`',
    `authority_response_code` STRING COMMENT 'Response code returned by the border control authority indicating acceptance, rejection reason, or error condition. Codes vary by authority (e.g., CBP response codes, UKBF codes).',
    `authority_response_message` STRING COMMENT 'Human-readable message returned by the border control authority providing additional detail on the submission outcome or rejection reason.',
    `authority_response_timestamp` TIMESTAMP COMMENT 'Date and time when the border control authority returned a response to the APIS submission.',
    `border_authority_code` STRING COMMENT 'Code identifying the specific border control authority that received the submission (e.g., CBP for US Customs and Border Protection, UKBF for UK Border Force, EES for EU Entry/Exit System).',
    `compliance_mandate` STRING COMMENT 'The specific regulatory mandate or legal requirement under which this APIS submission was made (e.g., US CBP APIS Final Rule, EU Entry/Exit System Regulation 2017/2226, ICAO Annex 9 Standard 3.47).',
    `created_timestamp` TIMESTAMP COMMENT 'Date and time when this APIS submission record was first created in the data platform.',
    `destination_country_code` STRING COMMENT 'Three-letter ISO 3166-1 alpha-3 code of the destination country whose border control authority received the APIS submission.. Valid values are `^[A-Z]{3}$`',
    `message_reference_number` STRING COMMENT 'Unique reference number assigned to the APIS transmission message by the sending system or border control authority for tracking and reconciliation purposes.',
    `resubmission_flag` BOOLEAN COMMENT 'Indicates whether this submission is a resubmission of previously rejected or corrected APIS data (True) or an original submission (False).',
    `scheduled_arrival_timestamp` TIMESTAMP COMMENT 'Scheduled arrival date and time of the flight leg for which APIS data was submitted.',
    `scheduled_departure_timestamp` TIMESTAMP COMMENT 'Scheduled departure date and time of the flight leg for which APIS data was submitted.',
    `submission_channel` STRING COMMENT 'Technical channel or interface used to transmit the APIS data (e.g., SITA Type B message, XML web service, EDI, proprietary API).',
    `submission_method` STRING COMMENT 'Method by which the APIS data was submitted to border control authorities: automated (system-triggered), manual (agent-initiated), batch (scheduled bulk transmission), real_time (interactive submission).. Valid values are `automated|manual|batch|real_time`',
    `submission_source_system` STRING COMMENT 'Name or code of the operational system that generated and transmitted the APIS submission (e.g., Amadeus Altéa DCS, Sabre AirCentre, SITA Horizon).',
    `submission_status` STRING COMMENT 'Current lifecycle status of the APIS submission: pending (awaiting authority response), accepted (approved by border control), rejected (denied by border control), error (technical transmission failure), cancelled (submission withdrawn).. Valid values are `pending|accepted|rejected|error|cancelled`',
    `submission_timestamp` TIMESTAMP COMMENT 'Date and time when the APIS data was transmitted to the destination country border control authority. This is the principal business event timestamp for the submission.',
    `updated_timestamp` TIMESTAMP COMMENT 'Date and time when this APIS submission record was last modified in the data platform.',
    CONSTRAINT pk_apis_submission PRIMARY KEY(`apis_submission_id`)
) COMMENT 'Transactional records of Advance Passenger Information System (APIS) data submissions to border control authorities — capturing the submission timestamp, destination country authority (CBP, UK Border Force, EU Entry/Exit System, etc.), submission status (pending, accepted, rejected, error), passenger travel document data snapshot at time of submission, flight reference, and authority response code. Required for regulatory compliance on international routes under ICAO Annex 9, US CBP APIS, and EU Entry/Exit System mandates. Distinct from travel_document (the master record) — this captures the regulatory submission event.';

CREATE OR REPLACE TABLE `airlines_ecm`.`passenger`.`accessibility_profile` (
    `accessibility_profile_id` BIGINT COMMENT 'Unique identifier for the accessibility profile record. Primary key.',
    `cabin_class_id` BIGINT COMMENT 'Foreign key linking to inventory.cabin_class. Business justification: Accessibility requirements (stretcher, wheelchair type) determine cabin class eligibility and seating restrictions. Operations must validate PRM requests against cabin configurations for safety compli',
    `mel_item_id` BIGINT COMMENT 'Foreign key linking to maintenance.mel_item. Business justification: PRM/accessibility pre-flight compliance: when a passenger requires onboard oxygen, stretcher, or specific mobility equipment, the airline must verify the governing MEL item is serviceable before accep',
    `profile_id` BIGINT COMMENT 'Reference to the passenger who owns this accessibility profile. Links to the passenger master record.',
    `seat_product_id` BIGINT COMMENT 'Foreign key linking to ancillary.seat_product. Business justification: PRM (Persons with Reduced Mobility) seat pre-assignment process: accessibility profiles mandate specific seat product types (bulkhead, aisle, no-exit-row). Check-in and seat assignment systems use thi',
    `ambulatory_status` STRING COMMENT 'Passengers ability to walk and move independently. Determines boarding method, seating restrictions, and emergency evacuation capability.. Valid values are `fully_ambulatory|partially_ambulatory|non_ambulatory|stretcher_required`',
    `assistance_at_arrival_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires ground handling assistance at arrival airport (deplaning, baggage claim, customs, onward connection). Triggers PRM service request to ground handler.',
    `assistance_at_departure_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires ground handling assistance at departure airport (check-in, security, gate, boarding). Triggers PRM service request to ground handler.',
    `assistance_at_transit_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires ground handling assistance during transit or connection. Ensures continuity of care between flights.',
    `boarding_method_preference` STRING COMMENT 'Preferred method for boarding the aircraft. Pre-board allows extra time; ambulift is a hydraulic lift vehicle; aisle chair is a narrow wheelchair for aircraft aisle; carry-onboard means passenger is carried by assistance personnel.. Valid values are `pre_board|ambulift|aisle_chair|carry_onboard|standard`',
    `cognitive_assistance_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires cognitive or developmental disability assistance. May require simplified instructions, extra time, or companion support.',
    `companion_traveler_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger is required to travel with a companion or safety assistant due to the severity of their disability. May be mandated by airline medical policy.',
    `created_timestamp` TIMESTAMP COMMENT 'Timestamp when this accessibility profile record was first created in the system. Immutable audit field.',
    `hearing_impairment_level` STRING COMMENT 'Degree of hearing impairment. Determines need for visual safety briefings, written communication, and assistive listening devices.. Valid values are `none|mild|moderate|severe|profound`',
    `last_verified_date` DATE COMMENT 'Date when the accessibility profile information was last verified or updated by the passenger or airline staff. Used for data quality and compliance auditing.',
    `medical_clearance_expiry_date` DATE COMMENT 'Date until which the medical clearance (MEDIF) is valid. Passenger cannot travel after this date without renewed clearance.',
    `medical_clearance_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires medical clearance (MEDIF form) from airline medical services before travel. Triggered by certain medical conditions or equipment.',
    `medical_equipment_carried` STRING COMMENT 'Description of medical equipment the passenger carries onboard (CPAP, portable oxygen concentrator, nebulizer, insulin pump). Free-text field for crew awareness and stowage planning.',
    `mobility_aid_battery_type` STRING COMMENT 'Type of battery powering the mobility aid device. Critical for dangerous goods compliance and cargo hold safety. Lithium-ion batteries have specific IATA DGR restrictions.. Valid values are `lithium_ion|dry_cell|wet_cell|none|unknown`',
    `mobility_aid_battery_watt_hours` DECIMAL(18,2) COMMENT 'Energy capacity of the mobility aid battery in watt-hours. Required for lithium battery compliance checks per IATA DGR (batteries over 300Wh require special handling).',
    `mobility_aid_foldable_flag` BOOLEAN COMMENT 'Indicates whether the mobility aid device can be folded or disassembled for stowage. Affects cargo hold space allocation and handling procedures.',
    `mobility_aid_height_cm` DECIMAL(18,2) COMMENT 'Height dimension of the mobility aid device in centimeters. Used to determine cargo hold compatibility and stowage location.',
    `mobility_aid_length_cm` DECIMAL(18,2) COMMENT 'Length dimension of the mobility aid device in centimeters. Used to determine cargo hold compatibility and stowage location.',
    `mobility_aid_type` STRING COMMENT 'Type of mobility aid device used by the passenger. Determines handling and stowage requirements. [ENUM-REF-CANDIDATE: manual_wheelchair|electric_wheelchair|mobility_scooter|walker|cane|crutches|prosthetic|none — 8 candidates stripped; promote to reference product]',
    `mobility_aid_weight_kg` DECIMAL(18,2) COMMENT 'Weight of the mobility aid device in kilograms. Required for cargo hold planning and aircraft weight and balance calculations.',
    `mobility_aid_width_cm` DECIMAL(18,2) COMMENT 'Width dimension of the mobility aid device in centimeters. Used to determine cargo hold compatibility and stowage location.',
    `oxygen_flow_rate_lpm` DECIMAL(18,2) COMMENT 'Prescribed oxygen flow rate in liters per minute. Required for aircraft oxygen system configuration and medical clearance.',
    `oxygen_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires supplemental oxygen during flight. Requires advance coordination with medical services and aircraft equipment availability.',
    `preferred_seating_location` STRING COMMENT 'Passengers preferred seating location based on accessibility needs. Bulkhead seats provide extra space for mobility aids; aisle seats facilitate lavatory access.. Valid values are `bulkhead|aisle|window|near_lavatory|extra_legroom|no_preference`',
    `prm_category` STRING COMMENT 'IATA standard PRM category code. WCHR=wheelchair for ramp, WCHS=wheelchair for stairs, WCHC=wheelchair for cabin seat, customerD=dry cell battery wheelchair, customerW=wet cell battery wheelchair, WCMP=manual wheelchair, BLND=blind, DEAF=deaf, DPNA=disabled passenger needing assistance, MAAS=meet and assist. [ENUM-REF-CANDIDATE: WCHR|WCHS|WCHC|customerD|customerW|WCMP|BLND|DEAF|DPNA|MAAS — 10 candidates stripped; promote to reference product]',
    `profile_effective_from_date` DATE COMMENT 'Date from which this accessibility profile becomes effective and can be used for booking and SSR generation.',
    `profile_effective_to_date` DATE COMMENT 'Date until which this accessibility profile remains valid. Nullable for indefinite profiles; populated for time-limited medical clearances.',
    `profile_status` STRING COMMENT 'Current lifecycle status of the accessibility profile. Active profiles are used for SSR generation; expired profiles require renewal of medical documentation.. Valid values are `active|inactive|expired|pending_verification`',
    `seating_restriction_notes` STRING COMMENT 'Free-text notes on seating restrictions or requirements (e.g., cannot sit in exit row, requires adjacent seat for companion, needs armrest removal). Used by inventory and departure control systems.',
    `service_animal_flag` BOOLEAN COMMENT 'Indicates whether the passenger travels with a trained service animal (guide dog, hearing dog, psychiatric service animal). Requires cabin accommodation and documentation.',
    `service_animal_type` STRING COMMENT 'Type of trained service animal accompanying the passenger. Determines seating location and cabin crew briefing requirements.. Valid values are `guide_dog|hearing_dog|psychiatric_service_dog|mobility_assistance_dog|other|none`',
    `source_system` STRING COMMENT 'Name of the operational system that created or last updated this accessibility profile record (e.g., Amadeus Altéa PSS, airport kiosk, mobile app, call center CRM).',
    `special_instructions` STRING COMMENT 'Free-text field for additional accessibility instructions, preferences, or notes that do not fit structured fields. Visible to ground handlers and cabin crew.',
    `stretcher_required_flag` BOOLEAN COMMENT 'Indicates whether the passenger requires stretcher accommodation. Requires removal of multiple seat rows and advance aircraft configuration.',
    `updated_timestamp` TIMESTAMP COMMENT 'Timestamp when this accessibility profile record was last modified. Updated on every change for audit trail and data freshness tracking.',
    `visual_impairment_level` STRING COMMENT 'Degree of visual impairment. Determines need for sighted guide, Braille materials, audio announcements, and service animal accommodation.. Valid values are `none|low_vision|legally_blind|totally_blind`',
    CONSTRAINT pk_accessibility_profile PRIMARY KEY(`accessibility_profile_id`)
) COMMENT 'Dedicated master record for passengers with disabilities or reduced mobility (PRM — Passengers with Reduced Mobility) — capturing mobility aid type (manual wheelchair, electric wheelchair, mobility scooter), dimensions and weight of mobility aid, battery type (lithium-ion, dry cell) for cargo hold compliance, ambulatory status, visual impairment level, hearing impairment level, cognitive assistance requirements, medical equipment carried (CPAP, oxygen concentrator), and preferred assistance workflow at each journey touchpoint (check-in, security, gate, boarding, deplaning). Aligns with IATA PRM Handling Guidelines and EU Regulation 1107/2006. Distinct from ssr_record — this is the persistent profile, not the per-flight SSR instance.';

-- ========= FOREIGN KEYS =========
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ADD CONSTRAINT `fk_passenger_travel_identity_document_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ADD CONSTRAINT `fk_passenger_contact_detail_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ADD CONSTRAINT `fk_passenger_ssr_record_accessibility_profile_id` FOREIGN KEY (`accessibility_profile_id`) REFERENCES `airlines_ecm`.`passenger`.`accessibility_profile`(`accessibility_profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ADD CONSTRAINT `fk_passenger_ssr_record_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ADD CONSTRAINT `fk_passenger_loyalty_linkage_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ADD CONSTRAINT `fk_passenger_traveller_segment_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ADD CONSTRAINT `fk_passenger_consent_minor_guardian_id` FOREIGN KEY (`minor_guardian_id`) REFERENCES `airlines_ecm`.`passenger`.`minor_guardian`(`minor_guardian_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ADD CONSTRAINT `fk_passenger_consent_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ADD CONSTRAINT `fk_passenger_minor_guardian_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ADD CONSTRAINT `fk_passenger_watchlist_check_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ADD CONSTRAINT `fk_passenger_watchlist_check_travel_identity_document_id` FOREIGN KEY (`travel_identity_document_id`) REFERENCES `airlines_ecm`.`passenger`.`travel_identity_document`(`travel_identity_document_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ADD CONSTRAINT `fk_passenger_watchlist_check_apis_submission_id` FOREIGN KEY (`apis_submission_id`) REFERENCES `airlines_ecm`.`passenger`.`apis_submission`(`apis_submission_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ADD CONSTRAINT `fk_passenger_apis_submission_original_submission_apis_submission_id` FOREIGN KEY (`original_submission_apis_submission_id`) REFERENCES `airlines_ecm`.`passenger`.`apis_submission`(`apis_submission_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ADD CONSTRAINT `fk_passenger_apis_submission_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ADD CONSTRAINT `fk_passenger_apis_submission_travel_identity_document_id` FOREIGN KEY (`travel_identity_document_id`) REFERENCES `airlines_ecm`.`passenger`.`travel_identity_document`(`travel_identity_document_id`);
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ADD CONSTRAINT `fk_passenger_accessibility_profile_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `airlines_ecm`.`passenger`.`profile`(`profile_id`);

-- ========= TAGS =========
ALTER SCHEMA `airlines_ecm`.`passenger` SET TAGS ('dbx_division' = 'business');
ALTER SCHEMA `airlines_ecm`.`passenger` SET TAGS ('dbx_domain' = 'passenger');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` SET TAGS ('dbx_subdomain' = 'passenger_identity');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Profile Identifier');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_business_glossary_term' = 'Frequent Flyer Program (FFP) Member ID');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `city_pair_id` SET TAGS ('dbx_business_glossary_term' = 'Preferred City Pair Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `accessibility_requirements` SET TAGS ('dbx_business_glossary_term' = 'Accessibility Requirements');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `accessibility_requirements` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `accessibility_requirements` SET TAGS ('dbx_pii_health' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `completeness_score` SET TAGS ('dbx_business_glossary_term' = 'Profile Completeness Score');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `country_of_residence` SET TAGS ('dbx_business_glossary_term' = 'Passenger Country of Residence');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `country_of_residence` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Profile Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `creation_source` SET TAGS ('dbx_business_glossary_term' = 'Profile Creation Source');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `creation_source` SET TAGS ('dbx_value_regex' = 'altea_pss|web|mobile|gds|call_center|airport_kiosk');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `customer_segment` SET TAGS ('dbx_business_glossary_term' = 'Customer Segment');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `data_sharing_consent` SET TAGS ('dbx_business_glossary_term' = 'Data Sharing Consent Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_business_glossary_term' = 'Passenger Date of Birth');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_pii_dob' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_name` SET TAGS ('dbx_business_glossary_term' = 'Emergency Contact Name');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_phone` SET TAGS ('dbx_business_glossary_term' = 'Emergency Contact Phone Number');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_phone` SET TAGS ('dbx_value_regex' = '^+?[1-9]d{1,14}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_phone` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_phone` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_relationship` SET TAGS ('dbx_business_glossary_term' = 'Emergency Contact Relationship');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `emergency_contact_relationship` SET TAGS ('dbx_value_regex' = 'spouse|parent|child|sibling|friend|other');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `first_name` SET TAGS ('dbx_business_glossary_term' = 'Passenger First Name');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `first_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `first_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `gender` SET TAGS ('dbx_business_glossary_term' = 'Passenger Gender');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `gender` SET TAGS ('dbx_value_regex' = 'M|F|X|U');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `gender` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `gender` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `known_traveler_number` SET TAGS ('dbx_business_glossary_term' = 'Known Traveler Number (KTN)');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `known_traveler_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `known_traveler_number` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `last_name` SET TAGS ('dbx_business_glossary_term' = 'Passenger Last Name');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `last_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `last_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `marketing_opt_in` SET TAGS ('dbx_business_glossary_term' = 'Marketing Opt-In Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `meal_preference` SET TAGS ('dbx_business_glossary_term' = 'Meal Preference Code');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `middle_name` SET TAGS ('dbx_business_glossary_term' = 'Passenger Middle Name');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `middle_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `middle_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `nationality` SET TAGS ('dbx_business_glossary_term' = 'Passenger Nationality');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `nationality` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `nationality` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `nationality` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `passenger_type` SET TAGS ('dbx_business_glossary_term' = 'Passenger Type Code');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `passenger_type` SET TAGS ('dbx_value_regex' = 'ADT|CHD|INF|UMN');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `preferred_language` SET TAGS ('dbx_business_glossary_term' = 'Passenger Preferred Language');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `preferred_language` SET TAGS ('dbx_value_regex' = '^[a-z]{2}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_email` SET TAGS ('dbx_business_glossary_term' = 'Primary Email Address');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_email` SET TAGS ('dbx_value_regex' = '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_email` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_email` SET TAGS ('dbx_pii_email' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_phone` SET TAGS ('dbx_business_glossary_term' = 'Primary Phone Number');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_phone` SET TAGS ('dbx_value_regex' = '^+?[1-9]d{1,14}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_phone` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `primary_phone` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `profile_status` SET TAGS ('dbx_business_glossary_term' = 'Profile Status');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `profile_status` SET TAGS ('dbx_value_regex' = 'active|inactive|suspended|merged|deceased');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `redress_number` SET TAGS ('dbx_business_glossary_term' = 'Redress Number');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `redress_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `redress_number` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `seat_preference` SET TAGS ('dbx_business_glossary_term' = 'Seat Preference');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `seat_preference` SET TAGS ('dbx_value_regex' = 'window|aisle|middle|no_preference');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `suffix` SET TAGS ('dbx_business_glossary_term' = 'Passenger Name Suffix');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `title` SET TAGS ('dbx_business_glossary_term' = 'Passenger Title');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `title` SET TAGS ('dbx_value_regex' = 'Mr|Mrs|Ms|Miss|Dr|Prof');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_name` SET TAGS ('dbx_business_glossary_term' = 'Unaccompanied Minor (UMN) Guardian Name');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_phone` SET TAGS ('dbx_business_glossary_term' = 'Unaccompanied Minor (UMN) Guardian Phone');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_phone` SET TAGS ('dbx_value_regex' = '^+?[1-9]d{1,14}$');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_phone` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `unaccompanied_minor_guardian_phone` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Profile Last Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`profile` ALTER COLUMN `vip_indicator` SET TAGS ('dbx_business_glossary_term' = 'VIP Indicator Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` SET TAGS ('dbx_subdomain' = 'passenger_identity');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `travel_identity_document_id` SET TAGS ('dbx_business_glossary_term' = 'Travel Identity Document ID');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `apis_response_code` SET TAGS ('dbx_business_glossary_term' = 'APIS (Advance Passenger Information System) Response Code');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `apis_transmission_timestamp` SET TAGS ('dbx_business_glossary_term' = 'APIS (Advance Passenger Information System) Transmission Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `apis_transmitted_flag` SET TAGS ('dbx_business_glossary_term' = 'APIS (Advance Passenger Information System) Transmitted Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_business_glossary_term' = 'Date of Birth');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_pii_dob' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_image_url` SET TAGS ('dbx_business_glossary_term' = 'Document Image URL');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_image_url` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_image_url` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_number` SET TAGS ('dbx_business_glossary_term' = 'Document Number');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_number` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_source` SET TAGS ('dbx_business_glossary_term' = 'Document Source');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_source` SET TAGS ('dbx_value_regex' = 'manual_entry|ocr_scan|mobile_app|gds|api_integration');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_type` SET TAGS ('dbx_business_glossary_term' = 'Document Type');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `document_type` SET TAGS ('dbx_value_regex' = 'passport|national_id|visa|residence_permit|refugee_travel_document|stateless_person_document');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `expiry_date` SET TAGS ('dbx_business_glossary_term' = 'Expiry Date');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `gender` SET TAGS ('dbx_business_glossary_term' = 'Gender');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `gender` SET TAGS ('dbx_value_regex' = 'M|F|X');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `gender` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `gender` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `given_names` SET TAGS ('dbx_business_glossary_term' = 'Given Names');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `given_names` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `given_names` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `is_primary_document` SET TAGS ('dbx_business_glossary_term' = 'Is Primary Document');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `issue_date` SET TAGS ('dbx_business_glossary_term' = 'Issue Date');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `issuing_authority` SET TAGS ('dbx_business_glossary_term' = 'Issuing Authority');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `issuing_country_code` SET TAGS ('dbx_business_glossary_term' = 'Issuing Country Code');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `issuing_country_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `known_traveller_number` SET TAGS ('dbx_business_glossary_term' = 'Known Traveller Number');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `known_traveller_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `known_traveller_number` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `known_traveller_program` SET TAGS ('dbx_business_glossary_term' = 'Known Traveller Program');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `known_traveller_program` SET TAGS ('dbx_value_regex' = 'TSA_PRECHECK|GLOBAL_ENTRY|NEXUS|SENTRI|APEC_BUSINESS_TRAVEL_CARD|CLEAR');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `last_used_flight_date` SET TAGS ('dbx_business_glossary_term' = 'Last Used Flight Date');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line1` SET TAGS ('dbx_business_glossary_term' = 'Machine Readable Zone (MRZ) Line 1');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line1` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line1` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line2` SET TAGS ('dbx_business_glossary_term' = 'Machine Readable Zone (MRZ) Line 2');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line2` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line2` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line3` SET TAGS ('dbx_business_glossary_term' = 'Machine Readable Zone (MRZ) Line 3');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line3` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `mrz_line3` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `nationality_code` SET TAGS ('dbx_business_glossary_term' = 'Nationality Code');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `nationality_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `nationality_code` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `nationality_code` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `notes` SET TAGS ('dbx_business_glossary_term' = 'Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `place_of_birth` SET TAGS ('dbx_business_glossary_term' = 'Place of Birth');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `place_of_birth` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `place_of_birth` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `redress_number` SET TAGS ('dbx_business_glossary_term' = 'Redress Number');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `redress_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `redress_number` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `secure_flight_status` SET TAGS ('dbx_business_glossary_term' = 'Secure Flight Status');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `secure_flight_status` SET TAGS ('dbx_value_regex' = 'not_submitted|cleared|inhibited|conditional');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `surname` SET TAGS ('dbx_business_glossary_term' = 'Surname');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `surname` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `surname` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `verification_status` SET TAGS ('dbx_business_glossary_term' = 'Verification Status');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `verification_status` SET TAGS ('dbx_value_regex' = 'not_verified|verified|failed|expired|flagged');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `verification_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Verification Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `verified_by` SET TAGS ('dbx_business_glossary_term' = 'Verified By');
ALTER TABLE `airlines_ecm`.`passenger`.`travel_identity_document` ALTER COLUMN `visa_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Visa Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` SET TAGS ('dbx_subdomain' = 'passenger_identity');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_detail_id` SET TAGS ('dbx_business_glossary_term' = 'Contact Detail ID');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `address_line_1` SET TAGS ('dbx_business_glossary_term' = 'Address Line 1');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `address_line_1` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `address_line_1` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `address_line_2` SET TAGS ('dbx_business_glossary_term' = 'Address Line 2');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `address_line_2` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `address_line_2` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `city` SET TAGS ('dbx_business_glossary_term' = 'City');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `city` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `city` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_channel` SET TAGS ('dbx_business_glossary_term' = 'Contact Channel');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_channel` SET TAGS ('dbx_value_regex' = 'voice|sms|email|postal|whatsapp|app_notification');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_status` SET TAGS ('dbx_business_glossary_term' = 'Contact Status');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_status` SET TAGS ('dbx_value_regex' = 'active|inactive|bounced|invalid|pending_verification');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_type` SET TAGS ('dbx_business_glossary_term' = 'Contact Type');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `contact_type` SET TAGS ('dbx_value_regex' = 'email|mobile|home_phone|work_phone|postal_address|emergency');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `country_code` SET TAGS ('dbx_business_glossary_term' = 'Country Code');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `country_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `effective_from_date` SET TAGS ('dbx_business_glossary_term' = 'Effective From Date');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `effective_to_date` SET TAGS ('dbx_business_glossary_term' = 'Effective To Date');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `email_address` SET TAGS ('dbx_business_glossary_term' = 'Email Address');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `email_address` SET TAGS ('dbx_value_regex' = '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `email_address` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `email_address` SET TAGS ('dbx_pii_email' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `emergency_contact_name` SET TAGS ('dbx_business_glossary_term' = 'Emergency Contact Name');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `emergency_contact_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `emergency_contact_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `emergency_contact_relationship` SET TAGS ('dbx_business_glossary_term' = 'Emergency Contact Relationship');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `emergency_contact_relationship` SET TAGS ('dbx_value_regex' = 'spouse|parent|child|sibling|friend|other');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `is_preferred` SET TAGS ('dbx_business_glossary_term' = 'Is Preferred Contact');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `is_verified` SET TAGS ('dbx_business_glossary_term' = 'Is Verified');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `last_used_date` SET TAGS ('dbx_business_glossary_term' = 'Last Used Date');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `opt_in_date` SET TAGS ('dbx_business_glossary_term' = 'Opt-In Date');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `opt_in_marketing` SET TAGS ('dbx_business_glossary_term' = 'Opt-In Marketing');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `opt_in_operational` SET TAGS ('dbx_business_glossary_term' = 'Opt-In Operational');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `opt_out_date` SET TAGS ('dbx_business_glossary_term' = 'Opt-Out Date');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_country_code` SET TAGS ('dbx_business_glossary_term' = 'Phone Country Code');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_country_code` SET TAGS ('dbx_value_regex' = '^+?[1-9]d{0,3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_country_code` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_country_code` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_number` SET TAGS ('dbx_business_glossary_term' = 'Phone Number');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_number` SET TAGS ('dbx_value_regex' = '^+?[1-9]d{1,14}$');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `phone_number` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `postal_code` SET TAGS ('dbx_business_glossary_term' = 'Postal Code');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `postal_code` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `postal_code` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `source_system` SET TAGS ('dbx_business_glossary_term' = 'Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `state_province` SET TAGS ('dbx_business_glossary_term' = 'State or Province');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `state_province` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `state_province` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`contact_detail` ALTER COLUMN `verification_date` SET TAGS ('dbx_business_glossary_term' = 'Verification Date');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` SET TAGS ('dbx_subdomain' = 'service_preferences');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_record_id` SET TAGS ('dbx_business_glossary_term' = 'Special Service Request (SSR) Record ID');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `accessibility_profile_id` SET TAGS ('dbx_business_glossary_term' = 'Accessibility Profile Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ancillary_emd_id` SET TAGS ('dbx_business_glossary_term' = 'Ancillary Emd Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `cabin_class_id` SET TAGS ('dbx_business_glossary_term' = 'Cabin Class Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `cost_centre_id` SET TAGS ('dbx_business_glossary_term' = 'Cost Centre Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_business_glossary_term' = 'Ffp Member Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `flight_inventory_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Inventory Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `flight_leg_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Leg ID');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `member_id` SET TAGS ('dbx_business_glossary_term' = 'Handling Crew Member Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `member_id` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `member_id` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `mel_item_id` SET TAGS ('dbx_business_glossary_term' = 'Mel Item Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `member_benefit_id` SET TAGS ('dbx_business_glossary_term' = 'Member Benefit Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `carrier_id` SET TAGS ('dbx_business_glossary_term' = 'Operating Carrier Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `pnr_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger Name Record (PNR) ID');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `product_catalog_id` SET TAGS ('dbx_business_glossary_term' = 'Product Catalog Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `route_id` SET TAGS ('dbx_business_glossary_term' = 'Route Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `advance_notice_hours` SET TAGS ('dbx_business_glossary_term' = 'Advance Notice Hours');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `booking_channel` SET TAGS ('dbx_business_glossary_term' = 'Booking Channel');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `cancellation_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Cancellation Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `charge_amount` SET TAGS ('dbx_business_glossary_term' = 'Charge Amount');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `charge_currency_code` SET TAGS ('dbx_business_glossary_term' = 'Charge Currency Code');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `charge_currency_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `confirmation_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Confirmation Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `equipment_required` SET TAGS ('dbx_business_glossary_term' = 'Equipment Required');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `fulfillment_notes` SET TAGS ('dbx_business_glossary_term' = 'Fulfillment Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `handling_instructions` SET TAGS ('dbx_business_glossary_term' = 'Handling Instructions');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `is_chargeable` SET TAGS ('dbx_business_glossary_term' = 'Is Chargeable Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `is_interline` SET TAGS ('dbx_business_glossary_term' = 'Is Interline Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `is_standing_preference` SET TAGS ('dbx_business_glossary_term' = 'Is Standing Preference Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `meal_code` SET TAGS ('dbx_business_glossary_term' = 'Meal Code');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `meal_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{4}$');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `medical_clearance_status` SET TAGS ('dbx_business_glossary_term' = 'Medical Clearance Status');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `medical_clearance_status` SET TAGS ('dbx_value_regex' = 'not_required|pending|approved|denied');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `medical_clearance_status` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `medical_clearance_status` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `request_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Request Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `requires_advance_notice` SET TAGS ('dbx_business_glossary_term' = 'Requires Advance Notice Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `requires_medical_clearance` SET TAGS ('dbx_business_glossary_term' = 'Requires Medical Clearance Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `requires_medical_clearance` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `requires_medical_clearance` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `service_delivery_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Service Delivery Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_category` SET TAGS ('dbx_business_glossary_term' = 'Special Service Request (SSR) Category');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_code` SET TAGS ('dbx_business_glossary_term' = 'Special Service Request (SSR) Code');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{4}$');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_description` SET TAGS ('dbx_business_glossary_term' = 'Special Service Request (SSR) Description');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_status` SET TAGS ('dbx_business_glossary_term' = 'Special Service Request (SSR) Status');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `ssr_status` SET TAGS ('dbx_value_regex' = 'requested|confirmed|waitlisted|cancelled|denied|completed');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `wheelchair_type` SET TAGS ('dbx_business_glossary_term' = 'Wheelchair Type');
ALTER TABLE `airlines_ecm`.`passenger`.`ssr_record` ALTER COLUMN `wheelchair_type` SET TAGS ('dbx_value_regex' = 'WCHR|WCHS|WCHC');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` SET TAGS ('dbx_data_type' = 'association_data');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` SET TAGS ('dbx_subdomain' = 'service_preferences');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `loyalty_linkage_id` SET TAGS ('dbx_business_glossary_term' = 'Loyalty Linkage Identifier (ID)');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_business_glossary_term' = 'Ffp Member Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger Identifier (ID)');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `tier_status_id` SET TAGS ('dbx_business_glossary_term' = 'Recognized Tier Status Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `alliance_code` SET TAGS ('dbx_business_glossary_term' = 'Alliance Code');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `alliance_code` SET TAGS ('dbx_value_regex' = 'star_alliance|oneworld|skyteam|none');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `auto_recognition_enabled_flag` SET TAGS ('dbx_business_glossary_term' = 'Auto Recognition Enabled Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `data_quality_score` SET TAGS ('dbx_business_glossary_term' = 'Data Quality Score');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `external_reference_code` SET TAGS ('dbx_business_glossary_term' = 'External Reference Identifier (ID)');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `ffp_program_code` SET TAGS ('dbx_business_glossary_term' = 'Frequent Flyer Program (FFP) Program Code');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `ffp_program_code` SET TAGS ('dbx_value_regex' = '^[A-Z0-9]{2,3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `last_modified_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Last Modified Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `last_sync_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Last Synchronization Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `last_verified_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Last Verified Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `linkage_source_system` SET TAGS ('dbx_business_glossary_term' = 'Linkage Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `linkage_status` SET TAGS ('dbx_business_glossary_term' = 'Linkage Status');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `linkage_status` SET TAGS ('dbx_value_regex' = 'active|suspended|unlinked|pending_verification|expired|merged');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `linkage_type` SET TAGS ('dbx_business_glossary_term' = 'Linkage Type');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `linkage_type` SET TAGS ('dbx_value_regex' = 'primary|secondary|partner|reciprocal');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `notes` SET TAGS ('dbx_business_glossary_term' = 'Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `reciprocal_benefit_eligible_flag` SET TAGS ('dbx_business_glossary_term' = 'Reciprocal Benefit Eligible Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `recognition_priority` SET TAGS ('dbx_business_glossary_term' = 'Recognition Priority');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `sync_status` SET TAGS ('dbx_business_glossary_term' = 'Synchronization Status');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `sync_status` SET TAGS ('dbx_value_regex' = 'success|failed|pending|skipped|partial');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `tier_effective_date` SET TAGS ('dbx_business_glossary_term' = 'Tier Effective Date');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `tier_expiry_date` SET TAGS ('dbx_business_glossary_term' = 'Tier Expiry Date');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `unlinked_date` SET TAGS ('dbx_business_glossary_term' = 'Unlinked Date');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `unlinked_reason_code` SET TAGS ('dbx_business_glossary_term' = 'Unlinked Reason Code');
ALTER TABLE `airlines_ecm`.`passenger`.`loyalty_linkage` ALTER COLUMN `unlinked_reason_code` SET TAGS ('dbx_value_regex' = 'passenger_request|fraud_detected|membership_expired|duplicate_linkage|data_quality_issue|system_migration');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` SET TAGS ('dbx_subdomain' = 'service_preferences');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `traveller_segment_id` SET TAGS ('dbx_business_glossary_term' = 'Traveller Segment Identifier');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `cabin_class_id` SET TAGS ('dbx_business_glossary_term' = 'Cabin Class Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_business_glossary_term' = 'Ffp Member Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `ffp_member_id` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `city_pair_id` SET TAGS ('dbx_business_glossary_term' = 'Preferred City Pair Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `ancillary_propensity_score` SET TAGS ('dbx_business_glossary_term' = 'Ancillary Propensity Score');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `assignment_date` SET TAGS ('dbx_business_glossary_term' = 'Assignment Date');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `booking_channel_preference` SET TAGS ('dbx_business_glossary_term' = 'Booking Channel Preference');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `booking_channel_preference` SET TAGS ('dbx_value_regex' = 'direct_web|mobile_app|gds|travel_agent|call_center|mixed');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `churn_risk_score` SET TAGS ('dbx_business_glossary_term' = 'Churn Risk Score');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `confidence_score` SET TAGS ('dbx_business_glossary_term' = 'Confidence Score');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `corporate_affiliation_flag` SET TAGS ('dbx_business_glossary_term' = 'Corporate Affiliation Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `effective_from_date` SET TAGS ('dbx_business_glossary_term' = 'Effective From Date');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `effective_to_date` SET TAGS ('dbx_business_glossary_term' = 'Effective To Date');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `last_modified_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Last Modified Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `last_review_date` SET TAGS ('dbx_business_glossary_term' = 'Last Review Date');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `lifetime_value_tier` SET TAGS ('dbx_business_glossary_term' = 'Lifetime Value (LTV) Tier');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `lifetime_value_tier` SET TAGS ('dbx_value_regex' = 'platinum|gold|silver|bronze|standard');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `lifetime_value_tier` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `loyalty_engagement_level` SET TAGS ('dbx_business_glossary_term' = 'Loyalty Engagement Level');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `loyalty_engagement_level` SET TAGS ('dbx_value_regex' = 'highly_engaged|engaged|moderately_engaged|low_engagement|not_enrolled');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `next_review_date` SET TAGS ('dbx_business_glossary_term' = 'Next Review Date');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `price_sensitivity_indicator` SET TAGS ('dbx_business_glossary_term' = 'Price Sensitivity Indicator');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `price_sensitivity_indicator` SET TAGS ('dbx_value_regex' = 'very_high|high|medium|low|very_low');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `revenue_contribution_score` SET TAGS ('dbx_business_glossary_term' = 'Revenue Contribution Score');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `revenue_contribution_score` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `route_preference_type` SET TAGS ('dbx_business_glossary_term' = 'Route Preference Type');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `route_preference_type` SET TAGS ('dbx_value_regex' = 'domestic|short_haul_intl|long_haul_intl|mixed');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_category` SET TAGS ('dbx_business_glossary_term' = 'Segment Category');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_category` SET TAGS ('dbx_value_regex' = 'value|behavior|lifecycle|propensity|demographic|geographic');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_code` SET TAGS ('dbx_business_glossary_term' = 'Segment Code');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_code` SET TAGS ('dbx_value_regex' = '^[A-Z0-9_]{2,20}$');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_description` SET TAGS ('dbx_business_glossary_term' = 'Segment Description');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_model_version` SET TAGS ('dbx_business_glossary_term' = 'Segment Model Version');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_name` SET TAGS ('dbx_business_glossary_term' = 'Segment Name');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_notes` SET TAGS ('dbx_business_glossary_term' = 'Segment Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_priority` SET TAGS ('dbx_business_glossary_term' = 'Segment Priority');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_source` SET TAGS ('dbx_business_glossary_term' = 'Segment Source');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_source` SET TAGS ('dbx_value_regex' = 'rules_engine|ml_model|manual|third_party|hybrid');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_source_system` SET TAGS ('dbx_business_glossary_term' = 'Segment Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_status` SET TAGS ('dbx_business_glossary_term' = 'Segment Status');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `segment_status` SET TAGS ('dbx_value_regex' = 'active|inactive|expired|suspended|pending');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `targeting_eligible_flag` SET TAGS ('dbx_business_glossary_term' = 'Targeting Eligible Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `travel_frequency_band` SET TAGS ('dbx_business_glossary_term' = 'Travel Frequency Band');
ALTER TABLE `airlines_ecm`.`passenger`.`traveller_segment` ALTER COLUMN `travel_frequency_band` SET TAGS ('dbx_value_regex' = 'very_high|high|medium|low|very_low|inactive');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` SET TAGS ('dbx_data_type' = 'transactional_data');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` SET TAGS ('dbx_subdomain' = 'compliance_screening');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `consent_id` SET TAGS ('dbx_business_glossary_term' = 'Consent Identifier');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `company_code_id` SET TAGS ('dbx_business_glossary_term' = 'Company Code Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `minor_guardian_id` SET TAGS ('dbx_business_glossary_term' = 'Minor Guardian Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger (Pax) Profile Identifier');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `promotion_id` SET TAGS ('dbx_business_glossary_term' = 'Loyalty Promotion Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `audit_trail` SET TAGS ('dbx_business_glossary_term' = 'Consent Audit Trail');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `channel` SET TAGS ('dbx_business_glossary_term' = 'Consent Channel');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `channel` SET TAGS ('dbx_value_regex' = 'web|mobile_app|call_centre|airport_kiosk|email|in_flight');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `consent_status` SET TAGS ('dbx_business_glossary_term' = 'Consent Status');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `consent_status` SET TAGS ('dbx_value_regex' = 'granted|withdrawn|pending|expired|declined');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `consent_type` SET TAGS ('dbx_business_glossary_term' = 'Consent Type');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `consent_type` SET TAGS ('dbx_value_regex' = 'marketing_email|marketing_sms|marketing_push|data_sharing_partner|profiling|personalisation');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Consent Record Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `device_type` SET TAGS ('dbx_business_glossary_term' = 'Consent Device Type');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `device_type` SET TAGS ('dbx_value_regex' = 'desktop|mobile|tablet|kiosk|other');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `dpo_review_flag` SET TAGS ('dbx_business_glossary_term' = 'Data Protection Officer (DPO) Review Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `expiry_date` SET TAGS ('dbx_business_glossary_term' = 'Consent Expiry Date');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `granted_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Consent Granted Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `ip_address` SET TAGS ('dbx_business_glossary_term' = 'Consent Internet Protocol (IP) Address');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `ip_address` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `ip_address` SET TAGS ('dbx_pii_ip' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `jurisdiction_code` SET TAGS ('dbx_business_glossary_term' = 'Jurisdiction Code');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `jurisdiction_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `language_code` SET TAGS ('dbx_business_glossary_term' = 'Consent Language Code');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `language_code` SET TAGS ('dbx_value_regex' = '^[a-z]{2}$');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `last_modified_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Consent Last Modified Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `legal_basis` SET TAGS ('dbx_business_glossary_term' = 'Legal Basis for Processing');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `legal_basis` SET TAGS ('dbx_value_regex' = 'consent|contract|legal_obligation|vital_interest|public_task|legitimate_interest');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `minor_consent_flag` SET TAGS ('dbx_business_glossary_term' = 'Minor Consent Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `modified_by_user` SET TAGS ('dbx_business_glossary_term' = 'Consent Modified By User');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `notes` SET TAGS ('dbx_business_glossary_term' = 'Consent Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `opt_in_flag` SET TAGS ('dbx_business_glossary_term' = 'Opt-In Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `parental_consent_verified_flag` SET TAGS ('dbx_business_glossary_term' = 'Parental Consent Verified Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `processing_purpose` SET TAGS ('dbx_business_glossary_term' = 'Data Processing Purpose');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `renewal_due_date` SET TAGS ('dbx_business_glossary_term' = 'Consent Renewal Due Date');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `source_system` SET TAGS ('dbx_business_glossary_term' = 'Consent Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `text_snapshot` SET TAGS ('dbx_business_glossary_term' = 'Consent Text Snapshot');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `third_party_sharing_scope` SET TAGS ('dbx_business_glossary_term' = 'Third-Party Sharing Scope');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `user_agent` SET TAGS ('dbx_business_glossary_term' = 'Consent User Agent');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `user_agent` SET TAGS ('dbx_internal' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `user_agent` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `version` SET TAGS ('dbx_business_glossary_term' = 'Consent Policy Version');
ALTER TABLE `airlines_ecm`.`passenger`.`consent` ALTER COLUMN `withdrawn_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Consent Withdrawn Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` SET TAGS ('dbx_subdomain' = 'passenger_identity');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `minor_guardian_id` SET TAGS ('dbx_business_glossary_term' = 'Minor Guardian ID');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `member_id` SET TAGS ('dbx_business_glossary_term' = 'Accepting Crew Member Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `member_id` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `member_id` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `flight_leg_assignment_id` SET TAGS ('dbx_business_glossary_term' = 'Accepting Flight Leg Assignment Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `pnr_id` SET TAGS ('dbx_business_glossary_term' = 'Pnr Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `ticket_id` SET TAGS ('dbx_business_glossary_term' = 'Ticket Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `authorization_document_expiry_date` SET TAGS ('dbx_business_glossary_term' = 'Authorization Document Expiry Date');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `authorization_document_reference` SET TAGS ('dbx_business_glossary_term' = 'Authorization Document Reference');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `authorization_document_reference` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `authorization_document_type` SET TAGS ('dbx_business_glossary_term' = 'Authorization Document Type');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `authorization_document_type` SET TAGS ('dbx_value_regex' = 'parental_consent|court_order|legal_guardianship|notarized_letter|airline_form|other');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `dropoff_authorization_flag` SET TAGS ('dbx_business_glossary_term' = 'Drop-off Authorization Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `effective_from_date` SET TAGS ('dbx_business_glossary_term' = 'Effective From Date');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `effective_to_date` SET TAGS ('dbx_business_glossary_term' = 'Effective To Date');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_address_line_1` SET TAGS ('dbx_business_glossary_term' = 'Guardian Address Line 1');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_address_line_1` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_address_line_1` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_address_line_2` SET TAGS ('dbx_business_glossary_term' = 'Guardian Address Line 2');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_address_line_2` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_address_line_2` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_alternate_phone_number` SET TAGS ('dbx_business_glossary_term' = 'Guardian Alternate Phone Number');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_alternate_phone_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_alternate_phone_number` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_city` SET TAGS ('dbx_business_glossary_term' = 'Guardian City');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_city` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_city` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_country_code` SET TAGS ('dbx_business_glossary_term' = 'Guardian Country Code');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_country_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_email_address` SET TAGS ('dbx_business_glossary_term' = 'Guardian Email Address');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_email_address` SET TAGS ('dbx_value_regex' = '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_email_address` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_email_address` SET TAGS ('dbx_pii_email' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_first_name` SET TAGS ('dbx_business_glossary_term' = 'Guardian First Name');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_first_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_first_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_full_name` SET TAGS ('dbx_business_glossary_term' = 'Guardian Full Name');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_full_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_full_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_government_id_number` SET TAGS ('dbx_business_glossary_term' = 'Guardian Government-Issued ID Number');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_government_id_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_government_id_number` SET TAGS ('dbx_pii_identifier' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_government_id_type` SET TAGS ('dbx_business_glossary_term' = 'Guardian Government-Issued ID Type');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_government_id_type` SET TAGS ('dbx_value_regex' = 'passport|national_id|drivers_license|state_id|other');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_id_issuing_country` SET TAGS ('dbx_business_glossary_term' = 'Guardian ID Issuing Country');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_id_issuing_country` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_last_name` SET TAGS ('dbx_business_glossary_term' = 'Guardian Last Name');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_last_name` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_last_name` SET TAGS ('dbx_pii_name' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_country_code` SET TAGS ('dbx_business_glossary_term' = 'Guardian Phone Country Code');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_country_code` SET TAGS ('dbx_value_regex' = '^+[0-9]{1,3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_country_code` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_country_code` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_number` SET TAGS ('dbx_business_glossary_term' = 'Guardian Phone Number');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_number` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_phone_number` SET TAGS ('dbx_pii_phone' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_postal_code` SET TAGS ('dbx_business_glossary_term' = 'Guardian Postal Code');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_postal_code` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_postal_code` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_role` SET TAGS ('dbx_business_glossary_term' = 'Guardian Role');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_role` SET TAGS ('dbx_value_regex' = 'origin_dropoff|destination_pickup|both|emergency_contact');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_state_province` SET TAGS ('dbx_business_glossary_term' = 'Guardian State or Province');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_state_province` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardian_state_province` SET TAGS ('dbx_pii_address' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardianship_status` SET TAGS ('dbx_business_glossary_term' = 'Guardianship Status');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `guardianship_status` SET TAGS ('dbx_value_regex' = 'active|inactive|expired|revoked|pending_verification');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `pickup_authorization_flag` SET TAGS ('dbx_business_glossary_term' = 'Pickup Authorization Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `relationship_to_minor` SET TAGS ('dbx_business_glossary_term' = 'Relationship to Minor');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `relationship_to_minor` SET TAGS ('dbx_value_regex' = 'parent|legal_guardian|authorized_adult|grandparent|sibling|other_relative');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `source_system` SET TAGS ('dbx_business_glossary_term' = 'Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `special_instructions` SET TAGS ('dbx_business_glossary_term' = 'Special Instructions');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `special_instructions` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `verification_date` SET TAGS ('dbx_business_glossary_term' = 'Verification Date');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `verification_status` SET TAGS ('dbx_business_glossary_term' = 'Verification Status');
ALTER TABLE `airlines_ecm`.`passenger`.`minor_guardian` ALTER COLUMN `verification_status` SET TAGS ('dbx_value_regex' = 'verified|pending|failed|not_required');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` SET TAGS ('dbx_data_type' = 'transactional_data');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` SET TAGS ('dbx_subdomain' = 'compliance_screening');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `watchlist_check_id` SET TAGS ('dbx_business_glossary_term' = 'Watchlist Check Identifier');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `checkin_session_id` SET TAGS ('dbx_business_glossary_term' = 'Checkin Session Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `station_id` SET TAGS ('dbx_business_glossary_term' = 'Departure Station Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `flight_inventory_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Inventory Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `flight_leg_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Leg Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `flight_number_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Number Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `pnr_id` SET TAGS ('dbx_business_glossary_term' = 'Pnr Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `ticket_id` SET TAGS ('dbx_business_glossary_term' = 'Ticket Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `travel_identity_document_id` SET TAGS ('dbx_business_glossary_term' = 'Travel Identity Document Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `apis_submission_id` SET TAGS ('dbx_business_glossary_term' = 'Triggering Apis Submission Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `api_pnr_indicator` SET TAGS ('dbx_business_glossary_term' = 'Advance Passenger Information (API) / Passenger Name Record (PNR) Indicator');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `api_pnr_indicator` SET TAGS ('dbx_value_regex' = 'API|PNR|BOTH');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `boarding_pass_issued` SET TAGS ('dbx_business_glossary_term' = 'Boarding Pass Issued');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `check_status` SET TAGS ('dbx_business_glossary_term' = 'Check Status');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `check_status` SET TAGS ('dbx_value_regex' = 'COMPLETED|IN_PROGRESS|FAILED|EXPIRED|CANCELLED');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `check_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Check Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `data_retention_date` SET TAGS ('dbx_business_glossary_term' = 'Data Retention Date');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `expiry_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Expiry Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `match_reason` SET TAGS ('dbx_business_glossary_term' = 'Match Reason');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `match_reason` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `match_score` SET TAGS ('dbx_business_glossary_term' = 'Match Score');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `match_status` SET TAGS ('dbx_business_glossary_term' = 'Match Status');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `match_status` SET TAGS ('dbx_value_regex' = 'CLEAR|POTENTIAL_MATCH|CONFIRMED_MATCH|RESOLVED|INHIBITED');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `regulatory_submission_reference` SET TAGS ('dbx_business_glossary_term' = 'Regulatory Submission Reference');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `resolution_action` SET TAGS ('dbx_business_glossary_term' = 'Resolution Action');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `resolution_action` SET TAGS ('dbx_value_regex' = 'CLEARED_BY_AGENT|REDRESS_NUMBER_APPLIED|DOCUMENT_VERIFICATION|ESCALATED_TO_SECURITY|BOARDING_DENIED|PENDING_REVIEW');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `resolution_notes` SET TAGS ('dbx_business_glossary_term' = 'Resolution Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `resolution_notes` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `resolution_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Resolution Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `screening_jurisdiction` SET TAGS ('dbx_business_glossary_term' = 'Screening Jurisdiction');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `screening_jurisdiction` SET TAGS ('dbx_value_regex' = '^[A-Z]{2,3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `screening_program` SET TAGS ('dbx_business_glossary_term' = 'Screening Program');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `screening_program` SET TAGS ('dbx_value_regex' = 'TSA_SECURE_FLIGHT|OFAC_SANCTIONS|INTERPOL_NOTICE|EU_PNR_DIRECTIVE|NATIONAL_NO_FLY|CUSTOMS_WATCHLIST');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `screening_system` SET TAGS ('dbx_business_glossary_term' = 'Screening System');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `screening_version` SET TAGS ('dbx_business_glossary_term' = 'Screening Version');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `selectee_indicator` SET TAGS ('dbx_business_glossary_term' = 'Selectee Indicator');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `submission_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Submission Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `watchlist_name` SET TAGS ('dbx_business_glossary_term' = 'Watchlist Name');
ALTER TABLE `airlines_ecm`.`passenger`.`watchlist_check` ALTER COLUMN `watchlist_name` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` SET TAGS ('dbx_data_type' = 'transactional_data');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` SET TAGS ('dbx_subdomain' = 'compliance_screening');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `apis_submission_id` SET TAGS ('dbx_business_glossary_term' = 'Advance Passenger Information System (APIS) Submission ID');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `aircraft_id` SET TAGS ('dbx_business_glossary_term' = 'Aircraft Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `booking_passenger_id` SET TAGS ('dbx_business_glossary_term' = 'Reservation Booking Passenger Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `station_id` SET TAGS ('dbx_business_glossary_term' = 'Departure Station Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `flight_inventory_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Inventory Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `flight_leg_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Leg ID');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `flight_number_id` SET TAGS ('dbx_business_glossary_term' = 'Flight Number Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `original_submission_apis_submission_id` SET TAGS ('dbx_business_glossary_term' = 'Original APIS Submission ID');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `pnr_id` SET TAGS ('dbx_business_glossary_term' = 'Pnr Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `ticket_id` SET TAGS ('dbx_business_glossary_term' = 'Ticket Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `travel_identity_document_id` SET TAGS ('dbx_business_glossary_term' = 'Travel Identity Document Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `arrival_airport_code` SET TAGS ('dbx_business_glossary_term' = 'Arrival Airport Code');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `arrival_airport_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `authority_response_code` SET TAGS ('dbx_business_glossary_term' = 'Border Authority Response Code');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `authority_response_message` SET TAGS ('dbx_business_glossary_term' = 'Border Authority Response Message');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `authority_response_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Border Authority Response Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `border_authority_code` SET TAGS ('dbx_business_glossary_term' = 'Border Control Authority Code');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `compliance_mandate` SET TAGS ('dbx_business_glossary_term' = 'APIS Compliance Mandate');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Record Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `destination_country_code` SET TAGS ('dbx_business_glossary_term' = 'Destination Country Code');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `destination_country_code` SET TAGS ('dbx_value_regex' = '^[A-Z]{3}$');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `message_reference_number` SET TAGS ('dbx_business_glossary_term' = 'APIS Message Reference Number');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `resubmission_flag` SET TAGS ('dbx_business_glossary_term' = 'APIS Resubmission Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `scheduled_arrival_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Scheduled Arrival Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `scheduled_departure_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Scheduled Departure Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_channel` SET TAGS ('dbx_business_glossary_term' = 'APIS Submission Channel');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_method` SET TAGS ('dbx_business_glossary_term' = 'APIS Submission Method');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_method` SET TAGS ('dbx_value_regex' = 'automated|manual|batch|real_time');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_source_system` SET TAGS ('dbx_business_glossary_term' = 'APIS Submission Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_status` SET TAGS ('dbx_business_glossary_term' = 'APIS Submission Status');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_status` SET TAGS ('dbx_value_regex' = 'pending|accepted|rejected|error|cancelled');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `submission_timestamp` SET TAGS ('dbx_business_glossary_term' = 'APIS Submission Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`apis_submission` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Record Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` SET TAGS ('dbx_data_type' = 'master_data');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` SET TAGS ('dbx_subdomain' = 'passenger_identity');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `accessibility_profile_id` SET TAGS ('dbx_business_glossary_term' = 'Accessibility Profile ID');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `cabin_class_id` SET TAGS ('dbx_business_glossary_term' = 'Cabin Class Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mel_item_id` SET TAGS ('dbx_business_glossary_term' = 'Mel Item Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `profile_id` SET TAGS ('dbx_business_glossary_term' = 'Passenger ID');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `seat_product_id` SET TAGS ('dbx_business_glossary_term' = 'Seat Product Id (Foreign Key)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `ambulatory_status` SET TAGS ('dbx_business_glossary_term' = 'Ambulatory Status');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `ambulatory_status` SET TAGS ('dbx_value_regex' = 'fully_ambulatory|partially_ambulatory|non_ambulatory|stretcher_required');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `assistance_at_arrival_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Assistance at Arrival Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `assistance_at_departure_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Assistance at Departure Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `assistance_at_transit_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Assistance at Transit Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `boarding_method_preference` SET TAGS ('dbx_business_glossary_term' = 'Boarding Method Preference');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `boarding_method_preference` SET TAGS ('dbx_value_regex' = 'pre_board|ambulift|aisle_chair|carry_onboard|standard');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `cognitive_assistance_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Cognitive Assistance Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `companion_traveler_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Companion Traveler Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `created_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Created Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `hearing_impairment_level` SET TAGS ('dbx_business_glossary_term' = 'Hearing Impairment Level');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `hearing_impairment_level` SET TAGS ('dbx_value_regex' = 'none|mild|moderate|severe|profound');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `last_verified_date` SET TAGS ('dbx_business_glossary_term' = 'Last Verified Date');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_clearance_expiry_date` SET TAGS ('dbx_business_glossary_term' = 'Medical Clearance Expiry Date');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_clearance_expiry_date` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_clearance_expiry_date` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_clearance_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Medical Clearance Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_clearance_required_flag` SET TAGS ('dbx_restricted' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_clearance_required_flag` SET TAGS ('dbx_pii' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_equipment_carried` SET TAGS ('dbx_business_glossary_term' = 'Medical Equipment Carried');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `medical_equipment_carried` SET TAGS ('dbx_confidential' = 'true');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_battery_type` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Battery Type');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_battery_type` SET TAGS ('dbx_value_regex' = 'lithium_ion|dry_cell|wet_cell|none|unknown');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_battery_watt_hours` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Battery Watt-Hours');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_foldable_flag` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Foldable Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_height_cm` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Height (Centimeters)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_length_cm` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Length (Centimeters)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_type` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Type');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_weight_kg` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Weight (Kilograms)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `mobility_aid_width_cm` SET TAGS ('dbx_business_glossary_term' = 'Mobility Aid Width (Centimeters)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `oxygen_flow_rate_lpm` SET TAGS ('dbx_business_glossary_term' = 'Oxygen Flow Rate (Liters Per Minute)');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `oxygen_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Oxygen Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `preferred_seating_location` SET TAGS ('dbx_business_glossary_term' = 'Preferred Seating Location');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `preferred_seating_location` SET TAGS ('dbx_value_regex' = 'bulkhead|aisle|window|near_lavatory|extra_legroom|no_preference');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `prm_category` SET TAGS ('dbx_business_glossary_term' = 'Passenger with Reduced Mobility (PRM) Category');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `profile_effective_from_date` SET TAGS ('dbx_business_glossary_term' = 'Profile Effective From Date');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `profile_effective_to_date` SET TAGS ('dbx_business_glossary_term' = 'Profile Effective To Date');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `profile_status` SET TAGS ('dbx_business_glossary_term' = 'Profile Status');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `profile_status` SET TAGS ('dbx_value_regex' = 'active|inactive|expired|pending_verification');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `seating_restriction_notes` SET TAGS ('dbx_business_glossary_term' = 'Seating Restriction Notes');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `service_animal_flag` SET TAGS ('dbx_business_glossary_term' = 'Service Animal Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `service_animal_type` SET TAGS ('dbx_business_glossary_term' = 'Service Animal Type');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `service_animal_type` SET TAGS ('dbx_value_regex' = 'guide_dog|hearing_dog|psychiatric_service_dog|mobility_assistance_dog|other|none');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `source_system` SET TAGS ('dbx_business_glossary_term' = 'Source System');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `special_instructions` SET TAGS ('dbx_business_glossary_term' = 'Special Instructions');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `stretcher_required_flag` SET TAGS ('dbx_business_glossary_term' = 'Stretcher Required Flag');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `updated_timestamp` SET TAGS ('dbx_business_glossary_term' = 'Updated Timestamp');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `visual_impairment_level` SET TAGS ('dbx_business_glossary_term' = 'Visual Impairment Level');
ALTER TABLE `airlines_ecm`.`passenger`.`accessibility_profile` ALTER COLUMN `visual_impairment_level` SET TAGS ('dbx_value_regex' = 'none|low_vision|legally_blind|totally_blind');
