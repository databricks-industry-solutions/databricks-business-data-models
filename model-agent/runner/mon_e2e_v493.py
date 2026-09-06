#!/usr/bin/env python3
"""Poll the v4.8.3 end-to-end run and mirror its volume logs locally.

Separate from launch_e2e_v493.py so a dead launcher shell never orphans the monitoring
of a run that is still alive server-side (which is exactly what happened at 17:38Z).
"""
import json
import os
import re
import subprocess
import sys
import time

PROFILE = "my-uae"
RUN_ID = str(json.load(open("/tmp/e2e492_run.json"))["run_id"])
CATALOG = "vibe_e2e_v493"
BUSINESS = "coffee_roastery"
MIRROR = "/tmp/e2e492_logs"
PULSES = "/tmp/e2e492_pulses.txt"
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


# Substring counts. Never put a signature with regex metacharacters here.
LITERAL_SIGNALS = (
        ("v493-physical-names-before-modeljson FIRED", "v493 names resolved pre-serialization"),
        ("fidelity-rollback-flag-clear FIRED", "v492 rollback latch cleared"),
        ("v487-colname-rename-sync FIRED", "v487 stale column_name resynced"),
        ("canonical-reconcile DRIFT", "physical/memory column drift"),
        ("mv-column-rename-before-prune FIRED", "v486 rename instead of prune"),
        ("shrink-guard-user-king FIRED", "v493 shrink-guard user-king"),
        ("selffixer-commit-reject", "selffixer mutation rejected"),
        ("selffixer-applied", "selffixer mutation applied"),
        ("duplicate_product_name", "v489 same-domain dup caught"),
        ("SAME-DOMAIN duplicate", "v489 dup label correct"),
        ("mv-column-prevalidate-prune FIRED", "column pruned (rename impossible)"),
        ("mv-inflight-repair-persist FIRED", "v493 repair captured"),
        ("mv-artifact-mirrors-executed FIRED", "v493 artifact rewritten"),
        ("mv-strict-parity-repair FIRED", "parity repair"),
        ("[Metrics] Retry succeeded", "mv repaired in flight"),
        ("[Metrics] Failed metric view", "R6 mv failed"),
        ("verifier-relation-target-resolvable FIRED", "v482 guard fired"),
        ("SparkException: The responseFormat is invalid", "F-responseFormat"),
        ("Fidelity gates FAILED", "N2 fidelity"),
        ("dup-product-same-domain-merge FIRED", "v493 same-domain dup merged"),
        ("immutable-merge-same-entity-allowed FIRED", "v493 dedup merge allowed"),
        ("duplicate_product_name", "dup-name gate finding"),
        ("Traceback (most recent", "traceback"),
)

# Counted-variant signatures. Three literals in the v4.8.x monitors under-reported
# silently and made my pulses dishonest:
#   "Found 1 cycle(s)"          -> a run with 2+ cycles scanned as ZERO cycles.
#   "SILOED TABLES DETECTED"    -> never emitted; the real line is
#                                  "Found N global siloed table(s) (no incoming AND ...)".
#   "Max retries (3) exhausted" -> misses "Max retries reached. Proceeding with N siloed
#                                  table(s)" and the {max_attempts} variants.
REGEX_SIGNALS = tuple(
    (re.compile(p), label)
    for p, label in (
        (r"Max retries[^\n]{0,40}(?:exhausted|reached)", "F2 soft-accept"),
        # Anchored on "Found N" because the healthy line is "No global siloed tables found",
        # which a bare "global siloed table" substring flags as a defect.
        (r"SILOED TABLES DETECTED|Found [1-9]\d* global siloed table", "F4 silo"),
        (r"Found [1-9]\d* cycle\(s\)", "R8 cycle"),
        (r"Found [1-9]\d* DIRECT BIDIRECTIONAL", "bidirectional FK"),
    )
)


def scan():
    hits = {}
    bodies = []
    for fn in os.listdir(MIRROR) if os.path.isdir(MIRROR) else []:
        if not fn.endswith(".log"):
            continue
        try:
            bodies.append(open(os.path.join(MIRROR, fn), errors="ignore").read())
        except Exception:
            pass
    for pat, label in LITERAL_SIGNALS:
        n = sum(b.count(pat) for b in bodies)
        if n:
            hits[label] = n
    for rx, label in REGEX_SIGNALS:
        n = sum(len(rx.findall(b)) for b in bodies)
        if n:
            hits[label] = n
    return hits


INVARIANTS_RE = re.compile(r"\[INVARIANTS:(\w+)\][^\n]*?warnings=(\d+), unlinked=(\d+), siloed=(\d+), cycles=(\d+)")


def invariants():
    """Last deterministic invariants line per stage.

    Authoritative over the scattered warning lines: mid-flight counts (e.g. 21 unlinked
    _id columns) are transient and repaired later, so scanning warnings alone reports
    defects that no longer exist at finalize.
    """
    latest = {}
    for fn in os.listdir(MIRROR) if os.path.isdir(MIRROR) else []:
        if not fn.endswith(".log"):
            continue
        try:
            body = open(os.path.join(MIRROR, fn), errors="ignore").read()
        except Exception:
            continue
        for stage, w, u, s, c in INVARIANTS_RE.findall(body):
            latest[stage] = f"w={w} unlinked={u} silo={s} cyc={c}"
    return latest


def main():
    pulse(f"MONITOR START run={RUN_ID} catalog={CATALOG}")
    while True:
        lc, rs, tasks = run_state()
        sizes = mirror()
        hits = scan()
        inv = invariants()
        pulse(f"lc={lc} result={rs} tasks={tasks} bytes={sizes} signals={hits} invariants={inv}")
        if lc in TERMINAL:
            pulse(f"TERMINAL lc={lc} result={rs}")
            return 0
        time.sleep(180)


if __name__ == "__main__":
    sys.exit(main())
