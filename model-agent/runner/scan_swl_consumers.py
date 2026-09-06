#!/usr/bin/env python3
"""Find every smart_worker_loop consumer whose result var is dict-consumed (.get/.items/
.keys/.values/subscript/dict-style iteration) anywhere in its enclosing function WITHOUT
an isinstance/_coerce_dict/_v466_coerce_llm_obj guard. These are issue-#21-class sites
(smart_worker_loop returns the RAW response, which can be a str/list on LLM drift)."""
import ast
import json

NB = "agent/dbx_vibe_modelling_agent.ipynb"
DICTM = {"get", "items", "keys", "values", "setdefault", "pop"}


def clean(src):
    return "\n".join(("pass  # magic" if l.lstrip().startswith(("%", "!")) else l) for l in src.split("\n"))


def guarded_vars(func):
    g = set()
    for n in ast.walk(func):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in (
                "_coerce_dict", "_v466_coerce_llm_obj", "_coerce_list_of_dicts", "isinstance"):
            if n.args and isinstance(n.args[0], ast.Name):
                g.add(n.args[0].id)
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = n.value
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id in (
                    "_coerce_dict", "_v466_coerce_llm_obj"):
                g.add(n.targets[0].id)
    return g


def swl_targets(func):
    """names bound from `= smart_worker_loop(...)` (2nd of 3-tuple, or single)."""
    out = {}
    for n in ast.walk(func):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) \
           and isinstance(n.value.func, ast.Name) and n.value.func.id == "smart_worker_loop":
            t = n.targets[0]
            if isinstance(t, ast.Tuple) and len(t.elts) == 3 and isinstance(t.elts[1], ast.Name):
                out[t.elts[1].id] = n.lineno
            elif isinstance(t, ast.Name):
                out[t.id] = n.lineno
    return out


def dict_used(func, var):
    for n in ast.walk(func):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == var and n.attr in DICTM:
            return True
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == var:
            return True
        if isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Attribute) \
           and isinstance(n.iter.func.value, ast.Name) and n.iter.func.value.id == var:
            return True
    return False


nb = json.load(open(NB))
rows = []
for ci, c in enumerate(nb["cells"]):
    if c.get("cell_type") != "code":
        continue
    s = c["source"]; s = "".join(s) if isinstance(s, list) else s
    try:
        tree = ast.parse(clean(s))
    except SyntaxError:
        continue
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        tg = swl_targets(func)
        if not tg:
            continue
        g = guarded_vars(func)
        for var, ln in tg.items():
            if var in g:
                continue
            if dict_used(func, var):
                rows.append({"cell": ci, "line": ln, "func": func.name, "var": var})
seen = set(); uniq = []
for r in rows:
    k = (r["cell"], r["line"], r["var"])
    if k in seen:
        continue
    seen.add(k); uniq.append(r)
uniq.sort(key=lambda r: (r["cell"], r["line"]))
json.dump(uniq, open("/tmp/swl_consumers.json", "w"), indent=2)
print(f"UNGUARDED smart_worker_loop dict-consumers: {len(uniq)}")
for r in uniq:
    print(f"  cell {r['cell']:>3} L{r['line']:<5} {r['func']:<44} {r['var']}")
