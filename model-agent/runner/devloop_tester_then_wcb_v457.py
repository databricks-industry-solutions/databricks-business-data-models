#!/usr/bin/env python3
"""Dev-loop orchestrator: wait for vibe_tester SUCCESS, then launch WCB issue-21 runner."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROFILE = "my-adp"
TESTER_STATE = Path("/tmp/tester458_myadp_run.json")
ORCH_LOG = Path("/tmp/devloop458_orch.log")
ROOT = Path(__file__).resolve().parents[1]


def log(msg):
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {msg}"
    print(line, flush=True)
    ORCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ORCH_LOG.open("a") as f:
        f.write(line + "\n")


def wait_tester():
    log("waiting for tester terminal in " + str(TESTER_STATE))
    while True:
        if not TESTER_STATE.exists():
            time.sleep(30)
            continue
        st = json.loads(TESTER_STATE.read_text())
        term = st.get("terminal")
        if term and term.get("life_cycle_state") in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return st
        # also poll live run
        rid = st.get("run_id")
        if rid:
            try:
                out = subprocess.check_output(
                    ["databricks", "jobs", "get-run", str(rid), "--profile", PROFILE, "-o", "json"],
                    text=True, timeout=60,
                )
                d = json.loads(out)
                s = d.get("state", {})
                log(f"tester live lc={s.get('life_cycle_state')} result={s.get('result_state')}")
                if s.get("life_cycle_state") in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
                    st["terminal"] = s
                    TESTER_STATE.write_text(json.dumps(st, indent=2))
                    return st
            except Exception as e:
                log(f"poll err: {e}")
        time.sleep(180)


def main():
    st = wait_tester()
    result = (st.get("terminal") or {}).get("result_state")
    log(f"tester terminal result={result}")
    if result != "SUCCESS":
        log("TESTER NOT SUCCESS — aborting WCB runner launch; fix required")
        Path("/tmp/devloop458_status.json").write_text(json.dumps({
            "stage": "tester_failed", "tester": st
        }, indent=2))
        sys.exit(2)

    log("tester SUCCESS — launching WCB Alberta issue-21 vibe_runner (agent job)")
    # Prefer dedicated WCB launch script (direct agent ECM = issue reporter path)
    cmd = [sys.executable, str(ROOT / "runner" / "launch_wcb_alberta_v457_myadp.py")]
    env = os.environ.copy()
    env["VOV_FORCE_REINSTALL"] = "1"  # clean catalog for honest repro
    Path("/tmp/devloop458_status.json").write_text(json.dumps({
        "stage": "launching_wcb", "tester": st
    }, indent=2))
    log("exec: " + " ".join(cmd))
    rc = subprocess.call(cmd, cwd=str(ROOT), env=env)
    log(f"wcb launcher exited rc={rc}")
    Path("/tmp/devloop458_status.json").write_text(json.dumps({
        "stage": "wcb_done", "tester": st, "wcb_rc": rc
    }, indent=2))
    sys.exit(rc)


if __name__ == "__main__":
    main()
