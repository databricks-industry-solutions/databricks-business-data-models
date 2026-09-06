#!/usr/bin/env python3
"""v4.4.2 automotive VOV regen on an idle, isolated workspace (fe-aws).

Reuses the vov_v2_marathon helpers (CLAUDE.md §3d) to run the automotive
v1 ECM -> v2 ECM -> v2 MVM pipeline with the merged USER-KING reviewer
next_vibes (Max Koehler value-chain review), fully isolated from the
in-flight retail run (retail is on fe-gcp/my-uae; automotive uses fe-aws,
separate metastore, catalog vibe_automotive_v1 -> no collision).

Clean fresh install (VOV_FORCE_REINSTALL=1) so VOV operates on the identical
staged automotive v1 seed. Consumes the deployed v4.4.2 agent (scratch/v435
HEAD, unmodified).
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "automotive", "fe-aws"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v442"

# isolate the marathon config onto fe-aws for automotive only (explicit > clever)
M.AGENT_VER = "442"
M.AGENT_PATH = NEW
M.ASSIGN = {PROF: [IND]}
M._IND_PROFILE = {IND: PROF}
M.WAREHOUSE[PROF] = "862f1d757f0424f7"  # dbdemos-shared-endpoint (RUNNING)


def main():
    reused = M.prepare_catalog(PROF, IND)          # DROP+CREATE vibe_automotive_v1
    M.stage_files(PROF, IND, reused=reused)         # stage model.json + next_vibes.txt to volume
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
