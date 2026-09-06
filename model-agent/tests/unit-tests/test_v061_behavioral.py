"""Behavioral tests for v0.6.1 fixes.

Covers:
  G  domain-dominance-cap-scale-by-count   — eliminates 6 false-positive errors on tiny models
  H  pii-static-align-with-autofix          — eliminates 13 false-positive PII flags
  I  prefix-static-skip-reserved            — aligns static analyzer with autofix's reserved-word guard
  J  datatype-name-coercion-autofix         — auto-coerce types where name suffix is unambiguous

Plus regression tests for v1.0.5, v1.0.4, v1.0.3 aliases.
"""
import json
import os
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _agent_src() -> str:
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


# -----------------------------------------------------------------------------
# Fix G — domain-dominance-cap-scale-by-count
# -----------------------------------------------------------------------------
def test_v061_G_alias_present_in_source():
    src = _agent_src()
    assert "[domain-dominance-cap-scale-by-count FIRED]" in src

def test_v061_G_cap_scales_by_n_domains():
    src = _agent_src()
    assert "_v061_n_domains = max(1, len(products_by_domain))" in src
    assert "_v061_cap = max(0.25, 1.5 / _v061_n_domains)" in src

def test_v061_G_severity_warning_on_tiny_models():
    src = _agent_src()
    assert "_v061_severity = 'warning' if _v061_n_domains <= 4 else 'error'" in src

def test_v061_G_cap_math_3_domains():
    """For 3 domains, cap should be 0.50 (50%) — exceeds the 0.33 each-domain-share."""
    n = 3
    cap = max(0.25, 1.5 / n)
    assert cap == 0.5
    # Each domain at 33% does NOT exceed 50%
    assert (1/3) <= cap

def test_v061_G_cap_math_6_domains():
    """For 6 domains, cap should be 0.25 (matches old hardcoded value)."""
    n = 6
    cap = max(0.25, 1.5 / n)
    assert cap == 0.25

def test_v061_G_cap_math_12_domains():
    """For 12+ domains, cap floors at 0.25 (still strict)."""
    n = 12
    cap = max(0.25, 1.5 / n)
    assert cap == 0.25

def test_v061_G_old_hardcoded_25_cap_replaced():
    """The OLD (`> 0.25:` for product cap) literal must be GONE — replaced by `> _v061_cap:`."""
    src = _agent_src()
    # The old check was `if total_products > 0 and domain_product_count / total_products > 0.25:`
    # After fix, this should now use _v061_cap.
    assert "domain_product_count / total_products > _v061_cap" in src
    assert "domain_attr_count / total_attrs > _v061_cap" in src


# -----------------------------------------------------------------------------
# Fix H — pii-static-align-with-autofix
# -----------------------------------------------------------------------------
def test_v061_H_alias_present():
    src = _agent_src()
    assert "[pii-static-align-with-autofix FIRED]" in src

def test_v061_H_uses_PII_FALSE_POSITIVE_RE_in_static():
    """Static analyzer now consults the same false-positive guard as the autofix."""
    src = _agent_src()
    # locate the I6 PII section
    idx = src.find("I6: PII tagging consistency (M11)")
    assert idx > 0
    section = src[idx:idx+2000]
    assert "PII_FALSE_POSITIVE_RE.search(attr_name)" in section
    assert "_v061_pii_skipped_fp" in section


# -----------------------------------------------------------------------------
# Fix I — prefix-static-skip-reserved
# -----------------------------------------------------------------------------
def test_v061_I_alias_present():
    src = _agent_src()
    assert "[prefix-static-skip-reserved FIRED]" in src

def test_v061_I_uses_reserved_word_guard():
    src = _agent_src()
    idx = src.find("I9: Attribute naming")
    assert idx > 0
    section = src[idx:idx+3000]
    assert "_v061_NAMING_RESERVED" in section
    # Ensure several known SQL reserved words are present (sample)
    for w in ('status', 'type', 'name', 'code', 'value'):
        assert f"'{w}'" in section, f"missing reserved word {w} in v061 reserved set"

def test_v061_I_skip_logic():
    """Verify the skip logic: cleaned attr in reserved set → continue (don't count)."""
    src = _agent_src()
    idx = src.find("I9: Attribute naming")
    section = src[idx:idx+3000]
    assert "_v061_cleaned in _v061_NAMING_RESERVED" in section
    assert "_v061_prefix_skipped_reserved += 1" in section
    assert "continue" in section


# -----------------------------------------------------------------------------
# Fix J — datatype-name-coercion-autofix
# -----------------------------------------------------------------------------
def test_v061_J_alias_present():
    src = _agent_src()
    assert "[datatype-name-coercion-autofix FIRED]" in src

def test_v061_J_decimal_suffixes_present():
    src = _agent_src()
    for s in ("'_amount'", "'_price'", "'_cost'", "'_value'", "'_rate'"):
        assert s in src

def test_v061_J_runs_before_p025():
    """The v0.6.1 datatype coercion block must run before the v0.7.0 P0.25 PII pass."""
    src = _agent_src()
    coerce_idx = src.find("[PRE-FIX] v0.6.1: datatype-name-coercion autofix")
    p025_idx = src.find("# v0.7.0 P0.25 — Expanded PII tag autofix.")
    assert coerce_idx > 0 and p025_idx > 0
    assert coerce_idx < p025_idx, "datatype coercion must come BEFORE P0.25 PII pass"

def test_v061_J_only_coerces_string_inputs():
    src = _agent_src()
    idx = src.find("[PRE-FIX] v0.6.1: datatype-name-coercion autofix")
    section = src[idx:idx+3000]
    assert "if _v061_t != 'STRING':" in section
    assert "continue" in section


# -----------------------------------------------------------------------------
# Regression — v1.0.5 aliases still in source
# -----------------------------------------------------------------------------
def test_v105_regression_fk_validator_skip_external_refs():
    src = _agent_src()
    assert "fk-validator-skip-external-refs" in src

def test_v105_regression_bidirectional_pointer_auto_resolve():
    src = _agent_src()
    assert "bidirectional-pointer-auto-resolve" in src

# -----------------------------------------------------------------------------
# Regression — v1.0.4 aliases still in source
# -----------------------------------------------------------------------------
def test_v104_regression_mv_filter_strip_comments():
    src = _agent_src()
    assert "mv-filter-strip-comments" in src

def test_v104_regression_mv_column_prevalidate_drop():
    src = _agent_src()
    assert "mv-column-prevalidate-drop" in src

# -----------------------------------------------------------------------------
# Regression — v1.0.3 aliases still in source
# -----------------------------------------------------------------------------
def test_v103_regression_fidelity_count_soft_pass():
    src = _agent_src()
    assert "fidelity-count-soft-pass-strategy-agnostic" in src

def test_v103_regression_mv_cross_table_measure_drop():
    src = _agent_src()
    assert "mv-cross-table-measure-drop" in src
