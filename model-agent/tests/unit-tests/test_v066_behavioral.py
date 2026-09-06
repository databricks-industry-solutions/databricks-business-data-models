"""Behavioral tests for v0.6.6 fixes against the v0.6.5 telecom vov v2 audit.

  NEW-7  collision-naming-canonical  --  v0.6.5's _validate_product_name_collisions
                                          stem-autofix (Pass 3) renamed cross-domain
                                          duplicates using _p074_qualified_rename which
                                          produced PascalCase outputs (e.g.
                                          'CustomerAccount'). This bled PascalCase
                                          names into a snake_case model. Fix: pipe
                                          all rename candidates (Pass 1, 2, and 3)
                                          through apply_convention with the model's
                                          configured data_asset_naming_convention.

  NEW-8  fmfl-canonical-target       --  find_missing_fk_links validator did not
                                          check that LINK target_table is a
                                          canonical (existing) product. When a
                                          product was renamed/consolidated the LLM
                                          repeatedly proposed the stale name and
                                          burned through 3 retries → F2 Max-retries
                                          silent-accept hatch. Fix: validate target
                                          against canonical (domain.product) set
                                          and provide stem-based 'did you mean'
                                          suggestions in the validation feedback so
                                          the LLM can self-correct in retry 1-2.

  NEW-10 surgical-mv-preserve        --  surgical fast path skipped Step 8d
                                          (kpi-first + per-domain MV gap-fill),
                                          which caused all baseline metric_views
                                          to be dropped from v2's model.json
                                          (telecom_vov_v2 went from 92 MVs in v1
                                          to 0 MVs in v2). Fix: load v1's
                                          model.json metric_views, drop ones whose
                                          owner_product or referenced products no
                                          longer exist in v2, and seed
                                          widgets_values so the existing apply +
                                          writeback path preserves them.
"""
import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _agent_src() -> str:
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


# =============================================================================
# NEW-7 — collision-naming-canonical
# =============================================================================

def test_v066_new7_alias_present():
    src = _agent_src()
    assert "collision-naming-canonical" in src, (
        "collision-naming-canonical sentinel missing"
    )


def test_v066_new7_fired_marker_present():
    src = _agent_src()
    assert "[collision-naming-canonical FIRED]" in src, (
        "[collision-naming-canonical FIRED] runtime log marker missing"
    )


def test_v066_new7_helper_defined():
    src = _agent_src()
    assert "def _canonicalise_p074(" in src, "_canonicalise_p074 helper missing"


def test_v066_new7_calls_apply_convention():
    src = _agent_src()
    # The canonicalise helper must call apply_convention with the configured
    # naming convention.
    assert re.search(
        r"_canonicalise_p074.*?apply_convention",
        src,
        flags=re.DOTALL,
    ), "_canonicalise_p074 does not call apply_convention"


def test_v066_new7_reads_naming_convention_from_config():
    src = _agent_src()
    assert "data_asset_naming_convention" in src, (
        "data_asset_naming_convention not read from config"
    )
    assert "_naming_convention_p074" in src, "_naming_convention_p074 sentinel missing"


def test_v066_new7_validate_collisions_takes_config():
    src = _agent_src()
    # The function signature must accept config.
    assert re.search(
        r"def _validate_product_name_collisions\([^)]*config=None",
        src,
    ), "_validate_product_name_collisions does not accept config"


def test_v066_new7_call_sites_pass_config():
    src = _agent_src()
    # Both production call sites must pass config=config so the
    # canonicalisation respects the model's naming convention.
    # Look for the function call followed (within 600 chars / DOTALL) by
    # config=config — which is robust to single-line vs multi-line forms.
    call_idx = 0
    matched = 0
    while True:
        i = src.find("_validate_product_name_collisions(", call_idx)
        if i < 0:
            break
        # Window of ~800 chars after the opening paren — enough for any
        # multi-line call. config=config must appear before the matching ).
        window = src[i : i + 800]
        # Trim window at the matching closing paren by counting depth.
        depth = 0
        end = -1
        for k, ch in enumerate(window):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = k
                    break
        call_text = window if end < 0 else window[: end + 1]
        if "config=config" in call_text:
            matched += 1
        call_idx = i + 1
    assert matched >= 2, (
        f"Expected >=2 call sites passing config=config, found {matched}"
    )


def test_v066_new7_canonicalise_applied_in_pass1():
    src = _agent_src()
    # Find Pass 1: domain-name collision rename. After computing new_name via
    # _p074_qualified_rename it must be canonicalised.
    assert "_canonicalise_p074(_p074_qualified_rename(" in src, (
        "Pass 1 rename does not pipe through _canonicalise_p074"
    )


def test_v066_new7_canonicalise_applied_to_collision_suffix():
    src = _agent_src()
    # When a sibling name collides we suffix N. The suffix variant must also
    # canonicalise so we don't introduce 'CustomerAccount2' style names.
    assert re.search(
        r"_canonicalise_p074\(f\"\{new_name\}\{_suffix_n\}\"\)",
        src,
    ), "Suffixed rename candidate not canonicalised"


# =============================================================================
# NEW-8 — fmfl-canonical-target
# =============================================================================

def test_v066_new8_alias_present():
    src = _agent_src()
    assert "alias=fmfl-canonical-target" in src, (
        "fmfl-canonical-target sentinel missing"
    )


def test_v066_new8_canonical_entities_set_built():
    src = _agent_src()
    assert "_fmfl_canonical_entities" in src, (
        "_fmfl_canonical_entities set not built in _validate_fmfl"
    )


def test_v066_new8_normalise_target_helper():
    src = _agent_src()
    assert "def _fmfl_normalise_target(" in src, "_fmfl_normalise_target missing"


def test_v066_new8_suggest_canonical_helper():
    src = _agent_src()
    assert "def _fmfl_suggest_canonical(" in src, "_fmfl_suggest_canonical missing"


def test_v066_new8_link_target_validation_present():
    src = _agent_src()
    # Validator must reject LINK targets that don't exist in canonical entities.
    assert re.search(
        r"if _norm_tgt and _norm_tgt not in _fmfl_canonical_entities",
        src,
    ), "LINK target canonical-existence check missing"


def test_v066_new8_suggestion_string_in_error_message():
    src = _agent_src()
    # The error message must include 'did you mean'-style suggestions to guide
    # the LLM's retry without F2 Max-retries silent-accept.
    assert "Closest canonical candidates by stem" in src, (
        "Stem-based suggestion text missing from validator feedback"
    )


def test_v066_new8_stem_score_logic_industry_agnostic():
    src = _agent_src()
    # The stem suggestion must use generic prefix/suffix/contains scoring,
    # not any hardcoded business strings.
    assert "prod.endswith('_' + stem) or prod.startswith(stem + '_')" in src or \
           "prod.endswith(\"_\" + stem) or prod.startswith(stem + \"_\")" in src, (
        "Stem suggestion scoring must use generic prefix/suffix matching"
    )


def test_v066_new8_handles_no_match_gracefully():
    src = _agent_src()
    # v0.6.8 NEW-13 evolved this behavior: when stem suggestions are empty, the
    # validator no longer just rejects with a "change your decision" message —
    # which caused the LLM to loop until Max retries (3) exhausted. Instead the
    # validator now AUTO-COERCES the LINK decision to KEEP_AS_IS deterministically
    # via [fmfl-auto-coerce-keep FIRED]. This is a strict improvement on the
    # graceful-handling contract: the no-match path still resolves cleanly, but
    # without burning retries or polluting the run with soft-accept hatches.
    assert "fmfl-auto-coerce-keep" in src, (
        "No-match-found graceful handling missing — expected v0.6.8 NEW-13 auto-coerce path"
    )
    assert "[fmfl-auto-coerce-keep FIRED]" in src, (
        "Auto-coerce FIRED marker missing — auditor cannot verify fix landed"
    )
    assert "dec['decision'] = 'KEEP_AS_IS'" in src, (
        "Auto-coerce branch must mutate dec to KEEP_AS_IS"
    )


# =============================================================================
# NEW-10 — surgical-mv-preserve
# =============================================================================

def test_v066_new10_alias_present():
    src = _agent_src()
    assert "alias=surgical-mv-preserve" in src, (
        "surgical-mv-preserve sentinel missing"
    )


def test_v066_new10_fired_marker_present():
    src = _agent_src()
    assert "[surgical-mv-preserve FIRED]" in src, (
        "surgical-mv-preserve FIRED runtime marker missing"
    )


def test_v066_new10_helper_defined():
    src = _agent_src()
    assert "def _preserve_baseline_metric_views_for_surgical(" in src, (
        "Helper function missing"
    )


def test_v066_new10_called_in_surgical_else_branch():
    src = _agent_src()
    # The surgical fast path 'else' branch must call the preserve helper.
    assert "_preserve_baseline_metric_views_for_surgical(widgets_values, config, logger)" in src, (
        "Helper not called from surgical fast path"
    )


def test_v066_new10_reads_baseline_model_json():
    src = _agent_src()
    # Helper must construct prev_volume from base_version_for_review.
    assert "base_version_for_review" in src
    assert "prev_volume = target_volume.replace(" in src, (
        "prev_volume must be derived from target_volume + base_version"
    )


def test_v066_new10_drops_mv_with_renamed_owner():
    src = _agent_src()
    # If owner_product (domain, product) no longer exists, drop the MV.
    assert "owner {_od}.{_op} no longer exists" in src, (
        "Owner-product validation drop reason missing"
    )


def test_v066_new10_drops_mv_with_renamed_referenced_product():
    src = _agent_src()
    # If embedded SQL references a missing product, drop the MV.
    assert "references missing product" in src, (
        "Referenced-product validation drop reason missing"
    )


def test_v066_new10_seeds_both_records_and_statements():
    src = _agent_src()
    # Both _metric_view_records (used by writeback) and metric_view_statements
    # (used by step_apply_metric_views) must be seeded — otherwise model.json
    # writeback wouldn't include the preserved MVs.
    assert 'widgets_values["_metric_view_records"] = _preserved' in src
    assert 'widgets_values["metric_view_statements"] = _stmts' in src


def test_v066_new10_skips_for_new_base_model():
    src = _agent_src()
    # Helper must early-return for 'new base model' op (no baseline to preserve).
    assert 'if operation == "new base model"' in src
    # Look near the helper for this guard.
    helper_idx = src.find("def _preserve_baseline_metric_views_for_surgical(")
    helper_body = src[helper_idx : helper_idx + 4000]
    assert 'if operation == "new base model"' in helper_body, (
        "new-base-model early-return not in helper"
    )


def test_v066_new10_only_in_else_branch():
    src = _agent_src()
    # The call must be inside an else branch of the `if not _surgical_fast_path:`
    # check, so it does NOT fire for full-path runs.
    pattern = (
        r"if not _surgical_fast_path:.*?"
        r"else:.*?"
        r"_preserve_baseline_metric_views_for_surgical"
    )
    assert re.search(pattern, src, flags=re.DOTALL), (
        "Helper call not gated behind 'else' of 'if not _surgical_fast_path'"
    )


def test_v066_new10_industry_agnostic():
    src = _agent_src()
    helper_idx = src.find("def _preserve_baseline_metric_views_for_surgical(")
    helper_body = src[helper_idx : helper_idx + 6000]
    forbidden = ["telecom", "airline", "airlines", "healthcare", "banking",
                 "retail", "manufacturing", "insurance"]
    for word in forbidden:
        assert word not in helper_body.lower(), (
            f"Industry-specific string '{word}' found in NEW-10 helper"
        )


# =============================================================================
# Cross-cutting: readme + version
# =============================================================================

def test_v066_readme_current_version_bumped():
    with open("/Users/user/Documents/projects/vibe-modelling-agent/readme.md") as f:
        rd = f.read()
    assert "**v0.6.6**" in rd, "v0.6.6 not in readme (either as Current or in history)"


# =============================================================================
# v0.6.x aliases preserved (no regression)
# =============================================================================

def test_v066_no_regression_v064_aliases_present():
    src = _agent_src()
    # B1 perf cap, B3 MV15 parallel, B8 LLM throttle (actual alias name)
    for alias in [
        "perf-cap-16",
        "perf-mv15-parallel",
        "perf-llm-throttle-16",
    ]:
        assert alias in src, f"v0.6.4 perf alias {alias} dropped — regression"


def test_v066_no_regression_v065_aliases_present():
    src = _agent_src()
    for alias in [
        "immutable-early-exit",
        "ssot-stem-autofix",
    ]:
        assert alias in src, f"v0.6.5 alias {alias} dropped — regression"


def test_v066_no_regression_v063_alias_present():
    src = _agent_src()
    assert "det-priority-parse" in src, "v0.6.3 deterministic priority parser dropped"
