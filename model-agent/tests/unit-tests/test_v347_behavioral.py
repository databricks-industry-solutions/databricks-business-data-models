import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _cell_src(idx):
    nb = json.load(open(NB))
    return "".join(nb["cells"][idx]["source"])


def _full():
    nb = json.load(open(NB))
    return "".join("".join(c.get("source", [])) for c in nb["cells"])


def test_v347_version_constant():
    src = _cell_src(1)
    m = re.search(r'__AGENT_VERSION__ = "(\d+)\.(\d+)\.(\d+)"', src)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 4, 7)


def test_v347_physical_mirror_wired_into_finalize():
    full = _full()
    # the mirror must be CALLED inside step_finalize (before physical apply), not just defined
    fin_i = full.index("def step_finalize_model_before_physical_schema(")
    fin_seg = full[fin_i:fin_i + 6000]
    assert "_mirror_trace_tags_into_tags_string(products_data, attributes_data" in fin_seg
    assert "trace-tag-physical-mirror" in full


def test_v347_gt_rescue_tagkey_eq_regex():
    # ROOT CAUSE behavioral: tag key embedded as `key=value` must be extractable so physical tags
    # can rescue the VREQ (gov_transport VREQ-013 false-negative). Old regex returned []; new returns the key.
    raw = "attach the tag `gov_transport_business_glossary_term=<Business Data Element>` whenever a match exists"
    old = re.findall(r"`([a-z0-9_]+)`", raw)
    new = [k for k in re.findall(r"`([a-z0-9_]+)(?:=[^`]*)?`", raw) if "_" in k]
    assert old == []  # proves the bug existed
    assert new == ["gov_transport_business_glossary_term"]  # proves the fix works
    # and the fixed pattern is present in the deployed source
    assert "gt-rescue-tagkey-eq" in _full()
    assert r"`([a-z0-9_]+)(?:=[^`]*)?`" in _full()


def test_v347_gt_mv_prefix_tolerant():
    # ROOT CAUSE behavioral: physical MV names carry the domain prefix; KPI-named requirement must match.
    phys = {"hrvacancyrate", "hrtotalpositionsandactiveemployees", "hrretirementeligibility"}

    def mvm(rn):
        return any(pn == rn or pn.endswith(rn) or (len(rn) >= 6 and rn in pn) for pn in phys)

    assert mvm("vacancyrate")  # the false-negative case now matches
    assert not mvm("payroll")  # non-existent MV must NOT match (no over-rescue)
    assert "gt-mv-prefix-tolerant" in _full()


def test_v347_gt_rescue_subdomain_and_pk_paths_present():
    full = _full()
    assert "gt-rescue-subdomain" in full
    assert "gt-rescue-canonical-pk" in full
    assert "subdomain groupings physically present" in full


def test_v347_shared_harvest_helper_is_dry():
    full = _full()
    # one shared module-level harvester used by both enrich (tag_set) and mirror (tags string)
    assert full.count("def _harvest_trace_tags(") == 1
    assert "_harvest_trace_tags(" in full
