"""v4.8.3 alias=mv-artifact-rewrite-on-repair

Second half of the in-flight-repair fix. The post-execution rewrite of
metrics/*.sql was gated on `_mv_failed_ct > 0`, so a run where every view was
created -- some of them only because the ladder repaired them -- never rewrote
the files. model.json picked the repaired statements up from the in-memory
substitution, but the SQL artifact on the volume kept the original text, which
is what a consumer replays.

Live case: coffee_roastery reported 0 failures and shipped 2 broken views.
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

OLD_GATE = "    if _mv_failed_ct > 0:\n"
NEW_GATE = (
    "    # v4.8.3 alias=mv-artifact-rewrite-on-repair -- also rewrite when the ladder repaired\n"
    "    # a view but nothing failed: the in-memory substitution reaches model.json, the file on\n"
    "    # the volume does not, and the file is what a consumer installs.\n"
    "    if _mv_failed_ct > 0 or _mv_fallback_statements:\n"
)

OLD_LOG = (
    '            logger.info(f"[Metrics][Cleanup] Rewrote {_rewritten_count} metric SQL file(s) '
    'on disk — failed statements removed")\n'
    '            print(f"   🧹 Metric cleanup: {len(_removed_stmts)} failed view(s) stripped from output files")\n'
)
NEW_LOG = (
    '            logger.info(f"[mv-artifact-rewrite-on-repair FIRED v4.8.3] rewrote {_rewritten_count} '
    'metric SQL file(s) on disk — {len(_removed_stmts)} failed statement(s) removed, '
    '{len(_mv_fallback_statements)} repaired statement(s) persisted '
    'alias=mv-artifact-rewrite-on-repair")\n'
    '            print(f"   🧹 Metric cleanup: {len(_removed_stmts)} failed view(s) stripped, '
    '{len(_mv_fallback_statements)} repaired view(s) persisted")\n'
)


def main():
    nb = json.load(open(NB))
    changed = {"gate": 0, "log": 0}

    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        if "_mv_fallback_statements" not in src:
            continue
        orig = src

        if OLD_GATE in src:
            src = src.replace(OLD_GATE, NEW_GATE, 1)
            changed["gate"] += 1
        if OLD_LOG in src:
            src = src.replace(OLD_LOG, NEW_LOG, 1)
            changed["log"] += 1

        if src != orig:
            cell["source"] = src if isinstance(cell.get("source"), str) else src.splitlines(keepends=True)

    if changed["gate"] != 1:
        sys.exit("gate: expected 1, got %d" % changed["gate"])
    if changed["log"] != 1:
        sys.exit("log: expected 1, got %d" % changed["log"])

    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    print("patched: %s" % changed)


if __name__ == "__main__":
    main()
