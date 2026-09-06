#!/usr/bin/env python3
"""Lean v3.7.0 gov_transport base-MVM relaunch (reuse base_mvm_proof helpers, non-blocking).

Proves the THREE batched root-cause fixes live on the EXACT workspace (<profile>):
  - selffixer-endpoint-default-fallback (v3.7.0): SelfFixer cascade returned None
    -> closed-loop fixer inert on the Spark UDF path -> N2 fidelity 0.6364 < 0.85.
    Now falls back to the authoritative widget endpoint the main path uses.
  - process-kill-watchdog (v3.6.9): GIL-independent SIGTERM->SIGKILL backstop for
    the post-success teardown hang.
  - mv-agg-arith-cast (v3.6.9): CAST bare operands inside SUM(a+b) so STRING
    physical columns no longer fail metric-view DDL.

Non-blocking: agent self-launches a child; poll the child from the shell. Drops the
catalog first via prepare_catalog so the run starts from a clean vibe_gov_transport_basemvm.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v370"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "gov_transport", "<profile>", "hr, project"


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_gov_transport_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v370"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
