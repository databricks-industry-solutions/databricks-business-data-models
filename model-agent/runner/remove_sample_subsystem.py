#!/usr/bin/env python3
"""v4.8.0 - remove the sample subsystem from the agent.

Sample generation now belongs to the model installer, which builds rows from the
INSTALLED catalog. This deletes the agent's engine, its entry point, the widget, the
`generate sample data` operation and every call site, and asserts every edit so the
script fails loudly rather than half-patching.

    python3 runner/remove_sample_subsystem.py [--check]
"""
import ast
import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

# Definitions reached only by sample code (proved by runner/plan_sample_removal.py).
DELETE_DEFS = [
    "step_generate_and_insert_samples", "_run_generate_samples",
    "_coerce_decimal_to_float", "_v471_coerce_to_schema_type",
    "_p068_faker_provider_map", "_p068_pick_faker_provider",
    "_p068_faker_tier2_sanity_check", "_P068_FAKER_PROVIDERS",
    "_p083_emit_raw_pool_log", "_P083_RAW_LOG_COUNT",
    "_v471_categorical_pool", "_v471_enforce_temporal_order", "_v471_parse_temporal",
    "_v471_semantic_numeric_range", "_v471_semantic_values", "_v471_temporal_edges",
    "_v471_temporal_order_plan", "_v471_token_pos", "_v471_token_role",
    "_v471_type_ceiling",
    "_V471_ALNUM", "_V471_CATEGORICAL_POOLS", "_V471_CITY", "_V471_CODE_TOKENS",
    "_V471_DERIVED_CATEGORICAL", "_V471_FIRST", "_V471_INT_CEILINGS", "_V471_LAST",
    "_V471_MAIL", "_V471_NUMERIC_RANGES", "_V471_PERSON_HINTS", "_V471_STREET",
    "_V471_TEMPORAL_FORMATS", "_V471_TEMPORAL_ORDER_TOKENS", "_V471_TEXT_TOKENS",
    "_V471_WORDS",
]
# _v471_decimal_precision stays: map_data_type uses it for DDL type mapping.

REPLACEMENTS = []


def rep(alias, old, new):
    REPLACEMENTS.append((alias, old, new))


rep("agent-version-global", '__AGENT_VERSION__ = "4.7.5"', '__AGENT_VERSION__ = "4.8.0"')

# ------------------------------------------------------------------ widgets
rep("widget-generate-samples",
    '''dbutils.widgets.dropdown("generate_samples", "0", ["0", "5", "10", "15", "20", "25", "50", "100"], "10. Sample Records (0 = No Samples)")\n''',
    "")
rep("widget-operation-list",
    '"install model", "uninstall model version", "generate sample data"], "03. Operation")',
    '"install model", "uninstall model version"], "03. Operation")')
rep("widget-names-list",
    '    "generate_samples", "context_file", "naming_convention", "primary_key_suffix",',
    '    "context_file", "naming_convention", "primary_key_suffix",')
rep("widget-log-keys",
    '        "generate_samples", "model_folder",',
    '        "model_folder",')

# --------------------------------------------------------------- operations
rep("early-clash-op-list",
    '''    if operation in ("uninstall model version", "generate sample data", "shrink ecm", "enlarge mvm", "vibe modeling of version"):''',
    '''    if operation in ("uninstall model version", "shrink ecm", "enlarge mvm", "vibe modeling of version"):''')
rep("vibe-lineage-skip-op-list",
    """        if operation in ('install model', 'uninstall model version', 'generate sample data'):""",
    """        if operation in ('install model', 'uninstall model version'):""")
rep("op-steps-map",
    '''        "generate sample data": [
            "step_generate_and_insert_samples",
        ],
''', "")
rep("step-scope-map",
    '''            "step_generate_and_insert_samples": {"model", "table"},\n''', "")
rep("progress-banner-steps",
    '''    "step_generate_and_insert_samples",\n''', "")

# ------------------------------------------------------ mutation aliases
rep("format-to-op-samples", """        'samples': 'generate_samples',\n""", "")
rep("legacy-action-alias",
    """    'generate_samples': ('generate_artifact', {'format': 'samples'}),\n""", "")
rep("legacy-action-doc",
    "Legacy action names (add_scd_columns, add_tag_to_product, mark_as_pii, generate_samples, reverse_engineer_from_ddl, etc.)",
    "Legacy action names (add_scd_columns, add_tag_to_product, mark_as_pii, reverse_engineer_from_ddl, etc.)")
rep("queued-generation-docstring",
    """    4. Generation operations (generate_samples)\n""", "")
rep("queued-generation-samples",
    """    if 'generate_samples' in queued_generation_ops:
        _log_banner(logger, "📊 GENERATE SAMPLES - Creating synthetic test data")
        
        sample_count = queued_generation_ops['generate_samples'].get('sample_count', 5)
        scope_filter = queued_generation_ops['generate_samples'].get('scope_filter', '*')
        
        logger.info(f"  Sample generation requested: {sample_count} records per product")
        logger.info(f"  ⚠️ Note: Sample generation requires running step_generate_and_insert_samples separately")
        
        widgets_values['queued_sample_generation'] = {
            'sample_count': sample_count,
            'scope_filter': scope_filter
        }
        widgets_values['generate_samples'] = str(sample_count)
        results['generation_results']['generate_samples'] = {
            'queued': True,
            'sample_count': sample_count
        }
        results['operations_executed'].append('generate_samples')
    
""", "")

# ------------------------------------------------------------------ prompts
rep("prompt-registry-sample-pool",
    '''        {"prompt_name": "SAMPLE_POOL_PROMPT",              "type": "worker",  "size": "tiny",  "temperature": 0.5, "prompt_operations": ["basemodel", "vibe", "enlarge", "shrink"]},\n''',
    "")
rep("prompt-keys-samples-worker",
    '''            "SAMPLES_WORKER": "SAMPLE_POOL_PROMPT",\n''', "")
rep("prompt-stage-sample-pool",
    '''    "SAMPLE_POOL_PROMPT": "SAMPLE_GENERATION",\n''', "")

# ----------------------------------------------------- operational settings
rep("technical-context-sample-records",
    '''    "product_sample_records": 10,\n''', "")
rep("operational-keys-sample-records",
    '''    "product_sample_records", "max_concurrent_batches", "batch_size",''',
    '''    "max_concurrent_batches", "batch_size",''')
rep("prompt-variables-sample-count",
    '''    _gs_widget_val = str(widgets_values.get("generate_samples", "0")).strip()
    if _gs_widget_val not in ("0", "", "no"):
        try:
            _gs_count = int(_gs_widget_val)
            if _gs_count > 0:
                config.setdefault("PROMPT_VARIABLES", {})["product_sample_records"] = _gs_count
        except ValueError:
            pass
''', "")

# ------------------------------------------------------- widget resolution
rep("safe-widget-generate-samples",
    '''        w_generate_samples = _safe_widget("generate_samples")\n''', "")
rep("merge-fields-generate-samples",
    '''                ("generate_samples", w_generate_samples, uc.get("generate_samples", "")),\n''', "")
rep("effective-generate-samples-file",
    '''            _eff_generate_samples = _prefer_widget_value(w_generate_samples, uc.get("generate_samples", ""))\n''', "")
rep("effective-generate-samples-widget",
    '''            _eff_generate_samples = w_generate_samples\n''', "")
rep("widget-values-generate-samples",
    '''            "generate_samples": _eff_generate_samples,\n''', "")
rep("effective-config-print",
    '''        print(f"   generate_samples = '{_eff_generate_samples}'")\n''', "")
rep("validation-op-list",
    '''        if operation not in ["install model", "uninstall model version", "generate sample data"]:''',
    '''        if operation not in ["install model", "uninstall model version"]:''')
rep("validation-sample-catalog",
    '''        if operation == "generate sample data":
            if not deployment_catalog:
                errors.append("'09. Installation Catalog' is required for 'generate sample data' — the model must already be installed")
''', "")
rep("business-context-op-list",
    '''        if operation in ["install model", "generate sample data"]:
            widget_values["business_context_data"] = {}''',
    '''        if operation == "install model":
            widget_values["business_context_data"] = {}''')
rep("model-conventions-op-list",
    '''        if _bcd and operation not in ["install model", "generate sample data"]:''',
    '''        if _bcd and operation != "install model":''')
rep("widget-values-assign-samples",
    '''        widget_values["generate_samples"] = _eff_generate_samples\n''', "")
rep("raise-sample-catalog",
    '''        if operation == "generate sample data":
            if not deployment_catalog:
                raise ValueError("❌ '09. Installation Catalog' is required for 'generate sample data' — the model must already be installed.")
''', "")

# ------------------------------------------------------------ install model
rep("install-samples-flag",
    '''        generate_samples = widgets_values.get("generate_samples", "0")
        _generate_samples_enabled = str(generate_samples).strip() not in ("0", "", "no")
''', "")
rep("install-banner-samples",
    '''[{_ts()}] ║  Generate Samples:   {generate_samples:<54} ║\n''', "")

# ------------------------------------------------------------- dispatch
rep("dispatch-generate-sample-data",
    '''    if operation == "generate sample data":
        try:
            _run_generate_samples(widgets_values)
        except Exception as _samples_err:
            _vw_samples = widgets_values.get("vibe_writer")
            if _vw_samples:
                try:
                    _vw_samples.finalize_pipeline_error(error_message=f"Generate samples failed: {str(_samples_err)[:500]}", error_details=str(_samples_err)[:2000])
                except Exception:
                    pass
            raise
        _safe_notebook_exit(widgets_values.get("_notebook_exit_result"), widgets_values)
        return
    
''', "")

# ------------------------------------------------------------- track 3
rep("track3-sample-step",
    '''                generate_samples_flag = track3_widgets.get("generate_samples", "0")
                _gs_enabled = str(generate_samples_flag).strip() not in ("0", "", "no")
                if _gs_enabled:
                    current_step_func = step_generate_and_insert_samples
                    step_start = _log_step_start(current_step_func)
                    logger.info(f"--- Track 3: Starting {current_step_func.__name__} ---")
                    if _vw_t3:
                        _vw_samp_step = _vw_t3.emit_step(stage_name="Sample Data Generation", step_name="Generate & Insert Samples", progress_increment=2.0, message="Generating and inserting sample data", status="stage_started")
                    if _vibe_orchestrator:
                        _vibe_orchestrator.wrap_step(current_step_func, track3_widgets)
                    else:
                        current_step_func(track3_widgets)
                    if _vw_t3:
                        _vw_t3.emit_step(stage_name="Sample Data Generation", step_name="Generate & Insert Samples", progress_increment=2.0, message="Sample data generated and inserted", status="stage_succeeded", step_id=_vw_samp_step)
                    logger.info(f"--- Track 3: Completed {current_step_func.__name__} ---")
                    _log_step_end(current_step_func, step_start)
                else:
                    logger.info("--- Track 3: Skipping sample generation (generate_samples = 0) ---")
                    if _vw_t3:
                        _vw_t3.emit_step(stage_name="Sample Data Generation", step_name="Samples Skipped", progress_increment=2.0, message="Sample generation skipped (generate_samples = 0)", status="stage_in_progress")
                
''', "")
rep("track3-header",
    '''        # Track 3: Tags + Samples (Step 11: Tagging, Step 12: Two-Phase Samples - LAST)
        generate_samples_flag = widgets_values.get("generate_samples", "0")
        _pipeline_gs_enabled = str(generate_samples_flag).strip() not in ("0", "", "no")
        
        logger.info("\\n" + "=" * 80)
        logger.info("🔢 TRACK 3: Tagging & Sample Generation (Steps 11-12)")
        logger.info("    Step 11: Apply Metadata Tags (BEFORE samples)")
        if _pipeline_gs_enabled:
            logger.info(f"    Step 12: Two-Phase Sample Generation - LAST STEP ({generate_samples_flag} records per product)")
        else:
            logger.info("    Step 12: SKIPPED (generate_samples = 0)")
        logger.info("=" * 80)''',
    '''        # Track 3: Tagging (Step 11) + Metric Views (Step 11.5)
        logger.info("\\n" + "=" * 80)
        logger.info("🔢 TRACK 3: Tagging & Metric Views (Step 11)")
        logger.info("    Step 11: Apply Metadata Tags")
        logger.info("=" * 80)''')
rep("track3-stats",
    '''        if _pipeline_gs_enabled:
            pipeline_stats["steps_completed"].extend([
                "step_apply_tags (Step 11)",
                "step_apply_metric_views (Step 11.5)",
                "step_generate_and_insert_samples (Step 12 - Two-Phase - LAST)"
            ])
        else:
            pipeline_stats["steps_completed"].extend([
                "step_apply_tags (Step 11)",
                "step_apply_metric_views (Step 11.5)",
                "step_generate_and_insert_samples (Step 12 - SKIPPED)"
            ])''',
    '''        pipeline_stats["steps_completed"].extend([
            "step_apply_tags (Step 11)",
            "step_apply_metric_views (Step 11.5)",
        ])''')

# --------------------------------------------------------- sanity harness
rep("faker-sanity-call", '''    _faker_ok = _p068_faker_tier2_sanity_check()\n''', "")


def cell_source(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def delete_definitions(cells, report):
    """Remove whole top-level definitions (plus the comments that introduce them)."""
    wanted = set(DELETE_DEFS)
    found = set()
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        source = cell_source(cell)
        if not any(name in source for name in wanted):
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        spans = []
        # `_run_generate_samples` is nested inside the dispatch function, so the walk
        # has to look deeper than tree.body for it.
        for node in ast.walk(tree):
            names = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = [node.name]
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            hit = [n for n in names if n in wanted]
            if not hit:
                continue
            start = min([d.lineno for d in getattr(node, "decorator_list", [])] or [node.lineno])
            spans.append((start, getattr(node, "end_lineno", node.lineno), hit[0]))
        if not spans:
            continue
        lines = source.split("\n")
        # A nested definition can be reported twice by the walk; keep outermost spans.
        spans.sort()
        merged = []
        for span in spans:
            if merged and span[0] <= merged[-1][1]:
                continue
            merged.append(span)
        for start, end, name in sorted(merged, reverse=True):
            head = start - 1
            while head > 0 and (lines[head - 1].lstrip().startswith("#")
                                or not lines[head - 1].strip()):
                head -= 1
            del lines[head:end]
            found.add(name)
            report.append("  - %s (%d lines)" % (name, end - head))
        cell["source"] = "\n".join(lines)
    missing = wanted - found
    if missing:
        raise SystemExit("DEFINITIONS NOT FOUND AT TOP LEVEL: %s" % sorted(missing))


def main():
    check_only = "--check" in sys.argv
    original = NB.read_text()
    notebook = json.loads(original)
    cells = notebook["cells"]
    report = ["DEFINITIONS REMOVED:"]

    delete_definitions(cells, report)

    report.append("CALL SITES EDITED:")
    for alias, old, new in REPLACEMENTS:
        hits = sum(cell_source(c).count(old) for c in cells if c.get("cell_type") == "code")
        if hits != 1:
            raise SystemExit("ANCHOR %s matched %d times (expected 1):\n%s"
                             % (alias, hits, old[:300]))
        for cell in cells:
            if cell.get("cell_type") != "code":
                continue
            source = cell_source(cell)
            if old in source:
                cell["source"] = source.replace(old, new, 1)
                break
        report.append("  ~ %s" % alias)

    text = json.dumps(notebook, indent=1, ensure_ascii=False) + "\n"
    print("\n".join(report))
    if check_only:
        print("WOULD CHANGE" if text != original else "NO CHANGE")
        return 0
    NB.write_text(text)
    print("notebook written (%d -> %d bytes)" % (len(original), len(text)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
