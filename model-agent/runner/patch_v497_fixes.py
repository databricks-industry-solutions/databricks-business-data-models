import json, sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

nb = json.load(open(NB))
cells = nb["cells"]


def cell_text(ci):
    return "".join(cells[ci].get("source", []))


def set_cell_text(ci, text):
    cells[ci]["source"] = text  # HEAD stores source as a single string; keep it that way for a minimal diff


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"[patch_v497] ANCHOR '{label}' found {n} times (expected 1) — aborting")
    return text.replace(old, new)


# ---- Fix 0: version bump 4.9.6 -> 4.9.7 (cell 1) ----
t1 = cell_text(1)
t1 = replace_once(t1, '__AGENT_VERSION__ = "4.9.6"', '__AGENT_VERSION__ = "4.9.7"', "version")
set_cell_text(1, t1)

# ---- Fix 3: domain-enrichment str-vs-dict guard (cell 156) ----
t156 = cell_text(156)
t156 = replace_once(
    t156,
    'data = _v466_coerce_llm_obj(json.loads(response_text), site="c156-enrich")',
    'data = _v466_coerce_llm_obj(json.loads(response_text) if isinstance(response_text, str) else response_text, site="c156-enrich")',
    "c156-enrich",
)
set_cell_text(156, t156)

# ---- Fix 1: enlarge/shrink resize must run AFTER VibeOrchestrator.parse() (cell 204) ----
t204 = cell_text(204)

remove_block = (
    '        operation = widgets_values.get("operation", "new base model")\n'
    '        if operation == "shrink ecm":\n'
    '            _run_resize_model(widgets_values, "shrink")\n'
    '        elif operation == "enlarge mvm":\n'
    '            _run_resize_model(widgets_values, "enlarge")\n'
    '        \n'
)
remove_with = (
    '        operation = widgets_values.get("operation", "new base model")\n'
    '        \n'
)
t204 = replace_once(t204, remove_block, remove_with, "resize-early-dispatch")

insert_anchor = (
    '        else:\n'
    '            logger.info("[VibeOrchestrator] Skipped — no vibes or orchestrator disabled")\n'
    '\n'
    '        # --- Define Track Helper Functions ---\n'
)
insert_with = (
    '        else:\n'
    '            logger.info("[VibeOrchestrator] Skipped — no vibes or orchestrator disabled")\n'
    '\n'
    '        # v497-resize-after-vibe-parse alias=resize-honors-sizing-cap\n'
    '        if operation == "shrink ecm":\n'
    '            _run_resize_model(widgets_values, "shrink")\n'
    '        elif operation == "enlarge mvm":\n'
    '            _run_resize_model(widgets_values, "enlarge")\n'
    '\n'
    '        # --- Define Track Helper Functions ---\n'
)
t204 = replace_once(t204, insert_anchor, insert_with, "resize-insert-anchor")
set_cell_text(204, t204)

with open(NB, "w") as _f:
    json.dump(nb, _f, indent=1)
    _f.write("\n")

# ---- verification ----
nb2 = json.load(open(NB))
full = "\n".join("".join(c.get("source", [])) for c in nb2["cells"])
checks = {
    "version 4.9.7": full.count('__AGENT_VERSION__ = "4.9.7"') == 1,
    "no 4.9.6 left": full.count('__AGENT_VERSION__ = "4.9.6"') == 0,
    "enrich guard": 'json.loads(response_text) if isinstance(response_text, str) else response_text, site="c156-enrich"' in full,
    "resize alias present": full.count("v497-resize-after-vibe-parse") == 1,
    "resize dispatch count == 1 (moved, not duplicated)": full.count('_run_resize_model(widgets_values, "enlarge")') == 1,
}
for k, v in checks.items():
    print(("OK  " if v else "FAIL") + " " + k)
if not all(checks.values()):
    sys.exit(1)
print("[patch_v497] all checks passed")
