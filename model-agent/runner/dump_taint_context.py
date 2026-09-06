#!/usr/bin/env python3
"""For each taint finding, print the flagged var's assignment RHS + a code window,
so each site can be triaged (genuine LLM-response vs config/API/model.json)."""
import json
import re

NB = "agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))
cells = []
for c in nb["cells"]:
    if c.get("cell_type") != "code":
        cells.append(None); continue
    s = c["source"]; s = "".join(s) if isinstance(s, list) else s
    cells.append(s.split("\n"))

rows = json.load(open("/tmp/taint_findings.json"))
# collapse to unique (cell,var,line) — funcs duplicate across exec scopes
seen = set(); uniq = []
for r in rows:
    k = (r["cell"], r["var"], r["line"])
    if k in seen:
        continue
    seen.add(k); uniq.append(r)

for i, r in enumerate(uniq):
    ci, var, ln = r["cell"], r["var"], r["line"]
    lines = cells[ci]
    # find the assignment of var (search upward from ln)
    asg = None
    for j in range(min(ln, len(lines)) - 1, -1, -1):
        if re.match(rf"\s*{re.escape(var)}\s*=", lines[j]):
            asg = (j + 1, lines[j].strip())
            break
    print(f"\n#{i:<3} cell {ci} L{ln} func={r['func']} var={var} uses={r['uses']}")
    if asg:
        print(f"     ASSIGN L{asg[0]}: {asg[1][:160]}")
    lo = max(0, ln - 4); hi = min(len(lines), ln + 3)
    for k in range(lo, hi):
        mark = ">>" if (k + 1) == ln else "  "
        print(f"   {mark} {k+1:<5} {lines[k][:150]}")
