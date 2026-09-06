#!/usr/bin/env python3
"""v4.6.6 part 3: wrap propagating non-validator nested-list iterations in _coerce_list_of_dicts.
Parent vars are already coerced to dict (parts 1-2); the inner array field could still be a
scalar / list-of-scalars on LLM drift -> `for item in X.get('k',[])` then `item.get(...)` = N4 crash.
Validator-internal iterations are EXCLUDED (smart_worker_loop wraps validator_func in try/except,
so they retry, not crash). Only the build/consume hot paths below propagate. Self-verifying."""
import ast
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

# (cell, lineno_in_cell, target_var, base_var, key)
TARGETS = [
    (100, 1438, "item", "data", "requirements"),
    (100, 4395, "vr", "data", "verification_results"),
    (148, 965, "_est", "_erc_data", "estimates"),
    (148, 993, "_viol", "_n3_data", "violations"),
    (148, 1046, "_dt", "_dn_data", "denormalized_tables"),
    (148, 1083, "_add", "_ait_data", "additions"),
    (156, 567, "product", "products_response", "products"),
    (156, 1390, "prod", "products_response", "products"),
    (156, 1446, "attr", "attrs_response", "attributes"),
    (156, 4364, "_d", "response_data", "domains"),
    (156, 4766, "product", "products_data", "products"),
]


def clean(src):
    return "\n".join(("pass  # magic" if l.lstrip().startswith(("%", "!")) else l) for l in src.split("\n"))


def main():
    nb = json.load(open(NB))
    cells = nb["cells"]

    def get(ci):
        s = cells[ci]["source"]
        return "".join(s) if isinstance(s, list) else s

    by_cell = {}
    for t in TARGETS:
        by_cell.setdefault(t[0], []).append(t)
    report = []
    for ci, items in by_cell.items():
        lines = get(ci).split("\n")
        for (ci_, ln, tv, base, key) in sorted(items, key=lambda x: -x[1]):
            idx = ln - 1
            assert 0 <= idx < len(lines), f"cell{ci} L{ln} OOB"
            line = lines[idx]
            # accept single/double quotes around key
            found = None
            for q in ("'", '"'):
                needle = f"for {tv} in {base}.get({q}{key}{q}, [])"
                if needle in line:
                    found = needle
                    break
            assert found, f"cell{ci} L{ln}: pattern not found. line: {line.strip()[:100]}"
            if "_coerce_list_of_dicts(" + base in line:
                report.append(f"cell{ci} L{ln} {base}.{key}: already wrapped (skip)")
                continue
            # extract the exact iterable expr and wrap
            q = found[found.index(".get(") + 5]
            iterable = f"{base}.get({q}{key}{q}, [])"
            replacement = f"for {tv} in _coerce_list_of_dicts({iterable})"
            lines[idx] = line.replace(f"for {tv} in {iterable}", replacement, 1)
            assert lines[idx] != line, f"cell{ci} L{ln}: replace no-op"
            report.append(f"cell{ci} L{ln}: wrapped {base}.{key} -> _coerce_list_of_dicts")
        cells[ci]["source"] = "\n".join(lines)

    for ci in by_cell:
        try:
            ast.parse(clean(get(ci)))
        except SyntaxError as e:
            print(f"SYNTAX ERROR cell {ci}: {e}", file=sys.stderr)
            sys.exit(2)

    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("NESTED-LIST COERCE APPLIED — all asserts passed, touched cells parse.\n")
    print("\n".join("  " + r for r in report))


if __name__ == "__main__":
    main()
