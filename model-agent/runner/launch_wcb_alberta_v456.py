#!/usr/bin/env python3
"""Issue #21 live ECM repro — WCB Alberta new base model on my-uae with agent v4.5.6.

Reporter: https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/issues/21
  operation=new base model, scope=ECM, complex workers' compensation domain.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

PROFILE = "my-uae"
AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v456"
CATALOG = "amr_ali"
BUSINESS = "wcb_alberta"
BUDGET_S = 54000
JOB_TIMEOUT_S = 57600

WCB_DESC = (
    "Workers' Compensation Board of Alberta (WCB Alberta) enterprise data model covering "
    "the full claims lifecycle from injury reporting through adjudication, medical treatment, "
    "return-to-work, and claim closure; premium assessment and employer rate-setting; "
    "experience rating and safety incentive programs; funding discipline, reserve adequacy, "
    "and actuarial valuation; employer accounts and industry classification; provider networks "
    "and fee schedules; legislative compliance and board governance."
)

M.AGENT_PATH = AGENT_PATH
M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/wcb456_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/wcb456_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/wcb456_KILL")
M.PULSE_S = 300
M.WAREHOUSE[PROFILE] = "6b2c33b3b2aae3ac"
M.FIXED_CATALOG[PROFILE] = CATALOG
M._IND_PROFILE = {BUSINESS: PROFILE}
M.cat_name = lambda ind: CATALOG  # noqa: E731


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
    }
    return {
        "name": "dbx_vibe_wcb_alberta_issue21_v456",
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
            pp = "/tmp/wcb456_jobpatch.json"
            Path(pp).write_text(json.dumps(patch))
            M.db(["jobs", "reset", "--json", f"@{pp}"], PROFILE)
            return j["job_id"]
    sp = "/tmp/wcb456_jobspec.json"
    Path(sp).write_text(json.dumps(spec))
    return M.dbj(["jobs", "create", "--json", f"@{sp}"], PROFILE)["job_id"]


def main():
    Path(os.path.dirname(M.PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    M.pulse(f"=== WCB ALBERTA ISSUE21 v456 START profile={PROFILE} catalog={CATALOG} ===")
    M.sql_exec(PROFILE, f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`_metamodel`")
    M.sql_exec(PROFILE, f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`_metamodel`.`vol_root`")
    spec = build_spec()
    job_id = find_or_create_job(spec)
    run_id = M.run_now(PROFILE, job_id)
    M.pulse(f"submitted job={job_id} run={run_id} agent={AGENT_PATH}")
    state = {"job_id": job_id, "run_id": run_id, "profile": PROFILE, "catalog": CATALOG}
    Path("/tmp/wcb456_run.json").write_text(json.dumps(state, indent=2))
    info = M.wait_terminal(PROFILE, BUSINESS, run_id)
    ts = ", ".join(f"{t['k']}={t['r'] or t['lc']}" for t in info.get("tasks", []))
    M.pulse(f"TERMINAL lc={info['lc']} result={info.get('result')} tasks=[{ts}] url={info.get('url')}")
    state.update(terminal=info)
    Path("/tmp/wcb456_run.json").write_text(json.dumps(state, indent=2, default=str))


if __name__ == "__main__":
    main()
