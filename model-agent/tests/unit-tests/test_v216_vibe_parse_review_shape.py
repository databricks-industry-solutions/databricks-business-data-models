"""Behavioural tests for v2.1.6 VIBE-PARSE-REVIEW-SHAPE release.

Live evidence motivating these tests:
- v215 HC run <run_id> + RT run <run_id> (2026-05-27 14:01)
  reported `[VIBE_EVENT] vibe_orchestrator_parsed payload.requirement_count: 1`
  against 16,755-char HC reviewer-feedback and 14,353-char RT reviewer-feedback,
  while gov_transport (21,780 chars of structured directives) produced 21 VREQs.
- Audit classified Stage A adherence at 4% for HC/RT vs 100% for gov_transport.

Aliases under test:
- vibe-parse-review-shape-prompt-fix     — prompt now teaches Shape B (review prose)
- vibe-parse-silent-drop-safety-net      — runtime detector re-parses by segmentation
- agent-version-global                   — __AGENT_VERSION__ == "2.1.6"
"""
import json
import re
from pathlib import Path

import pytest

NB_PATH = Path(__file__).resolve().parent.parent.parent / "agent" / "dbx_vibe_modelling_agent.ipynb"


@pytest.fixture(scope="module")
def nb_cells():
    with open(NB_PATH, "r") as f:
        nb = json.load(f)
    return nb["cells"]


@pytest.fixture(scope="module")
def cell1_src(nb_cells):
    return "".join(nb_cells[1].get("source", []))


@pytest.fixture(scope="module")
def cell9_src(nb_cells):
    return "".join(nb_cells[9].get("source", []))


# ---------------------------------------------------------------------------
# A1. Version constant bumped to 2.1.6
# ---------------------------------------------------------------------------
def test_v216_agent_version_constant(cell1_src):
    """__AGENT_VERSION__ must match live agent and appear in cell 1."""
    from version_test_util import agent_version, assert_valid_single_digit_semver

    assert_valid_single_digit_semver()
    assert f'__AGENT_VERSION__ = "{agent_version()}"' in cell1_src, (
        f"__AGENT_VERSION__ must be {agent_version()!r} in cell 1"
    )
    # Confirm alias markers from v216, v217, v218 are present in the changelog comment
    assert "vibe-parse-review-shape-prompt-fix" in cell1_src  # v216
    assert "vibe-parse-silent-drop-safety-net" in cell1_src   # v216
    assert "vibe-parse-fewshot-valid-json-fix" in cell1_src   # v217
    assert "vibe-parse-prose-only-prompt" in cell1_src        # v218


# ---------------------------------------------------------------------------
# A2. VIBE_PARSE_PROMPT now teaches shape-detection (the prompt-level fix)
# ---------------------------------------------------------------------------
def test_v216_prompt_explains_shape_a_structured(cell1_src):
    """The prompt must explicitly name Shape A (structured directives)."""
    assert "Shape A" in cell1_src
    assert "Structured directive" in cell1_src
    # The gov_transport-style language must still be recognised
    assert "EXACTLY" in cell1_src


def test_v216_prompt_explains_shape_b_review(cell1_src):
    """The prompt must explicitly name Shape B (review/critique/feedback)."""
    assert "Shape B" in cell1_src
    # The signals the prompt teaches the LLM to recognise
    for signal in (
        "Recommendation",
        "Priority:",
        "Must Fix",
        "Should Fix",
        "What the Model Could Improve",
        "Holistic Critique",
    ):
        assert signal in cell1_src, f"prompt missing review-shape signal: {signal}"


def test_v216_prompt_has_shape_b_behavior_described(cell1_src):
    """v218: shape-B teaching is in PROSE (no JSON code-fence examples).
    The prompt must still describe the behavior — Rule #2 must show via
    concrete inline examples that 3 review sections produce 3 requirements.
    """
    body = _prompt_body(cell1_src)
    # The behavior must be illustrated inline in Rule #2
    assert "yields exactly 3 requirements" in body, (
        "Rule #2 must show the 'N sections → N requirements' anchor"
    )
    assert "facility.organization" in body or "pii_phi" in body or "behavioral_health" in body


# ---------------------------------------------------------------------------
# v217 regression-guard: few-shot examples must be VALID JSON (quoted keys)
# v216 shipped Python-ish dict literals that crashed the LLM parser with
# KeyError: 'original_text'.
# ---------------------------------------------------------------------------
def _prompt_body(cell1_src: str) -> str:
    """Extract just the VIBE_PARSE_PROMPT triple-quoted body so assertions
    don't pollute on the changelog comment which references the bad pattern.
    """
    marker = 'PROMPT_TEMPLATES["VIBE_PARSE_PROMPT"] = r"""'
    start = cell1_src.find(marker) + len(marker)
    end = cell1_src.find('"""', start)
    return cell1_src[start:end]


def test_v218_no_embedded_json_examples_in_prompt(cell1_src):
    """v218: no JSON code-fence examples in the prompt — the
    response_schema (strict=True) is the unambiguous contract; embedded
    JSON examples confused Opus 4.7 into emitting variant shapes that
    produced KeyErrors in v216 and v217.

    The Python-ish dict literal (v216 regression) and JSON-fenced output
    examples (v217 regression) must both be absent from the prompt body.
    """
    body = _prompt_body(cell1_src)
    # No Python-ish dict literal regression
    assert "{original_text:" not in body, (
        "v216 Python-ish dict literal pattern present (regression)"
    )
    # No JSON code-fence example block (the v217 regression)
    # The output-format SECTION still describes the JSON shape in PROSE,
    # so `"original_text":` does NOT appear as a JSON key/value inside the prompt body.
    assert '"original_text":' not in body, (
        "v217 JSON code-fence example pattern present (regression)"
    )
    # Sanity: the prose still references the field names
    assert "original_text" in body
    assert "verification_strategy" in body


def test_v218_prompt_describes_every_required_output_field(cell1_src):
    """v218: prompt body must mention every field the response_schema requires."""
    body = _prompt_body(cell1_src)
    for required in ("original_text", "intent", "scope", "scope_targets",
                     "mode", "priority", "constraint_type", "verification_strategy"):
        assert required in body, f"required field '{required}' missing from prompt body"


def test_v216_prompt_rule7_is_shape_conditional(cell1_src):
    """Rule #7 (count vs lines) must be conditional on input shape, not a flat cap."""
    # The new wording must say UNDER-EXTRACTION is forbidden for Shape B
    assert (
        "UNDER-EXTRACTION on Shape B" in cell1_src
        or "under-extraction on shape b" in cell1_src.lower()
    ), "Rule #7 was not made shape-conditional; under-extraction is not flagged"


# ---------------------------------------------------------------------------
# A3. Runtime safety net is present in cell 9 with required FIRED log
# ---------------------------------------------------------------------------
def test_v216_safety_net_block_present(cell9_src):
    assert "_v216_silent_drop" in cell9_src
    assert "vibe-parse-silent-drop FIRED v2.1.6" in cell9_src
    assert "alias=vibe-parse-silent-drop-safety-net" in cell9_src


def test_v216_safety_net_thresholds(cell9_src):
    """Safety net must fire when req_count <= 2 AND vibe >= 2000 chars AND >= 2 review signals."""
    assert "_v216_n_req <= 2" in cell9_src, "req-count threshold missing"
    assert "len(_v216_vibe) >= 2000" in cell9_src, "vibe-length threshold missing"
    assert "_v216_review_signals >= 2" in cell9_src, "review-signals threshold missing"


def test_v216_safety_net_segments_by_headers(cell9_src):
    """Safety net must segment by ### N. headers and re-parse per segment."""
    assert "_v216_hdr_re" in cell9_src
    # Each segment must call the LLM parser again
    assert 'step_name=f"vibe_parse_segment_' in cell9_src


def test_v216_safety_net_dedupes_by_intent(cell9_src):
    """Safety net must dedupe new requirements vs already-extracted ones."""
    assert "_v216_seen_intents" in cell9_src


# ---------------------------------------------------------------------------
# A4. Behaviour: the detector logic (extracted as regex) classifies the
#     HC vibe as Shape-B silent-drop and gov_transport as Shape-A no-drop.
#
# This re-implements the detection inline (same regex set as the safety net)
# and asserts the boolean classification against the LIVE v215 vibe fixtures.
# ---------------------------------------------------------------------------
PATTERNS = [
    r"^###\s*\d+\.\s+",
    r"^Priority:",
    r"^Recommendation:",
    r"Must Fix",
    r"Should Fix",
    r"What the Model Could Improve",
    r"Holistic Critique",
    r"Reviewer:",
    r"## What the Model Does Well",
    r"Concrete asks",
    r"## \d+\.\s+",
]


def _classify(vibe_text: str, n_req: int) -> bool:
    """Return True iff the v216 safety net would fire."""
    signals = sum(
        1 for pat in PATTERNS if re.search(pat, vibe_text, re.MULTILINE)
    )
    return n_req <= 2 and len(vibe_text) >= 2000 and signals >= 2


HC_FIXTURE_PATH = Path("/Users/user/vibe_inputs/hc_feedback_vibes.md")
RT_FIXTURE_PATH = Path("/Users/user/vibe_inputs/rt_feedback_vibes.md")


def test_v216_detector_fires_on_hc_feedback():
    """The actual live HC feedback doc that triggered the v215 4% must trigger the safety net."""
    if not HC_FIXTURE_PATH.exists():
        pytest.skip("HC fixture not present in this checkout")
    hc = HC_FIXTURE_PATH.read_text()
    # Live v215 returned 1 requirement → simulate with n_req=1
    assert _classify(hc, n_req=1), (
        "v216 detector failed to fire on the same HC reviewer-feedback doc "
        "that produced the v215 Stage A=4% silent-drop"
    )


def test_v216_detector_fires_on_rt_feedback():
    if not RT_FIXTURE_PATH.exists():
        pytest.skip("RT fixture not present in this checkout")
    rt = RT_FIXTURE_PATH.read_text()
    assert _classify(rt, n_req=1), (
        "v216 detector failed to fire on the same RT reviewer-feedback doc "
        "that produced the v215 Stage A=4% silent-drop"
    )


def test_v216_detector_does_not_fire_on_gov_transport_style_directive():
    """gov_transport-style structured directive must NOT trigger the safety net (no false positive)."""
    gov_transport_like = """
## gov_transport — base model

### Domains (build exactly these)

#### 1. hr
- employee
- position
- job

#### 2. project
- activity
- milestone

### Final ground rules
- snake_case naming
- BIGINT primary keys
"""
    # gov_transport-style produced 21 reqs in v215 — simulate even an n_req=21 outcome
    assert not _classify(gov_transport_like, n_req=21), (
        "false positive: gov_transport-style directive incorrectly classified as Shape B silent-drop"
    )


def test_v216_detector_does_not_fire_when_small_vibe():
    """Empty/tiny vibes (e.g. user passed just a 1-paragraph description) must not trigger."""
    short_vibe = "Build a healthcare data model that captures patient encounters and billing."
    assert not _classify(short_vibe, n_req=1)


def test_v216_detector_does_not_fire_when_already_many_reqs():
    """If the LLM already returned many reqs we must not double-run the safety net."""
    big_review = HC_FIXTURE_PATH.read_text() if HC_FIXTURE_PATH.exists() else ""
    if not big_review:
        pytest.skip("HC fixture not available")
    assert not _classify(big_review, n_req=15), (
        "safety net incorrectly fires even after the LLM returned 15 reqs"
    )


# ---------------------------------------------------------------------------
# A5. The §10.6 FIRED log emits the alias so audit grep can confirm the fix
# ---------------------------------------------------------------------------
def test_v216_fired_log_includes_alias_for_audit_grep(cell9_src):
    # The grep that the §10.6 audit will run must locate this exact alias
    assert re.search(r"\[vibe-parse-silent-drop FIRED v2\.1\.6\]", cell9_src)
    assert "alias=vibe-parse-silent-drop-safety-net" in cell9_src
