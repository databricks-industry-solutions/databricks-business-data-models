#!/usr/bin/env python3
"""Live proof for the v4.7.1 sample-generation fixes on my-adp.

Two sequential tasks against a fresh isolated catalog:
  1. `mvm`     — new base MVM, generate_samples=0, so the build is fast and no row
                 is written by the in-pipeline path.
  2. `samples` — the standalone `generate sample data` operation, which is the
                 entry point the fixes target and the one that has never been run.

The audit that follows reads the physical tables, so a green terminal state alone
is not the pass condition.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

PROFILE = "my-adp"
AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v471"
CATALOG = "vibe_gensamples_v471"
BUSINESS = "coffee_roastery"
SAMPLE_ROWS = "60"
BUILD_BUDGET_S = 5400
SAMPLE_BUDGET_S = 3600
JOB_TIMEOUT_S = 12000

DESC = (
    "Specialty coffee roastery selling wholesale to cafes and direct to consumers: "
    "green bean sourcing and lot traceability, roast production batches and profiles, "
    "quality cupping scores, wholesale accounts and subscriptions, order fulfilment "
    "and delivery, and equipment maintenance."
)
VIBES = (
    "Keep this model intentionally small: exactly 3 domains and about 9 data products "
    "in total. Do not expand the scope."
)

M.AGENT_PATH = AGENT_PATH
M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/gensamples471_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/gensamples471_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/gensamples471_KILL")
M.PULSE_S = 300
M.WAREHOUSE[PROFILE] = "2ad1b26db73a7c6f"
M._IND_PROFILE = {BUSINESS: PROFILE}
M.cat_name = lambda ind: CATALOG  # noqa: E731

_PREFERRED_LOCATION = (
    "abfss://unity-catalog-storage@dbstoragem6ow6jhr3huvi.dfs.core.windows.net/"
    "7405617889454112"
)


def _create_catalog_with_location():
    bases = M._external_location_bases(PROFILE) + M._managed_bases(PROFILE)
    cand = [_PREFERRED_LOCATION] + [b for b in bases if b != _PREFERRED_LOCATION]
    last = "no candidates"
    for base in cand:
        for loc in (f"{base}/{CATALOG}", base):
            try:
                M.sql_exec(PROFILE, f"CREATE CATALOG `{CATALOG}` MANAGED LOCATION '{loc}'")
                M.pulse(f"created catalog `{CATALOG}` at {loc}")
                return
            except Exception as err:
                last = str(err)[:300]
                if "already exists" in last.lower():
                    return
    raise RuntimeError(f"could not create catalog: {last}")


def prepare_fresh_catalog():
    try:
        M.sql_exec(PROFILE, f"DROP CATALOG IF EXISTS `{CATALOG}` CASCADE", timeout=600)
    except Exception as err:
        M.pulse(f"drop failed ({str(err)[:160]}); trying CLI")
        M._try(["catalogs", "delete", CATALOG, "--force"], PROFILE,
               ("does not exist", "RESOURCE_DOES_NOT_EXIST"))
    _create_catalog_with_location()
    M.sql_exec(PROFILE, f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`_metamodel`")
    M.sql_exec(PROFILE, f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`_metamodel`.`vol_root`")


def _params(**over):
    params = {
        "operation": "new base model",
        "business_name": BUSINESS,
        "business_description": DESC,
        "model_vibes": VIBES,
        "data_model_scopes": "Minimum Viable Model - MVM",
        "deployment_catalog": CATALOG,
        "model_version": "1",
        "generate_samples": "0",
        "runtime_budget_seconds": str(BUILD_BUDGET_S),
        "cataloging_style": "One Catalog",
        "schema_prefix": "",
        "schema_suffix": "",
        "vibe_session_id": "{{job.run_id}}",
        "databricks_task_run_id": "{{task.run_id}}",
    }
    params.update(over)
    return params


def build_spec():
    return {
        "name": "dbx_vibe_gensamples_v471_myadp",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "mvm",
                "notebook_task": {
                    "notebook_path": AGENT_PATH,
                    "source": "WORKSPACE",
                    "base_parameters": _params(),
                },
                "timeout_seconds": BUILD_BUDGET_S,
                "max_retries": 0,
            },
            {
                "task_key": "samples",
                "depends_on": [{"task_key": "mvm"}],
                "notebook_task": {
                    "notebook_path": AGENT_PATH,
                    "source": "WORKSPACE",
                    "base_parameters": _params(
                        operation="generate sample data",
                        generate_samples=SAMPLE_ROWS,
                        model_vibes="",
                        runtime_budget_seconds=str(SAMPLE_BUDGET_S),
                    ),
                },
                "timeout_seconds": SAMPLE_BUDGET_S,
                "max_retries": 0,
            },
        ],
    }


def find_or_create_job(spec):
    jobs = M.dbj(["jobs", "list", "--limit", "100"], PROFILE)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for job in items:
        if (job.get("settings", {}) or {}).get("name") == spec["name"]:
            patch = Path("/tmp/gensamples471_jobpatch.json")
            patch.write_text(json.dumps({"job_id": job["job_id"], "new_settings": spec}))
            M.db(["jobs", "reset", "--json", f"@{patch}"], PROFILE)
            return job["job_id"]
    path = Path("/tmp/gensamples471_jobspec.json")
    path.write_text(json.dumps(spec))
    return M.dbj(["jobs", "create", "--json", f"@{path}"], PROFILE)["job_id"]


def wait_terminal(run_id):
    started = time.time()
    last_pulse = 0.0
    while True:
        if os.path.exists(M.KILL_FILE):
            M.pulse(f"KILL file present — leaving run {run_id}")
            return {"lc": "ABORTED", "result": "KILLED"}
        try:
            info = M.get_run(PROFILE, run_id)
        except Exception as err:
            M.pulse(f"poll err: {str(err)[:160]}")
            time.sleep(M.POLL_S)
            continue
        if info["lc"] in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return info
        if time.time() - last_pulse >= M.PULSE_S:
            tasks = ", ".join(f"{t['k']}={t['lc'] or '?'}/{t['r'] or '-'}"
                              for t in info["tasks"])
            M.pulse(f"[{BUSINESS}] elapsed={int((time.time() - started) / 60)}m "
                    f"lc={info['lc']} [{tasks}]")
            last_pulse = time.time()
        time.sleep(M.POLL_S)


def main():
    M.pulse(f"=== gensamples v4.7.1 live proof on {PROFILE} / `{CATALOG}` ===")
    if os.environ.get("VIBE_SKIP_PREP") == "1":
        M.pulse(f"reusing catalog `{CATALOG}` (VIBE_SKIP_PREP=1)")
    else:
        prepare_fresh_catalog()
    job_id = find_or_create_job(build_spec())
    run_id = M.dbj(["jobs", "run-now", str(job_id), "--no-wait"], PROFILE)["run_id"]
    M.pulse(f"submitted job {job_id} run {run_id}")
    info = wait_terminal(run_id)
    tasks = ", ".join(f"{t['k']}={t['lc'] or '?'}/{t['r'] or '-'}"
                      for t in info.get("tasks", []))
    M.pulse(f"TERMINAL run={run_id} lc={info['lc']} result={info.get('result')} [{tasks}]")
    print(json.dumps({"job_id": job_id, "run_id": run_id,
                      "lc": info["lc"], "result": info.get("result"),
                      "catalog": CATALOG, "url": info.get("url")}, indent=2))


if __name__ == "__main__":
    main()
