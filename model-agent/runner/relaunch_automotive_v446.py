#!/usr/bin/env python3
"""v4.4.6 automotive VOV regen on the idle, isolated fe-aws workspace.

Reuses the vov_v2_marathon helpers (CLAUDE.md §3d) to run automotive v1 ECM -> v2 ECM -> v2 MVM with
the merged USER-KING reviewer next_vibes (Max Koehler value-chain review). Proves the v4.4.6 automotive
capability gaps: GAP-1 (surgical-VOV outcome-scope guard whitelists a USER-KING new domain -> field_services
+ 12 products land), GAP-2 (connect FK re-scoped to the reviewer-named domain), GAP-3 (shrink force-keeps
the reviewer keep-in-MVM procurement/mobility products), GAP-4 (ai_query None-timeout null-guard), on top of
the retail G2/G5/G7 structural hardening. Fresh install (VOV_FORCE_REINSTALL=1) so VOV runs from the v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "automotive", "fe-aws"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v446"

M.AGENT_VER = "446"
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
