"""v0.8.6 behavioral tests — P61 install-clash widget-fallback + unconditional escape hatch."""
import json
import re
import pytest

NB_PATH = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"


@pytest.fixture(scope="module")
def nb():
    with open(NB_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cell1_src(nb):
    return "".join(nb["cells"][1]["source"])


def test_agent_version_is_at_least_086(cell1_src):
    """__AGENT_VERSION__ must be >= 0.8.6 (P61 baseline)."""
    m = re.search(r'__AGENT_VERSION__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', cell1_src)
    assert m is not None, "Could not find __AGENT_VERSION__"
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert (major, minor, patch) >= (0, 8, 6), f"Expected >= 0.8.6, got {major}.{minor}.{patch}"


def test_p61_widget_fallback_alias_present(cell1_src):
    """P61 install-clash-widget-fallback alias must appear in cell 1 (in fire site, not just comment)."""
    assert "install-clash-widget-fallback FIRED" in cell1_src, (
        "Alias install-clash-widget-fallback FIRED not found"
    )


def test_p61_unconditional_escape_alias_present(cell1_src):
    """P61 install-clash-unconditional-escape alias must appear in cell 1."""
    assert "install-clash-unconditional-escape FIRED" in cell1_src, (
        "Alias install-clash-unconditional-escape FIRED not found"
    )


def test_p61_widget_fallback_uses_dbutils_widgets_get(cell1_src):
    """P61 widget fallback must use dbutils.widgets.get for business_name and model_version."""
    # Find within _check_physical_deployment_clash function
    func_start = cell1_src.find("def _check_physical_deployment_clash")
    func_end = cell1_src.find("\ndef ", func_start + 10)
    func_src = cell1_src[func_start:func_end] if func_end > 0 else cell1_src[func_start:]
    assert "dbutils.widgets.get" in func_src or "_dbutils_obj.widgets.get" in func_src, (
        "P61 must call dbutils.widgets.get to read missing business_name/model_version"
    )


def test_p61_unconditional_escape_uses_metamodel_schema_check(cell1_src):
    """P61 unconditional escape must check for _metamodel schema before allowing soft-replace."""
    assert '"_metamodel" in _mm_schema_names_esc' in cell1_src or "'_metamodel' in _mm_schema_names_esc" in cell1_src, (
        "P61 escape hatch must check for _metamodel schema presence"
    )


def test_p61_unconditional_escape_gated_by_version_gt_1(cell1_src):
    """P61 unconditional escape must require current_version > 1."""
    # Find unconditional escape block
    esc_start = cell1_src.find("install-clash-unconditional-escape")
    assert esc_start > 0
    # Look in surrounding region
    ctx = cell1_src[max(0, esc_start - 1500):esc_start + 1500]
    assert "_cur_v_int_esc" in ctx
    assert "_cur_v_int_esc > 1" in ctx, "Escape must require current_version > 1"


def test_p61_does_not_remove_p58_or_p60(cell1_src):
    """P61 must preserve P58/P60 markers (no regression)."""
    assert "install-vov-handoff-allow-overwrite FIRED" in cell1_src, "P58 alias removed"
    assert "install-vov-handoff-allow-overwrite FIRED-RELAXED" in cell1_src, "P60b alias removed"


def test_p61_widget_fallback_runs_before_p58(cell1_src):
    """P61 widget fallback should run BEFORE the P58/P60 check; the fallback patches widgets_values
    so that the P58/P60 query can succeed."""
    fallback_pos = cell1_src.find("install-clash-widget-fallback FIRED")
    p58_pos = cell1_src.find("install-vov-handoff-allow-overwrite FIRED")
    assert fallback_pos > 0 and p58_pos > 0
    assert fallback_pos < p58_pos, "P61 widget fallback must come before P58 in source order"


def test_p61_prints_for_visibility(cell1_src):
    """P61 must call print() for stdout visibility even when logger is None or silenced."""
    # Find FIRED block region
    fired_pos = cell1_src.find("install-clash-widget-fallback FIRED")
    ctx = cell1_src[max(0, fired_pos - 200):fired_pos + 1500]
    # Should include print() calls within the same block
    assert "print(_msg)" in ctx, "P61 must print _msg to stdout for visibility"


def test_p60a_alias_still_in_cell_23(nb):
    """P60a alias install-clash-debug-logger-rescue must remain in cell 23 (anti-regression)."""
    cell23_src = "".join(nb["cells"][23]["source"])
    assert "install-clash-debug-logger-rescue" in cell23_src


def test_cell1_function_check_physical_deployment_clash_parses(cell1_src):
    """Sanity: extract _check_physical_deployment_clash and verify it's syntactically valid."""
    import ast
    m = re.search(r'def _check_physical_deployment_clash\([^)]*\):', cell1_src)
    assert m is not None
    start = m.start()
    m2 = re.search(r'\n(def |class )', cell1_src[start + 10:])
    end = start + 10 + m2.start() if m2 else len(cell1_src)
    func_src = cell1_src[start:end]
    ast.parse(func_src)  # raises SyntaxError on failure
