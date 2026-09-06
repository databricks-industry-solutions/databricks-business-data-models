import os, sys, json, time, threading
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

WS = "/Users/user@example.com"
PROFILE = "<profile>"
LOCAL_VIBE = "/tmp/basemvm/gov_transport/model_vibes.txt"
BUDGET_S = 5400
JOB_TIMEOUT_S = 6000
M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/ctl_probe_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/ctl_probe_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/ctl_probe_KILL")

ARMS = [
    {"tag": "cur",  "agent": f"{WS}/dbx_vibe_modelling_agent_v367",        "cat": "vibe_gov_transportcur_basemvm"},
    {"tag": "good", "agent": f"{WS}/dbx_vibe_modelling_agent_v367goodctl", "cat": "vibe_gov_transportgood_basemvm"},
]


def prep_cat(cat):
    M._try(["catalogs", "delete", cat, "--force"], PROFILE, ("does not exist", "RESOURCE_DOES_NOT_EXIST"))
    M.db(["catalogs", "create", cat], PROFILE)
    M.db(["schemas", "create", "_staging", cat], PROFILE)
    M.db(["volumes", "create", cat, "_staging", "src", "MANAGED"], PROFILE)
    base = f"/Volumes/{cat}/_staging/src"
    M.db(["fs", "cp", LOCAL_VIBE, f"dbfs:{base}/model_vibes.txt", "--overwrite"], PROFILE, timeout=300)
    return f"{base}/model_vibes.txt"


def spec(tag, agent, cat, vibe):
    return {
        "name": f"dbx_ctl_metamodel_{tag}",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": [{
            "task_key": "probe",
            "notebook_task": {"notebook_path": agent, "source": "WORKSPACE", "base_parameters": {
                "operation": "new base model", "business_name": "gov_transport",
                "business_description": "gov_transport enterprise data model.",
                "model_vibes": vibe, "data_model_scopes": "Minimum Viable Model - MVM",
                "deployment_catalog": cat, "model_version": "1", "generate_samples": "0",
                "business_domains": "hr, project", "runtime_budget_seconds": str(BUDGET_S),
            }},
            "timeout_seconds": BUDGET_S,
        }],
    }


def find_or_create(tag, sp):
    jobs = M.dbj(["jobs", "list", "--limit", "100"], PROFILE)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for j in items:
        if (j.get("settings", {}) or {}).get("name") == sp["name"]:
            pp = f"/tmp/ctl_patch_{tag}.json"
            Path(pp).write_text(json.dumps({"job_id": j["job_id"], "new_settings": sp}))
            M.db(["jobs", "reset", "--json", f"@{pp}"], PROFILE)
            return j["job_id"]
    sf = f"/tmp/ctl_spec_{tag}.json"
    Path(sf).write_text(json.dumps(sp))
    return M.dbj(["jobs", "create", "--json", f"@{sf}"], PROFILE)["job_id"]


def launch(arm):
    tag = arm["tag"]
    M.pulse(f"=== CTL {tag} prep catalog {arm['cat']} ===")
    vibe = prep_cat(arm["cat"])
    jid = find_or_create(tag, spec(tag, arm["agent"], arm["cat"], vibe))
    rid = M.run_now(PROFILE, jid)
    M.pulse(f"CTL {tag} job={jid} run={rid} agent={arm['agent']} cat={arm['cat']}")
    Path(os.path.expanduser("~/claude/vibe-agent")).mkdir(parents=True, exist_ok=True)
    Path(os.path.expanduser(f"~/claude/vibe-agent/ctl_{tag}.json")).write_text(json.dumps({"job": jid, "run": rid, "cat": arm["cat"]}))


def main():
    Path(os.path.dirname(M.PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    M.pulse("=== CTL METAMODEL PROBE START (cur vs good, gov_transport, <profile>) ===")
    ts = []
    for a in ARMS:
        t = threading.Thread(target=launch, args=(a,), name=a["tag"], daemon=True)
        t.start(); ts.append(t); time.sleep(3)
    for t in ts:
        t.join()
    M.pulse("=== CTL PROBE LAUNCHED (poll _metamodel externally) ===")


if __name__ == "__main__":
    main()
