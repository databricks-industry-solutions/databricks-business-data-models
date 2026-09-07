from datetime import date
from pathlib import Path

SEED = 42
CATALOG = "meridian_bronze"
DATE_START = date(2024, 7, 1)
DATE_END = date(2026, 6, 30)
OUTPUT_DIR = Path(__file__).parent / "output"
SCHEMAS = ["sap_sd", "salesforce_crm", "edi_gateway", "returns_portal", "fieldlink"]

# Row-count targets (see spec scale table). Downstream code scales children off these.
ROWS = {
    "customers": 300, "materials": 400, "plants": 4, "employees": 60,
    "orders": 5000, "opportunities": 3500, "quotes": 4000,
    "credit_checks": 5000, "edi_messages": 6000, "rmas": 400,
    "contracts": 120, "installed_assets": 8000, "service_orders": 3000,
    "warranty_claims": 500,
}

# Two seasonal OTD-crunch windows (month keys where late deliveries spike).
OTD_CRUNCH_MONTHS = {(2024, 12), (2025, 1), (2025, 11), (2025, 12)}

# --- Code enums (SAP-style short codes -> used raw in sap_sd, mapped in lookups) ---
ORDER_TYPES = {"TA": "Standard Order", "KB": "Consignment Fill-Up",
               "KE": "Consignment Issue", "ZBLK": "Blanket Order", "ZIC": "Intercompany"}
CHANNELS = {"10": "Direct/OE", "20": "Distributor", "30": "Dealer", "40": "Intercompany"}
INCOTERMS = {"EXW": "Ex Works", "FCA": "Free Carrier", "DAP": "Delivered At Place",
             "DDP": "Delivered Duty Paid", "CIP": "Carriage Insurance Paid"}
PAYMENT_TERMS = {"NT30": "Net 30", "NT45": "Net 45", "NT60": "Net 60", "PIA": "Prepaid"}
CURRENCIES = ["USD", "EUR", "GBP", "JPY"]
UOM = ["EA", "PC", "SET"]
ORDER_STATUSES = ["open", "in-process", "shipped", "invoiced", "closed", "cancelled"]

# MVM profile — row-count targets for the 6 new SAP SD source tables.
MVM_ROWS = {
    "status_events": 30000,   # nominal sizing note only (NOT a hard cap) — status_log emits one
                              #   row per lifecycle stage reached per order (see gen_sap_sd_mvm._status_log)
    "atp_log": 12000,
    "sched_agreement": 800,
    "cpq_config": 2500,
    "delivery": 4200,         # deliveries (subset of orders shipped)
    "delivery_line": 9000,
}
