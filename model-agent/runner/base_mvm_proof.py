#!/usr/bin/env python3
"""Autonomous BASE-MODEL MVM proof for the v3.6.1 unified agentic-convergence policy.

User directive (2026-06-15): "AGENTIC LOOP MUST RUN FOR ANY OPERATION base model,
vov, shrink, enlarge ... you exit the agentic loop when you are done, or there is no
more convergence or you are at good quality or approaching the timeout of 15hrs ...
choose a more complex industry with bigger complex vibes to test against in addition
to gov_transport, so run both in autonomous mode."

This launches TWO independent `new base model` (MVM scope) builds in parallel on two
workspaces and drives each to terminal, proving the architect-review agentic loop runs
(and exits on convergence/quality/15h, NOT a fixed 3-iter cap) for the base-model path:

  - gov_transport      @ <profile>  : 2-domain (hr, project) gov_transport base vibe (21.8KB model_vibes)
  - healthcare @ <profile>  : most-complex repo vibe (22 domains / 541 products, 34.5KB)

Reuse-first (CLAUDE.md 3d): marathon prepare_catalog / sql_exec / wait_terminal /
get_run / export helpers + audit extract. Only the single-task `new base model`
job-spec and the staging of model_vibes are net-new.
"""
import os
import sys
import json
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v368"
BUDGET_S = 54000          # 15h user-directive agent budget -> runtime_budget_seconds
JOB_TIMEOUT_S = 57600     # 16h job ceiling (15h agent + 1h teardown margin)
LOCAL_STAGE = "/tmp/basemvm"
OUT_DIR = "/tmp/basemvm_out"

# isolate marathon's pulse/state/kill files so this proof never collides with vov2 state
M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/basemvm_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/basemvm_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/basemvm_KILL")
M.AGENT_PATH = AGENT_PATH
# base-mvm-specific catalog naming so prepare_catalog / vol_base operate on our catalogs
M.cat_name = lambda ind: f"vibe_{ind}_basemvm"
M.PULSE_S = 600  # 10-min pulses

CASES = [
    {"ind": "gov_transport", "profile": "<profile>", "business_domains": "hr, project"},
    {"ind": "healthcare", "profile": "<profile>", "business_domains": ""},
]


def stage_vibe(profile, ind):
    base = M.vol_base(ind)  # /Volumes/vibe_<ind>_basemvm/_metamodel/vol_root/_input
    M._try(["fs", "mkdir", f"dbfs:{base}"], profile, ("already exists",))
    src = f"{LOCAL_STAGE}/{ind}/model_vibes.txt"
    dst = f"dbfs:{base}/model_vibes.txt"
    M.db(["fs", "cp", src, dst, "--overwrite"], profile, timeout=300)
    return f"{base}/model_vibes.txt"


def read_desc(ind):
    p = f"{LOCAL_STAGE}/{ind}/business_description.txt"
    return Path(p).read_text().strip() if os.path.exists(p) else f"{ind} enterprise data model."


def build_spec(ind, profile, vibe_path, desc, domains):
    cat = M.cat_name(ind)
    params = {
        "operation": "new base model",
        "business_name": ind,
        "business_description": desc,
        "model_vibes": vibe_path,
        "data_model_scopes": "Minimum Viable Model - MVM",
        "deployment_catalog": cat,
        "model_version": "1",
        "generate_samples": "0",
        "runtime_budget_seconds": str(BUDGET_S),
    }
    if domains:
        params["business_domains"] = domains
    return {
        "name": f"dbx_vibe_basemvm_{ind}_v368",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": [{
            "task_key": "basemvm",
            "notebook_task": {"notebook_path": AGENT_PATH, "source": "WORKSPACE",
                              "base_parameters": params},
            "timeout_seconds": BUDGET_S,
        }],
    }


def find_or_create_job(profile, ind, spec):
    name = spec["name"]
    jobs = M.dbj(["jobs", "list", "--limit", "100"], profile)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for j in items:
        if (j.get("settings", {}) or {}).get("name") == name:
            patch = {"job_id": j["job_id"], "new_settings": spec}
            pp = f"/tmp/basemvm_jobpatch_{ind}.json"
            Path(pp).write_text(json.dumps(patch))
            M.db(["jobs", "reset", "--json", f"@{pp}"], profile)
            return j["job_id"]
    sp = f"/tmp/basemvm_jobspec_{ind}.json"
    Path(sp).write_text(json.dumps(spec))
    res = M.dbj(["jobs", "create", "--json", f"@{sp}"], profile)
    return res["job_id"]


def export_model(profile, ind):
    cat = M.cat_name(ind)
    root = f"/Volumes/{cat}/_metamodel/vol_root/business/{ind}"
    dest = f"{OUT_DIR}/{ind}"
    Path(dest).mkdir(parents=True, exist_ok=True)
    got = {}
    # base model with MVM scope writes v1/mvm (and logs under logs/<ind>/...)
    for scope in ("mvm", "ecm"):
        src = f"dbfs:{root}/v1/{scope}"
        d = f"{dest}/v1/{scope}"
        Path(os.path.dirname(d)).mkdir(parents=True, exist_ok=True)
        try:
            M.db(["fs", "cp", "-r", src, d, "--overwrite"], profile, timeout=1200)
            got[scope] = os.path.exists(f"{d}/model.json")
        except Exception as e:
            got[scope] = False
    # logs
    try:
        M.db(["fs", "cp", "-r", f"dbfs:{cat}/_metamodel/vol_root/logs/{ind}".replace(f"{cat}/", f"{cat}/"),
              f"{dest}/logs", "--overwrite"], profile, timeout=1200)
    except Exception:
        pass
    return got


def run_case(case):
    ind, profile, domains = case["ind"], case["profile"], case["business_domains"]
    tag = f"[{ind}@{profile}]"
    try:
        M.pulse(f"=== BASEMVM START {tag} ===")
        M.prepare_catalog(profile, ind)
        vibe_path = stage_vibe(profile, ind)
        desc = read_desc(ind)
        spec = build_spec(ind, profile, vibe_path, desc, domains)
        job_id = find_or_create_job(profile, ind, spec)
        run_id = M.run_now(profile, job_id)
        M.pulse(f"{tag} submitted job={job_id} run={run_id} vibe={vibe_path}")
        state = {"ind": ind, "profile": profile, "job_id": job_id, "run_id": run_id}
        Path(f"{OUT_DIR}").mkdir(parents=True, exist_ok=True)
        Path(f"{OUT_DIR}/{ind}_run.json").write_text(json.dumps(state, indent=2))
        info = M.wait_terminal(profile, ind, run_id)
        ts = ", ".join(f"{t['k']}={t['r'] or t['lc']}" for t in info.get("tasks", []))
        M.pulse(f"{tag} TERMINAL lc={info['lc']} result={info.get('result')} tasks=[{ts}] url={info.get('url')}")
        got = export_model(profile, ind)
        M.pulse(f"{tag} EXPORTED mvm={got.get('mvm')} ecm={got.get('ecm')}")
        state.update(terminal=info.get("result"), lc=info["lc"], exported=got, url=info.get("url"))
        Path(f"{OUT_DIR}/{ind}_run.json").write_text(json.dumps(state, indent=2))
    except Exception as e:
        import traceback
        M.pulse(f"{tag} UNCAUGHT: {str(e)[:400]}")
        Path(f"{OUT_DIR}").mkdir(parents=True, exist_ok=True)
        Path(f"{OUT_DIR}/{ind}_error.txt").write_text(traceback.format_exc())


def main():
    Path(os.path.dirname(M.PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    M.pulse(f"=== BASEMVM PROOF START v368 cases={[c['ind'] for c in CASES]} ===")
    threads = []
    for c in CASES:
        t = threading.Thread(target=run_case, args=(c,), name=c["ind"], daemon=False)
        t.start()
        threads.append(t)
        time.sleep(5)  # stagger submissions
    for t in threads:
        t.join()
    M.pulse("=== BASEMVM PROOF DONE ===")


if __name__ == "__main__":
    main()
