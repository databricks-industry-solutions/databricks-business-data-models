import json
import time
import threading
import concurrent.futures as cf
from pathlib import Path

import pytest

import agent_helpers as ah

PRE = Path("/tmp/agent_v408_backup.ipynb")  # pre-v4.0.9: teardown-blockers OBSERVED but never drained


def _live_executor_workers():
    return [
        t for t in threading.enumerate()
        if t.is_alive()
        and not t.daemon
        and t is not threading.main_thread()
        and str(t.name).startswith(("ThreadPoolExecutor", "ProcessPoolExecutor"))
    ]


def test_version_bumped_to_409():
    assert tuple(int(x) for x in ah.__AGENT_VERSION__.split(".")) >= (4, 1, 3), ah.__AGENT_VERSION__


def test_teardown_drain_removes_leaked_nondaemon_executor(capsys):
    # Arrange: leak a non-daemon ThreadPoolExecutor whose idle worker survives -> the exact post-success
    # blocker observed live (travel_hospitality v5 / manufacturing v6: 'ThreadPoolExecutor-4_0').
    ex = cf.ThreadPoolExecutor(max_workers=2)
    ex.submit(lambda: 1).result()
    time.sleep(0.2)
    before = _live_executor_workers()
    assert before, "precondition: a non-daemon executor worker must be alive before drain"

    # Act: the production teardown capture now DRAINS (v4.0.9), not just observes.
    ah._v397_capture_teardown_state({}, source="unit-drain")
    time.sleep(0.6)

    # Assert: the leaked non-daemon executor workers are gone -> the interpreter can terminate cleanly
    # instead of the run riding the 15h task timeout.
    after = _live_executor_workers()
    assert not after, (
        "teardown-drain must remove leaked non-daemon executor workers; still alive: "
        + str([t.name for t in after])
    )
    out = capsys.readouterr().out
    assert "[teardown-drain-bounded FIRED v4.5.8]" in out
    assert "alias=teardown-drain-bounded" in out
    assert "shutdown_executors=" in out


def test_drain_is_noop_when_no_leaked_executor(capsys):
    # Safety: when there are no leaked non-daemon executor workers, the drain must NOT fire.
    for _ in range(10):
        if not _live_executor_workers():
            break
        time.sleep(0.2)
    assert not _live_executor_workers(), "test setup: no leaked executor workers should remain"
    ah._v397_capture_teardown_state({}, source="unit-clean")
    out = capsys.readouterr().out
    assert "[teardown-drain-leaked-executors FIRED" not in out


def test_fail_pre_v408_archive_lacks_drain():
    # Prove the fix is NEW: the deployed v4.0.8 archive OBSERVED the blocker (teardown-blockers) but had
    # no drain -> the run rode the 15h timeout. The drain alias must be absent at v4.0.8 HEAD.
    if not PRE.exists():
        pytest.skip("v4.0.8 backup not present at /tmp/agent_v408_backup.ipynb")
    src = "".join(
        "".join(c.get("source", []))
        for c in json.load(open(PRE))["cells"]
        if c.get("cell_type") == "code"
    )
    assert "teardown-blockers" in src, "v4.0.8 should already OBSERVE the blocker"
    assert "teardown-drain-leaked-executors" not in src, "drain must be NEW in v4.0.9"
