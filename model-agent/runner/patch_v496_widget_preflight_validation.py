# -*- coding: utf-8 -*-
"""v4.9.6 - validate required widget values in the PARENT, BEFORE launching the child job.

ROOT CAUSE (user report): on a first interactive run with an empty required widget
(e.g. business_name), the Job Launch Gate in main() submits the CHILD job FIRST and only
then validates the widgets inside the child (get_widget_values raises ValueError). So the
parent launches a doomed child that fails downstream - the "failed after launching the job"
experience the users hit.

FIX (root cause, DRY):
  1. Extract the existing required-field checks (previously inline in get_widget_values) into
     a single module-level SSOT function `_validate_required_widget_values(...)`.
  2. get_widget_values() now CALLS that function (identical messages/behaviour, no drift).
  3. The parent Job Launch Gate calls the SAME function as a PRE-FLIGHT, before submitting the
     child job: on failure it surfaces the actionable message and stops WITHOUT launching a job.

The deeper business-context raise (_eff description backstop) is left untouched as defence in
depth. Version bumped 4.9.5 -> 4.9.6 (single-digit semver).
"""
import json
import pathlib
import re

NB = pathlib.Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def sub_once(src, old, new, label):
    assert src.count(old) == 1, "%s: expected 1 occurrence, got %d" % (label, src.count(old))
    return src.replace(old, new)


# The exact required-field checks as they existed inline in get_widget_values (verbatim,
# including the em-dash message text) - this is the OLD block we lift out.
OLD_ERRORS_BLOCK = (
    '        errors = []\n'
    '        if operation not in ["install model", "uninstall model version"]:\n'
    '            if not _eff_business_name and not _context_file_loaded:\n'
    '                errors.append("Business name is required (widget \'01. Business\' or provide a Model JSON file \u2014 any *.json filename \u2014 via widget \'11. Model JSON File Path\')")\n'
    '            if not _eff_description and not _context_file_loaded:\n'
    '                errors.append("Business description is required (widget \'02. Description\' or provide a Model JSON file \u2014 any *.json filename \u2014 via widget \'11. Model JSON File Path\')")\n'
    '        if operation == "install model":\n'
    '            if not model_folder:\n'
    '                errors.append(f"For \'{operation}\', provide a Model JSON file (any *.json filename, widget \'11. Model JSON File Path\') so the model folder can be derived")\n'
    '            if not deployment_catalog:\n'
    '                errors.append(f"\'09. Installation Catalog\' is required for \'{operation}\' operation")\n'
    '        if operation == "uninstall model version":\n'
    '            if not str(_eff_business_name or "").strip():\n'
    '                errors.append("For \'uninstall model version\', widget \'01. Business\' is required")\n'
    '            if not str(_eff_version or "").strip():\n'
    '                errors.append("For \'uninstall model version\', widget \'04. Version\' is required")\n'
    '            if not deployment_catalog:\n'
    '                errors.append("\'09. Installation Catalog\' is required for \'uninstall model version\' operation")\n'
    '        if operation in ["shrink ecm", "enlarge mvm"]:\n'
    '            if not deployment_catalog:\n'
    '                errors.append(f"\'09. Installation Catalog\' is required for \'{operation}\' operation")\n'
)

# get_widget_values now delegates to the SSOT validator (same variables, same messages).
NEW_ERRORS_CALL = (
    '        errors = _validate_required_widget_values(\n'
    '            operation=operation,\n'
    '            business_name=_eff_business_name,\n'
    '            business_description=_eff_description,\n'
    '            model_version=_eff_version,\n'
    '            deployment_catalog=deployment_catalog,\n'
    '            context_file_loaded=_context_file_loaded,\n'
    '            model_folder=model_folder,\n'
    '        )\n'
)

# Module-level SSOT validator, inserted immediately before def main(). Message strings are
# copied VERBATIM from the old inline block so behaviour/messages are byte-identical.
VALIDATOR_DEF = (
    'def _validate_required_widget_values(operation, business_name, business_description,\n'
    '                                     model_version, deployment_catalog,\n'
    '                                     context_file_loaded, model_folder):\n'
    '    """SSOT for required-widget checks (v4.9.6). Returns a list of human-readable error\n'
    '    strings for any missing required value for the given operation. Called by BOTH the\n'
    '    parent Job Launch Gate (pre-flight, before submitting the child job) AND\n'
    '    get_widget_values() inside the child, so an empty required widget is caught BEFORE a\n'
    '    doomed job is launched rather than after. alias=validate-required-widget-values."""\n'
    '    errors = []\n'
    '    op = (operation or "").strip()\n'
    '    if op not in ["install model", "uninstall model version"]:\n'
    '        if not business_name and not context_file_loaded:\n'
    '            errors.append("Business name is required (widget \'01. Business\' or provide a Model JSON file \u2014 any *.json filename \u2014 via widget \'11. Model JSON File Path\')")\n'
    '        if not business_description and not context_file_loaded:\n'
    '            errors.append("Business description is required (widget \'02. Description\' or provide a Model JSON file \u2014 any *.json filename \u2014 via widget \'11. Model JSON File Path\')")\n'
    '    if op == "install model":\n'
    '        if not model_folder:\n'
    '            errors.append(f"For \'{op}\', provide a Model JSON file (any *.json filename, widget \'11. Model JSON File Path\') so the model folder can be derived")\n'
    '        if not deployment_catalog:\n'
    '            errors.append(f"\'09. Installation Catalog\' is required for \'{op}\' operation")\n'
    '    if op == "uninstall model version":\n'
    '        if not str(business_name or "").strip():\n'
    '            errors.append("For \'uninstall model version\', widget \'01. Business\' is required")\n'
    '        if not str(model_version or "").strip():\n'
    '            errors.append("For \'uninstall model version\', widget \'04. Version\' is required")\n'
    '        if not deployment_catalog:\n'
    '            errors.append("\'09. Installation Catalog\' is required for \'uninstall model version\' operation")\n'
    '    if op in ["shrink ecm", "enlarge mvm"]:\n'
    '        if not deployment_catalog:\n'
    '            errors.append(f"\'09. Installation Catalog\' is required for \'{op}\' operation")\n'
    '    return errors\n'
    '\n'
    '\n'
    'def main():'
)

# Parent pre-flight: run the SSOT validator BEFORE the launch, stop cleanly if invalid.
OLD_LAUNCH_ANCHOR = (
    '    if not _raw_session_id_from_widget:\n'
    '        try:\n'
    '            import uuid as _jl_uuid'
)
NEW_LAUNCH_PREFLIGHT = (
    '    if not _raw_session_id_from_widget:\n'
    '        # \u2500\u2500 v4.9.6 Widget Pre-Flight Validation (alias=widget-preflight-validate) \u2500\u2500\n'
    '        # The Job Launch Gate below submits the CHILD job. Validate the required widgets HERE,\n'
    '        # in the PARENT, using the SAME SSOT validator get_widget_values() uses in the child, so\n'
    '        # an empty required widget stops the run BEFORE a doomed child job is launched instead of\n'
    '        # after (the user-reported "failed after launching the job").\n'
    '        try:\n'
    '            def _pf_w(_n):\n'
    '                try:\n'
    '                    return (dbutils.widgets.get(_n) or "").strip()\n'
    '                except Exception:\n'
    '                    return ""\n'
    '            _pf_operation = _pf_w("operation")\n'
    '            _pf_context_file = _pf_w("context_file")\n'
    '            _pf_errors = _validate_required_widget_values(\n'
    '                operation=_pf_operation,\n'
    '                business_name=_pf_w("business_name"),\n'
    '                business_description=_pf_w("business_description"),\n'
    '                model_version=_pf_w("model_version"),\n'
    '                deployment_catalog=_pf_w("deployment_catalog"),\n'
    '                context_file_loaded=bool(_pf_context_file),\n'
    '                model_folder=_pf_context_file,\n'
    '            )\n'
    '        except Exception as _pf_exc:\n'
    '            _pf_errors = []\n'
    '            print(f"[widget-preflight-validate] non-fatal pre-flight error (deferring to child validation): {_pf_exc}")\n'
    '        if _pf_errors:\n'
    '            _pf_msg = "\u274c MISSING REQUIRED VALUES:\\n\\n" + "\\n".join("  \u2022 " + _e for _e in _pf_errors)\n'
    '            print("\\n" + "=" * 80)\n'
    '            print("\u26d4 WIDGET VALIDATION FAILED \u2014 job NOT launched. Fix the widgets and re-run.")\n'
    '            print("=" * 80)\n'
    '            print(_pf_msg)\n'
    '            print("=" * 80 + "\\n")\n'
    '            try:\n'
    '                _pf_biz = _pf_w("business_name") or "Unknown"\n'
    '                _pf_op = (_pf_operation or "Configuration Error").title()\n'
    '                _pf_items = "".join("<li>" + _e + "</li>" for _e in _pf_errors)\n'
    '                displayHTML("<div style=\\"font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;padding:16px 24px;margin:8px 0 16px 0;background:linear-gradient(135deg,#7A2828 0%,#B33A3A 100%);border-radius:12px;color:#fff;\\"><div style=\\"font-size:22px;font-weight:700;\\">\u26d4 " + _pf_biz + " \u2014 " + _pf_op + " \u2014 Configuration Invalid</div><div style=\\"font-size:13px;opacity:0.9;margin-top:6px;\\">Job NOT launched: required widget values are missing. Fix the widgets above and re-run.</div><ul style=\\"font-size:14px;margin-top:10px;\\">" + _pf_items + "</ul></div>")\n'
    '            except Exception:\n'
    '                pass\n'
    '            return\n'
    '        try:\n'
    '            import uuid as _jl_uuid'
)


def main():
    nb = json.loads(NB.read_text())

    def find(pred):
        hits = [i for i, c in enumerate(nb["cells"])
                if c.get("cell_type") == "code" and pred("".join(c["source"]))]
        assert len(hits) == 1, "expected exactly 1 cell, got %r" % (hits,)
        return hits[0]

    main_i = find(lambda s: "def main():" in s and "def get_widget_values():" in s)
    ver_i = find(lambda s: "__AGENT_VERSION__ = " in s and "agent-version-global" in s)

    s = "".join(nb["cells"][main_i]["source"])
    assert "_validate_required_widget_values" not in s, "validator already present - patch already applied?"

    s = sub_once(s, OLD_ERRORS_BLOCK, NEW_ERRORS_CALL, "child errors->validator call")
    s = sub_once(s, "def main():", VALIDATOR_DEF, "insert validator before main")
    s = sub_once(s, OLD_LAUNCH_ANCHOR, NEW_LAUNCH_PREFLIGHT, "parent pre-flight")
    nb["cells"][main_i]["source"] = s

    ver = "".join(nb["cells"][ver_i]["source"])
    new_ver, n = re.subn(r'__AGENT_VERSION__ = "\d+\.\d+\.\d+"', '__AGENT_VERSION__ = "4.9.6"', ver, count=1)
    assert n == 1, "version constant not rewritten"
    nb["cells"][ver_i]["source"] = new_ver

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print("patched main cell=%d version cell=%d -> 4.9.6" % (main_i, ver_i))


if __name__ == "__main__":
    main()
