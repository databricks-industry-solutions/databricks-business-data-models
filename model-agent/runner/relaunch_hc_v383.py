#!/usr/bin/env python3
"""v3.8.3 healthcare base-MVM live-prove on <profile> (reuse base_mvm_proof helpers, non-blocking).

Fresh healthcare rebuild on the FIXED agent. The prior healthcare run (1011303912650792) ran on
v3.8.0, which (a) lacked the 6 generic VREQ-lifecycle fixes shipped in v3.8.3 and (b) lacked the
v3.8.2 faulthandler-kill-backstop — it built a complete 25-domain / 564-product MVM (model.json
persisted) but then WEDGED in teardown for ~3h after FINAL-FLUSH because the v3.7.1 GIL-dependent
process-kill-watchdog armed (grace=300s) yet never fired. v3.8.3 carries the GIL-independent native
faulthandler terminator, so teardown self-terminates within grace.

healthcare uses NO business_domains widget (domains inferred) — the most complex repo vibe
(34.5KB). Per the user directive: generate_samples stays "0"; catalog name left as default.
Non-blocking: agent self-launches a child; poll from the shell. prepare_catalog drops the prior
vibe_healthcare_basemvm (the v3.8.0 artifact was archived to /tmp/hc_v380_archive first).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v383"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "healthcare", "<profile>", ""


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_healthcare_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v383"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
