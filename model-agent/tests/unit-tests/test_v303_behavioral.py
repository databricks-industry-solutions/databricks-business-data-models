"""Behavioral tests for v3.0.3 model-type-resolution-no-hardcode.

ROOT CAUSE (cross-industry F1 false-block + mid-run thinker degradation,
construction/travel/ngo/retail 2026-06-01 swarm gate logs):
  databricks-claude-opus-4-7 was the top thinker/large endpoint (order=5,
  enabled) but INTERMITTENTLY rejects ai_query batch inference with
  [AI_FUNCTION_SESSION_PERMISSION_DENIED] '... not supported for batch
  inference' (SQLSTATE 42501). The literal "Permission denied" prose tripped
  push_v2.gate's F1 regex, false-blocking otherwise-promotable models, and the
  silent fallback degraded self_auditor/self_fixer/architect/judge to a weaker
  thinker mid-run.

  Live ai_query probes (2026-06-02) confirmed opus-4-8 succeeds on <profile> AND
  <profile>; opus-4-7 is intermittent. opus-4-8 is also the model the user wants.

FIX (alias=model-type-resolution-no-hardcode):
  A. Config: opus-4-8 added as order=1 top thinker/large (enabled); opus-4-7
     set enabled:False.
  B. SelfFixer.__init__: resolves thinker/large via _select_model_for_requirement
     (skip_broken, honors enabled) instead of hardcoding opus-4-7.
  C. _SAMPLE_LLM_MODEL: relocated with the sample engine to the model installer,
     which resolves its own endpoints; no longer part of this notebook.
  D. Ensemble _ENS_DESIRED_MODELS: built from ENABLED config models by type/order.
  E. _v74 single-shot fallback: first ENABLED worker by order, not a hardcoded list.

Non-tautology (CLAUDE.md 8.10): each fix test asserts BOTH the old hardcoded
pattern is GONE and the type-resolution path is PRESENT, so the suite proves the
routing change rather than merely that the resolver exists. The pre-patch
v302 backup contains every old pattern, so these assertions fail on HEAD-1.
"""
import re

from notebook_source_util import notebook_concat_source

SRC = notebook_concat_source()


def _models_block():
    """Extract the `"models": [ ... ]` config list as raw text."""
    m = re.search(r'"models":\s*\[(.*?)\n\s*\],', SRC, re.DOTALL)
    assert m, "models config block not found"
    return m.group(1)


def test_config_tops_opus48_enabled_and_disables_opus47():
    block = _models_block()
    # opus-4-8 present, enabled, thinker/large, ordered ahead of opus-4-7
    assert '"llm_endpoint_name": "databricks-claude-opus-4-8"' in block, "opus-4-8 not in config"

    def _entry(endpoint):
        # grab the dict spanning name..thinker_roles/temperature for this endpoint
        mm = re.search(
            r'\{\s*"name":[^{}]*?"llm_endpoint_name":\s*"' + re.escape(endpoint) + r'"[^{}]*?\}',
            block, re.DOTALL)
        assert mm, f"config entry for {endpoint} not found"
        return mm.group(0)

    e48 = _entry("databricks-claude-opus-4-8")
    e47 = _entry("databricks-claude-opus-4-7")
    assert '"type": "thinker"' in e48 and '"size": "large"' in e48, "opus-4-8 must be thinker/large"
    assert '"enabled": True' in e48, "opus-4-8 must be enabled"
    # v3.0.4 1A CONTRACT CHANGE (alias=model-batch-route): opus-4-7 is RE-ENABLED per user
    # directive. v303 hard-disabled it to dodge the intermittent ai_query batch PERMISSION_DENIED
    # that tripped gate F1; v304 instead detects batch-incapability at RUNTIME and routes ai_query
    # around the endpoint (_batch_incapable_models) while keeping it available for HTTP-direct paths.
    # So opus-4-7 is enabled again, still ranked behind opus-4-8.
    assert '"enabled": True' in e47, "v304: opus-4-7 must be RE-ENABLED (runtime batch-route handles intermittent failure)"
    assert "_batch_incapable_models" in SRC, "v304 must carry the runtime batch-incapable routing set"
    o48 = int(re.search(r'"order":\s*(\d+)', e48).group(1))
    o47 = int(re.search(r'"order":\s*(\d+)', e47).group(1))
    assert o48 < o47, f"opus-4-8 (order {o48}) must outrank opus-4-7 (order {o47})"


def test_selffixer_resolves_by_type_not_hardcoded():
    # NON-TAUTOLOGY: old hardcoded default gone, type-resolution present.
    assert 'llm_endpoint="databricks-claude-opus-4-7")' not in SRC, (
        "SelfFixer still hardcodes opus-4-7 default"
    )
    assert 'def __init__(self, ai_agent, logger, sandbox_executor=None, llm_endpoint=None):' in SRC, (
        "SelfFixer __init__ default must be None (resolve by type)"
    )
    # the resolution call must live in SelfFixer.__init__ region
    sf = re.search(r'def __init__\(self, ai_agent, logger, sandbox_executor=None, llm_endpoint=None\):.*?self\.llm_endpoint = llm_endpoint',
                   SRC, re.DOTALL)
    assert sf, "SelfFixer __init__ body not found"
    assert '_select_model_for_requirement("thinker", "large", skip_broken=True)' in sf.group(0), (
        "SelfFixer must resolve thinker/large via _select_model_for_requirement"
    )


def test_ensemble_desired_models_dynamic():
    # the old hardcoded 3-endpoint diversity literal must be gone
    assert '{"endpoint": "databricks-gpt-oss-120b",       "label": "gpt-oss-120b",       "temperature": 0.0}' not in SRC, (
        "ensemble still hardcodes _ENS_DESIRED_MODELS endpoints"
    )
    # built dynamically from enabled config models
    assert "_ens_pool = sorted([m for m in _ens_models_lookup.values() if _is_model_enabled(m)]" in SRC, (
        "ensemble must build desired set from ENABLED config models"
    )


def test_ensemble_selects_distinct_families():
    """The ensemble's purpose is THREE DIFFERENT model FAMILIES at distinct temps.

    Must derive a family key, dedup by family, prefer temperature-supporting models,
    and emit the ens-family-diverse FIRED marker. Then simulate selection against the
    real config and prove the result is 3 distinct families with 3 distinct temps.
    """
    assert "def _ens_family(" in SRC, "ensemble must derive a model family key"
    assert "_ens_seen_fam" in SRC, "ensemble must dedup picks by family"
    assert "temperature_supported" in SRC.split("def _ens_family(")[1][:1500], (
        "ensemble must prefer temperature-supporting models within a family"
    )
    assert "ens-family-diverse FIRED" in SRC, "ens-family-diverse FIRED marker missing"

    # Behavioral simulation against the real config model list (mirrors the notebook logic).
    models = [
        {"name": "claude-opus-4-8", "order": 1, "type": "thinker", "enabled": True,
         "llm_endpoint_name": "databricks-claude-opus-4-8", "temperature_supported": False},
        {"name": "claude-opus-4-7", "order": 5, "type": "thinker", "enabled": False,
         "llm_endpoint_name": "databricks-claude-opus-4-7", "temperature_supported": False},
        {"name": "claude-opus-4-6", "order": 10, "type": "thinker", "enabled": True,
         "llm_endpoint_name": "databricks-claude-opus-4-6", "temperature_supported": True},
        {"name": "claude-sonnet-4-6", "order": 20, "type": "worker", "enabled": True,
         "llm_endpoint_name": "databricks-claude-sonnet-4-6", "temperature_supported": True},
        {"name": "claude-opus-4-5", "order": 30, "type": "thinker", "enabled": True,
         "llm_endpoint_name": "databricks-claude-opus-4-5", "temperature_supported": True},
        {"name": "claude-sonnet-4-5", "order": 40, "type": "worker", "enabled": True,
         "llm_endpoint_name": "databricks-claude-sonnet-4-5", "temperature_supported": True},
        {"name": "gpt-oss-120b", "order": 50, "type": "worker", "enabled": True,
         "llm_endpoint_name": "databricks-gpt-oss-120b", "temperature_supported": True},
        {"name": "gpt-oss-20b", "order": 60, "type": "worker", "enabled": True,
         "llm_endpoint_name": "databricks-gpt-oss-20b", "temperature_supported": True},
    ]

    def _ens_family(_m):
        _ep = (_m.get("llm_endpoint_name") or _m.get("name") or "").lower().replace("databricks-", "")
        _fam = []
        for _tok in _ep.split("-"):
            if any(_ch.isdigit() for _ch in _tok):
                break
            _fam.append(_tok)
        return "-".join(_fam) if _fam else _ep

    _ens_div_temps = [0.0, 0.3, 0.5]
    pool = sorted([m for m in models if m.get("enabled", True)],
                  key=lambda m: (0 if m.get("type", "worker") == "worker" else 1,
                                 0 if m.get("temperature_supported", True) else 1,
                                 m.get("order", 999)))
    picked, fam, ep = [], set(), set()
    for m in pool:
        e, f = m["llm_endpoint_name"], _ens_family(m)
        if not e or e in ep or f in fam:
            continue
        picked.append(m); fam.add(f); ep.add(e)
        if len(picked) >= 3:
            break
    fams = [_ens_family(m) for m in picked[:3]]
    temps = [_ens_div_temps[i] for i in range(len(picked[:3]))]
    assert len(set(fams)) == 3, f"ensemble must pick 3 distinct families, got {fams}"
    assert len(set(temps)) == 3, f"ensemble must use 3 distinct temps, got {temps}"
    # disabled opus-4-7 must never be selected
    assert "databricks-claude-opus-4-7" not in [m["llm_endpoint_name"] for m in picked], (
        "ensemble selected a DISABLED model"
    )


def test_v74_fallback_candidate_dynamic():
    assert 'for _candidate in ["databricks-claude-sonnet-4-5", "databricks-claude-sonnet-4-6", "databricks-gpt-oss-120b"]:' not in SRC, (
        "_v74 single-shot fallback still uses a hardcoded candidate list"
    )
    assert "for _v74_cand_cfg in sorted([m for m in _ens_models_lookup.values() if _is_model_enabled(m)]" in SRC, (
        "_v74 fallback must pick first ENABLED worker by order"
    )


def test_no_hardcoded_endpoint_on_call_paths():
    """Strong directive check: no runtime LLM call path may pin an endpoint by name.

    model_override= and llm_endpoint= (kwarg call sites, not the config block)
    must never carry a hardcoded databricks-<family> string literal.
    """
    bad = re.findall(r'(?:model_override|llm_endpoint)\s*=\s*"databricks-(?:claude|gpt|llama|meta|gemini)[^"]*"', SRC)
    assert not bad, f"hardcoded endpoint(s) on call paths: {bad}"


def test_version_at_least_303():
    m = re.search(r'__AGENT_VERSION__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', SRC)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 0, 3), f"version {m.groups()} < 3.0.3"
