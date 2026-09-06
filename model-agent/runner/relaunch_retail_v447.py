#!/usr/bin/env python3
"""v4.4.7 retail VOV relaunch on the idle my-uae workspace (fresh v1 reinstall).

v4.4.7 adds deterministic reviewer-NAMED-artifact enforcement (P8 finance.payment_instrument vault
rename, P10 effective_start_date/effective_end_date SCD-2 cols, P1 rehome/rename-aware retype) in
_v441_reviewer_finalization, fixing the retail v4.4.6 P8/P10 regression where the non-deterministic
LLM loop failed to land the reviewer-named artifacts. Fresh install (VOV_FORCE_REINSTALL=1) so VOV
operates on the identical v1 seed. Reuses vov_v2_marathon helpers (§3d).
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "retail", "my-uae"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v447"

M.AGENT_VER = "447"
M.AGENT_PATH = NEW


def main():
    reused = M.prepare_catalog(PROF, IND)
    M.stage_files(PROF, IND, reused=reused)
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
