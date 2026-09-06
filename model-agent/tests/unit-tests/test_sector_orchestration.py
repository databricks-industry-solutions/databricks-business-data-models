import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent.parent
SECTORS_DIR = REPO / "runner" / "industry-sectors"
ALL_INDUSTRIES = REPO / "runner" / "all-industries.json"
ORCHESTRATOR = REPO / "runner" / "orchestrate_sectors.py"
RUNNER_NB = REPO / "runner" / "vibe_runner.ipynb"


SECTOR_FILE_ORDER = [
    "agriculture.json",
    "real_estate_and_professional_services.json",
    "financial_services.json",
    "healthcare_and_life_sciences.json",
    "energy_and_utilities.json",
    "travel_transport_logistics.json",
    "public_sector_education_nonprofit.json",
    "communications_media_entertainment.json",
    "manufacturing.json",
    "retail_and_consumer_goods.json",
]


EXPECTED_TOTAL_INDUSTRIES = 40
EXPECTED_GLOBAL_VOLUME = "/Volumes/_root/default/root_vol"


def _all_sector_payloads():
    payloads = {}
    for fname in SECTOR_FILE_ORDER:
        p = SECTORS_DIR / fname
        payloads[fname] = json.loads(p.read_text())
    return payloads


def test_all_10_sector_files_exist():
    for fname in SECTOR_FILE_ORDER:
        p = SECTORS_DIR / fname
        assert p.exists(), f"sector file missing: {p}"


def test_total_industries_is_40():
    payloads = _all_sector_payloads()
    total = sum(len(p["businesses"]) for p in payloads.values())
    assert total == EXPECTED_TOTAL_INDUSTRIES, f"total industries = {total}, expected {EXPECTED_TOTAL_INDUSTRIES}"


def test_no_industry_appears_in_two_sector_files():
    payloads = _all_sector_payloads()
    seen = {}
    for fname, p in payloads.items():
        for b in p["businesses"]:
            assert b["name"] not in seen, (
                f"industry '{b['name']}' appears in BOTH {seen[b['name']]} and {fname}"
            )
            seen[b["name"]] = fname


def test_every_industry_name_exists_in_all_industries_json():
    src = json.loads(ALL_INDUSTRIES.read_text())
    src_names = {b["name"] for b in src["businesses"]}
    payloads = _all_sector_payloads()
    for fname, p in payloads.items():
        for b in p["businesses"]:
            assert b["name"] in src_names, (
                f"industry '{b['name']}' in {fname} not present in all-industries.json"
            )


def test_descriptions_match_all_industries_json():
    src = json.loads(ALL_INDUSTRIES.read_text())
    src_by_name = {b["name"]: b["description"] for b in src["businesses"]}
    payloads = _all_sector_payloads()
    for fname, p in payloads.items():
        for b in p["businesses"]:
            assert b["description"] == src_by_name[b["name"]], (
                f"description for '{b['name']}' in {fname} drifted from all-industries.json"
            )


def test_every_sector_has_global_collection_volume_widget_value():
    payloads = _all_sector_payloads()
    for fname, p in payloads.items():
        wv = p["widget_values"]
        assert "global_collection_volume" in wv, f"missing global_collection_volume in {fname}"
        assert wv["global_collection_volume"] == EXPECTED_GLOBAL_VOLUME, (
            f"global_collection_volume mismatch in {fname}: got {wv['global_collection_volume']!r}"
        )


def test_every_sector_widget_values_has_19_canonical_keys_plus_global_collection_volume():
    src = json.loads(ALL_INDUSTRIES.read_text())
    canonical_keys = set(src["widget_values"].keys())
    payloads = _all_sector_payloads()
    for fname, p in payloads.items():
        wv = p["widget_values"]
        missing = canonical_keys - set(wv.keys())
        assert not missing, f"sector {fname} missing canonical widget keys: {missing}"
        assert "global_collection_volume" in wv, f"sector {fname} missing global_collection_volume"


def test_sector_file_order_is_smallest_to_largest():
    payloads = _all_sector_payloads()
    sizes = [(fname, len(payloads[fname]["businesses"])) for fname in SECTOR_FILE_ORDER]
    for i in range(1, len(sizes)):
        assert sizes[i][1] >= sizes[i - 1][1], (
            f"sector order not non-decreasing at index {i}: "
            f"{sizes[i-1]} (size={sizes[i-1][1]}) -> {sizes[i]} (size={sizes[i][1]})"
        )


def test_runner_notebook_has_mirror_helper_and_call_site():
    nb = json.loads(RUNNER_NB.read_text())
    src = "".join(nb["cells"][1].get("source", []))
    assert "def _mirror_industry_to_global_volume(" in src, (
        "runner missing _mirror_industry_to_global_volume helper"
    )
    assert "[global-collection-volume FIRED]" in src, (
        "runner missing [global-collection-volume FIRED] sentinel log"
    )
    assert "_gcv_stats = _mirror_industry_to_global_volume(" in src, (
        "runner missing call site for _mirror_industry_to_global_volume"
    )
    assert "global-collection-volume-manifest" in src, (
        "runner missing manifest alias"
    )


def test_runner_notebook_call_site_runs_before_drop_catalog():
    nb = json.loads(RUNNER_NB.read_text())
    src = "".join(nb["cells"][1].get("source", []))
    call_idx = src.find("_gcv_stats = _mirror_industry_to_global_volume(")
    drop_idx = src.find("Dropping staging catalog...")
    assert call_idx >= 0 and drop_idx >= 0
    assert call_idx < drop_idx, (
        "_mirror_industry_to_global_volume call site MUST run before drop_catalog(staging) "
        "or the staging vol_root will be gone before the copy"
    )


def test_orchestrator_script_imports_and_help_runs():
    import subprocess
    p = subprocess.run(
        ["python3", str(ORCHESTRATOR), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert p.returncode == 0, f"orchestrator --help failed: {p.stderr[:500]}"
    assert "--profile" in p.stdout
    assert "--global-volume" in p.stdout
    assert "--dry-preflight" in p.stdout


def test_orchestrator_constants_match_user_directives():
    src = ORCHESTRATOR.read_text()
    assert 'DEFAULT_PROFILE = "<profile>"' in src
    assert 'DEFAULT_GLOBAL_VOLUME = "/Volumes/_root/default/root_vol"' in src
    assert 'DEFAULT_RUNNER_PATH = "/Users/user@example.com/vibe_runner_v71"' in src
    expected_block = "\n".join([f'    "{f}",' for f in SECTOR_FILE_ORDER])
    assert expected_block in src, (
        "orchestrator SECTOR_FILES_ORDER must list files smallest-to-largest exactly as test expects"
    )


def test_orchestrator_pulse_interval_is_10_minutes():
    src = ORCHESTRATOR.read_text()
    assert "PULSE_INTERVAL_S = 600" in src, "pulse cadence must be 10 minutes (per user directive 2026-04-30)"


def test_orchestrator_sector_timeout_is_14h():
    """SUPERSEDED by user directive 2026-05-18: "set timeout is always 15hrs for all jobs
    in all workflows". The v0.7.5 global is 15 * 3600 = 54000s. Function name kept for
    git-blame continuity. See test_orchestrator_sector_timeout_is_15h_global below."""
    src = ORCHESTRATOR.read_text()
    assert "SECTOR_TIMEOUT_S = 15 * 3600" in src, (
        "SECTOR_TIMEOUT_S MUST be 15 * 3600 (54000s) per user directive 2026-05-18. "
        'Setting timeout to "15hrs for all jobs in all workflows" supersedes earlier 14h/36h caps.'
    )


def test_orchestrator_job_spec_has_both_task_and_job_level_timeout():
    src = ORCHESTRATOR.read_text()
    create_fn = src.split("def find_or_create_job", 1)[1].split("\ndef ", 1)[0]
    assert '"timeout_seconds": SECTOR_TIMEOUT_S' in create_fn, (
        "find_or_create_job spec MUST set timeout_seconds: SECTOR_TIMEOUT_S "
        "(per user directive 2026-05-01: 'make the timeout 14hr for all tasks and jobs')"
    )
    timeout_lines = [l for l in create_fn.splitlines() if '"timeout_seconds": SECTOR_TIMEOUT_S' in l]
    assert len(timeout_lines) >= 2, (
        f"job spec MUST set timeout_seconds at BOTH job-level (top-level settings) AND "
        f"task-level (inside tasks[]). Found {len(timeout_lines)} occurrence(s); need >= 2. "
        "Without job-level timeout, the per-task 14h still risks Databricks-side default job timeout."
    )


def test_orchestrator_uploads_create_parent_dir():
    src = ORCHESTRATOR.read_text()
    upload_fn = src.split("def upload_sector_to_volume", 1)[1].split("\ndef ", 1)[0]
    assert '"fs", "mkdir"' in upload_fn, (
        "upload_sector_to_volume must mkdir the volume subdir before cp "
        "(databricks fs cp does NOT auto-create parents — caught in 2026-04-30 hot run)"
    )
    assert "RESOURCE_ALREADY_EXISTS" in upload_fn or "already exists" in upload_fn.lower(), (
        "mkdir must tolerate already-exists so reruns don't crash"
    )


def test_orchestrator_preflight_creates_sectors_subdir():
    src = ORCHESTRATOR.read_text()
    preflight_fn = src.split("def preflight", 1)[1].split("\ndef ", 1)[0]
    assert "_sectors" in preflight_fn and '"fs", "mkdir"' in preflight_fn, (
        "preflight must mkdir the _sectors subdir up-front so the first sector upload doesn't fail"
    )


def test_orchestrator_submit_uses_no_wait():
    src = ORCHESTRATOR.read_text()
    submit_fn = src.split("def submit_sector_run", 1)[1].split("\ndef ", 1)[0]
    assert '"--no-wait"' in submit_fn, (
        "submit_sector_run MUST pass --no-wait to `databricks jobs run-now` "
        "(per CLAUDE.md §10.11.2 GOTCHA C — without --no-wait the CLI blocks for the "
        "full run duration, defeating the orchestrator's polling loop)"
    )


def test_orchestrator_preflight_kills_orphan_child_runs():
    """Behavioural contract for orphan detection (logic now lives in helper).

    Hoisted out of preflight() into kill_orphan_pipeline_runs() so it can ALSO
    be called inside the retry loop (root-cause fix for 2026-05-02 16:46 UTC
    duplicate Staffing HR run incident — see test_process_sector_kills_orphans*).
    """
    src = ORCHESTRATOR.read_text()
    helper_body = src.split("def kill_orphan_pipeline_runs(", 1)[1].split("\ndef ", 1)[0]
    assert "ORPHAN-DETECTED" in helper_body, (
        "helper MUST detect orphan dbx_vibe_*_pipeline_* child runs"
    )
    assert "dbx_vibe_" in helper_body and "_pipeline_" in helper_body, (
        "orphan detector MUST match the runner's child-job naming pattern"
    )
    assert '"jobs", "cancel-run"' in helper_body, (
        "helper MUST actually cancel detected orphans, not just warn"
    )
    assert "creator_user_name" in helper_body or "creator ==" in helper_body, (
        "orphan detector MUST scope to current-user-owned runs (per §12 ownership rule)"
    )
    assert "CATALOG-DROP RULE" in helper_body or "§12" in helper_body, (
        "orphan cancellation MUST log §12 authorisation rationale"
    )

    preflight_fn = src.split("def preflight(", 1)[1].split("\ndef ", 1)[0]
    assert "kill_orphan_pipeline_runs(" in preflight_fn, (
        "preflight() MUST delegate to the shared helper (DRY)"
    )


def test_orchestrator_supports_kill_switch():
    src = ORCHESTRATOR.read_text()
    assert 'KILL_FILE_NAME = "_kill.json"' in src
    assert "def kill_switch_present(" in src
    assert "kill_switch_present(args.profile" in src or "kill_switch_present(" in src


def test_orchestrator_supports_one_retry_on_failure():
    src = ORCHESTRATOR.read_text()
    assert "retrying" in src and "failed industries one-by-one" in src
    assert "build_single_industry_payload" in src


def test_sync_to_repo_module_exists():
    p = REPO / "runner" / "sync_to_repo.py"
    assert p.exists(), "runner/sync_to_repo.py must exist (post-sector repo-push hook)"


def test_sync_to_repo_exposes_public_api():
    src = (REPO / "runner" / "sync_to_repo.py").read_text()
    assert "def sync_completed_industries(" in src, (
        "sync_to_repo must expose sync_completed_industries(...) for the orchestrator hook"
    )
    assert "DEFAULT_REPO_PATH" in src and "vibe-business-data-models" in src, (
        "sync_to_repo must hard-default to amralieg/vibe-business-data-models repo path"
    )
    assert "DEFAULT_WORKSPACE_ROOT" in src and "vibe_runner_models" in src, (
        "sync_to_repo must default to /Users/<user>/vibe_runner_models workspace folder "
        "(matches what the runner notebook writes per industry)"
    )


def test_sync_to_repo_uses_workspace_export_dir():
    src = (REPO / "runner" / "sync_to_repo.py").read_text()
    assert '"workspace", "export-dir"' in src, (
        "sync_to_repo MUST use 'databricks workspace export-dir' to mirror the entire "
        "industry tree (readme.md + ecm_v1/* + mvm_v1/*) into the local repo"
    )


def test_sync_to_repo_skips_already_present_industries():
    src = (REPO / "runner" / "sync_to_repo.py").read_text()
    assert "skipped_existing" in src, (
        "sync hook MUST skip industries already present in the local repo to keep the "
        "operation idempotent across orchestrator restarts (multiple sectors completing across runs)"
    )
    assert "os.path.isdir(local)" in src or "os.path.isdir(\n        local" in src or "isdir(local)" in src, (
        "sync hook must check os.path.isdir on the local industry folder before re-exporting"
    )


def test_sync_to_repo_commit_message_includes_counts():
    src = (REPO / "runner" / "sync_to_repo.py").read_text()
    assert "_extract_counts(" in src, (
        "commit message must include D/P/A/MV counts so the audit log shows scope at a glance"
    )
    assert "Co-authored-by: Isaac" in src, (
        "every auto-pushed commit must credit Isaac per repo convention"
    )


def test_sync_to_repo_pushes_to_origin_main():
    src = (REPO / "runner" / "sync_to_repo.py").read_text()
    assert '"git", "-C", repo_path, "push", "origin", branch' in src, (
        "sync hook MUST push to origin/<branch> after each industry commit so the repo "
        "is updated within ~1 min of each industry completing"
    )


def test_sync_to_repo_never_raises_for_orchestrator():
    src = (REPO / "runner" / "sync_to_repo.py").read_text()
    assert "result = {\"synced\": [], \"skipped_existing\": [], \"failed\": [], \"error\": None}" in src, (
        "sync_completed_industries MUST return a structured result dict on every path "
        "(success, partial failure, total failure) so the orchestrator can log without raising"
    )
    fn_body = src.split("def sync_completed_industries(", 1)[1]
    assert "return result" in fn_body, "sync_completed_industries must end by returning the result dict"


def test_orchestrator_calls_sync_to_repo_after_sector():
    src = ORCHESTRATOR.read_text()
    proc_fn = src.split("def process_sector(", 1)[1].split("\ndef ", 1)[0]
    assert "sync_to_repo" in proc_fn, (
        "process_sector MUST import the sync_to_repo module after a sector terminates so "
        "completed industries are pushed to vibe-business-data-models within seconds"
    )
    assert "sync_completed_industries(" in proc_fn, (
        "process_sector MUST call sync_completed_industries(...) post-sector"
    )
    assert "industry_allowlist=green_industries" in proc_fn, (
        "the sync call MUST pass the just-completed green industries as an allowlist so "
        "we don't accidentally re-export industries from other sessions"
    )
    assert "[repo-sync FIRED]" in proc_fn, (
        "post-sector pulse MUST log a [repo-sync FIRED] sentinel for §10.7 grep verification"
    )


def test_orchestrator_repo_sync_failure_is_non_fatal():
    src = ORCHESTRATOR.read_text()
    proc_fn = src.split("def process_sector(", 1)[1].split("\ndef ", 1)[0]
    sync_block = proc_fn.split("[repo-sync FIRED]", 1)[1] if "[repo-sync FIRED]" in proc_fn else ""
    assert "try:" in sync_block and "except Exception" in sync_block, (
        "the orchestrator's sync call MUST be wrapped in try/except so a git/network/auth "
        "error in the hook never blocks the next sector"
    )


def test_orchestrator_has_runner_notebook_sha_helper():
    src = ORCHESTRATOR.read_text()
    assert "def _runner_notebook_sha(" in src, (
        "orchestrator MUST expose _runner_notebook_sha(profile, runner_path) helper that "
        "exports the deployed runner notebook and returns SHA-256 — needed for §11.6 stale-import gate"
    )
    assert "hashlib.sha256" in src, (
        "_runner_notebook_sha must hash with SHA-256 (collision-resistant; sufficient for change detection)"
    )
    assert '"workspace", "export"' in src, (
        "the helper MUST call 'databricks workspace export' to obtain the live deployed notebook bytes"
    )


def test_orchestrator_runner_sha_helper_returns_none_on_failure():
    src = ORCHESTRATOR.read_text()
    fn_body = src.split("def _runner_notebook_sha(", 1)[1].split("\ndef ", 1)[0]
    assert "return None" in fn_body, (
        "_runner_notebook_sha MUST return None on subprocess failure / timeout / non-zero exit "
        "so the orchestrator's safety gate degrades gracefully without ever raising"
    )
    assert "except Exception" in fn_body, (
        "_runner_notebook_sha MUST swallow all exceptions and return None — this is a safety "
        "check, not a critical-path operation; raising would block legitimate sector submissions"
    )


def test_orchestrator_has_assert_runner_fresh_gate():
    src = ORCHESTRATOR.read_text()
    assert "def assert_runner_fresh(" in src, (
        "orchestrator MUST expose assert_runner_fresh(...) — the §11.6 stale-import gate "
        "called before each sector submission"
    )
    fn_body = src.split("def assert_runner_fresh(", 1)[1].split("\ndef ", 1)[0]
    assert "stale-runner-detected FIRED" in fn_body, (
        "stale-runner gate MUST emit the [stale-runner-detected FIRED] sentinel for §10.7 "
        "deployed-archive grep verification (this is the alias the auditor will search for)"
    )
    assert "startup_sha" in fn_body and "current_sha" in fn_body, (
        "the gate MUST log BOTH the startup SHA and the current SHA so the user can see "
        "what changed and when"
    )


def test_orchestrator_main_captures_startup_runner_sha():
    src = ORCHESTRATOR.read_text()
    main_body = src.split("def main():", 1)[1]
    assert "startup_runner_sha = _runner_notebook_sha(" in main_body, (
        "main() MUST capture the startup runner SHA AFTER find_or_create_job (when the runner_path "
        "is finalized) and BEFORE the sector loop — this snapshot is the §11.6 baseline"
    )
    assert "stale-runner-startup-sha" in main_body, (
        "main() MUST log the startup-sha alias for grep-verification of the §11.6 deploy"
    )


def test_orchestrator_sector_loop_calls_assert_runner_fresh():
    src = ORCHESTRATOR.read_text()
    main_body = src.split("def main():", 1)[1]
    loop_body = main_body.split("for spath in sector_paths:", 1)[1]
    assert "assert_runner_fresh(" in loop_body, (
        "the per-sector loop MUST call assert_runner_fresh(...) BEFORE process_sector(...) "
        "so a mid-loop runner re-deploy aborts the orchestrator instead of submitting a stale-DAG sector"
    )
    assert "sys.exit(4)" in loop_body, (
        "on stale-runner detection the orchestrator MUST exit with code 4 (distinct from "
        "preflight=3 / sectors-missing=2 / generic=1) so a wrapper / cron can re-launch"
    )


def test_agent_version_constant_unchanged_at_071():
    """v0.7.1 historical invariant; relaxed to >=0.7.1 with single-digit semver
    so later patches (v0.7.2, v0.7.3, v0.7.4, v0.7.5+) don't break it. Function
    name kept for git-blame continuity."""
    nb = json.loads(open(REPO / "agent" / "dbx_vibe_modelling_agent.ipynb").read())
    cell0_src = "".join(nb["cells"][0].get("source", [])) if nb["cells"][0].get("cell_type") == "code" else ""
    cell1_src = "".join(nb["cells"][1].get("source", [])) if len(nb["cells"]) > 1 and nb["cells"][1].get("cell_type") == "code" else ""
    text = cell0_src + "\n" + cell1_src
    import re
    m = re.search(r'__AGENT_VERSION__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    assert m, "agent notebook missing __AGENT_VERSION__"
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert (major, minor, patch) >= (0, 7, 1), (
        f"agent __AGENT_VERSION__ unexpected value: {major}.{minor}.{patch} "
        "(must be >= 0.7.1 per §3a single-digit semver)"
    )
    for seg in (major, minor, patch):
        assert 0 <= seg <= 9, f"version segment {seg} violates §3a single-digit semver"


def test_orchestrator_exposes_kill_orphan_pipeline_runs_helper():
    """The orphan-kill logic must be hoisted out of preflight() into a reusable helper.

    Bug observed 2026-05-02 16:46 UTC: when a sector parent timed out, its child
    'dbx_vibe_*_pipeline_*' run kept executing on its own job. The orchestrator's
    retry path then submitted a NEW child run, which queued behind the orphan
    (job concurrency=1). User saw two runs of the same model — exactly what
    'NO 2 RUNS FOR ANY MODEL' forbids.
    """
    src = ORCHESTRATOR.read_text()
    assert "def kill_orphan_pipeline_runs(" in src, (
        "orphan-kill must be a standalone helper, not buried in preflight()"
    )
    assert "alias_tag" in src.split("def kill_orphan_pipeline_runs(", 1)[1].split("\ndef ", 1)[0], (
        "helper must accept alias_tag so log lines distinguish 'preflight' vs 'retry' invocations"
    )


def test_orchestrator_has_resolve_sector_filter_helper():
    """v0.7.1 (alias=sectors-filter) — the orchestrator MUST expose
    _resolve_sector_filter(sectors_arg, default_sector_paths) so the Option B
    multi-cloud launcher can pass GCP its half of sectors and Azure the other half.
    Sentinel grep + signature contract.
    """
    src = ORCHESTRATOR.read_text()
    assert "def _resolve_sector_filter(" in src, (
        "orchestrator MUST expose _resolve_sector_filter(...) — required for Option B "
        "multi-cloud parallelisation (split SECTOR_FILES_ORDER across <profile> + fe-vm-feip)"
    )
    fn_body = src.split("def _resolve_sector_filter(", 1)[1].split("\ndef ", 1)[0]
    assert "alias=sectors-filter" in fn_body, (
        "_resolve_sector_filter MUST carry the sectors-filter alias in its docstring "
        "so §10.7 deployed-archive grep can verify the v0.7.1 fix is live"
    )
    assert "raise ValueError" in fn_body, (
        "_resolve_sector_filter MUST raise ValueError on unknown sector — fail loudly so "
        "a typo'd launcher arg never silently drops sectors from the run"
    )
    assert "specified more than once" in fn_body, (
        "_resolve_sector_filter MUST reject duplicates — submitting the same sector twice "
        "would create two parallel pipelines per industry, violating §10.6 'no two runs' rule"
    )


def test_orchestrator_supports_sectors_cli_arg():
    """The --sectors CLI arg must appear in --help and be plumbed into _resolve_sector_filter."""
    import subprocess
    p = subprocess.run(
        ["python3", str(ORCHESTRATOR), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert p.returncode == 0, f"orchestrator --help failed: {p.stderr[:500]}"
    assert "--sectors" in p.stdout, "--sectors CLI arg missing from orchestrator --help"
    src = ORCHESTRATOR.read_text()
    main_body = src.split("def main():", 1)[1]
    assert 'parser.add_argument(\n        "--sectors"' in main_body or 'parser.add_argument("--sectors"' in main_body, (
        "main() MUST register the --sectors CLI arg via parser.add_argument"
    )
    assert "_resolve_sector_filter(args.sectors, sector_paths)" in main_body, (
        "main() MUST call _resolve_sector_filter(args.sectors, sector_paths) AFTER "
        "building the default sector_paths list and BEFORE the sector loop"
    )


def test_orchestrator_logs_sectors_filter_fired_alias():
    """The [sectors-filter FIRED] sentinel must be logged when --sectors is set, and the
    [sectors-filter] no-op log when it isn't — both for §10.7 deployed-archive grep verification.
    """
    src = ORCHESTRATOR.read_text()
    main_body = src.split("def main():", 1)[1]
    assert "[sectors-filter FIRED]" in main_body, (
        "main() MUST log [sectors-filter FIRED] when --sectors is non-empty so the auditor "
        "can grep the deployed orchestrator to confirm the filter is wired into the live binary"
    )
    assert "alias=sectors-filter-default" in main_body, (
        "main() MUST log alias=sectors-filter-default when --sectors is omitted so the no-filter "
        "path also leaves an audit trail"
    )


def test_resolve_sector_filter_round_trip_with_real_sectors():
    """End-to-end: import the helper, call it with realistic GCP + Azure splits, verify
    the right Path objects come back in the right order. Catches accidental refactor-breakage.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("orchestrate_sectors", ORCHESTRATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    defaults = [Path(f"/fake/dir/{n}") for n in mod.SECTOR_FILES_ORDER]

    gcp_half = mod._resolve_sector_filter(
        "financial_services,healthcare_and_life_sciences,travel_transport_logistics,retail_and_consumer_goods",
        defaults,
    )
    assert [p.stem for p in gcp_half] == [
        "financial_services",
        "healthcare_and_life_sciences",
        "travel_transport_logistics",
        "retail_and_consumer_goods",
    ]

    azure_half = mod._resolve_sector_filter(
        "energy_and_utilities,public_sector_education_nonprofit,communications_media_entertainment,manufacturing",
        defaults,
    )
    assert [p.stem for p in azure_half] == [
        "energy_and_utilities",
        "public_sector_education_nonprofit",
        "communications_media_entertainment",
        "manufacturing",
    ]

    covered = {p.stem for p in gcp_half} | {p.stem for p in azure_half}
    expected_post_done = {p.stem for p in defaults} - {"agriculture", "real_estate_and_professional_services"}
    assert covered == expected_post_done, (
        f"GCP+Azure split must cover every sector NOT already done by the active GCP run "
        f"(agriculture + real_estate already in vibe-business-data-models). "
        f"Missing: {expected_post_done - covered}, extra: {covered - expected_post_done}"
    )

    none_arg = mod._resolve_sector_filter(None, defaults)
    assert len(none_arg) == 10
    empty_arg = mod._resolve_sector_filter("", defaults)
    assert len(empty_arg) == 10
    whitespace_arg = mod._resolve_sector_filter("   ", defaults)
    assert len(whitespace_arg) == 10


def test_resolve_sector_filter_rejects_unknown_and_duplicate():
    """Defensive contract: typo'd sector name MUST fail the orchestrator at startup
    so the user catches it before launching a run that silently skips sectors.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("orchestrate_sectors", ORCHESTRATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    defaults = [Path(f"/fake/dir/{n}") for n in mod.SECTOR_FILES_ORDER]

    with pytest.raises(ValueError, match="unknown sector"):
        mod._resolve_sector_filter("healthcare_and_life_sciences,not_a_real_sector", defaults)

    with pytest.raises(ValueError, match="more than once"):
        mod._resolve_sector_filter("manufacturing,manufacturing", defaults)


def test_preflight_invokes_kill_orphan_helper():
    src = ORCHESTRATOR.read_text()
    preflight_body = src.split("def preflight(", 1)[1].split("\ndef ", 1)[0]
    assert "kill_orphan_pipeline_runs(" in preflight_body, (
        "preflight() MUST delegate orphan-kill to the shared helper (DRY)"
    )


def test_process_sector_kills_orphans_before_each_retry_submission():
    """ROOT-CAUSE FIX for 2026-05-02 16:46 UTC duplicate-run incident.

    The retry loop inside process_sector MUST call kill_orphan_pipeline_runs
    BEFORE every submit_sector_run, so that any child run left behind by a
    timed-out previous parent is cancelled FIRST. Otherwise the new submission
    queues behind the orphan (Databricks job concurrency=1).

    The §10.6 'no two runs of the same model' invariant depends on this.
    """
    src = ORCHESTRATOR.read_text()
    process_sector_body = src.split("def process_sector(", 1)[1].split("\ndef ", 1)[0]
    retry_section = process_sector_body.split("retrying {len(failed)} failed industries", 1)
    assert len(retry_section) == 2, "process_sector must contain the retry loop guarded by 'retrying ... failed industries'"
    after_retry_log = retry_section[1]
    submit_idx = after_retry_log.find("submit_sector_run(")
    kill_idx = after_retry_log.find("kill_orphan_pipeline_runs(")
    assert kill_idx >= 0, "process_sector retry path MUST call kill_orphan_pipeline_runs before submission"
    assert submit_idx >= 0, "process_sector retry path MUST call submit_sector_run after the kill"
    assert kill_idx < submit_idx, (
        "kill_orphan_pipeline_runs MUST run BEFORE submit_sector_run inside the retry loop "
        "(otherwise the new submission queues behind the orphan and produces duplicate runs)"
    )


def test_kill_orphan_helper_uses_section12_ownership_filter():
    """§12 catalog/job ownership rule — never touch other users' runs."""
    src = ORCHESTRATOR.read_text()
    helper_body = src.split("def kill_orphan_pipeline_runs(", 1)[1].split("\ndef ", 1)[0]
    assert "creator == me" in helper_body, (
        "helper MUST filter by creator == authenticated user (§12 ownership rule)"
    )
    assert "dbx_vibe_" in helper_body and "_pipeline_" in helper_body, (
        "helper MUST filter by run_name pattern dbx_vibe_*_pipeline_* (do not cancel non-pipeline runs)"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
