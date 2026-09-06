#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime, timezone

PROFILE = "my-adp"
INTERVAL = 900
PARENT_RUN = 1049584180132908
CHILD_RUN = 911404721368368


def db(args):
    result = subprocess.run(
        ["databricks", *args, "--profile", PROFILE, "-o", "json"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode:
        return None
    return json.loads(result.stdout)


def emit(number):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parent = db(["jobs", "get-run", str(PARENT_RUN)]) or {}
    child = db(["jobs", "get-run", str(CHILD_RUN)]) or {}
    parent_state = parent.get("state", {})
    child_state = child.get("state", {})
    tasks = [
        {
            "task": task.get("task_key"),
            "attempt": int(task.get("attempt_number", 0)) + 1,
            "state": task.get("state", {}).get("life_cycle_state"),
            "result": task.get("state", {}).get("result_state"),
        }
        for task in child.get("tasks", [])
    ]
    print(
        f"HEARTBEAT WCB v457 #{number} {now}\n"
        f"parent={PARENT_RUN} state={parent_state.get('life_cycle_state')}/{parent_state.get('result_state')}\n"
        f"child={CHILD_RUN} state={child_state.get('life_cycle_state')}/{child_state.get('result_state')} "
        f"tasks={json.dumps(tasks)}",
        flush=True,
    )
    return parent_state.get("life_cycle_state") in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED")


def main():
    number = 1
    while True:
        if emit(number):
            print("MONITOR_TERMINAL WCB v457 reached terminal state", flush=True)
            return
        number += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
