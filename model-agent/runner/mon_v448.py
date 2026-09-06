#!/usr/bin/env python3
"""v4.4.8 dual-run monitor: automotive (fe-aws) + shipping_ports (fe-gcp).
Every POLL_S seconds append a compact status block for BOTH runs (life-cycle + per-task state +
tail of the freshest volume info log) to /tmp/v448_mon.txt. Exits when both runs are TERMINATED.
Read-only: never mutates a run. §11 pulse discipline is applied by the reader, not here."""
import json
import os
import subprocess
import time
from datetime import datetime, timezone

RUNS = [
    ("automotive", "fe-aws", "733589943485455", "vibe_automotive_v1"),
    ("shipping_ports", "fe-gcp", "702847387933612", "vibe_shipping_ports_v1"),
]
OUT = "/tmp/v448_mon.txt"
POLL_S = 300


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout
    except Exception as e:
        return f"__ERR__ {e}"


def run_state(prof, rid):
    out = sh(["databricks", "jobs", "get-run", str(rid), "--profile", prof, "-o", "json"])
    try:
        d = json.loads(out)
    except Exception:
        return None, "parse-fail", []
    s = d.get("state", {})
    tasks = [(t.get("task_key"), t.get("state", {}).get("life_cycle_state"),
              t.get("state", {}).get("result_state")) for t in d.get("tasks", [])]
    return s.get("life_cycle_state"), s.get("result_state"), tasks


def freshest_info_tail(prof, cat, ind):
    """Best-effort tail of the freshest v2 info log on the volume."""
    base = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/logs/{ind}"
    vers = sh(["databricks", "fs", "ls", base, "--profile", prof], timeout=60)
    best = None
    for line in vers.splitlines():
        tok = line.split()
        if not tok:
            continue
        v = tok[-1].rstrip("/")
        if v.startswith("v2") or v.startswith("mvm") or v.startswith("ecm"):
            best = v
    if not best:
        return "(no v2 log dir yet)"
    d2 = sh(["databricks", "fs", "ls", f"{base}/{best}", "--profile", prof], timeout=60)
    info = None
    for line in d2.splitlines():
        tok = line.split()
        if tok and "info" in tok[-1]:
            info = tok[-1]
    if not info:
        return f"({best}: no info log yet)"
    local = f"/tmp/v448_mon_{ind}.log"
    sh(["databricks", "fs", "cp", f"{base}/{best}/{info}", local, "--overwrite", "--profile", prof], timeout=120)
    try:
        lines = open(local, errors="ignore").read().splitlines()
        return f"[{best}/{info}] " + " || ".join(lines[-6:])
    except Exception:
        return f"({best}/{info} cp-fail)"


def main():
    while True:
        done = 0
        block = [f"===== PULSE {now()} ====="]
        for ind, prof, rid, cat in RUNS:
            lc, res, tasks = run_state(prof, rid)
            tstr = " ".join(f"{k}:{(l or '?')[:4]}/{(r or '-')[:4]}" for k, l, r in tasks)
            block.append(f"[{ind}/{prof}] lc={lc} result={res} | {tstr}")
            if lc == "TERMINATED":
                done += 1
            else:
                block.append("    " + freshest_info_tail(prof, cat, ind)[:400])
        with open(OUT, "a") as f:
            f.write("\n".join(block) + "\n")
        if done == len(RUNS):
            with open(OUT, "a") as f:
                f.write(f"===== ALL TERMINATED {now()} =====\n")
            return
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
