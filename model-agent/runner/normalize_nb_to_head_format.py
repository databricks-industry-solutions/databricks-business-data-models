import json, collections

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))

def join_src(s):
    if isinstance(s, list):
        return "".join(s)
    return s

# Rebuild top-level in HEAD key order: nbformat, nbformat_minor, metadata, cells
out = collections.OrderedDict()
out["nbformat"] = nb.get("nbformat", 4)
out["nbformat_minor"] = nb.get("nbformat_minor", 0)
out["metadata"] = nb.get("metadata", {})

new_cells = []
for cell in nb["cells"]:
    ct = cell.get("cell_type", "code")
    nc = collections.OrderedDict()
    nc["cell_type"] = ct
    nc["metadata"] = cell.get("metadata", {})
    if ct == "code":
        nc["outputs"] = cell.get("outputs", [])
        nc["execution_count"] = cell.get("execution_count", None)
    nc["source"] = join_src(cell.get("source", ""))
    # preserve any extra keys (e.g. 'id') at the end, in original order
    for k, v in cell.items():
        if k not in nc:
            nc[k] = v
    new_cells.append(nc)
out["cells"] = new_cells

json.dump(out, open(NB, "w"), indent=1, ensure_ascii=True)
print("NORMALIZED to HEAD format")
