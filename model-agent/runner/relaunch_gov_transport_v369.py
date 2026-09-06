#!/usr/bin/env python3
"""Lean v3.6.9 gov_transport base-MVM relaunch (reuse base_mvm_proof helpers, non-blocking).

Proves the two v3.6.9 gov_transport root-cause fixes on the EXACT workspace (<profile>) that
exhibited them, and produces terminal artifacts to root-cause the two remaining
BLOCKED bugs (nc-fidelity, nc-drift):
  - process-kill-watchdog: GIL-independent SIGTERM->SIGKILL backstop for the
    post-success teardown hang (gov_transport run <run_id> sat RUNNING 40min+).
  - mv-agg-arith-cast: CAST bare column operands inside SUM(a+b) so STRING-typed
    physical columns no longer fail metric-view DDL (dropped MV in prior gov_transport run).

Does NOT block on wait_terminal (parent) -- the agent self-launches a child; we poll
the child directly from the shell so monitoring stays responsive. Drops the catalog
first (prepare_catalog) so the run starts from a clean vibe_gov_transport_basemvm.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v369"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "gov_transport", "<profile>", "hr, project"


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_gov_transport_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v369"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
