"""Shared extraction helpers for the v4.3.5 VOV-reviewer-adherence behavioral tests.

These execute the ACTUAL notebook source (module-level functions, module-level dict
assignments, and one class method) so the tests exercise production code paths, not
stubs (CLAUDE.md 8.10). Every test can also target a pre-patch notebook string via
the `source` argument to prove fail-pre / pass-post.
"""
from __future__ import annotations

import ast
import json
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def concat_source(nb_path=None) -> str:
    nb = json.loads(Path(nb_path or NOTEBOOK_PATH).read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    return "\n\n".join(parts)


def slice_functions(fn_names, source, extra_globals=None):
    src_lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    chosen = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in fn_names:
            chosen[node.name] = "".join(src_lines[node.lineno - 1:node.end_lineno])
    missing = [n for n in fn_names if n not in chosen]
    if missing:
        raise LookupError("module-level def(s) not found: %r" % missing)
    ns = {"__name__": "_v435_slice"}
    if extra_globals:
        ns.update(extra_globals)
    blob = "\n\n".join(chosen[n] for n in fn_names)
    exec(compile(blob, str(NOTEBOOK_PATH), "exec"), ns)
    return ns


def module_dicts(names, source):
    """Exec the module-level `name = {...}` assignment statements and return the values."""
    tree = ast.parse(source)
    out = {}
    wanted = set(names)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in wanted:
                    seg = ast.get_source_segment(source, node)
                    ns = {}
                    exec(compile(seg, str(NOTEBOOK_PATH), "exec"), ns)
                    out[tgt.id] = ns[tgt.id]
    missing = wanted - set(out)
    if missing:
        raise LookupError("module-level dict(s) not found: %r" % missing)
    return out


def slice_method_as_function(method_name, source, extra_globals=None):
    """Find a class method by name, dedent it to module level, and exec it as a
    standalone `def method_name(self, ...)`. Returns the callable."""
    tree = ast.parse(source)
    seg = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name == method_name:
                    seg = ast.get_source_segment(source, sub)
    if seg is None:
        raise LookupError("class method %r not found" % method_name)
    seg = textwrap.dedent(seg)
    ns = {"__name__": "_v435_method"}
    if extra_globals:
        ns.update(extra_globals)
    exec(compile(seg, str(NOTEBOOK_PATH), "exec"), ns)
    return ns[method_name]


class Req:
    def __init__(self, original_text="", scope_targets=None, rid="REQ-T"):
        self.original_text = original_text
        self.scope_targets = scope_targets or []
        self.id = rid


class _NullLogger:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


class FakeVerifierSelf:
    """Minimal stand-in for the class hosting _verify_structural_target: the four
    pre-check sub-verifiers return None (so the removal branch is reached) and logger
    is a no-op. This exercises the REAL method body (FIX B), not a reimplementation."""
    def __init__(self):
        self.logger = _NullLogger()

    def _verify_domain_create_coverage(self, *a, **k):
        return None

    def _verify_stub_thin_enrichment(self, *a, **k):
        return None

    def _v395_verify_description_coverage(self, *a, **k):
        return None

    def _v394_verify_move_type_count(self, *a, **k):
        return None
