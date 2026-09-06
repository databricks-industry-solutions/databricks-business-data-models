#!/usr/bin/env python3
"""v4.4.6 shipping_ports VOV relaunch on an idle, isolated workspace (fe-gcp).

Reuses the vov_v2_marathon helpers (§3d) to run shipping_ports v1 ECM -> v2 ECM -> v2 MVM
with the merged USER-KING reviewer next_vibes (Ahmed Elmaadawy / DP World review), consuming
the LATEST fixed agent v4.4.6 (GAP-1 add_domain-with-products in surgical VOV scope) so the
reviewer 'create sustainability domain with products' directive lands. Runs in parallel with
the retail (my-uae) and automotive (fe-aws) siblings on a separate metastore/catalog
(vibe_shipping_ports_v1) -> no collision.

Clean fresh install (VOV_FORCE_REINSTALL=1) so VOV operates on the identical staged v1 seed.
Does NOT edit the agent notebook (consumes the committed HEAD v4.4.6 archive).
"""
import os
import sys

os.environ["VOV_FORCE_REINSTALL"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

IND, PROF = "shipping_ports", "fe-gcp"
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v446"

M.AGENT_VER = "446"
M.AGENT_PATH = NEW
# fe-gcp warehouse (Serverless Starter) — injected at runtime so the shared, sanitized
# WAREHOUSE map in the committed module is not edited (avoids disturbing the siblings).
M.WAREHOUSE["fe-gcp"] = "d6d89fb9fd47b835"


def main():
    reused = M.prepare_catalog(PROF, IND)          # DROP+CREATE vibe_shipping_ports_v1, install task runs
    M.stage_files(PROF, IND, reused=reused)        # stage model.json + next_vibes.txt to volume
    job_id = M.find_or_create_job(PROF, IND, installed=reused)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} PROFILE {PROF} CAT {M.cat_name(IND)} AGENT {NEW} reused={reused}")


if __name__ == "__main__":
    main()
