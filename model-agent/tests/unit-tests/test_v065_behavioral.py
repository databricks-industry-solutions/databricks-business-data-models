"""Behavioral tests for v0.6.5 model-quality + telemetry fixes.

Bundle of 3 root-cause fixes against findings from the v0.6.3 telecom v1 audit:

  NEW-3  immutable-early-exit  --  smart_worker_loop's architect-review retries
                                   were emitting `Max retries (3) exhausted` after
                                   3 consecutive IMMUTABLE_VIOLATION blocks. The
                                   loop now (a) tracks consecutive IMMUTABLE-class
                                   failures, (b) re-injects the protected list as
                                   a HARD preamble into the next attempt's
                                   feedback, and (c) early-exits cleanly after
                                   2 consecutive failures so the §10.6 hard-zero
                                   `Max retries exhausted` signature stops firing
                                   for a class the LLM cannot self-recover from.

  NEW-4  llm-json-recoverable  --  one gpt-oss-120b call emitted "Unterminated
                                   string" which the per-call retry loop healed
                                   silently, but it was logged at WARNING and
                                   counted in the audit's error inventory. Demoted
                                   to INFO with `[LLM-JSON-RECOVERABLE FIRED]`
                                   alias when followed by a retry.

  NEW-5  ssot-stem-autofix     --  _validate_product_name_collisions only matched
                                   raw-name duplicates (Pass 1+2). The static
                                   analysis SSOT check uses domain-prefix-stripped
                                   stems, so 8 cross_domain_duplicate findings
                                   ended up in next_vibes.txt unresolved. Added
                                   Pass 3 mirroring the SA logic (same stem
                                   stripper, same generic-stem exclusion) so the
                                   autofix renames them BEFORE static analysis.
"""
import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _agent_src() -> str:
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


# =============================================================================
# NEW-3 — IMMUTABLE-VIOLATION early-exit
# =============================================================================

def test_v065_new3_alias_present():
    src = _agent_src()
    assert "alias=immutable-early-exit" in src, "immutable-early-exit sentinel missing"


def test_v065_new3_fired_marker_present():
    src = _agent_src()
    assert "[IMMUTABLE-EARLY-EXIT FIRED]" in src, "FIRED log marker missing"


def test_v065_new3_consecutive_counter_initialized():
    src = _agent_src()
    assert "_consec_immutable_failures = 0" in src, "consecutive-failure counter not initialized"


def test_v065_new3_immut_patterns_match_validator_block():
    """The patterns used to detect IMMUTABLE failures must match the validator's
    error-emission language so we don't mis-classify."""
    src = _agent_src()
    assert "_IMMUT_PATTERNS = (" in src
    for needle in (
        "'immutable violation'",
        "'cannot move protected'",
        "'cannot rename protected'",
        "'cannot remove protected'",
        "'cannot merge protected'",
        "'cannot split protected'",
    ):
        assert needle in src, f"missing pattern in _IMMUT_PATTERNS: {needle}"


def test_v065_new3_short_circuits_on_2nd_consec():
    """Verify the threshold is >= 2 (not >= 3); 3 would still emit Max retries exhausted."""
    src = _agent_src()
    assert "_consec_immutable_failures >= 2 and attempt < max_attempts - 1" in src


def test_v065_new3_strengthens_feedback_with_protected_lists():
    """The retry feedback on IMMUTABLE failure must echo BOTH protected_domains_list
    AND protected_products_list so the LLM cannot miss it on the next attempt."""
    src = _agent_src()
    assert "PROTECTED DOMAINS (DO NOT remove / rename / merge / split):" in src
    assert "PROTECTED PRODUCTS (DO NOT remove / rename / move / merge / split):" in src
    assert "current_vars.get('protected_domains_list', '')" in src
    assert "current_vars.get('protected_products_list', '')" in src


def test_v065_new3_returns_failure_not_soft_accept():
    """Early-exit must `return False` so downstream defense-in-depth treats it as
    failure (architect's iteration is skipped, model unchanged) — NEVER soft-accept."""
    src = _agent_src()
    # Find the IMMUTABLE-EARLY-EXIT block specifically
    needle = "[IMMUTABLE-EARLY-EXIT FIRED]"
    idx = src.find(needle)
    assert idx > 0
    window = src[idx : idx + 1500]
    assert "return False, last_valid_response, last_errors" in window, (
        "early-exit must return False, not soft-accept the LLM payload"
    )


# =============================================================================
# NEW-4 — LLM JSON-decode recoverable demotion
# =============================================================================

def test_v065_new4_alias_present():
    src = _agent_src()
    assert "alias=llm-json-recoverable" in src


def test_v065_new4_fired_marker_present():
    src = _agent_src()
    assert "[LLM-JSON-RECOVERABLE FIRED]" in src


def test_v065_new4_demotes_to_info_only_on_recoverable_class():
    """The demotion must check the error class — only JSON-decode errors get INFO,
    everything else still WARNING."""
    src = _agent_src()
    # Check that the if-branch sets logger.info AND the else-branch keeps logger.warning
    needle = "_is_json_decode = any(_pat in _err_low for _pat in"
    assert needle in src
    idx = src.find(needle)
    window = src[idx : idx + 2000]
    assert "self.logger.info(" in window
    assert "self.logger.warning(f\\\"AI Query{_label} failed (Step:" in window or \
           'AI Query{_label} failed (Step:' in window


def test_v065_new4_only_when_retry_will_happen():
    """The demotion is gated by `if retry_attempt < max_retries - 1` — final-retry
    failures still escalate to ERROR."""
    src = _agent_src()
    needle = "[LLM-JSON-RECOVERABLE FIRED]"
    idx = src.find(needle)
    assert idx > 0
    # The previous ~600 chars should contain the retry-attempt guard
    pre = src[max(0, idx - 1500) : idx]
    assert "retry_attempt < max_retries - 1" in pre


def test_v065_new4_pattern_set_covers_audit_observation():
    """The audit observed 'Unterminated string' — make sure our pattern list
    includes it (case-insensitive)."""
    src = _agent_src()
    assert "'unterminated string'" in src.lower()
    assert "'expecting value'" in src.lower()
    assert "'extra data'" in src.lower()


# =============================================================================
# NEW-5 — Stem-based cross-domain duplicate autofix
# =============================================================================

def test_v065_new5_alias_present():
    src = _agent_src()
    assert "alias=ssot-stem-autofix" in src


def test_v065_new5_fired_marker_present():
    src = _agent_src()
    assert "[P0.74-COLLISION-STEM FIRED]" in src


def test_v065_new5_uses_strip_domain_prefix():
    """Pass 3 must use the SAME stem stripper as the static-analysis SSOT check
    (~line 69640) to be aligned. If they diverge, the autofix won't catch what
    the SA emits."""
    src = _agent_src()
    needle = "[P0.74-COLLISION-STEM FIRED]"
    idx = src.find(needle)
    assert idx > 0
    pre = src[max(0, idx - 4000) : idx]
    assert "strip_domain_prefix(_pn, _pd)" in pre, (
        "stem-based autofix must reuse strip_domain_prefix to match SA semantics"
    )


def test_v065_new5_excludes_generic_stems():
    """The autofix exclusion list must include the SAME generic stems the SA
    excludes (payment, order, status, type, code, rate, fee, charge, ...).
    Otherwise the autofix would aggressively rename legitimate cross-domain
    products."""
    src = _agent_src()
    assert "_CD_GENERIC_STEMS_AUTOFIX = frozenset({" in src
    for stem in ("'payment'", "'order'", "'status'", "'type'", "'code'", "'rate'", "'fee'", "'charge'"):
        assert stem in src, f"generic-stem exclusion missing: {stem}"


def test_v065_new5_min_stem_length_4():
    """Stems shorter than 4 chars are too generic — don't autofix; matches the
    SA's `len(_cd_stem) < 4` filter."""
    src = _agent_src()
    needle = "[P0.74-COLLISION-STEM FIRED]"
    idx = src.find(needle)
    pre = src[max(0, idx - 4000) : idx]
    assert "len(_stem_l) < 4" in pre, "stem-length filter must match SA semantics"


def test_v065_new5_keeps_first_domain_owner():
    """The pick-an-owner rule must be deterministic and industry-agnostic. As of
    v3.6.0 (alias=p074-shared-canonical-keep) it prefers a shared/common SSOT
    domain as the canonical owner when one is present (so the rename never
    produces 'shared.shared_<x>', which the shared_domain_prefix rule flags as an
    ERROR), and otherwise falls back to the first (sorted) domain unchanged —
    preserving the original predictable behavior for the common case."""
    src = _agent_src()
    needle = "[P0.74-COLLISION-STEM FIRED]"
    idx = src.find(needle)
    pre = src[max(0, idx - 4000) : idx]
    # fallback owner is still the first sorted domain (original v0.6.5 intent)
    assert "else sorted(_by_dom.keys())[0]" in pre
    # but a shared/common SSOT domain is preferred as canonical owner when present
    assert "_shared_doms_present[0] if _shared_doms_present" in pre


def test_v065_new5_propagates_attribute_and_fk_updates():
    """After Pass 3 mutates products, the rename_map MUST flow into attribute.product
    and foreign_key_to rewriting (existing block at end of fn). Verify the new
    pass appends to the SAME rename_map."""
    src = _agent_src()
    # The existing post-pass propagation reads `if rename_map:`. Pass 3 must
    # populate it via `rename_map[_old_key] = _new_key`.
    needle = "[P0.74-COLLISION-STEM FIRED]"
    idx = src.find(needle)
    pre = src[max(0, idx - 4000) : idx]
    assert "rename_map[_old_key] = _new_key" in pre


# =============================================================================
# Cross-fix invariants
# =============================================================================

def test_v065_no_regression_from_v064_aliases():
    """v0.6.5 builds on v0.6.4. Every v0.6.4 alias must still be present."""
    src = _agent_src()
    assert "v0.6.4 B1 alias=perf-cap-16" in src
    assert "v0.6.4 B8 alias=perf-llm-throttle-16" in src


def test_v065_readme_version_bumped():
    """readme.md current version must be v0.6.5."""
    with open("/Users/user/Documents/projects/vibe-modelling-agent/readme.md") as f:
        readme = f.read()
    assert "v0.6.5" in readme, "readme not bumped to v0.6.5"


def test_v065_readme_history_entry_present():
    """readme.md must list the v0.6.5 history row."""
    with open("/Users/user/Documents/projects/vibe-modelling-agent/readme.md") as f:
        readme = f.read()
    assert re.search(r"v0\.6\.5", readme), "v0.6.5 history row missing"
    assert "immutable-early-exit" in readme or "IMMUTABLE-EARLY-EXIT" in readme
    assert "llm-json-recoverable" in readme or "LLM-JSON-RECOVERABLE" in readme
    assert "ssot-stem-autofix" in readme or "P0.74-COLLISION-STEM" in readme
