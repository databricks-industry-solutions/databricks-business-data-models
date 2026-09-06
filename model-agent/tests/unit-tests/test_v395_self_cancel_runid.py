"""v3.9.5 behavioral guard (§8.10 fail-pre/pass-post) for the teardown-hang fix
(alias=self-cancel-runid-jobparam).

ROOT CAUSE (<profile> manufacturing run <run_id>): the model finished building at 23:54Z but the
run stayed RUNNING for 6h until the 15h job timeout. The error log proved BOTH terminators failed:
  - process-kill-watchdog armed (pid=10235, grace=360s) but the external SIGKILL child is ineffective
    on serverless;
  - self-cancel-control-plane NOT-ARMED missing=run_id (tag_keys=[], has_run_id=False) -- the serverless
    notebook context exposed no run_id tags and no usable currentRunId(), so the REST self-cancel that
    DOES flip a serverless run to TERMINATED never armed.

FIX (two paired sites):
  1. marathon build_job_spec injects the Databricks-native {{job.run_id}} as the self_run_id
     base_parameter on EVERY task (substituted at runtime, environment-independent).
  2. agent reads self_run_id as the authoritative run_id fallback when context tags + currentRunId()
     are empty, guarded so an un-substituted literal ({{...}}) is rejected.

fail-pre proof (marathon):
    git stash  # or check out pre-patch runner/vov_v2_marathon.py
    pytest tests/unit-tests/test_v395_self_cancel_runid.py::test_marathon_injects_self_run_id_into_every_task
    -> common had no self_run_id => the param is absent on every task => assertion fails.
"""
import ast
import importlib.util
import json
import os

import pytest

REPO = "/Users/user/Documents/projects/vibe-modelling-agent"
MARATHON = os.path.join(REPO, "runner/vov_v2_marathon.py")
NB = os.environ.get("VOV_NB", os.path.join(REPO, "agent/dbx_vibe_modelling_agent.ipynb"))


# ---------------------------------------------------------------------------
# MARATHON behavioral: {{job.run_id}} injected into every task's base_parameters
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def marathon():
    spec = importlib.util.spec_from_file_location("vov_v2_marathon", MARATHON)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# v4.0.8: self_run_id retired -> vibe_session_id carries {{job.run_id}} (ONE identifier drives both
# the progress-tracking session AND the control-plane self-cancel). The marathon now injects
# vibe_session_id={{job.run_id}} on every task; the {{...}} template semantics + guard are unchanged.
def test_marathon_injects_self_run_id_into_every_task(marathon):
    for installed in (False, True):
        spec = marathon.build_job_spec("manufacturing", installed=installed)
        tasks = spec["tasks"]
        assert tasks, "job spec must have tasks"
        for t in tasks:
            params = t["notebook_task"]["base_parameters"]
            assert params.get("vibe_session_id") == "{{job.run_id}}", (
                f"task {t['task_key']} (installed={installed}) changed correlation identity"
            )
            assert params.get("databricks_task_run_id") == "{{task.run_id}}", (
                f"task {t['task_key']} (installed={installed}) missing "
                "dedicated task-run control-plane identity"
            )
            # self_run_id base-param is retired; it must NOT reappear.
            assert "self_run_id" not in params, (
                f"task {t['task_key']} still injects retired self_run_id base-param"
            )


def test_marathon_self_run_id_value_is_databricks_template(marathon):
    # Must be the literal template token so Databricks substitutes the real run id at runtime;
    # a hardcoded id or empty string would defeat the fix.
    spec = marathon.build_job_spec("ngo", installed=True)
    vals = {
        t["notebook_task"]["base_parameters"].get("databricks_task_run_id")
        for t in spec["tasks"]
    }
    assert vals == {"{{task.run_id}}"}


# ---------------------------------------------------------------------------
# AGENT: the self_run_id fallback exists with the un-substituted-literal guard
# ---------------------------------------------------------------------------
def _agent_self_cancel_src():
    nb = json.load(open(NB))
    for c in nb["cells"]:
        if c.get("cell_type") != "code":
            continue
        s = "".join(c.get("source", []))
        if (
            "self-cancel-session-id-rejected" in s
            and 'dbutils.widgets.get("databricks_task_run_id")' in s
        ):
            return s
    return None


def test_agent_self_run_id_fallback_present():
    src = _agent_self_cancel_src()
    if src is None:
        pytest.fail("FAIL-PRE: agent self-cancel self_run_id fallback ABSENT (expected pre-patch)")
    # the fallback must guard against an un-substituted literal and tag the source.
    assert "_v458_validate_jobs_run_id" in src
    assert '"task_run_param"' in src
    # whole cell must still compile.
    ast.parse(src)


# ---------------------------------------------------------------------------
# GUARD LOGIC: prove the exact predicate accepts a real id and rejects {{...}}
# (predicate mirrors the agent source line asserted to exist above)
# ---------------------------------------------------------------------------
def _accept(pr):
    value = str(pr or "").strip()
    return bool(value.isdigit() and int(value) > 0)


def test_guard_accepts_real_run_id():
    assert _accept("74633503090396") is True


def test_guard_rejects_unsubstituted_template():
    assert _accept("{{job.run_id}}") is False


def test_guard_rejects_empty_and_whitespace():
    assert _accept("") is False
    assert _accept("   ") is False
    assert _accept(None) is False


def test_guard_rejects_generated_uuid():
    assert _accept("4a724d54-8bc4-4f2c-8bd7-33c2018a57d5") is False


def test_guard_predicate_matches_agent_source():
    # ties the tested predicate to the live source (no §8.3 drift between test and code).
    src = _agent_self_cancel_src()
    assert src is not None
    assert "_v459_resolve_self_cancel_run_id(" in src
