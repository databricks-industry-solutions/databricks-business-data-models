#!/usr/bin/env python3
"""Inventory every notebook definition the sample subsystem reaches.

Walks the call graph from the sample entry points and reports which top-level
notebook definitions are pulled in, so the port to the model installer can be a
closed set rather than a guess.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tests", "unit-tests"))
import notebook_source_util as nsu  # noqa: E402

ROOTS = ("step_generate_and_insert_samples", "_run_generate_samples")


def top_level_defs(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.setdefault(node.name, node)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.setdefault(t.id, node)
    return out


def names_used(node):
    seen = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            seen.add(n.id)
        elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            seen.add(n.value.id)
    return seen


def main():
    src = nsu.notebook_concat_source()
    tree = ast.parse(src)
    defs = top_level_defs(tree)
    reached, frontier = set(), [r for r in ROOTS if r in defs]
    missing_roots = [r for r in ROOTS if r not in defs]
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        reached.add(name)
        for used in names_used(defs[name]):
            if used in defs and used not in reached:
                frontier.append(used)

    funcs = sorted(n for n in reached
                   if isinstance(defs[n], (ast.FunctionDef, ast.AsyncFunctionDef)))
    classes = sorted(n for n in reached if isinstance(defs[n], ast.ClassDef))
    consts = sorted(n for n in reached if isinstance(defs[n], ast.Assign))

    def size(n):
        node = defs[n]
        return (getattr(node, "end_lineno", node.lineno) - node.lineno + 1)

    total = sum(size(n) for n in reached)
    print(f"roots resolved: {sorted(set(ROOTS) - set(missing_roots))}")
    if missing_roots:
        print(f"ROOTS NOT TOP-LEVEL (nested?): {missing_roots}")
    print(f"reached top-level defs: {len(reached)}  total lines: {total}\n")
    for label, group in (("CLASSES", classes), ("FUNCTIONS", funcs), ("CONSTANTS", consts)):
        print(f"--- {label} ({len(group)}) ---")
        for n in group:
            print(f"  {size(n):>6}  {n}")
        print()


if __name__ == "__main__":
    main()
