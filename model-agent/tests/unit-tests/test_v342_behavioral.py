"""Behavioral tests for v3.4.2 verifier-honesty fixes.

These prove the two false-negative classes that produced the "lying scoreboard"
(agent ground-truth-audit reported 45.5% while the model was ~89% physically
correct on gov_transport mvm_v1) are eliminated, WITHOUT re-running the multi-hour
pipeline. Each test execs the VERBATIM source slice from the deployed notebook
(not a re-implementation) so it exercises the real code path.

  RC tag-prefix scope (gt-tag-prefix-scope, cell 9 _verify_deterministic):
      The industry tag-prefix rule (`gov_transport_`) was applied to EVERY observed tag
      key, so universal/structural tag families (classification/pii/system/
      lineage) were force-failed as "missing prefix". The fix exempts universal
      tags; only industry-specific keys must carry the prefix.

  RC ground-truth rescue (gt-rescue, cell 23 _run_ground_truth_audit):
      Declaration-type VREQs (systems-of-record / governing-body) live in model
      root business_context, not as physical tags, and key-convention VREQs (id
      type) were read from a lossy snapshot -> both false-failed. The rescue
      GROUNDS them against model metadata + physical column types and ONLY
      upgrades a failed/partial verdict (never downgrades a deterministic PASS).
"""
import json
import re
import textwrap

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _cell_src(idx):
    nb = json.load(open(NB))
    return "".join(nb["cells"][idx]["source"])


def _slice(src, start_marker, end_marker, include_end=True):
    i = src.index(start_marker)
    i = src.rfind("\n", 0, i) + 1  # snap to start of line so indentation is uniform
    j = src.index(end_marker, i)
    if include_end:
        j = src.index("\n", j) + 1
    return src[i:j]


# --------------------------------------------------------------------------- #
# gt-tag-prefix-scope (cell 9)                                                 #
# --------------------------------------------------------------------------- #
def _exec_tag_prefix(tag_keys, prefix):
    """Exec the verbatim _UNIVERSAL_TAGS / _is_universal_tag / _viol slice."""
    src = _cell_src(9)
    # v3.4.4/v3.4.5 refactored the prefix check into _is_universal_token + _key_violates_prefix
    # (compound-tag aware), so the final _viol line now reads through _key_violates_prefix. Slice to
    # the CURRENT terminator so the white-box test exercises the live, improved implementation.
    block = _slice(src, "_UNIVERSAL_TAGS = {",
                   "_viol = [k for k in set(_tag_keys) if _key_violates_prefix(k)]")
    block = textwrap.dedent(block)
    ns = {"_rt": re, "_tag_keys": tag_keys, "_p": prefix}
    exec(block, ns)
    return ns["_viol"], ns["_industry_keys"]


def test_v342_tag_prefix_alias_present():
    assert "gt-tag-prefix-scope" in _cell_src(9)


def test_v342_universal_tags_exempt_from_prefix():
    """confidential/pii/system/self_ref_fk must NOT be flagged as prefix violations."""
    universal = ["confidential", "pii", "classification", "self_ref_fk",
                 "cg_business_unit", "system_load_ts", "primary_key"]
    viol, industry = _exec_tag_prefix(universal, "gov_transport_")
    assert viol == [], f"universal tags wrongly flagged: {viol}"
    assert industry == [], f"universal tags wrongly treated as industry: {industry}"


def test_v342_industry_tag_without_prefix_still_flagged():
    """A genuine industry tag missing the prefix MUST still be a violation (no over-rescue)."""
    keys = ["gov_transport_division", "route_classification", "confidential"]
    viol, industry = _exec_tag_prefix(keys, "gov_transport_")
    assert "route_classification" in viol, f"genuine violation missed: viol={viol}"
    assert "gov_transport_division" not in viol
    assert "confidential" not in viol  # universal exempt
    assert "confidential" not in industry


def test_v342_tag_prefix_differs_from_prepatch_behavior():
    """Prove the patch CHANGES behavior: pre-patch logic flags universal tags, post-patch does not."""
    keys = ["confidential", "pii", "gov_transport_division"]
    prefix = "gov_transport_"
    # pre-patch: _viol = [k for k in set(_tag_keys) if not k.startswith(_p)]
    prepatch_viol = sorted(k for k in set(keys) if not k.startswith(prefix))
    postpatch_viol, _ = _exec_tag_prefix(keys, prefix)
    assert "confidential" in prepatch_viol and "pii" in prepatch_viol  # old logic false-fails
    assert "confidential" not in postpatch_viol and "pii" not in postpatch_viol  # fixed


# --------------------------------------------------------------------------- #
# gt-rescue (cell 23)                                                          #
# --------------------------------------------------------------------------- #
class _Req:
    def __init__(self, text, rid="VREQ-X"):
        self.original_text = text
        self.id = rid


def _exec_gt_rescue():
    """Exec the verbatim _gt_rank + _gt_rescue closure definitions from cell 23."""
    src = _cell_src(23)
    block = _slice(src, "def _gt_rank(_s):", "# Re-verify EVERY VREQ", include_end=False)
    block = textwrap.dedent(block)
    ns = {}
    exec(block, ns)
    return ns["_gt_rank"], ns["_gt_rescue"]


def test_v342_gt_rescue_alias_present():
    s = _cell_src(23)
    assert "gt-rescue/context" in s and "gt-rescue/key" in s


def test_v342_gt_rank_ordering():
    rank, _ = _exec_gt_rescue()
    assert rank("fulfilled") > rank("partial") > rank("failed") > rank("unknown") == rank(None)


def test_v342_rescue_context_systems_of_record():
    """Declaration VREQ for systems-of-record is rescued to fulfilled when metadata present."""
    _, rescue = _exec_gt_rescue()
    req = _Req("All entities must declare their operational systems of record.")
    bc = {"operational_systems_of_records": "SAP S/4HANA, Oracle EBS, Salesforce"}
    res = rescue(req, [], bc)
    assert res and res["status"] == "fulfilled", res


def test_v342_rescue_context_absent_metadata_no_false_pass():
    """If the metadata is empty, rescue returns None -> never a false PASS."""
    _, rescue = _exec_gt_rescue()
    req = _Req("Declare the industry governing body for the model.")
    res = rescue(req, [], {"industry_governing_body": ""})
    assert res is None, res


def test_v342_rescue_key_idtype_bigint_physical():
    """Key-convention id-type VREQ grounds on PHYSICAL column data types."""
    _, rescue = _exec_gt_rescue()
    req = _Req("Use BIGINT as the table-id type for every primary key _id column.")
    phys = [{"attribute": "employee_id", "data_type": "bigint"},
            {"attribute": "project_id", "data_type": "bigint"}]
    res = rescue(req, phys, {})
    assert res and res["status"] == "fulfilled", res


def test_v342_rescue_never_downgrades_is_caller_guarded():
    """The rescue itself only emits fulfilled/partial/None; the caller guards rank-upgrade-only."""
    rank, rescue = _exec_gt_rescue()
    req = _Req("Use BIGINT as the table-id type.")
    phys = [{"attribute": "a_id", "data_type": "string"}] * 10  # all wrong type
    res = rescue(req, phys, {})
    # all-bad -> no partial/fulfilled returned (returns None), cannot fabricate a pass
    assert res is None, res
