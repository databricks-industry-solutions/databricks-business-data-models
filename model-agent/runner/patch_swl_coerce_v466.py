#!/usr/bin/env python3
"""v4.6.6 part 2: coerce smart_worker_loop results to dict at the 12 unguarded consumers.
smart_worker_loop returns the RAW response (str/list on LLM drift); every consumer here
does VAR.get(...)/iterates VAR guarded only by `if not success`, which does NOT guarantee
dict type. Insert `VAR = _v466_coerce_llm_obj(VAR, site=...)` right after the (multi-line)
call so all downstream dict access is safe. Self-verifying; aborts on any mismatch."""
import ast
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

# (cell, assign_lineno_in_cell, var)  — from scan_swl_consumers.py
TARGETS = [
    (142, 1309, "p_data"),
    (152, 390, "params_data"),
    (156, 360, "domain_response"),
    (156, 543, "products_response"),
    (156, 780, "attrs_data"),
    (156, 1375, "products_response"),
    (156, 1430, "attrs_response"),
    (156, 2732, "business_context_data"),
    (156, 4741, "products_data"),
    (156, 5356, "attrs_data"),
    (176, 584, "attrs_data_result"),
    (176, 864, "attrs_result"),
]


def clean(src):
    return "\n".join(("pass  # magic" if l.lstrip().startswith(("%", "!")) else l) for l in src.split("\n"))


def main():
    nb = json.load(open(NB))
    cells = nb["cells"]

    def get(ci):
        s = cells[ci]["source"]
        return "".join(s) if isinstance(s, list) else s

    # group targets by cell, process bottom-up so earlier line numbers stay valid
    by_cell = {}
    for (ci, ln, var) in TARGETS:
        by_cell.setdefault(ci, []).append((ln, var))
    report = []
    for ci, items in by_cell.items():
        lines = get(ci).split("\n")
        # process in DESCENDING line order so insertions don't shift earlier indices
        for (ln, var) in sorted(items, key=lambda x: -x[0]):
            idx = ln - 1
            assert 0 <= idx < len(lines), f"cell{ci} line {ln} OOB"
            assert "smart_worker_loop(" in lines[idx] and var in lines[idx], \
                f"cell{ci} L{ln}: expected smart_worker_loop unpack for {var}, got: {lines[idx].strip()[:80]}"
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
            # paren-match from idx to end of call
            depth = 0
            end = None
            for j in range(idx, len(lines)):
                for ch in lines[j]:
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                if depth == 0:
                    end = j
                    break
            assert end is not None, f"cell{ci} L{ln}: could not paren-match call end"
            newline = f'{indent}{var} = _v466_coerce_llm_obj({var}, site="swl-{var}-c{ci}L{ln}")'
            # idempotency guard
            if end + 1 < len(lines) and lines[end + 1].strip() == newline.strip():
                report.append(f"cell{ci} L{ln} {var}: already coerced (skip)")
                continue
            lines.insert(end + 1, newline)
            report.append(f"cell{ci} L{ln} {var}: coerced after call end L{end+1}")
        cells[ci]["source"] = "\n".join(lines)

    # validate parse
    for ci in by_cell:
        try:
            ast.parse(clean(get(ci)))
        except SyntaxError as e:
            print(f"SYNTAX ERROR cell {ci}: {e}", file=sys.stderr)
            sys.exit(2)

    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("SWL COERCE APPLIED — all asserts passed, touched cells parse.\n")
    print("\n".join("  " + r for r in report))


if __name__ == "__main__":
    main()
