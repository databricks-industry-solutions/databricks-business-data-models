#!/usr/bin/env python3
"""v4.4.3 retail VOV relaunch on an idle, isolated workspace (my-uae).

Reuses the vov_v2_marathon helpers (§3d) to run the retail v1 ECM -> v2 ECM -> v2 MVM
pipeline with the merged reviewer next_vibes, proving the 5 deterministic reviewer-directive
fixes (P2/P6/P9/P11/P12/P13 + G1/G3/G9/G12 hardening). Runs in parallel with the in-flight v4.3.8 retail run on fe-gcp
(separate metastore, catalog vibe_retail_v1 -> no collision).

Clean fresh install (VOV_FORCE_REINSTALL=1) so VOV operates on the identical staged v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "retail", "my-uae"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v443"

M.AGENT_VER = "443"
M.AGENT_PATH = NEW


def main():
    reused = M.prepare_catalog(PROF, IND)          # DROP+CREATE vibe_retail_v1, install task runs
    M.stage_files(PROF, IND, reused=reused)        # stage model.json + next_vibes.txt to volume
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
