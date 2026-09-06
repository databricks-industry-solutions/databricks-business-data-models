"""v4.8.5 - the published metric SQL must be the SQL that was actually executed.

Live evidence (coffee_roastery mvm_v1, agent 4.8.3, run 1060088887830650, then replayed by
the installer into catalog cr483_install):

  agent's own catalog      : 23/23 metric views, retail_loyalty_account present
  installer replaying the  : 22/23, retail_loyalty_account fails with
  PUBLISHED artifacts        [UNRESOLVED_COLUMN] `preferred_store_id` cannot be resolved

The agent built the view because mv-column-prevalidate-prune rewrote the statement in
memory first:

  [mv-column-prevalidate-prune] pruned: retail_loyalty_account -- physical
  `retail.loyalty_account` missing col(s) ['preferred_store_id'] -- pruned offending
  block(s), view KEPT

(the column had been renamed preferred_store_id -> store_id by the FK naming pass). The
pruned statement is what ran. The UNPRUNED statement is what was written to
metrics/*.sql and model.json, so every consumer of the published model inherits a broken
view the agent itself never executed.

v4.8.3 rewrote the artifacts only when a view FAILED or the retry ladder produced a
fallback. A prune produces neither: nothing fails, so the gate stayed shut. Chasing that
by teaching the gate about the prune would leave the next mutation path (dedup,
stale-catalog rewrite, or whatever is added later) with the same hole.

So this fixes the invariant instead of the instance: metric_view_statements is the
authoritative post-mutation list, and the artifacts are now mirrored from it on every
run. When nothing was mutated the rewrite is byte-identical, so the cost is one idempotent
write per domain and the artifact can no longer disagree with what executed.
"""
import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

OLD = '''    # v4.8.3 alias=mv-artifact-rewrite-on-repair -- also rewrite when the ladder repaired
    # a view but nothing failed: the in-memory substitution reaches model.json, the file on
    # the volume does not, and the file is what a consumer installs.
    if _mv_failed_ct > 0 or _mv_fallback_statements:'''

NEW = '''    # v4.8.5 alias=mv-artifact-mirrors-executed -- the artifact is mirrored from the
    # statements that actually executed, on every run. Gating this on "something failed or
    # the ladder produced a fallback" (v4.8.3) missed every OTHER mutation path: a
    # mv-column-prevalidate-prune drops an unresolvable column, the view then builds fine,
    # nothing fails, the gate stays shut, and the file on the volume keeps the unpruned SQL
    # that no consumer can install (coffee_roastery retail_loyalty_account,
    # preferred_store_id). metric_view_statements is authoritative post-mutation, so mirror
    # it unconditionally; with no mutation the rewrite is byte-identical.
    if metric_view_statements:'''

OLD_LOG = ('logger.info(f"[mv-artifact-rewrite-on-repair FIRED v4.8.3] rewrote '
           '{_rewritten_count} metric SQL file(s) on disk')
NEW_LOG = ('logger.info(f"[mv-artifact-mirrors-executed FIRED v4.8.5] rewrote '
           '{_rewritten_count} metric SQL file(s) on disk')


def cell_text(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def put(cell, text):
    cell["source"] = text.splitlines(keepends=True) if isinstance(cell.get("source"), list) else text


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    edits = {"gate": 0, "log": 0, "version": 0}

    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = cell_text(cell)
        out = src
        if OLD in out:
            out = out.replace(OLD, NEW)
            edits["gate"] += 1
        if OLD_LOG in out:
            out = out.replace(OLD_LOG, NEW_LOG)
            edits["log"] += 1
        if '__AGENT_VERSION__ = "4.8.4"' in out:
            out = out.replace('__AGENT_VERSION__ = "4.8.4"', '__AGENT_VERSION__ = "4.8.5"')
            edits["version"] += 1
        if out != src:
            put(cell, out)

    for key in edits:
        if edits[key] != 1:
            print("FAIL %s: expected 1 anchor, matched %d" % (key, edits[key]))
            return 1

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    print("patched: %s" % edits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
