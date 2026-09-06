import json, collections

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))
cells = nb["cells"]

def get(i):
    s = cells[i].get("source", "")
    return "".join(s) if isinstance(s, list) else s

OLD = '''    logger.info(f"  [kpi-first-stats FIRED] kpis={len(kpi_views)}, with_joins={_kpi_with_joins} ({100*_kpi_with_joins//max(1,len(kpi_views))}%), total_joins_proposed={_kpi_total_joins}, domains_covered={_domains_covered}")
    if _kpi_with_joins == 0:
        logger.warning(f"  [kpi-first-stats] WARNING: 0 KPIs use joins. The KPI-first redesign expected most KPIs to be multi-table. Check prompt or LLM behavior.")
    if len(kpi_views) < 10:
        logger.warning(f"  [kpi-first-stats] WARNING: only {len(kpi_views)} KPIs produced (target was {target_kpi_count}). LLM may have struggled with prompt or context size.")'''

NEW = '''    logger.info(f"  [kpi-first-stats FIRED] kpis={len(kpi_views)}, with_joins={_kpi_with_joins} ({100*_kpi_with_joins//max(1,len(kpi_views))}%), total_joins_proposed={_kpi_total_joins}, domains_covered={_domains_covered}")
    # v4.6.4 alias=kpi-warn-calibrate — calibrate the two KPI advisories so they do not emit
    # false-red WARNINGs that block the clean-install bar:
    #  (1) The join signal is a genuine quality concern only for FULL-scope models. On a small
    #      model (few products) single-table KPIs are legitimate — there simply are not enough
    #      related tables to join across — so downgrade to INFO at small scope.
    #  (2) The count check previously hardcoded `< 10`, so it false-warned "only 8 KPIs (target
    #      was 8)" whenever the scope target was under 10 even though the model MET its target.
    #      Warn only when the model UNDERSHOT its OWN target_kpi_count.
    _kpi_small_scope = len(products) < 10
    if _kpi_with_joins == 0:
        if _kpi_small_scope:
            logger.info(f"  [kpi-warn-calibrate FIRED v4.6.4] 0 KPIs use joins — expected at small scope ({len(products)} products); single-table KPIs are legitimate here. alias=kpi-warn-calibrate")
        else:
            logger.warning(f"  [kpi-first-stats] WARNING: 0 KPIs use joins. The KPI-first redesign expected most KPIs to be multi-table. Check prompt or LLM behavior.")
    if len(kpi_views) < target_kpi_count:
        logger.warning(f"  [kpi-first-stats] WARNING: only {len(kpi_views)} KPIs produced (target was {target_kpi_count}). LLM may have struggled with prompt or context size.")
    elif len(kpi_views) < 10:
        logger.info(f"  [kpi-warn-calibrate FIRED v4.6.4] {len(kpi_views)} KPI(s) produced, meeting the scope target of {target_kpi_count} (small-scope model, below the legacy display floor of 10). alias=kpi-warn-calibrate")'''

s192 = get(192)
assert s192.count(OLD) == 1, f"OLD count={s192.count(OLD)}"
cells[192]["source"] = s192.replace(OLD, NEW)

out = collections.OrderedDict()
out["nbformat"] = nb.get("nbformat", 4)
out["nbformat_minor"] = nb.get("nbformat_minor", 0)
out["metadata"] = nb.get("metadata", {})
new_cells = []
for cell in cells:
    ct = cell.get("cell_type", "code")
    nc = collections.OrderedDict()
    nc["cell_type"] = ct
    nc["metadata"] = cell.get("metadata", {})
    if ct == "code":
        nc["outputs"] = cell.get("outputs", [])
        nc["execution_count"] = cell.get("execution_count", None)
    s = cell.get("source", "")
    nc["source"] = "".join(s) if isinstance(s, list) else s
    for k, v in cell.items():
        if k not in nc:
            nc[k] = v
    new_cells.append(nc)
out["cells"] = new_cells
json.dump(out, open(NB, "w"), indent=1, ensure_ascii=True)
print("PATCHED OK: kpi-warn-calibrate applied")
