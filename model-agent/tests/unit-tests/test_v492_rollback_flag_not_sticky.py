"""v4.9.2 - the fidelity rollback recommendation must track the CURRENT gate verdict.

Live evidence (coffee_roastery, run 934019101231955, agent v4.9.1):

    14:11:44  Fidelity gates FAILED: precision 0.6667 < required 0.85 - rollback recommended
    14:11:44  [AUTOFIX-SUMMARY] fidelity_gate: passed=False, failed_gates=['precision'], rollback_recommended=True
    14:12:30  [shrink-guard-user-king FIRED] product_count 31 -> 28 ... (SelfFixer remediates VREQ-001)
    14:14:37  [AUTOFIX-SUMMARY] fidelity_gate: passed=True,  failed_gates=none,        rollback_recommended=True
    14:17:03  [gt-headline-reground FIRED] precision=1.0 fulfilled=3/3

The gate IS re-evaluated after remediation and it DOES pass. But the write site was a
one-way latch with no clearing branch, so a run that recovered to precision=1.0 still
advertised rollback_recommended=True. That is a lying scoreboard in the pessimistic
direction: it recommends discarding a model that met every requirement.
"""

import json
import os
import re

import pytest

from notebook_source_util import assert_agent_version_at_least, cell_containing

ANCHOR = 'self.widgets_values["vibe_rollout_rollback_recommended"]'


def _gate_region():
    """The fidelity-gate block out of VibeOrchestrator.score(), dedented to module level."""
    src = cell_containing(ANCHOR)
    lines = src.split("\n")
    start = next(i for i, l in enumerate(lines) if "contract = self.widgets_values.get" in l)
    end = next(i for i, l in enumerate(lines[start:], start)
               if "[AUTOFIX-SUMMARY] fidelity_gate:" in l)
    # run to the closing paren of that final logger call
    while not lines[end].strip().startswith(")"):
        end += 1
    block = lines[start:end + 1]
    indent = len(block[0]) - len(block[0].lstrip())
    return "\n".join(l[indent:] if len(l) > indent else l.lstrip() for l in block)


class _Logger:
    def __init__(self):
        self.text = ""

    def _w(self, m):
        self.text += str(m) + "\n"

    info = warning = error = debug = _w


class _Contract:
    hard_constraints = ["every table has a primary key"]


class _Self:
    def __init__(self, prior_flag):
        self.widgets_values = {
            "vibe_contract": _Contract(),
            "vibe_modelling_instructions": "keep it small and production clean",
            "vibe_requirements_checklist": [],
        }
        if prior_flag is not None:
            self.widgets_values["vibe_rollout_rollback_recommended"] = prior_flag
        self.logger = _Logger()


def _run(gate_passed, prior_flag=None):
    """Execute the real gate block with a stubbed evaluate_fidelity_gates verdict."""
    checks = ({"precision": {"passed": True, "observed": 1.0, "required_min": 0.85}}
              if gate_passed else
              {"precision": {"passed": False, "observed": 0.6667, "required_min": 0.85}})
    me = _Self(prior_flag)
    ns = {
        "self": me,
        "scorecard": {},
        "VibeContract": _Contract,
        "evaluate_fidelity_gates": lambda sc, c: {"passed": gate_passed, "checks": checks},
    }
    exec(compile(_gate_region(), "<gate>", "exec"), ns)
    return me


def _flag(me):
    return bool(me.widgets_values.get("vibe_rollout_rollback_recommended", False))


def _summary(me):
    for line in me.logger.text.split("\n"):
        if "[AUTOFIX-SUMMARY] fidelity_gate:" in line:
            return line
    raise AssertionError("no fidelity_gate summary line was logged")


# --------------------------------------------------------------------------- the defect

def test_a_passing_gate_clears_a_flag_set_by_an_earlier_failed_round():
    """The exact live sequence: fail, remediate, pass. The flag must not survive."""
    me = _run(gate_passed=True, prior_flag=True)
    assert _flag(me) is False, (
        "gate passed but rollback is still recommended - this is the v4.9.1 sticky latch")


def test_the_summary_line_agrees_with_itself_after_recovery():
    """passed=True and rollback_recommended=True in one line is self-contradictory."""
    line = _summary(_run(gate_passed=True, prior_flag=True))
    assert "passed=True" in line
    assert "rollback_recommended=False" in line, line


def test_two_evaluations_in_sequence_mirror_the_live_run():
    """Round 1 fails, round 2 passes on the same widgets dict, as score() is re-entered."""
    first = _run(gate_passed=False)
    assert _flag(first) is True, "a failing gate must recommend rollback"
    second = _run(gate_passed=True, prior_flag=_flag(first))
    assert _flag(second) is False
    assert "rollback_recommended=False" in _summary(second)


# ------------------------------------------------------------------ the failing branch

def test_a_failing_gate_still_recommends_rollback():
    """Negative control: the fix must not disarm the gate."""
    me = _run(gate_passed=False)
    assert _flag(me) is True
    assert "rollback_recommended=True" in _summary(me)


def test_a_failing_gate_still_warns_with_the_measured_shortfall():
    me = _run(gate_passed=False)
    assert "Fidelity gates FAILED" in me.logger.text
    assert "0.6667" in me.logger.text
    assert "rollback recommended" in me.logger.text


def test_a_failing_gate_after_a_passing_one_re_arms_the_flag():
    """Clearing must be a live reading, not a one-way clear replacing a one-way latch."""
    ok = _run(gate_passed=True)
    assert _flag(ok) is False
    regressed = _run(gate_passed=False, prior_flag=_flag(ok))
    assert _flag(regressed) is True


# ------------------------------------------------------------------------ clean starts

def test_a_first_ever_passing_gate_reports_no_rollback():
    me = _run(gate_passed=True)
    assert _flag(me) is False
    assert "rollback_recommended=False" in _summary(me)


def test_clearing_is_idempotent():
    me = _run(gate_passed=True, prior_flag=False)
    assert _flag(me) is False


def test_the_clear_is_announced_so_an_auditor_can_see_it():
    """A silent state change is unauditable; the run log must show why the flag dropped."""
    me = _run(gate_passed=True, prior_flag=True)
    assert "fidelity-rollback-flag-clear" in me.logger.text


def test_no_clear_line_when_there_was_nothing_to_clear():
    """Log noise on every clean run would bury the signal."""
    me = _run(gate_passed=True, prior_flag=None)
    assert "fidelity-rollback-flag-clear" not in me.logger.text


# ------------------------------------------------------------------------ source shape

def test_the_write_site_has_a_clearing_branch():
    src = cell_containing(ANCHOR)
    assert re.search(r'\[\s*"vibe_rollout_rollback_recommended"\s*\]\s*=\s*False', src), (
        "no assignment ever sets the flag back to False - it is still a one-way latch")


def test_version_is_492_or_later():
    assert_agent_version_at_least("4.9.2")
