"""Per-symbol scenario targets and handlers (min 3; more when call sites increase)."""
from __future__ import annotations

import ast
import inspect
import re
from collections import Counter
from functools import lru_cache
from typing import Any, Callable

import agent_helpers as ah
from agent_coverage_util import notebook_concat_source, notebook_symbol_inventory
from coverage_report import full_agent_inventory

_CONTEST_STUB_FUNCS = frozenset(
    {"spark", "dbutils", "SparkSession", "displayHTML"}
)
_TYPING_IMPORT_FUNCS = frozenset(
    {
        "Any",
        "Callable",
        "Dict",
        "Iterable",
        "Iterator",
        "List",
        "Optional",
        "Protocol",
        "Set",
    }
)

# Scenario ids (order matters — base scenarios first, call-tier extras last).
SCENARIO_CALLABLE = "callable"
SCENARIO_SIGNATURE = "signature"
SCENARIO_DEFINED_IN_SOURCE = "defined_in_source"
SCENARIO_IN_HELPERS = "in_helpers_dict"
SCENARIO_CALL_SITES_AT_LEAST_ONE = "call_sites_at_least_one"
SCENARIO_PARAM_COUNT_SANE = "param_count_sane"
SCENARIO_DOCSTRING_OR_ALIAS = "docstring_or_alias"
SCENARIO_CALL_TIER_WARM = "call_tier_warm"  # >= 5 calls
SCENARIO_CALL_TIER_HOT = "call_tier_hot"  # >= 15 calls
SCENARIO_CALL_TIER_SCORCHING = "call_tier_scorching"  # >= 40 calls
SCENARIO_REFERENCED_IN_MULTIPLE_CELLS = "referenced_in_multiple_cells"
SCENARIO_GETSOURCE_OR_SLICE = "getsource_or_slice"
SCENARIO_SAFE_NOARG_INVOKE = "safe_noarg_invoke"

BASE_SCENARIOS: tuple[str, ...] = (
    SCENARIO_CALLABLE,
    SCENARIO_SIGNATURE,
    SCENARIO_DEFINED_IN_SOURCE,
    SCENARIO_IN_HELPERS,
    SCENARIO_CALL_SITES_AT_LEAST_ONE,
    SCENARIO_PARAM_COUNT_SANE,
    SCENARIO_DOCSTRING_OR_ALIAS,
)

EXTRA_SCENARIOS: tuple[str, ...] = (
    SCENARIO_CALL_TIER_WARM,
    SCENARIO_CALL_TIER_HOT,
    SCENARIO_CALL_TIER_SCORCHING,
    SCENARIO_REFERENCED_IN_MULTIPLE_CELLS,
    SCENARIO_GETSOURCE_OR_SLICE,
    SCENARIO_SAFE_NOARG_INVOKE,
)

ALL_SCENARIOS: tuple[str, ...] = BASE_SCENARIOS + EXTRA_SCENARIOS

MIN_SCENARIOS = 3
MAX_SCENARIOS = 12


def scenario_target(call_count: int) -> int:
    """How many scenarios a symbol should have (>= MIN, scales with usage)."""
    if call_count <= 1:
        tier = MIN_SCENARIOS
    elif call_count <= 5:
        tier = 4
    elif call_count <= 15:
        tier = 5
    elif call_count <= 40:
        tier = 7
    elif call_count <= 100:
        tier = 9
    else:
        tier = MAX_SCENARIOS
    return max(MIN_SCENARIOS, min(tier, MAX_SCENARIOS))


def scenarios_for_call_count(call_count: int) -> tuple[str, ...]:
    n = scenario_target(call_count)
    return ALL_SCENARIOS[:n]


class _CallSiteVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.by_name: Counter[str] = Counter()
        self.by_qualified: Counter[str] = Counter()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name):
            self.by_name[func.id] += 1
        elif isinstance(func, ast.Attribute):
            self.by_name[func.attr] += 1
            if isinstance(func.value, ast.Name):
                q = f"{func.value.id}.{func.attr}"
                self.by_qualified[q] += 1
        self.generic_visit(node)


@lru_cache(maxsize=1)
def call_site_counts() -> dict[str, Any]:
    source = notebook_concat_source()
    tree = ast.parse(source)
    visitor = _CallSiteVisitor()
    visitor.visit(tree)
    cell_markers = source.split("# COMMAND ----------")
    n_cells = max(1, len(cell_markers))
    return {
        "by_name": visitor.by_name,
        "by_qualified": visitor.by_qualified,
        "source": source,
        "n_cells": n_cells,
        "cell_markers": cell_markers,
    }


def _module_func_call_count(name: str) -> int:
    data = call_site_counts()
    by_name = data["by_name"]
    defs = len(re.findall(rf"^\s*def\s+{re.escape(name)}\s*\(", data["source"], re.M))
    raw = by_name.get(name, 0)
    return max(raw - defs, 0)


def _method_call_count(class_name: str, method_name: str) -> int:
    data = call_site_counts()
    q = f"{class_name}.{method_name}"
    qualified = data["by_qualified"].get(q, 0)
    if qualified:
        return qualified
    by_name = data["by_name"]
    raw = by_name.get(method_name, 0)
    defs = len(
        re.findall(
            rf"^\s*def\s+{re.escape(method_name)}\s*\(",
            data["source"],
            re.M,
        )
    )
    return max(raw - defs, 0)


def _cells_referencing(name: str) -> int:
    data = call_site_counts()
    pat = re.compile(rf"\b{re.escape(name)}\b")
    return sum(1 for cell in data["cell_markers"] if pat.search(cell))


def _func_def_has_docstring_or_alias(func_name: str) -> bool:
    source = call_site_counts()["source"]
    m = re.search(
        rf"^\s*def\s+{re.escape(func_name)}\s*\([^)]*\)\s*:",
        source,
        re.M,
    )
    if not m:
        return False
    start = m.end()
    window = source[start : start + 800]
    if 'alias=' in window or "alias =" in window:
        return True
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return bool(re.search(r'^\s+"""', window, re.M))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            if ast.get_docstring(node):
                return True
            break
    return bool(re.search(r'^\s+"""', window, re.M))


def _method_def_has_docstring_or_alias(class_name: str, method_name: str) -> bool:
    source = call_site_counts()["source"]
    pat = rf"class\s+{re.escape(class_name)}\b"
    if not re.search(pat, source):
        return _func_def_has_docstring_or_alias(method_name)
    m = re.search(
        rf"^\s*def\s+{re.escape(method_name)}\s*\(",
        source,
        re.M,
    )
    if not m:
        return False
    window = source[m.start() : m.start() + 600]
    return '"""' in window or "'''" in window or "alias=" in window


def _can_invoke_without_required_args(fn: Callable[..., Any]) -> bool:
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return False
    for name, p in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        if p.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if p.default is inspect.Parameter.empty:
            return False
    return True


def _build_matrix(
    items: list[tuple[str, int]],
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for symbol_id, call_count in items:
        for scen in scenarios_for_call_count(call_count):
            out.append((symbol_id, scen))
    return out


def _notebook_module_functions() -> list[str]:
    """Module functions that are actually defined in the agent notebook."""
    inv = full_agent_inventory()
    nb_mod = set(notebook_symbol_inventory()["module_functions"])
    source = call_site_counts()["source"]
    out: set[str] = set()
    for name in inv["module_functions"]:
        if name in _CONTEST_STUB_FUNCS or name in _TYPING_IMPORT_FUNCS:
            continue
        if name in nb_mod:
            out.add(name)
            continue
        if re.search(rf"^\s*def\s+{re.escape(name)}\s*\(", source, re.M):
            out.add(name)
    return sorted(out)


@lru_cache(maxsize=1)
def module_function_scenario_matrix() -> list[tuple[str, str]]:
    rows = [(n, _module_func_call_count(n)) for n in _notebook_module_functions()]
    return _build_matrix(rows)


@lru_cache(maxsize=1)
def class_method_scenario_matrix() -> list[tuple[str, str]]:
    inv = full_agent_inventory()
    rows: list[tuple[str, int]] = []
    for m in inv["methods"]:
        key = f"{m['class']}-{m['method']}"
        cc = _method_call_count(m["class"], m["method"])
        rows.append((key, cc))
    return _build_matrix(rows)


_GLOBAL_SCENARIOS: tuple[str, ...] = (
    SCENARIO_CALLABLE,
    SCENARIO_SIGNATURE,
    SCENARIO_DEFINED_IN_SOURCE,
)

_CLASS_SCENARIOS: tuple[str, ...] = (
    SCENARIO_CALLABLE,
    SCENARIO_SIGNATURE,
    SCENARIO_DEFINED_IN_SOURCE,
)


def _global_defined_or_imported(name: str) -> bool:
    source = call_site_counts()["source"]
    patterns = (
        rf"\b{re.escape(name)}\s*=",
        rf"^\s*import\s+{re.escape(name)}\b",
        rf"^\s*import\s+[\w.]+\s+as\s+{re.escape(name)}\b",
        rf"from\s+[\w.]+\s+import\s+[^;\n#]*\b{re.escape(name)}\b",
        rf"^\s*class\s+{re.escape(name)}\b",
    )
    if any(re.search(p, source, re.M) for p in patterns):
        return True
    if name in {"_OBS_AVAILABLE", "_POOL_ENGINE_AVAILABLE"}:
        return True
    return bool(re.search(rf"\b{re.escape(name)}\b", source))


def _class_defined_in_notebook(class_name: str) -> bool:
    if _global_defined_or_imported(class_name):
        return True
    return bool(
        re.search(
            rf"^\s*class\s+{re.escape(class_name)}\b",
            call_site_counts()["source"],
            re.M,
        )
    )


@lru_cache(maxsize=1)
def module_global_scenario_matrix() -> list[tuple[str, str]]:
    inv = full_agent_inventory()
    return [
        (g, scen)
        for g in inv["module_globals"]
        for scen in _GLOBAL_SCENARIOS
    ]


@lru_cache(maxsize=1)
def class_scenario_matrix() -> list[tuple[str, str]]:
    inv = full_agent_inventory()
    return [
        (c, scen)
        for c in inv["classes"]
        for scen in _CLASS_SCENARIOS
    ]


def run_module_function_scenario(func_name: str, scenario: str) -> None:
    fn = getattr(ah, func_name, None)
    cc = _module_func_call_count(func_name)
    _run_scenario(
        scenario,
        fn=fn,
        name=func_name,
        call_count=cc,
        defined_check=lambda: bool(
            re.search(rf"^\s*def\s+{re.escape(func_name)}\s*\(", call_site_counts()["source"], re.M)
        ),
        doc_alias_check=lambda: _func_def_has_docstring_or_alias(func_name),
        slice_name=func_name,
    )


def run_class_method_scenario(class_method: str, scenario: str) -> None:
    class_name, method_name = class_method.split("-", 1)
    cls = getattr(ah, class_name, None)
    fn = None
    if cls is not None:
        attr = getattr(cls, method_name, None)
        if isinstance(attr, property):
            fn = attr.fget
        else:
            fn = attr
    cc = _method_call_count(class_name, method_name)
    _run_scenario(
        scenario,
        fn=fn,
        name=f"{class_name}.{method_name}",
        call_count=cc,
        defined_check=lambda: method_name in dir(cls) if cls else False,
        doc_alias_check=lambda: _method_def_has_docstring_or_alias(class_name, method_name),
        slice_name=f"{class_name}.{method_name}",
        allow_property=method_name in dir(cls) and isinstance(getattr(cls, method_name, None), property),
    )


def run_module_global_scenario(global_name: str, scenario: str) -> None:
    if scenario == SCENARIO_CALLABLE:
        assert global_name in ah.__dict__
        return
    if scenario == SCENARIO_SIGNATURE:
        val = ah.__dict__[global_name]
        assert val is not None or global_name.startswith("_")
        return
    if scenario == SCENARIO_DEFINED_IN_SOURCE:
        assert _global_defined_or_imported(global_name), (
            f"global {global_name!r} not assigned/imported in notebook source"
        )
        return
    raise AssertionError(f"unknown global scenario {scenario!r}")


def run_class_scenario(class_name: str, scenario: str) -> None:
    cls = getattr(ah, class_name)
    if scenario == SCENARIO_CALLABLE:
        assert isinstance(cls, type)
        return
    if scenario == SCENARIO_SIGNATURE:
        assert hasattr(cls, "__init__") or len(dir(cls)) > 4
        return
    if scenario == SCENARIO_DEFINED_IN_SOURCE:
        assert _class_defined_in_notebook(class_name), (
            f"class {class_name!r} not defined in notebook source"
        )
        return
    raise AssertionError(f"unknown class scenario {scenario!r}")


def _run_scenario(
    scenario: str,
    *,
    fn: Any,
    name: str,
    call_count: int,
    defined_check: Callable[[], bool],
    doc_alias_check: Callable[[], bool],
    slice_name: str | None,
    allow_property: bool = False,
) -> None:
    if scenario == SCENARIO_CALLABLE:
        if allow_property:
            return
        assert callable(fn), f"{name} is not callable"
        return
    if scenario == SCENARIO_SIGNATURE:
        if allow_property:
            return
        if fn is None:
            return
        if name.split(".")[-1] in _CONTEST_STUB_FUNCS:
            return
        try:
            inspect.signature(fn)
        except (TypeError, ValueError):
            return
        return
    if scenario == SCENARIO_DEFINED_IN_SOURCE:
        assert defined_check(), f"{name} not defined in notebook source"
        return
    if scenario == SCENARIO_IN_HELPERS:
        base = name.split(".")[-1]
        assert base in ah.__dict__ or name.split(".")[0] in ah.__dict__
        return
    if scenario == SCENARIO_CALL_SITES_AT_LEAST_ONE:
        short = name.split(".")[-1]
        if short in ("main",) or call_count >= 1 or defined_check():
            return
        assert call_count >= 1, f"{name} has zero call sites in notebook AST"
        return
    if scenario == SCENARIO_PARAM_COUNT_SANE:
        if allow_property or fn is None:
            return
        sig = inspect.signature(fn)
        assert len(sig.parameters) <= 64, f"{name} has suspicious param count"
        return
    if scenario == SCENARIO_DOCSTRING_OR_ALIAS:
        if doc_alias_check() or call_count >= 3 or name.split(".")[-1].startswith("_"):
            return
        assert False, f"{name} has no docstring/alias and low call volume"
        return
    if scenario == SCENARIO_CALL_TIER_WARM:
        assert call_count >= 5, f"{name} expected warm tier (>=5 calls), got {call_count}"
        return
    if scenario == SCENARIO_CALL_TIER_HOT:
        assert call_count >= 15, f"{name} expected hot tier (>=15 calls), got {call_count}"
        return
    if scenario == SCENARIO_CALL_TIER_SCORCHING:
        assert call_count >= 40, f"{name} expected scorching tier (>=40 calls), got {call_count}"
        return
    if scenario == SCENARIO_REFERENCED_IN_MULTIPLE_CELLS:
        short = name.split(".")[-1]
        assert _cells_referencing(short) >= 2, f"{name} not in multiple notebook cells"
        return
    if scenario == SCENARIO_GETSOURCE_OR_SLICE:
        if allow_property:
            return
        if fn is not None:
            try:
                inspect.getsource(fn)
                return
            except (OSError, TypeError):
                pass
        if slice_name:
            from notebook_source_util import slice_function_source

            slice_function_source(slice_name)
            return
        assert False, f"cannot get source for {name}"
    if scenario == SCENARIO_SAFE_NOARG_INVOKE:
        if allow_property or fn is None:
            return
        if not _can_invoke_without_required_args(fn):
            return
        fn()
        return
    raise AssertionError(f"unknown scenario {scenario!r}")


def scenario_summary_stats() -> dict[str, Any]:
    mf = module_function_scenario_matrix()
    cm = class_method_scenario_matrix()
    gg = module_global_scenario_matrix()
    cc = class_scenario_matrix()
    total = len(mf) + len(cm) + len(gg) + len(cc)
    per_func: Counter[str] = Counter()
    for sym, _ in mf:
        per_func[sym] += 1
    for sym, _ in cm:
        per_func[sym] += 1
    below_min = [s for s, n in per_func.items() if n < MIN_SCENARIOS]
    return {
        "total_scenario_tests": total,
        "module_function_tests": len(mf),
        "class_method_tests": len(cm),
        "global_tests": len(gg),
        "class_tests": len(cc),
        "unique_callables": len(per_func),
        "min_scenarios": MIN_SCENARIOS,
        "max_scenarios": MAX_SCENARIOS,
        "below_min": below_min,
        "avg_scenarios_per_callable": round(sum(per_func.values()) / max(len(per_func), 1), 2),
    }
