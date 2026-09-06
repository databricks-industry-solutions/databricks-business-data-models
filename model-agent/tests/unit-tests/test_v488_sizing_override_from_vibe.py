"""v4.8.8 alias=sizing-override-from-vibe.

The MODEL-PARAMS guardrail used to outrank the user whenever the LLM forgot to emit
user_sizing_override. On coffee_roastery the LLM read "roughly five to seven tables per
domain" correctly and emitted max_data_products_per_domain=7; the guardrail then clamped
it back UP to 10 (bounds [10, 16]) because the boolean was missing, and the model shipped
retail=10 / wholesale=9 against a stated ceiling of 7.

These tests execute the real helper and the real clamp out of the notebook, so a
pre-patch run fails on the NUMBERS rather than on a missing string.
"""
import ast
import json
import os

import pytest

from notebook_source_util import assert_agent_version_at_least, cell_containing

CLAMP_ANCHOR = "def _clamp_and_validate_model_params("
HELPER_NAME = "_v488_sizing_override_from_directives"


def _params_cell():
    return cell_containing(CLAMP_ANCHOR)


def _extract(*func_names):
    """Exec whichever of the requested top-level defs/assigns the params cell has."""
    src = _params_cell()
    tree = ast.parse(src)
    wanted, lines = [], src.split("\n")
    for node in tree.body:
        name = getattr(node, "name", None)
        if name is None and isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            name = targets[0] if targets else None
        if name in func_names:
            wanted.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
    ns = {}
    exec("\n\n".join(wanted), ns)
    return ns


def _load(*func_names):
    """Same, but skip when a name is missing: for tests OF the helper itself."""
    ns = _extract(*func_names)
    missing = [n for n in func_names if n not in ns]
    if missing:
        pytest.skip("pre-patch notebook: %s not present" % ", ".join(missing))
    return ns


def _load_optional(*func_names):
    """Same, but never skip: for tests of BEHAVIOUR that must fail pre-patch."""
    return _extract(*func_names)


class _Log:
    def __init__(self):
        self.lines = []

    def _add(self, msg):
        self.lines.append(str(msg))

    info = warning = error = _add

    @property
    def text(self):
        return "\n".join(self.lines)


# --- the helper's own contract -------------------------------------------------------

@pytest.mark.parametrize("directives,expected", [
    ({"max_products_per_domain": 7}, True),
    ({"min_products_per_domain": 5}, True),
    ({"max_domains": 3}, True),
    ({"min_total_products": 15}, True),
    ({"single_domain_mode": True}, True),
    ({"explicit_count_statements": ["exactly 25 products"]}, True),
    ({}, False),
    ({"max_products_per_domain": None}, False),
    ({"max_products_per_domain": 0}, False),
    ({"explicit_count_statements": []}, False),
    ({"explicit_count_statements": ["  "]}, False),
    ({"max_metric_views": 4}, False),          # a different axis, not a count clamp
    ({"single_domain_mode": False}, False),
])
def test_override_is_derived_from_the_parsed_vibe(directives, expected):
    ns = _load(HELPER_NAME, "_V488_SIZING_DIRECTIVE_KEYS")
    override, _keys = ns[HELPER_NAME](directives)
    assert override is expected


@pytest.mark.parametrize("bad", [None, "", [], 0, "max_products_per_domain=7"])
def test_a_non_dict_never_claims_an_override(bad):
    ns = _load(HELPER_NAME, "_V488_SIZING_DIRECTIVE_KEYS")
    assert ns[HELPER_NAME](bad) == (False, [])


def test_a_bool_is_not_read_as_a_count():
    """True == 1 in Python; a stray bool must not masquerade as "the user asked for 1"."""
    ns = _load(HELPER_NAME, "_V488_SIZING_DIRECTIVE_KEYS")
    assert ns[HELPER_NAME]({"max_products_per_domain": True}) == (False, [])


def test_the_reason_names_every_directive_that_earned_the_override():
    ns = _load(HELPER_NAME, "_V488_SIZING_DIRECTIVE_KEYS")
    override, keys = ns[HELPER_NAME]({"min_products_per_domain": 5,
                                      "max_products_per_domain": 7,
                                      "max_domains": 3})
    assert override is True
    assert set(keys) == {"min_products_per_domain=5", "max_products_per_domain=7",
                         "max_domains=3"}


# --- the behaviour the helper exists to change ---------------------------------------

def _resolve_override(ns, directives):
    """The override exactly as the shipped read site computes it.

    Deliberately does NOT skip when the helper is absent: pre-patch the LLM flag is the
    only input and it is missing here, so this returns False and the numeric assertion
    below fails on the NUMBER (7 clamped up to 10) rather than being skipped away.
    """
    if HELPER_NAME in ns:
        return ns[HELPER_NAME](directives)[0]
    return bool({}.get("user_sizing_override", False))


def test_the_users_ceiling_survives_the_tier_guardrail():
    """THE REGRESSION. Pre-patch the guardrail clamps 7 UP to 10 and the model overshoots."""
    ns = _load_optional("_clamp_and_validate_model_params", "_MODEL_PARAM_MIN_MAX_PAIRS",
                        "_SIZING_PARAM_KEYS", HELPER_NAME, "_V488_SIZING_DIRECTIVE_KEYS")
    ns["_MODEL_PARAM_GUARDRAILS"] = {
        "mvm_model": {"max_data_products_per_domain": {"min": 10, "max": 16},
                      "min_data_products_per_domain": {"min": 4, "max": 8}}
    }
    override = _resolve_override(ns, {"min_products_per_domain": 5,
                                      "max_products_per_domain": 7})
    log = _Log()
    out = ns["_clamp_and_validate_model_params"](
        "mvm_model", {"max_data_products_per_domain": 7,
                      "min_data_products_per_domain": 5}, log,
        user_sizing_override=override)
    assert out["max_data_products_per_domain"] == 7, (
        "the user said seven; the tier guardrail floor of 10 must not raise it")
    assert out["min_data_products_per_domain"] == 5


def test_without_a_sizing_vibe_the_guardrail_still_governs():
    """The escape hatch must stay shut when the user said nothing about size."""
    ns = _load_optional("_clamp_and_validate_model_params", "_MODEL_PARAM_MIN_MAX_PAIRS",
                        "_SIZING_PARAM_KEYS", HELPER_NAME, "_V488_SIZING_DIRECTIVE_KEYS")
    ns["_MODEL_PARAM_GUARDRAILS"] = {
        "mvm_model": {"max_data_products_per_domain": {"min": 10, "max": 16}}
    }
    override = _resolve_override(ns, {})
    assert override is False
    out = ns["_clamp_and_validate_model_params"](
        "mvm_model", {"max_data_products_per_domain": 7}, _Log(),
        user_sizing_override=override)
    assert out["max_data_products_per_domain"] == 10


# --- wiring: the helper has a live call site -----------------------------------------

def test_the_read_site_consults_the_vibe_not_only_the_llm():
    src = _params_cell()
    assert "_llm_uso or _vibe_uso" in src, (
        "user_sizing_override must OR the LLM flag with the parsed vibe")
    assert 'sizing_directives' in src.split("_llm_uso or _vibe_uso")[0][-800:], (
        "the vibe half of the OR must come from the parsed sizing_directives")


def test_the_helper_is_defined_before_the_clamp_that_uses_it():
    src = _params_cell()
    assert src.index("def " + HELPER_NAME) < src.index(CLAMP_ANCHOR)


def test_it_announces_itself_only_when_it_changed_the_outcome():
    """No FIRED line when the LLM already set the flag: that would be noise, not a fix."""
    src = _params_cell()
    assert "if _vibe_uso and not _llm_uso:" in src
    assert "alias=sizing-override-from-vibe" in src


def test_version_is_488_or_later():
    assert_agent_version_at_least("4.8.8")
