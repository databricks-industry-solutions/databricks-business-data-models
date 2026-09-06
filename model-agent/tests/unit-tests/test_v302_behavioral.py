"""Behavioral tests for v3.0.2 orphan-recovery batch grouping fix.

ROOT CAUSE (healthcare ecm_v3 2026-06-02): the orphan-recovery path inside
_apply_batches_for_vreqs built ONE 1-VREQ Batch per orphan VREQ:

    for _oid in sorted(_orphan_ids):
        ...
        _recovery_batches.append(Batch(batch_id=f"orphan-recovery-{_oid}",
                                       vreq_ids=(str(_oid),), ...))

477 user directives that did not resolve to a concrete (domain,product) all
orphaned -> ~487 one-VREQ batches, each byte-split x3 -> 843 batches -> 1300+
LLM synthesis calls in iteration 1 -> 3.7h with no iteration close.

FIX (alias=v302-orphan-recovery-grouped): reuse the existing _heuristic_batch
grouper (deterministic_pre_group + target-resolve + 25-VREQ window) so orphans
are batched together. Batch is frozen, so batch_id is re-tagged via
dataclasses.replace.

Non-tautology (CLAUDE.md 8.10): test_orphan_path_uses_grouper_not_per_vreq
fails on pre-patch HEAD (the 1-per-VREQ pattern is present and the
_heuristic_batch delegation is absent), so the suite proves the routing change,
not just that the grouper exists.
"""
import re
import textwrap

from notebook_source_util import notebook_concat_source

SRC = notebook_concat_source()


def _load_batcher_ns():
    """Slice the real dataclasses + batch grouper family from the notebook."""
    dc = re.search(
        r"@dataclass\(frozen=True\)\nclass RawVREQ:.*?(?=@dataclass\(frozen=True\)\nclass Handler:)",
        SRC,
        re.DOTALL,
    )
    assert dc, "RawVREQ/Batch dataclasses not found"
    # v4.6.4: slice the batcher family by AST rather than a trailing comment marker. The legacy
    # end-anchor "# ----- inlined from agent/vov_2_0/synthesizer" was removed in a prior notebook
    # refactor, so the old regex lookahead no longer matched (pre-existing collection break, fails
    # identically on HEAD). The family is the contiguous module-level span from
    # deterministic_pre_group through _heuristic_batch (inclusive) — the same span the marker bounded.
    import ast as _ast
    _tree = _ast.parse(SRC)
    _lines = SRC.splitlines(keepends=True)
    _fam_start = _fam_end = None
    for _node in _tree.body:
        if isinstance(_node, _ast.FunctionDef):
            if _node.name == "deterministic_pre_group":
                _fam_start = _node.lineno - 1
            if _node.name == "_heuristic_batch":
                _fam_end = _node.end_lineno
    assert _fam_start is not None and _fam_end is not None and _fam_end > _fam_start, (
        "batch grouper family not found"
    )
    fam_src = "".join(_lines[_fam_start:_fam_end])
    ns = {}
    exec(
        "from dataclasses import dataclass, field\n"
        "from collections import defaultdict\n"
        "from typing import Optional, List, Dict, Tuple\n"
        "import re, hashlib\n",
        ns,
    )
    exec(compile(textwrap.dedent(dc.group(0)), "agent_dataclasses", "exec"), ns)
    exec(compile(fam_src, "agent_batcher", "exec"), ns)
    return ns


NS = _load_batcher_ns()


def _orphans(n):
    R = NS["RawVREQ"]
    # "other"-bucket, no concrete target -> the worst case that previously
    # produced 1-per-VREQ orphan batches.
    return [
        R(
            vreq_id=f"V{i:04d}",
            intent="ensure attribute completeness for the entity",
            target="",
            source_quote="",
            source_chunk_id="c",
        )
        for i in range(n)
    ]


def test_grouper_collapses_orphans_into_windows():
    """The delegation target (_heuristic_batch) batches N orphans into few
    multi-VREQ windows, not N 1-VREQ batches. 60 orphans -> <=5 batches."""
    hb = NS["_heuristic_batch"]
    model = {"model": {"domains": [{"name": "ops", "products": [{"name": "shipment"}, {"name": "order"}]}]}}
    batches = hb(_orphans(60), model_snapshot=model)
    assert 0 < len(batches) <= 5, f"expected grouped (<=5) batches, got {len(batches)}"
    total = sum(len(b.vreq_ids) for b in batches)
    assert total == 60, f"all 60 orphans must be covered, got {total}"
    assert max(len(b.vreq_ids) for b in batches) > 1, "batches must be multi-VREQ (grouped)"


def test_grouper_window_cap_is_25():
    """Each grouped batch holds at most 25 VREQs (the existing window cap)."""
    hb = NS["_heuristic_batch"]
    batches = hb(_orphans(40), model_snapshot=None)
    assert batches, "expected at least one batch"
    assert all(len(b.vreq_ids) <= 25 for b in batches), "window cap of 25 violated"


def test_orphan_path_uses_grouper_not_per_vreq():
    """NON-TAUTOLOGY: fails on pre-patch HEAD.

    Pre-patch the orphan loop emitted Batch(batch_id=f"orphan-recovery-{_oid}",
    vreq_ids=(str(_oid),)). Post-patch it delegates to _heuristic_batch.
    """
    assert 'batch_id=f"orphan-recovery-{_oid}"' not in SRC, (
        "old 1-VREQ-per-orphan batch pattern still present — fix not applied"
    )
    assert "_heuristic_batch(_orphan_vreqs" in SRC, (
        "orphan-recovery must delegate to the _heuristic_batch grouper"
    )


def test_fired_alias_present():
    assert "v302-orphan-recovery-grouped FIRED" in SRC, "v302 FIRED log marker missing"
    assert "_dc302.replace(_rb, batch_id=" in SRC, "frozen Batch re-tag via dataclasses.replace missing"


def test_version_at_least_302():
    m = re.search(r'__AGENT_VERSION__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', SRC)
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 0, 2), f"version {m.groups()} < 3.0.2"
