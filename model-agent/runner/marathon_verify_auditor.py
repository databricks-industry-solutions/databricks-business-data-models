#!/usr/bin/env python3
"""Independent log auditor for verification installs — ZERO-error gate."""
from __future__ import annotations

import os
import sys

os.environ.setdefault(
    "MARATHON_STATE_FILE",
    os.path.expanduser("~/claude/vibe-agent/install_marathon_verify_state.json"),
)
os.environ.setdefault(
    "MARATHON_AUDIT_FILE",
    os.path.expanduser("~/claude/vibe-agent/install_marathon_verify_audit.log"),
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from install_marathon import (  # noqa: E402
    load_state,
    reconcile_pool,
    run_independent_audit,
)


def main() -> int:
    state = load_state()
    reconcile_pool(state)
    report = run_independent_audit(state, only_clean=True)
    print(
        f"audited={report['audited']} passed={report['passed']} "
        f"violations={report['failed']}"
    )
    if report["failed"]:
        for r in report["failures"]:
            print(f"  FAIL {r['key']}: {', '.join(r['issues'])}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
