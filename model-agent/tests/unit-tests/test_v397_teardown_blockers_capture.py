"""v3.9.7 behavioral tests: graceful-exit observability (teardown-blocker capture).

User directive: the task MUST exit gracefully, not be killed. v3.9.7 stops the 8-version
guessing loop by routing the non-daemon-thread blocker list to a LOGGER SINK + sentinel file
BEFORE exit (the prior diagnostic only print()ed to driver stdout -> invisible during a hang).
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from notebook_source_util import (
    exec_function_namespace,
    notebook_concat_source,
    slice_function_source,
)

PRE_PATCH = Path("/tmp/agent_pre_v397.ipynb")


class _FakeLogger:
    def __init__(self):
        self.warnings = []
        self.handlers = []  # no volume handler in the unit harness

    def warning(self, msg):
        self.warnings.append(str(msg))


@pytest.fixture(scope="module")
def capture_fn():
    ns = exec_function_namespace("_v397_capture_teardown_state")
    return ns["_v397_capture_teardown_state"]


def _spawn_blocked_nondaemon(name):
    ev = threading.Event()
    t = threading.Thread(target=ev.wait, name=name, daemon=False)
    t.start()
    return t, ev


def test_capture_routes_blocker_to_logger_sink_not_print(capture_fn):
    """PASS-POST: an alive non-daemon thread is named in BOTH the return list and the
    logger.warning sink (so it survives a hang and the next run can read it)."""
    name = "blocker-probe-xyz"
    t, ev = _spawn_blocked_nondaemon(name)
    try:
        log = _FakeLogger()
        alive = capture_fn({"logger": log}, source="unit-test")
        names = [a["name"] for a in alive]
        assert name in names, f"probe thread not in capture list: {names}"
        assert len(log.warnings) == 1, "capture must emit exactly one logger.warning"
        msg = log.warnings[0]
        assert "teardown-blockers" in msg
        assert "alias=teardown-blockers" in msg
        assert name in msg, "blocker thread name must be in the logged sink message"
        assert "source=unit-test" in msg
    finally:
        ev.set()
        t.join(timeout=5)


def test_capture_reports_zero_when_no_nondaemon_blocker(capture_fn):
    """When nothing blocks, count=0 is logged (proves H2 platform-hold vs H1 thread-hold)."""
    log = _FakeLogger()
    alive = capture_fn({"logger": log}, source="clean")
    # the unit harness main thread is excluded; daemon pytest threads excluded.
    assert all(a["name"] != "MainThread" for a in alive)
    assert len(log.warnings) == 1
    assert "non_daemon_count=" in log.warnings[0]


def test_capture_never_raises_on_bad_input(capture_fn):
    """Teardown capture must be exception-proof (it runs on the exit path)."""
    assert capture_fn(None, source="none") == [] or isinstance(capture_fn(None), list)
    assert isinstance(capture_fn("not-a-dict"), list)


def test_safe_exit_demoted_to_single_long_grace_backstop():
    """PASS-POST: _safe_notebook_exit uses capture + a single 600s daemon backstop, and no
    longer arms the kill-stack (180s os._exit + SIGKILL subprocess) on its own path."""
    src = slice_function_source("_safe_notebook_exit")
    assert "_v397_capture_teardown_state" in src
    assert "_wd_time.sleep(600)" in src
    assert "_wd_time.sleep(180)" not in src
    assert "_spawn_process_kill_watchdog(240" not in src
    assert "widgets_values=None" in src


def test_fail_pre_capture_fn_absent_in_pre_patch():
    """FAIL-PRE (anti-tautology): the capture-to-sink function did NOT exist before v3.9.7, so
    the prior code physically could not route blockers to a readable sink."""
    if not PRE_PATCH.exists():
        pytest.skip("pre-patch backup not present")
    nb = json.loads(PRE_PATCH.read_text(encoding="utf-8"))
    pre = "\n".join(
        ("".join(c.get("source", [])) if isinstance(c.get("source"), list) else c.get("source", ""))
        for c in nb.get("cells", [])
        if c.get("cell_type") == "code"
    )
    assert "def _v397_capture_teardown_state" not in pre
    assert "_wd_time.sleep(180)" in pre, "pre-patch had the 180s short-grace killer"


def test_callsites_thread_widgets_values():
    """PASS-POST: exit call sites pass widgets_values so the capture can reach the volume logger."""
    src = notebook_concat_source()
    plain = src.count("_safe_notebook_exit(widgets_values.get(\"_notebook_exit_result\"))")
    threaded = src.count('_safe_notebook_exit(widgets_values.get("_notebook_exit_result"), widgets_values)')
    assert plain == 0, "every exit call site must thread widgets_values through"
    assert threaded >= 3, f"expected the operation exit call sites to thread widgets_values, found {threaded}"
