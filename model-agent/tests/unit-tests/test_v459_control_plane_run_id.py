import ast
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from notebook_source_util import exec_functions_namespace


REPO = Path(__file__).resolve().parents[2]
TESTER = REPO / "tests" / "vibe_tester.ipynb"
RUNNER = REPO / "runner" / "vibe_runner.ipynb"


def _notebook_source(path):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source"), list)
        else cell.get("source", "")
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def _exec_notebook_function(path, function_name):
    source = _notebook_source(path)
    tree = ast.parse(source)
    node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    segment = ast.get_source_segment(source, node)
    namespace = {}
    exec(compile(segment, str(path), "exec"), namespace)
    return namespace[function_name]


def _exec_notebook_functions(path, function_names, extra_globals=None):
    source = _notebook_source(path)
    tree = ast.parse(source)
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in function_names
    ]
    namespace = dict(extra_globals or {})
    segments = [ast.get_source_segment(source, node) for node in nodes]
    exec(compile("\n\n".join(segments), str(path), "exec"), namespace)
    return namespace


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_numeric_vibe_session_id_cannot_arm_self_cancel():
    namespace = exec_functions_namespace(
        ["_v458_validate_jobs_run_id", "_v459_resolve_self_cancel_run_id"]
    )
    emitted = []

    run_id, source = namespace["_v459_resolve_self_cancel_run_id"](
        "", "", "74633503090396", emitted.append
    )

    assert (run_id, source) == ("", "")
    assert emitted == [
        "[self-cancel-session-id-rejected FIRED v4.5.9] "
        "source=vibe_session_id control_plane_cancel=not_armed "
        "alias=self-cancel-session-id-rejected"
    ]


def test_dedicated_numeric_task_run_id_arms_self_cancel():
    namespace = exec_functions_namespace(
        ["_v458_validate_jobs_run_id", "_v459_resolve_self_cancel_run_id"]
    )

    assert namespace["_v459_resolve_self_cancel_run_id"](
        "", "74633503090396", "918273645"
    ) == ("74633503090396", "task_run_param")


def test_context_run_id_remains_first_priority():
    namespace = exec_functions_namespace(
        ["_v458_validate_jobs_run_id", "_v459_resolve_self_cancel_run_id"]
    )

    assert namespace["_v459_resolve_self_cancel_run_id"](
        "111", "222", "333"
    ) == ("111", "context")


def test_missing_context_and_dedicated_id_does_not_arm():
    namespace = exec_functions_namespace(
        ["_v458_validate_jobs_run_id", "_v459_resolve_self_cancel_run_id"]
    )

    assert namespace["_v459_resolve_self_cancel_run_id"]("", "", "") == ("", "")


def test_tester_common_boundary_injects_task_run_reference():
    inject = _exec_notebook_function(TESTER, "_v459_inject_control_plane_run_id")
    original = {"vibe_session_id": "918273645", "operation": "new base model"}

    injected = inject(original, "74633503090396")

    assert injected["databricks_task_run_id"] == "74633503090396"
    assert injected["vibe_session_id"] == "918273645"
    assert original == {
        "vibe_session_id": "918273645",
        "operation": "new base model",
    }
    source = _notebook_source(TESTER)
    assert 'dbutils.widgets.get("databricks_task_run_id")' in source
    assert "params = _v459_inject_control_plane_run_id(" in source


def test_runner_common_task_builder_injects_every_task_run_reference():
    class NotebookTask:
        def __init__(self, **values):
            self.__dict__.update(values)

    class Task:
        def __init__(self, **values):
            self.__dict__.update(values)

    class JobsService:
        def __init__(self):
            self.created = None

        def list(self, name):
            return []

        def create(self, **values):
            self.created = values
            return SimpleNamespace(job_id=123)

        def run_now(self, job_id):
            return SimpleNamespace(run_id=456)

    jobs_module = SimpleNamespace(
        Task=Task,
        NotebookTask=NotebookTask,
        TaskDependency=lambda task_key: SimpleNamespace(task_key=task_key),
        JobSettings=lambda **values: SimpleNamespace(**values),
    )
    namespace = _exec_notebook_functions(
        RUNNER,
        {"_v459_with_control_plane_run_id", "find_or_create_job"},
        {"jobs": jobs_module, "JOB_TIMEOUT_SECONDS": 100, "log": lambda message: None},
    )
    service = JobsService()
    workspace = SimpleNamespace(jobs=service)
    task_configs = [
        {"task_key": "one", "params": {"vibe_session_id": "111"}},
        {"task_key": "two", "params": {"vibe_session_id": "222"}},
    ]

    namespace["find_or_create_job"](
        workspace, "test", "/agent", {}, {}, task_configs=task_configs
    )

    assert [
        task.notebook_task.base_parameters["databricks_task_run_id"]
        for task in service.created["tasks"]
    ] == ["{{task.run_id}}", "{{task.run_id}}"]
    assert [
        task.notebook_task.base_parameters["vibe_session_id"]
        for task in service.created["tasks"]
    ] == ["111", "222"]


def test_launchers_keep_correlation_and_add_task_identity():
    launcher_paths = [
        REPO / "runner" / "launch_vibe_tester_v457_myadp.py",
        REPO / "runner" / "launch_wcb_alberta_v457_myadp.py",
    ]
    for index, path in enumerate(launcher_paths):
        module = _load(path, f"v459_launcher_{index}")
        params = module.build_spec()["tasks"][0]["notebook_task"]["base_parameters"]
        assert params["vibe_session_id"] == "{{job.run_id}}"
        assert params["databricks_task_run_id"] == "{{task.run_id}}"
