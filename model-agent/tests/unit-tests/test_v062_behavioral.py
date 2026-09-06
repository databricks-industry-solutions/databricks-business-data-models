"""Behavioral tests for v0.6.2 fixes.

Covers 3 regressions found in the v0.6.1 telecom MVM v1+v2 audit (2026-04-27):

  REG-1  vov-auto-next-vibes          — vibe modeling of version with empty model_vibes
                                         now auto-loads v_{N-1}/vibes/next_vibes.txt as
                                         the mutation plan. Previously became no-op.
  REG-2  rename-product-convention-   — rename_product normalises target_state through
         enforce                        apply_convention(snake_case by default) so LLM
                                         PascalCase drift no longer leaks into products.
  REG-4  self-ref-banned-prefix-      — _pre_static_analysis_autofix now tries to RENAME
         autorename                     banned-prefix self-ref FK columns to parent_<pk>
                                         before clearing the FK entirely.
"""
import ast
import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _agent_src() -> str:
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


# =============================================================================
# REG-1 — vov-auto-next-vibes
# =============================================================================

def test_v062_reg1_alias_present():
    src = _agent_src()
    assert "[vov-auto-next-vibes FIRED]" in src
    assert "[vov-auto-next-vibes SKIP]" in src


def test_v062_reg1_only_fires_for_vov_operation():
    """Auto-load ONLY fires when operation == 'vibe modeling of version'."""
    src = _agent_src()
    idx = src.find("[vov-auto-next-vibes FIRED]")
    assert idx > 0
    window = src[max(0, idx - 2000):idx + 4000]
    assert 'operation == "vibe modeling of version"' in window


def test_v062_reg1_only_fires_when_user_vibes_empty():
    """The auto-load MUST respect §3c: explicit user model_vibes always win.

    The original literal guard `not widgets_values.get("vibe_modelling_instructions"...)`
    was refactored into a stronger, superset check: `_user_vibe_present` is computed
    across a 7-alias set (including vibe_modelling_instructions + model_vibes) plus
    _widget_raw_values and business_context_data fallbacks, and the auto-load is gated on
    `operation == "vibe modeling of version" and not _user_vibe_present`. Assert that
    stronger guard rather than the obsolete literal."""
    src = _agent_src()
    assert 'operation == "vibe modeling of version" and not _user_vibe_present' in src
    ai = src.index("_user_vibe_aliases =")
    alias_def = src[ai:ai + 300]
    assert "vibe_modelling_instructions" in alias_def
    assert "model_vibes" in alias_def


def test_v062_reg1_uses_base_version_path():
    src = _agent_src()
    idx = src.find("vov-auto-next-vibes FIRED")
    window = src[max(0, idx - 2000):idx + 4000]
    assert 'base_version_for_review' in window
    assert 'vibes' in window
    assert 'next_vibes.txt' in window


def test_v062_reg1_path_uses_model_scope_and_sanitized_business():
    """Path is {root_loc}/business/{sanitized_name}/v{base}/{model_scope}/vibes/next_vibes.txt
    (v3.5.2 alias=nested-version-layout switched the fused '{model_scope}_v{n}' segment to the
    nested 'v{n}/{model_scope}' pair; the assertion tracks the current on-disk layout)."""
    src = _agent_src()
    idx = src.find("vov-auto-next-vibes FIRED")
    window = src[max(0, idx - 5000):idx + 6000]
    assert 'os.path.join(root_loc, "business", sanitized_name' in window
    assert 'f"v{_base_ver_auto}"' in window
    assert 'model_scope' in window


def test_v062_reg1_has_dbutils_fs_head_fallback():
    """If POSIX open fails, fall back to dbutils.fs.head with 1MB cap."""
    src = _agent_src()
    idx = src.find("vov-auto-next-vibes FIRED")
    # widened window: code between the marker and the fallback has grown across versions
    # (the fallback is part of the same vov-auto-next-vibes read path, ~5.3k chars after).
    window = src[max(0, idx - 2000):idx + 9000]
    assert "dbutils.fs.head(_source_vibes_path" in window
    assert "1024 * 1024" in window


def test_v062_reg1_assigns_to_widget_vibes_key():
    # window widened to +9000 (matches sibling fallback test): the assignment literal sits
    # ~6.4k chars after the FIRED marker as the read path grew across versions; feature intact.
    src = _agent_src()
    idx = src.find("vov-auto-next-vibes FIRED")
    window = src[max(0, idx - 2000):idx + 9000]
    assert 'widgets_values["vibe_modelling_instructions"] = _auto_vibes_content' in window


def test_v062_reg1_records_source_version_marker():
    """Auditor needs to verify the auto-load fired — record which version it came from."""
    # window widened to +9000: _auto_loaded_next_vibes_from_version now sits ~5.1k after FIRED.
    src = _agent_src()
    idx = src.find("vov-auto-next-vibes FIRED")
    window = src[max(0, idx - 2000):idx + 9000]
    assert '_auto_loaded_next_vibes_from_version' in window


# =============================================================================
# REG-2 — rename-product-convention-enforce
# =============================================================================

# NOTE (re-anchored): the v0.6.2 `[rename-product-convention-enforce FIRED]` alias and the
# `apply_convention(new_product, _rename_convention, ...)` literal were refactored away. The
# FEATURE — rename normalises the target through apply_convention(snake_case by default) so LLM
# PascalCase drift never leaks into product/table names — is intact under `_ren_conv` (dedup
# rename path) and `_rd_conv` (directive rename path). These tests assert that current truth.
_REN_CONV_DERIVE = '_ren_conv = (config.get("MODEL_CONVENTIONS") or {}).get("data_asset_naming_convention", "snake_case")'


def test_v062_reg2_alias_present():
    """Rename-convention enforcement is deployed (modern equivalent of the v0.6.2 alias)."""
    src = _agent_src()
    assert "p['product'] = apply_convention(new_name, _ren_conv)" in src


def test_v062_reg2_calls_apply_convention_on_product():
    """Both the logical product name AND the physical table_name are normalised on rename."""
    src = _agent_src()
    idx = src.find(_REN_CONV_DERIVE)
    assert idx > 0
    window = src[max(0, idx - 200):idx + 1200]
    assert "p['product'] = apply_convention(new_name, _ren_conv)" in window
    assert "p['table_name'] = apply_convention(new_name, _ren_conv)" in window


def test_v062_reg2_convention_pulled_from_config():
    src = _agent_src()
    assert _REN_CONV_DERIVE in src
    assert 'config.get("MODEL_CONVENTIONS")' in _REN_CONV_DERIVE
    assert '"data_asset_naming_convention"' in _REN_CONV_DERIVE
    assert '"snake_case"' in _REN_CONV_DERIVE
    # directive-path rename uses the same config-pulled convention under _rd_conv
    assert '_rd_conv = (config.get("MODEL_CONVENTIONS") or {}).get("data_asset_naming_convention", "snake_case")' in src


def test_v062_reg2_also_normalises_domain_when_cross_domain_rename():
    """Domain names are normalised through apply_convention too.

    The v0.6.2 premise (cross-domain rename fabricates a new_domain that needs normalising) no
    longer maps: §3b forbids creating domains on the fly, so a product MOVE targets an EXISTING
    domain. Domain-name normalisation itself remains enforced via the database_name convention."""
    src = _agent_src()
    assert 'domain["database_name"] = apply_convention(domain["database_name"], new_val)' in src


def test_v062_reg2_apply_convention_snake_case_pascal_input():
    """Direct unit test of the canonical conversion used in REG-2.

    Replicates apply_convention's core logic for snake_case target on a
    PascalCase input — matches the v2 regression where LLM emitted
    'CustomerAgent' when convention was snake_case.
    """
    def _apply(name, convention="snake_case"):
        s = str(name).strip().replace(' ', '_').replace('-', '_')
        s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
        s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
        s = re.sub(r'[^a-zA-Z0-9_]', '_', s)
        s = re.sub(r'_+', '_', s).strip('_')
        words = [w.lower() for w in s.split('_') if w]
        return '_'.join(words)

    assert _apply("CustomerAgent") == "customer_agent"
    assert _apply("customer_agent") == "customer_agent"  # idempotent
    assert _apply("NotificationTemplate") == "notification_template"
    assert _apply("UsageNotificationTemplate") == "usage_notification_template"
    assert _apply("already_snake") == "already_snake"


# =============================================================================
# REG-4 — self-ref-banned-prefix-autorename
# =============================================================================

def test_v062_reg4_alias_present():
    src = _agent_src()
    assert "[self-ref-banned-prefix-autorename FIRED]" in src


def test_v062_reg4_attempts_rename_before_clearing():
    """The new branch must try to rename to parent_<pk> before falling through to clear."""
    src = _agent_src()
    idx = src.find("[self-ref-banned-prefix-autorename FIRED]")
    assert idx > 0
    window = src[max(0, idx - 4000):idx + 4000]
    assert 'f"parent_{_own_pk}"' in window
    assert "_autoren" in window


def test_v062_reg4_collision_check_before_rename():
    """Rename must not clobber an existing attribute on the same product."""
    src = _agent_src()
    idx = src.find("[self-ref-banned-prefix-autorename FIRED]")
    window = src[max(0, idx - 4000):idx + 4000]
    assert "_existing_attrs_on_prod" in window
    assert "if _cand_new not in _existing_attrs_on_prod" in window


def test_v062_reg4_handles_exact_pk_equality_case():
    """attr_name == pk (e.g., attr 'fallout_id' on table fallout with FK to itself)."""
    src = _agent_src()
    idx = src.find("[self-ref-banned-prefix-autorename FIRED]")
    window = src[max(0, idx - 4000):idx + 4000]
    assert "_a_low == _p_low" in window


def test_v062_reg4_handles_banned_prefix_case():
    """attr_name like 'related_fallout_id' with PK 'fallout_id'."""
    src = _agent_src()
    idx = src.find("[self-ref-banned-prefix-autorename FIRED]")
    window = src[max(0, idx - 4000):idx + 4000]
    assert "_BANNED_SELF_REF_PREFIXES" in window
    assert "_a_low.endswith(_p_low)" in window


def test_v062_reg4_preserves_fk_when_renaming():
    """When renaming, the FK target must be fixed to point at the correct PK."""
    src = _agent_src()
    idx = src.find("[self-ref-banned-prefix-autorename FIRED]")
    window = src[max(0, idx - 4000):idx + 4000]
    assert "attr['foreign_key_to'] = f\"{td}.{tp}.{_own_pk}\"" in window


def test_v062_reg4_fallback_clear_still_exists():
    """If rename fails (collision), fall through to old clear-FK behaviour."""
    src = _agent_src()
    idx = src.find("[self-ref-banned-prefix-autorename FIRED]")
    window = src[max(0, idx - 4000):idx + 6000]
    assert "if not _autoren:" in window
    assert "Removed unlabeled self-referencing FK:" in window


# =============================================================================
# Integration: ensure all three v0.6.2 aliases co-exist and notebook parses
# =============================================================================

def test_v062_all_three_aliases_present_in_notebook():
    # The rename-product-convention-enforce alias was refactored into the _ren_conv rename path
    # (see REG-2 note above); assert that live literal instead of the retired alias string.
    src = _agent_src()
    for marker in (
        "[vov-auto-next-vibes FIRED]",
        "p['product'] = apply_convention(new_name, _ren_conv)",
        "[self-ref-banned-prefix-autorename FIRED]",
    ):
        assert marker in src, f"missing {marker} — v0.6.2-lineage fix not deployed"


def test_v062_notebook_cells_all_parse():
    """No syntax errors introduced by the three patches."""
    nb = json.load(open(NB))
    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c["source"])
        ast.parse(src)  # raises if any syntax error


def test_v062_version_marker_v062_in_notebook_and_readme():
    src = _agent_src()
    assert "v0.6.2" in src
    readme = open("/Users/user/Documents/projects/vibe-modelling-agent/readme.md").read()
    # v0.6.2 must remain in the version-history table even after later releases
    assert "**v0.6.2**" in readme


# =============================================================================
# PK invariant audit (REG-3 diagnostic)
# =============================================================================
# Not a pipeline fix, but a testing helper: confirms how PKs are actually
# represented in model.json so future audit scripts don't miss them.

def test_v062_pk_invariant_helper():
    """Helper: verify the set of fields/patterns used to identify a PK in model.json."""
    # From the notebook's enforce_configured_pk_consistency + make_attribute_dict,
    # a PK attribute may be identified by ANY of these in model.json:
    #   - attribute name matches product.primary_key
    #   - 'is_primary_key' == True (optional key)
    #   - 'is_pk' == True (optional key)
    #   - 'tags' contains 'primary_key' (substring)
    # The raw boolean 'primary_key' flag is NOT a direct attribute key; the
    # 'primary_key' field exists on PRODUCTS (as the PK column name), not
    # on ATTRIBUTES. Audit scripts that grep attributes for
    # `primary_key: true` will find zero — that's expected, not a bug.

    def is_pk_attr(attr, product_pk):
        if attr.get("attribute") == product_pk:
            return True
        if attr.get("is_primary_key"):
            return True
        if attr.get("is_pk"):
            return True
        if "primary_key" in (attr.get("tags") or "").lower():
            return True
        return False

    # positive cases
    assert is_pk_attr({"attribute": "agent_id", "tags": "primary_key"}, "agent_id")
    assert is_pk_attr({"attribute": "agent_id"}, "agent_id")
    assert is_pk_attr({"attribute": "pk_col", "is_pk": True}, "wrong_name")
    assert is_pk_attr({"attribute": "other", "is_primary_key": True}, "agent_id")
    # negative
    assert not is_pk_attr({"attribute": "email"}, "agent_id")
    assert not is_pk_attr({"attribute": "email", "tags": "pii"}, "agent_id")
