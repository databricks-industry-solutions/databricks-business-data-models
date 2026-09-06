#!/usr/bin/env python3
"""Issue #21 live ECM repro — WCB Alberta new base model on my-adp with agent v4.6.1.

Isolated catalog (avoids the my-uae amr_ali clash hang). Stall-aware monitor:
cancels if info.log stays empty >20min after RUNNING.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

PROFILE = "my-adp"
AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v461"
CATALOG = "vibe_wcb_alberta_v1"
BUSINESS = "wcb_alberta"
BUDGET_S = 54000
JOB_TIMEOUT_S = 57600
STALL_EMPTY_INFO_S = 1200  # 20 min with 0-byte info.log after task RUNNING => cancel

WCB_DESC = (
    "Workers' Compensation Board of Alberta (WCB Alberta) enterprise data model covering "
    "the full claims lifecycle from injury reporting through adjudication, medical treatment, "
    "return-to-work, and claim closure; premium assessment and employer rate-setting; "
    "experience rating and safety incentive programs; funding discipline, reserve adequacy, "
    "and actuarial valuation; employer accounts and industry classification; provider networks "
    "and fee schedules; legislative compliance and board governance."
)

M.AGENT_PATH = AGENT_PATH
M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/wcb458_myadp_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/wcb458_myadp_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/wcb458_myadp_KILL")
M.PULSE_S = 300
M.WAREHOUSE[PROFILE] = "2ad1b26db73a7c6f"
M._IND_PROFILE = {BUSINESS: PROFILE}
M.cat_name = lambda ind: CATALOG  # noqa: E731


def _create_catalog_with_location():
    bases = M._external_location_bases(PROFILE) + M._managed_bases(PROFILE)
    # Prefer the named FEIP location used by existing catalogs on this workspace.
    preferred = "abfss://unity-catalog-storage@dbstoragem6ow6jhr3huvi.dfs.core.windows.net/7405617889454112"
    cand = [preferred] + [b for b in bases if b != preferred]
    last = "no candidates"
    for base in cand:
        for loc in (f"{base}/{CATALOG}", base):
            try:
                M.sql_exec(PROFILE, f"CREATE CATALOG `{CATALOG}` MANAGED LOCATION '{loc}'")
                M.pulse(f"created catalog `{CATALOG}` at {loc}")
                return
            except Exception as e2:
                last = str(e2)[:300]
                if "already exists" in last.lower():
                    return
    raise RuntimeError(f"could not create catalog: {last}")


def prepare_fresh_catalog():
    # my-adp metastore has no default storage root — CREATE CATALOG requires MANAGED LOCATION.
    # Prefer reuse of an already-writable isolated catalog; only DROP when force-reinstall.
    force = os.environ.get("VOV_FORCE_REINSTALL") == "1"
    exists = False
    try:
        cats = M.dbj(["catalogs", "list"], PROFILE)
        items = cats if isinstance(cats, list) else cats.get("catalogs", [])
        exists = any(c.get("name") == CATALOG for c in items)
    except Exception:
        exists = False
    if exists and not force:
        M.pulse(f"reusing existing catalog `{CATALOG}` (set VOV_FORCE_REINSTALL=1 to DROP+CREATE)")
    else:
        if exists:
            M.pulse(f"DROP catalog `{CATALOG}` (force reinstall)")
            try:
                M.sql_exec(PROFILE, f"DROP CATALOG IF EXISTS `{CATALOG}` CASCADE", timeout=300)
            except Exception as e:
                M.pulse(f"DROP via SQL failed ({e}); trying CLI")
                M._try(["catalogs", "delete", CATALOG, "--force"], PROFILE, ("does not exist", "RESOURCE_DOES_NOT_EXIST"))
        M.pulse(f"CREATE catalog `{CATALOG}` with MANAGED LOCATION")
        _create_catalog_with_location()
    M.sql_exec(PROFILE, f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`_metamodel`")
    M.sql_exec(PROFILE, f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`_metamodel`.`vol_root`")


def build_spec():
    params = {
        "operation": "new base model",
        "business_name": BUSINESS,
        "business_description": WCB_DESC,
        "model_vibes": "",
        "data_model_scopes": "Expanded Coverage Model - ECM",
        "deployment_catalog": CATALOG,
        "model_version": "1",
        "generate_samples": "0",
        "runtime_budget_seconds": str(BUDGET_S),
        "cataloging_style": "One Catalog",
        "schema_prefix": "",
        "schema_suffix": "",
        "vibe_session_id": "{{job.run_id}}",
        "databricks_task_run_id": "{{task.run_id}}",
    }
    return {
        "name": "dbx_vibe_wcb_alberta_issue21_v461_myadp",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": [{
            "task_key": "ecm",
            "notebook_task": {
                "notebook_path": AGENT_PATH,
                "source": "WORKSPACE",
                "base_parameters": params,
            },
            "timeout_seconds": BUDGET_S,
        }],
    }


def find_or_create_job(spec):
    name = spec["name"]
    jobs = M.dbj(["jobs", "list", "--limit", "100"], PROFILE)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for j in items:
        if (j.get("settings", {}) or {}).get("name") == name:
            patch = {"job_id": j["job_id"], "new_settings": spec}
            pp = "/tmp/wcb458_myadp_jobpatch.json"
            Path(pp).write_text(json.dumps(patch))
            M.db(["jobs", "reset", "--json", f"@{pp}"], PROFILE)
            return j["job_id"]
    sp = "/tmp/wcb458_myadp_jobspec.json"
    Path(sp).write_text(json.dumps(spec))
    return M.dbj(["jobs", "create", "--json", f"@{sp}"], PROFILE)["job_id"]


def info_log_bytes():
    path = f"dbfs:/Volumes/{CATALOG}/_metamodel/vol_root/logs/{BUSINESS}/v1/ecm/{BUSINESS}_info_v1_ecm.log"
    try:
        out = M.dbj(["fs", "ls", path.rsplit("/", 1)[0]], PROFILE, timeout=90)
        files = out if isinstance(out, list) else out.get("files", []) or []
        for e in files:
            if e.get("name") == f"{BUSINESS}_info_v1_ecm.log":
                return int(e.get("file_size") or e.get("size") or 0), e.get("last_modified")
    except Exception as ex:
        M.pulse(f"info-log probe err: {str(ex)[:120]}")
    return None, None


def wait_terminal_stall_aware(run_id):
    started = time.time()
    last_pulse = 0
    empty_since = None
    task_running_since = None
    while True:
        if os.path.exists(M.KILL_FILE):
            M.pulse(f"KILL file present — leaving run {run_id}")
            return {"lc": "ABORTED", "result": "KILLED"}
        try:
            info = M.get_run(PROFILE, run_id)
        except Exception as e:
            M.pulse(f"poll err: {str(e)[:160]}")
            time.sleep(M.POLL_S)
            continue
        if info["lc"] in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return info
        ecm = next((t for t in info.get("tasks", []) if t.get("k") == "ecm"), None)
        if ecm and ecm.get("lc") == "RUNNING":
            if task_running_since is None:
                task_running_since = time.time()
            size, _ = info_log_bytes()
            if size is None or size == 0:
                if empty_since is None:
                    empty_since = time.time()
                elif time.time() - empty_since >= STALL_EMPTY_INFO_S:
                    M.pulse(
                        f"STALL: info.log empty for >{STALL_EMPTY_INFO_S // 60}m while RUNNING — "
                        f"canceling run {run_id}. alias=wcb456-stall-cancel"
                    )
                    try:
                        M.db(["jobs", "cancel-run", str(run_id)], PROFILE)
                    except Exception as ce:
                        M.pulse(f"cancel failed: {ce}")
                    return {"lc": "TERMINATED", "result": "CANCELED", "msg": "stall-empty-info", "url": info.get("url"), "tasks": info.get("tasks", [])}
            else:
                empty_since = None
        if time.time() - last_pulse >= M.PULSE_S:
            ts = ", ".join(f"{t['k']}={t['lc'] or '?'}/{t['r'] or '-'}" for t in info["tasks"])
            size, _ = info_log_bytes()
            M.pulse(
                f"[{BUSINESS}] {PROFILE} elapsed={int((time.time()-started)/60)}m "
                f"lc={info['lc']} [{ts}] info_bytes={size}"
            )
            last_pulse = time.time()
        time.sleep(M.POLL_S)


def main():
    Path(os.path.dirname(M.PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    M.pulse(f"=== WCB ALBERTA ISSUE21 v461 my-adp START catalog={CATALOG} ===")
    prepare_fresh_catalog()
    spec = build_spec()
    job_id = find_or_create_job(spec)
    # cancel any leftover active runs of this job
    try:
        active = M.dbj(["jobs", "list-runs", "--job-id", str(job_id), "--active-only"], PROFILE)
        runs = active if isinstance(active, list) else active.get("runs", [])
        for r in runs:
            rid = r.get("run_id")
            if rid:
                M.pulse(f"canceling leftover active run {rid}")
                M.db(["jobs", "cancel-run", str(rid)], PROFILE)
    except Exception as e:
        M.pulse(f"active-run cleanup skipped: {e}")
    run_id = M.run_now(PROFILE, job_id)
    M.pulse(f"submitted job={job_id} run={run_id} agent={AGENT_PATH}")
    state = {"job_id": job_id, "run_id": run_id, "profile": PROFILE, "catalog": CATALOG}
    Path("/tmp/wcb458_myadp_run.json").write_text(json.dumps(state, indent=2))
    info = wait_terminal_stall_aware(run_id)
    ts = ", ".join(f"{t['k']}={t['r'] or t['lc']}" for t in info.get("tasks", []))
    M.pulse(f"TERMINAL lc={info['lc']} result={info.get('result')} tasks=[{ts}] url={info.get('url')}")
    state.update(terminal=info)
    Path("/tmp/wcb458_myadp_run.json").write_text(json.dumps(state, indent=2, default=str))


if __name__ == "__main__":
    main()
