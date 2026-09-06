"""v0.8.7 behavioral tests — P62 rdfs-business-row-asdict fix."""
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


@pytest.fixture(scope="module")
def cell23_src(nb):
    return "".join(nb["cells"][23]["source"])


def test_agent_version_at_least_087(cell1_src):
    m = re.search(r'__AGENT_VERSION__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', cell1_src)
    assert m
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert (major, minor, patch) >= (0, 8, 7), f"Expected >= 0.8.7, got {major}.{minor}.{patch}"


def test_p62_alias_present(cell23_src):
    """P62 rdfs-business-row-asdict alias must appear in cell 23."""
    assert "rdfs-business-row-asdict" in cell23_src


def test_p62_safe_desc_helper_defined(cell23_src):
    """_safe_desc helper must be defined inside _generate_rdf_schema."""
    assert "def _safe_desc(" in cell23_src


def test_p62_safe_desc_uses_asdict(cell23_src):
    """_safe_desc must call asDict() on Spark Row objects (not .get() directly)."""
    safe_desc_start = cell23_src.find("def _safe_desc(")
    assert safe_desc_start > 0
    # Find function body
    body = cell23_src[safe_desc_start:safe_desc_start + 1200]
    assert 'asDict' in body, "_safe_desc must use Row.asDict() for Spark Row support"


def test_p62_safe_desc_handles_none(cell23_src):
    """_safe_desc must guard against None input."""
    safe_desc_start = cell23_src.find("def _safe_desc(")
    body = cell23_src[safe_desc_start:safe_desc_start + 1200]
    assert "obj is None" in body


def test_p62_safe_desc_handles_dict(cell23_src):
    """_safe_desc must support dict input (for domain/product)."""
    safe_desc_start = cell23_src.find("def _safe_desc(")
    body = cell23_src[safe_desc_start:safe_desc_start + 1200]
    assert "isinstance(obj, dict)" in body


def test_p62_no_old_business_row_get_pattern(cell23_src):
    """The old `(business_row or {}).get('description'` pattern must be REMOVED."""
    assert "(business_row or {}).get('description'" not in cell23_src
    assert "(business_row or {}).get(\"description\"" not in cell23_src


def test_p62_business_row_uses_safe_desc(cell23_src):
    """The business_row RDFS comment line must use _safe_desc(business_row)."""
    assert "_safe_desc(business_row)" in cell23_src


def test_p62_domain_uses_safe_desc(cell23_src):
    """Domain RDFS line uses _safe_desc(domain) for consistency."""
    assert "_safe_desc(domain)" in cell23_src


def test_p62_product_uses_safe_desc(cell23_src):
    """Product RDFS line uses _safe_desc(product) for consistency."""
    assert "_safe_desc(product)" in cell23_src


def test_p62_preserves_prior_aliases(cell1_src, cell23_src):
    """v0.8.6 P61 aliases must still be present after v0.8.7 patch."""
    assert "install-clash-widget-fallback FIRED" in cell1_src
    assert "install-clash-unconditional-escape FIRED" in cell1_src
    assert "install-vov-handoff-allow-overwrite FIRED" in cell1_src
    assert "install-clash-debug-logger-rescue" in cell23_src
