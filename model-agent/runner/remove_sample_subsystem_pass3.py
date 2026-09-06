#!/usr/bin/env python3
"""Third removal pass: the last references, including one live NameError.

`generate_samples` survived in an install-time emit_step f-string, which would
raise NameError now that the widget is gone. Also drops the operation from the
prompt registry, the emptied step cell and its doc cell, and the cosmetic-field
regex token.

Run with --check for a dry run.
"""
import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

DELETE_CELLS = [163, 164]  # doc cell + the code cell the deleted step used to own

REPLACEMENTS = [
    (3, "prompt-registry-operations", 3,
     '"basemodel", "vibe", "enlarge", "shrink", "generate sample data"]},',
     '"basemodel", "vibe", "enlarge", "shrink"]},'),
    (92, "cosmetic-comment", 1,
     "# (description|sample|faker|observability|kpi|comment) keep prior soft-accept.",
     "# (description|sample|observability|kpi|comment) keep prior soft-accept."),
    (92, "cosmetic-regex", 1,
     "r'(?i)(description|sample|faker|observability|kpi|comment|metric.view.kpi)'",
     "r'(?i)(description|sample|observability|kpi|comment|metric.view.kpi)'"),
    (206, "install-config-emit-message", 1,
     ", {_j_metric_ct} metric domains, generate_samples={generate_samples}\"",
     ", {_j_metric_ct} metric domains\""),
    (206, "install-config-emit-result", 1,
     '"json_metric_domains": _j_metric_ct, "generate_samples": generate_samples, "max_concurrent_batches"',
     '"json_metric_domains": _j_metric_ct, "max_concurrent_batches"'),
]


def main():
    check = "--check" in sys.argv
    nb = json.loads(NB.read_text())
    cells = nb["cells"]
    applied = []

    for cell, alias, expected, old, new in REPLACEMENTS:
        src = cells[cell]["source"]
        count = src.count(old)
        if count != expected:
            raise SystemExit(f"{alias}: expected {expected} in cell {cell}, found {count}")
        cells[cell]["source"] = src.replace(old, new)
        applied.append(f"~ cell {cell} {alias} (x{count})")

    for index in sorted(DELETE_CELLS, reverse=True):
        head = cells[index]["source"].split("\n")[0][:70]
        if index == 164 and cells[index]["source"].strip():
            raise SystemExit(f"cell {index} is not empty, refusing to delete")
        del cells[index]
        applied.append(f"- cell {index} deleted ({head!r})")

    print("\n".join(applied))
    if check:
        print("DRY RUN \u2014 nothing written")
        return
    before = NB.stat().st_size
    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print(f"notebook written ({before} -> {NB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
