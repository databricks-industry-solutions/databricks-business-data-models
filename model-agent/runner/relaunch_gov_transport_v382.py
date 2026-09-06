#!/usr/bin/env python3
"""Lean v3.8.2 gov_transport base-MVM live-prove (reuse base_mvm_proof helpers, non-blocking).

Proves the v3.8.2 root-cause batch live on <profile> (the workspace that exhibited the
lying scoreboard + the 88min post-finalize hang on run <run_id>):
  - ground-truth-reaudit-post-tags: the EARLY ground-truth audit ran in the Track-1
    parallel next_vibes future BEFORE Track 3 applied physical SET TAGS, so every
    tag-coverage VREQ (subdomain/glossary/source_attribute) scored 0%/failed against an
    un-tagged catalog (gov_transport v2 recorded 56% while physical was ~77%). step_generate_next
    _vibes_late now clears the stale scorecard so the LATE pass re-grounds adherence
    against the REAL information_schema.column_tags. Recorded adherence must now equal
    physical truth (no more lying scoreboard).
  - faulthandler-kill-backstop: _spawn_process_kill_watchdog now arms a GIL-independent
    native C-thread terminator (faulthandler.dump_traceback_later(grace, exit=True)) so a
    teardown wedge self-terminates in <=grace instead of hanging for 88min.

Per the user directive (2026-06-18): samples are NOT generated (generate_samples stays "0"
from base_mvm_proof.build_spec) and the catalog name is left as base_mvm_proof default.

Non-blocking: agent self-launches a child; poll the child from the shell. Drops the
catalog first via prepare_catalog so the run starts from a clean vibe_gov_transport_basemvm.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v382"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "gov_transport", "<profile>", "hr, project"


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_gov_transport_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v382"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    # NOTE: generate_samples stays "0" (base_mvm_proof default) — user did not ask for samples.
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
