#!/usr/bin/env python3
"""Second removal pass: the residue pass 1 left behind.

Pass 1 deleted the sample-generation definitions and the widget/dispatch wiring.
This pass removes what still referenced them: the orphaned install-time sample
LOADER block, the SAMPLE_POOL_PROMPT template, the Faker import, the two dead
sanity harnesses, and every doc/markdown mention.

Run with --check for a dry run.
"""
import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

# (cell, first_line, last_line, why) — inclusive, 1-based. Applied per cell in
# descending order so earlier ranges keep their line numbers.
LINE_DELETIONS = [
    (82, 5469, 5589, "SAMPLE_POOL_PROMPT template + its preamble comment"),
    (82, 6107, 6122, "Faker import / _FAKER_AVAILABLE / _FAKER_INSTANCE"),
    (162, 1274, 1276, "dangling pool-contract comment"),
    (206, 2577, 2708, "orphaned install-time sample loader (_generate_samples_enabled)"),
    (210, 1, 247, "_sample_helpers_sanity_check + its disabled invocation"),
    (214, 267, 468, "_p083_pool_parse_sanity_check"),
]

REPLACEMENTS = [
    (0, "doc-op-table-row",
     "| Demo | `generate sample data` | Synthetic rows for demos and QA |\n", ""),
    (0, "doc-widget-table-row",
     "| 10 | `generate_samples` | No | Base / samples | `0` = off; `5`\u2013`100` rows per table |\n", ""),
    (25, "catalogresolver-comment",
     '        # form ("catalog_per_division"/...). ROOT CAUSE of the 05b sample-gen 0-rows silent\n'
     '        # no-op: _run_generate_samples built the resolver with the UNnormalized display style,\n'
     '        # so resolve_catalog() matched no branch and silently returned base_catalog \u2014 routing\n'
     '        # every Catalog-per-Division/Domain sample INSERT to the BASE catalog and leaving the\n'
     '        # division/domain tables empty while the op reported success. The install path\n'
     '        # normalized via _CATALOGING_STYLE_MAP; the standalone op did not. Normalizing HERE\n',
     '        # form ("catalog_per_division"/...). A caller that passes the UNnormalized display\n'
     '        # style makes resolve_catalog() match no branch and silently return base_catalog,\n'
     '        # routing every Catalog-per-Division/Domain write to the BASE catalog while the\n'
     '        # caller still reports success. Normalizing HERE\n'),
    (83, "doc-cell83-header",
     "## Utility Functions & Validators \u2014 `_p083_emit_raw_pool_log` \u2026 `_cached_json_load`",
     "## Utility Functions & Validators \u2014 `_io_with_timeout` \u2026 `_cached_json_load`"),
    (83, "doc-cell83-prose",
     "retry/backoff, sample-data pools, and", "retry/backoff, and"),
    (83, "doc-cell83-bullets",
     "- `_p083_emit_raw_pool_log` \u2014 the nested sample helper can call it without closure gymnastics. Capped\n"
     "- `_p068_faker_provider_map` \u2014 Ordering matters: more specific multi-token patterns come first so that\n"
     "- `_p068_pick_faker_provider` \u2014 Internal helper: p068 pick faker provider.\n", ""),
    (206, "op-icon-map",
     '            "generate sample data": "\U0001f522", "shrink model": "\U0001f4c9", "enlarge model": "\U0001f4c8",',
     '            "shrink model": "\U0001f4c9", "enlarge model": "\U0001f4c8",'),
    (209, "doc-cell209-header",
     "## Main Entry & Sanity Checks \u2014 `_sample_helpers_sanity_check` \u2026 `_product_collision_sanity_check`",
     "## Main Entry & Sanity Checks \u2014 `_autofix_sanity_check` \u2026 `_product_collision_sanity_check`"),
    (209, "doc-cell209-bullet",
     "- `_sample_helpers_sanity_check` \u2014 IMPORTANT: this harness re-implements the nested helpers (`_sample_temporal`,\n", ""),
    (210, "sanity-call-p083", "    _p083_ok = _p083_pool_parse_sanity_check()\n", ""),
    (210, "sanity-return",
     "    return (_nc_ok and _mv_ok and _collision_ok and _pii_ok and _rx_ok\n"
     "            and _faker_ok and _chunk_ok and _nv_ok\n"
     "            and _p081_ok and _p091_ok and _p089_ok and _p083_ok)",
     "    return (_nc_ok and _mv_ok and _collision_ok and _pii_ok and _rx_ok\n"
     "            and _chunk_ok and _nv_ok\n"
     "            and _p081_ok and _p091_ok and _p089_ok)"),
    (211, "doc-cell211-bullet",
     "- `_p068_faker_tier2_sanity_check` \u2014 Internal helper: p068 faker tier2 sanity check.\n", ""),
    (213, "doc-cell213-header",
     "## Main Entry & Sanity Checks \u2014 `_naming_convention_sanity_check` \u2026 `_p083_pool_parse_sanity_check`",
     "## Main Entry & Sanity Checks \u2014 `_naming_convention_sanity_check` \u2026 `_p089_vreq_bleed_sanity_check`"),
    (213, "doc-cell213-bullet",
     "- `_p083_pool_parse_sanity_check` \u2014 Internal helper: p083 pool parse sanity check.\n", ""),
]

# The twelve pipeline-step markdown headers all carry the same stale blurb.
STEP_DOC_CELLS = list(range(169, 192, 2))
STEP_DOC_REPLACEMENTS = [
    ("## Pipeline Steps: Physical Schema, FK, Tags & Samples \u2014",
     "## Pipeline Steps: Physical Schema, FK & Tags \u2014"),
    ("Builds Unity Catalog DDL, applies FK metadata, sets column/table tags, and optionally generates Faker-based sample rows for demos.",
     "Builds Unity Catalog DDL, applies FK metadata, and sets column/table tags."),
]


def cell_source(cell):
    src = cell["source"]
    return "".join(src) if isinstance(src, list) else src


def main():
    check = "--check" in sys.argv
    nb = json.loads(NB.read_text())
    cells = nb["cells"]
    sources = {i: cell_source(c) for i, c in enumerate(cells)}
    applied = []

    by_cell = {}
    for cell, start, end, why in LINE_DELETIONS:
        by_cell.setdefault(cell, []).append((start, end, why))
    for cell, spans in by_cell.items():
        lines = sources[cell].split("\n")
        for start, end, why in sorted(spans, reverse=True):
            del lines[start - 1:end]
            applied.append(f"- cell {cell} lines {start}-{end}: {why}")
        sources[cell] = "\n".join(lines)

    for cell, alias, old, new in REPLACEMENTS:
        count = sources[cell].count(old)
        if count != 1:
            raise SystemExit(f"{alias}: expected 1 occurrence in cell {cell}, found {count}")
        sources[cell] = sources[cell].replace(old, new)
        applied.append(f"~ cell {cell} {alias}")

    for cell in STEP_DOC_CELLS:
        for old, new in STEP_DOC_REPLACEMENTS:
            count = sources[cell].count(old)
            if count != 1:
                raise SystemExit(f"step-doc: expected 1 occurrence in cell {cell}, found {count}")
            sources[cell] = sources[cell].replace(old, new)
        applied.append(f"~ cell {cell} step-doc-header")

    for i, text in sources.items():
        cells[i]["source"] = text

    print("\n".join(applied))
    if check:
        print("DRY RUN \u2014 nothing written")
        return
    before = NB.stat().st_size
    # ensure_ascii=True restores the \uXXXX escaping the repo's copy uses, so the
    # diff stays scoped to the cells this pass actually edits.
    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print(f"notebook written ({before} -> {NB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
