import json
import re
import textwrap
import types

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _cell_src(idx):
    nb = json.load(open(NB))
    return "".join(nb["cells"][idx]["source"])


def _slice(src, start_marker, end_marker, include_end=False):
    i = src.index(start_marker)
    i = src.rfind("\n", 0, i) + 1
    j = src.index(end_marker, i)
    if include_end:
        j = src.index("\n", j) + 1
    return src[i:j]


# ---------------------------------------------------------------------------
# version anchor
# ---------------------------------------------------------------------------
def test_v344_version_constant():
    # forward-compatible anchor: v3.4.4 fixes must persist at or beyond 3.4.4
    # (exact-version assertion is owned by the current version's test file).
    src = _cell_src(1)
    m = re.search(r'__AGENT_VERSION__ = "(\d+)\.(\d+)\.(\d+)"', src)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 4, 4)


# ---------------------------------------------------------------------------
# vibe-conventions-extract: schema + prompt carry model_conventions
# ---------------------------------------------------------------------------
def _brace_match_dict(src, assign_marker):
    """Extract a full `NAME = { ... }` literal by balancing braces."""
    i = src.index(assign_marker)
    start = src.index("{", i)
    depth = 0
    for j in range(start, len(src)):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
    raise AssertionError("unbalanced braces")


def test_v344_schema_has_model_conventions():
    src = _cell_src(1)
    block = _brace_match_dict(src, "_VIBE_PARSE_RESPONSE_SCHEMA = {")
    block = textwrap.dedent(block)
    ns = {"False": False, "True": True, "None": None}
    exec(block, ns)
    schema = ns["_VIBE_PARSE_RESPONSE_SCHEMA"]["schema"]
    props = schema["properties"]
    assert "model_conventions" in props, "model_conventions missing from schema properties"
    mc = props["model_conventions"]["properties"]
    for f in ("tag_prefix", "tag_suffix", "schema_prefix", "schema_suffix",
              "data_asset_naming_convention", "cataloging_style"):
        assert f in mc, f"{f} missing from model_conventions schema"
    assert "model_conventions" in schema["required"], "model_conventions not in top-level required"


def test_v344_prompt_instructs_convention_extraction():
    src = _cell_src(1)
    # the instruction lives in VIBE_PARSE_PROMPT
    assert "`model_conventions`: Object capturing ANY EXPLICIT MODELING CONVENTION" in src
    assert "the EXACT tag prefix the user demanded" in src
    assert "gov_transport_" in src  # the verbatim-prefix example


# ---------------------------------------------------------------------------
# gt-tag-prefix-compound-split: the core verifier logic fix (behavioral)
# ---------------------------------------------------------------------------
def _exec_is_universal_tag():
    src = _cell_src(9)
    block = _slice(src, '_UNIVERSAL_TAGS = {"pii"',
                   "return all(_is_universal_token(p) for p in _parts)", include_end=True)
    block = textwrap.dedent(block)
    ns = {"_rt": re}
    exec(block, ns)
    return ns["_is_universal_tag"]


def test_v344_compound_classification_key_is_exempt():
    _is_universal_tag = _exec_is_universal_tag()
    # compound comma-joined classification labels -> universal (the gov_transport false-flag)
    assert _is_universal_tag("restricted,pii_dob") is True
    assert _is_universal_tag("confidential,pii_name") is True
    assert _is_universal_tag("restricted,pii") is True


def test_v344_classification_variant_root_is_exempt():
    _is_universal_tag = _exec_is_universal_tag()
    assert _is_universal_tag("pii_dob") is True
    assert _is_universal_tag("pii_address") is True
    assert _is_universal_tag("confidential") is True
    assert _is_universal_tag("cg_business_glossary_term") is True  # cg_ system prefix


def test_v344_genuine_industry_tag_without_prefix_still_flagged():
    # NON-TAUTOLOGY proof: a real industry-specific tag key that is NOT a classification
    # variant must STILL be flagged (not exempt), otherwise the prefix rule is meaningless.
    _is_universal_tag = _exec_is_universal_tag()
    assert _is_universal_tag("employee_status") is False
    assert _is_universal_tag("project_phase") is False
    # compound where one part is genuinely industry-specific -> NOT all-universal -> flagged
    assert _is_universal_tag("restricted,employee_status") is False


# ---------------------------------------------------------------------------
# vibe-conventions-override: vibe OVERRIDES generated config (behavioral)
# ---------------------------------------------------------------------------
def _exec_override(declared_conv, config, widgets_values):
    src = _cell_src(9)
    block = _slice(src, "if _declared_conv and isinstance(self.config, dict):",
                   "alias=vibe-conventions-override", include_end=True)
    block = textwrap.dedent(block)

    class _Self:
        pass
    s = _Self()
    s.config = config
    s.widgets_values = widgets_values
    s.logger = types.SimpleNamespace(info=lambda *a, **k: None)
    ns = {"self": s, "_declared_conv": declared_conv}
    exec(block, ns)
    return s


def test_v344_vibe_prefix_overrides_generated_cg():
    # The exact gov_transport failure: setup resolved TAG_PREFIX='cg_' from generated context;
    # vibe declared tag_prefix='gov_transport_'. After override, config must carry gov_transport_.
    cfg = {"TAG_PREFIX": "cg_", "SCHEMA_PREFIX": "", "TAG_SUFFIX": "", "SCHEMA_SUFFIX": "",
           "MODEL_CONVENTIONS": {"tag_prefix": "cg_"}}
    wv = {"business_context_data": {"model_conventions": {"tag_prefix": "cg_"}}}
    s = _exec_override({"tag_prefix": "gov_transport_"}, cfg, wv)
    assert s.config["TAG_PREFIX"] == "gov_transport_"
    assert s.config["MODEL_CONVENTIONS"]["tag_prefix"] == "gov_transport_"
    assert s.widgets_values["business_context_data"]["model_conventions"]["tag_prefix"] == "gov_transport_"


def test_v344_override_noop_when_vibe_silent():
    # vibe declared no conventions -> generated config must be left untouched.
    cfg = {"TAG_PREFIX": "cg_", "MODEL_CONVENTIONS": {"tag_prefix": "cg_"}}
    wv = {"business_context_data": {"model_conventions": {"tag_prefix": "cg_"}}}
    s = _exec_override({}, cfg, wv)
    assert s.config["TAG_PREFIX"] == "cg_"
    assert s.config["MODEL_CONVENTIONS"]["tag_prefix"] == "cg_"
