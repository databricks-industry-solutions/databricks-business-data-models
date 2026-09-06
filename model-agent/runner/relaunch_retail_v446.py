#!/usr/bin/env python3
"""v4.4.6 retail VOV relaunch on the idle my-uae workspace (fresh v1 reinstall).

Reuses the vov_v2_marathon helpers (§3d) to run retail v1 ECM -> v2 ECM -> v2 MVM with the merged
reviewer next_vibes. v4.4.6 adds the ECM structural-gate fixes (G2/G5 PK-corruption repair, G7 silo-relink
in _v443_structural_hardening) on top of the v4.4.5 P2/P3 finalization, so the retail v2 ECM clears all 12
marathon structural gates (v4.4.5 was 9/12: G2/G5/G7 failed). Fresh install (VOV_FORCE_REINSTALL=1) so VOV
operates on the identical v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "retail", "my-uae"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v446"

M.AGENT_VER = "446"
M.AGENT_PATH = NEW


def main():
    reused = M.prepare_catalog(PROF, IND)
    M.stage_files(PROF, IND, reused=reused)
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
