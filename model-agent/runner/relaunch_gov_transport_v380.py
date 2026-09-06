#!/usr/bin/env python3
"""Lean v3.8.0 gov_transport base-MVM live-prove (reuse base_mvm_proof helpers, non-blocking).

Proves the v3.8.0 batch live on <profile> (the workspace that exhibited ~1% source-tag coverage):
  - v371-bulk-vibe-apply / v371-verify-prefix-all: the gov_transport vibe already mandates
    "tag EVERY attribute with gov_transport_source_attribute=<orig>" (v348 VREQ-011). v3.8.0 now
    applies that deterministically to 100% of the flat SSOT in finalize, so source-tag
    coverage must jump from ~1% to ~100% and the verifier must score it fulfilled.
  - output-parity-samples-csv: generate_samples is forced to 20 so the post-Phase-2 CSV
    export fires; samples/*.csv must appear on the volume.
  - output-parity-dbml-ext / rdf-ext: diagram/*.dbml + ontology/*.rdf must be written.
  - sandbox-py-dump: any VOV/SelfFixer code-gen must drop .py files under /sandbox.

Non-blocking: agent self-launches a child; poll the child from the shell. Drops the
catalog first via prepare_catalog so the run starts from a clean vibe_gov_transport_basemvm.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v380"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "gov_transport", "<profile>", "hr, project"


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_gov_transport_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v380"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    # v3.8.0: enable sample generation so the samples/*.csv export path (output-parity-samples-csv) fires.
    spec["tasks"][0]["notebook_task"]["base_parameters"]["generate_samples"] = "20"
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
