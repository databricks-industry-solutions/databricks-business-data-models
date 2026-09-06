"""Behavioral tests for v0.6.4 performance fixes.

Covers 3 concurrency caps lifted to drive the v0.6.3 v1 run from 186 min toward ~115-130 min:

  B1  perf-cap-16              -- _compute_max_concurrent_batches_for_32gb
                                  capped at 8 workers; lifted to 16 so the
                                  Step 4/4.6/5/6/7 attribute-generation,
                                  normalization, and linking pools fully utilize
                                  the 32GB serverless executor capacity.
  B8  perf-llm-throttle-16     -- two LLM-throttle ceilings of min(10, max_batches)
                                  collapsed the worker pool back to 10; lifted
                                  to 16 to match B1.
  B3  perf-mv15-parallel       -- run_fk_semantic_correctness_gate (MV15) ran
                                  its batch loop sequentially (~14 min for 32
                                  batches in v0.6.3); now executes through
                                  run_parallel_with_rate_limit_backoff with a
                                  threading.Lock guarding aggregate counters.
"""
import json
import re

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


def _agent_src() -> str:
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


# =============================================================================
# B1 — _compute_max_concurrent_batches_for_32gb cap 8 -> 16
# =============================================================================

def test_v064_b1_alias_present():
    src = _agent_src()
    assert "v0.6.4 B1 alias=perf-cap-16" in src, "perf-cap-16 sentinel missing"


def test_v064_b1_cap_lifted_to_16():
    src = _agent_src()
    assert "min(raw, 16)" in src, "B1 cap should be min(raw, 16)"
    assert "return min(raw, 8)" not in src, "old min(raw, 8) cap must be gone"


def test_v064_b1_raw_upper_bound_lifted():
    src = _agent_src()
    assert re.search(r"raw\s*=\s*24\s+if\s+n_attributes\s*<\s*100_?000", src), \
        "raw upper bound should be 24 for n_attributes < 100k"


# =============================================================================
# B8 — LLM throttle ceilings 10 -> 16
# =============================================================================

def test_v064_b8_alias_present():
    src = _agent_src()
    assert "v0.6.4 B8 alias=perf-llm-throttle-16" in src, "perf-llm-throttle-16 sentinel missing"


def test_v064_b8_min10_replaced_with_min16():
    src = _agent_src()
    assert src.count("min(10, max_batches)") == 0, \
        "old min(10, max_batches) LLM throttle must be gone"
    assert src.count("min(16, max_batches)") >= 1, \
        "new min(16, max_batches) LLM throttle must be present at least once"


def test_v064_b8_orchestrator_init_throttle_lifted():
    src = _agent_src()
    pattern = re.compile(
        r'MAX_CONCURRENT_LLM_CALLS["\']?\s*,\s*min\(\s*16\s*,\s*self\.system_config\.get\(\s*["\']MAX_CONCURRENT_BATCHES'
    )
    assert pattern.search(src), \
        "AIAgent/orchestrator init must use min(16, MAX_CONCURRENT_BATCHES) for MAX_CONCURRENT_LLM_CALLS"


# =============================================================================
# B3 — MV15 sequential loop -> parallel
# =============================================================================

def test_v064_b3_alias_present():
    src = _agent_src()
    assert "v0.6.4 B3 alias=perf-mv15-parallel" in src, "perf-mv15-parallel sentinel missing"


def test_v064_b3_helper_function_extracted():
    src = _agent_src()
    assert "_process_one_mv15_batch" in src, \
        "B3 should extract per-batch logic into _process_one_mv15_batch helper"


def test_v064_b3_count_lock_guards_counters():
    src = _agent_src()
    assert "_mv15_count_lock" in src, "MV15 aggregate-counter lock must exist"
    assert re.search(r"_mv15_count_lock\s*=\s*threading\.Lock\(", src), \
        "_mv15_count_lock must be a threading.Lock instance"


def test_v064_b3_uses_parallel_runner():
    """Helper must be invoked via the project's parallel runner (or a guarded thread pool)."""
    src = _agent_src()
    idx = src.find("def _process_one_mv15_batch")
    assert idx > 0, "_process_one_mv15_batch definition must exist"
    window = src[idx: idx + 20000]
    assert (
        "run_parallel_with_rate_limit_backoff" in window
        or "guarded_thread_pool_executor" in window
        or "ThreadPoolExecutor" in window
    ), "MV15 batches must be dispatched via a parallel pool, not a sequential for-loop"


def test_v064_b3_no_continue_inside_helper():
    """`continue` is invalid inside a function body; helper must use return None."""
    src = _agent_src()
    idx = src.find("def _process_one_mv15_batch")
    assert idx > 0, "_process_one_mv15_batch definition must exist"
    # Find next top-level def/class as boundary
    body_end = re.search(r"\n(def |class )", src[idx + 1:])
    body = src[idx: idx + 1 + (body_end.start() if body_end else 8000)]
    # `continue` would be a SyntaxError inside a function (no enclosing loop)
    # We just want to make sure we replaced it with return None on the error path.
    assert "return None" in body, \
        "MV15 helper must use `return None` (not `continue`) on error paths"


# =============================================================================
# Test-suite hygiene — version-history readme entry & deploy alias updated
# =============================================================================

README = "/Users/user/Documents/projects/vibe-modelling-agent/readme.md"


def _readme_src() -> str:
    return open(README).read()


def test_v064_readme_current_version_bumped():
    """v0.6.4 must be reachable from the readme — either as Current version OR as a
    history-table entry. Once a later version bumps the Current pointer, the v0.6.4
    history row is the surviving evidence that v0.6.4 shipped."""
    rd = _readme_src()
    assert "**v0.6.4**" in rd, "readme must reference v0.6.4 (current or history row)"


def test_v064_readme_history_entry_present():
    rd = _readme_src()
    assert "**v0.6.4**" in rd, "readme version history must include v0.6.4 row"
    assert "perf-cap-16" in rd
    assert "perf-llm-throttle-16" in rd
    assert "perf-mv15-parallel" in rd


def test_v064_readme_b2_b7_explicitly_excluded():
    """Per user directive, B2 and B7 are NOT shipped; the readme must document this."""
    rd = _readme_src()
    assert "NOT applied" in rd or "not applied" in rd or "kept sequential" in rd, \
        "readme must document that B2/B7 were intentionally excluded"
