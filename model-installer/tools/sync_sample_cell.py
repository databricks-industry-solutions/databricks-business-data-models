#!/usr/bin/env python3
"""Sync sample_engine.py into data-model-installer.ipynb and wire it into the install.

The installer notebook has to stay self-contained (it is launched as a job from the
workspace, with no repo checkout), so the engine cannot be imported at runtime. It is
therefore edited as a normal Python file here and injected verbatim as one cell; a test
asserts the two never drift.

    python3 model-installer/tools/sync_sample_cell.py [--check]
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "sample_engine.py"
NOTEBOOK = HERE.parent / "data-model-installer.ipynb"
MARKER = "# === Sample data generation (self-contained; reads the installed catalog) ==="

# Anchored on the widget NAME, not its label: the labels carry a display ordinal that
# shifts whenever a widget is added, and pinning on that made this script break for a
# reason that had nothing to do with sample generation.
WIDGETS_ANCHOR_RE = r'dbutils\.widgets\.text\("local_install",[^\n]*\)'
WIDGETS_SENTINEL = 'dbutils.widgets.dropdown("generate_samples"'
WIDGETS_ADD = '''
dbutils.widgets.dropdown("generate_samples", "No", ["No", "Yes"], "9. generate samples")
dbutils.widgets.dropdown("sample_rows", "10", ["5", "10", "20", "50", "100"], "10. sample rows")'''

DEFAULTS_ANCHOR = '    "github_token": "",\n}'
DEFAULTS_ADD = '''    "github_token": "",
    # Sample generation advanced settings. The two visible widgets decide whether to
    # generate and how many rows; these tune HOW, and are forwarded to the job.
    "sample_seed": "20260801",
    "sample_threads": "8",
    "sample_llm": "true",
    "sample_llm_endpoints": "databricks-gpt-oss-120b,databricks-meta-llama-3-3-70b-instruct",
}'''

CONFIG_ANCHOR = '        "resolved_version": "unknown",\n    }'
CONFIG_ADD = '''        "resolved_version": "unknown",
        "sample": resolve_sample_config(_wget),
    }'''

FORWARD_ANCHOR = '        "github_token": cfg["github_token"],\n    }'
FORWARD_ADD = '''        "github_token": cfg["github_token"],
        "generate_samples": "Yes" if cfg["sample"]["enabled"] else "No",
        "sample_rows": str(cfg["sample"]["rows"]),
        "sample_seed": str(cfg["sample"]["seed"]),
        "sample_threads": str(cfg["sample"]["threads"]),
        "sample_llm": "true" if cfg["sample"]["llm"] else "false",
        "sample_llm_endpoints": ",".join(cfg["sample"]["llm_endpoints"]),
    }'''

LOG_ANCHOR = '    log("Metric views  : %s" % cfg["include_metrics"])'
LOG_ADD = '''    log("Metric views  : %s" % cfg["include_metrics"])
    log("Samples       : %s%s" % (
        "yes" if cfg["sample"]["enabled"] else "no",
        " (%d rows/table)" % cfg["sample"]["rows"] if cfg["sample"]["enabled"] else ""))'''

# The install/sample block is co-owned: other patches (e.g. the install manifest) edit
# the same region, so "already wired" is detected by this sentinel rather than by an
# exact match on the whole block, which any neighbouring edit would defeat.
INSTALL_SENTINEL = "summary = generate_sample_data("

INSTALL_ANCHOR = '''        plan = build_plan(cfg)
        final, elapsed, timings = install(cfg, plan)
'''
INSTALL_ADD = '''        plan = build_plan(cfg)
        final, elapsed, timings = install(cfg, plan)

        # Samples run only on a structurally clean install: populating tables whose
        # keys or foreign keys failed to apply would write rows that cannot be joined.
        sample_note = ""
        if cfg["sample"]["enabled"]:
            if [f for f in final if f[0] != "metric"]:
                log("Samples skipped: the install has structural failures.")
                sample_note = " | samples: skipped (structural failures)"
            else:
                t_samples = time.time()
                summary = generate_sample_data(
                    spark, cfg["sample"], cfg.get("target_catalogs") or [cfg["catalog"]], log)
                timings["samples"] = time.time() - t_samples
                sample_note = (" | samples: %d rows in %d tables"
                               % (summary["written"], summary["tables"]))
                if summary.get("failed"):
                    sample_note += " (%d failed)" % len(summary["failed"])
'''

RESULT_EDITS = (
    ('''                      % (cfg["industry"], cfg["model_size"], cfg["catalog"], total,
                         len(final), elapsed / 60.0, timing_str, _SINK["path"]))''',
     '''                      % (cfg["industry"], cfg["model_size"], cfg["catalog"], total,
                         len(final), elapsed / 60.0, timing_str, _SINK["path"])) + sample_note'''),
    ('''                      % (cfg["industry"], cfg["model_size"], cfg["catalog"],
                         total, elapsed / 60.0, timing_str, _SINK["path"]))''',
     '''                      % (cfg["industry"], cfg["model_size"], cfg["catalog"],
                         total, elapsed / 60.0, timing_str, _SINK["path"])) + sample_note'''),
)


def cell_source(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def apply_edit(source, anchor, replacement, label, report):
    if replacement in source:
        report.append("  = %s (already applied)" % label)
        return source
    if anchor not in source:
        raise SystemExit("ANCHOR NOT FOUND for %s:\n%s" % (label, anchor[:200]))
    report.append("  + %s" % label)
    return source.replace(anchor, replacement, 1)


def apply_edit_after(source, anchor_re, addition, label, report):
    """Insert after the line matching `anchor_re`, so a widget's display ordinal can
    change without breaking the sync."""
    if addition in source:
        report.append("  = %s (already applied)" % label)
        return source
    m = re.search(anchor_re, source)
    if not m:
        raise SystemExit("ANCHOR NOT FOUND for %s:\n%s" % (label, anchor_re))
    report.append("  + %s" % label)
    return source[:m.end()] + addition + source[m.end():]


def main():
    check_only = "--check" in sys.argv
    engine = ENGINE.read_text()
    notebook = json.loads(NOTEBOOK.read_text())
    cells = notebook["cells"]
    report = []

    existing = [i for i, c in enumerate(cells)
                if c.get("cell_type") == "code" and cell_source(c).startswith(MARKER)]
    if existing:
        index = existing[0]
        drifted = cell_source(cells[index]) != engine
        report.append("  %s sample cell at index %d"
                      % ("~ refreshed" if drifted else "= in sync", index))
        cells[index]["source"] = engine
    else:
        # Before the `main` markdown + main cell, so the definitions exist when main runs.
        index = next((i for i, c in enumerate(cells)
                      if c.get("cell_type") == "code" and "def main()" in cell_source(c)),
                     len(cells) - 1)
        # the markdown that introduces main belongs above the engine, not below it
        if index and cells[index - 1].get("cell_type") == "markdown":
            index -= 1
        cells.insert(index, {"cell_type": "code", "execution_count": None,
                             "metadata": {}, "outputs": [], "source": engine})
        report.append("  + sample cell inserted at index %d" % index)

    widget_cell = next(i for i, c in enumerate(cells)
                       if c.get("cell_type") == "code" and "INSTALLER_DEFAULTS" in cell_source(c))
    src = cell_source(cells[widget_cell])
    if WIDGETS_SENTINEL in src:
        report.append("  = sample widgets (already applied)")
    else:
        src = apply_edit_after(src, WIDGETS_ANCHOR_RE, WIDGETS_ADD, "sample widgets", report)
    src = apply_edit(src, DEFAULTS_ANCHOR, DEFAULTS_ADD, "sample defaults", report)
    cells[widget_cell]["source"] = src

    config_cell = next(i for i, c in enumerate(cells)
                       if c.get("cell_type") == "code" and "def resolve_config" in cell_source(c))
    src = cell_source(cells[config_cell])
    src = apply_edit(src, CONFIG_ANCHOR, CONFIG_ADD, "cfg['sample']", report)
    cells[config_cell]["source"] = src

    main_cell = next(i for i, c in enumerate(cells)
                     if c.get("cell_type") == "code" and "def main()" in cell_source(c))
    src = cell_source(cells[main_cell])
    src = apply_edit(src, FORWARD_ANCHOR, FORWARD_ADD, "job param forwarding", report)
    src = apply_edit(src, LOG_ANCHOR, LOG_ADD, "resolved-input log line", report)
    if INSTALL_SENTINEL in src:
        report.append("  = generate_sample_data call site (already applied)")
    else:
        src = apply_edit(src, INSTALL_ANCHOR, INSTALL_ADD, "generate_sample_data call site", report)
    for anchor, replacement in RESULT_EDITS:
        src = apply_edit(src, anchor, replacement, "result string", report)
    cells[main_cell]["source"] = src

    text = json.dumps(notebook, indent=1, ensure_ascii=True) + "\n"
    changed = text != NOTEBOOK.read_text()
    print("\n".join(report))
    if check_only:
        print("DRIFT" if changed else "IN SYNC")
        return 1 if changed else 0
    if changed:
        NOTEBOOK.write_text(text)
        print("notebook updated")
    else:
        print("notebook already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
