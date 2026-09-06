import json
import os
import re
import types

import pytest

NB = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb")


def _cells():
    nb = json.load(open(NB))
    return ["".join(c.get("source", [])) if isinstance(c.get("source"), list) else (c.get("source") or "")
            for c in nb["cells"]]


def _slice_def(src, name):
    """Slice a top-level `def <name>` (or method `    def <name>`) block out of a cell source."""
    lines = src.splitlines()
    start = None
    base = 0
    for i, l in enumerate(lines):
        if re.match(r"^(\s*)def %s\b" % re.escape(name), l):
            start = i
            base = len(l) - len(l.lstrip())
            break
    assert start is not None, "def %s not found" % name
    end = start + 1
    while end < len(lines):
        l = lines[end]
        if l.strip() and (len(l) - len(l.lstrip())) <= base and (l.lstrip().startswith(("def ", "class "))):
            break
        end += 1
    body = "\n".join(lines[start:end])
    # de-indent a method to module level so it can exec standalone
    if base:
        body = "\n".join(ln[base:] if ln[:base].strip() == "" else ln for ln in body.splitlines())
    return body


def _load_parser_and_finalizer():
    cells = _cells()
    ns = {"re": re}
    exec(_slice_def(cells[56], "_vov_named_create_targets"), ns)
    exec(_slice_def(cells[138], "_v441_reviewer_finalization"), ns)
    return ns


def _load_pcc():
    """_verify_product_create_coverage sliced as a standalone fn; drop leading `self` at call."""
    cells = _cells()
    ns = {"re": re}
    exec(_slice_def(cells[56], "_vov_named_create_targets"), ns)
    body = _slice_def(cells[100], "_verify_product_create_coverage")
    exec(body, ns)
    return ns


# real reviewer directive text (shipping & ports R1..R9), verbatim shape
R1 = ("REVIEWER-PRIORITY 1 - add_product: cargo.transhipment - model transhipment (T/S) as a FIRST-CLASS "
      "concept, not a generic container visit. Add product cargo.transhipment (a T/S move that links an "
      "inbound vessel call to an outbound vessel call) plus cargo.transhipment_leg. "
      "FK the transhipment to the existing inbound/outbound vessel.call and cargo.container.")
R2 = ("REVIEWER-PRIORITY 2 - add_product: cargo.empty_container_pool - add empty container / MTY pool / depot "
      "operations. Add products cargo.empty_container_pool (MTY pool balance), cargo.container_depot (depot "
      "facility), cargo.container_lease (leasing agreement), and cargo.depot_repair_order (M&R work order).")
R4 = ("REVIEWER-PRIORITY 4 - add_domain: sustainability - create a new FIRST-CLASS domain sustainability in "
      "the operations division for decarbonization tracking, with products cii_rating, eexi_record, "
      "shore_power_session, and bunker_carbon_intensity. Classify sustainability as division=operations; "
      "FK to masterdata.vessel_master and vessel.call where relevant.")

FULL = "\n".join([R1, R2, R4])


def _fake_req(text, scope="domain", scope_targets=None, rid="VREQ-005"):
    r = types.SimpleNamespace()
    r.original_text = text
    r.scope = scope
    r.scope_targets = scope_targets or []
    r.id = rid
    return r


# ---------------------------------------------------------------- parser
def test_parser_extracts_add_product_targets():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](R1)
    assert ("cargo", "transhipment") in tg["products"], tg["products"]
    assert ("cargo", "transhipment_leg") in tg["products"], tg["products"]
    # FK-target 'the existing ... vessel.call' must NOT be a create target
    assert ("vessel", "call") not in tg["products"], tg["products"]


def test_parser_extracts_multi_product_list():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](R2)
    prods = set(tg["products"])
    for p in ["empty_container_pool", "container_depot", "container_lease", "depot_repair_order"]:
        assert ("cargo", p) in prods, (p, prods)


def test_parser_extracts_add_domain_with_products():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](R4)
    assert "sustainability" in tg["domains"]
    meta = tg["domain_meta"]["sustainability"]
    assert meta["division"] == "operations", meta
    for p in ["cii_rating", "eexi_record", "shore_power_session", "bunker_carbon_intensity"]:
        assert p in meta["products"], (p, meta["products"])


# real shipping R4 carries parenthetical prose ('... kWh and emissions avoided') that leaked a phantom
# 'emissions' product when the 'with products' list was split on 'and'. The parenthetical-strip fix
# (alias=vov-named-create-targets) removes '(...)' before splitting. fail-pre: 'emissions' present.
R4_PARENS = ("REVIEWER-PRIORITY 4 - add_domain: sustainability - create a new FIRST-CLASS domain "
             "sustainability in the operations division, with products cii_rating (IMO CII A-E rating), "
             "eexi_record (Energy Efficiency Existing Ship Index), shore_power_session (cold-ironing / OPS "
             "session with kWh and emissions avoided), and bunker_carbon_intensity (well-to-wake). "
             "Classify sustainability as division=operations.")


def test_parser_strips_parenthetical_prose_no_phantom_product():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](R4_PARENS)
    prods = tg["domain_meta"]["sustainability"]["products"]
    assert "emissions" not in prods, ("phantom 'emissions' leaked from parenthetical prose", prods)
    for p in ["cii_rating", "eexi_record", "shore_power_session", "bunker_carbon_intensity"]:
        assert p in prods, (p, prods)


# ---------------------------------------------------------------- finalizer P0-create (behavioral)
def _base_model():
    # cargo exists (so a domain-present verifier would false-fulfill), but transhipment is absent;
    # sustainability domain is entirely absent.
    return {"model": {"domains": [
        {"name": "cargo", "products": [
            {"name": "container", "primary_key": "container_id",
             "attributes": [{"name": "container_id", "type": "BIGINT", "is_primary_key": True}]}]},
        {"name": "vessel", "products": [
            {"name": "call", "primary_key": "call_id",
             "attributes": [{"name": "call_id", "type": "BIGINT", "is_primary_key": True}]},
            {"name": "vessel_master", "primary_key": "vessel_master_id",
             "attributes": [{"name": "vessel_master_id", "type": "BIGINT", "is_primary_key": True}]}]},
        {"name": "masterdata", "products": [
            {"name": "vessel_master", "primary_key": "vessel_master_id",
             "attributes": [{"name": "vessel_master_id", "type": "BIGINT", "is_primary_key": True}]}]},
    ]}}


def _all_products(model):
    out = []
    for d in model["model"]["domains"]:
        for p in (d.get("products") or d.get("data_products") or []):
            out.append((d["name"], p["name"]))
    return out


def test_finalizer_materializes_missing_products_and_domain():
    ns = _load_parser_and_finalizer()
    m = _base_model()
    ns["_v441_reviewer_finalization"](m, FULL, logger=None)
    prods = _all_products(m)
    names = {p for (_d, p) in prods}
    # R1/R2 add_product targets now exist
    for p in ["transhipment", "transhipment_leg", "empty_container_pool", "container_depot",
              "container_lease", "depot_repair_order"]:
        assert p in names, (p, sorted(names))
    # R4 add_domain sustainability exists with its 4 products
    doms = {d["name"]: d for d in m["model"]["domains"]}
    assert "sustainability" in doms, list(doms)
    sp = {pp["name"] for pp in (doms["sustainability"].get("products") or doms["sustainability"].get("data_products") or [])}
    for p in ["cii_rating", "eexi_record", "shore_power_session", "bunker_carbon_intensity"]:
        assert p in sp, (p, sp)
    # every created product has a primary key (not a bare silo shell)
    for d in m["model"]["domains"]:
        for p in (d.get("products") or d.get("data_products") or []):
            assert any(a.get("is_primary_key") for a in p.get("attributes", [])), (d["name"], p["name"])


def test_finalizer_idempotent_no_dup():
    ns = _load_parser_and_finalizer()
    m = _base_model()
    ns["_v441_reviewer_finalization"](m, FULL, logger=None)
    n1 = len(_all_products(m))
    ns["_v441_reviewer_finalization"](m, FULL, logger=None)
    n2 = len(_all_products(m))
    assert n1 == n2, ("re-running finalization must not duplicate", n1, n2)


# v4.5.0: the LAST directive's secondary products were lost when a trailing agent-auto block (containing
# 'add column'/SA findings) bled into it and tripped the per-segment add-column veto (shipping live:
# R9 damage_liability dropped, 12/25 -> 48%). Per-line segmentation scopes each directive so ALL
# secondaries land. fail-pre: whole-text / loose-boundary parse drops the last directive's 2nd product.
FULL_WITH_TRAILING_AUTOBLOCK = "\n".join([
    "REVIEWER-PRIORITY 1 - add_product: cargo.transhipment - model transhipment as a first-class concept. "
    "Add product cargo.transhipment plus cargo.transhipment_leg.",
    "REVIEWER-PRIORITY 9 - add_product: cargo.container_condition_report - complete the damage workflow. "
    "Add products cargo.container_condition_report and cargo.damage_liability. FK cargo.damage_liability "
    "to the existing cargo.damage_claim; do NOT duplicate the claim table.",
    "================================================================================",
    "AGENT AUTO-GENERATED PRIORITIES (retain and also apply).",
    "  - [SA:denormalized_natural_key] Product 'x.y' has both FK 'y_id' and add column natural key 'y_code'.",
    "  - [SA:unlinked_fk] Column a.b.c_id looks like an FK but has no foreign_key_to reference.",
])


def test_finalizer_per_line_segmentation_captures_last_directive_secondary():
    ns = _load_parser_and_finalizer()
    m = _base_model()
    # ensure damage_claim exists so damage_liability is a genuine NEW product (not a dup)
    cargo = next(d for d in m["model"]["domains"] if d["name"] == "cargo")
    cargo.setdefault("products", []).append(
        {"name": "damage_claim", "primary_key": "damage_claim_id",
         "attributes": [{"name": "damage_claim_id", "type": "BIGINT", "is_primary_key": True}]})
    ns["_v441_reviewer_finalization"](m, FULL_WITH_TRAILING_AUTOBLOCK, logger=None)
    names = {p for (_d, p) in _all_products(m)}
    # the R9 SECONDARY product must be materialized despite the trailing add-column autoblock
    assert "damage_liability" in names, ("R9 secondary lost to trailing-block veto bleed", sorted(names))
    assert "transhipment_leg" in names, ("R1 secondary lost", sorted(names))
    # trailing SA/autoblock lines must NOT create spurious products
    for spurious in ["y", "b", "natural"]:
        assert spurious not in names, ("trailing autoblock leaked a phantom product", spurious, sorted(names))


# ---------------------------------------------------------------- verifier honesty (fail-pre/pass-post)
def test_verifier_scope_domain_named_product_scores_failed_when_missing():
    ns = _load_pcc()
    fn = ns["_verify_product_create_coverage"]
    self = types.SimpleNamespace(logger=types.SimpleNamespace(info=lambda *a, **k: None))
    products_data = [{"domain": "cargo", "product": "container"}]  # transhipment absent
    req = _fake_req(R1, scope="domain", rid="VREQ-005")
    verdict = fn(self, req, products_data)
    # v4.4.8 bug returned None (scope==domain bail) -> LLM fallback false-fulfilled.
    # v4.4.9 must return an authoritative non-fulfilled verdict.
    assert verdict is not None, "must not fall through for a domain-scoped named-product create"
    assert verdict["status"] in ("failed", "partial"), verdict
    assert verdict["status"] == "failed", verdict  # 0 of {transhipment,transhipment_leg} exist


def test_verifier_scores_fulfilled_when_products_present():
    ns = _load_pcc()
    fn = ns["_verify_product_create_coverage"]
    self = types.SimpleNamespace(logger=types.SimpleNamespace(info=lambda *a, **k: None))
    products_data = [{"domain": "cargo", "product": "container"},
                     {"domain": "cargo", "product": "transhipment"},
                     {"domain": "cargo", "product": "transhipment_leg"}]
    req = _fake_req(R1, scope="domain", rid="VREQ-005")
    verdict = fn(self, req, products_data)
    assert verdict is not None and verdict["status"] == "fulfilled", verdict


# ---------------------------------------------------------------- v4.5.1 automotive phrasings (fail-pre/pass-post)
# Automotive reviewer directives use two phrasings the shipping-tuned parser (v4.5.0) never matched, so it
# captured ZERO automotive targets -> the deterministic backstop was inert and ~36 secondary products rode the
# flaky LLM path. fail-pre (v4.5.0): add_domain requires a colon immediately after ('add_domain:'), and there is
# no domain-scoped bare-list extractor -> A1/A2/A5 capture nothing. pass-post (v4.5.1): all land.
A1 = ("REVIEWER-PRIORITY 1 - add_domain field_services: the value chain has NO dedicated Field Services domain. "
      "Add a field_services domain in the operations division. Create the field_services domain with the "
      "following products: field_technician_dispatch, mobile_service_order, roadside_assistance_case, "
      "towing_event, breakdown_case, field_visit, field_activity, field_quality_investigation, "
      "field_failure_analysis, field_engineering_report, field_service_appointment, field_parts_usage.")
A2 = ("REVIEWER-PRIORITY 2 - add F&I products to sales: Financing and leasing is a major revenue stream not "
      "modeled. Add more tables to the sales domain to cover Finance & Insurance (F&I): finance_contract, "
      "lease_contract, insurance_policy, fni_menu_product, credit_application, residual_value_schedule.")
A5 = ("REVIEWER-PRIORITY 5 - add ESG and energy products (production + governance): Add more tables to the "
      "manufacturing domain for ESG and energy tracking: energy_consumption_record, co2_emission_record, "
      "water_usage_record, line_energy_meter. Add more tables to the compliance domain for ESG reporting: "
      "esg_report, social_compliance_audit, sustainability_metric.")
A7 = ("REVIEWER-PRIORITY 7 - connect telemetry to aftersales: In the aftersales domain, the service appointment "
      "table should reference mobility.connected_vehicle: add column connected_vehicle_id to the aftersales "
      "service appointment table with FK to mobility.connected_vehicle.")


def test_parser_add_domain_name_before_colon():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](A1)
    assert "field_services" in tg["domains"], ("add_domain <name>: not recognized", tg["domains"])


def test_parser_new_domain_with_following_products_all_12():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](A1)
    prods = tg["domain_meta"]["field_services"]["products"]
    for p in ["field_technician_dispatch", "mobile_service_order", "roadside_assistance_case", "towing_event",
              "breakdown_case", "field_visit", "field_activity", "field_quality_investigation",
              "field_failure_analysis", "field_engineering_report", "field_service_appointment",
              "field_parts_usage"]:
        assert p in prods, (p, prods)
    assert tg["domain_meta"]["field_services"]["division"] == "operations", tg["domain_meta"]["field_services"]


def test_parser_existing_domain_bare_list_routes_to_products():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](A2)
    prods = set(tg["products"])
    for p in ["finance_contract", "lease_contract", "insurance_policy", "fni_menu_product",
              "credit_application", "residual_value_schedule"]:
        assert ("sales", p) in prods, (p, sorted(prods))
    assert not tg["domains"], ("existing-domain add must NOT declare a new domain", tg["domains"])


def test_parser_two_domain_directive_both_captured():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](A5)
    prods = set(tg["products"])
    for p in ["energy_consumption_record", "co2_emission_record", "water_usage_record", "line_energy_meter"]:
        assert ("manufacturing", p) in prods, ("manufacturing leg lost", p, sorted(prods))
    for p in ["esg_report", "social_compliance_audit", "sustainability_metric"]:
        assert ("compliance", p) in prods, ("compliance/governance leg lost", p, sorted(prods))


def test_parser_add_column_directive_creates_nothing():
    ns = _load_parser_and_finalizer()
    tg = ns["_vov_named_create_targets"](A7)
    # an add-column/FK directive is not a product create; the FK target 'mobility.connected_vehicle' must not
    # be mistaken for a product to create, and no bare-list is captured.
    assert ("mobility", "connected_vehicle") not in tg["products"], tg["products"]
    assert tg["products"] == [] and tg["domains"] == [], (tg["products"], tg["domains"])


def test_parser_shipping_capture_unchanged_regression():
    # the v4.5.1 additions are ADDITIVE — shipping's existing capture must be byte-for-byte unchanged.
    ns = _load_parser_and_finalizer()
    ship = ns["_vov_named_create_targets"](R4)  # add_domain: sustainability with 'with products' phrasing
    sp = ns["_vov_named_create_targets"](R1)
    assert "sustainability" in ship["domains"], ship["domains"]
    for p in ["cii_rating", "eexi_record", "shore_power_session", "bunker_carbon_intensity"]:
        assert p in ship["domain_meta"]["sustainability"]["products"], (p, ship["domain_meta"]["sustainability"])
    # R4 sustainability must NOT leak a phantom (parenthetical strip preserved)
    assert "emissions" not in ship["domain_meta"]["sustainability"]["products"], ship["domain_meta"]["sustainability"]
    # R1 dotted add_product still works
    assert ("cargo", "transhipment") in sp["products"] and ("cargo", "transhipment_leg") in sp["products"], sp["products"]


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
