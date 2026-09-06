"""v4.0.6 behavioral tests — three ground-truth verifier false-negative fixes.

Diagnosed from the live mfg v4 ECM ground-truth audit (<profile> 2026-06-20), which
reported PHYSICAL adherence 42/50 = 84% with 8 partials that were ALL
false-negatives (the model did the work; the verifier looked in the wrong place):

  1. verifier-preserve-structure   — VREQ-001 'preserve 20 domains/413 products' scored
                                      partial purely because the ATTRIBUTE count drifted
                                      (15631->15418) while domains (20->20) and products
                                      (413->413) were exactly preserved.
  2. verifier-domain-prefix-resolve — VREQ-044/045 'connect production.plant ->
                                      finance.company_code' scored partial because the
                                      SSOT normalizer renamed the table to
                                      production.production_plant; the verifier looked
                                      for 'production.plant' and missed the present FK.
  3. gt-division-schema-tags        — domains_with_division reported 0/20 because the
                                      audit read information_schema.table_tags while the
                                      division tag is SCHEMA-level (schema_tags); live
                                      catalog had 20/20 dbx_division on schema_tags.

Each test proves fail-pre on the committed v4.0.5 backup and pass-post on the live
notebook (§8.10).
"""
import ast
import json
import re
import sys
import types
from pathlib import Path

import agent_helpers as ah

PRE = Path("/tmp/agent_v405_backup.ipynb")  # committed v4.0.5, no v4.0.6 fixes


class _L:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


LOG = _L()


class _Req:
    def __init__(self, text, rid="VREQ-X", scope_targets=None):
        self.original_text = text
        self.id = rid
        self.scope_targets = scope_targets or []
        self.scope = ""


# ----------------------------------------------------------------------------
# tolerant loader for the pre-patch (v4.0.5) backup notebook -> fail-pre module
# (mirrors conftest's node-by-node exec so a few un-execable cells don't abort).
# ----------------------------------------------------------------------------
def _load_backup_module(path: Path):
    if not path.exists():
        import pytest
        pytest.skip(f"pre-patch backup {path} absent (ephemeral /tmp dev artifact); fail-pre half is historical, pass-post protects live behavior")
    nb = json.loads(path.read_bytes().decode("utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    source = "\n\n".join(parts)
    source = re.sub(
        r"\n+(?:#\s*COMMAND\s*-+\s*\n+)?if __name__ == \"__main__\":\s*\n\s+main\(\)\s*\n?\s*$",
        "\n", source, flags=re.DOTALL,
    )

    class _Stub:
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, n):
            return _Stub()

        def __call__(self, *a, **k):
            return _Stub()

        def __bool__(self):
            return False

        def __iter__(self):
            return iter([])

        def __getitem__(self, k):
            return _Stub()

        def __len__(self):
            return 0

    mod = types.ModuleType("agent_helpers_v405")
    mod.__dict__.update({"spark": _Stub(), "dbutils": _Stub(),
                         "displayHTML": lambda *a, **k: None, "SparkSession": _Stub(),
                         "_POOL_ENGINE_AVAILABLE": True,
                         "_OBS_AVAILABLE": False})
    _BLOCKED = {"pyspark", "databricks", "delta", "pandas", "numpy", "IPython",
                "ipywidgets", "matplotlib", "plotly"}
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mn = node.module if isinstance(node, ast.ImportFrom) else (node.names[0].name if node.names else "")
            if (mn or "").split(".")[0] in _BLOCKED:
                continue
        elif not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign)):
            continue
        try:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), mod.__dict__)
        except Exception:
            pass
    return mod


def _bare_orch(klass):
    o = object.__new__(klass)
    o.logger = LOG
    o._step_snapshots = {}
    return o


def _preserve_snapshot():
    return {
        "domains": {f"d{i}": {} for i in range(20)},
        "products": {f"p{i}": {} for i in range(413)},
        "product_attributes": {f"p{i}": [f"a{j}" for j in range(38)] for i in range(413)},
    }  # 413*38 = 15694 attrs before (drifts down after)


def _after_preserve(n_attrs):
    domains_data = [{"domain": f"d{i}"} for i in range(20)]
    products_data = [{"domain": "d0", "product": f"p{i}"} for i in range(413)]
    attributes_data = [{"domain": "d0", "product": "p0", "attribute": f"a{j}",
                        "foreign_key_to": "", "tags": ""} for j in range(n_attrs)]
    return domains_data, products_data, attributes_data


PRESERVE_TEXT = ("Preserve the existing model structure of 20 domains and 413 products "
                 "exactly as listed; do not remove, rename, or merge any listed domain or product.")


# ============================== version =====================================
def test_version_bumped_to_406():
    # v4.0.6 fixes still live in the current (>=4.0.6) notebook; pin to running version.
    assert tuple(int(x) for x in ah.__AGENT_VERSION__.split(".")) >= (4, 1, 3), ah.__AGENT_VERSION__


# ===================== FIX 1: preserve-structure ============================
def test_preserve_structure_fulfilled_despite_attr_drift_POST():
    o = _bare_orch(ah.VibeOrchestrator)
    o._step_snapshots["step_interpret_model_instructions_before"] = _preserve_snapshot()
    dd, pd, ad = _after_preserve(15418)  # fewer attrs than before (dedup) but 20D/413P preserved
    res = o._verify_state_diff(_Req(PRESERVE_TEXT, "VREQ-001"), dd, pd, ad)
    assert res and res["status"] == "fulfilled", res


def test_preserve_structure_partial_on_real_removal_POST():
    # If a product is genuinely removed (413 -> 400), it must NOT be fulfilled.
    o = _bare_orch(ah.VibeOrchestrator)
    o._step_snapshots["step_interpret_model_instructions_before"] = _preserve_snapshot()
    dd, _pd, ad = _after_preserve(15418)
    pd = [{"domain": "d0", "product": f"p{i}"} for i in range(400)]  # 13 removed
    res = o._verify_state_diff(_Req(PRESERVE_TEXT, "VREQ-001"), dd, pd, ad)
    assert res and res["status"] != "fulfilled", res


def test_preserve_structure_FAILPRE_v405_scores_partial():
    pre = _load_backup_module(PRE)
    assert pre.__AGENT_VERSION__ == "4.0.5", pre.__AGENT_VERSION__
    o = _bare_orch(pre.VibeOrchestrator)
    o.logger = LOG
    o._step_snapshots = {"step_interpret_model_instructions_before": _preserve_snapshot()}
    dd, pd, ad = _after_preserve(15418)
    res = o._verify_state_diff(_Req(PRESERVE_TEXT, "VREQ-001"), dd, pd, ad)
    # pre-patch: attribute drift -> coarse "cannot confirm intent" partial (the false-negative)
    assert res and res["status"] == "partial", res
    assert "cannot confirm intent" in (res.get("evidence") or "")


# ================ FIX 2: domain-prefix-resolve (SSOT rename) =================
PLANT_TEXT = ("P19: Connect production.plant to finance.company_code by adding column "
              "finance_company_code_id (BIGINT) with FK to finance.company_code.company_code_id.")


def _plant_after():
    # physical product was renamed production.plant -> production.production_plant by SSOT dedup
    attributes_data = [
        {"domain": "production", "product": "production_plant", "attribute": "production_plant_id",
         "foreign_key_to": "", "tags": "primary_key"},
        {"domain": "production", "product": "production_plant", "attribute": "finance_company_code_id",
         "foreign_key_to": "finance.company_code.company_code_id", "tags": ""},
        {"domain": "finance", "product": "company_code", "attribute": "company_code_id",
         "foreign_key_to": "", "tags": "primary_key"},
    ]
    products_data = [{"domain": "production", "product": "production_plant"},
                     {"domain": "finance", "product": "company_code"}]
    return products_data, attributes_data


def test_domain_prefix_resolve_fulfilled_POST():
    o = _bare_orch(ah.VibeOrchestrator)
    pd, ad = _plant_after()
    res = o._verify_structural_target(_Req(PLANT_TEXT, "VREQ-044", ["production.plant"]), pd, ad)
    assert res and res["status"] == "fulfilled", res


def test_domain_prefix_resolve_ambiguous_stays_honest_POST():
    # Two candidates ending in _plant in the same domain -> ambiguous -> NOT resolved (honest None/partial,
    # never a false fulfilled).
    o = _bare_orch(ah.VibeOrchestrator)
    ad = [
        {"domain": "production", "product": "production_plant", "attribute": "x_id",
         "foreign_key_to": "", "tags": ""},
        {"domain": "production", "product": "power_plant", "attribute": "y_id",
         "foreign_key_to": "", "tags": ""},
    ]
    pd = [{"domain": "production", "product": "production_plant"},
          {"domain": "production", "product": "power_plant"}]
    res = o._verify_structural_target(_Req(PLANT_TEXT, "VREQ-044", ["production.plant"]), pd, ad)
    # ambiguous: 'production_plant' (pref) is unique among <domain>_<name> form, so it resolves to it;
    # but the FK column is absent there -> failed, NOT fulfilled. Either way: never fulfilled here.
    assert (res is None) or (res.get("status") != "fulfilled"), res


def test_domain_prefix_resolve_FAILPRE_v405_returns_none():
    pre = _load_backup_module(PRE)
    o = _bare_orch(pre.VibeOrchestrator)
    o.logger = LOG
    pd, ad = _plant_after()
    res = o._verify_structural_target(_Req(PLANT_TEXT, "VREQ-044", ["production.plant"]), pd, ad)
    # pre-patch: 'production.plant' absent from prod_cols -> early None (falls to coarse partial)
    assert res is None, res


# ===================== FIX 3: division from schema_tags =====================
def test_division_schema_tags_grounds_domains_POST():
    dd = [{"domain": "production"}, {"domain": "finance"}, {"domain": "sales"}, {"domain": "untagged"}]
    dom_cs = {"production": ("c", "production"), "finance": ("c", "finance"),
              "sales": ("c", "sales"), "untagged": ("c", "untagged")}
    rows = [("c", "production", "dbx_division", "operations"),
            ("c", "finance", "dbx_division", "corporate"),
            ("c", "sales", "dbx_division", "business")]  # 'untagged' has no schema tag
    n = ah._v406_ground_division_from_schema_tags(dd, dom_cs, rows, LOG)
    assert n == 3, (n, dd)
    assert dd[0]["division"] == "operations"
    assert dd[1]["division"] == "corporate"
    assert dd[2]["division"] == "business"
    assert "division" not in dd[3]  # honest: never invent a division it did not find


def test_division_schema_tags_FAILPRE_helper_absent_v405():
    pre = _load_backup_module(PRE)
    assert not hasattr(pre, "_v406_ground_division_from_schema_tags"), \
        "v4.0.5 must NOT have the division-schema-tags helper (fail-pre proof)"
