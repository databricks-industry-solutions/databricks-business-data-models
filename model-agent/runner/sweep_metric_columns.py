#!/usr/bin/env python3
"""Complete, SAFE static sweep of metric-view column refs.

For every metric view, resolve EVERY expr identifier that is not a valid source-table
column to `{table}_{id}` (or a unique `_{id}` suffix match) verified against the real
schema DDL. RENAME-ONLY and EXPR-LINES-ONLY:
  - never drops a view (so SQL functions like date_add/regexp_extract that look like
    idents are simply left alone when they have no column resolution -> no false-positive
    drops, the flaw that made fix_all_metrics unusable repo-wide).
  - only edits `expr:` value lines, so dimension display names and comments are preserved.

Genuine source defects (a bare col with no `{table}_{id}` resolution, missing source
table, nested aggregate) are NOT touched here; they surface in a follow-up probe and are
dropped by patch_metric_failures.py.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fix_all_metrics as fam

REPO = Path.home() / "Documents/projects/lakehouse-business-data-models"
VIEW_BLOCK_RE = re.compile(r"CREATE OR REPLACE VIEW[\s\S]*?\$\$;", re.IGNORECASE)
EXPR_LINE_RE = re.compile(r"^(\s*expr:\s*)(.+?)(\s*)$", re.MULTILINE)


def rename_in_expr_lines(block: str, renames: dict[str, str]) -> str:
    if not renames:
        return block
    compiled = [(re.compile(rf"(?<![A-Za-z0-9_]){re.escape(b)}(?![A-Za-z0-9_])"), g)
                for b, g in sorted(renames.items(), key=lambda x: -len(x[0]))]

    def repl(m):
        val = m.group(2)
        for pat, g in compiled:
            val = pat.sub(g, val)
        return m.group(1) + val + m.group(3)

    return EXPR_LINE_RE.sub(repl, block)


def main() -> None:
    total_renames = 0
    touched = 0
    dm = REPO / "data-models"
    for ind_dir in sorted(d for d in dm.iterdir() if d.is_dir()):
        ver = fam.latest_version_dir(ind_dir)
        if not ver:
            continue
        for size in ("ecm", "mvm"):
            md = ver / size / "metrics"
            sd = ver / size / "schemas"
            if not md.is_dir():
                continue
            schema_cols = fam.parse_schema_columns(sd)
            for mf in sorted(md.glob("*.sql")):
                text = mf.read_text(errors="ignore")
                changed = False
                out = text
                for block in VIEW_BLOCK_RE.findall(text):
                    src = fam.extract_source(block)
                    if not src:
                        continue
                    valid = schema_cols.get(src, set())
                    if not valid:
                        continue
                    table = src[1]
                    renames: dict[str, str] = {}
                    for ident in fam.collect_expr_idents(block):
                        if ident in valid:
                            continue
                        good = fam.resolve_column(ident, valid, table)
                        if good and good != ident:
                            renames[ident] = good
                    if renames:
                        new_block = rename_in_expr_lines(block, renames)
                        if new_block != block:
                            out = out.replace(block, new_block, 1)
                            total_renames += len(renames)
                            changed = True
                if changed:
                    mf.write_text(out)
                    touched += 1
    print(f"sweep: touched_files={touched} total_renames={total_renames}")


if __name__ == "__main__":
    main()
