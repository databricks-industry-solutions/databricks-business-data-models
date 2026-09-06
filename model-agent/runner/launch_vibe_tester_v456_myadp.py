#!/usr/bin/env python3
"""Launch vibe_tester_v456 on my-adp against a tiny business (dev-loop stage 1)."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

PROFILE = "my-adp"
WS = "/Users/user@example.com"
TESTER_PATH = f"{WS}/vibe_tester_v456"
CATALOG = "vibe_vibetest_small_v1"
BUSINESS = "vibetest_small"
BUDGET_S = 28800  # 8h ceiling for full tester suite
JOB_TIMEOUT_S = 32400

M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/tester456_myadp_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/tester456_myadp_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/tester456_myadp_KILL")
M.PULSE_S = 300
M.WAREHOUSE[PROFILE] = "2ad1b26db73a7c6f"


def build_spec():
    params = {
        "business_name": BUSINESS,
        "business_description": (
            "A deliberately tiny smoke-test business for vibe_tester validation. "
            "Coffee shop loyalty + inventory only."
        ),
        "model_vibes": (
            "intentionally tiny — target 3 domains and ~15 products. do not expand."
        ),
        "catalog": CATALOG,
    }
    return {
        "name": "dbx_vibe_tester_v456_myadp_small",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": [{
            "task_key": "vibe_tester",
            "notebook_task": {
                "notebook_path": TESTER_PATH,
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
            jid = j["job_id"]
            # cancel active
            try:
                active = M.dbj(["jobs", "list-runs", "--job-id", str(jid), "--active-only"], PROFILE)
                runs = active if isinstance(active, list) else active.get("runs", [])
                for r in runs:
                    rid = r.get("run_id")
                    if rid:
                        M.pulse(f"canceling leftover tester run {rid}")
                        M._try(["jobs", "cancel-run", str(rid)], PROFILE, ())
                        time.sleep(3)
            except Exception:
                pass
            patch = {"job_id": jid, "new_settings": spec}
            pp = "/tmp/tester456_jobpatch.json"
            Path(pp).write_text(json.dumps(patch))
            M.db(["jobs", "reset", "--json", f"@{pp}"], PROFILE)
            return jid
    sp = "/tmp/tester456_jobspec.json"
    Path(sp).write_text(json.dumps(spec))
    res = M.dbj(["jobs", "create", "--json", f"@{sp}"], PROFILE)
    return res["job_id"]


def wait_terminal(run_id):
    t0 = time.time()
    while True:
        if os.path.exists(M.KILL_FILE):
            M.pulse("KILL file present — canceling")
            M._try(["jobs", "cancel-run", str(run_id)], PROFILE, ())
            return {"life_cycle_state": "TERMINATED", "result_state": "CANCELED"}
        info = M.get_run(PROFILE, run_id)
        st = info.get("state", {})
        lc = st.get("life_cycle_state")
        elapsed = int((time.time() - t0) / 60)
        tasks = info.get("tasks") or []
        tsum = []
        for t in tasks:
            ts = (t.get("state") or {})
            tsum.append(f"{t.get('task_key')}={ts.get('life_cycle_state')}/{ts.get('result_state')}")
        M.pulse(f"[tester] my-adp elapsed={elapsed}m lc={lc} [{','.join(tsum) or '-'}]")
        if lc in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return st
        time.sleep(M.PULSE_S)


def main():
    Path(os.path.dirname(M.PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    M.pulse(f"=== VIBE TESTER v456 my-adp START catalog={CATALOG} ===")
    spec = build_spec()
    job_id = find_or_create_job(spec)
    run_id = M.run_now(PROFILE, job_id)
    M.pulse(f"submitted job={job_id} run={run_id} tester={TESTER_PATH}")
    state = {"job_id": job_id, "run_id": run_id, "profile": PROFILE, "catalog": CATALOG, "stage": "tester"}
    Path("/tmp/tester456_myadp_run.json").write_text(json.dumps(state, indent=2))
    st = wait_terminal(run_id)
    M.pulse(f"TERMINAL lc={st.get('life_cycle_state')} result={st.get('result_state')} msg={st.get('state_message','')[:200]}")
    state["terminal"] = st
    Path("/tmp/tester456_myadp_run.json").write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
