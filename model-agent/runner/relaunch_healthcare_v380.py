#!/usr/bin/env python3
"""Lean v3.8.0 healthcare base-MVM live-prove (reuse base_mvm_proof helpers, non-blocking).

Most-complex repo vibe (22 domains / 541 products, 34.5KB) on <profile>. Open roster
(business_domains empty) so the vibe-named-domain harvest + agentic convergence loop are
exercised at scale. Proves the v3.8.0 batch (quality-adherence-bonus, v371 bulk vibe caps,
bc-section-memo, dedup, STAGE-TIMING, sandbox dump) on a tier-1 industry. Non-blocking:
agent self-launches a child; the shell poller tracks both gov_transport + healthcare.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v380"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "healthcare", "<profile>", ""


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_healthcare_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v380"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
