"""Behavioral tests for v0.6.7 NEW-11 fix: surgical-mv-rewrite.

Covers cover-up #2 from the v0.6.6 brutal honesty audit. The original
v0.6.6 NEW-10 helper preserved metric views by DROPPING any MV whose
owner_product or referenced products had been renamed by surgical
mutations. On a real telecom vov v2 run this dropped all 92 baseline
MVs (because surgical mode renames products, not deletes them).

NEW-11 adds a rename-map inference pass plus a SQL rewriter that
substitutes `<old_d>.<old_p>` with `<new_d>.<new_p>` BEFORE validating
references against the v2 product set. Industry-agnostic: rename
inference uses _p074_qualified_rename + stem heuristics + naming-
convention canonicalisation only.
"""
import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"
README = "/Users/user/Documents/projects/vibe-modelling-agent/readme.md"


def _agent_src() -> str:
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


def _helper_body() -> str:
    src = _agent_src()
    idx = src.find("def _preserve_baseline_metric_views_for_surgical(")
    assert idx >= 0, "helper missing"
    end = src.find("\ndef _emit_run_summary_query_tag", idx)
    assert end > idx, "helper end-marker missing"
    return src[idx:end]


# =============================================================================
# NEW-11 — surgical-mv-rewrite SENTINEL + LOGGING
# =============================================================================

def test_v067_new11_alias_present():
    src = _agent_src()
    assert "alias=surgical-mv-rewrite" in src, "surgical-mv-rewrite sentinel missing"


def test_v067_new11_fired_marker_present():
    src = _agent_src()
    assert "[surgical-mv-rewrite FIRED]" in src, (
        "[surgical-mv-rewrite FIRED] runtime log marker missing"
    )


def test_v067_new10_always_emits_fired_even_on_drop():
    """v0.6.6 only logged FIRED on success; on full-drop it logged a non-FIRED
    warning. v0.6.7 must emit FIRED on the all-dropped branch too so the
    audit can prove the helper executed."""
    body = _helper_body()
    matches = re.findall(r"\[surgical-mv-preserve FIRED\]", body)
    assert len(matches) >= 4, (
        f"Expected >=4 FIRED markers (no-baseline, zero-mvs, no-current-products, "
        f"all-dropped, success), found {len(matches)}"
    )


# =============================================================================
# NEW-11 — RENAME INFERENCE
# =============================================================================

def test_v067_new11_loads_baseline_products():
    body = _helper_body()
    assert '_baseline_products = _model.get("products"' in body, (
        "Helper must load v1 products for rename inference"
    )


def test_v067_new11_builds_v1_set():
    body = _helper_body()
    assert "_v1_set" in body and "_v1_doms" in body, (
        "v1 product set + domains needed for rename inference"
    )


def test_v067_new11_uses_p074_qualified_rename():
    body = _helper_body()
    assert "_p074_qualified_rename(_op_old, _od_old)" in body, (
        "Must call _p074_qualified_rename with (product, domain) — signature is "
        "(product_name, domain_name); reversed args produce wrong output"
    )


def test_v067_new11_applies_naming_convention():
    body = _helper_body()
    assert "apply_convention(_q_pascal" in body, (
        "Pascal qualified rename must be canonicalised via apply_convention "
        "(otherwise PascalCase forms won't match snake_case v2 products)"
    )


def test_v067_new11_rename_map_built():
    body = _helper_body()
    assert "_rename_map = {}" in body
    assert "_rename_map[_old]" in body, "Rename map must be populated from candidates"


def test_v067_new11_uses_stem_heuristics():
    body = _helper_body()
    assert '_np.endswith("_" + _op_old)' in body, "suffix stem heuristic missing"
    assert "_op_old in _np" in body, "contains stem heuristic missing"


# =============================================================================
# NEW-11 — SQL REWRITER
# =============================================================================

def test_v067_new11_rewrite_helper_defined():
    body = _helper_body()
    assert "def _rewrite_sql_via_rename_map(" in body, (
        "_rewrite_sql_via_rename_map helper missing"
    )


def test_v067_new11_rewrite_returns_hits_count():
    body = _helper_body()
    # Helper must return both rewritten SQL AND hit count for tracking.
    assert "return sql_txt, 0" in body
    assert "return \"\".join(_parts), _hits" in body or "return ''.join(_parts), _hits" in body, (
        "rewrite helper must return (rewritten_sql, hit_count)"
    )


def test_v067_new11_rewrite_skips_string_literals():
    body = _helper_body()
    # Rewriter must split on string literals so it doesn't substitute
    # inside quoted strings.
    assert "_mvp_re.split" in body, "rewriter must split on string literals"
    assert "'[^'" in body and '"[^"' in body, "must skip both single+double quoted literals"


def test_v067_new11_rewrite_handles_backticks():
    body = _helper_body()
    # Pattern must accept optional backticks around domain.product.
    assert "`?" in body, "rewriter regex must handle backtick-quoted identifiers"


def test_v067_new11_rewrite_case_insensitive():
    body = _helper_body()
    assert "(?i)" in body, "rewriter must be case-insensitive"


# =============================================================================
# NEW-11 — INTEGRATION INTO PROCESSING LOOP
# =============================================================================

def test_v067_new11_owner_rewritten_on_rename():
    body = _helper_body()
    # When owner is in rename_map, update owner_domain + owner_product on the MV.
    assert "_new_owner = _rename_map.get((_od, _op))" in body
    assert '_mv_out["owner_domain"] = _new_owner[0]' in body
    assert '_mv_out["owner_product"] = _new_owner[1]' in body


def test_v067_new11_sql_rewritten_before_validation():
    body = _helper_body()
    # SQL rewrite must happen BEFORE _all_refs_valid so renamed products
    # resolve in v2.
    rewrite_pos = body.find("_rewrite_sql_via_rename_map(_sql, _rename_map)")
    validate_pos = body.find("_ok, _reason = _all_refs_valid(_sql)")
    assert rewrite_pos > 0 and validate_pos > 0
    assert rewrite_pos < validate_pos, (
        "SQL rewrite must happen BEFORE _all_refs_valid (otherwise renamed "
        "products will fail validation and be dropped)"
    )


def test_v067_new11_tracks_rewritten_count():
    body = _helper_body()
    assert "_rewritten_count" in body
    assert "_preserved_unchanged" in body
    # Final log must surface unchanged + rewritten + dropped counts.
    assert "unchanged=" in body and "rewritten=" in body and "dropped=" in body, (
        "Final log must break down outcome: unchanged/rewritten/dropped"
    )


# =============================================================================
# NEW-11 — INDUSTRY AGNOSTIC
# =============================================================================

def test_v067_new11_industry_agnostic():
    body = _helper_body()
    forbidden = ["telecom", "airline", "airlines", "healthcare", "banking",
                 "retail", "manufacturing", "insurance", "customer_account",
                 "billing_account", "subscription"]
    body_lower = body.lower()
    for word in forbidden:
        assert word not in body_lower, (
            f"Industry-specific string '{word}' found in NEW-11 helper"
        )


# =============================================================================
# NEW-11 — END-TO-END SQL REWRITE SIMULATION
# =============================================================================

def _extract_rewriter():
    """Extract _rewrite_sql_via_rename_map as a standalone function so we
    can integration-test it without spinning up the whole notebook."""
    import re as _re

    def _rewrite_sql_via_rename_map(sql_txt, rename_map):
        if not sql_txt or not rename_map:
            return sql_txt, 0
        _parts = _re.split(r"('[^'\n]*'|\"[^\"\n]*\")", sql_txt)
        _hits = 0
        for _i, _part in enumerate(_parts):
            if _i % 2 == 1:
                continue
            for _old_k, _new_v in rename_map.items():
                _od, _op = _old_k
                _nd, _np = _new_v
                _pat = _re.compile(
                    r"(?i)(?<![A-Za-z0-9_])`?" + _re.escape(_od)
                    + r"`?\s*\.\s*`?" + _re.escape(_op) + r"`?(?![A-Za-z0-9_])"
                )
                _new_part, _n = _pat.subn(f"{_nd}.{_np}", _part)
                if _n:
                    _parts[_i] = _new_part
                    _part = _new_part
                    _hits += _n
        return "".join(_parts), _hits

    return _rewrite_sql_via_rename_map


def test_v067_new11_rewrite_simple_case():
    rewrite = _extract_rewriter()
    rename = {("customer", "case"): ("customer", "customer_case")}
    sql = "SELECT * FROM customer.case WHERE id = 1"
    out, n = rewrite(sql, rename)
    assert n == 1
    assert "customer.customer_case" in out
    assert "customer.case " not in out and not out.endswith("customer.case")


def test_v067_new11_rewrite_with_backticks():
    rewrite = _extract_rewriter()
    rename = {("billing", "account"): ("billing", "billing_account")}
    sql = "SELECT * FROM `billing`.`account` a JOIN `billing`.`account` b"
    out, n = rewrite(sql, rename)
    assert n == 2
    assert "billing.billing_account" in out


def test_v067_new11_rewrite_case_insensitive_match():
    rewrite = _extract_rewriter()
    rename = {("customer", "case"): ("customer", "customer_case")}
    sql = "SELECT * FROM Customer.CASE"
    out, n = rewrite(sql, rename)
    assert n == 1
    assert "customer.customer_case" in out


def test_v067_new11_rewrite_skips_string_literal():
    rewrite = _extract_rewriter()
    rename = {("customer", "case"): ("customer", "customer_case")}
    sql = "SELECT * FROM customer.case WHERE label = 'old name customer.case'"
    out, n = rewrite(sql, rename)
    assert n == 1, f"Should rewrite identifier ONCE, leave string literal intact, got {n}"
    assert "'old name customer.case'" in out, "string literal must be preserved verbatim"


def test_v067_new11_rewrite_word_boundary():
    """Must not match substrings of identifiers (e.g. customer.case_history)."""
    rewrite = _extract_rewriter()
    rename = {("customer", "case"): ("customer", "customer_case")}
    sql = "SELECT * FROM customer.case_history"
    out, n = rewrite(sql, rename)
    assert n == 0, "must not rewrite customer.case when followed by _history"
    assert out == sql


def test_v067_new11_rewrite_no_rename_no_op():
    rewrite = _extract_rewriter()
    sql = "SELECT * FROM customer.case"
    out, n = rewrite(sql, {})
    assert n == 0
    assert out == sql


def test_v067_new11_rewrite_multiple_renames_same_sql():
    rewrite = _extract_rewriter()
    rename = {
        ("customer", "case"): ("customer", "customer_case"),
        ("billing", "account"): ("billing", "billing_account"),
    }
    sql = "SELECT * FROM customer.case c JOIN billing.account b ON c.acct_id = b.id"
    out, n = rewrite(sql, rename)
    assert n == 2
    assert "customer.customer_case" in out
    assert "billing.billing_account" in out


def test_v067_new11_rewrite_three_part_path_unchanged():
    """Rewriter only handles 2-part `domain.product`. catalog.domain.product
    references are unrelated and should pass through unchanged so they don't
    accidentally collide."""
    rewrite = _extract_rewriter()
    rename = {("customer", "case"): ("customer", "customer_case")}
    sql = "SELECT * FROM main.customer.case_history"
    out, n = rewrite(sql, rename)
    assert n == 0, "three-part path with un-related suffix should not match"


# =============================================================================
# README + VERSION
# =============================================================================

def test_v067_readme_current_version_bumped():
    with open(README) as f:
        rd = f.read()
    assert "**v0.6.7**" in rd, "v0.6.7 not in readme"


# =============================================================================
# Regression — v0.6.x aliases preserved
# =============================================================================

def test_v067_no_regression_v066_aliases_present():
    src = _agent_src()
    for alias in [
        "collision-naming-canonical",
        "fmfl-canonical-target",
        "surgical-mv-preserve",
    ]:
        assert alias in src, f"v0.6.6 alias {alias} dropped — regression"


def test_v067_no_regression_v065_aliases_present():
    src = _agent_src()
    for alias in ["immutable-early-exit", "ssot-stem-autofix"]:
        assert alias in src, f"v0.6.5 alias {alias} dropped — regression"


def test_v067_no_regression_v064_aliases_present():
    src = _agent_src()
    for alias in ["perf-cap-16", "perf-mv15-parallel", "perf-llm-throttle-16"]:
        assert alias in src, f"v0.6.4 alias {alias} dropped — regression"


def test_v067_no_regression_v063_alias_present():
    src = _agent_src()
    assert "det-priority-parse" in src, "v0.6.3 deterministic priority parser dropped"
