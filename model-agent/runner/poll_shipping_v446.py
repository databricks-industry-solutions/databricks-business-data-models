#!/usr/bin/env python3
"""Background poller for the shipping_ports v4.4.6 VOV run (fe-gcp). NOT Monitor.
Pulses every POLL_S with per-task state + ecm/mvm info.log tail + §10.6 RED-signature scan.
Exits when the run reaches a terminal life-cycle state."""
import json
import os
import re
import subprocess
import time

P = "fe-gcp"
RID = "41077186567405"
CAT = "vibe_shipping_ports_v1"
IND = "shipping_ports"
POLL_S = 150
PULSE = "/tmp/ship_v446_pulses.txt"
LOGMIRROR = "/tmp/ship_v446_logs"
os.makedirs(LOGMIRROR, exist_ok=True)

RED = [
    ("F2/R7 soft-accept", r"Max retries \(3\) exhausted"),
    ("F4 siloed", r"SILOED TABLES DETECTED"),
    ("R8 cycles>0", r"Found [1-9]\d*\s*cycle\(s\)"),
    ("N2 fidelity", r"Fidelity gates FAILED"),
    ("R6 MV fail", r"Failed metric view"),
    ("NameError/Attr/Type", r"NameError|AttributeError|TypeError"),
    ("Traceback", r"Traceback \(most recent"),
    ("F1 perm-denied", r"Permission denied|\[Errno 13\]"),
]


def sh(cmd, t=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=t)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", str(e)


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(PULSE, "a") as f:
        f.write(line + "\n")


def latest_ver():
    base = f"dbfs:/Volumes/{CAT}/_metamodel/vol_root/logs/{IND}"
    rc, out, _ = sh(["databricks", "fs", "ls", base, "--profile", P], 90)
    vers = []
    for ln in out.splitlines():
        nm = ln.strip().rstrip("/").split("/")[-1].split()[0] if ln.strip() else ""
        m = re.fullmatch(r"v(\d+)", nm)
        if m:
            vers.append(int(m.group(1)))
    return max(vers) if vers else 1


def mirror_log(ver, scope):
    src = f"dbfs:/Volumes/{CAT}/_metamodel/vol_root/logs/{IND}/v{ver}/{scope}/{IND}_info_v{ver}_{scope}.log"
    dst = f"{LOGMIRROR}/v{ver}_{scope}_info.log"
    sh(["databricks", "fs", "cp", src, dst, "--overwrite", "--profile", P], 180)
    return dst if os.path.exists(dst) else None


def scan(path):
    if not path or not os.path.exists(path):
        return {}, 0
    txt = open(path, errors="ignore").read()
    hits = {}
    for label, pat in RED:
        n = len(re.findall(pat, txt))
        if n:
            hits[label] = n
    return hits, txt.count("\n")


def main():
    log(f"=== POLLER START run={RID} profile={P} cat={CAT} ===")
    while True:
        rc, out, err = sh(["databricks", "jobs", "get-run", RID, "--profile", P, "-o", "json"], 120)
        if rc != 0:
            log(f"poll err: {err[:150]}")
            time.sleep(POLL_S)
            continue
        d = json.loads(out)
        st = d.get("state", {})
        lc = st.get("life_cycle_state")
        res = st.get("result_state")
        tasks = ", ".join(f"{t.get('task_key')}={(t.get('state',{}) or {}).get('life_cycle_state')}/"
                          f"{(t.get('state',{}) or {}).get('result_state') or '-'}"
                          for t in d.get("tasks", []))
        ver = latest_ver()
        redall = {}
        loglines = {}
        for scope in ("ecm", "mvm"):
            path = mirror_log(ver, scope)
            hits, nl = scan(path)
            if nl:
                loglines[scope] = nl
            for k, v in hits.items():
                redall[k] = redall.get(k, 0) + v
        redstr = ("RED[" + ", ".join(f"{k}={v}" for k, v in redall.items()) + "]") if redall else "RED[none]"
        log(f"lc={lc}/{res or '-'} v{ver} [{tasks}] loglines={loglines} {redstr}")
        if lc in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            log(f"=== TERMINAL lc={lc} result={res} ===")
            break
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
