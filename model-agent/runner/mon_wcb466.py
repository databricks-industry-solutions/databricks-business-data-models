#!/usr/bin/env python3
"""15-min heartbeat monitor for the v4.6.6 WCB Alberta issue-#21 ECM run.
Closes the launcher gap: flags a FROZEN-GROWTH stall (last content ts older than
STALL_S while RUNNING), not just empty-info. Writes rich HEARTBEAT blocks to
/tmp/wcb466_hb.txt + stdout. Exits when the run is terminal. Read-only / no cancel."""
import json
import re
import subprocess
import time
from datetime import datetime, timezone

PROFILE = "my-adp"
RUN_ID = "908193301348249"
BASE = "dbfs:/Volumes/vibe_wcb_alberta_v466/_metamodel/vol_root/logs/wcb_alberta/v1/ecm"
INFO = f"{BASE}/wcb_alberta_info_v1_ecm.log"
ERR = f"{BASE}/wcb_alberta_error_v1_ecm.log"
HB = "/tmp/wcb466_hb.txt"
PERIOD_S = 900
STALL_S = 1500  # 25 min of no new content while RUNNING => flag stall

SIGS = [
    ("AttributeError/Traceback", r"AttributeError|Traceback"),
    ("Max-retries-exhausted", r"Max retries \(3\) exhausted"),
    # R8/R8b: true residual cycles only — the v403 serialize guard reporting remaining>0.
    # Mid-pipeline "[CYCLE DETECTION] Found N cycle(s)" is NORMAL (detector) and is
    # resolved by *-cycle-skip guards; it is tracked as a positive signal, not a red.
    ("residual-cycles(R8b)", r"v403-serialize-cycle-guard FIRED[^\n]*remaining=[1-9]"),
    ("SILOED", r"SILOED TABLES"),
    ("Fidelity-FAILED", r"Fidelity gates FAILED"),
    ("Failed-metric-view", r"Failed metric view"),
    ("NameError", r"NameError"),
    ("str-no-attr", r"'(?:str|int|float|list|NoneType)' object has no attribute"),
]


def sh(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def run_state():
    r = sh(["databricks", "jobs", "get-run", RUN_ID, "--profile", PROFILE])
    try:
        d = json.loads(r.stdout)
        s = d.get("state", {})
        return s.get("life_cycle_state"), s.get("result_state")
    except Exception:
        return "UNKNOWN", None


def pull(src, dst):
    sh(["databricks", "fs", "cp", src, dst, "--overwrite", "--profile", PROFILE])
    try:
        return open(dst, errors="ignore").read()
    except Exception:
        return ""


def emit(block):
    print(block, flush=True)
    with open(HB, "a") as f:
        f.write(block + "\n")


def main():
    start = time.time()
    while True:
        lc, res = run_state()
        info = pull(INFO, "/tmp/wcb466_info.log")
        err = pull(ERR, "/tmp/wcb466_err.log")
        ts = re.findall(r"^2026-\d\d-\d\d \d\d:\d\d:\d\d", info, re.M)
        last_ts = ts[-1] if ts else "?"
        now = datetime.now(timezone.utc)
        # stall calc
        stall = ""
        if last_ts != "?":
            try:
                lt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                age = (now - lt).total_seconds()
                if lc == "RUNNING" and age > STALL_S:
                    stall = f"  🔴 FROZEN-GROWTH STALL: last content {int(age)}s ago (>{STALL_S}s)"
                else:
                    stall = f"  content_age={int(age)}s"
            except Exception:
                pass
        # progress: last "Completed: X (n/total)"
        prog = re.findall(r"Completed: \S+ \((\d+)/(\d+)\)", info)
        progress = f"{prog[-1][0]}/{prog[-1][1]} products" if prog else "n/a"
        # last real content line
        content = [l for l in info.splitlines() if l.startswith("2026-") and "VolumeLogFlush" not in l]
        last_line = content[-1][:130] if content else "(none)"
        # signatures
        sig_hits = []
        blob = info + "\n" + err
        for name, pat in SIGS:
            c = len(re.findall(pat, blob))
            if c:
                sig_hits.append(f"{name}={c}")
        coerce = len(re.findall(r"llm-parse-coerce FIRED", info))
        # positive signals (guards working) — mid-pipeline cycle prevention
        cyc_detected = len(re.findall(r"\[CYCLE DETECTION\] Found [1-9][0-9]* cycle", blob))
        guard_fired = len(re.findall(r"cycle-skip FIRED", blob))
        no_cycle_ok = len(re.findall(r"\[CYCLE DETECTION\] .*No cycles", blob))
        elapsed = int((time.time() - start) / 60)
        sig_str = "ALL ZERO" if not sig_hits else "🔴 " + " ".join(sig_hits)
        block = (
            f"[HEARTBEAT {now.strftime('%H:%M:%SZ')}] mon_elapsed={elapsed}m lc={lc} result={res}\n"
            f"  stage/last: {last_line}\n"
            f"  progress={progress}  last_ts={last_ts}{stall}\n"
            f"  §10.6 signatures: {sig_str}  coerce_FIRED={coerce}\n"
            f"  cycle-guards: detected={cyc_detected} blocked={guard_fired} no-cycle-verdicts={no_cycle_ok}"
        )
        emit(block)
        if lc in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            emit(f"[TERMINAL] lc={lc} result={res} after mon_elapsed={elapsed}m")
            return
        time.sleep(PERIOD_S)


if __name__ == "__main__":
    main()
