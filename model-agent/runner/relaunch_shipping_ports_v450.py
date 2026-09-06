#!/usr/bin/env python3
"""v4.5.0 shipping_ports VOV relaunch on the idle, isolated fe-gcp workspace.

Reuses the vov_v2_marathon helpers (CLAUDE.md 3d) to run shipping_ports v1 ECM -> v2 ECM -> v2 MVM with
the merged USER-KING reviewer next_vibes (Ahmed Elmaadawy / DP World review, R1-R9) on the LATEST fixed
agent v4.5.0. The critical v4.5.0 fix here is GAP-5 (verifier-product-create-coverage +
vov-preskip-productcreate-guard): the deterministic "ALREADY FULFILLED" pre-skip no longer false-positives
on generative add_product VREQs when the concept token merely appears as an existing column/measure/flag
(transhipment_teu). With GAP-5 fixed, the 8 add_product directives (R1,R2,R3,R5,R6,R7,R8,R9 = 18 named
tables) land -> >=90% adherence + 12/12 gates. Fresh install (VOV_FORCE_REINSTALL=1) from the v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "shipping_ports", "fe-gcp"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v450"

M.AGENT_VER = "450"
M.AGENT_PATH = NEW
M.ASSIGN = {PROF: [IND]}
M._IND_PROFILE = {IND: PROF}
M.WAREHOUSE[PROF] = "d6d89fb9fd47b835"  # fe-gcp Serverless Starter


def main():
    reused = M.prepare_catalog(PROF, IND)
    M.stage_files(PROF, IND, reused=reused)
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
