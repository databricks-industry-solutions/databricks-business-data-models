#!/usr/bin/env python3
"""Submit the installer notebook as a one-off Databricks job and wait for it.

`session_id` is always set so the notebook runs the operation in place instead of
launching a second job to do it, which keeps one run to watch and one log to read.

    python3 run_installer_job.py <profile> <notebook_path> k=v [k=v ...]
"""
import json
import subprocess
import sys
import time

POLL_S = 20


def cli(args, profile, timeout=300):
    proc = subprocess.run(["databricks"] + args + ["--profile", profile, "-o", "json"],
                          capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(" ".join(args) + " -> " + (proc.stderr or "")[:400])
    return json.loads(proc.stdout or "{}")


def submit(profile, notebook, params):
    params = dict(params)
    params.setdefault("session_id", str(int(time.time())))
    spec = {
        "run_name": "dmi_%s_%s" % (params.get("operation", "install").lower(),
                                   params.get("catalog_name", "run")),
        "timeout_seconds": 10800,
        "tasks": [{
            "task_key": "run",
            "notebook_task": {"notebook_path": notebook, "source": "WORKSPACE",
                              "base_parameters": params},
            "timeout_seconds": 10800,
        }],
    }
    with open("/tmp/_installer_job.json", "w") as f:
        json.dump(spec, f)
    return cli(["jobs", "submit", "--no-wait", "--json", "@/tmp/_installer_job.json"],
               profile)["run_id"]


def wait(profile, run_id):
    started = time.time()
    while True:
        info = cli(["jobs", "get-run", str(run_id)], profile)
        state = info.get("state", {}) or {}
        life = state.get("life_cycle_state")
        if life in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return info
        print("  [%4ds] %s" % (int(time.time() - started), life), flush=True)
        time.sleep(POLL_S)


def submit_and_wait(profile, notebook, params):
    """Run the notebook once and return (result_state, notebook result or error)."""
    run_id = submit(profile, notebook, params)
    print("run_id=%s  params=%s" % (run_id, params), flush=True)
    info = wait(profile, run_id)
    state = info.get("state", {}) or {}
    print("TERMINAL %s / %s" % (state.get("life_cycle_state"), state.get("result_state")))
    print("url: %s" % info.get("run_page_url"))
    message = ""
    tasks = info.get("tasks") or []
    if tasks:
        try:
            out = cli(["jobs", "get-run-output", str(tasks[0]["run_id"])], profile)
            message = (out.get("notebook_output", {}) or {}).get("result") or ""
            if out.get("error"):
                message = (message + " | " if message else "") + str(out["error"])[:2000]
        except Exception as exc:
            message = "could not read run output: %s" % exc
    return state.get("result_state"), message


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    profile, notebook = argv[1], argv[2]
    params = dict(kv.split("=", 1) for kv in argv[3:])
    state, message = submit_and_wait(profile, notebook, params)
    if message:
        print("result: %s" % message)
    return 0 if state == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
