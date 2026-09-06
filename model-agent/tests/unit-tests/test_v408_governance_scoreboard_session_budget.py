"""v4.0.8 behavioral tests — four root-cause fixes, fail-pre (v4.0.7) / pass-post (live).

  1. prompt-governance            — the 9 previously-ungoverned prompts (verifier fallbacks,
                                     selffixer_repair, subdomain/provenance/source-trace enforcers,
                                     self_ref_naming) are now routed in TECHNICAL_CONTEXT.prompts_models
                                     at thinker/large. In v4.0.7 they fell to _default_model_config:
                                     today that default IS thinker/large (matches the FIRST prompt
                                     VIBE_MASTER_PROMPT), so this is a DETERMINISM/robustness fix — it
                                     immunises the verifier prompts against default-drift if prompt
                                     order ever changes (which would silently route them to a weaker
                                     model). No prompt is downgraded. Proven behaviorally: a governed
                                     thinker/large requirement resolves to the thinker model EVEN WHEN
                                     the default is a worker model; an ungoverned prompt resolves to
                                     that worker default (the silent-degradation class the fix removes).
  2. scoreboard-persist-vibe-progress — the per-VREQ adherence scoreboard previously lived ONLY in the
                                     info-log as the 'vibe_orchestrator_scored' event; UI consumers read
                                     the _vibe_progress Delta table and never saw adherence. Now persisted
                                     via emit_step("Vibe Adherence Scoreboard", ...).
  3. self-cancel-reuse-vibe-session-id — the retired self_run_id base-param is folded into
                                     vibe_session_id (one identifier carries {{job.run_id}} for both the
                                     progress session AND the control-plane self-cancel).
  4. runtime-budget-config-base-param — runtime_budget_seconds removed from the operator widget surface;
                                     injected by BOTH launch paths (self-launcher + marathon) = the REAL
                                     task timeout so the per-VREQ verifier honours the full 15h budget
                                     instead of throttling at 4h (the marathon path never set it before).
"""
import json
import threading
from pathlib import Path

import agent_helpers as ah

from test_v406_verifier_false_negatives import _load_backup_module  # noqa: F401 (kept for parity)

PRE = Path("/tmp/agent_v407_backup.ipynb")  # committed v4.0.7 — no v4.0.8 fixes
MARATHON = Path(__file__).resolve().parents[2] / "runner" / "vov_v2_marathon.py"

GOVERNED_9 = [
    "VERIFIER_LLM_FALLBACK", "VERIFIER_LLM_FALLBACK_RESCUE", "selffixer_repair",
    "SUBDOMAIN_NAME_ENFORCE", "SUBDOMAIN_STEWARD_ENFORCE", "RE_PROVENANCE_ADD_MISSING",
    "SOURCE_TRACE_RESIDUAL_MAP", "SOURCE_TRACE_RESIDUAL_MAP_TBL", "self_ref_naming",
]


def _src(nb_path=None):
    p = Path(nb_path) if nb_path else Path(ah.__file__)
    if nb_path and not p.exists():
        import pytest
        pytest.skip(f"pre-patch backup {p} absent (ephemeral /tmp dev artifact); fail-pre half historical, pass-post protects live behavior")
    nb = json.loads(p.read_bytes().decode("utf-8"))
    return "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")


def _cell1(nb_path=None):
    p = Path(nb_path) if nb_path else Path(ah.__file__)
    if nb_path and not p.exists():
        import pytest
        pytest.skip(f"pre-patch backup {p} absent (ephemeral /tmp dev artifact); fail-pre half historical, pass-post protects live behavior")
    nb = json.loads(p.read_bytes().decode("utf-8"))
    return "".join(nb["cells"][1]["source"])


# ============================== version =====================================
def test_version_bumped_to_408():
    assert tuple(int(x) for x in ah.__AGENT_VERSION__.split(".")) >= (4, 1, 3), ah.__AGENT_VERSION__


def test_version_is_first_line_then_banner_POST():
    lines = _cell1().split("\n")
    assert lines[0].startswith('__AGENT_VERSION__ = "' + ah.__AGENT_VERSION__ + '"'), lines[0]
    # v0.8.0 [release-version-public]: the public release label is paired immediately
    # after the engine version (still the first code statement per §3a-bis), so the
    # banner moves one line down. Accept the release line at index 1, banner within the
    # first few lines.
    if lines[1].startswith("__RELEASE_VERSION__ = "):
        assert any(
            "AGENT BANNER" in line or "CELL 1" in line or "VIBE_MODELING_ASCII_ART" in line
            for line in lines[2:7]
        ), lines[2:7]
    else:
        assert ("AGENT BANNER" in lines[1]) or ("CELL 1" in lines[1]), lines[1]


def test_version_was_second_line_in_v407_FAILPRE():
    lines = _cell1(PRE).split("\n")
    # v4.0.7: banner header was line 0, version line 1 (the ordering the user asked us to swap)
    assert lines[0].startswith("# === CELL 1"), lines[0]
    assert lines[1].startswith('__AGENT_VERSION__ = "4.0.7"'), lines[1]


# ===================== FIX 1: prompt governance =============================
def _pm_entry(name):
    for p in ah.TECHNICAL_CONTEXT["prompts_models"]:
        if p.get("prompt_name") == name:
            return p
    return None


def test_nine_prompts_governed_thinker_large_POST():
    for n in GOVERNED_9:
        e = _pm_entry(n)
        assert e is not None, f"{n} not routed in prompts_models"
        assert e["type"] == "thinker" and e["size"] == "large", (n, e)


def test_governed_prompts_absent_in_v407_FAILPRE():
    pre = _src(PRE)
    # prompts_models ENTRY form is {"prompt_name": "X", "type": ...; call sites use prompt_name="X".
    for n in GOVERNED_9:
        assert ('{"prompt_name": "%s"' % n) not in pre, f"{n} unexpectedly routed in v4.0.7"


def test_governed_prompts_are_real_call_sites_not_dead_config():
    live = _src()
    for n in GOVERNED_9:
        assert ('prompt_name="%s"' % n) in live, f"{n} is not invoked anywhere (dead config)"


def _agent_with_reqs(reqs):
    if not hasattr(ah.AIAgent, "_broken_models"):
        ah.AIAgent._broken_models = set()
    if not hasattr(ah.AIAgent, "_timeout_tracker_lock"):
        ah.AIAgent._timeout_tracker_lock = threading.Lock()
    a = object.__new__(ah.AIAgent)
    a._models_lookup = {
        "opus": {"name": "opus", "type": "thinker", "size": "large", "enabled": True,
                 "llm_endpoint_name": "ep-opus", "order": 1,
                 "llm_input_context_tokens_count": 200000, "llm_output_context_tokens_count": 64000},
        "mini": {"name": "mini", "type": "worker", "size": "small", "enabled": True,
                 "llm_endpoint_name": "ep-mini", "order": 2,
                 "llm_input_context_tokens_count": 200000, "llm_output_context_tokens_count": 64000},
    }
    a._prompt_model_requirements = reqs
    a._prompt_model_mapping = {}
    a._default_model_config = a._models_lookup["mini"]  # WORKER default (adversarial)
    a._fallback_chain = {}
    a.llm_config = {}
    return a


def test_governed_verifier_resolves_thinker_over_worker_default_POST():
    a = _agent_with_reqs({"VERIFIER_LLM_FALLBACK": {"type": "thinker", "size": "large"}})
    cfg = a._get_model_config_for_prompt("VERIFIER_LLM_FALLBACK")
    assert cfg.get("type") == "thinker" and cfg.get("size") == "large", cfg


def test_ungoverned_verifier_falls_to_worker_default_PROVES_WHY():
    # The v4.0.7 state: no requirement -> falls to default. With an adversarial worker default this
    # resolves to a WEAKER model. Governance (FIX 1) removes that silent-degradation pathway.
    a = _agent_with_reqs({})
    cfg = a._get_model_config_for_prompt("VERIFIER_LLM_FALLBACK")
    assert cfg.get("type") == "worker", cfg


# ================== FIX 2: scoreboard persistence ===========================
def test_scoreboard_persist_wired_POST():
    live = _src()
    assert 'emit_step("Vibe Adherence Scoreboard"' in live, "scoreboard emit_step call site missing"
    assert "scoreboard-persist-vibe-progress" in live


def test_scoreboard_persist_absent_in_v407_FAILPRE():
    pre = _src(PRE)
    assert "Vibe Adherence Scoreboard" not in pre
    assert "scoreboard-persist-vibe-progress" not in pre


class _RecWriter:
    def __init__(self):
        self.calls = []

    def emit_step(self, stage_name, step_name, progress_increment=0.0, message="",
                  status="stage_started", result_json=None, step_id=None):
        self.calls.append({"stage": stage_name, "status": status, "result_json": result_json})
        return 1


def test_scoreboard_persists_via_active_writer_registry_BEHAVIORAL():
    # Proves the mechanism the persistence block relies on: the active-writer registry round-trips and
    # emit_step accepts the full scorecard payload as result_json.
    rec = _RecWriter()
    ah.HeartbeatWatchdog.register_active(rec)
    try:
        vw = getattr(ah.HeartbeatWatchdog, "_ACTIVE_VW", None)
        assert vw is rec
        scorecard = {"total_requirements": 10, "fulfilled_count": 8, "precision": 0.8,
                     "unfulfilled_details": [{"id": "VREQ-3", "status": "failed"}]}
        vw.emit_step("Vibe Adherence Scoreboard", "vreq_verification",
                     status="stage_succeeded", message="x", result_json=scorecard)
        assert any(c["stage"] == "Vibe Adherence Scoreboard" and c["result_json"] is scorecard
                   and c["status"] == "stage_succeeded" for c in rec.calls)
    finally:
        ah.HeartbeatWatchdog.clear_active()


# ============ FIX 3: dedicated task run ID controls self-cancel =============
def test_self_cancel_reads_dedicated_task_run_id_POST():
    live = _src()
    assert 'dbutils.widgets.get("databricks_task_run_id")' in live
    assert 'dbutils.widgets.get("vibe_session_id")' in live
    assert 'dbutils.widgets.get("self_run_id")' not in live


def test_self_cancel_read_self_run_id_in_v407_FAILPRE():
    pre = _src(PRE)
    assert 'dbutils.widgets.get("self_run_id")' in pre


def test_marathon_injects_vibe_session_id_runid():
    txt = MARATHON.read_text()
    assert '"vibe_session_id": "{{job.run_id}}"' in txt
    assert '"databricks_task_run_id": "{{task.run_id}}"' in txt
    assert '"self_run_id":' not in txt


# ============ FIX 4: runtime_budget_seconds off operator widget =============
def test_runtime_budget_widget_removed_POST():
    live = _src()
    assert 'dbutils.widgets.text("runtime_budget_seconds"' not in live
    # still readable as a base-parameter (Databricks creates the widget from base_parameters)
    assert 'dbutils.widgets.get("runtime_budget_seconds")' in live


def test_runtime_budget_widget_present_in_v407_FAILPRE():
    pre = _src(PRE)
    assert 'dbutils.widgets.text("runtime_budget_seconds"' in pre


def test_self_launcher_injects_real_budget_POST():
    live = _src()
    assert '_job_widgets["runtime_budget_seconds"] = "54000"' in live


def test_marathon_injects_per_task_budget_POST():
    txt = MARATHON.read_text()
    assert 'params["runtime_budget_seconds"] = str(int(tmo))' in txt
