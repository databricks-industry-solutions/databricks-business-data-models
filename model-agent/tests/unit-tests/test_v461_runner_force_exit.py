import ast
import json
import threading
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "runner" / "vibe_runner.ipynb"
TESTER = REPO / "tests" / "vibe_tester.ipynb"


def _notebook(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source(path):
    parts = []
    for cell in _notebook(path)["cells"]:
        if cell.get("cell_type") != "code":
            continue
        value = cell.get("source", "")
        parts.append("".join(value) if isinstance(value, list) else value)
    return "\n\n".join(parts)


def _function_source(path, name):
    source = _source(path)
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    lines = source.splitlines(keepends=True)
    return "".join(lines[node.lineno - 1:node.end_lineno])


def _functions(path, names, extra=None):
    namespace = {} if extra is None else dict(extra)
    code = "\n\n".join(_function_source(path, name) for name in names)
    exec(compile(code, str(path), "exec"), namespace)
    return namespace


def test_runner_success_arms_watchdog_before_parseable_notebook_exit(monkeypatch):
    events = []
    logs = []

    class FakeThread:
        def __init__(self, **kwargs):
            events.append(("created", kwargs["name"], kwargs["daemon"]))

        def start(self):
            events.append(("started",))

    monkeypatch.setattr(threading, "Thread", FakeThread)
    namespace = _functions(
        RUNNER,
        [
            "_v461_runner_success_payload",
            "_v461_arm_runner_exit_watchdog",
            "_v461_finish_runner_success",
        ],
        {"json": json, "log": logs.append},
    )

    def notebook_exit(payload):
        events.append(("exit", payload))

    returned = namespace["_v461_finish_runner_success"](
        [{"industry": "tiny", "warning_count": 2}],
        12.3456,
        notebook_exit=notebook_exit,
        watchdog_grace_seconds=5,
    )

    assert events[0] == ("created", "runner_post_pipeline_exit_watchdog", True)
    assert events[1] == ("started",)
    assert events[2][0] == "exit"
    assert returned == events[2][1]
    payload = json.loads(returned)
    assert payload == {
        "status": "SUCCESS",
        "summary": {
            "industries_processed": 1,
            "industries": ["tiny"],
            "warning_count": 2,
            "elapsed_seconds": 12.346,
        },
    }
    assert any("[runner-post-child-terminal-complete FIRED v4.6.1]" in line for line in logs)
    assert any("[runner-post-pipeline-force-exit FIRED v4.6.1]" in line for line in logs)


def test_runner_main_exception_never_invokes_success_exit():
    final_cell = _notebook(RUNNER)["cells"][-1]["source"]
    final_source = "".join(final_cell) if isinstance(final_cell, list) else final_cell
    success_calls = []

    class FakeTime:
        @staticmethod
        def monotonic():
            return 1.0

    def failing_main():
        raise RuntimeError("child pipeline failed")

    with pytest.raises(RuntimeError, match="child pipeline failed"):
        exec(
            compile(final_source, str(RUNNER), "exec"),
            {
                "__name__": "__main__",
                "time": FakeTime(),
                "main": failing_main,
                "_v461_finish_runner_success": success_calls.append,
            },
        )

    assert success_calls == []


@pytest.mark.parametrize(
    "payload,error_type",
    [
        ("", ValueError),
        ("not-json", ValueError),
        (json.dumps({"status": "FAILED", "summary": {"reason": "x"}}), RuntimeError),
        (json.dumps({"status": "SUCCESS", "summary": {}}), ValueError),
    ],
)
def test_tester_rejects_malformed_or_non_success_runner_payload(payload, error_type):
    validate = _functions(
        TESTER,
        ["_v461_validate_runner_payload"],
        {"json": json},
    )["_v461_validate_runner_payload"]

    with pytest.raises(error_type):
        validate(payload)


def test_tester_accepts_runner_success_payload():
    validate = _functions(
        TESTER,
        ["_v461_validate_runner_payload"],
        {"json": json},
    )["_v461_validate_runner_payload"]
    raw = json.dumps({"status": "SUCCESS", "summary": {"industries_processed": 1}})

    assert validate(raw)["summary"]["industries_processed"] == 1


def test_dry_run_generated_notebook_still_exits_with_original_value():
    create_source = _function_source(RUNNER, "create_dry_run_notebook")
    create_tree = ast.parse(create_source)
    notebook_content = next(
        node.value.value
        for node in ast.walk(create_tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "notebook_content" for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )
    dry_tree = ast.parse(notebook_content)
    exit_node = next(
        node
        for node in ast.walk(dry_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "exit"
    )
    exit_values = []

    class Notebook:
        def exit(self, value):
            exit_values.append(value)

    class Dbutils:
        notebook = Notebook()

    exit_module = ast.fix_missing_locations(
        ast.Module(body=[ast.Expr(value=exit_node)], type_ignores=[])
    )
    exec(
        compile(exit_module, "<dry-run-exit>", "exec"),
        {"dbutils": Dbutils(), "business_name": "tiny", "operation": "new base model"},
    )

    assert exit_values == ["DRY_RUN_OK: tiny - new base model"]
