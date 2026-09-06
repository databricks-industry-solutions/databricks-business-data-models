"""Behavioral tests for v3.7.1 alias=bc-domain-floor-user-king.

ROOT CAUSE this fixes (live, gov_transport base-MVM run <run_id> @ <profile>, v3.7.0):
SmartWorkerValidator.validate_business_context hardcoded a `len(domains) < 3`
floor ("need at least 3 domains for a meaningful model"). A user who PINS exactly
2 domains via the business_domains widget (_user_specified_domains = ["hr","project"])
got a hard validation ERROR on every Step-1 attempt, burning retries and emitting a
scary "Domain count 2 is too low" warning that directly contradicts §3b/§3c
(the user's explicit widget OUTRANKS the heuristic floor).

THE FIX: read the user's explicit domains from the SAME SSOT the class already uses
(config["_widgets_values"]["_user_specified_domains"], cf. __init__/_detect_user_vibes
at L30287 and the config build at L43697) and compute
`_domain_floor = min(3, len(user_domains)) if user_domains else 3`. The heuristic
3-floor is preserved when the user pinned nothing (empty list) and is LOWERED to the
user's count when they pinned fewer. The floor never RISES, so it cannot weaken
protection for larger requests.

These tests extract the REAL SmartWorkerValidator from the notebook. The positive case
FAILS on pre-v3.7.1 HEAD (2 user-pinned domains rejected by the hardcoded 3-floor) and
PASSES post-fix. Negative controls prove selectivity: no widget keeps the 3-floor, and a
user who pins 2 but the LLM returns 1 still fails (floor still protects).
"""
import ast
import json
import os
import re

NB = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb")


def _src():
    nb = json.load(open(NB))
    return "".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")


def _coerce_helpers():
    """Slice the real coerce helpers from cell 25 so the isolated SmartWorkerValidator
    (whose methods reference _v466_coerce_llm_obj after v4.6.6 hardening) execs cleanly."""
    nb = json.load(open(NB))
    cell25 = "".join(nb["cells"][25]["source"])
    tree = ast.parse(cell25)
    wanted = {"_coerce_dict", "_coerce_list_of_dicts", "_v466_coerce_llm_obj"}
    body = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted
    ]
    ns = {"json": json, "re": re, "logging": __import__("logging")}
    exec(compile(ast.Module(body=body, type_ignores=[]), "<cell25>", "exec"), ns)
    return {k: ns[k] for k in wanted}


def _extract_class(name):
    src = _src()
    m = re.search(r"\nclass " + re.escape(name) + r"\b[\s\S]*?\n(?=\n(?:class |def )[A-Za-z_])", "\n" + src)
    assert m, f"class {name} not found in notebook"
    return m.group(0).lstrip("\n")


def _load_validator():
    g = {"json": json, "re": re, "_DOMAIN_CEILING_FACTOR": 1.5, **_coerce_helpers()}
    exec(_extract_class("SmartWorkerValidator"), g)
    return g["SmartWorkerValidator"]


class _Log:
    def __init__(self):
        self.lines = []

    def info(self, m):
        self.lines.append(("info", m))

    def warning(self, m):
        self.lines.append(("warning", m))

    def error(self, m):
        self.lines.append(("error", m))

    def debug(self, m):
        self.lines.append(("debug", m))


def _config(user_domains=None):
    cfg = {
        "PROMPT_VARIABLES": {
            "min_business_domains": 4,
            "max_business_domains": 6,
            "business_config": {},
        },
        "_widgets_values": {},
    }
    if user_domains is not None:
        cfg["_widgets_values"]["_user_specified_domains"] = list(user_domains)
    return cfg


def _response(domains_csv):
    """Otherwise-valid Step-1 business-context response; ONLY the domain count varies."""
    return json.dumps({
        "core_business_processes": "recruiting, project delivery",
        "data_domains": domains_csv,
        "common_business_jargons": "req, offer, sprint, milestone, timesheet, allocation",
        "operational_systems_of_records": "Workday, Jira",
        "industry_governing_body": "n/a",
        "industry_complexity_tier": "tier_5",
    })


def _has_too_low(errors):
    return any("too low" in e for e in errors)


def test_user_pinned_two_domains_accepted():
    """POSITIVE — user pins exactly 2 domains; a 2-domain response MUST pass the floor.
    FAILS pre-fix (hardcoded <3 rejects), PASSES post-fix."""
    V = _load_validator()
    log = _Log()
    v = V(log, _config(user_domains=["hr", "project"]))
    ok, errors = v.validate_business_context(_response("hr, project"))
    assert not _has_too_low(errors), f"2 user-pinned domains wrongly flagged too low: {errors}"
    assert ok, f"expected valid; errors={errors}"
    # FIRED log evidence (non-no-op)
    assert any("bc-domain-floor-user-king FIRED" in m for _, m in log.lines), \
        f"expected FIRED log; got {log.lines}"


def test_no_widget_keeps_heuristic_three_floor():
    """NEGATIVE CONTROL — no _user_specified_domains => heuristic 3-floor preserved.
    A 2-domain response MUST still be rejected. Proves the fix is selective."""
    V = _load_validator()
    v = V(_Log(), _config(user_domains=None))
    ok, errors = v.validate_business_context(_response("hr, project"))
    assert _has_too_low(errors), f"expected too-low rejection with no widget; errors={errors}"
    assert not ok


def test_user_pinned_two_but_one_domain_still_fails():
    """NEGATIVE CONTROL — user pins 2 but LLM returns 1 domain.
    1 < floor(2) => MUST still fail. Proves the floor still protects."""
    V = _load_validator()
    v = V(_Log(), _config(user_domains=["hr", "project"]))
    ok, errors = v.validate_business_context(_response("hr"))
    assert _has_too_low(errors), f"1 domain vs floor 2 should fail; errors={errors}"
    assert not ok


def test_user_pinned_five_floor_does_not_rise_above_three():
    """NEGATIVE CONTROL — user pins 5 domains; floor must stay 3 (min(3,5)), NOT rise to 5.
    A 3-domain response MUST pass (the fix never raises the floor / tightens beyond heuristic)."""
    V = _load_validator()
    v = V(_Log(), _config(user_domains=["a", "b", "c", "d", "e"]))
    ok, errors = v.validate_business_context(_response("a, b, c"))
    assert not _has_too_low(errors), f"3 domains should pass when user pinned 5 (floor=min(3,5)=3): {errors}"
    assert ok
