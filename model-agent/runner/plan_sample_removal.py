#!/usr/bin/env python3
"""Work out which agent definitions are EXCLUSIVELY sample code, so removing them
cannot take a shared helper with them.

Seeds are the sample entry point plus the sample-only name prefixes; anything a seed
reaches is a candidate, and a candidate survives only while nothing outside the
removal set still references it.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tests", "unit-tests"))
import notebook_source_util as nsu  # noqa: E402

SEED_NAMES = {"step_generate_and_insert_samples"}
SEED_PATTERNS = (r"^_v471_", r"^_V471_", r"^_p068_", r"^_P068_", r"^SAMPLE_POOL_PROMPT$",
                 r"^_p083_emit_raw_pool_log$", r"^_P083_RAW_LOG_COUNT$")


def top_level_defs(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.setdefault(node.name, node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out.setdefault(target.id, node)
    return out


def names_used(node):
    seen = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            seen.add(sub.id)
        elif isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name):
            seen.add(sub.value.id)
    return seen


def main():
    src = nsu.notebook_concat_source()
    tree = ast.parse(src)
    defs = top_level_defs(tree)

    seeds = set(n for n in SEED_NAMES if n in defs)
    for name in defs:
        if any(re.search(p, name) for p in SEED_PATTERNS):
            seeds.add(name)

    candidates, frontier = set(), list(seeds)
    while frontier:
        name = frontier.pop()
        if name in candidates:
            continue
        candidates.add(name)
        for used in names_used(defs[name]):
            if used in defs and used not in candidates:
                frontier.append(used)

    module_nodes = [n for n in tree.body
                    if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.ClassDef, ast.Assign))]
    module_names = set()
    for node in module_nodes:
        module_names |= names_used(node)
    for node in tree.body:
        if isinstance(node, ast.Assign) and not any(
                isinstance(t, ast.Name) and t.id in defs for t in node.targets):
            module_names |= names_used(node)

    removable = set(candidates)
    changed = True
    while changed:
        changed = False
        for name in sorted(removable):
            if name in module_names:
                removable.discard(name)
                changed = True
                continue
            for other, node in defs.items():
                if other in removable or other == name:
                    continue
                if name in names_used(node):
                    removable.discard(name)
                    changed = True
                    break

    def size(name):
        node = defs[name]
        return getattr(node, "end_lineno", node.lineno) - node.lineno + 1

    kept = sorted(candidates - removable)
    print("SEEDS: %d" % len(seeds))
    print("REMOVABLE (exclusively sample): %d defs, %d lines"
          % (len(removable), sum(size(n) for n in removable)))
    for name in sorted(removable, key=size, reverse=True):
        print("   %6d  %s" % (size(name), name))
    print("\nSHARED (reached by sample code but used elsewhere too - KEEP): %d" % len(kept))
    for name in kept:
        print("   %6d  %s" % (size(name), name))

    print("\nModule-level references to sample seeds:")
    for name in sorted(seeds):
        hits = [i + 1 for i, line in enumerate(src.split("\n"))
                if re.search(r"\b%s\b" % re.escape(name), line)]
        if len(hits) <= 6:
            print("   %s -> lines %s" % (name, hits))
        else:
            print("   %s -> %d references" % (name, len(hits)))


if __name__ == "__main__":
    main()
