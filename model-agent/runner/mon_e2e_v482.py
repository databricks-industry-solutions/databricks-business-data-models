#!/usr/bin/env python3
"""Poll the v4.8.2 end-to-end run and mirror its volume logs locally.

Separate from launch_e2e_v482.py so a dead launcher shell never orphans the monitoring
of a run that is still alive server-side (which is exactly what happened at 17:38Z).
"""
import json
import os
import subprocess
import sys
import time

PROFILE = "my-uae"
RUN_ID = "165849254839239"
CATALOG = "vibe_e2e_v482"
BUSINESS = "coffee_roastery"
MIRROR = "/tmp/e2e482_logs"
PULSES = "/tmp/e2e482_pulses.txt"
LOG_DIR = f"dbfs:/Volumes/{CATALOG}/_metamodel/vol_root/logs/{BUSINESS}/v1/mvm"
TERMINAL = ("TERMINATED", "INTERNAL_ERROR", "SKIPPED")


def sh(args, timeout=180):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def pulse(msg):
    line = f"[{time.strftime('%H:%M:%SZ', time.gmtime())}] {msg}"
    print(line, flush=True)
    with open(PULSES, "a") as fh:
        fh.write(line + "\n")


def run_state():
    out = sh(["databricks", "jobs", "get-run", RUN_ID, "--profile", PROFILE, "-o", "json"])
    try:
        d = json.loads(out)
    except Exception:
        return None, None, []
    st = d.get("state", {})
    tasks = [(t.get("task_key"), (t.get("state", {}) or {}).get("life_cycle_state"),
              (t.get("state", {}) or {}).get("result_state")) for t in d.get("tasks", [])]
    return st.get("life_cycle_state"), st.get("result_state"), tasks


def mirror():
    os.makedirs(MIRROR, exist_ok=True)
    listing = sh(["databricks", "fs", "ls", LOG_DIR, "--profile", PROFILE])
    names = [ln.split()[0] for ln in listing.splitlines() if ln.strip()]
    sizes = {}
    for n in names:
        dst = os.path.join(MIRROR, n)
        sh(["databricks", "fs", "cp", f"{LOG_DIR}/{n}", dst, "--overwrite", "--profile", PROFILE])
        if os.path.exists(dst):
            sizes[n] = os.path.getsize(dst)
    return sizes


def scan():
    hits = {}
    for pat, label in (
        ("verifier-relation-target-resolvable FIRED", "v482 guard fired"),
        # anchored on the SparkException prefix: the v4.8.1 envelope log line quotes the
        # bare message, so an unanchored needle self-triggers on every healthy run.
        ("SparkException: The responseFormat is invalid", "F-responseFormat"),
        ("Max retries (3) exhausted", "F2 soft-accept"),
        ("SILOED TABLES DETECTED", "F4 silo"),
        ("Fidelity gates FAILED", "N2 fidelity"),
        ("ground-truth-audit FIRED", "GT audit"),
        ("VREQ-003", "VREQ-003"),
    ):
        n = 0
        for fn in os.listdir(MIRROR) if os.path.isdir(MIRROR) else []:
            if not fn.endswith(".log"):
                continue
            try:
                n += open(os.path.join(MIRROR, fn), errors="ignore").read().count(pat)
            except Exception:
                pass
        if n:
            hits[label] = n
    return hits


def main():
    pulse(f"MONITOR START run={RUN_ID} catalog={CATALOG}")
    while True:
        lc, rs, tasks = run_state()
        sizes = mirror()
        hits = scan()
        pulse(f"lc={lc} result={rs} tasks={tasks} bytes={sizes} signals={hits}")
        if lc in TERMINAL:
            pulse(f"TERMINAL lc={lc} result={rs}")
            return 0
        time.sleep(180)


if __name__ == "__main__":
    sys.exit(main())
