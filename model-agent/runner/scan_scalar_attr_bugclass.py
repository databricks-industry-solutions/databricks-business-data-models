#!/usr/bin/env python3
"""AST TAINT scanner for the issue-#21 bug class.

Seed taint from genuine LLM-response sources:
    - RHS containing json.loads(...) / clean_json_response(...) / smart_worker_loop(...)
    - variables named like known LLM results (judge_response, ensemble_results, core_result,
      *_review_results, response_data, *_parsed, raw_response, llm_response, *_llm_*)
Propagate intra-function:
    - child = <tainted>.get(...)      -> child tainted
    - child = <tainted>[...]          -> child tainted
    - child = <tainted>.get(k, {}|[]|None)  -> child tainted (issue #21 shape)
Flag DANGEROUS USE of a tainted var (dict/list treatment) with NO guard:
    - var.get/items/keys/values/setdefault/update/pop( , var.append/extend/insert(
    - var[...]  , for _ in var: (with item.get / item[...] inside)
Guard (suppress): _coerce_dict(var)/_coerce_list_of_dicts(var)/isinstance(var,...) in func,
    or `if isinstance(var,str): var=json.loads(var)`, or wrapped-at-use _coerce_*(var).
"""
import ast
import json
import re

NB = "agent/dbx_vibe_modelling_agent.ipynb"

SEED_NAME_RE = re.compile(
    r"(judge_response|ensemble_result|core_result|_review_results?|response_data|"
    r"_parsed$|raw_response|llm_response|_llm_|selection_analysis|_domain_raw|"
    r"architect_review|domain_review|fix_result|mutation_result|verdict|assessment)",
    re.I,
)
SEED_RHS_RE = re.compile(r"json\.loads\(|clean_json_response\(|smart_worker_loop\(")

DICT_METHODS = {"get", "items", "keys", "values", "setdefault", "update", "pop"}
LIST_METHODS = {"append", "extend", "insert"}


def U(n):
    try:
        return ast.unparse(n)
    except Exception:
        return "<?>"


class FuncScan:
    def __init__(self, func, cell_idx):
        self.func = func
        self.cell_idx = cell_idx
        self.findings = []

    def guarded(self):
        g = set()
        COERCERS = ("_coerce_dict", "_coerce_list_of_dicts", "_v466_coerce_llm_obj", "_to_dict")
        # var = _coercer(...)  -> var is guaranteed dict/list
        for n in ast.walk(self.func):
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                v = n.value
                if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id in COERCERS:
                    g.add(n.targets[0].id)
        for n in ast.walk(self.func):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in (
                "_coerce_dict", "_coerce_list_of_dicts", "_to_dict", "_ensure_dict", "_ensure_list",
                "_v466_coerce_llm_obj",
            ):
                for a in n.args:
                    if isinstance(a, ast.Name):
                        g.add(a.id)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "isinstance":
                if n.args and isinstance(n.args[0], ast.Name):
                    g.add(n.args[0].id)
        return g

    def run(self):
        # gather assignments in order
        assigns = []  # (lineno, target, rhs_node, rhs_src)
        for n in ast.walk(self.func):
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                assigns.append((n.lineno, n.targets[0].id, n.value, U(n.value)))

        # seed taint
        tainted = {}  # name -> first lineno tainted
        for ln, tgt, val, src in assigns:
            if SEED_RHS_RE.search(src) or SEED_NAME_RE.search(tgt):
                tainted.setdefault(tgt, ln)

        # propagate to fixpoint: child = <tainted>.get(...) / <tainted>[...]
        changed = True
        while changed:
            changed = False
            for ln, tgt, val, src in assigns:
                base = None
                if isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute) and val.func.attr in ("get", "pop"):
                    base = val.func.value
                elif isinstance(val, ast.Subscript):
                    base = val.value
                if base is not None and isinstance(base, ast.Name) and base.id in tainted:
                    if tgt not in tainted:
                        tainted[tgt] = ln
                        changed = True

        if not tainted:
            return
        guarded = self.guarded()
        # flag dangerous uses
        for n in ast.walk(self.func):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                nm = n.value.id
                if nm in tainted and nm not in guarded and (n.attr in DICT_METHODS or n.attr in LIST_METHODS):
                    if n.lineno >= tainted[nm]:
                        self.findings.append((n.lineno, nm, n.attr))
            if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name):
                nm = n.value.id
                if nm in tainted and nm not in guarded and n.lineno >= tainted[nm]:
                    self.findings.append((n.lineno, nm, "[]"))
        return self.findings


def clean_magics(src):
    out = []
    for ln in src.split("\n"):
        s = ln.lstrip()
        if s.startswith("%") or s.startswith("!"):
            out.append("pass  # magic")
        else:
            out.append(ln)
    return "\n".join(out)


def main():
    nb = json.load(open(NB))
    finds = []
    pf = 0
    for ci, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = c["source"]; src = "".join(src) if isinstance(src, list) else src
        try:
            tree = ast.parse(clean_magics(src))
        except SyntaxError:
            pf += 1
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fs = FuncScan(node, ci)
                fs.run()
                for (lineno, nm, use) in fs.findings:
                    finds.append({"cell": ci, "line": lineno, "func": node.name, "var": nm, "use": use})
    # collapse to one row per (cell,func,var) with use-count + min line
    from collections import defaultdict
    agg = defaultdict(lambda: {"uses": set(), "min": 10**9})
    for f in finds:
        k = (f["cell"], f["func"], f["var"])
        agg[k]["uses"].add(f["use"])
        agg[k]["min"] = min(agg[k]["min"], f["line"])
    rows = []
    for (ci, fn, var), d in agg.items():
        rows.append({"cell": ci, "func": fn, "var": var, "line": d["min"], "uses": sorted(d["uses"])})
    rows.sort(key=lambda r: (r["cell"], r["line"]))
    json.dump(rows, open("/tmp/taint_findings.json", "w"), indent=2)
    print(f"parse-failed cells: {pf}")
    print(f"TAINTED dangerous-use sites (var-level): {len(rows)}  (raw uses: {len(finds)})")
    for r in rows:
        print(f"  cell {r['cell']:>3} L{r['line']:<5} {r['func']:<44} {r['var']:<26} uses={r['uses']}")


if __name__ == "__main__":
    main()
