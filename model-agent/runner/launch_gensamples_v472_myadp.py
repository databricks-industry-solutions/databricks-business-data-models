#!/usr/bin/env python3
"""Live re-proof of the standalone `generate sample data` path on the v4.7.2 archive.

The MVM in `vibe_gensamples_v471` is already published, so this reruns only the
samples task: the operation rewrites every table, which is exactly the surface the
v4.7.2 `v471-code-suffix-pool` fix changes.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import launch_gensamples_v471_myadp as L
import vov_v2_marathon as M

VERSION_TOKEN = os.environ.get("VIBE_AGENT_VERSION_TOKEN", "v472")
AGENT_PATH = f"/Users/user@example.com/dbx_vibe_modelling_agent_{VERSION_TOKEN}"
L.AGENT_PATH = AGENT_PATH
M.AGENT_PATH = AGENT_PATH
M.PULSE_FILE = os.path.expanduser(f"~/claude/vibe-agent/gensamples_{VERSION_TOKEN}_pulses.txt")
M.STATE_FILE = os.path.expanduser(f"~/claude/vibe-agent/gensamples_{VERSION_TOKEN}_state.json")
M.KILL_FILE = os.path.expanduser(f"~/claude/vibe-agent/gensamples_{VERSION_TOKEN}_KILL")


def samples_only_spec():
    return {
        "name": f"dbx_vibe_gensamples_{VERSION_TOKEN}_myadp",
        "timeout_seconds": L.JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "samples",
                "notebook_task": {
                    "notebook_path": AGENT_PATH,
                    "source": "WORKSPACE",
                    "base_parameters": L._params(
                        operation="generate sample data",
                        generate_samples=L.SAMPLE_ROWS,
                        model_vibes="",
                        runtime_budget_seconds=str(L.SAMPLE_BUDGET_S),
                    ),
                },
                "timeout_seconds": L.SAMPLE_BUDGET_S,
                "max_retries": 0,
            },
        ],
    }


def main():
    M.pulse(f"=== gensamples {VERSION_TOKEN} live re-proof on {L.PROFILE} / `{L.CATALOG}` ===")
    job_id = L.find_or_create_job(samples_only_spec())
    run_id = M.dbj(["jobs", "run-now", str(job_id), "--no-wait"], L.PROFILE)["run_id"]
    M.pulse(f"submitted job {job_id} run {run_id}")
    info = L.wait_terminal(run_id)
    tasks = ", ".join(f"{t['k']}={t['lc'] or '?'}/{t['r'] or '-'}"
                      for t in info.get("tasks", []))
    M.pulse(f"TERMINAL run={run_id} lc={info['lc']} result={info.get('result')} [{tasks}]")
    print(json.dumps({"job_id": job_id, "run_id": run_id, "lc": info["lc"],
                      "result": info.get("result"), "catalog": L.CATALOG,
                      "url": info.get("url")}, indent=2))


if __name__ == "__main__":
    main()
