"""Tests for v0.8.2 fixes that close the 10-failure report from the
tiny-test run (v0.8.1-failure-report.md, dated 2026-04-24).

Each fix is pinned by the mechanism it introduced, not by its `v0.8.2 P<N>`
sentinel comment: those comments were dropped during later refactors while the
mechanisms survived, so asserting on them tested the comment, not the fix.
Reverting any mechanism breaks at least one test.

Failure index <-> alias map:
    F1  -> v0.8.2 P1   /tmp scratch path -> tempfile.mkdtemp + DRY
    F2  -> v0.8.2 P2   smart_worker_loop accepts wrong domain name
    F3  -> v0.8.2 P3   pool-spec assembly Decimal -> double
    F4  -> v0.8.2 P4   shrink prompt forbids siloed tables
    F5  -> v0.8.2 P5   update_job_tags short-circuits on NotFound
    F6  -> v0.8.2 P6   VIBE_CREATE_NEXT_PROMPT brace escaping
    F7  -> v0.8.2 P7   Job Launch Gate blocks on child run
    F8  -> v0.8.2 P8   _resolve_managed_location validates accessibility
    F10 -> v0.8.2 P10  metric-view install count cross-validation
"""
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


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
def helpers():
    import agent_helpers as ah
    return ah


# =====================================================================
# F6 -- v0.8.2 P6 -- prompt-brace-escape
# =====================================================================

class TestF6PromptBraceEscape:
    def test_vibe_create_next_prompt_renders_without_keyerror(self, helpers):
        templates = helpers.PROMPT_TEMPLATES
        assert "VIBE_CREATE_NEXT_PROMPT" in templates
        template = templates["VIBE_CREATE_NEXT_PROMPT"]
        # Capture every {placeholder} that needs to be filled and synthesize values
        # Same regex used by smoke_render_all_prompts at runtime
        placeholder_re = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})")
        placeholders = set(placeholder_re.findall(template))
        synthetic = {p: f"<<{p}>>" for p in placeholders}
        # The pre-fix template would raise KeyError '0,62' here -- post-fix MUST render.
        try:
            rendered = template.format(**synthetic)
        except KeyError as e:
            pytest.fail(f"VIBE_CREATE_NEXT_PROMPT KeyError on render: {e}")
        # And the post-render output MUST contain the literal `{0,62}` (the regex
        # bound), proving the double-brace escape unfolded correctly.
        assert "{0,62}" in rendered, (
            "Post-render output must contain literal '{0,62}' (regex bound) "
            "after brace unescape. If absent, the escape was wrong."
        )

    def test_smoke_render_all_prompts_succeeds(self, helpers):
        helpers.smoke_render_all_prompts(helpers.PROMPT_TEMPLATES)

    def test_the_regex_bound_is_escaped_in_the_template_source(self, agent_src):
        assert "{{0,62}}" in agent_src, (
            "The regex bound inside VIBE_CREATE_NEXT_PROMPT must stay double-braced "
            "in the notebook source, or .format() raises KeyError '0,62' again"
        )


# =====================================================================
# F5 -- v0.8.2 P5 -- jobtags-skip-deleted-job
# =====================================================================

class TestF5JobTagsSkipDeleted:
    def test_update_job_tags_short_circuits_on_get_failure(self, agent_src):
        """The fix moves jobs.get OUT of try/except so NotFound returns early."""
        # Find the update_job_tags function body
        m = re.search(
            r"def update_job_tags\(updated_tags\):.*?(?=\n    @staticmethod|\n    def [a-zA-Z_])",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate update_job_tags"
        body = m.group(0)
        # The jobs.get call must sit OUTSIDE the block that swallows SDK errors, so a
        # deleted job returns early instead of falling through to jobs.update.
        assert re.search(r"except Exception as _get_err:.*?return _result", body, re.DOTALL), (
            "the jobs.get failure path must return early rather than continue to update"
        )
        # Must check existence before update -- presence of the early-return path
        assert "_job_exists" in body or "JobNotFoundException" in body or "does not exist" in body.lower(), (
            "update_job_tags must explicitly verify the job exists before calling jobs.update"
        )


# =====================================================================
# F2 -- v0.8.2 P2 -- domain-name-mismatch-critical
# =====================================================================

class TestF2DomainNameMismatchCritical:
    def test_smart_worker_loop_classifies_domain_name_mismatch_as_critical(self, agent_src):
        # The critical_error_patterns list must contain 'domain name mismatch'
        # (case-insensitive substring match used by the loop)
        m = re.search(
            r"critical_error_patterns\s*=\s*\[(.*?)\]",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate critical_error_patterns list"
        patterns_block = m.group(1).lower()
        assert "domain name mismatch" in patterns_block, (
            "'domain name mismatch' MUST be in critical_error_patterns so the soft-accept "
            "path at end of smart_worker_loop does NOT bypass it."
        )

    def test_domain_name_mismatch_is_not_reachable_by_the_soft_accept_path(self, agent_src):
        m = re.search(r"critical_error_patterns\s*=\s*\[(.*?)\]", agent_src, re.DOTALL)
        assert m, "Could not locate critical_error_patterns list"
        assert len(re.findall(r"['\"]", m.group(1))) >= 2, (
            "critical_error_patterns must not be emptied; an empty list routes every "
            "validation error through the soft-accept path"
        )


# =====================================================================
# F1 -- v0.8.2 P1 -- scratch-path-tempfile
# =====================================================================

class TestF1ScratchPathTempfile:
    def test_no_hardcoded_tmp_model_data_default(self, agent_src):
        # The pre-fix string was f'/tmp/{sql_name}_model_data/{run_token}'.
        # After fix, every occurrence MUST go through the new helper.
        assert '/tmp/{sql_name}_model_data/{run_token}' not in agent_src, (
            "Hardcoded /tmp/{sql_name}_model_data fallback must not appear -- "
            "use _resolve_business_scratch_path() helper"
        )

    def test_helper_present(self, agent_src):
        assert "_resolve_business_scratch_path" in agent_src, (
            "The DRY helper _resolve_business_scratch_path must exist"
        )

    def test_helper_uses_tempfile(self, agent_src):
        m = re.search(
            r"def _resolve_business_scratch_path\(.*?\):.*?(?=\ndef [a-zA-Z_])",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate _resolve_business_scratch_path body"
        body = m.group(0)
        assert "tempfile" in body and "mkdtemp" in body, (
            "Helper must use tempfile.mkdtemp() for guaranteed-writable scratch dir"
        )

    def test_callers_use_helper(self, agent_src):
        # Both former call sites at L53072 + L56859 must now call the helper.
        # Count occurrences of the helper invocation.
        helper_calls = len(re.findall(r"_resolve_business_scratch_path\s*\(", agent_src))
        assert helper_calls >= 3, (
            f"Expected >=3 references (def + 2 call sites), got {helper_calls}"
        )

    def test_helper_callable(self, helpers):
        # Module-level function must be importable and produce a writable path
        assert hasattr(helpers, "_resolve_business_scratch_path"), (
            "_resolve_business_scratch_path must be a module-level function"
        )
        path = helpers._resolve_business_scratch_path("test_sql_name", "abc123")
        import os
        assert path and os.path.isdir(path), f"Helper must return an existing dir, got: {path}"
        # Must be writable
        test_file = os.path.join(path, "write_test.txt")
        with open(test_file, "w") as f:
            f.write("ok")
        assert os.path.exists(test_file)
        # Cleanup
        try:
            import shutil
            shutil.rmtree(path)
        except Exception:
            pass


# =====================================================================
# F8 -- v0.8.2 P8 -- managed-location-accessibility-check
# =====================================================================

class TestF8ManagedLocationAccessibility:
    def test_p8_alias_present(self, agent_src):
        assert "v0.8.2 P8" in agent_src
        assert "managed-location-accessibility-check" in agent_src

    def test_validate_storage_accessible_helper_exists(self, agent_src):
        assert "def _validate_storage_accessible(" in agent_src

    def test_resolve_managed_location_validates_accessibility(self, agent_src):
        m = re.search(
            r"def _resolve_managed_location\(.*?\n    return \"\"",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate _resolve_managed_location"
        body = m.group(0)
        assert "_validate_storage_accessible" in body, (
            "_resolve_managed_location must call _validate_storage_accessible before "
            "returning a borrowed storage_root"
        )

    def test_ensure_catalog_falls_back_on_permission_denied(self, agent_src):
        m = re.search(
            r"def _ensure_catalog_exists\(.*?\n\n\ndef ",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate _ensure_catalog_exists"
        body = m.group(0)
        assert "permission_denied" in body.lower() and "bare CREATE CATALOG" in body, (
            "_ensure_catalog_exists must handle PERMISSION_DENIED by retrying with "
            "bare CREATE CATALOG (no MANAGED LOCATION) so Default Storage takes over"
        )

    def test_validate_storage_accessible_returns_false_on_permission_denied(self, helpers, monkeypatch):
        # Build a fake dbutils that raises a PERMISSION_DENIED-flavoured exception
        class _FakeFs:
            def ls(self, path):
                raise Exception("PERMISSION_DENIED: External Location 'x' is not accessible")
        class _FakeDbu:
            fs = _FakeFs()
        # Inject into the module's globals so the helper picks it up
        helpers_module_globals = vars(helpers)
        helpers_module_globals['dbutils'] = _FakeDbu()
        try:
            assert helpers._validate_storage_accessible("abfss://foo@bar.dfs.core.windows.net/") is False
        finally:
            helpers_module_globals.pop('dbutils', None)

    def test_validate_storage_accessible_true_on_unknown_error(self, helpers):
        # Unknown error -> conservative TRUE (don't block on inability-to-probe)
        class _FakeFs:
            def ls(self, path):
                raise Exception("some-unrelated-network-blip")
        class _FakeDbu:
            fs = _FakeFs()
        helpers_module_globals = vars(helpers)
        helpers_module_globals['dbutils'] = _FakeDbu()
        try:
            assert helpers._validate_storage_accessible("abfss://foo@bar.dfs.core.windows.net/") is True
        finally:
            helpers_module_globals.pop('dbutils', None)

    def test_validate_storage_accessible_true_on_success(self, helpers):
        class _FakeFs:
            def ls(self, path):
                return []
        class _FakeDbu:
            fs = _FakeFs()
        helpers_module_globals = vars(helpers)
        helpers_module_globals['dbutils'] = _FakeDbu()
        try:
            assert helpers._validate_storage_accessible("abfss://foo@bar.dfs.core.windows.net/") is True
        finally:
            helpers_module_globals.pop('dbutils', None)

    def test_validate_storage_accessible_false_on_empty(self, helpers):
        assert helpers._validate_storage_accessible("") is False
        assert helpers._validate_storage_accessible(None) is False


# =====================================================================
# F7 -- v0.8.2 P7 -- job-launch-gate-blocks-on-child
# =====================================================================

class TestF7JobLaunchGateBlocksOnChild:
    def test_wait_for_run_terminal_helper_exists(self, agent_src):
        assert "def wait_for_run_terminal(" in agent_src

    def test_wait_helper_uses_get_run(self, agent_src):
        m = re.search(
            r"def wait_for_run_terminal\(.*?(?=\n    @staticmethod|\n    def [a-zA-Z_])",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate wait_for_run_terminal body"
        body = m.group(0)
        assert "get_run" in body, "wait_for_run_terminal must call w.jobs.get_run to poll"
        assert "TERMINATED" in body, "wait_for_run_terminal must check life_cycle_state == TERMINATED"
        assert "result_state" in body, "wait_for_run_terminal must read result_state"
        assert "TimeoutError" in body, "wait_for_run_terminal must enforce a timeout"

    def test_launch_gate_invokes_wait_helper(self, agent_src):
        # Find the Job Launch Gate block and confirm it calls wait_for_run_terminal
        m = re.search(
            r"Job Launch Gate.*?End Job Launch Gate",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate Job Launch Gate block"
        body = m.group(0)
        assert "wait_for_run_terminal" in body, (
            "Job Launch Gate must invoke wait_for_run_terminal after a successful launch"
        )
        # Must propagate child failure -- raise on FAILED/TIMEDOUT/CANCELED
        assert "FAILED" in body and ("raise" in body), (
            "Launch gate must raise on child terminal FAILED/TIMEDOUT/CANCELED"
        )


# =====================================================================
# F4 -- v0.8.2 P4 -- shrink-forbids-siloed
# =====================================================================

class TestF4ShrinkForbidsSiloed:
    def test_p4_alias_present(self, agent_src):
        assert "v0.8.2 P4" in agent_src
        assert "shrink-forbids-siloed" in agent_src

    def test_shrink_prompt_mentions_no_siloed(self, agent_src):
        m = re.search(
            r'PROMPT_TEMPLATES\[\"RESIZE_SHRINK_DOMAIN_PROMPT\"\]\s*=\s*r\"\"\"(.+?)\"\"\"',
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate RESIZE_SHRINK_DOMAIN_PROMPT"
        body = m.group(1).lower()
        assert "siloed" in body or "silos" in body, (
            "SHRINK prompt MUST instruct the LLM not to leave any siloed tables"
        )

    def test_silo_validator_helper_exists(self, agent_src):
        assert "def _detect_post_shrink_silos(" in agent_src

    def test_silo_validator_called_in_shrink_path(self, agent_src):
        assert "_detect_post_shrink_silos(" in agent_src
        # Specifically must be called inside the shrink direction handler
        m = re.search(
            r'if direction == \"shrink\":.*?_detect_post_shrink_silos',
            agent_src,
            re.DOTALL,
        )
        assert m, "Silo validator must be invoked inside the shrink direction handler"

    def test_silo_helper_detects_silo(self, helpers):
        # Three tables, FK chain: A -> B; C is siloed (no FK in or out)
        attrs = [
            {"domain": "d1", "product": "a", "attribute": "id"},
            {"domain": "d1", "product": "a", "attribute": "b_id", "foreign_key_to": "d1.b.id"},
            {"domain": "d1", "product": "b", "attribute": "id"},
            {"domain": "d1", "product": "c", "attribute": "id"},
        ]
        silos = helpers._detect_post_shrink_silos(["a", "b", "c"], attrs)
        assert silos == ["c"], f"Expected ['c'] silo, got {silos}"

    def test_silo_helper_no_silos_when_chain_intact(self, helpers):
        attrs = [
            {"domain": "d1", "product": "a", "attribute": "id"},
            {"domain": "d1", "product": "a", "attribute": "b_id", "foreign_key_to": "d1.b.id"},
            {"domain": "d1", "product": "b", "attribute": "id"},
        ]
        silos = helpers._detect_post_shrink_silos(["a", "b"], attrs)
        assert silos == []

    def test_silo_helper_ignores_self_fk(self, helpers):
        # Self-reference must not count as a connection
        attrs = [
            {"domain": "d1", "product": "x", "attribute": "id"},
            {"domain": "d1", "product": "x", "attribute": "parent_id", "foreign_key_to": "d1.x.id"},
        ]
        silos = helpers._detect_post_shrink_silos(["x"], attrs)
        assert silos == ["x"], "self-FK must NOT exempt a table from silo classification"

    def test_silo_helper_skips_fk_to_removed(self, helpers):
        # FK target NOT in keep set must NOT exempt the source
        attrs = [
            {"domain": "d1", "product": "a", "attribute": "id"},
            {"domain": "d1", "product": "a", "attribute": "z_id", "foreign_key_to": "d2.z.id"},
        ]
        silos = helpers._detect_post_shrink_silos(["a"], attrs)
        assert silos == ["a"], "FK to a removed table must NOT save the survivor from silo"

    def test_silo_helper_handles_empty_inputs(self, helpers):
        assert helpers._detect_post_shrink_silos([], []) == []
        assert helpers._detect_post_shrink_silos(None, None) == []
        assert helpers._detect_post_shrink_silos(["a"], None) == []


# =====================================================================
# F10 -- v0.8.2 P10 -- mv-install-count-validation
# =====================================================================

class TestF10MetricViewInstallCountValidation:
    def test_count_audit_helper_exists(self, agent_src):
        assert "def _validate_metric_view_count(" in agent_src

    def test_count_audit_helper_called_in_install_path(self, agent_src):
        m = re.search(
            r"def step_apply_metric_views\(.*?\n\ndef ",
            agent_src,
            re.DOTALL,
        )
        assert m, "Could not locate step_apply_metric_views"
        body = m.group(0)
        assert "_validate_metric_view_count(" in body, (
            "step_apply_metric_views must invoke _validate_metric_view_count"
        )

    def test_count_audit_returns_structured(self, helpers):
        audit = helpers._validate_metric_view_count(13, 8, 0, min_required_fraction=0.5)
        assert audit['declared_metric_view_count'] == 13
        assert audit['filter_dropped_count'] == 8
        assert audit['exec_failed_count'] == 0
        assert audit['installed_count'] == 5
        assert abs(audit['survival_fraction'] - (5 / 13)) < 1e-6
        assert audit['below_threshold'] is True
        assert "[MV-COUNT-AUDIT]" in audit['summary']
        assert "BELOW" in audit['summary']

    def test_count_audit_passes_threshold(self, helpers):
        audit = helpers._validate_metric_view_count(10, 1, 1, min_required_fraction=0.5)
        assert audit['installed_count'] == 8
        assert audit['below_threshold'] is False
        assert "OK" in audit['summary']

    def test_count_audit_handles_zero_declared(self, helpers):
        audit = helpers._validate_metric_view_count(0, 0, 0)
        assert audit['installed_count'] == 0
        assert audit['below_threshold'] is False
        assert audit['survival_fraction'] == 1.0

    def test_count_audit_clamps_negative_install(self, helpers):
        # If filter_dropped + exec_failed exceeds declared (shouldn't happen but be defensive)
        audit = helpers._validate_metric_view_count(5, 4, 4)
        assert audit['installed_count'] == 0  # clamped, not negative

    def test_filter_logs_drop_reason_per_view(self, agent_src):
        # The MV filter must report WHY each MV was dropped (for root-cause hunting)
        m = re.search(
            r"def _mv_refs_installed\(stmt\):.*?return True, ''",
            agent_src,
            re.DOTALL,
        )
        assert m, "_mv_refs_installed must return (bool, reason) tuple"
        body = m.group(0)
        assert "return False, f" in body, (
            "_mv_refs_installed must return a reason string when dropping a view"
        )
