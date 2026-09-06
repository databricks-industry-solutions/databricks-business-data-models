import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _cell_src(idx):
    nb = json.load(open(NB))
    return "".join(nb["cells"][idx]["source"])


def _full():
    nb = json.load(open(NB))
    return "".join("".join(c.get("source", [])) for c in nb["cells"])


# ---- version anchor (exact for the current version) ----
def test_v346_version_constant():
    src = _cell_src(1)
    m = re.search(r'__AGENT_VERSION__ = "(\d+)\.(\d+)\.(\d+)"', src)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 4, 6)


# ---- domain-closed-no-shared: alias + gate present at all three sites ----
def test_v346_alias_present():
    full = _full()
    assert full.count("domain-closed-no-shared") >= 3
    assert full.count("USER_DOMAINS_EXHAUSTIVE") >= 3


# ---- behavioral: _ensure_shared_domain is a no-op when the roster is closed ----
def _exec_ensure_shared_domain():
    full = _full()
    i = full.index("def _ensure_shared_domain(domains_data, config=None, logger=None):")
    # slice to just before the next top-level def
    j = full.index("\ndef _cleanup_phantom_domains", i)
    block = full[i:j]
    # the slice came from the joined notebook source where each physical line still
    # ends in \n; it is already valid python. exec it.
    ns = {
        "SHARED_DOMAIN_TEMPLATE": {"domain": "shared", "database_name": "shared",
                                   "description": "shared", "products": []},
    }
    exec(block, ns)
    return ns["_ensure_shared_domain"]


def test_v346_closed_roster_suppresses_shared():
    fn = _exec_ensure_shared_domain()
    doms = [{"domain": "hr"}, {"domain": "project"}]
    # CLOSED roster -> must NOT add shared, returns False, domains unchanged
    created = fn(doms, {"USER_DOMAINS_EXHAUSTIVE": True}, None)
    assert created is False
    assert all(d["domain"] != "shared" for d in doms)
    assert len(doms) == 2


def test_v346_open_roster_still_creates_shared_nontautology():
    # NON-TAUTOLOGY: the gate must ONLY fire when closed. Open roster keeps the
    # original behavior (shared IS created) so healthcare/automotive SSOT survives.
    fn = _exec_ensure_shared_domain()
    doms = [{"domain": "claims"}, {"domain": "member"}]
    created = fn(doms, {"USER_DOMAINS_EXHAUSTIVE": False}, None)
    assert created is True
    assert any(d.get("domain") == "shared" for d in doms)


def test_v346_open_roster_idempotent_when_shared_exists():
    fn = _exec_ensure_shared_domain()
    doms = [{"domain": "claims"}, {"domain": "shared"}]
    created = fn(doms, {"USER_DOMAINS_EXHAUSTIVE": False}, None)
    assert created is False  # already present
    assert sum(1 for d in doms if d.get("domain") == "shared") == 1


# ---- dedup keeps 'shared' out of the valid-merge set when closed ----
def test_v346_dedup_excludes_shared_when_closed():
    full = _full()
    i = full.index("# v3.4.6 alias=domain-closed-no-shared: when the user fixed the domain roster")
    seg = full[i:i + 900]
    # closed -> shared NOT added to valid set
    assert "if not _closed_roster:" in seg
    assert "valid_domains_set.add('shared')" in seg
    # last-resort fallback is a real user domain when closed, never 'shared'
    assert "_last_resort" in seg


# ============================================================================
# model-json-authoritative-tags (v3.4.6) — make model.json the single source
# of truth for tags at domain / subdomain / table / column levels.
# ============================================================================

def _exec_tag_helpers():
    full = _full()
    i = full.index("def _tagset_from_string(")
    j = full.index("\ndef _cleanup_phantom_domains", i)
    block = full[i:j]
    ns = {}
    exec(block, ns)
    return ns


def test_v346_tag_alias_and_callsite_present():
    full = _full()
    # function defined + at least one production call site (wired into model.json write)
    assert "def _enrich_model_authoritative_tags(" in full
    assert "model-json-authoritative-tags" in full
    assert full.count("_enrich_model_authoritative_tags(") >= 2  # def + >=1 call


def test_v346_tagset_from_string_parses_kv_and_labels():
    ns = _exec_tag_helpers()
    fn = ns["_tagset_from_string"]
    ts = fn("gov_transport_source_table=emp_history, primary_key, pii_identifier")
    keys = {t["key"]: t for t in ts}
    assert keys["gov_transport_source_table"]["value"] == "emp_history"
    assert keys["gov_transport_source_table"]["kind"] == "key_value"
    assert keys["primary_key"]["kind"] == "label"
    assert keys["pii_identifier"]["kind"] == "label"


def test_v346_enrich_adds_tagset_all_levels_and_subdomains():
    ns = _exec_tag_helpers()
    enrich = ns["_enrich_model_authoritative_tags"]
    dm = {
        "domains": [{
            "domain": "hr", "division": "corporate",
            "products": [{
                "name": "employee", "subdomain": "workforce",
                "tags": "gov_transport_source_table=emp_history", "data_type": "master_data",
                "attributes": [
                    {"name": "employee_id", "data_type": "BIGINT",
                     "tags": "primary_key, pii_identifier",
                     "business_glossary_term": "Employee Identifier"},
                ],
            }],
        }]
    }
    cfg = {"MODEL_CONVENTIONS": {"tag_prefix": "gov_transport_", "tag_suffix": ""}}
    enrich(dm, cfg, None)
    d0 = dm["domains"][0]
    # DOMAIN level
    dkeys = {t["key"] for t in d0["tag_set"]}
    assert "gov_transport_domain" in dkeys and "gov_transport_division" in dkeys
    # SUBDOMAIN promoted to first-class object with its own tag_set
    assert d0.get("subdomains"), "subdomains not promoted"
    sd = d0["subdomains"][0]
    assert sd["name"] == "workforce"
    assert any(t["key"] == "gov_transport_subdomain" for t in sd["tag_set"])
    assert "steward" in sd
    # TABLE level
    p0 = d0["products"][0]
    pkeys = {t["key"] for t in p0["tag_set"]}
    assert "gov_transport_source_table" in pkeys and "gov_transport_data_type" in pkeys
    assert "gov_transport_subdomain" in pkeys
    # COLUMN level
    a0 = p0["attributes"][0]
    akeys = {t["key"] for t in a0["tag_set"]}
    assert "primary_key" in akeys and "pii_identifier" in akeys
    assert "gov_transport_business_glossary_term" in akeys


def test_v346_trace_tag_harvest_from_description():
    # VREQ-011: gov_transport_source_attribute buried in description prose must be promoted to a tag.
    ns = _exec_tag_helpers()
    enrich = ns["_enrich_model_authoritative_tags"]
    dm = {"domains": [{"domain": "hr", "products": [{
        "name": "employee", "attributes": [
            {"name": "employee_id", "type": "BIGINT",
             "description": "Canonical employee key. gov_transport_source_attribute=PERNR maps to SAP."},
        ]}]}]}
    cfg = {"MODEL_CONVENTIONS": {"tag_prefix": "gov_transport_", "tag_suffix": ""}}
    enrich(dm, cfg, None)
    ts = dm["domains"][0]["products"][0]["attributes"][0]["tag_set"]
    hit = [t for t in ts if t["key"] == "gov_transport_source_attribute"]
    assert hit, "trace tag not harvested from description"
    assert hit[0]["value"] == "PERNR"
    assert hit[0]["source"] == "harvested"


def test_v346_physical_mirror_promotes_description_trace_into_tags_string():
    # VREQ-011 PHYSICAL: step_apply_tags reads the flat 'tags' string. The mirror must move a
    # description-buried trace tag into 'tags' so it becomes a real UC tag. (flat-list signature)
    ns = _exec_tag_helpers()
    mirror = ns["_mirror_trace_tags_into_tags_string"]
    attrs = [
        {"name": "employee_id", "tags": "primary_key",
         "description": "Key. gov_transport_source_attribute=PERNR maps to SAP."},
        {"name": "x", "tags": "", "description": "no trace token here"},
    ]
    cfg = {"MODEL_CONVENTIONS": {"tag_prefix": "gov_transport_", "tag_suffix": ""}}
    mirror([], attrs, cfg, None)
    assert "gov_transport_source_attribute=PERNR" in attrs[0]["tags"]
    assert "primary_key" in attrs[0]["tags"]  # existing tag preserved
    assert attrs[1]["tags"] == ""  # no false promotion
    # idempotent
    mirror([], attrs, cfg, None)
    assert attrs[0]["tags"].count("gov_transport_source_attribute") == 1


def test_v346_harvest_ignores_non_trace_kv():
    # NON-TAUTOLOGY: a random key=value in prose must NOT become a tag (only prefix/trace keys).
    ns = _exec_tag_helpers()
    enrich = ns["_enrich_model_authoritative_tags"]
    dm = {"domains": [{"domain": "hr", "products": [{
        "name": "employee", "attributes": [
            {"name": "x", "description": "threshold=0.85 and ratio=12 are tuning knobs."},
        ]}]}]}
    cfg = {"MODEL_CONVENTIONS": {"tag_prefix": "gov_transport_", "tag_suffix": ""}}
    enrich(dm, cfg, None)
    ts = dm["domains"][0]["products"][0]["attributes"][0]["tag_set"]
    assert not any(t["key"] in ("threshold", "ratio") for t in ts)


# ---- subdomain-user-sizing-respect: subdomain counts survive clamp under user override ----
def test_v346_subdomain_keys_in_sizing_set():
    full = _full()
    i = full.index("_SIZING_PARAM_KEYS = {")
    seg = full[i:full.index("}", i + 1500)]
    assert "max_business_subdomains" in seg
    assert "min_business_subdomains" in seg
    assert "min_products_per_subdomain" in seg
    assert "subdomain-user-sizing-respect" in full


def test_v346_clamp_respects_subdomains_under_override():
    # Behavioral: with user_sizing_override, max_business_subdomains=9 must NOT be clamped to tier max.
    full = _full()
    i = full.index("_SIZING_PARAM_KEYS = {")
    j = full.index("\ndef _determine_model_parameters", i)
    block = full[i:j]
    # provide guardrails that would clamp 9 -> 4 if the key were not override-exempt
    ns = {
        "_MODEL_PARAM_GUARDRAILS": {"mvm_model": {"max_business_subdomains": {"min": 3, "max": 4}}},
        "_MODEL_PARAM_MIN_MAX_PAIRS": [],
    }
    exec(block, ns)
    clamp = ns["_clamp_and_validate_model_params"]

    class _L:
        def info(self, *a, **k): pass
        def warning(self, *a, **k): pass
    out = clamp("mvm_model", {"max_business_subdomains": 9}, _L(), user_sizing_override=True)
    assert out["max_business_subdomains"] == 9, f"user-mandated 9 subdomains was clamped to {out['max_business_subdomains']}"
    # NON-TAUTOLOGY: without override, the tier guardrail DOES clamp 9 -> 4
    out2 = clamp("mvm_model", {"max_business_subdomains": 9}, _L(), user_sizing_override=False)
    assert out2["max_business_subdomains"] == 4


def test_v346_enrich_is_idempotent_and_preserves_legacy_tags():
    ns = _exec_tag_helpers()
    enrich = ns["_enrich_model_authoritative_tags"]
    dm = {"domains": [{"domain": "hr", "products": [
        {"name": "employee", "tags": "gov_transport_source_table=emp_history", "attributes": []}]}]}
    cfg = {"MODEL_CONVENTIONS": {"tag_prefix": "gov_transport_", "tag_suffix": ""}}
    enrich(dm, cfg, None)
    n1 = len(dm["domains"][0]["products"][0]["tag_set"])
    # legacy flat string preserved for backward compat
    assert dm["domains"][0]["products"][0]["tags"] == "gov_transport_source_table=emp_history"
    # second pass must not duplicate tags (derived view, re-computed cleanly)
    enrich(dm, cfg, None)
    n2 = len(dm["domains"][0]["products"][0]["tag_set"])
    assert n1 == n2, f"enrich not idempotent: {n1} -> {n2}"
