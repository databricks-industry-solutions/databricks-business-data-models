import json
import re
import textwrap
from pathlib import Path

NB = Path(__file__).resolve().parent.parent.parent / "agent" / "dbx_vibe_modelling_agent.ipynb"

HEAD = 'logger.warning(f"[MODEL-PARAMS] enumerated-product cap-floor failed: {_epc_e}")'
TAIL = 'logger.info(f"[MODEL-PARAMS]   {param_name}: {old_value} \u2192 {new_value}{marker}")'


_CACHE = {}


def cells():
    if "cells" not in _CACHE:
        _CACHE["cells"] = json.loads(NB.read_text())["cells"]
    return _CACHE["cells"]


def apply_block():
    """The real region between the cap-floor guard and the end of the apply loop.

    Anchored on lines that exist both before and after the patch, so a pre-patch run
    executes cleanly and simply fails to clamp - a behavioural failure, not an
    extraction error.
    """
    if "block" in _CACHE:
        return _CACHE["block"]
    for c in cells():
        if c.get("cell_type") != "code":
            continue
        src = c["source"]
        text = "".join(src) if isinstance(src, list) else src
        if HEAD in text and TAIL in text:
            start = text.index(HEAD) + len(HEAD)
            end = text.index(TAIL, start) + len(TAIL)
            _CACHE["block"] = textwrap.dedent(text[start:end])
            return _CACHE["block"]
    raise AssertionError("apply-loop region not found in the notebook")


class _Log:
    def __init__(self):
        self.lines = []

    def info(self, m=""):
        self.lines.append(str(m))

    def warning(self, m=""):
        self.lines.append("WARN " + str(m))


def run(validated, sizing):
    log = _Log()
    config = {"PROMPT_VARIABLES": {}}
    ns = {
        "logger": log,
        "config": config,
        "model_scope": "mvm",
        "validated_params": dict(validated),
        "widgets_values": {"sizing_directives": sizing},
    }
    exec(compile(apply_block(), "<apply>", "exec"), ns)
    return ns["validated_params"], config["PROMPT_VARIABLES"], log.lines


# the live coffee_roastery numbers: the vibe said 5-7, the tier heuristic said 7-13
LIVE = {"min_data_products_per_domain": 7, "max_data_products_per_domain": 13}
VIBE = {"min_products_per_domain": 5, "max_products_per_domain": 7}


def test_the_generator_is_told_the_range_the_user_actually_asked_for():
    params, prompt_vars, _ = run(LIVE, VIBE)
    assert params["max_data_products_per_domain"] == 7, params
    assert params["min_data_products_per_domain"] == 5, params
    # the prompt variables are what the generator actually reads
    assert prompt_vars["max_data_products_per_domain"] == 7
    assert prompt_vars["min_data_products_per_domain"] == 5


def test_a_heuristic_stricter_than_the_user_is_left_alone():
    # the user stated a ceiling, not a quota to fill
    params, _, _ = run({"min_data_products_per_domain": 3,
                        "max_data_products_per_domain": 5}, VIBE)
    assert params["max_data_products_per_domain"] == 5, params


def test_no_vibe_bounds_changes_nothing():
    before = dict(LIVE)
    params, _, _ = run(LIVE, {})
    assert params == before, params


def test_a_lowered_ceiling_never_strands_the_floor_above_it():
    # ceiling only: the heuristic floor of 12 would make the range impossible
    params, _, _ = run({"min_data_products_per_domain": 12,
                        "max_data_products_per_domain": 20},
                       {"max_products_per_domain": 7})
    assert params["max_data_products_per_domain"] == 7, params
    assert params["min_data_products_per_domain"] <= 7, params


def test_a_floor_above_the_users_own_ceiling_is_pulled_down_to_it():
    params, _, _ = run(LIVE, {"min_products_per_domain": 9, "max_products_per_domain": 7})
    assert params["min_data_products_per_domain"] <= params["max_data_products_per_domain"], params


def test_a_bad_directive_cannot_break_the_run():
    params, _, lines = run(LIVE, {"max_products_per_domain": "not-a-number"})
    # the apply loop must still have run
    assert any("Applying LLM-determined parameters" in ln for ln in lines)
    assert params["max_data_products_per_domain"] in (13, 7), params


def test_the_clamp_reports_itself_so_a_live_run_can_be_audited():
    _, _, lines = run(LIVE, VIBE)
    assert any("vibe-per-domain-bounds-clamp FIRED" in ln for ln in lines), lines


def test_the_agent_version_is_at_least_the_one_that_shipped_this_fix():
    m = None
    for c in cells():
        src = c.get("source")
        t = "".join(src) if isinstance(src, list) else (src or "")
        m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', t)
        if m:
            break
    assert m, "no __AGENT_VERSION__"
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 6), m.group(0)
