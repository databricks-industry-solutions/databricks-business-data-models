"""
v4.5.6 behavioral test -- judge-selection-analysis-coerce (GitHub issue #21).

Reporter: https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/issues/21

Exact crash (agent 4.5.5, new base model / ECM):
    selection_analysis = judge_response.get("selection_analysis", {})
    duplicates_resolved = selection_analysis.get("duplicates_resolved", [])
    AttributeError: 'str' object has no attribute 'get'

Reporter cases covered:
  1. free-text narrative string (WCB Alberta-class judge drift)
  2. JSON-encoded string of the analysis object
  3. already-dict happy path (must not change)
  4. missing key -> default {}
"""
import ast

from notebook_source_util import agent_version_line
import json
import os

import pytest

NB = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb")

# Reporter reproduction: complex workers'-compensation narrative as free-text
# selection_analysis (the shape that crashed step_create_logical_schema line 4414).
_WCB_STYLE_FREE_TEXT = (
    "Resolved overlaps across claims lifecycle, premium assessment, experience "
    "rating, and funding discipline variants; kept 'claims' over 'claim_mgmt', "
    "merged premium_assessment into assessment."
)

_STRUCTURED_ANALYSIS = {
    "duplicates_resolved": [
        {
            "kept": "claims",
            "removed": ["claim_mgmt", "claim_management"],
            "reason": "canonical claims lifecycle domain",
        }
    ],
    "unique_additions": [
        {
            "domain": "experience_rating",
            "source": "variant_2",
            "reason": "missing from majority vote",
        }
    ],
    "conflicts_resolved": [
        {
            "domain": "premium_assessment",
            "conflict_type": "name",
            "resolution": "normalized to assessment",
        }
    ],
}


def _full_src():
    cells = json.load(open(NB))["cells"]
    parts = []
    for c in cells:
        s = c.get("source", [])
        parts.append("".join(s) if isinstance(s, list) else s)
    return "\n".join(parts)


def _load_coerce_helpers():
    cells = json.load(open(NB))["cells"]
    for c in cells:
        s = c.get("source", [])
        text = "".join(s) if isinstance(s, list) else s
        if "def _coerce_dict" not in text or "def _coerce_list_of_dicts" not in text:
            continue
        tree = ast.parse(text)
        wanted = {"_coerce_dict", "_coerce_list_of_dicts"}
        nodes = [
            n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in wanted
        ]
        assert {n.name for n in nodes} == wanted
        ns = {}
        exec(compile(ast.Module(nodes, []), "<coerce-helpers>", "exec"), ns)
        return ns["_coerce_dict"], ns["_coerce_list_of_dicts"]
    raise AssertionError("_coerce_dict / _coerce_list_of_dicts not found")


def _reporter_pre_patch_path(judge_response):
    """Exact pre-4.5.6 lines from the issue stack trace."""
    if isinstance(judge_response, str):
        judge_response = json.loads(judge_response)
    selection_analysis = judge_response.get("selection_analysis", {})
    duplicates_resolved = selection_analysis.get("duplicates_resolved", [])
    unique_additions = selection_analysis.get("unique_additions", [])
    return selection_analysis, duplicates_resolved, unique_additions


def _reporter_post_patch_path(coerce_dict, coerce_list_of_dicts, judge_response, logs):
    """v4.5.6 production path (reporter cases + existing _coerce_* helpers)."""
    if isinstance(judge_response, str):
        judge_response = json.loads(judge_response)
    _sa_raw = judge_response.get("selection_analysis", {})
    if isinstance(_sa_raw, str):
        try:
            _sa_raw = json.loads(_sa_raw)
        except (json.JSONDecodeError, TypeError):
            pass
    if not isinstance(_sa_raw, dict):
        logs.append(
            f"[judge-selection-analysis-coerce FIRED v4.5.6] "
            f"non-dict selection_analysis type={type(_sa_raw).__name__} - coerced to {{}}"
        )
    selection_analysis = coerce_dict(_sa_raw)
    duplicates_resolved = coerce_list_of_dicts(
        selection_analysis.get("duplicates_resolved", [])
    )
    unique_additions = coerce_list_of_dicts(
        selection_analysis.get("unique_additions", [])
    )
    return selection_analysis, duplicates_resolved, unique_additions


def _issue21_judge(selection_analysis):
    return {
        "business": "wcb_alberta",
        "description": "Workers compensation with claims lifecycle, premium assessment, experience rating, funding discipline",
        "standards": [],
        "domains": [
            {"domain": "claims", "division": "operations", "description": "claims lifecycle", "source_models": ["v1"]},
            {"domain": "assessment", "division": "business", "description": "premium assessment", "source_models": ["v2"]},
        ],
        "selection_analysis": selection_analysis,
        "confidence_score": 78,
        "feedback": "complex domain drift",
    }


def test_version_is_456():
    assert agent_version_line() in _full_src()


def test_wiring_matches_issue21_fix_site():
    src = _full_src()
    assert "judge-selection-analysis-coerce FIRED v4.5.6" in src
    assert "if isinstance(_sa_raw, str):" in src
    assert "_sa_raw = json.loads(_sa_raw)" in src
    assert "selection_analysis = _coerce_dict(_sa_raw)" in src
    assert "_coerce_list_of_dicts(selection_analysis.get(\"duplicates_resolved\"" in src
    assert 'selection_analysis = judge_response.get("selection_analysis", {})' not in src
    assert "Explanation of how you resolved overlaps and duplicates" not in src
    assert "NOT a free-text string" in src


def test_issue21_fail_pre_free_text_selection_analysis_raises_attributeerror():
    """Reporter case 1: narrative string -> exact AttributeError from issue body."""
    judge = _issue21_judge(_WCB_STYLE_FREE_TEXT)
    with pytest.raises(AttributeError, match="'str' object has no attribute 'get'"):
        _reporter_pre_patch_path(judge)


def test_issue21_pass_post_free_text_coerces_to_empty_dict():
    """Reporter proposed fix branch: free-text -> {} without crash."""
    coerce_dict, coerce_list = _load_coerce_helpers()
    logs = []
    sa, dups, adds = _reporter_post_patch_path(
        coerce_dict, coerce_list, _issue21_judge(_WCB_STYLE_FREE_TEXT), logs
    )
    assert sa == {}
    assert dups == []
    assert adds == []
    assert any("judge-selection-analysis-coerce FIRED v4.5.6" in x for x in logs)
    assert any("type=str" in x for x in logs)


def test_issue21_pass_post_json_encoded_string_parses_to_object():
    """Reporter proposed fix branch: JSON-encoded string -> parse, keep structure."""
    coerce_dict, coerce_list = _load_coerce_helpers()
    logs = []
    judge = _issue21_judge(json.dumps(_STRUCTURED_ANALYSIS))
    sa, dups, adds = _reporter_post_patch_path(coerce_dict, coerce_list, judge, logs)
    assert sa["duplicates_resolved"][0]["kept"] == "claims"
    assert dups[0]["kept"] == "claims"
    assert adds[0]["domain"] == "experience_rating"
    assert logs == []


def test_issue21_fail_pre_json_encoded_string_also_crashes():
    """Pre-patch: even a JSON string is still a str, so .get crashes the same way."""
    judge = _issue21_judge(json.dumps(_STRUCTURED_ANALYSIS))
    with pytest.raises(AttributeError, match="'str' object has no attribute 'get'"):
        _reporter_pre_patch_path(judge)


def test_issue21_pass_post_dict_selection_analysis_unchanged():
    coerce_dict, coerce_list = _load_coerce_helpers()
    logs = []
    sa, dups, adds = _reporter_post_patch_path(
        coerce_dict, coerce_list, _issue21_judge(_STRUCTURED_ANALYSIS), logs
    )
    assert dups[0]["kept"] == "claims"
    assert adds[0]["domain"] == "experience_rating"
    assert logs == []


def test_issue21_missing_key_defaults_to_empty_dict():
    coerce_dict, coerce_list = _load_coerce_helpers()
    logs = []
    judge = {
        "domains": [{"domain": "claims", "division": "operations", "description": "x"}],
        "confidence_score": 80,
        "feedback": "ok",
    }
    sa, dups, adds = _reporter_post_patch_path(coerce_dict, coerce_list, judge, logs)
    assert sa == {}
    assert dups == []
    assert adds == []
    assert logs == []


def test_issue21_non_dict_non_string_coerces():
    coerce_dict, coerce_list = _load_coerce_helpers()
    logs = []
    sa, dups, adds = _reporter_post_patch_path(
        coerce_dict, coerce_list, _issue21_judge([1, 2, 3]), logs
    )
    assert sa == {}
    assert dups == []
    assert any("type=list" in x for x in logs)
