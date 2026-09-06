import json
import re
from pathlib import Path

import pytest

from notebook_source_util import notebook_concat_source

AGENT_NB = Path(__file__).resolve().parents[2] / "agent" / "dbx_vibe_modelling_agent.ipynb"


@pytest.fixture(scope="module")
def nb_cells():
    nb = json.loads(AGENT_NB.read_text())
    return {ci: "".join(c["source"]) for ci, c in enumerate(nb["cells"]) if c["cell_type"] == "code"}


@pytest.fixture(scope="module")
def nb_text():
    return AGENT_NB.read_text()


def _cell_with(nb_cells, needle):
    """The code cell that owns `needle`.

    Cell indices drift every time a cell is added or removed, so locate the cell
    by the code it contains instead of pinning an index.
    """
    hits = [src for src in nb_cells.values() if needle in src]
    assert len(hits) == 1, f"expected exactly 1 cell containing {needle!r}, found {len(hits)}"
    return hits[0]


def test_agent_version_at_least_084(nb_cells):
    src = nb_cells[1]
    m = re.search(r'__AGENT_VERSION__\s*=\s*"([^"]+)"', src)
    assert m, "__AGENT_VERSION__ not found"
    v = tuple(int(p) for p in m.group(1).split("."))
    assert v >= (0, 8, 4), f"expected >= 0.8.4 got {m.group(1)}"


# v0.8.4 aliases (P58 + P59)
@pytest.mark.parametrize("alias", [
    "install-vov-handoff-allow-overwrite",
    "soft-accept-hard-fail-on-critical-step",
])
def test_v84_alias_present(nb_text, alias):
    assert alias in nb_text, f"alias {alias} missing from notebook"


def test_p58_fires_log_marker(nb_cells):
    src = _cell_with(nb_cells, "install-vov-handoff-allow-overwrite")
    assert "[install-vov-handoff-allow-overwrite FIRED]" in src, (
        "P58 must emit FIRED marker"
    )
    assert "_vov_successor_match" in src, "P58 must use _vov_successor_match flag"
    assert "_max_prior" in src, "P58 must compute _max_prior"
    assert "MAX(CAST(version AS INT))" in src, (
        "P58 must query MAX(version) from _metamodel.business"
    )


def test_p58_only_promotes_when_current_greater_than_max_prior(nb_cells):
    src = _cell_with(nb_cells, "install-vov-handoff-allow-overwrite")
    assert "if _max_prior < _cur_v_int:" in src, (
        "P58 must check current > max_prior before allowing overwrite"
    )


def test_p58_sits_before_existing_prior_install_match(nb_cells):
    src = _cell_with(nb_cells, "install-vov-handoff-allow-overwrite")
    p58_ix = src.find("install-vov-handoff-allow-overwrite")
    legacy_ix = src.find("if _mm_hits > 0:")
    assert 0 < p58_ix < legacy_ix, (
        "P58 block must be injected BEFORE the legacy `if _mm_hits > 0:` so "
        "_prior_install_match can be set by the vov-successor branch first."
    )


def test_p58_requires_current_version_at_least_2(nb_cells):
    src = _cell_with(nb_cells, "install-vov-handoff-allow-overwrite")
    assert "_cur_v_int > 1" in src, "P58 must require current_version >= 2"


def test_p59_fires_log_marker_in_cell7(nb_cells):
    src = nb_cells[7]
    assert "[soft-accept-hard-fail-on-critical-step FIRED]" in src, (
        "P59 must emit FIRED marker on critical-step soft-accept"
    )
    assert "[soft-accept-hard-fail-on-critical-step SKIP-COSMETIC]" in src, (
        "P59 must emit SKIP-COSMETIC marker on cosmetic-step soft-accept"
    )


def test_p59_critical_regex_includes_key_patterns(nb_cells):
    src = nb_cells[7]
    m = re.search(r"_p59_critical_re\s*=\s*re\.compile\(r'\(\?i\)\(([^)]+)\)'\)", src)
    assert m, "P59 critical regex pattern not found"
    pattern = m.group(1)
    for must in ("fk", "structural", "schema", "immutable", "ssot",
                 "normaliz", "validat", "gate", "architect", "cycle", "silo"):
        assert must in pattern, (
            f"P59 critical regex missing '{must}' pattern: {pattern}"
        )


def test_p59_cosmetic_regex_includes_safe_patterns(nb_cells):
    src = nb_cells[7]
    m = re.search(r"_p59_cosmetic_re\s*=\s*re\.compile\(r'\(\?i\)\(([^)]+)\)'\)", src)
    assert m, "P59 cosmetic regex pattern not found"
    pattern = m.group(1)
    for must in ("description", "sample", "observability", "kpi", "comment"):
        assert must in pattern, (
            f"P59 cosmetic regex missing '{must}' pattern: {pattern}"
        )


def test_p59_returns_false_on_critical(nb_cells):
    src = nb_cells[7]
    # After the FIRED log, the next return must be `return False, last_valid_response, last_errors`
    fired_ix = src.find("[soft-accept-hard-fail-on-critical-step FIRED]")
    assert fired_ix > 0
    tail = src[fired_ix : fired_ix + 1200]
    assert "return False, last_valid_response, last_errors" in tail, (
        "P59 must return False on critical-step soft-accept"
    )


def test_p59_returns_true_on_cosmetic(nb_cells):
    src = nb_cells[7]
    skip_ix = src.find("[soft-accept-hard-fail-on-critical-step SKIP-COSMETIC]")
    assert skip_ix > 0
    tail = src[skip_ix : skip_ix + 1200]
    assert "return True, last_valid_response, last_errors" in tail, (
        "P59 must return True on cosmetic-step soft-accept (preserves legacy behavior)"
    )


def test_p59_cosmetic_check_excludes_critical_overlap(nb_cells):
    src = nb_cells[7]
    # The is_cosmetic gate must require BOTH cosmetic match AND no critical match,
    # so a step like "kpi-fk-validation" still fails critical.
    assert "and not bool(_p59_critical_re.search(_p59_step))" in src, (
        "P59 must require NOT critical even when cosmetic regex matches"
    )


# ─── Anti-regression: every v0.8.3 alias must remain present ───
@pytest.mark.parametrize("alias", [
    "autofix-p016-user-vibe-skip",
    "connect-table-upsert-fk",
    "vov-auto-latest-version-when-v1",
    "install-mv-hard-gate",
    "unconditional-cascade-drop-extras",
    "honest-adherence-precision",
    "next-vibes-sa-target-filter",
])
def test_v83_aliases_still_present(nb_text, alias):
    assert alias in nb_text, f"v0.8.3 alias {alias} regressed in v0.8.4"


def test_old_soft_accept_warning_removed(nb_cells):
    """
    The bare 'Proceeding with last response despite validation errors' should no
    longer be the SOLE branch — it must be inside the cosmetic path under P59.
    """
    src = nb_cells[7]
    occurrences = src.count("Proceeding with last response despite validation errors")
    # Allowed: the cosmetic path keeps the warning, plus historical comments.
    # Bug shape: pre-v0.8.4 it appeared once as a top-level un-guarded branch.
    # Post-v0.8.4 the same string appears inside the cosmetic if-block.
    assert occurrences >= 1, "soft-accept warning string disappeared entirely"
    # Confirm it appears inside an `if _p59_is_cosmetic:` block.
    cosmetic_ix = src.find("if _p59_is_cosmetic:")
    assert cosmetic_ix > 0
    warn_ix = src.find("Proceeding with last response", cosmetic_ix)
    assert warn_ix > cosmetic_ix, (
        "soft-accept warning must live INSIDE the cosmetic-path branch in P59"
    )
