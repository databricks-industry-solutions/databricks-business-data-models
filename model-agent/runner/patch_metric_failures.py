#!/usr/bin/env python3
"""Surgically patch ONLY the metric views that actually failed at install (ground truth
from probe_metric_failures.json) against the real schema. No repo-wide sweep, so working
views are never touched.

Actions per failing view:
  - UNRESOLVED_COLUMN  -> rename bad generic col to `{table}_{col}` / unique `_{col}` match;
                          if unresolvable, drop the whole view block.
  - TABLE_OR_VIEW_NOT_FOUND / NESTED_AGGREGATE -> drop the view block (genuine source defect).
  - DATETIME_UNIT      -> unquote the DATEDIFF unit inside that view block.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fix_all_metrics as fam

REPO = Path.home() / "Documents/projects/lakehouse-business-data-models"
PROBE = Path.home() / "claude/vibe-agent/metric_probe_failures.json"
VIEW_BLOCK_RE = re.compile(r"CREATE OR REPLACE VIEW[\s\S]*?\$\$;", re.IGNORECASE)
MV_NAME_RE = re.compile(r"CREATE OR REPLACE VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`", re.IGNORECASE)
SRC_RE = re.compile(r'source:\s*"`[^`]+`\.`([^`]+)`\.`([^`]+)`"', re.IGNORECASE)
DATEDIFF_Q_RE = re.compile(r"DATEDIFF\(\s*'([^']+)'\s*,", re.IGNORECASE)
BAD_COL_RE = re.compile(r"name `([^`]+)` cannot be resolved")
EXPR_LINE_RE = re.compile(r"^(\s*expr:\s*)(.+?)(\s*)$", re.MULTILINE)


def rename_in_expr_lines(block: str, bad: str, good: str) -> str:
    """Replace whole-word `bad` -> `good` ONLY inside `expr:` value lines, case-sensitive,
    so dimension display names and comments are never mangled."""
    tok = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(bad)}(?![A-Za-z0-9_])")

    def repl(m):
        return m.group(1) + tok.sub(good, m.group(2)) + m.group(3)

    return EXPR_LINE_RE.sub(repl, block)


def latest_version_dir(industry_dir: Path) -> Path:
    vers = sorted((d for d in industry_dir.iterdir()
                   if d.is_dir() and re.match(r"^v\d+$", d.name)),
                  key=lambda d: int(d.name[1:]))
    return vers[-1]


def fix_datediff(block: str) -> str:
    def repl(m):
        u = m.group(1).strip().upper()
        return f"DATEDIFF({u}," if u in fam.DATEDIFF_ALLOWED_UNITS else m.group(0)
    return DATEDIFF_Q_RE.sub(repl, block)


def resolve_rename(bad: str, valid: set[str], table: str) -> str | None:
    return fam.resolve_column(bad, valid, table)


def main() -> None:
    probe = json.loads(PROBE.read_text())
    # group failures by (ind, size, file)
    by_file: dict[tuple[str, str, str], list[dict]] = {}
    for key, r in probe.items():
        _, ind, size = key.split(":")
        for f in r.get("failures", []):
            by_file.setdefault((ind, size, f["file"]), []).append(f)

    schema_cache: dict[tuple[str, str], dict] = {}
    renamed = dropped = datediff = unresolved_drop = 0
    touched_files = 0

    for (ind, size, fname), fails in sorted(by_file.items()):
        ver = latest_version_dir(REPO / "data-models" / ind)
        size_dir = ver / size
        mf = size_dir / "metrics" / fname
        text = mf.read_text(errors="ignore")
        ck = (ind, size)
        if ck not in schema_cache:
            schema_cache[ck] = fam.parse_schema_columns(size_dir / "schemas")
        schema_cols = schema_cache[ck]

        blocks = list(VIEW_BLOCK_RE.finditer(text))
        block_by_view = {}
        for m in blocks:
            mv = MV_NAME_RE.search(m.group(0))
            if mv:
                block_by_view[mv.group(1)] = m.group(0)

        new_text = text
        for f in fails:
            view = f["view"]
            err = f["error"]
            block = block_by_view.get(view)
            if not block:
                continue
            action = None
            new_block = block
            if "NESTED_AGGREGATE" in err or "TABLE_OR_VIEW_NOT_FOUND" in err:
                action = "drop"
            elif "DATETIME_UNIT" in err:
                new_block = fix_datediff(block)
                action = "datediff" if new_block != block else "drop"
            elif "UNRESOLVED_COLUMN" in err:
                bm = BAD_COL_RE.search(err)
                sm = SRC_RE.search(block)
                if bm and sm:
                    bad = bm.group(1)
                    table = sm.group(2)
                    valid = schema_cols.get((sm.group(1), table), set())
                    good = resolve_rename(bad, valid, table)
                    if good:
                        new_block = rename_in_expr_lines(block, bad, good)
                        action = "rename" if new_block != block else "drop"
                    else:
                        action = "drop"
                else:
                    action = "drop"
            else:
                action = "drop"

            if action == "drop":
                # remove block + any trailing blank lines
                new_text = new_text.replace(block, "", 1)
                dropped += 1
                if "UNRESOLVED_COLUMN" in err:
                    unresolved_drop += 1
            elif action == "datediff":
                new_text = new_text.replace(block, new_block, 1)
                datediff += 1
            elif action == "rename":
                new_text = new_text.replace(block, new_block, 1)
                renamed += 1
            # keep block_by_view current for repeated views in same file
            block_by_view[view] = new_block

        if new_text != text:
            new_text = re.sub(r"\n{3,}", "\n\n", new_text).rstrip() + "\n"
            mf.write_text(new_text)
            touched_files += 1

    print(f"touched_files={touched_files} renamed={renamed} datediff={datediff} "
          f"dropped={dropped} (of which unresolved_col_drop={unresolved_drop})")


if __name__ == "__main__":
    main()
