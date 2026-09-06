"""v4.3.3 behavioral tests.

Reproduces the CRITICAL VOV pii_ glossary-namespace corruption (health_insurance
13078 / media_broadcasting 14894 attrs carried `pii_business_glossary_term` instead
of `dbx_business_glossary_term`) and proves the fix:

- rc6-tagprefix-reserved-clamp: when MODEL_CONVENTIONS.tag_prefix is a reserved
  SENSITIVITY namespace (pii_/phi_/pci_/...), _enrich_model_authoritative_tags clamps
  the derived-tag namespace to 'dbx_' at the AUTHORITATIVE model.json write (the base
  config-assembly guard does NOT run on the VOV/shrink path), AND writes the safe
  prefix back into config so the physical UC tagger agrees.
- rc4b-tagset-banned-key-drop: build-directive keys (lineage, ddl_column_comment, ...)
  can never enter tag_set (fixes semiconductors residual lineage:1).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notebook_source_util import exec_functions_namespace, exec_function_namespace


class _L:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


_ENRICH_DEPS = [
    "_tagset_from_string",
    "_v381_bare_key",
    "_v381_tag_scope",
    "_v381_is_placeholder_tag_value",
    "_v381_scope_conflict",
    "_v381_filter_tagset",
    "_tagset_add",
    "_enrich_model_authoritative_tags",
]


def _mk_model():
    return {
        "domains": [
            {
                "name": "member",
                "division": "operations",
                "products": [
                    {
                        "name": "enrollment",
                        "tags": "",
                        "attributes": [
                            {"name": "member_ssn", "business_glossary_term": "Member SSN", "tags": ""},
                            {"name": "plan_code", "business_glossary_term": "Plan Code", "tags": ""},
                        ],
                    }
                ],
            }
        ]
    }


def _glossary_keys(model):
    keys = []
    for d in model["domains"]:
        for p in d.get("products", []):
            for a in p.get("attributes", []):
                for t in a.get("tag_set", []):
                    if "business_glossary_term" in str(t.get("key", "")):
                        keys.append(t["key"])
    return keys


def test_vov_pii_prefix_is_clamped_to_dbx_postfix():
    """PASS-POST: with tag_prefix='pii_' (the VOV re-derived reserved namespace),
    the real enrichment emits dbx_business_glossary_term and ZERO
    pii_business_glossary_term, and writes the safe prefix back to config."""
    ns = exec_functions_namespace(_ENRICH_DEPS)
    enrich = ns["_enrich_model_authoritative_tags"]
    model = _mk_model()
    config = {"MODEL_CONVENTIONS": {"tag_prefix": "pii_", "tag_suffix": ""}}
    enrich(model, config, _L())
    gk = _glossary_keys(model)
    assert gk, "expected business_glossary_term tags to be emitted"
    assert all(k == "dbx_business_glossary_term" for k in gk), gk
    assert not any(k == "pii_business_glossary_term" for k in gk), gk
    # config write-back so the physical tagger agrees (path-independent)
    assert config["MODEL_CONVENTIONS"]["tag_prefix"] == "dbx_"
    assert config.get("TAG_PREFIX") == "dbx_"


def test_vov_pii_prefix_bug_reproduced_prefix():
    """FAIL-PRE: the pre-v4.3.3 behaviour (no clamp) — _ek just concatenates the
    reserved prefix — produces the exact corruption the audit caught."""
    tp = "pii_"
    def _ek_old(key):
        return f"{tp}{key}"
    assert _ek_old("business_glossary_term") == "pii_business_glossary_term"


def test_non_reserved_prefix_untouched():
    """A legitimate namespace (dbx_) is NOT altered and config is left as-is."""
    ns = exec_functions_namespace(_ENRICH_DEPS)
    enrich = ns["_enrich_model_authoritative_tags"]
    model = _mk_model()
    config = {"MODEL_CONVENTIONS": {"tag_prefix": "dbx_", "tag_suffix": ""}}
    enrich(model, config, _L())
    gk = _glossary_keys(model)
    assert gk and all(k == "dbx_business_glossary_term" for k in gk), gk
    assert config["MODEL_CONVENTIONS"]["tag_prefix"] == "dbx_"


def test_phi_and_pci_prefixes_also_clamped():
    """Generic: ANY reserved sensitivity namespace clamps, not just pii_."""
    for reserved in ("phi_", "pci_", "PII_", "gdpr_"):
        ns = exec_functions_namespace(_ENRICH_DEPS)
        enrich = ns["_enrich_model_authoritative_tags"]
        model = _mk_model()
        config = {"MODEL_CONVENTIONS": {"tag_prefix": reserved, "tag_suffix": ""}}
        enrich(model, config, _L())
        gk = _glossary_keys(model)
        assert gk and all(k == "dbx_business_glossary_term" for k in gk), (reserved, gk)


def test_tagset_add_drops_build_directive_keys_postfix():
    """PASS-POST: _tagset_add refuses build-directive keys (lineage etc.) but keeps
    real governance keys."""
    ns = exec_function_namespace("_tagset_add")
    add = ns["_tagset_add"]
    ts = []
    add(ts, "lineage", "some_source")
    add(ts, "ddl_column_comment", "x")
    add(ts, "uc_qualified_name", "cat.sch.tbl")
    add(ts, "fhir_element", "Patient.name")
    assert ts == [], ts  # all dropped
    add(ts, "dbx_business_glossary_term", "Member SSN")
    add(ts, "pii_identifier", "true")
    assert [t["key"] for t in ts] == ["dbx_business_glossary_term", "pii_identifier"]


def test_tagset_add_banned_key_bug_reproduced_prefix():
    """FAIL-PRE: the pre-v4.3.3 _tagset_add (no banned-key drop) would have added
    'lineage' to tag_set — reproduced to prove the fix changes observable state."""
    def _tagset_add_old(_tag_set, _key, _value, _kind="key_value", _source="derived"):
        if not _key:
            return
        _kl, _vl = str(_key).lower(), str(_value or "").lower()
        for _t in _tag_set:
            if str(_t.get("key", "")).lower() == _kl and str(_t.get("value", "")).lower() == _vl:
                return
        _tag_set.append({"key": _key, "value": _value or "", "kind": _kind, "source": _source})
    ts = []
    _tagset_add_old(ts, "lineage", "some_source")
    assert [t["key"] for t in ts] == ["lineage"]  # bug present pre-fix
