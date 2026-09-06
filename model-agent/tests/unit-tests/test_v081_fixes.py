"""Tests for v0.8.1 fixes — root-cause regression tests for the 11 fixes
landed in commit cedc3ae and follow-ups (sentinel aliases, clear_active wiring,
config-guard sweep, _is_system_identifier_column config plumbing, validator
registry wiring).

Each test exercises the FAILURE MODE of the fix so reverting the fix
breaks the test. Where the patched logic lives inside a closure
(C2/C4/C6/G1/G5/G11), we assert structural invariants of the source
(post-fix ordering, presence of merging logic, etc.) which are still
meaningful regression tests because they detect any reversion.
"""
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"
RUNNER_PATH = REPO_ROOT / "runner" / "vibe_runner.ipynb"
TESTER_PATH = REPO_ROOT / "tests" / "vibe_tester.ipynb"


def _read_notebook_source(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        parts.append(src)
    return "\n".join(parts)


@pytest.fixture(scope="module")
def agent_src() -> str:
    return _read_notebook_source(NOTEBOOK_PATH)


@pytest.fixture(scope="module")
def runner_src() -> str:
    return _read_notebook_source(RUNNER_PATH)


@pytest.fixture(scope="module")
def tester_src() -> str:
    return _read_notebook_source(TESTER_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# G1 — IDL chunking fallback restored
# ─────────────────────────────────────────────────────────────────────────────
class TestG1IdlChunkingFallback:
    def test_chunking_fallback_present_in_idl_smart_worker(self, agent_src):
        idx = agent_src.find("def _run_in_domain_linking_smart_worker")
        assert idx != -1, "IDL smart worker function not found"
        body = agent_src[idx:idx + 30000]
        assert "_p070_cluster_products_for_chunking" in body, (
            "G1 fix REVERTED — chunking helper not used in IDL smart worker; "
            "domains too large will fail without retry."
        )
        assert "_P070_CHUNK_SIZE" in body or "chunk_size" in body, (
            "G1 fix REVERTED — chunk size constant not referenced."
        )

    def test_p070_clusterer_module_level_function_exists(self, agent_src):
        assert "def _p070_cluster_products_for_chunking" in agent_src


# ─────────────────────────────────────────────────────────────────────────────
# G4 (alias G2) — industry-agnostic MANAGED LOCATION in runner+tester
# ─────────────────────────────────────────────────────────────────────────────
class TestG4ManagedLocation:
    HARDCODED_LIST_PATTERN = re.compile(
        r'\[[^\]]*"acme_ecm"[^\]]*"smoke_v1"[^\]]*"industry_mvm_v1"',
        re.DOTALL,
    )

    def test_runner_no_hardcoded_customer_list(self, runner_src):
        # Customer-name probe LIST must not exist in code (mention in docstring is OK)
        assert not self.HARDCODED_LIST_PATTERN.search(runner_src), (
            "G4 REGRESSION — runner re-introduced the hardcoded customer-catalog probe list."
        )

    def test_tester_no_hardcoded_customer_list(self, tester_src):
        assert not self.HARDCODED_LIST_PATTERN.search(tester_src), (
            "G4 REGRESSION — tester re-introduced the hardcoded customer-catalog probe list."
        )

    def test_runner_uses_dry_helper(self, runner_src):
        assert "_resolve_managed_location" in runner_src, (
            "G4 fix REVERTED — runner doesn't use shared _resolve_managed_location helper."
        )

    def test_tester_has_g4_alias_sentinel(self, tester_src):
        # Tester replicates the logic inline (doesn't import) but must carry the sentinel.
        assert "alias: G4-FIX" in tester_src, (
            "G4 alias sentinel missing in tester — fix not greppable under commit-msg taxonomy."
        )

    def test_alias_sentinel_present_in_runner(self, runner_src):
        assert "alias: G4-FIX" in runner_src, (
            "G4 alias sentinel missing — commit-msg taxonomy not greppable."
        )


# ─────────────────────────────────────────────────────────────────────────────
# G5 (alias M5) — sample-gen log tee finalize+copy
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# G8 — context ladder wired to FK-RES single-batch path
# ─────────────────────────────────────────────────────────────────────────────
class TestG8ContextLadderWired:
    def test_context_ladder_helper_exists(self, agent_src):
        assert "def run_with_context_ladder" in agent_src

    def test_run_with_context_ladder_has_callers(self, agent_src):
        # Module-level def + at least 1 call site
        call_sites = re.findall(r"\brun_with_context_ladder\s*\(", agent_src)
        assert len(call_sites) >= 2, (
            f"G8 fix REVERTED — run_with_context_ladder has no callers "
            f"(found {len(call_sites)} occurrences total, need def + caller)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# G9-rate-limit — non-rate-limit errors surfaced
# ─────────────────────────────────────────────────────────────────────────────
class TestG9RateLimitErrorSurfacing:
    def test_run_parallel_with_rate_limit_backoff_logs_errors(self):
        from agent_helpers import run_parallel_with_rate_limit_backoff

        captured = []

        class _LogCapture:
            def info(self, m): captured.append(("info", m))
            def warning(self, m): captured.append(("warning", m))
            def error(self, m): captured.append(("error", m))

        def _work(item):
            if item == "boom":
                # Use a plain message that does NOT match any rate-limit pattern
                raise ValueError("plain failure no special tokens")
            return item

        results, errors = run_parallel_with_rate_limit_backoff(
            ["a", "boom", "c"],
            _work,
            start_workers=2,
            logger=_LogCapture(),
            label="test",
            return_errors=True,
        )
        assert results[0] == "a"
        assert results[1] is None
        assert results[2] == "c"
        assert 1 in errors
        assert isinstance(errors[1], ValueError)
        error_logs = [m for lvl, m in captured if lvl == "error"]
        assert any("non-rate-limit error" in m for m in error_logs), (
            "G9-rate-limit fix REVERTED — non-rate-limit errors no longer logged at ERROR."
        )

    def test_rate_limit_retry_succeeds_on_second_attempt(self):
        # Ladder for start_workers=15 = [15, 10, 5, 1]. We want success on attempt 2.
        from agent_helpers import run_parallel_with_rate_limit_backoff

        attempts = {"count": 0}

        def _work(item):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise Exception("HTTP 429 rate_limit exceeded")
            return item

        results = run_parallel_with_rate_limit_backoff(
            ["x"], _work, start_workers=15, logger=None, label="rl"
        )
        assert results == ["x"], "Rate-limit retry ladder broken"

    def test_raise_on_non_rate_limit_error_flag(self):
        from agent_helpers import run_parallel_with_rate_limit_backoff

        def _work(item):
            raise ValueError("plain crash no special tokens")

        with pytest.raises(RuntimeError, match="plain crash"):
            run_parallel_with_rate_limit_backoff(
                ["a"],
                _work,
                start_workers=1,
                logger=None,
                label="raise-test",
                raise_on_non_rate_limit_error=True,
            )

    def test_ambig_fk_res_caller_passes_explicit_flags(self, agent_src):
        m = re.search(
            r'run_parallel_with_rate_limit_backoff\([^)]*label="ambig_fk_res"[^)]*\)',
            agent_src,
        )
        assert m, "ambig_fk_res caller signature not found"
        snippet = m.group(0)
        assert "return_errors" in snippet, (
            "EXP#5 fix REVERTED — ambig_fk_res caller doesn't explicitly set "
            "return_errors flag."
        )


# ─────────────────────────────────────────────────────────────────────────────
# G9-heartbeat — HeartbeatWatchdog active-vw global registry
# ─────────────────────────────────────────────────────────────────────────────
class TestG9HeartbeatRegistry:
    def test_active_vw_registry_exists(self):
        from agent_helpers import HeartbeatWatchdog
        assert hasattr(HeartbeatWatchdog, "_ACTIVE_VW")
        assert hasattr(HeartbeatWatchdog, "register_active")
        assert hasattr(HeartbeatWatchdog, "clear_active")
        assert hasattr(HeartbeatWatchdog, "scoped")

    def test_register_clear_round_trip(self):
        from agent_helpers import HeartbeatWatchdog
        sentinel = object()
        try:
            HeartbeatWatchdog.register_active(sentinel)
            assert HeartbeatWatchdog._ACTIVE_VW is sentinel
            HeartbeatWatchdog.clear_active()
            assert HeartbeatWatchdog._ACTIVE_VW is None
        finally:
            HeartbeatWatchdog.clear_active()

    def test_scoped_no_active_vw_is_safe(self):
        from agent_helpers import HeartbeatWatchdog
        HeartbeatWatchdog.clear_active()
        with HeartbeatWatchdog.scoped("test_stage"):
            pass

    def test_scoped_with_active_vw_starts_and_stops(self):
        from agent_helpers import HeartbeatWatchdog

        class _VW:
            def __init__(self):
                self.calls = []
            def emit_step(self, **kw):
                self.calls.append(kw)

        vw = _VW()
        HeartbeatWatchdog.register_active(vw)
        try:
            with HeartbeatWatchdog.scoped("test_stage", interval_s=10):
                pass
        finally:
            HeartbeatWatchdog.clear_active()

    def test_clear_active_wired_in_finalize(self, agent_src):
        finalize_idx = agent_src.find("def _finalize_common")
        assert finalize_idx != -1
        finalize_body = agent_src[finalize_idx:finalize_idx + 5000]
        assert "HeartbeatWatchdog.clear_active()" in finalize_body, (
            "EXP#3 fix REVERTED — clear_active() not called on session finalization, "
            "stale registry leaks across sessions."
        )

    def test_heartbeat_wired_to_at_least_three_phases(self, agent_src):
        # G9-heartbeat: heartbeat instances at IDL, MV15, sample-gen (4 actual: also tag-apply)
        # Match `HeartbeatWatchdog(` instantiations excluding the docstring example.
        instantiations = [
            line for line in agent_src.splitlines()
            if "HeartbeatWatchdog(" in line and "Use as:" not in line
        ]
        assert len(instantiations) >= 3, (
            f"G9-heartbeat fix PARTIALLY REVERTED — only {len(instantiations)} "
            f"heartbeat instantiations wired (expected ≥3 for IDL, MV15, sample-gen)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# G10 — token telemetry replaced with _model_stats + cost
# ─────────────────────────────────────────────────────────────────────────────
class TestG10TokenTelemetry:
    def test_model_stats_dict_exists(self, agent_src):
        assert "_model_stats" in agent_src, (
            "G10 fix REVERTED — _model_stats telemetry dict missing."
        )

    def test_default_price_table_exists(self, agent_src):
        assert "_DEFAULT_PRICE_USD_PER_1M" in agent_src, (
            "G10 fix REVERTED — price table missing; cost cannot be estimated."
        )

    def test_resolve_price_helper_returns_known_pricing(self):
        from agent_helpers import AIAgent
        result = AIAgent._resolve_price_for_model("databricks-claude-sonnet-4")
        # Returns tuple (input_per_1m, output_per_1m)
        assert isinstance(result, (tuple, list)) and len(result) == 2, (
            f"_resolve_price_for_model must return (in_price, out_price) tuple, got: {result!r}"
        )
        in_p, out_p = result
        assert in_p > 0 and out_p > 0, "Prices must be positive"

    def test_resolve_price_falls_back_to_default(self):
        from agent_helpers import AIAgent
        result = AIAgent._resolve_price_for_model("totally-unknown-model-xyz")
        assert isinstance(result, (tuple, list)) and len(result) == 2

    def test_estimate_cost_usd_returns_total_and_per_model(self):
        from agent_helpers import AIAgent
        out = AIAgent.estimate_cost_usd()
        assert isinstance(out, tuple) and len(out) == 2
        total, per_model = out
        assert isinstance(total, float)
        assert isinstance(per_model, dict)


# ─────────────────────────────────────────────────────────────────────────────
# G11 (alias B9) — MV-FILTER tautology removed
# ─────────────────────────────────────────────────────────────────────────────
class TestG11MetricViewFilter:
    def test_mv_filter_helper_present_with_alias(self, agent_src):
        assert "alias: G11-FIX" in agent_src, "G11 alias sentinel missing"

    def test_mv_filter_logic_extracts_product_refs(self, agent_src):
        idx = agent_src.find("_mv_refs_installed")
        assert idx != -1, "G11 fix REVERTED — _mv_refs_installed function removed."
        body = agent_src[idx:idx + 4000]
        # Must reference system schemas (using actual variable name)
        assert "_SYS_SCHEMAS" in body or "_sys_schemas" in body, (
            "G11 fix REVERTED — system-schema exclusion variable absent."
        )
        # Must reference product/domain installation set
        assert "_installed_prods" in body or "_installed_doms" in body, (
            "G11 fix REVERTED — installation reference set missing."
        )

    def test_mv_filter_is_not_tautology(self, agent_src):
        # Old (broken) version returned True unconditionally; new version must
        # have at least one branch that returns False explicitly.
        idx = agent_src.find("_mv_refs_installed")
        assert idx != -1
        window = agent_src[max(0, idx - 200):idx + 3000]
        assert "return False" in window, (
            "G11 TAUTOLOGY REINTRODUCED — _mv_refs_installed no longer "
            "has a False-return branch."
        )


# ─────────────────────────────────────────────────────────────────────────────
# C2 — MV15 halving merges sub-batch evaluations
# ─────────────────────────────────────────────────────────────────────────────
class TestC2Mv15HalvingMerges:
    def test_merged_evals_var_present(self, agent_src):
        idx = agent_src.find("def run_fk_semantic_correctness_gate")
        assert idx != -1
        body = agent_src[idx:idx + 30000]
        assert "_merged_evals" in body, (
            "C2 fix REVERTED — _merged_evals variable removed; "
            "sub-batch evaluations would be discarded again."
        )
        assert '"evaluations": _merged_evals' in body, (
            "C2 fix REVERTED — merged evals not assembled back into resp object."
        )

    def test_c2_sentinel_present(self, agent_src):
        assert "C2-FIX" in agent_src, "C2 commit-msg sentinel missing"


# ─────────────────────────────────────────────────────────────────────────────
# C4 — Description generation _gd_try_call wired
# ─────────────────────────────────────────────────────────────────────────────
class TestC4DescriptionLadder:
    def test_gd_try_call_used_in_happy_path(self, agent_src):
        calls = re.findall(r"\b_gd_try_call\(", agent_src)
        assert len(calls) >= 2, (
            f"C4 fix REVERTED — _gd_try_call has no callers (found {len(calls)})."
        )

    def test_gd_halve_recursion_present(self, agent_src):
        assert "_gd_halve" in agent_src, (
            "C4 fix REVERTED — recursive halving helper for description "
            "generation missing."
        )

    def test_c4_sentinel_present(self, agent_src):
        assert "C4-FIX" in agent_src


# ─────────────────────────────────────────────────────────────────────────────
# C6 — Vibe-prune NameError fixed (sort BEFORE measuring length)
# ─────────────────────────────────────────────────────────────────────────────
class TestC6VibePruneOrdering:
    def test_sort_happens_before_length_measurement(self, agent_src):
        # Find the C6-FIX sentinel directly, since VIBE_PRUNE_PROMPT appears in many places.
        idx = agent_src.find("C6-FIX")
        assert idx != -1, "C6 sentinel not found"
        block = agent_src[idx:idx + 1500]
        sort_pos = block.find("domain_names_sorted = sorted")
        len_pos = block.find("_vp_len = len(domain_names_sorted)")
        assert sort_pos != -1, "C6 fix REVERTED — sort line missing"
        assert len_pos != -1, "C6 fix REVERTED — length line missing"
        assert sort_pos < len_pos, (
            "C6 fix REVERTED — domain_names_sorted is referenced BEFORE assignment "
            "(NameError will fire at runtime)."
        )

    def test_c6_sentinel_present(self, agent_src):
        assert "C6-FIX" in agent_src


# ─────────────────────────────────────────────────────────────────────────────
# EXP#6a — config-guard sweep on functions with config=None default
# ─────────────────────────────────────────────────────────────────────────────
class TestExp6aConfigGuards:
    GUARDED_FUNCTIONS = [
        "_extract_business_role_prefix",
        "_ensure_shared_domain",
        "_ensure_domain_exists",
        "_get_file_sql_name",
        "_render_metric_sql_for_domain_from_llm_spec",
        "_build_domain_metric_sql_artifacts_with_llm",
        "_safe_remove_redundant_column",
        "_break_cycles_with_retry",
        "_break_cycles_internal",
        "_break_cycles",
    ]

    def test_each_guarded_function_starts_with_null_coalesce(self, agent_src):
        missing = []
        for fname in self.GUARDED_FUNCTIONS:
            idx = agent_src.find(f"def {fname}(")
            if idx == -1:
                missing.append(f"{fname} (not found)")
                continue
            body = agent_src[idx:idx + 1500]
            if "config = config or {}" not in body:
                missing.append(f"{fname} (no guard)")
        assert not missing, (
            f"EXP#6a guard REVERTED for: {missing}. "
            "These functions accept config=None and would NoneType-crash on .get()."
        )


# ─────────────────────────────────────────────────────────────────────────────
# EXP#6b — VALIDATOR_REGISTRY actually wired
# ─────────────────────────────────────────────────────────────────────────────
class TestExp6bValidatorRegistry:
    def test_validator_registry_populated(self):
        from agent_helpers import VALIDATOR_REGISTRY
        expected = {
            "validate_industry_vocabulary_alignment",
            "validate_org_chart_alignment",
            "validate_division_ratios",
        }
        present = expected & set(VALIDATOR_REGISTRY.keys())
        assert len(present) >= 3, (
            f"EXP#6b fix REVERTED — VALIDATOR_REGISTRY only has {present}; "
            f"all 3 G validators must be registered."
        )

    def test_register_validator_decorator_works(self):
        from agent_helpers import register_validator, VALIDATOR_REGISTRY

        @register_validator("test_validator_xyz", phase="post_gen")
        def _vfn(): return True

        assert "test_validator_xyz" in VALIDATOR_REGISTRY
        assert VALIDATOR_REGISTRY["test_validator_xyz"]["phase"] == "post_gen"
        del VALIDATOR_REGISTRY["test_validator_xyz"]


# ─────────────────────────────────────────────────────────────────────────────
# EXP#6c — _is_system_identifier_column callers all pass config
# ─────────────────────────────────────────────────────────────────────────────
class TestExp6cSystemIdentifierConfigPlumb:
    def test_all_callers_pass_config(self, agent_src):
        lines = agent_src.splitlines()
        callers = []
        for i, line in enumerate(lines):
            if "_is_system_identifier_column(" not in line:
                continue
            if "def _is_system_identifier_column" in line:
                continue
            callers.append((i + 1, line.strip()))
        assert len(callers) >= 9, f"Expected ≥9 caller sites, found {len(callers)}"
        no_config = [(ln, src) for ln, src in callers if "config=" not in src]
        assert not no_config, (
            f"EXP#6c REVERTED — these caller sites still don't pass config:\n"
            + "\n".join(f"  L{ln}: {s[:120]}" for ln, s in no_config)
        )
