#!/usr/bin/env python3
"""Dual-run monitor: shipping_ports (fe-gcp, v450) + automotive (fe-aws, v451).
Append a compact §11 status block for BOTH runs every POLL_S to /tmp/v45_dual_mon.txt.
Read-only. Exits when BOTH runs are TERMINATED."""
import json
import subprocess
import time
from datetime import datetime, timezone

RUNS = [
    ("shipping", "fe-gcp", "521695476500351", "vibe_shipping_ports_v1", "shipping_ports"),
    ("automotive", "fe-aws", "150601952969108", "vibe_automotive_v1", "automotive"),
]
OUT = "/tmp/v45_dual_mon.txt"
POLL_S = 180


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(cmd, t=120):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout
    except Exception as e:
        return f"__ERR__ {e}"


def state(prof, rid):
    out = sh(["databricks", "jobs", "get-run", rid, "--profile", prof, "-o", "json"])
    try:
        d = json.loads(out or "{}")
    except Exception:
        return None, "parse-fail", []
    s = d.get("state", {})
    tasks = [(t.get("task_key"), t.get("state", {}).get("life_cycle_state"),
              t.get("state", {}).get("result_state")) for t in d.get("tasks", [])]
    return s.get("life_cycle_state"), s.get("result_state"), tasks


def info_tail(prof, cat, ind):
    base = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/logs/{ind}/v2/ecm"
    d2 = sh(["databricks", "fs", "ls", base, "--profile", prof], 60)
    info = None
    for ln in d2.splitlines():
        tok = ln.split()
        if tok and tok[-1].endswith("_info_v2_ecm.log"):
            info = tok[-1]
    if not info:
        # fall back to a flat v2 dir layout
        base2 = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/logs/{ind}/v2"
        d3 = sh(["databricks", "fs", "ls", base2, "--profile", prof], 60)
        for ln in d3.splitlines():
            tok = ln.split()
            if tok and "info" in tok[-1] and tok[-1].endswith(".log"):
                base, info = base2, tok[-1]
    if not info:
        return "(no v2 ecm info log yet)"
    loc = f"/tmp/v45_{ind}_ecm.log"
    sh(["databricks", "fs", "cp", f"{base}/{info}", loc, "--overwrite", "--profile", prof], 150)
    try:
        L = open(loc, errors="ignore").read().splitlines()
        # §11 red signatures + GAP-5 markers
        soft = sum(1 for x in L if "Max retries (3) exhausted" in x)
        fired = [x.split("]")[0] + "]" for x in L
                 if "vov-named-create-targets FIRED" in x or "P0-create" in x
                 or "v443-silo" in x or "verifier-product-create-coverage" in x]
        tag = f"lines={len(L)} soft_accept={soft}"
        if soft:
            tag = "RED " + tag
        return f"[{info} {tag}] TAIL:: " + " || ".join(L[-4:]) + (
            (" || FIRED:: " + " | ".join(sorted(set(fired))[:4])) if fired else "")
    except Exception:
        return f"({info} cp-fail)"


def main():
    while True:
        done = 0
        blk = [f"===== PULSE {now()} ====="]
        for label, prof, rid, cat, ind in RUNS:
            lc, res, tasks = state(prof, rid)
            tstr = " ".join(f"{k}:{(l or '?')[:4]}/{(r or '-')[:4]}" for k, l, r in tasks)
            blk.append(f"[{label}/{prof} {rid}] lc={lc} result={res} | {tstr}")
            if lc == "TERMINATED":
                done += 1
            else:
                blk.append("    " + info_tail(prof, cat, ind)[:520])
        open(OUT, "a").write("\n".join(blk) + "\n")
        if done == len(RUNS):
            open(OUT, "a").write(f"===== ALL TERMINATED {now()} =====\n")
            return
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
