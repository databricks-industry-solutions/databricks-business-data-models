#!/usr/bin/env python3
"""v4.5.2 automotive VOV regen on the idle, isolated fe-aws workspace.

Reuses the vov_v2_marathon helpers (CLAUDE.md 3d) to run automotive v1 ECM -> v2 ECM -> v2 MVM with the
merged USER-KING reviewer next_vibes (Max Koehler value-chain review) on the LATEST fixed agent v4.5.2.
v4.5.2 adds v452-post-finalize-cycle-guard: the deterministic _v403 serialize cycle guard is re-run at the
TRUE-last mutator boundary (AFTER _v441_reviewer_finalization), so mutual FK pairs the reviewer finalizer
stubs between two sibling products (A.b_id->B, B.a_id->A) can no longer ship as 2-cycles / bidirectional
FKs (G4+G6). Carries the v4.5.1 parser generalization (vov-named-create-targets) + v443 G7 silo-inbound
relink. Target: 8/8 reviewer adherence retained + ECM 12/12. Fresh install (VOV_FORCE_REINSTALL=1).
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "automotive", "fe-aws"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v452"

M.AGENT_VER = "452"
M.AGENT_PATH = NEW
M.ASSIGN = {PROF: [IND]}
M._IND_PROFILE = {IND: PROF}
M.WAREHOUSE[PROF] = "862f1d757f0424f7"  # dbdemos-shared-endpoint (RUNNING)


def main():
    reused = M.prepare_catalog(PROF, IND)
    M.stage_files(PROF, IND, reused=reused)
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
