#!/usr/bin/env python3
"""v4.5.2 shipping_ports VOV relaunch on the idle, isolated fe-gcp workspace.

Reuses the vov_v2_marathon helpers (CLAUDE.md 3d) to run shipping_ports v1 ECM -> v2 ECM -> v2 MVM with
the merged USER-KING reviewer next_vibes (Ahmed Elmaadawy / DP World review, R1-R9) on the LATEST fixed
agent v4.5.2. v4.5.0 already lands the 18 named tables via GAP-5 (100% reviewer adherence in the v4.5.0
run). v4.5.2 fixes the residual ECM structural miss: the reviewer finalizer stubbed mutual FK pairs
between 3 sibling product pairs (transhipment<->transhipment_leg, container_condition_report<->
container_depot, dg_positioning_constraint<->dg_segregation_rule) that shipped as 2-cycles / bidirectional
FKs because _v403 ran BEFORE the finalizer. v452-post-finalize-cycle-guard re-runs the guard at the
true-last boundary -> ECM G4+G6 clean -> 12/12 gates. Fresh install (VOV_FORCE_REINSTALL=1) from v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "shipping_ports", "fe-gcp"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v452"

M.AGENT_VER = "452"
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
