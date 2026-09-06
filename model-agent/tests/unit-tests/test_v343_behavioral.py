import json
import re
import textwrap

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


class _Req:
    def __init__(self, text, rid="VREQ-X", scope="", scope_targets=None):
        self.original_text = text
        self.id = rid
        self.scope = scope
        self.scope_targets = scope_targets or []


def _exec_rescue():
    src = _cell_src(23)
    block = _slice(src, "def _gt_rank(_s):", "# Re-verify EVERY VREQ", include_end=False)
    block = textwrap.dedent(block)
    ns = {}
    exec(block, ns)
    return ns["_gt_rank"], ns["_gt_overlap"], ns["_gt_rescue"]


# ---- version anchor ----
def test_v343_version_constant():
    # forward-compatible anchor: v3.4.3 fixes must persist at or beyond 3.4.3
    # (exact-version assertion is owned by the current version's test file).
    import re as _re
    c1 = _cell_src(1)
    m = _re.search(r'__AGENT_VERSION__ = "(\d+)\.(\d+)\.(\d+)"', c1)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 4, 3)


# ---- FIX A: gt-bc-source merges the right context dicts ----
def test_v343_bc_source_merges_business_config_context():
    src = _cell_src(23)
    assert "gt-bc-source FIRED v3.4.3" in src
    # must read business_config.business_context (the real source), not only business_context_data
    blk = _slice(src, "_gt_bc = {}", "def _gt_rank(_s):")
    assert '_bcfg_bc.get("business_context")' in blk
    assert '_pv_bc.get("business_context_generated")' in blk


# ---- FIX A behavior: declaration VREQ grounds against model business_context ----
def test_v343_context_rescue_systems_of_record_fulfilled():
    _, _, rescue = _exec_rescue()
    req = _Req("The operational systems of record for this base model are: SAP, DCH, Beacon, "
               "DB2 Mainframe, SharePoint, and Web Applications.")
    bc = {"operational_systems_of_records": "SAP, DCH, Beacon, DB2 Mainframe, SharePoint, Web Applications"}
    res = rescue(req, [], bc)
    assert res and res["status"] == "fulfilled", res


def test_v343_context_rescue_empty_metadata_returns_none():
    # honesty: no declared metadata -> do NOT rubber-stamp
    _, _, rescue = _exec_rescue()
    req = _Req("The operational systems of record are: SAP, DCH, Beacon.")
    res = rescue(req, [], {})
    assert res is None, res


def test_v343_context_rescue_wrong_systems_not_fulfilled():
    # honesty: declared value that does NOT overlap the required systems must not pass as fulfilled
    _, _, rescue = _exec_rescue()
    req = _Req("The operational systems of record are: SAP, DCH, Beacon, DB2 Mainframe, SharePoint, Web Applications.")
    bc = {"operational_systems_of_records": "Salesforce, Workday, Oracle"}
    res = rescue(req, [], bc)
    assert (res is None) or (res["status"] != "fulfilled"), res


# ---- FIX C: conditional bulk-tag grounds against physical tag presence ----
def test_v343_conditional_tag_present_fulfilled():
    _, _, rescue = _exec_rescue()
    req = _Req("For every attribute, attach the tag `gov_transport_business_glossary_term` whenever a match "
               "exists in the business glossary table.")
    phys = [{"attribute": "c%d" % i, "tags": "gov_transport_business_glossary_term=cde_%d" % i} for i in range(100)]
    phys += [{"attribute": "u%d" % i, "tags": ""} for i in range(200)]  # most untagged (conditional => OK)
    res = rescue(req, phys, {})
    assert res and res["status"] == "fulfilled", res


def test_v343_tag_no_physical_hits_returns_none():
    # honesty: tag-key never physically present -> no rescue
    _, _, rescue = _exec_rescue()
    req = _Req("Attach the tag `gov_transport_business_glossary_term` whenever a match exists.")
    phys = [{"attribute": "c%d" % i, "tags": "pii=true"} for i in range(50)]
    res = rescue(req, phys, {})
    assert res is None, res


def test_v343_unconditional_tag_low_coverage_partial_not_fulfilled():
    # unconditional "every attribute" with only 33% coverage must be partial, never fulfilled
    _, _, rescue = _exec_rescue()
    req = _Req("Attach the tag `gov_transport_source_attribute` to every attribute in the model.")
    phys = [{"attribute": "c%d" % i, "tags": "gov_transport_source_attribute=x"} for i in range(33)]
    phys += [{"attribute": "u%d" % i, "tags": ""} for i in range(67)]
    res = rescue(req, phys, {})
    assert res and res["status"] == "partial", res


# ---- FIX B: gt-mv-verify name regex now captures names followed by ':' ----
def test_v343_mv_name_regex_captures_colon_terminated():
    src = _cell_src(23)
    # the exact regex used by gt-mv-verify
    assert r"(?:\s+metric\s+view|[\.,:;]|$)" in src
    pat = re.compile(r'kpi[\s_-]*\d+\s+([A-Za-z][A-Za-z &/]+?)(?:\s+metric\s+view|[\.,:;]|$)', re.I)
    txt = ("Build EXACTLY this metric view - KPI-3 Total Positions and Active Employees: "
           "Active Employee = currently employed.")
    names = pat.findall(txt)
    assert any("total positions and active employees" == n.strip().lower() for n in names), names
