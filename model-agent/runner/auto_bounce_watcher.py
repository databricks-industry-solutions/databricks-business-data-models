#!/usr/bin/env python3
"""
v0.7.4 (alias=auto-bounce-watcher) — auto-bounces AWS + Azure orchestrators to v0.7.4
the moment their current in-flight industry (Consumer Goods / Mining) lands in the repo.

Why: the user can't afford another Pharma-style 14h N5 timeout collision.
Existing AWS + Azure orchestrators are running pre-v0.7.4 code (14h sector timeout).
They CANNOT be bounced mid-MVM (would kill the in-flight industry).
This watcher polls the repo + manifests; once Consumer Goods lands, it bounces AWS.
Once Mining lands, it bounces Azure.

Run:  nohup python3 -u runner/auto_bounce_watcher.py > /Users/user/claude/vibe-agent/auto_bounce_watcher.log 2>&1 &
"""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_PATH = "/Users/user/Documents/projects/vibe-business-data-models"
LOG_FILE = "/Users/user/claude/vibe-agent/auto_bounce_watcher.log"
STATE_FILE = "/Users/user/claude/vibe-agent/auto_bounce_watcher_state.json"
PROJECT_ROOT = "/Users/user/Documents/projects/vibe-modelling-agent"

POLL_INTERVAL_S = 60
GLOBAL_VOLUME = "/Volumes/_root/default/root_vol"

TARGETS = [
    {
        "cloud": "AWS",
        "profile": "<profile>",
        "industry_snake": "consumer_goods",
        "industry_repo_dir": "consumer_goods",
        "sectors": "retail_and_consumer_goods,manufacturing",
        "runner_path": "/Users/user@example.com/vibe_runner_v73",
        "job_name": "dbx_vibe_modelling_sector_runner_v73_aws",
        "pulse_file": "/Users/user/claude/vibe-agent/aws_pulses.txt",
        "state_file": "/Users/user/claude/vibe-agent/aws_state.json",
        "stdout_log": "/Users/user/claude/vibe-agent/aws_orchestrator_stdout.log",
        "old_pid": 97464,
        "bounced": False,
    },
    {
        "cloud": "AZURE",
        "profile": "fe-vm-feip",
        "industry_snake": "mining",
        "industry_repo_dir": "mining",
        "sectors": "energy_and_utilities,public_sector_education_nonprofit,communications_media_entertainment,manufacturing",
        "runner_path": "/Users/user@example.com/vibe_runner_v72",
        "job_name": "dbx_vibe_modelling_sector_runner_v72_azure",
        "pulse_file": "/Users/user/claude/vibe-agent/azure_pulses.txt",
        "state_file": "/Users/user/claude/vibe-agent/azure_state.json",
        "stdout_log": "/Users/user/claude/vibe-agent/azure_orchestrator_stdout.log",
        "old_pid": 33226,
        "bounced": False,
    },
]


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    line = f"[{now_utc()}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def industry_in_repo(industry_dir):
    p = os.path.join(REPO_PATH, industry_dir)
    return os.path.isdir(p) and os.path.isdir(os.path.join(p, "ecm_v1")) and os.path.isdir(os.path.join(p, "mvm_v1"))


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def manifest_says_done(profile, industry_snake):
    """Check if the orchestrator's _manifest.json on the global volume marks the
    industry as fully successful with healthy file counts."""
    remote = f"dbfs:{GLOBAL_VOLUME}/{industry_snake}/_manifest.json"
    local = f"/tmp/abw_check_{industry_snake}_{int(time.time())}.json"
    try:
        if os.path.isfile(local):
            os.remove(local)
        out = subprocess.run(
            ["databricks", "fs", "cp", remote, local, "--overwrite", "--profile", profile],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0 or not os.path.isfile(local):
            return False
        m = json.loads(Path(local).read_text())
        rm = m.get("run_metadata", {})
        if not rm.get("all_tasks_succeeded"):
            return False
        fc = m.get("files_copied", 0)
        ecm = m.get("scopes", {}).get("ecm_v1", {}).get("files", 0)
        mvm = m.get("scopes", {}).get("mvm_v1", {}).get("files", 0)
        return fc >= 30 and ecm >= 20 and mvm >= 15
    except Exception as e:
        log(f"  [{profile}] manifest_says_done error: {e}")
        return False
    finally:
        try:
            os.remove(local)
        except OSError:
            pass


def cancel_orphan_sector_runners(profile, job_name, cloud):
    """v0.7.4 (alias=auto-bounce-cancel-old-sector-runner) — when bouncing an
    orchestrator, the orchestrator PROCESS is killed but the in-flight
    sector_runner JOB it submitted KEEPS RUNNING in Databricks until terminal,
    driving its own retry loop and spawning fresh pipeline children. Those
    children would then COLLIDE with the new orchestrator's pipeline children
    on the same industry catalog. So we cancel any active sector_runner job
    matching the orchestrator's job_name BEFORE launching the new instance."""
    try:
        out = subprocess.run(
            ["databricks", "jobs", "list-runs", "--active-only", "--limit", "25",
             "--profile", profile, "-o", "json"],
            capture_output=True, text=True, timeout=180,
        )
        if out.returncode != 0:
            log(f"  [{cloud}] list-runs failed: {out.stderr[:200]}")
            return
        d = json.loads(out.stdout)
        runs = d if isinstance(d, list) else d.get("runs", [])
        for r in runs:
            rn = r.get("run_name", "") or ""
            if rn == job_name:
                rid = r.get("run_id")
                log(f"  [{cloud}] cancelling old sector_runner RID={rid} (job_name={rn})")
                cc = subprocess.run(
                    ["databricks", "jobs", "cancel-run", str(rid), "--profile", profile],
                    capture_output=True, text=True, timeout=60,
                )
                if cc.returncode == 0:
                    log(f"  [{cloud}] sector_runner RID={rid} cancelled")
                else:
                    log(f"  [{cloud}] sector_runner cancel error: {cc.stderr[:200]}")
            elif rn.startswith("dbx_vibe_") and "_pipeline_" in rn:
                rid = r.get("run_id")
                log(f"  [{cloud}] cancelling orphan child pipeline RID={rid} ({rn[:60]})")
                subprocess.run(
                    ["databricks", "jobs", "cancel-run", str(rid), "--profile", profile],
                    capture_output=True, text=True, timeout=60,
                )
    except Exception as e:
        log(f"  [{cloud}] cancel_orphan_sector_runners error: {e}")


def bounce(target):
    cloud = target["cloud"]
    log(f"=== {cloud}: bouncing orchestrator to v0.7.4 ===")
    old_pid = target["old_pid"]
    if pid_alive(old_pid):
        log(f"  [{cloud}] killing old PID={old_pid}")
        try:
            os.kill(old_pid, signal.SIGTERM)
            time.sleep(5)
            if pid_alive(old_pid):
                log(f"  [{cloud}] SIGTERM didn't kill, trying SIGKILL")
                os.kill(old_pid, signal.SIGKILL)
                time.sleep(2)
        except Exception as e:
            log(f"  [{cloud}] kill error: {e}")
    else:
        log(f"  [{cloud}] old PID={old_pid} not alive, skipping kill")

    cancel_orphan_sector_runners(target["profile"], target["job_name"], cloud)

    backup = f"{target['stdout_log']}.pre-bounce-{int(time.time())}.bak"
    if os.path.isfile(target["stdout_log"]):
        os.rename(target["stdout_log"], backup)
        log(f"  [{cloud}] backed up stdout log to {backup}")

    cmd = [
        "python3", "-u", "runner/orchestrate_sectors.py",
        "--profile", target["profile"],
        "--runner-path", target["runner_path"],
        "--job-name", target["job_name"],
        "--sectors", target["sectors"],
        "--pulse-file", target["pulse_file"],
        "--state-file", target["state_file"],
    ]
    log(f"  [{cloud}] launching: {' '.join(cmd)}")
    with open(target["stdout_log"], "w") as fout:
        proc = subprocess.Popen(
            cmd, cwd=PROJECT_ROOT, stdout=fout, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    log(f"  [{cloud}] new PID={proc.pid} (detached)")
    target["bounced"] = True
    target["new_pid"] = proc.pid
    persistent = load_persistent_state()
    persistent[cloud] = {"bounced": True, "new_pid": proc.pid, "ts": now_utc()}
    save_persistent_state(persistent)
    log(f"=== {cloud}: bounce complete (state persisted) ===")


def load_persistent_state():
    """v0.7.4 (alias=auto-bounce-state-persistence) — survives watcher restarts.
    Without persistence, killing+relaunching the watcher (e.g. for a code reload)
    causes the new watcher to forget which targets it already bounced. It then
    re-bounces them, which (a) re-cancels the now-LEGITIMATE child pipelines of
    the freshly-bounced orchestrator and (b) submits a duplicate sector_runner
    that conflicts with the running one. This bug manifested at 11:59:35 UTC
    on 2026-05-05 when the watcher killed a 17-min-old Apparel Fashion run."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_persistent_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"  WARN failed to save persistent state: {e}")


def main():
    log("=== auto_bounce_watcher started ===")
    log(f"Watching: {[t['cloud'] for t in TARGETS]}")

    persistent = load_persistent_state()
    for target in TARGETS:
        cloud = target["cloud"]
        if persistent.get(cloud, {}).get("bounced"):
            target["bounced"] = True
            target["new_pid"] = persistent[cloud].get("new_pid")
            log(f"  [{cloud}] persistent state says ALREADY BOUNCED (new_pid={target['new_pid']}) — skip")

    while True:
        all_done = True
        for target in TARGETS:
            if target["bounced"]:
                continue
            all_done = False
            cloud = target["cloud"]
            ind_snake = target["industry_snake"]
            ind_dir = target["industry_repo_dir"]
            in_repo = industry_in_repo(ind_dir)
            in_manifest = manifest_says_done(target["profile"], ind_snake)
            if in_repo:
                log(f"  [{cloud}] {ind_snake} IN REPO ✓ — bouncing now")
                bounce(target)
            elif in_manifest:
                log(f"  [{cloud}] {ind_snake} manifest GREEN ✓ but not yet in repo (waiting for sync)")
            else:
                log(f"  [{cloud}] {ind_snake} not yet done (no repo dir, no green manifest) — wait")
        if all_done:
            log("=== all targets bounced — exiting ===")
            break
        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
