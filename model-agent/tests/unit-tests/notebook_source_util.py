"""Load and slice functions from the full agent notebook (all code cells)."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def notebook_concat_source() -> str:
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
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


def cell_containing(needle: str) -> str:
    """Source of the first code cell that contains `needle`.

    Tests that pinned a cell INDEX go dead as the notebook grows and silently stop
    exercising the code they name. The marker they assert on is stable; the position
    is not.
    """
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if needle in src:
            return src
    raise AssertionError("no code cell contains %r" % needle)


AGENT_VERSION_LINE_RE = re.compile(
    r'^__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"  # alias=agent-version-global$'
)


def agent_version_line() -> str:
    """First code statement of Cell 1, which CLAUDE.md 3a-bis pins to the version.

    Returned instead of a frozen literal so a version bump does not redden every
    prior version's test file.
    """
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        for line in src.split("\n"):
            if line.strip() and not line.lstrip().startswith("#"):
                assert AGENT_VERSION_LINE_RE.match(line), (
                    f"first code statement must be the single-digit-semver version "
                    f"constant, got: {line!r}"
                )
                return line
    raise AssertionError("no code cell found in the agent notebook")


def agent_version_tuple() -> tuple:
    """The running version as a comparable tuple, e.g. "4.8.8" -> (4, 8, 8)."""
    match = AGENT_VERSION_LINE_RE.match(agent_version_line())
    assert match, "version line does not match the CLAUDE.md 3a-bis shape"
    return tuple(int(part) for part in match.groups())


def assert_agent_version_at_least(version: str) -> None:
    """A fix stays shipped at every later version, so pin a FLOOR, not an equality.

    Pinning equality is why so much of this suite reddens on every bump: a v4.8.7 test
    asserting `== "4.8.7"` fails at v4.8.8 even though the v4.8.7 fix is still present
    and still correct. The floor keeps the guarantee (the fix cannot be shipped on an
    older agent) without the false alarm.
    """
    floor = tuple(int(part) for part in version.split("."))
    running = agent_version_tuple()
    assert running >= floor, (
        f"agent is v{'.'.join(map(str, running))}, older than the v{version} "
        f"this fix shipped in"
    )


def slice_function_source(fn_name: str, source: Optional[str] = None) -> str:
    """Return source of the last module-level function named fn_name.

    Also supports a dotted ``"ClassName.method"`` form: it walks the matching
    ClassDef and returns the last method of that name defined inside it. This is
    the ``getsource_OR_slice`` fallback for class methods whose LIVE object has
    no introspectable Python source (e.g. re-bound / dynamically assigned
    methods, or a class swapped for a C-extension) — the source still exists in
    the notebook, so we prove it by slicing. Method lookup is class-scoped so a
    common method name (e.g. ``add``) defined in several classes resolves to the
    right one.
    """
    source = source or notebook_concat_source()
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    _func_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    target = None
    if "." in fn_name:
        class_name, method_name = fn_name.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for sub in node.body:
                    if isinstance(sub, _func_types) and sub.name == method_name:
                        target = sub
        if target is None:
            raise LookupError(
                f"method {fn_name!r} not found in agent notebook"
            )
    else:
        for node in tree.body:
            if isinstance(node, _func_types) and node.name == fn_name:
                target = node
        if target is None:
            raise LookupError(f"module-level def {fn_name!r} not found in agent notebook")
    start = target.lineno - 1
    end = target.end_lineno
    return "".join(lines[start:end])


def exec_function_namespace(
    fn_name: str,
    extra_globals: Optional[dict] = None,
    source: Optional[str] = None,
) -> dict:
    """Exec a notebook function into a namespace and return it."""
    fn_src = slice_function_source(fn_name, source=source)
    ns = {"__name__": f"_test_slice_{fn_name}"}
    if extra_globals:
        ns.update(extra_globals)
    exec(compile(fn_src, str(NOTEBOOK_PATH), "exec"), ns)
    return ns


def exec_functions_namespace(
    fn_names,
    extra_globals: Optional[dict] = None,
    source: Optional[str] = None,
) -> dict:
    """Exec several notebook functions into ONE shared namespace (so callees resolve
    their siblings). Slices are concatenated in the given order and exec'd together."""
    source = source or notebook_concat_source()
    ns = {"__name__": "_test_slice_multi"}
    if extra_globals:
        ns.update(extra_globals)
    blob = "\n\n".join(slice_function_source(n, source=source) for n in fn_names)
    exec(compile(blob, str(NOTEBOOK_PATH), "exec"), ns)
    return ns
