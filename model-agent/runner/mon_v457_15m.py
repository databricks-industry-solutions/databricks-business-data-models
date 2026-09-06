#!/usr/bin/env python3
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

PROFILE = "my-adp"
TESTER_RUN = 857012893473954
PIPELINE_RUN = 496719838790949
INTERVAL = 900
OUT = Path("/tmp/mon_v457_15m.log")
PATTERNS = {
    "soft_accept": r"Max retries \(3\) exhausted",
    "cycles": r"Found [1-9]\d* cycle\(s\)",
    "silos": r"SILOED TABLES DETECTED",
    "bidirectional": r"DIRECT BIDIRECTIONAL",
    "fidelity": r"Fidelity gates FAILED",
    "metric_fail": r"Failed metric view",
    "permission": r"Permission denied",
    "type_crash": r"NameError|AttributeError|TypeError|Traceback \(most recent",
    "error_lines": r"\bERROR\b",
}


def db(args):
    result = subprocess.run(
        ["databricks", *args, "--profile", PROFILE, "-o", "json"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode:
        return {"_error": (result.stderr or result.stdout).strip()[:400]}
    return json.loads(result.stdout)


def state(run_id):
    data = db(["jobs", "get-run", str(run_id)])
    current = data.get("state", {})
    return data, current.get("life_cycle_state"), current.get("result_state")


def scan():
    text = ""
    for path in Path("/tmp/v457_monitor_logs").glob("*.log"):
        text += path.read_text(errors="ignore")
    return {name: len(re.findall(pattern, text)) for name, pattern in PATTERNS.items()}


def active():
    data = db(["jobs", "list-runs", "--active-only"])
    runs = data if isinstance(data, list) else data.get("runs", [])
    return [
        (run.get("run_id"), run.get("run_name"), run.get("state", {}).get("life_cycle_state"))
        for run in runs
    ]


def emit(number):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tester, tester_lc, tester_result = state(TESTER_RUN)
    pipeline, pipeline_lc, pipeline_result = state(PIPELINE_RUN)
    started = tester.get("start_time", 0) / 1000
    elapsed = round((time.time() - started) / 60, 1) if started else None
    signatures = scan()
    peers = active()
    terminal = tester_lc in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED")
    red = signatures["soft_accept"] + signatures["cycles"] + signatures["silos"]
    probability = max(0, 100 - signatures["soft_accept"] * 5 - signatures["cycles"] * 5 - signatures["silos"] * 10)
    if not terminal and pipeline_lc == "TERMINATED" and pipeline_result == "SUCCESS":
        probability = min(probability, 70)
    lines = [
        f"HEARTBEAT v457 #{number} {now}",
        f"tester={TESTER_RUN} attempt=1/1 state={tester_lc}/{tester_result} elapsed_min={elapsed}",
        f"pipeline={PIPELINE_RUN} attempt=1/1 state={pipeline_lc}/{pipeline_result}",
        f"signatures={json.dumps(signatures, sort_keys=True)}",
        f"active_runs={json.dumps(peers)}",
        f"success_probability={probability}% red_signature_count={red}",
    ]
    if not terminal and pipeline_lc == "TERMINATED" and pipeline_result == "SUCCESS":
        lines.append("stage=POST-PIPELINE WAIT possible_stall=true evidence=no_active_child+empty_tester_results")
    block = "\n".join(lines)
    print(block, flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a") as handle:
        handle.write(block + "\n")
    return terminal


def main():
    number = 1
    while True:
        if emit(number):
            print("MONITOR_TERMINAL tester reached terminal state", flush=True)
            return
        number += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
