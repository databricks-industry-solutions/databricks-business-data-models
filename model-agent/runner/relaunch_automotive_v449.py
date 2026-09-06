#!/usr/bin/env python3
"""v4.4.9 automotive VOV regen on the idle, isolated fe-aws workspace.

Reuses the vov_v2_marathon helpers (CLAUDE.md 3d) to run automotive v1 ECM -> v2 ECM -> v2 MVM with the
merged USER-KING reviewer next_vibes (Max Koehler value-chain review) on the LATEST fixed agent v4.4.9.
The v4.4.9 fix that matters here is G7 (v443-silo-inbound-relink + v443-silo-selffk-exclude): the FK-linker
now wires INBOUND FKs into siloed hierarchical/geographic reference dims (customer.organization_account,
aftersales.aftersales_market) instead of trying wrong OUTBOUND FKs -> 0 silos -> ECM 12/12. Target: 8/8
reviewer adherence retained + ECM 12/12. Fresh install (VOV_FORCE_REINSTALL=1) so VOV runs from the v1 seed.
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "automotive", "fe-aws"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v449"

M.AGENT_VER = "449"
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
