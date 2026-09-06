"""v4.6.4 — behavioral tests for the KPI advisory false-red calibration.

ROOT CAUSE (v4.6.3 KPI-first stats): two advisories emitted WARNING lines that block the
clean-install bar on legitimate small-scope models:
  (1) `if _kpi_with_joins == 0:` warned unconditionally — but a tiny model (few products)
      legitimately has single-table KPIs (not enough related tables to join across).
  (2) `if len(kpi_views) < 10:` hardcoded the floor at 10, so it false-warned
      "only 8 KPIs produced (target was 8)" whenever the scope target was < 10, even though
      the model MET its own target exactly (the "N==N" false-red).

FIX (v4.6.4 alias=kpi-warn-calibrate):
  - join advisory downgraded to INFO at small scope (len(products) < 10), kept WARNING for
    full scope (real quality signal).
  - count advisory warns only when the model UNDERSHOT its OWN target_kpi_count.

This test EXECUTES the real patched calibration block sliced from the notebook against
controlled inputs with a recording logger — so it exercises production code, not a re-impl.
It FAILS on pre-patch HEAD (WARNING at small scope / target-met) and PASSES post-patch.
"""
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _cell_source(idx_hint_marker):
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if idx_hint_marker in src:
            return src
    raise LookupError(idx_hint_marker)


SRC = _cell_source("kpi-warn-calibrate FIRED v4.6.4")


def _calibration_block():
    """Slice the real calibration block: from the [kpi-first-stats FIRED] info line through
    the closing `elif len(kpi_views) < 10:` info line."""
    lines = SRC.splitlines(keepends=True)
    start = end = None
    for n, l in enumerate(lines):
        if "[kpi-first-stats FIRED] kpis=" in l and start is None:
            start = n
        if "meeting the scope target of" in l:
            end = n
    assert start is not None and end is not None, (start, end)
    # dedent to column 0 (block is indented 4 spaces inside the function)
    block = "".join(lines[start: end + 1])
    dedented = "\n".join(ln[4:] if ln.startswith("    ") else ln for ln in block.splitlines())
    return dedented


BLOCK = _calibration_block()


class _RecLogger:
    def __init__(self):
        self.warnings = []
        self.infos = []
    def warning(self, m):
        self.warnings.append(m)
    def info(self, m):
        self.infos.append(m)


def _run(kpi_count, products_count, target, with_joins):
    logger = _RecLogger()
    ns = {
        "logger": logger,
        "kpi_views": [{"v": i} for i in range(kpi_count)],
        "products": list(range(products_count)),
        "target_kpi_count": target,
        "_kpi_with_joins": with_joins,
        "_kpi_total_joins": with_joins,
        "_domains_covered": 3,
    }
    exec(compile(BLOCK, str(NOTEBOOK_PATH), "exec"), ns)
    return logger


def test_small_scope_zero_joins_is_info_not_warning():
    """7-product tiny model, 0 joins => INFO, NOT a warning."""
    log = _run(kpi_count=5, products_count=7, target=5, with_joins=0)
    assert not any("0 KPIs use joins" in w for w in log.warnings)
    assert any("expected at small scope" in i for i in log.infos)


def test_full_scope_zero_joins_still_warns():
    """160-product full model, 0 joins => WARNING preserved (real quality signal)."""
    log = _run(kpi_count=40, products_count=160, target=40, with_joins=0)
    assert any("0 KPIs use joins" in w for w in log.warnings)


def test_target_met_below_ten_is_not_a_warning():
    """The N==N false-red: produced 8, target 8 => NO count warning (was WARNING pre-patch)."""
    log = _run(kpi_count=8, products_count=17, target=8, with_joins=1)
    assert not any("KPIs produced" in w for w in log.warnings)
    assert any("meeting the scope target" in i for i in log.infos)


def test_undershoot_own_target_still_warns():
    """Produced 3 but target 8 => genuine undershoot => WARNING preserved."""
    log = _run(kpi_count=3, products_count=17, target=8, with_joins=1)
    assert any("only 3 KPIs produced (target was 8)" in w for w in log.warnings)


def test_meets_target_above_ten_no_info_spam():
    """Produced 12, target 12 (>=10) => no count warning, no small-scope info line."""
    log = _run(kpi_count=12, products_count=40, target=12, with_joins=2)
    assert not any("KPIs produced" in w for w in log.warnings)
    assert not any("meeting the scope target" in i for i in log.infos)


def test_alias_present_in_source():
    assert "kpi-warn-calibrate FIRED v4.6.4" in SRC
    assert "if len(kpi_views) < target_kpi_count:" in SRC
