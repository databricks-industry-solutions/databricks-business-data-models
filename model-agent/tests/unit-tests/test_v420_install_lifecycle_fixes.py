import json
import os
import re

import pytest

_NB = os.path.join(
    os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb"
)


def _nb_source():
    with open(_NB) as f:
        nb = json.load(f)
    parts = []
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            parts.append("".join(c["source"]))
    return "\n".join(parts)


def _cell_source(idx):
    with open(_NB) as f:
        nb = json.load(f)
    return "".join(nb["cells"][idx]["source"])


# ---------------------------------------------------------------------------
# Version constant (CLAUDE.md §3a single-digit semver + §3a-bis global)
# ---------------------------------------------------------------------------

def test_agent_version_is_420():
    src = _cell_source(1)
    m = re.search(r'__AGENT_VERSION__\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', src)
    assert m, "no __AGENT_VERSION__ literal found in cell 1"
    assert m.group(1) == "4.2.0", f"expected 4.2.0, got {m.group(1)}"
    # every segment single-digit
    assert all(len(seg) == 1 for seg in m.group(1).split(".")), "single-digit semver violated"


# ---------------------------------------------------------------------------
# RC1 — generate-samples print UnboundLocalError (tests 05/08)
# ---------------------------------------------------------------------------

def test_rc1_behavioral_old_pattern_raises_new_pattern_works():
    """Proves the failure mode and the fix at the language level: the OLD pattern
    (read bare `print` then `def print`) raises UnboundLocalError; the NEW pattern
    (capture via `builtins`) does not."""

    def _old_pattern():
        _builtin_print = print  # reads function-local `print` -> UnboundLocalError

        def print(*a, **k):  # noqa: A001 - intentional shadow to reproduce the bug
            pass

        return _builtin_print

    with pytest.raises(UnboundLocalError):
        _old_pattern()

    def _new_pattern():
        import builtins as _sg_builtins

        _builtin_print = _sg_builtins.print

        def print(*a, **k):  # noqa: A001 - same shadow, but capture is safe now
            pass

        return _builtin_print

    import builtins as _b
    captured = _new_pattern()
    assert captured is _b.print, "new pattern must capture the real builtins.print"


# ---------------------------------------------------------------------------
# RC3 — per-division soft-replace must probe the BASE deployment_catalog
# ---------------------------------------------------------------------------

def test_rc3_softreplace_probes_base_catalog_marker():
    src = _cell_source(1)
    assert "v420-softreplace-base-metamodel" in src, "RC3 alias/marker missing"
    assert "_base_deploy_cat" in src
    # the probe set must be the UNION of clashing catalogs and the base catalog
    assert "_clashing_cats | ({_base_deploy_cat}" in src, "base catalog not unioned into probe set"


def test_rc3_behavioral_base_catalog_in_probe_set():
    """Replicates the v4.2.0 probe-set computation: even when the base
    deployment_catalog has NONE of the clashing schemas (the per-division case
    where `_metamodel` lives only in the base catalog), it MUST be in the set the
    soft-replace logic probes for `_metamodel`."""

    def _probe_set(clashing, base_deploy_cat):
        _clashing_cats = {cat for cat, _ in clashing}
        return sorted(_clashing_cats | ({base_deploy_cat} if base_deploy_cat else set()))

    # per-division: clashing schemas are in child catalogs; _metamodel is in base
    clashing = [("cdiv_operations_zone", "src_roasting_layer"),
                ("cdiv_business_zone", "src_customer_layer")]
    base = "repro_inst"
    probe = _probe_set(clashing, base)
    assert base in probe, "base deployment_catalog missing from probe set (RC3 regression)"
    assert "cdiv_operations_zone" in probe and "cdiv_business_zone" in probe

    # one_catalog: base IS the clashing catalog -> union is a no-op (no duplication)
    clashing_one = [("repro_inst", "roasting_layer")]
    probe_one = _probe_set(clashing_one, "repro_inst")
    assert probe_one == ["repro_inst"], "one_catalog probe set should be exactly the base catalog"

    # no base catalog supplied -> only clashing catalogs
    assert _probe_set(clashing, "") == ["cdiv_business_zone", "cdiv_operations_zone"]
