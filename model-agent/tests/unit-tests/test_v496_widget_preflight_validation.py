# -*- coding: utf-8 -*-
"""v4.9.6 behavioral tests - required-widget validation runs in the PARENT before the job launch.

ROOT CAUSE (user report): a first interactive run with an empty required widget launched the
CHILD job first and only validated inside the child, so the parent launched a doomed child that
failed downstream ("failed after launching the job").

FIX: single SSOT `_validate_required_widget_values(...)` is called BOTH by get_widget_values
(child) AND by the parent Job Launch Gate as a pre-flight, before submitting the child job.

These tests prove:
  * the validator returns the correct errors per operation (pass-post behaviour),
  * get_widget_values delegates to the SSOT validator (DRY - no drift),
  * the parent pre-flight calls the SSOT validator and returns BEFORE the JobLauncher launch
    (fail-pre replication: pre-patch there was NO validation before the launch call).
"""
import json
import os

NB = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb")


def _cells():
    return json.load(open(NB))["cells"]


def _src_containing(needle):
    for c in _cells():
        if c["cell_type"] != "code":
            continue
        s = "".join(c["source"])
        if needle in s:
            return s
    raise AssertionError("cell containing %r not found" % needle)


def _extract_toplevel_func(src, name):
    lines = src.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("def %s(" % name):
            start = i
            break
    assert start is not None, "def %s( not found" % name
    out = [lines[start]]
    for ln in lines[start + 1:]:
        if ln.strip() == "" or ln[:1] in (" ", "\t"):
            out.append(ln)
        else:
            break
    return "\n".join(out)


def _load(name):
    src = _src_containing("def %s(" % name)
    g = {}
    exec(_extract_toplevel_func(src, name), g)
    return g[name]


def _v():
    return _load("_validate_required_widget_values")


# ── pass-post: the validator catches every missing required value ─────────────

def test_empty_new_base_flags_name_and_description():
    errs = _v()(operation="new base model", business_name="", business_description="",
                model_version="", deployment_catalog="", context_file_loaded=False, model_folder="")
    assert len(errs) == 2
    assert any("Business name is required" in e for e in errs)
    assert any("Business description is required" in e for e in errs)


def test_airline_name_plus_description_is_valid():
    # the exact shape of the airline MVM test: name + a short description, defaults elsewhere
    errs = _v()(operation="new base model", business_name="airline",
                business_description="Airline industry", model_version="",
                deployment_catalog="", context_file_loaded=False, model_folder="")
    assert errs == []


def test_context_file_relaxes_name_and_description():
    errs = _v()(operation="new base model", business_name="", business_description="",
                model_version="", deployment_catalog="", context_file_loaded=True,
                model_folder="/Volumes/x/model.json")
    assert errs == []


def test_install_requires_model_folder_and_catalog():
    errs = _v()(operation="install model", business_name="", business_description="",
                model_version="1", deployment_catalog="", context_file_loaded=False, model_folder="")
    assert len(errs) == 2
    assert any("Model JSON file" in e for e in errs)
    assert any("Installation Catalog" in e for e in errs)


def test_install_with_folder_and_catalog_is_valid():
    errs = _v()(operation="install model", business_name="", business_description="",
                model_version="1", deployment_catalog="cat", context_file_loaded=True,
                model_folder="/Volumes/x/model.json")
    assert errs == []


def test_uninstall_requires_business_version_catalog():
    errs = _v()(operation="uninstall model version", business_name="", business_description="",
                model_version="", deployment_catalog="", context_file_loaded=False, model_folder="")
    assert len(errs) == 3
    assert any("'01. Business' is required" in e for e in errs)
    assert any("'04. Version' is required" in e for e in errs)
    assert any("Installation Catalog" in e for e in errs)


def test_shrink_and_enlarge_require_catalog():
    for op in ("shrink ecm", "enlarge mvm"):
        errs = _v()(operation=op, business_name="airline", business_description="Airline",
                    model_version="1", deployment_catalog="", context_file_loaded=False, model_folder="")
        assert any("Installation Catalog" in e for e in errs), op


# ── DRY: get_widget_values delegates to the SSOT validator ────────────────────

def test_get_widget_values_delegates_to_validator():
    src = _src_containing("def get_widget_values():")
    assert "errors = _validate_required_widget_values(" in src
    # the old inline duplicate must be gone (no drift possible)
    assert 'if not _eff_business_name and not _context_file_loaded:' not in src


# ── fail-pre replication: the parent validates and returns BEFORE launching ───

def test_parent_preflight_runs_before_job_launch():
    src = _src_containing("widget-preflight-validate")
    i_preflight = src.index("_pf_errors = _validate_required_widget_values(")
    i_return = src.index("            return", i_preflight)
    i_launch = src.index("_launcher.launch(")
    # pre-flight validation + its clean-exit return both precede the actual job launch
    assert i_preflight < i_return < i_launch
    # and the pre-flight sits inside the interactive (no session id) branch
    i_branch = src.index("if not _raw_session_id_from_widget:")
    assert i_branch < i_preflight
