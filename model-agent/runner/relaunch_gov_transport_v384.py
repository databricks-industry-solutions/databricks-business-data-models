#!/usr/bin/env python3
"""v3.8.4 gov_transport base-MVM relaunch (reuse base_mvm_proof helpers, non-blocking).

Proves the v3.8.4 root-cause fixes on <profile> (the workspace that exhibited the v383 hang +
lying scoreboard):
  - self-cancel-control-plane: serverless teardown hang -> Jobs runs/cancel on own run_id
  - gt-table-tag-enrich + gt-tag-verify-table-scope: subdomain/division false-negatives ->
    ground the audit verifier on physical information_schema.table_tags
  - canonical-key-apply: vibe-declared canonical keys honored as product PK (+ FK re-point)

Drops the catalog first. Non-blocking: the agent self-launches a child; poll the child directly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v384"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "gov_transport", "<profile>", "hr, project"


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_gov_transport_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v384"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
