"""v4.6.4 — behavioral tests for the 05b sample-data-not-landing root cause.

ROOT CAUSE (proven): a caller built its
CatalogResolver from the widget cataloging_style in its DISPLAY form
("Catalog per Division") without normalizing to the snake form
("catalog_per_division") that CatalogResolver.resolve_catalog() matches on.
With the unmatched display form, resolve_catalog() fell through every branch
and silently returned base_catalog — so Catalog-per-Division / Catalog-per-Domain
installs routed every sample INSERT to the BASE catalog and left the division /
domain tables empty, while the op still reported success (05b: 0/7 tables had rows).

FIX (v4.6.4 alias=catalogresolver-style-normalize): CatalogResolver.__init__
normalizes the style (display -> snake) so every caller is protected at the one
component that requires the snake form.

These tests exercise the REAL CatalogResolver sliced from the agent notebook and
assert the observable catalog resolution. They FAIL on pre-patch HEAD (display
form -> base_catalog) and PASS post-patch (display form -> division/domain catalog).
"""
import ast
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _concat_source():
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    return "\n\n".join(parts)


SOURCE = _concat_source()


def _slice_named(name, kinds):
    """Slice the last module-level def/class named `name` from the notebook."""
    lines = SOURCE.splitlines(keepends=True)
    tree = ast.parse(SOURCE)
    target = None
    for node in tree.body:
        if isinstance(node, kinds) and getattr(node, "name", None) == name:
            target = node
    if target is None:
        raise LookupError(f"{name!r} not found at module level")
    return "".join(lines[target.lineno - 1: target.end_lineno])


def _resolver_namespace():
    blob = "\n\n".join([
        _slice_named("apply_convention", (ast.FunctionDef,)),
        _slice_named("CatalogResolver", (ast.ClassDef,)),
    ])
    import re as _re
    ns = {"__name__": "_test_catalogresolver", "re": _re}
    exec(compile(blob, str(NOTEBOOK_PATH), "exec"), ns)
    return ns


BUSINESS_DOMAIN = {"domain": "customer", "name": "customer", "division": "business",
                   "database_name": "stg_customer"}
OPS_DOMAIN = {"domain": "inventory", "name": "inventory", "division": "operations",
              "database_name": "stg_inventory"}


def test_display_form_catalog_per_division_resolves_division_catalog():
    """The exact 05b failure: display 'Catalog per Division' must resolve to the
    prefixed division catalog, NOT the base catalog."""
    ns = _resolver_namespace()
    CatalogResolver = ns["CatalogResolver"]
    r = CatalogResolver(
        style="Catalog per Division",  # DISPLAY form — what the tester/op passes
        base_catalog="t04_mvm_v1_installed",
        prefix="t04_instmv1_",
        suffix="_zone",
        naming_convention="snake_case",
        schema_suffix="_layer",
    )
    cat = r.resolve_catalog(BUSINESS_DOMAIN)
    # Pre-patch this returned the base catalog 't04_mvm_v1_installed' (the bug).
    assert cat == "t04_instmv1_business_zone", (
        f"display 'Catalog per Division' resolved to {cat!r}; expected the "
        f"division catalog 't04_instmv1_business_zone' (pre-patch bug returns base_catalog)"
    )
    assert r.resolve_catalog(OPS_DOMAIN) == "t04_instmv1_operations_zone"


def test_display_form_catalog_per_domain_resolves_domain_catalog():
    ns = _resolver_namespace()
    CatalogResolver = ns["CatalogResolver"]
    r = CatalogResolver(
        style="Catalog per Domain",  # DISPLAY form
        base_catalog="base_cat",
        prefix="pre_",
        suffix="_suf",
        naming_convention="snake_case",
    )
    # per-domain catalog = affixed domain name, NOT base_catalog
    assert r.resolve_catalog(BUSINESS_DOMAIN) == "pre_customer_suf"


def test_snake_forms_unchanged():
    """Already-snake styles must pass through unchanged (no regression)."""
    ns = _resolver_namespace()
    CatalogResolver = ns["CatalogResolver"]
    r = CatalogResolver(style="catalog_per_division", base_catalog="b",
                        prefix="p_", suffix="_s")
    assert r.resolve_catalog(BUSINESS_DOMAIN) == "p_business_s"


def test_one_catalog_display_and_snake_return_base():
    """One Catalog (both forms) must return the base catalog — unchanged behavior."""
    ns = _resolver_namespace()
    CatalogResolver = ns["CatalogResolver"]
    for style in ("One Catalog", "one_catalog"):
        r = CatalogResolver(style=style, base_catalog="the_base")
        assert r.resolve_catalog(BUSINESS_DOMAIN) == "the_base"


def test_style_normalization_recorded_on_instance():
    """After construction, self.style must be the canonical snake form regardless
    of the input casing/spacing."""
    ns = _resolver_namespace()
    CatalogResolver = ns["CatalogResolver"]
    assert CatalogResolver("Catalog per Division", "b").style == "catalog_per_division"
    assert CatalogResolver("  Catalog Per Division  ", "b").style == "catalog_per_division"
    assert CatalogResolver("catalog_per_domain", "b").style == "catalog_per_domain"


def test_style_normalize_alias_present_in_source():
    """Smoke: the resolver's normalization is wired at the one component that
    needs the snake form. The gensamples landing gates left with the sample
    subsystem in v4.8.0 and now live in the model installer."""
    assert "catalogresolver-style-normalize FIRED v4.6.4" in SOURCE
