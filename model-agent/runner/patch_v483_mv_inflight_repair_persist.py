"""v4.8.3 alias=mv-inflight-repair-persist

The metric-view executor repairs a failing view inside the worker and returns
SUCCESS, but only `_v467_install_mv_fallback` ever recorded its repaired text
into `fallback_statements`. Everything the in-worker repair ladder fixed was
therefore executed and then thrown away, so the artifact on the volume kept the
broken original and any consumer replaying it lost the view.

This records every in-flight repair into the same channel the existing
`mv-strict-parity-repair` consumer already persists.
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

RECORDER = '''    fallback_statements = {}
    def _v483_record_repair(metric_view_name, repaired_stmt):
        # v4.8.3 alias=mv-inflight-repair-persist -- the repair ladder below rewrites a
        # statement, executes it, and returns SUCCESS. Without this the repaired text dies
        # with the worker: metrics/*.sql and model.json keep the original, so the agent's
        # catalog has the view and every consumer installing the artifact loses it.
        # Trailing ';' is stripped because the artifact writer re-joins statements on ';'.
        if not metric_view_name or not isinstance(repaired_stmt, str) or not repaired_stmt.strip():
            return
        _clean = repaired_stmt.strip()
        while _clean.endswith(";"):
            _clean = _clean[:-1].rstrip()
        # dict/list mutation is atomic under the GIL; the pool has no other writer.
        fallback_statements[metric_view_name] = _clean
        if metric_view_name not in fallback_repaired:
            fallback_repaired.append(metric_view_name)
        logger.info(
            f"  [mv-inflight-repair-persist FIRED v4.8.3] view='{metric_view_name}' "
            f"repaired statement captured for the shipped artifact "
            f"alias=mv-inflight-repair-persist"
        )
'''

# (anchor line, statement variable holding the text that Spark accepted)
SITES = [
    ('                    logger.info(f"[Metrics] Retry succeeded for \'{metric_view_name}\' with safe measures")', "safe_stmt"),
    ('                        logger.info(f"[Metrics] Retry succeeded for \'{metric_view_name}\' after column rewrite")', "_rewritten"),
    ('                                logger.info(f"[Metrics] Retry2 succeeded for \'{metric_view_name}\' after 2-column rewrite")', "_rewritten2"),
    ('                        logger.info(f"[Metrics] Retry (DESCRIBE-rewrite) succeeded for \'{metric_view_name}\'")', "_rewritten_desc"),
    ('                                logger.info(f"[Metrics] Retry2 (DESCRIBE-rewrite) succeeded for \'{metric_view_name}\'")', "_rewritten_desc2"),
    ('                        logger.info(f"[Metrics] Retry3b (strip-bare-column-entries) succeeded for \'{metric_view_name}\'")', "_stripped_stmt"),
    ('                    logger.info(f"[Metrics] Retry4 (safe-measures fallback) succeeded for \'{metric_view_name}\'")', "safe_stmt"),
]


def main():
    nb = json.load(open(NB))
    changed = {"recorder": 0, "sites": 0, "version": 0}

    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        orig = src

        if "    fallback_statements = {}\n" in src and "_v483_record_repair" not in src:
            src = src.replace("    fallback_statements = {}\n", RECORDER, 1)
            changed["recorder"] += 1

        if "_v483_record_repair" in src:
            for anchor, var in SITES:
                if anchor not in src:
                    continue
                indent = " " * (len(anchor) - len(anchor.lstrip()))
                call = "%s_v483_record_repair(metric_view_name, %s)\n" % (indent, var)
                # Guard per anchor, not per call text: the two safe-measures sites emit an
                # identical call line, so a global "already present" test skips the second.
                if anchor + "\n" + call in src:
                    continue
                src = src.replace(anchor + "\n", anchor + "\n" + call, 1)
                changed["sites"] += 1

        if '__AGENT_VERSION__ = "4.8.2"' in src:
            src = src.replace('__AGENT_VERSION__ = "4.8.2"', '__AGENT_VERSION__ = "4.8.3"', 1)
            changed["version"] += 1

        if src != orig:
            # Preserve the cell's original source representation. These cells store source
            # as one JSON string; re-emitting a list of lines is semantically identical to
            # Jupyter but rewrites the whole cell and buries the change in an 850-line diff.
            cell["source"] = src if isinstance(cell.get("source"), str) else src.splitlines(keepends=True)

    if changed["recorder"] != 1:
        sys.exit("recorder: expected 1 insertion, got %d" % changed["recorder"])
    if changed["sites"] != len(SITES):
        sys.exit("sites: expected %d, got %d" % (len(SITES), changed["sites"]))
    if changed["version"] != 1:
        sys.exit("version: expected 1 bump, got %d" % changed["version"])

    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    print("patched: %s" % changed)


if __name__ == "__main__":
    main()
