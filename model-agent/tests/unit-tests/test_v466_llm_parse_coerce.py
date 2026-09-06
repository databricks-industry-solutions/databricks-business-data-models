"""v4.6.6 behavioral tests -- llm-parse-coerce (issue-#21 systemic hardening).

The LLM can return a valid-JSON scalar / list where the consumer expects a dict
(or an array field set to a scalar / list-of-scalars). Pre-fix, the consumer did
`X.get(...)` / iterated `X` and crashed with AttributeError -- the exact issue-#21
class. v4.6.6 adds `_v466_coerce_llm_obj` (35 parse + smart_worker_loop sites) and
wraps 11 propagating non-validator nested-list iterations in `_coerce_list_of_dicts`.

These tests:
- isolate `_v466_coerce_llm_obj` + `_coerce_dict` / `_coerce_list_of_dicts` via AST,
- prove the helper coerces scalars/lists/None to a safely-consumable dict AND fires,
- prove `_coerce_list_of_dicts` neutralises list-of-scalars (the N4 nested crash),
- static-assert the fixes are physically present in the deployed cells.
"""
from __future__ import annotations

from notebook_source_util import agent_version_line

import ast
import json
from pathlib import Path

NB = Path(__file__).resolve().parents[2] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _nb():
    return json.loads(NB.read_text())


def _cell_src(idx: int) -> str:
    src = _nb()["cells"][idx]["source"]
    return "".join(src) if isinstance(src, list) else src


def _full_src() -> str:
    return "".join(
        ("".join(c["source"]) if isinstance(c["source"], list) else c["source"])
        for c in _nb()["cells"]
    )


class _Log:
    def __init__(self):
        self.lines = []

    def warning(self, m):
        self.lines.append(str(m))

    info = warning
    error = warning


def _load_coerce_ns():
    """Isolate the three coerce helpers from cell 25 via AST (no notebook exec)."""
    cell25 = _cell_src(25)
    tree = ast.parse(cell25)
    wanted = {"_coerce_dict", "_coerce_list_of_dicts", "_v466_coerce_llm_obj"}
    body = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted
    ]
    names = {n.name for n in body}
    assert wanted <= names, f"missing helpers in cell 25: {wanted - names}"
    ns: dict = {"json": json, "re": __import__("re"), "logging": __import__("logging")}
    exec(compile(ast.Module(body=body, type_ignores=[]), "<cell25>", "exec"), ns)
    return ns


# ----------------------------- version + presence -----------------------------

def test_agent_version_is_466():
    src = _cell_src(1)
    assert agent_version_line() in src
    for line in src.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert s == agent_version_line()
        break


def test_helper_defined_once():
    assert _cell_src(25).count("def _v466_coerce_llm_obj(") == 1


def test_all_llm_parse_sites_present():
    """35 call sites (23 json-parse + 12 smart_worker_loop) + 1 def = 36."""
    assert _full_src().count("_v466_coerce_llm_obj") == 36


def test_nested_list_coercions_present():
    """11 propagating non-validator nested-list iterations wrapped."""
    src = _full_src()
    for expr in [
        'for product in _coerce_list_of_dicts(products_response.get("products", []))',
        'for prod in _coerce_list_of_dicts(products_response.get("products", []))',
        'for attr in _coerce_list_of_dicts(attrs_response.get("attributes", []))',
        'for product in _coerce_list_of_dicts(products_data.get("products", []))',
        'for _d in _coerce_list_of_dicts(response_data.get("domains", []))',
        'for item in _coerce_list_of_dicts(data.get("requirements", []))',
        'for vr in _coerce_list_of_dicts(data.get("verification_results", []))',
    ]:
        assert expr in src, f"missing nested-list coercion: {expr}"


# ----------------------------- behavioral: the helper -----------------------------

def test_scalar_string_coerced_and_fires():
    ns = _load_coerce_ns()
    coerce = ns["_v466_coerce_llm_obj"]
    out = coerce("Domain looks fine, no changes needed.", site="unit")
    assert isinstance(out, dict)  # pre-fix a str would flow through and crash on .get
    assert out.get("anything", "dflt") == "dflt"  # safely consumable


def test_list_coerced_to_dict():
    ns = _load_coerce_ns()
    coerce = ns["_v466_coerce_llm_obj"]
    out = coerce([{"k": 1}, "noise"], site="unit")
    assert isinstance(out, dict)
    assert hasattr(out, "get")


def test_none_coerced_to_dict():
    ns = _load_coerce_ns()
    coerce = ns["_v466_coerce_llm_obj"]
    out = coerce(None, site="unit")
    assert isinstance(out, dict)


def test_valid_dict_passthrough_unchanged():
    ns = _load_coerce_ns()
    coerce = ns["_v466_coerce_llm_obj"]
    d = {"products": [{"name": "x"}], "assessment": "ok"}
    assert coerce(d, site="unit") is d  # identity: no wasteful copy on the happy path


def test_fired_signal_logged_on_drift():
    """The FIRED signal is the diagnostic that a would-be issue-#21 crash was prevented."""
    ns = _load_coerce_ns()
    import logging

    log = logging.getLogger("vibe_agent")
    captured = []

    class _H(logging.Handler):
        def emit(self, r):
            captured.append(r.getMessage())

    h = _H()
    log.addHandler(h)
    log.setLevel(logging.WARNING)
    try:
        ns["_v466_coerce_llm_obj"]("scalar", site="mysite")
    finally:
        log.removeHandler(h)
    assert any("llm-parse-coerce FIRED v4.6.6" in m and "mysite" in m for m in captured)


# ------------------- behavioral: the N4 nested-list crash class -------------------

def test_list_of_scalars_iteration_is_neutralised():
    """`for x in _coerce_list_of_dicts(resp.get('k',[]))` must not yield scalars
    (pre-fix: `for x in resp.get('k',[])` with k=list-of-str -> x.get crashes)."""
    ns = _load_coerce_ns()
    clod = ns["_coerce_list_of_dicts"]
    resp = {"products": ["just_a_name", 7, None, {"name": "real"}]}
    items = clod(resp.get("products", []))
    # every yielded item is safely .get-able
    for it in items:
        assert hasattr(it, "get")
    assert {"name": "real"} in items


def test_scalar_array_field_neutralised():
    ns = _load_coerce_ns()
    clod = ns["_coerce_list_of_dicts"]
    assert clod("not a list") == []
    assert clod(None) == []
