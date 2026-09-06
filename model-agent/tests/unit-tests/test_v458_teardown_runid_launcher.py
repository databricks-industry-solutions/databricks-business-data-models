import concurrent.futures
import gc
import importlib.util
import threading
import time
from pathlib import Path

from notebook_source_util import exec_function_namespace


REPO = Path(__file__).resolve().parents[2]


class Logger:
    def __init__(self):
        self.lines = []
        self.handlers = []

    def warning(self, message):
        self.lines.append(message)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_active_v457_launchers_separate_session_and_task_run_ids():
    wcb = _load(
        REPO / "runner" / "launch_wcb_alberta_v457_myadp.py",
        "launch_wcb_v457_for_test",
    )
    tester = _load(
        REPO / "runner" / "launch_vibe_tester_v457_myadp.py",
        "launch_tester_v457_for_test",
    )

    assert (
        wcb.build_spec()["tasks"][0]["notebook_task"]["base_parameters"][
            "databricks_task_run_id"
        ]
        == "{{task.run_id}}"
    )
    assert (
        tester.build_spec()["tasks"][0]["notebook_task"]["base_parameters"][
            "databricks_task_run_id"
        ]
        == "{{task.run_id}}"
    )


def test_generated_uuid_is_rejected_as_jobs_run_id():
    validate = exec_function_namespace("_v458_validate_jobs_run_id")[
        "_v458_validate_jobs_run_id"
    ]

    assert validate("74633503090396") == "74633503090396"
    assert validate("4a724d54-8bc4-4f2c-8bd7-33c2018a57d5") == ""
    assert validate("{{job.run_id}}") == ""
    assert validate("") == ""


def test_bounded_teardown_reports_lingering_executor(monkeypatch):
    capture = exec_function_namespace("_v397_capture_teardown_state")[
        "_v397_capture_teardown_state"
    ]
    release = threading.Event()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(lambda: release.wait(30))
    logger = Logger()
    monkeypatch.setattr(gc, "get_objects", lambda: [executor])

    started = time.monotonic()
    try:
        capture({"logger": logger}, source="v458-unit")
        elapsed = time.monotonic() - started
        assert 7.5 <= elapsed < 10.0
        assert any(
            "[teardown-drain-bounded FIRED v4.5.8]" in line
            and "ThreadPoolExecutor" in line
            for line in logger.lines
        )
    finally:
        release.set()
        future.result(timeout=3)
