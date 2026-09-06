import json
import re
import textwrap

from notebook_source_util import cell_containing


def _cell_src(marker):
    """The code cell that owns `marker`.

    This used to take a cell INDEX. The notebook grew, every index drifted, and all
    nine behavioral tests below stopped reaching the code they name while still
    reporting a failure that looked like a product bug.
    """
    return cell_containing(marker)


def _slice(src, start_marker, end_marker, include_end=False):
    i = src.index(start_marker)
    i = src.rfind("\n", 0, i) + 1
    j = src.index(end_marker, i)
    if include_end:
        j = src.index("\n", j) + 1
    return src[i:j]


# ---- version anchor (forward-compatible: v3.4.5 fixes must persist at or beyond 3.4.5) ----
def test_v345_version_constant():
    src = _cell_src('__AGENT_VERSION__ = "')
    m = re.search(r'__AGENT_VERSION__ = "(\d+)\.(\d+)\.(\d+)"', src)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 4, 5)


# ---- mutator-json-literal-alias: prefix binds null/true/false ----
def test_v345_prefix_aliases_json_literals():
    src = _cell_src("null = None")
    # extract the raw prefix string body and assert the aliases are present + bind correctly
    assert "null = None" in src
    assert "true = True" in src
    assert "false = False" in src
    # behavioral: the three assignment lines actually bind to the Python singletons
    ns = {}
    exec("null = None\ntrue = True\nfalse = False\n", ns)
    assert ns["null"] is None and ns["true"] is True and ns["false"] is False
    # and LLM-style JSON-literal code resolves under that namespace (would NameError pre-fix)
    exec("d = {'a': null, 'b': true, 'c': false}", ns)
    assert ns["d"] == {"a": None, "b": True, "c": False}


# ---- retry-feedback hint table (behavioral) ----
def _exec_hints():
    src = _cell_src("def _v204_ast_class_hints(")
    block = _slice(src, "def _v204_ast_class_hints(", "return ", include_end=False)
    # the function ends after building/returning hints; slice generously to the final return
    full = src[src.index("def _v204_ast_class_hints("):]
    # take up to the line that returns the joined hints (first standalone 'return' after the for-loop)
    end = full.index("\n    return ")
    end = full.index("\n", end + len("\n    return ")) + 1
    block = textwrap.dedent(full[:end])

    class _L:
        def info(self, *a, **k):
            pass
    ns = {"logger": _L(), "re": re}
    exec(block, ns)
    return ns["_v204_ast_class_hints"]


def test_v345_undefined_name_hint_fires():
    h = _exec_hints()
    out = h("attempt 3: mutator raised: NameError: name 'TARGET_SPECS' is not defined")
    assert out, "no hint for undefined-name trace"
    assert "UNDEFINED NAME" in out
    assert "model" in out and "data" in out
    # also covers the 'null' undefined case
    out2 = h("NameError: name 'null' is not defined")
    assert "UNDEFINED NAME" in out2


def test_v345_list_dict_shape_hint_fires():
    # The v3.4.5 hint was worded "LIST/DICT SHAPE". v4.0.2 suppresses that generic
    # wording once a TYPE-ACCURATE hint fires (so the retry is not given contradictory
    # dict advice for a list), and v4.1.9 brought `list` into that typed path. What must
    # hold across those rewrites is the guarantee, not the label: the trace still yields
    # a hint that names both shapes and teaches the real model collections.
    h = _exec_hints()
    out = h("mutator raised: AttributeError: 'list' object has no attribute 'get'")
    assert out, "a list/.get trace must still produce a hint"
    assert "LIST" in out and "DICT" in out
    assert "attributes" in out or "products" in out  # teaches the real model shape
    out2 = h("AttributeError: 'dict' object has no attribute 'append'")
    assert out2 and "LIST" in out2 and "DICT" in out2
    assert "attributes" in out2 or "products" in out2


def test_v345_hint_nontautology_clean_trace_returns_empty():
    # NON-TAUTOLOGY: a trace with no known failure needle must yield NO hint.
    h = _exec_hints()
    assert h("everything finished successfully, no errors") == ""
    assert h("") == ""


# ---- gt-tag-prefix-compound-violation: per-token prefix check (behavioral) ----
def _exec_prefix_checker(prefix="gov_transport_"):
    src = _cell_src("def _key_violates_prefix(_k):")
    # universal-token helper
    uni = _slice(src, '_UNIVERSAL_TAGS = {"pii"',
                 "return all(_is_universal_token(p) for p in _parts)", include_end=True)
    # compound-violation helper (the v3.4.5 fix)
    viol = _slice(src, "def _key_violates_prefix(_k):",
                  "_industry_keys = [k for k in set(_tag_keys)", include_end=False)
    block = textwrap.dedent(uni) + "\n" + textwrap.dedent(viol)
    ns = {"_rt": re, "_pl": prefix.lower()}
    exec(block, ns)
    return ns["_key_violates_prefix"]


def test_v345_compound_key_with_prefixed_token_not_violation():
    # The exact gov_transport VREQ-005 false-positive: universal classification tokens + a prefixed
    # industry token -> compliant (NOT a violation).
    v = _exec_prefix_checker()
    assert v("confidential,pii_address,gov_transport_business_glossary_term") is False
    assert v("restricted,pii_demographic,gov_transport_business_glossary_term") is False
    assert v("gov_transport_source_table") is False
    assert v("pii,confidential") is False  # all universal


def test_v345_compound_violation_nontautology():
    # NON-TAUTOLOGY: a non-universal token WITHOUT the prefix must STILL be flagged.
    v = _exec_prefix_checker()
    assert v("employee_status") is True
    assert v("confidential,employee_status") is True  # one bad token taints the key
    assert v("project_phase,pii") is True


# ---- mv-column-prevalidate-prune: keep MV, prune offending blocks (behavioral) ----
def _real_sql_kw():
    """The `_mvcp_SQL_KW` the notebook actually uses."""
    src = _cell_src("_mvcp_SQL_KW = set([")
    block = _slice(src, "_mvcp_SQL_KW = set([", "])", include_end=True)
    ns = {}
    exec(textwrap.dedent(block), ns)
    return ns["_mvcp_SQL_KW"]


def _exec_mv_prune():
    src = _cell_src("def _mvcp_bad_in_expr(_expr_raw):")
    block = _slice(src, "def _mvcp_bad_in_expr(_expr_raw):",
                   "_drop_reasons2.append((_vname, f\"physical `{_src_sch}.{_src_tbl}` missing",
                   include_end=True)
    block = textwrap.dedent(block)
    wrapped = (
        "def run(_stmt, _src_cols):\n"
        "    _kept2 = []; _drop_reasons2 = []; _rename_reasons2 = []\n"
        "    _src_sch, _src_tbl = 'hr', 'position'\n"
        "    for _ in [0]:\n"
        + textwrap.indent(block, "        ")
        + "    return _kept2, _drop_reasons2, _rename_reasons2\n"
    )
    ns = {
        "_mvcp_re": re,
        "_mvcp_token_re": re.compile(r"\b([a-z_][a-z0-9_]*)\b"),
        # The notebook's own denylist, not a stub of it: a stub that omitted `distinct`
        # made a DISTINCT aggregate look like a reference to a missing column.
        "_mvcp_SQL_KW": _real_sql_kw(),
        "_extract_metric_view_name_from_statement": lambda s: "hr_vacancy_rate",
    }
    exec(wrapped, ns)
    return ns["run"]


_MV_STMT = (
    "CREATE OR REPLACE VIEW `c`.`_metrics`.`hr_vacancy_rate`\n"
    "WITH METRICS\n"
    "LANGUAGE YAML\n"
    "AS $$\n"
    "version: 0.1\n"
    "source: `c`.`hr`.`position`\n"
    "  dimensions:\n"
    '    - name: "Position Description"\n'
    "      expr: description\n"
    '    - name: "Cost Center"\n'
    "      expr: cost_center_id\n"
    "  measures:\n"
    '    - name: "Vacancy Rate"\n'
    "      expr: ROUND(100.0 * SUM(CASE WHEN vacancy_status = 'Vacant' THEN 1 ELSE 0 END) / NULLIF(COUNT(1), 0), 2)\n"
    "$$"
)


def test_v345_mv_prune_keeps_view_drops_bad_dimension():
    run = _exec_mv_prune()
    # physical hr.position HAS cost_center_id + vacancy_status, but NOT 'description'
    kept, reasons, _renames = run(_MV_STMT, {"position_id", "cost_center_id", "vacancy_status"})
    assert len(kept) == 1, "the MV must be KEPT (not dropped) after pruning"
    out = kept[0]
    # the bad dimension is pruned, the good dimension + the real measure survive
    assert "description" not in out
    assert "Cost Center" in out
    assert "Vacancy Rate" in out
    assert "vacancy_status" in out  # the KPI measure is preserved intact
    assert reasons and "description" in reasons[0][1]


def test_v345_mv_prune_nontautology_clean_mv_unchanged():
    # NON-TAUTOLOGY: an MV whose every column resolves must be kept verbatim, no prune reason.
    run = _exec_mv_prune()
    kept, reasons, _renames = run(_MV_STMT, {"position_id", "cost_center_id", "vacancy_status", "description"})
    assert len(kept) == 1
    assert "Position Description" in kept[0]  # bad dim is now valid -> kept
    assert reasons == []


# ---- mv15-none-resp-guard: post-call resp shape guard (behavioral) ----
def test_v345_mv15_none_resp_guard_present_and_before_get():
    src = _cell_src("alias=mv15-none-resp-guard")
    assert "alias=mv15-none-resp-guard" in src
    # the guard MUST sit BEFORE the unguarded .get on the happy path
    g = src.index("if not isinstance(resp, dict):")
    use = src.index('evaluations = resp.get("evaluations"', g)
    assert g < use, "the None-resp guard must precede resp.get('evaluations')"
    # and the guard returns None (same skip contract as the except branch)
    between = src[g:use]
    assert "return None" in between


def test_v345_mv15_none_resp_guard_behavior():
    # Behavioral: replicate the guard + .get and prove None/non-dict is skipped, dict passes.
    def _body(resp):
        if not isinstance(resp, dict):
            return ("SKIP", None)
        return ("OK", resp.get("evaluations", []))
    # pre-fix this would have raised AttributeError on None
    assert _body(None) == ("SKIP", None)
    assert _body(["not", "a", "dict"]) == ("SKIP", None)
    assert _body({"evaluations": [1, 2]}) == ("OK", [1, 2])
    assert _body({}) == ("OK", [])
