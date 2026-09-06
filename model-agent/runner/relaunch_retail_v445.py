#!/usr/bin/env python3
"""v4.4.5 retail VOV relaunch on the idle, isolated my-uae workspace.

Reuses the vov_v2_marathon helpers (§3d) to run retail v1 ECM -> v2 ECM -> v2 MVM with the merged
reviewer next_vibes, proving the v4.4.5 fixes: P2 generic vendor lexicon + anchored strip + color-std
shield, P3 enum free-STRING, on top of the v4.4.1-4 finalization (P6/P7/P9/P11/P12/P13) and
_v443_structural_hardening (G1/G3/G9/G11/G12). Fresh install so VOV operates on the identical v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "retail", "my-uae"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v445"

M.AGENT_VER = "445"
M.AGENT_PATH = NEW


def main():
    reused = M.prepare_catalog(PROF, IND)
    M.stage_files(PROF, IND, reused=reused)
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
