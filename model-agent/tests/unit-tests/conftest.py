"""pytest configuration — extracts agent notebook code for unit tests.

Loads ALL code cells from agent/dbx_vibe_modelling_agent.ipynb (concatenated),
not cell[1] only. Databricks runtime globals are stubbed; tests patch as needed.
"""
import hashlib
import json
import os
import re
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _extract_source_from_notebook() -> str:
    """Return concatenated source from every code cell in the agent notebook.

    The cache is keyed on the SHA-256 of the notebook bytes, not its mtime.
    History of the two hazards this guards against:
      1. (2026-06-15) A stale /tmp/agent_source.py dumped days earlier at an old
         __AGENT_VERSION__ silently shadowed the live notebook, so agent_helpers
         tests ran against code that no longer existed — a 'lying scoreboard'.
      2. (2026-06-18, v3.8.4) The original mtime guard trusted the cache whenever
         cache_mtime >= notebook_mtime. A notebook restored/patched with a
         preserved (older) mtime left a NEWER stale cache that the guard honored,
         so agent_helpers loaded 3.8.3 while the live notebook was 3.8.4 →
         test_v100_agent_version_bumped failed as a FALSE regression. mtime is
         not a reliable freshness signal (restores, git ops, mtime-preserving
         editors all move it backwards). A content hash is exact: the cache is
         reused only when it was derived from byte-identical notebook source.

    The cache path is WORKER-SCOPED (PYTEST_XDIST_WORKER). Under `pytest -n`,
    workers parse concurrently; a per-worker cache + atomic (temp + os.replace)
    write removes the shared-write race while keeping within-worker reuse.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    tmp_src = Path("/tmp") / f"agent_source.{worker}.py"
    tmp_hash = Path("/tmp") / f"agent_source.{worker}.sha256"

    nb_bytes = NOTEBOOK_PATH.read_bytes()
    nb_hash = hashlib.sha256(nb_bytes).hexdigest()

    if tmp_src.exists() and tmp_hash.exists():
        try:
            if tmp_hash.read_text(encoding="utf-8").strip() == nb_hash:
                return tmp_src.read_text(encoding="utf-8")
        except Exception:
            pass  # corrupt/partial cache — fall through and re-extract

    nb = json.loads(nb_bytes.decode("utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    if not parts:
        raise RuntimeError("No code cells found in agent notebook")
    concat = "\n\n".join(parts)
    # Refresh the (worker-scoped) cache + its hash sidecar atomically so a
    # same-worker re-entry reuses it without ever seeing a partial file, and a
    # later run validates freshness by content hash rather than mtime.
    try:
        tmp_partial = tmp_src.with_suffix(f".py.{os.getpid()}.tmp")
        tmp_partial.write_text(concat, encoding="utf-8")
        os.replace(str(tmp_partial), str(tmp_src))
        hash_partial = tmp_hash.with_suffix(f".sha256.{os.getpid()}.tmp")
        hash_partial.write_text(nb_hash, encoding="utf-8")
        os.replace(str(hash_partial), str(tmp_hash))
    except Exception:
        pass
    return concat


def _build_agent_helpers_module():
    """Parse full notebook source and exec defs with lightweight Databricks stubs."""
    import ast

    source = _extract_source_from_notebook()
    source = re.sub(
        r"\n+(?:#\s*COMMAND\s*-+\s*\n+)?if __name__ == \"__main__\":\s*\n\s+main\(\)\s*\n?\s*$",
        "\n",
        source,
        flags=re.DOTALL,
    )

    module = types.ModuleType("agent_helpers")

    class _Stub:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return _Stub()

        def __call__(self, *args, **kwargs):
            return _Stub()

        def __bool__(self):
            return False

        def __iter__(self):
            return iter([])

        def __getitem__(self, k):
            return _Stub()

        def __setitem__(self, k, v):
            pass

        def __len__(self):
            return 0

    module.__dict__.update(
        {
            "spark": _Stub(),
            "dbutils": _Stub(),
            "displayHTML": lambda *a, **k: None,
            "SparkSession": _Stub(),
            "_POOL_ENGINE_AVAILABLE": True,
            "_OBS_AVAILABLE": False,
        }
    )

    tree = ast.parse(source)
    kept = []
    _BLOCKED_IMPORTS = {
        "pyspark",
        "databricks",
        "delta",
        "pandas",
        "numpy",
        "IPython",
        "ipywidgets",
        "matplotlib",
        "plotly",
    }
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod_name = (
                node.module
                if isinstance(node, ast.ImportFrom)
                else (node.names[0].name if node.names else "")
            )
            top = (mod_name or "").split(".")[0]
            if top in _BLOCKED_IMPORTS:
                continue
            kept.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kept.append(node)
        elif isinstance(node, ast.Assign):
            rhs_has_runtime = False
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Name) and sub.id in {
                    "spark",
                    "dbutils",
                    "SparkSession",
                }:
                    rhs_has_runtime = True
                    break
            if not rhs_has_runtime:
                kept.append(node)

    module.__dict__["_load_errors"] = []
    module.__dict__["_load_error"] = None
    module.__dict__["_loaded_node_count"] = 0
    for node in kept:
        try:
            snippet = ast.Module(body=[node], type_ignores=[])
            code = compile(snippet, str(NOTEBOOK_PATH), "exec")
            exec(code, module.__dict__)
            module.__dict__["_loaded_node_count"] += 1
        except Exception as e:
            _name = getattr(node, "name", type(node).__name__)
            module.__dict__["_load_errors"].append(
                f"{_name}: {type(e).__name__}: {e}"
            )
            if module.__dict__["_load_error"] is None:
                module.__dict__["_load_error"] = f"{_name}: {e}"

    module.__file__ = str(NOTEBOOK_PATH)
    sys.modules["agent_helpers"] = module
    return module


_build_agent_helpers_module()


@pytest.fixture(scope="session")
def agent_source_text():
    """Full notebook Python source (all code cells) — prefer over raw .ipynb JSON."""
    from notebook_source_util import notebook_concat_source

    return notebook_concat_source()


def pytest_collection_modifyitems(config, items):
    try:
        from _stale_quarantine import STALE_XFAIL_NODEIDS
    except Exception:
        return
    mark = pytest.mark.xfail(
        reason="stale pre-v0.8.0 version-pinned assertion (quarantined at main-bridge; cleanup tracked)",
        strict=False,
        run=True,
    )
    for item in items:
        if item.nodeid in STALE_XFAIL_NODEIDS:
            item.add_marker(mark)


def pytest_sessionfinish(session, exitstatus):
    """Print symbol-coverage summary after the full test run."""
    # Opt-out for CI/local full-suite validation runs where the notebook-parsing coverage +
    # scenario reports add multi-minute session-finish overhead that can stall under xdist.
    if os.environ.get("VIBE_SKIP_COV_REPORT") == "1":
        return
    try:
        from coverage_report import emit_symbol_coverage_report

        emit_symbol_coverage_report(session)
    except Exception as exc:
        import traceback

        print(f"\n[coverage-report] skipped: {exc}")
        traceback.print_exc()
    try:
        from scenario_coverage_report import emit_scenario_summary

        emit_scenario_summary()
    except Exception as exc:
        import traceback

        print(f"\n[scenario-report] skipped: {exc}")
        traceback.print_exc()
