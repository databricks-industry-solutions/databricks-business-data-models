#!/usr/bin/env python3
"""Standalone 15-minute heartbeat — verification or marathon state via env."""
from __future__ import annotations

import os
import sys
import time

os.environ.setdefault(
    "MARATHON_STATE_FILE",
    os.path.expanduser("~/claude/vibe-agent/install_marathon_v2_state.json"),
)
os.environ.setdefault(
    "MARATHON_HEARTBEAT_FILE",
    os.path.expanduser("~/claude/vibe-agent/install_marathon_heartbeat.log"),
)
os.environ.setdefault(
    "MARATHON_HEARTBEAT_STATE_FILE",
    os.path.expanduser("~/claude/vibe-agent/install_marathon_heartbeat_state.json"),
)
os.environ.setdefault(
    "MARATHON_AUDIT_FILE",
    os.path.expanduser("~/claude/vibe-agent/install_marathon_verify_audit.log"),
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from install_marathon import (  # noqa: E402
    HEARTBEAT_FILE,
    HEARTBEAT_INTERVAL_S,
    emit_marathon_heartbeat,
    load_state,
    pulse,
)


def main() -> None:
    interval = int(os.environ.get("MARATHON_HEARTBEAT_S", HEARTBEAT_INTERVAL_S))
    pulse(f"[heartbeat-daemon] every {interval}s -> {HEARTBEAT_FILE}")
    while True:
        try:
            state = load_state()
            block = emit_marathon_heartbeat(state)
            print(block, flush=True)
        except Exception as e:
            pulse(f"[heartbeat-daemon] error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
