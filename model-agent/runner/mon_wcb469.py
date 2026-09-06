#!/usr/bin/env python3
"""15-min heartbeat monitor for the v4.6.9 WCB Alberta ECM run on my-adp.
Polls the run, mirrors info.log, greps for §10.6 hard signatures + v469 aliases,
prints a HEARTBEAT block each cycle, stops at terminal state."""
import json
import re
import subprocess
import sys
import time

PROFILE = "my-adp"
RUN_ID = "1066535684179784"
CATALOG = "vibe_wcb_alberta_v469"
BUSINESS = "wcb_alberta"
INFO = f"dbfs:/Volumes/{CATALOG}/_metamodel/vol_root/logs/{BUSINESS}/v1/ecm/{BUSINESS}_info_v1_ecm.log"
ERR = f"dbfs:/Volumes/{CATALOG}/_metamodel/vol_root/logs/{BUSINESS}/v1/ecm/{BUSINESS}_error_v1_ecm.log"
HEARTBEAT_S = 900

SIGS = [
    ("ERROR", r"\bERROR\b"),
    ("Max-retries-exhausted", r"Max retries \(3\) exhausted"),
    ("SILOED", r"SILOED TABLES DETECTED"),
    ("cycles>0", r"v403-serialize-cycle-guard FIRED[^\n]*remaining=[1-9]"),
    ("Fidelity-FAILED", r"Fidelity gates FAILED"),
    ("Failed-MV", r"Failed metric view"),
    ("parity-FAILED", r"physical parity failed"),
    ("NameError/Attr/Type", r"NameError|AttributeError|TypeError"),
    ("Traceback", r"Traceback \(most recent"),
]
POS = [
    ("mv-dedup FIRED", r"mv-dedup-by-target FIRED"),
    ("mv-parity-selfheal FIRED", r"mv-parity-selfheal FIRED"),
    ("mv-fallback FIRED", r"_v467_install_mv_fallback|mv-fallback"),
]


def db(args, timeout=90):
    try:
        r = subprocess.run(["databricks"] + args + ["--profile", PROFILE],
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr
    except Exception as e:
        return "", str(e)


def get_run():
    out, _ = db(["jobs", "get-run", RUN_ID, "-o", "json"])
    try:
        d = json.loads(out)
    except Exception:
        return None
    lc = (d.get("state") or {}).get("life_cycle_state")
    rs = (d.get("state") or {}).get("result_state")
    tasks = []
    for t in d.get("tasks", []):
        st = t.get("state") or {}
        tasks.append(f"{t.get('task_key')}={st.get('life_cycle_state')}/{st.get('result_state') or '-'}")
    return lc, rs, tasks


def mirror(remote, local):
    _, err = db(["fs", "cp", remote, local, "--overwrite"], timeout=120)
    try:
        return open(local, errors="ignore").read()
    except Exception:
        return ""


def main():
    cyc = 0
    while True:
        cyc += 1
        r = get_run()
        ts = time.strftime("%H:%M:%SZ", time.gmtime())
        if r is None:
            print(f"HEARTBEAT #{cyc} {ts} — poll failed, retrying", flush=True)
            time.sleep(60)
            continue
        lc, rs, tasks = r
        info = mirror(INFO, f"/tmp/wcb469_info.log")
        errtxt = mirror(ERR, f"/tmp/wcb469_error.log")
        both = info + "\n" + errtxt
        sig_hits = {name: len(re.findall(pat, both)) for name, pat in SIGS}
        pos_hits = {name: len(re.findall(pat, both)) for name, pat in POS}
        last = [ln for ln in info.splitlines() if ln.strip()][-3:]
        print(f"HEARTBEAT #{cyc} {ts} lc={lc} rs={rs} tasks={tasks} "
              f"info_lines={len(info.splitlines())}", flush=True)
        print(f"  SIGS: " + " ".join(f"{k}={v}" for k, v in sig_hits.items()), flush=True)
        print(f"  POS:  " + " ".join(f"{k}={v}" for k, v in pos_hits.items()), flush=True)
        for ln in last:
            print(f"  | {ln[:200]}", flush=True)
        if lc in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            print(f"TERMINAL lc={lc} rs={rs}", flush=True)
            return
        time.sleep(HEARTBEAT_S)


if __name__ == "__main__":
    main()
