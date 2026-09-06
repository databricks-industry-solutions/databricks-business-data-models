#!/usr/bin/env python3
"""Focused scan for the N4 crash class: iterating an LLM-derived list whose items are
used as dicts (item.get / item[...]) WITHOUT _coerce_list_of_dicts, so a list-of-scalars
(or a non-list) raises 'str' object has no attribute 'get'.

Flags:  for X in EXPR:  where EXPR is  NAME.get(K[, []]) | NAME[K]  (NAME tainted/LLM),
        EXPR is NOT already _coerce_list_of_dicts(...)/_coerce_*(...), and the body uses
        X.get( / X[...]  (dict treatment).
"""
import ast
import json
import re

NB = "agent/dbx_vibe_modelling_agent.ipynb"
SEED = re.compile(
    r"(judge_response|ensemble_result|core_result|_review_results?|response_data|"
    r"_parsed|raw_response|llm_response|_llm_|selection_analysis|_domain_raw|assessment|"
    r"architect_review|domain_review|fix_result|mutation_result|verdict|_data$|data$|core_products|"
    r"decisions|violations|estimates|additions|denormalized_tables|requirements|domains|products)",
    re.I,
)


def U(n):
    try:
        return ast.unparse(n)
    except Exception:
        return "<?>"


def is_coerced(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in ("_coerce_list_of_dicts", "_coerce_dict", "_v466_coerce_llm_obj"))


def item_used_as_dict(func, varname):
    for n in ast.walk(func):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == varname and n.attr in ("get", "items", "keys", "values"):
            return True
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == varname:
            return True
    return False


def clean_magics(src):
    return "\n".join(("pass  # magic" if l.lstrip().startswith(("%", "!")) else l) for l in src.split("\n"))


def main():
    nb = json.load(open(NB))
    rows = []
    for ci, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = c["source"]; src = "".join(src) if isinstance(src, list) else src
        try:
            tree = ast.parse(clean_magics(src))
        except SyntaxError:
            continue
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for n in ast.walk(func):
                if not isinstance(n, ast.For) or not isinstance(n.target, ast.Name):
                    continue
                it = n.iter
                if is_coerced(it):
                    continue
                base = key = None
                if isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute) and it.func.attr == "get":
                    base = it.func.value
                elif isinstance(it, ast.Subscript):
                    base = it.value
                if base is None:
                    continue
                base_src = U(base)
                if not SEED.search(base_src) and not SEED.search(U(it)):
                    continue
                var = n.target.id
                # is the loop var used as a dict inside the loop body?
                used = False
                for b in ast.walk(n):
                    if isinstance(b, ast.Attribute) and isinstance(b.value, ast.Name) and b.value.id == var and b.attr in ("get", "items", "keys", "values"):
                        used = True; break
                    if isinstance(b, ast.Subscript) and isinstance(b.value, ast.Name) and b.value.id == var:
                        used = True; break
                if used:
                    rows.append({"cell": ci, "line": n.lineno, "func": func.name, "iter": U(it)[:80], "var": var})
    # dedupe
    seen = set(); uniq = []
    for r in rows:
        k = (r["cell"], r["line"], r["iter"])
        if k in seen:
            continue
        seen.add(k); uniq.append(r)
    uniq.sort(key=lambda r: (r["cell"], r["line"]))
    json.dump(uniq, open("/tmp/nested_iter_findings.json", "w"), indent=2)
    print(f"UNWRAPPED nested LLM-list iterations used as dicts: {len(uniq)}")
    for r in uniq:
        print(f"  cell {r['cell']:>3} L{r['line']:<5} {r['func']:<44} for {r['var']} in {r['iter']}")


if __name__ == "__main__":
    main()
